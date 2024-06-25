from typing import List

from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.pruning_strategy import (
    PruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class ComposedPruningStrategy(PruningStrategy):
    def __init__(self, strategies: List[PruningStrategy]):
        self.strategies = strategies

    def can_prune(self, candidate: EventuallyFollowsPattern, iteration: int) -> bool:
        for strategy in self.strategies:
            if strategy.can_prune(candidate, iteration):
                return True

        return False
