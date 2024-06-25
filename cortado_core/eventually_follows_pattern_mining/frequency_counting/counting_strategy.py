import abc
from typing import List, Dict, Tuple

from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class CountingStrategy(abc.ABC):
    @abc.abstractmethod
    def get_support_for_1_pattern(
        self,
        occurrences: Dict[
            int, List[Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]]
        ],
    ) -> int:
        pass

    @abc.abstractmethod
    def get_support_for_single_tree(
        self,
        occurrence_list: List[
            Tuple[ConcurrencyTree, ConcurrencyTree, List[ConcurrencyTree]]
        ],
        tree_id: int,
    ) -> int:
        pass

    @abc.abstractmethod
    def get_support_for_1_pattern_combination_occ_list(
        self,
        occurrences: Dict[
            int, List[Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]]
        ],
    ) -> int:
        pass

    @abc.abstractmethod
    def get_support_for_single_tree_combination_occ_list(
        self,
        occurrence_list: List[
            Tuple[List[ConcurrencyTree], ConcurrencyTree, ConcurrencyTree]
        ],
        tree_id: int,
    ) -> int:
        pass

    @abc.abstractmethod
    def get_support_for_1_pattern_full_occ_list(
        self, occurrences: Dict[int, List[List[ConcurrencyTree]]]
    ) -> int:
        pass

    @abc.abstractmethod
    def get_support_for_single_tree_full_occ_list(
        self,
        occurrence_list: List[List[ConcurrencyTree]],
        tree_id: int,
        pattern: EventuallyFollowsPattern,
    ) -> int:
        pass
