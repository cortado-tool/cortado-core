import sys
from copy import copy

from pm4py.objects.petri_net.utils import align_utils
from pm4py.util.xes_constants import DEFAULT_NAME_KEY
from pm4py.util import exec_utils
from enum import Enum
from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY, PARAMETER_CONSTANT_CASEID_KEY
from pm4py.objects.log.obj import Trace
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.util import typing as pm4pyTyping
from pm4py.objects.conversion.process_tree import converter as pt_converter

from cortado_core.alignments.prefix_alignments.variants import dijkstra_no_heuristics, a_star


class Variants(Enum):
    VERSION_DIJKSTRA_NO_HEURISTICS = dijkstra_no_heuristics
    VERSION_A_STAR = a_star


class Parameters(Enum):
    PARAM_TRACE_COST_FUNCTION = 'trace_cost_function'
    PARAM_MODEL_COST_FUNCTION = 'model_cost_function'
    PARAM_SYNC_COST_FUNCTION = 'sync_cost_function'
    PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE = 'ret_tuple_as_trans_desc'
    PARAM_TRACE_NET_COSTS = "trace_net_costs"
    TRACE_NET_CONSTR_FUNCTION = "trace_net_constr_function"
    TRACE_NET_COST_AWARE_CONSTR_FUNCTION = "trace_net_cost_aware_constr_function"
    PARAM_MAX_ALIGN_TIME_TRACE = "max_align_time_trace"
    PARAM_MAX_ALIGN_TIME = "max_align_time"
    PARAMETER_VARIANT_DELIMITER = "variant_delimiter"
    CASE_ID_KEY = PARAMETER_CONSTANT_CASEID_KEY
    ACTIVITY_KEY = PARAMETER_CONSTANT_ACTIVITY_KEY
    VARIANTS_IDX = "variants_idx"
    SHOW_PROGRESS_BAR = "show_progress_bar"
    CORES = 'cores'
    BEST_WORST_COST_INTERNAL = "best_worst_cost_internal"
    FITNESS_ROUND_DIGITS = "fitness_round_digits"
    PARAM_ENFORCE_FIRST_TAU_MOVE = "enforce_first_tau_move"


DEFAULT_VARIANT = Variants.VERSION_A_STAR
VERSION_DIJKSTRA_NO_HEURISTICS = Variants.VERSION_DIJKSTRA_NO_HEURISTICS
VERSION_A_STAR = Variants.VERSION_A_STAR

VERSIONS = {Variants.VERSION_DIJKSTRA_NO_HEURISTICS, Variants.VERSION_A_STAR}


def calculate_optimal_prefix_alignment(trace: Trace, process_tree: ProcessTree, use_dijkstra: bool = False,
                                       timeout: int = sys.maxsize) -> pm4pyTyping.AlignmentResult:
    net, im, fm = pt_converter.apply(process_tree)
    align_variant = __get_prefix_alignment_variant(use_dijkstra)

    return apply_trace(trace, net, im, fm, variant=align_variant, parameters={
        Parameters.PARAM_MAX_ALIGN_TIME_TRACE: timeout,
    })


def __get_prefix_alignment_variant(use_dijkstra: bool):
    if use_dijkstra:
        return VERSION_DIJKSTRA_NO_HEURISTICS
    return VERSION_A_STAR


def apply_trace(trace, petri_net, initial_marking, final_marking, parameters=None,
                variant=DEFAULT_VARIANT):
    """
    apply alignments to a trace
    Parameters
    -----------
    trace
        :class:`pm4py.log.log.Trace` trace of events
    petri_net
        :class:`pm4py.objects.petri.petrinet.PetriNet` the model to use for the alignment
    initial_marking
        :class:`pm4py.objects.petri.petrinet.Marking` initial marking of the net
    final_marking
        :class:`pm4py.objects.petri.petrinet.Marking` final marking of the net
    variant
        selected variant of the algorithm, possible values: {\'Variants.VERSION_STATE_EQUATION_A_STAR, Variants.VERSION_DIJKSTRA_NO_HEURISTICS \'}
    parameters
        :class:`dict` parameters of the algorithm, for key \'state_equation_a_star\':
            Parameters.ACTIVITY_KEY -> Attribute in the log that contains the activity
            Parameters.PARAM_MODEL_COST_FUNCTION ->
            mapping of each transition in the model to corresponding synchronous costs
            Parameters.PARAM_SYNC_COST_FUNCTION ->
            mapping of each transition in the model to corresponding model cost
            Parameters.PARAM_TRACE_COST_FUNCTION ->
            mapping of each index of the trace to a positive cost value
    Returns
    -----------
    alignment
        :class:`dict` with keys **alignment**, **cost**, **visited_states**, **queued_states** and
        **traversed_arcs**
        The alignment is a sequence of labels of the form (a,t), (a,>>), or (>>,t)
        representing synchronous/log/model-moves.
    """
    if parameters is None:
        parameters = copy({PARAMETER_CONSTANT_ACTIVITY_KEY: DEFAULT_NAME_KEY})

    parameters = copy(parameters)

    ali = exec_utils.get_variant(variant).apply(trace, petri_net, initial_marking, final_marking,
                                                parameters=parameters)

    if ali is None:
        return None

    ltrace_bwc = len(trace)

    fitness = 1 - (ali['cost'] // align_utils.STD_MODEL_LOG_MOVE_COST) / (
        ltrace_bwc) if ltrace_bwc > 0 else 0

    ali["fitness"] = fitness
    # returning also the best worst cost, for log fitness computation
    ali["bwc"] = ltrace_bwc * align_utils.STD_MODEL_LOG_MOVE_COST

    return ali


def __get_best_worst_cost(petri_net, initial_marking, final_marking, variant, parameters):
    parameters_best_worst = copy(parameters)

    best_worst_cost = exec_utils.get_variant(variant).get_best_worst_cost(petri_net, initial_marking, final_marking,
                                                                          parameters=parameters_best_worst)

    return best_worst_cost
