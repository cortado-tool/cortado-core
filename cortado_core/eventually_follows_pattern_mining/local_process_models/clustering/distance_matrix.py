from typing import List
import numpy as np

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.edit_distance import (
    calculate_edit_distance,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.pairwise_edit_distance import (
    calculate_pairwise_edit_distance,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


def calculate_distance_matrix(
    patterns: List[EventuallyFollowsPattern], pairwise_distance=False
):
    distance_func = calculate_edit_distance
    if pairwise_distance:
        distance_func = calculate_pairwise_edit_distance

    print("start cal dist matrix")
    n = len(patterns)
    result = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(i + 1, n):
            result[i, j] = distance_func(patterns[i], patterns[j])
            result[j, i] = result[i, j]

    print("end cal dist matrix")

    return result
