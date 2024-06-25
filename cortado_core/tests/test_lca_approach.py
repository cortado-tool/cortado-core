import random
import unittest
from multiprocessing import Pool

from pm4py.objects.log.obj import EventLog, Event, Trace
from pm4py.objects.process_tree.obj import Operator
from pm4py.objects.process_tree.utils.generic import parse as pt_parse, tree_sort

from cortado_core.lca_approach import add_trace_to_pt_language
from cortado_core.models.infix_type import InfixType
from cortado_core.tests.test_infix_alignments import generate_test_trace
from cortado_core.utils.alignment_utils import typed_trace_fits_process_tree
from cortado_core.utils.trace import TypedTrace

L = EventLog()
e1 = Event()
e1["concept:name"] = "A"
e2 = Event()
e2["concept:name"] = "B"
e3 = Event()
e3["concept:name"] = "C"
e4 = Event()
e4["concept:name"] = "D"
e5 = Event()
e5["concept:name"] = "A"
e6 = Event()
e6["concept:name"] = "B"
e7 = Event()
e7["concept:name"] = "E"
e8 = Event()
e8["concept:name"] = "F"
t = Trace()
t.append(e1)
t.append(e2)
t.append(e3)
t.append(e4)
t.append(e5)
t.append(e6)
t.append(e7)
t.append(e8)
L.append(t)

t2 = Trace()
t2.append(e1)
t2.append(e2)
t2.append(e2)
t2.append(e3)
t2.append(e4)
t2.append(e5)
t2.append(e6)
t2.append(e7)
t2.append(e8)

t3 = Trace()
t3.append(Event({"concept:name": "Wrench"}))
t3.append(e1)
t3.append(e2)
t3.append(e3)
t3.append(e4)
t3.append(e5)
t3.append(e6)
t3.append(e7)
t3.append(e8)
t3.append(Event({"concept:name": "Wrench"}))
t3.append(Event({"concept:name": "Wrench"}))


class LCA_Approach_Tests(unittest.TestCase):
    def test_pull_LCA_down(self):
        # The result isn't consistent across multiple applications of the Algorithm
        # tree_cnt = pt_parse("->( X( 'Wrench', tau ), *( X( ->( 'A', 'B' ), ->( 'C', 'D' ) ), tau ), 'E', 'F', X( ->( 'Wrench', X( 'Wrench', tau ) ), tau ) )")

        # tree = pt_parse("->(*(X(->('A','B'),->('C','D')), tau), ->('E','F') )")
        # tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end = False, try_pulling_lca_down=True)

        # self.assertEqual(tree, tree_cnt)

        tree_cnt = pt_parse(
            "->(X(tau, 'Wrench'), *(->('A', 'B'), ->('C', 'D')), 'E', 'F', *(tau,'Wrench'))"
        )

        tree = pt_parse("-> (*(X(->('A','B'),->('C','D')), tau) ,->('E','F') )")
        tree = add_trace_to_pt_language(
            tree, L, t3, add_artificial_start_end=True, try_pulling_lca_down=True
        )

        self.assertEqual(tree_sort(tree), tree_sort(tree_cnt))

    def test_not_pulling_LCA_down(self):
        tree_cnt = pt_parse(
            "+( 'C', 'D', 'E', 'F', *( 'A', tau ), *( tau, 'Wrench' ), *( 'B', tau ) )"
        )

        tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
        tree = add_trace_to_pt_language(
            tree, L, t3, add_artificial_start_end=True, try_pulling_lca_down=False
        )

        self.assertEqual(set(tree_cnt.children), set(tree.children))
        self.assertEqual(Operator.PARALLEL, tree.operator)

    def test_add_trace_to_tree_without_operators(self):
        tree = pt_parse("'a'")

        init_log = EventLog()
        init_trace = Trace()
        init_event = Event()
        init_event["concept:name"] = "a"

        init_trace.append(init_event)
        init_log.append(init_trace)

        new_trace = Trace()
        new_trace.append(init_event)
        new_event = Event()
        new_event["concept:name"] = "b"
        new_trace.append(new_event)

        # add trace <a,b> to a tree with that contains a single node 'a' and <a> in the initial log
        new_tree = add_trace_to_pt_language(tree, init_log, new_trace, True)
        expected_tree = pt_parse("->('a', X(tau, 'b'))")

        self.assertEqual(tree_sort(new_tree), tree_sort(expected_tree))

    def test_situation_that_led_to_infinite_loop_in_previous_version(self):
        tree = pt_parse("->('a', *(->('b', X('c', tau), 'd', X('e', tau)), tau), 'f')")

        trace_to_add = generate_test_trace("abcdebcf")
        previously_added_traces = EventLog([generate_test_trace("abdf")])
        new_tree = add_trace_to_pt_language(
            tree,
            previously_added_traces,
            trace_to_add,
            try_pulling_lca_down=True,
            add_artificial_start_end=False,
        )
        expected_tree = pt_parse(
            "->('a', *(->('b', X(tau, 'c'), X(tau, ->('d', X(tau, 'e')))), tau), 'f')"
        )

        self.assertEqual(tree_sort(expected_tree), tree_sort(new_tree))

    def test_lca_approach_with_process_pool(self):
        tree = pt_parse("->('a', *(->('b', X('c', tau), 'd', X('e', tau)), tau), 'f')")

        trace_to_add = generate_test_trace("abcdebcf")
        previously_added_traces = EventLog([generate_test_trace("abdf")])
        with Pool() as pool:
            new_tree = add_trace_to_pt_language(
                tree,
                previously_added_traces,
                trace_to_add,
                try_pulling_lca_down=True,
                add_artificial_start_end=False,
                pool=pool,
            )
        expected_tree = pt_parse(
            "->('a', *(->('b', X(tau, 'c'), X(tau, ->('d', X(tau, 'e')))), tau), 'f')"
        )

        self.assertEqual(tree_sort(expected_tree), tree_sort(new_tree))

    def test_lca_approach_add_infix(self):
        tree = pt_parse("->('a', 'b', +('c', 'd'))")
        trace_to_add = TypedTrace(generate_test_trace("be"), InfixType.PROPER_INFIX)
        previously_added = [
            TypedTrace(generate_test_trace("abcd"), InfixType.NOT_AN_INFIX),
            TypedTrace(generate_test_trace("abdc"), InfixType.NOT_AN_INFIX),
        ]

        expected_tree = pt_parse("->('a', 'b', X(tau, 'e'), +('c', 'd'))")
        new_tree = add_trace_to_pt_language(
            tree,
            previously_added,
            trace_to_add,
            try_pulling_lca_down=True,
            add_artificial_start_end=False,
        )

        self.assertEqual(tree_sort(expected_tree), tree_sort(new_tree))

    def test_lca_approach_add_postfix(self):
        tree = pt_parse("->('a', 'b', +('c', 'd'))")
        trace_to_add = TypedTrace(generate_test_trace("becd"), InfixType.POSTFIX)
        previously_added = [
            TypedTrace(generate_test_trace("abcd"), InfixType.NOT_AN_INFIX),
            TypedTrace(generate_test_trace("abdc"), InfixType.NOT_AN_INFIX),
        ]

        # X(tau, 'd') in introduced because of the lca to rediscover after pulldown is ->(b, +(c,d)) with sublog
        # <b,c,d>, <b,d,c>, <b,e,c> <---- added trace
        expected_tree = pt_parse("->('a', 'b', X(tau, 'e'), +('c', 'd'))")
        new_tree = add_trace_to_pt_language(
            tree,
            previously_added,
            trace_to_add,
            try_pulling_lca_down=True,
            add_artificial_start_end=False,
        )

        self.assertEqual(tree_sort(expected_tree), tree_sort(new_tree))

    def test_lca_approach_add_prefix(self):
        tree = pt_parse("->('a', 'b', +('c', 'd'))")
        trace_to_add = TypedTrace(generate_test_trace("ea"), InfixType.PREFIX)
        previously_added = [
            TypedTrace(generate_test_trace("abcd"), InfixType.NOT_AN_INFIX),
            TypedTrace(generate_test_trace("abdc"), InfixType.NOT_AN_INFIX),
        ]

        expected_tree = pt_parse("->(X(tau, 'e'), 'a', 'b', +('c', 'd'))")
        new_tree = add_trace_to_pt_language(
            tree,
            previously_added,
            trace_to_add,
            try_pulling_lca_down=True,
            add_artificial_start_end=False,
        )

        self.assertEqual(tree_sort(expected_tree), tree_sort(new_tree))

    def test_infixes_in_already_added_traces(self):
        tree = pt_parse("->('a', 'b', +('c', 'd'))")
        trace_to_add = TypedTrace(generate_test_trace("aefg"), InfixType.NOT_AN_INFIX)
        previously_added = [
            TypedTrace(generate_test_trace("a"), InfixType.PREFIX),
            TypedTrace(generate_test_trace("bc"), InfixType.PROPER_INFIX),
            TypedTrace(generate_test_trace("cd"), InfixType.POSTFIX),
        ]

        expected_tree = pt_parse(
            "->( 'a', X( ->( 'e', X( ->( 'f', X( 'g', tau ) ), tau ) ), tau ), X( tau, ->( X( tau, 'b' ), +( 'd', X( tau, 'c' ) ) ) ) )"
        )
        new_tree = add_trace_to_pt_language(
            tree,
            previously_added,
            trace_to_add,
            try_pulling_lca_down=True,
            add_artificial_start_end=True,
        )

        self.assertEqual(tree_sort(expected_tree), tree_sort(new_tree))

    def test_add_infix_without_lca_pulldown(self):
        tree = pt_parse("->('a', 'b', 'c' , 'd', 'e', 'f')")
        trace_to_add = TypedTrace(generate_test_trace("bcef"), InfixType.PROPER_INFIX)
        previously_added = [
            TypedTrace(generate_test_trace("abcdef"), InfixType.NOT_AN_INFIX)
        ]
        expected_tree = pt_parse("->( 'a', 'b', 'c', X( tau, 'd' ), 'e', 'f' )")
        new_tree = add_trace_to_pt_language(
            tree,
            previously_added,
            trace_to_add,
            try_pulling_lca_down=False,
            add_artificial_start_end=True,
        )
        self.assertEqual(tree_sort(expected_tree), tree_sort(new_tree))

    def test_random_traces(self):
        random.seed(10)

        def generate_random_trace(max_length: int, labels: list[str]):
            trace = Trace()
            length = random.randint(0, max_length)
            for i in range(length):
                label = labels[random.randint(0, len(labels) - 1)]
                e = Event()
                e["concept:name"] = label
                trace.append(e)

            return TypedTrace(trace, InfixType(random.randint(1, 4)))

        tree = pt_parse("->('a', 'b', +('c', 'd'))")
        log = [
            generate_random_trace(8, ["a", "b", "c", "d", "e", "f"]) for _ in range(10)
        ]
        added = []

        for idx, trace_to_add in enumerate(log):
            tree = add_trace_to_pt_language(
                tree,
                added,
                trace_to_add,
                try_pulling_lca_down=True,
                add_artificial_start_end=False,
            )
            added.append(trace_to_add)
            for i2, trace in enumerate(added):
                self.assertTrue(typed_trace_fits_process_tree(trace, tree))
