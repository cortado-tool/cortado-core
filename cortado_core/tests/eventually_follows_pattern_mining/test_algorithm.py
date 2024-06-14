import pickle
import time
import unittest
from typing import Set, Dict

import pm4py

from cortado_core.eventually_follows_pattern_mining.algorithm import (
    generate_eventually_follows_patterns_from_groups,
    Algorithm,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_grow import (
    cm_min_sub_mining,
)
from cortado_core.subprocess_discovery.subtree_mining.ct_frequency_counting import (
    count_activites_in_tree,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
)
from cortado_core.subprocess_discovery.subtree_mining.right_most_path_extension.min_sub_mining import (
    min_sub_mining,
)
from cortado_core.subprocess_discovery.subtree_mining.treebank import (
    create_treebank_from_cv_variants,
)
from cortado_core.utils.cvariants import get_concurrency_variants

MIN_SUP = 2000
COUNTING_STRATEGY = FrequencyCountingStrategy.TraceTransaction


@unittest.skip("not in pipeline")
class TestAlgorithm(unittest.TestCase):
    def load_variants(self):
        # log = pm4py.read_xes('C:\\sources\\arbeit\\cortado\\event-logs\\sepsis_cases.xes')
        # variants = get_concurrency_variants(log)
        # pickle.dump(variants, open('C:\\sources\\arbeit\\cortado\\event-logs\\variants\\sepsis_cases.pkl', "wb"))
        variants = pickle.load(
            open(
                "C:\\sources\\arbeit\\cortado\\event-logs\\variants\\BPI_Challenge_2012.pkl",
                "rb",
            )
        )
        return variants

    def test_occ_vs_transaction(self):
        variants = self.load_variants()
        patterns_trans = generate_eventually_follows_patterns_from_groups(
            variants,
            MIN_SUP,
            FrequencyCountingStrategy.TraceTransaction,
            Algorithm.RightmostExpansion,
        )
        patterns_occ = generate_eventually_follows_patterns_from_groups(
            variants,
            MIN_SUP,
            FrequencyCountingStrategy.TraceOccurence,
            Algorithm.RightmostExpansion,
        )

        for k, p_occ in patterns_occ.items():
            p_occ = set([str(p) for p in p_occ])
            if k in patterns_trans:
                p_trans = set([str(p) for p in patterns_trans[k]])
            else:
                continue
            self.assertEqual(0, len(p_trans.difference(p_occ)))

        self.check_a_priori(patterns_trans)
        self.check_a_priori(patterns_occ)

    def check_a_priori(self, patterns: Dict[int, Set[EventuallyFollowsPattern]]):
        k = max(patterns.keys())

        while k != 0:
            if k in patterns:
                k_patterns = patterns[k]
                for k_pattern in k_patterns:
                    p = k_pattern
                    predecessor = p.predecessor_pattern
                    while predecessor is not None:
                        self.assertLessEqual(p.support, predecessor.support)
                        p = predecessor
                        predecessor = p.predecessor_pattern

            k -= 1

    def test_algorithm(self):
        variants = self.load_variants()
        start = time.time()
        patterns_ext = {}
        patterns_ext = generate_eventually_follows_patterns_from_groups(
            variants, MIN_SUP, COUNTING_STRATEGY, Algorithm.RightmostExpansion
        )
        print("RIGHTMOST EXPANSION TIME:", time.time() - start)
        start = time.time()
        patterns_comb = {}
        patterns_comb = generate_eventually_follows_patterns_from_groups(
            variants,
            MIN_SUP,
            COUNTING_STRATEGY,
            Algorithm.InfixPatternCombinationEnumerationGraph,
        )
        print("COMBINATION APPROACH TIME:", time.time() - start)

        # print('PATTERNS Ext: \n')
        # print(patterns_ext)

        print("NUMBER OF EF PATTERNS:", sum([len(p) for p in patterns_ext.values()]))
        print(
            "NUMBER OF INFIX PATTERNS:",
            sum([len([fp for fp in p if len(fp) == 1]) for p in patterns_ext.values()]),
        )

        print(
            "INFIX PATTERNS:",
            [[fp for fp in p if len(fp) == 1] for p in patterns_ext.values()],
        )

        print(
            "NUMBER OF EF PATTERNS COMBINATION",
            sum([len(p) for p in patterns_comb.values()]),
        )

        self.eval_patterns(patterns_ext, patterns_comb)

    def eval_patterns(self, patterns_ext, patterns_comb):
        patterns_ext = {k: v for k, v in patterns_ext.items() if len(v) > 0}
        if len(patterns_ext) != len(patterns_comb):
            print(
                "LEN MISMATCH IN PATTERNS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )

        for k in patterns_ext:
            p_ext = set([str(p) for p in patterns_ext[k]])
            p_comb = set([str(p) for p in patterns_comb[k]])

            if len(p_ext.intersection(p_comb)) != len(p_ext) or len(
                p_ext.intersection(p_comb)
            ) != len(p_comb):
                print("different patterns", k)
                print("in comb but not in ext", p_comb.difference(p_ext))
                print("in ext but not in comb", p_ext.difference(p_comb))

    def test_blanket_mining(self):
        variants = self.load_variants()
        start = time.time()
        (
            closed_baseline,
            maximal_baseline,
        ) = generate_eventually_follows_patterns_from_groups(
            variants, MIN_SUP, COUNTING_STRATEGY, Algorithm.ClosedMaximalBaseline
        )
        print("BL TIME", time.time() - start)

        print("BL CLOSED", closed_baseline)
        print("BL MAXIMAL", maximal_baseline)
        print("LEN BL CLOSED", len(closed_baseline))
        print("LEN BL MAXIMAL", len(maximal_baseline))

        start = time.time()
        closed, maximal = generate_eventually_follows_patterns_from_groups(
            variants, MIN_SUP, COUNTING_STRATEGY, Algorithm.BlanketMining
        )
        print("TIME", time.time() - start)
        print("CLOSED", closed)
        print("MAXIMAL", maximal)
        print("LEN CLOSED", len(closed))
        print("LEN MAXIMAL", len(maximal))

        self.assertTrue(maximal.issubset(closed))

        self.assertEqual(
            set([repr(p) for p in maximal_baseline]), set([repr(p) for p in maximal])
        )
        self.assertEqual(
            set([repr(p) for p in closed_baseline]), set([repr(p) for p in closed])
        )

    def test_cm_mining(self):
        variants = self.load_variants()
        treebank = create_treebank_from_cv_variants(variants, artifical_start=False)
        cm_k_patterns = cm_min_sub_mining(
            treebank,
            frequency_counting_strat=COUNTING_STRATEGY,
            k_it=100,
            min_sup=MIN_SUP - 1,
        )
        print(cm_k_patterns)

    def test_compare_to_michaels_patterns(self):
        variants = self.load_variants()
        start_time = time.time()
        treebank = create_treebank_from_cv_variants(variants, artifical_start=False)
        michael_patterns, _ = min_sub_mining(
            treebank,
            frequency_counting_strat=COUNTING_STRATEGY,
            k_it=100,
            min_sup=MIN_SUP - 1,
        )
        print("MICHAEL TIME:", time.time() - start_time)
        michael_patterns = self.filter_incomplete_infix_patterns(michael_patterns)
        start_time = time.time()
        patterns_ext = generate_eventually_follows_patterns_from_groups(
            variants,
            MIN_SUP,
            COUNTING_STRATEGY,
            Algorithm.RightmostExpansionOnlyInfixPatterns,
        )
        print("MY TIME:", time.time() - start_time)
        patterns_ext = self.filter_my_patterns_to_match_michaels(patterns_ext)

        print("LEN MICHAELS PATTERNS", len(michael_patterns))
        print("LEN MY INFIX PATTERNS", len(patterns_ext))

        in_michaels_but_not_in_mine = michael_patterns.difference(patterns_ext)
        for p in in_michaels_but_not_in_mine:
            print("in michaels, not in mine", p)

        in_mine_but_not_in_michaels = patterns_ext.difference(michael_patterns)
        for p in in_mine_but_not_in_michaels:
            print("in mine, not in michaels", p)

    def filter_my_patterns_to_match_michaels(self, patterns):
        filtered = set()

        for k, p in patterns.items():
            if k == 1:
                continue

            for pattern in p:
                if len(pattern) == 1:
                    filtered.add(repr(pattern).replace(" ", ""))

        return filtered

    def filter_incomplete_infix_patterns(self, patterns):
        filtered = set()

        for k, p in patterns.items():
            for pattern in p:
                if self.is_not_valid(pattern.tree):
                    continue

                filtered.add(repr(pattern).replace(" ", "").replace(":", ""))

        return filtered

    def is_not_valid(self, ctree):
        if ctree.op is not None:
            if len(ctree.children) <= 1:
                return True

            for child in ctree.children:
                if self.is_not_valid(child):
                    return True

        return False
