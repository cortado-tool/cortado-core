from enum import Enum
from typing import Tuple, List, Optional, Set

from cortado_core.eventually_follows_pattern_mining.obj import (
    SubPattern,
    EventuallyFollowsPattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator as ConcurrencyTreeOperator,
)


class EventuallyFollowsStrategy(Enum):
    RealEventuallyFollows = 1
    SoftEventuallyFollows = 2


def __set_tree_attributes_bfs(tree: ConcurrencyTree, offset: int):
    """
    Sets the bfsid attribute for all nodes in the tree
    """
    queue = [tree]

    while queue:
        current = queue.pop(0)
        current.bfsid = offset
        offset += 1

        if current.children:
            queue += current.children


def set_tree_attributes(tree: ConcurrencyTree):
    __set_tree_attributes_bfs(tree, 0)
    __set_tree_attributes_dfs(tree, 0, 0)


def __set_tree_attributes_dfs(
    tree: ConcurrencyTree, current_index: int, depth: int
) -> int:
    tree.id = tree.id or current_index
    tree.depth = depth
    current_index += 1
    depth += 1

    for child in tree.children:
        current_index = __set_tree_attributes_dfs(child, current_index, depth)

    return current_index


def is_eventually_follows_relation_with_ef_dict(
    left_check_node: ConcurrencyTree, right_check_node: ConcurrencyTree, ef_dict
) -> bool:
    if left_check_node.id not in ef_dict:
        return False

    return right_check_node.id >= ef_dict[left_check_node.id]


def is_eventually_follows_relation(
    left_occurrence: Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]],
    right_occurrence: Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]],
) -> bool:
    """
    Determines whether there is a eventually follows relationship between left_occurrence and right_occurrence.
    Assumes that depth is set for all nodes (e.g. by calling __set_tree_attributes()).
    Assumes that is it not possible that a direct child of a sequential operator is a sequential operator itself.
    Assumes that the left occurrence is actually left of the right occurrence. Has to be ensured before,
     e.g. by a preorder index check.
    :param left_occurrence:
    :param right_occurrence:
    :return:
    """

    left_check_node = get_left_check_node(left_occurrence)
    right_check_node = get_right_check_node(right_occurrence)

    lca, has_sequential_in_between = get_lca_with_ef_sequential_check(
        left_check_node, right_check_node
    )
    if not has_sequential_in_between:
        return False

    return lca.op == ConcurrencyTreeOperator.Sequential


def get_left_check_node(left_occurrence):
    _, left_rmo, left_ro = left_occurrence

    if left_ro[-1].op == ConcurrencyTreeOperator.Sequential:
        if len(left_ro[-1].children) == 0:
            raise Exception(
                "EF-relation is not defined for single sequential operators"
            )
        left_root_id = left_ro[-1].id
        left_check_node = left_rmo
        while left_check_node.parent.id != left_root_id:
            left_check_node = left_check_node.parent
    else:
        left_check_node = left_ro[-1]

    return left_check_node


def get_right_check_node(right_occurrence):
    right_lmo, _, right_ro = right_occurrence
    if right_ro[0].op == ConcurrencyTreeOperator.Sequential:
        if len(right_ro[0].children) == 0:
            raise Exception(
                "EF-relation is not defined for single sequential operators"
            )
        right_root_id = right_ro[0].id
        right_check_node = right_lmo
        while right_check_node.parent.id != right_root_id:
            right_check_node = right_check_node.parent
    else:
        right_check_node = right_ro[0]

    return right_check_node


def get_left_check_node_for_full_occurrence(pattern: SubPattern, left_occurrence):
    if pattern.operator != ConcurrencyTreeOperator.Sequential:
        return left_occurrence[pattern.id]

    if len(pattern.children) == 0:
        raise Exception("EF-relation is not defined for single sequential operators")

    return left_occurrence[pattern.children[-1].id]


def get_right_check_node_for_full_occurrence(pattern: SubPattern, right_occurrence):
    if pattern.operator != ConcurrencyTreeOperator.Sequential:
        return right_occurrence[pattern.id]

    if len(pattern.children) == 0:
        raise Exception("EF-relation is not defined for single sequential operators")

    return right_occurrence[pattern.children[0].id]


def lca_is_sequential(tree1: ConcurrencyTree, tree2: ConcurrencyTree) -> bool:
    return get_lca(tree1, tree2).op == ConcurrencyTreeOperator.Sequential


def get_lca_with_ef_sequential_check(
    tree1: ConcurrencyTree, tree2: ConcurrencyTree
) -> Tuple[ConcurrencyTree, bool]:
    depth_difference = tree1.depth - tree2.depth
    has_sequential_in_between = False
    while depth_difference > 0:
        parent = tree1.parent
        if (
            not has_sequential_in_between
            and parent.op == ConcurrencyTreeOperator.Sequential
        ):
            if tree1.rSib is not None:
                has_sequential_in_between = True

        tree1 = parent
        depth_difference -= 1

    while depth_difference < 0:
        parent = tree2.parent
        if (
            not has_sequential_in_between
            and parent.op == ConcurrencyTreeOperator.Sequential
        ):
            if id(parent.children[0]) != id(tree2):
                has_sequential_in_between = True

        tree2 = parent
        depth_difference += 1

    while id(tree1) != id(tree2):
        parent1 = tree1.parent
        parent2 = tree2.parent

        if (
            not has_sequential_in_between
            and parent1.op == ConcurrencyTreeOperator.Sequential
        ):
            if tree1.rSib is not None and id(tree1.rSib) != id(tree2):
                has_sequential_in_between = True

        if (
            not has_sequential_in_between
            and parent2.op == ConcurrencyTreeOperator.Sequential
        ):
            child_index = get_index(parent2.children, tree2)
            if child_index != 0 and id(parent2.children[child_index - 1]) != id(tree1):
                has_sequential_in_between = True

        tree1 = parent1
        tree2 = parent2

    return tree1, has_sequential_in_between


def get_lca(tree1: ConcurrencyTree, tree2: ConcurrencyTree) -> ConcurrencyTree:
    depth_difference = tree1.depth - tree2.depth
    while depth_difference > 0:
        tree1 = tree1.parent
        depth_difference -= 1

    while depth_difference < 0:
        tree2 = tree2.parent
        depth_difference += 1

    while id(tree1) != id(tree2):
        tree1 = tree1.parent
        tree2 = tree2.parent

    return tree1


def get_first_ef_node_id_per_node_for_trees(
    trees: List[ConcurrencyTree],
    ef_strategy: EventuallyFollowsStrategy = EventuallyFollowsStrategy.RealEventuallyFollows,
):
    result = dict()

    for i, tree in enumerate(trees):
        result[i] = get_first_ef_node_id_per_node(tree, ef_strategy)

    return result


def get_first_ef_node_id_per_node(
    tree: ConcurrencyTree, ef_strategy: EventuallyFollowsStrategy
):
    inactive_nodes = set()
    active_nodes = set()
    result = dict()

    if ef_strategy == EventuallyFollowsStrategy.RealEventuallyFollows:
        __update_active_inactive_nodes(tree, inactive_nodes, active_nodes, result)
    else:
        __update_active_nodes_soft_ef(tree, active_nodes, result)

    return result


def __update_active_nodes_soft_ef(tree, active_nodes, ef_dict):
    if tree.parent is None:
        for child in tree.children:
            active_nodes = __update_active_nodes_soft_ef(child, active_nodes, ef_dict)
        return active_nodes

    elif __has_sequential_parent(tree):
        active_nodes = __apply_active_nodes(active_nodes, ef_dict, tree)

        if __has_no_sequential_child(tree):
            active_nodes.add((tree.id, tree.id))

        for child in tree.children:
            active_nodes = __update_active_nodes_soft_ef(child, active_nodes, ef_dict)

        active_nodes.add((tree.id, tree.id))
        return active_nodes
    else:
        for child in tree.children:
            active_nodes = __update_active_nodes_soft_ef(child, active_nodes, ef_dict)

        search_minimum = __get_search_minimum(tree.parent)
        if search_minimum is None:
            return active_nodes

        active_nodes.add((tree.id, search_minimum))

        return active_nodes


def __update_active_inactive_nodes(
    tree: ConcurrencyTree,
    active_nodes: Set[Tuple[int, int]],
    inactive_nodes: Set[Tuple[int, int]],
    ef_dict,
):
    if tree.parent is None:
        for child in tree.children:
            active_nodes, inactive_nodes = __update_active_inactive_nodes(
                child, active_nodes, inactive_nodes, ef_dict
            )
        return active_nodes, inactive_nodes

    elif __has_sequential_parent(tree):
        active_nodes = __apply_active_nodes(active_nodes, ef_dict, tree)

        if __has_no_sequential_child(tree):
            active_nodes, inactive_nodes = __move_inactive_to_active(
                inactive_nodes, active_nodes, tree
            )
            inactive_nodes.add((tree.id, tree.id))

        for child in tree.children:
            active_nodes, inactive_nodes = __update_active_inactive_nodes(
                child, active_nodes, inactive_nodes, ef_dict
            )

        inactive_nodes.add((tree.id, tree.id))
        return active_nodes, inactive_nodes
    else:
        for child in tree.children:
            active_nodes, inactive_nodes = __update_active_inactive_nodes(
                child, active_nodes, inactive_nodes, ef_dict
            )

        search_minimum = __get_search_minimum(tree.parent)
        if search_minimum is None:
            return active_nodes, inactive_nodes

        inactive_nodes.add((tree.id, search_minimum))

        return active_nodes, inactive_nodes


def __apply_active_nodes(active_nodes, ef_dict, tree):
    removal_nodes = set()
    for active_node, min_node_id in active_nodes:
        if tree.id >= min_node_id:
            ef_dict[active_node] = tree.id
            removal_nodes.add((active_node, min_node_id))

    return active_nodes.difference(removal_nodes)


def __has_sequential_parent(tree):
    return (
        tree.parent is not None and tree.parent.op == ConcurrencyTreeOperator.Sequential
    )


def __has_no_sequential_child(tree):
    return len(tree.children) == 0 or tree.children[-1].op is None


def __move_inactive_to_active(inactive_nodes, active_nodes, tree):
    new_active_nodes = set(
        [(n, min_n_id) for n, min_n_id in inactive_nodes if tree.id >= min_n_id]
    )
    active_nodes = active_nodes.union(new_active_nodes)
    inactive_nodes = inactive_nodes.difference(new_active_nodes)

    return active_nodes, inactive_nodes


def __get_search_minimum(tree: ConcurrencyTree) -> Optional[int]:
    node = tree
    while node.rSib is None and node.parent is not None:
        node = node.parent

    if node.rSib is None:
        return None

    return node.rSib.id


def get_index(l, elem, start=0):
    idx = l.index(elem, start)

    if id(elem) == id(l[idx]):
        return idx

    return get_index(l, elem, idx + 1)


def get_preorder_sorted_pattern_nodes(
    pattern: EventuallyFollowsPattern,
) -> List[SubPattern]:
    res = []
    for sub_pattern in pattern.sub_patterns:
        res += get_preorder_sorted_sub_pattern_nodes(sub_pattern)

    return res


def get_preorder_sorted_sub_pattern_nodes(sub_pattern: SubPattern) -> List[SubPattern]:
    res = [sub_pattern]

    for child in sub_pattern.children:
        res += get_preorder_sorted_sub_pattern_nodes(child)

    return res


def get_root(node):
    while node.parent is not None:
        node = node.parent

    return node


def get_leftmost_leaf(root):
    node = root
    while len(node.children) != 0:
        node = node.children[0]

    return node


def get_rightmost_leaf(root):
    node = root
    while len(node.children) != 0:
        node = node.children[-1]

    return node


def get_left_sub_pattern(
    pattern: EventuallyFollowsPattern, root: SubPattern
) -> Optional[SubPattern]:
    if root.id == 0:
        return None

    idx = get_index(pattern.sub_patterns, root)
    return pattern.sub_patterns[idx - 1]


def get_rightmost_path_preorder_indexes(rml: SubPattern) -> List[int]:
    res = []
    node = rml

    if node.operator is None:
        res.append(node.id)

    while node.parent is not None:
        res.append(node.id)
        node = node.parent

    return res


def is_on_rightmost_path(node):
    while node.parent is not None:
        if get_right_sibling(node) is not None:
            return False

        node = node.parent

    return True


def get_siblings_in_between(left_node, right_node):
    if left_node is None:
        idx_left = -1
    else:
        idx_left = get_index(left_node.parent.children, left_node)
    idx_right = get_index(right_node.parent.children, right_node)

    return right_node.parent.children[idx_left + 1 : idx_right]


def get_right_siblings(node):
    idx = get_index(node.parent.children, node)
    if idx == len(node.parent.children) - 1:
        return []

    return node.parent.children[idx + 1 :]


def get_right_sibling(node):
    idx = get_index(node.parent.children, node)
    if idx == len(node.parent.children) - 1:
        return None

    return node.parent.children[idx + 1]


def get_left_sibling(node):
    idx = get_index(node.parent.children, node)
    if idx == 0:
        return None

    return node.parent.children[idx - 1]


def get_level_1_parent(tree: ConcurrencyTree) -> Optional[ConcurrencyTree]:
    node = tree
    if node.parent is None:
        return None
    while node.parent.parent is not None:
        node = node.parent
    return node
