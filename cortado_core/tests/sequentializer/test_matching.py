import unittest

from cortado_core.subprocess_discovery.concurrency_trees.parse_concurrency_tree import (
    parse_concurrency_tree,
)
from cortado_core.sequentializer.pattern import parse_sequentializer_pattern
from cortado_core.sequentializer.matching import is_matching


class TestMatching(unittest.TestCase):
    def test_matching(self):
        variant = parse_concurrency_tree("+('b','c','d')")
        source_pattern = parse_sequentializer_pattern("+('b','c', ...)")

        is_m, match = is_matching(variant, source_pattern)
        self.assertTrue(is_m)
