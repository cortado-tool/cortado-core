import copy
import sys
import time

from pm4py.objects.log.obj import Trace
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.util import typing as pm4py_typing
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
from cortado_core.alignments.infix_alignments import utils as infix_utils
from cortado_core.alignments.infix_alignments.variants.tree_based_preprocessing import (
    build_extended_petri_net_for_infix_alignments,
)
from cortado_core.alignments.infix_alignments.variants.baseline_approach import (
    build_extended_petri_net_for_infix_alignments as build_extended_petri_net_for_infix_alignments_baseline,
)
from cortado_core.alignments.prefix_alignments.algorithm import add_to_parameters

VARIANT_TREE_BASED_PREPROCESSING = 1
VARIANT_BASELINE_APPROACH = 2


def calculate_optimal_suffix_alignment(
    trace: Trace,
    process_tree: ProcessTree,
    naive: bool = True,
    use_dijkstra: bool = False,
    variant: int = VARIANT_TREE_BASED_PREPROCESSING,
    timeout: int = sys.maxsize,
    use_cortado_tree_converter=True,
    copy_tree=True,
    parameters=None,
) -> pm4py_typing.AlignmentResult:
    if copy_tree:
        process_tree = copy.deepcopy(process_tree)

    start = time.time()

    try:
        if variant == VARIANT_BASELINE_APPROACH:
            (
                net,
                im,
                fm,
                n_added_tau_transitions,
                unmodified_net_getter,
            ) = build_extended_petri_net_for_infix_alignments_baseline(
                process_tree,
                trace,
                naive,
                timeout,
                use_cortado_tree_converter=use_cortado_tree_converter,
            )
        else:
            # never reduce the tree, because this can lead to incorrect suffix alignments
            (
                net,
                im,
                fm,
                n_added_tau_transitions,
                unmodified_net_getter,
            ) = build_extended_petri_net_for_infix_alignments(
                trace,
                process_tree,
                naive,
                False,
                True,
                timeout,
                use_cortado_tree_converter=use_cortado_tree_converter,
            )
    except TimeoutError:
        return {"timeout": True}

    preprocessing_duration = time.time() - start
    timeout = timeout - preprocessing_duration

    alignment_variant = __get_alignment_variant(use_dijkstra)
    align_start = time.time()

    try:
        params = {
            alignments.Parameters.PARAM_MAX_ALIGN_TIME_TRACE: timeout,
        }

        # needed because of a bug in pm4py that results in an exception for timeouts
        alignment = alignments.apply_trace(
            trace,
            net,
            im,
            fm,
            variant=alignment_variant,
            parameters=add_to_parameters(params, parameters),
        )
    except:
        alignment = {"timeout": True}
        return alignment

    if alignment is None:
        alignment = {"timeout": True}
        return alignment

    alignment = infix_utils.remove_first_tau_move_from_alignment(alignment, net, im)

    alignment["alignment_duration"] = time.time() - align_start
    alignment["preprocessing_duration"] = preprocessing_duration
    alignment["added_tau_transitions"] = n_added_tau_transitions
    alignment["net"] = unmodified_net_getter()
    if "start_marking" not in alignment:
        alignment["start_marking"] = alignment["net"][1]

    return alignment


def __get_alignment_variant(use_dijkstra: bool):
    if use_dijkstra:
        return alignments.VERSION_DIJKSTRA_NO_HEURISTICS
    return alignments.VERSION_STATE_EQUATION_A_STAR
