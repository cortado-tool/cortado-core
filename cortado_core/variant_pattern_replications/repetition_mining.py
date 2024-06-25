from typing import Dict, List, Set, Any

from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_concurrency_tree,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    lca_is_sequential,
    get_level_1_parent,
)
from cortado_core.subprocess_discovery.subtree_mining.maximal_connected_components.maximal_connected_check import (
    check_if_valid_tree,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
)
from cortado_core.subprocess_discovery.subtree_mining.right_most_path_extension.min_sub_mining import (
    min_sub_mining,
)
from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import TreePattern
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry
from cortado_core.variant_pattern_replications.locate_patterns import locate_pattern
from cortado_core.variant_pattern_replications.pair import Pair, Positions


def generate_dummy_tree():
    return TreeBankEntry(
        parse_concurrency_tree("→('l', 'l', 'a', 'b', 'l', 'l')"), 1, 1
    )


def generate_consecutive_pairs(act_reps: Dict[str, List]):
    pairs = set()

    for act, reps in act_reps.items():
        for i in range(len(reps) - 1):
            if lca_is_sequential(reps[i][1], reps[i + 1][1]):
                ll1occ = get_level_1_parent(reps[i][1])
                rl1occ = get_level_1_parent(reps[i + 1][1])
                pairs.add(
                    Pair(
                        positions=Positions(
                            (ll1occ.id, rl1occ.id), (ll1occ.bfsid, rl1occ.bfsid)
                        ),
                        pattern=act,
                        matches={reps[i][1].id, reps[i + 1][1].id},
                        activities=[act],
                    )
                )

    return pairs


def create_non_overlapping_pairs(treepat, roottree):
    """
    returns Dict{(lrmo, rrmo): Pair}
    """

    i = 0
    non_overlapping_pairs: dict[Any, Pair] = dict()
    rmo = treepat.rmo[0]

    while i < len(rmo) - 1:
        pair = create_pair(rmo[i], rmo[i + 1], treepat.tree, roottree)
        if not pair.__overlapping__():
            non_overlapping_pairs[(rmo[i], rmo[i + 1])] = pair
        i += 1

    return non_overlapping_pairs


def create_pair(left_occ_rmo, right_occ_rmo, treepat, roottree):
    ll1occ = get_level_1_parent(left_occ_rmo[1])
    rl1occ = get_level_1_parent(right_occ_rmo[1])
    length = 1

    if left_occ_rmo[0] == 0:
        ll1occ = roottree.children[ll1occ.bfsid - len(treepat.children)]
        length = len(treepat.children)

    if right_occ_rmo[0] == 0:
        rl1occ = roottree.children[rl1occ.bfsid - len(treepat.children)]
        length = len(treepat.children)

    return Pair(
        Positions((ll1occ.id, rl1occ.id), (ll1occ.bfsid, rl1occ.bfsid)),
        treepat,
        length=length,
        activities=treepat.leaf_nodes,
    )


def pair_unions(kpatpairs: Set[Pair], singleactpairs: Set[Pair]):
    result = kpatpairs.copy()

    for sgpair in singleactpairs:
        equivalent_found = False

        for kppair in kpatpairs:
            if sgpair.__equivalent__(kppair):
                equivalent_found = True

        if not equivalent_found:
            result.add(sgpair)

    return result


def filter_overlapping_invalid_patterns(k_patterns, ks, root):
    """
    returns (non_overlapping_pairs: Dict{TreePattern: Dict{(lrmo, rrmo): Pair}}, kpatterns: Dict{int: Set{TreePattern}})
    """
    non_overlapping_pairs: dict[TreePattern, dict[Any, Pair]] = dict()
    kpatterns: dict[int, set[TreePattern]] = dict()

    for k in ks:
        for tp in k_patterns[k]:
            if len(tp.tree.children) > 1 and check_if_valid_tree(tp.tree):
                tp.tree.set_leaf_nodes()
                non_overlapping_pairs[tp] = create_non_overlapping_pairs(tp, root)

                if len(non_overlapping_pairs[tp]) > 0:
                    if k not in kpatterns:
                        kpatterns[k] = set()
                    kpatterns[k].add(tp)

    return non_overlapping_pairs, kpatterns


def filter_maximal_patterns(kpatterns, pairs, ks, variant: TreeBankEntry):
    maximal_pairs = set()

    maximal_length = 1
    maximal_size = 1

    for k in ks:
        if k in kpatterns:
            for tp in kpatterns[k]:
                for lrmo, rrmo in zip(tp.rmo[0], tp.rmo[0][1:]):
                    if (lrmo, rrmo) in pairs[tp] and not any(
                        (
                            mpair.__equivalent__(pairs[tp][(lrmo, rrmo)])
                            for mpair in maximal_pairs
                        )
                    ):
                        _, lmatching_locs = locate_pattern(
                            variant.tree.get_node_by_dfsid(lrmo[0]),
                            tp.tree,
                            lrmo[1].id,
                        )
                        _, rmatching_locs = locate_pattern(
                            variant.tree.get_node_by_dfsid(rrmo[0]),
                            tp.tree,
                            rrmo[1].id,
                        )

                        pairs[tp][(lrmo, rrmo)].matches = lmatching_locs.union(
                            rmatching_locs
                        )

                        if pairs[tp][(lrmo, rrmo)].length > maximal_length:
                            maximal_length = pairs[tp][(lrmo, rrmo)].length
                        if pairs[tp][(lrmo, rrmo)].size > maximal_size:
                            maximal_size = pairs[tp][(lrmo, rrmo)].size

                        maximal_pairs.add(pairs[tp][(lrmo, rrmo)])

    return maximal_pairs, maximal_size, maximal_length


def generate_and_filter_patterns(treebank: Dict[int, TreeBankEntry]):
    k_patterns, single_act_reps = min_sub_mining(
        treebank,
        FrequencyCountingStrategy.VariantOccurence,
        20,
        1,
        repetition_pairs_mining=True,
    )

    single_act_pairs = set()
    for tid, pattern in single_act_reps.items():
        single_act_pairs = generate_consecutive_pairs(pattern)

    ks = list(k_patterns)
    ks.reverse()

    non_overlapping_pairs, kpatterns_filtered = filter_overlapping_invalid_patterns(
        k_patterns, ks, treebank[0].tree
    )

    return non_overlapping_pairs, kpatterns_filtered, ks, single_act_pairs
