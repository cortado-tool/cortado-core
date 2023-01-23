import statistics

import numpy as np


def avg(values):
    if values is None:
        return None
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def index(values):
    return {
        i: v for (i, v) in enumerate(values) if v is not None
    }


def stats(values):
    if values is None:
        return None
    n = len(values)
    values = [v for v in values if v is not None]
    if values:
        stats = {
            'min': min(values, default=None),
            'max': max(values, default=None),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'n': n,
            'n_not_none': len(values),
            '50th': np.percentile(values, 50),
            '95th': np.percentile(values, 95),
        }
        if len(values) > 1:
            stats['stdev'] = statistics.stdev(values)
            if stats['mean'] != 0:
                stats['percentage_variance'] = (statistics.stdev(values) / statistics.mean(values)) * 100
        else:
            stats['stdev'] = 0
            stats['percentage_variance'] = 0
        return stats
    else:
        return None


def stat_stats(stats_list):
    if stats_list is None:
        return None

    stats_list = [s for s in stats_list if s is not None]
    if not stats_list:
        return []

    stats_stats = {}
    keys = {k for s in stats_list for k in s.keys()}
    for key in keys:
        values = [s[key] for s in stats_list if key in s]
        stats_stats[key] = stats(values)
    return stats_stats


def noop(values):
    return values
