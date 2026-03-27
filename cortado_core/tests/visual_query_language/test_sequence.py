import pytest
from cortado_core.utils.split_graph import (
    SequenceGroup,
    ParallelGroup,
    LeafGroup,
    StartGroup,
    EndGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


class TestSimpleSequence:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
            ),
            query_type=query_type,
        )

    def test_exact_match(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
        )

        assert query.match(variant)

    def test_with_prefix(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert query.match(variant)

    def test_with_suffix(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                LeafGroup(lst=["y"]),
            ]
        )

        assert query.match(variant)

    def test_within(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                LeafGroup(lst=["y"]),
            ]
        )

        assert query.match(variant)

    def test_non_matching(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["x"]), LeafGroup(lst=["c"])]
        )

        assert not query.match(variant)

    def test_wrong_order(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["c"]), LeafGroup(lst=["b"]), LeafGroup(lst=["a"])]
        )

        assert not query.match(variant)


class TestOverlappingSequence:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    LeafGroup(lst=["b"]),
                    LeafGroup(lst=["c"]),
                    LeafGroup(lst=["a"]),
                    LeafGroup(lst=["b"]),
                    LeafGroup(lst=["d"]),
                ]
            ),
            query_type=query_type,
        )

    @pytest.fixture
    def parallel_query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    LeafGroup(lst=["b"]),
                    LeafGroup(lst=["c"]),
                    ParallelGroup(lst=[LeafGroup(lst=["d"]), LeafGroup(lst=["e"])]),
                    LeafGroup(lst=["a"]),
                    LeafGroup(lst=["b"]),
                    LeafGroup(lst=["c"]),
                ],
            ),
            query_type=query_type,
        )

    def test_overlapping_match(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["d"]),
            ]
        )

        assert query.match(variant)

    def test_parallel_overlapping_match(self, parallel_query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                ParallelGroup(lst=[LeafGroup(lst=["x"]), LeafGroup(lst=["y"])]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                ParallelGroup(lst=[LeafGroup(lst=["d"]), LeafGroup(lst=["e"])]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert parallel_query.match(variant)

        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                ParallelGroup(lst=[LeafGroup(lst=["d"]), LeafGroup(lst=["e"])]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                ParallelGroup(lst=[LeafGroup(lst=["x"]), LeafGroup(lst=["y"])]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert parallel_query.match(variant)

    def test_wrong_parallel(self, parallel_query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                ParallelGroup(lst=[LeafGroup(lst=["x"]), LeafGroup(lst=["y"])]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                ParallelGroup(lst=[LeafGroup(lst=["x"]), LeafGroup(lst=["y"])]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert not parallel_query.match(variant)


class TestMixSequenceParallel:

    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    ParallelGroup(
                        lst=[
                            LeafGroup(lst=["b"]),
                            SequenceGroup(
                                lst=[LeafGroup(lst=["c"]), LeafGroup(lst=["d"])]
                            ),
                        ]
                    ),
                    LeafGroup(lst=["e"]),
                ],
            ),
            query_type=query_type,
        )

    def test_matching(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                ParallelGroup(
                    lst=[
                        SequenceGroup(lst=[LeafGroup(lst=["c"]), LeafGroup(lst=["d"])]),
                        LeafGroup(lst=["b"]),
                    ]
                ),
                LeafGroup(lst=["e"]),
            ]
        )

        assert query.match(variant)
