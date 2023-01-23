from collections import defaultdict, deque
from typing import Mapping
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
)
from cortado_core.subprocess_discovery.subtree_mining.three_pattern_candiate_generation import (
    compute_freq3,
)

from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import TreePattern

from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry

from cortado_core.subprocess_discovery.subtree_mining.tree_pruning import (
    compute_f3_pruned_set,
)
from cortado_core.subprocess_discovery.subtree_mining.folding_label import fold_loops

def min_sub_mining(
    treebank: Mapping[int, TreeBankEntry],
    frequency_counting_strat: FrequencyCountingStrategy,
    k_it,
    min_sup,
    loop=False,
    bfs_traversal=True,
):

    """ """

    if loop:
        fold_loops(treebank, loop)

    fSets, F3 = compute_freq3(treebank, frequency_counting_strat, min_sup)

    pSets, F3 = compute_f3_pruned_set(fSets, F3)
    k_patterns = defaultdict(set)
    k_patterns[3] = F3

    patterns = set([repr(f.tree) for f in F3])
    Q: deque[TreePattern] = deque(F3)

    while len(Q) > 0:
        tp = Q.pop()

        if tp.size >= k_it:
            continue  # Skip after reaching k cut off

        # Compute the right most path extension of all k-1 pattern
        tps = tp.right_most_path_extension(pSets)
        sup_to_gain = tp.support

        
        for c in tps:
            
            if f := c.update_rmo_list(
                treebank, min_sup, frequency_counting_strat, sup_to_gain
            ):
                if bfs_traversal:
                    Q.appendleft(f)
                else:
                    Q.append(f)

                k_patterns[tp.size + 1].add(f)
                patterns.add(repr(f.tree))

    return k_patterns
