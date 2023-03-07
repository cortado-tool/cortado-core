from typing import List, Tuple
import logging

import pm4py.visualization.process_tree.visualizer as tree_vis
from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.algo.discovery.inductive import algorithm as inductive_miner

from cortado_core.process_tree_utils.miscellaneous import get_index_of_pt_in_children_list, get_root

DEBUG = False


def find_lowest_common_ancestor(pt1: ProcessTree, pt2: ProcessTree, try_pulling_lca_down) -> Tuple[ProcessTree, bool]:
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


def rediscover_subtree_and_modify_pt(subtree: ProcessTree, sublog: EventLog) -> ProcessTree:
    assert type(subtree) is ProcessTree
    assert type(sublog) is EventLog

    rediscovered_subtree: ProcessTree = inductive_miner.apply(sublog, None)
    # detach old subtree and add rediscovered subtree
    logging.debug("rediscovered subtree:", rediscovered_subtree)
    if DEBUG:
        tree_vis.view(tree_vis.apply(rediscovered_subtree, parameters={"format": "svg"}))
    if subtree.parent:
        index = get_index_of_pt_in_children_list(subtree.parent, subtree)
        subtree.parent.children[index] = rediscovered_subtree
        rediscovered_subtree.parent = subtree.parent

    return get_root(rediscovered_subtree)
