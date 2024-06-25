from collections import defaultdict
from typing import List, Set

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.clusterer import (
    Clusterer,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator


class StartActivityClusterer(Clusterer):
    def calculate_clusters(
        self, patterns: List[EventuallyFollowsPattern]
    ) -> List[List[EventuallyFollowsPattern]]:
        clusters = defaultdict(list)

        for pattern in patterns:
            start_activities = self.get_start_activities(pattern)

            for start_activity in start_activities:
                clusters[start_activity].append(pattern)

        return list(clusters.values())

    def get_start_activities(self, pattern: EventuallyFollowsPattern) -> Set[str]:
        return self.__get_start_activities_for_infix_pattern(pattern.sub_patterns[0])

    def __get_start_activities_for_infix_pattern(self, pattern: SubPattern) -> Set[str]:
        if pattern.label is not None:
            return {pattern.label}

        if pattern.operator == cTreeOperator.Sequential:
            return self.__get_start_activities_for_infix_pattern(pattern.children[0])

        result = set()

        for child in pattern.children:
            result = result.union(self.__get_start_activities_for_infix_pattern(child))

        return result
