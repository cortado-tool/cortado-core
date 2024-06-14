from collections import defaultdict
from typing import List
from pyclustering.cluster.kmedoids import kmedoids

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.clusterer import (
    Clusterer,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class EditDistanceKMedoidsClusterer(Clusterer):
    def __init__(
        self, n_clusters: int, postprocess_add_threshold: int, distance_matrix
    ):
        self.n_clusters = n_clusters
        self.postprocess_add_threshold = postprocess_add_threshold
        self.distance_matrix = distance_matrix

    def calculate_clusters(
        self, patterns: List[EventuallyFollowsPattern]
    ) -> List[List[EventuallyFollowsPattern]]:
        initial_medoids = [i for i in range(self.n_clusters)]
        kmedoids_instance = kmedoids(
            self.distance_matrix, initial_medoids, data_type="distance_matrix"
        )
        kmedoids_instance.process()
        clusters = kmedoids_instance.get_clusters()
        medoids = kmedoids_instance.get_medoids()

        # clusters = self.__postprocess_clusters(clusters, medoids, self.distance_matrix)
        clusters = [[patterns[i] for i in cluster] for cluster in clusters]

        return clusters

    def __postprocess_clusters(
        self, clusters: List[List[int]], medoids: List[int], distance_matrix
    ):
        add_to_cluster = defaultdict(list)
        for i, cluster in enumerate(clusters):
            for other_cluster in clusters[0:i] + clusters[i + 1 :]:
                for pattern_index in other_cluster:
                    if (
                        distance_matrix[pattern_index, medoids[i]]
                        < self.postprocess_add_threshold
                    ):
                        add_to_cluster[i].append(pattern_index)
                        print("add")

        for c_index, to_add in add_to_cluster.items():
            clusters[c_index] += to_add

        return clusters
