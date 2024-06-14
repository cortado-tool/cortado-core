from typing import List

import zss

from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
import numpy as np

from cortado_core.eventually_follows_pattern_mining.util.tree import (
    get_preorder_sorted_pattern_nodes,
    get_rightmost_leaf,
)


def calculate_edit_distance(
    pattern1: EventuallyFollowsPattern, pattern2: EventuallyFollowsPattern
) -> int:
    return zss.simple_distance(pattern1, pattern2, get_children, get_label, label_dist)


def get_children(p):
    if isinstance(p, EventuallyFollowsPattern):
        return p.sub_patterns

    return p.children


def get_label(p):
    if isinstance(p, EventuallyFollowsPattern):
        return "..."

    if p.operator is not None:
        return str(p.operator)

    return p.label


def label_dist(a, b):
    if a == b:
        return 0
    return 1


def calculate_edit_distance_own(
    pattern1: EventuallyFollowsPattern, pattern2: EventuallyFollowsPattern
) -> int:
    """
    Computes the edit distance for two eventually follows patterns. For an introduction for the calculation, have a
    look at https://arxiv.org/abs/1805.06869. Note that there are some small deviations in this implementation to ensure
    that the edit distance can not only be calculated for single trees but also for eventually follows patterns (that
    might consist of multiple trees).
    :param pattern1:
    :param pattern2:
    :return:
    """
    m = sum([len(s) for s in pattern1.sub_patterns]) + 1  # +1 for artificial root node
    n = sum([len(s) for s in pattern2.sub_patterns]) + 1  # +1 for artificial root node
    d = np.zeros((m, n))
    D = np.zeros((m + 1, n + 1))
    p1_nodes = get_preorder_sorted_pattern_nodes(pattern1)
    p2_nodes = get_preorder_sorted_pattern_nodes(pattern2)
    key_roots_p1 = get_key_roots(pattern1, p1_nodes)
    key_roots_p2 = get_key_roots(pattern2, p2_nodes)
    rightmost_leaves_p1 = get_rightmost_leaves(pattern1, p1_nodes)
    rightmost_leaves_p2 = get_rightmost_leaves(pattern2, p2_nodes)

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
    if i == 0:
        if j == 0:
            return 0
        return 1

    if j == 0:
        return 1

    node1 = p1_nodes[i - 1]
    node2 = p2_nodes[j - 1]
    if node1.label is not None:
        if node1.label == node2.label:
            return 0
        return 1

    if node1.operator == node2.operator:
        return 0
    return 1


def get_key_roots(
    pattern: EventuallyFollowsPattern, preorder_sorted_nodes: List[SubPattern]
) -> List[int]:
    rightmost_leaves = {pattern.rightmost_leaf.id + 1}
    key_roots = [0]

    for node in preorder_sorted_nodes:
        rightmost_leaf = get_rightmost_leaf(node)
        if rightmost_leaf.id not in rightmost_leaves:
            rightmost_leaves.add(rightmost_leaf.id + 1)
            key_roots.append(node.id + 1)

    return key_roots


def get_rightmost_leaves(
    pattern: EventuallyFollowsPattern, preorder_sorted_nodes: List[SubPattern]
) -> List[int]:
    rightmost_leaves = [pattern.rightmost_leaf.id + 1]

    for node in preorder_sorted_nodes:
        rightmost_leaves.append(get_rightmost_leaf(node).id + 1)

    return rightmost_leaves
