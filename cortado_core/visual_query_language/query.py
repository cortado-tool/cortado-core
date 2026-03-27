from enum import Enum
from cortado_core.utils.split_graph import SequenceGroup
from cortado_core.visual_query_language.expand_tree import expand_tree
from cortado_core.visual_query_language.matching_algorithm import match_sequential
from cortado_core.visual_query_language.dfs_matching import match_sequential_dfs
from cortado_core.visual_query_language.relaxng.query import (
    build_query as build_relaxng_query,
)
from cortado_core.visual_query_language.relaxng.variant import (
    build_variant as build_relaxng_variant,
)
from cortado_core.visual_query_language.virtual_machine.vm import compile_vm


class QueryType(Enum):
    BFS = 1
    DFS = 2
    RELAXED_NG = 3
    VM = 4
    VM_LAZY = 5


class PatternQuery:
    """
    Base class for pattern queries.
    """

    def match(self, variant: SequenceGroup) -> bool:
        raise NotImplementedError("Subclasses should implement this!")


class DFSCompareQuery(PatternQuery):
    def __init__(self, query: SequenceGroup):
        self.unfolded_trees = expand_tree(query)

    def match(self, variant: SequenceGroup) -> bool:
        for query in self.unfolded_trees:
            if self.__check_variant(variant, query):
                return True
        return False

    def __check_variant(self, variant: SequenceGroup, query: SequenceGroup) -> bool:
        """
        Check if the given variant matches the query pattern.

        Args:
            variant (Group): The variant to be checked.
            query (Group): The query pattern.

        Returns:
            bool: True if the variant matches the query, False otherwise.
        """

        return match_sequential_dfs(query, variant)


class CustomTreeCompareQuery(PatternQuery):
    def __init__(self, query: SequenceGroup):
        self.unfolded_trees = expand_tree(query)

    def match(self, variant: SequenceGroup) -> bool:
        for query in self.unfolded_trees:
            if self.__check_variant(variant, query):
                return True
        return False

    def __check_variant(self, variant: SequenceGroup, query: SequenceGroup) -> bool:
        """
        Check if the given variant matches the query pattern.

        Args:
            variant (Group): The variant to be checked.
            query (Group): The query pattern.

        Returns:
            bool: True if the variant matches the query, False otherwise.
        """

        return match_sequential(query, variant)


class RelaxNGQuery(PatternQuery):
    def __init__(self, query: SequenceGroup):
        self.relaxng_query = build_relaxng_query(query)

    def match(self, variant: SequenceGroup) -> bool:
        relaxng_variant = build_relaxng_variant(variant)
        return self.relaxng_query(relaxng_variant)


class VMQuery(PatternQuery):
    def __init__(self, query: SequenceGroup, use_debt):
        self.vm = compile_vm(query, use_debt)

    def match(self, variant):
        return self.vm.run(variant)


def create_query_instance(
    query: SequenceGroup, query_type: QueryType = QueryType.DFS
) -> PatternQuery:
    """
    Create an instance of a PatternQuery from a given query tree.
    """
    if query_type == QueryType.DFS:
        return DFSCompareQuery(query)
    elif query_type == QueryType.RELAXED_NG:
        return RelaxNGQuery(query)
    elif query_type == QueryType.VM:
        return VMQuery(query, False)
    elif query_type == QueryType.VM_LAZY:
        return VMQuery(query, True)
    return CustomTreeCompareQuery(query)
