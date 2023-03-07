from dataclasses import dataclass

from pm4py.objects.log.obj import Trace, EventLog

from cortado_core.models.infix_type import InfixType


@dataclass
class TypedTrace:
    trace: Trace
    infix_type: InfixType

    def __hash__(self):
        return hash((hash(self.trace), self.infix_type.value))

    def __eq__(self, other):
        return self.trace == other.trace and self.infix_type == other.infix_type


def combine_event_logs(log1: EventLog, log2: EventLog) -> EventLog:
    for trace in log2:
        log1.append(trace)

    return log1
