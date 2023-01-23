import copy
from typing import List

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.process_tree.obj import ProcessTree


from cortado_core.trace_ordering.scoring.trace_scorer import TraceScorer
from cortado_core.lca_approach import add_trace_to_pt_language
from cortado_core.trace_ordering.utils.f_mesaure import calculate_f_measure


class BruteForceTraceScorer(TraceScorer):
    def __init__(self, try_pulling_lca_down=True, add_artificial_start_end=False):
        self.try_pulling_lca_down = try_pulling_lca_down
        self.add_artificial_start_end = add_artificial_start_end

    def score(self, log: EventLog, previously_added_traces: List[Trace], process_tree: ProcessTree,
              trace_candidate: Trace) -> float:
        tree = copy.deepcopy(process_tree)
        pt = add_trace_to_pt_language(tree, EventLog(previously_added_traces), trace_candidate,
                                      try_pulling_lca_down=self.try_pulling_lca_down,
                                      add_artificial_start_end=self.add_artificial_start_end)

        f_measure, _, _ = calculate_f_measure(pt, log)
        return f_measure
