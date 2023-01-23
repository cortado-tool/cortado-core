import unittest

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.utils.generic import parse as pt_parse

from cortado_core.tests.trace_ordering.utils import generate_test_trace
from cortado_core.trace_ordering.scoring.alignment_trace_scorer import AlignmentTraceScorer


class AlignmentTraceScorerTest(unittest.TestCase):
    def test_get_activities_in_trace(self):
        trace = generate_test_trace("aefg")
        tree = pt_parse("->('a','b','g','f')")
        scorer = AlignmentTraceScorer()
        score = scorer.score(EventLog(), [], tree, trace)

        self.assertEqual(score, 4)