from typing import Mapping
import networkx as nx
from pm4py.util.xes_constants import DEFAULT_START_TIMESTAMP_KEY, DEFAULT_TIMESTAMP_KEY, DEFAULT_TRANSITION_KEY, \
    DEFAULT_NAME_KEY
from cortado_core.utils.timestamp_utils import TimeUnit, transform_timestamp


class ConcurrencyGroup:
    def __init__(self):
        self.events = []
        self.concurrency_pairs = set()
        self.follows = set()
        self.directly_follows = set()
        self.start_activities = set()
        self.end_activities = set()

    def get(self):
        return (frozenset(self.events), frozenset([frozenset(e) for e in self.concurrency_pairs]),
                frozenset(self.directly_follows), frozenset(self.start_activities), frozenset(self.end_activities),
                frozenset(self.follows))

    def to_simple(self):
        return frozenset(self.events)
        
    def to_nx_graph(self):
        G = nx.DiGraph()

        G.add_nodes_from(self.events)

        for e1, e2 in self.concurrency_pairs:
            G.add_edge(e1, e2)
            G.add_edge(e2, e1)

        for e1, e2 in self.follows:
            G.add_edge(e1, e2)

        for e1, e2 in self.directly_follows:
            G.add_edge(e1, e2)

        return G

    def restore_names(self, names: Mapping[str, str], id_name_map):

        def _restore_names_unary(graph_set):
            tmp = {}

            for e in graph_set:

                if names[e] in tmp:
                    tmp[names[e]].add(id_name_map[e])

                else:
                    tmp[names[e]] = set([(id_name_map[e])])

            return tmp

        def _restore_names_binary(graph_set, sort=False):
            tmp = {}

            for (x, y) in graph_set:

                # Sort Concurrency Pairs, such that the lexigographically smaller one is infront
                if sort:
                    x, y = sorted((x, y))

                if (names[x], names[y]) in tmp:
                    tmp[(names[x], names[y])].add(
                        (id_name_map[x], id_name_map[y]))

                else:
                    tmp[(names[x], names[y])] = set(
                        [(id_name_map[x], id_name_map[y])])

            return tmp

        self.events = _restore_names_unary(self.events)
        self.start_activities = _restore_names_unary(self.start_activities)
        self.end_activities = _restore_names_unary(self.end_activities)

        self.concurrency_pairs = _restore_names_binary(
            self.concurrency_pairs, sort=True)
        self.directly_follows = _restore_names_binary(
            self.directly_follows, sort=False)
        self.follows = _restore_names_binary(self.follows, sort=False)

    def __eq__(self, o: object) -> bool:
        return self.get().__hash__() == o.__hash__()

    def __hash__(self) -> int:
        return self.get().__hash__()

    def __str__(self):
        return f"{{ events: {self.events}, concurrent: {self.concurrency_pairs}, directly_follows: {self.directly_follows}, follows: {self.follows} }}"

    def __repr__(self):
        return self.__str__()


def cgroups_graph(trace, time_granularity):
    trace = sorted(trace, key=lambda e: e[DEFAULT_START_TIMESTAMP_KEY])

    parallel = set()
    follows = set()

    directly_follows = set()
    activities = set()

    start_activities = set()
    not_end_activitites = set()

    is_start = True

    for i, event in enumerate(trace):
        start = transform_timestamp(
            event[DEFAULT_START_TIMESTAMP_KEY], time_granularity)

        complete = transform_timestamp(
            event[DEFAULT_TIMESTAMP_KEY], time_granularity)

        activity = event[DEFAULT_NAME_KEY]
        activities.add(activity)
        earliest_complete = None

        for event2 in trace[i + 1:]:
            start2 = transform_timestamp(
                event2[DEFAULT_START_TIMESTAMP_KEY], time_granularity)
            complete2 = transform_timestamp(
                event2[DEFAULT_TIMESTAMP_KEY], time_granularity)
            activity2 = event2[DEFAULT_NAME_KEY]

            if complete < start2:
                follows.add((activity, activity2))
                not_end_activitites.add(activity)

                if is_start:
                    start_activities.add(activity)

                is_start = False

                if earliest_complete is None or earliest_complete > start2:
                    directly_follows.add((activity, activity2))

                    if earliest_complete is None:
                        earliest_complete = complete2
                    else:
                        earliest_complete = min(earliest_complete, complete2)

            # All other cases are parallel
            else:
                parallel.add((activity, activity2))

                if is_start:
                    start_activities.add(activity)
                    start_activities.add(activity2)

    grp = ConcurrencyGroup()
    grp.events = activities
    grp.follows = follows
    grp.concurrency_pairs = parallel
    grp.directly_follows = directly_follows
    grp.start_activities = start_activities
    grp.end_activities = activities.difference(not_end_activitites)

    return grp
