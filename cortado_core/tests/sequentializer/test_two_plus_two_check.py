import unittest

from cortado_core.subprocess_discovery.concurrency_trees.parse_concurrency_tree import (
    parse_concurrency_tree,
)
from cortado_core.sequentializer.pattern import (
    parse_sequentializer_pattern,
    set_preorder_ids,
)
from cortado_core.sequentializer.two_plus_two_free_check import (
    contains_possibly_violating_construct,
    can_apply_without_violating_two_plus_two_freeness,
)


class TestTwoPlusTwoCheck(unittest.TestCase):
    def test_target_pattern_contains_possibly_violating_construct(self):
        target_pattern = parse_sequentializer_pattern("+(->('a','b'), 'c', 'd', ...)")
        self.assertTrue(contains_possibly_violating_construct(target_pattern))

    def test_target_pattern_contains_possibly_violating_construct_in_parent_level(self):
        target_pattern = parse_sequentializer_pattern(
            "+(->(+('c', 'd', ...), 'b'), ->('a','b'))"
        )
        self.assertTrue(contains_possibly_violating_construct(target_pattern))

    def test_target_pattern_contains_only_concurrent_leaf_nodes(self):
        target_pattern = parse_sequentializer_pattern("+('a', 'b', 'c', 'd', ...)")
        self.assertFalse(contains_possibly_violating_construct(target_pattern))

    def test_target_pattern_has_sub_specific_match_node_in_outer_sequence(self):
        target_pattern = parse_sequentializer_pattern("->('a', 'b', ...,+('c', 'd'))")
        self.assertFalse(contains_possibly_violating_construct(target_pattern))

    def test_can_apply_without_violation(self):
        target_pattern = parse_sequentializer_pattern("+(->('a','b'), 'c', 'd', ...)")
        variant = parse_concurrency_tree("+('a', 'b', 'c', 'd', 'e', 'f')")
        set_preorder_ids(target_pattern)

        match = {
            target_pattern.children[-1].id: [variant.children[-2], variant.children[-1]]
        }

        target_to_source = {idx: idx for idx in range(10)}

        self.assertTrue(
            can_apply_without_violating_two_plus_two_freeness(
                target_pattern, match, target_to_source
            )
        )

    def test_cannot_apply_without_violation(self):
        target_pattern = parse_sequentializer_pattern("+(->('a','b'), 'c', 'd', ...)")
        variant = parse_concurrency_tree("+('a', 'b', 'c', 'd', ->('e', 'f'), 'g')")
        set_preorder_ids(target_pattern)

        match = {
            target_pattern.children[-1].id: [variant.children[-2], variant.children[-1]]
        }
        target_to_source = {idx: idx for idx in range(10)}

        self.assertFalse(
            can_apply_without_violating_two_plus_two_freeness(
                target_pattern, match, target_to_source
            )
        )
