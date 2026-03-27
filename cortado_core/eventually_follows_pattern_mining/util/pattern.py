from typing import Set, Dict, Iterable, List, Tuple, Any

from cortado_core.eventually_follows_pattern_mining.util.is_superpattern import (
    get_ef_preserving_concurrency_tree,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    get_first_ef_node_id_per_node_for_trees,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree

from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)


def get_activities_for_pattern(pattern: EventuallyFollowsPattern) -> Set[str]:
    result = set()

    for sub_pattern in pattern.sub_patterns:
        result = result.union(get_activities_for_sub_pattern(sub_pattern))

    return result


def get_activities_for_sub_pattern(sub_pattern: SubPattern) -> Set[str]:
    if sub_pattern.label is not None:
        return {sub_pattern.label}

    result = set()
    for child in sub_pattern.children:
        result = result.union(get_activities_for_sub_pattern(child))

    return result


def flatten_patterns(
    patterns: Dict[int, Iterable[EventuallyFollowsPattern]],
) -> List[EventuallyFollowsPattern]:
    flat_patterns = []

    for _, pts in patterns.items():
        for pattern in pts:
            flat_patterns.append(pattern)

    return flat_patterns


def get_activities_for_patterns(
    patterns: Iterable[EventuallyFollowsPattern],
) -> Dict[int, Set[str]]:
    result = dict()

    for pattern in patterns:
        result[pattern.id] = get_activities_for_pattern(pattern)

    return result


def get_ef_preserving_tree_for_patterns(
    patterns: Iterable[EventuallyFollowsPattern],
) -> Dict[int, Tuple[ConcurrencyTree, Any]]:
    result = dict()

    for pattern in patterns:
        ef_preserving_tree = get_ef_preserving_concurrency_tree(pattern)
        result[pattern.id] = (
            ef_preserving_tree,
            get_first_ef_node_id_per_node_for_trees([ef_preserving_tree]),
        )

    return result
