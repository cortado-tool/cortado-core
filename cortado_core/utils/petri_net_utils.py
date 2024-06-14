from collections import defaultdict
import math
import networkx
from pm4py.objects.petri_net.obj import PetriNet


def _generate_networkx_graph(petri_net: PetriNet):
    graph = networkx.DiGraph()
    for place in petri_net.places:
        graph.add_node(place)
    for transition in petri_net.transitions:
        graph.add_node(transition)
        for a in transition.out_arcs:
            target_place = a.target
            graph.add_edge(transition, target_place)
        for a in transition.in_arcs:
            source_place = a.source
            graph.add_edge(source_place, transition)
    return graph


def get_all_paths_between_transitions(
    petri_net: PetriNet,
    transition1: PetriNet.Transition,
    transition2: PetriNet.Transition,
):
    g = _generate_networkx_graph(petri_net)
    return networkx.all_simple_paths(g, transition1, transition2)


def get_all_distances(petri_net: PetriNet):
    return networkx.shortest_path_length(_generate_networkx_graph(petri_net))


def get_distances_from_transitions_to_places(petri_net: PetriNet):
    """
    Returns the distances from all transitions to all reachable places.
    The distance denotes the number of arcs in the petri_net.
    """
    distances = get_all_distances(petri_net)
    res = {}
    for source, distances in distances:
        if type(source) is PetriNet.Transition:
            res[source] = defaultdict(
                lambda: math.inf,
                {
                    target.name: distances[target]
                    for target in distances
                    if type(target) is PetriNet.Place
                },
            )
    return res


def get_transitions_by_label(petri_net: PetriNet, label: str):
    res = set()
    for t in petri_net.transitions:
        if t.label == label:
            res.add(t)
    return res
