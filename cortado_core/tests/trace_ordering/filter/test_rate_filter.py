import unittest

from cortado_core.tests.trace_ordering.utils import generate_variants_from_lists
from cortado_core.trace_ordering.filter.rate_filter import RateFilter


class RateFilterTest(unittest.TestCase):
    def test_filter_all_but_one(self):
        filter = RateFilter(0)
        variants = generate_variants_from_lists([["a", "b", "c", "d"], ["a", "c", "e"], ["a", ["parallel", "b", "c"]]])
        result = filter.filter(variants)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], variants[-1])

    def test_filter_keep_all(self):
        filter = RateFilter(1)
        variants = generate_variants_from_lists([["a", "b", "c", "d"], ["a", "c", "e"], ["a", ["parallel", "b", "c"]]])
        result = filter.filter(variants)

        self.assertEqual(len(result), 3)
        self.assertEqual(result, variants)

    def test_filter_keep_two(self):
        filter = RateFilter(0.5)
        variants = generate_variants_from_lists([["a", "b", "c", "d"], ["a", "c", "e"], ["a", ["parallel", "b", "c"]]])
        result = filter.filter(variants)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], variants[1])
        self.assertEqual(result[1], variants[2])
