from typing import List, Dict, Set

from cortado_core.eventually_follows_pattern_mining.algorithm_pattern_combination_enumeration_graph import (
    build_pattern,
    update_occurrences_with_ef_check,
    initialize_occurrence_list,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.pruning_strategy import (
    PruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.infix_sub_patterns_pruning_strategy import (
    InfixSubPatternsPruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_transaction_counting_strategy import (
    TraceTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_statistic_tracker import (
    OccurrenceStatisticTracker,
    NoOccurrenceStatisticTracker,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.rightmost_occurence_store import (
    RightmostOccurrenceStore,
)

from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_list_cleaner import (
    NoOccurrenceListCleaner,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree
from cortado_core.eventually_follows_pattern_mining.algorithm_expansion import (
    generate_eventually_follows_patterns as generate_infix_patterns,
)


def generate_eventually_follows_patterns_using_combination_approach(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    counting_strategy: CountingStrategy,
    prune_sets,
    ef_dict,
    size_tracker=None,
    max_size=1000,
):
    size_tracker = (
        size_tracker if size_tracker is not None else NoOccurrenceStatisticTracker()
    )

    occurrence_store = RightmostOccurrenceStore(
        trees, counting_strategy, min_support_count, ef_dict, size_tracker
    )
    patterns = generate_infix_patterns(
        min_support_count,
        occurrence_store,
        NoOccurrenceListCleaner(),
        prune_sets,
        generate_only_infix_patterns=True,
        max_iterations=max_size,
    )
    pruning_strategy = InfixSubPatternsPruningStrategy(patterns)

    flat_infix_patterns = []

    for _, pts in patterns.items():
        for pattern in pts:
            flat_infix_patterns.append(pattern)

    if len(flat_infix_patterns) == 0:
        max_pattern_id = 1
    else:
        max_pattern_id = max(flat_infix_patterns, key=lambda x: x.id).id

    generate_combined_patterns(
        patterns,
        flat_infix_patterns,
        occurrence_store,
        min_support_count,
        pruning_strategy,
        max_pattern_id + 1,
        ef_dict,
        size_tracker,
        counting_strategy,
        max_size,
    )

    return patterns


def generate_combined_patterns(
    patterns: Dict[int, Set],
    infix_patterns: List[EventuallyFollowsPattern],
    occurrence_store: RightmostOccurrenceStore,
    min_support_count: int,
    pruning_strategy: PruningStrategy,
    current_pattern_id: int,
    ef_dict,
    size_tracker: OccurrenceStatisticTracker,
    counting_strategy: CountingStrategy,
    max_size: int,
):
    postfix_candidates = infix_patterns
    prefix_candidates = infix_patterns
    iteration = 1
    n_tested_patterns = 0

    occurrence_lists = initialize_occurrence_list(infix_patterns, occurrence_store)
    is_transaction_counting = isinstance(
        counting_strategy, VariantTransactionCountingStrategy
    ) or isinstance(counting_strategy, TraceTransactionCountingStrategy)

    while len(prefix_candidates) > 0:
        next_iteration_prefix_candidates = []
        for prefix_candidate in prefix_candidates:
            prefix_occurrence_list = occurrence_lists[prefix_candidate.id]
            for postfix_candidate in postfix_candidates:
                current_pattern_id, new_pattern, new_pattern_n_nodes = build_pattern(
                    current_pattern_id, postfix_candidate, prefix_candidate
                )

                if new_pattern_n_nodes > max_size:
                    continue

                if pruning_strategy.can_prune(new_pattern, new_pattern_n_nodes):
                    continue

                n_tested_patterns += 1

                postfix_occurrence_list = occurrence_lists[postfix_candidate.id]
                support_to_gain = prefix_candidate.support

                update_occurrences_with_ef_check(
                    new_pattern,
                    postfix_occurrence_list,
                    prefix_occurrence_list,
                    support_to_gain,
                    occurrence_lists,
                    is_transaction_counting,
                    min_support_count,
                    ef_dict,
                    counting_strategy,
                )

                if new_pattern.support >= min_support_count:
                    next_iteration_prefix_candidates.append(new_pattern)

                    if new_pattern_n_nodes in patterns:
                        patterns[new_pattern_n_nodes].add(new_pattern)
                    else:
                        patterns[new_pattern_n_nodes] = {new_pattern}

        size_tracker.track_after_iteration(occurrence_lists)

        if iteration > 1:
            for pattern in prefix_candidates:
                del occurrence_lists[pattern.id]

        prefix_candidates = next_iteration_prefix_candidates
        iteration += 1

    # print('BF tested patterns:', n_tested_patterns)
