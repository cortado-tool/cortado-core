from typing import List

import pm4py
from pm4py.objects.log.obj import EventLog

from cortado_core.eventually_follows_pattern_mining.local_process_models.discovery.discoverer import (
    Discoverer,
)
from cortado_core.eventually_follows_pattern_mining.local_process_models.discovery.sequentialize_pattern import (
    sequentialize_pattern,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern


class InductiveMiner(Discoverer):
    def discover_model(self, patterns: List[EventuallyFollowsPattern]):
        traces = set()

        for pattern in patterns:
            traces = traces.union(sequentialize_pattern(pattern))

        return pm4py.discover_process_tree_inductive(EventLog(traces))
