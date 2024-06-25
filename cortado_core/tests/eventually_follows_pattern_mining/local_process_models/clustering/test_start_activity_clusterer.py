import unittest

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.start_activity_clusterer import (
    StartActivityClusterer,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_pattern,
)


class TestStartActivityClusterer(unittest.TestCase):
    def test_get_start_activities(self):
        pattern = parse_pattern("→('a', →(∧('b','c')))")
        self.assertEqual({"a"}, StartActivityClusterer().get_start_activities(pattern))

    def test_get_start_activities_concurrent(self):
        pattern = parse_pattern("∧('d', 'e', →('a', →(∧('b','c'))))")
        self.assertEqual(
            {"a", "d", "e"}, StartActivityClusterer().get_start_activities(pattern)
        )

    def test_get_clusters(self):
        pattern = parse_pattern("→('a', →(∧('b','c')))")
        pattern2 = parse_pattern("∧('d', 'e', →('a', →(∧('b','c'))))")
        clusterer = StartActivityClusterer()
        clusters = clusterer.calculate_clusters([pattern, pattern2])
        self.assertEqual(3, len(clusters))
        self.assertEqual(1, len([c for c in clusters if len(c) == 2]))
        self.assertEqual(2, len([c for c in clusters if len(c) == 1]))
