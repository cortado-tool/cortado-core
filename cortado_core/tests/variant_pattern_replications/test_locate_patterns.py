import unittest

from cortado_core.eventually_follows_pattern_mining.util.tree import set_tree_attributes
from cortado_core.subprocess_discovery.concurrency_trees.parse_concurrency_tree import (
    parse_concurrency_tree,
)
from cortado_core.variant_pattern_replications.locate_patterns import locate_pattern


class TestLocatePatterns(unittest.TestCase):
    def test_sequential_match_early_stop(self):
        variant = parse_concurrency_tree("->('c','d','a','c','d')")
        set_tree_attributes(variant)
        source_pattern = parse_concurrency_tree("->('c','d')")
        has_match, matching_locs = locate_pattern(variant, source_pattern, 2)
        self.assertTrue(has_match)
        self.assertEqual(matching_locs, {0, 1, 2})

    def test_sequential_match(self):
        variant = parse_concurrency_tree("->('c','a','d','a','c','d')")
        set_tree_attributes(variant)
        source_pattern = parse_concurrency_tree("->('c','d')")
        has_match, matching_locs = locate_pattern(variant, source_pattern, 6)
        self.assertTrue(has_match)
        self.assertEqual(matching_locs, {0, 5, 6})

    def test_concurrent_match(self):
        variant = parse_concurrency_tree("+('c','d','a','c','d')")
        set_tree_attributes(variant)
        source_pattern = parse_concurrency_tree("+('c','d')")
        has_match, matching_locs = locate_pattern(variant, source_pattern, 5)
        self.assertTrue(has_match)
        self.assertEqual(matching_locs, {0, 1, 2, 4, 5})
