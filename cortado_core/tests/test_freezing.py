import unittest

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.utils.generic import parse

from cortado_core.freezing.apply import add_trace_to_pt_language_with_freezing


class TestFreezing(unittest.TestCase):

    def test_frozen_subtree_removal_when_corresponding_flag_is_true(self):
        pt = parse("->('a', X('b', 'c'), 'd')")
        frozen_subtree = pt.children[1]

        trace = Trace()
        e1 = Event()
        e1['concept:name'] = 'a'
        e2 = Event()
        e2['concept:name'] = 'd'

        trace.append(e1)
        trace.append(e2)

        resulting_pt, frozen_subtrees = add_trace_to_pt_language_with_freezing(pt, [frozen_subtree], EventLog(), trace,
                                                                               try_pulling_lca_down=True,
                                                                               add_missing_frozen_subtrees_at_root_level=True)

        self.assertEqual(parse("+(->('a', 'd'), X(tau,X('b', 'c')))"), resulting_pt)
        self.assertEqual(frozen_subtree, frozen_subtrees[0])

    def test_frozen_subtree_removal_when_corresponding_flag_is_false(self):
        pt = parse("->('a', X('b', 'c'), 'd')")
        frozen_subtree = pt.children[1]

        trace = Trace()
        e1 = Event()
        e1['concept:name'] = 'a'
        e2 = Event()
        e2['concept:name'] = 'd'

        trace.append(e1)
        trace.append(e2)

        resulting_pt, frozen_subtrees = add_trace_to_pt_language_with_freezing(pt, [frozen_subtree], EventLog(), trace,
                                                                               try_pulling_lca_down=True,
                                                                               add_missing_frozen_subtrees_at_root_level=False)

        self.assertEqual(parse("->('a', 'd')"), resulting_pt)
        self.assertEqual(frozen_subtree, frozen_subtrees[0])

    def test_frozen_subtree_removal_when_corresponding_flag_is_true_multiple_missing_subtrees(self):
        pt = parse("->('a', X('b', 'c'), ->('e', 'f', 'g'), 'd')")
        frozen_subtrees = [pt.children[1], pt.children[2]]

        trace = Trace()
        e1 = Event()
        e1['concept:name'] = 'a'
        e2 = Event()
        e2['concept:name'] = 'd'

        trace.append(e1)
        trace.append(e2)

        resulting_pt, res_frozen_subtrees = add_trace_to_pt_language_with_freezing(pt, frozen_subtrees, EventLog(),
                                                                                   trace,
                                                                                   try_pulling_lca_down=True,
                                                                                   add_missing_frozen_subtrees_at_root_level=True)

        self.assertEqual(parse("+(->('a', 'd'), X(tau,->('e', 'f', 'g')), X(tau,X('b', 'c')))"), resulting_pt)
        self.assertEqual(frozen_subtrees, res_frozen_subtrees)

    def test_frozen_subtree_removal_when_corresponding_flag_is_false_multiple_missing_subtrees(self):
        pt = parse("->('a', X('b', 'c'), ->('e', 'f', 'g'), 'd')")
        frozen_subtrees = [pt.children[1], pt.children[2]]

        trace = Trace()
        e1 = Event()
        e1['concept:name'] = 'a'
        e2 = Event()
        e2['concept:name'] = 'd'

        trace.append(e1)
        trace.append(e2)

        resulting_pt, res_frozen_subtrees = add_trace_to_pt_language_with_freezing(pt, frozen_subtrees, EventLog(),
                                                                                   trace,
                                                                                   try_pulling_lca_down=True,
                                                                                   add_missing_frozen_subtrees_at_root_level=False)

        self.assertEqual(parse("->('a', 'd')"), resulting_pt)
        self.assertEqual(frozen_subtrees, res_frozen_subtrees)


if __name__ == '__main__':
    unittest.main()
