import unittest

from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_occurrence_counting_strategy import (
    TraceOccurrenceCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_transaction_counting_strategy import (
    TraceTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_occurrence_counting_strategy import (
    VariantOccurrenceCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
)


class TestFrequencyCounting(unittest.TestCase):
    # TODO write test for more complex patterns
    def test_get_support_not_overlapping_occurrences(self):
        tree = parse_concurrency_tree("→('a','b','a','b')")
        tree.n_traces = 5

        # occurrences for pattern ->(a,b)
        occ_list = [
            (tree.children[0], tree.children[1], [tree]),
            (tree.children[2], tree.children[3], [tree]),
        ]

        self.assertEqual(
            1,
            VariantTransactionCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceTransactionCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            1,
            VariantOccurrenceCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceOccurrenceCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )

    def test_get_support_not_overlapping_occurrences_in_sequence(self):
        tree = parse_concurrency_tree("→('a','a','a','a','a')")
        tree.n_traces = 5
        # occurrences for pattern ->(a,a)
        occ_list = [
            (tree.children[0], tree.children[1], [tree]),
            (tree.children[1], tree.children[2], [tree]),
            (tree.children[2], tree.children[3], [tree]),
            (tree.children[3], tree.children[4], [tree]),
        ]

        self.assertEqual(
            1,
            VariantTransactionCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceTransactionCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            1,
            VariantOccurrenceCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceOccurrenceCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )

    def test_get_support_not_overlapping_occurrences_in_concurrent(self):
        tree = parse_concurrency_tree("∧('a','a','a','a','a')")
        tree.n_traces = 5
        # occurrences for pattern +(a,a)
        occ_list = [
            (tree.children[0], tree.children[1], [tree]),
            (tree.children[0], tree.children[2], [tree]),
            (tree.children[0], tree.children[3], [tree]),
            (tree.children[0], tree.children[4], [tree]),
        ]

        self.assertEqual(
            1,
            VariantTransactionCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceTransactionCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            1,
            VariantOccurrenceCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceOccurrenceCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )

    def test_get_support_different_root_nodes(self):
        tree = parse_concurrency_tree("→(∧('a','b'),∧('a','b'))")
        tree.n_traces = 5
        # occurrences for pattern +(a,b)
        occ_list = [
            (
                tree.children[0].children[0],
                tree.children[0].children[1],
                [tree.children[0]],
            ),
            (
                tree.children[1].children[0],
                tree.children[1].children[1],
                [tree.children[1]],
            ),
        ]

        self.assertEqual(
            1,
            VariantTransactionCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceTransactionCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            2,
            VariantOccurrenceCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            10,
            TraceOccurrenceCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )

    def test_get_support_ef_pattern(self):
        tree = parse_concurrency_tree(
            "→(∧('a','b'),'c',∧('a','b'),'c',∧('a','b'),'c',∧('a','b'),'c')"
        )
        tree.n_traces = 5
        # occurrences for pattern +(a,b)...+(a,b)
        occ_list = [
            (
                tree.children[0].children[0],
                tree.children[2].children[1],
                [tree.children[0], tree.children[2]],
            ),
            (
                tree.children[0].children[0],
                tree.children[4].children[1],
                [tree.children[0], tree.children[4]],
            ),
            (
                tree.children[0].children[0],
                tree.children[6].children[1],
                [tree.children[0], tree.children[6]],
            ),
            (
                tree.children[2].children[0],
                tree.children[4].children[1],
                [tree.children[2], tree.children[4]],
            ),
            (
                tree.children[2].children[0],
                tree.children[6].children[1],
                [tree.children[2], tree.children[6]],
            ),
            (
                tree.children[4].children[0],
                tree.children[6].children[1],
                [tree.children[4], tree.children[6]],
            ),
        ]

        self.assertEqual(
            1,
            VariantTransactionCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            5,
            TraceTransactionCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            3,
            VariantOccurrenceCountingStrategy().get_support_for_single_tree(
                occ_list, 0
            ),
        )
        self.assertEqual(
            15,
            TraceOccurrenceCountingStrategy([tree]).get_support_for_single_tree(
                occ_list, 0
            ),
        )
