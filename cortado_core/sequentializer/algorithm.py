from collections import defaultdict
from typing import Dict, List

from pm4py.objects.log.obj import Trace

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
    cTreeFromcGroup,
)
from cortado_core.sequentializer.matching import (
    is_matching,
    get_target_to_source_mapping,
)
from cortado_core.sequentializer.pattern import (
    SequentializerPattern,
    WILDCARD_MATCH,
    set_preorder_ids,
)
from cortado_core.sequentializer.reduction_rules import (
    apply_reduction_rules,
    get_child_position,
)
from cortado_core.sequentializer.two_plus_two_free_check import (
    contains_possibly_violating_construct,
    can_apply_without_violating_two_plus_two_freeness,
)
from cortado_core.utils.split_graph import Group, create_graph_for_cvariant


def apply_sequentializer_on_variants(
    variants,
    source_pattern: SequentializerPattern,
    target_pattern: SequentializerPattern,
) -> Dict[Group, List[Trace]]:
    new_variants = defaultdict(list)

    for variant, traces in variants.items():
        new_variant = apply_sequentializer_on_variant(
            variant, source_pattern, target_pattern
        )
        if new_variant != variant:
            new_graph = create_graph_for_cvariant(new_variant)
            new_variant.graphs = {new_graph: len(traces)}
        else:
            new_variant.graphs = variant.graphs
        new_variants[new_variant] += traces

    return new_variants


def apply_sequentializer_on_variant(
    variant,
    source_pattern: SequentializerPattern,
    target_pattern: SequentializerPattern,
) -> Group:
    variant_tree = cTreeFromcGroup(variant)
    variant_tree_str = str(variant_tree)
    new_variant_tree = apply_sequentializer(
        variant_tree, source_pattern, target_pattern
    )

    if variant_tree_str != str(new_variant_tree):
        print("FROM:", variant_tree_str)
        print("TO:", str(new_variant_tree))

    return new_variant_tree.to_concurrency_group()


def apply_sequentializer(
    variant: ConcurrencyTree,
    source_pattern: SequentializerPattern,
    target_pattern: SequentializerPattern,
) -> ConcurrencyTree:
    set_preorder_ids(source_pattern)
    set_preorder_ids(target_pattern)
    target_has_pot_violating_construct = contains_possibly_violating_construct(
        target_pattern
    )
    target_source_mapping = get_target_to_source_mapping(source_pattern, target_pattern)

    new_variant = apply_sequentializer_intern(
        variant,
        source_pattern,
        target_pattern,
        target_has_pot_violating_construct,
        target_source_mapping,
    )

    return apply_reduction_rules(new_variant)


def apply_sequentializer_intern(
    variant: ConcurrencyTree,
    source_pattern: SequentializerPattern,
    target_pattern: SequentializerPattern,
    target_has_pot_violating_construct: bool,
    target_source_mapping,
) -> ConcurrencyTree:
    has_match, match = is_matching(variant, source_pattern)
    if has_match:
        parent = variant.parent
        if (
            not target_has_pot_violating_construct
            or can_apply_without_violating_two_plus_two_freeness(
                target_pattern, match, target_source_mapping
            )
        ):
            child_position = get_child_position(parent, variant)
            variant = apply_match(match, target_pattern, target_source_mapping)
            variant.parent = parent
            if parent is not None:
                parent.children[child_position] = variant

    new_children = []
    for child in variant.children:
        child = apply_sequentializer_intern(
            child,
            source_pattern,
            target_pattern,
            target_has_pot_violating_construct,
            target_source_mapping,
        )
        child.parent = variant

        new_children.append(child)
    variant.children = new_children

    return variant


def apply_match(
    match: Dict[int, List[ConcurrencyTree]],
    target_pattern: SequentializerPattern,
    target_source_mapping,
    parent=None,
):
    if (
        target_pattern.operator is not None
        and target_pattern.operator != WILDCARD_MATCH
    ):
        new_tree = ConcurrencyTree(parent=parent, op=target_pattern.operator)

        for child in target_pattern.children:
            new_child = apply_match(match, child, target_source_mapping, new_tree)
            if new_child is not None:
                new_tree.children.append(new_child)

        return new_tree

    matching_nodes = match[target_source_mapping[target_pattern.id]]
    if len(matching_nodes) == 0:
        return None
    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        node.parent = parent

        return node

    new_tree = ConcurrencyTree(parent=parent, op=cTreeOperator.Concurrent)
    for node in matching_nodes:
        node.parent = new_tree
        new_tree.children.append(node)

    return new_tree
