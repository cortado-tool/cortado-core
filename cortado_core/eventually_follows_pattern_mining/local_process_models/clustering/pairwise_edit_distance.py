from typing import List

import numpy as np

from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    get_preorder_sorted_sub_pattern_nodes,
    get_rightmost_leaf,
)


def calculate_pairwise_edit_distance(
    pattern1: EventuallyFollowsPattern, pattern2: EventuallyFollowsPattern
):
    res1 = [-1 for _ in range(len(pattern1))]
    res2 = [-1 for _ in range(len(pattern2))]

    for i in range(len(pattern1)):
        for j in range(i, len(pattern2)):
            dist = calculate_edit_distance(
                pattern1.sub_patterns[i], pattern2.sub_patterns[j]
            )
            if res1[i] == -1 or res1[i] > dist:
                res1[i] = dist
            if res2[j] == -1 or res2[j] > dist:
                res2[j] = dist

    return sum(res1) + sum(res2)


def calculate_edit_distance(sub_pattern1: SubPattern, sub_pattern2: SubPattern) -> int:
    """
    Computes the edit distance for two infix patterns. For an introduction for the calculation, have a
    look at https://arxiv.org/abs/1805.06869.
    """
    m = len(sub_pattern1)
    n = len(sub_pattern2)
    d = np.zeros((m, n))
    D = np.zeros((m + 1, n + 1))
    p1_nodes = get_preorder_sorted_sub_pattern_nodes(sub_pattern1)
    p2_nodes = get_preorder_sorted_sub_pattern_nodes(sub_pattern2)
    key_roots_p1 = get_key_roots(p1_nodes)
    key_roots_p2 = get_key_roots(p2_nodes)
    rightmost_leaves_p1 = get_rightmost_leaves(p1_nodes)
    rightmost_leaves_p2 = get_rightmost_leaves(p2_nodes)

    for k in sorted(key_roots_p1, reverse=True):
        rlxk_id = rightmost_leaves_p1[k]
        for l in sorted(key_roots_p2, reverse=True):
            rlyl_id = rightmost_leaves_p2[l]
            D[rlxk_id + 1, rlyl_id + 1] = 0
            for i in reversed(range(k, rlxk_id + 1)):
                D[i, rlyl_id + 1] = D[i + 1, rlyl_id + 1] + 1
            for j in reversed(range(l, rlyl_id + 1)):
                D[rlxk_id + 1, j] = D[rlxk_id + 1, j + 1] + 1

            for i in reversed(range(k, rlxk_id + 1)):
                rlxi_id = rightmost_leaves_p1[i]
                for j in reversed(range(l, rlyl_id + 1)):
                    rlyj_id = rightmost_leaves_p2[j]
                    renaming_cost = get_renaming_cost(i, j, p1_nodes, p2_nodes)
                    if rlxi_id == rlxk_id and rlyj_id == rlyl_id:
                        D[i, j] = min(
                            [
                                D[i + 1, j] + 1,
                                D[i, j + 1] + 1,
                                D[i + 1, j + 1] + renaming_cost,
                            ]
                        )
                        d[i, j] = D[i, j]
                    else:
                        D[i, j] = min(
                            [
                                D[i + 1, j] + 1,
                                D[i, j + 1] + 1,
                                D[rlxi_id + 1, rlyj_id + 1] + d[i, j],
                            ]
                        )

    return d[0, 0]


def get_renaming_cost(i, j, p1_nodes, p2_nodes):
    node1 = p1_nodes[i - 1]
    node2 = p2_nodes[j - 1]
    if node1.label is not None:
        if node1.label == node2.label:
            return 0
        return 1

    if node1.operator == node2.operator:
        return 0
    return 1


def get_key_roots(preorder_sorted_nodes: List[SubPattern]) -> List[int]:
    rightmost_leaves = set()
    key_roots = []
    root_id = preorder_sorted_nodes[0].id

    for node in preorder_sorted_nodes:
        rightmost_leaf = get_rightmost_leaf(node)
        if rightmost_leaf.id not in rightmost_leaves:
            rightmost_leaves.add(rightmost_leaf.id - root_id)
            key_roots.append(node.id - root_id)

    return key_roots


def get_rightmost_leaves(preorder_sorted_nodes: List[SubPattern]) -> List[int]:
    rightmost_leaves = []
    root_id = preorder_sorted_nodes[0].id

    for node in preorder_sorted_nodes:
        rightmost_leaves.append(get_rightmost_leaf(node).id - root_id)

    return rightmost_leaves
