from typing import Tuple

from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils as pn_util
from pm4py.objects.process_tree.obj import Operator as pt_operator, ProcessTree


def apply(tree: ProcessTree) -> Tuple[PetriNet, Marking, Marking]:
    """
    Only supports loops with 2 children!
    :param tree:
    :return:
    """
    net = PetriNet(name=str(tree))
    if len(tree.children) == 0:
        pn_util.add_transition(net, label=tree.label, name=(tree, "active+closed"))
    else:
        sub_nets = list()
        for c in tree.children:
            sub_net, ini, fin = apply(c)
            sub_nets.append(sub_net)
        pn_util.merge(net, sub_nets)
        switch = {
            pt_operator.SEQUENCE: construct_sequence_pattern,
            pt_operator.XOR: construct_xor_pattern,
            pt_operator.PARALLEL: construct_and_pattern,
            pt_operator.LOOP: construct_loop_pattern,
        }
        net, ini, fin = switch[tree.operator](net, sub_nets, tree)
    if tree.parent is None:
        p_ini = pn_util.add_place(net)
        p_fin = pn_util.add_place(net)
        pn_util.add_arc_from_to(p_ini, _get_src_transition(net), net)
        pn_util.add_arc_from_to(_get_sink_transition(net), p_fin, net)
        return net, Marking({p_ini: 1}), Marking({p_fin: 1})
    return net, Marking(), Marking()


def _get_src_transition(sub_net):
    for t in sub_net.transitions:
        if len(pn_util.pre_set(t)) == 0:
            return t
    return None


def _get_sink_transition(sub_net):
    for t in sub_net.transitions:
        if len(pn_util.post_set(t)) == 0:
            return t
    return None


def _add_src_sink_transitions(net, p_s, p_t, tree):
    src = pn_util.add_transition(net, name=(tree, "active"))
    pn_util.add_arc_from_to(src, p_s, net)
    sink = pn_util.add_transition(net, name=(tree, "closed"))
    pn_util.add_arc_from_to(p_t, sink, net)
    return net, Marking(), Marking()


def construct_sequence_pattern(net, sub_nets, tree):
    places = [None] * (len(sub_nets) + 1)
    for i in range(len(sub_nets) + 1):
        places[i] = pn_util.add_place(net)
    for i in range(len(sub_nets)):
        pn_util.add_arc_from_to(places[i], _get_src_transition(sub_nets[i]), net)
        pn_util.add_arc_from_to(_get_sink_transition(sub_nets[i]), places[i + 1], net)
    src = pn_util.add_transition(net, name=(tree, "active"))
    pn_util.add_arc_from_to(src, places[0], net)
    sink = pn_util.add_transition(net, name=(tree, "closed"))
    pn_util.add_arc_from_to(places[len(places) - 1], sink, net)
    return net, Marking(), Marking()


def construct_xor_pattern(net, sub_nets, tree):
    p_s = pn_util.add_place(net)
    p_o = pn_util.add_place(net)
    for n in sub_nets:
        pn_util.add_arc_from_to(p_s, _get_src_transition(n), net)
        pn_util.add_arc_from_to(_get_sink_transition(n), p_o, net)
    return _add_src_sink_transitions(net, p_s, p_o, tree)


def construct_and_pattern(net, sub_nets, tree):
    p_s = [None] * len(sub_nets)
    p_t = [None] * len(sub_nets)
    for i in range(len(sub_nets)):
        p_s[i] = pn_util.add_place(net)
        p_t[i] = pn_util.add_place(net)
        pn_util.add_arc_from_to(p_s[i], _get_src_transition(sub_nets[i]), net)
        pn_util.add_arc_from_to(_get_sink_transition(sub_nets[i]), p_t[i], net)
    src = pn_util.add_transition(net, name=(tree, "active"))
    for p in p_s:
        pn_util.add_arc_from_to(src, p, net)
    sink = pn_util.add_transition(net, name=(tree, "closed"))
    for p in p_t:
        pn_util.add_arc_from_to(p, sink, net)
    return net, Marking(), Marking()


def construct_loop_pattern(net, sub_nets, tree):
    assert len(sub_nets) == 2
    p_s = pn_util.add_place(net)
    p_t = pn_util.add_place(net)
    pn_util.add_arc_from_to(p_s, _get_src_transition(sub_nets[0]), net)
    pn_util.add_arc_from_to(p_t, _get_src_transition(sub_nets[1]), net)
    pn_util.add_arc_from_to(_get_sink_transition(sub_nets[0]), p_t, net)
    pn_util.add_arc_from_to(_get_sink_transition(sub_nets[1]), p_s, net)
    net, ini, fin = _add_src_sink_transitions(net, p_s, p_t, tree)
    return net, Marking(), Marking()
