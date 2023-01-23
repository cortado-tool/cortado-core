from typing import List

from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree.obj import ProcessTree

from cortado_core.trace_ordering.scoring.scorer import Scorer
from cortado_core.utils.split_graph import Group, SequenceGroup, LeafGroup, ParallelGroup


class MockScorer(Scorer):
    def __init__(self, mock_scores: List[float]):
        self.mock_scores = mock_scores
        self.i = 0

    def score(self, log: EventLog, previously_added_variants: List[Group], process_tree: ProcessTree,
              variant_candidate: Group) -> float:
        score = self.mock_scores[self.i % len(self.mock_scores)]
        self.i += 1

        return score


def generate_variants_from_lists(l: List) -> List[Group]:
    return [generate_variant_from_list(c) for c in l]


def generate_variant_from_list(children: List) -> Group:
    return SequenceGroup([__generate_test_variant_recursive(child) for child in children])


def __generate_test_variant_recursive(element) -> Group:
    if isinstance(element, str):
        return LeafGroup([element])

    if element[0] == 'sequence':
        return SequenceGroup([__generate_test_variant_recursive(child) for child in element[1:]])

    if element[0] == 'parallel':
        return ParallelGroup([__generate_test_variant_recursive(child) for child in element[1:]])

    raise Exception('Cannot parse the given format: ' + str(element))


def generate_test_trace(trace_unformatted) -> Trace:
    trace = Trace()
    for event_unformatted in trace_unformatted:
        event = Event()
        event["concept:name"] = event_unformatted
        trace.append(event)

    return trace
