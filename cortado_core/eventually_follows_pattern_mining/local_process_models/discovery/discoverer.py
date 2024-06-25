import abc
from typing import List

from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class Discoverer(abc.ABC):
    @abc.abstractmethod
    def discover_model(self, patterns: List[EventuallyFollowsPattern]):
        pass
