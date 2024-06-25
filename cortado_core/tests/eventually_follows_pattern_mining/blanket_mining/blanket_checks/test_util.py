import unittest

from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.util import (
    get_ef_labeled_nodes_left_of,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
)


class TestUtil(unittest.TestCase):
    def test_get_left_ef_predecessor_activities(self):
        tree = parse_concurrency_tree("→('a', 'b', 'c', 'd')")
        possible_nodes = get_ef_labeled_nodes_left_of(tree, tree.children[3], 0)
        self.assertEqual({"a", "b"}, set([l.label for l in possible_nodes]))

    def test_get_left_ef_predecessor_activities_with_stop(self):
        tree = parse_concurrency_tree("→('a', 'b', 'c', 'd')")
        possible_nodes = get_ef_labeled_nodes_left_of(tree, tree.children[3], 1)
        self.assertEqual({"b"}, set([l.label for l in possible_nodes]))

    def test_get_left_ef_predecessor_activities_nested_tree_1(self):
        tree = parse_concurrency_tree(
            "→('a',∧('b','c',→(∧('d','e'),'f')), 'g', 'h', ✕('i','j','k', 'l'))"
        )
        possible_nodes = get_ef_labeled_nodes_left_of(
            tree.children[2], tree.children[2], 0
        )
        self.assertEqual({"a", "d", "e"}, set([l.label for l in possible_nodes]))

    def test_get_left_ef_predecessor_activities_nested_tree_2(self):
        tree = parse_concurrency_tree(
            "→('a',∧('b','c',→(∧('d','e'),'f')), 'g', 'h', ✕('i','j','k', 'l'))"
        )
        possible_nodes = get_ef_labeled_nodes_left_of(
            tree.children[4], tree.children[4].children[0], 0
        )
        self.assertEqual(
            set([a for a in "abcdefg"]), set([l.label for l in possible_nodes])
        )

    def test_get_left_ef_predecessor_activities_nested_tree_3(self):
        tree = parse_concurrency_tree(
            "→('a','m',∧('b','c',→('n',∧('d','e'),'f')), 'g', 'h', ✕('i','j','k', 'l'))"
        )
        possible_nodes = get_ef_labeled_nodes_left_of(
            tree, tree.children[2].children[1], 0
        )
        self.assertEqual({"a"}, set([l.label for l in possible_nodes]))

    def test_get_left_ef_predecessor_activities_nested_tree_4(self):
        tree = parse_concurrency_tree(
            "→('a','m',∧('b','c',→('n',∧('d','e'),'f')), 'g', 'h', ✕('i','j','k', 'l'))"
        )
        possible_nodes = get_ef_labeled_nodes_left_of(
            tree.children[2].children[2].children[1],
            tree.children[2].children[2].children[1].children[0],
            0,
        )
        self.assertEqual({"a"}, set([l.label for l in possible_nodes]))
