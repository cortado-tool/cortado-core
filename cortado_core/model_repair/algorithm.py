# Implementation of https://doi.org/10.1016/j.is.2013.12.007

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from functools import reduce
from itertools import chain, combinations, product
import math
from multiprocessing import Pool

from typing import Callable, Dict, FrozenSet, List, Optional, Set, Tuple, Union
from uuid import uuid4
import warnings
from pm4py.objects.log.obj import EventLog, Event, Trace
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.discovery import discover_petri_net_inductive
from pm4py.util.typing import AlignmentResult
from cortado_core.alignments.prefix_alignments.variants.a_star import (
    PARAM_MODEL_COST_FUNCTION,
    PARAM_TRACE_COST_FUNCTION,
)
from pm4py.algo.conformance.alignments.petri_net.algorithm import (
    apply as calculate_alignment,
    variants as variants_calculate_alignments,
)

from cortado_core.models.infix_type import InfixType
from cortado_core.utils.alignment_utils import (
    alignment_contains_deviation,
    is_log_move,
    is_model_move,
    is_model_move_on_visible_activity,
    is_sync_move,
)
from cortado_core.utils.parallel_alignments import (
    calculate_alignment_a_star,
    calculate_alignments_parallel,
)
from cortado_core.utils.start_and_end_activities import (
    ARTIFICIAL_END_ACTIVITY_NAME,
    ARTIFICIAL_START_ACTIVITY_NAME,
    add_artificial_start_and_end_activity_to_Log,
)
from cortado_core.utils.sublog_utils import remove_zeros_from_marking, replay_move
from cortado_core.utils.trace import TypedTrace
from cortado_core.utils.petri_net_utils import (
    get_all_distances,
    get_all_paths_between_transitions,
    get_distances_from_transitions_to_places,
    get_transitions_by_label,
)

from more_itertools import partitions

from pm4py.vis import view_petri_net, view_alignments
import pm4py.visualization.process_tree.visualizer as tree_vis

SHOW_VISUALIZATIONS = False


@dataclass
class Subtrace:
    trace: Tuple[str]
    location: FrozenSet[PetriNet.Place]
    previous_last_place: FrozenSet[PetriNet.Place] = None

    def __hash__(self):
        return hash((self.trace, self.location))

    def __eq__(self, other):
        if not isinstance(other, Subtrace):
            return False
        return self.trace == other.trace and self.location == other.location

    def __len__(self):
        return len(self.trace)


@dataclass
class Sublog:
    log: FrozenSet[Subtrace]
    location: FrozenSet[PetriNet.Place]

    def __hash__(self):
        return hash((self.log, self.location))

    def __eq__(self, other):
        if not isinstance(other, Sublog):
            return False
        return self.log == other.log and self.location == other.location

    def __len__(self):
        return len(self.log)

    def to_event_log(self):
        event_log = EventLog()
        for trace in self.log:
            t = Trace()
            for activity in trace.trace:
                t.append(Event({"concept:name": activity}))
            event_log.append(t)
        return event_log


def induced_subnet(
    full_petri_net: PetriNet, inducing_transitions: set[PetriNet.Transition]
) -> Tuple[PetriNet, Marking, Marking]:
    subnet = PetriNet("Induced Subnet")
    for t in inducing_transitions:
        petri_utils.add_transition(subnet, t.name, t.label)
        for p in petri_utils.pre_set(t).union(petri_utils.post_set(t)):
            if p.name not in [p.name for p in subnet.places]:
                petri_utils.add_place(subnet, p.name)

    for arc in full_petri_net.arcs:
        if type(arc.source) is PetriNet.Place:
            for p, t in product(subnet.places, subnet.transitions):
                if p.name == arc.source.name and (t.name, t.label) == (
                    arc.target.name,
                    arc.target.label,
                ):
                    petri_utils.add_arc_from_to(p, t, subnet)
        else:
            for t, p in product(subnet.transitions, subnet.places):
                if (t.name, t.label) == (
                    arc.source.name,
                    arc.source.label,
                ) and p.name == arc.target.name:
                    petri_utils.add_arc_from_to(t, p, subnet)
    initial_marking = Marking()
    final_marking = Marking()

    for place in subnet.places:
        if len(place.in_arcs) == 0:
            initial_marking[place] = 1
        if len(place.out_arcs) == 0:
            final_marking[place] = 1

    if __debug__ and SHOW_VISUALIZATIONS:
        view_petri_net(subnet, initial_marking, final_marking)

    return subnet, initial_marking, final_marking


def add_parallel_silent_transitions(
    petri_net: PetriNet, trans_to_be_skipped: Set[PetriNet.Transition]
):
    for skipped_trans in trans_to_be_skipped:
        tau = petri_utils.add_transition(petri_net, str(uuid4()))
        pre_set = petri_utils.pre_set(skipped_trans)
        post_set = petri_utils.post_set(skipped_trans)
        for place in pre_set:
            petri_utils.add_arc_from_to(place, tau, petri_net)
        for place in post_set:
            petri_utils.add_arc_from_to(tau, place, petri_net)


def repair_for_loops(
    petri_net: PetriNet,
    initial_marking: Marking,
    final_marking: Marking,
    log: EventLog,
    pool: Optional[Pool] = None,
):
    if pool:
        alignments = calculate_alignments_parallel(
            log,
            petri_net,
            initial_marking,
            final_marking,
            parameters={"ret_tuple_as_trans_desc": True},
            pool=pool,
        )
    else:
        alignments = calculate_alignment(
            log,
            petri_net,
            initial_marking,
            final_marking,
            parameters={"ret_tuple_as_trans_desc": True},
        )

    subtraces: Set[Subtrace] = set()

    for alignment in alignments:
        if alignment_contains_deviation(alignment):
            if not validate_iteration_preserving_alignment(alignment):
                alignment = make_alignment_iteration_preserving(alignment)
            assert validate_iteration_preserving_alignment(alignment)

            subs = get_subtraces(alignment, petri_net, initial_marking)
            subtraces.update(subs)

    sublogs = group_into_aligned_sublogs(subtraces)
    sublogs = pick_relevant_locations(sublogs)

    add_loops(petri_net, sublogs, pool=pool)


def repair_for_subprocess_and_skipped_events(
    petri_net: PetriNet,
    initial_marking: Marking,
    final_marking: Marking,
    log: EventLog,
    pool: Optional[Pool] = None,
):
    global_cost_function = get_global_cost_function(
        petri_net, initial_marking, final_marking, log, pool=pool
    )

    alignments = []
    for trace in log:
        if pool:
            alignment = pool.apply_async(
                calculate_alignment_a_star,
                args=[trace, petri_net, initial_marking, final_marking],
                kwds={
                    "parameters": {
                        "ret_tuple_as_trans_desc": True,
                        PARAM_TRACE_COST_FUNCTION: [
                            global_cost_function(act) for act in trace
                        ],
                        PARAM_MODEL_COST_FUNCTION: {
                            t: global_cost_function(t) for t in petri_net.transitions
                        },
                    }
                },
            )
        else:
            alignment = calculate_alignment(
                trace,
                petri_net,
                initial_marking,
                final_marking,
                parameters={
                    "ret_tuple_as_trans_desc": True,
                    PARAM_TRACE_COST_FUNCTION: [
                        global_cost_function(act) for act in trace
                    ],
                    PARAM_MODEL_COST_FUNCTION: {
                        t: global_cost_function(t) for t in petri_net.transitions
                    },
                },
                variant=variants_calculate_alignments.state_equation_a_star,
            )

        alignments.append(alignment)

    if pool:
        alignments = [async_result.get() for async_result in alignments]

    subtraces: Set[Subtrace] = set()
    skipped_transitions: Set[PetriNet.Transition] = set()

    for alignment in alignments:
        if alignment_contains_deviation(alignment):
            skipped_transitions.update(get_skipped_transitions(alignment, petri_net))
            subs = get_subtraces(alignment, petri_net, initial_marking)
            subtraces.update(subs)

    sublogs = group_into_aligned_sublogs(subtraces)
    sublogs = pick_relevant_locations(sublogs)

    add_parallel_silent_transitions(petri_net, skipped_transitions)

    for sublog in sublogs:
        repair_model_at_location(petri_net, sublog)


def remove_infrequent_nodes(
    petri_net: PetriNet,
    initial_marking: Marking,
    final_marking: Marking,
    log: EventLog,
    threshold: float = 0,
    pool: Optional[Pool] = None,
):
    if threshold < 0:
        raise ValueError("threshold has to be greater or equal to 0.")
    if pool:
        alignments = calculate_alignments_parallel(
            log,
            petri_net,
            initial_marking,
            final_marking,
            parameters={"ret_tuple_as_trans_desc": True},
            pool=pool,
        )
    else:
        alignments = calculate_alignment(
            log,
            petri_net,
            initial_marking,
            final_marking,
            parameters={"ret_tuple_as_trans_desc": True},
        )

    place_counter = Counter(initial_marking)
    transition_counter = Counter()
    for alignment in alignments:
        assert not alignment_contains_deviation(alignment)
        for move in alignment["alignment"]:
            transition = petri_utils.get_transition_by_name(petri_net, move[0][1])
            assert transition is not None
            transition_counter[transition] += 1
            for place in petri_utils.post_set(transition):
                place_counter[place] += 1
    for infrequent_place in [
        place for place in petri_net.places if place_counter[place] <= threshold
    ]:
        petri_utils.remove_place(petri_net, infrequent_place)
    for infrequent_transition in [
        transition
        for transition in petri_net.transitions
        if transition_counter[transition] <= threshold
    ]:
        petri_utils.remove_transition(petri_net, infrequent_transition)
    if __debug__ and SHOW_VISUALIZATIONS:
        view_petri_net(petri_net, initial_marking, final_marking)


def get_global_cost_function(
    petri_net: PetriNet,
    initial_marking: Marking,
    final_marking: Marking,
    log: EventLog,
    pool: Optional[Pool] = None,
):
    if pool:
        alignments = calculate_alignments_parallel(
            log,
            petri_net,
            initial_marking,
            final_marking,
            parameters={"ret_tuple_as_trans_desc": True},
            pool=pool,
        )
    else:
        alignments = calculate_alignment(
            log,
            petri_net,
            initial_marking,
            final_marking,
            parameters={"ret_tuple_as_trans_desc": True},
        )
    log_move_counter = Counter()
    model_move_counter = Counter()
    for alignment in alignments:
        for move in alignment["alignment"]:
            if is_log_move(move):
                log_move_counter[move[1][0]] += 1
            elif is_model_move(move):
                model_move_counter[move[0][1]] += 1
    if len(log_move_counter) > 0 and len(model_move_counter) > 0:
        devMax = max(*log_move_counter.values(), *model_move_counter.values())
    elif len(model_move_counter) > 0:
        devMax = max(model_move_counter.values())
    elif len(log_move_counter) > 0:
        devMax = max(log_move_counter.values())
    else:
        return lambda _: 1

    def global_cost_function(x: PetriNet.Transition | Event):
        if type(x) is PetriNet.Transition:
            return devMax / (model_move_counter[x.name] + 1)
        elif type(x) is Event:
            return devMax / (log_move_counter[x["concept:name"]] + 1)
        else:
            raise TypeError()

    return global_cost_function


def repair_petri_net_with_log(
    petri_net: PetriNet,
    initial_marking: Marking,
    final_marking: Marking,
    log: EventLog,
    pool: Optional[Pool] = None,
):
    """
    Splits the log into fitting and non-fitting traces.
    Then the process model is repaired s.t. the log will then fit all traces.
    :param petri_net: petri_net to repaired
    :param initial_marking: initial marking of the petri net
    :param final_marking: final marking of the petri net
    :param log: event log
    :param pool: Pool to parallelize alignment computations
    :return: process model that accepts the given log
    """

    repair_for_loops(petri_net, initial_marking, final_marking, log, pool=pool)
    repair_for_subprocess_and_skipped_events(
        petri_net, initial_marking, final_marking, log, pool=pool
    )
    remove_infrequent_nodes(petri_net, initial_marking, final_marking, log, pool=pool)

    if __debug__:
        if pool:
            final_alignments = calculate_alignments_parallel(
                log,
                petri_net,
                initial_marking,
                final_marking,
                parameters={"ret_tuple_as_trans_desc": True},
                pool=pool,
            )
        else:
            final_alignments = calculate_alignment(
                log,
                petri_net,
                initial_marking,
                final_marking,
                parameters={"ret_tuple_as_trans_desc": True},
            )

        for alignment in final_alignments:
            assert not alignment_contains_deviation(alignment)


def add_loops(
    petri_net: PetriNet,
    sublogs: Set[Sublog],
    pool: Optional[Pool] = None,
):
    # Find the body of a loop that contains all transitions related to log moves
    # in the given loop hypotheses. The loop body consists of all transitions given
    # in the log moves, their pre- and post-places, and all nodes of the net that
    # lie on a path between any two of the given transitions.
    # The loop hypotheses is then tested. If it can replay the sublog, a transition is
    # added to the petri_net.
    petri_net_unmodified = deepcopy(petri_net)
    distances_transitions_to_places = get_distances_from_transitions_to_places(
        petri_net_unmodified
    )
    for sublog in sublogs:
        T_s = set()
        for trace in sublog.log:
            for activity_label in set(trace.trace):
                transition_candidates = get_transitions_by_label(
                    petri_net_unmodified, activity_label
                )
                # find transition with minimal distance to a place from the location of the log
                shortest_distance_to_loop_exit = math.inf
                transition_closest_to_loop_exit = None
                for transition in transition_candidates:
                    distances = distances_transitions_to_places[transition]
                    distance_to_loop_exit = math.inf
                    for loop_exit_place in sublog.location:
                        distance_to_loop_exit = min(
                            distance_to_loop_exit, distances[loop_exit_place.name]
                        )
                    if distance_to_loop_exit < shortest_distance_to_loop_exit:
                        shortest_distance_to_loop_exit = distance_to_loop_exit
                        transition_closest_to_loop_exit = transition
                if transition_closest_to_loop_exit:
                    T_s.add(transition_closest_to_loop_exit)
        if (len(T_s)) == 0:
            continue
        else:
            for t1, t2 in combinations(T_s, 2):
                for vertex in get_all_paths_between_transitions(
                    petri_net_unmodified, t1, t2
                ):
                    if type(vertex) is PetriNet.Transition:
                        T_s.add(vertex)
        subnet, subnet_im, subnet_fm = induced_subnet(petri_net_unmodified, T_s)

        loop_back = petri_utils.add_transition(subnet, str(uuid4()))
        for p in subnet_im:
            petri_utils.add_arc_from_to(loop_back, p, subnet)
        for p in subnet_fm:
            petri_utils.add_arc_from_to(p, loop_back, subnet)

        if __debug__ and SHOW_VISUALIZATIONS:
            view_petri_net(subnet, subnet_im, subnet_fm)

        alignments = []
        for trace in sublog.to_event_log():
            if pool:
                alignment = pool.apply_async(
                    calculate_alignment_a_star,
                    args=[trace, subnet, subnet_im, subnet_fm],
                    kwds={
                        "parameters": {
                            "ret_tuple_as_trans_desc": True,
                            # high cost for all log moves and zero cost for all model moves
                            # s.t. log moves are avoided if possible
                            PARAM_TRACE_COST_FUNCTION: [100] * len(trace),
                            PARAM_MODEL_COST_FUNCTION: {
                                t: 0 for t in subnet.transitions
                            },
                        }
                    },
                )
            else:
                alignment = calculate_alignment(
                    trace,
                    subnet,
                    subnet_im,
                    subnet_fm,
                    parameters={
                        "ret_tuple_as_trans_desc": True,
                        # high cost for all log moves and zero cost for all model moves
                        # s.t. log moves are avoided if possible
                        PARAM_TRACE_COST_FUNCTION: [100] * len(trace),
                        PARAM_MODEL_COST_FUNCTION: {t: 0 for t in subnet.transitions},
                    },
                    variant=variants_calculate_alignments.state_equation_a_star,
                )

            alignments.append(alignment)

        if pool:
            alignments = [async_result.get() for async_result in alignments]

        no_log_moves_in_alignments = True
        for alignment in alignments:
            log_moves = [move for move in alignment["alignment"] if is_log_move(move)]
            if len(log_moves) > 0:
                no_log_moves_in_alignments = False

        if no_log_moves_in_alignments:
            loop_back = petri_utils.add_transition(petri_net, str(uuid4()))
            for p in subnet_im:
                p = {place for place in petri_net.places if place.name == p.name}.pop()
                petri_utils.add_arc_from_to(loop_back, p, petri_net)
            for p in subnet_fm:
                p = {place for place in petri_net.places if place.name == p.name}.pop()
                petri_utils.add_arc_from_to(p, loop_back, petri_net)

    if __debug__ and SHOW_VISUALIZATIONS:
        view_petri_net(petri_net)


def insert_submodel(
    petri_net: PetriNet,
    submodel: PetriNet,
    submodel_start: Optional[PetriNet.Transition],
    submodel_end: Optional[PetriNet.Transition],
    location: Set[PetriNet.Place],
):
    # rename submodel places
    used_p_names = {p.name for p in petri_net.places}
    place_number = len(petri_net.places)

    for p in submodel.places:
        while p.name in used_p_names:
            p.name = f"p_{place_number}"
            place_number += 1

    # add submodel as disconnected component
    petri_net = petri_utils.merge(petri_net, [submodel])

    # connect start and end of submodel to location
    for place in location:
        if submodel_start:
            petri_utils.add_arc_from_to(place, submodel_start, petri_net)
        if submodel_end:
            petri_utils.add_arc_from_to(submodel_end, place, petri_net)


def repair_model_at_location(petri_net: PetriNet, sublog: Sublog):
    sublog.log = add_artificial_start_and_end_activity_to_Log(sublog.to_event_log())
    subnet, subnet_im, subnet_fm = discover_petri_net_inductive(sublog.log)

    # make artifical start/end transition to silent transition
    subnet_start = get_transitions_by_label(
        subnet, ARTIFICIAL_START_ACTIVITY_NAME
    ).pop()
    subnet_start.label = None
    subnet_end = get_transitions_by_label(subnet, ARTIFICIAL_END_ACTIVITY_NAME).pop()
    subnet_end.label = None

    # remove place before/after start/end transition
    for place in petri_utils.pre_set(subnet_start):
        petri_utils.remove_place(subnet, place)
    for place in petri_utils.post_set(subnet_end):
        petri_utils.remove_place(subnet, place)

    insert_submodel(petri_net, subnet, subnet_start, subnet_end, sublog.location)


def get_subtraces(
    alignment: AlignmentResult, petri_net: PetriNet, initial_marking: Marking
):
    """
    Returns the subtraces found in an alignment that consist of only log moves
    """
    # -----
    subtraces: Set[Subtrace] = set()

    current_marking = initial_marking
    latest_places: FrozenSet[PetriNet.Place] = frozenset(initial_marking.keys())
    subtrace: Subtrace = None
    for move in alignment["alignment"]:
        if is_log_move(move):
            if subtrace is None:
                subtrace = Subtrace(
                    (move[1][0],), frozenset(current_marking), latest_places
                )
            else:
                subtrace.trace += (move[1][0],)

        else:
            if subtrace:
                subtraces.add(subtrace)
                subtrace = None

            transition_fired = petri_utils.get_transition_by_name(petri_net, move[0][1])
            latest_places = frozenset(petri_utils.post_set(transition_fired))

        current_marking = remove_zeros_from_marking(
            replay_move(petri_net, current_marking, move)
        )

    # Check if alignment ended with ongoing subtrace
    if subtrace:
        subtraces.add(subtrace)

    return subtraces


def get_skipped_transitions(alignment: AlignmentResult, petri_net: PetriNet):
    skipped_trans: Set[PetriNet.Transition] = set()
    for move in alignment["alignment"]:
        if is_model_move_on_visible_activity(move):
            skipped_trans.add(petri_utils.get_transition_by_name(petri_net, move[0][1]))
    return skipped_trans


def align_subtraces(
    subtraces: Set[Subtrace],
    similiarty_threshold=0.5,
):
    """
    Implementation of algorithm 5.
    Group subtraces into sets based on their shared activities ignoring ordering.
    """

    def _are_similar(
        trace1: Tuple[str], trace2: Tuple[str], similiarty_threshold: float
    ):
        intersection: Set[str] = set(trace1).intersection(set(trace2))
        return (
            len(intersection) / len(trace1) >= similiarty_threshold
            and len(intersection) / len(trace2) >= similiarty_threshold
        )

    n_max = max([*map(lambda t: len(t), subtraces), 0])
    for n in range(n_max, 0, -1):
        for subtrace in [sub for sub in subtraces if len(sub) == n]:
            candidates = []
            for partition in partitions(subtrace.trace):
                partition = [tuple(p) for p in partition]
                if len(partition) == 1:
                    candidates.append(((), *partition, ()))
                elif len(partition) == 3:
                    candidates.append(partition)
                elif len(partition) == 2:
                    candidates.append((*partition, ()))
                    candidates.append(((), *partition))

            # sort for getting maximal length b1 with original subtrace and b1 being dissimilar
            for b0, b1, b2 in sorted(
                candidates, key=lambda part: len(part[1]), reverse=True
            ):
                if _are_similar(subtrace.trace, b1, similiarty_threshold):
                    continue
                if b1 in list(map(lambda sub: sub.trace, subtraces)):
                    subtraces.remove(subtrace)
                    if len(b0) > 0:
                        subtraces.add(
                            Subtrace(
                                b0, subtrace.location, subtrace.previous_last_place
                            )
                        )
                    if len(b1) > 0:
                        subtraces.add(
                            Subtrace(
                                b1, subtrace.location, subtrace.previous_last_place
                            )
                        )
                    if len(b2) > 0:
                        subtraces.add(
                            Subtrace(
                                b2, subtrace.location, subtrace.previous_last_place
                            )
                        )
                    break

    # group subtraces into equivalence classes w.r.t. similarity
    res: List[List[Subtrace]] = []
    for subtrace in subtraces:
        eq_class_found = False
        for eq_class in res:
            eq_match = True
            for other_subtrace in eq_class:
                if not _are_similar(
                    subtrace.trace, other_subtrace.trace, similiarty_threshold
                ):
                    eq_match = False
            if eq_match:
                eq_class.append(subtrace)
                eq_class_found = True
                break
        if not eq_class_found:
            res.append([subtrace])
    return {frozenset(eq_class) for eq_class in res}


def group_into_sublogs(subtraces: FrozenSet[Subtrace]):
    """
    Implementation of algorithm 6.
    """

    if len(subtraces) == 1:
        subtrace = list(subtraces)[0]
        return {Sublog(subtraces, subtrace.location)}

    subtraces = set(subtraces)

    res: Set[Sublog] = set()

    while len(subtraces) > 0:
        subtraces_per_place: Dict[PetriNet.Place, Set[Subtrace]] = dict()
        for subtrace in subtraces:
            for place in subtrace.location:
                if place not in subtraces_per_place:
                    subtraces_per_place[place] = set()
                subtraces_per_place[place].add(subtrace)

        p, subs_at_p = max(subtraces_per_place.items(), key=lambda item: len(item[1]))

        locations = [sub.location for sub in subs_at_p]
        if len(subs_at_p) > 1:
            new_loc = frozenset.intersection(*locations)
        else:
            new_loc = frozenset(locations[0])

        assert p in new_loc

        res.add(Sublog(frozenset(subs_at_p), new_loc))
        subtraces.difference_update(subs_at_p)
    return res


def group_into_aligned_sublogs(subtraces):
    """
    Implementation of algorithm 7.
    """
    res: Set[Sublog] = set()

    decomposed_traces = align_subtraces(subtraces)
    for eq_class in decomposed_traces:
        res.update(group_into_sublogs(eq_class))
    return res


def pick_relevant_locations(sublogs: Set[Sublog]):
    """
    Implementation of algorithm 8:
    find the place that was most frequently marked directly before the first log
    move of each trace, use this place as the place that covers the sub-location
    """
    res: Set[Sublog] = set()
    for sublog in sublogs:
        last_places = Counter(
            reduce(chain, [subtrace.previous_last_place for subtrace in sublog.log])
        ).most_common()
        most_frequent_count = last_places[0][1]
        most_frequent_last_places = {
            place_count[0]
            for place_count in last_places
            if place_count[1] == most_frequent_count
        }
        if len(set.intersection(most_frequent_last_places, sublog.location)) > 0:
            most_frequent_last_places.intersection_update(sublog.location)
            res.add((Sublog(sublog.log, frozenset(most_frequent_last_places))))
        else:
            res.add(sublog)
    return res


def validate_iteration_preserving_alignment(alignment):
    """
    Validates if an alignment is iteration preserving s.t.:
    1. For any synchronous move (a,t) that is preceded by a sequence (a_1,>>), ..., (a_k,>>) of log moves,
    no log move (a_i,>>) could have matched t, i.e., a /= a_i for all 1 <= i <= k.
    2. A model move is eithera         a   i, t) is eianother model movms or a synchronous move, i.e. l are put
    """
    preceding_log_moves = []
    for move in alignment["alignment"]:
        if is_sync_move(move):
            for log_move in preceding_log_moves:
                if log_move[1][0] == move[1][0]:
                    return False
            preceding_log_moves = []
        elif is_model_move(move):
            if len(preceding_log_moves) > 0:
                return False
            else:
                preceding_log_moves = []
        elif is_log_move(move):
            preceding_log_moves.append(move)
    return True


def make_alignment_iteration_preserving(alignment):
    while not validate_iteration_preserving_alignment(alignment):
        alignment_moves = alignment["alignment"]
        preceding_log_moves = []
        for i, move in enumerate(alignment_moves):
            if is_sync_move(move):
                for j, log_move in enumerate(preceding_log_moves):
                    if log_move[1][0] == move[1][0]:
                        index_of_log_move = i - (len(preceding_log_moves) - j)
                        alignment_moves[i], alignment_moves[index_of_log_move] = (
                            alignment_moves[index_of_log_move],
                            alignment_moves[i],
                        )
                        preceding_log_moves = preceding_log_moves[j + 1 :]
                        preceding_log_moves.append(alignment_moves[i])
                        break
                else:
                    preceding_log_moves = []
            elif is_model_move(move):
                if len(preceding_log_moves) > 0:
                    alignment_moves = (
                        alignment_moves[: i - len(preceding_log_moves)]
                        + [move]
                        + preceding_log_moves
                        + alignment_moves[i + 1 :]
                    )
                else:
                    preceding_log_moves = []
            elif is_log_move(move):
                preceding_log_moves.append(move)

        alignment["alignment"] = alignment_moves
    return alignment


if __name__ == "__main__":
    # pt1: process_tree_utils = pt_parse("->('a', +('c', *('b', 'e')), 'd')")
    # tree_vis.view(tree_vis.apply(pt1, parameters={"format": "svg"}))

    # net, im, fm = pt_to_petri_net_cortado(pt1)
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
    # t_d1 = PetriNet.Transition("d2", "d")
    t_e = PetriNet.Transition("e1", "e")

    net = PetriNet("net1", {p1, p2, p3, p4, p5, p6}, {t_a, t_b, t_c, t_d, t_e})
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

    # petri_utils.add_arc_from_to(p1, t_d1, net)
    # petri_utils.add_arc_from_to(t_d1, p6, net)

    im = Marking({p1: 1})
    fm = Marking({p6: 1})

    if __debug__ and SHOW_VISUALIZATIONS:
        view_petri_net(net, im, fm)

    log = EventLog()
    a = Event({"concept:name": "a"})
    b = Event({"concept:name": "b"})
    c = Event({"concept:name": "c"})
    d = Event({"concept:name": "d"})
    e = Event({"concept:name": "e"})
    f = Event({"concept:name": "f"})

    t1 = Trace([a, c, f, c, e, d])
    t2 = Trace([a, b, c, c, f, e, d])
    t3 = Trace([f, e, a, b, c, f, e, d])
    t4 = Trace([a, b, c, d, b, c, b, c, d])
    log.append(t1)
    log.append(t2)
    log.append(t3)
    log.append(t4)

    repair_petri_net_with_log(net, im, fm, log)

    if __debug__ and SHOW_VISUALIZATIONS:
        view_petri_net(net, im, fm)
