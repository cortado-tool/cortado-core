from collections import defaultdict
from typing import List, Optional

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree, cTreeOperator
from cortado_core.tiebreaker.pattern import TiebreakerPattern, WILDCARD_MATCH


def is_matching(tree: ConcurrencyTree, source_pattern: TiebreakerPattern):
    if tree.op is None or (tree.op != cTreeOperator.Concurrent and tree.op != cTreeOperator.Fallthrough):
        return False, None

    wildcard_child = None
    tree_children = [child for child in tree.children if child.op != cTreeOperator.Fallthrough]
    tree_children += get_children_below_fallthrough(tree.children)

    match_mapping = dict()

    for source_child in source_pattern.children:
        if source_child.operator is not None:
            wildcard_child = source_child
            continue
        matches = []
        if not source_child.match_multiple:
            match = get_first_match(source_child.labels[0], tree_children)
            if match is None:
                return False, None
            matches = [match]
        else:
            for label in source_child.labels:
                matches += get_all_matches(label, tree_children)

            if len(matches) == 0:
                return False, None

        tree_children = [t for t in tree_children if t not in matches]
        match_mapping[source_child.id] = matches

    if wildcard_child is not None:
        match_mapping[wildcard_child.id] = tree_children
        return True, match_mapping

    return len(tree_children) == 0, match_mapping


def get_target_to_source_mapping(source_pattern: TiebreakerPattern, target_pattern: TiebreakerPattern):
    source_nodes = get_non_operator_nodes(source_pattern)
    target_nodes = get_non_operator_nodes(target_pattern)
    target_nodes_dict = defaultdict(list)
    target_wildcard_node = None
    mapping = dict()

    for target_node in target_nodes:
        if target_node.operator == WILDCARD_MATCH:
            target_wildcard_node = target_node

        target_nodes_dict[tuple(target_node.labels)].append(target_node)

    for source_node in source_nodes:
        if source_node.operator == WILDCARD_MATCH:
            mapping[target_wildcard_node.id] = source_node.id
            continue

        matching_target_node = target_nodes_dict[tuple(source_node.labels)][0]
        target_nodes_dict[tuple(source_node.labels)] = target_nodes_dict[tuple(source_node.labels)][1:]
        mapping[matching_target_node.id] = source_node.id

    return mapping


def get_non_operator_nodes(pattern: TiebreakerPattern):
    nodes = []
    if len(pattern.labels) > 0:
        nodes.append(pattern)

    if pattern.operator == WILDCARD_MATCH:
        nodes.append(pattern)

    for child in pattern.children:
        nodes += get_non_operator_nodes(child)

    return nodes


def get_first_match(label: str, leaves: List[ConcurrencyTree]) -> Optional[ConcurrencyTree]:
    for leaf in leaves:
        if leaf.label == label:
            return leaf

    return None


def get_all_matches(label: str, leaves: List[ConcurrencyTree]) -> List[ConcurrencyTree]:
    matches = []
    for leaf in leaves:
        if leaf.label == label:
            matches.append(leaf)

    return matches


def get_children_below_fallthrough(trees: List[ConcurrencyTree]):
    children = []

    for tree in trees:
        if tree.op == cTreeOperator.Fallthrough:
            children += tree.children

    return children
