from pm4py.objects.log.obj import Trace
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.util import typing as pm4pyTyping
from cortado_core.alignments.infix_alignments.variants import tree_based_preprocessing, baseline_approach

VARIANT_TREE_BASED_PREPROCESSING = 1
VARIANT_BASELINE_APPROACH = 2


def calculate_optimal_infix_alignment(trace: Trace, process_tree: ProcessTree, variant: int,
                                      **kwargs) -> pm4pyTyping.AlignmentResult:
    if variant == 1:
        return tree_based_preprocessing.calculate_optimal_infix_alignment(trace, process_tree, **kwargs)

    return baseline_approach.calculate_optimal_infix_alignment(trace, process_tree, **kwargs)
