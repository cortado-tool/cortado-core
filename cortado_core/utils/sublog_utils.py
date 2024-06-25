import multiprocessing
from typing import Optional

from pm4py import ProcessTree, Marking
from pm4py.algo.conformance.alignments.petri_net.algorithm import (
    apply as calculate_alignments,
)
from pm4py.algo.conformance.alignments.petri_net.algorithm import (
    variants as variants_calculate_alignments,
)
from pm4py.objects.log.obj import Trace, EventLog, Event
from pm4py.objects.petri_net.semantics import PetriNetSemantics
from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST
from pm4py.util.typing import AlignmentResult

from cortado_core.models.infix_type import InfixType
from cortado_core.process_tree_utils.miscellaneous import is_leaf_node, is_subtree
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import (
    apply as pt_to_petri_net,
)
from cortado_core.utils.alignment_utils import (
    alignment_contains_deviation,
    calculate_infix_postfix_prefix_alignment,
    is_log_move,
)
from cortado_core.utils.parallel_alignments import calculate_alignments_parallel
from cortado_core.utils.trace import TypedTrace, combine_event_logs


def calculate_sublog_for_lca(
    pt: ProcessTree,
    log: list[TypedTrace],
    lca: ProcessTree,
    alignment,
    deviation_i,
    trace_to_add,
    infix_type: InfixType,
    pool,
) -> EventLog:
    """
    Calculates the sublog given a process tree with its lca.
    Parameters
    ----------
    pt: process tree that will be rediscovered
    log: already added traces
    lca: lca that need to be rediscovered
    alignment: alignment of the added trace/fragment. Full alignments for traces, infix/prefix/postfix alignments otherwise
    deviation_i: index i in the alignment that marks the deviation
    trace_to_add: trace/fragment that is added
    infix_type: type of the trace/fragment that is added
    pool

    Returns
    -------

    """
    not_infix_log, infix_traces = __split_log_by_infix_type(log)
    sublogs = __calculate_sub_log_for_each_node_regular_traces(
        pt, not_infix_log, pool=pool
    )
    # adding the fitting prefix is important to ensure that we do not add deviations in the alignment that are on
    # the left-hand side of the current deviation
    sublogs = __add_fitting_alignment_prefix_to_sublogs(
        alignment, deviation_i, infix_type, sublogs
    )

    sublog = sublogs[lca.id] if lca.id in sublogs else EventLog()
    sublog.append(trace_to_add)

    return combine_event_logs(
        sublog, calculate_sublog_for_infix_prefix_postfix_traces(infix_traces, pt, lca)
    )


def calculate_sublog_for_infix_prefix_postfix_traces(
    infixes: list[TypedTrace], process_tree: ProcessTree, lca: ProcessTree
):
    sublog = EventLog()
    for infix in infixes:
        sublog = combine_event_logs(
            sublog,
            generate_infix_sublog(infix.trace, infix.infix_type, process_tree, lca),
        )

    return sublog


def generate_infix_sublog(
    infix: Trace, infix_type: InfixType, process_tree: ProcessTree, lca: ProcessTree
) -> EventLog:
    """
    Calculates the sublog for the lca of a fitting infix/prefix/postfix
    Parameters
    ----------
    infix
    infix_type
    process_tree
    lca

    Returns
    -------

    """
    alignment = calculate_infix_postfix_prefix_alignment(
        infix, process_tree, infix_type
    )
    assert alignment["cost"] < STD_MODEL_LOG_MOVE_COST

    alignment = generate_full_alignment_based_on_infix_alignment(infix_type, alignment)
    sublogs = dict()
    sublogs = add_alignment_to_sublogs(alignment, sublogs, allow_deviations=True)

    return sublogs[lca.id] if lca.id in sublogs else EventLog()


def generate_full_alignment_based_on_infix_alignment(
    infix_type: InfixType, infix_alignment, only_prefix: bool = False
):
    full_alignment = infix_alignment
    alignment_prefix = None
    alignment_postfix = None
    net, im, fm = infix_alignment["net"]
    if infix_type == InfixType.PROPER_INFIX or infix_type == InfixType.POSTFIX:
        alignment_prefix = calculate_alignments(
            Trace(),
            net,
            im,
            infix_alignment["start_marking"],
            parameters={"ret_tuple_as_trans_desc": True},
            variant=variants_calculate_alignments.state_equation_a_star,
        )
        full_alignment = combine_alignments(alignment_prefix, full_alignment)

    if not only_prefix and (
        infix_type == InfixType.PROPER_INFIX or infix_type == InfixType.PREFIX
    ):
        end_marking_of_alignment = __get_end_marking_of_alignment(
            infix_alignment, infix_type
        )
        alignment_postfix = calculate_alignments(
            Trace(),
            net,
            end_marking_of_alignment,
            fm,
            parameters={"ret_tuple_as_trans_desc": True},
            variant=variants_calculate_alignments.state_equation_a_star,
        )
        full_alignment = combine_alignments(full_alignment, alignment_postfix)

    full_alignment["prefix_length"] = (
        len(alignment_prefix["alignment"]) if alignment_prefix is not None else 0
    )
    full_alignment["postfix_length"] = (
        len(alignment_postfix["alignment"]) if alignment_postfix is not None else 0
    )

    return full_alignment


def combine_alignments(a1, a2):
    copy_keys = {
        "alignment",
        "cost",
        "visited_states",
        "queued_states",
        "traversed_arcs",
        "lp_solved",
    }
    new_alignment = dict()

    for k, v in a1.items():
        if k in copy_keys and k in a2:
            new_alignment[k] = v + a2[k]

    return new_alignment


def __get_end_marking_of_alignment(infix_alignment, infix_type):
    net, im, fm = infix_alignment["net"]
    marking = im if infix_type == InfixType.PREFIX else infix_alignment["start_marking"]

    for move in infix_alignment["alignment"]:
        marking = replay_move(net, marking, move)

    return remove_zeros_from_marking(marking)


def replay_move(net, marking, move):
    if is_log_move(move):
        return marking

    transition = None
    for t in net.transitions:
        if t.name != move[0][1]:
            continue
        elif isinstance(t.name[0], ProcessTree) and not t.name[0] is move[0][1][0]:
            continue
        elif (
            hasattr(t.name[0], "id")
            and hasattr(move[0][1][0], "id")
            and t.name[0].id != move[0][1][0].id
        ):
            continue
        else:
            transition = t
            break

    new_marking = PetriNetSemantics.fire(net, transition, marking)
    return new_marking


def remove_zeros_from_marking(marking):
    zero_removed_marking = Marking()

    for p, w in marking.items():
        if w != 0:
            zero_removed_marking[p] = w

    return zero_removed_marking


def add_alignment_to_sublogs(alignment, sublogs, allow_deviations=False):
    if not allow_deviations:
        assert not alignment_contains_deviation(alignment)
    currently_active_pt_nodes = {}

    for step in alignment["alignment"]:
        # executed transition always corresponds to a node in the process tree
        current_pt = step[0][1][0]
        if (current_pt, current_pt.id) in currently_active_pt_nodes:
            if current_pt.id not in sublogs:
                sublogs[current_pt.id] = EventLog()

            sublogs[current_pt.id].append(
                currently_active_pt_nodes[(current_pt, current_pt.id)]
            )
            # every pt node occurs at least twice in an alignment, i.e., start and end. Hence when we observe a pt
            # node for the second time, we know it is closed
            assert step[0][1][1] == "closed"
            del currently_active_pt_nodes[(current_pt, current_pt.id)]
        elif not is_leaf_node(current_pt):
            currently_active_pt_nodes[(current_pt, current_pt.id)] = Trace()

        if is_leaf_node(current_pt):
            activity_name = step[1][1]
            if activity_name:
                for active_node, active_node_obj_id in currently_active_pt_nodes:
                    if is_subtree(active_node, current_pt):
                        event = Event()
                        event["concept:name"] = activity_name
                        currently_active_pt_nodes[(active_node, active_node.id)].append(
                            event
                        )

    return sublogs


def __split_log_by_infix_type(
    log: list[TypedTrace],
) -> tuple[EventLog, list[TypedTrace]]:
    """
    Splits the traces/fragments in the log into two logs/lists - one for full traces and one for infixes/postfixes/prefixes.
    Parameters
    ----------
    log

    Returns
    -------

    """
    not_infix_log = EventLog()
    infix_traces = []

    for trace in log:
        if trace.infix_type == InfixType.NOT_AN_INFIX:
            not_infix_log.append(trace.trace)
        else:
            infix_traces.append(trace)

    return not_infix_log, infix_traces


def __calculate_sub_log_for_each_node_regular_traces(
    pt: ProcessTree, log: EventLog, pool: Optional[multiprocessing.pool.Pool]
) -> dict[int, EventLog]:
    """
    Calculates the sublog for each full, already added trace by first computing the alignment and then adding the relevant
    parts to the sublog of the lca.
    Parameters
    ----------
    pt
    log
    pool

    Returns
    -------

    """
    sublogs: dict[int, EventLog] = {}
    # assumption: log is replayable on process tree without deviations
    net, im, fm = pt_to_petri_net(pt)
    if pool is not None:
        alignments = calculate_alignments_parallel(
            log, net, im, fm, parameters={"ret_tuple_as_trans_desc": True}, pool=pool
        )
    else:
        alignments = calculate_alignments(
            log,
            net,
            im,
            fm,
            parameters={
                "ret_tuple_as_trans_desc": True,
                "show_progress_bar": False,
            },
            variant=variants_calculate_alignments.state_equation_a_star,
        )
    for alignment in alignments:
        sublogs = add_alignment_to_sublogs(alignment, sublogs)

    return sublogs


def __add_fitting_alignment_prefix_to_sublogs(
    alignment: AlignmentResult,
    deviation_i: int,
    infix_type: InfixType,
    sublogs: dict[int, EventLog],
) -> dict[int, EventLog]:
    """
    Adds the fitting prefix of an alignment, i.e. the part in front of the deviation, to the sublog. This is relevant
    in case of loops, because there might be complete fitting executions of the lca in the prefix that we want to ensure
    to stay in the language of the rediscovered model.
    Parameters
    ----------
    alignment
    deviation_i
    infix_type
    sublogs

    Returns
    -------

    """
    fitting_alignment_prefix = __cut_alignment_to_fitting_prefix(alignment, deviation_i)

    # full trace alignment prefixes can be added directly
    if infix_type == InfixType.NOT_AN_INFIX:
        return add_alignment_to_sublogs(fitting_alignment_prefix, sublogs)

    # for postfixes and infixes, we first need to enrich the infix-/postfix-alignment with the model part starting
    # from the initial marking
    # Example with model = lca: Model ->(a,b,c,d,e), Infix <c,d,f>
    # Infix-alignment: [(c,c), (d,d), (f, >>)] (f is the deviation here)
    # fitting_alignment_prefix after the call: [(>>,a), (>>,b), (c,c), (d,d)], s.t. <a,b,c,d> is added to the sublog
    fitting_alignment_prefix = generate_full_alignment_based_on_infix_alignment(
        infix_type, fitting_alignment_prefix, only_prefix=True
    )

    sublogs = add_alignment_to_sublogs(
        fitting_alignment_prefix, sublogs, allow_deviations=True
    )

    return sublogs


def __cut_alignment_to_fitting_prefix(
    alignment: AlignmentResult, deviation_i: int
) -> AlignmentResult:
    new_alignment = {"cost": 0, "alignment": alignment["alignment"][:deviation_i]}

    for key in alignment:
        if key in {"start_marking", "net"}:
            new_alignment[key] = alignment[key]

    return new_alignment
