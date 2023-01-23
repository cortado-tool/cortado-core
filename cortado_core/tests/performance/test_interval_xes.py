import unittest

from cortado_core.performance import tree_performance
from cortado_core.performance.aggregators import stats, avg
from cortado_core.performance.tree_performance import apply_aggregation
from cortado_core.utils.cvariants import get_concurrency_variants
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.util.xes_constants import DEFAULT_TRANSITION_KEY, DEFAULT_NAME_KEY

from cortado_core.utils.sequentializations import generate_variants


class TestPerformanceIntervalXes(unittest.TestCase):

    @unittest.skip("no real use in this test")
    def test_performance_interval(self):
        filename = 'cortado_core/tests/performance/interval.xes'

        # read and filter event log
        lifecycles = ['start', 'complete']
        event_log = xes_importer.apply(filename, parameters={})
        event_log = EventLog(
            [Trace([Event(e) for e in t if e[DEFAULT_TRANSITION_KEY].lower() in lifecycles]) for t in event_log])

        # get variants and create initial model
        variants = get_concurrency_variants(event_log)
        variants_sorted = sorted(variants.items(), key=lambda x: len(x[1]), reverse=True)
        total_order_variants = [tv for v in variants_sorted[:5]
                                for tv in generate_variants(v[0])]
        train_log = [Trace([Event({DEFAULT_NAME_KEY: a}) for a in v])
                     for v in total_order_variants]
        train_log = EventLog(train_log)

        test_log = EventLog([Trace(t)
                             for v, traces in variants_sorted[:10] for t in traces])

        pt = inductive_miner.apply_tree(train_log)

        (all_service_times, all_idle_times, all_waiting_times, all_cycle_times), mean_fitness = \
            tree_performance.get_tree_performance_intervals(pt, test_log)

        service_times_aggregated = apply_aggregation(all_service_times, stats, avg, avg)
        idle_times_aggregated = apply_aggregation(all_idle_times, stats, avg, avg)
        waiting_times_aggregated = apply_aggregation(all_waiting_times, stats, avg, avg)
        cycle_times_aggregated = apply_aggregation(all_cycle_times, stats, avg, avg)


if __name__ == '__main__':
    unittest.main()
