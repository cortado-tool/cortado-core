from typing import Optional, List

from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator,
    ConcurrencyTree,
)


def get_leaf_nodes_with_label(
    label: str, tree: ConcurrencyTree
) -> List[ConcurrencyTree]:
    if tree.label == label:
        # labeled nodes have no children
        return [tree]

    leaf_nodes = []
    if len(tree.children) > 0:
        for child in tree.children:
            leaf_nodes += get_leaf_nodes_with_label(label, child)

    return leaf_nodes


def get_nodes_with_operator(
    operator: cTreeOperator, tree: ConcurrencyTree
) -> List[ConcurrencyTree]:
    operator_nodes = []

    if tree.op == operator:
        operator_nodes.append(tree)

    if len(tree.children) > 0:
        for child in tree.children:
            operator_nodes += get_nodes_with_operator(operator, child)

    return operator_nodes


def should_check_only_first_search_node(pattern: EventuallyFollowsPattern) -> bool:
    return should_enforce_left_completeness(pattern)


def should_enforce_left_completeness(pattern: EventuallyFollowsPattern) -> bool:
    node = pattern.rightmost_leaf

    if node.parent is not None and node.parent.operator != cTreeOperator.Sequential:
        return False

    while node.parent is not None:
        if node.parent.operator == cTreeOperator.Sequential:
            if node.parent.id != node.id - 1:
                return True

        node = node.parent

    return False


def get_first_search_node(
    height_diff: int, predecessor_rmo: ConcurrencyTree
) -> Optional[ConcurrencyTree]:
    if height_diff == -1:
        return predecessor_rmo.children[0]

    search_node = predecessor_rmo

    while height_diff > 0:
        height_diff -= 1
        child = search_node
        search_node = search_node.parent

        # ensure right completeness
        if search_node.op == cTreeOperator.Sequential and id(child) != id(
            search_node.children[-1]
        ):
            return None

    return search_node.rSib


def get_rightmost_occurrences_from_search_node(
    pattern: EventuallyFollowsPattern,
    search_node: ConcurrencyTree,
    check_only_first_search_node: bool,
) -> List[ConcurrencyTree]:
    occurrences = []

    while search_node is not None:
        # TODO niklas: break on first concurrent or fallthrough label match? See michaels code
        if rightmost_leaf_label_or_operator_matches(
            pattern.rightmost_leaf, search_node
        ):
            occurrences.append(search_node)

        search_node = search_node.rSib

        if check_only_first_search_node:
            break

    return occurrences


def rightmost_leaf_label_or_operator_matches(
    rml: SubPattern, node: ConcurrencyTree
) -> bool:
    if rml.operator is not None:
        return rml.operator == node.op

    return rml.label == node.label


def updated_sub_pattern_to_single_child_with_sequential_root(
    pattern: EventuallyFollowsPattern,
) -> bool:
    if len(pattern) == 1:
        return False

    last_sub_pattern = pattern.sub_patterns[-1]

    if last_sub_pattern.operator != cTreeOperator.Sequential:
        return False

    return (
        len(last_sub_pattern.children) == 1
        and len(last_sub_pattern.children[0].children) == 0
    )
