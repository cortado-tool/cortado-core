import copy
from typing import List, Dict, Set, Tuple

from cortado_core.eventually_follows_pattern_mining.algorithm_pattern_combination_enumeration_graph import (
    EnumerationNode,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.algorithm import (
    postprocess_maximal_patterns,
    postprocess_closed_patterns,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.algorithm_baseline import (
    flatten_patterns,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.algorithm_infix_patterns_without_occurrence_match import (
    generate_infix_patterns_without_occurrence_match,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.occurrence_blanket import (
    left_occurrence_blanket_contains_elements,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.full_occurrence_store import (
    FullOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.util.enumeration_graph import (
    build_enumeration_graph,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    set_preorder_ids,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    is_eventually_follows_relation_with_ef_dict,
    get_left_check_node_for_full_occurrence,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)


def generate_maximal_closed_eventually_follows_patterns_using_combination_approach(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    counting_strategy: CountingStrategy,
    prune_sets,
    ef_dict,
):
    occurrence_store = FullOccurrenceStore(
        trees, counting_strategy, min_support_count, ef_dict
    )
    patterns = generate_infix_patterns_without_occurrence_match(
        trees, min_support_count, occurrence_store, counting_strategy, prune_sets
    )

    generator = CombinedPatternGenerator(
        patterns, occurrence_store, min_support_count, ef_dict, counting_strategy
    )

    generator.generate_combined_patterns()

    candidates = set(flatten_patterns(generator.get_patterns()))

    return postprocess_closed_patterns(
        candidates, occurrence_store.occurrence_lists
    ), postprocess_maximal_patterns(candidates, occurrence_store.occurrence_lists)


class CombinedPatternGenerator:
    def __init__(
        self,
        patterns: Dict[int, Set],
        occurrence_store: FullOccurrenceStore,
        min_support_count: int,
        ef_dict,
        counting_strategy: CountingStrategy,
    ):
        self.patterns = patterns
        self.counting_strategy = counting_strategy

        self.flat_infix_patterns = flatten_patterns(patterns)

        self.infix_graph = build_enumeration_graph(
            occurrence_store, patterns, self.flat_infix_patterns
        )
        self.current_pattern_id = (
            max(self.flat_infix_patterns, key=lambda x: x.id).id + 1
        )
        self.min_support_count = min_support_count
        self.ef_dict = ef_dict
        self.occurrence_store = occurrence_store

    def get_patterns(self):
        return self.patterns

    def generate_combined_patterns(self):
        candidates = [(self.flat_infix_patterns, set(), set())]

        while len(candidates) != 0:
            next_iteration_candidates = []
            for (
                prefix_candidates,
                excluded_pattern_ids,
                skipable_pattern_ids,
            ) in candidates:
                for prefix_candidate in prefix_candidates:
                    new_excluded_pattern_ids = copy.copy(excluded_pattern_ids)
                    new_skipable_pattern_ids = copy.copy(skipable_pattern_ids)

                    new_patterns = self.combine_to_ef_patterns(
                        prefix_candidate,
                        {self.infix_graph},
                        new_excluded_pattern_ids,
                        new_skipable_pattern_ids,
                    )

                    next_iteration_candidates.append(
                        (
                            new_patterns,
                            new_excluded_pattern_ids,
                            new_skipable_pattern_ids,
                        )
                    )
            candidates = next_iteration_candidates

    def combine_to_ef_patterns(
        self,
        prefix_candidate: EventuallyFollowsPattern,
        nodes: Set[EnumerationNode],
        excluded_pattern_ids,
        skipable_pattern_ids,
    ) -> List[EventuallyFollowsPattern]:
        prefix_occurrence_list = self.occurrence_store.occurrence_lists[
            prefix_candidate.id
        ]
        iteration_patterns = []
        successors = set()
        ignorable_successors = set()

        for node in nodes:
            if node.pattern is None:
                successors = set(
                    [s for s in node.direct_successors if s not in excluded_pattern_ids]
                )
                return self.combine_to_ef_patterns(
                    prefix_candidate,
                    successors,
                    excluded_pattern_ids,
                    skipable_pattern_ids,
                )

            if node.pattern.id in skipable_pattern_ids:
                successors = set(
                    [s for s in node.direct_successors if s not in excluded_pattern_ids]
                )
                continue

            postfix_candidate = node.pattern

            (
                self.current_pattern_id,
                new_pattern,
                new_pattern_n_nodes,
            ) = self.__build_pattern(
                self.current_pattern_id, postfix_candidate, prefix_candidate
            )

            postfix_occurrence_list = self.occurrence_store.occurrence_lists[
                postfix_candidate.id
            ]
            support_to_gain = prefix_candidate.support

            self.__update_occurrences_with_ef_check(
                new_pattern,
                postfix_occurrence_list,
                prefix_occurrence_list,
                support_to_gain,
            )

            if new_pattern.support >= self.min_support_count:
                # TODO think about the usage of ef_checks and sequential_checks
                left_occurrence_matched = left_occurrence_blanket_contains_elements(
                    new_pattern,
                    self.occurrence_store.occurrence_lists[new_pattern.id],
                    perform_ef_checks=False,
                    perform_sequential_checks=False,
                )
                if not left_occurrence_matched:
                    iteration_patterns.append(new_pattern)
                    if new_pattern_n_nodes in self.patterns:
                        self.patterns[new_pattern_n_nodes].add(new_pattern)
                    else:
                        self.patterns[new_pattern_n_nodes] = {new_pattern}
                else:
                    skipable_pattern_ids.add(postfix_candidate.id)
                for child in node.direct_successors:
                    if node.pattern.id not in excluded_pattern_ids:
                        successors.add(child)
            else:
                excluded_pattern_ids.add(node.pattern.id)
                ignorable_successors = ignorable_successors.union(
                    set(node.direct_successors)
                )

        successors = successors.difference(ignorable_successors)
        if len(successors) == 0:
            return iteration_patterns

        return iteration_patterns + self.combine_to_ef_patterns(
            prefix_candidate, successors, excluded_pattern_ids, skipable_pattern_ids
        )

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

            for postfix_occurrence in postfix_occurrence_list[tree_id]:
                right_check_node = self.__get_right_check_node(
                    new_pattern.sub_patterns[-1], postfix_occurrence
                )
                for prefix_occurrence in prefix_occurrence_list[tree_id]:
                    left_check_node = get_left_check_node_for_full_occurrence(
                        new_pattern.sub_patterns[-2], prefix_occurrence
                    )
                    if is_eventually_follows_relation_with_ef_dict(
                        left_check_node, right_check_node, self.ef_dict[tree_id]
                    ):
                        new_occurrence_list.append(
                            prefix_occurrence + postfix_occurrence
                        )

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

    def __get_right_check_node(self, pattern: SubPattern, right_occurrence):
        if pattern.operator != cTreeOperator.Sequential:
            return right_occurrence[0]

        if len(pattern.children) == 0:
            raise Exception(
                "EF-relation is not defined for single sequential operators"
            )

        return right_occurrence[pattern.children[0].id - pattern.id]

    def __build_pattern(self, current_pattern_id, postfix_candidate, prefix_candidate):
        prefix_candidate = copy.deepcopy(prefix_candidate)
        postfix_candidate = copy.deepcopy(postfix_candidate)
        new_pattern = EventuallyFollowsPattern(
            sub_patterns=prefix_candidate.sub_patterns
            + [postfix_candidate.sub_patterns[0]],
            rightmost_leaf=postfix_candidate.rightmost_leaf,
        )
        set_preorder_ids(new_pattern)
        new_pattern.id = current_pattern_id
        current_pattern_id += 1
        new_pattern_n_nodes = new_pattern.rightmost_leaf.id + 1
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
            tree_id, support_to_gain, predecessor_occurrence_list, pattern
        )

        if pattern.support + support_to_gain < self.min_support_count:
            if pattern.id in self.occurrence_store.occurrence_lists:
                del self.occurrence_store.occurrence_lists[pattern.id]

            pattern.support = -1
            return support_to_gain, True

        return support_to_gain, False

    def update_support_count(
        self, tree_idx, new_occurrence_list, pattern: EventuallyFollowsPattern
    ):
        pattern.support += (
            self.counting_strategy.get_support_for_single_tree_full_occ_list(
                new_occurrence_list, tree_idx, pattern
            )
        )

    def update_support_to_gain(
        self, tree_id: int, support_to_gain: int, predecessor_occurrence_list, pattern
    ) -> int:
        return (
            support_to_gain
            - self.counting_strategy.get_support_for_single_tree_full_occ_list(
                predecessor_occurrence_list, tree_id, pattern
            )
        )

    def update_occurrence_list_for_pattern_and_tree(
        self, tree_idx, new_occurrence_list, pattern
    ):
        if len(new_occurrence_list) > 0:
            if pattern.id not in self.occurrence_store.occurrence_lists:
                self.occurrence_store.occurrence_lists[pattern.id] = dict()

            # TODO niklas: check if needed
            new_occurrence_list.sort(key=lambda o: o[-1].id)
            self.occurrence_store.occurrence_lists[pattern.id][
                tree_idx
            ] = new_occurrence_list
