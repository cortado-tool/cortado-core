import unittest
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.conversion.process_tree import converter as pt_converter

from cortado_core.eventually_follows_pattern_mining.local_process_models.similarity.causal_footprint import (
    create_causal_footprint,
)


class TestCausalFootprint(unittest.TestCase):
    def test_causal_footprint(self):
        tree = pt_parse("->('a', 'b', +('c', 'd'))")
        net, im, fm = pt_converter.apply(tree)
        N, look_ahead_links, look_back_links = create_causal_footprint(net, im, fm)

        self.assertEqual({"a", "b", "c", "d"}, N)
        self.assertIn(frozenset({"b"}), look_ahead_links["a"])
        self.assertIn(frozenset({"b", "c"}), look_ahead_links["a"])
        self.assertIn(frozenset({"b", "d"}), look_ahead_links["a"])
        self.assertIn(frozenset({"b", "a"}), look_ahead_links["a"])
        self.assertIn(frozenset({"b", "c", "d"}), look_ahead_links["a"])
        self.assertIn(frozenset({"b", "c", "a"}), look_ahead_links["a"])
        self.assertIn(frozenset({"b", "d", "a"}), look_ahead_links["a"])
        self.assertIn(frozenset({"b", "d", "a", "c"}), look_ahead_links["a"])
        self.assertIn(frozenset({"c"}), look_ahead_links["a"])
        self.assertIn(frozenset({"d"}), look_ahead_links["a"])
        self.assertFalse("c" in look_ahead_links)
        self.assertFalse("d" in look_ahead_links)
        self.assertFalse("a" in look_back_links)
        self.assertNotIn(frozenset({"a"}), look_ahead_links["a"])
        self.assertNotIn(frozenset({"c"}), look_back_links["b"])
        self.assertNotIn(frozenset({"d"}), look_back_links["b"])
