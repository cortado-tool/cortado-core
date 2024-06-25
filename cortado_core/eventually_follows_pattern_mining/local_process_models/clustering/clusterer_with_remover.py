from typing import List, Optional

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.cluster_remover import (
    ClusterRemover,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.clusterer import (
    Clusterer,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class ClustererWithRemover(Clusterer):
    def __init__(self, clusterer: Clusterer, remover: Optional[ClusterRemover]):
        self.clusterer = clusterer
        self.remover = remover

    def calculate_clusters(
        self, patterns: List[EventuallyFollowsPattern]
    ) -> List[List[EventuallyFollowsPattern]]:
        clusters = self.clusterer.calculate_clusters(patterns)

        if self.remover is not None:
            clusters = self.remover.remove_clusters(clusters)

        return clusters
