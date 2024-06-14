import logging
import multiprocessing.pool
import multiprocessing.pool
from typing import List, Tuple, Optional, Union

import pm4py.visualization.process_tree.visualizer as tree_vis
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.log.obj import EventLog, Event, Trace
from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.util.typing import AlignmentResult

from cortado_core.models.infix_type import InfixType
from cortado_core.process_tree_utils.miscellaneous import (
    get_number_leaves,
    get_height,
    get_number_silent_leaves,
    get_number_nodes,
    is_leaf_node,
    get_index_of_pt_in_children_list,
)
from cortado_core.process_tree_utils.reduction import (
    apply_reduction_rules,
    reduce_loops_with_more_than_two_children,
)
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import (
    apply as pt_to_petri_net,
)
from cortado_core.utils.alignment_utils import (
    is_log_move,
    alignment_step_represents_no_deviation,
    is_sync_move,
    get_first_deviation,
    calculate_alignment_typed_trace,
)
from cortado_core.utils.deviation_solvers import (
    DeviationType,
    get_deviation_solver,
    Deviation,
)
from cortado_core.utils.start_and_end_activities import (
    add_artificial_start_and_end_to_pt,
    remove_artificial_start_and_end_activity_leaves_from_pt,
    add_artificial_start_end_activity_to_typed_trace,
    add_artificial_start_end_activity_to_typed_log,
)
from cortado_core.utils.sublog_utils import calculate_infix_postfix_prefix_alignment
from cortado_core.utils.trace import TypedTrace
from cortado_core.utils.visualize_petri_net import visualize_petri_net

DEBUG = False


# TODO implement shuffling, switch log move position to find lowest common ancestor


def add_trace_to_pt_language(
    pt: ProcessTree,
    log: Union[EventLog, List[TypedTrace]],
    trace: Union[Trace, TypedTrace],
    try_pulling_lca_down=False,
    add_artificial_start_end=True,
    pool: Optional[multiprocessing.pool.Pool] = None,
    only_first_matching_alignment=True,
) -> ProcessTree:
    """
    Checks if a given trace can be replayed on the given process tree. If not, the tree will be altered to accept the
    given trace
    :param pt: process tree to update
    :param log: event log or list of typed traces, accepted by pt
    :param trace: trace that should be accepted by pt in the end
    :param try_pulling_lca_down:
    :param add_artificial_start_end:
    :param pool: Pool to parallelize alignment computations
    :return: process tree that accepts the given log and trace
    """

    if isinstance(log, EventLog):
        log = __add_typing_information_to_event_log(log)

    if isinstance(trace, Trace):
        trace = TypedTrace(trace, InfixType.NOT_AN_INFIX)

    return __add_trace_to_pt_language(
        pt,
        log,
        trace,
        try_pulling_lca_down=try_pulling_lca_down,
        add_artificial_start_end=add_artificial_start_end,
        pool=pool,
    )


def __add_typing_information_to_event_log(log: EventLog):
    return [TypedTrace(trace, InfixType.NOT_AN_INFIX) for trace in log]


def __add_artificial_start_end_activities(
    pt: ProcessTree,
    trace: TypedTrace,
    log: list[TypedTrace],
    add_artificial_start_end: bool,
) -> tuple[ProcessTree, TypedTrace, list[TypedTrace], bool]:
    if not add_artificial_start_end and (
        trace.infix_type == InfixType.NOT_AN_INFIX
        or trace.infix_type == InfixType.PROPER_INFIX
    ):
        return pt, trace, log, False

    pt = add_artificial_start_and_end_to_pt(pt)
    trace = add_artificial_start_end_activity_to_typed_trace(trace)
    log = add_artificial_start_end_activity_to_typed_log(log)

    return pt, trace, log, True


def __add_trace_to_pt_language(
    pt: ProcessTree,
    log: Union[EventLog, List[TypedTrace]],
    trace: TypedTrace,
    try_pulling_lca_down=False,
    add_artificial_start_end=True,
    pool: Optional[multiprocessing.pool.Pool] = None,
) -> ProcessTree:
    pt, trace, log, art_nodes_added = __add_artificial_start_end_activities(
        pt, trace, log, add_artificial_start_end
    )

    deviation = True
    while deviation:
        # necessary, because pt_to_petri_net method is only implemented for 2-loops
        reduce_loops_with_more_than_two_children(pt)

        if DEBUG:
            tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))
        set_preorder_ids_in_tree(pt)
        alignment = calculate_alignment_typed_trace(pt, trace)
        if alignment["cost"] >= STD_MODEL_LOG_MOVE_COST:
            # deviation found
            pt = __repair_process_tree(
                pt, log, alignment, try_pulling_lca_down, pool, trace.infix_type
            )
        else:
            deviation = False

    if art_nodes_added:
        pt = remove_artificial_start_and_end_activity_leaves_from_pt(pt)
    else:
        apply_reduction_rules(pt)

    return pt


def __repair_process_tree(
    pt_root: ProcessTree,
    log: List[TypedTrace],
    alignment: AlignmentResult,
    try_pulling_lca_down: bool,
    pool: Optional[multiprocessing.pool.Pool],
    infix_type: InfixType,
) -> ProcessTree:
    logging.debug("repair_process_tree()")

    deviation = get_deviation(alignment)
    solver = get_deviation_solver(deviation, infix_type, try_pulling_lca_down, pool)
    return solver.solve(deviation, pt_root, log)


def get_deviation(alignment) -> Deviation:
    step, i = get_first_deviation(alignment)
    if step is None:
        logging.debug("found no deviation")
        return Deviation(
            DeviationType.NO_DEVIATION, (None, -1), (None, -1), alignment, i
        )

    logging.debug("deviation at ", i)
    exec_pt_leave_before_deviation = __get_leaf_before_deviation(alignment, i)
    exec_pt_leave_after_deviation = __get_leaf_after_deviation(alignment, i)

    if (
        exec_pt_leave_before_deviation[0] is None
        and exec_pt_leave_after_deviation[0] is None
    ):
        return Deviation(
            DeviationType.NOT_ENCLOSED, (None, -1), (None, -1), alignment, i
        )

    if (
        exec_pt_leave_before_deviation[0] is not None
        and exec_pt_leave_after_deviation[0] is not None
    ):
        return Deviation(
            DeviationType.ENCLOSED,
            exec_pt_leave_before_deviation,
            exec_pt_leave_after_deviation,
            alignment,
            i,
        )

    if exec_pt_leave_before_deviation[0] is not None:
        return Deviation(
            DeviationType.LEFT_ENCLOSED,
            exec_pt_leave_before_deviation,
            (None, -1),
            alignment,
            i,
        )

    return Deviation(
        DeviationType.RIGHT_ENCLOSED,
        (None, -1),
        exec_pt_leave_after_deviation,
        alignment,
        i,
    )


def __get_leaf_before_deviation(
    alignment: AlignmentResult, deviation_i: int
) -> tuple[ProcessTree, int]:
    exec_pt_leave_before_deviation = None
    h = deviation_i - 1
    while h >= 0 and not exec_pt_leave_before_deviation:
        step_before: Tuple = alignment["alignment"][h]
        if alignment_step_represents_no_deviation(step_before) and is_leaf_node(
            step_before[0][1][0]
        ):
            exec_pt_leave_before_deviation = step_before[0][1][0]
        h -= 1

    return exec_pt_leave_before_deviation, h + 1


def __get_leaf_after_deviation(
    alignment: AlignmentResult, deviation_i: int
) -> tuple[ProcessTree, int]:
    exec_pt_leave_after_deviation = None
    j = deviation_i + 1
    while j < len(alignment["alignment"]) and not exec_pt_leave_after_deviation:
        step_after: Tuple = alignment["alignment"][j]
        if alignment_step_represents_no_deviation(step_after) and is_leaf_node(
            step_after[0][1][0]
        ):
            exec_pt_leave_after_deviation = step_after[0][1][0]
        j += 1

    return exec_pt_leave_after_deviation, j - 1


def set_preorder_ids_in_tree(pt: ProcessTree, current_index=0) -> int:
    pt.id = current_index
    current_index += 1

    for child in pt.children:
        current_index = set_preorder_ids_in_tree(child, current_index)

    return current_index


def test_im():
    l = EventLog()
    e1 = Event()
    e2 = Event()
    e1["concept:name"] = "A"
    e2["concept:name"] = "B"
    t = Trace()
    t.append(e1)
    t.append(e2)
    l.append(t)

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e1["concept:name"] = "A"
    e2["concept:name"] = "B"
    e3["concept:name"] = "B"
    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    l.append(t)

    pt = inductive_miner.apply_tree(l)
    tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))


if __name__ == "__main__":
    tree: ProcessTree = pt_parse("+ (->('A','A'),'C'))")
    print(tree.children[0].children.index(tree.children[0].children[0]))  # --> 0
    print(tree.children[0].children.index(tree.children[0].children[1]))  # --> 0

    print(
        get_index_of_pt_in_children_list(tree.children[0], tree.children[0].children[1])
    )

    # create log
    test_im()

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

    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    net, im, fm = pt_to_petri_net(tree)
    visualize_petri_net(net)

    print("height", get_height(tree))
    print("silent leaves", get_number_silent_leaves(tree))
    print("leaves", get_number_leaves(tree))
    print("nodes", get_number_nodes(tree))

    """tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = False)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = False, try_pulling_lca_down=True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = True, try_pulling_lca_down= True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))"""

    print("\n Not Pulling LCA Down, Artif. Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)

    print("\n Not Pulling LCA Down, No Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=False)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)

    print("\n Pulling LCA Down, No Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(
        tree, L, t3, add_artificial_start_end=False, try_pulling_lca_down=True
    )
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)

    print("\n Pulling LCA Down, Artif. Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(
        tree, L, t3, add_artificial_start_end=True, try_pulling_lca_down=True
    )
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)
