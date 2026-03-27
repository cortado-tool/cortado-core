from typing import List, Set, Dict, Optional

from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.composed_pruning_strategy import (
    ComposedPruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.pruning_strategy import (
    PruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.infix_sub_patterns_pruning_strategy import (
    InfixSubPatternsPruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.rightmost_expansion import (
    RightmostExpansionCandidateGenerator,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_list_cleaner import (
    OccurrenceListCleaner,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_statistic_tracker import (
    OccurrenceStatisticTracker,
    NoOccurrenceStatisticTracker,
)
from cortado_core.eventually_follows_pattern_mining.util.filter import (
    filter_incomplete_patterns,
)


def generate_eventually_follows_patterns(
    min_support_count: int,
    occurrence_store,
    occ_store_cleaner: OccurrenceListCleaner,
    prune_sets,
    generate_only_infix_patterns: bool = False,
    max_iterations: int = 1000,
    filter_incomplete=True,
):
    patterns = dict()
    candidate_generator = RightmostExpansionCandidateGenerator(
        prune_sets, get_pruning_strategy(patterns), not generate_only_infix_patterns
    )
    tested_patterns = 0
    candidates = candidate_generator.generate_initial_candidates()
    tested_patterns += len(candidates)
    occurrence_store.update_occurrence_lists(candidates)
    iteration_patterns = remove_not_frequent_patterns_from_candidates(
        candidates, min_support_count
    )
    frequent_1_sub_patterns = [
        pattern.sub_patterns[0] for pattern in iteration_patterns
    ]
    candidate_generator.set_frequent_1_patterns(frequent_1_sub_patterns)
    occurrence_store.set_frequent_1_patterns(list(iteration_patterns))
    patterns[1] = set(iteration_patterns)
    iteration = 2

    while len(iteration_patterns) > 0 and iteration <= max_iterations:
        # print('Iteration', iteration)
        candidates = candidate_generator.generate_next_candidates(
            iteration_patterns, iteration
        )
        tested_patterns += len(candidates)
        # print('Candidates', len(candidates))
        occurrence_store.update_occurrence_lists(candidates)
        iteration_patterns = remove_not_frequent_patterns_from_candidates(
            candidates, min_support_count
        )
        # print('Frequent Patterns', len(iteration_patterns))

        if len(iteration_patterns) > 0:
            patterns[iteration] = iteration_patterns

        if iteration == 2 and len(iteration_patterns) > 0:
            candidate_generator.set_frequent_2_patterns(patterns[iteration])
        if iteration == 3 and len(iteration_patterns) > 0:
            candidate_generator.set_frequent_3_patterns(patterns[iteration])

        occ_store_cleaner.clear_occurrence_list_after_iteration(
            iteration, occurrence_store, patterns
        )

        iteration += 1

    # print('Tested pattern expansion', tested_patterns)

    if filter_incomplete:
        return filter_incomplete_patterns(patterns)

    return patterns


def remove_not_frequent_patterns_from_candidates(
    candidates: List[EventuallyFollowsPattern], min_support_count: int
) -> Set[EventuallyFollowsPattern]:
    return set([c for c in candidates if c.support >= min_support_count])


def get_pruning_strategy(
    patterns: Dict[int, Set[EventuallyFollowsPattern]],
) -> PruningStrategy:
    right_sub_pattern_pruning = InfixSubPatternsPruningStrategy(patterns)
    pruning_strategy = ComposedPruningStrategy([right_sub_pattern_pruning])

    return pruning_strategy
