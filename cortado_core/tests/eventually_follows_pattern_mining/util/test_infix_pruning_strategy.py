import unittest

from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.infix_sub_patterns_pruning_strategy import (
    InfixSubPatternsPruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator as ConcurrencyTreeOperator,
)


class TestLeftmostLeafRemover(unittest.TestCase):
    def test_remove_leftmost_leaf_single_node_leftmost_subpattern(self):
        subpattern1 = SubPattern(label="a", depth=0)
        subpattern2 = SubPattern(label="b", depth=0)
        # a...b
        pattern = EventuallyFollowsPattern(
            sub_patterns=[subpattern1, subpattern2], rightmost_leaf=subpattern1
        )

        remover = InfixSubPatternsPruningStrategy(dict())
        new_pattern, n_removed_nodes = remover.remove_sub_pattern(pattern, 0)

        self.assertNotEqual(pattern, new_pattern)
        self.assertEqual(1, len(new_pattern))
        self.assertEqual("b", new_pattern.sub_patterns[0].label)
        self.assertEqual(1, n_removed_nodes)

    def test_remove_leftmost_sub_pattern_single_sub_pattern(self):
        subpattern_child_child = SubPattern(label="a", depth=2)
        subpattern_child = SubPattern(
            operator=ConcurrencyTreeOperator.Concurrent,
            depth=1,
            children=[subpattern_child_child],
        )
        subpattern_root = SubPattern(
            operator=ConcurrencyTreeOperator.Sequential,
            depth=0,
            children=[subpattern_child],
        )
        subpattern_child_child.parent = subpattern_child
        subpattern_child.parent = subpattern_root
        # ->(+(a))
        pattern = EventuallyFollowsPattern(
            sub_patterns=[subpattern_root], rightmost_leaf=subpattern_child_child
        )

        remover = InfixSubPatternsPruningStrategy(dict())
        new_pattern, n_removed_nodes = remover.remove_sub_pattern(pattern, 0)

        self.assertEqual(0, n_removed_nodes)
        self.assertEqual(pattern, new_pattern)

    def test_remove_leftmost_sub_pattern_multiple_nodes(self):
        subpattern_child_child = SubPattern(label="a", depth=2)
        subpattern_child = SubPattern(
            operator=ConcurrencyTreeOperator.Concurrent,
            depth=1,
            children=[subpattern_child_child],
        )
        subpattern_root = SubPattern(
            operator=ConcurrencyTreeOperator.Sequential,
            depth=0,
            children=[subpattern_child],
        )
        subpattern_child_child.parent = subpattern_child
        subpattern_child.parent = subpattern_root
        b_pattern = SubPattern(label="b", depth=0)
        # ->(+(a))...b
        pattern = EventuallyFollowsPattern(
            sub_patterns=[subpattern_root, b_pattern], rightmost_leaf=b_pattern
        )

        remover = InfixSubPatternsPruningStrategy(dict())
        new_pattern, n_removed_nodes = remover.remove_sub_pattern(pattern, 0)

        self.assertEqual(3, n_removed_nodes)
        self.assertEqual("b", new_pattern.sub_patterns[0].label)
