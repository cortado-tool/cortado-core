from datetime import datetime
from typing import Tuple

from cortado_core.performance import tree_performance
from cortado_core.utils.process_tree import CortadoProcessTree
from pm4py.objects.process_tree.obj import Operator


def timestamp(t):
    return datetime.fromtimestamp(t)


def set_parent(pt: CortadoProcessTree):
    for n in pt.children:
        n._parent = pt
        set_parent(n)


# FIXME: is this the best way?
class PerformanceHelpers:
    @staticmethod
    def to_seconds(d: Tuple[datetime, datetime]):
        return [(d[0] - datetime.fromtimestamp(0)).total_seconds() if d[0] is not None else None,
                (d[1] - datetime.fromtimestamp(0)).total_seconds() if d[1] is not None else None]

    @staticmethod
    def timestamps_to_seconds_multi_interval(multi_interval):
        return {
            t: [[[[PerformanceHelpers.to_seconds(interval) for interval in intervals] for intervals in
                  instances] if instances else None
                 for instances in alignments] if alignments else None
                for alignments in cases] for t, cases in multi_interval.items()}

    @staticmethod
    def timestamps_to_seconds_single_interval(single_interval):
        return {
            t: [list(list(PerformanceHelpers.to_seconds(interval) for interval in instances) if instances else None
                     for instances in alignments) if alignments else None
                for alignments in cases] for t, cases in single_interval.items()}

    @staticmethod
    def test_performance(log, tree):
        (all_service_times, all_idle_times, all_waiting_times, all_cycle_times), mean_fitness \
            = tree_performance.get_tree_performance_intervals(tree, log)
        all_service_times = PerformanceHelpers.timestamps_to_seconds_multi_interval(all_service_times)
        all_idle_times = PerformanceHelpers.timestamps_to_seconds_multi_interval(all_idle_times)
        all_waiting_times = PerformanceHelpers.timestamps_to_seconds_single_interval(all_waiting_times)
        all_cycle_times = PerformanceHelpers.timestamps_to_seconds_single_interval(all_cycle_times)
        return all_service_times, all_idle_times, all_waiting_times, all_cycle_times


def create_test_tree():
    T41 = CortadoProcessTree(label="A")
    T42 = CortadoProcessTree(label="B")
    T31 = CortadoProcessTree(operator=Operator.SEQUENCE, children=[T41, T42])

    T43 = CortadoProcessTree(label="C")
    T44 = CortadoProcessTree(label="D")
    T32 = CortadoProcessTree(operator=Operator.PARALLEL, children=[T43, T44])

    T21 = CortadoProcessTree(operator=Operator.XOR, children=[T31, T32])

    T22 = CortadoProcessTree()  # Tau
    T11 = CortadoProcessTree(operator=Operator.LOOP, children=[T21, T22])

    T23 = CortadoProcessTree(label="B")
    T24 = CortadoProcessTree(label="E")
    T12 = CortadoProcessTree(operator=Operator.PARALLEL, children=[T23, T24])

    T0 = CortadoProcessTree(operator=Operator.SEQUENCE, children=[T11, T12])
    return T0, T11, T12, T21, T22, T23, T24, T31, T32, T41, T42, T43, T44
