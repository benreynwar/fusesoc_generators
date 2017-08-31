import sys
import os

from vunit import VUnitCLI, VUnit

from fusesoc_generators import get_filenames_from_core, add_cores_roots
from fusesoc_generators.examples.binary_tree import binary_tree

def test_binary_tree():
    # FIXME: Why does commented out lines not work.
    #args = VUnitCLI().parse_args(argv=sys.argv)
    #vu = VUnit.from_args(args)
    vu = VUnit.from_argv()
    lib_name = 'lib'
    lib = vu.add_library(lib_name)
    vu._builtins._add_osvvm()
    vu._builtins._add_data_types()
    vu._builtins.add_vhdl_builtins()

    add_cores_roots([binary_tree.thisdir])
    work_root = 'fusesoc_generators_test_work_directory'
    os.mkdir(work_root)
    filenames = get_filenames_from_core(
        work_root=work_root,
        top_core_name='binary_tree',
        top_entity_name='binary_tree',
        generic_sets=[{
            'width': 3,
            'n_inputs': 7,
            'meta_width': 4,
            'operation': 'binary_minimum',
            'pipeline': 0,
        }],
        top_params={},
    )
    filenames.append(os.path.join(binary_tree.thisdir, 'binary_tree_tb.vhd'))
    lib.add_source_files(filenames)
    vu.main()


if __name__ == '__main__':
    test_binary_tree()
