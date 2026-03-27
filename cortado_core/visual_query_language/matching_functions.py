from typing import cast

from cortado_core.utils.split_graph import (
    ChoiceGroup,
    LeafGroup,
    WildcardGroup,
    Group,
    FallthroughGroup,
)


def match(node_query: Group, node_variant: Group) -> bool:
    """
    Checks the two Group have the same type and calls the matching function to compare if both are leafs.
    Else it just checks if the types are the same.
    Args:
        node_query: The Group of the query.
        node_variant: The Group of the variant.

    Returns:
        bool: True if the types are equal or if the leafs match.
    """
    qtype = type(node_query)
    vtype = type(node_variant)

    if vtype is LeafGroup:
        if qtype is LeafGroup:
            return node_variant[0] == node_query[0]

        if qtype is ChoiceGroup:
            return any(node_variant[0] == child[0] for child in node_query)

        if qtype is WildcardGroup:
            return True

        return False

    if qtype is FallthroughGroup and vtype is FallthroughGroup:
        return match_no_order(node_query, node_variant)

    # Just check the type, because we can only check the exact match when we encounter two leafs.
    return qtype is vtype


def match_no_order(
    node_query: FallthroughGroup, node_variant: FallthroughGroup
) -> bool:
    """
        Checks if the node_variant matches the node_query.
    Args:
        node_query: The FallthroughGroup of the query.
        node_variant: The FallthroughGroup of the variant.

    Returns:
        bool: True if the node_variant matches the node_query.
    """

    if node_query.list_length() != node_variant.list_length():
        return False

    return all(child in node_query for child in node_variant)
