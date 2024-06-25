import Levenshtein

from typing import List

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.stats import get_variants


from cortado_core.trace_ordering.scoring.trace_scorer import TraceScorer


class LevenshteinTraceScorer(TraceScorer):
    def score(
        self,
        log: EventLog,
        previously_added_traces: List[Trace],
        process_tree: ProcessTree,
        trace_candidate: Trace,
    ) -> float:
        trace_to_variant = lambda a: tuple(map(lambda b: b["concept:name"], a))
        previously_added_variants = set(map(trace_to_variant, previously_added_traces))
        variant_candidate = trace_to_variant(trace_candidate)
        variants = get_variants(log)
        weighted_distances = []
        for other_variant, other_traces in variants.items():
            if other_variant in previously_added_variants:
                continue
            distance = Levenshtein.distance(variant_candidate, other_variant)
            other_variant_frequency = (
                other_traces if isinstance(other_traces, int) else len(other_traces)
            )
            weighted_distances.append(distance * other_variant_frequency)
        return sum(weighted_distances)
