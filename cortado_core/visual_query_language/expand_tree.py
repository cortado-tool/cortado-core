import copy
from typing import List

from cortado_core.utils.split_graph import (
    Group,
    LeafGroup,
    FallthroughGroup,
    WildcardGroup,
    AnythingGroup,
    ChoiceGroup,
    SequenceGroup,
    LoopGroup,
    ParallelGroup,
    OptionalGroup,
    StartGroup,
    EndGroup,
)


def expand_tree(tree_query: Group | List[Group]) -> List[Group]:
    """
    Turns the given query tree into a query tree to be used for filtering a variant.
    Args:
        tree_query: The query given as a tree.

    Returns:
        Group: A tree that is unfolded to be used for filtering.
    """
    if check_leaf(tree_query):
        return [tree_query]

    # Handle LoopGroup directly (e.g., when inside OptionalGroup at the root of recursion)
    if type(tree_query) is LoopGroup:
        unfold_tree_list = expand_tree(tree_query[0])
        min_count = tree_query.min_count if tree_query.min_count is not None else 1
        max_count = tree_query.max_count if tree_query.max_count is not None else 1
        max_count = min(max_count, 200)

        # Generate variants for each repetition count
        all_variants = []
        parent_type = None
        for count in range(min_count, max_count + 1):
            count_trees = []
            for _ in range(count):
                count_trees = merge_and_flatten(
                    count_trees, unfold_tree_list, parent_type
                )
            all_variants.extend(count_trees)

        # Wrap variants in SequenceGroup if they are lists
        result = []
        for variant in all_variants:
            if isinstance(variant, list):
                result.append(SequenceGroup(lst=variant))
            else:
                result.append(variant)
        return result

    tree_query = add_start_end_to_parallel_group(tree_query)

    # Determine parent type for flattening same-type nesting
    parent_type = (
        type(tree_query) if type(tree_query) in (SequenceGroup, ParallelGroup) else None
    )
    new_trees: List[List[Group]] = []
    for child in tree_query:
        if check_leaf(child):
            new_trees = add_to_tree_list(child, new_trees)
        elif type(child) is OptionalGroup:
            new_trees_copy = copy.deepcopy(new_trees)
            unfold_tree_list = expand_tree(child[0])
            # Use merge_and_flatten to flatten same-type nesting (e.g., SequenceGroup inside SequenceGroup)
            new_trees = merge_and_flatten(new_trees, unfold_tree_list, parent_type)
            # Append the paths where the optional is skipped
            new_trees.extend(new_trees_copy)
        elif type(child) is LoopGroup:
            # Generate variants for each repetition count from min_count to max_count
            unfold_tree_list = expand_tree(child[0])

            min_count = child.min_count if child.min_count is not None else 1
            max_count = child.max_count if child.max_count is not None else 1

            max_count = min(
                max_count, 200
            )  # Cap max_count to prevent explosion of variants for infinite loops

            # For each valid repetition count, create a separate path in the tree variants
            # We need to branch: create multiple separate query variants
            # inside is actual group object
            # 2nd most inside is different path (if it contained choice for example) for that specific repetition count
            # outermost is all different repetition counts combined
            new_trees_by_count: List[List[List[Group]]] = []

            for count in range(min_count, max_count + 1):
                # For this specific count, repeat the loop content 'count' times
                count_trees = copy.deepcopy(new_trees) if new_trees else []
                for _ in range(count):
                    count_trees = merge_and_flatten(
                        count_trees, unfold_tree_list, parent_type
                    )
                new_trees_by_count.append(count_trees)

            # Merge all the variants from different counts
            # Each count produces separate variants that should all be tried
            if new_trees_by_count:
                new_trees = []
                for count_variants in new_trees_by_count:
                    new_trees.extend(count_variants)
        elif type(child) is SequenceGroup:
            unfold_tree_list = expand_tree(child)
            new_trees = merge_and_flatten(new_trees, unfold_tree_list, parent_type)
        elif type(child) is ParallelGroup:
            list_of_unfolded_trees = expand_tree(child)
            new_trees = merge_and_flatten(
                new_trees, list_of_unfolded_trees, parent_type
            )

        else:
            raise TypeError(
                f"Unexpected type {type(child)}. Should be implemented in unfold_tree."
            )
    list_of_groups: List[Group] = []
    if type(tree_query) is ParallelGroup:
        for list_of_nodes in new_trees:
            list_of_groups.append(ParallelGroup(lst=list_of_nodes))
        return list_of_groups

    elif type(tree_query) is SequenceGroup:
        for list_of_nodes in new_trees:
            list_of_groups.append(SequenceGroup(lst=list_of_nodes))
        return list_of_groups
    elif type(tree_query) is list:
        return tree_query
    else:
        raise Exception(
            f"Unexpected input type {type(tree_query)}. This should never happen."
        )


def add_to_tree_list(node: Group, tree_list: List[List[Group]]) -> List[List[Group]]:
    if len(tree_list) == 0:
        tree_list.append([node])
    else:
        for tree in tree_list:
            tree.append(node)
    return tree_list


def add_start_end_to_parallel_group(variant: Group):
    if type(variant) is ParallelGroup:
        for child in variant:
            if type(child) is SequenceGroup:
                child.append(EndGroup())
                child.insert(0, StartGroup())
    return variant


def merge_and_flatten(
    list1: List[Group], list2: List[Group], parent_type: type = None
) -> List[Group]:
    """
    Merge two lists of tree components, flattening same-type nesting.

    Args:
        list1: Current list of tree components being built
        list2: New components to merge in
        parent_type: The type of the parent group (SequenceGroup or ParallelGroup).
                     If item2 matches this type, its contents are flattened.
    """
    result: List[Group] = []
    if len(list1) == 0:
        for item2 in list2:
            # Flatten if item2 is the same type as parent
            if parent_type is not None and type(item2) is parent_type:
                result.append(list(item2))
            else:
                result.append([item2])
        return result
    for item1 in list1:
        for item2 in list2:
            # Flatten if item2 is the same type as parent
            if parent_type is not None and type(item2) is parent_type:
                combine = item1 + list(item2)
            else:
                combine = item1 + [item2]

            result.append(combine)
    return result


def check_leaf(node: Group) -> bool:
    if (
        type(node) is LeafGroup
        or type(node) is FallthroughGroup
        or type(node) is WildcardGroup
        or type(node) is AnythingGroup
        or type(node) is ChoiceGroup
        or type(node) is StartGroup
        or type(node) is EndGroup
    ):
        return True
    else:
        return False
