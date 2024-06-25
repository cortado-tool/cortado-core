from typing import List

from cortado_core.eventually_follows_pattern_mining.algorithm_expansion import (
    generate_eventually_follows_patterns,
)
from cortado_core.eventually_follows_pattern_mining.algorithm_pattern_combination_enumeration_graph import (
    generate_eventually_follows_patterns_using_combination_approach_enumeration_tree,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.algorithm import (
    postprocess_closed_patterns,
    postprocess_maximal_patterns,
    postprocess_closed_patterns_old,
    postprocess_maximal_patterns_old,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.full_occurrence_store import (
    FullOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_list_cleaner import (
    NoOccurrenceListCleaner,
    LastIterationOccurrenceListCleaner,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.rightmost_occurence_store import (
    RightmostOccurrenceStore,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


def generate_closed_maximal_eventually_follows_patterns(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    counting_strategy: CountingStrategy,
    prune_sets,
    ef_dict,
    max_size,
):
    patterns = generate_eventually_follows_patterns_using_combination_approach_enumeration_tree(
        trees,
        min_support_count,
        counting_strategy,
        prune_sets,
        ef_dict,
        max_size=max_size,
    )

    patterns = flatten_patterns(patterns)

    return postprocess_closed_patterns(patterns), postprocess_maximal_patterns(patterns)


def generate_closed_maximal_eventually_follows_patterns_old(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    counting_strategy: CountingStrategy,
    prune_sets,
    ef_dict,
):
    occurrence_store = FullOccurrenceStore(
        trees, counting_strategy, min_support_count, ef_dict
    )
    patterns = generate_eventually_follows_patterns(
        min_support_count, occurrence_store, NoOccurrenceListCleaner(), prune_sets
    )
    patterns = flatten_patterns(patterns)

    return postprocess_closed_patterns_old(
        patterns, occurrence_store.occurrence_lists
    ), postprocess_maximal_patterns_old(patterns, occurrence_store.occurrence_lists)


def flatten_patterns(patterns):
    res = set()
    for _, p in patterns.items():
        res = res.union(p)

    return res
