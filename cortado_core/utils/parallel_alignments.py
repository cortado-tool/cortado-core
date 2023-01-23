from typing import List

from pm4py.objects.log.obj import EventLog, Trace
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.util.typing import AlignmentResult
from pm4py.algo.conformance.alignments.petri_net.algorithm import apply as calculate_alignment
from pm4py.algo.conformance.alignments.petri_net.algorithm import variants as variants_calculate_alignments


def calculate_alignments_parallel(log: EventLog, net: PetriNet, im: Marking, fm: Marking, parameters, pool) -> List[
    AlignmentResult]:
    results = []
    for trace in log:
        result = pool.apply_async(
            calculate_alignment_a_star,
            args=[trace, net, im, fm],
            kwds={'parameters': parameters}
        )
        results.append(result)

    return [r.get() for r in results]


def calculate_alignment_a_star(trace: Trace, net: PetriNet, im: Marking, fm: Marking, parameters) -> AlignmentResult:
    """
    Calculates an alignment using the a star search algorithm. This function is necessary as the variants accepted
    by PM4PY are python modules. So, they cannot be pickled and therefore not used directly in a pool.apply_async()-call
    """
    return calculate_alignment(trace, net, im, fm, parameters=parameters,
                               variant=variants_calculate_alignments.state_equation_a_star)
