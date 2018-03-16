import logging

import jinja2

from fusesoc import config
from fusesoc.coremanager import CoreManager
from fusesoc_generators import coreprocessor

# Import section so that generator section gets registered.
from fusesoc_generators import section


logger = logging.getLogger(__name__)

cm = coreprocessor.cm


def add_cores_roots(cores_roots):
    if isinstance(cores_roots, str):
        raise ValueError('cores_roots should be a list of filenames.  It seems to be a single filename.')
    for cores_root in cores_roots:
        logger.debug('Adding directory {} to core_roots'.format(cores_root))
        cm.add_cores_root(cores_root)


def get_filenames_from_core(
        work_root, top_core_name, top_entity_name, generic_sets, top_params,
        additional_generator=None):
    '''
    Returns a list of filenames required by a core.  Generates the files if
    necessary.
    Args:
      `work_root`: The working directory for file generation.  Generated files
        are written here, and the directory is also used for temporary files.
      `top_core_name`: The name of the core that we want to generate.
      `top_entity_name`: The name of the entity in that core.
      `generic_sets`: At iterable of dictionarys of the generic parameters for
        which the core should work.
      `top_params`: Top level parameters that will be used by the generators.
      `additional_generator`: An optional generator that processes the list
        of files to generate an updated list of files.
    '''
    core_requirements = coreprocessor.get_core_requirements(
        top_core_name, work_root)
    src_files, incdirs = coreprocessor.run_generators(
        core_requirements, work_root, top_entity_name, generic_sets,
        top_params, additional_generator)
    filenames = []
    for f in src_files:
        if f.name not in filenames:
            filenames.append(f.name)
    return filenames


def format_file(template_filename, output_filename, parameters):
    '''
    Create a file from a template and parameters.
    '''
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**parameters)
    with open(output_filename, 'w') as g:
        g.write(formatted_text)
