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
from cortado_core.subprocess_discovery.subtree_mining.right_most_path_extension.support_counting import (
    check_min_sup,
)
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry
from cortado_core.tests.pattern_mining.util.tree_pattern_2_patterns import (
    TreePattern_2_patterns as TreePattern,
)


def _create_operator_leaf_2_pattern(activity: str, operator: cTreeOperator):
    leaf = ConcurrencyTree(None, None, None, activity, None)
    parent = ConcurrencyTree([leaf], None, None, None, operator)

    leaf.parent = parent

    tp = TreePattern(parent, leaf, 0)

    tp.size = 2

    return tp


def _create_operator_operator_2_pattern(
    child_operator: cTreeOperator, parent_operator: cTreeOperator
):
    leaf = ConcurrencyTree(None, None, None, None, child_operator)
    parent = ConcurrencyTree([leaf], None, None, None, parent_operator)

    leaf.parent = parent

    tp = TreePattern(parent, leaf, 0)

    tp.size = 2

    return tp


def _create_rmo_list_entries(
    tid: int, tree: ConcurrencyTree, C2: Mapping[any, TreePattern]
):
    if pOp := tree.op:
        # FOr every child
        for child in tree.children:
            # If it is an operator node, set the label accordingly and recurse over its children
            if cT := child.op:
                _create_rmo_list_entries(tid, child, C2)

            # Else simply use the child label in the next step
            else:
                cT = child.label

            # If the entry exists, add the child to the rmo list as a place of occurence
            if (pOp, cT) in C2:
                C2[(pOp, cT)].add_rmo((tid, tree.id, child))


def generate_initial_candidates(
    treebank: Mapping[int, TreeBankEntry],
    min_sup: int,
    frequency_counting_strat: FrequencyCountingStrategy,
    fSets: FrequentActivitySets,
):
    C2 = dict()

    # Create all frequent "P" -> Activity patterns
    for activity in fSets.ccR:
        C2[(cTreeOperator.Concurrent, activity)] = _create_operator_leaf_2_pattern(
            activity, cTreeOperator.Concurrent
        )

    for child, parent in itertools.product(
        [cTreeOperator.Concurrent, cTreeOperator.Sequential, cTreeOperator.Fallthrough],
        [cTreeOperator.Concurrent, cTreeOperator.Sequential],
    ):
        if child != parent:
            C2[(parent, child)] = _create_operator_operator_2_pattern(child, parent)

    for activity in fSets.fA:
        C2[(cTreeOperator.Fallthrough, activity)] = _create_operator_leaf_2_pattern(
            activity, cTreeOperator.Fallthrough
        )

    # Create the frequent "S" -> Activity pattern
    for activity in fSets.efR:
        C2[(cTreeOperator.Sequential, activity)] = _create_operator_leaf_2_pattern(
            activity, cTreeOperator.Sequential
        )

    # Parallelizable

    # Compute the RMO list for the 2-Patterns
    for i in treebank:
        tree = treebank[i].tree
        _create_rmo_list_entries(i, tree, C2)

    F2 = set()

    # Compute the set of frequent 2-Patterns
    for c in C2:
        pattern = C2[c]
        if check_min_sup(pattern, frequency_counting_strat, treebank, min_sup=min_sup):
            F2.add(pattern)
        else:
            # Clean up
            del pattern

    # Clean up
    del C2

    return F2
