import os
import unittest

import pm4py
from pm4py.objects.log.obj import Trace, Event, EventLog
from pm4py.objects.log.util.interval_lifecycle import to_interval
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.log.importer.xes.importer import apply as xes_import

from cortado_core.eventually_follows_pattern_mining.local_process_models.metrics import (
    calculate_metrics,
)

LOG_FILE = os.getenv("LOG_FILE", "BPI_Challenge_2012_short.xes")
EVENT_LOG_DIRECTORY = os.getenv(
    "EVENT_LOG_DIRECTORY", "C:\\sources\\arbeit\\cortado\\event-logs"
)


class TestMetrics(unittest.TestCase):
    def __generate_test_trace(self, trace_unformatted):
        trace = Trace()
        for event_unformatted in trace_unformatted:
            event = Event()
            event["concept:name"] = event_unformatted
            trace.append(event)

        return trace

    def test_range_metric(self):
        tree = pt_parse("->('a',X('c','d'),'b')")
        trace1 = self.__generate_test_trace("opopacfffedbopop")  # range 7
        trace2 = self.__generate_test_trace(
            "opopacfedbopopacffedbpop"
        )  # range 5 and range 6
        trace3 = self.__generate_test_trace("bbakkkkkdkkkbsdf")  # range 10
        trace4 = self.__generate_test_trace("bbfakkkkkdkkkbsdf")  # range 10
        # 10 + 10 + 10 + 12 + 28 = 70

        log = EventLog([trace1, trace1, trace1, trace1, trace2, trace2, trace3, trace4])
        metrics = calculate_metrics(tree, log, include_skip_metrics=False)
        self.assertEqual(7, metrics[-3])
