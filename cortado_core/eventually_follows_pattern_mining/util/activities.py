from typing import List, Set

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


def get_activities_in_concurrency_trees(trees: List[ConcurrencyTree]) -> Set[str]:
    activities = set()

    for tree in trees:
        activities = activities.union(get_activities_in_concurrency_tree(tree))

    return activities


def get_activities_in_concurrency_tree(tree: ConcurrencyTree) -> Set[str]:
    activities = set()

    if tree.label is not None:
        activities.add(tree.label)

    for child in tree.children:
        activities = activities.union(get_activities_in_concurrency_tree(child))

    return activities


def get_labeled_nodes_in_concurrency_tree(
    tree: ConcurrencyTree,
) -> Set[ConcurrencyTree]:
    activities = set()

    if tree.label is not None:
        activities.add(tree)

    for child in tree.children:
        activities = activities.union(get_labeled_nodes_in_concurrency_tree(child))

    return activities
