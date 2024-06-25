import unittest
from typing import Set

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


class TestBlanketAlgorithm(unittest.TestCase):
    def test_algorithms_sequential_tree_with_multiple_same_nodes(self):
        v = parse_concurrency_tree("→('a','a','a','a')").to_concurrency_group()
        num_traces = 8
        variants = {v: [Trace() for _ in range(num_traces)]}
        expected_patterns = {
            FrequencyCountingStrategy.TraceTransaction: (
                8,
                [self.__parse_pattern("→('a','a','a','a')", 8)],
                [self.__parse_pattern("→('a','a','a','a')", 8)],
            ),
            FrequencyCountingStrategy.VariantTransaction: (
                1,
                [self.__parse_pattern("→('a','a','a','a')", 1)],
                [self.__parse_pattern("→('a','a','a','a')", 1)],
            ),
        }

        self.__evaluate_for_counting_strategies(variants, expected_patterns)

    def test_algorithms_nested_trees(self):
        v1 = parse_concurrency_tree(
            "→('a','j',∧('c', →('d','e')), 'j','g')"
        ).to_concurrency_group()
        v2 = parse_concurrency_tree(
            "→('a','b',∧('c', →('d','e')), 'f','g')"
        ).to_concurrency_group()

        num_traces = 8
        variants = {
            v1: [Trace() for _ in range(num_traces)],
            v2: [Trace() for _ in range(num_traces)],
        }
        expected_patterns = {
            FrequencyCountingStrategy.TraceTransaction: (
                8,
                [
                    self.__parse_pattern(p, s)
                    for p, s in [
                        ("→('a','j',∧('c',→('d','e')),'j','g')", 8),
                        ("→('a','b',∧('c', →('d','e')),'f','g')", 8),
                    ]
                ],
                [
                    self.__parse_pattern(p, s)
                    for p, s in [
                        ("→('a','j',∧('c', →('d','e')),'j','g')", 8),
                        ("→('a','b',∧('c', →('d','e')),'f','g')", 8),
                        ("'a'...∧('c', →('d','e'))...'g'", 16),
                    ]
                ],
            ),
            FrequencyCountingStrategy.VariantTransaction: (
                1,
                [
                    self.__parse_pattern(p, s)
                    for p, s in [
                        ("→('a','j',∧('c', →('d','e')),'j','g')", 1),
                        ("→('a','b',∧('c', →('d','e')),'f','g')", 1),
                    ]
                ],
                [
                    self.__parse_pattern(p, s)
                    for p, s in [
                        ("→('a','j',∧('c', →('d','e')),'j','g')", 1),
                        ("→('a','b',∧('c', →('d','e')),'f','g')", 1),
                        ("'a'...∧('c', →('d','e'))...'g'", 2),
                    ]
                ],
            ),
        }

        self.__evaluate_for_counting_strategies(variants, expected_patterns)

    def __evaluate_for_counting_strategies(self, variants, expected_patterns):
        for strategy, (
            min_support_count,
            expected_maximal,
            expected_closed,
        ) in expected_patterns.items():
            closed, maximal = generate_eventually_follows_patterns_from_groups(
                variants, min_support_count, strategy, Algorithm.BlanketMining
            )
            print(closed)
            print(maximal)
            self.__eval_patterns(expected_maximal, maximal)
            self.__eval_patterns(expected_closed, closed)

    def __eval_patterns(
        self,
        expected_pts: Set[EventuallyFollowsPattern],
        found_patterns: Set[EventuallyFollowsPattern],
    ):
        expected_pts = set([repr(p) for p in expected_pts])
        flat_found_patterns = set([repr(p) for p in found_patterns])

        self.assertEqual(
            len(expected_pts.intersection(flat_found_patterns)),
            max([len(expected_pts), len(flat_found_patterns)]),
        )

    def __parse_pattern(self, pattern: str, support: int):
        pattern = parse_pattern(pattern)
        pattern.support = support

        return pattern
