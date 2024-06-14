from typing import List

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.clusterer import (
    Clusterer,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.distance_matrix import (
    calculate_distance_matrix,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.edit_distance_agglomerative_clusterer import (
    EditDistanceAgglomerativeClusterer,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.label_vector_clusterer import (
    LabelVectorClusterer,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.start_activity_clusterer import (
    StartActivityClusterer,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class EditDistanceAgglomerativeClustererWithPreclustering(Clusterer):
    def __init__(self, max_distance, preclustering_type, precalculated_distance_matrix):
        self.max_distance = max_distance
        self.preclustering_type = preclustering_type
        self.precalculated_distance_matrix = precalculated_distance_matrix

    def calculate_clusters(
        self, patterns: List[EventuallyFollowsPattern]
    ) -> List[List[EventuallyFollowsPattern]]:
        # use agglomerative clustering directly if distance matrix is provided
        if self.precalculated_distance_matrix is not None:
            pre_clusters = [patterns]
        else:
            if self.preclustering_type == "start_activities":
                preclusterer = StartActivityClusterer()
            else:
                preclusterer = LabelVectorClusterer(
                    n_clusters=max(1, (len(patterns) // 100))
                )
            pre_clusters = preclusterer.calculate_clusters(patterns)

        final_clusters = []
        for pre_cluster in pre_clusters:
            print("Precluster size", len(pre_cluster))
            distance_matrix = calculate_distance_matrix(pre_cluster)
            clusterer = EditDistanceAgglomerativeClusterer(
                max_distance=self.max_distance, distance_matrix=distance_matrix
            )
            clusters = clusterer.calculate_clusters(pre_cluster)
            final_clusters += clusters

        return final_clusters
