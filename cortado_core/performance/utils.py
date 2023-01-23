from pm4py.objects.process_tree.obj import ProcessTree


def get_alignment_tree_nodes(alignment):
    return [a[0][1][0] if a[0][1] != ">>" else None for a in alignment]


def get_alignment_events(alignment, trace):
    events = []
    i = 0
    for (log_move_label, _), (_, _) in alignment:
        if log_move_label != ">>":
            events.append(trace[i])
            i += 1
        else:
            events.append(None)
    return events


def get_alignment_activities(alignment):
    return [a[1][0] if a[1][0] != ">>" else a[1][1] for a in alignment]


def get_alignment_tree_lf(alignment):
    return [a[0][1][1] for a in alignment]


def get_all_nodes(tree: ProcessTree):
    return {tree}.union({n for nn in tree.children for n in get_all_nodes(nn)})


def get_leaf_nodes(pt):
    if pt.children:
        return {n for c in pt.children for n in get_leaf_nodes(c)}
    else:
        return {pt}


def get_all_indices(lst, item):
    if item is None:
        return [-1]
    # for some reason equals of ProcessTree is not used here, so compare ids
    return [i for i, x in enumerate(lst) if id(x) == id(item)]


def get_tree_instances(alignment, nodes=None):
    alignment_activities = get_alignment_activities(alignment)
    alignment_tree_nodes = get_alignment_tree_nodes(alignment)

    starts = {}
    instances = []
    for i, (a, t) in enumerate(zip(alignment_activities, alignment_tree_nodes)):
        if nodes is None or t not in nodes:
            continue
        if t is None or not a:
            continue

        if "_start" in a:
            starts[t] = starts.get(t, []) + [i]
        else:
            start_idx = starts[t].pop()
            instances.append((start_idx, i))
    return instances
