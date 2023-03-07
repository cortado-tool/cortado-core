from typing import List, Optional

from pm4py.objects.process_tree.obj import ProcessTree, Operator
import pm4py.visualization.process_tree.visualizer as tree_vis
from pm4py.objects.process_tree.utils.generic import parse as pt_parse

from cortado_core.process_tree_utils.miscellaneous import replace_tree_in_children, get_index_of_pt_in_children_list, \
    is_tau_leaf


def apply_reduction_rules(pt: ProcessTree, excluded_subtrees: List[ProcessTree] = []) -> None:
    """
    Applies language preserving reduction rules to the given process tree
    :param excluded_subtrees:
    :param pt:
    :return:
    """
    if pt.children and len(pt.children) > 0:
        _associativity_reduction_choice_parallelism(pt, excluded_subtrees=excluded_subtrees)
        _reduce_sequences(pt, excluded_subtrees=excluded_subtrees)
        _tau_reduction_sequence_parallelism(pt, excluded_subtrees=excluded_subtrees)
        _tau_reduction_choice(pt, excluded_subtrees=excluded_subtrees)
        __reduce_tau_loops(pt, excluded_subtrees=excluded_subtrees)
        __reduce_to_at_most_two_loop_children(pt, excluded_subtrees)
    for subtree in pt.children:
        if not _tree_in_list_of_trees_based_on_id(subtree, excluded_subtrees):
            apply_reduction_rules(subtree, excluded_subtrees)


def _tree_in_list_of_trees_based_on_id(tree: ProcessTree, trees: List[ProcessTree]) -> bool:
    tree_ids = [id(pt) for pt in trees]
    return id(tree) in tree_ids


def reduce_loops_with_more_than_two_children(pt, excluded_subtrees = []):
    __reduce_to_at_most_two_loop_children(pt, excluded_subtrees)
    for subtree in pt.children:
        if not _tree_in_list_of_trees_based_on_id(subtree, excluded_subtrees):
            reduce_loops_with_more_than_two_children(subtree, excluded_subtrees)

def __reduce_to_at_most_two_loop_children(pt, excluded_subtrees):
    if _tree_in_list_of_trees_based_on_id(pt, excluded_subtrees):
        return

    if pt.operator != Operator.LOOP or len(pt.children) <= 2:
        return

    new_xor = ProcessTree(operator=Operator.XOR, parent=pt, children=pt.children[1:])
    for child in pt.children[1:]:
        child.parent = new_xor

    pt.children = [pt.children[0], new_xor]


def _associativity_reduction_choice_parallelism(pt: ProcessTree, excluded_subtrees: List[ProcessTree] = []) -> None:
    def child_has_matching_operator(operator, pt):
        for child in pt.children:
            if child.operator == operator and not _tree_in_list_of_trees_based_on_id(child, excluded_subtrees):
                return True
        return False

    root_operator = pt.operator
    if root_operator != Operator.XOR and root_operator != Operator.PARALLEL:
        return

    while child_has_matching_operator(root_operator, pt):
        subtree_children_to_lift_up: List[ProcessTree] = []
        children_to_remove_from_pt: List[ProcessTree] = []
        for subtree in pt.children:
            if subtree.operator == root_operator and not _tree_in_list_of_trees_based_on_id(subtree,
                                                                                            excluded_subtrees):
                children_to_remove_from_pt.append(subtree)
                subtree_children_to_lift_up.extend(subtree.children)
        for subtree in subtree_children_to_lift_up:
            subtree.parent = pt
        pt.children = [x for x in pt.children if x not in children_to_remove_from_pt]
        pt.children.extend(subtree_children_to_lift_up)


def _reduce_sequences(pt: ProcessTree, excluded_subtrees: List[ProcessTree] = []) -> None:
    def check_for_subtree_with_sequence_op(tree: ProcessTree):
        for s in tree.children:
            if s.operator == Operator.SEQUENCE and s not in excluded_subtrees:
                return True
        return False

    if pt.operator == Operator.SEQUENCE:
        while check_for_subtree_with_sequence_op(pt):
            for idx, c in enumerate(pt.children):
                if c.operator == Operator.SEQUENCE and not _tree_in_list_of_trees_based_on_id(c, excluded_subtrees):
                    subtrees_to_lift_up = c.children
                    for subtree in subtrees_to_lift_up:
                        subtree.parent = pt
                    new_children = pt.children[:idx] + subtrees_to_lift_up + pt.children[idx + 1:]
                    pt.children = new_children
                    del c
                    break


def _tau_reduction_sequence_parallelism(pt: ProcessTree, excluded_subtrees: List[ProcessTree] = []) -> None:
    if pt.operator == Operator.SEQUENCE or pt.operator == Operator.PARALLEL:
        tau_leaves_to_remove: List[ProcessTree] = []
        for c in pt.children:
            if (not c.children or len(c.children) == 0) and not c.operator and not c.label and \
                    not _tree_in_list_of_trees_based_on_id(c, excluded_subtrees):
                tau_leaves_to_remove.append(c)

        if len(tau_leaves_to_remove) == len(pt.children):
            pt.operator = None
            pt.children = []
            return

        for leaf_node in tau_leaves_to_remove:
            pt.children.remove(leaf_node)
            del leaf_node


def _tau_reduction_choice(pt: ProcessTree, excluded_subtrees: List[ProcessTree] = []) -> None:
    if pt.operator == Operator.XOR:
        tau_leaves: List[ProcessTree] = []
        for c in pt.children:
            if not c.children and c.label is None and not _tree_in_list_of_trees_based_on_id(c, excluded_subtrees):
                tau_leaves.append(c)
        while len(tau_leaves) > 1:
            tau_leave_to_remove = tau_leaves.pop()
            pt.children.remove(tau_leave_to_remove)
            del tau_leave_to_remove


def general_tau_reduction(pt: ProcessTree, excluded_subtrees: List[ProcessTree] = []) -> ProcessTree:
    # replace operator nodes with tau nodes if they have just tau leaf nodes
    if pt.operator and not _tree_in_list_of_trees_based_on_id(pt, excluded_subtrees):
        all_children_tau = True
        for c in pt.children:
            if not is_tau_leaf(c):
                all_children_tau = False
        if all_children_tau:
            pt.operator = None
            pt.label = None
            pt.children = []

            return pt

    if pt and pt.children:
        for c in pt.children:
            general_tau_reduction(c, excluded_subtrees)

    return pt


def remove_operator_node_with_one_or_no_child(pt: ProcessTree,
                                              excluded_subtrees: List[ProcessTree] = []) -> Optional[ProcessTree]:
    if _tree_in_list_of_trees_based_on_id(pt, excluded_subtrees):
        return pt

    if pt.operator is None:
        return pt

    new_children = []
    for child in pt.children:
        if _tree_in_list_of_trees_based_on_id(pt, excluded_subtrees):
            new_children.append(child)
        else:
            new_child = remove_operator_node_with_one_or_no_child(child, excluded_subtrees)
            if new_child is not None:
                new_children.append(remove_operator_node_with_one_or_no_child(child, excluded_subtrees))

    pt.children = new_children

    if len(pt.children) == 0:
        return None

    if len(pt.children) == 1:
        pt.children[0].parent = pt.parent
        return pt.children[0]

    return pt


def __reduce_tau_loops(tree: ProcessTree, excluded_subtrees: List[ProcessTree]):
    """
    Reduces process trees of the shape xor(tau, loop(T, tau)) to loop(tau, T)
    :param tree:
    :param excluded_subtrees:
    :return:
    """
    if _tree_in_list_of_trees_based_on_id(tree, excluded_subtrees):
        return

    if tree.operator != Operator.XOR:
        return

    if len(tree.children) != 2:
        return

    child1 = tree.children[0]
    child2 = tree.children[1]

    if child1.operator == Operator.LOOP:
        loop_child = child1
        potential_tau_child = child2
    elif child2.operator == Operator.LOOP:
        loop_child = child2
        potential_tau_child = child1
    else:
        return

    if potential_tau_child.operator is not None or potential_tau_child.label is not None:
        return

    if _tree_in_list_of_trees_based_on_id(loop_child, excluded_subtrees):
        return

    if len(loop_child.children) != 2:
        return

    potential_tau_redo_child = loop_child.children[1]
    if potential_tau_redo_child.label is not None or potential_tau_redo_child.operator is not None:
        return

    tree.operator = Operator.LOOP
    tree.children = [potential_tau_redo_child, loop_child.children[0]]
    for child in tree.children:
        child.parent = tree


def reduction_test():
    t = pt_parse(
        "->('Create Fine', X( 'Payment', tau ), X( 'Send Fine', tau ), X( 'Insert Fine Notification', tau ), +( ->( X( tau ), X( tau ) ), X( +( *( tau, 'Payment' ), 'Add penalty' ), tau ) ), X( 'Send for Credit Collection', tau ) )")
    tree_vis.view(tree_vis.apply(t, parameters={"format": "svg"}))

    t = remove_operator_node_with_one_or_no_child(t)
    t = general_tau_reduction(t)
    t = remove_operator_node_with_one_or_no_child(t)

    tree_vis.view(tree_vis.apply(t, parameters={"format": "svg"}))
    print(t)

    t2 = pt_parse("->( +( ->( 'A', 'A' ), 'C' ))")
    t2 = remove_operator_node_with_one_or_no_child(t2)

    # Expected +( ->( 'A', 'A' ), 'C')
    tree_vis.view(tree_vis.apply(t2, parameters={"format": "svg"}))
    print(t2)

    # Expected +('A','C')
    t3 = ProcessTree(operator="->", children=[pt_parse("->( +( 'A', 'C' ))"), ProcessTree(operator="->")])
    t3 = remove_operator_node_with_one_or_no_child(t3)

    tree_vis.view(tree_vis.apply(t2, parameters={"format": "svg"}))
    print(t2)


if __name__ == "__main__":
    # reduction_test()
    # t = pt_parse("-> (*(X(tau,->('A','B'),tau,X('C','D')),tau) ,->(tau,'E',->('E',tau,'F')) )")
    # tree_vis.view(tree_vis.apply(t, parameters={"format": "svg"}))
    # apply_reduction_rules(t)
    # tree_vis.view(tree_vis.apply(t, parameters={"format": "svg"}))
    #
    # t_tau = pt_parse("->(X( X(X(tau))),X( X(X(tau,'A'))))")
    # tree_vis.view(tree_vis.apply(t_tau, parameters={"format": "svg"}))
    # # t_tau = __remove_operator_with_only_one_child(t_tau, excluded_subtrees=[t_tau.children[0]])
    # copy_t_tau = copy.deepcopy(t_tau)
    # res = remove_operator_node_with_one_or_no_child(t_tau, excluded_subtrees=t_tau.children)
    # print(copy_t_tau == res)
    # print(t_tau == res)
    # print(t_tau is res)
    #
    # print(t_tau)
    # tree_vis.view(tree_vis.apply(t_tau, parameters={"format": "svg"}))

    pt_test_1 = pt_parse("+('A', 'C', tau, ->('H','G'), ->('X'), X(+('G'), 'H', +('A', 'C', tau, tau, tau, tau)))")
    pt_true_1 = pt_parse("+('A', 'C', ->('H','G'), 'X', X('G', 'H', +('A', 'C')))")

    apply_reduction_rules(pt_test_1)
