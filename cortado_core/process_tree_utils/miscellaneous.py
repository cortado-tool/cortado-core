from typing import List, Tuple, Set

from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse


# function is needed to have a unique key in a dictionary for structurally identical but different trees in mem
def pt_dict_key(pt: ProcessTree) -> Tuple[ProcessTree, int]:
    return pt, id(pt)


def get_index_of_pt_in_children_list(pt: ProcessTree, wanted_child: ProcessTree) -> int:
    for i, c in enumerate(pt.children):
        if c is wanted_child:
            return i
    return -1


def is_subtree(pt: ProcessTree, potential_subtree_of_pt: ProcessTree) -> bool:
    if pt is potential_subtree_of_pt:
        return True
    elif pt.children:
        res = False
        for c in pt.children:
            res = res or is_subtree(c, potential_subtree_of_pt)
        return res
    else:
        return False


def is_leaf_node(process_tree: ProcessTree) -> bool:
    # TODO investigate if addition from comment causes any problems
    return process_tree is not None and \
           len(process_tree.children) == 0 and \
           process_tree.operator is None


def get_root(process_tree: ProcessTree) -> ProcessTree:
    while process_tree.parent:
        process_tree = process_tree.parent
    return process_tree


def get_height(process_tree: ProcessTree) -> int:
    if not process_tree.children:
        return 1
    else:
        height_values: List[int] = [get_height(c) + 1 for c in process_tree.children]
        return max(height_values)


def get_number_leaves(process_tree: ProcessTree) -> int:
    if not process_tree.children:
        return 1
    else:
        children: List[int] = [get_number_leaves(c) for c in process_tree.children]
        return sum(children)


def get_number_silent_leaves(process_tree: ProcessTree) -> int:
    if not process_tree.children and process_tree.label is None:
        return 1
    else:
        children: List[int] = [get_number_silent_leaves(c) for c in process_tree.children]
        return sum(children)


def get_number_nodes(process_tree: ProcessTree) -> int:
    if process_tree.children:
        children: List[int] = [get_number_nodes(c) for c in process_tree.children]
        return sum(children) + 1
    else:
        return 1


def get_pt_node_height(node: ProcessTree) -> int:
    """
    returns the node's height
    the root node has height 0, children of root have height 1, etc.
    :param node:
    :return:
    """
    if node.parent:
        return 1 + get_pt_node_height(node.parent)
    else:
        return 0


def subtree_is_part_of_tree_based_on_obj_id(subtree: ProcessTree, tree: ProcessTree) -> bool:
    if subtree is tree:
        return True
    else:
        current_tree = subtree
        while current_tree.parent:
            if current_tree.parent is tree:
                return True
            current_tree = current_tree.parent
        return False


def subtree_contained_in_tree(subtree: ProcessTree, tree: ProcessTree) -> bool:
    if subtree == tree:
        return True
    else:
        res = False
        for c in tree.children:
            res = res or subtree_contained_in_tree(subtree, c)
        return res


def replace_tree_in_children(parent_tree: ProcessTree, old_tree: ProcessTree, new_tree: ProcessTree) -> ProcessTree:
    for i in range(len(parent_tree.children)):
        if parent_tree.children[i] is old_tree:
            parent_tree.children[i] = new_tree
            new_tree.parent = parent_tree
            return parent_tree
    raise ValueError("old_tree not found")


def is_tau_leaf(pt: ProcessTree):
    return (pt.children == [] or pt.children is None) and pt.operator is None and pt.label == None


def get_all_leaf_node_labels(tree: ProcessTree, all_labels=None, duplicated_labels=None) -> Tuple[Set[str], Set[str]]:
    if all_labels is None:
        all_labels: Set = set()
    if duplicated_labels is None:
        duplicated_labels: Set = set()

    if is_leaf_node(tree):
        if tree.label in all_labels:
            duplicated_labels.add(tree.label)
        else:
            all_labels.add(tree.label)
    else:
        for c in tree.children:
            res1, res2 = get_all_leaf_node_labels(c, all_labels, duplicated_labels)
            all_labels.union(res1)
            duplicated_labels.union(res2)
    return all_labels, duplicated_labels


def get_all_leaf_nodes(tree: ProcessTree, all_trees=None) -> List[ProcessTree]:
    if all_trees is None:
        all_trees: List = []

    if is_leaf_node(tree):
        all_trees.append(tree)
    else:
        for c in tree.children:
            get_all_leaf_nodes(c, all_trees)
    return all_trees


if __name__ == "__main__":
    pt_1 = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    pt_2 = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    pt_3 = pt_parse("-> (*(X(->('A','B'),->('B','D')),tau) ,->('E','F') )")
    pt_4 = pt_parse("-> (*(X(->('A','B'))")

    print((pt_1 == pt_2))  # True
    print((pt_1 == pt_1))  # True
    print((pt_4 == pt_3))  # False
    print((pt_2 == pt_3))  # False
    print((pt_1 == pt_3))  # False

    print(get_all_leaf_node_labels(pt_1))
    print(get_all_leaf_node_labels(pt_3))
    print(get_all_leaf_node_labels(pt_4))
