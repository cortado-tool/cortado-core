from collections import defaultdict

from pm4py.objects.petri_net.obj import PetriNet, Marking
from itertools import chain, combinations

from pm4py.objects.petri_net.utils.petri_utils import post_set, pre_set


def create_causal_footprint(net: PetriNet, im: Marking, fm: Marking):
    causal_graph = create_causal_graph(net, im, fm)
    causal_footprint = derive_causal_closure(*causal_graph)

    return causal_footprint


def create_causal_graph(net: PetriNet, im: Marking, fm: Marking):
    N = set([t.label for t in net.transitions if t.label is not None])

    # check if there are duplicated labels
    assert len(N) == len([t.label for t in net.transitions if t.label is not None])

    look_ahead_links = defaultdict(set)

    for transition in net.transitions:
        if transition.label is None:
            continue

        places = post_set(transition)
        for place in places:
            if place in fm:
                continue
            follow_links = frozenset(
                [t.label for t in post_set(place) if t.label is not None]
            )
            if len(follow_links) > 0:
                look_ahead_links[transition.label].add(follow_links)

    look_back_links = defaultdict(set)

    for transition in net.transitions:
        if transition.label is None:
            continue

        places = pre_set(transition)
        for place in places:
            if place in im:
                continue
            previous_links = frozenset(
                [t.label for t in pre_set(place) if t.label is not None]
            )
            if len(previous_links) > 0:
                look_back_links[transition.label].add(previous_links)

    return N, look_ahead_links, look_back_links


def derive_causal_closure(N, look_ahead_links, look_back_links):
    # Rule 3
    new_links = defaultdict(set)
    for a, Bs in look_ahead_links.items():
        for B in Bs:
            for subset in powerset(N.difference(B)):
                new_links[a].add(frozenset(set(subset).union(B)))

    for a, Bs in new_links.items():
        look_ahead_links[a] = look_ahead_links[a].union(Bs)

    # Rule 4
    new_links = defaultdict(set)
    for b, As in look_back_links.items():
        for A in As:
            for subset in powerset(N.difference(A)):
                new_links[b].add(frozenset(set(subset).union(A)))

    for b, As in new_links.items():
        look_back_links[b] = look_back_links[b].union(As)

    # Rule 5
    new_links = defaultdict(set)
    for a, Bs in look_ahead_links.items():
        for B in Bs:
            for b in B:
                if b not in look_ahead_links:
                    continue
                for C in look_ahead_links[b]:
                    new_links[a].add(frozenset(B.difference({b}).union(C)))

    for a, Bs in new_links.items():
        look_ahead_links[a] = look_ahead_links[a].union(Bs)

    # Rule 6
    new_links = defaultdict(set)
    for c, Bs in look_back_links.items():
        for B in Bs:
            for b in B:
                if b not in look_back_links:
                    continue
                for A in look_back_links[b]:
                    new_links[c].add(frozenset(B.difference({b}).union(A)))

    for b, As in new_links.items():
        look_back_links[b] = look_back_links[b].union(As)

    return N, look_ahead_links, look_back_links


def get_look_ahead_links_for_label(look_ahead_links):
    res = defaultdict(list)

    for a, B in look_ahead_links:
        res[a].append(B)

    return look_ahead_links


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))
