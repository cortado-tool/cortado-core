import unittest
from typing import List

from pm4py.objects.process_tree.importer.importer import apply as import_pt
from pm4py.objects.process_tree.obj import ProcessTree


class TestInfixAlignments(unittest.TestCase):

    def test_prefix_alignments_basic_parallel_case(self):
        tree: ProcessTree = import_pt("files/process_tree_freezing.ptml")
        print(tree)

        frozen_subtrees = [tree.children[1], tree.children[2], tree.children[3]]
        print(frozen_subtrees)


if __name__ == '__main__':
    unittest.main()
