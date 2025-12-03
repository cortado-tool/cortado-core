from cortado_core.utils.split_graph import SequenceGroup
from cortado_core.visual_query_language.matching_algorithm import match_sequential
from cortado_core.visual_query_language.relaxng.query import build_query
from cortado_core.visual_query_language.relaxng.variant import build_variant
from typing import List


def check_variant(
    variant: SequenceGroup, query: SequenceGroup, activities: List[str]
) -> bool:
    """
    Check if the given variant matches the query pattern.

    Args:
        variant (Group): The variant to be checked.
        query (Group): The query pattern.
        activities (List[str]): List of all possible activites in the variant.

    Returns:
        bool: True if the variant matches the query, False otherwise.
    """

    ngquery = build_query(query)
    ngvariant = build_variant(variant)

    return ngquery(ngvariant)
