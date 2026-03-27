"""
DFS-based matching algorithm for visual query language.

This module provides depth-first search based matching of query patterns against
process variants. The query can contain special constructs like:
- LeafGroup: matches a specific activity
- ChoiceGroup: matches any of several activities
- WildcardGroup: matches any single activity
- AnythingGroup: matches 1 or more consecutive elements (leaves or subtrees)
- ParallelGroup: matches parallel branches (order doesn't matter)
- StartGroup/EndGroup: anchors the match to start/end of variant

The variant only contains: LeafGroup, SequenceGroup, ParallelGroup (nested).

NOTE: LoopGroup and OptionalGroup are handled by unfold_tree.py which expands
them into multiple query variants before this matching code is called.
LoopGroup is unrolled for any number of nested subgroups.
"""

from typing import List

from cortado_core.utils.split_graph import (
    Group,
    StartGroup,
    EndGroup,
    ParallelGroup,
    SequenceGroup,
    LeafGroup,
    AnythingGroup,
    ChoiceGroup,
    FallthroughGroup,
)
from cortado_core.visual_query_language.matching_functions import match


def match_sequential_dfs(query: SequenceGroup, variant: SequenceGroup) -> bool:
    """
    Main entry point: Check if query pattern exists in variant using DFS.

    Args:
        query: The query pattern (SequenceGroup, may contain special groups)
        variant: The variant to search in (SequenceGroup with only Leaf/Sequence/Parallel)

    Returns:
        True if query matches somewhere in variant, False otherwise.
    """
    query_list = list(query)
    variant_list = list(variant)

    # Handle empty cases
    if len(query_list) == 0:
        return True
    if len(variant_list) == 0:
        return False

    # Check for StartGroup and EndGroup anchors
    has_start = isinstance(query_list[0], StartGroup)
    has_end = isinstance(query_list[-1], EndGroup)

    # Determine the actual query content (excluding Start/End markers)
    # query_start: first index of actual content
    # query_end: last index of actual content (inclusive)
    query_start = 1 if has_start else 0
    query_end = len(query_list) - 2 if has_end else len(query_list) - 1

    # Edge case: query is only StartGroup and/or EndGroup with no content
    if query_start > query_end:
        return True

    # If anchored to start, we must begin matching at variant index 0
    if has_start:
        return _dfs_match(query_list, variant_list, query_start, 0, query_end, has_end)

    # If not anchored to start, try matching from each position in variant
    for variant_start in range(len(variant_list)):
        if _dfs_match(
            query_list, variant_list, query_start, variant_start, query_end, has_end
        ):
            return True

    return False


def _dfs_match(
    query_list: List[Group],
    variant_list: List[Group],
    q_idx: int,
    v_idx: int,
    q_end: int,
    must_consume_all: bool,
) -> bool:
    """
    Recursive DFS matching function.

    Args:
        query_list: List of query elements
        variant_list: List of variant elements
        q_idx: Current index in query (what we're trying to match)
        v_idx: Current index in variant (where we're looking)
        q_end: Last index in query to match (inclusive)
        must_consume_all: If True, variant must be fully consumed when query ends

    Returns:
        True if we can match query[q_idx:q_end+1] against variant starting at v_idx
    """
    # Base case 1: We've matched all query elements
    if q_idx > q_end:
        if must_consume_all:
            # With EndGroup, variant must also be fully consumed
            return v_idx >= len(variant_list)
        else:
            # Without EndGroup, we're done (remaining variant is OK)
            return True

    # Base case 2: Variant exhausted but query has more elements
    if v_idx >= len(variant_list):
        # Check if remaining query is all AnythingGroups that could match empty
        # Actually, AnythingGroup needs at least 1 element, so this fails
        return False

    current_query = query_list[q_idx]
    current_variant = variant_list[v_idx]

    # --- Handle AnythingGroup: matches 1 or more variant elements ---
    if isinstance(current_query, AnythingGroup):
        return _match_anything_group(
            query_list, variant_list, q_idx, v_idx, q_end, must_consume_all
        )

    # --- Handle ParallelGroup in query ---
    if isinstance(current_query, ParallelGroup):
        # Variant element must also be ParallelGroup
        if not isinstance(current_variant, ParallelGroup):
            return False

        # Check if the parallel groups match
        if not match_parallel(current_query, current_variant):
            return False

        # Continue with next elements
        return _dfs_match(
            query_list, variant_list, q_idx + 1, v_idx + 1, q_end, must_consume_all
        )

    # --- Handle SequenceGroup nested in query ---
    if isinstance(current_query, SequenceGroup):
        # Variant element must also be SequenceGroup
        if not isinstance(current_variant, SequenceGroup):
            return False

        # Recursively match the nested sequences
        if not match_sequential_dfs(current_query, current_variant):
            return False

        # Continue with next elements
        return _dfs_match(
            query_list, variant_list, q_idx + 1, v_idx + 1, q_end, must_consume_all
        )

    # --- Handle leaf-level matching (LeafGroup, ChoiceGroup, WildcardGroup, etc.) ---
    # Use the match() function from matching_functions.py
    if match(current_query, current_variant):
        # Match succeeded, continue to next elements
        return _dfs_match(
            query_list, variant_list, q_idx + 1, v_idx + 1, q_end, must_consume_all
        )

    # No match at this position
    return False


def _match_anything_group(
    query_list: List[Group],
    variant_list: List[Group],
    q_idx: int,
    v_idx: int,
    q_end: int,
    must_consume_all: bool,
) -> bool:
    """
    Handle AnythingGroup matching with backtracking. AnythingGroup matches 1 or more
    consecutive variant elements (can be leaves or entire subtrees).

    We try consuming 1 element, then 2, then 3, etc. until we find a valid
    continuation or run out of variant elements. Uses backtracking to explore all
    possible consumption amounts.

    Args:
        query_list: List of query elements
        variant_list: List of variant elements
        q_idx: Index of the AnythingGroup in query
        v_idx: Current index in variant
        q_end: Last index in query to match (inclusive)
        must_consume_all: If True, variant must be fully consumed when query ends

    Returns:
        True if AnythingGroup can be matched and rest of query succeeds
    """
    remaining_variant = len(variant_list) - v_idx

    # Try consuming 1, 2, 3, ... elements with AnythingGroup using backtracking
    # We need at least 1 element for AnythingGroup
    for consume_count in range(1, remaining_variant + 1):
        # After consuming 'consume_count' elements, try to match the rest
        new_v_idx = v_idx + consume_count

        if _dfs_match(
            query_list, variant_list, q_idx + 1, new_v_idx, q_end, must_consume_all
        ):
            return True
        # If rest of query fails with this consumption, backtrack and try more elements

    # No valid consumption amount worked
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
        return match_sequential_dfs(q_branch, v_branch)

    # Both are ParallelGroups - recursive parallel matching
    if isinstance(q_branch, ParallelGroup) and isinstance(v_branch, ParallelGroup):
        return match_parallel(q_branch, v_branch)

    # Leaf-level comparison (LeafGroup, ChoiceGroup, WildcardGroup, etc.)
    # Use match() from matching_functions.py
    return match(q_branch, v_branch)
