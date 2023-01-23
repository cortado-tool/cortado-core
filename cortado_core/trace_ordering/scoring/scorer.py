from abc import ABC, abstractmethod
from typing import List

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.utils.split_graph import Group


class Scorer(ABC):
    @abstractmethod
    def score(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidate: Group) -> float:
        pass
