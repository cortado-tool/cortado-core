import copy
import itertools
from typing import List

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.lca_approach import add_trace_to_pt_language
from cortado_core.process_tree_utils.miscellaneous import get_root, subtree_is_part_of_tree_based_on_obj_id, \
    subtree_contained_in_tree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.process_tree.obj import Operator

from cortado_core.utils.alignment_utils import trace_fits_process_tree


def add_trace_to_pt_language_with_freezing_baseline_approach(pt: ProcessTree, frozen_subtrees: List[ProcessTree],
                                                             log: EventLog,
                                                             trace: Trace,
                                                             try_pulling_lca_down=True) -> ProcessTree:
    """
    Checks if a given trace can be replayed on the given process tree. If not, the tree will be altered to accept the
    given trace
    :param frozen_subtrees: list of frozen subtrees. Note: frozen subtrees do not contain each other and are unique,
    i.e., there is no other subtree in pt that is structurally identical
    :param try_pulling_lca_down:
    :param pt: ProcessTree
    :param log: EventLog accepted by pt
    :param trace: trace that should be accepted by pt in the end
    :return: process tree that accepts the given log and trace
    """
    for pt_1, pt_2 in itertools.combinations(frozen_subtrees, 2):
        assert get_root(pt_1) is pt
        assert get_root(pt_2) is pt
        assert not subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_2)
        assert not subtree_is_part_of_tree_based_on_obj_id(pt_2, pt_1)

    if not trace_fits_process_tree(trace, pt):
        # deepcopy frozen subtrees because otherwise they might get changed due to process tree changes
        frozen_subtrees = [copy.deepcopy(frozen_subtree) for frozen_subtree in frozen_subtrees]
        # execute 'standard' incremental approach
        pt = add_trace_to_pt_language(pt, log, trace, try_pulling_lca_down=try_pulling_lca_down)

        # add frozen subtrees to pt if pt does not contain frozen subtrees
        missing_frozen_subtrees: List[ProcessTree] = []
        for frozen_subtree in frozen_subtrees:
            if not subtree_contained_in_tree(frozen_subtree, pt):
                missing_frozen_subtrees.append(frozen_subtree)

        # print("pt before potential reinsert:", pt)
        # print("missing frozen subtrees:", missing_frozen_subtrees)

        if len(missing_frozen_subtrees) > 0:
            # print("reinsert frozen subtrees")
            optional_frozen_subtrees = [__create_optional_tree_from_given_subtree(t) for t in missing_frozen_subtrees]
            res: ProcessTree = ProcessTree(operator=Operator.PARALLEL, children=[pt] + optional_frozen_subtrees)
            for c in res.children:
                c.parent = res
            return res, frozen_subtrees
    return pt, frozen_subtrees


def __create_optional_tree_from_given_subtree(pt: ProcessTree) -> ProcessTree:
    tau = ProcessTree()
    res = ProcessTree(operator=Operator.XOR, children=[tau, pt])
    tau.parent = res
    pt.parent = res
    return res


if __name__ == "__main__":
    pt_1 = pt_parse("+ (->('A','B'),->('C','D'))")
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
    t1.append(e3)
    t1.append(e4)
    t1.append(e2)

    t2 = Trace()
    t2.append(e3)
    t2.append(e4)
    t2.append(e1)
    t2.append(e2)

    t3 = Trace()
    t3.append(e3)
    t3.append(e1)
    t3.append(e4)
    t3.append(e2)

    log = EventLog()
    log.append(t1)
    log.append(t2)
    log.append(t3)

    t_next = Trace()
    t_next.append(e1)
    t_next.append(e2)
    t_next.append(e2)
    t_next.append(e3)
    t_next.append(e4)

    print(pt_1)
    frozen_trees = []
    frozen_trees.append(pt_1.children[0])
    print(frozen_trees)
    res, frozen_subtrees = add_trace_to_pt_language_with_freezing_baseline_approach(pt_1, frozen_trees, log, t_next)
    print(res)
    print(frozen_subtrees)
