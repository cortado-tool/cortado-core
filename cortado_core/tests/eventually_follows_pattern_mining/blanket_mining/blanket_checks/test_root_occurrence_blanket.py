import unittest

from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.root_occurrence_blanket import (
    __check_insertion_in_sub_patterns as check_insertion_in_sub_patterns,
    right_root_occurrence_blanket_contains_elements,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
    parse_pattern,
)


class TestRootOccurrenceBlanket(unittest.TestCase):
    def test_left_blanket_sequential_match(self):
        tree = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("→('b','c')")
        occurrence_list = {0: [[tree, tree.children[1], tree.children[2]]]}

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_left_blanket_sequential_match_with_violating_ef_constraint(self):
        tree = parse_concurrency_tree("→('a','b','c','d')")
        pattern = parse_pattern("'a'...→('c','d')")
        occurrence_list = {
            0: [[tree.children[0], tree, tree.children[2], tree.children[3]]]
        }

        self.assertFalse(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_left_blanket_sequential_match_with_different_label_matches(self):
        tree1 = parse_concurrency_tree("→('a','b','c','d')")
        tree2 = parse_concurrency_tree("→('a','c','c','d')")
        pattern = parse_pattern("→('c','d')")
        occurrence_list = {
            0: [[tree1, tree1.children[2], tree1.children[3]]],
            1: [[tree2, tree2.children[2], tree2.children[3]]],
        }

        self.assertFalse(check_insertion_in_sub_patterns(pattern, occurrence_list))

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

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list))

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

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_left_blanket_concurrent_match(self):
        tree = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('b','c')")
        occurrence_list = {0: [[tree, tree.children[1], tree.children[2]]]}

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_left_blanket_concurrent_match_in_between(self):
        tree = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('a','c')")
        occurrence_list = {0: [[tree, tree.children[0], tree.children[2]]]}

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_left_blanket_concurrent_no_match(self):
        tree = parse_concurrency_tree("∧('a','b','c','d')")
        pattern = parse_pattern("∧('a','b')")
        occurrence_list = {0: [[tree, tree.children[0], tree.children[1]]]}

        self.assertFalse(check_insertion_in_sub_patterns(pattern, occurrence_list))

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

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_left_blanket_concurrent_multiple_trees_with_different_label_matches(self):
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

        self.assertTrue(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_left_blanket_concurrent_multiple_trees_without_matching(self):
        tree1 = parse_concurrency_tree("→(∧('a','b','c','d'), ∧('a','b','e', 'd'))")
        tree2 = parse_concurrency_tree("∧('a','b','f','d')")
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

        self.assertFalse(check_insertion_in_sub_patterns(pattern, occurrence_list))

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

        self.assertFalse(check_insertion_in_sub_patterns(pattern, occurrence_list))

    def test_right_occurrence_blanket_contains_elements_with_match(self):
        tree1 = parse_concurrency_tree("→(∧('a','b','c','d'), ∧('a','b','e', 'd'))")
        tree2 = parse_concurrency_tree("∧('a','b','f','d')")
        pattern = parse_pattern("∧('a','b')")
        occurrence_list = {
            0: [
                [tree1, tree1.children[0].children[0], tree1.children[0].children[1]],
                [tree1, tree1.children[1].children[0], tree1.children[1].children[1]],
            ],
            1: [[tree2, tree2.children[0], tree2.children[1]]],
        }

        self.assertTrue(
            right_root_occurrence_blanket_contains_elements(pattern, occurrence_list)
        )

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

        self.assertFalse(
            right_root_occurrence_blanket_contains_elements(pattern, occurrence_list)
        )

    def test_right_occurrence_blanket_sequential_match_on_subset_of_occurrences(self):
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

        self.assertTrue(
            right_root_occurrence_blanket_contains_elements(pattern, occurrence_list)
        )

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

        self.assertTrue(
            right_root_occurrence_blanket_contains_elements(pattern, occurrence_list)
        )

    def test_right_occurrence_blanket_no_match(self):
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

        self.assertFalse(
            right_root_occurrence_blanket_contains_elements(pattern, occurrence_list)
        )

    def test_right_occurrence_blanket_no_match_for_second_occurrence(self):
        tree = parse_concurrency_tree("→('a','b','c','c','a')")
        pattern = parse_pattern("'a'")
        occurrence_list = {0: [[tree.children[0]], [tree.children[-1]]]}

        self.assertFalse(
            right_root_occurrence_blanket_contains_elements(pattern, occurrence_list)
        )
