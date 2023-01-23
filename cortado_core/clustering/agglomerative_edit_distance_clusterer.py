from collections import defaultdict
from typing import List

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from cortado_core.clustering.clusterer import Clusterer
from cortado_core.clustering.edit_distance import calculate_edit_distance
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class AgglomerativeEditDistanceClusterer(Clusterer):
    def __init__(self, max_distance):
        self.max_distance = max_distance

    def calculate_clusters(self, variants: List[ConcurrencyTree]) -> List[List[ConcurrencyTree]]:
        if len(variants) == 0:
            return []
        elif len(variants) == 1:
            return [[variants[0]]]

        distance_matrix = self.calculate_distance_matrix(variants)
        result = AgglomerativeClustering(affinity='precomputed', distance_threshold=self.max_distance,
                                         linkage='complete', n_clusters=None).fit(distance_matrix)

        cluster_dict = defaultdict(list)
        for i in range(len(variants)):
            cluster_dict[result.labels_[i]].append(variants[i])

        return [cluster_dict[i] for i in cluster_dict.keys()]

    @staticmethod
    def calculate_distance_matrix(variants: List[ConcurrencyTree], distance_func=calculate_edit_distance):
        n = len(variants)
        result = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(i + 1, n):
                result[i, j] = distance_func(variants[i], variants[j])
                # assumes that the distance function is symmetric
                result[j, i] = result[i, j]

        return result
