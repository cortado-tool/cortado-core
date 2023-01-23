import unittest

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.tests.trace_ordering.utils import generate_variants_from_lists, MockScorer
from cortado_core.trace_ordering.strategy_component.highest_best_strategy_component import HighestBestStrategyComponent
from cortado_core.trace_ordering.strategy_component.parallel_strategy_component import ParallelStrategyComponent


class ParallelStrategyComponentTest(unittest.TestCase):
    def test_parallel_strategy_component(self):
        scorer1 = MockScorer([3, 1, 2, 4])
        scorer2 = MockScorer([4, 1, 3, 2])
        variants = generate_variants_from_lists(
            [["a", "b", "c", "d"], ["a", "c", "e"], ["a", ["parallel", "b", "c"]], ["a", "c", "e", "f"]])
        sc1 = HighestBestStrategyComponent(scorer1)
        sc2 = HighestBestStrategyComponent(scorer2)
        sc = ParallelStrategyComponent([(sc1, 1), (sc2, 1)])
        result = sc.apply(EventLog(), [], ProcessTree(), variants)

        self.assertEqual(len(result), len(variants))
        self.assertEqual(result[0], variants[1])
        self.assertEqual(result[1], variants[2])
        self.assertEqual(result[2], variants[3])
        self.assertEqual(result[3], variants[0])

    def test_parallel_strategy_weighted_components_1(self):
        scorer1 = MockScorer([3, 1, 2, 4])
        scorer2 = MockScorer([4, 1, 3, 2])
        variants = generate_variants_from_lists(
            [["a", "b", "c", "d"], ["a", "c", "e"], ["a", ["parallel", "b", "c"]], ["a", "c", "e", "f"]])
        sc1 = HighestBestStrategyComponent(scorer1)
        sc2 = HighestBestStrategyComponent(scorer2)
        sc = ParallelStrategyComponent([(sc1, 3), (sc2, 1)])
        result = sc.apply(EventLog(), [], ProcessTree(), variants)

        self.assertEqual(len(result), len(variants))
        self.assertEqual(result[0], variants[1])
        self.assertEqual(result[1], variants[2])
        self.assertEqual(result[2], variants[0])
        self.assertEqual(result[3], variants[3])

    def test_parallel_strategy_weighted_components_2(self):
        scorer1 = MockScorer([1, 3, 2, 4])
        scorer2 = MockScorer([4, 3, 2, 1])
        variants = generate_variants_from_lists(
            [["a", "b", "c", "d"], ["a", "c", "e"], ["a", ["parallel", "b", "c"]], ["a", "c", "e", "f"]])
        sc1 = HighestBestStrategyComponent(scorer1)
        sc2 = HighestBestStrategyComponent(scorer2)
        sc = ParallelStrategyComponent([(sc1, 0.9), (sc2, 0.1)])
        result = sc.apply(EventLog(), [], ProcessTree(), variants)

        self.assertEqual(len(result), len(variants))
        self.assertEqual(result[0], variants[0])
        self.assertEqual(result[1], variants[2])
        self.assertEqual(result[2], variants[1])
        self.assertEqual(result[3], variants[3])

    def test_empty_candidate_set(self):
        scorer1 = MockScorer([3, 1, 2, 4])
        scorer2 = MockScorer([4, 1, 3, 2])
        sc1 = HighestBestStrategyComponent(scorer1)
        sc2 = HighestBestStrategyComponent(scorer2)
        sc = ParallelStrategyComponent([(sc1, 1), (sc2, 1)])
        result = sc.apply(EventLog(), [], ProcessTree(), [])

        self.assertEqual(len(result), 0)
