import unittest

from cortado_core.clustering.label_vector_clusterer import LabelVectorClusterer
from cortado_core.subprocess_discovery.concurrency_trees.parse_concurrency_tree import parse_concurrency_tree


class TestLabelVectorClusterer(unittest.TestCase):
    def test_each_variant_get_a_cluster(self):
        v1 = parse_concurrency_tree("→('a', ∧('d',→('b','c')))")
        v2 = parse_concurrency_tree("→('d', ∧('d',→('b','c')))")

        clusterer = LabelVectorClusterer(n_clusters=2)
        clusters = clusterer.calculate_clusters([v1, v2])
        self.assertEqual(2, len(clusters))
        self.assertEqual(1, len(clusters[0]))
        self.assertEqual(1, len(clusters[1]))
        self.ensure_one_to_one_mapping_to_clusters([v1, v2], clusters)

    def test_all_variants_in_single_cluster(self):
        v1 = parse_concurrency_tree("→('a', ∧('d',→('b','c')))")
        v2 = parse_concurrency_tree("→('d', ∧('d',→('b','c')))")

        clusterer = LabelVectorClusterer(n_clusters=1)
        clusters = clusterer.calculate_clusters([v1, v2])
        self.assertEqual(1, len(clusters))
        self.assertEqual(2, len(clusters[0]))
        self.ensure_one_to_one_mapping_to_clusters([v1, v2], clusters)

    def test_distribution_in_two_clusters(self):
        v1 = parse_concurrency_tree("→('a', ∧('d',→('b','c')))")
        v2 = parse_concurrency_tree("→('d', ∧('d',→('b','c')))")
        v3 = parse_concurrency_tree("→('e', ∧('d',→('f','c')))")
        v4 = parse_concurrency_tree("→('i', ∧('i',→('f','g')))")

        clusterer = LabelVectorClusterer(n_clusters=2)
        clusters = clusterer.calculate_clusters([v1, v2, v3, v4])

        self.assertEqual({1, 3}, set([len(c) for c in clusters]))
        self.assertEqual(3, len(clusters[0]))
        self.ensure_one_to_one_mapping_to_clusters([v1, v2, v3, v4], clusters)

    def ensure_one_to_one_mapping_to_clusters(self, variants, clusters):
        search_trees = set(variants)

        for cluster in clusters:
            for variant in cluster:
                search_trees.remove(variant)

        self.assertEqual(0, len(search_trees))
