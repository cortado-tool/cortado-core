import unittest
from multiprocessing import Pool

from pm4py.objects.process_tree.obj import Operator

from cortado_core.lca_approach import add_trace_to_pt_language
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.log.obj import EventLog, Event, Trace

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
    def __generate_test_trace(self, trace_unformatted: str):
        trace = Trace()
        for event_unformatted in trace_unformatted:
            event = Event()
            event["concept:name"] = event_unformatted
            trace.append(event)

        return trace

    def test_pull_LCA_down(self):
        # The result isn't consistent across multiple applications of the Algorithm
        # tree_cnt = pt_parse("->( X( 'Wrench', tau ), *( X( ->( 'A', 'B' ), ->( 'C', 'D' ) ), tau ), 'E', 'F', X( ->( 'Wrench', X( 'Wrench', tau ) ), tau ) )")

        # tree = pt_parse("->(*(X(->('A','B'),->('C','D')), tau), ->('E','F') )")
        # tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end = False, try_pulling_lca_down=True)

        # self.assertEqual(tree, tree_cnt)

        tree_cnt = pt_parse(
            "->(X(tau, 'Wrench'), *(->('A', 'B'), ->('C', 'D')), 'E', 'F', *(tau,'Wrench'))")

        tree = pt_parse("-> (*(X(->('A','B'),->('C','D')), tau) ,->('E','F') )")
        tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=True, try_pulling_lca_down=True)

        self.assertEqual(tree, tree_cnt)

    def test_not_pulling_LCA_down(self):
        tree_cnt = pt_parse("+( 'C', 'D', 'E', 'F', *( 'A', tau ), *( tau, 'Wrench' ), *( 'B', tau ) )")

        tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
        tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=True, try_pulling_lca_down=False)

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
        new_event["concept:name"] = 'b'
        new_trace.append(new_event)

        # add trace <a,b> to a tree with that contains a single node 'a' and <a> in the initial log
        new_tree = add_trace_to_pt_language(tree, init_log, new_trace, True)
        expected_tree = pt_parse("->('a', X(tau, 'b'))")

        self.assertEqual(new_tree, expected_tree)

    def test_situation_that_led_to_infinite_loop_in_previous_version(self):
        tree = pt_parse("->('a', *(->('b', X('c', tau), 'd', X('e', tau)), tau), 'f')")

        trace_to_add = self.__generate_test_trace('abcdebcf')
        previously_added_traces = EventLog([self.__generate_test_trace('abdf')])
        new_tree = add_trace_to_pt_language(tree, previously_added_traces, trace_to_add, try_pulling_lca_down=True,
                                            add_artificial_start_end=False)
        expected_tree = pt_parse("->('a', *(->('b', X(tau, 'c'), X(tau, ->('d', X(tau, 'e')))), tau), 'f')")

        self.assertEqual(expected_tree, new_tree)

    def test_lca_approach_with_process_pool(self):
        tree = pt_parse("->('a', *(->('b', X('c', tau), 'd', X('e', tau)), tau), 'f')")

        trace_to_add = self.__generate_test_trace('abcdebcf')
        previously_added_traces = EventLog([self.__generate_test_trace('abdf')])
        with Pool() as pool:
            new_tree = add_trace_to_pt_language(tree, previously_added_traces, trace_to_add, try_pulling_lca_down=True,
                                                add_artificial_start_end=False, pool=pool)
        expected_tree = pt_parse("->('a', *(->('b', X(tau, 'c'), X(tau, ->('d', X(tau, 'e')))), tau), 'f')")

        self.assertEqual(expected_tree, new_tree)
