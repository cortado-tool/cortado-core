import unittest

from cortado_core.clustering.edit_distance import calculate_edit_distance
from cortado_core.subprocess_discovery.concurrency_trees.parse_concurrency_tree import parse_concurrency_tree


class TestEditDistance(unittest.TestCase):
    def test_edit_distance_for_single_trees(self):
        t1 = parse_concurrency_tree("→('a',→('d','c'))")
        t2 = parse_concurrency_tree("→('a',→('f','e'))")
        dist = calculate_edit_distance(t1, t2)

        self.assertEqual(2, dist)

    def test_edit_distance_example_trees_from_paper(self):
        t1 = parse_concurrency_tree("→(∧('b','c'),'e')")
        t2 = parse_concurrency_tree("✕('f')")
        dist = calculate_edit_distance(t1, t2)

        self.assertEqual(5, dist)
