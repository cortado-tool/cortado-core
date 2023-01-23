import unittest
from typing import List

from cortado_core.alignments.suffix_alignments.algorithm import calculate_optimal_suffix_alignment
from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.process_tree.utils.generic import parse
from pm4py.objects.petri_net.utils import align_utils


class TestSuffixAlignments(unittest.TestCase):
    def __generate_test_trace(self, trace_unformatted: str):
        trace = Trace()
        for event_unformatted in trace_unformatted:
            event = Event()
            event["concept:name"] = event_unformatted
            trace.append(event)

        return trace


    def __test_tree(self, tree, acceptable_suffixes, unacceptable_suffixes):
        process_tree = parse(tree)

        for variant in self.__get_variants():

            for suffix in acceptable_suffixes:
                trace = self.__generate_test_trace(suffix)
                alignment = variant(trace, process_tree)
                # less than because tau moves have a small cost, too
                self.assertLess(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST, suffix)

            for suffix in unacceptable_suffixes:
                trace = self.__generate_test_trace(suffix)
                alignment = variant(trace, process_tree)
                # less than because tau moves have a small cost, too
                self.assertGreaterEqual(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST, suffix)

    def __get_variants(self):
        variant_dijkstra_naive = lambda t, pt: calculate_optimal_suffix_alignment(t, pt, naive=True, use_dijkstra=True)
        variant_dijkstra_not_naive = lambda t, pt: calculate_optimal_suffix_alignment(t, pt, naive=False, use_dijkstra=True)
        variant_a_star_naive = lambda t, pt: calculate_optimal_suffix_alignment(t, pt, naive=True, use_dijkstra=False)
        variant_a_star_not_naive = lambda t, pt: calculate_optimal_suffix_alignment(t, pt, naive=False, use_dijkstra=False)

        return [variant_dijkstra_naive, variant_dijkstra_not_naive, variant_a_star_naive, variant_a_star_not_naive]

    def test_suffix_alignments_complex_tree_case_1(self):
        tree = "X(+(->('a','b'),+('c','d')),*(+('e','f'),'b'))"

        acceptable_suffixes = ['ab', 'abdc', 'febef', 'bd']
        not_acceptable_suffixes = ['fea', 'cbfe', 'abcda', 'a']

        self.__test_tree(tree, acceptable_suffixes, not_acceptable_suffixes)

    def test_suffix_alignments_complex_tree_case_2(self):
        tree = "*(+(+(->('a','b'),+('c','d')),*(+('e','f'),'b')), ->('i',+('g','h')))"

        acceptable_suffixes = ['dc', 'dcab', 'ghabcdef', 'ghabcdfe', 'febefdcab']
        not_acceptable_suffixes = ['febefdcba', 'ihg', 'g', 'h', 'i']

        self.__test_tree(tree, acceptable_suffixes, not_acceptable_suffixes)


    def test_suffix_alignments_no_matching_activity_in_trace(self):
        tree = parse("->('a', 'b', 'c', 'd')")
        trace = self.__generate_test_trace("ef")

        for variant in self.__get_variants():
            alignment = variant(trace, tree)
            self.assertEqual(alignment['cost'], 20000)


    def test_suffix_alignments_matching_trace_in_the_very_beginning(self):
        tree = parse("->('a', 'b', 'c', 'd')")
        trace = self.__generate_test_trace("a")

        for variant in self.__get_variants():
            alignment = variant(trace, tree)
            # single log move
            self.assertEqual(alignment['cost'], 10000)



if __name__ == '__main__':
    unittest.main()
