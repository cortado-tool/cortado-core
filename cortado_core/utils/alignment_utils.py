from pm4py.objects.log.obj import Trace
from pm4py.objects.petri_net.utils.align_utils import SKIP
from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.conversion.process_tree.converter import apply as pt_to_pn
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignment


def is_log_move(alignment_step, skip=SKIP) -> bool:
    return alignment_step[1][1] == skip


def is_model_move_on_visible_activity(alignment_step, skip=SKIP) -> bool:
    return alignment_step[1][0] == skip and alignment_step[1][1] is not None


def is_model_move(alignment_step, skip=SKIP) -> bool:
    return alignment_step[1][0] == skip


def alignment_step_represents_no_deviation(alignment_step) -> bool:
    return not is_log_move(alignment_step) and not is_model_move_on_visible_activity(alignment_step)


def is_sync_move(alignment_step) -> bool:
    return alignment_step_represents_no_deviation(alignment_step) and alignment_step[1][1] is not None


def alignment_contains_deviation(alignment) -> bool:
    return alignment['cost'] >= STD_MODEL_LOG_MOVE_COST


def trace_fits_process_tree(trace: Trace, pt: ProcessTree) -> bool:
    net, im, fm = pt_to_pn(pt)
    alignment = calculate_alignment(trace, net, im, fm)
    return not alignment_contains_deviation(alignment)


