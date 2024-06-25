from typing import List, Set

from cortado_core.eventually_follows_pattern_mining.algorithm_expansion import (
    remove_not_frequent_patterns_from_candidates,
    generate_eventually_follows_patterns,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.occurrence_blanket import (
    left_occurrence_blanket_contains_elements,
    right_occurrence_blanket_contains_elements,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.root_occurrence_blanket import (
    root_occurrence_blanket_contains_elements,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.blanket_checks.transaction_blanket import (
    transaction_blanket_contains_elements,
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
from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_transaction_counting_strategy import (
    TraceTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import EventuallyFollowsPattern
from cortado_core.eventually_follows_pattern_mining.occurrence_store.full_occurrence_store import (
    FullOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_list_cleaner import (
    OccurrenceListCleaner,
    LastIterationOccurrenceListCleaner,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.rightmost_occurence_store import (
    RightmostOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.util import (
    updated_sub_pattern_to_single_child_with_sequential_root,
)
from cortado_core.eventually_follows_pattern_mining.util.filter import is_pattern_valid
from cortado_core.eventually_follows_pattern_mining.util.is_superpattern import (
    is_superpattern,
)
from cortado_core.eventually_follows_pattern_mining.util.pattern import (
    get_activities_for_patterns,
    get_ef_preserving_tree_for_patterns,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


def generate_closed_maximal_eventually_follows_patterns(
    trees: List[ConcurrencyTree],
    min_support_count: int,
    counting_strategy: CountingStrategy,
    occ_list_cleaner: OccurrenceListCleaner,
    prune_sets,
    ef_dict,
):
    closed = set()
    maximal = set()
    patterns = dict()
    candidate_generator = RightmostExpansionCandidateGenerator(
        prune_sets, ComposedPruningStrategy([])
    )
    occurrence_store = FullOccurrenceStore(
        trees, counting_strategy, min_support_count, ef_dict
    )
    initialize_with_initial_patterns_for_pruning(
        occurrence_store,
        candidate_generator,
        min_support_count,
        prune_sets,
        trees,
        counting_strategy,
        ef_dict,
    )
    candidates = candidate_generator.generate_initial_candidates()
    occurrence_store.update_occurrence_lists(candidates)
    iteration_patterns = remove_not_frequent_patterns_from_candidates(
        candidates, min_support_count
    )
    patterns[1] = set(iteration_patterns)
    iteration = 2
    n_occ_filtered = 0
    is_transaction_based_counting = isinstance(
        counting_strategy, VariantTransactionCountingStrategy
    ) or isinstance(counting_strategy, TraceTransactionCountingStrategy)

    while len(iteration_patterns) > 0:
        candidate_generator.iteration = iteration
        found_patterns = set()

        for pattern in iteration_patterns:
            l_occ_blanket_contains_elements = left_occurrence_blanket_contains_elements(
                pattern,
                occurrence_store.occurrence_lists[pattern.id],
                perform_ef_checks=is_transaction_based_counting,
            )
            if l_occ_blanket_contains_elements:
                n_occ_filtered += 1
                continue

            (
                r_occ_blanket_contains_elements,
                max_height_diff,
                create_new_sp,
            ) = right_occurrence_blanket_contains_elements(
                pattern,
                occurrence_store.occurrence_lists[pattern.id],
                perform_ef_checks=is_transaction_based_counting,
            )
            candidates = candidate_generator.generate_candidates_from_current_pattern(
                pattern, max_height_diff, create_new_sp
            )
            occurrence_store.update_occurrence_lists(candidates)
            frequent_candidates = remove_not_frequent_patterns_from_candidates(
                candidates, min_support_count
            )
            found_patterns = found_patterns.union(frequent_candidates)

            if r_occ_blanket_contains_elements:
                continue

            if not is_pattern_valid(pattern):
                continue

            if is_transaction_based_counting:
                if transaction_blanket_contains_elements(
                    pattern, occurrence_store.occurrence_lists[pattern.id]
                ):
                    continue
            else:
                if root_occurrence_blanket_contains_elements(
                    pattern, occurrence_store.occurrence_lists[pattern.id]
                ):
                    continue

            closed.add(pattern)

            if (
                len(
                    [
                        c
                        for c in frequent_candidates
                        if c.rightmost_leaf.label is not None
                        and not updated_sub_pattern_to_single_child_with_sequential_root(
                            c
                        )
                    ]
                )
                != 0
            ):
                continue

            maximal.add(pattern)

        iteration_patterns = found_patterns
        if len(iteration_patterns) > 0:
            patterns[iteration] = iteration_patterns

        occ_list_cleaner.clear_occurrence_list_after_iteration(
            iteration, occurrence_store, patterns
        )

        iteration += 1

    # print('occ filtered:', n_occ_filtered)

    return postprocess_closed_patterns(closed), postprocess_maximal_patterns(maximal)


def initialize_with_initial_patterns_for_pruning(
    occurrence_store,
    candidate_generator,
    min_support_count,
    prune_sets,
    trees,
    counting_strategy,
    ef_dict,
):
    patterns = generate_eventually_follows_patterns(
        min_support_count,
        RightmostOccurrenceStore(trees, counting_strategy, min_support_count, ef_dict),
        LastIterationOccurrenceListCleaner(),
        prune_sets,
        max_iterations=3,
        filter_incomplete=False,
    )
    # print(patterns)
    if 1 in patterns:
        frequent_1_sub_patterns = [pattern.sub_patterns[0] for pattern in patterns[1]]
        candidate_generator.set_frequent_1_patterns(frequent_1_sub_patterns)
        occurrence_store.set_frequent_1_patterns(list(patterns[1]))

    if 2 in patterns:
        candidate_generator.set_frequent_2_patterns(patterns[2])

    if 3 in patterns:
        candidate_generator.set_frequent_3_patterns(patterns[3])


def postprocess_maximal_patterns(
    maximal: Set[EventuallyFollowsPattern],
) -> Set[EventuallyFollowsPattern]:
    filtered = set()
    activities_for_pattern = get_activities_for_patterns(maximal)
    ef_preserving_tree_for_pattern = get_ef_preserving_tree_for_patterns(maximal)
    superpattern_candidates = maximal.copy()

    for pattern in maximal:
        is_maximal = True
        for superpattern_candidate in superpattern_candidates:
            if pattern.id == superpattern_candidate.id:
                continue

            if not activities_for_pattern[pattern.id].issubset(
                activities_for_pattern[superpattern_candidate.id]
            ):
                continue

            ef_preserving_tree, ef_dict = ef_preserving_tree_for_pattern[
                superpattern_candidate.id
            ]

            if is_superpattern(ef_preserving_tree, pattern, ef_dict):
                is_maximal = False
                break
        if is_maximal:
            filtered.add(pattern)
        else:
            superpattern_candidates.remove(pattern)

    return filtered


def postprocess_maximal_patterns_old(
    maximal: Set[EventuallyFollowsPattern], occurrence_list
) -> Set[EventuallyFollowsPattern]:
    filtered = set()
    activities_for_pattern = get_activities_for_patterns(maximal)
    superpattern_candidates = maximal.copy()

    for pattern in maximal:
        is_maximal = True
        for superpattern_candidate in superpattern_candidates:
            if pattern.id == superpattern_candidate.id:
                continue

            if not activities_for_pattern[pattern.id].issubset(
                activities_for_pattern[superpattern_candidate.id]
            ):
                continue

            if is_superpattern_relationship_based_on_occurrence_list(
                pattern, superpattern_candidate, occurrence_list
            ):
                is_maximal = False
                break
        if is_maximal:
            filtered.add(pattern)
        else:
            superpattern_candidates.remove(pattern)

    return filtered


def postprocess_closed_patterns(
    closed: Set[EventuallyFollowsPattern],
) -> Set[EventuallyFollowsPattern]:
    filtered = set()
    activities_for_pattern = get_activities_for_patterns(closed)
    ef_preserving_tree_for_pattern = get_ef_preserving_tree_for_patterns(closed)
    superpattern_candidates = closed.copy()

    for pattern in closed:
        is_closed = True
        for superpattern_candidate in superpattern_candidates:
            if pattern.id == superpattern_candidate.id:
                continue

            if superpattern_candidate.support < pattern.support:
                continue

            if not activities_for_pattern[pattern.id].issubset(
                activities_for_pattern[superpattern_candidate.id]
            ):
                continue

            ef_preserving_tree, ef_dict = ef_preserving_tree_for_pattern[
                superpattern_candidate.id
            ]

            if (
                is_superpattern(ef_preserving_tree, pattern, ef_dict)
                and superpattern_candidate.support >= pattern.support
            ):
                assert superpattern_candidate.support == pattern.support
                is_closed = False
                break
        if is_closed:
            filtered.add(pattern)
        else:
            superpattern_candidates.remove(pattern)
    return filtered


def postprocess_closed_patterns_old(
    closed: Set[EventuallyFollowsPattern], occurrence_list
) -> Set[EventuallyFollowsPattern]:
    filtered = set()
    activities_for_pattern = get_activities_for_patterns(closed)
    superpattern_candidates = closed.copy()

    for pattern in closed:
        is_closed = True
        for superpattern_candidate in superpattern_candidates:
            if pattern.id == superpattern_candidate.id:
                continue

            if superpattern_candidate.support < pattern.support:
                continue

            if not activities_for_pattern[pattern.id].issubset(
                activities_for_pattern[superpattern_candidate.id]
            ):
                continue

            if (
                is_superpattern_relationship_based_on_occurrence_list(
                    pattern, superpattern_candidate, occurrence_list
                )
                and superpattern_candidate.support >= pattern.support
            ):
                assert superpattern_candidate.support == pattern.support
                is_closed = False
                break
        if is_closed:
            filtered.add(pattern)
        else:
            superpattern_candidates.remove(pattern)
    return filtered


def is_superpattern_relationship_based_on_occurrence_list(
    pattern: EventuallyFollowsPattern,
    potential_super_pattern: EventuallyFollowsPattern,
    occ_list,
) -> bool:
    tree_id, sp_occurrences = next(iter(occ_list[potential_super_pattern.id].items()))
    if tree_id not in occ_list[pattern.id]:
        return False

    sp_occurrences = sp_occurrences[0]
    sp_occ_idx = set([n.id for n in sp_occurrences])

    p_occurrences = occ_list[pattern.id][tree_id]

    for pattern_occurrence in p_occurrences:
        p_occ_idx = set([n.id for n in pattern_occurrence])

        if p_occ_idx.issubset(sp_occ_idx):
            return True

    return False
