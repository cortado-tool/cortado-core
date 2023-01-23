import unittest

from cortado_core.utils.split_graph import Group, LeafGroup, ParallelGroup, SequenceGroup


class DeserializeGroupTestCase(unittest.TestCase):

    def test_deserialize_parallel_group(self):
        variant_serialized = {
            'parallel': [
                {'leaf': ['a']},
                {'leaf': ['b']}
            ]
        }

        result = Group.deserialize(variant_serialized)

        expected = ParallelGroup(
            lst=[LeafGroup(lst=['a']), LeafGroup(lst=['b'])])

        self.assertEqual(result, expected)

    def test_deserialize_sequence_group(self):
        variant_serialized = {'follows': [{'leaf': ['a']},
                                          {'leaf': ['b']}]}
        result = Group.deserialize(variant_serialized)

        expected = SequenceGroup(
            lst=[LeafGroup(lst=['a']), LeafGroup(lst=['b'])])

        self.assertEqual(result, expected)

    def test_deserialize_leaf_group(self):
        variant_serialized = {'leaf': ['a']}
        result = Group.deserialize(variant_serialized)
        expected = LeafGroup(lst=['a'])
        self.assertEqual(result, expected)

    def test_deserialize_mixed(self):
        variant_serialized = {
            'follows': [
                {'leaf': ['a']},
                {
                    'parallel': [
                        {'leaf': ['b']},
                        {'leaf': ['c']}
                    ]
                },
                {'leaf': ['d']},
                {'leaf': ['e']}
            ]
        }

        result = Group.deserialize(variant_serialized)

        expected = SequenceGroup(lst=[LeafGroup(lst=['a']), ParallelGroup(lst=[LeafGroup(
            lst=['b']), LeafGroup(lst=['c'])]), LeafGroup(lst=['d']), LeafGroup(lst=['e'])])

        self.assertEqual(result, expected)
