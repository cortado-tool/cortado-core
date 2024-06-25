import itertools
from typing import List

from pm4py.objects.log.obj import Trace, Event

from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree
from cortado_core.utils.sequentializations import generate_sequentializations


def sub_pattern_to_ctree(pattern: SubPattern, parent=None):
    t = ConcurrencyTree(parent=parent, op=pattern.operator, label=pattern.label)
    t.children = [sub_pattern_to_ctree(child, t) for child in pattern.children]
    return t


def sequentialize_pattern(
    pattern: EventuallyFollowsPattern, add_artificial_skip_nodes=True
) -> List[Trace]:
    sub_pattern_sequentializations = []
    for sub_pattern in pattern.sub_patterns:
        sub_pattern_sequentializations.append(__sequentialize_sub_pattern(sub_pattern))

    if add_artificial_skip_nodes:
        sub_pattern_sequentializations = add_artificial_skip_activities(
            sub_pattern_sequentializations
        )

    traces = __sequential_combination(sub_pattern_sequentializations)

    return [__to_pm4py_trace(t) for t in traces]


def __sequentialize_sub_pattern(sub_pattern: SubPattern) -> List[List[str]]:
    group = sub_pattern_to_ctree(sub_pattern).to_concurrency_group()

    return generate_sequentializations(group)


def __sequential_combination(elements: List[List[List[str]]]):
    combined_c_sequentializations = itertools.product(*elements)

    traces = []
    for tup in combined_c_sequentializations:
        trace = []
        for elem in tup:
            trace += elem
        traces.append(trace)

    return traces


def __concurrent_combination(elements: List[List[List[str]]]):
    if len(elements) == 0:
        return [[]]

    if len(elements) == 1:
        return elements[0]

    permutations = []
    for i, child_traces in enumerate(elements):
        for trace in child_traces:
            input = elements[:i] + elements[i + 1 :]
            for postfix in __concurrent_combination(input):
                permutations.append(trace + postfix)

    return permutations


def add_artificial_skip_activities(
    sub_pattern_sequentializations: List[List[List[str]]],
) -> List[List[List[str]]]:
    for i in range(len(sub_pattern_sequentializations) - 1):
        for j in range(len(sub_pattern_sequentializations[i])):
            sub_pattern_sequentializations[i][j].append("...")

    return sub_pattern_sequentializations


def __to_pm4py_trace(trace: List[str]) -> Trace:
    t = Trace()
    for event_name in trace:
        event = Event()
        event["concept:name"] = event_name
        t.append(event)

    return t
