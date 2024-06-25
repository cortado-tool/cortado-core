import unittest

from cortado_core.subprocess_discovery.concurrency_trees.parse_concurrency_tree import (
    parse_concurrency_tree,
)
from cortado_core.sequentializer.reduction_rules import apply_reduction_rules


class TestReductionRules(unittest.TestCase):
    def test_multiple_sequential_operators(self):
        variant = parse_concurrency_tree("->('a', ->('b', 'c', x('d','e'), ->('f')))")
        reduced = apply_reduction_rules(variant)

        self.assertEqual("→(a, b, c, ✕(d, e), f)", str(reduced))

    def test_multiple_parallel_operators(self):
        variant = parse_concurrency_tree("+('a', +('b', 'c', x('d','e'), +('f')))")
        reduced = apply_reduction_rules(variant)

        self.assertEqual("∧(a, b, c, ✕(d, e), f)", str(reduced))

    def test_remove_operators_with_only_one_child(self):
        variant = parse_concurrency_tree("->('a', +('b', 'c', ->('f')))")
        reduced = apply_reduction_rules(variant)

        self.assertEqual("→(a, ∧(b, c, f))", str(reduced))
