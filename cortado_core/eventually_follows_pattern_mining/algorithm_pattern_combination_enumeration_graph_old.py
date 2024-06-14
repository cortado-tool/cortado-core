import copy
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional

import networkx as nx
from matplotlib import pyplot as plt

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
from cortado_core.eventually_follows_pattern_mining.util.pattern import (
    get_activities_for_pattern,
    flatten_patterns,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    is_eventually_follows_relation_with_ef_dict,
    get_left_check_node,
    get_right_check_node,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


def generate_eventually_follows_patterns_using_combination_approach_enumeration_tree(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    counting_strategy: CountingStrategy,
    prune_sets,
    ef_dict,
    size_tracker: Optional[OccurrenceStatisticTracker] = None,
):
    size_tracker = (
        size_tracker if size_tracker is not None else NoOccurrenceStatisticTracker()
    )

    occurrence_store = RightmostOccurrenceStore(
        trees, counting_strategy, min_support_count, ef_dict
    )
    patterns = generate_infix_patterns(
        min_support_count,
        occurrence_store,
        NoOccurrenceListCleaner(),
        prune_sets,
        generate_only_infix_patterns=True,
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
    )

    plot_graph(generator.infix_graph)

    generator.generate_combined_patterns()

    print("Tested patterns", generator.tested_patterns)

    return generator.get_patterns()


def plot_graph(root: EnumerationNode):
    return
    graph = build_nx_graph(root, x_pos=defaultdict(int))
    plt.figure(figsize=(50, 50))
    pos = nx.get_node_attributes(graph, "pos")
    nx.draw(graph, pos, with_labels=True)
    plt.savefig("Graph.png", format="PNG")


def build_nx_graph(
    node: EnumerationNode,
    graph=None,
    already_added_nodes=None,
    x_pos=None,
    relabeling_dict=None,
    current_label=None,
):
    if graph is None:
        graph = nx.DiGraph()
        already_added_nodes = set()
        relabeling_dict = dict()
        current_label = "a"
        node_label, current_label = get_pattern_string(
            node.pattern, relabeling_dict, current_label
        )
        graph.add_node(node_label, pos=(6, 0))

    node_label, current_label = get_pattern_string(
        node.pattern, relabeling_dict, current_label
    )

    for s in node.all_successors:
        if s not in already_added_nodes:
            l = sum([len(sp) for sp in s.pattern.sub_patterns])
            s_label, current_label = get_pattern_string(
                s.pattern, relabeling_dict, current_label
            )
            graph.add_node(s_label, pos=(x_pos[l], l))
            x_pos[l] += 1
        s_label, current_label = get_pattern_string(
            s.pattern, relabeling_dict, current_label
        )
        graph.add_edge(node_label, s_label)

    for s in node.all_successors:
        if s not in already_added_nodes:
            build_nx_graph(
                s, graph, already_added_nodes, x_pos, relabeling_dict, current_label
            )
            already_added_nodes.add(s)

    return graph


def get_pattern_string(
    pattern: EventuallyFollowsPattern, relabeling_dict, current_label
):
    if pattern is None:
        return "None", current_label

    labels = get_activities_for_pattern(pattern)
    for label in labels:
        if label not in relabeling_dict:
            relabeling_dict[label] = current_label
            current_label = chr(ord(current_label) + 1)

    return (
        "...".join(
            [get_sub_pattern_string(sp, relabeling_dict) for sp in pattern.sub_patterns]
        ),
        current_label,
    )


def get_sub_pattern_string(sub_pattern: SubPattern, relabeling_dict):
    if sub_pattern.label:
        return relabeling_dict[sub_pattern.label]

    return (
        sub_pattern.operator.value
        + "("
        + ",".join(
            [get_sub_pattern_string(c, relabeling_dict) for c in sub_pattern.children]
        )
        + ")"
    )


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
    ):
        self.size_tracker = size_tracker
        self.patterns = patterns
        self.counting_strategy = counting_strategy

        self.flat_infix_patterns = flatten_patterns(patterns)

        self.infix_graph, self.infix_graph_node_for_pattern = build_enumeration_graph(
            patterns, self.flat_infix_patterns
        )
        self.current_pattern_id = (
            max(self.flat_infix_patterns, key=lambda x: x.id).id + 1
        )
        self.pruning_strategy = pruning_strategy
        self.min_support_count = min_support_count
        self.ef_dict = ef_dict
        self.occurrence_lists = self.__initialize_occurrence_list(occurrence_store)
        self.tested_patterns = 0
        self.is_transaction_based_counting = isinstance(
            self.counting_strategy, VariantTransactionCountingStrategy
        ) or isinstance(self.counting_strategy, TraceTransactionCountingStrategy)

    def __initialize_occurrence_list(self, occurrence_store: RightmostOccurrenceStore):
        occurrence_list = dict()
        for pattern in self.flat_infix_patterns:
            pattern_occurrence_list = dict()
            for tree_id in occurrence_store.occurrence_lists[pattern.id]:
                tree_occurrence_list = []
                for occurrence in occurrence_store.occurrence_lists[pattern.id][
                    tree_id
                ]:
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

    def get_patterns(self):
        return self.patterns

    def generate_combined_patterns(self):
        candidates = {pattern.id: set() for pattern in self.flat_infix_patterns}
        iteration = 1
        pattern_by_id = dict()

        while len(candidates) != 0:
            next_iteration_candidates = dict()
            candidate_ids = sorted(list(candidates.keys()))
            iteration_patterns = []
            new_pattern_by_id = dict()
            for candidate_id in candidate_ids:
                excluded_pattern_ids = candidates[candidate_id]
                if iteration == 1:
                    prefix_candidate_node = self.infix_graph_node_for_pattern[
                        candidate_id
                    ]
                    prefix_candidate = prefix_candidate_node.pattern
                else:
                    prefix_candidate = pattern_by_id[candidate_id]
                    prefix_candidate_node = None
                new_excluded_pattern_ids = copy.copy(excluded_pattern_ids)
                new_patterns, new_excluded_pattern_ids = self.combine_to_ef_patterns(
                    prefix_candidate, {self.infix_graph}, new_excluded_pattern_ids
                )
                iteration_patterns += new_patterns
                if iteration == 1:
                    for prefix_successor in prefix_candidate_node.all_successors:
                        candidates[prefix_successor.pattern.id] = candidates[
                            prefix_successor.pattern.id
                        ].union(new_excluded_pattern_ids)

                for new_pattern in new_patterns:
                    next_iteration_candidates[new_pattern.id] = new_excluded_pattern_ids
                    new_pattern_by_id[new_pattern.id] = new_pattern

            self.size_tracker.track_after_iteration(self.occurrence_lists)

            if iteration > 1:
                for candidate in candidates:
                    del self.occurrence_lists[candidate]

            candidates = next_iteration_candidates
            pattern_by_id = new_pattern_by_id
            iteration += 1

    def combine_to_ef_patterns(
        self,
        prefix_candidate: EventuallyFollowsPattern,
        nodes: Set[EnumerationNode],
        excluded_pattern_ids,
    ) -> Tuple[List[EventuallyFollowsPattern], Set[int]]:
        prefix_occurrence_list = self.occurrence_lists[prefix_candidate.id]
        iteration_patterns = []
        successors = set()

        for node in nodes:
            if node.pattern is None:
                successors = set(
                    [
                        s
                        for s in node.direct_successors
                        if s.pattern.id not in excluded_pattern_ids
                    ]
                )
                return self.combine_to_ef_patterns(
                    prefix_candidate, successors, excluded_pattern_ids
                )

            postfix_candidate = node.pattern

            (
                self.current_pattern_id,
                new_pattern,
                new_pattern_n_nodes,
            ) = self.__build_pattern(
                self.current_pattern_id, postfix_candidate, prefix_candidate
            )

            if self.pruning_strategy.can_prune(new_pattern, new_pattern_n_nodes):
                excluded_pattern_ids.add(node.pattern.id)
                excluded_pattern_ids = excluded_pattern_ids.union(
                    set([s.pattern.id for s in node.direct_successors])
                )
                continue

            self.tested_patterns += 1

            postfix_occurrence_list = self.occurrence_lists[postfix_candidate.id]
            support_to_gain = prefix_candidate.support

            self.__update_occurrences_with_ef_check(
                new_pattern,
                postfix_occurrence_list,
                prefix_occurrence_list,
                support_to_gain,
            )

            if new_pattern.support >= self.min_support_count:
                # print('Frequent', new_pattern)
                iteration_patterns.append(new_pattern)
                if new_pattern_n_nodes in self.patterns:
                    self.patterns[new_pattern_n_nodes].add(new_pattern)
                else:
                    self.patterns[new_pattern_n_nodes] = {new_pattern}

                for child in node.direct_successors:
                    if child.pattern.id not in excluded_pattern_ids:
                        successors.add(child)
            else:
                # print('Infrequent', new_pattern)
                excluded_pattern_ids.add(node.pattern.id)
                excluded_pattern_ids = excluded_pattern_ids.union(
                    set([s.pattern.id for s in node.direct_successors])
                )

        successors = set(
            [s for s in successors if s.pattern.id not in excluded_pattern_ids]
        )
        if len(successors) == 0:
            return iteration_patterns, excluded_pattern_ids

        recursion_patterns, excluded_pattern_ids = self.combine_to_ef_patterns(
            prefix_candidate, successors, excluded_pattern_ids
        )

        return iteration_patterns + recursion_patterns, excluded_pattern_ids

    def __update_occurrences_with_ef_check(
        self,
        new_pattern,
        postfix_occurrence_list,
        prefix_occurrence_list,
        support_to_gain,
    ):
        for tree_id in prefix_occurrence_list:
            new_occurrence_list = []
            if tree_id not in postfix_occurrence_list:
                support_to_gain, early_stopping = self.update_support(
                    tree_id,
                    new_pattern,
                    new_occurrence_list,
                    prefix_occurrence_list[tree_id],
                    support_to_gain,
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
                        prefix_left_check_node,
                        postfix_right_check_node,
                        self.ef_dict[tree_id],
                    ):
                        new_ro = copy.copy(prefix_roots)
                        new_ro.append(postfix_roots[0])
                        new_occurrence_list.append(
                            (new_ro, postfix_left_check_node, prefix_right_check_node)
                        )

                        if self.is_transaction_based_counting:
                            break

            support_to_gain, early_stopping = self.update_support(
                tree_id,
                new_pattern,
                new_occurrence_list,
                prefix_occurrence_list[tree_id],
                support_to_gain,
            )
            if early_stopping:
                break

            self.update_occurrence_list_for_pattern_and_tree(
                tree_id, new_occurrence_list, new_pattern
            )

    def __build_pattern(self, current_pattern_id, postfix_candidate, prefix_candidate):
        new_pattern = EventuallyFollowsPattern(
            sub_patterns=prefix_candidate.sub_patterns
            + [postfix_candidate.sub_patterns[0]],
            rightmost_leaf=postfix_candidate.rightmost_leaf,
        )
        new_pattern.id = current_pattern_id
        current_pattern_id += 1
        new_pattern_n_nodes = sum([len(sp) for sp in new_pattern.sub_patterns])
        return current_pattern_id, new_pattern, new_pattern_n_nodes

    def update_support(
        self,
        tree_id,
        pattern,
        new_occurrence_list,
        predecessor_occurrence_list,
        support_to_gain,
    ) -> Tuple[int, bool]:
        self.update_support_count(tree_id, new_occurrence_list, pattern)
        support_to_gain = self.update_support_to_gain(
            tree_id, support_to_gain, predecessor_occurrence_list
        )

        if pattern.support + support_to_gain < self.min_support_count:
            if pattern.id in self.occurrence_lists:
                del self.occurrence_lists[pattern.id]

            pattern.support = -1
            return support_to_gain, True

        return support_to_gain, False

    def update_support_count(
        self, tree_idx, new_occurrence_list, pattern: EventuallyFollowsPattern
    ):
        pattern.support += (
            self.counting_strategy.get_support_for_single_tree_combination_occ_list(
                new_occurrence_list, tree_idx
            )
        )

    def update_support_to_gain(
        self, tree_id: int, support_to_gain: int, predecessor_occurrence_list
    ) -> int:
        return (
            support_to_gain
            - self.counting_strategy.get_support_for_single_tree_combination_occ_list(
                predecessor_occurrence_list, tree_id
            )
        )

    def update_occurrence_list_for_pattern_and_tree(
        self, tree_idx, new_occurrence_list, pattern
    ):
        if len(new_occurrence_list) > 0:
            if pattern.id not in self.occurrence_lists:
                self.occurrence_lists[pattern.id] = dict()

            # TODO niklas: check if needed
            new_occurrence_list.sort(key=lambda o: o[-1].id)
            self.occurrence_lists[pattern.id][tree_idx] = new_occurrence_list
