from typing import List, Set

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.process_tree_utils.miscellaneous import get_all_leaf_node_labels
from cortado_core.trace_ordering.scoring.scorer import Scorer
from cortado_core.utils.split_graph import Group, LeafGroup


class MissingActivitiesScorer(Scorer):
    def score(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidate: Group) -> float:
        activities_in_tree, _ = get_all_leaf_node_labels(process_tree)
        activities_in_trace = self.get_activities_in_trace(variant_candidate)

        missing_activities = activities_in_trace.difference(activities_in_tree)

        return len(missing_activities)

    def get_activities_in_trace(self, trace: Group) -> Set[str]:
        activities: Set[str] = set()
        for child in trace:
            if isinstance(child, LeafGroup):
                for c in child:
                    activities.add(c)
            else:
                activities = activities.union(self.get_activities_in_trace(child))

        return activities
