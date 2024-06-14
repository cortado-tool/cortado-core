import copy
from typing import List, Dict, Optional, Tuple

from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_transaction_counting_strategy import (
    TraceTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_statistic_tracker import (
    OccurrenceStatisticTracker,
    NoOccurrenceStatisticTracker,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.util import (
    get_rightmost_occurrences_from_search_node,
    get_first_search_node,
    should_check_only_first_search_node,
    get_nodes_with_operator,
    get_leaf_nodes_with_label,
    updated_sub_pattern_to_single_child_with_sequential_root,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    is_eventually_follows_relation,
    get_right_check_node,
    get_left_check_node,
    is_eventually_follows_relation_with_ef_dict,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator as ConcurrencyTreeOperator,
)


class RightmostOccurrenceStore:
    def __init__(
        self,
        trees: List[ConcurrencyTree],
        counting_strategy: CountingStrategy,
        min_support_count: int,
        ef_dict,
        size_tracker: Optional[OccurrenceStatisticTracker] = None,
    ):
        self.trees = trees
        # pattern -> tree_index -> list((leftmost_occurrence, rightmost_occurrence, list(root_occurrences)))
        # maybe one can optimize this data structure. Currently, it enforces that the GC cannot delete any generated pattern.
        # However, id(pattern) is not suitable as a key, because it is only guaranteed to be unique in the lifetime of an object.
        self.occurrence_lists: Dict[
            int,
            Dict[
                int,
                List[Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]],
            ],
        ] = dict()
        self.counting_strategy = counting_strategy
        self.min_support_count = min_support_count
        self.is_transaction_based_counting = isinstance(
            self.counting_strategy, VariantTransactionCountingStrategy
        ) or isinstance(self.counting_strategy, TraceTransactionCountingStrategy)
        self.frequent_1_pattern_ids = None
        self.ef_dict = ef_dict
        self.size_tracker = (
            size_tracker if size_tracker is not None else NoOccurrenceStatisticTracker()
        )

    def set_frequent_1_patterns(self, frequent_1_patterns):
        self.frequent_1_pattern_ids = dict()
        for pattern in frequent_1_patterns:
            self.frequent_1_pattern_ids[pattern] = pattern.id

    def update_occurrence_lists(self, patterns: List[EventuallyFollowsPattern]):
        for pattern in patterns:
            self.update_occurrence_lists_for_pattern(pattern)

        self.size_tracker.track_after_iteration(self.occurrence_lists)

    def update_occurrence_lists_for_pattern(self, pattern: EventuallyFollowsPattern):
        if pattern.predecessor_pattern is None:
            self.update_occurrence_lists_for_initial_pattern(pattern)
        else:
            self.update_occurrence_lists_using_predecessor_patterns(pattern)

    def update_occurrence_lists_for_initial_pattern(
        self, pattern: EventuallyFollowsPattern
    ):
        initial_sub_pattern = pattern.sub_patterns[0]

        if initial_sub_pattern.operator is not None:
            self.update_occurrence_lists_for_initial_pattern_with_operator(
                pattern, initial_sub_pattern.operator
            )
        else:
            self.update_occurrence_lists_for_initial_pattern_with_label(
                pattern, initial_sub_pattern.label
            )
        self.set_support_for_initial_pattern(pattern)

    def update_occurrence_lists_for_initial_pattern_with_operator(
        self, pattern: EventuallyFollowsPattern, operator: ConcurrencyTreeOperator
    ):
        for i, tree in enumerate(self.trees):
            rightmost_occurrence_list = get_nodes_with_operator(operator, tree)
            occurrence_list = [
                (node, node, [node]) for node in rightmost_occurrence_list
            ]
            self.update_occurrence_list_for_pattern_and_tree(
                i, occurrence_list, pattern
            )

    def update_occurrence_lists_for_initial_pattern_with_label(
        self, pattern: EventuallyFollowsPattern, label: str
    ):
        for i, tree in enumerate(self.trees):
            rightmost_occurrence_list = get_leaf_nodes_with_label(label, tree)
            occurrence_list = [
                (node, node, [node]) for node in rightmost_occurrence_list
            ]
            self.update_occurrence_list_for_pattern_and_tree(
                i, occurrence_list, pattern
            )

    def set_support_for_initial_pattern(self, pattern: EventuallyFollowsPattern):
        if pattern.id not in self.occurrence_lists:
            pattern.support = -1
            return

        pattern.support = self.counting_strategy.get_support_for_1_pattern(
            self.occurrence_lists[pattern.id]
        )

    def update_occurrence_lists_using_predecessor_patterns(self, pattern):
        added_new_subpattern = len(pattern) > len(pattern.predecessor_pattern)
        if added_new_subpattern:
            self.update_occurrence_lists_using_predecessor_pattern_for_new_subpattern(
                pattern
            )
        elif updated_sub_pattern_to_single_child_with_sequential_root(pattern):
            self.update_occurrence_lists_for_sub_pattern_with_single_child_and_sequential_root(
                pattern
            )
        else:
            self.update_occurrence_lists_using_predecessor_pattern_for_new_inner_node(
                pattern
            )

    def update_occurrence_lists_using_predecessor_pattern_for_new_subpattern(
        self, pattern: EventuallyFollowsPattern
    ):
        matching_1_pattern = EventuallyFollowsPattern(
            sub_patterns=[pattern.rightmost_leaf], rightmost_leaf=pattern.rightmost_leaf
        )
        matching_1_pattern_id = self.frequent_1_pattern_ids[matching_1_pattern]

        predecessor_pattern = pattern.predecessor_pattern
        predecessor_pattern_id = predecessor_pattern.id
        support_to_gain = predecessor_pattern.support

        matching_frequent_pattern_occ = self.occurrence_lists[matching_1_pattern_id]

        for tree_id in self.occurrence_lists[predecessor_pattern_id]:
            new_occurrence_list = []
            predecessor_occurrence_list = self.occurrence_lists[predecessor_pattern_id][
                tree_id
            ]

            if tree_id not in matching_frequent_pattern_occ:
                support_to_gain, early_stopping = self.update_support(
                    tree_id,
                    pattern,
                    new_occurrence_list,
                    predecessor_occurrence_list,
                    support_to_gain,
                )
                if early_stopping:
                    break
                continue

            matching_frequent_last_sub_pattern_occ_list = matching_frequent_pattern_occ[
                tree_id
            ]

            for matching_occurrence in matching_frequent_last_sub_pattern_occ_list:
                matching_lmo, matching_rmo, matching_ro = matching_occurrence
                right_check_node = get_right_check_node(matching_occurrence)

                for predecessor_occurrence in predecessor_occurrence_list:
                    (
                        predecessor_lmo,
                        predecessor_rmo,
                        predecessor_ro,
                    ) = predecessor_occurrence
                    left_check_node = get_left_check_node(predecessor_occurrence)
                    if is_eventually_follows_relation_with_ef_dict(
                        left_check_node, right_check_node, self.ef_dict[tree_id]
                    ):
                        new_ro = copy.copy(predecessor_ro)
                        new_ro.append(matching_rmo)
                        occurrence = (predecessor_lmo, matching_rmo, new_ro)
                        new_occurrence_list.append(occurrence)
                        if self.is_transaction_based_counting:
                            break

            support_to_gain, early_stopping = self.update_support(
                tree_id,
                pattern,
                new_occurrence_list,
                predecessor_occurrence_list,
                support_to_gain,
            )
            if early_stopping:
                break

            self.update_occurrence_list_for_pattern_and_tree(
                tree_id, new_occurrence_list, pattern
            )

    def update_occurrence_lists_for_sub_pattern_with_single_child_and_sequential_root(
        self, pattern: EventuallyFollowsPattern
    ):
        predecessor_pattern = pattern.predecessor_pattern
        support_to_gain = predecessor_pattern.support

        for tree_id in self.occurrence_lists[predecessor_pattern.id]:
            new_occurrence_list = []

            predecessor_occurrence_list = self.occurrence_lists[predecessor_pattern.id][
                tree_id
            ]
            for predecessor_occurrence in predecessor_occurrence_list:
                (
                    predecessor_lmo,
                    predecessor_rmo,
                    predecessor_ro,
                ) = predecessor_occurrence
                if predecessor_ro[-1].parent is None:
                    continue

                if predecessor_ro[-1].parent.op != ConcurrencyTreeOperator.Sequential:
                    continue

                new_ro = copy.copy(predecessor_ro)
                new_ro[-1] = predecessor_ro[-1].parent
                new_occurrence_list.append((predecessor_lmo, predecessor_rmo, new_ro))

            support_to_gain, early_stopping = self.update_support(
                tree_id,
                pattern,
                new_occurrence_list,
                predecessor_occurrence_list,
                support_to_gain,
            )
            if early_stopping:
                break

            self.update_occurrence_list_for_pattern_and_tree(
                tree_id, new_occurrence_list, pattern
            )

    def update_occurrence_lists_using_predecessor_pattern_for_new_inner_node(
        self, pattern
    ):
        predecessor_pattern = pattern.predecessor_pattern
        support_to_gain = predecessor_pattern.support

        check_only_first_search_node = should_check_only_first_search_node(pattern)

        for tree_id in self.occurrence_lists[predecessor_pattern.id]:
            new_occurrence_list = []
            predecessor_occurrence_list = self.occurrence_lists[predecessor_pattern.id][
                tree_id
            ]
            check = None

            for predecessor_occurrence in predecessor_occurrence_list:
                (
                    predecessor_lmo,
                    predecessor_rmo,
                    predecessor_ro,
                ) = predecessor_occurrence
                search_node = get_first_search_node(
                    pattern.height_diff, predecessor_rmo
                )
                if search_node is None:
                    continue

                if (
                    search_node.parent == check
                    and search_node.parent.op != ConcurrencyTreeOperator.Sequential
                    and self.is_transaction_based_counting
                ):
                    continue
                check = search_node.parent

                rm_occurrence_list = get_rightmost_occurrences_from_search_node(
                    pattern, search_node, check_only_first_search_node
                )
                if pattern.is_leftmost_occurrence_update_required:
                    new_occurrence_list += [
                        (node, node, predecessor_ro) for node in rm_occurrence_list
                    ]
                else:
                    new_occurrence_list += [
                        (predecessor_lmo, node, predecessor_ro)
                        for node in rm_occurrence_list
                    ]

            support_to_gain, early_stopping = self.update_support(
                tree_id,
                pattern,
                new_occurrence_list,
                predecessor_occurrence_list,
                support_to_gain,
            )
            if early_stopping:
                break

            self.update_occurrence_list_for_pattern_and_tree(
                tree_id, new_occurrence_list, pattern
            )

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
        pattern.support += self.counting_strategy.get_support_for_single_tree(
            new_occurrence_list, tree_idx
        )

    def update_support_to_gain(
        self, tree_id: int, support_to_gain: int, predecessor_occurrence_list
    ) -> int:
        return support_to_gain - self.counting_strategy.get_support_for_single_tree(
            predecessor_occurrence_list, tree_id
        )

    def update_occurrence_list_for_pattern_and_tree(
        self, tree_idx, new_occurrence_list, pattern
    ):
        if len(new_occurrence_list) > 0:
            if pattern.id not in self.occurrence_lists:
                self.occurrence_lists[pattern.id] = dict()

            # TODO niklas: check if needed
            new_occurrence_list.sort(key=lambda o: o[1].id)
            self.occurrence_lists[pattern.id][tree_idx] = new_occurrence_list

    def remove_pattern(self, pattern: EventuallyFollowsPattern):
        del self.occurrence_lists[pattern.id]
