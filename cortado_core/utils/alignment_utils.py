from pm4py.objects.log.obj import Trace
from pm4py.objects.petri_net.utils.align_utils import SKIP
from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.conversion.process_tree.converter import apply as pt_to_pn
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignment
from pm4py.util.typing import AlignmentResult
from pm4py.algo.conformance.alignments.petri_net.algorithm import variants as variants_calculate_alignments

from cortado_core.models.infix_type import InfixType
from cortado_core.utils.trace import TypedTrace
from cortado_core.alignments.infix_alignments import algorithm as infix_alignments
from cortado_core.alignments.prefix_alignments import algorithm as prefix_alignments
from cortado_core.alignments.suffix_alignments import algorithm as suffix_alignments
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import apply as pt_to_petri_net_cortado


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


def get_first_deviation(alignment: AlignmentResult):
    for i, step in enumerate(alignment['alignment']):
        if is_log_move(step) or is_model_move_on_visible_activity(step):
            return step, i

    return None, -1


def calculate_alignment_typed_trace(pt: ProcessTree, trace: TypedTrace):
    match trace.infix_type:
        case InfixType.NOT_AN_INFIX:
            net, im, fm = pt_to_petri_net_cortado(pt)
            return calculate_alignment(trace.trace, net, im, fm, parameters={'ret_tuple_as_trans_desc': True},
                                       variant=variants_calculate_alignments.state_equation_a_star)
        case inf_type:
            return calculate_infix_postfix_prefix_alignment(trace.trace, pt, inf_type)


def typed_trace_fits_process_tree(trace: TypedTrace, pt: ProcessTree) -> bool:
    alignment = calculate_alignment_typed_trace(pt, trace)
    return not alignment_contains_deviation(alignment)


def calculate_infix_postfix_prefix_alignment(trace: Trace, pt: ProcessTree, infix_type: InfixType):
    params = {
        'ret_tuple_as_trans_desc': True
    }

    old_parent = pt.parent
    pt.parent = None

    match infix_type:
        case InfixType.PROPER_INFIX:
            alignment = infix_alignments.calculate_optimal_infix_alignment(trace, pt,
                                                                           infix_alignments.VARIANT_TREE_BASED_PREPROCESSING,
                                                                           naive=False, use_cortado_tree_converter=True,
                                                                           parameters=params)
        case InfixType.PREFIX:
            alignment = prefix_alignments.calculate_optimal_prefix_alignment(trace, pt, use_dijkstra=True,
                                                                             use_cortado_tree_converter=True,
                                                                             parameters=params)
        case InfixType.POSTFIX:
            alignment = suffix_alignments.calculate_optimal_suffix_alignment(trace, pt, naive=False, use_dijkstra=True,
                                                                             use_cortado_tree_converter=True,
                                                                             parameters=params)

        case InfixType.NOT_AN_INFIX:
            raise Exception('Infix Type is not supported')

    pt.parent = old_parent
    return alignment
