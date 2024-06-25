import abc


class OccurrenceStatisticTracker(abc.ABC):
    @abc.abstractmethod
    def track_after_iteration(self, occurrence_list):
        pass

    @abc.abstractmethod
    def get_max_occurrence_size(self):
        pass


class NoOccurrenceStatisticTracker(OccurrenceStatisticTracker):
    def track_after_iteration(self, occurrence_list):
        pass

    def get_max_occurrence_size(self):
        return -1


class MaxOccurrenceStatisticTracker(OccurrenceStatisticTracker):
    def __init__(self):
        self.max_size = 0

    def track_after_iteration(self, occurrence_list):
        size = 0

        for occ_for_trees in occurrence_list.values():
            for occs in occ_for_trees.values():
                size += len(occs)

        if size > self.max_size:
            self.max_size = size

    def get_max_occurrence_size(self):
        return self.max_size
