import copy
import logging

import pm4py.visualization.petri_net.visualizer as petri_vis
import pm4py.visualization.process_tree.visualizer as tree_vis
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignments
from pm4py.algo.conformance.alignments.petri_net.algorithm import variants as variants_calculate_alignments
from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST, SKIP
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.obj import Operator
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignments
from pm4py.algo.conformance.alignments.petri_net.algorithm import variants as variants_calculate_alignments
from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST, SKIP
from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.objects.process_tree.semantics import generate_log
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.log.obj import Trace

from cortado_core.process_tree_utils.miscellaneous import is_leaf_node, get_index_of_pt_in_children_list
from cortado_core.process_tree_utils.reduction import apply_reduction_rules
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import apply as pt_to_petri_net
from cortado_core.utils.visualize_petri_net import visualize_petri_net

DEBUG = False


def __repair_model_move(step, process_tree_root):
    model_move_leave = step[0][1][0]
    choice_pt = ProcessTree(Operator.XOR, parent=model_move_leave.parent)
    # remove last executed leave node from parent's children list
    index_last_executed_leave_node = get_index_of_pt_in_children_list(model_move_leave.parent, model_move_leave)
    model_move_leave.parent.children[index_last_executed_leave_node] = choice_pt
    model_move_leave.parent = choice_pt
    choice_pt.children.append(model_move_leave)
    tau_pt = ProcessTree(parent=choice_pt)
    choice_pt.children.append(tau_pt)
    return process_tree_root


def __repair_log_move(log_move_activity, last_executed_leave_node, process_tree_root):
    # create sub-process-tree: choice of log move activity and tau
    choice_pt = pt_parse("X ( '" + log_move_activity + "', tau)")
    if last_executed_leave_node:
        # add sequence of last executed leave node followed by choice of tau or log move activity
        sequence_pt = ProcessTree(operator=Operator.SEQUENCE, parent=last_executed_leave_node.parent,
                                  children=[last_executed_leave_node, choice_pt])
        # set sequence pt as the parent of choice pt
        choice_pt.parent = sequence_pt
        # attach sequence to process tree
        sequence_parent = last_executed_leave_node.parent
        # update last_executed_leave_node parent
        last_executed_leave_node.parent = sequence_pt

        if sequence_parent is None:
            return sequence_pt
        else:
            index_last_executed_leave_node = get_index_of_pt_in_children_list(sequence_parent, last_executed_leave_node)
            sequence_parent.children[index_last_executed_leave_node] = sequence_pt

            return process_tree_root
    else:
        # root is a sequence of an optional log move activity followed by the original process tree
        sequence_pt = ProcessTree(operator=Operator.SEQUENCE, children=[choice_pt, process_tree_root])
        process_tree_root.parent = sequence_pt
        choice_pt.parent = sequence_pt
        return sequence_pt


def repair_first_deviation(alignment, process_tree_root, debug=DEBUG):
    assert process_tree_root
    for i, step in enumerate(alignment['alignment']):
        is_log_move = step[1][1] == SKIP
        is_model_move_on_pt = step[1][0] == SKIP and isinstance(step[0][1][0], ProcessTree) and is_leaf_node(
            step[0][1][0]) and step[0][1][0].label

        if is_model_move_on_pt:
            if debug:
                logging.debug("repair model move")
            res: ProcessTree = __repair_model_move(step, process_tree_root)
            apply_reduction_rules(res)
            return res
        elif is_log_move:
            if debug:
                logging.debug("repair log move")
            last_executed_leave_node = None
            while i > 0 and last_executed_leave_node is None:
                i -= 1
                previous_step = alignment['alignment'][i]
                # check if executed transition is part of process tree
                if is_leaf_node(previous_step[0][1][0]):
                    last_executed_leave_node = previous_step[0][1][0]
            log_move_activity = str(step[1][0])
            res: ProcessTree = __repair_log_move(log_move_activity, last_executed_leave_node, process_tree_root)
            apply_reduction_rules(res)
            return res


def ensure_trace_replayable_on_process_tree(trace: Trace, process_tree_root: ProcessTree, debug=DEBUG):
    deviation_found = True
    while deviation_found:
        net, im, fm = pt_to_petri_net(process_tree_root)
        if debug:
            pass
            visualize_petri_net(net)
        alignment = calculate_alignments(trace, net, im, fm, parameters={'ret_tuple_as_trans_desc': True},
                                         variant=variants_calculate_alignments.state_equation_a_star)
        deviation_found = alignment['cost'] >= STD_MODEL_LOG_MOVE_COST
        if deviation_found:
            process_tree_root = repair_first_deviation(alignment, process_tree_root)
            if debug:
                tree_vis.view(tree_vis.apply(process_tree_root, parameters={"format": "svg", "debug": True}))
    return process_tree_root


if __name__ == '__main__':
    DEBUG = True
    process_tree = pt_parse("-> ( 'A',tau, * ( 'A', 'B' ), 'C')")
    vis_2 = tree_vis.apply(process_tree, parameters={"format": "svg", "debug": True})
    tree_vis.view(vis_2)
    # deepcopy is a workaround, since generate_log alters the process_tree object
    copy_process_tree = copy.deepcopy(process_tree)
    log = generate_log(copy_process_tree, 10)

    # adding deviation to trace
    trace = log[1]
    trace_copy = copy.deepcopy(trace)
    trace[0] = trace_copy[2]
    trace[2] = trace_copy[1]

    for e in trace:
        print(e)

    pt = ensure_trace_replayable_on_process_tree(trace, process_tree, debug=True)
