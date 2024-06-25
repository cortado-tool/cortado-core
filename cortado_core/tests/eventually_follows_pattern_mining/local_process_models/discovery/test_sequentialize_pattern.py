import os
import unittest

from cortado_core.eventually_follows_pattern_mining.local_process_models.discovery.sequentialize_pattern import (
    sequentialize_pattern,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    SubPattern,
    EventuallyFollowsPattern,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_pattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeFromcGroup
from cortado_core.utils.cvariants import get_concurrency_variants
from cortado_core.utils.sequentializations import generate_sequentializations


class TestSequentializePattern(unittest.TestCase):
    def test_sequential_base_case(self):
        pattern = parse_pattern("→('a','b','c')")
        traces = sequentialize_pattern(pattern)
        self.assertEqual(1, len(traces))
        self.assertEqual(["a", "b", "c"], [e["concept:name"] for e in traces[0]])

    def test_fallthrough_base_case(self):
        pattern = parse_pattern("✕('a','b','c')")
        traces = sequentialize_pattern(pattern)
        traces_as_lists = [[e["concept:name"] for e in t] for t in traces]
        self.assertEqual(6, len(traces))
        self.assertIn(["a", "b", "c"], traces_as_lists)
        self.assertIn(["a", "c", "b"], traces_as_lists)
        self.assertIn(["b", "a", "c"], traces_as_lists)
        self.assertIn(["b", "c", "a"], traces_as_lists)
        self.assertIn(["c", "a", "b"], traces_as_lists)
        self.assertIn(["c", "b", "a"], traces_as_lists)

    def test_concurrent_base_case(self):
        pattern = parse_pattern("∧('a','b',→('c','d'))")
        traces = sequentialize_pattern(pattern)
        self.assertEqual(12, len(traces))
        traces_as_lists = [[e["concept:name"] for e in t] for t in traces]
        self.assertIn(["a", "b", "c", "d"], traces_as_lists)
        self.assertIn(["a", "c", "d", "b"], traces_as_lists)
        self.assertIn(["b", "a", "c", "d"], traces_as_lists)
        self.assertIn(["b", "c", "d", "a"], traces_as_lists)
        self.assertIn(["c", "d", "a", "b"], traces_as_lists)
        self.assertIn(["c", "d", "b", "a"], traces_as_lists)

        self.assertIn(["a", "c", "b", "d"], traces_as_lists)
        self.assertIn(["b", "c", "a", "d"], traces_as_lists)
        self.assertIn(["c", "a", "b", "d"], traces_as_lists)
        self.assertIn(["c", "a", "d", "b"], traces_as_lists)
        self.assertIn(["c", "b", "a", "d"], traces_as_lists)
        self.assertIn(["c", "b", "d", "a"], traces_as_lists)

    def test_ef_base_case(self):
        pattern = parse_pattern("'a'...'b'...'c'")
        traces = sequentialize_pattern(pattern)
        self.assertEqual(1, len(traces))
        self.assertEqual(
            ["a", "...", "b", "...", "c"], [e["concept:name"] for e in traces[0]]
        )

    def test_sequentialize_nested_pattern(self):
        pattern = parse_pattern("∧('a','b',→('c','d',∧('e','f')))...→('g','h')")
        traces = sequentialize_pattern(pattern)
        self.assertEqual(60, len(traces))

    def test_sequentialize_two_sub_patterns(self):
        pattern = parse_pattern("∧('a','b',→('c','d',∧('e','f')))...∧('g','h')")
        traces = sequentialize_pattern(pattern)
        self.assertEqual(120, len(traces))

    def test_sequentialize_three_sub_patterns(self):
        pattern = parse_pattern(
            "∧('a','b',→('c','d',∧('e','f')))...∧('g','h')...∧('i','j')"
        )
        traces = sequentialize_pattern(pattern)
        self.assertEqual(240, len(traces))

    def test_larger_pattern_names_sequentialization(self):
        pattern = parse_pattern("→('asdf','basdf','casdf',∧('dasdf',→('easdf','f')))")
        traces = sequentialize_pattern(pattern)
        self.assertEqual(3, len(traces))
        traces_as_lists = [[e["concept:name"] for e in t] for t in traces]
        self.assertIn(
            ["asdf", "basdf", "casdf", "dasdf", "easdf", "f"], traces_as_lists
        )
        self.assertIn(
            ["asdf", "basdf", "casdf", "easdf", "f", "dasdf"], traces_as_lists
        )
        self.assertIn(
            ["asdf", "basdf", "casdf", "easdf", "dasdf", "f"], traces_as_lists
        )

    def __cTreeToPattern(self, tree):
        p = SubPattern(label=tree.label, operator=tree.op)
        p.children = [self.__cTreeToPattern(c) for c in tree.children]

        return p
