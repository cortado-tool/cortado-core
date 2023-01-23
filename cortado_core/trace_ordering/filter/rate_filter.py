import math
from typing import List

from cortado_core.trace_ordering.filter.filter import Filter
from cortado_core.utils.split_graph import Group


class RateFilter(Filter):
    def __init__(self, filter_rate: float):
        self.filter_rate = filter_rate

    def filter(self, ordered_candidates: List[Group]) -> List[Group]:
        n_remaining_candidates = max(1, math.ceil(self.filter_rate * len(ordered_candidates)))
        n_deleted_candidates = len(ordered_candidates) - n_remaining_candidates

        return ordered_candidates[n_deleted_candidates:]
