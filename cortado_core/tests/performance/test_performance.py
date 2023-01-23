import unittest

from cortado_core.utils.process_tree import index_leaf_labels
from pm4py.objects.log.obj import EventLog, Trace
from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_TIMESTAMP_KEY, \
    DEFAULT_TRANSITION_KEY
from .test_utils import set_parent, timestamp, create_test_tree, PerformanceHelpers

T0, T11, T12, T21, T22, T23, T24, T31, T32, T41, T42, T43, T44 = create_test_tree()
T0 = index_leaf_labels(T0)
set_parent(T0)


class TestPerformance(unittest.TestCase):
    def test_no_deviation(self):
        log = [
            Trace([
                {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(0), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(3), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(6), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(10), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(12), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(17), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(14), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(20), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(22), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(25), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(26), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(28), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'E', DEFAULT_TIMESTAMP_KEY: timestamp(35), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'E', DEFAULT_TIMESTAMP_KEY: timestamp(38), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(35), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(40), DEFAULT_TRANSITION_KEY: "complete"},
            ]),
        ]
        event_log = EventLog(log)
        all_service_times, all_idle_times, all_waiting_times, all_cycle_times \
            = PerformanceHelpers.test_performance(event_log, T0)
        assert all_service_times[T0] == [
            [
                [
                    [
                        [0, 3],
                        [6, 10],
                        [12, 20],
                        [22, 25],
                        [26, 28],
                        [35, 40]
                    ]
                ]
            ]
        ]

        assert all_idle_times[T0] == [
            [
                [
                    [
                        [3, 6],
                        [10, 12],
                        [20, 22],
                        [25, 26],
                        [28, 35],
                    ]
                ]
            ]
        ]

        assert all_cycle_times[T0] == [
            [
                [
                    [0, 40]
                ]
            ]
        ]

        assert all_waiting_times[T0] == [
            [
                [
                    [0, 0]
                ]
            ]
        ]

        # T12
        assert all_service_times[T12] == [[[[[35, 40]]]]]
        assert all_idle_times[T12] == [[[[]]]]
        assert all_cycle_times[T12] == [[[[28, 40]]]]
        assert all_waiting_times[T12] == [[[[28, 35]]]]

        # T11
        assert all_service_times[T11] == [[[[[0, 3], [6, 10], [12, 20], [22, 25], [26, 28]]]]]
        assert all_idle_times[T11] == [[[all_idle_times[T0][0][0][0][:-1]]]]
        assert all_cycle_times[T11] == [[[[0, 28]]]]
        assert all_waiting_times[T11] == [[[[0, 0]]]]

        # T21
        assert all_service_times[T21] == [[[
            [
                [0, 3], [6, 10]
            ],
            [
                [12, 20]
            ],
            [
                [22, 25], [26, 28]
            ]
        ]]]
        assert all_idle_times[T21] == [[[[[3, 6]], [], [[25, 26]]]]]
        assert all_cycle_times[T21] == [[[[0, 10], [10, 20], [20, 28]]]]
        assert all_waiting_times[T21] == [[[[0, 0], [10, 12], [20, 22]]]]

        # T31
        assert all_service_times[T31] == [[[[[0, 3], [6, 10]]]]]
        assert all_idle_times[T31] == [[[[[3, 6]]]]]
        assert all_cycle_times[T31] == [[[[0, 10]]]]
        assert all_waiting_times[T31] == [[[[0, 0]]]]

        # T32
        assert all_service_times[T32] == [[[[[12, 20]], [[22, 25], [26, 28]]]]]
        assert all_idle_times[T32] == [[[[], [[25, 26]]]]]
        assert all_cycle_times[T32] == [[[[10, 20], [20, 28]]]]
        assert all_waiting_times[T32] == [[[[10, 12], [20, 22]]]]

        # T23 B, equal to T12
        assert all_service_times[T23] == [[[[[35, 40]]]]]
        assert all_idle_times[T23] == [[[[]]]]
        assert all_cycle_times[T23] == [[[[28, 40]]]]
        assert all_waiting_times[T23] == [[[[28, 35]]]]

        # T24 E
        assert all_service_times[T24] == [[[[[35, 38]]]]]
        assert all_idle_times[T24] == [[[[]]]]
        assert all_cycle_times[T24] == [[[[28, 38]]]]
        assert all_waiting_times[T24] == [[[[28, 35]]]]

        # T41 A
        assert all_service_times[T41] == [[[[[0, 3]]]]]
        assert all_idle_times[T41] == [[[[]]]]
        assert all_cycle_times[T41] == [[[[0, 3]]]]
        assert all_waiting_times[T41] == [[[[0, 0]]]]

        # T42 B
        assert all_service_times[T42] == [[[[[6, 10]]]]]
        assert all_idle_times[T42] == [[[[]]]]
        assert all_cycle_times[T42] == [[[[3, 10]]]]
        assert all_waiting_times[T42] == [[[[3, 6]]]]

        # T43 C
        assert all_service_times[T43] == [[[[[12, 17]], [[22, 25]]]]]
        assert all_idle_times[T43] == [[[[], []]]]
        assert all_cycle_times[T43] == [[[[10, 17], [20, 25]]]]
        assert all_waiting_times[T43] == [[[[10, 12], [20, 22]]]]

        # T44 D
        assert all_service_times[T44] == [[[[[14, 20]], [[26, 28]]]]]
        assert all_idle_times[T44] == [[[[], []]]]
        assert all_cycle_times[T44] == [[[[10, 20], [20, 28]]]]
        assert all_waiting_times[T44] == [[[[10, 14], [20, 26]]]]

    @unittest.skip("a start full search not merged yet")
    def test_with_deviation_1(self):
        log = [
            Trace([
                {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(0), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(3), DEFAULT_TRANSITION_KEY: "complete"},

                # {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(6), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(10), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(12), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(17), DEFAULT_TRANSITION_KEY: "complete"},

                # {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(14), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(20), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(22), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(25), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(26), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(28), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'E', DEFAULT_TIMESTAMP_KEY: timestamp(35), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'E', DEFAULT_TIMESTAMP_KEY: timestamp(38), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(35), DEFAULT_TRANSITION_KEY: "start"},
                # {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(40), DEFAULT_TRANSITION_KEY: "complete"},
            ]),
        ]
        event_log = EventLog(log)
        all_service_times, all_idle_times, all_waiting_times, all_cycle_times = \
            PerformanceHelpers.test_performance(event_log, T0)

        assert all_service_times[T0][0][0] == [
            [
                [0, 3],
                [None, 10],
                [12, 17],
                [None, 20],
                [22, 25],
                [26, 28],
                [35, None],
                [35, 38],
            ]
        ]

        assert all_idle_times[T0][0][0] == [
            [
                [3, None],
                [10, 12],
                [17, None],
                [20, 22],
                [25, 26],
                [28, 35],
            ]
        ]

        assert all_cycle_times[T0][0][0] == [[0, None]]

        assert all_waiting_times[T0][0][0] == [[0, 0]]

    @unittest.skip("a start full search not merged yet")
    def test_with_deviation_2(self):
        log = [
            Trace([
                {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(0), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(5), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(6), DEFAULT_TRANSITION_KEY: "start"},
                # {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(10), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(7), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'C', DEFAULT_TIMESTAMP_KEY: timestamp(8), DEFAULT_TRANSITION_KEY: "complete"},

                # {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(_), DEFAULT_TRANSITION_KEY: "start"},
                # {DEFAULT_NAME_KEY: 'D', DEFAULT_TIMESTAMP_KEY: timestamp(_), DEFAULT_TRANSITION_KEY: "complete"},

                # {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(_), DEFAULT_TRANSITION_KEY: "start"},
                # {DEFAULT_NAME_KEY: 'A', DEFAULT_TIMESTAMP_KEY: timestamp(_), DEFAULT_TRANSITION_KEY: "complete"},

                {DEFAULT_NAME_KEY: 'E', DEFAULT_TIMESTAMP_KEY: timestamp(19), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'E', DEFAULT_TIMESTAMP_KEY: timestamp(21), DEFAULT_TRANSITION_KEY: "complete"},

                # {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(_), DEFAULT_TRANSITION_KEY: "start"},
                {DEFAULT_NAME_KEY: 'B', DEFAULT_TIMESTAMP_KEY: timestamp(20), DEFAULT_TRANSITION_KEY: "complete"},
            ]),
        ]
        log = [sorted(t, key=lambda x: x[DEFAULT_TIMESTAMP_KEY]) for t in log]
        event_log = EventLog(log)
        all_service_times, all_idle_times, all_waiting_times, all_cycle_times \
            = PerformanceHelpers.test_performance(event_log, T0)
        # FIXME: assertions


if __name__ == '__main__':
    unittest.main()
