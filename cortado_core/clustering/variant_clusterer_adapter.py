from typing import List

from cortado_core.clustering.clusterer import Clusterer
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeFromcGroup,
)
from cortado_core.utils.split_graph import Group


def calculate_clusters(
    variants: List[Group], clusterer: Clusterer
) -> List[List[Group]]:
    trees = __preprocess_variants(variants)
    clusters = clusterer.calculate_clusters(trees)

    return __postprocess_clusters(clusters)


def __preprocess_variants(variants: List[Group]) -> List[ConcurrencyTree]:
    trees = []

    for variant in variants:
        variant = variant.sort()
        tree = cTreeFromcGroup(group=variant, infix_type=variant.infix_type)
        trees.append(tree)

    return trees


def __postprocess_clusters(
    tree_clusters: List[List[ConcurrencyTree]],
) -> List[List[Group]]:
    clusters = []
    for cluster in tree_clusters:
        new_cluster = []
        for tree in cluster:
            new_group = tree.to_concurrency_group()
            new_cluster.append(new_group)
        clusters.append(new_cluster)

    return clusters
