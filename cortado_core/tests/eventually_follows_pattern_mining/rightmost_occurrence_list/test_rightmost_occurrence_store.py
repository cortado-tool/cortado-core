import unittest

from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.rightmost_occurence_store import (
    RightmostOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
    parse_pattern,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    get_first_ef_node_id_per_node_for_trees,
)


class TestRightmostOccurrenceStore(unittest.TestCase):
    def test_initial_pattern_occurrence_list_initialization(self):
        tree = parse_concurrency_tree("→('a','a',∧('a','b'))")
        ef_dict = get_first_ef_node_id_per_node_for_trees([tree])

        pattern = parse_pattern("'a'")
        pattern.id = 0
        store = RightmostOccurrenceStore(
            [tree],
            VariantTransactionCountingStrategy(),
            min_support_count=1,
            ef_dict=ef_dict,
        )
        store.update_occurrence_lists([pattern])

        self.assertEqual(tree.children[0], store.occurrence_lists[pattern.id][0][0][0])
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern.id][0][0][1])
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern.id][0][0][2][0]
        )
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern.id][0][1][0])
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern.id][0][1][1])
        self.assertEqual(
            tree.children[1], store.occurrence_lists[pattern.id][0][1][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern.id][0][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern.id][0][2][1]
        )
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern.id][0][2][2][0]
        )
        self.assertEqual(3, len(store.occurrence_lists[pattern.id][0]))

    def test_pattern_occurrence_list_initialization(self):
        tree = parse_concurrency_tree("→('a','a',∧('a','b'))")
        ef_dict = get_first_ef_node_id_per_node_for_trees([tree])

        pattern1 = parse_pattern("∧()")
        pattern1.id = 0
        pattern2 = parse_pattern("∧('a')")
        pattern2.predecessor_pattern = pattern1
        pattern2.height_diff = -1
        pattern2.id = 1
        pattern3 = parse_pattern("∧('a','b')")
        pattern3.height_diff = 0
        pattern3.predecessor_pattern = pattern2
        pattern3.is_leftmost_occurrence_update_required = False
        pattern3.id = 2
        patterns = [pattern1, pattern2, pattern3]
        store = RightmostOccurrenceStore(
            [tree], VariantTransactionCountingStrategy(), 1, ef_dict
        )
        store.update_occurrence_lists(patterns)

        self.assertEqual(
            tree.children[-1], store.occurrence_lists[pattern1.id][0][0][0]
        )
        self.assertEqual(
            tree.children[-1], store.occurrence_lists[pattern1.id][0][0][1]
        )
        self.assertEqual(
            tree.children[-1], store.occurrence_lists[pattern1.id][0][0][2][0]
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern1.id][0]))
        self.assertEqual(
            tree.children[-1].children[0], store.occurrence_lists[pattern2.id][0][0][0]
        )
        self.assertEqual(
            tree.children[-1].children[0], store.occurrence_lists[pattern2.id][0][0][1]
        )
        self.assertEqual(
            tree.children[-1], store.occurrence_lists[pattern2.id][0][0][2][0]
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern2.id][0]))
        self.assertEqual(
            tree.children[-1].children[0], store.occurrence_lists[pattern3.id][0][0][0]
        )
        self.assertEqual(
            tree.children[-1].children[1], store.occurrence_lists[pattern3.id][0][0][1]
        )
        self.assertEqual(
            tree.children[-1], store.occurrence_lists[pattern3.id][0][0][2][0]
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern3.id][0]))
        self.assertEqual(1, pattern1.support)
        self.assertEqual(1, pattern2.support)
        self.assertEqual(1, pattern3.support)

    def test_pattern_occurrence_list_initialization_more_nested_tree(self):
        tree = parse_concurrency_tree("→('a','a',∧('a',→('b','c')))")
        ef_dict = get_first_ef_node_id_per_node_for_trees([tree])

        # ->()
        pattern1 = parse_pattern("→()")
        pattern1.id = 0
        pattern2 = parse_pattern("→('a')")
        pattern2.height_diff = -1
        pattern2.predecessor_pattern = pattern1
        pattern2.id = 1
        pattern3 = parse_pattern("→('a', 'a')")
        pattern3.height_diff = 0
        pattern3.predecessor_pattern = pattern2
        pattern3.is_leftmost_occurrence_update_required = False
        pattern3.id = 2

        patterns = [pattern1, pattern2, pattern3]
        store = RightmostOccurrenceStore(
            [tree], VariantTransactionCountingStrategy(), 1, ef_dict
        )
        store.update_occurrence_lists(patterns)

        self.assertEqual(tree, store.occurrence_lists[pattern1.id][0][0][0])
        self.assertEqual(tree, store.occurrence_lists[pattern1.id][0][0][1])
        self.assertEqual(tree, store.occurrence_lists[pattern1.id][0][0][2][0])
        self.assertEqual(
            tree.children[2].children[1], store.occurrence_lists[pattern1.id][0][1][0]
        )
        self.assertEqual(
            tree.children[2].children[1], store.occurrence_lists[pattern1.id][0][1][1]
        )
        self.assertEqual(
            tree.children[2].children[1],
            store.occurrence_lists[pattern1.id][0][1][2][0],
        )
        self.assertEqual(2, len(store.occurrence_lists[pattern1.id][0]))
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern2.id][0][0][0])
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern2.id][0][0][1])
        self.assertEqual(tree, store.occurrence_lists[pattern2.id][0][0][2][0])
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern2.id][0][1][0])
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern2.id][0][1][1])
        self.assertEqual(tree, store.occurrence_lists[pattern2.id][0][1][2][0])
        self.assertEqual(2, len(store.occurrence_lists[pattern2.id][0]))
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern3.id][0][0][0])
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern3.id][0][0][1])
        self.assertEqual(tree, store.occurrence_lists[pattern3.id][0][0][2][0])
        self.assertEqual(1, len(store.occurrence_lists[pattern3.id][0]))

    def test_pattern_occurrence_list_initialization_more_nested_tree_without_match(
        self,
    ):
        tree = parse_concurrency_tree("→('a','a',∧('a',→('b','c')))")
        ef_dict = get_first_ef_node_id_per_node_for_trees([tree])

        pattern1 = parse_pattern("→()")
        pattern1.id = 0
        pattern2 = parse_pattern("→('a')")
        pattern2.height_diff = -1
        pattern2.predecessor_pattern = pattern1
        pattern2.id = 1
        pattern3 = parse_pattern("→('a', 'b')")
        pattern3.height_diff = 0
        pattern3.predecessor_pattern = pattern2
        pattern3.is_leftmost_occurrence_update_required = False
        pattern3.id = 2
        patterns = [pattern1, pattern2, pattern3]
        store = RightmostOccurrenceStore(
            [tree], VariantTransactionCountingStrategy(), 1, ef_dict
        )
        store.update_occurrence_lists(patterns)

        self.assertEqual(2, len(store.occurrence_lists[pattern1.id][0]))
        self.assertEqual(2, len(store.occurrence_lists[pattern2.id][0]))
        self.assertFalse(pattern3 in store.occurrence_lists)

    def test_pattern_occurrence_list_initialization_new_sub_pattern(self):
        tree = parse_concurrency_tree("→('a','a',∧('a','b'))")
        ef_dict = get_first_ef_node_id_per_node_for_trees([tree])
        pattern1 = parse_pattern("'a'")
        pattern1.id = 0
        pattern2 = parse_pattern("'a'...'a'")
        pattern2.predecessor_pattern = pattern1
        pattern2.is_leftmost_occurrence_update_required = False
        pattern2.id = 1
        patterns = [pattern1, pattern2]
        store = RightmostOccurrenceStore(
            [tree], VariantTransactionCountingStrategy(), 1, ef_dict
        )
        store.set_frequent_1_patterns([pattern1])
        store.update_occurrence_lists(patterns)

        self.assertEqual(tree.children[0], store.occurrence_lists[pattern1.id][0][0][0])
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern1.id][0][0][1])
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern1.id][0][0][2][0]
        )
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern1.id][0][1][0])
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern1.id][0][1][1])
        self.assertEqual(
            tree.children[1], store.occurrence_lists[pattern1.id][0][1][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern1.id][0][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern1.id][0][2][1]
        )
        self.assertEqual(
            tree.children[2].children[0],
            store.occurrence_lists[pattern1.id][0][2][2][0],
        )
        self.assertEqual(3, len(store.occurrence_lists[pattern1.id][0]))
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern2.id][0][0][0])
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern2.id][0][0][1]
        )
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern2.id][0][0][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0],
            store.occurrence_lists[pattern2.id][0][0][2][1],
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern2.id][0]))

    def test_pattern_occurrence_list_initialization_new_sub_pattern_2(self):
        tree = parse_concurrency_tree("→('a','a',∧('a','b'))")
        ef_dict = get_first_ef_node_id_per_node_for_trees([tree])

        pattern1 = parse_pattern("'a'")
        pattern1.id = 0
        pattern2 = parse_pattern("'b'")
        pattern1.id = 1
        pattern3 = parse_pattern("'a'...'b'")
        pattern3.predecessor_pattern = pattern1
        pattern3.is_leftmost_occurrence_update_required = False
        pattern3.id = 2

        patterns = [pattern1, pattern2, pattern3]
        store = RightmostOccurrenceStore(
            [tree], VariantTransactionCountingStrategy(), 1, ef_dict
        )
        store.set_frequent_1_patterns([pattern1, pattern2])
        store.update_occurrence_lists(patterns)

        self.assertEqual(tree.children[0], store.occurrence_lists[pattern1.id][0][0][0])
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern1.id][0][0][1])
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern1.id][0][0][2][0]
        )
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern1.id][0][1][0])
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern1.id][0][1][1])
        self.assertEqual(
            tree.children[1], store.occurrence_lists[pattern1.id][0][1][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern1.id][0][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0], store.occurrence_lists[pattern1.id][0][2][1]
        )
        self.assertEqual(
            tree.children[2].children[0],
            store.occurrence_lists[pattern1.id][0][2][2][0],
        )
        self.assertEqual(3, len(store.occurrence_lists[pattern1.id][0]))
        self.assertEqual(
            tree.children[2].children[1], store.occurrence_lists[pattern2.id][0][0][0]
        )
        self.assertEqual(
            tree.children[2].children[1], store.occurrence_lists[pattern2.id][0][0][1]
        )
        self.assertEqual(
            tree.children[2].children[1],
            store.occurrence_lists[pattern2.id][0][0][2][0],
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern2.id][0]))
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern3.id][0][0][0])
        self.assertEqual(
            tree.children[2].children[1], store.occurrence_lists[pattern3.id][0][0][1]
        )
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern3.id][0][0][2][0]
        )
        self.assertEqual(
            tree.children[2].children[1],
            store.occurrence_lists[pattern3.id][0][0][2][1],
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern3.id][0]))

    def test_pattern_occurrence_list_new_sub_pattern_with_single_node_sequential_operator(
        self,
    ):
        tree = parse_concurrency_tree("→('a','a',∧(→('a','b'), 'c'))")
        ef_dict = get_first_ef_node_id_per_node_for_trees([tree])

        pattern1 = parse_pattern("'a'")
        pattern1.id = 0
        pattern2 = parse_pattern("'b'")
        pattern2.id = 1
        pattern3 = parse_pattern("'a'...'b'")
        pattern3.predecessor_pattern = pattern1
        pattern3.is_leftmost_occurrence_update_required = False
        pattern3.id = 2
        pattern4 = parse_pattern("'a'...→('b')")
        pattern4.predecessor_pattern = pattern3
        pattern4.is_leftmost_occurrence_update_required = False
        pattern4.id = 3

        patterns = [pattern1, pattern2, pattern3, pattern4]
        store = RightmostOccurrenceStore(
            [tree], VariantTransactionCountingStrategy(), 1, ef_dict
        )
        store.set_frequent_1_patterns([pattern1, pattern2])
        store.update_occurrence_lists(patterns)

        self.assertEqual(tree.children[0], store.occurrence_lists[pattern1.id][0][0][0])
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern1.id][0][0][1])
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern1.id][0][0][2][0]
        )
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern1.id][0][1][0])
        self.assertEqual(tree.children[1], store.occurrence_lists[pattern1.id][0][1][1])
        self.assertEqual(
            tree.children[1], store.occurrence_lists[pattern1.id][0][1][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0].children[0],
            store.occurrence_lists[pattern1.id][0][2][0],
        )
        self.assertEqual(
            tree.children[2].children[0].children[0],
            store.occurrence_lists[pattern1.id][0][2][1],
        )
        self.assertEqual(
            tree.children[2].children[0].children[0],
            store.occurrence_lists[pattern1.id][0][2][2][0],
        )
        self.assertEqual(3, len(store.occurrence_lists[pattern1.id][0]))
        self.assertEqual(
            tree.children[2].children[0].children[1],
            store.occurrence_lists[pattern2.id][0][0][0],
        )
        self.assertEqual(
            tree.children[2].children[0].children[1],
            store.occurrence_lists[pattern2.id][0][0][1],
        )
        self.assertEqual(
            tree.children[2].children[0].children[1],
            store.occurrence_lists[pattern2.id][0][0][2][0],
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern2.id][0]))
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern3.id][0][0][0])
        self.assertEqual(
            tree.children[2].children[0].children[1],
            store.occurrence_lists[pattern3.id][0][0][1],
        )
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern3.id][0][0][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0].children[1],
            store.occurrence_lists[pattern3.id][0][0][2][1],
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern3.id][0]))
        self.assertEqual(tree.children[0], store.occurrence_lists[pattern4.id][0][0][0])
        self.assertEqual(
            tree.children[2].children[0].children[1],
            store.occurrence_lists[pattern4.id][0][0][1],
        )
        self.assertEqual(
            tree.children[0], store.occurrence_lists[pattern4.id][0][0][2][0]
        )
        self.assertEqual(
            tree.children[2].children[0],
            store.occurrence_lists[pattern4.id][0][0][2][1],
        )
        self.assertEqual(1, len(store.occurrence_lists[pattern4.id][0]))
