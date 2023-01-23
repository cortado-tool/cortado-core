import unittest
from trace import Trace

from cortado_core.subprocess_discovery.concurrency_trees.parse_concurrency_tree import parse_concurrency_tree
from cortado_core.tiebreaker.algorithm import apply_tiebreaker, apply_tiebreaker_on_variants
from cortado_core.tiebreaker.pattern import parse_tiebreaker_pattern


class TestTiebreakerAlgorithm(unittest.TestCase):
    def test_algorithm_specific_match(self):
        variant = parse_concurrency_tree("+('b','c')")
        source_pattern = parse_tiebreaker_pattern("+('b','c')")
        target_pattern = parse_tiebreaker_pattern("->('b','c')")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(b, c)', str(new_variant))

    def test_algorithm_specific_match_on_lower_level_1(self):
        variant = parse_concurrency_tree("->('a', 'b', +('b','c', ->('d', +('b','c'))))")
        source_pattern = parse_tiebreaker_pattern("+('b','c')")
        target_pattern = parse_tiebreaker_pattern("->('b','c')")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(a, b, ∧(b, c, →(d, b, c)))', str(new_variant))

    def test_algorithm_specific_match_on_lower_level_2(self):
        variant = parse_concurrency_tree("->('a', 'b', +('b','c'))")
        source_pattern = parse_tiebreaker_pattern("+('b','c')")
        target_pattern = parse_tiebreaker_pattern("->('b','c')")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(a, b, b, c)', str(new_variant))

    def test_algorithm_no_specific_match(self):
        variant = parse_concurrency_tree("->('a', 'b', +('b','c','d'))")
        source_pattern = parse_tiebreaker_pattern("+('b','c')")
        target_pattern = parse_tiebreaker_pattern("->('b','c')")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(a, b, ∧(b, c, d))', str(new_variant))

    def test_algorithm_sub_specific_match(self):
        variant = parse_concurrency_tree("+('b','c','d')")
        source_pattern = parse_tiebreaker_pattern("+('b','c', ...)")
        target_pattern = parse_tiebreaker_pattern("->('b','c', ...)")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(b, c, d)', str(new_variant))

    def test_algorithm_sub_specific_match_add_in_between(self):
        variant = parse_concurrency_tree("+('b','c','d')")
        source_pattern = parse_tiebreaker_pattern("+('b','c', ...)")
        target_pattern = parse_tiebreaker_pattern("->('b',..., 'c')")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(b, d, c)', str(new_variant))

    def test_algorithm_sub_specific_match_on_lower_level(self):
        variant = parse_concurrency_tree("->('a', 'b', +('b','c','d'))")
        source_pattern = parse_tiebreaker_pattern("+('b','c', ...)")
        target_pattern = parse_tiebreaker_pattern("->('b','c', ...)")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(a, b, b, c, d)', str(new_variant))

    def test_algorithm_multiple_sub_specific_matches_on_lower_level(self):
        variant = parse_concurrency_tree("->('a', 'b', +('b','c','e','f', ->('d', +('b','c')))")
        source_pattern = parse_tiebreaker_pattern("+('b','c', ...)")
        target_pattern = parse_tiebreaker_pattern("->('b','c', ...)")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(a, b, b, c, ∧(e, f, →(d, b, c)))', str(new_variant))

    def test_algorithm_no_sub_specific_match(self):
        variant = parse_concurrency_tree("->('a', 'b', +('b','c','d'))")
        source_pattern = parse_tiebreaker_pattern("+('b','c', 'e' ...)")
        target_pattern = parse_tiebreaker_pattern("->('b','c', 'e', ...)")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(a, b, ∧(b, c, d))', str(new_variant))

    def test_algorithm_sub_specific_match_with_non_violating_parallel_construct(self):
        variant = parse_concurrency_tree("+('b','c','d')")
        source_pattern = parse_tiebreaker_pattern("+('b','c', ...)")
        target_pattern = parse_tiebreaker_pattern("+(->('b','c'), ...)")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('∧(→(b, c), d)', str(new_variant))

    def test_algorithm_sub_specific_match_with_violating_parallel_construct(self):
        variant = parse_concurrency_tree("+('b','c',->('d','e'))")
        source_pattern = parse_tiebreaker_pattern("+('b','c', ...)")
        target_pattern = parse_tiebreaker_pattern("+(->('b','c'), ...)")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('∧(b, c, →(d, e))', str(new_variant))

    def test_algorithm_specific_match_set_notation(self):
        variant = parse_concurrency_tree("+('b','c',->('d',+('b','c')))")
        source_pattern = parse_tiebreaker_pattern("+({'a','c'}, {'b'})")
        target_pattern = parse_tiebreaker_pattern("->({'a','c'}, {'b'})")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('∧(b, c, →(d, c, b))', str(new_variant))

    def test_algorithm_set_notation_matches_all_matching_nodes(self):
        variant = parse_concurrency_tree("+('b','c',->('d',+('b','c', 'c', 'c', 'c')))")
        source_pattern = parse_tiebreaker_pattern("+({'a','c'}, {'b'})")
        target_pattern = parse_tiebreaker_pattern("->({'a','c'}, {'b'})")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('∧(b, c, →(d, ∧(c, c, c, c), b))', str(new_variant))

    def test_algorithm_set_notation_matches_all_matching_nodes_2(self):
        variant = parse_concurrency_tree("+('b','c',->('d',+('b','b', 'c', 'c', 'c', 'c')))")
        source_pattern = parse_tiebreaker_pattern("+({'a','c'}, {'b'})")
        target_pattern = parse_tiebreaker_pattern("->({'a','c'}, {'b'})")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('∧(b, c, →(d, ∧(c, c, c, c), ∧(b, b)))', str(new_variant))

    def test_algorithm_no_specific_match_set_notation_1(self):
        variant = parse_concurrency_tree("+('b','c',->('d','e'))")
        source_pattern = parse_tiebreaker_pattern("+({'a','c'}, {'b'})")
        target_pattern = parse_tiebreaker_pattern("->({'a','c'}, {'b'})")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('∧(b, c, →(d, e))', str(new_variant))

    def test_algorithm_no_specific_match_set_notation_2(self):
        variant = parse_concurrency_tree("+('b','c', 'a', 'd','e'))")
        source_pattern = parse_tiebreaker_pattern("+({'a','c'}, {'b'})")
        target_pattern = parse_tiebreaker_pattern("->({'a','c'}, {'b'})")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('∧(b, c, a, d, e)', str(new_variant))

    def test_algorithm_specific_match_on_fallthrough(self):
        variant = parse_concurrency_tree("x('b','c')")
        source_pattern = parse_tiebreaker_pattern("+('b','c')")
        target_pattern = parse_tiebreaker_pattern("->('b','c')")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(b, c)', str(new_variant))

    def test_algorithm_no_specific_match_on_fallthrough(self):
        variant = parse_concurrency_tree("x('b','c', 'd')")
        source_pattern = parse_tiebreaker_pattern("+('b','c')")
        target_pattern = parse_tiebreaker_pattern("->('b','c')")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('✕(b, c, d)', str(new_variant))

    def test_algorithm_fallthrough_set_notation_match(self):
        variant = parse_concurrency_tree("+('a', 'b', x('c', 'd'))")
        source_pattern = parse_tiebreaker_pattern("+({'a','c'}, {'b','d'})")
        target_pattern = parse_tiebreaker_pattern("->({'a','c'}, {'b','d'})")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(∧(a, c), ∧(b, d))', str(new_variant))

    def test_sequence_when_matching_with_set_notation(self):
        variant = parse_concurrency_tree("+('a', 'b', ->('c', 'd'))")
        source_pattern = parse_tiebreaker_pattern("+({'a','c'}, {'b','d'}, ...)")
        target_pattern = parse_tiebreaker_pattern("->({'a','c'},..., {'b','d'})")

        new_variant = apply_tiebreaker(variant, source_pattern, target_pattern)

        self.assertEqual('→(a, c, d, b)', str(new_variant))

    def test_apply_on_variants(self):
        v1 = parse_concurrency_tree("+('a', 'b', ->('c', 'd'))").to_concurrency_group()
        v2 = parse_concurrency_tree("+('a', 'b', 'e', ->('c', 'd'))").to_concurrency_group()
        v3 = parse_concurrency_tree("->('a', 'b', 'e', 'c', 'd')").to_concurrency_group()
        v4 = parse_concurrency_tree("->('a', 'b', ->('e', 'c', 'd'))").to_concurrency_group()
        trace = Trace([])

        variants = {
            v1: [trace for _ in range(5)],
            v2: [trace for _ in range(10)],
            v3: [trace for _ in range(7)],
            v4: [trace for _ in range(1)]
        }

        source_pattern = parse_tiebreaker_pattern("+('a', 'b', ...)")
        target_pattern = parse_tiebreaker_pattern("->('a', 'b',...)")

        new_variants = apply_tiebreaker_on_variants(variants, source_pattern, target_pattern)

        self.assertEqual(5, len(
            new_variants[parse_concurrency_tree("->('a', 'b', 'c', 'd')").to_concurrency_group()]))
        self.assertEqual(10, len(
            new_variants[parse_concurrency_tree("->('a', 'b', +('e', ->('c', 'd')))").to_concurrency_group()]))
        self.assertEqual(8, len(
            new_variants[parse_concurrency_tree("->('a', 'b', 'e', 'c', 'd')").to_concurrency_group()]))
