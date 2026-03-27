import pytest
from cortado_core.utils.split_graph import (
    SequenceGroup,
    LeafGroup,
    ParallelGroup,
    AnythingGroup,
    OptionalGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


class TestSingleAnything:

    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[LeafGroup(lst=["a"]), AnythingGroup(), LeafGroup(lst=["b"])]
            ),
            query_type=query_type,
        )

    @pytest.fixture
    def query2(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    AnythingGroup(),
                    LeafGroup(lst=["b"]),
                    LeafGroup(lst=["c"]),
                ]
            ),
            query_type=query_type,
        )

    def test_no_element_in_between(self, query):
        variant = SequenceGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"])])
        assert not query.match(variant)

    def test_single_element_in_between(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["x"]), LeafGroup(lst=["b"])]
        )

        assert query.match(variant)

    def test_multiple_elements_in_between(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["y"]),
                LeafGroup(lst=["b"]),
            ]
        )

        assert query.match(variant)

    def test_parallel_elements_in_between(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                ParallelGroup(lst=[LeafGroup(lst=["x"]), LeafGroup(lst=["y"])]),
                LeafGroup(lst=["b"]),
            ]
        )

        assert query.match(variant)

    def test_no_ending_element(self, query):
        variant = SequenceGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["x"])])

        assert not query.match(variant)

    def test_backtracking(self, query2):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert query2.match(variant)


class TestDoubleAnything:

    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    AnythingGroup(),
                    AnythingGroup(),
                    LeafGroup(lst=["b"]),
                ]
            ),
            query_type=query_type,
        )

    def test_one_element_between(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["x"]), LeafGroup(lst=["b"])]
        )

        assert not query.match(variant)

    def test_two_elements_between(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["y"]),
                LeafGroup(lst=["b"]),
            ]
        )

        assert query.match(variant)

    def test_multiple_elements_between(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["y"]),
                LeafGroup(lst=["z"]),
                LeafGroup(lst=["b"]),
            ]
        )

        assert query.match(variant)


class TestTwoAnythings:

    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    AnythingGroup(),
                    LeafGroup(lst=["b"]),
                    AnythingGroup(),
                    LeafGroup(lst=["c"]),
                ]
            ),
            query_type=query_type,
        )

    def test_fitting(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["y"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert query.match(variant)

    def test_missing_middle_element(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["y"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert not query.match(variant)

    def test_missing_gap(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["y"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert not query.match(variant)

        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        assert not query.match(variant)


class TestOptionalAnything:

    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    OptionalGroup(lst=[AnythingGroup()]),
                    LeafGroup(lst=["b"]),
                ]
            ),
            query_type=query_type,
        )

    def test_with_element_in_between(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["x"]), LeafGroup(lst=["b"])]
        )

        assert query.match(variant)

    def test_without_element_in_between(self, query):
        variant = SequenceGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"])])

        assert query.match(variant)
