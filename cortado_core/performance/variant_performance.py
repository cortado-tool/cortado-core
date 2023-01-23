from collections import Counter
from typing import List, Tuple, Dict, Any

from cortado_core.performance.aggregators import stats
from cortado_core.utils.split_graph import Group, LeafGroup, ParallelGroup, SequenceGroup
from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.log.util.interval_lifecycle import to_interval
from pm4py.objects.log.util.xes import DEFAULT_START_TIMESTAMP_KEY, DEFAULT_TIMESTAMP_KEY
from pm4py.util.xes_constants import DEFAULT_NAME_KEY

DEFAULT_NAME_KEY_UNIQUE = DEFAULT_NAME_KEY + "_unique"


def assign_variants_performances(variants: Dict[int, Tuple[Group, List[Trace], List, Any]]):
    for variant, traces, _, info in variants.values():
        if info.is_user_defined:
            continue
        log = EventLog(traces)
        log = to_interval(log)
        v_unique = unique_names(variant)

        unique_activity_names(log)
        assign_wait_time(variant, v_unique, log)
        assign_variant_service_time(variant, v_unique, log)


def assign_variant_service_time(variant: Group, variant_unique: Group, traces: List[Trace]):
    events = get_variant_events(variant_unique, traces)
    service_times = []
    for t_events in events:
        if len(t_events) == 0:
            continue
        e_start = min(t_events, key=lambda e: e[DEFAULT_START_TIMESTAMP_KEY] if DEFAULT_START_TIMESTAMP_KEY in e else e[
            DEFAULT_TIMESTAMP_KEY])
        e_end = max(t_events, key=lambda e: e[DEFAULT_TIMESTAMP_KEY])

        t_start = e_start[DEFAULT_START_TIMESTAMP_KEY] if DEFAULT_START_TIMESTAMP_KEY in e_start else e_start[
            DEFAULT_TIMESTAMP_KEY]
        t_end = e_end[DEFAULT_TIMESTAMP_KEY]

        service_time = (t_end - t_start).total_seconds()
        service_times.append(service_time)

    variant.performance['service_time'] = stats(service_times)

    if type(variant) != LeafGroup and len(events) > 0:
        for g, g_unique in zip(variant, variant_unique):
            assign_variant_service_time(g, g_unique, traces)


def assign_wait_time(variant: Group, variant_unique: Group, traces: List[Trace]):
    if type(variant) == SequenceGroup:
        for i in range(variant_unique.list_length() - 1):
            e1 = variant_unique[i]
            e2 = variant_unique[i + 1]
            e2_orig = variant[i + 1]
            wait_time = get_wait_time_between(e1, e2, traces)
            e2_orig.performance['wait_time'] = wait_time

    if type(variant) == ParallelGroup:
        assign_wait_times_parallel(variant, variant_unique, traces)

    if type(variant) != LeafGroup:
        for g, g_unique in zip(variant, variant_unique):
            assign_wait_time(g, g_unique, traces)


def get_wait_time_between(g1: Group, g2: Group, traces: List[Trace]):
    events_g1 = get_variant_events(g1, traces)
    events_g2 = get_variant_events(g2, traces)

    wait_times = []
    for t_events_g1, t_events_g2 in zip(events_g1, events_g2):
        g1_end = max(t_events_g1, key=lambda e: e[DEFAULT_TIMESTAMP_KEY])
        g2_start = min(t_events_g2,
                       key=lambda e: e[DEFAULT_START_TIMESTAMP_KEY] if DEFAULT_START_TIMESTAMP_KEY in e else e[
                           DEFAULT_TIMESTAMP_KEY])
        wait_time = (g2_start[DEFAULT_START_TIMESTAMP_KEY] - g1_end[DEFAULT_TIMESTAMP_KEY]).total_seconds()
        wait_times.append(wait_time)

    results_dict = stats(wait_times)
    return results_dict


def assign_wait_times_parallel(variant: ParallelGroup, variant_unique: ParallelGroup, traces: List[Trace]):
    events = get_variant_events(variant_unique, traces)

    def get_start(trace):
        start = min(trace, key=lambda e: e[DEFAULT_START_TIMESTAMP_KEY] if DEFAULT_START_TIMESTAMP_KEY in e else e[
            DEFAULT_TIMESTAMP_KEY])
        return start[DEFAULT_START_TIMESTAMP_KEY] if DEFAULT_START_TIMESTAMP_KEY in start else start[
            DEFAULT_TIMESTAMP_KEY]

    def get_end(trace):
        end = max(trace, key=lambda e: e[DEFAULT_TIMESTAMP_KEY])
        return end[DEFAULT_TIMESTAMP_KEY]

    start_ends = [(get_start(trace), get_end(trace)) for trace in events]

    for g, g_unique in zip(variant, variant_unique):
        events_g = get_variant_events(g_unique, traces)

        wait_times = []
        wait_times_next = []

        for (start, end), trace_g in zip(start_ends, events_g):
            start_g = min(trace_g,
                          key=lambda e: e[DEFAULT_START_TIMESTAMP_KEY] if DEFAULT_START_TIMESTAMP_KEY in e else e[
                              DEFAULT_TIMESTAMP_KEY])
            end_g = max(trace_g, key=lambda e: e[DEFAULT_TIMESTAMP_KEY])

            t_start_g = start_g[DEFAULT_START_TIMESTAMP_KEY] if DEFAULT_START_TIMESTAMP_KEY in start_g else start_g[
                DEFAULT_TIMESTAMP_KEY]
            t_end_g = end_g[DEFAULT_TIMESTAMP_KEY]

            wait_times.append((t_start_g - start).total_seconds())
            wait_times_next.append((end - t_end_g).total_seconds())

        g.performance['wait_time_start'] = stats(wait_times)
        g.performance['wait_time_end'] = stats(wait_times_next)


variant_events_cache = {}


def get_variant_events(variant, traces):
    cache_key = (str(variant.serialize(include_performance=False)), id(traces))
    if cache_key in variant_events_cache:
        return variant_events_cache[cache_key]

    activities = get_all_activities(variant)
    events = [[e for e in t if e[DEFAULT_NAME_KEY_UNIQUE] in activities]
              for t in traces]

    # variant_events_cache[cache_key] = events
    return events


get_all_activities_cache = {}


def get_all_activities(variant):
    cache_key = str(variant.serialize(include_performance=False))
    if cache_key in get_all_activities_cache:
        return get_all_activities_cache[cache_key]

    all_activities = []
    if isinstance(variant, (SequenceGroup, ParallelGroup)):
        all_activities = [e for g in variant for e in get_all_activities(g)]
    elif isinstance(variant, LeafGroup):
        all_activities = [e for e in variant]

    get_all_activities_cache[cache_key] = all_activities
    return all_activities


def unique_activity_names(traces):
    for t in traces:
        counter = Counter()
        for e in t:
            unique_name(e, counter)


def unique_name(event, counter=None):
    if counter is None:
        counter = Counter()
    event[DEFAULT_NAME_KEY_UNIQUE] = event[DEFAULT_NAME_KEY] + str(counter[event[DEFAULT_NAME_KEY]])
    counter[event[DEFAULT_NAME_KEY]] += 1


def unique_names(variant):
    variant = unique_names_rek(variant, counter=Counter())
    return variant


def unique_name_v(activity, counter=None):
    if counter is None:
        counter = Counter()
    unique_activity_name = activity + str(counter[activity])
    counter[activity] += 1
    return unique_activity_name


def unique_names_rek(variant, counter=None):
    if counter is None:
        counter = Counter()
    if isinstance(variant, SequenceGroup):
        return SequenceGroup([unique_names_rek(g, counter) for g in variant])
    elif isinstance(variant, ParallelGroup):
        return ParallelGroup([unique_names_rek(g, counter) for g in variant])
    elif isinstance(variant, LeafGroup):
        return LeafGroup([unique_name_v(e, counter) for e in variant])

    return variant
