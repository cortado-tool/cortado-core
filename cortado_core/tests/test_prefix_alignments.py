import unittest
from typing import List

from cortado_core.alignments.prefix_alignments import algorithm as prefix_alignments
from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.process_tree.utils.generic import parse
from pm4py.objects.petri_net.utils import align_utils

from pm4py.objects.conversion.process_tree import converter as pt_converter


class TestInfixAlignments(unittest.TestCase):
    def __generate_test_trace(self, trace_unformatted: List[str]):
        trace = Trace()
        for event_unformatted in trace_unformatted:
            event = Event()
            event["concept:name"] = event_unformatted
            trace.append(event)

        return trace

    def __test_tree(self, tree, acceptable, unacceptable):
        process_tree = parse(tree)
        net, im, fm = pt_converter.apply(process_tree)

        for variant in self.__get_variants():
            for prefix in acceptable:
                trace = self.__generate_test_trace(prefix)
                alignment = variant(trace, net, im, fm)
                # less than because tau moves have a small cost, too
                self.assertLess(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST, prefix)

            for prefix in unacceptable:
                trace = self.__generate_test_trace(prefix)
                alignment = variant(trace, net, im, fm)
                # less than because tau moves have a small cost, too
                self.assertGreaterEqual(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST, prefix)

    def __get_variants(self):
        variant_dijkstra = lambda t, pn, im, fm: prefix_alignments.apply_trace(t, pn, im, fm,
                                                                               variant=prefix_alignments.VERSION_DIJKSTRA_NO_HEURISTICS)
        variant_a_star = lambda t, pn, im, fm: prefix_alignments.apply_trace(t, pn, im, fm,
                                                                             variant=prefix_alignments.VERSION_A_STAR)

        return [variant_dijkstra, variant_a_star]

    def test_prefix_alignments_basic_parallel_case(self):
        tree = "+(->('a','b','c'),->('d','e','f'))"

        acceptable_prefixes = [[], ['a'], ['a', 'b'], ['d', 'a'], ['a', 'd', 'e', 'b'], ['a', 'd', 'e', 'b', 'c', 'f']]
        not_acceptable_prefixes = [['b'], ['f'], ['e', 'd'], ['a', 'd', 'f'], ['a', 'b', 'c', 'd', 'e', 'f', 'a']]

        self.__test_tree(tree, acceptable_prefixes, not_acceptable_prefixes)

    def test_prefix_alignments_basic_xor_case(self):
        tree = "X(->('a','b','c'),->('d','e','f'))"

        acceptable_prefixes = [[], ['a'], ['a', 'b'], ['a', 'b', 'c'], ['d'], ['d', 'e'], ['d', 'e', 'f']]
        not_acceptable_prefixes = [['b'], ['f'], ['a', 'd'], ['a', 'd', 'f'], ['a', 'b', 'c', 'a']]

        self.__test_tree(tree, acceptable_prefixes, not_acceptable_prefixes)

    def test_prefix_alignments_basic_loop_case(self):
        tree = "*(->('a','b','c'),->('d','e','f'))"

        acceptable_prefixes = [[], ['a'], ['a', 'b'], ['a', 'b', 'c'], ['a', 'b', 'c', 'd'],
                               ['a', 'b', 'c', 'd', 'e', 'f', 'a']]
        not_acceptable_prefixes = [['b'], ['f'], ['a', 'd'], ['a', 'd', 'f'], ['a', 'b', 'c', 'a'],
                                   ['a', 'b', 'c', 'd', 'e', 'f', 'a', 'a']]

        self.__test_tree(tree, acceptable_prefixes, not_acceptable_prefixes)

    def test_prefix_alignments_complex_case(self):
        tree = "X(+(->('a','b'),+('c','d')),*(+('e','f'),'b'))"

        acceptable_prefixes = [[], ['a', 'd', 'c', 'b'], ['c', 'a'], ['f', 'e', 'b', 'e', 'f']]
        not_acceptable_prefixes = [['a', 'd', 'c', 'b', 'f'], ['b'], ['b', 'a']]

        self.__test_tree(tree, acceptable_prefixes, not_acceptable_prefixes)


if __name__ == '__main__':
    unittest.main()
