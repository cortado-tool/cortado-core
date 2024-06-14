import unittest
from cortado_core.model_repair.algorithm import (
    Sublog,
    Subtrace,
    align_subtraces,
    group_into_sublogs,
)
from pm4py.objects.log.obj import EventLog, Event, Trace
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils

p1 = PetriNet.Place("p1")
p2 = PetriNet.Place("p2")
p3 = PetriNet.Place("p3")
p4 = PetriNet.Place("p4")
p5 = PetriNet.Place("p5")
p6 = PetriNet.Place("p6")

t_a = PetriNet.Transition("a1", "a")
t_b = PetriNet.Transition("b1", "b")
t_c = PetriNet.Transition("c1", "c")
t_d = PetriNet.Transition("d1", "d")
t_d1 = PetriNet.Transition("d2", "d")
t_e = PetriNet.Transition("e1", "e")

net = PetriNet("net1", [p1, p2, p3, p4, p5, p6], [t_a, t_b, t_c, t_d, t_d1, t_e])
petri_utils.add_arc_from_to(p1, t_a, net)
petri_utils.add_arc_from_to(p2, t_c, net)
petri_utils.add_arc_from_to(p3, t_b, net)
petri_utils.add_arc_from_to(p4, t_d, net)
petri_utils.add_arc_from_to(p5, t_e, net)
petri_utils.add_arc_from_to(p5, t_d, net)

petri_utils.add_arc_from_to(t_a, p2, net)
petri_utils.add_arc_from_to(t_a, p3, net)
petri_utils.add_arc_from_to(t_b, p5, net)
petri_utils.add_arc_from_to(t_c, p4, net)
petri_utils.add_arc_from_to(t_d, p6, net)
petri_utils.add_arc_from_to(t_e, p3, net)

petri_utils.add_arc_from_to(p1, t_d1, net)
petri_utils.add_arc_from_to(t_d1, p6, net)

im = Marking({p1: 1})
fm = Marking({p6: 1})

# view_petri_net(net, im, fm)

log = EventLog()
a = Event({"concept:name": "a"})
b = Event({"concept:name": "b"})
c = Event({"concept:name": "c"})
d = Event({"concept:name": "d"})
e = Event({"concept:name": "e"})
f = Event({"concept:name": "f"})

t1 = Trace([a, c, f, c, e, d])
log.append(t1)

t2 = Trace([a, b, c, c, f, e, d])
log.append(t2)


class ModelRepairTests(unittest.TestCase):
    def test_subtrace_decomposition(self):
        subtraces_test = set()
        subtraces_test.add(Subtrace(tuple("abcdefghi"), frozenset({p1})))
        subtraces_test.add(Subtrace(tuple("abghf"), frozenset({p2})))
        subtraces_test.add(Subtrace(tuple("cdef"), frozenset({p1, p3})))
        subtraces_test.add(Subtrace(tuple("cd"), frozenset({p2})))
        subtraces_test.add(Subtrace(tuple("dc"), frozenset({p1, p2})))

        decomposed_subtraces = {
            frozenset({subtrace.trace for subtrace in eq_class})
            for eq_class in align_subtraces(subtraces_test)
        }

        sub1 = frozenset({tuple("ab")})
        sub2 = frozenset({tuple("cdef"), tuple("cd"), tuple("dc")})
        sub3 = frozenset({tuple("ghf"), tuple("ghi")})

        assert decomposed_subtraces == {sub1, sub2, sub3}

    def test_grouping_subtraces(self):
        sub1 = Subtrace(tuple("abc"), frozenset({p1, p2}))
        sub2 = Subtrace(tuple("abd"), frozenset({p2, p3}))
        sub3 = Subtrace(tuple("abe"), frozenset({p2, p3}))
        sub4 = Subtrace(tuple("abf"), frozenset({p1, p4}))

        subs = set([sub1, sub2, sub3, sub4])

        sublogs = group_into_sublogs(subs)

        sublog1 = Sublog(
            frozenset([sub1, sub2, sub3]),
            frozenset({p2}),
        )
        sublog2 = Sublog(frozenset({sub4}), frozenset({p1, p4}))

        assert sublogs == {sublog1, sublog2}
