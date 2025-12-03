import unittest

from cortado_core.utils.split_graph import LeafGroup, ParallelGroup, SequenceGroup
from cortado_core.visual_query_language.query import check_variant


class SimpleParallelTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.query = SequenceGroup(
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

        self.activities = [chr(i) for i in range(ord("a"), ord("z") + 1)]

    def test_exact_match(self):
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

        self.assertTrue(check_variant(variant, self.query, self.activities))

    def test_with_additional_branch(self):
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

        self.assertFalse(check_variant(variant, self.query, self.activities))

    def test_missing_branch(self):
        variant = SequenceGroup(
            lst=[ParallelGroup(lst=[LeafGroup(lst=["a"]), LeafGroup(lst=["b"])])]
        )

        self.assertFalse(check_variant(variant, self.query, self.activities))

    def test_different_order(self):
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

        self.assertTrue(check_variant(variant, self.query, self.activities))

    def test_in_sequence(self):
        variant = SequenceGroup(
            lst=[
                LeafGroup(lst=["x"]),
                ParallelGroup(
                    lst=[
                        LeafGroup(lst=["a"]),
                        LeafGroup(lst=["b"]),
                        LeafGroup(lst=["c"]),
                    ]
                ),
                LeafGroup(lst=["y"]),
            ]
        )

        self.assertTrue(check_variant(variant, self.query, self.activities))
