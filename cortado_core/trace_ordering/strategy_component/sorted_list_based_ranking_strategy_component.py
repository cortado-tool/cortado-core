from typing import List

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.scoring.scorer import Scorer
from cortado_core.trace_ordering.strategy_component.strategy_component import StrategyComponent
from cortado_core.utils.split_graph import Group


class SortedListBasedRankingStrategyComponent(StrategyComponent):
    def __init__(self, scorer: Scorer, reverse: bool):
        self.scorer = scorer
        self.reverse = reverse

    def apply(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidates: List[Group]) -> List[Group]:
        ranking = []
        for candidate in variant_candidates:
            score = self.scorer.score(log, previously_added_variants, process_tree, candidate)
            ranking.append((candidate, score))

        ranking = sorted(ranking, key=lambda x: x[1], reverse=self.reverse)

        return [variant for variant, _ in ranking]

