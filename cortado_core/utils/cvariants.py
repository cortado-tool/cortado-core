from collections import Counter
from copy import copy
from dataclasses import dataclass
from typing import Mapping, Tuple, Dict, List, Any
from collections import defaultdict

from cortado_core.utils.timestamp_utils import TimeUnit, transform_timestamp

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.log.util.interval_lifecycle import to_interval
from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_START_TIMESTAMP_KEY, DEFAULT_TIMESTAMP_KEY, \
    DEFAULT_TRANSITION_KEY
from .cgroups_graph import cgroups_graph, ConcurrencyGroup
from .parallel_utils import workload_split, workload_split_graphs
from .split_graph import Group, LeafGroup, ParallelGroup, SequenceGroup, split_group

ACTIVITY_INSTANCE_KEY = 'cortado_activity_instance'


@dataclass
class SubvariantNode:
    activity: str
    lifecycle: str
    activity_instance: int
    performance_stats: Any

    def __hash__(self):
        return hash((self.activity, self.lifecycle, self.activity_instance))

    def __eq__(self, other):
        return (self.activity, self.lifecycle, self.activity_instance) == (
            other.activity, other.lifecycle, other.activity_instance)


def create_graphs(log_renamed: EventLog, interval_log: EventLog, use_mp: bool, time_granularity, pool):
    if not use_mp or pool is None:
        return __create_graphs(log_renamed, interval_log, time_granularity)

    graphs = {}
    log_renamed_bounded, interval_log_bounded, time_granularity_bounded = workload_split(log_renamed, interval_log,
                                                                                         time_granularity)
    res = pool.starmap(__create_graphs, zip(log_renamed_bounded, interval_log_bounded, time_granularity_bounded))
    while len(res) > 0:  # "Merge" the results of all workers
        partial_result = res.pop()
        for variant in partial_result:
            graphs[variant] = graphs.get(
                variant, []) + partial_result[variant]

    return graphs


def __create_graphs(log_renamed: EventLog, interval_log: EventLog, time_granularity: TimeUnit) -> Mapping[
    ConcurrencyGroup, List[Trace]]:
    own_results: Dict[ConcurrencyGroup, List[Trace]] = dict()
    for trace, original_trace in zip(log_renamed, interval_log):
        variant: ConcurrencyGroup = cgroups_graph(trace, time_granularity=time_granularity)
        own_results[variant] = own_results.get(variant, []) + [original_trace]

    return own_results


def create_variants(graphs: Mapping[ConcurrencyGroup, List[Trace]], names, id_name_map, use_mp: bool, pool):
    if not use_mp or pool is None:
        return __create_variants(list(graphs.items()), names, id_name_map)

    workload_graphs = workload_split_graphs(graphs)
    workload_names = [names for _ in range(len(workload_graphs))]
    workload_id_name_map = [id_name_map for _ in range(len(workload_graphs))]

    variants = dict()
    res = pool.starmap(__create_variants, zip(workload_graphs, workload_names, workload_id_name_map))
    while len(res) > 0:  # "Merge" the results of all workers
        partial_result = res.pop()
        for v in partial_result:
            variants[v] = graphs.get(v, []) + partial_result[v]

    return variants


def __create_variants(graphs: List[Tuple[ConcurrencyGroup, List[Trace]]], names, id_name_map):
    variants = dict()
    for variant, traces in graphs:
        v = split_group(variant)

        # Restore name and add a Reference to the Group
        variant.restore_names(names, id_name_map)
        variants[v] = variants.get(v, []) + [(variant, traces)]

    return variants


def get_concurrency_variants(log: EventLog, use_mp: bool = False, time_granularity: TimeUnit = min(TimeUnit),
                             pool=None):
    if log.attributes.get('PM4PY_TYPE', "") != 'interval':
        if DEFAULT_TRANSITION_KEY in log[0][0]:
            traces = [Trace([e for e in trace if e[DEFAULT_TRANSITION_KEY].lower() == 'start'
                             or e[DEFAULT_TRANSITION_KEY].lower() == 'complete'], attributes=trace.attributes,
                            properties=trace.properties)
                      for trace in log]
            log = EventLog(traces, attributes=copy(log.attributes),
                           extensions=log.extensions, classifiers=log.classifiers,
                           omni_present=log.omni_present, properties=log.properties)

    interval_log = to_interval(log)
    log_renamed, names = unique_activities(interval_log)
    graphs = create_graphs(log_renamed, interval_log, use_mp, time_granularity, pool)

    id_name_map = {name: id for id, name in enumerate(names.keys())}
    variants = create_variants(graphs, names, id_name_map, use_mp, pool)

    res_variants = {}
    for v, ls in variants.items():
        for g, ts in ls:
            res_variants[v] = res_variants.get(v, []) + ts
            v.graphs[g] = v.graphs.get(g, 0) + len(ts)

    res_variants = restore_names(res_variants, names)

    return res_variants


def get_detailed_variants(traces, time_granularity: TimeUnit = min(TimeUnit)):
    variants = {}
    traces = to_interval(EventLog(traces))
    for trace in traces:
        act_counter = defaultdict(int)
        v = defaultdict(list)
        trace = __sort_trace_on_timestamps(trace, time_granularity)
        for event in trace:
            start = transform_timestamp(event[DEFAULT_START_TIMESTAMP_KEY], time_granularity)
            complete = transform_timestamp(event[DEFAULT_TIMESTAMP_KEY], time_granularity)
            activity = event[DEFAULT_NAME_KEY]
            activity_instance = act_counter[activity]
            event[ACTIVITY_INSTANCE_KEY] = activity_instance
            act_counter[activity] += 1

            v[start] += [SubvariantNode(activity, 'start', activity_instance, None)]
            v[complete] += [SubvariantNode(activity, 'complete', activity_instance, None)]

        v = sorted(v.items(), key=lambda x: x[0])
        v = tuple(tuple(vv[1]) for vv in v)
        variants[v] = variants.get(v, []) + [trace]

    return variants


def unique_activities(log):
    log = to_interval(log)

    log = copy(log)
    log._list = [Trace([copy(e) for e in trace]) for trace in log]

    activity_names = {}
    for trace in log:
        c = Counter()
        for event in trace:
            activity = event[DEFAULT_NAME_KEY]
            new_name = activity + str(c[activity])

            event[DEFAULT_NAME_KEY] = new_name
            event['@@startevent_concept:name'] = new_name

            activity_names[new_name] = activity

            c[activity] += 1

    return log, activity_names


def restore_name(event, names):
    event[DEFAULT_NAME_KEY] = names[event[DEFAULT_NAME_KEY]]


def restore_names(variants, names) -> Dict[Group, List[Trace]]:
    variants_new = {}
    for v in variants:
        v_new = restore_names_rek(v, names)
        variants_new[v_new] = variants_new.get(v_new, []) + variants[v]
        v_new.graphs = v.graphs
    return variants_new


def restore_names_rek(variant, names):
    if isinstance(variant, SequenceGroup):
        g = SequenceGroup([restore_names_rek(g, names) for g in variant])
        return g
    elif isinstance(variant, ParallelGroup):
        g = ParallelGroup([restore_names_rek(g, names) for g in variant])
        return g

    elif isinstance(variant, LeafGroup):
        g = LeafGroup([names[e] for e in variant])
        return g

    return variant


def __sort_trace_on_timestamps(trace, time_granularity):
    events = sorted(trace._list, key=lambda x: __get_sort_tuple(x, time_granularity))
    new_trace = Trace(events, attributes=trace.attributes)
    return new_trace


def __get_sort_tuple(event, time_granularity):
    start_timestamp = transform_timestamp(event[DEFAULT_START_TIMESTAMP_KEY], time_granularity)
    complete_timestamp = transform_timestamp(event[DEFAULT_TIMESTAMP_KEY], time_granularity)

    return start_timestamp, complete_timestamp, event[DEFAULT_NAME_KEY]
