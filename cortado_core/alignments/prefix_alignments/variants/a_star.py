import heapq
import math
import sys
import time
from copy import copy
from enum import Enum
import numpy as np

from ortools.linear_solver import pywraplp

from pm4py.objects.log import obj as log_implementation
from pm4py.objects.petri_net.utils import align_utils as utils
from pm4py.objects.petri_net.utils.synchronous_product import construct_cost_aware, construct
from pm4py.objects.petri_net.utils.petri_utils import construct_trace_net_cost_aware, decorate_places_preset_trans, \
    decorate_transitions_prepostset
from pm4py.util import exec_utils
from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY
from pm4py.util.lp import solver as lp_solver
from pm4py.util.xes_constants import DEFAULT_NAME_KEY
from typing import Optional, Dict, Any, Union
from pm4py.objects.log.obj import Trace
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util import typing
from pm4py.objects.petri_net.utils.incidence_matrix import construct as inc_mat_construct


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
    ACTIVITY_KEY = PARAMETER_CONSTANT_ACTIVITY_KEY
    VARIANTS_IDX = "variants_idx"
    RETURN_SYNC_COST_FUNCTION = "return_sync_cost_function"


PARAM_TRACE_COST_FUNCTION = Parameters.PARAM_TRACE_COST_FUNCTION.value
PARAM_MODEL_COST_FUNCTION = Parameters.PARAM_MODEL_COST_FUNCTION.value
PARAM_SYNC_COST_FUNCTION = Parameters.PARAM_SYNC_COST_FUNCTION.value


def apply(trace: Trace, petri_net: PetriNet, initial_marking: Marking, final_marking: Marking,
          parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> typing.AlignmentResult:
    """
    Performs the basic alignment search, given a trace and a net.

    Parameters
    ----------
    trace: :class:`list` input trace, assumed to be a list of events (i.e. the code will use the activity key
    to get the attributes)
    petri_net: :class:`pm4py.objects.petri.net.PetriNet` the Petri net to use in the alignment
    initial_marking: :class:`pm4py.objects.petri.net.Marking` initial marking in the Petri net
    final_marking: :class:`pm4py.objects.petri.net.Marking` final marking in the Petri net
    parameters: :class:`dict` (optional) dictionary containing one of the following:
        Parameters.PARAM_TRACE_COST_FUNCTION: :class:`list` (parameter) mapping of each index of the trace to a positive cost value
        Parameters.PARAM_MODEL_COST_FUNCTION: :class:`dict` (parameter) mapping of each transition in the model to corresponding
        model cost
        Parameters.PARAM_SYNC_COST_FUNCTION: :class:`dict` (parameter) mapping of each transition in the model to corresponding
        synchronous costs
        Parameters.ACTIVITY_KEY: :class:`str` (parameter) key to use to identify the activity described by the events

    Returns
    -------
    dictionary: `dict` with keys **alignment**, **cost**, **visited_states**, **queued_states** and **traversed_arcs**
    """
    if parameters is None:
        parameters = {}

    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, DEFAULT_NAME_KEY)
    trace_cost_function = exec_utils.get_param_value(Parameters.PARAM_TRACE_COST_FUNCTION, parameters, None)
    model_cost_function = exec_utils.get_param_value(Parameters.PARAM_MODEL_COST_FUNCTION, parameters, None)
    trace_net_constr_function = exec_utils.get_param_value(Parameters.TRACE_NET_CONSTR_FUNCTION, parameters,
                                                           None)
    trace_net_cost_aware_constr_function = exec_utils.get_param_value(Parameters.TRACE_NET_COST_AWARE_CONSTR_FUNCTION,
                                                                      parameters, construct_trace_net_cost_aware)

    if trace_cost_function is None:
        trace_cost_function = list(
            map(lambda e: utils.STD_MODEL_LOG_MOVE_COST, trace))
        parameters[Parameters.PARAM_TRACE_COST_FUNCTION] = trace_cost_function

    if model_cost_function is None:
        # reset variables value
        model_cost_function = dict()
        sync_cost_function = dict()
        for t in petri_net.transitions:
            if t.label is not None:
                model_cost_function[t] = utils.STD_MODEL_LOG_MOVE_COST
                sync_cost_function[t] = utils.STD_SYNC_COST
            else:
                model_cost_function[t] = utils.STD_TAU_COST
        parameters[Parameters.PARAM_MODEL_COST_FUNCTION] = model_cost_function
        parameters[Parameters.PARAM_SYNC_COST_FUNCTION] = sync_cost_function

    if trace_net_constr_function is not None:
        # keep the possibility to pass TRACE_NET_CONSTR_FUNCTION in this old version
        trace_net, trace_im, trace_fm = trace_net_constr_function(trace, activity_key=activity_key)
    else:
        trace_net, trace_im, trace_fm, parameters[
            Parameters.PARAM_TRACE_NET_COSTS] = trace_net_cost_aware_constr_function(trace,
                                                                                     trace_cost_function,
                                                                                     activity_key=activity_key)

    alignment = apply_trace_net(petri_net, initial_marking, final_marking, trace_net, trace_im, trace_fm, parameters)

    return alignment


def apply_trace_net(petri_net, initial_marking, final_marking, trace_net, trace_im, trace_fm, parameters=None):
    """
        Performs the basic alignment search, given a trace net and a net.

        Parameters
        ----------
        trace: :class:`list` input trace, assumed to be a list of events (i.e. the code will use the activity key
        to get the attributes)
        petri_net: :class:`pm4py.objects.petri.net.PetriNet` the Petri net to use in the alignment
        initial_marking: :class:`pm4py.objects.petri.net.Marking` initial marking in the Petri net
        final_marking: :class:`pm4py.objects.petri.net.Marking` final marking in the Petri net
        parameters: :class:`dict` (optional) dictionary containing one of the following:
            Parameters.PARAM_TRACE_COST_FUNCTION: :class:`list` (parameter) mapping of each index of the trace to a positive cost value
            Parameters.PARAM_MODEL_COST_FUNCTION: :class:`dict` (parameter) mapping of each transition in the model to corresponding
            model cost
            Parameters.PARAM_SYNC_COST_FUNCTION: :class:`dict` (parameter) mapping of each transition in the model to corresponding
            synchronous costs
            Parameters.ACTIVITY_KEY: :class:`str` (parameter) key to use to identify the activity described by the events
            Parameters.PARAM_TRACE_NET_COSTS: :class:`dict` (parameter) mapping between transitions and costs

        Returns
        -------
        dictionary: `dict` with keys **alignment**, **cost**, **visited_states**, **queued_states** and **traversed_arcs**
        """
    if parameters is None:
        parameters = {}

    ret_tuple_as_trans_desc = exec_utils.get_param_value(Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE,
                                                         parameters, False)

    trace_cost_function = exec_utils.get_param_value(Parameters.PARAM_TRACE_COST_FUNCTION, parameters, None)
    model_cost_function = exec_utils.get_param_value(Parameters.PARAM_MODEL_COST_FUNCTION, parameters, None)
    sync_cost_function = exec_utils.get_param_value(Parameters.PARAM_SYNC_COST_FUNCTION, parameters, None)
    trace_net_costs = exec_utils.get_param_value(Parameters.PARAM_TRACE_NET_COSTS, parameters, None)

    if trace_cost_function is None or model_cost_function is None or sync_cost_function is None:
        sync_prod, sync_initial_marking, sync_final_marking = construct(trace_net, trace_im,
                                                                        trace_fm, petri_net,
                                                                        initial_marking,
                                                                        final_marking,
                                                                        utils.SKIP)
        cost_function = utils.construct_standard_cost_function(sync_prod, utils.SKIP)
    else:
        revised_sync = dict()
        for t_trace in trace_net.transitions:
            for t_model in petri_net.transitions:
                if t_trace.label == t_model.label:
                    revised_sync[(t_trace, t_model)] = sync_cost_function[t_model]

        sync_prod, sync_initial_marking, sync_final_marking, cost_function = construct_cost_aware(
            trace_net, trace_im, trace_fm, petri_net, initial_marking, final_marking, utils.SKIP,
            trace_net_costs, model_cost_function, revised_sync)

    max_align_time_trace = exec_utils.get_param_value(Parameters.PARAM_MAX_ALIGN_TIME_TRACE, parameters,
                                                      sys.maxsize)

    alignment = apply_sync_prod(sync_prod, sync_initial_marking, sync_final_marking, cost_function,
                                utils.SKIP, ret_tuple_as_trans_desc=ret_tuple_as_trans_desc,
                                max_align_time_trace=max_align_time_trace)

    return_sync_cost = exec_utils.get_param_value(Parameters.RETURN_SYNC_COST_FUNCTION, parameters, False)
    if return_sync_cost:
        # needed for the decomposed alignments (switching them from state_equation_less_memory)
        return alignment, cost_function

    return alignment


def apply_sync_prod(sync_prod, initial_marking, final_marking, cost_function, skip, ret_tuple_as_trans_desc=False,
                    max_align_time_trace=sys.maxsize):
    """
    Performs the basic alignment search on top of the synchronous product net, given a cost function and skip-symbol

    Parameters
    ----------
    sync_prod: :class:`pm4py.objects.petri.net.PetriNet` synchronous product net
    initial_marking: :class:`pm4py.objects.petri.net.Marking` initial marking in the synchronous product net
    final_marking: :class:`pm4py.objects.petri.net.Marking` final marking in the synchronous product net
    cost_function: :class:`dict` cost function mapping transitions to the synchronous product net
    skip: :class:`Any` symbol to use for skips in the alignment

    Returns
    -------
    dictionary : :class:`dict` with keys **alignment**, **cost**, **visited_states**, **queued_states**
    and **traversed_arcs**
    """
    return __search(sync_prod, initial_marking, final_marking, cost_function, skip,
                    ret_tuple_as_trans_desc=ret_tuple_as_trans_desc, max_align_time_trace=max_align_time_trace)


def __search(sync_net, ini, fin, cost_function, skip, ret_tuple_as_trans_desc=False,
             max_align_time_trace=sys.maxsize):
    start_time = time.time()

    decorate_transitions_prepostset(sync_net)
    decorate_places_preset_trans(sync_net)

    a_matrix, g_matrix, h_cvx, cost_vec, incidence_matrix, fin_vec, trace_net_filter, model_filter = __compute_heuristic_matrices(
        sync_net, ini, fin, cost_function)

    final_place_trace_net = None

    for final_place in fin:
        if __place_from_spn_belongs_to_trace_net_part(final_place):
            final_place_trace_net = final_place

    assert final_place_trace_net is not None

    closed = set()

    h, x = __compute_exact_heuristic_new_version(sync_net, a_matrix, h_cvx, g_matrix, cost_vec, incidence_matrix,
                                                 ini, fin_vec, trace_net_filter, model_filter)
    ini_state = utils.SearchTuple(0 + h, 0, h, ini, None, None, x, True)
    open_set = [ini_state]
    heapq.heapify(open_set)
    visited = 0
    queued = 0
    traversed = 0
    lp_solved = 1

    trans_empty_preset = set(t for t in sync_net.transitions if len(t.in_arcs) == 0)

    while not len(open_set) == 0:
        if (time.time() - start_time) > max_align_time_trace:
            return None

        curr = heapq.heappop(open_set)

        current_marking = curr.m

        while not curr.trust:
            if (time.time() - start_time) > max_align_time_trace:
                return None

            already_closed = current_marking in closed
            if already_closed:
                curr = heapq.heappop(open_set)
                current_marking = curr.m
                continue

            h, x = __compute_exact_heuristic_new_version(sync_net, a_matrix, h_cvx, g_matrix, cost_vec,
                                                         incidence_matrix, current_marking, fin_vec, trace_net_filter,
                                                         model_filter)
            lp_solved += 1

            # 11/10/19: shall not a state for which we compute the exact heuristics be
            # by nature a trusted solution?
            tp = utils.SearchTuple(curr.g + h, curr.g, h, curr.m, curr.p, curr.t, x, True)
            # 11/10/2019 (optimization ZA) heappushpop is slightly more efficient than pushing
            # and popping separately
            curr = heapq.heappushpop(open_set, tp)
            current_marking = curr.m

        # max allowed heuristics value (27/10/2019, due to the numerical instability of some of our solvers)
        if curr.h > lp_solver.MAX_ALLOWED_HEURISTICS:
            continue

        # 12/10/2019: do it again, since the marking could be changed
        already_closed = current_marking in closed
        if already_closed:
            continue

        # 12/10/2019: the current marking can be equal to the final marking only if the heuristics
        # (underestimation of the remaining cost) is 0. Low-hanging fruits
        if curr.h < 0.01:
            if final_place_trace_net in current_marking:
                return utils.__reconstruct_alignment(curr, visited, queued, traversed,
                                                     ret_tuple_as_trans_desc=ret_tuple_as_trans_desc,
                                                     lp_solved=lp_solved)

        closed.add(current_marking)
        visited += 1

        enabled_trans = copy(trans_empty_preset)
        for p in current_marking:
            for t in p.ass_trans:
                if t.sub_marking <= current_marking:
                    enabled_trans.add(t)

        trans_to_visit_with_cost = [(t, cost_function[t]) for t in enabled_trans if not (
                t is not None and utils.__is_log_move(t, skip) and utils.__is_model_move(t, skip))]

        for t, cost in trans_to_visit_with_cost:
            traversed += 1
            new_marking = utils.add_markings(current_marking, t.add_marking)

            if new_marking in closed:
                continue
            g = curr.g + cost

            queued += 1
            h, x = __derive_heuristic(incidence_matrix, cost_vec, curr.x, t, curr.h)
            trustable = utils.__trust_solution(x)

            new_f = g + h
            tp = utils.SearchTuple(new_f, g, h, new_marking, curr, t, x, trustable)
            heapq.heappush(open_set, tp)


def __compute_heuristic_matrices(sync_net, ini, fin, cost_function):
    incidence_matrix = inc_mat_construct(sync_net)
    ini_vec, fin_vec, cost_vec = utils.__vectorize_initial_final_cost(incidence_matrix, ini, fin, cost_function)

    a_matrix = np.asmatrix(incidence_matrix.a_matrix).astype(np.float64)
    g_matrix = -np.eye(len(sync_net.transitions))
    cost_vec = [x * 1.0 for x in cost_vec]

    trace_net_filter = []
    model_filter = []
    for place in sync_net.places:
        if __place_from_spn_belongs_to_trace_net_part(place):
            trace_net_filter.append(incidence_matrix.places[place])
        else:
            model_filter.append(incidence_matrix.places[place])

    # Ax = b constraints only for the trace net part, we do not care if the model part reaches its final marking
    a_matrix_new = a_matrix[trace_net_filter]
    # Ax <= b constraints for the model part. Because we have marking[model_filter] + incidence[model_filter] * x >= 0
    # (see paper on prefix alignments), we have to multiply with -1 to get the constraint
    # -incidence[model_filter] * x <= marking[model_filter]
    g_matrix = np.vstack([g_matrix, -a_matrix[model_filter]])
    # note that we do not add the b part of the Ax <= b constraints for the model part here. We have to do this for
    # each marking because the b part is marking[model_filter]. See function __compute_exact_heuristic_new_version.
    h_cvx = np.asmatrix(np.zeros(len(sync_net.transitions))).transpose()

    if lp_solver.CVXOPT in lp_solver.DEFAULT_LP_SOLVER_VARIANT:
        from cvxopt import matrix
        a_matrix_new = matrix(a_matrix_new)
        g_matrix = matrix(g_matrix)
        h_cvx = matrix(h_cvx)
        cost_vec = matrix(cost_vec)

    return a_matrix_new, g_matrix, h_cvx, cost_vec, incidence_matrix, fin_vec, trace_net_filter, model_filter


def __compute_exact_heuristic_new_version(sync_net, a_matrix, h_cvx, g_matrix, cost_vec, incidence_matrix,
                                          marking, fin_vec, trace_net_filter, model_filter):
    m_vec = incidence_matrix.encode_marking(marking)
    b_term = [i - j for i, j in zip(fin_vec, m_vec)]
    b_term = np.asmatrix([x * 1.0 for x in b_term]).transpose()
    m_vec = np.asmatrix([x * 1.0 for x in m_vec]).transpose()

    h_cvx = np.vstack([h_cvx, m_vec[model_filter]])
    b_term = b_term[trace_net_filter]

    if lp_solver.CVXOPT in lp_solver.DEFAULT_LP_SOLVER_VARIANT:
        from cvxopt import matrix
        b_term = matrix(b_term)
        h_cvx = matrix(h_cvx)

    parameters_solving = {"solver": "glpk"}

    sol = lp_solver.apply(cost_vec, g_matrix, h_cvx, a_matrix, b_term, parameters=parameters_solving,
                          variant=lp_solver.DEFAULT_LP_SOLVER_VARIANT)
    prim_obj = lp_solver.get_prim_obj_from_sol(sol, variant=lp_solver.DEFAULT_LP_SOLVER_VARIANT)
    points = lp_solver.get_points_from_sol(sol, variant=lp_solver.DEFAULT_LP_SOLVER_VARIANT)

    prim_obj = prim_obj if prim_obj is not None else sys.maxsize
    points = points if points is not None else [0.0] * len(sync_net.transitions)

    return prim_obj, points


def __compute_heuristic_regular_cost(sync_net, current_marking, final_marking, costs):
    start_time = time.time()
    solver = pywraplp.Solver('LP', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    variables = {}
    constraints = []
    for t in sync_net.transitions:
        if costs[t] < math.inf:
            # only create variables that have finite cost/ probability > 0
            variables[t] = solver.NumVar(0, solver.infinity(), str(t.name))
    # calculate current number of tokens in the process net part of the synchronous product net
    number_tokens_in_process_net_part = 0
    for p in current_marking:
        if p.name[0] == utils.SKIP:
            number_tokens_in_process_net_part += current_marking[p]

    # constraint that enforces that at least one token is in the process net part of the synchronous product net
    # example: 1 <= var1 * coefficient1 + var2 * coefficient2 + ... + constant
    # rewrite to -->  1 - constant <= var1 * coefficient1 + var2 * coefficient2 + ...
    lb = 1 - number_tokens_in_process_net_part
    constraint_one_token_in_process_net_part = solver.Constraint(lb, solver.infinity())
    # store coefficients for each variable here because when calling constraint.SetCoefficient multiple times for the
    # same variable it overwrites always the last value for the given variable, i.e. it is NOT possible to model the
    # following constraint: x >= x1 + x2 -x1 with:
    # c.SetCoefficient(x1 , 1)
    # c.SetCoefficient(x2 , 1)
    # c.SetCoefficient(x1 , -1) --> overwrites the previous coefficient of x1
    constraint_one_token_in_process_net_part_coefficients = {}
    for v in variables:
        constraint_one_token_in_process_net_part_coefficients[v] = 0

    # define constraints
    for p in sync_net.places:
        arcs_to_transitions = []  # list of all transitions that have an incoming arc from the current place
        arcs_from_transitions = []  # list of all transitions that have an arc pointing to the current place

        for out_arc in p.out_arcs:
            arcs_to_transitions.append(out_arc.target)

        for in_arc in p.in_arcs:
            arcs_from_transitions.append(in_arc.source)

        if p.name[1] == utils.SKIP:
            # place belongs to the trace net part
            lb_and_ub = final_marking[p] - current_marking[p]
            c = solver.Constraint(lb_and_ub, lb_and_ub)
        else:
            # place belongs to the process net part
            # enforce that the constraint is greater or equal 0, i.e.,
            # constraint + constant >= 0  -->  constraint >= 0 - constant
            c = solver.Constraint(0 - current_marking[p], solver.infinity())

            for t in arcs_to_transitions:
                if t in variables:
                    constraint_one_token_in_process_net_part_coefficients[t] -= 1

            for t in arcs_from_transitions:
                if t in variables:
                    constraint_one_token_in_process_net_part_coefficients[t] += 1

        for t in arcs_to_transitions:
            if t in variables:
                c.SetCoefficient(variables[t], -1)
        for t in arcs_from_transitions:
            if t in variables:
                c.SetCoefficient(variables[t], 1)
        constraints.append(c)
    # build constraint that enforces at least one token in the process net part
    for v in variables:
        constraint_one_token_in_process_net_part.SetCoefficient(variables[v],
                                                                constraint_one_token_in_process_net_part_coefficients[v]
                                                                )
    objective = solver.Objective()
    for v in variables:
        objective.SetCoefficient(variables[v], costs[v])
    objective.SetMinimization()
    solver.Solve()
    # debugging
    # print('Number of variables =', solver.NumVariables())
    # print('Number of constraints =', solver.NumConstraints())
    # print('Solution:')
    # for v in variables:
    #     print(str(v.name) + ":" + str(variables[v].solution_value()))
    lp_solution = 0
    res_vector = {}
    for v in variables:
        lp_solution += variables[v].solution_value() * costs[v]
        res_vector[v] = variables[v].solution_value()
    duration = time.time() - start_time
    return lp_solution, res_vector, duration


def __derive_heuristic(incidence_matrix, cost_vec, x, t, h):
    x_prime = x.copy()
    x_prime[incidence_matrix.transitions[t]] -= 1
    return max(0, h - cost_vec[incidence_matrix.transitions[t]]), x_prime


def __place_from_spn_belongs_to_trace_net_part(place):
    return place.name[1] == utils.SKIP
