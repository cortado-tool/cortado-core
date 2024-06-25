import unittest
from typing import Dict, Set, Tuple

from pm4py.objects.log.obj import Trace

from cortado_core.eventually_follows_pattern_mining.algorithm import (
    generate_eventually_follows_patterns_from_groups,
    Algorithm,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
    parse_pattern,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
)


class TestAlgorithms(unittest.TestCase):
    def test_algorithms_sequential_tree_with_multiple_same_nodes(self):
        v = parse_concurrency_tree("→('a','a','a','a')").to_concurrency_group()
        num_traces = 8
        variants = {v: [Trace() for _ in range(num_traces)]}
        expected_patterns = {
            FrequencyCountingStrategy.TraceOccurence: (
                8,
                set(
                    [
                        self.__parse_pattern(p, s * num_traces)
                        for p, s in [
                            ("'a'", 4),
                            ("→('a','a')", 1),
                            ("→('a','a','a')", 1),
                            ("→('a','a','a','a')", 1),
                            ("'a'...'a'", 2),
                            ("→('a', 'a')...'a'", 1),
                            ("'a'...→('a', 'a')", 1),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.TraceTransaction: (
                8,
                set(
                    [
                        self.__parse_pattern(p, s * num_traces)
                        for p, s in [
                            ("'a'", 1),
                            ("→('a','a')", 1),
                            ("→('a','a','a')", 1),
                            ("→('a','a','a','a')", 1),
                            ("'a'...'a'", 1),
                            ("→('a', 'a')...'a'", 1),
                            ("'a'...→('a', 'a')", 1),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.VariantOccurence: (
                1,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 4),
                            ("→('a','a')", 1),
                            ("→('a','a','a')", 1),
                            ("→('a','a','a','a')", 1),
                            ("'a'...'a'", 2),
                            ("→('a', 'a')...'a'", 1),
                            ("'a'...→('a', 'a')", 1),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.VariantTransaction: (
                1,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 1),
                            ("→('a','a')", 1),
                            ("→('a','a','a')", 1),
                            ("→('a','a','a','a')", 1),
                            ("'a'...'a'", 1),
                            ("→('a', 'a')...'a'", 1),
                            ("'a'...→('a', 'a')", 1),
                        ]
                    ]
                ),
            ),
        }

        self.__evaluate_for_algorithms(variants, expected_patterns)

    def test_algorithms_concurrent_tree_with_multiple_same_nodes(self):
        v = parse_concurrency_tree("∧('a','a','a','a')").to_concurrency_group()
        num_traces = 8
        variants = {v: [Trace() for _ in range(num_traces)]}
        expected_patterns = {
            FrequencyCountingStrategy.TraceOccurence: (
                8,
                set(
                    [
                        self.__parse_pattern(p, s * num_traces)
                        for p, s in [
                            ("'a'", 4),
                            ("∧('a','a')", 1),
                            ("∧('a','a','a')", 1),
                            ("∧('a','a','a','a')", 1),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.TraceTransaction: (
                8,
                set(
                    [
                        self.__parse_pattern(p, s * num_traces)
                        for p, s in [
                            ("'a'", 1),
                            ("∧('a','a')", 1),
                            ("∧('a','a','a')", 1),
                            ("∧('a','a','a','a')", 1),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.VariantOccurence: (
                1,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 4),
                            ("∧('a','a')", 1),
                            ("∧('a','a','a')", 1),
                            ("∧('a','a','a','a')", 1),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.VariantTransaction: (
                1,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 1),
                            ("∧('a','a')", 1),
                            ("∧('a','a','a')", 1),
                            ("∧('a','a','a','a')", 1),
                        ]
                    ]
                ),
            ),
        }

        self.__evaluate_for_algorithms(variants, expected_patterns)

    def test_algorithms_more_complex_tree(self):
        v = parse_concurrency_tree(
            "→(∧('a','b'),'c',∧('d',→('e','f')))"
        ).to_concurrency_group()
        v2 = parse_concurrency_tree("→('a','c',∧('d','e')))").to_concurrency_group()
        variants = {v: [Trace() for _ in range(4)], v2: [Trace() for _ in range(1)]}
        expected_patterns = {
            FrequencyCountingStrategy.TraceOccurence: (
                5,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 5),
                            ("'c'", 5),
                            ("'d'", 5),
                            ("'e'", 5),
                            ("'a'...'d'", 5),
                            ("'a'...'e'", 5),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.TraceTransaction: (
                5,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 5),
                            ("'c'", 5),
                            ("'d'", 5),
                            ("'e'", 5),
                            ("'a'...'d'", 5),
                            ("'a'...'e'", 5),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.VariantOccurence: (
                2,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 2),
                            ("'c'", 2),
                            ("'d'", 2),
                            ("'e'", 2),
                            ("'a'...'d'", 2),
                            ("'a'...'e'", 2),
                        ]
                    ]
                ),
            ),
            FrequencyCountingStrategy.VariantTransaction: (
                2,
                set(
                    [
                        self.__parse_pattern(p, s)
                        for p, s in [
                            ("'a'", 2),
                            ("'c'", 2),
                            ("'d'", 2),
                            ("'e'", 2),
                            ("'a'...'d'", 2),
                            ("'a'...'e'", 2),
                        ]
                    ]
                ),
            ),
        }

        self.__evaluate_for_algorithms(variants, expected_patterns)

    def __evaluate_for_algorithms(
        self,
        variants,
        expected_patterns: Dict[
            FrequencyCountingStrategy, Tuple[int, Set[EventuallyFollowsPattern]]
        ],
    ):
        for strategy, (min_support_count, expected_pts) in expected_patterns.items():
            found_patterns = generate_eventually_follows_patterns_from_groups(
                variants,
                min_support_count,
                strategy,
                Algorithm.InfixPatternCombinationBruteForce,
            )
            self.__eval_patterns(expected_pts, found_patterns)
            found_patterns = generate_eventually_follows_patterns_from_groups(
                variants,
                min_support_count,
                strategy,
                Algorithm.InfixPatternCombinationEnumerationGraph,
            )
            self.__eval_patterns(expected_pts, found_patterns)
            found_patterns = generate_eventually_follows_patterns_from_groups(
                variants, min_support_count, strategy, Algorithm.RightmostExpansion
            )
            self.__eval_patterns(expected_pts, found_patterns)

    def __eval_patterns(
        self,
        expected_pts: Set[EventuallyFollowsPattern],
        found_patterns: Dict[int, Set[EventuallyFollowsPattern]],
    ):
        flat_found_patterns = set()
        for pts in found_patterns.values():
            flat_found_patterns = flat_found_patterns.union(pts)

        expected_pts = set([repr(p) for p in expected_pts])
        flat_found_patterns = set([repr(p) for p in flat_found_patterns])

        self.assertEqual(
            len(expected_pts.intersection(flat_found_patterns)),
            max([len(expected_pts), len(flat_found_patterns)]),
        )

    def __parse_pattern(self, pattern: str, support: int):
        pattern = parse_pattern(pattern)
        pattern.support = support

        return pattern
