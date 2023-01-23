import collections
import copy
import math
import logging
from typing import Dict, List, Tuple, OrderedDict, FrozenSet

from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.process_tree.obj import Operator
from pm4py.objects.log.obj import Trace, Event, EventLog
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignment
from pm4py.algo.conformance.alignments.petri_net.algorithm import Parameters as alignment_param
from pm4py.objects.petri_net.utils import align_utils

from pm4py.objects.conversion.process_tree.converter import apply as pt_to_net

from cortado_core.lca_approach import __find_lowest_common_ancestor
from cortado_core.process_tree_utils.miscellaneous import is_leaf_node, replace_tree_in_children, \
    get_root, pt_dict_key
import pm4py.visualization.process_tree.visualizer as tree_vis

from cortado_core.process_tree_utils.reduction import apply_reduction_rules, remove_operator_node_with_one_or_no_child, \
    general_tau_reduction
from cortado_core.utils.alignment_utils import trace_fits_process_tree


def reinsert_frozen_subtrees(subtrees_to_insert: OrderedDict[str, ProcessTree], pt: ProcessTree,
                             incremental_projected_logs: Dict[FrozenSet[Tuple[ProcessTree, int]], EventLog],
                             original_log: EventLog,
                             incremental_projected_traces: Dict[FrozenSet[Tuple[ProcessTree, int]], Trace],
                             original_trace: Trace,
                             add_missing_frozen_subtrees_at_root_level: bool = False) -> ProcessTree:
    # tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))

    for replacement_label in subtrees_to_insert:
        logging.debug("replacement label", replacement_label)
    # reinsert frozen subtrees in reverse order as when they were replaced
    subtrees_to_insert = collections.OrderedDict(reversed(subtrees_to_insert.items()))
    frozen_subtrees_to_be_inserted: List[Tuple[ProcessTree, int]] = list(
        (v, int(k)) for k, v in subtrees_to_insert.items())

    missing_frozen_trees: List[ProcessTree] = []

    for replacement_label, frozen_subtree in subtrees_to_insert.items():
        frozen_subtrees_to_be_inserted.remove((frozen_subtree, int(replacement_label)))
        projected_log: EventLog
        projected_trace: Trace
        if len(frozen_subtrees_to_be_inserted) > 0:
            projected_log = incremental_projected_logs[frozenset(frozen_subtrees_to_be_inserted)]
            projected_trace = incremental_projected_traces[frozenset(frozen_subtrees_to_be_inserted)]
        else:
            projected_log = original_log
            projected_trace = original_trace

        pt_activated: List[ProcessTree] = __get_leaf_node_by_label(pt, replacement_label + "+ACTIVATED")
        pt_closed: List[ProcessTree] = __get_leaf_node_by_label(pt, replacement_label + "+CLOSED")

        if len(pt_activated) == 0 or len(pt_closed) == 0:
            missing_frozen_trees.append(frozen_subtree)
            continue

        lca_pt_activated = pt_activated[0]
        if len(pt_activated) > 1:
            for i in range(1, len(pt_activated)):
                tree_changed = True
                while tree_changed:
                    res, tree_changed = __find_lowest_common_ancestor(lca_pt_activated, pt_activated[i], True)
                lca_pt_activated = res

        lca_pt_closed = pt_closed[0]
        if len(pt_closed) > 1:
            for i in range(1, len(pt_closed)):
                tree_changed = True
                while tree_changed:
                    res, tree_changed = __find_lowest_common_ancestor(lca_pt_closed, pt_closed[i], True)
                lca_pt_closed = res

        # tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))
        tree_changed = True
        while tree_changed:
            lca, tree_changed = __find_lowest_common_ancestor(lca_pt_activated, lca_pt_closed, True)

        # tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))

        # new strategy since LCA is not always correct

        ################################################

        if lca.operator == Operator.SEQUENCE and len(lca.children) == 2 and lca.children[0] is lca_pt_activated and \
                lca.children[1] is lca_pt_closed and is_leaf_node(lca_pt_closed) and is_leaf_node(lca_pt_activated):
            # standard case ==> replace ->('replacement_label+ACTIVATED', 'replacement_label+CLOSED') by frozen tree
            assert lca.parent
            replace_tree_in_children(lca.parent, lca, subtrees_to_insert[replacement_label])
        else:
            # not enough to simply use the LCA - Idea: start to re-insert the frozen subtree next to the LCA, if it does
            # not work, go up until it fits

            insert_candidate: ProcessTree = lca
            appropriate_insert_position_found: bool = False
            logging.debug("lca", lca)

            while not appropriate_insert_position_found:
                tree_copy_for_assert_statement = copy.deepcopy(pt)
                # non-standard case ==> put subtree to be inserted in parallel next to the remaining tree
                ACTIVATED_execution_numbers = calculate_execution_numbers(insert_candidate,
                                                                          replacement_label + "+ACTIVATED")
                CLOSED_execution_numbers = calculate_execution_numbers(insert_candidate, replacement_label + "+CLOSED")
                intersection = ACTIVATED_execution_numbers.intersection(CLOSED_execution_numbers)

                logging.debug("ACTIVATED_execution_numbers", ACTIVATED_execution_numbers)
                logging.debug("CLOSED_execution_numbers", CLOSED_execution_numbers)
                logging.debug(intersection)

                assert intersection == {0, 1} or intersection == {1} or \
                       intersection == {1, math.inf} or intersection == {0, 1, math.inf}

                inserted_parallel: ProcessTree = None
                if intersection == {1}:
                    inserted_parallel = apply_case_1(insert_candidate, subtrees_to_insert[replacement_label])
                elif intersection == {0, 1}:
                    inserted_parallel = apply_case_0_1(insert_candidate, subtrees_to_insert[replacement_label])
                elif intersection == {1, math.inf}:
                    inserted_parallel = apply_case_1_inf(insert_candidate, subtrees_to_insert[replacement_label])
                elif intersection == {0, 1, math.inf}:
                    inserted_parallel = apply_case_0_1_inf(insert_candidate, subtrees_to_insert[replacement_label])
                assert inserted_parallel is not None

                replaced_leaves: Dict[Tuple[ProcessTree, int], str] = replace_activation_and_closing_by_tau(
                    insert_candidate, replacement_label)

                pt = get_root(pt)

                # check if insert_candidate is suited, i.e., all traces fit
                appropriate_insert_position_found = True
                # tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))
                if trace_fits_process_tree(projected_trace, pt):
                    for trace in projected_log:
                        if not trace_fits_process_tree(trace, pt):
                            appropriate_insert_position_found = False
                else:
                    appropriate_insert_position_found = False

                # undo changes if insert_candidate is not suited
                if not appropriate_insert_position_found:
                    # tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))
                    assert inserted_parallel.parent is not None
                    logging.debug(
                        "LCA is not appropriate to insert the frozen subtree !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    undo_replace_leaves_with_label_by_tau(pt, replaced_leaves)
                    assert inserted_parallel.children[0] == insert_candidate
                    replace_tree_in_children(inserted_parallel.parent, inserted_parallel, insert_candidate)
                    insert_candidate.parent = inserted_parallel.parent
                    del inserted_parallel
                    assert insert_candidate.parent
                    assert tree_copy_for_assert_statement == pt
                    insert_candidate = insert_candidate.parent
                    logging.debug("NEXT iteration")

    frozen_trees: List[ProcessTree] = [subtrees_to_insert[k] for k in subtrees_to_insert]
    pt = post_process_tree(pt, excluded_subtrees=frozen_trees)

    if add_missing_frozen_subtrees_at_root_level and len(missing_frozen_trees) > 0:
        pt = add_missing_frozen_subtrees(pt, missing_frozen_trees)

    # tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))
    logging.debug(pt)
    return pt


def post_process_tree(pt: ProcessTree, excluded_subtrees=[]) -> ProcessTree:
    tree_changed = True
    while tree_changed:
        pt_before_post_process = copy.deepcopy(pt)
        pt = remove_operator_node_with_one_or_no_child(pt, excluded_subtrees=excluded_subtrees)
        pt = general_tau_reduction(pt, excluded_subtrees=excluded_subtrees)
        apply_reduction_rules(pt, excluded_subtrees=excluded_subtrees)
        if pt == pt_before_post_process:
            tree_changed = False
    return get_root(pt)


def add_missing_frozen_subtrees(pt: ProcessTree, missing_frozen_subtrees: List[ProcessTree]) -> ProcessTree:
    new_root_node = ProcessTree(operator=Operator.PARALLEL, children=[pt])
    pt.parent = new_root_node

    for missing_tree in missing_frozen_subtrees:
        inner_xor_node = ProcessTree(parent=new_root_node, operator=Operator.XOR, children=[])
        new_root_node.children.append(inner_xor_node)

        tau_leaf = ProcessTree(parent=inner_xor_node)
        inner_xor_node.children.append(tau_leaf)

        missing_tree.parent = inner_xor_node
        inner_xor_node.children.append(missing_tree)

    return new_root_node


def replace_activation_and_closing_by_tau(tree: ProcessTree, label_to_be_removed: str) -> \
        Dict[Tuple[ProcessTree, int], str]:
    leaves_activated = replace_given_leaf_node_label_by_tau(tree, label_to_be_removed + "+ACTIVATED")
    leaves_closed = replace_given_leaf_node_label_by_tau(tree, label_to_be_removed + "+CLOSED")
    return {**leaves_activated, **leaves_closed}


def apply_case_1(lca: ProcessTree, frozen: ProcessTree) -> ProcessTree:
    parallel = ProcessTree(operator=Operator.PARALLEL, parent=lca.parent, children=[lca, frozen])
    if lca.parent:
        replace_tree_in_children(lca.parent, lca, parallel)
    lca.parent = parallel
    frozen.parent = parallel
    return parallel


def apply_case_0_1(lca: ProcessTree, frozen: ProcessTree) -> ProcessTree:
    tau = ProcessTree()
    choice = ProcessTree(operator=Operator.XOR, children=[frozen, tau])
    tau.parent = choice
    frozen.parent = choice
    parallel = ProcessTree(operator=Operator.PARALLEL, parent=lca.parent, children=[lca, choice])
    choice.parent = parallel
    if lca.parent:
        replace_tree_in_children(lca.parent, lca, parallel)
    lca.parent = parallel
    return parallel


def apply_case_1_inf(lca: ProcessTree, frozen: ProcessTree) -> ProcessTree:
    tau = ProcessTree()
    loop = ProcessTree(operator=Operator.LOOP, children=[frozen, tau])
    tau.parent = loop
    frozen.parent = loop
    parallel = ProcessTree(operator=Operator.PARALLEL, parent=lca.parent, children=[lca, loop])
    loop.parent = parallel
    if lca.parent:
        replace_tree_in_children(lca.parent, lca, parallel)
    lca.parent = parallel
    return parallel


def apply_case_0_1_inf(lca: ProcessTree, frozen: ProcessTree) -> ProcessTree:
    tau = ProcessTree()
    loop = ProcessTree(operator=Operator.LOOP, children=[tau, frozen])
    tau.parent = loop
    frozen.parent = loop
    parallel = ProcessTree(operator=Operator.PARALLEL, parent=lca.parent, children=[lca, loop])
    loop.parent = parallel
    if lca.parent:
        replace_tree_in_children(lca.parent, lca, parallel)
    lca.parent = parallel
    return parallel


def calculate_execution_numbers(tree: ProcessTree, label: str) -> set:
    res = set()
    if activity_zero_times_replayable(tree, label):
        res.add(0)
    if activity_one_times_replayable(tree, label):
        res.add(1)
        if activity_multiple_times_replayable(tree, label):
            res.add(math.inf)
    return res


def activity_zero_times_replayable(tree: ProcessTree, label: str) -> bool:
    # idea: align empty trace and give high model move costs for transitions with given label --> force alignment to
    # not take these transitions
    trace = Trace()
    net, im, fm = pt_to_net(tree)
    # define alternative cost function
    trace_log_moves_cost = []
    sync_cost = {t: align_utils.STD_SYNC_COST for t in net.transitions}
    model_cost = {}
    M = align_utils.STD_MODEL_LOG_MOVE_COST * 10000
    for t in net.transitions:
        if t.label is not None and not t.label == label:
            model_cost[t] = align_utils.STD_MODEL_LOG_MOVE_COST
        elif t.label is not None and t.label == label:
            # try to avoid these transitions by assigning very high cost
            model_cost[t] = M
        else:
            assert t.label is None
            model_cost[t] = align_utils.STD_TAU_COST
    param = {
        alignment_param.PARAM_SYNC_COST_FUNCTION: sync_cost,
        alignment_param.PARAM_MODEL_COST_FUNCTION: model_cost,
        alignment_param.PARAM_TRACE_COST_FUNCTION: trace_log_moves_cost
    }
    a = calculate_alignment(trace, net, im, fm, parameters=param)
    if a["cost"] >= M:
        # transitions with
        return False
    else:
        return True


def activity_one_times_replayable(tree: ProcessTree, label: str) -> bool:
    t = Trace()
    e = Event()
    e["concept:name"] = label
    t.append(e)
    net, im, fm = pt_to_net(tree)
    M = align_utils.STD_MODEL_LOG_MOVE_COST * 10000
    trace_log_moves_cost = [M]
    sync_cost = {t: align_utils.STD_SYNC_COST for t in net.transitions}
    model_cost = {t: align_utils.STD_MODEL_LOG_MOVE_COST for t in net.transitions}
    for transition in net.transitions:
        if transition.label is not None:
            model_cost[transition] = align_utils.STD_MODEL_LOG_MOVE_COST
        else:
            assert transition.label is None
            model_cost[transition] = align_utils.STD_TAU_COST
    param = {
        alignment_param.PARAM_SYNC_COST_FUNCTION: sync_cost,
        alignment_param.PARAM_MODEL_COST_FUNCTION: model_cost,
        alignment_param.PARAM_TRACE_COST_FUNCTION: trace_log_moves_cost
    }
    a = calculate_alignment(t, net, im, fm, parameters=param)
    for move in a["alignment"]:
        if move[0] == move[1]:
            # found sync move
            return True
    return False


def activity_multiple_times_replayable(tree: ProcessTree, label: str) -> bool:
    trace = Trace()
    for i in range(2):
        e = Event()
        e["concept:name"] = label
        trace.append(e)
    assert len(trace) == 2
    net, im, fm = pt_to_net(tree)
    M = align_utils.STD_MODEL_LOG_MOVE_COST * 10000
    trace_log_moves_cost = [M] * len(trace)
    sync_cost = {t: align_utils.STD_SYNC_COST for t in net.transitions}
    model_cost = {}
    for t in net.transitions:
        model_cost[t] = align_utils.STD_MODEL_LOG_MOVE_COST
    param = {
        alignment_param.PARAM_SYNC_COST_FUNCTION: sync_cost,
        alignment_param.PARAM_MODEL_COST_FUNCTION: model_cost,
        alignment_param.PARAM_TRACE_COST_FUNCTION: trace_log_moves_cost
    }
    a = calculate_alignment(trace, net, im, fm, parameters=param)
    number_sync_moves = 0
    for move in a["alignment"]:
        if move[0] == move[1]:
            number_sync_moves += 1
    assert number_sync_moves <= 2
    if number_sync_moves == 2:
        # we can replay the activity at least twice
        return True
    else:
        return False


def __get_leaf_node_by_label(tree: ProcessTree, label: str, res: List[ProcessTree] = None) -> List[ProcessTree]:
    if res is None:
        res = []
    if tree.label == label:
        assert is_leaf_node(tree)
        res.append(tree)
    elif tree.children:
        for c in tree.children:
            __get_leaf_node_by_label(c, label, res)
    return res


def replace_given_leaf_node_label_by_tau(pt: ProcessTree, label: str, replacement_log=None) -> \
        Dict[Tuple[ProcessTree, int], str]:
    if replacement_log is None:
        replacement_log = {}
    if pt.label and pt.label == label:
        replacement_log[pt_dict_key(pt)] = label
        assert len(pt.children) == 0 and pt.operator is None
        pt.label = None
        return replacement_log
    elif pt.children:
        for c in pt.children:
            replacement_log = replace_given_leaf_node_label_by_tau(c, label, replacement_log)
    return replacement_log


def undo_replace_leaves_with_label_by_tau(pt: ProcessTree, replacement_log: Dict[Tuple[ProcessTree, int], str]):
    for k, v in replacement_log.items():
        tree = k[0]
        original_label = v
        tree.label = original_label


def cardinality_test():
    t = pt_parse(
        "->( +( X( tau, 'Insert Date Appeal to Prefecture' ), X( tau, +( 'Insert Fine Notification', '2191926628512+ACTIVATED' ) ) ), *( X( 'Appeal to Judge', ->( X( tau, '2191926628512+CLOSED', 'Receive Result Appeal from Prefecture' ), X( tau, 'Notify Result Appeal to Offender' ), X( tau, 'Send for Credit Collection' ), X( tau, 'Send Appeal to Prefecture' ) ) ), tau ) )")
    tree_vis.view(tree_vis.apply(t, parameters={format: "svg"}))
    c = calculate_execution_numbers(t, "2191926628512+ACTIVATED")
    print(c)


if __name__ == "__main__":
    cardinality_test()

    # pt_1 = pt_parse("-> (*(X(->('A','A','X'),->('C','D')),tau) ,->('E',->('A','F')) )")
    # # pt_2 = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    # pt_3 = pt_parse("X ('E','F') )")
    pt_4 = pt_parse("->('Y','Z')")
    #
    # res = __get_leaf_node_by_label(pt_1, 'F')
    # print(res)
    #
    # print("\nReplace X by ->('Y','Z')")
    # pt_5 = pt_parse("+( ->('X+ACTIVATED',X('b',tau),'X+CLOSED'),->('c','d'))")
    # print("Input tree:\n", pt_5)
    # print("\nReplace X by:")
    # print(pt_4)
    # reinsert_frozen_subtrees({'X': pt_4}, pt_5)
    # print("\nResult")
    # print(pt_5)

    pt_6 = pt_parse(
        "->( +( 'Create Fine', ->( '1990281212736+ACTIVATED', '1990281212736+CLOSED' ), ->( X( τ ), +( X( τ, 'Send Appeal to Prefecture' ), ->( +( X( τ, 'Insert Fine Notification' ), X( τ ), ->( X( τ, +( 'Send Fine', X( τ, *( X( ->( X( τ, '1990281212736+ACTIVATED' ), X( τ, 'Send Appeal to Prefecture' ), 'Receive Result Appeal from Prefecture', X( τ, 'Appeal to Judge' ), X( τ, 'Notify Result Appeal to Offender' ) ), 'Insert Date Appeal to Prefecture', 'Appeal to Judge' ), τ ) ) ) ), X( τ, 'Payment' ) ) ), X( τ, 'Send for Credit Collection' ) ) ) ) ), X( τ, 'Send for Credit Collection' ) )")
    tree_vis.view(tree_vis.apply(pt_6, parameters={"format": "svg"}))

    print(activity_zero_times_replayable(pt_6, "1990281212736+ACTIVATED"))
    print(activity_one_times_replayable(pt_6, "1990281212736+ACTIVATED"))
    print(activity_multiple_times_replayable(pt_6, "1990281212736+ACTIVATED"))

    print(activity_zero_times_replayable(pt_6, "1990281212736+CLOSED"))
    print(activity_one_times_replayable(pt_6, "1990281212736+CLOSED"))
    print(activity_multiple_times_replayable(pt_6, "1990281212736+CLOSED"))

    pt_6 = reinsert_frozen_subtrees({'1990281212736': pt_4}, pt_6)
    tree_vis.view(tree_vis.apply(pt_6, parameters={"format": "svg"}))
