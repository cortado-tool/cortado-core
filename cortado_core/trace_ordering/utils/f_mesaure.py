from typing import Tuple

from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.conversion.process_tree.converter import apply as pt_to_petri_net
from pm4py.algo.evaluation.precision import evaluator as precision_evaluator
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator


def calculate_f_measure(process_tree: ProcessTree, log: EventLog) -> Tuple[float, float, float]:
    net, im, fm = pt_to_petri_net(process_tree)

    fitness = replay_fitness_evaluator.apply(log, net, im, fm,
                                             variant=replay_fitness_evaluator.Variants.ALIGNMENT_BASED)[
        'averageFitness']
    precision = precision_evaluator.apply(log, net, im, fm,
                                          variant=precision_evaluator.Variants.ALIGN_ETCONFORMANCE)

    return 2 * ((fitness * precision) / (fitness + precision)), fitness, precision
