import collections
import copy
import sys
import uuid
import time
from itertools import product
from typing import Tuple, List, Set, Dict, Optional

from pm4py.objects.log.obj import Trace
from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util import typing as pm4py_typing
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.objects.conversion.process_tree import converter as pt_converter

from cortado_core.process_tree_utils.miscellaneous import is_leaf_node, get_pt_node_height
from cortado_core.alignments.prefix_alignments import algorithm as prefix_alignments
from cortado_core.alignments.infix_alignments import utils as infix_utils
from cortado_core.process_tree_utils.miscellaneous import is_tau_leaf
from cortado_core.alignments.infix_alignments.utils import generate_reachable_markings


def calculate_optimal_infix_alignment(trace: Trace, process_tree: ProcessTree, naive: bool = True,
                                      use_dijkstra: bool = False, enforce_first_tau_move=False,
                                      timeout: int = sys.maxsize) -> pm4py_typing.AlignmentResult:
    process_tree = copy.deepcopy(process_tree)

    start = time.time()

    try:
        # reduce the tree always for the not naive approach
        net, im, fm, n_added_tau_transitions = build_extended_petri_net_for_infix_alignments(trace, process_tree,
                                                                                             naive,
                                                                                             reduce_tree=not naive,
                                                                                             use_for_suffix_alignments=False,
                                                                                             timeout=timeout)
    except TimeoutError:
        return {'timeout': True}

    preprocessing_duration = time.time() - start
    timeout = timeout - preprocessing_duration

    prefix_alignment_variant = __get_prefix_alignment_variant(use_dijkstra)
    align_start = time.time()
    alignment = prefix_alignments.apply_trace(trace, net, im, fm, variant=prefix_alignment_variant,
                                              parameters={
                                                  prefix_alignments.Parameters.PARAM_MAX_ALIGN_TIME_TRACE: timeout,
                                                  prefix_alignments.Parameters.PARAM_ENFORCE_FIRST_TAU_MOVE: enforce_first_tau_move,
                                              })
    if alignment is None:
        alignment = {'timeout': True}
        return alignment

    alignment = infix_utils.remove_first_tau_move_from_alignment(alignment)

    alignment['alignment_duration'] = time.time() - align_start
    alignment['preprocessing_duration'] = preprocessing_duration
    alignment['added_tau_transitions'] = n_added_tau_transitions

    return alignment


def __get_prefix_alignment_variant(use_dijkstra: bool):
    if use_dijkstra:
        return prefix_alignments.VERSION_DIJKSTRA_NO_HEURISTICS
    return prefix_alignments.VERSION_A_STAR


def build_extended_petri_net_for_infix_alignments(trace: Trace, process_tree: ProcessTree, naive: bool,
                                                  reduce_tree: bool, use_for_suffix_alignments: bool, timeout: int) -> \
        Tuple[
            PetriNet, Marking, Marking, int]:
    all_leaf_nodes = search_leaf_nodes_in_tree(process_tree)
    trace_activities = set([e['concept:name'] for e in trace])
    matching_leaf_nodes = get_matching_leaf_nodes(trace_activities, all_leaf_nodes)

    if len(matching_leaf_nodes) > 0 and reduce_tree:
        process_tree = reduce_process_tree(matching_leaf_nodes)

    renaming_func = __rename_duplicate_labels(all_leaf_nodes)
    renaming_func = __rename_tau_leaves(all_leaf_nodes, renaming_func)

    net, im, fm = pt_converter.apply(process_tree)
    new_im, start_place = infix_utils.add_new_initial_place(net)
    n_added_tau_transitions = __add_infix_alignment_transitions(net, matching_leaf_nodes, all_leaf_nodes, start_place,
                                                                fm, naive, use_for_suffix_alignments, timeout)

    __revert_renaming(net, renaming_func)

    return net, new_im, fm, n_added_tau_transitions


def __add_tau_transition_from_new_initial_to_final_place(fm: Marking, net: PetriNet, start_place: PetriNet.Place):
    new_transition = PetriNet.Transition(str(uuid.uuid4()))
    net.transitions.add(new_transition)
    petri_utils.add_arc_from_to(start_place, new_transition, net)
    petri_utils.add_arc_from_to(new_transition, list(fm.keys())[0], net)

    return net


def __add_infix_alignment_transitions(net: PetriNet, matching_leaf_nodes: List[ProcessTree],
                                      all_leaf_nodes: List[ProcessTree], initial_place: PetriNet.Place, fm: Marking,
                                      naive: bool, use_for_suffix_alignments: False, timeout: int):
    matching_leaf_nodes_labels = set([n.label for n in matching_leaf_nodes])
    markings = __generate_markings(matching_leaf_nodes, matching_leaf_nodes_labels, naive, timeout)

    if use_for_suffix_alignments or len(markings) == 0:
        # For suffix alignments, we always need the option to directly start with the final marking.
        # Same holds for infix alignments if we have no generated markings because this results in disconnected parts
        # of the net. This is especially a problem for the variant that enforces a tau-move in the first place.
        net = __add_tau_transition_from_new_initial_to_final_place(fm, net, initial_place)

    pre_sets, post_sets = __generate_pre_post_sets(all_leaf_nodes, net)

    already_marked = set()
    for marking in markings:
        petri_marking = set()

        for label, should_mark_preset in marking:
            if should_mark_preset:
                to = pre_sets[label]
            else:
                to = post_sets[label]

            petri_marking = petri_marking.union(to)

        if frozenset(petri_marking) in already_marked:
            continue

        already_marked.add(frozenset(petri_marking))

        new_transition = PetriNet.Transition(str(uuid.uuid4()))
        net.transitions.add(new_transition)
        petri_utils.add_arc_from_to(initial_place, new_transition, net)
        for p in petri_marking:
            petri_utils.add_arc_from_to(new_transition, p, net)

    return len(already_marked)


def __generate_pre_post_sets(leaf_nodes: List[ProcessTree], net: PetriNet):
    post_sets = dict()
    pre_sets = dict()

    for leaf_node in leaf_nodes:
        label = leaf_node.label
        transition, match_found = __get_first_matching_transition_from_net(net, label)
        # can happen if we previously reduced the process tree
        if not match_found:
            continue
        post_sets[label] = petri_utils.post_set(transition)
        pre_sets[label] = petri_utils.pre_set(transition)

    return pre_sets, post_sets


def __get_first_matching_transition_from_net(net: PetriNet, label: str) -> Tuple[PetriNet.Transition, bool]:
    for transition in net.transitions:
        if transition.label == label:
            return transition, True

    return PetriNet.Transition('no matching transition found'), False


def __generate_markings(leaf_nodes: List[ProcessTree], trace_activities: Set[str], naive: bool, timeout: int) -> \
        Set[Tuple[Tuple[str, bool]]]:
    # One marking is a set of (label in tree, bool), which indicates that the places in the preset (bool=True) or in the
    # postset (bool=False) should be marked. Note that the label is always unique because of the previous renaming.
    # For example: {("a", True), ("b", False)} indicates that the preset of activity "a" and
    # the postset of activity "b" should be marked.
    markings = set()
    marking_cache = dict()
    start = time.time()

    for leaf_node in leaf_nodes:
        if time.time() - start >= timeout:
            raise TimeoutError()

        last_child = leaf_node
        parent = leaf_node.parent
        markings_for_leaf = {(leaf_node.label, True)}

        while parent:
            # if we visit a PARALLEL node on our way to the root of the tree, we calculate the necessary markings for
            # all the children of the particular PARALLEL node.
            if parent.operator == Operator.PARALLEL:
                for child in parent.children:
                    if id(child) == id(last_child):
                        continue

                    m = __generate_markings_for_subtree(child, trace_activities, naive, True, marking_cache)

                    # For parallel operators, build the cross product of the discovered subtree markings.
                    markings_for_leaf = set(product(markings_for_leaf, m))

            last_child = parent
            parent = parent.parent

        markings_for_leaf = set([frozenset(__flatten(m)) for m in markings_for_leaf])
        markings = markings.union(markings_for_leaf)

    return markings


def __flatten(marking):
    if type(marking[0]) is not tuple:
        return {marking}

    results = set()

    for m in marking:
        if type(m[0]) is tuple:
            results = results.union(__flatten(m))
        else:
            results.add(m)
    return results


def __generate_markings_for_subtree(tree: ProcessTree, trace_activities: Set[str], naive: bool,
                                    is_on_parallel_branch_closing_path: bool, marking_cache: Dict):
    if is_leaf_node(tree):
        markings = set()

        # When using the naive approach, we mark all the presets of leaf nodes in the Petri Net.
        # When using the advanced approach, we only mark the presets of activities that are present in the trace.
        # This advanced approach is only possible because we always add a marking of the postset of the last
        # activity in a parallel branch.
        if naive or (tree.label in trace_activities):
            markings.add((tree.label, True))

        if is_on_parallel_branch_closing_path:
            markings.add((tree.label, False))

        return markings
    else:
        if tree in marking_cache:
            return marking_cache[tree]

        child_markings = []
        for child in tree.children:
            child_stays_parallel_branch_closing_path = is_on_parallel_branch_closing_path
            if is_on_parallel_branch_closing_path or tree.operator == Operator.PARALLEL:
                child_stays_parallel_branch_closing_path = __stays_on_parallel_branch_closing_path(child)

            child_markings.append(
                __generate_markings_for_subtree(child, trace_activities, naive,
                                                child_stays_parallel_branch_closing_path, marking_cache))

        join_func = lambda a, b: a.union(b)
        if tree.operator == Operator.PARALLEL:
            join_func = lambda a, b: set(product(a, b))

        markings = child_markings[0]

        for child_marking in child_markings[1:]:
            markings = join_func(markings, child_marking)

        marking_cache[tree] = markings

        return markings


def __stays_on_parallel_branch_closing_path(node: ProcessTree) -> bool:
    parent = node.parent

    # LOOP branches always end with the DO part, for XOR branches we can freely choose one child to stay on the
    # parallel branch closing path.
    if parent.operator == Operator.LOOP or parent.operator == Operator.XOR:
        return id(parent.children[0]) == id(node)

    # SEQUENCE branches always end with the last activity in the sequence
    if parent.operator == Operator.SEQUENCE:
        return id(parent.children[-1]) == id(node)

    # For PARALLEL branches, each one has its own end
    if parent.operator == Operator.PARALLEL:
        return True

    raise Exception('Unknown operator is used')


def reduce_process_tree(leaf_nodes: List[ProcessTree]) -> ProcessTree:
    lca, matching_lca_children_ids = __get_lca(leaf_nodes)
    reduced_tree = __get_parent_loop_node_if_present(lca)
    reduced_tree.parent = None

    return __reduce_not_matching_root_children(reduced_tree, matching_lca_children_ids)


def __reduce_not_matching_root_children(tree: ProcessTree, matching_lca_children_ids: Set[int]) -> ProcessTree:
    root_operator = tree.operator
    if root_operator == Operator.LOOP:
        return tree

    # we can delete all nodes directly under the reduced tree's root that are not on a path from a matching leaf to the root
    if root_operator == Operator.PARALLEL or root_operator == Operator.XOR:
        deletable_children_idx = []
        for i, child in enumerate(tree.children):
            if not id(child) in matching_lca_children_ids:
                deletable_children_idx.append(i)

        for i in sorted(deletable_children_idx, reverse=True):
            del tree.children[i]

        return tree

    # we can delete only nodes directly under the reduced tree's root that are not in between two matching nodes
    # e.g. if b and d are matching leaves, we can delete a and e in ->(a,b,c,d,e) but NOT c
    if root_operator == Operator.SEQUENCE:
        found_first_matching = False
        deletable_children_idx = []
        deletable_nodes_afterwards = []
        for i, child in enumerate(tree.children):
            if id(child) in matching_lca_children_ids:
                found_first_matching = True
                deletable_nodes_afterwards = []
                continue
            if not found_first_matching:
                deletable_children_idx.append(i)
            else:
                deletable_nodes_afterwards.append(i)

        deletable_children_idx = deletable_children_idx + deletable_nodes_afterwards
        for i in sorted(deletable_children_idx, reverse=True):
            del tree.children[i]

    return tree


def __get_lca(leaf_nodes: List[ProcessTree]) -> Tuple[ProcessTree, Set[int]]:
    nodes_for_leaves = [__create_list_of_all_parents(leaf) for leaf in leaf_nodes]
    node_ids_for_leaves: List[Set[int]] = []
    node_id_to_node: Dict[int, ProcessTree] = {}
    for i in range(len(nodes_for_leaves)):
        node_ids = set()
        for node_ids_for_leaf in nodes_for_leaves[i]:
            node_id = id(node_ids_for_leaf)
            node_ids.add(node_id)
            node_id_to_node[node_id] = node_ids_for_leaf

        node_ids_for_leaves.append(node_ids)

    common_node_ids = node_ids_for_leaves[0]
    for node_ids_for_leaf in node_ids_for_leaves[1:]:
        common_node_ids = common_node_ids.intersection(node_ids_for_leaf)

    lca_height = 0
    lca = None

    for common_node_id in common_node_ids:
        height = get_pt_node_height(node_id_to_node[common_node_id])
        if height >= lca_height:
            lca_height = height
            lca = node_id_to_node[common_node_id]

    # children of the lca that also occur in a path from a matching leaf node to the lca
    # for example, if the tree is ->(a,b,c) and the matching leaf nodes are a and b, then matching_lca_children contains
    # id(a) and id(b) but NOT id(c)
    matching_lca_children_ids = set([id(c) for c in lca.children]).intersection(set(node_id_to_node.keys()))

    return lca, matching_lca_children_ids


def __get_parent_loop_node_if_present(process_tree: ProcessTree) -> ProcessTree:
    tree = process_tree
    parent = process_tree.parent

    while parent:
        if parent.operator == Operator.LOOP:
            tree = parent

            # tau redo loop
            redo_children = tree.children[1:]
            for redo_child in redo_children:
                if is_tau_leaf(redo_child):
                    return tree

        parent = parent.parent

    return tree


def __create_list_of_all_parents(pt: ProcessTree) -> List[ProcessTree]:
    ancestors: List[ProcessTree] = [pt]
    parent = pt.parent
    while parent:
        ancestors.append(parent)
        parent = parent.parent
    return ancestors


def __revert_renaming(net: PetriNet, renaming_func: Dict[str, str]):
    for transition in net.transitions:
        if transition.label in renaming_func:
            transition.label = renaming_func[transition.label]


def __rename_duplicate_labels(nodes: List[ProcessTree]) -> Dict[str, Optional[str]]:
    labels = [node.label for node in nodes if node.label is not None]
    duplicates = [item for item, count in collections.Counter(labels).items() if count > 1]
    renaming_func = {}
    for node in nodes:
        if node.label in duplicates:
            unique_label = node.label + str(uuid.uuid4())
            renaming_func[unique_label] = node.label
            node.label = unique_label

    return renaming_func


# Renaming is necessary because the process tree to petri net conversion sometimes removes tau nodes.
# This is a problem if we discovered in the process tree that we have to mark the postset of this tau node.
def __rename_tau_leaves(nodes: List[ProcessTree], renaming_func: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    tau_nodes = [node for node in nodes if node.label is None]
    for node in tau_nodes:
        unique_label = str(uuid.uuid4())
        renaming_func[unique_label] = None
        node.label = unique_label

    return renaming_func


def search_leaf_nodes_in_tree(process_tree: ProcessTree) -> List[ProcessTree]:
    if is_leaf_node(process_tree):
        return [process_tree]
    else:
        leaf_nodes = []
        for child in process_tree.children:
            leaf_nodes = leaf_nodes + search_leaf_nodes_in_tree(child)

        return leaf_nodes


def get_matching_leaf_nodes(trace_activities: Set[str], leaf_nodes: List[ProcessTree]) -> List[ProcessTree]:
    return [node for node in leaf_nodes if (node.label is not None and node.label in trace_activities)]
