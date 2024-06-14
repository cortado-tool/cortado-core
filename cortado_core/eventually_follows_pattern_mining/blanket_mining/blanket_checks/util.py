from typing import Set

from cortado_core.eventually_follows_pattern_mining.obj import (
    SubPattern,
    EventuallyFollowsPattern,
)
from cortado_core.eventually_follows_pattern_mining.util.activities import (
    get_labeled_nodes_in_concurrency_tree,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    get_index,
    get_left_sibling,
    get_rightmost_leaf,
    get_leftmost_leaf,
    get_right_sibling,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator,
    ConcurrencyTree,
)


def enforce_left_completeness_for_children(rml: SubPattern) -> bool:
    if rml.operator != cTreeOperator.Sequential:
        return False

    node = rml
    while node.parent is not None:
        if node.parent.operator == cTreeOperator.Sequential:
            if id(node.parent.children[0]) != id(node):
                return True

        node = node.parent

    return False


def is_sequential_completeness_violated(
    node_to_expand_sibling: ConcurrencyTree, rml: ConcurrencyTree
) -> bool:
    node = rml

    if id(node_to_expand_sibling) == id(rml):
        return False

    while id(node.parent) != id(node_to_expand_sibling):
        if (
            node.parent.op == cTreeOperator.Sequential
            and get_right_sibling(node) is not None
        ):
            return True
        node = node.parent

    return False


def get_ef_activities_between(
    left_ro: ConcurrencyTree,
    left_rmo: ConcurrencyTree,
    right_ro: ConcurrencyTree,
    right_lmo: ConcurrencyTree,
) -> Set[ConcurrencyTree]:
    left_bound = 0
    if left_rmo is not None:
        left_bound = left_rmo.id
    possible_nodes = get_ef_labeled_nodes_left_of(right_ro, right_lmo, left_bound)
    if len(possible_nodes) == 0 or left_ro is None:
        return possible_nodes

    return possible_nodes.intersection(
        get_ef_labeled_nodes_right_of(left_ro, left_rmo, right_lmo.id)
    )


def get_ef_labeled_nodes_left_of(
    ro: ConcurrencyTree, lmo: ConcurrencyTree, stop_id: int = None
) -> Set[ConcurrencyTree]:
    child = lmo
    parent = lmo.parent
    possible_nodes = set()
    reached_root_occurrence = lmo == ro

    while parent is not None:
        if parent.op == cTreeOperator.Sequential:
            child_index = get_index(parent.children, child)
            if child_index > 0:
                if len(possible_nodes) == 0:
                    possible_nodes = possible_nodes.union(
                        get_left_ef_activities(get_left_sibling(child))
                    )
                else:
                    possible_nodes = possible_nodes.union(
                        get_labeled_nodes_in_concurrency_tree(get_left_sibling(child))
                    )
            if child_index > 1:
                stop = False
                for child in parent.children[: child_index - 1]:
                    if stop_id is not None and child.id <= stop_id:
                        stop = True
                        continue
                    possible_nodes = possible_nodes.union(
                        get_labeled_nodes_in_concurrency_tree(child)
                    )

                if stop:
                    return possible_nodes
        else:
            if not reached_root_occurrence:
                possible_nodes = set()

        child = parent
        parent = parent.parent

        if id(parent) == id(ro):
            reached_root_occurrence = True

    return possible_nodes


def get_ef_labeled_nodes_right_of(
    ro: ConcurrencyTree, rmo: ConcurrencyTree, stop_id: int = None
) -> Set[ConcurrencyTree]:
    child = rmo
    parent = rmo.parent
    possible_nodes = set()
    reached_root_occurrence = rmo == ro

    while parent is not None:
        if parent.op == cTreeOperator.Sequential:
            right_sibling = child.rSib
            if right_sibling is not None:
                if len(possible_nodes) == 0:
                    possible_nodes = possible_nodes.union(
                        get_right_ef_activities(right_sibling)
                    )
                else:
                    possible_nodes = possible_nodes.union(
                        get_labeled_nodes_in_concurrency_tree(right_sibling)
                    )
            if right_sibling is not None and right_sibling.rSib is not None:
                while right_sibling.rSib is not None:
                    if stop_id is not None and right_sibling.rSib.id >= stop_id:
                        return possible_nodes

                    possible_nodes = possible_nodes.union(
                        get_labeled_nodes_in_concurrency_tree(right_sibling.rSib)
                    )
                    right_sibling = right_sibling.rSib
        else:
            if not reached_root_occurrence:
                possible_nodes = set()

        child = parent
        parent = parent.parent

        if id(parent) == id(ro):
            reached_root_occurrence = True

    return possible_nodes


def get_left_ef_activities(tree: ConcurrencyTree):
    if tree.label is not None or tree.op == cTreeOperator.Fallthrough:
        return set()

    if tree.op == cTreeOperator.Concurrent:
        return get_left_ef_activities(tree.children[-1])

    result = set()

    for child in tree.children:
        if child.rSib is not None:
            result = result.union(get_labeled_nodes_in_concurrency_tree(child))
        else:
            result = result.union(get_left_ef_activities(child))

    return result


def get_right_ef_activities(tree: ConcurrencyTree):
    if tree.label is not None or tree.op == cTreeOperator.Fallthrough:
        return set()

    if tree.op == cTreeOperator.Concurrent:
        return get_right_ef_activities(tree.children[-1])

    result = set()

    for child in tree.children:
        if get_left_sibling(child) is not None:
            result = result.union(get_labeled_nodes_in_concurrency_tree(child))
        else:
            result = result.union(get_right_ef_activities(child))

    return result


def get_occurrences_for_ef_check(
    pattern: EventuallyFollowsPattern, insert_position: int, occurrences
):
    left_ro = None
    left_rmo = None

    if insert_position > 0:
        left_sub_pattern = pattern.sub_patterns[insert_position - 1]
        left_ro = occurrences[left_sub_pattern.id]
        left_rmo = occurrences[get_rightmost_leaf(left_sub_pattern).id]

    right_sub_pattern = pattern.sub_patterns[insert_position]
    right_ro = occurrences[right_sub_pattern.id]
    right_lmo = occurrences[get_leftmost_leaf(right_sub_pattern).id]

    return left_ro, left_rmo, right_ro, right_lmo


def get_child_sequential_indexes_to_ensure_left_completeness(
    node: SubPattern, include_self=False
) -> Set[int]:
    """
    Returns all node ids for which we have to check if they have a left sibling. If this is the case, then sequential
    completeness is violated (on the left side).
    :param node:
    :param include_self:
    :return:
    """
    result = set()
    if (
        include_self
        and node.operator == cTreeOperator.Sequential
        and len(node.children) > 0
    ):
        result.add(node.children[0].id)

    for child in node.children:
        result = result.union(
            get_child_sequential_indexes_to_ensure_left_completeness(child, True)
        )

    return result


def left_completeness_violated(occurrences, indexes_to_check: Set[int]) -> bool:
    for idx in indexes_to_check:
        if occurrences[idx].parent.id != occurrences[idx].id - 1:
            return True

    return False
