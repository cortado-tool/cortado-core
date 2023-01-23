from typing import List, Tuple

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.filter.filter import Filter
from cortado_core.trace_ordering.strategy_component.strategy_component import StrategyComponent
from cortado_core.utils.split_graph import Group, SequenceGroup, LeafGroup


class Strategy:
    def __init__(self, components_filter: List[Tuple[StrategyComponent, Filter]]):
        self.components_filter = components_filter

    def apply(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidates: List[Group]) -> Group:
        candidates = variant_candidates

        for sc, candidates_filter in self.components_filter:
            candidates = sc.apply(log, previously_added_variants, process_tree, candidates)
            candidates = candidates_filter.filter(candidates)

        assert (len(candidates) == 1)

        return candidates[0]

    def apply_trace(self, log: EventLog, previously_added_traces: List[Trace], process_tree: ProcessTree,
                    trace_candidates: List[Trace]) -> Trace:
        previously_added_variants = [self.__trace_to_sequence_group(t) for t in previously_added_traces]
        variant_candidates = [self.__trace_to_sequence_group(t) for t in trace_candidates]

        selected_variant = self.apply(log, previously_added_variants, process_tree, variant_candidates)

        return self.__sequence_group_to_trace(selected_variant)

    def __trace_to_sequence_group(self, trace: Trace) -> Group:
        return SequenceGroup([LeafGroup([e['concept:name']]) for e in trace])

    def __sequence_group_to_trace(self, group: Group) -> Trace:
        trace = Trace()

        for leaf_group in group:
            event = Event()
            event['concept:name'] = leaf_group[0]

            trace.append(event)

        return trace
