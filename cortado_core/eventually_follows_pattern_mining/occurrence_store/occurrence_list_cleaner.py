import abc
from typing import Dict, Set

from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class OccurrenceListCleaner(abc.ABC):
    @abc.abstractmethod
    def clear_occurrence_list_after_iteration(
        self,
        iteration: int,
        occ_list,
        patterns: Dict[int, Set[EventuallyFollowsPattern]],
    ):
        pass


class LastIterationOccurrenceListCleaner(OccurrenceListCleaner):
    def clear_occurrence_list_after_iteration(
        self,
        iteration: int,
        occ_list,
        patterns: Dict[int, Set[EventuallyFollowsPattern]],
    ):
        if iteration - 1 <= 1:
            return

        for pattern in patterns[iteration - 1]:
            occ_list.remove_pattern(pattern)


class NoOccurrenceListCleaner(OccurrenceListCleaner):
    def clear_occurrence_list_after_iteration(
        self,
        iteration: int,
        occ_list,
        patterns: Dict[int, Set[EventuallyFollowsPattern]],
    ):
        return
