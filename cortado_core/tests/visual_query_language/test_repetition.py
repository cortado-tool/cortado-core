import pytest

from cortado_core.utils.split_graph import (
    ParallelGroup,
    SequenceGroup,
    LeafGroup,
    LoopGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


class TestExactRepetition:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    LoopGroup(lst=[LeafGroup(lst=["b"])], min_count=3, max_count=3),
                    LeafGroup(lst=["c"]),
                ]
            ),
            query_type=query_type,
        )

    def test_match(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert query.match(variant)

    def test_too_few_repetitions(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
        )

        assert not query.match(variant)

    def test_too_many_repetitions(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert not query.match(variant)


class TestRangeRepetition:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    LoopGroup(lst=[LeafGroup(lst=["b"])], min_count=2, max_count=4),
                    LeafGroup(lst=["c"]),
                ]
            ),
            query_type=query_type,
        )

    def test_min_repetitions(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert query.match(variant)

    def test_middle_repetitions(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert query.match(variant)

    def test_max_repetitions(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert query.match(variant)

    def test_too_few_repetitions(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
        )

        assert not query.match(variant)

    def test_too_many_repetitions(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )
        assert not query.match(variant)
