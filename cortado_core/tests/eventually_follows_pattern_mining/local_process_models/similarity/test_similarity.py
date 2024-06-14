import unittest
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.conversion.process_tree import converter as pt_converter

from cortado_core.eventually_follows_pattern_mining.local_process_models.similarity.causal_footprint_similarity import (
    similarity_score,
    similarity_score_model_lists,
)


class TestSimilarity(unittest.TestCase):
    def test_same_model(self):
        tree = pt_parse("->('a', 'b', +('c', 'd', 'e', 'f', 'g', 'h'))")
        net, im, fm = pt_converter.apply(tree)
        net2, im2, fm2 = pt_converter.apply(tree)

        self.assertGreater(similarity_score(net, im, fm, net2, im2, fm2), 0.99)

    def test_completely_different_models(self):
        tree = pt_parse("->('a', 'b', +('c', 'd', 'e', 'f', 'g', 'h'))")
        tree2 = pt_parse("->('i', 'o')")
        net, im, fm = pt_converter.apply(tree)
        net2, im2, fm2 = pt_converter.apply(tree2)

        self.assertEqual(similarity_score(net, im, fm, net2, im2, fm2), 0)

    def test_parts_are_equal(self):
        tree = pt_parse("->('a', 'b', +('c', 'd', 'e', 'f', 'g', 'h'))")
        tree2 = pt_parse("->('a', 'd')")
        net, im, fm = pt_converter.apply(tree)
        net2, im2, fm2 = pt_converter.apply(tree2)
        score = similarity_score(net, im, fm, net2, im2, fm2)

        self.assertGreater(score, 0.2)
        self.assertLess(score, 0.6)

    def test_parts_are_equal2(self):
        tree = pt_parse("->('a', 'b', +('c', 'd', 'e', 'f', 'g', 'h'))")
        tree2 = pt_parse("->('a', 'c', 'd', 'e', 'f', 'g', 'h')")
        net, im, fm = pt_converter.apply(tree)
        net2, im2, fm2 = pt_converter.apply(tree2)
        score = similarity_score(net, im, fm, net2, im2, fm2)

        self.assertGreater(score, 0.2)
        self.assertLess(score, 0.6)

    def test_similarity_score_model_lists(self):
        tree = pt_parse("->('a', 'b', +('c', 'd', 'e', 'f', 'g', 'h'))")
        tree2 = pt_parse("->('a', 'c', 'd', 'e', 'f', 'g', 'h')")
        tree3 = pt_parse("->('i', 'j')")
        net, im, fm = pt_converter.apply(tree)
        net2, im2, fm2 = pt_converter.apply(tree2)
        net3, im3, fm3 = pt_converter.apply(tree3)

        score = similarity_score_model_lists(
            [(net, im, fm), (net2, im2, fm2), (net3, im3, fm3)],
            [(net, im, fm), (net2, im2, fm2)],
        )
        self.assertGreater(score, 2 / 3 - 0.01)
        self.assertLess(score, 2 / 3 + 0.01)
