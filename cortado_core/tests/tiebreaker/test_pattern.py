import unittest

from cortado_core.tiebreaker.pattern import parse_tiebreaker_pattern, set_preorder_ids


class TestTiebreakerPattern(unittest.TestCase):
    def test_set_preorder_ids(self):
        pattern = parse_tiebreaker_pattern("->('a', x('b', ...))")
        set_preorder_ids(pattern)

        self.assertEqual(0, pattern.id)
        self.assertEqual(1, pattern.children[0].id)
        self.assertEqual(2, pattern.children[1].id)
        self.assertEqual(3, pattern.children[1].children[0].id)
        self.assertEqual(4, pattern.children[1].children[1].id)
