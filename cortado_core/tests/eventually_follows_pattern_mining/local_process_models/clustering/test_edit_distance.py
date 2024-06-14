import unittest


from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.edit_distance import (
    calculate_edit_distance,
    calculate_edit_distance_own,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_pattern,
)


class TestEditDistance(unittest.TestCase):
    def test_edit_distance_for_single_trees(self):
        p1 = parse_pattern("→('a',→('d','c'))")
        p2 = parse_pattern("→('a',→('f','e'))")
        dist = calculate_edit_distance(p1, p2)
        dist_1 = calculate_edit_distance_own(p1, p2)

        self.assertEqual(2, dist)
        self.assertEqual(2, dist_1)

    def test_edit_distance_for_larger_patterns(self):
        p1 = parse_pattern("→('a',→('d','c'))...'c'")
        p2 = parse_pattern("→('a',→('f','e'))...'d'")
        dist = calculate_edit_distance(p1, p2)
        dist_1 = calculate_edit_distance_own(p1, p2)

        self.assertEqual(3, dist)
        self.assertEqual(3, dist_1)

    def test_edit_distance_ef_example_pattern_from_paper(self):
        p1 = parse_pattern("→(∧('b','c'),'e')")
        p2 = parse_pattern("✕('f')")
        dist = calculate_edit_distance(p1, p2)
        dist_1 = calculate_edit_distance_own(p1, p2)

        self.assertEqual(5, dist)
        self.assertEqual(5, dist_1)
