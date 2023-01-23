import random
from typing import List

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.scoring.scorer import Scorer
from cortado_core.utils.split_graph import Group


class RandomScorer(Scorer):
    def score(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidate: Group) -> float:
        return random.random()
