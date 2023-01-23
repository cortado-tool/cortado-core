import sys
import time
import uuid
from typing import Tuple, Set

from pm4py.objects.log.obj import Trace
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util import typing as pm4pyTyping
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.petri_net.semantics import ClassicSemantics

from cortado_core.alignments.prefix_alignments import algorithm as prefix_alignments
from cortado_core.alignments.infix_alignments import utils as infix_utils


def calculate_optimal_infix_alignment(trace: Trace, process_tree: ProcessTree,
                                      use_dijkstra: bool = False, naive: bool = True,
                                      timeout: int = sys.maxsize) -> pm4pyTyping.AlignmentResult:
    start = time.time()
    net, im, fm, n_added_tau_transitions = build_extended_petri_net_for_infix_alignments(process_tree, trace,
                                                                                         naive=naive, timeout=timeout)

    preprocessing_duration = time.time() - start
    timeout = timeout - preprocessing_duration

    prefix_alignment_variant = __get_prefix_alignment_variant(use_dijkstra)
    align_start = time.time()
    alignment = prefix_alignments.apply_trace(trace, net, im, fm, variant=prefix_alignment_variant,
                                              parameters={
                                                  prefix_alignments.Parameters.PARAM_MAX_ALIGN_TIME_TRACE: timeout})
    if alignment is None:
        alignment = {'timeout': True}
        return alignment

    alignment = infix_utils.remove_first_tau_move_from_alignment(alignment)

    alignment['alignment_duration'] = time.time() - align_start
    alignment['preprocessing_duration'] = preprocessing_duration
    alignment['added_tau_transitions'] = n_added_tau_transitions

    return alignment


def build_extended_petri_net_for_infix_alignments(process_tree: ProcessTree, trace: Trace, naive: bool, timeout: int) -> \
        Tuple[PetriNet, Marking, Marking, int]:
    net, im, fm = pt_converter.apply(process_tree)
    reachable_markings, is_timeout = infix_utils.generate_reachable_markings(net, im, timeout)
    if is_timeout:
        raise TimeoutError()

    if not naive:
        trace_activities = set([e['concept:name'] for e in trace])
        reachable_markings = __filter_reachable_markings(net, fm, reachable_markings, trace_activities)

    net, im = __add_invisible_tau_transitions(net, reachable_markings)

    return net, im, fm, len(reachable_markings)


def __filter_reachable_markings(net: PetriNet, fm: Marking, reachable_markings: Set[Marking],
                                trace_activities: Set[str]) -> Set[Marking]:
    semantics = ClassicSemantics()
    filtered_markings = {fm}

    for reachable_marking in reachable_markings:
        enabled_transitions = semantics.enabled_transitions(net, reachable_marking)
        for enabled_transition in enabled_transitions:
            if enabled_transition.label in trace_activities:
                filtered_markings.add(reachable_marking)
                break

    return filtered_markings


def __add_invisible_tau_transitions(net: PetriNet, reachable_markings: Set[Marking]) -> Tuple[PetriNet, Marking]:
    im, start_place = infix_utils.add_new_initial_place(net)

    for marking in reachable_markings:
        new_transition = PetriNet.Transition(str(uuid.uuid4()))
        net.transitions.add(new_transition)
        petri_utils.add_arc_from_to(start_place, new_transition, net)

        for place in marking:
            for i in range(marking.get(place)):
                petri_utils.add_arc_from_to(new_transition, place, net)

    return net, im


def __get_prefix_alignment_variant(use_dijkstra: bool):
    if use_dijkstra:
        return prefix_alignments.VERSION_DIJKSTRA_NO_HEURISTICS
    return prefix_alignments.VERSION_A_STAR
