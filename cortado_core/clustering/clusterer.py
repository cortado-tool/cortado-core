import abc
from typing import List

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class Clusterer(abc.ABC):
    @abc.abstractmethod
    def calculate_clusters(self, variants: List[ConcurrencyTree]) -> List[List[ConcurrencyTree]]:
        pass
