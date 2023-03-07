import unittest

from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignments

from cortado_core.lca_approach import set_preorder_ids_in_tree
from cortado_core.models.infix_type import InfixType
from cortado_core.tests.test_infix_alignments import generate_test_trace
from cortado_core.utils.alignment_utils import get_first_deviation
from cortado_core.utils.sublog_utils import generate_infix_sublog, calculate_sublog_for_lca
from cortado_core.utils.trace import TypedTrace
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import apply as pt_to_petri_net


class TestFragmentUtils(unittest.TestCase):
    def test_generate_infix_sublog_trace_lca_is_lca_infix(self):
        model = pt_parse("->('a', ->('b', X('c', tau), 'd'))")
        set_preorder_ids_in_tree(model)
        lca = model.children[1]
        infix = generate_test_trace('bc')

        sublog = generate_infix_sublog(infix, InfixType.PROPER_INFIX, model, lca)

        self.assertEqual(['b', 'c', 'd'], [e['concept:name'] for e in sublog[0]])

    def test_generate_infix_sublog_trace_lca_is_ancestor_of_lca_infix(self):
        model = pt_parse("->('a', ->('b', X('c', tau), 'd'))")
        set_preorder_ids_in_tree(model)
        lca = model
        infix = generate_test_trace('bc')

        sublog = generate_infix_sublog(infix, InfixType.PROPER_INFIX, model, lca)

        self.assertEqual(['a', 'b', 'c', 'd'], [e['concept:name'] for e in sublog[0]])

    def test_generate_infix_sublog_trace_lca_is_descendant_of_lca_infix(self):
        model = pt_parse("X(->('a', ->(*('b', tau), X('c', tau)), 'd'), 'e')")
        set_preorder_ids_in_tree(model)
        lca = model.children[0].children[1].children[0]
        infix = generate_test_trace('bbbd')

        sublog = generate_infix_sublog(infix, InfixType.PROPER_INFIX, model, lca)
        self.assertEqual(['b', 'b', 'b'], [e['concept:name'] for e in sublog[0]])

    def test_generate_infix_sublog_trace_lca_is_descendant_of_lca_infix_replayed_two_times(self):
        model = pt_parse("->('a', *(->(*('b', tau), 'c'), tau), 'e')")
        set_preorder_ids_in_tree(model)
        # lca: *('b', tau)
        lca = model.children[1].children[0].children[0]
        infix = generate_test_trace('bbcbbbc')

        sublog = generate_infix_sublog(infix, InfixType.PROPER_INFIX, model, lca)
        traces_as_tuples = [tuple([e['concept:name'] for e in t]) for t in sublog]
        self.assertEqual(2, len(sublog))
        self.assertIn(('b', 'b'), traces_as_tuples)
        self.assertIn(('b', 'b', 'b'), traces_as_tuples)

    def test_generate_infix_sublog_choice_with_lower_cost_without_replay(self):
        model = pt_parse("X(->('c','d'), ->('a', 'b', 'c', 'c', 'c', 'c', 'c', 'c', 'c'))")
        set_preorder_ids_in_tree(model)
        # lca: *('b', tau)
        lca = model
        infix = generate_test_trace('b')

        sublog = generate_infix_sublog(infix, InfixType.PROPER_INFIX, model, lca)

        self.assertEqual(['a', 'b', 'c', 'c', 'c', 'c', 'c', 'c', 'c'], [e['concept:name'] for e in sublog[0]])

    def test_generate_infix_sublog_not_replayable_infix(self):
        model = pt_parse("X(->('c','d'), ->('a', 'b', 'c', 'c', 'c', 'c', 'c', 'c', 'c'))")
        set_preorder_ids_in_tree(model)
        # lca: *('b', tau)
        lca = model
        infix = generate_test_trace('gh')

        perform_generation = lambda: generate_infix_sublog(infix, InfixType.PROPER_INFIX, model, lca)
        self.assertRaises(AssertionError, perform_generation)

    def test_generate_sublog(self):
        model = pt_parse("->('a', 'b', X('c', tau), 'd')")
        set_preorder_ids_in_tree(model)

        log = [TypedTrace(generate_test_trace('bc'), InfixType.PROPER_INFIX),
               TypedTrace(generate_test_trace('abd'), InfixType.NOT_AN_INFIX)]

        trace_to_add = generate_test_trace('bacd')
        net, im, fm = pt_to_petri_net(model)
        alignment = calculate_alignments(trace_to_add, net, im, fm, parameters={'ret_tuple_as_trans_desc': True})
        _, deviation_i = get_first_deviation(alignment)
        sublog = calculate_sublog_for_lca(model, log, model, alignment, deviation_i, trace_to_add,
                                          InfixType.NOT_AN_INFIX, None)
        traces_as_tuples = [tuple([e['concept:name'] for e in t]) for t in sublog]

        self.assertEqual(3, len(traces_as_tuples))
        self.assertIn(('a', 'b', 'd'), traces_as_tuples)
        self.assertIn(('b', 'a', 'c', 'd'), traces_as_tuples)
        self.assertIn(('a', 'b', 'c', 'd'), traces_as_tuples)

    def test_generate_sublog_lower_level_lca(self):
        model = pt_parse("->('a', 'b', *(X('c', 'e', tau), tau), 'd')")
        set_preorder_ids_in_tree(model)

        log = [TypedTrace(generate_test_trace('bccecccee'), InfixType.PROPER_INFIX),
               TypedTrace(generate_test_trace('abd'), InfixType.NOT_AN_INFIX)]

        trace_to_add = generate_test_trace('abcfed')
        net, im, fm = pt_to_petri_net(model)
        alignment = calculate_alignments(trace_to_add, net, im, fm, parameters={'ret_tuple_as_trans_desc': True})
        _, deviation_i = get_first_deviation(alignment)
        sublog = calculate_sublog_for_lca(model, log, model.children[2], alignment, deviation_i,
                                          generate_test_trace('cfe'),
                                          InfixType.NOT_AN_INFIX, None)
        traces_as_tuples = [tuple([e['concept:name'] for e in t]) for t in sublog]
        print(traces_as_tuples)
        self.assertEqual(3, len(traces_as_tuples))
        self.assertIn((), traces_as_tuples)
        self.assertIn(('c', 'f', 'e'), traces_as_tuples)
        self.assertIn(('c', 'c', 'e', 'c', 'c', 'c', 'e', 'e'), traces_as_tuples)

    def test_generate_sublog_filter_alignments_to_contain_valid_prefixes(self):
        model = pt_parse("+('d', 'c', 'b', 'a')")
        set_preorder_ids_in_tree(model)
        lca = model
        prefix = generate_test_trace('ab')

        sublog = generate_infix_sublog(prefix, InfixType.PREFIX, model, lca)

        self.assertTrue(sublog[0][0]['concept:name'] == 'a')
        self.assertTrue(sublog[0][1]['concept:name'] == 'b')

    def test_generate_sublog_filter_alignments_to_contain_valid_postfixes(self):
        model = pt_parse("+('d', 'c', 'b', 'a')")
        set_preorder_ids_in_tree(model)
        lca = model
        postfix = generate_test_trace('ab')

        sublog = generate_infix_sublog(postfix, InfixType.POSTFIX, model, lca)

        self.assertTrue(sublog[0][-2]['concept:name'] == 'a')
        self.assertTrue(sublog[0][-1]['concept:name'] == 'b')

    def test_generate_sublog_filter_alignments_to_contain_valid_infixes(self):
        model = pt_parse("+('d', 'c', 'b', 'a')")
        set_preorder_ids_in_tree(model)
        lca = model
        postfix = generate_test_trace('ca')

        sublog = generate_infix_sublog(postfix, InfixType.PROPER_INFIX, model, lca)

        for idx, event in enumerate(sublog[0]):
            if event['concept:name'] == 'c':
                self.assertEqual(sublog[0][idx + 1]['concept:name'], 'a')
