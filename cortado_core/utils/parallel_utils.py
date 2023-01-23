from typing import List, Tuple, Mapping

from cortado_core.utils.cgroups_graph import ConcurrencyGroup

from cortado_core.utils.timestamp_utils import TimeUnit
from pm4py.objects.log.obj import EventLog, Trace

MIN_CHUNKS = 8


def workload_split(log_renamed: EventLog, interval_log: EventLog, time_granularity: TimeUnit) -> Tuple[
    List[EventLog], List[EventLog], List[TimeUnit]]:
    len_log = len(log_renamed)
    step_size = min(100, len_log // MIN_CHUNKS)
    bounds = [(i, min([i + step_size, len_log])) for i in range(0, len_log, step_size)]

    log_renamed_bounds = [log_renamed[lower:upper] for lower, upper in bounds]
    interval_log_bounds = [interval_log[lower:upper] for lower, upper in bounds]

    return log_renamed_bounds, interval_log_bounds, [time_granularity for _ in range(len(bounds))]


def workload_split_graphs(graphs: Mapping[ConcurrencyGroup, List[Trace]]):
    len_graphs = len(graphs)
    step_size = min(100, len_graphs // MIN_CHUNKS)
    bounds = [(i, min([i + step_size, len_graphs])) for i in range(0, len_graphs, step_size)]
    flattend_graphs = list(graphs.items())

    return [flattend_graphs[lower:upper] for lower, upper in bounds]
