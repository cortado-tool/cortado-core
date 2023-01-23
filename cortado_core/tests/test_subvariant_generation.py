import unittest
from datetime import datetime

from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.log.util.xes import DEFAULT_START_TIMESTAMP_KEY, DEFAULT_TIMESTAMP_KEY, DEFAULT_TRANSITION_KEY

from cortado_core.utils.cvariants import get_detailed_variants, SubvariantNode


class TestSubvariantGeneration(unittest.TestCase):
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

    def test_parallel_starting_timestamps(self):
        events = []
        events += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 2))
        events += self.__create_event('a', datetime(2020, 1, 1, 1), datetime(2020, 1, 1, 3))
        events += self.__create_event('b', datetime(2020, 1, 1, 4), datetime(2020, 1, 1, 5))

        traces = []
        traces.append(Trace(events))

        events = []
        events += self.__create_event('a', datetime(2020, 1, 1, 2), datetime(2020, 1, 1, 4))
        events += self.__create_event('a', datetime(2020, 1, 1, 2), datetime(2020, 1, 1, 3))
        events += self.__create_event('b', datetime(2020, 1, 1, 7), datetime(2020, 1, 1, 9))

        traces.append(Trace(events))

        subvariants = get_detailed_variants(traces)

        self.assertEqual(len(list(subvariants.keys())), 1)

        subvariant = list(subvariants.keys())[0]

        expected = (
            (SubvariantNode('a', 'start', 0, None), SubvariantNode('a', 'start', 1, None)),
            (SubvariantNode('a', 'complete', 0, None),),
            (SubvariantNode('a', 'complete', 1, None),), (SubvariantNode('b', 'start', 0, None),),
            (SubvariantNode('b', 'complete', 0, None),))

        self.assertEquals(subvariant, expected)
        self.assertEquals(len(subvariants[subvariant]), 2)


if __name__ == '__main__':
    unittest.main()
