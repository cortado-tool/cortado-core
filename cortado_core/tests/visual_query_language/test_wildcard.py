import pytest

from cortado_core.utils.split_graph import (
    ParallelGroup,
    SequenceGroup,
    LeafGroup,
    WildcardGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


class TestWildcard:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[LeafGroup(lst=["a"]), WildcardGroup(), LeafGroup(lst=["b"])]
            ),
            query_type=query_type,
        )

    def test_wildcard_matching(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["x"]), LeafGroup(lst=["b"])]
        )

        assert query.match(variant)

        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["y"]), LeafGroup(lst=["b"])]
        )

        assert query.match(variant)

    def test_wildcard_with_multiple_elements(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["y"]),
                LeafGroup(lst=["b"]),
            ]
        )

        assert not query.match(variant)

    def test_wildcard_parallel(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                ParallelGroup(lst=[LeafGroup(lst=["x"]), LeafGroup(lst=["y"])]),
                LeafGroup(lst=["b"]),
            ]
        )

        assert not query.match(variant)
