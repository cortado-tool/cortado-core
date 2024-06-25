from typing import Optional, Dict

import numpy as np
from pm4py.objects.petri_net.obj import PetriNet, Marking
from numpy import dot
from numpy.linalg import norm

from cortado_core.eventually_follows_pattern_mining.local_process_models.similarity.causal_footprint import (
    create_causal_footprint,
)


def similarity_score(
    net1: PetriNet,
    im1: Marking,
    fm1: Marking,
    net2: PetriNet,
    im2: Marking,
    fm2: Marking,
) -> float:
    causal_footprint_1 = create_causal_footprint(net1, im1, fm1)
    causal_footprint_2 = create_causal_footprint(net2, im2, fm2)

    return similarity_score_for_footprints(causal_footprint_1, causal_footprint_2)


def similarity_score_for_footprints(footprint1, footprint2):
    indexing_func = build_indexing_function(*footprint1, *footprint2)
    vector_1 = build_vector(*footprint1, indexing_func)
    vector_2 = build_vector(*footprint2, indexing_func)

    return cosine_similarity(vector_1, vector_2)


def similarity_score_model_lists(
    models1, models2, precalculated_footprints: Optional[Dict] = None
) -> float:
    footprints = precalculated_footprints
    if footprints is None:
        footprints_m1 = calculate_footprints_for_models(models1)
        footprints_m2 = calculate_footprints_for_models(models2)
        footprints = combine_footprints([footprints_m1, footprints_m2])

    results = []

    for net1, im1, fm1 in models1:
        best_similarity_score_for_model = 0
        for net2, im2, fm2 in models2:
            score = similarity_score_for_footprints(
                footprints[net1, im1, fm1], footprints[net2, im2, fm2]
            )
            if score > best_similarity_score_for_model:
                best_similarity_score_for_model = score

            if best_similarity_score_for_model >= 0.99:
                break

        results.append(best_similarity_score_for_model)

    avg = np.mean(results)

    return avg


def calculate_footprints_for_models(models):
    footprints = dict()
    for net, im, fm in models:
        footprints[net, im, fm] = create_causal_footprint(net, im, fm)

    return footprints


def combine_footprints(footprints):
    result = dict()
    for footprint in footprints:
        for model, fp in footprint.items():
            result[model] = fp

    return result


def cosine_similarity(v1, v2) -> float:
    cos_sim = dot(v1, v2) / (norm(v1) * norm(v2))

    return cos_sim


def build_vector(N, look_ahead, look_back, indexing_func):
    vector_length = len(indexing_func)
    vector = np.zeros(vector_length)

    for act in N:
        vector[indexing_func[act]] = 1

    for a, Bs in look_ahead.items():
        for B in Bs:
            vector[indexing_func[(a, B)]] = 1 / (2 ** len(B))

    for b, As in look_back.items():
        for A in As:
            vector[indexing_func[(A, b)]] = 1 / (2 ** len(A))

    return vector


def build_indexing_function(
    N1, look_ahead_1, look_back_1, N2, look_ahead_2, look_back_2
):
    result = dict()
    counter = 0

    for act in N1:
        result[act] = counter
        counter += 1

    for act in N2:
        if act in result:
            continue

        result[act] = counter
        counter += 1

    for a, Bs in look_ahead_1.items():
        for B in Bs:
            if (a, B) in result:
                continue
            result[(a, B)] = counter
            counter += 1

    for b, As in look_back_1.items():
        for A in As:
            if (A, b) in result:
                continue
            result[(A, b)] = counter
            counter += 1

    for a, Bs in look_ahead_2.items():
        for B in Bs:
            if (a, B) in result:
                continue
            result[(a, B)] = counter
            counter += 1

    for b, As in look_back_2.items():
        for A in As:
            if (A, b) in result:
                continue
            result[(A, b)] = counter
            counter += 1

    return result
