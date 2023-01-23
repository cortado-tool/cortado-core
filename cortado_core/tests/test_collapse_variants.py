import unittest

from cortado_core.utils.collapse_variants import collapse_variant
from cortado_core.utils.split_graph import SequenceGroup as S, LeafGroup as L, LoopGroup as Lo, ParallelGroup as P


class TestCollapseVariants(unittest.TestCase):
    def test_collapse_sequence_group_with_only_leaf_nodes(self):
        variant = S([L(['a']), L(['b']), L(['b']), L(['b']), L(['c'])])
        collapsed = collapse_variant(variant)

        expected = S([L(['a']), Lo([L(['b'])]), L(['c'])])

        self.assertEqual(expected, collapsed)

    def test_collapse_parallel_group_with_only_leaf_nodes(self):
        variant = P([L(['a']), L(['b']), L(['b']), L(['b']), L(['c'])])
        collapsed = collapse_variant(variant)

        self.assertEqual(variant, collapsed)

    def test_collapse_nested_sequence_groups(self):
        variant1 = S([L(['a']), L(['b']), L(['b']), L(['b']), P([L('a'), S([L('a'), L(['b']), L(['b'])])])])
        variant2 = S([L(['a']), L(['b']), L(['b']), P([L('a'), S([L('a'), L(['b']), L(['b']), L(['b'])])])])
        collapsed1 = collapse_variant(variant1)
        collapsed2 = collapse_variant(variant2)

        expected = S(
            [L(['a']), Lo([L(['b'])]), P([L('a'), S([L('a'), Lo([L(['b'])])])])])

        self.assertEqual(expected, collapsed1)
        self.assertEqual(expected, collapsed2)

    def test_collapse_nested_parallel_groups(self):
        variant = S([P([L('a'), L('b')]), P([L('a'), L('b')]), L('c'), P([L('a'), L('b')]), P([L('a'), L('b')]),
                     P([L('a'), L('b')]), L('c')])
        collapsed = collapse_variant(variant)

        self.assertEqual(variant, collapsed)
