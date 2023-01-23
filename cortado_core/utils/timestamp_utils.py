import datetime
import functools
from enum import Enum

from pm4py.objects.log.util.sampling import sample_log
from pm4py.objects.log.obj import EventLog
from pm4py.util.xes_constants import DEFAULT_TIMESTAMP_KEY


@functools.total_ordering
class TimeUnit(str, Enum):
    MS = "Milliseconds"
    SEC = "Seconds"
    MIN = "Minutes"
    HOUR = "Hours"
    DAY = "Days"
    MONTH = "Month"

    def __gt__(self, other):
        if isinstance(other, TimeUnit):
            return (
                self._member_names_.index(self.name) >
                self._member_names_.index(other.name)
            )
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, TimeUnit):
            return (
                self._member_names_.index(self.name) <
                self._member_names_.index(other.name)
            )
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, TimeUnit):
            return (
                self._member_names_.index(self.name) ==
                self._member_names_.index(other.name)
            )
        return NotImplemented


def to_utc(timestamp: datetime):
    if timestamp.utcoffset() is not None:
        # subtract utcoffset
        timestamp = timestamp - timestamp.utcoffset()

    # remove time zone info
    return timestamp.replace(tzinfo=None)


def transform_timestamp(timestamp: datetime, granularity: TimeUnit):
    timestamp = to_utc(timestamp)
    if granularity is TimeUnit.SEC:
        return timestamp.replace(microsecond=0)
    elif granularity is TimeUnit.MIN:
        return timestamp.replace(microsecond=0, second=0)
    elif granularity is TimeUnit.HOUR:
        return timestamp.replace(microsecond=0, second=0, minute=0)
    elif granularity is TimeUnit.DAY:
        return timestamp.replace(microsecond=0, second=0, minute=0, hour=0)
    elif granularity is TimeUnit.MONTH:
        return timestamp.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
    else:
        return timestamp


def get_time_granularity(event_log: EventLog):
    sample = sample_log(event_log, 500)
    timestamps = [event[DEFAULT_TIMESTAMP_KEY]
                  for trace in sample for event in trace]

    if not_all_zero(timestamps, 'microsecond'):
        return TimeUnit.MS
    elif not_all_zero(timestamps, 'second'):
        return TimeUnit.SEC
    elif not_all_zero(timestamps, 'minute'):
        return TimeUnit.MIN
    elif not_all_zero(timestamps, 'hour'):
        return TimeUnit.HOUR
    elif not_all_zero(timestamps, 'day'):
        return TimeUnit.DAY


def not_all_zero(timestamps, time_unit_key):
    return not all(getattr(timestamp, time_unit_key) == 0 for timestamp in timestamps)
