from collections import deque
from typing import List, Set

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)


def get_first_match(
    label: str, leaves: List[ConcurrencyTree], rml_dfsid: int
) -> tuple[int | None, set[ConcurrencyTree] | None]:
    for idx, leaf in enumerate(leaves):
        if leaf.label == label:
            return idx, {leaf}
        if leaf.id > rml_dfsid:
            return -1, None
    return None, None


def get_all_matches(label: str, leaves: List[ConcurrencyTree]) -> Set[ConcurrencyTree]:
    matches = set()

    for leaf in leaves:
        if leaf.label == label:
            matches.add(leaf)

    return matches


def match_concurrent_pattern(
    pattern: ConcurrencyTree,
    tree_children: List[ConcurrencyTree],
    rml_dfsid: int,
    match_res: deque[ConcurrencyTree],
):
    for pattern_child in pattern.children:
        matches = None
        if (
            pattern_child.op is not None
        ):  # matching an op node, so must recurse down the tree
            for tree_child in tree_children:
                has_match, matches = is_matching(tree_child, pattern_child, rml_dfsid)
                if has_match and matches is not None:
                    matches.add(tree_child)
                if tree_child.id > rml_dfsid:  # to break out early if the rml is seen
                    break

        else:  # matching a leaf node, so just get all matches as the match is on a concurrent node
            matches = get_all_matches(pattern_child.label, tree_children)
            if len(matches) == 0:
                return False, None

        if matches is not None:
            tree_children = [
                t for t in tree_children if t not in matches
            ]  # remove the matched children from the list of children to match
            match_res.extend(matches)


def match_sequential_pattern(
    pattern: ConcurrencyTree,
    tree_children: List[ConcurrencyTree],
    rml_dfsid: int,
    match_res: deque[ConcurrencyTree],
):
    idx_tree_start = idx_pattern = 0
    idx_match_start = -1
    idx_tree_end = len(tree_children) - 1
    match_temp = deque()

    while (
        idx_tree_start < len(tree_children)
        and tree_children[idx_tree_start].id <= rml_dfsid
    ):
        if idx_pattern == len(
            pattern.children
        ):  # if all pattern nodes are matched, add the match and continue
            if (
                match_temp[-1].get_rml().id == rml_dfsid
            ):  # is it the pattern at the exact rml we're looking for? if yes, only then store this res and continue
                # otherwise just continue
                match_res.extend(match_temp)
            idx_tree_start = idx_match_start + 1
            match_temp.clear()
            idx_pattern = 0
            idx_match_start = -1
            idx_tree_end = len(tree_children) - 1
            continue

        pattern_child = pattern.children[idx_pattern]
        tree_children_to_check = tree_children[idx_tree_start : idx_tree_end + 1]

        matched_in_tree = False

        if (
            pattern_child.op is not None
        ):  # looking at an operator node, so must recurse down the tree
            for idx, tree_child in enumerate(tree_children_to_check):
                has_match, matches = is_matching(tree_child, pattern_child, rml_dfsid)

                if has_match and matches is not None:  # if a node match is found,
                    # prepare to compare the next pattern node with the next tree node
                    matches.append(tree_child)
                    match_temp.extend(matches)
                    idx_pattern += 1
                    if idx_match_start == -1:  # store the idx of first pattern match
                        idx_match_start = idx_tree_start + idx
                    idx_tree_start = idx_tree_end = idx_tree_start + idx + 1
                    matched_in_tree = True
                    break

        else:  # looking at a leaf node
            idx, match = get_first_match(
                pattern_child.label, tree_children_to_check, rml_dfsid
            )

            if (
                match is not None and idx != -1
            ):  # if a node match is found, prepare to compare the next pattern node with the next tree node
                match_temp.extend(match)
                idx_pattern += 1
                if idx_match_start == -1:  # store the idx of first pattern match
                    idx_match_start = idx_tree_start + idx
                idx_tree_start = idx_tree_end = idx_tree_start + idx + 1
                matched_in_tree = True

            elif idx == -1:  # if the rml is seen
                break

        if not matched_in_tree:  # if no match is found and rml wasn't also seen,
            # restart the search from the next tree node
            idx_pattern = 0
            idx_tree_start = idx_match_start + 1
            idx_match_start = -1
            idx_tree_end = len(tree_children) - 1
            match_temp.clear()

    match_res.extend(match_temp)


def is_matching(tree: ConcurrencyTree, pattern: ConcurrencyTree, rml_dfsid: int):
    if tree.op is None or tree.op != pattern.op:
        return False, None

    match_res = deque[ConcurrencyTree]()

    if pattern.op == cTreeOperator.Sequential:
        match_sequential_pattern(pattern, tree.children, rml_dfsid, match_res)

    else:
        match_concurrent_pattern(pattern, tree.children, rml_dfsid, match_res)

    return len(match_res) != 0, match_res


def locate_pattern(variant: ConcurrencyTree, pattern: ConcurrencyTree, rml_dfsid: int):
    if variant.op is None:
        return False, None

    has_match, matches = is_matching(variant, pattern, rml_dfsid)

    if has_match and matches is not None:
        matches.append(variant)

    return has_match, {m.id for m in matches}
