import zss

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


def calculate_edit_distance(tree1: ConcurrencyTree, tree2: ConcurrencyTree) -> int:
    return zss.simple_distance(tree1, tree2, get_children, get_label, label_dist)


def get_children(n):
    return n.children


def get_label(n):
    if n.op is not None:
        return n.op.value

    return n.label


def label_dist(a, b):
    if a == b:
        return 0
    return 1
