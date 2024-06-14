from collections import Counter, defaultdict
import itertools

from typing import Mapping
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
    FrequentActivitySets,
)
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry


def count_activites_in_tree(tree: ConcurrencyTree):
    act = Counter()
    ef = Counter()
    df = Counter()
    con = Counter()

    lSet = set()
    rSet = set()

    df_pairs = set()
    ef_pairs = set()
    c_pairs = set()

    rLabels = set()

    for i, child in enumerate(tree.children):
        if child.label:
            labels = set([child.label])

            if tree.op == cTreeOperator.Sequential:
                df_pairs.update(
                    _compute_directly_follows_relation_pairs(rLabels, labels)
                )  # DF
                ef_pairs.update(
                    _compute_directly_follows_relation_pairs(act.keys(), labels)
                )  # EF

                if i == 0:
                    lSet = labels

                if i == len(tree.children) - 1:
                    rSet = labels

            elif tree.op == cTreeOperator.Concurrent:
                c_pairs.update(
                    _compute_concurrent_relation_pairs(act.keys(), labels)
                )  # C

                lSet.add(child.label)
                rSet.add(child.label)

            act.update({child.label: 1})
            rLabels = labels

        else:
            ef_c, df_c, act_c, con_c, rSet_c, lSet_c = count_activites_in_tree(child)

            if tree.op == cTreeOperator.Sequential:
                df_pairs.update(
                    _compute_directly_follows_relation_pairs(rLabels, lSet_c)
                )  # DF
                ef_pairs.update(
                    _compute_directly_follows_relation_pairs(act.keys(), act_c.keys())
                )  # EF

                if i == 0:
                    lSet = lSet_c

                if i == len(tree.children) - 1:
                    rSet = rSet_c

            elif tree.op == cTreeOperator.Concurrent:
                c_pairs.update(
                    _compute_concurrent_relation_pairs(act.keys(), act_c.keys())
                )  # C

                lSet.update(lSet_c)
                rSet.update(rSet_c)

            ef += ef_c
            df += df_c
            con += con_c

            act += act_c
            rLabels = rSet_c

    ef += Counter(ef_pairs)
    df += Counter(df_pairs)
    con += Counter(c_pairs)

    return ef, df, act, con, rSet, lSet


def _compute_concurrent_relation_pairs(lLabels, rLabels):
    return itertools.chain(
        itertools.product(lLabels, rLabels), itertools.product(rLabels, lLabels)
    )


def _compute_directly_follows_relation_pairs(lLabels, rLabels):
    return itertools.product(lLabels, rLabels)


def ct_compute_frequent_activity_sets(
    treebank: Mapping[int, TreeBankEntry],
    freq_strat: FrequencyCountingStrategy,
    min_sup: int,
):
    directly_follows_counter = Counter()
    eventually_follows_counter = Counter()
    concurrent_counter = Counter()
    activities_counter = Counter()

    for entry in treebank.values():
        ef, df, act, con, _, _ = count_activites_in_tree(entry.tree)

        if (
            freq_strat == FrequencyCountingStrategy.TraceTransaction
            or freq_strat == FrequencyCountingStrategy.TraceOccurence
        ):
            nT = entry.nTraces

        else:
            nT = 1

        if (
            freq_strat == FrequencyCountingStrategy.TraceOccurence
            or freq_strat == FrequencyCountingStrategy.VariantOccurence
        ):
            directly_follows_counter.update(
                {key: count * nT for key, count in df.items()}
            )
            eventually_follows_counter.update(
                {key: count * nT for key, count in ef.items()}
            )
            concurrent_counter.update({key: count * nT for key, count in con.items()})
            activities_counter.update({key: count * nT for key, count in act.items()})

        else:
            directly_follows_counter.update({key: nT for key, count in df.items()})
            eventually_follows_counter.update({key: nT for key, count in ef.items()})
            concurrent_counter.update({key: nT for key, count in con.items()})
            activities_counter.update({key: nT for key, count in act.items()})

    # print()
    # print('Tree')
    # for act, value in activities_counter.items():
    #    print(act, value)

    # print()
    # for pair, value in directly_follows_counter.items():
    #    print(pair, value)

    # Check if the Activites are above a certain support

    frequent_df_pairs = set(
        [
            pair
            for pair in directly_follows_counter
            if directly_follows_counter[pair] > min_sup
        ]
    )

    frequent_ef_pairs = set(
        [
            pair
            for pair in eventually_follows_counter
            if eventually_follows_counter[pair] > min_sup
        ]
    )

    frequent_cc_pairs = set(
        [pair for pair in concurrent_counter if concurrent_counter[pair] > min_sup]
    )

    frequent_activities = set(
        [act for act in activities_counter if activities_counter[act] > min_sup]
    )

    def flatten_pairs(pairs, both_sides=False):
        """
        Flatten a pair into a {l : rs} dict
        """

        freq_dict = defaultdict(set)

        for l, r in pairs:
            freq_dict[l].add(r)

            if both_sides:
                freq_dict[r].add(l)

        return freq_dict

    frequent_df_relations = flatten_pairs(frequent_df_pairs)
    frequent_cc_relations = flatten_pairs(frequent_cc_pairs, both_sides=True)
    frequent_ef_relations = flatten_pairs(frequent_ef_pairs)

    return FrequentActivitySets(
        fA=frequent_activities,
        dfR=frequent_df_relations,
        efR=frequent_ef_relations,
        ccR=frequent_cc_relations,
    )
