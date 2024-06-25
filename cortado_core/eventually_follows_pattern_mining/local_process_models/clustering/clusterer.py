import abc
from typing import List

from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class Clusterer(abc.ABC):
    @abc.abstractmethod
    def calculate_clusters(
        self, patterns: List[EventuallyFollowsPattern]
    ) -> List[List[EventuallyFollowsPattern]]:
        pass
