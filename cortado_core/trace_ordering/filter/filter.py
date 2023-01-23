from abc import ABC, abstractmethod
from typing import List

from cortado_core.utils.split_graph import Group


class Filter(ABC):
    @abstractmethod
    def filter(self, ordered_candidates: List[Group]) -> List[Group]:
        pass
