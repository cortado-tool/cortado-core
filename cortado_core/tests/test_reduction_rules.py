import unittest
import cortado_core.process_tree_utils.reduction as reduction
from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from cortado_core.process_tree_utils.reduction import __reduce_tau_loops as reduce_tau_loops


class ReductionRuleTests(unittest.TestCase):
    def test_remove_nodes_two_one_child_parents(self):
        pt_test = pt_parse("->(->('a'))")
        pt_true = pt_parse("'a'")
        self.assertEqual(pt_true, reduction.remove_operator_node_with_one_or_no_child(pt_test))

    def test_Remove_Nodes_One_Child(self):
        pt_test = pt_parse("->('A', 'B', X('C'))")
        pt_true = pt_parse("->('A', 'B', 'C')")
        self.assertEqual(reduction.remove_operator_node_with_one_or_no_child(pt_test), pt_true)

    def test_Remove_Nodes_One_Child_Root(self):
        pt_test = pt_parse("->('A')")
        pt_true = pt_parse("'A'")
        self.assertEqual(reduction.remove_operator_node_with_one_or_no_child(pt_test), pt_true)

    def test_Remove_Nodes_No_Child(self):
        pt_r = ProcessTree(operator=Operator.SEQUENCE)
        pt_l = pt_parse("->( +( 'A', 'C' ))")

        # ->(+(A, C), ->())
        pt_test = ProcessTree(operator=Operator.SEQUENCE, children=[pt_l, pt_r])

        pt_r.parent = pt_test
        pt_l.parent = pt_test

        pt_true = pt_parse("+('A','C')")

        self.assertEqual(reduction.remove_operator_node_with_one_or_no_child(pt_test), pt_true)

    def test_Remove_Nodes_No_Child_Root(self):
        pt_test = ProcessTree(operator=Operator.SEQUENCE)
        pt_true = None
        self.assertEqual(reduction.remove_operator_node_with_one_or_no_child(pt_test), pt_true)

    def test_associativity_reduction_choice(self):
        pt_test = pt_parse("X('A', 'B', X('Y', ->('C', 'E'), 'X', X('H', 'I', X('M', 'N'))))")
        pt_true = pt_parse("X('A', 'B', 'Y', ->('C', 'E'), 'X', 'H', 'I', 'M', 'N')")
        reduction._associativity_reduction_choice_parallelism(pt_test)
        self.assertEqual((pt_test), pt_true)

    def test_associativity_reduction_parallelism(self):
        pt_test = pt_parse("+('A', 'B', +('Y', ->('C', 'E'), 'X', +('H', 'I', +('M', 'N'))))")
        pt_true = pt_parse("+('A', 'B', 'Y', ->('C', 'E'), 'X', 'H', 'I', 'M', 'N')")
        reduction._associativity_reduction_choice_parallelism(pt_test)
        self.assertEqual((pt_test), pt_true)

    def test_reduce_sequences(self):
        pt_test = pt_parse("->('A', 'B', ->('Y', ->('C', 'E'), 'X', ->('H', 'I', +('M', 'N'))))")
        pt_true = pt_parse("->('A', 'B', 'Y', 'C', 'E', 'X', 'H', 'I', +('M', 'N'))")

        reduction._reduce_sequences(pt_test)
        self.assertEqual(pt_test, pt_true)

        pt_test_3 = pt_parse("->('A', 'C', tau, ->('H','G'), ->('X'))")
        pt_true_3 = pt_parse("->('A', 'C', tau, 'H', 'G', 'X')")

        reduction._reduce_sequences(pt_test_3)
        self.assertEqual(pt_test_3, pt_true_3)

    def test_general_tau_reduction(self):
        pt_test_1 = pt_parse("X('A', ->( tau, tau, tau)")
        pt_true_1 = pt_parse("X('A', tau)")
        pt_test_1 = reduction.general_tau_reduction(pt_test_1)

        self.assertEqual(pt_test_1, pt_true_1)

        pt_test_2 = pt_parse("->( tau, tau, tau)")
        pt_true_2 = ProcessTree()

        pt_test_2 = reduction.general_tau_reduction(pt_test_2)

        self.assertEqual(pt_test_2, pt_true_2)

        pt_test_3 = pt_parse("X('A',->( tau, tau, tau, ->( tau, tau, tau ) ) )")
        pt_true_3 = pt_parse("X('A', ->(tau, tau, tau, tau))")

        pt_test_3 = reduction.general_tau_reduction(pt_test_3)

        self.assertEqual(pt_test_3, pt_true_3)

    def test_tau_reduction_sequence(self):
        pt_test_1 = pt_parse("->('A', tau, 'C', tau, tau, +('H','G'))")
        pt_true_1 = pt_parse("->('A', 'C', +('H','G'))")

        reduction._tau_reduction_sequence_parallelism(pt_test_1)

        self.assertEqual(pt_test_1, pt_true_1)

        pt_test_2 = pt_parse("->(tau,tau)")
        pt_true_2 = pt_parse("tau")

        reduction._tau_reduction_sequence_parallelism(pt_test_2)

        self.assertEqual(pt_test_2, pt_true_2)

    def test_tau_reduction_parallelism(self):
        pt_test_1 = pt_parse("+('A', tau, 'C', tau, tau, ->('H','G'))")
        pt_true_1 = pt_parse("+('A', 'C', ->('H','G'))")

        reduction._tau_reduction_sequence_parallelism(pt_test_1)

        self.assertEqual(pt_test_1, pt_true_1)

    def test_tau_reduction_choice(self):
        pt_test_1 = pt_parse("X('A', tau, 'C', tau, tau, X('H','G'))")
        pt_true_1 = pt_parse("X('A', 'C', tau, X('H', 'G'))")

        reduction._tau_reduction_choice(pt_test_1)

        self.assertEqual(pt_test_1, pt_true_1)

    def test_apply_reduction_rules(self):
        pt_test_1 = pt_parse("+('A', 'C', tau, ->('H','G'), ->('X'), X(X('G'), 'H', +('A', 'C', tau, tau, tau, tau)))")
        pt_true_1 = pt_parse("+('A', 'C', ->('H','G'), ->('X'), X('H', +('A', 'C'), 'G'))")

        reduction.apply_reduction_rules(pt_test_1)

        self.assertEqual(pt_test_1, pt_true_1)

        pt_test_2 = pt_parse("+('A', 'C', tau, +('H','G'), ->('X'))")
        pt_true_2 = pt_parse("+('A', 'C', ->('X'), 'H', 'G')")

        reduction.apply_reduction_rules(pt_test_2)

        self.assertEqual(pt_test_2, pt_true_2)

    def test_reduce_tau_loops(self):
        pt = pt_parse("X(tau,*('a',tau))")
        reduce_tau_loops(pt, [])
        self.assertEqual(pt_parse("*(tau, 'a')"), pt)

    def test_reduce_tau_loops_both_positions_under_xor(self):
        pt = pt_parse("X(*('a',tau),tau)")
        reduce_tau_loops(pt, [])
        self.assertEqual(pt_parse("*(tau, 'a')"), pt)

    def test_reduce_tau_loops_nested_tree_in_do_part(self):
        pt = pt_parse("X(*(->('a', +('b', 'c')),tau),tau)")
        reduce_tau_loops(pt, [])
        self.assertEqual(pt_parse("*(tau, ->('a', +('b', 'c')))"), pt)

    def test_reduce_tau_loops_do_not_replace_frozen_trees(self):
        pt = pt_parse("X(tau,*('a',tau))")
        reduce_tau_loops(pt, [pt])
        self.assertEqual(pt_parse("X(tau,*('a',tau))"), pt)
        reduce_tau_loops(pt, [pt.children[1]])
        self.assertEqual(pt_parse("X(tau,*('a',tau))"), pt)
        reduce_tau_loops(pt, [pt.children[0]])
        self.assertEqual(pt_parse("*(tau, 'a')"), pt)
        pt = pt_parse("X(tau,*('a',tau))")
        reduce_tau_loops(pt, [pt.children[1].children[0]])
        self.assertEqual(pt_parse("*(tau, 'a')"), pt)
        pt = pt_parse("X(tau,*('a',tau))")
        reduce_tau_loops(pt, [pt.children[1].children[1]])
        self.assertEqual(pt_parse("*(tau, 'a')"), pt)

    def test_reduce_tau_loops_at_higher_depth(self):
        pt = pt_parse("->('a',+('f',X(tau,*('a',tau))),'c','d')")
        reduction.apply_reduction_rules(pt)
        self.assertEqual(pt_parse("->('a',+('f',*(tau,'a')),'c','d')"), pt)

    def test_reduce_to_at_most_two_loop_children(self):
        pt = pt_parse("*('a', 'b', 'c')")
        reduction.apply_reduction_rules(pt)
        self.assertEqual(pt_parse("*('a', X('b', 'c'))"), pt)

    def test_reduce_to_at_most_two_loop_children_complex(self):
        pt = pt_parse("*(->('a', X('b', tau)), +('a', 'b'), X('c', +('d', 'e')))")
        reduction.apply_reduction_rules(pt)
        self.assertEqual(pt_parse("*(->('a', X('b', tau)), X(+('a', 'b'), 'c', +('d', 'e')))"), pt)


if __name__ == '__main__':
    unittest.main()
