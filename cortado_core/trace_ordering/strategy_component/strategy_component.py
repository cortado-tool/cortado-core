from abc import ABC, abstractmethod
from typing import List

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.utils.split_graph import Group


class StrategyComponent(ABC):
    @abstractmethod
    def apply(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidates: List[Group]) -> List[Group]:
        """
        :param log: Event Log
        :param previously_added_variants: Added traces of previous iterations of the incremental discovery approach
        :param process_tree: Current process tree
        :param variant_candidates: Candidates that are selected to be added
        :return: Sorted list with candidate variants. Candidates with lower indices are worse than candidates with higher
                 indices.
        """
        pass
