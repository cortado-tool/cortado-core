import copy
import sys
from collections import defaultdict
from typing import Set

import numpy as np
import pm4py
from pm4py.algo.conformance.alignments.petri_net.algorithm import (
    apply as calculate_alignments,
    Parameters,
)
from pm4py.algo.conformance.alignments.petri_net.algorithm import (
    variants as variants_calculate_alignments,
)
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator
from pm4py.algo.simulation.playout.petri_net import algorithm as simulator
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.semantics import PetriNetSemantics
from pm4py.objects.petri_net.utils import align_utils
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.util.variants_util import variant_to_trace

from cortado_core.utils.alignment_utils import (
    is_sync_move,
    is_log_move,
    alignment_step_represents_no_deviation,
)

LPM_REDO_MARKER = "REDO_LMP"


def calculate_metrics(
    lpm, log: EventLog, include_skip_metrics=True, is_place_net_algorithm=False
):
    if isinstance(lpm, tuple):
        initial_net, i_im, i_fm = lpm
    else:
        initial_net, i_im, i_fm = pt_converter.apply(lpm)

    labels = __get_labels_in_model(initial_net)

    if include_skip_metrics:
        skip_precision = __calculate_skip_metric(
            initial_net,
            i_im,
            i_fm,
            isinstance(lpm, tuple),
            log,
            labels,
            is_place_net_algorithm=is_place_net_algorithm,
        )
    else:
        skip_precision = 0

    labels = __get_labels_in_model(initial_net, remove_dots=True)
    log_length = len(log)
    projected_log = __project_log_on_lpm_activities(labels, log)
    variants_with_count = __get_variants_with_count(projected_log)

    if not is_place_net_algorithm:
        initial_net = __replace_ef_skip_with_tau(initial_net)
        net, im = __preprocess_lpm(initial_net, i_im, i_fm)
        alignments = __calculate_alignments(net, im, variants_with_count)
        discovered_fragments = __get_discovered_fragments_from_alignments(alignments)
        mean_rng, min_rng, max_rng = __calculate_range(alignments)
    else:
        alignments = __calculate_alignments(initial_net, Marking(), variants_with_count)
        discovered_fragments = __get_discovered_fragments_for_place_net_models(
            alignments, initial_net
        )
        mean_rng, min_rng, max_rng = __calculate_range_place_net_algorithm(
            alignments, initial_net
        )

    support_tax = __calculate_support_tax(discovered_fragments)
    support_trans = __calculate_support_transaction(discovered_fragments, log_length)
    support_occ = __calculate_support_occ(discovered_fragments, log_length)
    confidence = __calculate_confidence(discovered_fragments, labels)
    precision = __calculate_precision(discovered_fragments, initial_net, i_im, i_fm)
    coverage = __calculate_coverage(log, projected_log)
    simplicity = __calculate_simplicity(initial_net)

    n_transitions = len([t for t in initial_net.transitions if t.label is not None])

    return (
        support_tax,
        support_trans,
        support_occ,
        confidence,
        precision,
        coverage,
        simplicity,
        n_transitions,
        skip_precision,
        mean_rng,
        min_rng,
        max_rng,
    )


def __replace_ef_skip_with_tau(initial_net):
    for transition in initial_net.transitions:
        if transition.label == "...":
            transition.label = None

    return initial_net


def __calculate_support_tax(discovered_fragments):
    absolute_support = sum(
        [
            __calculate_support_occ_in_trace(fragment_counts) * count
            for _, (count, fragment_counts) in discovered_fragments.items()
        ]
    )

    return absolute_support / (absolute_support + 1)


def __calculate_support_transaction(discovered_fragments, log_length):
    absolute_support = sum(
        [
            __calculate_support_transaction_in_trace(fragment_counts) * count
            for _, (count, fragment_counts) in discovered_fragments.items()
        ]
    )

    return absolute_support / log_length


def __calculate_support_transaction_in_trace(fragment_counts):
    if len(fragment_counts) == 0:
        return 0

    return 1


def __calculate_support_occ(discovered_fragments, log_length):
    absolute_support = sum(
        [
            __calculate_support_occ_in_trace(fragment_counts) * count
            for _, (count, fragment_counts) in discovered_fragments.items()
        ]
    )

    return min(absolute_support / log_length, 1)


def __calculate_support_occ_in_trace(fragment_counts):
    return sum(fragment_counts.values())


def __calculate_confidence(discovered_fragments, labels: Set[str]) -> float:
    return len(labels) / sum(
        [
            __calculate_confidence_for_label(discovered_fragments, label)
            for label in labels
        ]
    )


def __calculate_confidence_for_label(discovered_fragments, label: str) -> float:
    n_label_in_log = 0
    n_label_in_fragment = 0
    eps = 0.001

    for trace, (count, fragment_counts) in discovered_fragments.items():
        for e in trace:
            if e == label:
                n_label_in_log += count

        for fragment, fragment_count in fragment_counts.items():
            for e in fragment:
                if e == label:
                    n_label_in_fragment += fragment_count * count

    if n_label_in_log == 0 or n_label_in_fragment == 0:
        return 1 / eps

    return 1 / (n_label_in_fragment / n_label_in_log)


def __calculate_language_fit(
    discovered_fragments, max_trace_length: int, net, im, fm
) -> float:
    model_language = simulator.apply(
        net,
        im,
        fm,
        variant=simulator.Variants.EXTENSIVE,
        parameters={
            simulator.Variants.EXTENSIVE.value.Parameters.MAX_TRACE_LENGTH: max_trace_length
        },
    )

    discovered_fragments_flat = set()
    for _, (_, fragment_counts) in discovered_fragments.items():
        discovered_fragments_flat = discovered_fragments_flat.union(
            set(fragment_counts.keys())
        )

    n_replayable_traces = 0
    for trace in model_language:
        trace_as_tuple = tuple([e["concept:name"] for e in trace])
        if trace_as_tuple in discovered_fragments_flat:
            n_replayable_traces += 1
            break

    return n_replayable_traces / len(model_language)


def __calculate_precision(discovered_fragments, net, im, fm):
    discovered_fragments_flat = set()
    for _, (_, fragment_counts) in discovered_fragments.items():
        discovered_fragments_flat = discovered_fragments_flat.union(
            set(fragment_counts.keys())
        )

    evaluation_log = EventLog()

    for discovered_fragment in discovered_fragments_flat:
        trace = Trace()

        for event in discovered_fragment:
            e = Event()
            e["concept:name"] = event
            trace.append(e)

        evaluation_log.append(trace)

    return pm4py.precision_token_based_replay(evaluation_log, net, im, fm)


def __calculate_coverage(log: EventLog, projected_log: EventLog):
    log_length = __calculate_number_of_events(log)
    projected_log_length = __calculate_number_of_events(projected_log)

    return projected_log_length / log_length


def __calculate_number_of_events(log: EventLog):
    return sum([len(trace) for trace in log])


def __calculate_simplicity(net):
    return simplicity_evaluator.apply(net)


def __calculate_alignments(net, im, variants_with_count):
    result = []
    parameters = __get_parameters_with_model_cost_function_for_net(net)

    for variant, count, orig_positions in variants_with_count:
        trace = variant_to_trace(variant)
        alignment = calculate_alignments(
            trace,
            net,
            im,
            im,
            parameters=parameters,
            variant=variants_calculate_alignments.dijkstra_no_heuristics,
        )
        result.append((variant, count, orig_positions, alignment))

    return result


def __preprocess_lpm(net, im, fm):
    net, im, fm = copy.deepcopy((net, im, fm))
    new_transition = PetriNet.Transition(LPM_REDO_MARKER)
    net.transitions.add(new_transition)
    for final_place in fm:
        petri_utils.add_arc_from_to(final_place, new_transition, net)

    for initial_place in im:
        petri_utils.add_arc_from_to(new_transition, initial_place, net)

    return net, im


def __get_discovered_fragments_from_alignments(alignments):
    result = {}
    for variant, count, _, alignment in alignments:
        discovered_fragments = defaultdict(int)
        discovered_fragment = []
        for trans_tuple, move in alignment["alignment"]:
            if trans_tuple == (align_utils.SKIP, LPM_REDO_MARKER):
                discovered_fragments[tuple(discovered_fragment)] += 1
                discovered_fragment = []
            elif is_sync_move((trans_tuple, move)):
                discovered_fragment.append(move[0])

        result[variant] = (count, discovered_fragments)

    return result


def __get_discovered_fragments_for_place_net_models(alignments, net):
    result = {}
    for variant, count, _, alignment in alignments:
        discovered_fragments = defaultdict(int)
        discovered_fragment = []
        marking = Marking()
        for move in alignment["alignment"]:
            if is_sync_move(move):
                discovered_fragment.append(move[1][0])

            marking = replay_move(net, marking, move)
            if len(marking) == 0 and len(discovered_fragment) > 0:
                discovered_fragments[tuple(discovered_fragment)] += 1
                discovered_fragment = []

        result[variant] = (count, discovered_fragments)

    return result


def __calculate_range(alignments):
    ranges = []
    for _, _, orig_positions, alignment in alignments:
        start_idx = -1
        end_idx = -1
        current_idx = 0
        for trans_tuple, move in alignment["alignment"]:
            if trans_tuple == (align_utils.SKIP, LPM_REDO_MARKER):
                for orig_position in orig_positions:
                    ranges.append(orig_position[end_idx] - orig_position[start_idx])
                start_idx = -1
            elif is_sync_move((trans_tuple, move)):
                if start_idx == -1:
                    start_idx = current_idx
                current_idx += 1
                end_idx = current_idx - 1
            elif is_log_move((trans_tuple, move)):
                current_idx += 1

    return np.mean(ranges), np.min(ranges), np.max(ranges)


def __calculate_range_place_net_algorithm(alignments, net):
    ranges = []
    for _, _, orig_positions, alignment in alignments:
        start_idx = -1
        end_idx = -1
        current_idx = 0
        marking = Marking()
        saw_sync_move = False
        for move in alignment["alignment"]:
            if is_sync_move(move):
                if start_idx == -1:
                    start_idx = current_idx
                current_idx += 1
                end_idx = current_idx - 1
                saw_sync_move = True
            elif is_log_move(move):
                current_idx += 1

            marking = replay_move(net, marking, move)
            if len(marking) == 0 and saw_sync_move:
                for orig_position in orig_positions:
                    ranges.append(orig_position[end_idx] - orig_position[start_idx])
                start_idx = -1
                saw_sync_move = False

    if len(ranges) == 0:
        ranges = [0]

    return np.mean(ranges), np.min(ranges), np.max(ranges)


def __get_parameters_with_model_cost_function_for_net(net):
    model_cost_function = dict()
    sync_cost_function = dict()
    for t in net.transitions:
        if t.label is not None:
            model_cost_function[t] = sys.maxsize / 1000
            sync_cost_function[t] = align_utils.STD_SYNC_COST
        else:
            model_cost_function[t] = align_utils.STD_TAU_COST

    return {
        Parameters.PARAM_MODEL_COST_FUNCTION: model_cost_function,
        Parameters.PARAM_SYNC_COST_FUNCTION: sync_cost_function,
        "ret_tuple_as_trans_desc": True,
    }


def __get_variants_with_count(log: EventLog):
    variants = pm4py.get_variants_as_tuples(log)

    return [
        (v, len(traces), [__get_positions(t) for t in traces])
        for v, traces in variants.items()
    ]


def __get_positions(trace):
    return [event["orig_idx"] for event in trace]


def __get_labels_in_model(net: PetriNet, remove_dots: bool = False) -> Set[str]:
    labels = set()

    for t in net.transitions:
        if t.label is not None and t.label != "...":
            labels.add(t.label)

    return labels


def __project_log_on_lpm_activities(labels: Set[str], log: EventLog) -> EventLog:
    new_traces = []

    for trace in log:
        new_trace = __project_trace(trace, labels)
        new_traces.append(new_trace)

    return EventLog(new_traces)


def __project_trace(trace: Trace, labels: Set[str]):
    new_trace = []
    for idx, event in enumerate(trace):
        if event["concept:name"] in labels:
            event["orig_idx"] = idx
            new_trace.append(event)

    return Trace(new_trace)


def __calculate_skip_metric(
    net,
    im,
    fm,
    add_artificial_skip: bool,
    log: EventLog,
    labels: set[str],
    is_place_net_algorithm: bool = False,
):
    if add_artificial_skip:
        net, im, fm = __get_fallback_skip_petri_net(net, im, fm)

    if not is_place_net_algorithm:
        net, im = __preprocess_lpm(net, im, fm)
    log_with_skips = __project_log_on_lpm_activities_with_skips(labels, log)
    variants = __get_variants_with_count(log_with_skips)
    skip_precision = 0
    n = 0

    for variant, count, orig_positions, alignment in __calculate_alignments(
        net, im, variants
    ):
        res, should_use = get_skip_statistics_for_alignment(alignment, net, im)
        if should_use:
            skip_precision += res * count
            n += count

    return skip_precision / n


def get_skip_statistics_for_alignment(alignment, net, im):
    skip_transitions = [t for t in net.transitions if t.label == "..."]
    if len(skip_transitions) == 0:
        return 1, True

    n_skip_enabled_but_not_used = 0
    n_sync_moves = 0
    has_sync_move_on_activity = False
    skip_transition = skip_transitions[0]
    marking = im

    for move in alignment["alignment"]:
        if is_log_move(move):
            continue
        if alignment_step_represents_no_deviation(move) and move[1][1] is None:
            marking = replay_move(net, marking, move)
            continue

        n_sync_moves += 1
        if is_skip_enabled(net, skip_transition, marking):
            if move[1][0] != "...":
                n_skip_enabled_but_not_used += 1

        if move[1][0] != "...":
            has_sync_move_on_activity = True
        marking = replay_move(net, marking, move)

    if n_sync_moves == 0 or not has_sync_move_on_activity:
        return 1, False

    res = 1 - (n_skip_enabled_but_not_used / n_sync_moves)

    return res, True


def __move_is_on_skip(move):
    return move[1][0] == "..."


def is_skip_enabled(net, skip_transition, marking, n=5):
    if PetriNetSemantics.is_enabled(net, skip_transition, marking):
        return True

    # mechanism to avoid recursion running forever if we can execute a loop with tau transitions
    if n <= 0:
        return False

    n -= 1
    enabled_tau_transitions = [
        t
        for t in net.transitions
        if t.label is None and PetriNetSemantics.is_enabled(net, t, marking)
    ]

    for tau_transition in enabled_tau_transitions:
        new_marking = PetriNetSemantics.fire(net, tau_transition, marking)
        if is_skip_enabled(net, skip_transition, new_marking, n):
            return True

    return False


def replay_move(net, marking, move):
    if is_log_move(move):
        return marking

    transition = [
        t
        for t in net.transitions
        if t.name == move[0][1] and PetriNetSemantics.is_enabled(net, t, marking)
    ][0]

    new_marking = PetriNetSemantics.fire(net, transition, marking)
    return __remove_zero_entries_from_marking(new_marking)


def __project_log_on_lpm_activities_with_skips(
    labels: set[str], log: EventLog
) -> EventLog:
    new_traces = []

    for trace in log:
        new_trace = __project_trace_with_skips(trace, labels)
        new_traces.append(new_trace)

    return EventLog(new_traces)


def __project_trace_with_skips(trace: Trace, labels: set[str]):
    new_trace = []

    for idx, event in enumerate(trace):
        if event["concept:name"] in labels:
            event["orig_idx"] = idx
            new_trace.append(event)
            continue

        if len(new_trace) == 0 or new_trace[-1]["concept:name"] == "...":
            continue

        skip_event = Event()
        skip_event["concept:name"] = "..."
        skip_event["orig_idx"] = -1
        new_trace.append(skip_event)

    if len(new_trace) > 0 and new_trace[-1]["concept:name"] == "...":
        new_trace = new_trace[:-1]

    return new_trace


def __project_trace_with_skips_partial_order_based(trace, labels: set[str]):
    new_trace = []
    skipped_events = set()

    for idx, event in enumerate(trace):
        if event["concept:name"] in labels:
            for skipped_event in skipped_events:
                if skipped_event["time:timestamp"] < event["start_timestamp"]:
                    skip_event = Event()
                    skip_event["concept:name"] = "..."
                    skip_event["orig_idx"] = -1
                    new_trace.append(skip_event)
                    break
            event["orig_idx"] = idx
            new_trace.append(event)
            skipped_events = set()
        else:
            if len(new_trace) == 0:
                continue

            if event["start_timestamp"] > new_trace[-1]["time:timestamp"]:
                skipped_events.add(event)

    return Trace(new_trace)


def __get_fallback_skip_petri_net(net, im, fm):
    """
    Adds an unconnected new transition labeled with ...
    Parameters
    ----------
    net
    im
    fm

    Returns
    -------

    """
    net, im, fm = copy.deepcopy((net, im, fm))
    petri_utils.add_transition(net, "skip_transition", "...")

    return net, im, fm


def __remove_zero_entries_from_marking(marking):
    zero_removed_marking = Marking()

    for p, w in marking.items():
        if w != 0:
            zero_removed_marking[p] = w

    return zero_removed_marking
