from typing import Tuple, Dict

from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.objects.process_tree.obj import Operator

from cortado_core.process_tree_utils.miscellaneous import subtree_is_part_of_tree_based_on_obj_id, pt_dict_key


def replace_frozen_subtrees_in_pt(pt: ProcessTree, subtrees_to_be_replaced: Dict[Tuple[ProcessTree, int], str]) -> ProcessTree:
    for subtree, subtree_id in subtrees_to_be_replaced:
        pt = __replace_subtree_in_pt(pt, subtree, subtrees_to_be_replaced[(subtree, subtree_id)])
    return pt


def __replace_subtree_in_pt(pt: ProcessTree, subtree_to_be_replaced: ProcessTree,
                            replacement_label: str) -> ProcessTree:
    if subtree_is_part_of_tree_based_on_obj_id(subtree_to_be_replaced, pt):
        # remove subtree_to_be_replaced in parent's children and add replacement tree
        replacement_tree: ProcessTree = __generate_replacement_tree_from_label(replacement_label)
        for i, c in enumerate(subtree_to_be_replaced.parent.children):
            if c is subtree_to_be_replaced:
                subtree_to_be_replaced.parent.children[i] = replacement_tree
        replacement_tree.parent = subtree_to_be_replaced.parent
        # if subtree_to_be_replaced == pt:
        #     replacement_tree: ProcessTree = __generate_replacement_tree_from_label(replacement_label)
        #     pt.children = []
        #     pt.label = replacement_label
        #     pt.operator = None
        #     return pt
        # else:
        #     for c in pt.children:
        #         __replace_subtree_in_pt(c, subtree_to_be_replaced, replacement_label)
        #     return pt
    return pt


def __generate_replacement_tree_from_label(replacement_label: str) -> ProcessTree:
    root: ProcessTree = ProcessTree(operator=Operator.SEQUENCE)
    c1: ProcessTree = ProcessTree(parent=root, label=replacement_label + "+ACTIVATED")
    c2: ProcessTree = ProcessTree(parent=root, label=replacement_label + "+CLOSED")
    root.children.append(c1)
    root.children.append(c2)
    return root


if __name__ == "__main__":
    pt_1 = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E',->('A','F')) )")
    pt_2 = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E','F') )")
    pt_3 = pt_parse("-> (*(X(->('A','B'),->('B','D')),tau) ,->('E','F') )")
    pt_4 = pt_parse("-> (*(X(->('A','B'))")

    print(subtree_is_part_of_tree_based_on_obj_id(pt_parse("->('A','F') )"), pt_1))  # True
    print(subtree_is_part_of_tree_based_on_obj_id(pt_1, pt_1))  # True

    pt_1: ProcessTree = pt_parse("-> (*(X(->('A','B'),->('C','D')),tau) ,->('E',->('A','F')) )")

    print("tree:\n", pt_1)

    subtrees = {pt_dict_key(pt_1.children[1].children[1]): 'X_1',
                pt_dict_key(pt_1.children[0].children[0].children[0]): 'X_2'}
    print("subtree to be replaced:", subtrees)

    modified_pt_1 = replace_frozen_subtrees_in_pt(pt_1, subtrees)
    print("modified tree:\n", modified_pt_1)
