from typing import Mapping
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.compute_root_occurence_blanket import (
    check_root_occurence_blanket,
)
from cortado_core.subprocess_discovery.subtree_mining.ct_frequency_counting import ct_compute_frequent_activity_sets
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequencyCountingStrategy, PruningSets
from cortado_core.subprocess_discovery.subtree_mining.tree_pruning import (
    _get_prune_sets,
    compute_f3_pruned_set_2_patterns,
)
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry
from cortado_core.subprocess_discovery.subtree_mining.utilities import (
    _contains_fallthrough,
)   

from cortado_core.subprocess_discovery.subtree_mining.maximal_connected_components.maximal_connected_check import (
    check_if_valid_tree
)

from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree_pattern import (
    CMTreePattern,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.compute_frequency_blanket import (
    check_frequency_blanket,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.compute_occurence_blanket import (
    check_occ_blanket,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.compute_transaction_blanket import (
    check_transaction_blanket,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.create_initial_candidates import (
    generate_initial_candidates,
)

from cortado_core.subprocess_discovery.subtree_mining.folding_label import fold_loops


def cm_min_sub_mining(
    treebank : Mapping[int, TreeBankEntry],
    frequency_counting_strat: FrequencyCountingStrategy,
    k_it : int,
    min_sup : int,
    loop : int = 0,
):

    if loop:
        fold_loops(treebank, loop, fSets)
    
    fSets = ct_compute_frequent_activity_sets(treebank, frequency_counting_strat, min_sup)
    
    C = generate_initial_candidates(
        treebank, min_sup, frequency_counting_strat, fSets
    )
    
    k_pattern = {2: C}

    has_fallthroughs = any([_contains_fallthrough(f.tree) for f in C])

    # Define the initial Prune Sets
    pSets = _get_prune_sets(fSets, C)

    # Skip the initial pruning step to compute the full set of F3 Patterns too properly update the Pruning Sets
    skipPrune = True

    for k in range(k_it):
        E = []

        for c in C:

            if res := cm_grow(
                c,
                treebank,
                min_sup,
                frequency_counting_strat,
                skipPrune,
                pSets,
                has_fallthroughs,
            ):
                E.extend(res)

            c.tree

        if len(E) == 0:
            break

        C = E

        if len(E) > 0:
            k_pattern[k + 3] = E
        else:
            break

        if k == 0: 
            pSets, C = compute_f3_pruned_set_2_patterns(pSets, C)
            skipPrune = False

    return k_pattern


def cm_grow(
    tp: CMTreePattern,
    treebank,
    min_sup: int,
    frequency_counting_strat: FrequencyCountingStrategy,
    skipPrune: bool,
    pSets: PruningSets,
    has_fallthroughs: bool,
):
    
    occurenceBased = (
        frequency_counting_strat == FrequencyCountingStrategy.TraceOccurence
        or frequency_counting_strat == FrequencyCountingStrategy.VariantOccurence
    )
    
    E = []

    B_left_occ_not_empty, B_occ_not_empty = check_occ_blanket(tp)

    if (not skipPrune) and B_left_occ_not_empty:
        return None

    else:

        patterns = tp.right_most_path_extension(pSets, skipPrune, has_fallthroughs)
        sup_to_gain = tp.support

        for e in patterns:
            if p := e.update_rmo_list(
                treebank, min_sup, frequency_counting_strat, sup_to_gain
            ):
                E.append(p)
        

    if not B_occ_not_empty and check_if_valid_tree(tp.tree):

        if (occurenceBased and not check_root_occurence_blanket(tp)) or (
            not occurenceBased and not check_transaction_blanket(tp)
        ):

            tp.closed = True

            # NO VALID EXTENSION EXISTS, thus we can check if it is maximal
            # if len(E) == 0:  Check if any Extension exists, that isn't based on an operator Node => Easier Exclusion
            if not any([p.rml.label for p in E]):

                B_freq_not_empty = check_frequency_blanket(
                    tp=tp,
                    min_sup=min_sup,
                    treeBank=treebank,
                    strategy=frequency_counting_strat,
                )

                if not B_freq_not_empty:
                   tp.maximal = True               

    return E