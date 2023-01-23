from typing import Dict, Tuple, List, FrozenSet, OrderedDict

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignments
from pm4py.algo.conformance.alignments.petri_net.algorithm import variants as variants_calculate_alignments
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
import pm4py.visualization.process_tree.visualizer as tree_vis

from cortado_core.process_tree_utils.miscellaneous import is_leaf_node, pt_dict_key, subtree_is_part_of_tree_based_on_obj_id
from cortado_core.process_tree_utils.to_petri_net_transition_bordered import apply as pt_to_petri_net
from cortado_core.utils.alignment_utils import alignment_contains_deviation
from cortado_core.utils.visualize_petri_net import visualize_petri_net


def project_log(pt: ProcessTree, log: EventLog, frozen_subtrees: OrderedDict[Tuple[ProcessTree, int], str]) \
        -> Tuple[Dict[FrozenSet[Tuple[ProcessTree, int]], EventLog], EventLog]:
    # assumption: log is replayable on process tree without deviations
    net, im, fm = pt_to_petri_net(pt)
    alignments = calculate_alignments(log, net, im, fm, parameters={'ret_tuple_as_trans_desc': True},
                                      variant=variants_calculate_alignments.state_equation_a_star)

    replaced_frozen_subtrees: List[Tuple[ProcessTree, int]] = []
    incrementally_projected_logs: Dict[FrozenSet[Tuple[ProcessTree, int]], EventLog] = {}
    final_projected_log: EventLog

    for frozen_subtree in frozen_subtrees:
        # incrementally replace the frozen subtree(s)

        replaced_frozen_subtrees.append(frozen_subtree)
        res = EventLog()

        for i, alignment in enumerate(alignments):
            assert not alignment_contains_deviation(alignment)
            trace = Trace()
            for step in alignment["alignment"]:
                # executed transition always corresponds to a node in the process tree
                current_pt: ProcessTree = step[0][1][0]
                assert type(current_pt) is ProcessTree
                # determine if current_pt is frozen
                current_pt_frozen = False
                for f_pt, f_pt_id in replaced_frozen_subtrees:
                    if subtree_is_part_of_tree_based_on_obj_id(current_pt, f_pt):
                        current_pt_frozen = True

                activity_label = None
                if is_leaf_node(current_pt) and \
                        current_pt.operator is None and \
                        current_pt.label is not None and \
                        not current_pt_frozen:
                    activity_label = step[1][1]
                elif current_pt_frozen and pt_dict_key(current_pt) in replaced_frozen_subtrees:
                    if step[0][1][1] == 'active':
                        activity_label = frozen_subtrees[pt_dict_key(current_pt)] + "+ACTIVATED"
                    elif step[0][1][1] == 'closed':
                        activity_label = frozen_subtrees[pt_dict_key(current_pt)] + "+CLOSED"
                if activity_label:
                    event = Event()
                    event["concept:name"] = activity_label
                    trace.append(event)
            res.append(trace)
        incrementally_projected_logs[frozenset(replaced_frozen_subtrees)] = res
        final_projected_log = res
    return incrementally_projected_logs, final_projected_log


if __name__ == "__main__":
    pt_1: ProcessTree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E',->('A','F')) )")
    pt_2: ProcessTree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F' )")

    print(subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_1))  # True

    print("tree:", pt_1)
    print("subtree:", pt_1.children[1].children[1])
    print(subtree_is_part_of_tree_based_on_obj_id(pt_1.children[1].children[1], pt_1))  # True
    print(subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_1.children[1].children[1]))  # False
    print(subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_2))

    L = EventLog()
    e1 = Event()
    e1["concept:name"] = "A"
    e2 = Event()
    e2["concept:name"] = "B"
    e3 = Event()
    e3["concept:name"] = "C"
    e4 = Event()
    e4["concept:name"] = "D"

    t1 = Trace()
    t1.append(e1)
    t1.append(e1)
    t1.append(e3)
    t1.append(e4)
    t1.append(e2)
    L.append(t1)

    t2 = Trace()
    t2.append(e3)
    t2.append(e4)
    t2.append(e1)
    t2.append(e1)
    t2.append(e2)
    L.append(t2)

    t3 = Trace()
    t3.append(e3)
    t3.append(e1)
    t3.append(e1)
    t3.append(e4)
    t3.append(e2)
    L.append(t3)

    tree: ProcessTree = pt_parse("+ (->('A','A','B'),->('C','D'))")
    tree_vis.view(tree_vis.apply(tree, parameters={"format": "svg", "debug": True}))
    net_tree, im, fm = pt_to_petri_net(tree)
    visualize_petri_net(net_tree)
    log = project_log(tree, L,
                      {(tree.children[1], id(tree.children[1])): 'X', (tree.children[0], id(tree.children[0])): 'Y'})
    print(log)
