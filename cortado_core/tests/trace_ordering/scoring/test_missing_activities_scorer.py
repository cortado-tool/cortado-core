import unittest

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.utils.generic import parse as pt_parse

from cortado_core.trace_ordering.scoring.missing_activities_scorer import MissingActivitiesScorer
from cortado_core.utils.split_graph import SequenceGroup, LeafGroup, ParallelGroup


class MissingActivitiesScorerTest(unittest.TestCase):
    def test_get_activities_in_trace(self):
        variant = SequenceGroup(
            [LeafGroup(['a']), ParallelGroup([LeafGroup(['b']), LeafGroup(['c', 'd']), LeafGroup(['a'])])])
        scorer = MissingActivitiesScorer()
        variant_activities = scorer.get_activities_in_trace(variant)

        self.assertEqual({'a', 'b', 'c', 'd'}, variant_activities)

    def test_two_missing_events(self):
        process_tree = pt_parse("->('a','b')")
        variant = SequenceGroup(
            [LeafGroup(['a']), ParallelGroup([LeafGroup(['b']), LeafGroup(['c', 'd']), LeafGroup(['a'])])])
        scorer = MissingActivitiesScorer()

        score = scorer.score(EventLog(), [], process_tree, variant)

        self.assertEqual(score, 2)

    def test_no_missing_events(self):
        process_tree = pt_parse("->('a','b', 'c', 'd', 'e')")
        variant = SequenceGroup(
            [LeafGroup(['a']), ParallelGroup([LeafGroup(['b']), LeafGroup(['c', 'd']), LeafGroup(['a'])])])
        scorer = MissingActivitiesScorer()

        score = scorer.score(EventLog(), [], process_tree, variant)

        self.assertEqual(score, 0)
