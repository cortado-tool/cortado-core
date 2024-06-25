import unittest

from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.pruning_strategy import (
    PruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.rightmost_expansion import (
    RightmostExpansionCandidateGenerator,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_pattern,
    parse_sub_pattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator as ConcurrencyTreeOperator,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequentActivitySets


class MockPruningStrategy(PruningStrategy):
    def can_prune(self, candidate: EventuallyFollowsPattern, iteration: int) -> bool:
        return False


class TestRightExpansion(unittest.TestCase):
    def test_initial_pattern_generation(self):
        frequent_activities = {"a", "b", "c", "d"}
        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        patterns = generator.generate_initial_candidates()
        self.assertEqual(len(patterns), 7)

        for pattern in patterns:
            self.assertEqual(len(pattern), 1)
            self.assertEqual(len(pattern.sub_patterns[0].children), 0)
            self.assertEqual(pattern.predecessor_pattern, None)
            self.assertTrue(pattern.is_leftmost_occurrence_update_required)

    def test_generate_new_patterns_with_additional_subpattern(self):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.iteration = 2
        generator.set_frequent_1_patterns(frequent_1_patterns)
        init_pattern = parse_pattern("'a'")

        patterns = generator.generate_new_candidates_with_additional_subpattern(
            init_pattern
        )
        self.assertEqual(len(patterns), 2)

        for pattern in patterns:
            # ensure that we do not add new sequential operator nodes
            self.assertEqual(None, pattern.sub_patterns[-1].operator)
            self.assertEqual(len(pattern), 2)
            self.assertEqual(len(pattern.sub_patterns[0].children), 0)
            self.assertEqual(len(pattern.sub_patterns[1].children), 0)
            self.assertEqual(pattern.predecessor_pattern, init_pattern)
            self.assertEqual(0, pattern.height_diff)
            self.assertFalse(pattern.is_leftmost_occurrence_update_required)

    def test_generate_no_new_patterns_with_additional_subpattern_for_incomplete_prefixes_nested(
        self,
    ):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.set_frequent_1_patterns(frequent_1_patterns)
        generator.iteration = 7
        init_pattern = parse_pattern("→('a', →(∧('a','a')))")

        patterns = generator.generate_new_candidates_with_additional_subpattern(
            init_pattern
        )
        self.assertEqual(0, len(patterns))

    def test_generate_no_new_patterns_with_additional_subpattern_for_incomplete_prefixes(
        self,
    ):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.set_frequent_1_patterns(frequent_1_patterns)
        generator.iteration = 2

        init_pattern = parse_pattern("∧()")

        patterns = generator.generate_new_candidates_with_additional_subpattern(
            init_pattern
        )
        self.assertEqual(0, len(patterns))

    def test_generate_no_new_patterns_with_additional_subpattern_for_incomplete_prefixes_2(
        self,
    ):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.iteration = 3
        generator.set_frequent_1_patterns(frequent_1_patterns)
        init_pattern = parse_pattern("∧('a')")

        patterns = generator.generate_new_candidates_with_additional_subpattern(
            init_pattern
        )
        self.assertEqual(0, len(patterns))

    def test_generate_right_expansion_patterns_no_operator_node(self):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.iteration = 2
        generator.set_frequent_1_patterns(frequent_1_patterns)

        pattern = parse_pattern("'a'")

        patterns = generator.generate_right_expansion_candidates(pattern)
        self.assertEqual(len(patterns), 0)

    def test_generate_right_expansion_patterns_single_operator_node(self):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.iteration = 2
        generator.set_frequent_1_patterns(frequent_1_patterns)

        init_pattern = parse_pattern("→()")

        patterns = generator.generate_right_expansion_candidates(init_pattern)
        self.assertEqual(len(patterns), 2)

        for pattern in patterns:
            self.assertEqual(len(pattern), 1)
            self.assertEqual(len(pattern.sub_patterns[0].children), 1)
            self.assertEqual(pattern.predecessor_pattern, init_pattern)
            self.assertEqual(-1, pattern.height_diff)
            self.assertTrue(pattern.is_leftmost_occurrence_update_required)

    def test_generate_right_expansion_patterns_multiple_sub_patterns(self):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]
        frequent_2_patterns = set(
            [
                parse_pattern(p)
                for p in [
                    "∧('a')",
                    "∧('b')",
                    "∧(→())",
                    "'a'...'b'",
                    "'b'...∧()",
                    "'a'...∧()",
                ]
            ]
        )

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.iteration = 4
        generator.set_frequent_1_patterns(frequent_1_patterns)
        generator.set_frequent_2_patterns(frequent_2_patterns)

        pattern = parse_pattern("'a'...'b'...∧()")
        pattern.is_leftmost_occurrence_update_required = False

        patterns = generator.generate_right_expansion_candidates(pattern)
        self.assertEqual(len(patterns), 2)

        for new_pattern in patterns:
            self.assertEqual(len(new_pattern), 3)
            self.assertEqual(new_pattern.sub_patterns[0].label, "a")
            self.assertEqual(new_pattern.sub_patterns[1].label, "b")
            self.assertEqual(len(new_pattern.sub_patterns[2].children), 1)
            self.assertEqual(new_pattern.predecessor_pattern, pattern)
            self.assertEqual(-1, new_pattern.height_diff)
            self.assertFalse(new_pattern.is_leftmost_occurrence_update_required)

    def test_generate_right_expansion_patterns_multiple_sub_patterns_with_nested_last_pattern(
        self,
    ):
        frequent_activities = {"a", "b"}

        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]
        frequent_2_patterns = set(
            [
                parse_pattern(p)
                for p in [
                    "∧('a')",
                    "∧('b')",
                    "∧(→())",
                    "'a'...'b'",
                    "'b'...∧()",
                    "'a'...∧()",
                ]
            ]
        )

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.iteration = 3
        generator.set_frequent_1_patterns(frequent_1_patterns)
        generator.set_frequent_2_patterns(frequent_2_patterns)

        pattern = parse_pattern("'a'...∧('a')")
        pattern.is_leftmost_occurrence_update_required = False

        patterns = generator.generate_right_expansion_candidates(pattern)
        self.assertEqual(3, len(patterns))

        for new_pattern in patterns:
            self.assertEqual(len(new_pattern), 2)
            self.assertEqual(new_pattern.sub_patterns[0].label, "a")
            self.assertEqual(
                new_pattern.sub_patterns[1].operator, ConcurrencyTreeOperator.Concurrent
            )
            self.assertEqual(new_pattern.sub_patterns[1].children[0].label, "a")
            self.assertEqual(0, new_pattern.height_diff)
            self.assertFalse(new_pattern.is_leftmost_occurrence_update_required)

        self.assertEqual(
            {"a", "b", None}, {p.sub_patterns[1].children[1].label for p in patterns}
        )
        self.assertEqual(
            {ConcurrencyTreeOperator.Sequential, None},
            {p.sub_patterns[1].children[1].operator for p in patterns},
        )

    def test_generate_right_expansion_patterns_multiple_sub_patterns_with_nested_last_pattern_2(
        self,
    ):
        frequent_activities = {"a", "b"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
        ]
        frequent_2_patterns = set(
            [
                parse_pattern(p)
                for p in ["∧('a')", "∧('b')", "∧(→())", "→('a')", "∧('a')", "'a'...→()"]
            ]
        )

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.set_frequent_1_patterns(frequent_1_patterns)
        generator.set_frequent_2_patterns(frequent_2_patterns)
        generator.iteration = 4
        pattern = parse_pattern("'a'...→('a', ∧())")
        pattern.is_leftmost_occurrence_update_required = False

        patterns = generator.generate_right_expansion_candidates(pattern)
        self.assertEqual(2, len(patterns))

        for new_pattern in patterns:
            self.assertEqual(len(new_pattern), 2)
            self.assertEqual(-1, new_pattern.height_diff)
            self.assertFalse(new_pattern.is_leftmost_occurrence_update_required)

        depth1_patterns = [
            p for p in patterns if self.__get_depth_of_rml(p.rightmost_leaf) == 1
        ]
        depth2_patterns = [
            p for p in patterns if self.__get_depth_of_rml(p.rightmost_leaf) == 2
        ]
        self.assertEqual(0, len(depth1_patterns))
        self.assertEqual(2, len(depth2_patterns))

        self.assertEqual(
            {"a", "b"},
            {p.sub_patterns[1].children[1].children[0].label for p in depth2_patterns},
        )

    def test_generate_right_expansion_patterns_multiple_sub_patterns_with_nested_last_pattern_3(
        self,
    ):
        frequent_activities = {"a", "b", "c", "d"}
        frequent_1_patterns = [
            parse_sub_pattern("'a'"),
            parse_sub_pattern("'b'"),
            parse_sub_pattern("→()"),
            parse_sub_pattern("∧()"),
        ]
        frequent_2_patterns = set(
            [
                parse_pattern(p)
                for p in [
                    "∧('a')",
                    "→('a')",
                    "→('b')",
                    "→(∧())",
                    "'a'...'b'",
                    "'a'...∧()",
                ]
            ]
        )
        frequent_3_patterns = set(
            [parse_pattern(p) for p in ["→('b', 'a')", "→('b', 'b')", "→('b', ∧())"]]
        )

        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets(frequent_activities), MockPruningStrategy()
        )
        generator.set_frequent_1_patterns(frequent_1_patterns)
        generator.set_frequent_2_patterns(frequent_2_patterns)
        generator.set_frequent_3_patterns(frequent_3_patterns)
        generator.iteration = 7
        pattern = parse_pattern("'a'...∧('a', →('a','b'))")
        pattern.is_leftmost_occurrence_update_required = False

        patterns = generator.generate_right_expansion_candidates(pattern)
        self.assertEqual(3, len(patterns))

        for new_pattern in patterns:
            self.assertEqual(len(new_pattern), 2)
            self.assertFalse(new_pattern.is_leftmost_occurrence_update_required)

        depth1_patterns = [
            p for p in patterns if self.__get_depth_of_rml(p.rightmost_leaf) == 1
        ]
        depth2_patterns = [
            p for p in patterns if self.__get_depth_of_rml(p.rightmost_leaf) == 2
        ]
        self.assertEqual(0, len(depth1_patterns))
        self.assertEqual(3, len(depth2_patterns))

        for depth2_pattern in depth2_patterns:
            self.assertEqual(0, depth2_pattern.height_diff)

        self.assertEqual(
            {"a", "b", None},
            {p.sub_patterns[1].children[1].children[2].label for p in depth2_patterns},
        )
        self.assertEqual(
            {ConcurrencyTreeOperator.Concurrent, None},
            {
                p.sub_patterns[1].children[1].children[2].operator
                for p in depth2_patterns
            },
        )

    def test_generate_new_sequential_root_single_child_patterns_length_one_pattern(
        self,
    ):
        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets({"a", "b"}), MockPruningStrategy()
        )

        init_pattern = parse_pattern("'a'")

        patterns = generator.generate_sequential_ef_extension_patterns(init_pattern)
        self.assertEqual(0, len(patterns))

    def test_generate_new_sequential_root_single_child_patterns_nested_last_sub_pattern(
        self,
    ):
        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets({"a", "b"}), MockPruningStrategy()
        )

        init_pattern = parse_pattern("'a'...∧('b')")

        patterns = generator.generate_sequential_ef_extension_patterns(init_pattern)
        self.assertEqual(0, len(patterns))

    def test_generate_new_sequential_root_single_child_patterns_single_label_child(
        self,
    ):
        frequent_2_patterns = set([parse_pattern(p) for p in ["→('b')"]])
        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets({"a", "b"}), MockPruningStrategy()
        )
        generator.set_frequent_2_patterns(frequent_2_patterns)

        init_pattern = parse_pattern("'a'...'b'")

        patterns = generator.generate_sequential_ef_extension_patterns(init_pattern)
        self.assertEqual(1, len(patterns))
        self.assertEqual(
            ConcurrencyTreeOperator.Sequential, patterns[0].sub_patterns[-1].operator
        )
        self.assertEqual("b", patterns[0].sub_patterns[-1].children[0].label)
        self.assertEqual("b", patterns[0].rightmost_leaf.label)
        self.assertEqual(0, patterns[0].height_diff)
        self.assertFalse(patterns[0].is_leftmost_occurrence_update_required)

    def test_generate_new_sequential_root_single_child_patterns_single_label_operator(
        self,
    ):
        frequent_2_patterns = set(
            [parse_pattern(p) for p in ["'a'...✕()", "→('a')", "→('b')", "→(✕())"]]
        )
        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets({"a", "b"}), MockPruningStrategy()
        )
        generator.set_frequent_2_patterns(frequent_2_patterns)

        init_pattern = parse_pattern("'a'...✕()")

        patterns = generator.generate_sequential_ef_extension_patterns(init_pattern)
        self.assertEqual(1, len(patterns))
        self.assertEqual(
            ConcurrencyTreeOperator.Sequential, patterns[0].sub_patterns[-1].operator
        )
        self.assertEqual(
            ConcurrencyTreeOperator.Fallthrough,
            patterns[0].sub_patterns[-1].children[0].operator,
        )
        self.assertEqual(
            ConcurrencyTreeOperator.Fallthrough, patterns[0].rightmost_leaf.operator
        )
        self.assertEqual(0, patterns[0].height_diff)
        self.assertFalse(patterns[0].is_leftmost_occurrence_update_required)

    def test_generate_new_sequential_root_single_child_patterns_single_label_operator_infrequent(
        self,
    ):
        frequent_2_patterns = set(
            [parse_pattern(p) for p in ["'a'...✕()", "→('a')", "→('b')"]]
        )
        generator = RightmostExpansionCandidateGenerator(
            self.__get_default_prune_sets({"a", "b"}), MockPruningStrategy()
        )
        generator.set_frequent_2_patterns(frequent_2_patterns)

        init_pattern = parse_pattern("'a'...✕()")

        patterns = generator.generate_sequential_ef_extension_patterns(init_pattern)
        self.assertEqual(0, len(patterns))

    def test_relation_prune(self):
        pattern = parse_pattern("→(∧('a',→(∧('b','c'),∧('d','e'))))")
        freq_act_sets = FrequentActivitySets(
            fA={"a", "b", "c", "d", "e"},
            dfR={"a": {"a", "d"}, "d": {"a", "b"}, "e": {"a", "d"}},
            efR={"b": {"a", "b"}, "c": {"a", "d"}},
            ccR=dict(),
        )
        generator = RightmostExpansionCandidateGenerator(
            freq_act_sets, MockPruningStrategy()
        )
        labels = generator.relation_prune(pattern.sub_patterns[0], freq_act_sets.fA)
        self.assertEqual({"a"}, labels)

        df_acts, ef_acts = generator.get_relation_prune_df_ef_sets(
            pattern.sub_patterns[0]
        )
        self.assertEqual({"a", "d", "e"}, df_acts)
        self.assertEqual({"b", "c"}, ef_acts)

    def __get_depth_of_rml(self, rml):
        depth = 0

        while rml.parent is not None:
            depth += 1
            rml = rml.parent

        return depth

    def __get_default_prune_sets(self, frequent_activities):
        return FrequentActivitySets(
            fA=frequent_activities,
            dfR={k: frequent_activities for k in frequent_activities},
            efR={k: frequent_activities for k in frequent_activities},
            ccR={k: frequent_activities for k in frequent_activities},
        )
