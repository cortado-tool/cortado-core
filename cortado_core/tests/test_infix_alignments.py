import unittest
from typing import List

from cortado_core.alignments.infix_alignments.algorithm import calculate_optimal_infix_alignment
from cortado_core.alignments.infix_alignments.algorithm import VARIANT_TREE_BASED_PREPROCESSING, \
    VARIANT_BASELINE_APPROACH
from cortado_core.alignments.infix_alignments.variants.tree_based_preprocessing import reduce_process_tree, \
    search_leaf_nodes_in_tree, get_matching_leaf_nodes
from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.process_tree.utils.generic import parse
from pm4py.objects.petri_net.utils import align_utils


class TestInfixAlignments(unittest.TestCase):
    def __generate_test_trace(self, trace_unformatted: List[str]):
        trace = Trace()
        for event_unformatted in trace_unformatted:
            event = Event()
            event["concept:name"] = event_unformatted
            trace.append(event)

        return trace

    def __alignment_contains_move(self, alignment, move):
        alignment = alignment['alignment']
        for al_move in alignment:
            if move == al_move:
                return True
        return False

    def __test_tree(self, tree, acceptable_infixes, unacceptable_infixes):
        process_tree = parse(tree)

        for variant in self.__get_variants():

            for infix in acceptable_infixes:
                trace = self.__generate_test_trace(infix)
                alignment = variant(trace, process_tree)
                # less than because tau moves have a small cost, too
                self.assertLess(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST, infix)

            for infix in unacceptable_infixes:
                trace = self.__generate_test_trace(infix)
                alignment = variant(trace, process_tree)
                # less than because tau moves have a small cost, too
                self.assertGreaterEqual(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST, infix)

    def __get_variants(self):
        variant_dijkstra_naive = lambda t, pt: calculate_optimal_infix_alignment(t, pt, naive=True, use_dijkstra=True,
                                                                                 variant=VARIANT_TREE_BASED_PREPROCESSING)
        variant_dijkstra_advanced = lambda t, pt: calculate_optimal_infix_alignment(t, pt, naive=False,
                                                                                    use_dijkstra=True,
                                                                                    variant=VARIANT_TREE_BASED_PREPROCESSING)
        variant_dijkstra_advanced_enforce_tau = lambda t, pt: calculate_optimal_infix_alignment(t, pt, naive=False,
                                                                                                use_dijkstra=True,
                                                                                                enforce_first_tau_move=True,
                                                                                                variant=VARIANT_TREE_BASED_PREPROCESSING)
        variant_astar_naive = lambda t, pt: calculate_optimal_infix_alignment(t, pt, naive=True, use_dijkstra=False,
                                                                              variant=VARIANT_TREE_BASED_PREPROCESSING)
        variant_astar_advanced = lambda t, pt: calculate_optimal_infix_alignment(t, pt, naive=False, use_dijkstra=False,
                                                                                 variant=VARIANT_TREE_BASED_PREPROCESSING)
        variant_baseline_dijkstra = lambda t, pt: calculate_optimal_infix_alignment(t, pt, use_dijkstra=True,
                                                                                    naive=True,
                                                                                    variant=VARIANT_BASELINE_APPROACH)
        variant_baseline_a_star = lambda t, pt: calculate_optimal_infix_alignment(t, pt, use_dijkstra=False, naive=True,
                                                                                  variant=VARIANT_BASELINE_APPROACH)
        variant_baseline_not_naive_dijkstra = lambda t, pt: calculate_optimal_infix_alignment(t, pt, use_dijkstra=True,
                                                                                              naive=False,
                                                                                              variant=VARIANT_BASELINE_APPROACH)
        variant_baseline_not_naive_a_star = lambda t, pt: calculate_optimal_infix_alignment(t, pt, use_dijkstra=False,
                                                                                            naive=False,
                                                                                            variant=VARIANT_BASELINE_APPROACH)
        return [variant_dijkstra_naive, variant_dijkstra_advanced, variant_astar_naive, variant_astar_advanced,
                variant_dijkstra_advanced_enforce_tau, variant_baseline_dijkstra, variant_baseline_a_star,
                variant_baseline_not_naive_dijkstra, variant_baseline_not_naive_a_star]

    def test_infix_alignments_basic_parallel_case_1(self):
        process_tree = parse("+(->('a','b','c'),->('d','e','f'))")
        trace = self.__generate_test_trace(['a', 'b', 'e'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertEqual(alignment['cost'], 0)
            self.assertEqual(len(alignment['alignment']), 3)
            self.assertEqual(alignment['alignment'][0], ('a', 'a'))
            self.assertEqual(alignment['alignment'][1], ('b', 'b'))
            self.assertEqual(alignment['alignment'][2], ('e', 'e'))

    def test_infix_alignments_basic_parallel_case_2(self):
        process_tree = parse("+(->('a','b','c'),->('d','e','f'))")
        trace = self.__generate_test_trace(['a', 'c', 'd', 'e'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)
            self.assertGreaterEqual(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST)

    def test_infix_alignments_basic_xor_case(self):
        process_tree = parse("X(->('a','b','c'),->('d','e','f'))")
        trace = self.__generate_test_trace(['a', 'b', 'e'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertGreaterEqual(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST)
            self.assertTrue(self.__alignment_contains_move(alignment, ('a', 'a')))
            self.assertTrue(self.__alignment_contains_move(alignment, ('b', 'b')))
            self.assertFalse(self.__alignment_contains_move(alignment, ('e', 'e')))

    def test_infix_alignments_basic_loop_case_1(self):
        process_tree = parse("*(->('a','b'),->('c','d'))")
        trace = self.__generate_test_trace(['a', 'b', 'c'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertEqual(alignment['cost'], 0)
            self.assertEqual(len(alignment['alignment']), 3)
            self.assertTrue(self.__alignment_contains_move(alignment, ('a', 'a')))
            self.assertTrue(self.__alignment_contains_move(alignment, ('b', 'b')))
            self.assertTrue(self.__alignment_contains_move(alignment, ('c', 'c')))

    def test_infix_alignments_basic_loop_case_2(self):
        process_tree = parse("*(->('a','b'),->('c','d'))")
        trace = self.__generate_test_trace(['a', 'b', 'd'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertGreaterEqual(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST)
            self.assertTrue(self.__alignment_contains_move(alignment, ('a', 'a')))
            self.assertTrue(self.__alignment_contains_move(alignment, ('b', 'b')))

    def test_infix_alignments_basic_loop_case_3(self):
        process_tree = parse("*(->('a','b'),->('c','d'))")
        trace = self.__generate_test_trace(['b', 'c', 'd', 'a'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertEqual(alignment['cost'], 0)
            self.assertEqual(len(alignment['alignment']), 4)

    def test_infix_alignments_basic_loop_case_4(self):
        process_tree = parse("*(->('a','b'),->('c','d'))")
        trace = self.__generate_test_trace(['b', 'c', 'a', 'c', 'a', 'b', 'c'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)
            self.assertEqual(alignment['cost'], 30000)

    def test_infix_alignments_basic_loop_case_5(self):
        process_tree = parse("*(*(->('a','b'),tau), 'g')")
        trace = self.__generate_test_trace(['b', 'a', 'b'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)
            self.assertLess(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST)

    def test_infix_alignments_basic_loop_case_6(self):
        process_tree = parse("*(*(->('a','b'),'h'),tau)")
        trace = self.__generate_test_trace(['b', 'a', 'b'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)
            self.assertLess(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST)

    def test_infix_alignments_complex_tree_case_1(self):
        tree = "X(+(->('a','b'),+('c','d')),*(+('e','f'),'b'))"

        acceptable_infixes = [['b', 'c', 'd'], ['b', 'd'], ['a', 'd'], ['b', 'f'], ['e', 'b', 'e', 'f', 'b', 'f'],
                              ['d', 'c', 'b'],
                              ['f', 'e', 'b'], ['d', 'a', 'c', 'b']]
        not_acceptable_infixes = [['b', 'a'], ['c', 'd', 'b', 'f'], ['c', 'd', 'b', 'a']]

        self.__test_tree(tree, acceptable_infixes, not_acceptable_infixes)

    def test_infix_alignments_complex_tree_case_2(self):
        tree = "*(+(+(->('a','b'),+('c','d')),*(+('e','f'),'b')), ->('i',+('g','h')))"

        acceptable_infixes = [['b', 'c', 'd'], ['b', 'f', 'd', 'e', 'b', 'i', 'g'], ['i', 'h', 'g', 'd', 'e', 'a']]
        not_acceptable_infixes = [['b', 'f', 'd', 'e', 'b', 'i', 'g', 'h', 'b'], ['i', 'h', 'g', 'd', 'e', 'b']]

        self.__test_tree(tree, acceptable_infixes, not_acceptable_infixes)

    def test_infix_alignments_generates_postset_for_tau_transitions_in_tree(self):
        process_tree = parse("->(+(->('a','c'),->('b',tau)),->('d','e'))")
        trace = self.__generate_test_trace(['a', 'c', 'd'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertEqual(alignment['cost'], 0)
            self.assertEqual(len(alignment['alignment']), 3)

    def test_infix_alignments_duplicate_label(self):
        process_tree = parse("+(+('a',+('b','c')),->(+('c',X('f','g')),'d'))")
        trace = self.__generate_test_trace(['g', 'a', 'c', 'c'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertEqual(alignment['cost'], 0)

    def test_infix_alignments_activity_not_present_in_model(self):
        process_tree = parse("+(+('a',+('b','c')),->(+('c',X('f','g')),'d'))")
        trace = self.__generate_test_trace(['p'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertEqual(alignment['cost'], align_utils.STD_MODEL_LOG_MOVE_COST)

    def test_infix_alignments_single_activity_trace(self):
        process_tree = parse("+(+('a',+('b','c')),->(+('c',X('f','g')),'d'))")
        trace = self.__generate_test_trace(['a'])

        for variant in self.__get_variants():
            alignment = variant(trace, process_tree)

            self.assertEqual(alignment['cost'], 0)

    def test_reduce_process_tree(self):
        test_data = [
            {
                'tree': "->('a', +('b','c', ->('e', 'd')))",
                'expected_result': "+('b', 'c')",
                'activities_in_trace': ['b', 'c']
            },
            {
                'tree': "->('a', X('b','c', ->('e', 'd')))",
                'expected_result': "X('b', 'c')",
                'activities_in_trace': ['b', 'c']
            },
            {
                'tree': "->('a', ->('b','c', +('e', 'd'), 'f', X('g', 'h')))",
                'expected_result': "->('c', +('e', 'd'), 'f')",
                'activities_in_trace': ['c', 'f']
            },
            {
                'tree': "*(->('a', X('b','c', ->('e', 'd'), 'f')))",
                'expected_result': "*(->('a', X('b','c', ->('e', 'd'), 'f')))",
                'activities_in_trace': ['b', 'c']
            },
            {
                'tree': "+('a', *(*(->('d', 'e'), tau), 'b'))",
                'expected_result': "*(->('d', 'e'), tau)",
                'activities_in_trace': ['d']
            }
        ]

        for data in test_data:
            tree = parse(data['tree'])
            expected_result = parse(data['expected_result'])

            all_leaf_nodes = search_leaf_nodes_in_tree(tree)
            matching_leaf_nodes = get_matching_leaf_nodes(set(data['activities_in_trace']), all_leaf_nodes)
            reduced_tree = reduce_process_tree(matching_leaf_nodes)

            self.assertEqual(reduced_tree, expected_result)


if __name__ == '__main__':
    unittest.main()
