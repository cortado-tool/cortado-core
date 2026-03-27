from collections import defaultdict
from typing import List, Iterable, Dict

from cortado_core.eventually_follows_pattern_mining.algorithm_expansion import (
    remove_not_frequent_patterns_from_candidates,
    generate_eventually_follows_patterns,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.occurrence_blanket import (
    left_occurrence_blanket_contains_elements,
    right_occurrence_blanket_contains_elements,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.composed_pruning_strategy import (
    ComposedPruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.rightmost_expansion import (
    RightmostExpansionCandidateGenerator,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.occurrence_store.full_occurrence_store import (
    FullOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_list_cleaner import (
    LastIterationOccurrenceListCleaner,
)
from cortado_core.eventually_follows_pattern_mining.util.filter import is_pattern_valid
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


def generate_infix_patterns_without_occurrence_match(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    occurrence_store: FullOccurrenceStore,
    counting_strategy: CountingStrategy,
    prune_sets,
):
    patterns = defaultdict(set)
    candidate_generator = RightmostExpansionCandidateGenerator(
        prune_sets, ComposedPruningStrategy([]), generate_ef_patterns=False
    )
    __initialize_with_initial_patterns_for_pruning(
        occurrence_store,
        trees,
        counting_strategy,
        candidate_generator,
        min_support_count,
        prune_sets,
    )
    candidates = candidate_generator.generate_initial_candidates()
    occurrence_store.update_occurrence_lists(candidates)
    iteration_patterns = remove_not_frequent_patterns_from_candidates(
        candidates, min_support_count
    )
    iteration = 2
    n_occ_filtered = 0

    while len(iteration_patterns) > 0:
        candidate_generator.iteration = iteration
        found_patterns = set()

        for pattern in iteration_patterns:
            l_occ_blanket_contains_elements = left_occurrence_blanket_contains_elements(
                pattern,
                occurrence_store.occurrence_lists[pattern.id],
                perform_ef_checks=False,
                perform_sequential_checks=False,
            )
            if l_occ_blanket_contains_elements:
                n_occ_filtered += 1
                continue

            (
                r_occ_blanket_contains_elements,
                max_height_diff,
                _,
            ) = right_occurrence_blanket_contains_elements(
                pattern,
                occurrence_store.occurrence_lists[pattern.id],
                perform_ef_checks=False,
                perform_sequential_checks=False,
            )
            candidates = candidate_generator.generate_candidates_from_current_pattern(
                pattern, max_height_diff, False
            )
            occurrence_store.update_occurrence_lists(candidates)
            frequent_candidates = remove_not_frequent_patterns_from_candidates(
                candidates, min_support_count
            )
            found_patterns = found_patterns.union(frequent_candidates)

            if r_occ_blanket_contains_elements:
                n_occ_filtered += 1
                continue

            if not is_pattern_valid(pattern):
                continue

            patterns[iteration - 1].add(pattern)

        iteration_patterns = found_patterns

        iteration += 1

    # print('occ filtered', n_occ_filtered)

    return __remove_predecessor_from_patterns(patterns)


def __initialize_with_initial_patterns_for_pruning(
    occurrence_store,
    trees,
    counting_strategy,
    candidate_generator,
    min_support_count,
    prune_sets,
):
    patterns = generate_eventually_follows_patterns(
        min_support_count,
        FullOccurrenceStore(trees, counting_strategy, min_support_count, dict()),
        LastIterationOccurrenceListCleaner(),
        prune_sets,
        max_iterations=3,
        filter_incomplete=False,
        generate_only_infix_patterns=True,
    )
    if 1 in patterns:
        frequent_1_sub_patterns = [pattern.sub_patterns[0] for pattern in patterns[1]]
        candidate_generator.set_frequent_1_patterns(frequent_1_sub_patterns)
        occurrence_store.set_frequent_1_patterns(list(patterns[1]))

    if 2 in patterns:
        candidate_generator.set_frequent_2_patterns(patterns[2])

    if 3 in patterns:
        candidate_generator.set_frequent_3_patterns(patterns[3])


def __remove_predecessor_from_patterns(
    patterns: Dict[int, Iterable[EventuallyFollowsPattern]],
):
    for pts in patterns.values():
        for pattern in pts:
            pattern.predecessor_pattern = None

    return patterns
