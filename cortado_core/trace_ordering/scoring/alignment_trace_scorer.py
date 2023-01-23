from typing import List

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.algo.conformance.alignments.process_tree.variants import search_graph_pt as tree_alignment

from cortado_core.trace_ordering.scoring.trace_scorer import TraceScorer


class AlignmentTraceScorer(TraceScorer):
    def score(self, log: EventLog, previously_added_traces: List[Trace], process_tree: ProcessTree,
              trace_candidate: Trace) -> float:
        alignment = tree_alignment.apply(trace_candidate, process_tree)

        return alignment['cost']
