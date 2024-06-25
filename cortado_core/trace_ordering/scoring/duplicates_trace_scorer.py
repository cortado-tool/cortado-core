from typing import List

from pm4py.objects.petri_net.utils.align_utils import STD_MODEL_LOG_MOVE_COST
from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.process_tree.obj import ProcessTree
from cortado_core.lca_approach import get_deviation, set_preorder_ids_in_tree
from cortado_core.process_tree_utils.miscellaneous import get_all_leaf_node_labels
from cortado_core.process_tree_utils.reduction import (
    reduce_loops_with_more_than_two_children,
)
from cortado_core.trace_ordering.scoring.trace_scorer import TraceScorer
from cortado_core.utils.alignment_utils import calculate_alignment_typed_trace
from cortado_core.utils.deviation_solvers import DeviationType
from cortado_core.utils.lca_utils import find_lowest_common_ancestor
from cortado_core.utils.trace import TypedTrace
from cortado_core.models.infix_type import InfixType


class DuplicatesTraceScorer(TraceScorer):
    def __init__(self, try_pulling_lca_down=True) -> None:
        self.try_pulling_lca_down = try_pulling_lca_down
        super().__init__()

    def score(
        self,
        log: EventLog,
        previously_added_traces: List[Trace],
        process_tree: ProcessTree,
        trace_candidate: Trace,
    ) -> float:
        reduce_loops_with_more_than_two_children(process_tree)

        set_preorder_ids_in_tree(process_tree)
        alignment = calculate_alignment_typed_trace(
            process_tree, TypedTrace(trace_candidate, InfixType.NOT_AN_INFIX)
        )

        if alignment["cost"] < STD_MODEL_LOG_MOVE_COST:
            return 0

        deviation = get_deviation(alignment)

        if deviation.type != DeviationType.ENCLOSED:
            return 0

        lca, _ = find_lowest_common_ancestor(
            deviation.left_node[0],
            deviation.right_node[0],
            self.try_pulling_lca_down,
        )
        return len(get_all_leaf_node_labels(lca)[1])
