from enum import Enum
from typing import List, Dict, Optional

from pm4py.objects.log.obj import Trace

from cortado_core.eventually_follows_pattern_mining.algorithm_expansion import (
    generate_eventually_follows_patterns,
)
from cortado_core.eventually_follows_pattern_mining.algorithm_pattern_combination_brute_force import (
    generate_eventually_follows_patterns_using_combination_approach,
)
from cortado_core.eventually_follows_pattern_mining.algorithm_pattern_combination_enumeration_graph import (
    generate_eventually_follows_patterns_using_combination_approach_enumeration_tree,
)
from cortado_core.eventually_follows_pattern_mining.algorithm_pattern_combination_enumeration_graph_old import (
    generate_eventually_follows_patterns_using_combination_approach_enumeration_tree as generate_eventually_follows_patterns_using_combination_approach_enumeration_tree_old,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.algorithm import (
    generate_closed_maximal_eventually_follows_patterns,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.algorithm_baseline import (
    generate_closed_maximal_eventually_follows_patterns as generate_closed_maximal_eventually_follows_patterns_baseline,
)
from cortado_core.eventually_follows_pattern_mining.blanket_mining.combination_blanket_mining import (
    generate_maximal_closed_eventually_follows_patterns_using_combination_approach,
)
from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.frequent_activity_sets import (
    compute_frequent_activity_sets,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy_factory import (
    get_counting_strategy,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_statistic_tracker import (
    OccurrenceStatisticTracker,
    NoOccurrenceStatisticTracker,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.rightmost_occurence_store import (
    RightmostOccurrenceStore,
)

from cortado_core.eventually_follows_pattern_mining.occurrence_store.occurrence_list_cleaner import (
    LastIterationOccurrenceListCleaner,
    NoOccurrenceListCleaner,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    set_tree_attributes,
    get_first_ef_node_id_per_node_for_trees,
    EventuallyFollowsStrategy,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeFromcGroup
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
)
from cortado_core.utils.split_graph import Group


class Algorithm(Enum):
    RightmostExpansion = 1
    InfixPatternCombinationBruteForce = 2
    RightmostExpansionOnlyInfixPatterns = 3
    BlanketMining = 4
    ClosedMaximalBaseline = 5
    InfixPatternCombinationEnumerationGraph = 6
    BlanketMiningCombination = 7
    InfixPatternCombinationEnumerationGraphOld = 8


def generate_eventually_follows_patterns_from_groups(
    variants: Dict[Group, List[Trace]],
    min_support_count: int,
    freq_counting_strategy: FrequencyCountingStrategy,
    algorithm: Algorithm = Algorithm.InfixPatternCombinationEnumerationGraph,
    size_tracker: Optional[OccurrenceStatisticTracker] = None,
    ef_strategy: EventuallyFollowsStrategy = EventuallyFollowsStrategy.RealEventuallyFollows,
    max_size: int = 1000,
):
    trees = []

    for group, traces in variants.items():
        group = group.sort()
        tree = cTreeFromcGroup(group)
        tree.n_traces = len(traces)
        set_tree_attributes(tree)
        trees.append(tree)

    trees.sort(key=lambda t: t.n_traces, reverse=True)

    ef_dict = get_first_ef_node_id_per_node_for_trees(trees, ef_strategy)

    counting_strategy = get_counting_strategy(freq_counting_strategy, trees)
    prune_sets = compute_frequent_activity_sets(
        trees, freq_counting_strategy, min_support_count
    )
    size_tracker = (
        size_tracker if size_tracker is not None else NoOccurrenceStatisticTracker()
    )

    return __execute_algorithm(
        trees,
        min_support_count,
        counting_strategy,
        prune_sets,
        algorithm,
        ef_dict,
        size_tracker,
        max_size,
    )


def __execute_algorithm(
    trees,
    min_support_count,
    counting_strategy,
    prune_sets,
    algorithm: Algorithm,
    ef_dict,
    size_tracker,
    max_size,
):
    if algorithm == Algorithm.InfixPatternCombinationBruteForce:
        return generate_eventually_follows_patterns_using_combination_approach(
            trees,
            min_support_count,
            counting_strategy,
            prune_sets,
            ef_dict,
            size_tracker,
            max_size,
        )
    if algorithm == Algorithm.InfixPatternCombinationEnumerationGraph:
        return generate_eventually_follows_patterns_using_combination_approach_enumeration_tree(
            trees,
            min_support_count,
            counting_strategy,
            prune_sets,
            ef_dict,
            size_tracker,
            max_size,
        )
    if algorithm == Algorithm.InfixPatternCombinationEnumerationGraphOld:
        return generate_eventually_follows_patterns_using_combination_approach_enumeration_tree_old(
            trees,
            min_support_count,
            counting_strategy,
            prune_sets,
            ef_dict,
            size_tracker,
        )
    # unused, only first prototype, not sure if everything works
    if algorithm == Algorithm.BlanketMining:
        return generate_closed_maximal_eventually_follows_patterns(
            trees,
            min_support_count,
            counting_strategy,
            NoOccurrenceListCleaner(),
            prune_sets,
            ef_dict,
        )
    # unused, only first prototype, not sure if everything works
    if algorithm == Algorithm.BlanketMiningCombination:
        return generate_maximal_closed_eventually_follows_patterns_using_combination_approach(
            trees, min_support_count, counting_strategy, prune_sets, ef_dict
        )

    if algorithm == Algorithm.ClosedMaximalBaseline:
        return generate_closed_maximal_eventually_follows_patterns_baseline(
            trees, min_support_count, counting_strategy, prune_sets, ef_dict, max_size
        )

    only_infix_patterns = False
    if algorithm == Algorithm.RightmostExpansionOnlyInfixPatterns:
        only_infix_patterns = True

    occurrence_store = RightmostOccurrenceStore(
        trees, counting_strategy, min_support_count, ef_dict, size_tracker
    )

    patterns = generate_eventually_follows_patterns(
        min_support_count,
        occurrence_store,
        LastIterationOccurrenceListCleaner(),
        prune_sets,
        generate_only_infix_patterns=only_infix_patterns,
        max_iterations=max_size,
    )
    return patterns
