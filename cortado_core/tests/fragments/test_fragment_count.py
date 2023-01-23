import unittest

from cortado_core.models.infix_type import InfixType
from cortado_core.utils.split_graph import Group, ParallelGroup, SequenceGroup
from parameterized import parameterized


def generate_variant_with_depth_n(fragment: Group, depth):
    if depth == 1:
        return fragment

    if depth % 2 == 0:
        return ParallelGroup(lst=[fragment, generate_variant_with_depth_n(fragment, depth - 1)])
    else:
        return SequenceGroup(lst=[fragment, generate_variant_with_depth_n(fragment, depth - 1)])


class FragmentCountTestCase(unittest.TestCase):

    variant_1: ParallelGroup = Group.deserialize(
        {
            'parallel': [
                {'leaf': ['a']},
                {'leaf': ['b']},
                {'leaf': ['b']},
                {'leaf': ['a']},
                {'leaf': ['a']},
                {'leaf': ['b']}
            ]
        }
    )

    variant_2: SequenceGroup = Group.deserialize(
        {
            'follows': [
                {'leaf': ['a']},
                {'leaf': ['b']},
                {'leaf': ['b']},
                {'leaf': ['a']},
                {'leaf': ['a']},
                {'leaf': ['b']}
            ]
        }
    )

    empty_sequence = Group.deserialize(
        {
            'follows': []
        }
    )

    def test_fragment_multiple_times_in_parallel_group(self):

        variant_fragment = Group.deserialize(
            {
                'parallel': [
                    {'leaf': ['a']},
                    {'leaf': ['b']},
                ]
            }
        )

        self.assertEqual(self.variant_1.countInfixOccurrences(
            variant_fragment), 3)

    def test_fragment_multiple_times_in_sequence_group(self):
        variant_fragment = Group.deserialize(
            {
                'follows': [
                    {'leaf': ['a']},
                    {'leaf': ['b']},
                ]
            }
        )

        self.assertEqual(self.variant_2.countInfixOccurrences(
            variant_fragment), 2)

    @parameterized.expand(
        [
            (
                generate_variant_with_depth_n(
                    Group.deserialize(
                        {
                            'parallel': [
                                {'leaf': ['a']},
                                {'leaf': ['b']},
                            ]
                        }
                    ), i + 1
                ),
                Group.deserialize(
                    {
                        'parallel': [
                            {'leaf': ['a']},
                            {'leaf': ['b']},
                        ]
                    }
                ),
                i + 1) for i in range(6)
        ]
    )
    def test_nested_depth_n(self, group: Group, fragment, n):
        self.assertEqual(group.countInfixOccurrences(
            fragment), n)

    def test_not_contained(self):
        variant_fragment = Group.deserialize(
            {
                'parallel': [
                    {'leaf': ['a']},
                    {'leaf': ['c']},
                ]
            }
        )
        self.assertEqual(self.variant_1.countInfixOccurrences(
            variant_fragment), 0)

    def test_prefix(self):

        contained_as_prefix = Group.deserialize(
            {
                'follows': [
                    {'leaf': ['a']},
                    {'leaf': ['b']},
                ]
            }
        )

        not_contained_as_prefix = Group.deserialize(
            {
                'follows': [
                    {'leaf': ['b']},
                    {'leaf': ['a']},
                ]
            }
        )

        self.assertEqual(self.variant_2.countInfixOccurrences(
            contained_as_prefix, InfixType.PREFIX, isRootNode=True), 1)

        self.assertEqual(self.variant_2.countInfixOccurrences(
            not_contained_as_prefix, InfixType.PREFIX, isRootNode=True), 0)

        self.assertEqual(self.empty_sequence.countInfixOccurrences(
            not_contained_as_prefix, InfixType.PREFIX, isRootNode=True), 0)

    def test_postfix(self):

        contained_as_postfix = Group.deserialize(
            {
                'follows': [
                    {'leaf': ['a']},
                    {'leaf': ['b']},
                ]
            }
        )

        not_contained_as_postfix = Group.deserialize(
            {
                'follows': [
                    {'leaf': ['b']},
                    {'leaf': ['a']},
                ]
            }
        )

        self.assertEqual(self.variant_2.countInfixOccurrences(
            contained_as_postfix, InfixType.POSTFIX, isRootNode=True), 1)

        self.assertEqual(self.variant_2.countInfixOccurrences(
            not_contained_as_postfix, InfixType.POSTFIX, isRootNode=True), 0)

        self.assertEqual(self.empty_sequence.countInfixOccurrences(
            not_contained_as_postfix, InfixType.POSTFIX, isRootNode=True), 0)
