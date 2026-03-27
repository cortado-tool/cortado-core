from typing import List

from cortado_core.utils.split_graph import (
    Group,
    StartGroup,
    EndGroup,
    ParallelGroup,
    SequenceGroup,
    AnythingGroup,
    FallthroughGroup,
    LeafGroup,
)
from cortado_core.visual_query_language.matching_functions import match


def check_start_point(query: List[Group], variant: List[Group]) -> bool:
    """Checks if the start point in the variant matches just after the start node in the query."""

    if variant.list_length() == 0:
        return False

    if not match(query[1], variant[0]):
        return False

    return True


def check_end_point(query: List[Group], variant: List[Group]) -> bool:
    """Checks if the end point in the variant matches just before the end node in the query."""

    if variant.list_length() == 0:
        return False

    if not match(query[-2], variant[-1]):
        return False

    return True


def match_sequential(query: SequenceGroup, variant: SequenceGroup) -> bool:
    """
    Given a pattern [query] and a variant [variant], checks if the variant matches the query pattern.
    """
    # Cannot use len() because it computes not the elements of the list but the "longest path"
    query_length = query.list_length()
    variant_length = variant.list_length()

    if query_length == 0:
        return True

    has_start_point = isinstance(query[0], StartGroup)
    has_end_point = isinstance(query[-1], EndGroup)

    # Edge case: Query only consists of a start or end point -> matches anything
    if variant_length == 1 and (has_start_point or has_end_point):
        return True

    if has_start_point and not check_start_point(query, variant):
        return False

    if has_end_point and not check_end_point(query, variant):
        return False

    # Walk the query and varianat backwards
    if has_end_point:
        query = SequenceGroup(lst=query[::-1])
        variant = SequenceGroup(lst=variant[::-1])
        query_length = query.list_length()
        variant_length = variant.list_length()

    candidates = []  # Possible candidates with unchecked subproblems
    subproblems = []  # Subproblems/Subtrees of possible candidate for later checking

    offset = 1 if (has_start_point or has_end_point) else 0
    idxTarget = (
        query_length - 1 if (has_start_point and has_end_point) else query_length
    )

    idxQuery = offset
    idxVariant = 0

    while idxQuery < query_length and idxVariant < variant_length:

        if isinstance(query[idxQuery], AnythingGroup):
            # 1. Anything found: We cannot proceed linearly.
            # We must try to "consume" 1 element, then 2, then 3...
            # and see if the REST of the query matches the REST of the variant.

            # First, verify the subproblems we collected BEFORE this AnythingGroup.
            # If the part before the AnythingGroup is invalid, skip or return false
            prefix_match = True
            for sub_q, sub_v in subproblems:
                if not match_parallel(sub_q, sub_v):
                    prefix_match = False
                    break
            # Return false if we have a start point and the subproblem does not match
            if has_start_point and not prefix_match:
                return False

            found_anything_match = False
            if prefix_match:
                if handle_anything(query, variant, idxQuery, idxVariant):
                    return True

            # Otherwise, reset and slide the window
            if idxQuery == 0 + (has_start_point or has_end_point):
                idxVariant += 1
            idxQuery = 0 + (has_start_point or has_end_point)
            subproblems = []
            continue

        if not match(query[idxQuery], variant[idxVariant]):
            # Query has start point and there is a missmatch, return false
            # (same for end_point because we reverse the list)
            if has_start_point or has_end_point:
                return False

            # 1. Calculate how many items we matched in this current attempt: (idxQuery - offset)
            # 2. Rewind idxVariant to the start of this attempt, then advance by 1 (Catch overlapping sequences)
            idxVariant = idxVariant - (idxQuery - offset) + 1
            idxQuery = offset
            subproblems = []

        else:
            # Parallel are treated as subproblems -> only needs to be checked if the sequential parts match
            if isinstance(variant[idxVariant], ParallelGroup):
                subproblems.append((query[idxQuery], variant[idxVariant]))

            idxQuery += 1
            idxVariant += 1

            # End of query reached -> all sequential parts matched -> possible candiate found
            if idxQuery == idxTarget:
                # Match must be from start to end -> variant must also be fully consumed
                if has_start_point and has_end_point:
                    if idxVariant == variant_length:
                        candidates.append(subproblems)
                    else:
                        return False

                else:
                    candidates.append(subproblems)
                    subproblems = []

                    idxVariant -= query_length - has_start_point - has_end_point - 1
                    idxQuery = 0 + (has_start_point or has_end_point)

                # If start or end point is present, we are done after first match (other candidates would not be aligned to start/end)
                if has_start_point or has_end_point:
                    break

    for candidate in candidates:
        for subquery, subvariant in candidate:
            if not match_parallel(subquery, subvariant):
                break
        else:
            return True

    return False


def match_parallel(query: ParallelGroup, variant: ParallelGroup) -> bool:
    """
    Match a ParallelGroup query against a ParallelGroup variant.

    For parallel matching: every branch in the query must find a matching
    branch in the variant, AND every branch in the variant must be matched.
    This ensures exact structural match (no extra branches in variant).
    Order doesn't matter.

    Uses backtracking DFS to correctly handle overlapping ChoiceGroups where
    a single variant branch could potentially match multiple query branches.
    Also handles AnythingGroup which can match 1 or more variant branches.

    Args:
        query: ParallelGroup from the query
        variant: ParallelGroup from the variant

    Returns:
        True if query and variant have matching branches (bijective match)
    """

    # at least as many variant branches as query branches for match (anything group can be more ofc)
    if variant.list_length() < query.list_length():
        return False

    # Use backtracking to find a valid assignment
    def backtrack(q_idx: int, used: set) -> bool:
        """
        Recursively try to match remaining query branches to unused variant branches.

        Args:
            q_idx: Current query branch index
            used: Set of variant branch indices already assigned

        Returns:
            True if remaining query branches can be matched to remaining variant branches
        """
        # Base case: all query branches have been matched
        if q_idx == query.list_length():
            # All variant branches should be used (bijective match)
            return len(used) == variant.list_length()

        q_branch = query[q_idx]

        # Special handling for AnythingGroup: try matching 1, 2, 3, ... unused variant branches
        if isinstance(q_branch, AnythingGroup):
            unused_indices = [i for i in range(variant.list_length()) if i not in used]
            # Try consuming 1, 2, 3, ... unused variant branches with AnythingGroup
            for consume_count in range(1, len(unused_indices) + 1):
                # Take the first consume_count unused branches
                branches_to_use = unused_indices[:consume_count]
                # Mark them as used
                for v_idx in branches_to_use:
                    used.add(v_idx)

                if backtrack(q_idx + 1, used):
                    return True

                # Backtrack: remove from used set
                for v_idx in branches_to_use:
                    used.remove(v_idx)

            return False

        # Regular branch matching: try matching this query branch against each unused variant branch
        for v_idx in range(variant.list_length()):
            if v_idx not in used:
                if _branches_match(q_branch, variant[v_idx]):
                    # Found a match, mark it as used and continue
                    used.add(v_idx)
                    if backtrack(q_idx + 1, used):
                        return True
                    # Backtrack: remove from used set and try next variant branch
                    used.remove(v_idx)

                    if isinstance(q_branch, FallthroughGroup) or isinstance(
                        q_branch, LeafGroup
                    ):
                        # No need to try further variant branches for FallthroughGroup or LeafGroup
                        break

        return False

    return backtrack(0, set())


def _branches_match(q_branch: Group, v_branch: Group) -> bool:
    """
    Check if a single query branch matches a single variant branch.

    Args:
        q_branch: A branch from the query ParallelGroup
        v_branch: A branch from the variant ParallelGroup

    Returns:
        True if the branches match
    """
    # Both are SequenceGroups - use sequential matching
    if isinstance(q_branch, SequenceGroup) and isinstance(v_branch, SequenceGroup):
        return match_sequential(q_branch, v_branch)

    # Both are ParallelGroups - recursive parallel matching
    if isinstance(q_branch, ParallelGroup) and isinstance(v_branch, ParallelGroup):
        return match_parallel(q_branch, v_branch)

    # Leaf-level comparison (LeafGroup, ChoiceGroup, WildcardGroup, etc.)
    # Use match() from matching_functions.py
    return match(q_branch, v_branch)


def handle_anything(
    full_query: SequenceGroup,
    full_variant: SequenceGroup,
    q_idx: int,
    v_idx: int,
) -> bool:
    """
    Helper to handle the 'Anything' operator.
    It tries to consume k items from the variant (k=1 to remaining),
    and recursively checks if the remainder matches using match_sequential.
    """
    # Create the rest of the query (skip the AnythingGroup itself)
    # We wrap it in SequenceGroup to be compatible with match_sequential
    query_remainder = SequenceGroup(lst=full_query[q_idx + 1 :])

    # Calculate how many items are left in the variant
    variant_remaining_len = full_variant.list_length() - v_idx

    # AnythingGroup is greedy/variable: It consumes 'consume_len' items.
    # It must consume at least 1 item
    # It can consume up to the end of the variant.
    for consume_len in range(1, variant_remaining_len + 1):

        # Calculate where the remainder of the variant starts
        next_v_idx = v_idx + consume_len

        # Get the variant remainder
        variant_remainder = SequenceGroup(lst=full_variant[next_v_idx:])

        if match_sequential(query_remainder, variant_remainder):
            return True

    return False
