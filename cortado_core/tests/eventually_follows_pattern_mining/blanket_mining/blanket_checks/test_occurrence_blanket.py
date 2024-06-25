import unittest

from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.occurrence_blanket import (
    __check_left_blanket_insertion_in_sub_patterns as check_insertion_in_sub_patterns,
    right_occurrence_blanket_contains_elements,
    __check_inner_node_insertions_on_rightmost_path as check_inner_node_insertions_on_rightmost_path,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
    parse_pattern,
)


class TestOccurrenceBlanket(unittest.TestCase):
    def test_left_blanket_sequential_match(self):
        tree = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("→('b','c')")
        occurrence_list = {0: [[tree, tree.children[1], tree.children[2]]]}

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list, True))

    def test_left_blanket_sequential_match_with_violating_ef_constraint(self):
        tree = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("'a'...→('c','d')")
        occurrence_list = {
            0: [[tree.children[0], tree, tree.children[2], tree.children[3]]]
        }

        self.assertFalse(
            check_insertion_in_sub_patterns(pattern, occurrence_list, True)
        )

    def test_left_blanket_sequential_match_with_different_label_matches(self):
        tree1 = parse_concurrency_tree("→('a','b','c','d')")
        tree2 = parse_concurrency_tree("→('a','c','c','d')")
        pattern = parse_pattern("→('c','d')")
        occurrence_list = {
            0: [[tree1, tree1.children[2], tree1.children[3]]],
            1: [[tree2, tree2.children[2], tree2.children[3]]],
        }

        self.assertFalse(
            check_insertion_in_sub_patterns(pattern, occurrence_list, True)
        )

    def test_left_blanket_sequential_match_multiple_occurrences(self):
        tree1 = parse_concurrency_tree("→('a','b','c','d','b','c','d')")
        tree2 = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("→('c','d')")
        occurrence_list = {
            0: [
                [tree1, tree1.children[2], tree1.children[3]],
                [tree1, tree1.children[5], tree1.children[6]],
            ],
            1: [[tree2, tree2.children[2], tree2.children[3]]],
        }

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list, True))

    def test_left_blanket_sequential_match_multiple_occurrences_with_different_label_matches(
        self,
    ):
        tree1 = parse_concurrency_tree("→('a','b','c','d','f','c','d')")
        tree2 = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("→('c','d')")
        occurrence_list = {
            0: [
                [tree1, tree1.children[2], tree1.children[3]],
                [tree1, tree1.children[5], tree1.children[6]],
            ],
            1: [[tree2, tree2.children[2], tree2.children[3]]],
        }

        self.assertFalse(
            check_insertion_in_sub_patterns(pattern, occurrence_list, True)
        )

    def test_left_blanket_concurrent_match(self):
        tree = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('b','c')")
        occurrence_list = {0: [[tree, tree.children[1], tree.children[2]]]}

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list, True))

    def test_left_blanket_concurrent_match_in_between(self):
        tree = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('a','c')")
        occurrence_list = {0: [[tree, tree.children[0], tree.children[2]]]}

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list, True))

    def test_left_blanket_concurrent_no_match(self):
        tree = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('a','b')")
        occurrence_list = {0: [[tree, tree.children[0], tree.children[1]]]}

        self.assertFalse(
            check_insertion_in_sub_patterns(pattern, occurrence_list, True)
        )

    def test_left_blanket_concurrent_multiple_trees_with_match(self):
        tree1 = parse_concurrency_tree(
            "→(∧('a','b','c','d'), ∧('a','b','c', 'c', 'd'))"
        )
        tree2 = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('a','b','d')")
        occurrence_list = {
            0: [
                [
                    tree1,
                    tree1.children[0].children[0],
                    tree1.children[0].children[1],
                    tree1.children[0].children[3],
                ],
                [
                    tree1,
                    tree1.children[0].children[1],
                    tree1.children[1].children[1],
                    tree1.children[1].children[3],
                ],
            ],
            1: [[tree2, tree2.children[0], tree2.children[1], tree2.children[3]]],
        }

        self.assertTrue(
            check_insertion_in_sub_patterns(pattern, occurrence_list, False)
        )

    def test_left_blanket_concurrent_multiple_trees_without_match(self):
        tree1 = parse_concurrency_tree("→(∧('a','b','c','d'), ∧('a','b','e', 'd'))")
        tree2 = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('a','b','d')")
        occurrence_list = {
            0: [
                [
                    tree1,
                    tree1.children[0].children[0],
                    tree1.children[0].children[1],
                    tree1.children[0].children[3],
                ],
                [
                    tree1,
                    tree1.children[1].children[0],
                    tree1.children[1].children[1],
                    tree1.children[1].children[3],
                ],
            ],
            1: [[tree2, tree2.children[0], tree2.children[1], tree2.children[3]]],
        }

        self.assertFalse(
            check_insertion_in_sub_patterns(pattern, occurrence_list, False)
        )

    def test_left_blanket_sequential_completeness_violated(self):
        tree1 = parse_concurrency_tree("→('a',∧('b',→('c','d','e')))")
        tree2 = parse_concurrency_tree("→('a',∧('b',→('d','e')))")
        pattern = parse_pattern("→(∧('b',→('d','e')))")
        occurrence_list = {
            0: [
                [
                    tree1,
                    tree1.children[1],
                    tree1.children[1].children[0],
                    tree1.children[1].children[1],
                    tree1.children[1].children[1].children[1],
                    tree1.children[1].children[1].children[2],
                ]
            ],
            1: [
                [
                    tree2,
                    tree2.children[1],
                    tree2.children[1].children[0],
                    tree2.children[1].children[1],
                    tree2.children[1].children[1].children[0],
                    tree2.children[1].children[1].children[1],
                ]
            ],
        }

        self.assertFalse(
            check_insertion_in_sub_patterns(pattern, occurrence_list, True)
        )

    def test_right_occurrence_blanket_contains_elements_with_match(self):
        tree1 = parse_concurrency_tree("→(∧('a','b','c','d'), ∧('a','b','e', 'd'))")
        tree2 = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('a','b')")
        occurrence_list = {
            0: [
                [tree1, tree1.children[0].children[0], tree1.children[0].children[1]],
                [tree1, tree1.children[1].children[0], tree1.children[1].children[1]],
            ],
            1: [[tree2, tree2.children[0], tree2.children[1]]],
        }

        (
            contains_element,
            height_diff,
            create_new_sp,
        ) = right_occurrence_blanket_contains_elements(pattern, occurrence_list)
        self.assertTrue(contains_element)
        self.assertEqual(0, height_diff)
        self.assertFalse(create_new_sp)

    def test_right_occurrence_blanket_contains_elements_without_match(self):
        tree1 = parse_concurrency_tree("→(∧('a','b','c','d'), ∧('a','b','e', 'd'))")
        tree2 = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('c','d')")
        occurrence_list = {
            0: [
                [tree1, tree1.children[0].children[2], tree1.children[0].children[3]],
                [tree1, tree1.children[1].children[2], tree1.children[1].children[3]],
            ],
            1: [[tree2, tree2.children[2], tree2.children[3]]],
        }

        (
            contains_element,
            height_diff,
            create_new_sp,
        ) = right_occurrence_blanket_contains_elements(pattern, occurrence_list)
        self.assertFalse(contains_element)
        self.assertEqual(1, height_diff)
        self.assertTrue(create_new_sp)

    def test_right_occurrence_blanket_sequential_match_not_given(self):
        tree1 = parse_concurrency_tree("→('a','b','c','d', 'b', 'c', 'e')")
        tree2 = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("→('b','c')")
        occurrence_list = {
            0: [
                [tree1, tree1.children[1], tree1.children[2]],
                [tree1, tree1.children[4], tree1.children[5]],
            ],
            1: [[tree2, tree2.children[1], tree2.children[2]]],
        }

        (
            contains_element,
            height_diff,
            create_new_sp,
        ) = right_occurrence_blanket_contains_elements(pattern, occurrence_list)
        self.assertFalse(contains_element)
        self.assertEqual(1, height_diff)
        self.assertTrue(create_new_sp)

    def test_right_occurrence_blanket_sequential_match_given(self):
        tree1 = parse_concurrency_tree("→('a','b','c','d', 'b', 'c', 'd')")
        tree2 = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("→('b','c')")
        occurrence_list = {
            0: [
                [tree1, tree1.children[1], tree1.children[2]],
                [tree1, tree1.children[4], tree1.children[5]],
            ],
            1: [[tree2, tree2.children[1], tree2.children[2]]],
        }

        (
            contains_element,
            height_diff,
            create_new_sp,
        ) = right_occurrence_blanket_contains_elements(pattern, occurrence_list)
        self.assertTrue(contains_element)
        self.assertEqual(0, height_diff)
        self.assertTrue(create_new_sp)

    def test_right_occurrence_blanket_no_eventually_follows_match(self):
        tree1 = parse_concurrency_tree("→('a',∧('b',→('c','d','e')), 'f')")
        tree2 = parse_concurrency_tree("→('a',∧('b',→('c','d','g')), 'f')")
        pattern = parse_pattern("→('a',∧('b',→('c','d')")
        occurrence_list = {
            0: [
                [
                    tree1,
                    tree1.children[0],
                    tree1.children[1],
                    tree1.children[1].children[0],
                    tree1.children[1].children[1],
                    tree1.children[1].children[1].children[0],
                    tree1.children[1].children[1].children[1],
                ]
            ],
            1: [
                [
                    tree2,
                    tree2.children[0],
                    tree2.children[1],
                    tree2.children[1].children[0],
                    tree2.children[1].children[1],
                    tree2.children[1].children[1].children[0],
                    tree2.children[1].children[1].children[1],
                ]
            ],
        }

        (
            contains_element,
            height_diff,
            create_new_sp,
        ) = right_occurrence_blanket_contains_elements(pattern, occurrence_list)
        self.assertFalse(contains_element)
        self.assertEqual(3, height_diff)
        self.assertTrue(create_new_sp)

    def test_right_occurrence_blanket_children_match_on_rml(self):
        tree1 = parse_concurrency_tree("→('b', 'c')")
        tree2 = parse_concurrency_tree("→('a', 'c')")
        pattern = parse_pattern("→()")
        occurrence_list = {
            0: [[tree1, tree1.children[0], tree1.children[1]]],
            1: [[tree2, tree2.children[0], tree2.children[1]]],
        }

        (
            contains_element,
            height_diff,
            create_new_sp,
        ) = right_occurrence_blanket_contains_elements(pattern, occurrence_list)
        self.assertTrue(contains_element)
        self.assertEqual(-1, height_diff)
        self.assertTrue(create_new_sp)

    def test_right_occurrence_blanket_looks_for_sequential_completeness(self):
        tree1 = parse_concurrency_tree("→('b', ∧('a', →('c','d')))")
        tree2 = parse_concurrency_tree("→('b', ∧('a', →('b','d')))")
        pattern = parse_pattern("→('b', ∧('a', →()))")
        occurrence_list = {
            0: [
                [
                    tree1,
                    tree1.children[0],
                    tree1.children[1],
                    tree1.children[1].children[0],
                    tree1.children[1].children[1],
                ]
            ],
            1: [
                [
                    tree2,
                    tree2.children[0],
                    tree2.children[1],
                    tree2.children[1].children[0],
                    tree2.children[1].children[1],
                ]
            ],
        }

        (
            contains_element,
            height_diff,
            _,
        ) = check_inner_node_insertions_on_rightmost_path(
            pattern, occurrence_list, True
        )
        self.assertFalse(contains_element)
        self.assertEqual(1, height_diff)

    def test_right_occurrence_blanket_create_new_sub_patterns_if_sequential_occ_match(
        self,
    ):
        tree1 = parse_concurrency_tree("→('a','b','c',∧('d','e'))")
        tree2 = parse_concurrency_tree("→('a','b','c',∧('d','f'))")
        pattern = parse_pattern("→('a','b')")
        occurrence_list = {
            0: [[tree1, tree1.children[0], tree1.children[1]]],
            1: [[tree2, tree2.children[0], tree2.children[1]]],
        }

        (
            contains_element,
            height_diff,
            create_new_sp,
        ) = check_inner_node_insertions_on_rightmost_path(
            pattern, occurrence_list, True
        )
        self.assertTrue(contains_element)
        self.assertEqual(0, height_diff)
        self.assertTrue(create_new_sp)
