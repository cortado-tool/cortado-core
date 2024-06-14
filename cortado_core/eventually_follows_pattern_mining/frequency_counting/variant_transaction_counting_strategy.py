from typing import List, Tuple, Dict

from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class VariantTransactionCountingStrategy(CountingStrategy):
    def get_support_for_1_pattern(
        self,
        occurrences: Dict[
            int, List[Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]]
        ],
    ) -> int:
        return len(occurrences)

    def get_support_for_single_tree(
        self,
        occurrence_list: List[
            Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]
        ],
        _,
    ):
        if len(occurrence_list) > 0:
            return 1

        return 0

    def get_support_for_1_pattern_combination_occ_list(
        self,
        occurrences: Dict[
            int, List[Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]]
        ],
    ) -> int:
        return len(occurrences)

    def get_support_for_single_tree_combination_occ_list(
        self,
        occurrence_list: List[
            Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]
        ],
        _,
    ):
        if len(occurrence_list) > 0:
            return 1

        return 0

    def get_support_for_1_pattern_full_occ_list(
        self, occurrences: Dict[int, List[List[ConcurrencyTree]]]
    ) -> int:
        return len(occurrences)

    def get_support_for_single_tree_full_occ_list(
        self,
        occurrence_list: List[List[ConcurrencyTree]],
        tree_id: int,
        pattern: EventuallyFollowsPattern,
    ) -> int:
        if len(occurrence_list) > 0:
            return 1

        return 0
