from typing import Set
from cortado_core.subprocess_discovery.subtree_mining.maximal_connected_components.valid_subpatterns import (
    _compute_left_most_path_eliminated_leafs,
    _compute_left_most_path_eliminated_subtree,
    _compute_right_most_path_eliminated_leafs,
    _compute_right_most_path_eliminated_subtree,
    _compute_subtree_eliminated_children,
    _get_root_enclosed_subtrees,
    compute_valid_leaf_eliminated_children,
)
from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import TreePattern

# Pruning Strategy testing if all subtrees of size k-1 of a size k subtree are frequent
def n_tree_prune(tp: TreePattern, patterns: Set[str]):

    return (
        all(
            [sub in patterns for sub in compute_valid_leaf_eliminated_children(tp.tree)]
        )
        and all(
            [
                sub in patterns if level > 2 else True
                for level, sub in _compute_subtree_eliminated_children(tp.tree)
                if level > 2
            ]
        )
        and all(
            [
                sub in patterns if level > 2 else True
                for level, sub in _get_root_enclosed_subtrees(tp.tree, False)
            ]
        )
        and all(
            [
                sub in patterns
                for sub in _compute_left_most_path_eliminated_leafs(tp.tree)
            ]
        )
        and all(
            [
                sub in patterns
                for sub in _compute_right_most_path_eliminated_leafs(tp.tree)
            ]
        )
        and all(
            [
                sub in patterns if level > 2 else True
                for level, sub in _compute_left_most_path_eliminated_subtree(tp.tree)
            ]
        )
        and all(
            [
                sub in patterns if level > 2 else True
                for level, sub in _compute_right_most_path_eliminated_subtree(tp.tree)
            ]
        )
    )
