from collections import defaultdict
from typing import List
from sklearn.cluster import AgglomerativeClustering

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.clusterer import (
    Clusterer,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class EditDistanceAgglomerativeClusterer(Clusterer):
    def __init__(self, max_distance: int, distance_matrix):
        self.max_distance = max_distance
        self.distance_matrix = distance_matrix

    def calculate_clusters(
        self, patterns: List[EventuallyFollowsPattern]
    ) -> List[List[EventuallyFollowsPattern]]:
        if len(patterns) == 0:
            return []
        elif len(patterns) == 1:
            return [[patterns[0]]]

        result = AgglomerativeClustering(
            affinity="precomputed",
            distance_threshold=self.max_distance,
            linkage="complete",
            n_clusters=None,
        ).fit(self.distance_matrix)

        cluster_dict = defaultdict(list)
        for i in range(len(patterns)):
            cluster_dict[result.labels_[i]].append(patterns[i])

        return [cluster_dict[i] for i in cluster_dict.keys()]
