import copy
import os
import logging
import sys
import importlib

from fusesoc.vlnv import Vlnv
from fusesoc.config import Config
from fusesoc.coremanager import CoreManager
from fusesoc.utils import Launcher
from fusesoc import section

logger = logging.getLogger(__name__)

c = Config()
cm = CoreManager()

new_style_fusesoc = False

def get_core_requirements(system_name, output_directory, export=False, usage=['synth']):
    '''
    Takes a top level core name and produces a list of tuples of
    (filenames, include directories, generators).
    One tuple of each required core.
    '''
    output_directory = os.path.abspath(output_directory)
    if new_style_fusesoc:
        flags = {
            'flow': 'sim',
            'tool': 'ghdl',
            }
        cores = cm.get_depends(Vlnv(system_name), flags=flags)
    else:
        cores = cm.get_depends(Vlnv(system_name))
    logger.debug('cores are {}'.format(cores))
    all_requirements = []
    for core in cores:
        src_files = []
        incdirs = []
        generators = []
        logger.debug('expanding core {}'.format(core.name))
        # Perhaps we should be catching errors in setup.
        # Maybe this could be included in another core method instead?
        core.setup()
        if export:
            files_root = os.path.join(output_directory, core.sanitized_name)
            core.export(os.path.join(files_root))
        else:
            files_root = os.path.abspath(core.files_root)
        is_toplevel = (core.name.name == system_name)
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
            generators.append(g)
        for fs in core.file_sets:
            fileset_has_relevant_usage = set(fs.usage) & set(usage)
            if fileset_has_relevant_usage and (is_toplevel or not fs.private):
                for file in fs.file:
                    if file.is_include_file:
                        incdir = os.path.join(files_root, os.path.dirname(file.name))
                        if incdir not in incdirs:
                            incdirs.append(incdir)
                    else:
                        new_file = copy.deepcopy(file)
                        new_file.name = os.path.join(files_root, file.name)
                        src_files.append(new_file)
        all_requirements.append((src_files, incdirs, generators))
    return all_requirements


def process_generator(g, top_params):
    '''
    Runs a generator and returns a (filenames, include_directories) tuple
    of the generated items (although these may have already been generated
    on an earlier call).
    '''
    if g['type'] == 'python':
        sys.path.append(g['generator_dir'])
        module_name = g['module']
        if module_name not in sys.modules:
            logger.warning('Importing module {}'.format(module_name))
            module = importlib.import_module(module_name)
        else:
            module = sys.modules[module_name]
        function_name = g['function']
        if not hasattr(module, function_name):
            raise Exception('{} does not contain {} function'.format(
                module_name, function_name))
        else:
            g_func = getattr(module, function_name)
        if not os.path.exists(g['files_root']):
            os.makedirs(g['files_root'])
        params = [dict([(k, v) for k, v in paramset])
                  for paramset in g['params']]
        filenames, incdirs = g_func(directory=g['files_root'],
                                    generics=params,
                                    top_params=top_params)
    else:
        raise RuntimeError('Unknown generator type: {}.'.format(g['type']))
    return [section.File(fn) for fn in filenames], incdirs


def compile_elab_and_run(core_requirements, work_root, all_top_generics,
                         top_params, top_name):
    assert(all_top_generics)
    cmd = 'ghdl'
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
            assert(g['name'] not in generator_d)
            generator_d[g['name']] = g
            new_filenames, new_incdirs = process_generator(g, top_params)
            all_new_filenames += new_filenames
            all_new_incdirs += new_incdirs
        updated_src_files = all_new_filenames + updated_src_files
        updated_incdirs = all_new_incdirs + updated_incdirs
        logger.debug('Updated src files are {}'.format([f.name for f in updated_src_files]))
        # Compile files with ghdl
        for f in updated_src_files:
            args = ['-a']
            args += [f.name]
            Launcher(cmd, args,
                     cwd=work_root,
                     errormsg="Failed to analyze {}".format(f.name)).run()
        all_src_files += updated_src_files
        all_incdirs += updated_incdirs
    # Elaborate
    Launcher(cmd, ['-e']+[top_name],
             cwd=work_root,
             errormsg="Failed to elaborate {}".format(top_name)).run()
    # Run
    for top_generics in all_top_generics:
        stderr_fn = os.path.join(work_root, 'stderr_0')
        args = ['-r']
        args += [top_name]
        for generic_name, generic_value in top_generics.items():
            args.append('-g{}={}'.format(generic_name, generic_value))
        with open(stderr_fn, 'w') as stderr_f:
            Launcher(cmd, args,
                     cwd=work_root,
                     stderr=stderr_f,
                     errormsg="Simulation failed").run()
        ds = []
        with open(stderr_fn, 'r') as stderr_f:
            for line in stderr_f:
                d = {}
                pieces = line.split('Generator')
                if len(pieces) == 2:
                    params = pieces[1].split()
                    for param in params:
                        key, value = param.split('=')
                        assert(key not in d)
                        d[key] = value
                        ds.append(d)
        updated_generators = (len(ds) > 0)
        for d in ds:
            fd = frozenset((k, v) for k, v in d.items())
            g = generator_d[d['name']]
            g['params'].add(fd)
    return all_src_files, all_incdirs, updated_generators


def run_generators(requirements, work_root, top_name, generic_sets={}, top_params={}):
    updated = True
    while updated:
        src_files, incdirs, updated = compile_elab_and_run(
            requirements, work_root, generic_sets, top_params, top_name)
    return src_files, incdirs
