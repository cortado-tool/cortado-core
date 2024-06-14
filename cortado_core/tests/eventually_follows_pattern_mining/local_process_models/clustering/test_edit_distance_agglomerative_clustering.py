import unittest

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.distance_matrix import (
    calculate_distance_matrix,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.edit_distance_agglomerative_clusterer import (
    EditDistanceAgglomerativeClusterer,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_pattern,
)


class TestEditDistanceAgglomerativeClustering(unittest.TestCase):
    def test_clustering(self):
        p1 = parse_pattern("→('a',✕('b','c'))...'d'")
        p2 = parse_pattern("→('a',✕('c','c'))...'d'")
        p3 = parse_pattern("→('a',✕('c','d'))...'d'")

        p4 = parse_pattern("∧('a',→('b','f'))...✕('d','e')")
        p5 = parse_pattern("∧('a',→('b','f'))...✕('d','a')")
        p6 = parse_pattern("∧('a',→('b','f'))...'c'...✕('d','e')")

        p7 = parse_pattern("'a'...'b'...'c'")
        p8 = parse_pattern("'a'...'b'...'c'...'s'")
        p9 = parse_pattern("'i'...'a'...'b'...'c'")

        patterns = [p1, p2, p3, p4, p5, p6, p7, p8, p9]

        distance_matrix = calculate_distance_matrix(patterns)
        clusterer = EditDistanceAgglomerativeClusterer(
            max_distance=3, distance_matrix=distance_matrix
        )
        clusters = clusterer.calculate_clusters(patterns)
        self.assertEqual(3, len(clusters))
        self.assertIn([p1, p2, p3], clusters)
        self.assertIn([p4, p5, p6], clusters)
        self.assertIn([p7, p8, p9], clusters)

    def test_clustering_max_distance_is_zero(self):
        p1 = parse_pattern("→('a',✕('b','c'))...'d'")
        p2 = parse_pattern("→('a',✕('c','c'))...'d'")
        p3 = parse_pattern("→('a',✕('c','d'))...'d'")

        patterns = [p1, p2, p3]

        distance_matrix = calculate_distance_matrix(patterns)
        clusterer = EditDistanceAgglomerativeClusterer(
            max_distance=0, distance_matrix=distance_matrix
        )
        clusters = clusterer.calculate_clusters(patterns)
        self.assertEqual(3, len(clusters))
        for cluster in clusters:
            self.assertEqual(1, len(cluster))
