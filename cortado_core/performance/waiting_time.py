from typing import List
from cortado_core.performance.utils import get_all_nodes
from cortado_core.process_tree_utils.miscellaneous import is_tau_leaf

from pm4py.objects.process_tree.obj import Operator, ProcessTree


def get_completing_nodes(tree: ProcessTree):
    if tree.operator is None:
        return {tree}
    if tree.operator == Operator.SEQUENCE:
        return get_completing_nodes(tree.children[-1])
    if tree.operator in [Operator.PARALLEL, Operator.XOR]:
        return [completing for n in tree.children for completing in get_completing_nodes(n)]
    if tree.operator == Operator.LOOP:
        return get_completing_nodes(tree.children[0])
    assert False, f"tree operator {tree.operator} not implemented"


def fix_tau(enabling_nodes: List[ProcessTree]):
    nodes = set()
    for n in enabling_nodes:
        if is_tau_leaf(n):
            tau_enabling = get_enabling_nodes(n)
            nodes.update(tau_enabling)
        else:
            nodes.add(n)
    return nodes


def get_enabling_nodes(tree: ProcessTree):
    """
    Gets all enabling nodes.
    These are all nodes that when the last of them finishes, the given tree node is enabled
    """
    parent: ProcessTree = tree.parent
    if parent is None:
        return {None}
    elif parent.operator == Operator.SEQUENCE:
        parent_children: List[ProcessTree] = parent.children
        self_index = parent_children.index(tree)
        # first node in sequence is enabled when parent node is enabled
        if self_index == 0:
            return get_enabling_nodes(parent)
        # other node are enabled by previous node in the sequence
        enabling_node = parent_children[self_index - 1]
        # if enabling_node is tau, get enabling of tau
        return fix_tau(get_completing_nodes(enabling_node))
    elif parent.operator == Operator.LOOP:
        parent_children: List[ProcessTree] = parent.children
        all_child_nodes = get_all_nodes(tree.parent) - {tree.parent}
        if all([is_tau_leaf(t) for t in all_child_nodes]):
            return get_enabling_nodes(parent)
        self_index = parent_children.index(tree)
        # Do node is enabled by parent or redo node
        if self_index == 0:
            redo = fix_tau([parent_children[-1]])
            return get_enabling_nodes(parent).union(redo)
        # redo node is enabled by do node
        enabling_node = parent_children[0]
        # if enabling_node is tau, get enabling of tau
        completing_nodes = get_completing_nodes(enabling_node)
        return fix_tau(completing_nodes)
    elif parent.operator in [Operator.PARALLEL, Operator.XOR]:
        # child nodes of parallel or xor are directly enabled when parent is enabled
        return get_enabling_nodes(tree.parent)
    else:
        assert False, f"tree operator {parent.label} not implemented"


def get_starting_nodes(tree: ProcessTree):
    if tree.operator is None:
        return [tree]
    elif tree.operator == Operator.SEQUENCE:
        return get_starting_nodes(tree.children[0])
    elif tree.operator == Operator.LOOP:
        return get_starting_nodes(tree.children[0])
    elif tree.operator in [Operator.PARALLEL, Operator.XOR]:
        return [n for n in tree.children for n in get_starting_nodes(n)]
    return [n for n in tree.children for n in get_starting_nodes(n)]
