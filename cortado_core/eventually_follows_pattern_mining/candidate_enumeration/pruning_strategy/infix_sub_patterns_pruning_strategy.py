from typing import Dict, Tuple, Set

from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.pruning_strategy import (
    PruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class InfixSubPatternsPruningStrategy(PruningStrategy):
    def __init__(self, found_patterns: Dict[int, Set[EventuallyFollowsPattern]]):
        self.found_patterns = found_patterns

    def can_prune(self, candidate: EventuallyFollowsPattern, iteration: int) -> bool:
        candidate_length = len(candidate)
        if candidate_length == 1 or iteration <= 2:
            return False

        for delete_position in range(candidate_length - 1):
            pattern_after_removal, n_removed_nodes = self.remove_sub_pattern(
                candidate, delete_position
            )

            search_iteration = iteration - n_removed_nodes
            if search_iteration not in self.found_patterns:
                return True

            if pattern_after_removal not in self.found_patterns[search_iteration]:
                return True

        return False

    @staticmethod
    def remove_sub_pattern(
        pattern: EventuallyFollowsPattern, position: int
    ) -> Tuple[EventuallyFollowsPattern, int]:
        if len(pattern) <= 1:
            return pattern, 0

        new_pattern = pattern.copy()
        n_removed_nodes = len(pattern.sub_patterns[position])
        new_pattern.sub_patterns = (
            new_pattern.sub_patterns[:position]
            + new_pattern.sub_patterns[position + 1 :]
        )

        return new_pattern, n_removed_nodes
