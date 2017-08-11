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
    core_requirements = coreprocessor.get_core_requirements(top_core_name, work_root)
    src_files, incdirs = coreprocessor.run_generators(
        core_requirements, work_root, top_entity_name, generic_sets, top_params, additional_generator)
    filenames = [f.name for f in src_files]
    return filenames
