import dataclasses
from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing import Pool
from typing import Optional

from pm4py import ProcessTree
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.log.obj import Trace, Event, EventLog
from pm4py.objects.process_tree.obj import Operator
from pm4py.util.typing import AlignmentResult

from cortado_core.models.infix_type import InfixType
from cortado_core.naive_approach import repair_first_deviation
from cortado_core.process_tree_utils.miscellaneous import is_subtree, get_root
from cortado_core.utils.alignment_utils import is_log_move, is_sync_move, is_model_move
from cortado_core.utils.lca_utils import (
    find_lowest_common_ancestor,
    rediscover_subtree_and_modify_pt,
)
from cortado_core.utils.sublog_utils import (
    calculate_sublog_for_lca,
    generate_full_alignment_based_on_infix_alignment,
)


class DeviationType(Enum):
    NONE = (1,)
    ENCLOSED = (2,)
    LEFT_ENCLOSED = (3,)
    RIGHT_ENCLOSED = (4,)
    NOT_ENCLOSED = 5


@dataclasses.dataclass
class Deviation:
    type: DeviationType
    # (node, index in alignment)
    left_node: tuple[Optional[ProcessTree], int]
    # (node, index in alignment)
    right_node: tuple[Optional[ProcessTree], int]
    alignment: AlignmentResult
    deviation_index: int


class DeviationSolver(ABC):
    """
    A DeviationSolver is able to solve one special kind of deviation.
    """

    @abstractmethod
    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        pass

    @staticmethod
    def get_trace_to_add(
        alignment,
        lca: ProcessTree,
        start_idx=None,
        end_idx=None,
        prefix_boundary: Optional[int] = None,
        postfix_boundary: Optional[int] = None,
    ):
        """
        In general, the trace to add is constructed using log-moves and sync-moves that are a subtree of the lca that is
        rediscovered. In most cases, these moves are restricted to begin at the opening of the lca (start_idx) and end
        at the closing of the lca (end_idx). If start_idx is None, the trace_to_add begins add the beginning of the
        alignment. Vice versa, if end_idx is None, trace_to_add ends at the last position of the alignment.
        For infix/postfix/prefix alignments, model moves are included in the full-alignment part that is NOT the infix/
        postfix/prefix alignment. Therefore, prefix_boundary and postfix_boundary signalize where the infix/postfix/prefix
        alignment starts.
        Parameters
        ----------
        alignment
        lca
        start_idx
        end_idx
        prefix_boundary: first index of the infix/postfix/prefix alignment in the full alignment
        postfix_boundary: last index of the infix/postfix/prefix alignment in the full alignment

        Returns
        -------

        """
        if start_idx is None:
            start_idx = 0

        if end_idx is None:
            end_idx = len(alignment["alignment"]) - 1

        if prefix_boundary is None:
            prefix_boundary = 0
        if postfix_boundary is None:
            postfix_boundary = len(alignment["alignment"])

        trace_to_add = Trace()

        for idx in range(start_idx, end_idx + 1):
            align_step = alignment["alignment"][idx]
            if is_log_move(align_step):
                e = Event()
                e["concept:name"] = align_step[1][0]
                trace_to_add.append(e)
            elif is_sync_move(align_step) and is_subtree(lca, align_step[0][1][0]):
                e = Event()
                e["concept:name"] = align_step[1][1]
                trace_to_add.append(e)
            elif (
                is_model_move(align_step)
                and (idx < prefix_boundary or idx > postfix_boundary)
                and is_subtree(lca, align_step[0][1][0])
                and align_step[1][1] is not None
            ):
                e = Event()
                e["concept:name"] = align_step[1][1]
                trace_to_add.append(e)

        return trace_to_add

    @staticmethod
    def get_alignment_step_index_of_lca_activation(
        move_i: int, alignment, lca: ProcessTree
    ) -> int:
        alignment_step_index_lca_activated = None
        h = move_i - 1
        while h >= 0 and not alignment_step_index_lca_activated:
            if (
                type(alignment["alignment"][h][0][1]) != str
                and alignment["alignment"][h][0][1][0].id is lca.id
                and alignment["alignment"][h][0][1][1] == "active"
            ):
                alignment_step_index_lca_activated = h
            h -= 1

        assert alignment_step_index_lca_activated is not None

        return alignment_step_index_lca_activated

    @staticmethod
    def get_alignment_step_index_of_lca_closing(
        move_i: int, alignment, lca: ProcessTree
    ) -> int:
        alignment_step_index_lca_closed = None
        j = move_i + 1
        while j < len(alignment["alignment"]) and not alignment_step_index_lca_closed:
            if (
                type(alignment["alignment"][j][0][1]) != str
                and alignment["alignment"][j][0][1][0].id is lca.id
                and alignment["alignment"][j][0][1][1] == "closed"
            ):
                alignment_step_index_lca_closed = j
            j += 1
        assert alignment_step_index_lca_closed is not None

        return alignment_step_index_lca_closed


class NoDeviationSolver(DeviationSolver):
    """
    Returns the current process tree, because the calling function found no deviation in the alignment.
    """

    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        return pt


class EnclosedDeviationSolverTrace(DeviationSolver):
    """
    Solves deviations for full-traces, i.e. NOT infixes/postfixes/prefixes, by applying the LCA-algorithm.
    """

    def __init__(self, try_pulldown: bool, pool: Optional[Pool]):
        self.try_pulldown = try_pulldown
        self.pool = pool

    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        lca, process_tree_modified = find_lowest_common_ancestor(
            deviation.left_node[0], deviation.right_node[0], self.try_pulldown
        )
        lca_is_leaf_node = len(lca.children) == 0
        if lca_is_leaf_node:
            lca = lca.parent

        assert lca
        assert is_subtree(pt, lca)

        if process_tree_modified:
            # process tree was modified, recalculation of the alignment is needed
            return get_root(lca)

        alignment_step_index_lca_activated = (
            DeviationSolver.get_alignment_step_index_of_lca_activation(
                deviation.deviation_index, deviation.alignment, lca
            )
        )
        alignment_step_index_lca_closed = (
            DeviationSolver.get_alignment_step_index_of_lca_closing(
                deviation.deviation_index, deviation.alignment, lca
            )
        )

        trace_to_add = DeviationSolver.get_trace_to_add(
            deviation.alignment,
            lca,
            alignment_step_index_lca_activated + 1,
            alignment_step_index_lca_closed - 1,
        )

        sublog = calculate_sublog_for_lca(
            pt,
            log,
            lca,
            deviation.alignment,
            deviation.deviation_index,
            trace_to_add,
            InfixType.NOT_AN_INFIX,
            self.pool,
        )

        pt = rediscover_subtree_and_modify_pt(lca, sublog)
        return pt


class FallbackDeviationSolverTrace(DeviationSolver):
    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        assert pt is not None
        return repair_first_deviation(deviation.alignment, pt)


class EnclosedDeviationSolverInfix(DeviationSolver):
    """
    Solves enclosed deviations, i.e. deviations that have a sync move or a model move on a tau-leaf node to the left AND
    to the right, for infixes/prefixes/postfixes.
    """

    def __init__(self, pool, infix_type, try_pulling_down_lca):
        self.pool = pool
        self.infix_type = infix_type
        self.try_pulling_down_lca = try_pulling_down_lca

    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        left_node, left_dev_idx = deviation.left_node
        right_node, right_dev_idx = deviation.right_node
        lca, process_tree_modified = find_lowest_common_ancestor(
            left_node, right_node, try_pulling_lca_down=self.try_pulling_down_lca
        )
        lca_is_leaf_node = len(lca.children) == 0
        if lca_is_leaf_node:
            lca = lca.parent

        if process_tree_modified:
            # process tree was modified, recalculation of the alignment is needed
            return get_root(lca)

        full_alignment = generate_full_alignment_based_on_infix_alignment(
            self.infix_type, deviation.alignment
        )
        left_dev_idx_full_alignment = left_dev_idx + full_alignment["prefix_length"]
        right_dev_idx_full_alignment = right_dev_idx + full_alignment["prefix_length"]

        left_idx = DeviationSolver.get_alignment_step_index_of_lca_activation(
            left_dev_idx_full_alignment, full_alignment, lca
        )
        right_idx = DeviationSolver.get_alignment_step_index_of_lca_closing(
            right_dev_idx_full_alignment, full_alignment, lca
        )
        trace_to_add = DeviationSolver.get_trace_to_add(
            full_alignment,
            lca,
            left_idx,
            right_idx,
            prefix_boundary=full_alignment["prefix_length"],
            postfix_boundary=len(full_alignment["alignment"])
            - 1
            - full_alignment["postfix_length"],
        )

        sublog = calculate_sublog_for_lca(
            pt,
            log,
            lca,
            deviation.alignment,
            deviation.deviation_index,
            trace_to_add,
            self.infix_type,
            self.pool,
        )

        return rediscover_subtree_and_modify_pt(lca, sublog)


class LeftEnclosedDeviationSolver(DeviationSolver):
    """
    Solves deviations for infixes/postfixes/prefixes that ONLY have a sync move or model move on tau to the left, but
    NO such move to the right of the deviation.
    """

    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        left_node, left_dev_idx = deviation.left_node
        trace_to_add = DeviationSolver.get_trace_to_add(
            deviation.alignment, left_node, left_dev_idx
        )

        trace_leaf_node = Trace()
        if left_node.label is not None:
            event_leaf_node = Event()
            event_leaf_node["concept:name"] = left_node.label
            trace_leaf_node.append(event_leaf_node)

        return rediscover_subtree_and_modify_pt(
            left_node, EventLog([trace_to_add, trace_leaf_node])
        )


class RightEnclosedDeviationSolver(DeviationSolver):
    """
    Solves deviations for infixes/postfixes/prefixes that ONLY have a sync move or model move on tau to the right, but
    NO such move to the left of the deviation.
    """

    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        right_node, right_dev_idx = deviation.right_node
        trace_to_add = DeviationSolver.get_trace_to_add(
            deviation.alignment, right_node, None, right_dev_idx
        )

        trace_leaf_node = Trace()
        if right_node.label is not None:
            event_leaf_node = Event()
            event_leaf_node["concept:name"] = right_node.label
            trace_leaf_node.append(event_leaf_node)

        return rediscover_subtree_and_modify_pt(
            right_node, EventLog([trace_to_add, trace_leaf_node])
        )


class FallbackDeviationSolverInfix(DeviationSolver):
    """
    Solves deviations with neither a sync move or model move on tau to the right nor such a move to the left. When using
    artificial start and end activities, this can only happen for infixes.
    """

    def solve(self, deviation: Deviation, pt: ProcessTree, log):
        new_infix = DeviationSolver.get_trace_to_add(deviation.alignment, pt)
        new_pt_part = inductive_miner.apply(EventLog([new_infix, Trace()]), None)
        new_root = ProcessTree(operator=Operator.PARALLEL, children=[pt, new_pt_part])
        new_pt_part.parent = new_root
        pt.parent = new_root

        return new_root


def get_deviation_solver(
    deviation: Deviation,
    infix_type: InfixType,
    try_pulling_lca_down: bool,
    pool: Optional[Pool],
):
    """
    Factory-method that returns the correct DeviationSolver for the present deviation.
    Parameters
    ----------
    deviation
    infix_type
    try_pulling_lca_down
    pool

    Returns
    -------

    """
    match deviation.type, infix_type:
        case DeviationType.NONE, _:
            return NoDeviationSolver()
        case DeviationType.ENCLOSED, InfixType.NOT_AN_INFIX:
            return EnclosedDeviationSolverTrace(try_pulling_lca_down, pool)
        case _, InfixType.NOT_AN_INFIX:
            return FallbackDeviationSolverTrace()
        case DeviationType.NOT_ENCLOSED, _:
            return FallbackDeviationSolverInfix()
        case DeviationType.ENCLOSED, _:
            return EnclosedDeviationSolverInfix(pool, infix_type, try_pulling_lca_down)
        case DeviationType.LEFT_ENCLOSED, _:
            return LeftEnclosedDeviationSolver()
        case DeviationType.RIGHT_ENCLOSED, _:
            return RightEnclosedDeviationSolver()
