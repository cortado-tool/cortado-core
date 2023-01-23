def service_time_instances(tree, activity_instances):
    return [(ai[0], ai[1]) for ai in activity_instances[tree]]


def intervals_sort_key(x):
    return x[0] if x[0] else (x[1] if x[1] else -1)


def compute_service_times(instances_ais):
    instances_ais = [ai for ai in instances_ais if ai != [None, None]]
    instances_ais = sorted(instances_ais, key=intervals_sort_key)
    if len(instances_ais) == 0:
        return []
    result = []
    current = list(instances_ais[0])
    for ai in instances_ais[1:]:
        if None in ai:
            result.append(ai)
        elif current[1] is None:
            result.append(current)
            current = ai
        elif ai[0] <= current[1]:
            current[1] = ai[1]
        else:
            result.append(current)
            current = list(ai)
    result.append(current)
    return sorted(result, key=intervals_sort_key)


def merge_ranges(ai1, ai2):
    start1, end1 = ai1
    start2, end2 = ai2
    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)
    if latest_start < earliest_end:
        return [[min(start1, start2), max(end1, end2)]]
    else:
        return [ai1, ai2]


def compute_idle_times(instances_ais):
    instances_ais = [ai for ai in instances_ais if ai != [None, None]]
    instances_ais = sorted(instances_ais, key=intervals_sort_key)
    if len(instances_ais) == 0:
        return []
    idle_times = []
    running = instances_ais[0]
    for ai in instances_ais[1:]:
        if ai[0] is None:
            # [t0, t1], [None, _]
            idle_times.append([running[1], None])
            running = ai
        elif running[1] is None:
            # [t0, None], [t'0, _]
            idle_times.append([None, ai[1]])
            running = ai
        elif ai[0] > running[1]:
            # [_, 0], [1, _]
            idle_times.append([running[1], ai[0]])
            running = ai
        elif ai[1] is not None and ai[1] > running[1]:
            # [0, 2], [1, 3]
            running = ai

    return idle_times


def get_overlap(ai1, ai2):
    start1, end1 = ai1
    start2, end2 = ai2
    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)
    overlap = (earliest_end - latest_start).total_seconds()
    return max(0, overlap)
