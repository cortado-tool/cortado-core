import copy
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional, Iterable

from cortado_core.eventually_follows_pattern_mining.algorithm_expansion import (
    generate_eventually_follows_patterns as generate_infix_patterns,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.infix_sub_patterns_pruning_strategy import (
    InfixSubPatternsPruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.pruning_strategy import (
    PruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_transaction_counting_strategy import (
    TraceTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_list_cleaner import (
    NoOccurrenceListCleaner,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_statistic_tracker import (
    OccurrenceStatisticTracker,
    NoOccurrenceStatisticTracker,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.rightmost_occurence_store import (
    RightmostOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.util.enumeration_graph import (
    build_enumeration_graph,
    EnumerationNode,
)
from cortado_core.eventually_follows_pattern_mining.util.pattern import flatten_patterns
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    is_eventually_follows_relation_with_ef_dict,
    get_left_check_node,
    get_right_check_node,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class GraphIterator:
    def __init__(self, infix_graph):
        self.infix_graph = infix_graph
        self.nodes = sorted(
            self.get_all_nodes(self.infix_graph),
            key=lambda n: sum([len(sp) for sp in n.pattern.sub_patterns]),
        )
        self.excluded_pattern_ids = set()
        self.i = 0

    def reinit(self):
        self.i = 0

    def set_excluded_pattern_ids(self, excluded_pattern_ids: Set[int]):
        self.excluded_pattern_ids = excluded_pattern_ids

    def __iter__(self):
        return self

    def __next__(self):
        if self.i == len(self.nodes):
            raise StopIteration

        c = self.nodes[self.i]
        self.i += 1

        while c.pattern.id in self.excluded_pattern_ids:
            if self.i == len(self.nodes):
                raise StopIteration
            c = self.nodes[self.i]
            self.i += 1

        return c

    def get_all_nodes(self, graph):
        nodes = set()
        if graph.pattern is not None:
            nodes.add(graph)

        for succ in graph.direct_successors:
            nodes = nodes.union(self.get_all_nodes(succ))

        return nodes


def generate_eventually_follows_patterns_using_combination_approach_enumeration_tree(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    counting_strategy: CountingStrategy,
    prune_sets,
    ef_dict,
    size_tracker: Optional[OccurrenceStatisticTracker] = None,
    max_size=1000,
):
    size_tracker = (
        size_tracker if size_tracker is not None else NoOccurrenceStatisticTracker()
    )

    occurrence_store = RightmostOccurrenceStore(
        trees, counting_strategy, min_support_count, ef_dict, size_tracker
    )
    patterns = generate_infix_patterns(
        min_support_count,
        occurrence_store,
        NoOccurrenceListCleaner(),
        prune_sets,
        generate_only_infix_patterns=True,
        max_iterations=max_size,
    )
    pruning_strategy = InfixSubPatternsPruningStrategy(patterns)

    generator = CombinedPatternGenerator(
        patterns,
        occurrence_store,
        min_support_count,
        pruning_strategy,
        ef_dict,
        counting_strategy,
        size_tracker,
        max_size,
    )

    generator.generate_combined_patterns()

    return generator.get_patterns()


class CombinedPatternGenerator:
    def __init__(
        self,
        patterns: Dict[int, Set],
        occurrence_store: RightmostOccurrenceStore,
        min_support_count: int,
        pruning_strategy: PruningStrategy,
        ef_dict,
        counting_strategy: CountingStrategy,
        size_tracker: OccurrenceStatisticTracker,
        max_size: int,
    ):
        self.size_tracker = size_tracker
        self.patterns = patterns
        self.counting_strategy = counting_strategy
        self.max_size = max_size

        self.flat_infix_patterns = flatten_patterns(patterns)

        self.infix_graph, self.infix_graph_node_for_pattern = build_enumeration_graph(
            patterns, self.flat_infix_patterns
        )
        if len(self.flat_infix_patterns) == 0:
            self.current_pattern_id = 1
        else:
            self.current_pattern_id = (
                max(self.flat_infix_patterns, key=lambda x: x.id).id + 1
            )
        self.pruning_strategy = pruning_strategy
        self.min_support_count = min_support_count
        self.ef_dict = ef_dict
        self.occurrence_lists = initialize_occurrence_list(
            self.flat_infix_patterns, occurrence_store
        )
        self.tested_patterns = 0
        self.is_transaction_based_counting = isinstance(
            self.counting_strategy, VariantTransactionCountingStrategy
        ) or isinstance(self.counting_strategy, TraceTransactionCountingStrategy)

    def get_patterns(self):
        return self.patterns

    def generate_combined_patterns(self):
        graph_iterator = GraphIterator(self.infix_graph)
        candidates = {
            node.pattern.id: (
                node.pattern,
                set(),
                set([s.pattern.id for s in node.all_successors]),
            )
            for node in graph_iterator
        }
        iteration = 1

        while len(candidates) != 0:
            next_iteration_candidates = dict()
            candidate_ids = sorted(list(candidates.keys()))
            iteration_patterns = []
            for candidate_id in candidate_ids:
                prefix_candidate, excluded_pattern_ids, successors = candidates[
                    candidate_id
                ]

                graph_iterator.reinit()
                new_excluded_pattern_ids = excluded_pattern_ids.copy()
                graph_iterator.set_excluded_pattern_ids(new_excluded_pattern_ids)
                new_patterns, new_excluded_pattern_ids = self.combine_to_ef_patterns(
                    prefix_candidate, graph_iterator, new_excluded_pattern_ids
                )
                iteration_patterns += new_patterns
                for succ in successors:
                    p, excl, s = candidates[succ]
                    candidates[succ] = p, excl.union(new_excluded_pattern_ids), s

                for new_pattern, succ in new_patterns:
                    next_iteration_candidates[new_pattern.id] = (
                        new_pattern,
                        new_excluded_pattern_ids,
                        succ,
                    )

            self.size_tracker.track_after_iteration(self.occurrence_lists)

            if iteration > 1:
                for candidate in candidates:
                    del self.occurrence_lists[candidate]

            candidates = next_iteration_candidates
            iteration += 1
        # print('Combination Graph Tested Patterns:', self.tested_patterns)

    def combine_to_ef_patterns(
        self,
        prefix_candidate: EventuallyFollowsPattern,
        graph_iterator: GraphIterator,
        excluded_pattern_ids,
    ):
        successors_for_pattern = defaultdict(set)
        prefix_occurrence_list = self.occurrence_lists[prefix_candidate.id]
        frequent_nodes_with_pattern: List[
            Tuple[EnumerationNode, EventuallyFollowsPattern]
        ] = []

        for node in graph_iterator:
            postfix_candidate = node.pattern

            self.current_pattern_id, new_pattern, new_pattern_n_nodes = build_pattern(
                self.current_pattern_id, postfix_candidate, prefix_candidate
            )

            if new_pattern_n_nodes > self.max_size or self.pruning_strategy.can_prune(
                new_pattern, new_pattern_n_nodes
            ):
                excluded_pattern_ids.add(node.pattern.id)
                excluded_pattern_ids = excluded_pattern_ids.union(
                    set([s.pattern.id for s in node.all_successors])
                )
                graph_iterator.set_excluded_pattern_ids(excluded_pattern_ids)
                continue

            self.tested_patterns += 1

            postfix_occurrence_list = self.occurrence_lists[postfix_candidate.id]
            support_to_gain = prefix_candidate.support

            update_occurrences_with_ef_check(
                new_pattern,
                postfix_occurrence_list,
                prefix_occurrence_list,
                support_to_gain,
                self.occurrence_lists,
                self.is_transaction_based_counting,
                self.min_support_count,
                self.ef_dict,
                self.counting_strategy,
            )

            if new_pattern.support >= self.min_support_count:
                # print('Frequent', new_pattern)
                for n, p in frequent_nodes_with_pattern:
                    if node in n.all_successors:
                        successors_for_pattern[p.id].add(new_pattern.id)

                frequent_nodes_with_pattern.append((node, new_pattern))
                if new_pattern_n_nodes in self.patterns:
                    self.patterns[new_pattern_n_nodes].add(new_pattern)
                else:
                    self.patterns[new_pattern_n_nodes] = {new_pattern}
            else:
                # print('Infrequent', new_pattern)
                excluded_pattern_ids.add(node.pattern.id)
                excluded_pattern_ids = excluded_pattern_ids.union(
                    set([s.pattern.id for s in node.all_successors])
                )
                graph_iterator.set_excluded_pattern_ids(excluded_pattern_ids)

        return [
            (pattern, successors_for_pattern[pattern.id])
            for _, pattern in frequent_nodes_with_pattern
        ], excluded_pattern_ids


def update_occurrences_with_ef_check(
    new_pattern,
    postfix_occurrence_list,
    prefix_occurrence_list,
    support_to_gain,
    occurrence_lists,
    is_transaction_counting,
    min_sup_count,
    ef_dict,
    counting_strategy,
):
    for tree_id in prefix_occurrence_list:
        new_occurrence_list = []
        if tree_id not in postfix_occurrence_list:
            support_to_gain, early_stopping = update_support(
                tree_id,
                new_pattern,
                new_occurrence_list,
                prefix_occurrence_list[tree_id],
                support_to_gain,
                occurrence_lists,
                min_sup_count,
                counting_strategy,
            )
            if early_stopping:
                break
            continue

        # It would not be correct to break the outer loop, see the following example:
        # we have a tree ->(a[0], x, +(a[1], ->(a[2],b,c))). First, we search for the pattern a...a.
        # If we would break after finding the first occurrence (a[0]...a[1]), in the remainder,
        # we could not find the pattern a...a...c (which is present using the occurrence a[0]...a[2]...c).
        for postfix_occurrence in postfix_occurrence_list[tree_id]:
            (
                postfix_roots,
                postfix_left_check_node,
                postfix_right_check_node,
            ) = postfix_occurrence
            for prefix_occurrence in prefix_occurrence_list[tree_id]:
                (
                    prefix_roots,
                    prefix_left_check_node,
                    prefix_right_check_node,
                ) = prefix_occurrence
                if is_eventually_follows_relation_with_ef_dict(
                    prefix_left_check_node, postfix_right_check_node, ef_dict[tree_id]
                ):
                    new_ro = copy.copy(prefix_roots)
                    new_ro.append(postfix_roots[0])
                    new_occurrence_list.append(
                        (new_ro, postfix_left_check_node, prefix_right_check_node)
                    )

                    if is_transaction_counting:
                        break

        support_to_gain, early_stopping = update_support(
            tree_id,
            new_pattern,
            new_occurrence_list,
            prefix_occurrence_list[tree_id],
            support_to_gain,
            occurrence_lists,
            min_sup_count,
            counting_strategy,
        )
        if early_stopping:
            break

        update_occurrence_list_for_pattern_and_tree(
            tree_id, new_occurrence_list, new_pattern, occurrence_lists
        )


def update_support(
    tree_id,
    pattern,
    new_occurrence_list,
    predecessor_occurrence_list,
    support_to_gain,
    occurrence_lists,
    min_sup_count,
    counting_strategy,
) -> Tuple[int, bool]:
    update_support_count(tree_id, new_occurrence_list, pattern, counting_strategy)
    support_to_gain = update_support_to_gain(
        tree_id, support_to_gain, predecessor_occurrence_list, counting_strategy
    )

    if pattern.support + support_to_gain < min_sup_count:
        if pattern.id in occurrence_lists:
            del occurrence_lists[pattern.id]

        pattern.support = -1
        return support_to_gain, True

    return support_to_gain, False


def update_support_count(
    tree_idx,
    new_occurrence_list,
    pattern: EventuallyFollowsPattern,
    counting_strategy: CountingStrategy,
):
    pattern.support += (
        counting_strategy.get_support_for_single_tree_combination_occ_list(
            new_occurrence_list, tree_idx
        )
    )


def update_support_to_gain(
    tree_id: int,
    support_to_gain: int,
    predecessor_occurrence_list,
    counting_strategy: CountingStrategy,
) -> int:
    return (
        support_to_gain
        - counting_strategy.get_support_for_single_tree_combination_occ_list(
            predecessor_occurrence_list, tree_id
        )
    )


def update_occurrence_list_for_pattern_and_tree(
    tree_idx, new_occurrence_list, pattern, occurrence_lists
):
    if len(new_occurrence_list) > 0:
        if pattern.id not in occurrence_lists:
            occurrence_lists[pattern.id] = dict()

        # TODO niklas: check if needed
        new_occurrence_list.sort(key=lambda o: o[-1].id)
        occurrence_lists[pattern.id][tree_idx] = new_occurrence_list


def initialize_occurrence_list(
    flat_infix_patterns: Iterable[EventuallyFollowsPattern],
    occurrence_store: RightmostOccurrenceStore,
):
    occurrence_list = dict()
    for pattern in flat_infix_patterns:
        pattern_occurrence_list = dict()
        for tree_id in occurrence_store.occurrence_lists[pattern.id]:
            tree_occurrence_list = []
            for occurrence in occurrence_store.occurrence_lists[pattern.id][tree_id]:
                _, _, ros = occurrence
                tree_occurrence_list.append(
                    (
                        ros,
                        get_left_check_node(occurrence),
                        get_right_check_node(occurrence),
                    )
                )
            pattern_occurrence_list[tree_id] = tree_occurrence_list
        occurrence_list[pattern.id] = pattern_occurrence_list

    return occurrence_list


def build_pattern(current_pattern_id, postfix_candidate, prefix_candidate):
    new_pattern = EventuallyFollowsPattern(
        sub_patterns=prefix_candidate.sub_patterns
        + [postfix_candidate.sub_patterns[0]],
        rightmost_leaf=postfix_candidate.rightmost_leaf,
    )
    new_pattern.id = current_pattern_id
    current_pattern_id += 1
    new_pattern_n_nodes = sum([len(sp) for sp in new_pattern.sub_patterns])
    return current_pattern_id, new_pattern, new_pattern_n_nodes
