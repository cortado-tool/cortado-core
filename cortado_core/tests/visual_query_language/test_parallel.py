import pytest

from cortado_core.utils.split_graph import (
    LeafGroup,
    ParallelGroup,
    SequenceGroup,
    AnythingGroup,
    ChoiceGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


class TestSimpleParallel:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    ParallelGroup(
                        lst=[
                            LeafGroup(lst=["a"]),
                            LeafGroup(lst=["b"]),
                            LeafGroup(lst=["c"]),
                        ]
                    )
                ]
            ),
            query_type=query_type,
        )

    def test_exact_match(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["a"]),
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                    ]
                )
            ]
        )

        assert query.match(variant)

    def test_different_order(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["c"]),
                        LeafGroup(lst=["a"]),
                        LeafGroup(lst=["b"]),
                    ]
                )
            ]
        )

        assert query.match(variant)

    def test_additional_element(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["a"]),
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                        LeafGroup(lst=["d"]),
                    ]
                )
            ]
        )

        assert not query.match(variant)

    def test_missing_element(self, query):
        variant = SequenceGroup(
            lst=[ParallelGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"])])]
        )

        assert not query.match(variant)


class TestAnythingParallel:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    ParallelGroup(
                        lst=[
                            LeafGroup(lst=["a"]),
                            AnythingGroup(),
                        ]
                    )
                ]
            ),
            query_type=query_type,
        )

    def test_empty(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["a"]),
                    ]
                )
            ]
        )

        assert not query.match(variant)

    def test_single_element(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["a"]),
                        LeafGroup(lst=["b"]),
                    ]
                )
            ]
        )

        assert query.match(variant)

    def test_multiple_elements(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["a"]),
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                        LeafGroup(lst=["d"]),
                    ]
                )
            ]
        )

        assert query.match(variant)

    def test_missing_required_element(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                    ]
                )
            ]
        )

        assert not query.match(variant)


class TestChoiceParallel:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                lst=[
                    ParallelGroup(
                        lst=[
                            ChoiceGroup(
                                lst=[
                                    LeafGroup(lst=["a"]),
                                    LeafGroup(lst=["b"]),
                                ]
                            ),
                            ChoiceGroup(
                                lst=[
                                    LeafGroup(lst=["b"]),
                                    LeafGroup(lst=["c"]),
                                ]
                            ),
                            LeafGroup(lst=["a"]),
                        ]
                    )
                ]
            ),
            query_type=query_type,
        )

    def test_choice_match(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["a"]),
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                    ]
                )
            ]
        )

        assert query.match(variant)

    def test_single_take(self, query):
        variant = SequenceGroup(
            lst=[
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["a"]),
                    ]
                )
            ]
        )

        assert query.match(variant)


class TestLargeParallel:
    @pytest.fixture
    def query(self, query_type):
        return create_query_instance(
            SequenceGroup(
                [ParallelGroup(lst=[LeafGroup(["a"])] * 10 + [LeafGroup(["b"])])]
            ),
            query_type=query_type,
        )

    @pytest.mark.timeout(5)
    def test_match(self, query):
        variant = SequenceGroup(
            [ParallelGroup(lst=[LeafGroup(["a"])] * 10 + [LeafGroup(["b"])])]
        )

        assert query.match(variant)

    @pytest.mark.timeout(5)
    def test_missing_last_element(self, query):
        variant = SequenceGroup(
            [ParallelGroup(lst=[LeafGroup(["a"])] * 10 + [LeafGroup(["c"])])]
        )

        assert not query.match(variant)
