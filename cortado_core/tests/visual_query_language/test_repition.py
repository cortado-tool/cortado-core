import unittest

from cortado_core.utils.split_graph import (
    ParallelGroup,
    SequenceGroup,
    LeafGroup,
    LoopGroup,
)
from cortado_core.visual_query_language.query import check_variant


class SimpleRepitionTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.query = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LoopGroup(lst=[LeafGroup(lst=["b"])], min_count=2, max_count=2),
                LeafGroup(lst=["c"]),
            ]
        )

        self.activities = [chr(i) for i in range(ord("a"), ord("z") + 1)]

    def test_match(self):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        self.assertTrue(check_variant(variant, self.query, self.activities))

    def test_too_few_repetitions(self):
        variant = SequenceGroup(
            lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"]), LeafGroup(lst=["c"])]
        )

        self.assertFalse(check_variant(variant, self.query, self.activities))

    def test_too_many_repetitions(self):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["a"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["b"]),
                LeafGroup(lst=["c"]),
            ]
        )

        self.assertFalse(check_variant(variant, self.query, self.activities))
