from collections import defaultdict
from typing import Dict, List, Tuple

from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class VariantOccurrenceCountingStrategy(CountingStrategy):
    def get_support_for_1_pattern(
        self,
        occurrences: Dict[
            int, List[Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]]
        ],
    ) -> int:
        support = 0
        for _, occ in occurrences.items():
            rmo_ids = set([rmo.id for _, rmo, _ in occ])
            support += len(rmo_ids)

        return support

    def get_support_for_single_tree(
        self,
        occurrence_list: List[
            Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]
        ],
        _,
    ):
        if len(occurrence_list) == 0:
            return 0

        distinct_roots_for_sub_patters = defaultdict(set)

        for _, _, ros in occurrence_list:
            for i, ro in enumerate(ros):
                distinct_roots_for_sub_patters[i].add(ro.id)

        support = min([len(ids) for ids in distinct_roots_for_sub_patters.values()])

        return support

    def get_support_for_1_pattern_combination_occ_list(
        self,
        occurrences: Dict[
            int, List[Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]]
        ],
    ) -> int:
        support = 0
        for _, occ in occurrences.items():
            root_ids = set([roots[0].id for roots, _, _ in occ])
            support += len(root_ids)

        return support

    def get_support_for_single_tree_combination_occ_list(
        self,
        occurrence_list: List[
            Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]
        ],
        _,
    ):
        if len(occurrence_list) == 0:
            return 0

        distinct_roots_for_sub_patters = defaultdict(set)

        for roots, _, _ in occurrence_list:
            for i, ro in enumerate(roots):
                distinct_roots_for_sub_patters[i].add(ro.id)

        support = min([len(ids) for ids in distinct_roots_for_sub_patters.values()])

        return support

    def get_support_for_1_pattern_full_occ_list(
        self, occurrences: Dict[int, List[List[ConcurrencyTree]]]
    ) -> int:
        support = 0
        for tree_id, occ in occurrences.items():
            ids = set([nodes[0].id for nodes in occ])
            support += len(ids)

        return support

    def get_support_for_single_tree_full_occ_list(
        self,
        occurrence_list: List[List[ConcurrencyTree]],
        tree_id: int,
        pattern: EventuallyFollowsPattern,
    ) -> int:
        if len(occurrence_list) == 0:
            return 0

        distinct_roots_for_sub_patters = defaultdict(set)

        for occurrences in occurrence_list:
            for i, sub_pattern_root in enumerate(pattern.sub_patterns):
                distinct_roots_for_sub_patters[i].add(
                    occurrences[sub_pattern_root.id].id
                )

        support = min([len(ids) for ids in distinct_roots_for_sub_patters.values()])

        return support
