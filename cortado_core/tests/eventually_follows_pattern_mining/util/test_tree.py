import unittest

from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    set_tree_attributes,
    get_lca,
    lca_is_sequential,
    is_eventually_follows_relation,
    get_first_ef_node_id_per_node,
    EventuallyFollowsStrategy,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator as ConcurrencyTreeOperator,
)


class TestTree(unittest.TestCase):
    def test_preorder_index(self):
        # ->('a','a', +('a', 'b'))
        root = ConcurrencyTree(op=ConcurrencyTreeOperator.Sequential)

        child3_root = ConcurrencyTree(
            op=ConcurrencyTreeOperator.Concurrent, parent=root
        )
        child3_child2 = ConcurrencyTree(label="b", parent=child3_root)
        child3_child1 = ConcurrencyTree(
            label="a", rSib=child3_child2, parent=child3_root
        )
        child3_root.children = [child3_child1, child3_child2]

        child2 = ConcurrencyTree(label="a", rSib=child3_root, parent=root)
        child1 = ConcurrencyTree(label="a", rSib=child2, parent=root)

        root.children = [child1, child2, child3_root]

        set_tree_attributes(root)

        self.assertEqual(0, root.id)
        self.assertEqual(1, root.children[0].id)
        self.assertEqual(2, root.children[1].id)
        self.assertEqual(3, root.children[2].id)
        self.assertEqual(4, root.children[2].children[0].id)
        self.assertEqual(5, root.children[2].children[1].id)

    def test_depth(self):
        # ->('a','a', +('a', 'b'))
        root = ConcurrencyTree(op=ConcurrencyTreeOperator.Sequential)

        child3_root = ConcurrencyTree(
            op=ConcurrencyTreeOperator.Concurrent, parent=root
        )
        child3_child2 = ConcurrencyTree(label="b", parent=child3_root)
        child3_child1 = ConcurrencyTree(
            label="a", rSib=child3_child2, parent=child3_root
        )
        child3_root.children = [child3_child1, child3_child2]

        child2 = ConcurrencyTree(label="a", rSib=child3_root, parent=root)
        child1 = ConcurrencyTree(label="a", rSib=child2, parent=root)

        root.children = [child1, child2, child3_root]

        set_tree_attributes(root)

        self.assertEqual(0, root.depth)
        self.assertEqual(1, root.children[0].depth)
        self.assertEqual(1, root.children[1].depth)
        self.assertEqual(1, root.children[2].depth)
        self.assertEqual(2, root.children[2].children[0].depth)
        self.assertEqual(2, root.children[2].children[1].depth)

    def test_get_lca(self):
        root = ConcurrencyTree(op=ConcurrencyTreeOperator.Sequential)

        child3_root = ConcurrencyTree(
            op=ConcurrencyTreeOperator.Concurrent, parent=root
        )
        child3_child2 = ConcurrencyTree(label="b", parent=child3_root)
        child3_child1 = ConcurrencyTree(
            label="a", rSib=child3_child2, parent=child3_root
        )
        child3_root.children = [child3_child1, child3_child2]

        child2 = ConcurrencyTree(label="a", rSib=child3_root, parent=root)
        child1 = ConcurrencyTree(label="a", rSib=child2, parent=root)
        root.children = [child1, child2, child3_root]

        set_tree_attributes(root)

        lca = get_lca(child1, child2)
        self.assertEqual(root, lca)
        self.assertTrue(lca_is_sequential(child1, child2))

        lca = get_lca(child1, child3_child2)
        self.assertEqual(root, lca)
        self.assertTrue(lca_is_sequential(child1, child3_child2))

        lca = get_lca(child3_child1, child3_child2)
        self.assertEqual(child3_root, lca)
        self.assertFalse(lca_is_sequential(child3_child1, child3_child2))

    def test_get_children_by_index(self):
        root = ConcurrencyTree(op=ConcurrencyTreeOperator.Sequential)
        child1 = ConcurrencyTree(label="a", parent=root)
        child2 = ConcurrencyTree(label="a", parent=root)
        root.children = [child1, child2]

        self.assertEqual(1, root.children.index(child2))

    def test_is_eventually_follows_relation(self):
        tree = parse_concurrency_tree("→('a','a',∧('a','b'))")
        single_node_occ = lambda t: (t, t, [t])

        self.assertTrue(
            is_eventually_follows_relation(
                single_node_occ(tree.children[0]), single_node_occ(tree.children[2])
            )
        )
        self.assertTrue(
            is_eventually_follows_relation(
                single_node_occ(tree.children[0]),
                single_node_occ(tree.children[2].children[0]),
            )
        )
        self.assertTrue(
            is_eventually_follows_relation(
                single_node_occ(tree.children[0]),
                single_node_occ(tree.children[2].children[1]),
            )
        )
        self.assertFalse(
            is_eventually_follows_relation(
                single_node_occ(tree.children[0]), single_node_occ(tree.children[1])
            )
        )
        self.assertFalse(
            is_eventually_follows_relation(
                single_node_occ(tree.children[1]), single_node_occ(tree.children[2])
            )
        )
        self.assertFalse(
            is_eventually_follows_relation(
                single_node_occ(tree.children[1]),
                single_node_occ(tree.children[2].children[0]),
            )
        )
        self.assertFalse(
            is_eventually_follows_relation(
                single_node_occ(tree.children[1]),
                single_node_occ(tree.children[2].children[1]),
            )
        )

    def test_is_eventually_follows_relation_complex_1(self):
        tree = parse_concurrency_tree("→('a',∧('b','c','d','e'))")

        # ->(a, +(b,c))
        left_occurrences = (tree.children[0], tree.children[1].children[1], [tree])
        # 'e'
        right_occurrences = (
            tree.children[1].children[3],
            tree.children[1].children[3],
            [tree.children[1].children[3]],
        )
        self.assertFalse(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_complex_2(self):
        tree = parse_concurrency_tree("→('a','b','c','d')")

        # ->(a, b)
        left_occurrences = (tree.children[0], tree.children[1], [tree])
        # 'd'
        right_occurrences = (tree.children[3], tree.children[3], [tree.children[3]])
        self.assertTrue(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_complex_3(self):
        tree = parse_concurrency_tree("→('a','b','c','d','e')")

        # ->(a, b)
        left_occurrences = (tree.children[0], tree.children[1], [tree])
        # ->('d','e')
        right_occurrences = (tree.children[3], tree.children[4], [tree])
        self.assertTrue(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_complex_4(self):
        tree = parse_concurrency_tree("∧('a',→(∧('b','c'),'d','e','f'))")

        # ∧('a',→(∧('b','c'),'d'))
        left_occurrences = (tree.children[0], tree.children[1].children[1], [tree])
        # 'f'
        right_occurrences = (
            tree.children[1].children[3],
            tree.children[1].children[3],
            [tree.children[1].children[3]],
        )
        self.assertFalse(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_complex_5(self):
        tree = parse_concurrency_tree("→(∧('b',→('a','c')), ∧('e',→('f','g')))")

        # →('a','c')
        left_occurrences = (
            tree.children[0].children[1].children[0],
            tree.children[0].children[1].children[1],
            [tree.children[0].children[1]],
        )
        # 'g'
        right_occurrences = (
            tree.children[1].children[1].children[1],
            tree.children[1].children[1].children[1],
            [tree.children[1].children[1].children[1]],
        )
        self.assertTrue(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_complex_6(self):
        tree = parse_concurrency_tree("→(∧('b',→('a','c')), ∧('e',→('f','g')))")

        # →('a','c')
        left_occurrences = (
            tree.children[0].children[1].children[0],
            tree.children[0].children[1].children[1],
            [tree.children[0].children[1]],
        )
        # 'f'
        right_occurrences = (
            tree.children[1].children[1].children[0],
            tree.children[1].children[1].children[0],
            [tree.children[1].children[1].children[0]],
        )
        self.assertFalse(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_ef_patterns(self):
        tree = parse_concurrency_tree("→('a','b','c','d','e','f','g')")

        # ->(a,b)...d
        left_occurrences = (tree.children[0], tree.children[3], [tree])
        # 'f'
        right_occurrences = (tree.children[-2], tree.children[-2], [tree.children[-2]])
        self.assertTrue(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_ef_patterns2(self):
        tree = parse_concurrency_tree("→('a','b','c','d','e','f','g')")

        # ->(a,b)...d
        left_occurrences = (tree.children[0], tree.children[3], [tree])
        # 'f'
        right_occurrences = (tree.children[-3], tree.children[-3], [tree.children[-3]])
        self.assertFalse(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_is_eventually_follows_relation_nested_pattern(self):
        tree = parse_concurrency_tree("→(∧('a',→('b','c','d')),'e','f')")
        # ∧(a,->(b,c)
        left_occurrences = (
            tree.children[0].children[0],
            tree.children[0].children[1].children[2],
            [tree.children[0]],
        )
        # ->(e,f)
        right_occurrences = (tree.children[0], tree.children[2], [tree])
        self.assertFalse(
            is_eventually_follows_relation(left_occurrences, right_occurrences)
        )

    def test_first_ef_nodes(self):  # 0 1  2  3  4   5   6     7   8
        tree = parse_concurrency_tree("→(∧('a',→('b','c','d')),'e','f')")
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.RealEventuallyFollows
        )

        self.assertFalse(0 in result)
        self.assertEqual(8, result[1])
        self.assertEqual(8, result[2])
        self.assertEqual(8, result[3])
        self.assertEqual(6, result[4])
        self.assertEqual(7, result[5])
        self.assertEqual(8, result[6])
        self.assertFalse(7 in result)
        self.assertFalse(8 in result)

    def test_first_ef_nodes_nested_sequential(self):
        #  0 1  2  3  4   5    6  7  8  9   10    11
        tree = parse_concurrency_tree("→(∧('a',→('b','c')),∧('d',→('e','f')),'g')")
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.RealEventuallyFollows
        )

        self.assertEqual(10, result[2])
        self.assertEqual(10, result[5])

    def test_first_ef_nodes_nested_sequential_2(self):
        tree = parse_concurrency_tree("→('a','b',∧('a',→('b','c')))")
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.RealEventuallyFollows
        )

        self.assertEqual(7, result[2])
        self.assertEqual(3, result[1])

    def test_large_tree(
        self,
    ):  # 0  1   2  3    4   5  6    7 8    9    10   11 12  13 14  15       16    17   18
        tree = parse_concurrency_tree(
            "→('a', ∧('b', 'c', →('d', ∧('e', 'f'), 'g', ∧('h', →('i', 'j')))), 'k', 'l', 'm')"
        )
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.RealEventuallyFollows
        )

        self.assertEqual(7, result[1])
        self.assertEqual(17, result[2])
        self.assertEqual(17, result[3])
        self.assertEqual(17, result[4])
        self.assertEqual(17, result[5])
        self.assertEqual(10, result[6])
        self.assertEqual(11, result[7])
        self.assertEqual(11, result[8])
        self.assertEqual(11, result[9])
        self.assertEqual(15, result[10])
        self.assertEqual(17, result[11])
        self.assertEqual(17, result[12])
        self.assertEqual(17, result[13])
        self.assertEqual(16, result[14])
        self.assertEqual(17, result[15])
        self.assertEqual(18, result[16])

    def test_first_ef_nodes_soft(self):  # 0 1  2  3  4   5   6     7   8
        tree = parse_concurrency_tree("→(∧('a',→('b','c','d')),'e','f')")
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.SoftEventuallyFollows
        )

        self.assertFalse(0 in result)
        self.assertEqual(7, result[1])
        self.assertEqual(7, result[2])
        self.assertEqual(7, result[3])
        self.assertEqual(5, result[4])
        self.assertEqual(6, result[5])
        self.assertEqual(7, result[6])
        self.assertEqual(8, result[7])
        self.assertFalse(8 in result)

    def test_first_ef_nodes_nested_sequential_soft(self):
        #  0 1  2  3  4   5    6  7  8  9   10    11
        tree = parse_concurrency_tree("→(∧('a',→('b','c')),∧('d',→('e','f')),'g')")
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.SoftEventuallyFollows
        )

        self.assertEqual(6, result[2])
        self.assertEqual(6, result[5])

    def test_first_ef_nodes_nested_sequential_2_soft(self):
        tree = parse_concurrency_tree("→('a','b',∧('a',→('b','c')))")
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.SoftEventuallyFollows
        )

        self.assertEqual(3, result[2])
        self.assertEqual(2, result[1])

    def test_large_tree_soft(
        self,
    ):  # 0  1   2  3    4   5  6    7 8    9    10   11 12  13 14  15       16    17   18
        tree = parse_concurrency_tree(
            "→('a', ∧('b', 'c', →('d', ∧('e', 'f'), 'g', ∧('h', →('i', 'j')))), 'k', 'l', 'm')"
        )
        result = get_first_ef_node_id_per_node(
            tree, EventuallyFollowsStrategy.SoftEventuallyFollows
        )

        self.assertEqual(2, result[1])
        self.assertEqual(16, result[2])
        self.assertEqual(16, result[3])
        self.assertEqual(16, result[4])
        self.assertEqual(16, result[5])
        self.assertEqual(7, result[6])
        self.assertEqual(10, result[7])
        self.assertEqual(10, result[8])
        self.assertEqual(10, result[9])
        self.assertEqual(11, result[10])
        self.assertEqual(16, result[11])
        self.assertEqual(16, result[12])
        self.assertEqual(16, result[13])
        self.assertEqual(15, result[14])
        self.assertEqual(16, result[15])
        self.assertEqual(17, result[16])
        self.assertEqual(18, result[17])
        self.assertFalse(18 in result)
