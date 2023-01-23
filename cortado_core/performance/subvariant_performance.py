from pm4py.objects.log.obj import EventLog, Event, Trace
from pm4py.objects.log.util.interval_lifecycle import to_interval
from pm4py.objects.log.util.xes import DEFAULT_START_TIMESTAMP_KEY, DEFAULT_TIMESTAMP_KEY, DEFAULT_NAME_KEY

from cortado_core.performance.aggregators import stats
from cortado_core.utils.cvariants import ACTIVITY_INSTANCE_KEY, SubvariantNode
from cortado_core.utils.timestamp_utils import TimeUnit, transform_timestamp

from collections import defaultdict
from typing import List, Any
from dataclasses import dataclass


@dataclass
class WaitingTimeEvent:
    start: SubvariantNode
    complete: SubvariantNode
    performance_stats: Any
    anchor: str = 'complete'

    def __hash__(self):
        return hash((self.start, self.complete))

    def __eq__(self, other):
        return (self.start, self.complete) == (other.start, other.complete)


@dataclass
class SubvariantWithPerformance:
    subvariant: Any
    waiting_time_events: List[WaitingTimeEvent]
    global_performance_stats: Any


def calculate_subvariant_performance(subvariant, traces, time_granularity: TimeUnit) -> SubvariantWithPerformance:
    log = EventLog(traces)
    log = to_interval(log)

    global_stats = __get_global_performance_stats(log, time_granularity)
    service_times_per_activity = __get_service_times_per_activity(log, time_granularity)

    subvariant_with_service_times = __append_service_time_to_subvariant(subvariant, service_times_per_activity)
    waiting_time_events = calculate_waiting_time_events(subvariant, traces, time_granularity)

    return SubvariantWithPerformance(subvariant_with_service_times, waiting_time_events,
                                     global_performance_stats=global_stats)


def __get_global_performance_stats(interval_log: EventLog, time_granularity: TimeUnit):
    durations = []
    min_timestamp = None
    max_timestamp = None

    for trace in interval_log:
        for event in trace:
            start_timestamp = transform_timestamp(event[DEFAULT_START_TIMESTAMP_KEY], time_granularity)
            complete_timestamp = transform_timestamp(event[DEFAULT_TIMESTAMP_KEY], time_granularity)

            if min_timestamp is None or start_timestamp < min_timestamp:
                min_timestamp = start_timestamp

            if max_timestamp is None or complete_timestamp > max_timestamp:
                max_timestamp = complete_timestamp

        if max_timestamp is None or min_timestamp is None:
            continue

        durations.append((max_timestamp - min_timestamp).total_seconds())

    return stats(durations)


def __get_service_times_per_activity(interval_log: EventLog, time_granularity: TimeUnit):
    service_times_per_activity = defaultdict(dict)

    for trace in interval_log:
        for event in trace:
            service_time = __calculate_service_time(event, time_granularity)
            activity = event[DEFAULT_NAME_KEY]
            activity_instance = event[ACTIVITY_INSTANCE_KEY]

            service_times_per_activity[activity][activity_instance] = service_times_per_activity[activity].get(
                activity_instance, []) + [service_time]

    return service_times_per_activity


def __calculate_service_time(event: Event, time_granularity: TimeUnit) -> int:
    start_timestamp = transform_timestamp(event[DEFAULT_START_TIMESTAMP_KEY], time_granularity)
    complete_timestamp = transform_timestamp(event[DEFAULT_TIMESTAMP_KEY], time_granularity)

    return (complete_timestamp - start_timestamp).total_seconds()


def __append_service_time_to_subvariant(subvariant, service_times_per_activity):
    """
    Appends the already computed service times per activity and instance to the complete nodes of the subvariant
    :param subvariant:
    :param service_times_per_activity:
    :return:
    """
    for parallel_subvariant_nodes in subvariant:
        for subvariant_node in parallel_subvariant_nodes:
            if subvariant_node.lifecycle == 'start':
                continue

            subvariant_node.performance_stats = stats(
                service_times_per_activity[subvariant_node.activity][subvariant_node.activity_instance])

    return subvariant


def calculate_waiting_time_events(subvariant, traces, time_granularity: TimeUnit):
    waiting_time_events = get_waiting_time_events(subvariant)

    return add_performance_to_waiting_time_events(waiting_time_events, traces, time_granularity)


def get_waiting_time_events(subvariant) -> List[WaitingTimeEvent]:
    waiting_time_events = []

    for i in range(len(subvariant) - 1):
        predecessor_part = subvariant[i]
        successor_part = subvariant[i + 1]

        forward_looking_wt_events = get_waiting_time_events_forward_looking(predecessor_part, successor_part)
        backward_looking_wt_events = get_waiting_time_events_backward_looking(predecessor_part, successor_part)

        if len(backward_looking_wt_events) >= len(forward_looking_wt_events):
            waiting_time_events += backward_looking_wt_events
        else:
            waiting_time_events += forward_looking_wt_events

    return waiting_time_events


def get_waiting_time_events_backward_looking(predecessor_part, successor_part):
    waiting_time_events = []
    predecessor_node = get_predecessor_start_node(predecessor_part)

    for subvariant_node in successor_part:
        if subvariant_node.lifecycle == 'start':
            waiting_time_events.append(WaitingTimeEvent(predecessor_node, subvariant_node, None, 'complete'))

    return waiting_time_events


def get_waiting_time_events_forward_looking(predecessor_part, successor_part):
    waiting_time_events = []
    successor_node = get_successor_complete_node(successor_part)

    for subvariant_node in predecessor_part:
        if subvariant_node.lifecycle == 'complete':
            waiting_time_events.append(WaitingTimeEvent(subvariant_node, successor_node, None, 'start'))

    return waiting_time_events


def get_predecessor_start_node(subvariant_group: List[SubvariantNode]) -> SubvariantNode:
    for node in subvariant_group:
        if node.lifecycle == 'complete':
            return node

    return subvariant_group[0]


def get_successor_complete_node(subvariant_group: List[SubvariantNode]) -> SubvariantNode:
    for node in subvariant_group:
        if node.lifecycle == 'start':
            return node

    return subvariant_group[0]


def add_performance_to_waiting_time_events(waiting_time_events: List[WaitingTimeEvent], traces,
                                           time_granularity: TimeUnit):
    traces_as_act_instance_dicts = traces_to_activity_instance_dicts(traces)

    for waiting_time_event in waiting_time_events:
        waiting_times = []
        for trace_as_instance_dict in traces_as_act_instance_dicts:
            start_timestamp_key = DEFAULT_START_TIMESTAMP_KEY if waiting_time_event.start.lifecycle == "start" else DEFAULT_TIMESTAMP_KEY
            start_timestamp = \
                trace_as_instance_dict[waiting_time_event.start.activity, waiting_time_event.start.activity_instance][
                    start_timestamp_key]
            start_timestamp = transform_timestamp(start_timestamp, time_granularity)

            complete_timestamp_key = DEFAULT_START_TIMESTAMP_KEY if waiting_time_event.complete.lifecycle == "start" else DEFAULT_TIMESTAMP_KEY
            complete_timestamp = \
                trace_as_instance_dict[
                    waiting_time_event.complete.activity, waiting_time_event.complete.activity_instance][
                    complete_timestamp_key]
            complete_timestamp = transform_timestamp(complete_timestamp, time_granularity)

            waiting_time = (complete_timestamp - start_timestamp).total_seconds()
            waiting_times.append(waiting_time)

        waiting_time_event.performance_stats = stats(waiting_times)

    return waiting_time_events


def traces_to_activity_instance_dicts(traces: List[Trace]):
    return [trace_to_activity_instance_dict(t) for t in traces]


def trace_to_activity_instance_dict(trace: Trace):
    result = {}

    for event in trace:
        activity = event[DEFAULT_NAME_KEY]
        activity_instance = event[ACTIVITY_INSTANCE_KEY]
        result[(activity, activity_instance)] = event

    return result
