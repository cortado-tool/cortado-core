import statistics
import unittest
from typing import List

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.scoring.trace_scorer import TraceScorer
from cortado_core.trace_ordering.scoring.trace_scorer_adapter import TraceScorerAdapter
from cortado_core.utils.split_graph import SequenceGroup, LeafGroup, ParallelGroup


class TraceScorerAdapterTest(unittest.TestCase):
    class MockTraceScorer(TraceScorer):
        def score(self, log: EventLog, previously_added_traces: List[Trace], process_tree: ProcessTree,
                  trace_candidate: Trace) -> float:
            return 1

    def test_adapter_runs_scorer_for_each_sequentialization(self):
        variant = SequenceGroup(
            [LeafGroup(['a']), ParallelGroup([LeafGroup(['b']), LeafGroup(['c']), LeafGroup(['a'])])])
        trace_scorer = TraceScorerAdapterTest.MockTraceScorer()
        scorer = TraceScorerAdapter(trace_scorer, statistic=sum)

        score = scorer.score(EventLog(), [], ProcessTree(), variant)
        self.assertEqual(score, 6)

    def test_adapter_applies_statistic_function(self):
        variant = SequenceGroup(
            [LeafGroup(['a']), ParallelGroup([LeafGroup(['b']), LeafGroup(['c']), LeafGroup(['a'])])])
        trace_scorer = TraceScorerAdapterTest.MockTraceScorer()
        scorer = TraceScorerAdapter(trace_scorer, statistic=statistics.mean)

        score = scorer.score(EventLog(), [], ProcessTree(), variant)
        self.assertEqual(score, 1)
