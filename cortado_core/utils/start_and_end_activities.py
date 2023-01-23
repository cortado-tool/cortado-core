from typing import List
from cortado_core.process_tree_utils.reduction import apply_reduction_rules, remove_operator_node_with_one_or_no_child
from pm4py.objects.log.obj import Event, EventLog, Trace
from pm4py.objects.process_tree.obj import Operator, ProcessTree
from pm4py.objects.process_tree.utils.generic import parse as pt_parse
from pm4py.util.xes_constants import DEFAULT_TRACEID_KEY

ARTIFICIAL_START_ACTIVITY_NAME = "Artificial Start Activity Name"
ARTIFICIAL_END_ACTIVITY_NAME = "Artificial End Activity Name"

artificialStartEvent = Event({DEFAULT_TRACEID_KEY: ARTIFICIAL_START_ACTIVITY_NAME})
artificialEndEvent = Event({DEFAULT_TRACEID_KEY: ARTIFICIAL_END_ACTIVITY_NAME})

# Not in place
def add_artificial_start_and_end_to_pt(
    tree: ProcessTree, excluded_subtrees: List[ProcessTree] = []
) -> ProcessTree:
    """
    Adds an artificial start and end activity node at the root of the provided process tree
    :param tree: ProcessTree
    :return: process tree of the form ->(Art. Start Activity, tree, Art End Activity)
    """

    # Create Start and End Activity
    startLeaf = ProcessTree(label=ARTIFICIAL_START_ACTIVITY_NAME)
    endLeaf = ProcessTree(label=ARTIFICIAL_END_ACTIVITY_NAME)

    # Create the expanded tree
    expanded_tree = ProcessTree(Operator.SEQUENCE, children=[startLeaf, tree, endLeaf])

    # Set the backward references
    tree.parent = expanded_tree
    startLeaf.parent = expanded_tree
    endLeaf.parent = expanded_tree

    apply_reduction_rules(expanded_tree, excluded_subtrees=excluded_subtrees)

    return expanded_tree

def add_artificial_start_and_end_activity_to_trace(
    trace: Trace, inplace: bool = False
) -> EventLog or None:
    """
    Adds an artificial start and end activity to the trace
    :param trace: Trace
    :return: A trace with added art. start and end activity
    """

    if inplace:
        trace._list = [artificialStartEvent] + trace._list + [artificialEndEvent]
    else:
        return Trace(
            [artificialStartEvent] + trace._list + [artificialEndEvent],
            kwargs={"properties": trace.properties, "attributes": trace.attributes},
        )


def add_artificial_start_and_end_activity_to_Log(
    log: EventLog, inplace: bool = False
) -> EventLog or None:
    """
    Adds an artificial start and end activity to the trace
    :param trace: Trace
    :return: A trace with added art. start and end activity
    """

    if inplace:
        log._list = [
            add_artificial_start_and_end_activity_to_trace(trc, inplace=False)
            for trc in log
        ]
    else:
        return EventLog(
            [
                add_artificial_start_and_end_activity_to_trace(trc, inplace=False)
                for trc in log
            ],
            kwargs={
                "attributes": log._get_attributes(),
                "extensions": log._get_extensions(),
                "omni_present": log._get_omni(),
                "classifiers": log._get_classifiers(),
                "properties": log._get_properties(),
            },
        )


def remove_artificial_start_and_end_activity_leaves_from_pt(
    tree: ProcessTree, excluded_subtrees: List[ProcessTree] = []
):
    """
    Recurses over the trees and remove all leaf nodes with a label equal to the artificial start and end activities
    :param tree: ProcessTree
    :return: process tree with all occurences of the artificial start and end activities removed
    """

    if tree.children:
        new_children = []

        for child in tree.children:
            if child_tree := remove_artificial_start_and_end_activity_leaves_from_pt(
                child
            ):
                new_children.append(child_tree)

        tree.children = new_children
        del new_children

    elif tree.label in [ARTIFICIAL_START_ACTIVITY_NAME, ARTIFICIAL_END_ACTIVITY_NAME]:
        return None

    if tree.parent is None:
        tree = remove_operator_node_with_one_or_no_child(
            tree, excluded_subtrees=excluded_subtrees
        )
        apply_reduction_rules(tree, excluded_subtrees=excluded_subtrees)

    return tree

if __name__ == "__main__":

    tree: ProcessTree = pt_parse(
        "+ (->('A','"
        + ARTIFICIAL_END_ACTIVITY_NAME
        + "','A', '"
        + ARTIFICIAL_START_ACTIVITY_NAME
        + "'),'C'))"
    )

    print("Test Tree:", tree)
    tree_with_start_end = add_artificial_start_and_end_to_pt(tree)

    print("Tree With:", tree_with_start_end)
    tree_without_start_end = remove_artificial_start_and_end_activity_leaves_from_pt(
        tree_with_start_end
    )

    print("Tree without", tree_without_start_end)

    L = EventLog()
    e1 = Event()
    e1["concept:name"] = "A"
    e2 = Event()
    e2["concept:name"] = "B"
    e3 = Event()
    e3["concept:name"] = "C"
    e4 = Event()
    e4["concept:name"] = "D"
    e5 = Event()
    e5["concept:name"] = "A"
    e6 = Event()
    e6["concept:name"] = "B"
    e7 = Event()
    e7["concept:name"] = "E"
    e8 = Event()
    e8["concept:name"] = "F"
    t = Trace()
    t.append(e1)
    t.append(e2)
    t.append(e3)
    t.append(e4)
    t.append(e5)
    t.append(e6)
    t.append(e7)
    t.append(e8)
    L.append(t)

    t2 = Trace()
    t2.append(e1)
    t2.append(e2)
    t2.append(e2)
    t2.append(e3)
    t2.append(e4)
    t2.append(e5)
    t2.append(e6)
    t2.append(e7)
    t2.append(e8)
    L.append(t)

    print(t)
    print(add_artificial_start_and_end_activity_to_trace(t))

    print(t2)
    print(add_artificial_start_and_end_activity_to_trace(t2))

    print(add_artificial_start_and_end_activity_to_Log(L))