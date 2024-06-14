from typing import Tuple

import pm4py
from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.conversion.process_tree.converter import apply as pt_to_petri_net


def calculate_f_measure(
    process_tree: ProcessTree, log: EventLog
) -> Tuple[float, float, float]:
    net, im, fm = pt_to_petri_net(process_tree)

    fitness = pm4py.fitness_alignments(log, net, im, fm, multi_processing=True)[
        "averageFitness"
    ]
    precision = pm4py.precision_alignments(log, net, im, fm, multi_processing=True)

    return 2 * ((fitness * precision) / (fitness + precision)), fitness, precision
