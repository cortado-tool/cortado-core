from copy import copy, deepcopy
from datetime import datetime
from typing import List, Tuple, Optional, Dict

from tqdm import tqdm

import pm4py.visualization.process_tree.visualizer as tree_vis
from cortado_core.performance.utils import get_alignment_activities, get_alignment_events, get_alignment_tree_nodes, \
    get_all_indices, get_alignment_tree_lf, get_tree_instances, get_all_nodes
from pm4py.algo.conformance.alignments.petri_net import algorithm as net_alignment
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.objects.log.util.interval_lifecycle import to_lifecycle
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.objects.process_tree.obj import Operator, ProcessTree as CortadoProcessTree
from pm4py.objects.process_tree.utils.generic import is_leaf
from pm4py.util import variants_util
from pm4py.util.variants_util import variant_to_trace
from pm4py.util.xes_constants import DEFAULT_NAME_KEY, DEFAULT_TRANSITION_KEY, DEFAULT_TIMESTAMP_KEY
from pm4py.visualization.petri_net import visualizer as net_visualizer
from .service_time import compute_service_times, compute_idle_times
from .waiting_time import get_enabling_nodes
from ..process_tree_utils import to_petri_net_transition_bordered
from cortado_core.process_tree_utils.miscellaneous import is_tau_leaf


def create_low_level_tree(pt, parent=None, instances={}):
    pt_copy = copy(pt)
    pt_copy.parent = parent

    # Tau transitions
    if is_tau_leaf(pt):
        parent.children.append(pt_copy)
    elif is_leaf(pt):
        pt_sequence = CortadoProcessTree(parent=parent, operator=Operator.SEQUENCE)
        pt_start = CortadoProcessTree(parent=pt_sequence, label=pt.label + "_start")
        pt_complete = CortadoProcessTree(
            parent=pt_sequence, label=pt.label + "_complete")
        pt_sequence._children = [pt_start, pt_complete]

        parent.children.append(pt_sequence)
    else:
        children_copy = copy(pt_copy.children)
        pt_copy.children = []
        for child in children_copy:
            create_low_level_tree(child, parent=pt_copy, instances=instances)

        if parent:
            parent.children.append(pt_copy)

    return pt_copy, instances


class PerformanceMeasures:
    service_times: List[List[Tuple[datetime, datetime]]]
    idle_times: List[List[Tuple[datetime, datetime]]]
    waiting_times: List[Tuple[datetime, datetime]]
    cycle_times: List[Tuple[datetime, datetime]]

    def __init__(self, service_times, waiting_times, cycle_times, idle_times) -> None:
        self.service_times = service_times
        self.waiting_times = waiting_times
        self.cycle_times = cycle_times
        self.idle_times = idle_times


def get_low_level_net(net: PetriNet):
    net = deepcopy(net)
    instances = {}
    transitions = copy(net.transitions)
    for t in transitions:
        # Skip silent transition and subtrees
        if not t.label:
            continue

        tree_node = t.name[0]
        t_start = petri_utils.add_transition(net, t.name, label=t.label + '_start')
        t_complete = petri_utils.add_transition(net, t.name, label=t.label + '_complete')

        instances[tree_node] = (t_start, t_complete)
        instances[t_start] = tree_node
        instances[t_complete] = tree_node

        place = petri_utils.add_place(net, str(t.name) + '_place')

        for in_arc in t.in_arcs:
            petri_utils.add_arc_from_to(in_arc.source, t_start, net)
        for out_arc in t.out_arcs:
            petri_utils.add_arc_from_to(t_complete, out_arc.target, net)

        petri_utils.remove_transition(net, t)
        petri_utils.add_arc_from_to(t_start, place, net)
        petri_utils.add_arc_from_to(place, t_complete, net)

    im = Marking({p: 1 for p in net.places if len(p.in_arcs) == 0})
    fm = Marking({p: 1 for p in net.places if len(p.out_arcs) == 0})

    return net, im, fm, instances


def compute_performances_intervals(tree, log, alignments, selected_tree_nodes=None):
    if selected_tree_nodes is None:
        tree_nodes = get_all_nodes(tree)
    else:
        tree_nodes = selected_tree_nodes

    all_service_times = {t: [None for _ in range(len(log))] for t in tree_nodes}
    all_idle_times = {t: [None for _ in range(len(log))] for t in tree_nodes}
    all_waiting_times = {t: [None for _ in range(len(log))] for t in tree_nodes}
    all_cycle_times = {t: [None for _ in range(len(log))] for t in tree_nodes}

    cache = {}
    for t in tree_nodes:
        # *tau* nodes
        if is_tau_leaf(t):
            continue
        child_nodes = get_all_nodes(t) - {t}
        enabling_nodes = get_enabling_nodes(t)
        for trace_idx, trace in enumerate(log):
            variant = variants_util.get_variant_from_trace(trace)
            trace_alignments = alignments[variant]

            all_service_times[t][trace_idx] = [None for _ in range(len(trace_alignments))]
            all_waiting_times[t][trace_idx] = [None for _ in range(len(trace_alignments))]
            all_idle_times[t][trace_idx] = [None for _ in range(len(trace_alignments))]
            all_cycle_times[t][trace_idx] = [None for _ in range(len(trace_alignments))]

            for alignment_idx, alignment in enumerate(trace_alignments):
                if (trace_idx, alignment_idx) in cache:
                    alignment_tree_nodes, alignment_events, alignment_activities, alignment_active_close \
                        = cache[(trace_idx, alignment_idx)]
                else:
                    alignment_tree_nodes = get_alignment_tree_nodes(alignment)
                    alignment_events = get_alignment_events(alignment, trace)
                    alignment_activities = get_alignment_activities(alignment)
                    alignment_active_close = get_alignment_tree_lf(alignment)
                    cache[(trace_idx, alignment_idx)] \
                        = alignment_tree_nodes, alignment_events, alignment_activities, alignment_active_close

                performance = compute_performance_trace(t, alignment, child_nodes, enabling_nodes,
                                                        alignment_tree_nodes, alignment_events,
                                                        alignment_activities, alignment_active_close)
                all_service_times[t][trace_idx][alignment_idx] = performance.service_times if performance else None
                all_idle_times[t][trace_idx][alignment_idx] = performance.idle_times if performance else None
                all_waiting_times[t][trace_idx][alignment_idx] = performance.waiting_times if performance else None
                all_cycle_times[t][trace_idx][alignment_idx] = performance.cycle_times if performance else None

    return all_service_times, all_idle_times, all_waiting_times, all_cycle_times


def reduce_alignments(alignments):
    reduced_alignments = {}
    for alignment in alignments:
        reduced = tuple(tuple(a) for a in alignment if '>>' not in a[1])
        if reduced not in reduced_alignments:
            reduced_alignments[reduced] = alignment
    return set(reduced_alignments.values())


def compute_performance_trace(tree: CortadoProcessTree, alignment, child_nodes, enabling_nodes,
                              alignment_tree_nodes, alignment_events, alignment_activities,
                              alignment_active_close) -> PerformanceMeasures:
    instances = get_all_indices(alignment_tree_nodes, tree)
    instances = [instances[i:i + 2] for i in range(0, len(instances), 2)]

    if len(instances) == 0:
        return None

    parent_indices = get_all_indices(alignment_tree_nodes, tree.parent)
    parent_active_indices = [i for i in parent_indices if i == -1 or alignment_active_close[i] == 'active']

    enabling_indices = [i for n in enabling_nodes for i in get_all_indices(alignment_tree_nodes, n)]
    enabling_completing_indices = [i for i in enabling_indices if
                                   alignment_activities[i] and 'complete' in alignment_activities[i] or i == -1]

    waiting_times = []
    service_times = []
    cycle_times = []
    idle_times = []

    for self_index_start, self_index_end in instances:
        if len(tree.children) == 0:
            self_start_event = alignment_events[self_index_start]
            self_complete_event = alignment_events[self_index_end]
            service_time_intervals = [[self_start_event[DEFAULT_TIMESTAMP_KEY] if self_start_event else None,
                                       self_complete_event[DEFAULT_TIMESTAMP_KEY] if self_complete_event else None]]
        else:
            # restrict search to range self_start to self_end
            starting_nodes_indices = [i for i in range(self_index_start, self_index_end) if
                                      (bool(alignment_activities[i]) and alignment[i] and 'start' in alignment_activities[i]) and
                                      alignment_tree_nodes[i] in child_nodes]
            if not starting_nodes_indices:
                # only log moves of child nodes
                return None
            self_start_event = min(starting_nodes_indices)
            self_start_event = alignment_events[self_start_event]

            completing_indices = [i for i in range(self_index_start, self_index_end) if
                                  (alignment_activities[i] and 'complete' in alignment_activities[i]) and
                                  alignment_tree_nodes[i] in child_nodes]
            if not completing_indices:
                # only log moves of child nodes
                return None
            self_complete_event = max(completing_indices)
            self_complete_event = alignment_events[self_complete_event]

            activity_instances = get_tree_instances(alignment[self_index_start:self_index_end], nodes=child_nodes)
            activity_instances_events = [
                (alignment_events[self_index_start + ai[0]], alignment_events[self_index_start + ai[1]])
                for ai in activity_instances]
            service_time_intervals = [[ai[0][DEFAULT_TIMESTAMP_KEY] if ai[0] else None,
                                       ai[1][DEFAULT_TIMESTAMP_KEY] if ai[1] else None]
                                      for ai in activity_instances_events]

        service_times.append(compute_service_times(service_time_intervals))
        idle_times.append(compute_idle_times(service_time_intervals))

        if tree.parent and tree.parent.operator == Operator.PARALLEL:
            parent_active_index = max([i for i in parent_active_indices if i < self_index_start])
        else:
            parent_active_index = self_index_start

        candidates = [i for i in enabling_completing_indices if i < parent_active_index]
        if not candidates:
            # Should not happen
            assert False, "no enabling candidates"

        max_enabling = max(candidates)
        # enabled by root
        if max_enabling == -1:
            waiting_times.append((self_start_event[DEFAULT_TIMESTAMP_KEY] if self_start_event else None,
                                  self_start_event[DEFAULT_TIMESTAMP_KEY] if self_start_event else None))
            cycle_times.append([self_start_event[DEFAULT_TIMESTAMP_KEY] if self_start_event else None,
                                self_complete_event[DEFAULT_TIMESTAMP_KEY] if self_complete_event else None])
            continue

        enabling_event = alignment_events[max_enabling]
        waiting_time_interval = (enabling_event[DEFAULT_TIMESTAMP_KEY] if enabling_event else None,
                                 self_start_event[DEFAULT_TIMESTAMP_KEY] if self_start_event else None)
        waiting_times.append(waiting_time_interval)
        cycle_times.append([enabling_event[DEFAULT_TIMESTAMP_KEY] if enabling_event else None,
                            self_complete_event[DEFAULT_TIMESTAMP_KEY] if self_complete_event else None])

    return PerformanceMeasures(service_times=service_times, idle_times=idle_times, waiting_times=waiting_times,
                               cycle_times=cycle_times)


def get_tree_performance_intervals(pt, log, alignment_variant=net_alignment.Variants.VERSION_STATE_EQUATION_A_STAR,
                                   alignment_time_limit=None, alignment_params={}, selected_tree_nodes=None):
    log_lifecycle = to_low_level_log(log)

    alignments, log_lifecycle, mean_fitness = get_all_alignments(pt, log_lifecycle, alignment_variant=alignment_variant,
                                                                 alignment_time_limit=alignment_time_limit,
                                                                 alignment_params=alignment_params)
    performances = compute_performances_intervals(pt, log_lifecycle, alignments, selected_tree_nodes)
    # all_service_times, all_idle_times, all_waiting_times, all_cycle_times
    return performances, mean_fitness


def get_interval_length(interval: Tuple[Optional[datetime], Optional[datetime]], none_to_null=False):
    if None in interval:
        if none_to_null:
            return 0
        else:
            return None
    else:
        if type(interval[1]) == datetime:
            return (interval[1] - interval[0]).total_seconds()
        else:
            return interval[1] - interval[0]


def apply_aggregation(tree_values: Dict, cases_aggregator, alignments_aggregator, instances_aggregator):
    return {t: apply_aggregation_intervals(values, cases_aggregator, alignments_aggregator, instances_aggregator) for
            t, values in tree_values.items()}


def apply_aggregation_intervals(values: List, cases_aggregator, alignments_aggregator, instances_aggregator):
    return cases_aggregator([
        alignments_aggregator(
            [decide_aggregator(instances, instances_aggregator) for instances in alignments])
        for alignments in values if alignments is not None])


def decide_aggregator(instances, aggregator):
    if instances is None:
        return None
    if instances[0] == [] or type(instances[0][0]) == list:
        return apply_multi_interval_aggregation(instances, aggregator)
    else:
        return apply_single_interval_aggregation(instances, aggregator)


def sum_ignore_null(lst):
    # if len(lst) == 0:
    #     return 0
    lst = [x for x in lst if x is not None]
    if not lst:
        return None
    else:
        return sum(lst)


def apply_multi_interval_aggregation(values: List[List[Tuple[datetime, datetime]]], aggregator):
    return aggregator(
        [sum_ignore_null([get_interval_length(interval) for interval in instance]) for instance in values])


def apply_single_interval_aggregation(values: List[Tuple[datetime, datetime]], aggregator):
    return aggregator([get_interval_length(interval) for interval in values])


def to_low_level_log(log):
    log_lifecycle = to_lifecycle(log)
    if '_start' not in log_lifecycle[0][0][DEFAULT_NAME_KEY].lower() and \
            '_complete' not in log_lifecycle[0][0][DEFAULT_NAME_KEY].lower():
        for t in log_lifecycle:
            for e in t:
                e[DEFAULT_NAME_KEY] = e[DEFAULT_NAME_KEY] + '_' + e[DEFAULT_TRANSITION_KEY].lower()
    return log_lifecycle


def get_all_alignments(pt, log_lifecycle, alignment_variant=net_alignment.Variants.VERSION_STATE_EQUATION_A_STAR,
                       alignment_time_limit=None, alignment_params={}):
    net, im, fm = to_petri_net_transition_bordered.apply(pt)
    low_level_net, im, fm, _ = get_low_level_net(net)
    variants = variants_filter.get_variants(log_lifecycle)
    all_alignments = {}
    fitness = 0
    for variant in tqdm(variants):
        v_trace = variant_to_trace(variant)
        if alignment_time_limit is not None:
            alignment_params[net_alignment.Parameters.PARAM_MAX_ALIGN_TIME_TRACE] = alignment_time_limit
        alignment_params[net_alignment.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE] = True
        alignments = net_alignment.apply(v_trace, low_level_net, im, fm, variant=alignment_variant,
                                         parameters=alignment_params)
        if "all_alignments" in alignments:
            # reduced_alignments = reduce_alignments(alignments["all_alignments"])
            all_alignments[variant] = alignments["all_alignments"]
        else:
            all_alignments[variant] = [alignments["alignment"]]
        fitness += alignments["fitness"]
    mean_fitness = fitness / len(variants)
    return all_alignments, log_lifecycle, mean_fitness


def view_tree(pt):
    tree_vis.view(tree_vis.apply(pt, variant=tree_vis.Variants.SYMBOLIC))


def view_net(net):
    net = deepcopy(net)
    for t in net.transitions:
        t.name = str(t.name)
    for t in net.places:
        t.name = str(t.name)
    net_visualizer.view(net_visualizer.apply(net))
