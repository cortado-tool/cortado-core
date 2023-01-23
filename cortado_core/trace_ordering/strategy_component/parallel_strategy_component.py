from collections import defaultdict
from typing import List, Tuple

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.strategy_component.strategy_component import StrategyComponent
from cortado_core.utils.split_graph import Group


class ParallelStrategyComponent(StrategyComponent):
    def __init__(self, strategies: List[Tuple[StrategyComponent, float]]):
        self.strategies = strategies

    def apply(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidates: List[Group]) -> List[Group]:
        results = defaultdict(int)

        for strategy, weight in self.strategies:
            strategy_order = strategy.apply(log, previously_added_variants, process_tree, variant_candidates)
            for i, candidate in enumerate(strategy_order):
                results[candidate] += (i+1) * weight

        ordered_candidates = []

        for candidate, order in results.items():
            ordered_candidates.append((candidate, order))

        ordered_candidates = sorted(ordered_candidates, key=lambda x: x[1])

        return [variant for variant, _ in ordered_candidates]
