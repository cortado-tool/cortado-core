from typing import Tuple, Set
import time
import sys

from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util import typing as pm4py_typing
from pm4py.objects.petri_net.utils import align_utils
from pm4py.objects.petri_net.semantics import ClassicSemantics


def add_new_initial_place(net: PetriNet) -> Tuple[Marking, PetriNet.Place]:
    new_place = PetriNet.Place('new_initial_place')
    net.places.add(new_place)
    new_initial_marking = Marking()
    new_initial_marking[new_place] = 1

    return new_initial_marking, new_place


def remove_first_tau_move_from_alignment(alignment: pm4py_typing.AlignmentResult) -> pm4py_typing.AlignmentResult:
    for idx, move in enumerate(alignment['alignment']):
        if move[1] is None:
            # is tau move
            del alignment['alignment'][idx]

            # we have to adapt this line if we want to use a different cost function
            alignment['cost'] = alignment['cost'] - align_utils.STD_TAU_COST

            return alignment

    return alignment


def generate_reachable_markings(net: PetriNet, initial_marking: Marking, timeout: float = sys.maxsize) -> Tuple[
    Set[Marking], bool]:
    start_time = time.time()

    semantics = ClassicSemantics()
    to_discover = {initial_marking}
    discovered = set()

    while to_discover:
        if (time.time() - start_time) >= timeout:
            # interrupt the execution
            return set(), True
        m = to_discover.pop()
        discovered.add(m)

        enabled_transitions = semantics.enabled_transitions(net, m)

        for t in enabled_transitions:
            nm = semantics.weak_execute(t, net, m)
            if nm not in discovered:
                to_discover.add(nm)

    return discovered, False
