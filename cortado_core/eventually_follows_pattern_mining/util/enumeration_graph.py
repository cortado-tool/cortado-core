from typing import Iterable, Optional, Dict, List

from cortado_core.eventually_follows_pattern_mining.blanket_mining.algorithm import (
    get_activities_for_patterns,
    get_ef_preserving_tree_for_patterns,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.occurrence_store.full_occurrence_store import (
    FullOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.util.is_superpattern import (
    is_superpattern,
)


class EnumerationNode:
    def __init__(
        self,
        pattern: Optional[EventuallyFollowsPattern],
        direct_successors=None,
        all_successors=None,
    ):
        if direct_successors is None:
            self.direct_successors = set()

        if all_successors is None:
            self.all_successors = set()

        self.pattern = pattern


def build_enumeration_graph(
    patterns: Dict[int, Iterable[EventuallyFollowsPattern]], flat_patterns
):
    activities_for_pattern = get_activities_for_patterns(flat_patterns)
    graph_root = EnumerationNode(pattern=None)
    graph_node_for_pattern = dict()
    ef_preserving_trees_for_patterns = get_ef_preserving_tree_for_patterns(
        flat_patterns
    )

    for k, k_patterns in patterns.items():
        for pattern in k_patterns:
            node = EnumerationNode(pattern=pattern)
            graph_node_for_pattern[pattern.id] = node

            if k == 1:
                graph_root.direct_successors.add(node)
                graph_root.all_successors.add(node)
            else:
                direct_predecessors, all_predecessors = __get_predecessors(
                    patterns,
                    pattern,
                    k,
                    activities_for_pattern,
                    ef_preserving_trees_for_patterns,
                )
                for predecessor_id in direct_predecessors:
                    graph_node_for_pattern[predecessor_id].direct_successors.add(node)

                for predecessor_id in all_predecessors:
                    graph_node_for_pattern[predecessor_id].all_successors.add(node)

    return graph_root, graph_node_for_pattern


def build_enumeration_graph_for_combined_patterns(
    patterns: List[EventuallyFollowsPattern],
    infix_patterns: Iterable[EventuallyFollowsPattern],
    graph_node_for_pattern,
):
    if len(patterns) == 0:
        return EnumerationNode(None), dict()

    infix_pattern_by_id = dict()
    for infix_pattern in infix_patterns:
        infix_pattern_by_id[infix_pattern.sub_patterns[0]] = infix_pattern.id

    pattern_length = len(patterns[0])
    covered_patterns = set()
    root_node = EnumerationNode(pattern=None)

    new_node_for_pattern = dict()
    for pattern in patterns:
        new_node_for_pattern[pattern.id] = EnumerationNode(pattern=pattern)

    for predecessor in patterns:
        for successor in patterns:
            is_successor = True
            if predecessor.id == successor.id:
                continue

            for i in range(pattern_length):
                if successor.sub_patterns[i] == predecessor.sub_patterns[i]:
                    continue

                if (
                    not graph_node_for_pattern[
                        infix_pattern_by_id[successor.sub_patterns[i]]
                    ]
                    in graph_node_for_pattern[
                        infix_pattern_by_id[predecessor.sub_patterns[i]]
                    ].all_successors
                ):
                    is_successor = False
                    break

            if is_successor:
                covered_patterns.add(successor.id)
                new_node_for_pattern[predecessor.id].all_successors.add(
                    new_node_for_pattern[successor.id]
                )

    for pattern in patterns:
        if pattern.id not in covered_patterns:
            root_node.all_successors.add(new_node_for_pattern[pattern.id])

    return root_node, new_node_for_pattern


def __get_predecessors(
    infix_patterns, pattern, k, activities_for_pattern, ef_preserving_trees_for_pattern
):
    pattern_activities = activities_for_pattern[pattern.id]
    direct_predecessors = set()
    all_predecessors = set()
    search_direct = True
    pattern_ef_preserving_tree, ef_dict = ef_preserving_trees_for_pattern[pattern.id]

    for it_k in range(k - 1, 0, -1):
        sub_pattern_candidates = infix_patterns[it_k]
        for sub_pattern_candidate in sub_pattern_candidates:
            if not activities_for_pattern[sub_pattern_candidate.id].issubset(
                pattern_activities
            ):
                continue

            if is_superpattern(
                pattern_ef_preserving_tree, sub_pattern_candidate, ef_dict
            ):
                if search_direct:
                    direct_predecessors.add(sub_pattern_candidate.id)
                    all_predecessors.add(sub_pattern_candidate.id)
                all_predecessors.add(sub_pattern_candidate.id)

        if len(direct_predecessors) != 0:
            search_direct = False

    return direct_predecessors, all_predecessors
