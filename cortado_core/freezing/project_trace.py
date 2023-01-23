import copy
from typing import List, Dict, Set, Tuple, OrderedDict, FrozenSet

from pm4py.objects.log.obj import Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.obj import Operator as ProcessTreeOperator
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignment
from pm4py.algo.conformance.alignments.petri_net.algorithm import variants as variants_calculate_alignments
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.vis import view_process_tree

from cortado_core.process_tree_utils.miscellaneous import pt_dict_key, subtree_is_part_of_tree_based_on_obj_id, is_leaf_node
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import apply as pt_to_petri_net
from cortado_core.utils.alignment_utils import is_log_move, is_sync_move, is_model_move, is_model_move_on_visible_activity


def __generate_process_tree_from_frozen_trees(trees: List[ProcessTree]):
    assert len(trees) > 0
    if len(trees) > 1:
        frozen_trees_in_loop = []
        for t in trees:
            frozen_trees_in_loop.append(__generate_loop_with_frozen_tree(t))
        root = ProcessTree(operator=ProcessTreeOperator.PARALLEL)
        for t in frozen_trees_in_loop:
            root.children.append(t)
            t.parent = root
        return root
    else:
        assert len(trees) == 1
        return __generate_loop_with_frozen_tree(trees[0])


def __generate_loop_with_frozen_tree(tree: ProcessTree) -> ProcessTree:
    # tree = copy.deepcopy(tree)
    tau = ProcessTree()
    res = ProcessTree(operator=ProcessTreeOperator.LOOP, children=[tau, tree])
    tau.parent = res
    tree.parent = res
    return res


def project_trace(trace: Trace, frozen_subtrees_replacement_labels: OrderedDict[Tuple[ProcessTree, int], str]) -> \
        Tuple[Dict[FrozenSet[Tuple[ProcessTree, int]], Trace], Trace]:
    # for pt_1, pt_2 in itertools.combinations(frozen_subtrees, 2):
    #     assert pt_1 != pt_2  # TODO discuss if there is a solution to not require pt_1 != pt_2

    # prepare frozen_subtrees, i.e., deepcopy frozen trees because they get changed and added to a new tree
    copied_frozen_subtrees_replacement_label: Dict[Tuple[ProcessTree, int], str] = OrderedDict()
    copied_frozen_subtrees: List[ProcessTree] = []
    mapping_copied_tree_to_original_tree: Dict[Tuple[ProcessTree, int], Tuple[ProcessTree, int]] = {}
    for k in frozen_subtrees_replacement_labels:
        tree_copy = copy.deepcopy(k[0])
        mapping_copied_tree_to_original_tree[pt_dict_key(tree_copy)] = k
        copied_frozen_subtrees.append(tree_copy)
        copied_frozen_subtrees_replacement_label[pt_dict_key(tree_copy)] = frozen_subtrees_replacement_labels[k]
    copied_frozen_subtrees: List[ProcessTree] = []
    for k in copied_frozen_subtrees_replacement_label:
        copied_frozen_subtrees.append(k[0])

    frozen_subtrees_model = __generate_process_tree_from_frozen_trees(copied_frozen_subtrees)
    # view_process_tree(frozen_subtrees_model, "svg")

    net, im, fm = pt_to_petri_net(frozen_subtrees_model)
    alignment = calculate_alignment(trace, net, im, fm, parameters={'ret_tuple_as_trans_desc': True},
                                    variant=variants_calculate_alignments.state_equation_a_star)

    res: Dict[FrozenSet[Tuple[ProcessTree, int]], Trace] = {}
    # gradually create projected trace by following the order in frozen_subtrees_replacement_labels
    currently_considered_frozen_subtrees: List[Tuple[ProcessTree, int]] = []
    for k in copied_frozen_subtrees:
        currently_considered_frozen_subtrees.append(pt_dict_key(k))

        provisional_trace: List[str] = []
        # create provisional trace from alignment
        active_frozen_trees_fully_executed: Set[Tuple[ProcessTree, int]] = set()
        active_frozen_trees_incompletely_executed: Set[Tuple[ProcessTree, int]] = set()

        for i, step in enumerate(alignment['alignment']):
            if is_log_move(step):
                activity = step[1][0]
                provisional_trace.append(activity)
                continue
            elif is_model_move(step):
                executed_tree: ProcessTree = step[0][1][0]
                tree_status: str = step[0][1][1]

                if pt_dict_key(executed_tree) in copied_frozen_subtrees_replacement_label and \
                        pt_dict_key(executed_tree) in currently_considered_frozen_subtrees:

                    if tree_status == 'active':
                        # look ahead to see if frozen tree was fully executed, i.e., no model moves regarding frozen subtree
                        executed_tree_not_yet_closed = True
                        j = i + 1
                        while executed_tree_not_yet_closed:
                            step_ahead = alignment['alignment'][j]
                            corresponding_tree_ahead = step_ahead[0][1][0]
                            # look ahead until tree is closed again
                            if corresponding_tree_ahead is executed_tree and step_ahead[0][1][1] == 'closed':
                                executed_tree_not_yet_closed = False
                                continue
                            # corresponding tree is a frozen subtree that just got activated (position i in alignment)
                            if is_model_move(step_ahead) and is_leaf_node(corresponding_tree_ahead) and \
                                    subtree_is_part_of_tree_based_on_obj_id(corresponding_tree_ahead, executed_tree) and \
                                    is_model_move_on_visible_activity(step_ahead):
                                # mark activated frozen subtree (executed_tree) as incompletely executed
                                active_frozen_trees_incompletely_executed.add(pt_dict_key(executed_tree))
                            j += 1
                        if pt_dict_key(executed_tree) not in active_frozen_trees_incompletely_executed:
                            active_frozen_trees_fully_executed.add(pt_dict_key(executed_tree))
                            # add activation of a frozen tree if fully executed
                            provisional_trace.append(
                                copied_frozen_subtrees_replacement_label[pt_dict_key(executed_tree)] + '+ACTIVATED')
                        else:
                            pass
                    elif tree_status == 'closed':
                        if pt_dict_key(executed_tree) not in active_frozen_trees_incompletely_executed:
                            assert pt_dict_key(executed_tree) in active_frozen_trees_fully_executed
                            # add closing of a frozen tree if fully executed
                            provisional_trace.append(
                                copied_frozen_subtrees_replacement_label[pt_dict_key(executed_tree)] + '+CLOSED')
                            # remove frozen tree from active list
                            active_frozen_trees_fully_executed.remove(pt_dict_key(executed_tree))
            elif is_sync_move(step):
                executed_tree: ProcessTree = step[0][1][0]
                # check if executed_tree is part of a fully executed frozen tree
                executed_tree_part_of_fully_executed_frozen_tree = False
                for key in active_frozen_trees_fully_executed:
                    if subtree_is_part_of_tree_based_on_obj_id(executed_tree, key[0]):
                        executed_tree_part_of_fully_executed_frozen_tree = True
                if not executed_tree_part_of_fully_executed_frozen_tree:
                    provisional_trace.append(step[1][0])
        t = Trace()
        for e in provisional_trace:
            event = Event()
            print(e)
            event['concept:name'] = e
            t.append(event)
        print(t)

        original_trees_considered: List[Tuple[ProcessTree, int]] = []
        for k in currently_considered_frozen_subtrees:
            original_trees_considered.append(mapping_copied_tree_to_original_tree[k])
        res[frozenset(original_trees_considered)] = t
    return res, t


if __name__ == '__main__':
    def __pretty_print_trace(t: Trace):
        res = []
        for a in t:
            res.append(a['concept:name'])
        return res


    # pt_1: ProcessTree = pt_parse("-> (*(X(->('A','A','B'),->('C','D')),tau) ,->('E',->('A','F')) )")
    # e1 = Event()
    # e1["concept:name"] = "A"
    # e2 = Event()
    # e2["concept:name"] = "B"
    # e3 = Event()
    # e3["concept:name"] = "C"
    # e4 = Event()
    # e4["concept:name"] = "D"
    # t1 = Trace()
    # t1.append(e1)
    # t1.append(e2)
    # t1.append(e3)
    # t1.append(e4)
    #
    # print("tree:", pt_1)
    # print("frozen subtree(s):", pt_1.children[0].children[0].children[1])
    # print("trace:", __pretty_print_trace(t1))
    # res_1 = project_trace(t1, {pt_dict_key(pt_1.children[0].children[0].children[1]): 'X'})
    # print('RESULT:', __pretty_print_trace(res_1), "\n\n")
    #
    # pt_2: ProcessTree = pt_parse("+ (-> ('A','B'),-> ('A','C'))")
    # print(pt_2)
    # print("frozen subtree(s):")
    # print(pt_2.children[0], pt_2.children[1])
    # t2 = Trace()
    # t2.append(e2)
    # t2.append(e1)
    # t2.append(e1)
    # t2.append(e3)
    # t2.append(e1)
    # print("trace:", __pretty_print_trace(t2))
    # res_2 = project_trace(t2, {pt_dict_key(pt_2.children[0]): 'Y', pt_dict_key(pt_2.children[1]): 'Z'})
    # print('RESULT:', __pretty_print_trace(res_2), "\n\n")
    #
    # t3 = Trace()
    # t3.append(e1)
    # t3.append(e3)
    # t3.append(e3)
    # t3.append(e1)
    # t3.append(e3)
    # t3.append(e1)
    # t3.append(e4)
    # t3.append(e2)
    # print("trace:", __pretty_print_trace(t3))
    # res_2 = project_trace(t3, {pt_dict_key(pt_2.children[0]): 'Y', pt_dict_key(pt_2.children[1]): 'Z'})
    # print('RESULT:', __pretty_print_trace(res_2), "\n\n")

    pt_3: ProcessTree = pt_parse("+(*(tau,'Payment'),'Add penalty')")
    e1 = Event()
    e1["concept:name"] = "Create Fine"
    e2 = Event()
    e2["concept:name"] = "Payment"
    e3 = Event()
    e3["concept:name"] = "Send Fine"
    e4 = Event()
    e4["concept:name"] = "Insert Fine Notification"
    e5 = Event()
    e5["concept:name"] = "Add penalty"
    t3 = Trace()
    t3.append(e1)
    t3.append(e2)
    t3.append(e2)
    t3.append(e3)
    t3.append(e4)
    t3.append(e5)
    t3.append(e2)

    print("frozen subtree(s):", pt_3)
    print("trace:", __pretty_print_trace(t3))
    res_1 = project_trace(t3, {pt_dict_key(pt_3): 'X'})
    print('RESULT:', __pretty_print_trace(res_1), "\n\n")
