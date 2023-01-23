import multiprocessing.pool
from typing import Dict, List, Tuple, Optional
import logging

import pm4py.visualization.process_tree.visualizer as tree_vis
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignments
from pm4py.algo.conformance.alignments.petri_net.algorithm import variants as variants_calculate_alignments
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.log.obj import EventLog, Event, Trace
from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST
from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.util.typing import AlignmentResult

from cortado_core.naive_approach import repair_first_deviation
from cortado_core.process_tree_utils.reduction import apply_reduction_rules
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import apply as pt_to_petri_net
from cortado_core.process_tree_utils.miscellaneous import get_number_leaves, get_height, get_number_silent_leaves, \
    get_number_nodes, \
    is_leaf_node, get_root, is_subtree, get_index_of_pt_in_children_list
from cortado_core.utils.alignment_utils import is_log_move, is_model_move_on_visible_activity, \
    alignment_step_represents_no_deviation, is_sync_move, alignment_contains_deviation
from cortado_core.utils.parallel_alignments import calculate_alignments_parallel
from cortado_core.utils.visualize_petri_net import visualize_petri_net
from cortado_core.utils.start_and_end_activities import add_artificial_start_and_end_activity_to_Log, \
    add_artificial_start_and_end_activity_to_trace, \
    add_artificial_start_and_end_to_pt, remove_artificial_start_and_end_activity_leaves_from_pt

DEBUG = False


# TODO implement shuffling, switch log move position to find lowest common ancestor

def add_trace_to_pt_language(pt: ProcessTree, log: EventLog, trace: Trace, try_pulling_lca_down=False,
                             add_artificial_start_end=True,
                             pool: Optional[multiprocessing.pool.Pool] = None) -> ProcessTree:
    """
    Checks if a given trace can be replayed on the given process tree. If not, the tree will be altered to accept the
    given trace
    :param sublogs:
    :param try_pulling_lca_down:
    :param add_artificial_start_end:
    :param pt: ProcessTree
    :param log: EventLog accepted by pt
    :param trace: trace that should be accepted by pt in the end
    :return: process tree that accepts the given log and trace
    """
    # print("add_trace_to_pt_language")
    # print("pt:", pt)
    # print("trace:", [a["concept:name"] for a in trace])

    if add_artificial_start_end:
        trace = add_artificial_start_and_end_activity_to_trace(trace, inplace=False)
        pt = add_artificial_start_and_end_to_pt(pt)
        log = add_artificial_start_and_end_activity_to_Log(log, inplace=False)

    deviation = True
    while deviation:
        # print(pt)
        # print(trace)
        if DEBUG:
            tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))
        __set_preorder_ids_in_tree(pt)
        net, im, fm = pt_to_petri_net(pt)
        if DEBUG:
            visualize_petri_net(net)
        alignment = calculate_alignments(trace, net, im, fm, parameters={'ret_tuple_as_trans_desc': True},
                                         variant=variants_calculate_alignments.state_equation_a_star)
        # print(alignment["alignment"])
        # for s, j in enumerate(alignment["alignment"]):
        #     print(s, j)
        # print(alignment["cost"])
        if alignment["cost"] >= STD_MODEL_LOG_MOVE_COST:
            # deviation found
            pt = __repair_process_tree(pt, log, alignment, try_pulling_lca_down, pool)
        else:
            deviation = False

    if add_artificial_start_end:
        pt = remove_artificial_start_and_end_activity_leaves_from_pt(pt)
    else:
        apply_reduction_rules(pt)

    # assert trace_fits_process_tree(trace, pt)
    # for t in log:
    # assert trace_fits_process_tree(t, pt)

    return pt


def __repair_process_tree(pt_root: ProcessTree, log: EventLog, alignment: AlignmentResult,
                          try_pulling_lca_down: bool, pool: Optional[multiprocessing.pool.Pool]) -> ProcessTree:
    logging.debug("repair_process_tree()")

    step, i = __get_first_deviation(alignment)
    if step is None:
        logging.debug("found no deviation")
        return pt_root

    logging.debug("deviation at ", i)
    exec_pt_leave_before_deviation: ProcessTree or None = __get_leaf_before_deviation(alignment, i)
    exec_pt_leave_after_deviation: ProcessTree or None = __get_leaf_after_deviation(alignment, i)

    deviation_is_between_non_deviating_moves = exec_pt_leave_before_deviation is not None and exec_pt_leave_after_deviation is not None
    if deviation_is_between_non_deviating_moves:
        logging.debug("exec_pt_leave_before_deviation:", exec_pt_leave_before_deviation)
        logging.debug("exec_pt_leave_after_deviation:", exec_pt_leave_after_deviation)
        lca, process_tree_modified = __find_lowest_common_ancestor(exec_pt_leave_before_deviation,
                                                                   exec_pt_leave_after_deviation,
                                                                   try_pulling_lca_down)
        lca_is_leaf_node = len(lca.children) == 0
        if lca_is_leaf_node:
            lca = lca.parent

        assert lca
        assert is_subtree(pt_root, lca)

        if process_tree_modified:
            # process tree was modified, recalculation of the alignment is needed
            return get_root(lca)

        alignment_step_index_lca_activated = __get_alignment_step_index_of_lca_activation(alignment, i, lca)
        alignment_step_index_lca_closed = __get_alignment_step_index_of_lca_closing(alignment, i, lca)

        trace_to_add = __get_trace_to_add(alignment, alignment_step_index_lca_activated,
                                          alignment_step_index_lca_closed)

        sublogs = __calculate_sub_log_for_each_node(pt_root, log, pool=pool)
        # adding the fitting prefix is important to ensure that we do not add deviations in the alignment that are on
        # the left-hand side of the current deviation
        sublogs = __add_fitting_alignment_prefix_to_sublogs(alignment, i, sublogs)

        assert is_subtree(pt_root, lca)
        assert lca.id in sublogs
        sublogs[lca.id].append(trace_to_add)

        pt = __rediscover_subtree_and_modify_pt(lca, sublogs)
        return pt
    else:
        assert pt_root is not None
        return repair_first_deviation(alignment, pt_root)


def __get_first_deviation(alignment: AlignmentResult):
    for i, step in enumerate(alignment['alignment']):
        if is_log_move(step) or is_model_move_on_visible_activity(step):
            return step, i

    return None, -1


def __get_leaf_before_deviation(alignment: AlignmentResult, deviation_i: int) -> ProcessTree:
    exec_pt_leave_before_deviation = None
    h = deviation_i - 1
    while h >= 0 and not exec_pt_leave_before_deviation:
        step_before: Tuple = alignment["alignment"][h]
        if alignment_step_represents_no_deviation(step_before) and is_leaf_node(step_before[0][1][0]):
            exec_pt_leave_before_deviation = step_before[0][1][0]
        h -= 1

    return exec_pt_leave_before_deviation


def __get_leaf_after_deviation(alignment: AlignmentResult, deviation_i: int) -> ProcessTree:
    exec_pt_leave_after_deviation = None
    j = deviation_i + 1
    while j < len(alignment["alignment"]) and not exec_pt_leave_after_deviation:
        step_after: Tuple = alignment["alignment"][j]
        if alignment_step_represents_no_deviation(step_after) and is_leaf_node(step_after[0][1][0]):
            exec_pt_leave_after_deviation = step_after[0][1][0]
        j += 1

    return exec_pt_leave_after_deviation


def __get_alignment_step_index_of_lca_activation(alignment: AlignmentResult, deviation_i: int, lca: ProcessTree) -> int:
    alignment_step_index_lca_activated = None
    h = deviation_i - 1
    while h >= 0 and not alignment_step_index_lca_activated:
        if type(alignment["alignment"][h][0][1]) != str and \
                alignment["alignment"][h][0][1][0] is lca and \
                alignment["alignment"][h][0][1][1] == "active":
            alignment_step_index_lca_activated = h
        h -= 1

    assert alignment_step_index_lca_activated is not None

    return alignment_step_index_lca_activated


def __get_alignment_step_index_of_lca_closing(alignment: AlignmentResult, deviation_i: int, lca: ProcessTree) -> int:
    alignment_step_index_lca_closed = None
    j = deviation_i + 1
    while j < len(alignment["alignment"]) and not alignment_step_index_lca_closed:
        if type(alignment["alignment"][j][0][1]) != str and \
                alignment["alignment"][j][0][1][0] is lca and \
                alignment["alignment"][j][0][1][1] == "closed":
            alignment_step_index_lca_closed = j
        j += 1
    assert alignment_step_index_lca_closed is not None

    return alignment_step_index_lca_closed


def __get_trace_to_add(alignment: AlignmentResult, lca_activation_index: int, lca_closing_index: int) -> Trace:
    trace_to_add = Trace()

    # add activities that happen during LCA is active (between LCA became open and closed)
    for idx in range(lca_activation_index + 1, lca_closing_index):
        align_step = alignment["alignment"][idx]
        if is_log_move(align_step):
            e = Event()
            e["concept:name"] = align_step[1][0]
            trace_to_add.append(e)
        elif is_sync_move(align_step):
            e = Event()
            e["concept:name"] = align_step[1][1]
            trace_to_add.append(e)

    return trace_to_add


def __calculate_sub_log_for_each_node(pt: ProcessTree, log: EventLog, pool: Optional[multiprocessing.pool.Pool]) -> \
        Dict[int, EventLog]:
    sublogs: Dict[int, EventLog] = {}
    # assumption: log is replayable on process tree without deviations
    net, im, fm = pt_to_petri_net(pt)
    if pool is not None:
        alignments = calculate_alignments_parallel(log, net, im, fm, parameters={'ret_tuple_as_trans_desc': True},
                                                   pool=pool)
    else:
        alignments = calculate_alignments(log, net, im, fm, parameters={'ret_tuple_as_trans_desc': True},
                                          variant=variants_calculate_alignments.state_equation_a_star)
    for alignment in alignments:
        sublogs = __add_alignment_to_sublogs(alignment, sublogs)

    def add_missing_process_trees_to_sublogs(process_tree: ProcessTree):
        nonlocal sublogs
        if process_tree.id not in sublogs:
            sublogs[process_tree.id] = EventLog()
        if process_tree.children:
            for c in process_tree.children:
                add_missing_process_trees_to_sublogs(c)

    add_missing_process_trees_to_sublogs(pt)

    return sublogs


# This method also works for prefixes of alignments. In that case, it adds the sublogs for all closed trees.
def __add_alignment_to_sublogs(alignment: AlignmentResult, sublogs: Dict[int, EventLog]) -> Dict[int, EventLog]:
    assert not alignment_contains_deviation(alignment)
    currently_active_pt_nodes: Dict[Tuple[ProcessTree, int], Trace] = {}

    for step in alignment["alignment"]:
        # executed transition always corresponds to a node in the process tree
        current_pt = step[0][1][0]
        if (current_pt, current_pt.id) in currently_active_pt_nodes:
            if current_pt.id not in sublogs:
                sublogs[current_pt.id] = EventLog()

            sublogs[current_pt.id].append(currently_active_pt_nodes[(current_pt, current_pt.id)])
            # every pt node occurs at least twice in an alignment, i.e., start and end. Hence when we observe a pt
            # node for the second time, we know it is closed
            assert step[0][1][1] == 'closed'
            del currently_active_pt_nodes[(current_pt, current_pt.id)]
        elif not is_leaf_node(current_pt):
            currently_active_pt_nodes[(current_pt, current_pt.id)] = Trace()

        if is_leaf_node(current_pt):
            activity_name = step[1][1]
            if activity_name:
                for (active_node, active_node_obj_id) in currently_active_pt_nodes:
                    if is_subtree(active_node, current_pt):
                        event = Event()
                        event["concept:name"] = activity_name
                        currently_active_pt_nodes[(active_node, active_node.id)].append(event)

    return sublogs


def __add_fitting_alignment_prefix_to_sublogs(alignment: AlignmentResult, deviation_i: int,
                                              sublogs: Dict[int, EventLog]) -> Dict[int, EventLog]:
    fitting_alignment_prefix = __cut_alignment_to_fitting_prefix(alignment, deviation_i)
    return __add_alignment_to_sublogs(fitting_alignment_prefix, sublogs)


def __cut_alignment_to_fitting_prefix(alignment: AlignmentResult, deviation_i: int) -> AlignmentResult:
    return {'cost': 0, 'alignment': alignment['alignment'][:deviation_i]}


def __rediscover_subtree_and_modify_pt(subtree: ProcessTree, sublogs: Dict[int, EventLog]) -> ProcessTree:
    assert type(subtree) is ProcessTree
    assert type(sublogs[subtree.id]) is EventLog

    rediscovered_subtree: ProcessTree = inductive_miner.apply(sublogs[subtree.id], None)
    # detach old subtree and add rediscovered subtree
    logging.debug("rediscovered subtree:", rediscovered_subtree)
    if DEBUG:
        tree_vis.view(tree_vis.apply(rediscovered_subtree, parameters={"format": "svg"}))
    if subtree.parent:
        index = get_index_of_pt_in_children_list(subtree.parent, subtree)
        subtree.parent.children[index] = rediscovered_subtree
        rediscovered_subtree.parent = subtree.parent

    return get_root(rediscovered_subtree)


def __find_lowest_common_ancestor(pt1: ProcessTree, pt2: ProcessTree, try_pulling_lca_down) -> Tuple[ProcessTree, bool]:
    """
    Finds the lowest common ancestor (LCA) of two given process trees
    If try_pull_down=true, LCA is tried to move one level down in the process tree (Note: this alteration of the process
    tree does not change the accepted language, it is just a structural change)
    :param pt1:
    :param pt2:
    :param try_pulling_lca_down:
    :return:
    """
    if id(pt1) == id(pt2):
        # same tree
        return pt1, False

    def create_list_of_all_parents(pt: ProcessTree) -> List[ProcessTree]:
        """
        creates list of all parents including pt itself for given pt
        :param pt:
        :return:
        """
        ancestors: List[ProcessTree] = [pt]
        parent = pt.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors

    # this function is needed since, e.g., two process trees (pt1 and pt2) consisting just of one leaf node with
    # identical activity name but different parents are considered to be the equal pt1 == pt2 --> True
    def pt_in_pt_list(pt: ProcessTree, pt_list: List[ProcessTree]) -> bool:
        pt_id = id(pt)
        pt_list_ids = []
        for p in pt_list:
            pt_list_ids.append(id(p))
        return pt_id in pt_list_ids

    ancestors_pt1: List[ProcessTree] = create_list_of_all_parents(pt1)
    ancestors_pt2: List[ProcessTree] = create_list_of_all_parents(pt2)
    # find lowest common ancestor
    for i, node in enumerate(ancestors_pt1):
        if pt_in_pt_list(node, ancestors_pt2):
            lca = node
            j = -1
            for idx, a in enumerate(ancestors_pt2):
                if a is lca:
                    j = idx
            assert j > -1
            assert ancestors_pt1[i] is ancestors_pt2[j]
            assert not ancestors_pt1[i - 1] is ancestors_pt2[j - 1]

            lca_changed = False
            if try_pulling_lca_down and lca is not pt1 and lca is not pt2:
                index_children_containing_pt1 = get_index_of_pt_in_children_list(lca, ancestors_pt1[i - 1])
                index_children_containing_pt2 = get_index_of_pt_in_children_list(lca, ancestors_pt2[j - 1])
                lca, lca_changed = __try_pulling_down_lca(lca, index_children_containing_pt1,
                                                          index_children_containing_pt2)
            return lca, lca_changed
    raise Exception("lowest common ancestor could not be found")


def __try_pulling_down_lca(lca: ProcessTree, index_children_containing_pt1: int,
                           index_children_containing_pt2: int) -> Tuple[ProcessTree, bool]:
    if DEBUG:
        tree_vis.view(tree_vis.apply(lca, parameters={"format": "svg"}))
    max_idx = max(index_children_containing_pt1, index_children_containing_pt2)
    min_idx = min(index_children_containing_pt1, index_children_containing_pt2)
    assert max_idx != min_idx
    # if lca has only two children no need to pull down. if all lca children would be pulled down, do not pull down
    if lca.operator == Operator.SEQUENCE and len(lca.children) > 2 and max_idx - min_idx + 1 < len(lca.children):
        children_to_move_down: List[ProcessTree] = lca.children[min_idx:max_idx + 1]
        new_sequence = ProcessTree(operator=Operator.SEQUENCE, parent=lca, children=children_to_move_down)
        for moved_down_pt in children_to_move_down:
            moved_down_pt.parent = new_sequence
        new_lca_children: List[ProcessTree] = []
        if min_idx - 1 >= 0:
            new_lca_children.extend(lca.children[:min_idx])
        new_lca_children.append(new_sequence)
        if max_idx + 1 < len(lca.children):
            new_lca_children.extend(lca.children[max_idx + 1:])
        for c in new_lca_children:
            c.parent = lca
        lca.children = new_lca_children
        if DEBUG:
            tree_vis.view(tree_vis.apply(lca, parameters={"format": "svg"}))
        return lca, True

    elif lca.operator == Operator.XOR and len(lca.children) > 2:
        children_containing_pt1: ProcessTree = lca.children[index_children_containing_pt1]
        children_containing_pt2: ProcessTree = lca.children[index_children_containing_pt2]
        lca.children.remove(children_containing_pt1)
        lca.children.remove(children_containing_pt2)
        new_xor = ProcessTree(operator=Operator.XOR, parent=lca,
                              children=[children_containing_pt1, children_containing_pt2])
        children_containing_pt1.parent = new_xor
        children_containing_pt2.parent = new_xor
        lca.children.append(new_xor)
        if DEBUG:
            tree_vis.view(tree_vis.apply(lca, parameters={"format": "svg"}))
        return lca, True

    elif lca.operator == Operator.PARALLEL and len(lca.children) > 2:
        children_containing_pt1: ProcessTree = lca.children[index_children_containing_pt1]
        children_containing_pt2: ProcessTree = lca.children[index_children_containing_pt2]
        lca.children.remove(children_containing_pt1)
        lca.children.remove(children_containing_pt2)
        new_par = ProcessTree(operator=Operator.PARALLEL, parent=lca,
                              children=[children_containing_pt1, children_containing_pt2])
        children_containing_pt1.parent = new_par
        children_containing_pt2.parent = new_par
        lca.children.append(new_par)
        if DEBUG:
            tree_vis.view(tree_vis.apply(lca, parameters={"format": "svg"}))
        return lca, True

    else:
        return lca, False


def __set_preorder_ids_in_tree(pt: ProcessTree, current_index=0) -> int:
    pt.id = current_index
    current_index += 1

    for child in pt.children:
        current_index = __set_preorder_ids_in_tree(child, current_index)

    return current_index


def test_im():
    l = EventLog()
    e1 = Event()
    e2 = Event()
    e1["concept:name"] = 'A'
    e2["concept:name"] = 'B'
    t = Trace()
    t.append(e1)
    t.append(e2)
    l.append(t)

    e1 = Event()
    e2 = Event()
    e3 = Event()
    e1["concept:name"] = 'A'
    e2["concept:name"] = 'B'
    e3["concept:name"] = 'B'
    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    l.append(t)

    pt = inductive_miner.apply_tree(l)
    tree_vis.view(tree_vis.apply(pt, parameters={"format": "svg"}))


if __name__ == '__main__':
    tree: ProcessTree = pt_parse("+ (->('A','A'),'C'))")
    print(tree.children[0].children.index(tree.children[0].children[0]))  # --> 0
    print(tree.children[0].children.index(tree.children[0].children[1]))  # --> 0

    print(get_index_of_pt_in_children_list(tree.children[0], tree.children[0].children[1]))

    # create log
    test_im()

    L = EventLog()
    e1 = Event()
    e1["concept:name"] = "A"
    e2 = Event()
    e2["concept:name"] = "B"
    e3 = Event()
    e3["concept:name"] = "C"
    e4 = Event()
    e4["concept:name"] = "D"
    e5 = Event()
    e5["concept:name"] = "A"
    e6 = Event()
    e6["concept:name"] = "B"
    e7 = Event()
    e7["concept:name"] = "E"
    e8 = Event()
    e8["concept:name"] = "F"
    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    t.append(e5)
    t.append(e6)
    t.append(e7)
    t.append(e8)
    L.append(t)

    t2 = Trace()
    t2.append(e1)
    t2.append(e2)
    t2.append(e2)
    t2.append(e3)
    t2.append(e4)
    t2.append(e5)
    t2.append(e6)
    t2.append(e7)
    t2.append(e8)

    t3 = Trace()
    t3.append(Event({"concept:name": "Wrench"}))
    t3.append(e1)
    t3.append(e2)
    t3.append(e3)
    t3.append(e4)
    t3.append(e5)
    t3.append(e6)
    t3.append(e7)
    t3.append(e8)
    t3.append(Event({"concept:name": "Wrench"}))
    t3.append(Event({"concept:name": "Wrench"}))

    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    net, im, fm = pt_to_petri_net(tree)
    visualize_petri_net(net)

    print("height", get_height(tree))
    print("silent leaves", get_number_silent_leaves(tree))
    print("leaves", get_number_leaves(tree))
    print("nodes", get_number_nodes(tree))

    """tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = False)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = False, try_pulling_lca_down=True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))

    tree = add_trace_to_pt_language(tree, L, t2, add_artificial_start_end = True, try_pulling_lca_down= True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))"""

    print("\n Not Pulling LCA Down, Artif. Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)

    print("\n Not Pulling LCA Down, No Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=False)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)

    print("\n Pulling LCA Down, No Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=False, try_pulling_lca_down=True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)

    print("\n Pulling LCA Down, Artif. Start \n")
    tree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    tree = add_trace_to_pt_language(tree, L, t3, add_artificial_start_end=True, try_pulling_lca_down=True)
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg"}))
    print(tree)

    print("\nCalculate Sub Log for each Node")
    res = __calculate_sub_log_for_each_node(tree, L)
