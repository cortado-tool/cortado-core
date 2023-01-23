from collections import Counter
from typing import Mapping, Set, List

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree import (
    CMConcurrencyTree,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree_pattern import (
    CMTreePattern,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequencyCountingStrategy
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry
from cortado_core.subprocess_discovery.subtree_mining.utilities import (
    _update_subToGain,
    get_child_labels,
)

def check_frequency_blanket(
    tp: CMTreePattern, min_sup, treeBank, strategy
):

    # Creat an Iterator over the Occurence Lists
    occLists = iter(tp.tree.occList)

    # For the First Entry, compute the Candidate Expansions
    tid = next(occLists)

    # Compute the candidates starting at the root and from a single occurence
    return compute_blanket_frequent_candidates(
        tp,
        tree=tp.tree,
        tid=tid,
        treeBank=treeBank,
        min_sup=min_sup,
        strategy=strategy,
    )


def check_seq_frequent_blanket_match_left_right(
    tp: CMTreePattern,
    tree: CMConcurrencyTree,
    treeBank: Mapping[int, TreeBankEntry],
    min_sup: int,
    strategy: FrequencyCountingStrategy,
):

    left_sup = Counter()
    right_sup = Counter()

    lChildOccList = tree.children[0].occList
    rChildOccList = tree.children[-1].occList

    supToGain = tp.support

    for oId, occurences in tree.occList.items():
        rootIds = [e[0] for e in tp.rmo[oId]]
        lOccs, rOccs = _compute_left_right_seq_occurences(
            strategy,
            oId,
            treeBank,
            rootIds,
            occurences,
            lChildOccList[oId],
            rChildOccList[oId],
        )

        left_sup.update(lOccs)
        right_sup.update(rOccs)

        if _check_if_any_support_above_threshold(min_sup, left_sup, right_sup):
            return True

        else:
            supToGain = _update_subToGain(treeBank, strategy, supToGain, oId, tp.rmo[oId])

            # Break Early if no counter can become frequent
            if _check_if_no_more_supToGain(min_sup, supToGain, left_sup, right_sup):
                return False  # No Frequent Child to be found

    return False  # No Frequent Child found


def _check_if_any_support_above_threshold(min_sup: int, *supCounters: Counter):

    # Check if any of the counters has a frequent element
    for supCounter in supCounters:

        if supCounter and supCounter.most_common(1)[0][1] > min_sup:
            return True

    return False


def _check_if_no_more_supToGain(min_sup: int, supToGain: int, *supCounters: Counter):

    tmp = []

    for supCounter in supCounters:

        if supCounter:
            tmp.append(min_sup > (supCounter.most_common(1)[0][1] + supToGain))
        
        else: 
            tmp.append(min_sup > supToGain)

    return all(tmp)


def _compute_support_update(
    strategy: FrequencyCountingStrategy,
    tid: int,
    treeBank: Mapping[int, TreeBankEntry],
    *OccCounters
):

    res = []

    for occCounter in OccCounters:

        if strategy == FrequencyCountingStrategy.TraceTransaction:
            res.append({k: treeBank[tid].nTraces for k in occCounter.keys()})

        if strategy == FrequencyCountingStrategy.VariantTransaction:
            res.append({k: 1 for k in occCounter.keys()})

        if strategy == FrequencyCountingStrategy.TraceOccurence:
            res.append({k: v * treeBank[tid].nTraces for k, v in occCounter.items()})

        if strategy == FrequencyCountingStrategy.VariantOccurence:
            res.append({k: v for k, v in occCounter.items()})

    return tuple(res)


def _compute_left_right_seq_occurences(
    strategy: FrequencyCountingStrategy,
    oId: int,
    treeBank: Mapping[int, TreeBankEntry],
    rootIds: List[int],
    occurences: Mapping[int, ConcurrencyTree],
    lChildOccList: Mapping[int, ConcurrencyTree],
    rChildOccList: Mapping[int, ConcurrencyTree],
):

    lOccs = {}
    rOccs = {}

    for idx, occurence in enumerate(occurences):

        lIdx = occurence.children.index(lChildOccList[idx])

        if lIdx > 0 and occurence.children[lIdx - 1].label:
            lOcc = occurence.children[lIdx - 1].label

            if lOcc in lOccs:
                lOccs[lOcc].add(rootIds[idx])
            else:
                lOccs[lOcc] = set([rootIds[idx]])

        rIdx = occurence.children.index(rChildOccList[idx])

        if rIdx < (len(occurence.children) - 1) and occurence.children[rIdx + 1].label:

            rOcc = occurence.children[rIdx + 1].label

            if rOcc in rOccs:
                rOccs[rOcc].add(rootIds[idx])
            else:
                rOccs[rOcc] = set([rootIds[idx]])

    lOccs = {k: len(v) for k, v in lOccs.items()}
    rOccs = {k: len(v) for k, v in rOccs.items()}

    return _compute_support_update(strategy, oId, treeBank, lOccs, rOccs)


def _compute_bottom_occurences(
    strategy: FrequencyCountingStrategy,
    oId: int,
    treeBank: Mapping[int, TreeBankEntry],
    rootIds: List[int],
    occurences: Mapping[int, ConcurrencyTree],
):

    bOccs = {}

    for idx, occurence in enumerate(occurences):

        for bOcc in get_child_labels(occurence.children):

            if bOcc in bOccs:
                bOccs[bOcc].add(rootIds[idx])
            else:
                bOccs[bOcc] = set([rootIds[idx]])

    bOccs = {k: len(v) for k, v in bOccs.items()}

    return _compute_support_update(strategy, oId, treeBank, bOccs)


def check_frequent_blanket_match_bottom(
    tp: CMTreePattern,
    tree: CMConcurrencyTree,
    treeBank: Mapping[int, TreeBankEntry],
    min_sup: int,
    strategy: FrequencyCountingStrategy,
):

    bottom_sup = Counter()
    supToGain = tp.support

    for oId, occurences in tree.occList.items():
        rootIds = [e[0] for e in tp.rmo[oId]]
        (bOccs,) = _compute_bottom_occurences(
            strategy, oId, treeBank, rootIds, occurences
        )

        try:
            bottom_sup.update(bOccs)
        except:
            print()
            print("bOccs", bOccs)

        if _check_if_any_support_above_threshold(min_sup, bottom_sup):
            return True

        else:
            supToGain = _update_subToGain(treeBank, strategy, supToGain, oId, tp.rmo[oId])

            # Break Early if no counter can become frequent
            if _check_if_no_more_supToGain(min_sup, supToGain, bottom_sup):
                return False  # No Frequent Child to be found

    return False  # No Frequent Child found

def check_concurrent_frequent_blanket_match_left_right(
    tp: CMTreePattern,
    tree: CMConcurrencyTree,
    treeBank: Mapping[int, TreeBankEntry],
    min_sup: int,
    strategy: FrequencyCountingStrategy,
):

    left_sup = Counter()
    right_sup = Counter()
    between_sup = Counter()

    lChildOccList = tree.children[0].occList
    rChildOccList = tree.children[-1].occList

    children_labels = get_child_labels(tree.children[1:-1])
    
    supToGain = tp.support

    for oId, occurences in tree.occList.items():

        rootIds = [e[0] for e in tp.rmo[oId]]
        lOccs, rOccs, bOccs = _compute_left_right_con_occurences(
            strategy,
            oId,
            treeBank,
            rootIds,
            occurences,
            lChildOccList[oId],
            rChildOccList[oId],
            children_labels,
        )

        left_sup.update(lOccs)
        right_sup.update(rOccs)
        between_sup.update(bOccs)
        
        if _check_if_any_support_above_threshold(
            min_sup, left_sup, right_sup, between_sup
        ):
            return True

        else:
            
            supToGain = _update_subToGain(treeBank, strategy, supToGain, oId, tp.rmo[oId])

            # Break Early if no counter can become frequent
            if _check_if_no_more_supToGain(
                min_sup, supToGain, left_sup, right_sup, between_sup
            ):
                return False  # No Frequent Child to be found

    return False  # No Frequent Child found


def _compute_left_right_con_occurences(
    strategy: FrequencyCountingStrategy,
    oId: int,
    treeBank: Mapping[int, TreeBankEntry],
    rootIds: List[int],
    occurences: Mapping[int, ConcurrencyTree],
    lChildOccList: Mapping[int, ConcurrencyTree],
    rChildOccList: Mapping[int, ConcurrencyTree],
    children_labels: Set[str],
):

    lOccs = {}
    rOccs = {}
    bOccs = {}

    for idx, occurence in enumerate(occurences):

        lIdx = occurence.children.index(lChildOccList[idx])

        if lIdx > 0:

            for lOcc in get_child_labels(occurence.children[:lIdx]):

                if lOcc in lOccs:
                    lOccs[lOcc].add(rootIds[idx])
                else:
                    lOccs[lOcc] = set([rootIds[idx]])

        rIdx = occurence.children.index(rChildOccList[idx])

        if rIdx < len(occurence.children) - 1:

            for rOcc in get_child_labels(occurence.children[rIdx + 1 :]):

                if rOcc in rOccs:
                    rOccs[rOcc].add(rootIds[idx])
                else:
                    rOccs[rOcc] = set([rootIds[idx]])

        if lIdx != rIdx:

            betweenSiblings = get_child_labels(occurence.children[lIdx + 1 : rIdx])

            for child in children_labels:
                betweenSiblings.remove(child)

            for bOcc in betweenSiblings:
                if bOcc in bOccs:
                    bOccs[bOcc].add(rootIds[idx])
                else:
                    bOccs[bOcc] = set([rootIds[idx]])

    lOccs = {k: len(v) for k, v in lOccs.items()}
    rOccs = {k: len(v) for k, v in rOccs.items()}
    bOccs = {k: len(v) for k, v in bOccs.items()}
    
    return _compute_support_update(strategy, oId, treeBank, lOccs, rOccs, bOccs)


def check_concurrent_frequent_blanket_match(
    tp: CMTreePattern,
    tree: CMConcurrencyTree,
    treeBank: Mapping[int, TreeBankEntry],
    min_sup: int,
    strategy: FrequencyCountingStrategy,
):

    if len(tree.children) > 0:
        return check_concurrent_frequent_blanket_match_left_right(
            tp,
            tree,
            treeBank=treeBank,
            min_sup=min_sup,
            strategy=strategy,
        )

    else:
        return False
        """
        return check_frequent_blanket_match_bottom(
            tp,
            tree,
            treeBank=treeBank,
            min_sup=min_sup,
            strategy=strategy,
            tSize=tSize,
            tTree=tTree,
        )
        """


def check_seq_frequent_blanket_match(
    tp: CMTreePattern,
    tree: CMConcurrencyTree,
    treeBank: Mapping[int, TreeBankEntry],
    min_sup: int,
    strategy: FrequencyCountingStrategy,
):

    if len(tree.children) > 0:
        return check_seq_frequent_blanket_match_left_right(
            tp,
            tree,
            treeBank=treeBank,
            min_sup=min_sup,
            strategy=strategy,
        )
    else:
        return False
        pass 

        """
        return check_frequent_blanket_match_bottom(
            tp,
            tree,
            treeBank=treeBank,
            min_sup=min_sup,
            strategy=strategy,
            tSize=tSize,
            tTree=tTree,
        )
        """


def compute_blanket_frequent_candidates(
    tp: CMTreePattern,
    tree: CMConcurrencyTree,
    tid: int,
    treeBank: Mapping[int, TreeBankEntry],
    min_sup: int,
    strategy: FrequencyCountingStrategy,
):

    # Is Empty
    freqBlanketNotEmpty = False

    """
    if tree.op == cTreeOperator.Sequential:
        freqBlanketNotEmpty |= check_seq_frequent_blanket_match(
        tp,
        tree,
        treeBank=treeBank,
        min_sup=min_sup,
        strategy=strategy,
    )
    """

    if tree.op == cTreeOperator.Concurrent or tree.op == cTreeOperator.Fallthrough:
        freqBlanketNotEmpty |= check_concurrent_frequent_blanket_match(
            tp,
            tree,
            treeBank=treeBank,
            min_sup=min_sup,
            strategy=strategy,
        )

    if not freqBlanketNotEmpty:
        for child in tree.children:
            
            if child.op: 
                freqBlanketNotEmpty |= compute_blanket_frequent_candidates(
                    tp=tp,
                    tree=child,
                    tid=tid,
                    treeBank=treeBank,
                    min_sup=min_sup,
                    strategy=strategy,
                )
                
            if freqBlanketNotEmpty: 
                break

    return freqBlanketNotEmpty
