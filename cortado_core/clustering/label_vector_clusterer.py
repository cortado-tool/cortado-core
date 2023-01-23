from collections import defaultdict
from typing import List, Dict, Optional
import numpy as np
from sklearn.cluster import KMeans

from cortado_core.clustering.clusterer import Clusterer
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class LabelVectorClusterer(Clusterer):
    def __init__(self, n_clusters: int):
        self.n_clusters = n_clusters

    def calculate_clusters(self, variants: List[ConcurrencyTree]) -> List[List[ConcurrencyTree]]:
        X = self.__calculate_feature_matrix(variants)
        result = KMeans(n_clusters=self.n_clusters).fit(X)

        cluster_dict = defaultdict(list)
        for i in range(len(variants)):
            cluster_dict[result.labels_[i]].append(variants[i])

        return [cluster_dict[i] for i in cluster_dict.keys()]

    def __calculate_feature_matrix(self, variants: List[ConcurrencyTree]):
        variant_dicts = []

        for variant in variants:
            variant_dicts.append(self.__get_labels_for_variant(variant))

        labels = set()
        for variant_dict in variant_dicts:
            labels = labels.union(set(variant_dict.keys()))

        labels_list = list(labels)
        X = np.zeros(shape=(len(variants), len(labels)), dtype=int)

        for i, variant_label_counts in enumerate(variant_dicts):
            X[i] = np.array([variant_label_counts[label] for label in labels_list])

        return X

    def __get_labels_for_variant(self, variant: ConcurrencyTree, result_dict: Optional[Dict[str, int]] = None) -> Dict[
        str, int]:
        if result_dict is None:
            result_dict = defaultdict(int)

        if variant.label is not None:
            result_dict[variant.label] += 1
        else:
            result_dict[variant.op.value] += 1

        for child in variant.children:
            self.__get_labels_for_variant(child, result_dict)

        return result_dict
