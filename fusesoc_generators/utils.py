from fusesoc.coremanager import CoreManager
from fusesoc_generators import coreprocessor

# Import section so that generator section gets registered.
from fusesoc_generators import section


cm = CoreManager()


def add_cores_roots(cores_roots):
    for cores_root in cores_roots:
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
    filenames = [f.name for f in src_files]
    return filenames
