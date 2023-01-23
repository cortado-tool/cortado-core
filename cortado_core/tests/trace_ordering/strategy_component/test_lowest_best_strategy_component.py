import unittest

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.tests.trace_ordering.utils import generate_variants_from_lists, MockScorer
from cortado_core.trace_ordering.strategy_component.lowest_best_strategy_component import LowestBestStrategyComponent


class LowestBestStrategyComponentTest(unittest.TestCase):
    def test_lowest_best_strategy(self):
        scorer = MockScorer([1, 3, 2, 7])
        variants = generate_variants_from_lists(
            [["a", "b", "c", "d"], ["a", "c", "e"], ["a", ["parallel", "b", "c"]], ["a", "c", "e", "f"]])
        sc = LowestBestStrategyComponent(scorer)
        result = sc.apply(EventLog(), [], ProcessTree(), variants)

        self.assertEqual(len(result), len(variants))
        self.assertEqual(result[0], variants[3])
        self.assertEqual(result[1], variants[1])
        self.assertEqual(result[2], variants[2])
        self.assertEqual(result[3], variants[0])

    def test_empty_candidate_set(self):
        scorer = MockScorer([1, 3, 2, 7])
        sc = LowestBestStrategyComponent(scorer)
        result = sc.apply(EventLog(), [], ProcessTree(), [])

        self.assertEqual(len(result), 0)
