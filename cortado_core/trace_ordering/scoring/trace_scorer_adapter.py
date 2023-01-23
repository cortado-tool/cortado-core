import statistics
from typing import List

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.scoring.scorer import Scorer
from cortado_core.trace_ordering.scoring.trace_scorer import TraceScorer
from cortado_core.utils.sequentializations import generate_variants
from cortado_core.utils.split_graph import Group


class TraceScorerAdapter(Scorer):
    def __init__(self, trace_scorer: TraceScorer, statistic=statistics.mean):
        self.trace_scorer = trace_scorer
        self.statistic = statistic

    def score(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidate: Group) -> float:
        traces_candidate = self.__generate_traces_from_variant(variant_candidate)
        previously_added_traces = self.__generate_traces_for_previously_added_variants(previously_added_variants)

        scores: List[float] = []

        for trace_candidate in traces_candidate:
            scores.append(self.trace_scorer.score(log, previously_added_traces, process_tree, trace_candidate))

        return self.statistic(scores)

    def __generate_traces_for_previously_added_variants(self, previously_added_variants: List[Group]):
        # when performance becomes a problem because the serializations for the previously_added_variants are
        # calculated too often, implement a cache
        traces: List[Trace] = []

        for previously_added_variant in previously_added_variants:
            traces = traces + self.__generate_traces_from_variant(previously_added_variant)

        return traces

    def __generate_traces_from_variant(self, variant: Group):
        traces: List[Trace] = []
        sequentializations = generate_variants(variant)

        for sequentialization in sequentializations:
            traces.append(self.__list_to_trace(sequentialization))

        return traces

    def __list_to_trace(self, trace_list: List[str]):
        trace = Trace()

        for activity in trace_list:
            event = Event()
            event['concept:name'] = activity

            trace.append(event)

        return trace
