import pytest

from cortado_core.utils.split_graph import (
    ParallelGroup,
    SequenceGroup,
    LeafGroup,
    OptionalGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


class TestSingleOptional:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    OptionalGroup(lst=[LeafGroup(lst=["b"])]),
                    LeafGroup(lst=["c"]),
                ]
            ),
            query_type=query_type,
        )

    def test_element_present(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
        )

        assert query.match(variant)

    def test_element_absent(self, query):
        variant = SequenceGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["c"])])

        assert query.match(variant)

    def test_extra_element(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert not query.match(variant)


class TestOptionalGroup:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    OptionalGroup(
                        lst=[
                            SequenceGroup(
                                lst=[LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
                            )
                        ]
                    ),
                    LeafGroup(lst=["d"]),
                ]
            ),
            query_type=query_type,
        )

    def test_group_present(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
                LeafGroup(lst=["d"]),
            ]
        )

        assert query.match(variant)

    def test_group_absent(self, query):
        variant = SequenceGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["d"])])

        assert query.match(variant)

    def test_partial_group(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["d"]),
            ]
        )

        assert not query.match(variant)


class TestOptionalParallel:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    OptionalGroup(
                        lst=[
                            ParallelGroup(
                                lst=[LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
                            )
                        ]
                    ),
                    LeafGroup(lst=["d"]),
                ]
            ),
            query_type=query_type,
        )

    def test_parallel_present(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                    ]
                ),
                LeafGroup(lst=["d"]),
            ]
        )

        assert query.match(variant)

    def test_parallel_absent(self, query):
        variant = SequenceGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["d"])])

        assert query.match(variant)

    def test_other_parallel(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["e"]),
                    ]
                ),
                LeafGroup(lst=["d"]),
            ]
        )

        assert not query.match(variant)
