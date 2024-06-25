from typing import List

from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class ClusterRemover:
    def __init__(self, n_clusters: int = -1):
        self.n_clusters = n_clusters

    def remove_clusters(
        self, clusters: List[List[EventuallyFollowsPattern]]
    ) -> List[List[EventuallyFollowsPattern]]:
        if self.n_clusters == -1:
            return clusters

        cluster_max_supports = [
            (max([p.support for p in cluster]), i) for i, cluster in enumerate(clusters)
        ]
        cluster_max_supports = sorted(
            cluster_max_supports, key=lambda elem: elem[0], reverse=True
        )

        usable_cluster_indexes = set(
            [idx for _, idx in cluster_max_supports[: self.n_clusters]]
        )

        new_clusters = [clusters[idx] for idx in usable_cluster_indexes]

        return new_clusters
