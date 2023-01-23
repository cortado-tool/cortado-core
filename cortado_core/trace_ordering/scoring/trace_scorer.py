from abc import ABC, abstractmethod
from typing import List

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.process_tree.obj import ProcessTree


class TraceScorer(ABC):
    @abstractmethod
    def score(self, log: EventLog, previously_added_traces: List[Trace], process_tree: ProcessTree,
              trace_candidate: Trace) -> float:
        pass
