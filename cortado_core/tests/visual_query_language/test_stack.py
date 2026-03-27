import pytest

from cortado_core.utils.split_graph import (
    SequenceGroup,
    ParallelGroup,
    LeafGroup,
    ChoiceGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


class TestSimpleStack:

    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    LeafGroup(lst=["a"]),
                    ChoiceGroup(lst=[LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]),
                    LeafGroup(lst=["d"]),
                ]
            ),
            query_type=query_type,
        )

    def test_choice1(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"]), LeafGroup(lst=["d"])]
        )

        assert query.match(variant)

    def test_choice2(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["c"]), LeafGroup(lst=["d"])]
        )

        assert query.match(variant)

    def test_non_matching(self, query):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["e"]), LeafGroup(lst=["d"])]
        )

        assert not query.match(variant)

    def test_additional_elements(self, query):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["x"]),
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["d"]),
                LeafGroup(lst=["y"]),
            ]
        )

        assert query.match(variant)
