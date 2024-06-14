from typing import Dict, Tuple, List, FrozenSet, OrderedDict, Union

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
import pm4py.visualization.process_tree.visualizer as tree_vis
from cortado_core.models.infix_type import InfixType

from cortado_core.process_tree_utils.miscellaneous import (
    is_leaf_node,
    is_visible_leaf,
    pt_dict_key,
    subtree_is_part_of_tree_based_on_obj_id,
)
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import (
    apply as pt_to_petri_net,
)
from cortado_core.utils.alignment_utils import (
    alignment_contains_deviation,
    calculate_alignment_typed_trace,
    is_sync_move,
    alignment_step_represents_no_deviation,
)
from cortado_core.utils.sublog_utils import (
    generate_full_alignment_based_on_infix_alignment,
)
from cortado_core.utils.trace import TypedTrace
from cortado_core.utils.visualize_petri_net import visualize_petri_net


def project_log(
    pt: ProcessTree,
    log: Union[EventLog, List[TypedTrace]],
    frozen_subtrees: OrderedDict[Tuple[ProcessTree, int], str],
) -> Tuple[Dict[FrozenSet[Tuple[ProcessTree, int]], EventLog], EventLog]:
    if isinstance(log, EventLog):
        log = [TypedTrace(trace, InfixType.NOT_AN_INFIX) for trace in log]

    # assumption: log is replayable on process tree without deviations
    alignments = []
    for trace in log:
        alignment = calculate_alignment_typed_trace(pt, trace)
        if trace.infix_type != InfixType.NOT_AN_INFIX:
            alignment = generate_full_alignment_based_on_infix_alignment(
                trace.infix_type, alignment
            )
        alignments.append(alignment)

    replaced_frozen_subtrees: List[Tuple[ProcessTree, int]] = []
    incrementally_projected_logs: Dict[
        FrozenSet[Tuple[ProcessTree, int]], EventLog
    ] = {}
    final_projected_log: EventLog

    for frozen_subtree in frozen_subtrees:
        # incrementally replace the frozen subtree(s)

        replaced_frozen_subtrees.append(frozen_subtree)
        res = []

        for i, alignment in enumerate(alignments):
            current_infix_type = log[i].infix_type
            assert (
                not alignment_contains_deviation(alignment)
                or current_infix_type != InfixType.NOT_AN_INFIX
            )
            trace = Trace()

            if current_infix_type == InfixType.NOT_AN_INFIX:
                for step in alignment["alignment"]:
                    # executed transition always corresponds to a node in the process tree
                    current_pt: ProcessTree = step[0][1][0]
                    assert type(current_pt) is ProcessTree
                    # determine if current_pt is frozen
                    current_pt_frozen = False
                    for f_pt, f_pt_id in replaced_frozen_subtrees:
                        if subtree_is_part_of_tree_based_on_obj_id(current_pt, f_pt):
                            current_pt_frozen = True

                    activity_label = None
                    if is_visible_leaf(current_pt) and not current_pt_frozen:
                        activity_label = step[1][1]
                    elif (
                        current_pt_frozen
                        and pt_dict_key(current_pt) in replaced_frozen_subtrees
                    ):
                        if step[0][1][1] == "active":
                            activity_label = (
                                frozen_subtrees[pt_dict_key(current_pt)] + "+ACTIVATED"
                            )
                        elif step[0][1][1] == "closed":
                            activity_label = (
                                frozen_subtrees[pt_dict_key(current_pt)] + "+CLOSED"
                            )
                    if activity_label:
                        event = Event()
                        event["concept:name"] = activity_label
                        trace.append(event)
            else:
                infix_opened = False
                open_frozen_trees = []
                for step in alignment["alignment"]:
                    # executed transition always corresponds to a node in the process tree
                    current_pt: ProcessTree = step[0][1][0]
                    assert type(current_pt) is ProcessTree
                    # determine if current_pt is frozen
                    current_pt_frozen = False
                    for f_pt, f_pt_id in replaced_frozen_subtrees:
                        if subtree_is_part_of_tree_based_on_obj_id(current_pt, f_pt):
                            current_pt_frozen = True

                    if not infix_opened and is_sync_move(step):
                        infix_opened = True
                        # insert open replacement labels for frozen subtrees opened before infix
                        for open_pt in open_frozen_trees:
                            replacement_label = (
                                frozen_subtrees[pt_dict_key(open_pt)] + "+ACTIVATED"
                            )
                            trace.append(Event({"concept:name": replacement_label}))
                    elif infix_opened and not alignment_step_represents_no_deviation(
                        step
                    ):
                        # the rest of the alignment has deviations and the infix closed
                        infix_opened = False
                        # insert closing replacement labels for open frozen subtrees
                        for open_pt in reversed(open_frozen_trees):
                            replacement_label = (
                                frozen_subtrees[pt_dict_key(open_pt)] + "+CLOSED"
                            )
                            trace.append(Event({"concept:name": replacement_label}))
                        break

                    if pt_dict_key(current_pt) in replaced_frozen_subtrees:
                        if step[0][1][1] == "active":
                            open_frozen_trees.append(current_pt)
                            if infix_opened:
                                replacement_label = (
                                    frozen_subtrees[pt_dict_key(current_pt)]
                                    + "+ACTIVATED"
                                )
                                trace.append(Event({"concept:name": replacement_label}))

                        elif step[0][1][1] == "closed":
                            open_frozen_trees.remove(current_pt)
                            if infix_opened:
                                replacement_label = (
                                    frozen_subtrees[pt_dict_key(current_pt)] + "+CLOSED"
                                )
                                trace.append(Event({"concept:name": replacement_label}))

                    if (
                        is_visible_leaf(current_pt)
                        and is_sync_move(step)
                        and not current_pt_frozen
                    ):
                        trace.append(Event({"concept:name": step[1][1]}))

            typed_trace = TypedTrace(trace, log[i].infix_type)
            res.append(typed_trace)
        incrementally_projected_logs[frozenset(replaced_frozen_subtrees)] = res
        final_projected_log = res
    return incrementally_projected_logs, final_projected_log


if __name__ == "__main__":
    pt_1: ProcessTree = pt_parse(
        "-> (*(X(->('A','B'),->('C','D')),tau) ,->('E',->('A','F')) )"
    )
    pt_2: ProcessTree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F' )")

    print(subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_1))  # True

    print("tree:", pt_1)
    print("subtree:", pt_1.children[1].children[1])
    print(
        subtree_is_part_of_tree_based_on_obj_id(pt_1.children[1].children[1], pt_1)
    )  # True
    print(
        subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_1.children[1].children[1])
    )  # False
    print(subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_2))

    L = EventLog()
    e1 = Event()
    e1["concept:name"] = "A"
    e2 = Event()
    e2["concept:name"] = "B"
    e3 = Event()
    e3["concept:name"] = "C"
    e4 = Event()
    e4["concept:name"] = "D"

    t1 = Trace()
    t1.append(e1)
    t1.append(e1)
    t1.append(e3)
    t1.append(e4)
    t1.append(e2)
    L.append(t1)

    t2 = Trace()
    t2.append(e3)
    t2.append(e4)
    t2.append(e1)
    t2.append(e1)
    t2.append(e2)
    L.append(t2)

    t3 = Trace()
    t3.append(e3)
    t3.append(e1)
    t3.append(e1)
    t3.append(e4)
    t3.append(e2)
    L.append(t3)

    tree: ProcessTree = pt_parse("+ (->('A','A','B'),->('C','D'))")
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg", "debug": True}))
    net_tree, im, fm = pt_to_petri_net(tree)
    visualize_petri_net(net_tree)
    log = project_log(
        tree,
        L,
        {
            (tree.children[1], id(tree.children[1])): "X",
            (tree.children[0], id(tree.children[0])): "Y",
        },
    )
    print(log)
