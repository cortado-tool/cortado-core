from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.util import (
    enforce_left_completeness_for_children,
    is_sequential_completeness_violated,
    get_ef_activities_between,
    get_ef_labeled_nodes_right_of,
    get_occurrences_for_ef_check,
    get_child_sequential_indexes_to_ensure_left_completeness,
    left_completeness_violated,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import get_index
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    is_eventually_follows_relation,
    get_preorder_sorted_pattern_nodes,
    get_left_sub_pattern,
    get_root,
    get_rightmost_leaf,
    get_leftmost_leaf,
    get_left_sibling,
    is_on_rightmost_path,
    get_right_sibling,
    get_right_siblings,
    get_siblings_in_between,
    get_rightmost_path_preorder_indexes,
)


def transaction_blanket_contains_elements(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    if right_transaction_blanket_contains_elements(pattern, occurrence_list):
        return True

    return left_transaction_blanket_contains_elements(pattern, occurrence_list)


def left_transaction_blanket_contains_elements(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    if __check_eventually_follows_left_blanket(pattern, occurrence_list):
        return True

    return __check_insertion_in_sub_patterns(pattern, occurrence_list)


def right_transaction_blanket_contains_elements(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    if __check_inner_node_insertions_on_rightmost_path(pattern, occurrence_list):
        return True

    return __check_eventually_follows_right_blanket(pattern, occurrence_list)


def __check_eventually_follows_left_blanket(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    """
    Checks if it is possible to insert an new transaction-matched subpattern with one activity between two existing
    subpatterns

    :param pattern:
    :param occurrence_list:
    :return:
    """
    possible_insert_positions = range(len(pattern.sub_patterns))

    for insert_position in possible_insert_positions:
        if __check_for_eventually_follows_insert_position(
            pattern, occurrence_list, insert_position
        ):
            return True

    return False


def __check_eventually_follows_right_blanket(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    possible_labels = None
    for tree_id, ol in occurrence_list.items():
        possible_labels_for_tree = set()
        for occurrences in ol:
            possible_nodes = get_ef_labeled_nodes_right_of(
                occurrences[pattern.sub_patterns[-1].id],
                occurrences[pattern.rightmost_leaf.id],
            )

            possible_labels_for_tree = possible_labels_for_tree.union(
                set([n.label for n in possible_nodes])
            )

        if possible_labels is None:
            possible_labels = possible_labels_for_tree
        else:
            possible_labels = possible_labels.intersection(possible_labels_for_tree)

        if len(possible_labels) == 0:
            return False

    return True


def __check_for_eventually_follows_insert_position(
    pattern: EventuallyFollowsPattern, occurrence_list, insert_position
):
    possible_labels = None
    for tree_id, ol in occurrence_list.items():
        possible_labels_tree = set()
        for occurrences in ol:
            possible_nodes = get_ef_activities_between(
                *get_occurrences_for_ef_check(pattern, insert_position, occurrences)
            )
            possible_labels_tree = possible_labels_tree.union(
                set([n.label for n in possible_nodes])
            )

        if possible_labels is None:
            possible_labels = possible_labels_tree
        else:
            possible_labels = possible_labels.intersection(possible_labels_tree)

        if len(possible_labels) == 0:
            return False

    return True


def __check_insertion_in_sub_patterns(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    """
    Checks if there is an insertion position in one of the subpatterns that is not a new rightmost leaf, which is
    transaction-matched with the current pattern. We don't have to check if we can add a new root to one of the
    subpatterns, as this would result per definition in an incomplete tree (we create a root with a single child).
    For sequence nodes, we know that we can only add nodes before or after, but never in between.
    :param pattern:
    :param occurrence_list:
    :return:
    """
    pattern_node_by_preorder_index = get_preorder_sorted_pattern_nodes(pattern)
    insert_positions = range(sum([len(sp) for sp in pattern.sub_patterns]))
    for insert_position in insert_positions:
        node = pattern_node_by_preorder_index[insert_position]
        if node.parent is None:
            continue
        if node.parent.operator != cTreeOperator.Sequential:
            if __check_concurrent_fallthrough_insertion_for_node(
                occurrence_list, node, insert_position
            ):
                return True
        else:
            if __check_sequential_insertion_for_node(
                pattern, occurrence_list, node, insert_position
            ):
                return True

    return False


def __check_sequential_insertion_for_node(
    pattern: EventuallyFollowsPattern,
    occurrence_list,
    node: SubPattern,
    insert_position: int,
) -> bool:
    left_sub_pattern = get_left_sub_pattern(pattern, get_root(node))
    return __check_sequential_insertion_in_front_of_node(
        left_sub_pattern, occurrence_list, node, insert_position
    )


def __check_sequential_insertion_in_front_of_node(
    left_sub_pattern: SubPattern,
    occurrence_list,
    node: SubPattern,
    insert_position: int,
) -> bool:
    # we can only insert in front of the first child of a sequential operator
    if get_index(node.parent.children, node) != 0:
        return False

    if left_sub_pattern is not None:
        left_rml_id = get_rightmost_leaf(left_sub_pattern).id
        left_ro_id = left_sub_pattern.id

    root = get_root(node)
    leftmost_leaf = get_leftmost_leaf(root)
    # we have to check if the new pattern violates the ef constraint
    # sequential children below a concurrent operator never change the result of the ef constraint, because we
    # have to include always at least one label node under the concurrent operator
    do_eventually_follows_check = left_sub_pattern is not None and id(
        node.parent
    ) == id(root)
    indexes_to_ensure_left_completeness = (
        get_child_sequential_indexes_to_ensure_left_completeness(node.parent)
    )
    do_left_completeness_check = len(indexes_to_ensure_left_completeness) != 0

    possible_labels = None
    for tree_id, ol in occurrence_list.items():
        possible_labels_for_tree = set()
        for occurrences in ol:
            new_possible_node = get_left_sibling(occurrences[insert_position])
            if new_possible_node is None or new_possible_node.label is None:
                continue

            if do_left_completeness_check and left_completeness_violated(
                occurrences, indexes_to_ensure_left_completeness
            ):
                continue

            if do_eventually_follows_check:
                if occurrences[leftmost_leaf.id].id < new_possible_node.id:
                    continue
                if not is_eventually_follows_relation(
                    (
                        occurrences[left_rml_id],
                        occurrences[left_rml_id],
                        [occurrences[left_ro_id]],
                    ),
                    (new_possible_node, new_possible_node, [occurrences[root.id]]),
                ):
                    continue

            possible_labels_for_tree.add(new_possible_node.label)

        if possible_labels is None:
            possible_labels = possible_labels_for_tree
        else:
            possible_labels = possible_labels.intersection(possible_labels_for_tree)

        if len(possible_labels) == 0:
            return False

    return True


def __check_sequential_insertion_after_node(
    pattern: EventuallyFollowsPattern, occurrence_list, insert_position: int
) -> bool:
    possible_labels = None
    rightmost_leaf_id = pattern.rightmost_leaf.id

    for tree_id, ol in occurrence_list.items():
        possible_labels_for_tree = set()

        for occurrences in ol:
            if is_sequential_completeness_violated(
                occurrences[insert_position], occurrences[rightmost_leaf_id]
            ):
                continue

            new_possible_node = occurrences[insert_position].rSib
            if new_possible_node is None or new_possible_node.label is None:
                continue

            possible_labels_for_tree.add(new_possible_node.label)

        if possible_labels is None:
            possible_labels = possible_labels_for_tree
        else:
            possible_labels = possible_labels.intersection(possible_labels_for_tree)

        if len(possible_labels) == 0:
            return False

    return True


def __check_insertion_as_child_of_rightmost_leaf(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    rml = pattern.rightmost_leaf

    if rml.operator is None:
        return False

    possible_labels = None
    rml_position = rml.id

    for tree_id, ol in occurrence_list.items():
        possible_labels_in_tree = set()
        for occurrences in ol:
            check_only_first_child = enforce_left_completeness_for_children(rml)

            if check_only_first_child:
                new_possible_nodes = [occurrences[rml_position].children[0]]
            else:
                new_possible_nodes = occurrences[rml_position].children

            possible_labels_in_tree = possible_labels_in_tree.union(
                set([n.label for n in new_possible_nodes if n.label is not None])
            )

        if possible_labels is None:
            possible_labels = possible_labels_in_tree
        else:
            possible_labels = possible_labels.intersection(possible_labels_in_tree)

        if len(possible_labels) == 0:
            return False

    return True


def __check_concurrent_fallthrough_insertion_for_node(
    occurrence_list, node: SubPattern, insert_position: int
) -> bool:
    check_also_right_candidate = (
        not is_on_rightmost_path(node)
        and get_right_sibling(node) is None
        and node.operator is None
    )
    if check_also_right_candidate:
        if __check_concurrent_fallthrough_insertion_after_node(
            occurrence_list, insert_position
        ):
            return True

    return __check_concurrent_fallthrough_insertion_in_front_of_node(
        occurrence_list, node, insert_position
    )


def __check_concurrent_fallthrough_insertion_after_node(
    occurrence_list, insert_position: int
) -> bool:
    possible_labels = None
    for tree_id, ol in occurrence_list.items():
        possible_labels_for_tree = set()
        for occurrences in ol:
            possible_nodes = get_right_siblings(occurrences[insert_position])
            possible_labels_for_tree = possible_labels_for_tree.union(
                set([n.label for n in possible_nodes if n.label is not None])
            )

        if possible_labels is None:
            possible_labels = possible_labels_for_tree
        else:
            possible_labels = possible_labels.intersection(possible_labels_for_tree)

        if len(possible_labels) == 0:
            return False

    return True


def __check_concurrent_fallthrough_insertion_in_front_of_node(
    occurrence_list, node: SubPattern, insert_position: int
) -> bool:
    left_sibling = get_left_sibling(node)
    possible_labels = None
    for tree_id, ol in occurrence_list.items():
        possible_labels_for_tree = set()
        for occurrences in ol:
            if left_sibling is None:
                possible_nodes = get_siblings_in_between(
                    None, occurrences[insert_position]
                )
            else:
                possible_nodes = get_siblings_in_between(
                    occurrences[left_sibling.id], occurrences[insert_position]
                )

            possible_labels_for_tree = possible_labels_for_tree.union(
                set([n.label for n in possible_nodes if n.label is not None])
            )

        if possible_labels is None:
            possible_labels = possible_labels_for_tree
        else:
            possible_labels = possible_labels.intersection(possible_labels_for_tree)

        if len(possible_labels) == 0:
            return False

    return True


def __check_inner_node_insertions_on_rightmost_path(
    pattern: EventuallyFollowsPattern, occurrence_list
) -> bool:
    insert_positions = get_rightmost_path_preorder_indexes(pattern.rightmost_leaf)
    pattern_node_by_preorder_index = get_preorder_sorted_pattern_nodes(pattern)

    if __check_insertion_as_child_of_rightmost_leaf(pattern, occurrence_list):
        return True

    for height_diff, insert_position in enumerate(insert_positions):
        node = pattern_node_by_preorder_index[insert_position]
        if node.parent is None:
            continue
        if node.parent.operator != cTreeOperator.Sequential:
            if __check_concurrent_fallthrough_insertion_after_node(
                occurrence_list, insert_position
            ):
                return True
        else:
            if __check_sequential_insertion_after_node(
                pattern, occurrence_list, insert_position
            ):
                return True

    return False
