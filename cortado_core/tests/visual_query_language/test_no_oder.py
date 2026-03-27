import pytest
from itertools import permutations
from cortado_core.utils.split_graph import (
    LeafGroup,
    SequenceGroup,
    ParallelGroup,
    FallthroughGroup,
)
from cortado_core.visual_query_language.query import create_query_instance
from cortado_core.tests.visual_query_language.query_type_fixture import query_type


@pytest.fixture
def query(query_type):
    return create_query_instance(
        SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                FallthroughGroup(
                    lst=[
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                        LeafGroup(lst=["d"]),
                    ]
                ),
                LeafGroup(lst=["e"]),
            ]
        ),
        query_type=query_type,
    )


def test_same_order(query):
    variant = SequenceGroup(
        lst=[
            LeafGroup(lst=["a"]),
            FallthroughGroup(
                lst=[
                    LeafGroup(lst=["b"]),
                    LeafGroup(lst=["c"]),
                    LeafGroup(lst=["d"]),
                ]
            ),
            LeafGroup(lst=["e"]),
        ]
    )

    assert query.match(variant)


def test_different_orders(query):
    base_lst = [LeafGroup(lst=["b"]), LeafGroup(lst=["c"]), LeafGroup(lst=["d"])]
    for perm in permutations(base_lst):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                FallthroughGroup(lst=list(perm)),
                LeafGroup(lst=["e"]),
            ]
        )

        assert query.match(variant)
