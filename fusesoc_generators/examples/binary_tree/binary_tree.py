import os
import itertools

from fusesoc_generators import utils

thisdir = os.path.abspath(os.path.dirname(__file__))


def logceil(val):
    f = 1
    p = 0
    while f < val:
        f *= 2
        p += 1
    return p
        

def generate(directory, generics, top_params):
    all_n_inputs = set([int(d['n_inputs']) for d in generics])
    operations = set([d['operation'] for d in generics])
    generated_fns = []

    generated_fns.append(os.path.join(thisdir, 'binary_minimum.vhd'))

    # Make operation
    binary_tree_operation_tn = os.path.join(thisdir, 'binary_tree_operation.vhd')
    binary_tree_operation_fn = os.path.join(directory, 'binary_tree_operation.vhd')
    utils.format_file(
        binary_tree_operation_tn, binary_tree_operation_fn, {'operations': operations})
    generated_fns.append(binary_tree_operation_fn)

    # Make binary_tree_level
    max_n_inputs = max(list(all_n_inputs) + [2])
    max_level = logceil(max_n_inputs)
    binary_tree_level_tn = os.path.join(thisdir, 'binary_tree_level.vhd')
    for level in range(max_level, -1, -1):
        binary_tree_level_fn = os.path.join(directory, 'binary_tree_level_{}.vhd'.format(level))
        utils.format_file(
            binary_tree_level_tn, binary_tree_level_fn, {'level': level, 'last_level': level == max_level})
        generated_fns.append(binary_tree_level_fn)

    # Make binary_tree.vhd
    operation_and_n_inputs = [
        (operation, n_inputs) for n_inputs, operation in
        itertools.product(all_n_inputs, operations)] 
    binary_tree_tn = os.path.join(thisdir, 'binary_tree.vhd')
    binary_tree_fn = os.path.join(directory, 'binary_tree.vhd')
    utils.format_file(
        binary_tree_tn, binary_tree_fn,
        {'operation_and_n_inputs': operation_and_n_inputs})
    generated_fns.append(binary_tree_fn)

    return generated_fns, []
