import itertools
from collections import Counter, defaultdict
from typing import Dict, List, Mapping, Tuple, Any

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
    FrequentActivitySets,
)
from cortado_core.subprocess_discovery.subtree_mining.right_most_path_extension.support_counting import (
    check_min_sup,
)
from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import TreePattern
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry
from cortado_core.subprocess_discovery.subtree_mining.utilities import _getLabel


def count_activites_in_tree(
    tid, tree: ConcurrencyTree, candidate_rmos: Dict[Tuple, List]
):
    act = Counter()
    ef = Counter()
    df = Counter()

    lSet = set()
    rSet = set()

    df_pairs = set()
    ef_pairs = set()

    rLabels = set()
    lSibsLabels = []

    for i, child in enumerate(tree.children):
        _get_candidate_rmos(tid, tree, child, lSibsLabels, candidate_rmos)

        if child.label:
            labels = {child.label}

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
                lSet.add(child.label)
                rSet.add(child.label)

            act.update({child.label: 1})
            rLabels = labels

        else:
            ef_c, df_c, act_c, rSet_c, lSet_c = count_activites_in_tree(
                tid, child, candidate_rmos
            )

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
                lSet.update(lSet_c)
                rSet.update(rSet_c)

            ef += ef_c
            df += df_c

            act += act_c
            rLabels = rSet_c

    ef += Counter(ef_pairs)
    df += Counter(df_pairs)

    return ef, df, act, rSet, lSet


def merge_dictionary(dict_1, dict_2):
    dict_3 = {**dict_1, **dict_2}
    for key, value in dict_3.items():
        if key in dict_1 and key in dict_2:
            dict_3[key] = sorted(value + dict_1[key], key=lambda x: x[1].id)
    return dict_3


def count_activities_in_tree_reps_mining(
    tid, tree: ConcurrencyTree, candidate_rmos: Dict[Tuple, List]
):
    act = Counter()
    ef = Counter()
    df = Counter()

    lSet = list()
    rSet = list()

    df_pairs = list()
    ef_pairs = list()

    rLabels = list()
    lSibsLabels = []

    single_act_reps = defaultdict(list)

    for i, child in enumerate(tree.children):
        _get_candidate_rmos(tid, tree, child, lSibsLabels, candidate_rmos)

        if child.label:
            labels = [child.label]

            if tree.op == cTreeOperator.Sequential:
                df_pairs += list(
                    _compute_directly_follows_relation_pairs(rLabels, labels)
                )  # DF
                ef_pairs += list(
                    _compute_directly_follows_relation_pairs(act.elements(), labels)
                )  # EF

                if i == 0:
                    lSet = labels

                if i == len(tree.children) - 1:
                    rSet = labels

            elif tree.op == cTreeOperator.Concurrent:
                lSet.append(child.label)
                rSet.append(child.label)

            act.update({child.label: 1})
            rLabels = labels

            if child.label in single_act_reps:
                single_act_reps[child.label].append((child.parent.id, child))

            else:
                single_act_reps[child.label] = [(child.parent.id, child)]

        else:
            (
                ef_c,
                df_c,
                act_c,
                rSet_c,
                lSet_c,
                single_act_reps_c,
            ) = count_activities_in_tree_reps_mining(tid, child, candidate_rmos)

            if tree.op == cTreeOperator.Sequential:
                df_pairs += list(
                    _compute_directly_follows_relation_pairs(rLabels, lSet_c)
                )  # DF
                ef_pairs += list(
                    _compute_directly_follows_relation_pairs(
                        act.elements(), act_c.elements()
                    )
                )  # EF

                if i == 0:
                    lSet = lSet_c

                if i == len(tree.children) - 1:
                    rSet = rSet_c

            elif tree.op == cTreeOperator.Concurrent:
                lSet += lSet_c
                rSet += rSet_c

            ef += ef_c
            df += df_c

            act += act_c
            rLabels = rSet_c
            single_act_reps = merge_dictionary(single_act_reps, single_act_reps_c)

    ef += Counter(ef_pairs)
    df += Counter(df_pairs)

    return ef, df, act, rSet, lSet, single_act_reps


def _compute_directly_follows_relation_pairs(lLabels, rLabels):
    return itertools.product(lLabels, rLabels)


def _get_candidate_rmos(
    tid: int,
    tree: ConcurrencyTree,
    child: ConcurrencyTree,
    lSibsLabels: List,
    candidate_rmos: Dict[Tuple, List],
):
    cLabel = _getLabel(child)
    pLabel = tree.op

    if tree.parent:
        # 4 Code, 3 Labels and 1 Indicator Boolean if it is a 1 Child 2 Leaves or a 3 Chain Tree
        candidate_rmos[(tree.parent.op, pLabel, cLabel, True)].append(
            (tid, tree.parent.id, child)
        )

    if len(lSibsLabels) > 0:
        if tree.op == cTreeOperator.Sequential:
            lSibLabel = lSibsLabels[-1]
            candidate_rmos[(pLabel, lSibLabel, cLabel, False)].append(
                (tid, tree.id, child)
            )

        elif (
            tree.op == cTreeOperator.Concurrent or tree.op == cTreeOperator.Fallthrough
        ):
            for lSiblabel in set(lSibsLabels):
                candidate_rmos[(pLabel, lSiblabel, cLabel, False)].append(
                    (tid, tree.id, child)
                )

    lSibsLabels.append(cLabel)


def _create_3_patterns(pLabel, lLabel, rLabel, nested: bool):
    if isinstance(rLabel, cTreeOperator):
        leaf = ConcurrencyTree(None, None, None, None, rLabel)

    else:
        leaf = ConcurrencyTree(None, None, None, rLabel, None)

    if nested:
        parent = ConcurrencyTree([leaf], None, None, None, lLabel)
        leaf.parent = parent

        grand_parent = ConcurrencyTree([parent], None, None, None, pLabel)
        parent.parent = grand_parent

        tp = TreePattern(grand_parent, leaf, 0)

    else:
        if isinstance(lLabel, cTreeOperator):
            sibling = ConcurrencyTree(None, None, None, None, lLabel)

        else:
            sibling = ConcurrencyTree(None, None, None, lLabel, None)

        parent = ConcurrencyTree([sibling, leaf], None, None, None, pLabel)
        leaf.parent = parent
        sibling.parent = parent

        tp = TreePattern(parent, leaf, 1)

    tp.size = 3

    return tp


def compute_freq3(
    treebank: Mapping[int, TreeBankEntry],
    freq_strat: FrequencyCountingStrategy,
    min_sup: int,
    repetition_pairs_mining: bool = None,
) -> tuple[FrequentActivitySets, set[TreePattern], defaultdict[Any, dict[int, list]]]:
    """
    Args:
        treebank (Mapping[int, TreeBankEntry]): _description_
        freq_strat (FrequencyCountingStrategy): _description_
        min_sup (int): _description_
        repetition_pairs_mining (bool, optional): indicate if the `repetition pairs mining` is active

    Returns:
        frequentActivitySet (without frequnet concurrent relations)
        F3 Set of frequnet infix subtrees of size 3
    """

    directly_follows_counter = Counter()
    eventually_follows_counter = Counter()
    candidate_rmos = defaultdict(list)
    single_act_reps = defaultdict(dict[int, list])

    for tid, entry in treebank.items():
        if repetition_pairs_mining:
            (
                ef,
                df,
                _,
                _,
                _,
                single_reps_per_tree,
            ) = count_activities_in_tree_reps_mining(tid, entry.tree, candidate_rmos)
            single_reps_per_tree = {
                act: reps for act, reps in single_reps_per_tree.items() if len(reps) > 1
            }  # filter out the single activity occurences
            single_act_reps[tid] = single_reps_per_tree
        else:
            ef, df, _, _, _ = count_activites_in_tree(tid, entry.tree, candidate_rmos)

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

        else:
            directly_follows_counter.update({key: nT for key, _ in df.items()})
            eventually_follows_counter.update({key: nT for key, _ in ef.items()})

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
    frequent_ef_relations = flatten_pairs(frequent_ef_pairs)

    F3 = set()

    for k, v in candidate_rmos.items():
        tp = _create_3_patterns(*k)

        for entry in v:
            tp.add_rmo(entry)

        if check_min_sup(
            tp,
            freq_strat,
            treebank,
            min_sup=min_sup,
            unique_roots=not repetition_pairs_mining,
        ):
            F3.add(tp)

        else:
            # Clean up
            del tp

    return (
        FrequentActivitySets(
            fA=set(),
            dfR=frequent_df_relations,
            efR=frequent_ef_relations,
            ccR=set(),
        ),
        F3,
        single_act_reps,
    )
