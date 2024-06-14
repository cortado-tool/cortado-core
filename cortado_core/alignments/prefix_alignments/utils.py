from pm4py.objects.petri_net.utils import align_utils


def __place_from_spn_belongs_to_trace_net_part(place):
    return place.name[1] == align_utils.SKIP
