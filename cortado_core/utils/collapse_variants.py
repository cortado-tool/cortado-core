from collections import defaultdict
from typing import Dict, List

from pm4py.objects.log.obj import Trace

from cortado_core.utils.split_graph import Group, SequenceGroup, ParallelGroup, LeafGroup, LoopGroup


def collapse_variants(variants: Dict[Group, List[Trace]]) -> Dict[Group, List[Trace]]:
    collapsed_variants = defaultdict(list)

    for variant, traces in variants.items():
        collapsed_variant = collapse_variant(variant)
        collapsed_variant.graphs = variant.graphs
        collapsed_variants[collapsed_variant] += traces

    return collapsed_variants


def collapse_variant(variant: Group) -> Group:
    if isinstance(variant, LeafGroup):
        return variant

    children = []
    for group in variant:
        children.append(collapse_variant(group))

    if isinstance(variant, ParallelGroup):
        return ParallelGroup(children)

    collapsed_children = []
    next_insert_child = children[0]

    for i in range(1, len(children)):
        if children[i].number_of_activities() > 1 or not isinstance(children[i], LeafGroup) or children[i] != children[
            i - 1]:
            collapsed_children.append(next_insert_child)
            next_insert_child = children[i]
        else:
            if isinstance(next_insert_child, LoopGroup):
                continue

            next_insert_child = LoopGroup([next_insert_child])

    collapsed_children.append(next_insert_child)

    return SequenceGroup(collapsed_children)
