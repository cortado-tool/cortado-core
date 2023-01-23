from typing import Dict, Optional

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator
from cortado_core.tiebreaker.pattern import TiebreakerPattern, WILDCARD_MATCH


def can_apply_without_violating_two_plus_two_freeness(target_pattern: TiebreakerPattern, match: Dict,
                                                      target_to_source_mapping: Dict[int, int]) -> bool:
    """
    Assumes that the target pattern contains a possibly violating construct
    Parameters
    ----------
    target_pattern
    match

    Returns
    -------

    """
    wildcard_node = get_wildcard_node(target_pattern)
    match_nodes = match[target_to_source_mapping[wildcard_node.id]]

    for match_node in match_nodes:
        if contains_sequence_group(match_node):
            return False

    return True


def contains_sequence_group(node):
    if node.op == cTreeOperator.Sequential:
        return True

    for child in node.children:
        if contains_sequence_group(child):
            return True

    return False


def contains_possibly_violating_construct(target_pattern: TiebreakerPattern):
    wildcard_node = get_wildcard_node(target_pattern)
    if wildcard_node is None:
        return False

    return node_is_parallel_to_sequence(wildcard_node)


def node_is_parallel_to_sequence(node: TiebreakerPattern):
    parent = node.parent
    if parent is None:
        return False

    if parent.operator == cTreeOperator.Concurrent:
        for sibling in parent.children:
            if sibling == node:
                continue

            if sibling.operator == cTreeOperator.Sequential:
                return True

    return node_is_parallel_to_sequence(parent)


def get_wildcard_node(pattern: TiebreakerPattern) -> Optional[TiebreakerPattern]:
    if pattern.operator == WILDCARD_MATCH:
        return pattern

    for child in pattern.children:
        match = get_wildcard_node(child)
        if match is not None:
            return match

    return None
