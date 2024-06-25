from collections import defaultdict
from typing import List, Dict
import numpy as np
from sklearn.mixture import GaussianMixture

from cortado_core.eventually_follows_pattern_mining.local_process_models.clustering.clusterer import (
    Clusterer,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)


class GmmLabelVectorClusterer(Clusterer):
    def __init__(self, n_clusters: int, threshold: float):
        self.n_clusters = n_clusters
        self.threshold = threshold

    def calculate_clusters(
        self, patterns: List[EventuallyFollowsPattern]
    ) -> List[List[EventuallyFollowsPattern]]:
        X = self.__calculate_feature_matrix(patterns)
        print("start fit")
        gmm = GaussianMixture(n_components=self.n_clusters).fit(X)
        print("start predict")
        result = gmm.predict_proba(X)
        print("end predict")
        cluster_dict = defaultdict(list)
        for i in range(len(patterns)):
            for j, probability in enumerate(result[i]):
                if probability > self.threshold:
                    cluster_dict[j].append(patterns[i])

        return [cluster_dict[i] for i in cluster_dict.keys()]

    def __calculate_feature_matrix(self, patterns: List[EventuallyFollowsPattern]):
        pattern_dicts = []

        for pattern in patterns:
            pattern_dicts.append(self.__get_labels_for_pattern(pattern))

        labels = set()
        for p_dict in pattern_dicts:
            labels = labels.union(set(p_dict.keys()))

        labels_list = list(labels)
        X = np.zeros(shape=(len(patterns), len(labels)), dtype=int)

        for i, pattern_label_counts in enumerate(pattern_dicts):
            X[i] = np.array([pattern_label_counts[label] for label in labels_list])

        return X

    def __get_labels_for_pattern(
        self, pattern: EventuallyFollowsPattern
    ) -> Dict[str, int]:
        result_dict = defaultdict(int)
        result_dict["..."] = len(pattern) - 1

        for sub_pattern in pattern.sub_patterns:
            self.__set_label_counts_for_sub_pattern(sub_pattern, result_dict)

        return result_dict

    def __set_label_counts_for_sub_pattern(
        self, sub_pattern: SubPattern, result_dict: Dict[str, int]
    ):
        if sub_pattern.label is not None:
            result_dict[sub_pattern.label] += 1
        else:
            result_dict[str(sub_pattern.operator)] += 1

        for child in sub_pattern.children:
            self.__set_label_counts_for_sub_pattern(child, result_dict)
