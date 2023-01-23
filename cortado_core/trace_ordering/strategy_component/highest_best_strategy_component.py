from typing import List

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.scoring.scorer import Scorer
from cortado_core.trace_ordering.strategy_component.sorted_list_based_ranking_strategy_component import \
    SortedListBasedRankingStrategyComponent
from cortado_core.trace_ordering.strategy_component.strategy_component import StrategyComponent
from cortado_core.utils.split_graph import Group


class HighestBestStrategyComponent(StrategyComponent):
    def __init__(self, scorer: Scorer):
        self.scorer = scorer
        self.sorted_list_strategy = SortedListBasedRankingStrategyComponent(scorer, reverse=False)

    def apply(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidates: List[Group]) -> List[Group]:
        return self.sorted_list_strategy.apply(log, previously_added_variants, process_tree, variant_candidates)
