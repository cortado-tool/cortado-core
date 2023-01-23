import unittest
from datetime import datetime

from cortado_core.utils.timestamp_utils import TimeUnit
from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.log.util.xes import DEFAULT_START_TIMESTAMP_KEY, DEFAULT_TIMESTAMP_KEY, DEFAULT_TRANSITION_KEY

from cortado_core.performance import subvariant_performance
from cortado_core.performance.subvariant_performance import WaitingTimeEvent
from cortado_core.utils.cvariants import get_detailed_variants, SubvariantNode


class TestSubvariantPerformance(unittest.TestCase):
    @staticmethod
    def __create_event(name, start_timestamp, complete_timestamp, use_lifecycle: bool = False):
        event = Event()
        event['concept:name'] = name
        event[DEFAULT_TIMESTAMP_KEY] = complete_timestamp

        if not use_lifecycle:
            event[DEFAULT_START_TIMESTAMP_KEY] = start_timestamp

            return [event]

        event[DEFAULT_TRANSITION_KEY] = 'complete'

        event_start = Event()
        event_start['concept:name'] = name
        event_start[DEFAULT_TIMESTAMP_KEY] = start_timestamp
        event_start[DEFAULT_TRANSITION_KEY] = 'start'

        return [event_start, event]

    def test_basic(self):
        events = []
        events += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 2))
        events += self.__create_event('b', datetime(2020, 1, 1, 3), datetime(2020, 1, 1, 4))

        trace = Trace(events)

        subvariants = get_detailed_variants([trace])
        subvariant = list(subvariants.keys())[0]

        subvariant_with_performance = subvariant_performance.calculate_subvariant_performance(subvariant, [trace],
                                                                                              TimeUnit.SEC)

        self.assertEqual(subvariant_with_performance.global_performance_stats['mean'], 10800)

        for parallel_subvariant_nodes in subvariant_with_performance.subvariant:
            for subvariant_node in parallel_subvariant_nodes:
                if subvariant_node.lifecycle == 'start':
                    self.assertEqual(subvariant_node.performance_stats, None)
                    continue

                self.assertEqual(subvariant_node.performance_stats['mean'], 3600)

        self.assertEqual(len(subvariant_with_performance.waiting_time_events), 1)
        waiting_time_event = subvariant_with_performance.waiting_time_events[0]
        self.assertEqual(waiting_time_event.performance_stats['mean'], 3600)
        self.assertEqual(waiting_time_event.start, SubvariantNode('a', 'complete', 0, None))
        self.assertEqual(waiting_time_event.complete, SubvariantNode('b', 'start', 0, None))

    def test_basic_multiple_traces(self):
        traces = []
        events1 = []
        events1 += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 2))
        events1 += self.__create_event('b', datetime(2020, 1, 1, 3), datetime(2020, 1, 1, 4))

        traces.append(Trace(events1))

        events2 = []
        events2 += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 3))
        events2 += self.__create_event('b', datetime(2020, 1, 1, 4), datetime(2020, 1, 1, 5))

        traces.append(Trace(events2))

        subvariants = get_detailed_variants(traces)
        self.assertEqual(len(subvariants.keys()), 1)
        subvariant = list(subvariants.keys())[0]

        subvariant_with_performance = subvariant_performance.calculate_subvariant_performance(subvariant, traces,
                                                                                              TimeUnit.SEC)

        for parallel_subvariant_nodes in subvariant_with_performance.subvariant:
            for subvariant_node in parallel_subvariant_nodes:
                if subvariant_node.lifecycle == 'start':
                    self.assertEqual(subvariant_node.performance_stats, None)
                    continue

                if subvariant_node.activity == 'a':
                    self.assertEqual(subvariant_node.performance_stats['mean'], 5400)
                    self.assertEqual(subvariant_node.performance_stats['min'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['max'], 7200)
                    self.assertEqual(subvariant_node.performance_stats['n'], 2)

                if subvariant_node.activity == 'b':
                    self.assertEqual(subvariant_node.performance_stats['mean'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['min'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['max'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['n'], 2)

    def test_basic_multiple_traces_with_repeating_activity(self):
        traces = []
        events1 = []
        events1 += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 2))
        events1 += self.__create_event('b', datetime(2020, 1, 1, 3), datetime(2020, 1, 1, 4))
        events1 += self.__create_event('a', datetime(2020, 1, 1, 5), datetime(2020, 1, 1, 6))

        traces.append(Trace(events1))

        events2 = []
        events2 += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 3))
        events2 += self.__create_event('b', datetime(2020, 1, 1, 4), datetime(2020, 1, 1, 5))
        events2 += self.__create_event('a', datetime(2020, 1, 1, 6), datetime(2020, 1, 1, 7))

        traces.append(Trace(events2))

        subvariants = get_detailed_variants(traces)
        self.assertEqual(len(subvariants.keys()), 1)
        subvariant = list(subvariants.keys())[0]

        subvariant_with_performance = subvariant_performance.calculate_subvariant_performance(subvariant, traces,
                                                                                              TimeUnit.SEC)

        for parallel_subvariant_nodes in subvariant_with_performance.subvariant:
            for subvariant_node in parallel_subvariant_nodes:
                if subvariant_node.lifecycle == 'start':
                    self.assertEqual(subvariant_node.performance_stats, None)
                    continue

                if subvariant_node.activity == 'a' and subvariant_node.activity_instance == 0:
                    self.assertEqual(subvariant_node.performance_stats['mean'], 5400)
                    self.assertEqual(subvariant_node.performance_stats['min'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['max'], 7200)
                    self.assertEqual(subvariant_node.performance_stats['n'], 2)

                if subvariant_node.activity == 'a' and subvariant_node.activity_instance > 0:
                    self.assertEqual(subvariant_node.performance_stats['mean'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['min'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['max'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['n'], 2)

                if subvariant_node.activity == 'b':
                    self.assertEqual(subvariant_node.performance_stats['mean'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['min'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['max'], 3600)
                    self.assertEqual(subvariant_node.performance_stats['n'], 2)

    def test_parallel_events(self):
        events = []
        events += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 2))
        events += self.__create_event('b', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 2))

        trace = Trace(events)

        subvariants = get_detailed_variants([trace])
        subvariant = list(subvariants.keys())[0]

        subvariant_with_performance = subvariant_performance.calculate_subvariant_performance(subvariant, [trace],
                                                                                              TimeUnit.SEC)

        self.assertEqual(len(subvariant_with_performance.waiting_time_events), 0)

        for parallel_subvariant_nodes in subvariant_with_performance.subvariant:
            for subvariant_node in parallel_subvariant_nodes:
                if subvariant_node.lifecycle == 'start':
                    self.assertEqual(subvariant_node.performance_stats, None)
                    continue

                self.assertEqual(subvariant_node.performance_stats['mean'], 3600)

    def test_overlapping_events(self):
        events = []
        events += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 3))
        events += self.__create_event('b', datetime(2020, 1, 1, 2), datetime(2020, 1, 1, 4))

        trace = Trace(events)

        subvariants = get_detailed_variants([trace])
        subvariant = list(subvariants.keys())[0]

        subvariant_with_performance = subvariant_performance.calculate_subvariant_performance(subvariant, [trace],
                                                                                              TimeUnit.SEC)

        for parallel_subvariant_nodes in subvariant_with_performance.subvariant:
            for subvariant_node in parallel_subvariant_nodes:
                if subvariant_node.lifecycle == 'start':
                    self.assertEqual(subvariant_node.performance_stats, None)
                    continue

                self.assertEqual(subvariant_node.performance_stats['mean'], 7200)

        for waiting_time_node in subvariant_with_performance.waiting_time_events:
            self.assertEqual(waiting_time_node.performance_stats['mean'], 3600)


if __name__ == '__main__':
    unittest.main()
