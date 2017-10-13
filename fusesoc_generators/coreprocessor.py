'''
Defines functions for an extended elaboration that includes steps for
generating additional files.
'''

import copy
import os
import logging
import sys
import importlib

from fusesoc.vlnv import Vlnv
from fusesoc.coremanager import CoreManager
from fusesoc.utils import Launcher
from fusesoc import section
try:
    from fusesoc.version import version
except ImportError:
    version =None


logger = logging.getLogger(__name__)

cm = CoreManager()


def get_version():
    '''
    Convert the version string into a list of integers so that
    it can be compared easily.
    '''
    if version is None:
        bits_as_int = [0, 0]
    else:
        bits = version.split('.')
        bits_as_int = []
        for bit in bits:
            try:
                as_int = int(bit)
            except ValueError:
                as_int = bit
            bits_as_int.append(as_int)
    return bits_as_int


def get_cores(system_name):
    '''
    Gets a list of core dependencies from a top level core name.
    '''
    vers = get_version()
    if vers[:2] > [1, 6]:
        flags = {
            'flow': 'sim',
            'tool': 'ghdl',
            }
        cores = cm.get_depends(Vlnv(system_name), flags=flags)
    else:
        cores = cm.get_depends(Vlnv(system_name))
    return cores


def get_core_files(core):
    '''
    Get all the files and include directories required by a core for synthesis.
    Ignores generators.
    '''
    usage = ['synth']
    files_root = os.path.abspath(core.files_root)
    src_files = []
    incdirs = []
    for fileset in core.file_sets:
        fileset_has_relevant_usage = set(fileset.usage) & set(usage)
        if fileset_has_relevant_usage and not fileset.private:
            for file in fileset.file:
                if file.is_include_file:
                    incdir = os.path.join(
                        files_root, os.path.dirname(file.name))
                    if incdir not in incdirs:
                        incdirs.append(incdir)
                else:
                    new_file = copy.deepcopy(file)
                    new_file.name = os.path.join(files_root, file.name)
                    src_files.append(new_file)
    return src_files, incdirs


def get_core_generators(core, output_directory):
    '''
    Get all the generators directly required by this core (not dependencies).
    `output_directory` is the directory where generated files will be placed.
    '''
    if hasattr(core, 'generator') and core.generator:
        logger.debug('{} has a generator'.format(core.name.name))
        g = {
            'function': core.generator.function,
            'module': core.generator.module,
            'type': core.generator.type,
            'files_root': os.path.join(output_directory),
            'generator_dir': os.path.abspath(core.files_root),
            'name': core.name.name,
            'params': set(),
            }
        generators = [g]
    else:
        generators = []
    return generators


def get_core_requirements(system_name, output_directory):
    '''
    Takes a top level core name and produces a list of tuples of
    (filenames, include directories, generators).
    One tuple for each required core.
    `output_directory` is the directory where generated files are placed.
    '''
    all_requirements = []
    abs_output_directory = os.path.abspath(output_directory)
    cores = get_cores(system_name)
    for core in cores:
        core.setup()
        src_files, incdirs = get_core_files(core)
        generators = get_core_generators(core, abs_output_directory)
        all_requirements.append((src_files, incdirs, generators))
    return all_requirements


def process_generator(generator, top_params):
    '''
    Runs a generator and returns a (filenames, include_directories) tuple
    of the generated items (although these may have already been generated
    on an earlier call).
    '''
    if generator['type'] == 'python':
        sys.path.append(generator['generator_dir'])
        module_name = generator['module']
        if module_name not in sys.modules:
            logger.warning('Importing module {}'.format(module_name))
            module = importlib.import_module(module_name)
        else:
            module = sys.modules[module_name]
        function_name = generator['function']
        if not hasattr(module, function_name):
            raise Exception('{} does not contain {} function'.format(
                module_name, function_name))
        else:
            g_func = getattr(module, function_name)
        if not os.path.exists(generator['files_root']):
            os.makedirs(generator['files_root'])
        params = [dict([(k, v) for k, v in paramset])
                  for paramset in generator['params']]
        filenames, incdirs = g_func(directory=generator['files_root'],
                                    generics=params,
                                    top_params=top_params)
    else:
        raise RuntimeError(
            'Unknown generator type: {}.'.format(generator['type']))
    return [section.File(fn) for fn in filenames], incdirs


def run_generators_once(core_requirements, all_top_generics, top_params):
    '''
    Takes a list of core requirements (filenames, include_directories, generators) tuples,
    runs the generators and combines the results into a (dictionary of generators,
    list of src files, list of include directories) tuple.
    '''
    if not all_top_generics:
        raise ValueError(
            'all_to_generics arguments must be an iterable of non-zero length')
    assert all_top_generics
    generator_d = {}
    all_src_files = []
    all_incdirs = []
    for requirements in core_requirements:
        src_files, incdirs, generators = requirements
        updated_src_files = src_files.copy()
        updated_incdirs = incdirs.copy()
        all_new_filenames = []
        all_new_incdirs = []
        for g in generators:
            logger.debug('Running generator {}'.format(g['name']))
            assert g['name'] not in generator_d
            generator_d[g['name']] = g
            new_filenames, new_incdirs = process_generator(g, top_params)
            all_new_filenames += new_filenames
            all_new_incdirs += new_incdirs
        updated_src_files = all_new_filenames + updated_src_files
        updated_incdirs = all_new_incdirs + updated_incdirs
        logger.debug('Updated src files are {}'.format(
            [f.name for f in updated_src_files]))
        all_src_files += updated_src_files
        all_incdirs += updated_incdirs
    return generator_d, all_src_files, all_incdirs


def compile_src_files(work_root, src_files):
    '''
    Compiles src files using ghdl.
    '''
    logger.debug('compiling src files {}'.format([f.name for f in src_files]))
    for f in src_files:
        args = ['-a', '--std=08']
        args += [f.name]
        logger.debug('Compiling {}'.format(f.name))
        Launcher('ghdl', args,
                 cwd=work_root,
                 errormsg="Failed to analyze {}".format(f.name)).run()


def elaborate(work_root, top_name):
    '''
    Elaborate the design using ghdl.
    '''
    Launcher('ghdl', ['-e', '--std=08']+[top_name],
             cwd=work_root,
             errormsg="Failed to elaborate {}".format(top_name)).run()


def run_single(work_root, top_name, top_generics):
    '''
    Run a single ghdl simulation and return a list of errors.
    Used to determine which generics are required by generated entities.
    '''
    stderr_fn = os.path.join(work_root, 'stderr_0')
    stdout_fn = os.path.join(work_root, 'stdout_0')
    args = ['-r', '--std=08']
    args += [top_name]
    for generic_name, generic_value in top_generics.items():
        args.append('-g{}={}'.format(generic_name, generic_value))
    with open(stderr_fn, 'w') as stderr_f:
        with open(stdout_fn, 'w') as stdout_f:
            Launcher('ghdl', args,
                     cwd=work_root,
                     stdout=stdout_f,
                     stderr=stderr_f,
                     errormsg="Simulation failed").run()
    with open(stderr_fn, 'r') as stderr_f:
        error_lines = stderr_f.readlines()
    with open(stdout_fn, 'r') as stdout_f:
        error_lines += stdout_f.readlines()
    return error_lines


def extract_generics(error_lines):
    '''
    Parse the errors output from ghdl to determine what generics
    are required by the generators.
    '''
    ds = []
    for line in error_lines:
        d = {}
        pieces = line.split('Generator')
        if len(pieces) == 2:
            params = pieces[1].split()
            for param in params:
                key, value = param.split('=')
                assert key not in d
                d[key] = value
                ds.append(d)
    return ds


def run(work_root, top_name, all_top_generics, generator_d):
    '''
    Run the design using ghdl.
    The purpose is to see which modules are used with which generic parameters
    so that we can call the generic parameters appropriately.
    '''
    updated_generators = False
    for top_generics in all_top_generics:
        error_lines = run_single(work_root, top_name, top_generics)
        ds = extract_generics(error_lines)
        for d in ds:
            fd = frozenset((k, v) for k, v in d.items())
            g = generator_d[d['name']]
            g['params'].add(fd)
            updated_generators = True
    return updated_generators


def compile_elab_and_run(core_requirements, work_root, all_top_generics,
                         top_params, top_name, additional_generator=None):
    '''
    Run the generators, compile and elaborate the files, and run ghdl
    to see if any of the generators were missing generics.
    '''
    generator_d, all_src_files, all_incdirs = run_generators_once(
        core_requirements, all_top_generics, top_params)
    if additional_generator is not None:
        file_names = [f.name for f in all_src_files]
        new_file_names = additional_generator(work_root, file_names)
        extended_src_files = [section.File(f) for f in new_file_names]
    else:
        extended_src_files = all_src_files
    compile_src_files(work_root, extended_src_files)
    if top_name is not None:
        elaborate(work_root, top_name)
        updated_generators = run(
            work_root, top_name, all_top_generics, generator_d)
    else:
        updated_generators = False
    return extended_src_files, all_incdirs, updated_generators


def run_generators(requirements, work_root, top_name, generic_sets=None,
                   top_params=None, additional_generator=None):
    '''
    Iteratively run the generators, and then run the core in ghdl to make
    sure the generators were passed the correct generic parameters.
    '''
    if generic_sets is None:
        generic_sets = {}
    if top_params is None:
        top_params = {}
    updated = True
    while updated:
        src_files, incdirs, updated = compile_elab_and_run(
            requirements, work_root, generic_sets, top_params, top_name,
            additional_generator)
    return src_files, incdirs
