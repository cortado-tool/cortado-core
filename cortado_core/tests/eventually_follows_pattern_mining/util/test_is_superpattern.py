import unittest

from cortado_core.eventually_follows_pattern_mining.util.is_superpattern import (
    get_ef_preserving_concurrency_tree,
    enumerate_infix_pattern,
    enumerate_pattern,
    is_superpattern,
)
from cortado_core.eventually_follows_pattern_mining.util.parse_pattern import (
    parse_pattern,
    parse_concurrency_tree,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    get_first_ef_node_id_per_node_for_trees,
)


class TestIsSuperpattern(unittest.TestCase):
    def test_generate_ef_preserving_tree(self):
        pattern = parse_pattern(
            "→(∧('a','b'),'c')...∧('d',→('e','f'))...'g'...→('a','b')"
        )
        tree = get_ef_preserving_concurrency_tree(pattern, "ef_label")
        expected_tree = (
            "→(∧(a, b), c, ef_label, ∧(d, →(e, f)), ef_label, g, ef_label, a, b)"
        )

        self.assertEqual(expected_tree, str(tree))
        self.verify_ids(tree)

    def verify_ids(self, tree, current_id=0):
        self.assertEqual(current_id, tree.id)
        current_id += 1

        for child in tree.children:
            current_id = self.verify_ids(child, current_id)

        return current_id

    def test_is_superpattern(self):
        super_pattern = parse_pattern("→('a','b','c')")
        pattern = parse_pattern("'a'...'c'")
        super_pattern_ef_pres_tree = get_ef_preserving_concurrency_tree(super_pattern)
        ef_dict = get_first_ef_node_id_per_node_for_trees([super_pattern_ef_pres_tree])

        self.assertTrue(is_superpattern(super_pattern_ef_pres_tree, pattern, ef_dict))

    def test_is_superpattern_complex(self):
        super_pattern = parse_pattern(
            "→(∧('a','b', →('e',∧('s','i'),'f')),'c')...∧('d',→('e','f'))...'g'...→('a','b')"
        )
        super_pattern_ef_pres_tree = get_ef_preserving_concurrency_tree(super_pattern)
        ef_dict = get_first_ef_node_id_per_node_for_trees([super_pattern_ef_pres_tree])
        pts = [
            "→(∧('a', →('e',∧('s','i'),'f')),'c')...→('e','f')...'g'...→('a','b')",
            "'a'...'b'",
        ]

        for p in pts:
            pattern = parse_pattern(p)
            self.assertTrue(
                is_superpattern(super_pattern_ef_pres_tree, pattern, ef_dict)
            )

        not_successfull_pts = ["→('e','g')", "'g'...→('e',∧('s','i'),'f')"]

        for p in not_successfull_pts:
            pattern = parse_pattern(p)
            self.assertFalse(
                is_superpattern(super_pattern_ef_pres_tree, pattern, ef_dict)
            )

    def test_abs(self):
        super_pattern_tree = parse_concurrency_tree(
            "→('ER Registration', 'ER Triage', 'e3164e06-f033-4321-9312-fc946f4bd98f', 'LacticAcid', 'e3164e06-f033-4321-9312-fc946f4bd98f', 'Leucocytes')"
        )
        pattern = parse_pattern(
            "→('ER Registration','ER Triage')...∧('LacticAcid','Leucocytes')...'Leucocytes'"
        )
        ef_dict = get_first_ef_node_id_per_node_for_trees([super_pattern_tree])

        self.assertFalse(is_superpattern(super_pattern_tree, pattern, ef_dict))
