import abc

from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class PruningStrategy(abc.ABC):
    @abc.abstractmethod
    def can_prune(self, candidate: EventuallyFollowsPattern, iteration: int) -> bool:
        pass
