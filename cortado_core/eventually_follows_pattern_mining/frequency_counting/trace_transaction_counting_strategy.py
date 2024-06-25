from typing import List, Dict, Tuple

from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class TraceTransactionCountingStrategy(CountingStrategy):
    def __init__(self, trees: List[ConcurrencyTree]):
        self.trees = trees

    def get_support_for_1_pattern(
        self,
        occurrences: Dict[
            int, List[Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]]
        ],
    ):
        return sum([self.trees[tree_id].n_traces for tree_id in occurrences])

    def get_support_for_single_tree(
        self,
        occurrence_list: List[
            Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]
        ],
        tree_id: int,
    ):
        if len(occurrence_list) > 0:
            return self.trees[tree_id].n_traces

        return 0

    def get_support_for_1_pattern_combination_occ_list(
        self,
        occurrences: Dict[
            int, List[Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]]
        ],
    ):
        return sum([self.trees[tree_id].n_traces for tree_id in occurrences])

    def get_support_for_single_tree_combination_occ_list(
        self,
        occurrence_list: List[
            Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]
        ],
        tree_id: int,
    ):
        if len(occurrence_list) > 0:
            return self.trees[tree_id].n_traces

        return 0

    def get_support_for_1_pattern_full_occ_list(
        self, occurrences: Dict[int, List[List[ConcurrencyTree]]]
    ) -> int:
        return sum([self.trees[tree_id].n_traces for tree_id in occurrences])

    def get_support_for_single_tree_full_occ_list(
        self,
        occurrence_list: List[List[ConcurrencyTree]],
        tree_id: int,
        pattern: EventuallyFollowsPattern,
    ) -> int:
        if len(occurrence_list) > 0:
            return self.trees[tree_id].n_traces

        return 0
