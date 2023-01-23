import math
import unittest

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeFromcGroup
from cortado_core.utils.sequentializations import get_number_of_sequentializations, generate_sequentializations
from cortado_core.utils.split_graph import SequenceGroup as S, LeafGroup as L, ParallelGroup as P, LoopGroup


class TestSequentializations(unittest.TestCase):
    def test_number_of_sequentializations(self):
        # ->(+(a,b), +(a,b), c, +(a,b), +(a,b), +(a,b), c)
        variant = S([P([L('a'), L('b')]), P([L('a'), L('b')]), L('c'), P([L('a'), L('b')]), P([L('a'), L('b')]),
                     P([L('a'), L('b')]), L('c')])

        sequentializations = generate_sequentializations(variant)
        n_sequentializations = get_number_of_sequentializations(cTreeFromcGroup(variant))

        self.assertEqual(2 * 2 * 2 * 2 * 2, n_sequentializations)
        self.assertEqual(len(sequentializations), n_sequentializations)

    def test_number_of_sequentializations_nested_case(self):
        # ->(+(a,b, ->(e, +(d,e,g))), +(a,b), c, +(a,b), +(a,b), +(a,b), c)
        variant = S([P([L('a'), L('b'), S([L('e'), P([L('d'), L('e'), L('g')])])]), P([L('a'), L('b')]), L('c'),
                     P([L('a'), L('b')]), P([L('a'), L('b')]),
                     P([L('a'), L('b')]), L('c')])

        sequentializations = generate_sequentializations(variant)
        n_sequentializations = get_number_of_sequentializations(cTreeFromcGroup(variant))
        self.assertEqual(180 * 2 * 2 * 2 * 2, n_sequentializations)
        self.assertEqual(len(sequentializations), n_sequentializations)

    def test_sequentializations_nested_case_with_n_seq_parameter(self):
        # ->(+(a,b, ->(e, +(d,e,g))), +(a,b), c, +(a,b), +(a,b), +(a,b), c)
        variant = S([P([L('a'), L('b'), S([L('e'), P([L('d'), L('e'), L('g')])])]), P([L('a'), L('b')]), L('c'),
                     P([L('a'), L('b')]), P([L('a'), L('b')]),
                     P([L('a'), L('b')]), L('c')])

        sequentializations = generate_sequentializations(variant, n_sequentializations=5)
        self.assertEqual(5, len(sequentializations))

    def test_sequentializations_more_than_ten_million_sequentializations(self):
        variant = S([P([L('a'), L('b'), L('c')]) for _ in range(9)])

        self.assertEqual(10_077_696, get_number_of_sequentializations(cTreeFromcGroup(variant)))

        sequentializations = generate_sequentializations(variant, n_sequentializations=5)
        self.assertEqual(5, len(sequentializations))

    def test_sequentializations_terminates_for_very_large_variants(self):
        variant = S([P([L('a'), L('b'), L('c')]) for _ in range(50)])

        sequentializations = generate_sequentializations(variant, n_sequentializations=500)
        self.assertEqual(500, len(sequentializations))

    def test_sequentializations_with_loop_operator(self):
        variant = S([P([LoopGroup([L('a')]), L('b'), L('c')])])
        n_seq = get_number_of_sequentializations(cTreeFromcGroup(variant))

        sequentializations = generate_sequentializations(variant)
        self.assertEqual(12, len(sequentializations))
        self.assertEqual(12, n_seq)
