import itertools
import logging
from collections import OrderedDict
from typing import List, Tuple, Dict, OrderedDict, FrozenSet, Iterable

import pm4py
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.stats import get_event_attribute_values

from cortado_core.freezing.project_log import project_log
from cortado_core.freezing.reinsert_frozen_subtrees import reinsert_frozen_subtrees
from cortado_core.freezing.project_trace import project_trace
from cortado_core.freezing.replace_frozen_subtrees import replace_frozen_subtrees_in_pt
from cortado_core.lca_approach import add_trace_to_pt_language
from cortado_core.process_tree_utils.miscellaneous import get_root, subtree_is_part_of_tree_based_on_obj_id, pt_dict_key
from cortado_core.utils.alignment_utils import trace_fits_process_tree


def add_trace_to_pt_language_with_freezing(pt: ProcessTree,
                                           frozen_subtrees: List[ProcessTree],
                                           log: EventLog,
                                           trace: Trace,
                                           try_pulling_lca_down=True,
                                           add_missing_frozen_subtrees_at_root_level: bool = False,
                                           add_artificial_start_end: bool = True, pool=None) -> Tuple[
    ProcessTree, List[ProcessTree]]:
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
        # frozen_subtrees = [copy.deepcopy(frozen_subtree) for frozen_subtree in frozen_subtrees]

        activities_in_log: Iterable[str] = get_event_attribute_values(log, 'concept:name').keys()
        frozen_subtrees_replacement_label: OrderedDict[Tuple[ProcessTree, int], str] = OrderedDict()

        for frozen_subtree in frozen_subtrees:
            replacement_label = str(id(frozen_subtree))
            # TODO create function that ensures replacement_label not in activities_in_log
            assert replacement_label not in activities_in_log
            frozen_subtrees_replacement_label[pt_dict_key(frozen_subtree)] = replacement_label

        incremental_projected_logs: Dict[FrozenSet[Tuple[ProcessTree, int]], EventLog]
        final_projected_log: EventLog
        incremental_projected_logs, final_projected_log = project_log(pt, log, frozen_subtrees_replacement_label)

        incremental_projected_traces: Dict[FrozenSet[Tuple[ProcessTree, int]], Trace]
        final_projected_trace: Trace
        incremental_projected_traces, final_projected_trace = project_trace(trace, frozen_subtrees_replacement_label)

        # replace frozen subtrees
        pt = replace_frozen_subtrees_in_pt(pt, frozen_subtrees_replacement_label)

        # executed incremental process discovery
        pt = add_trace_to_pt_language(pt, final_projected_log, final_projected_trace,
                                      try_pulling_lca_down=try_pulling_lca_down,
                                      add_artificial_start_end=add_artificial_start_end, pool=pool)
        assert trace_fits_process_tree(final_projected_trace, pt)
        res_print = []
        for a in final_projected_trace:
            res_print.append(a["concept:name"])
        logging.debug(res_print)

        # reinsert frozen subtrees
        label_to_frozen_subtree = OrderedDict()
        for k in frozen_subtrees_replacement_label:
            assert frozen_subtrees_replacement_label[k] not in label_to_frozen_subtree  # labels are unique
            label_to_frozen_subtree[frozen_subtrees_replacement_label[k]] = k[0]
        pt = reinsert_frozen_subtrees(label_to_frozen_subtree, pt, incremental_projected_logs, log,
                                      incremental_projected_traces, trace,
                                      add_missing_frozen_subtrees_at_root_level=add_missing_frozen_subtrees_at_root_level)
        print(pt)

        res_print = []
        for a in trace:
            res_print.append(a["concept:name"])
        logging.debug(res_print)

        assert trace_fits_process_tree(trace, pt)
    return pt, frozen_subtrees


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
    frozen_trees.append(pt_1.children[1])
    print(frozen_trees)
    res, frozen_subtrees = add_trace_to_pt_language_with_freezing(pt_1, frozen_trees, log, t_next)
    print(res)
    print(frozen_subtrees)
