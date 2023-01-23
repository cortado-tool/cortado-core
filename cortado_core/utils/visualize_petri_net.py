import copy

from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.visualization.petri_net import visualizer as petri_vis


def visualize_petri_net(net: PetriNet) -> None:
    """
    Visualizes a Petri net whose place names contain a process tree object
    :param net:
    :return:
    """
    net_copied: PetriNet = copy.deepcopy(net)
    for t in net_copied.transitions:
        t.name = "".join(str(t.name))
    # since petri net describes a process tree, it is always possible to get im and fm from list of places
    for p in net_copied.places:
        if len(p.in_arcs) == 0:
            im: Marking = Marking({p: 1})
        if len(p.out_arcs) == 0:
            fm: Marking = Marking({p: 1})
    petri_vis.view(petri_vis.apply(net_copied, im, fm, parameters={"format": "svg", "debug": True}))
    petri_vis.view(petri_vis.apply(net_copied, im, fm, parameters={"format": "svg", "debug": False}))
