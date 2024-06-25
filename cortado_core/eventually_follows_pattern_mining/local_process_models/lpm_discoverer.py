from typing import List

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.clusterer import (
    Clusterer,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.discovery.discoverer import (
    Discoverer,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class LpmDiscoverer:
    def __init__(self, clusterer: Clusterer, discoverer: Discoverer):
        self.clusterer = clusterer
        self.discoverer = discoverer

    def discover_lpms(self, patterns: List[EventuallyFollowsPattern]):
        clustered_patterns = self.clusterer.calculate_clusters(patterns)

        # for i, cl in enumerate(clustered_patterns):
        #     print(f'Cluster {i}')
        #     for p in cl:
        #         print(p)

        models = []
        for cluster in clustered_patterns:
            model = self.discoverer.discover_model(cluster)
            models.append((model, cluster))

        return models
