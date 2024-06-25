import copy
from collections import defaultdict
from typing import List, Set, Tuple, Optional

from cortado_core.eventually_follows_pattern_mining.candidate_enumeration.pruning_strategy.pruning_strategy import (
    PruningStrategy,
)
from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)
from cortado_core.eventually_follows_pattern_mining.util.pattern import (
    get_activities_for_pattern,
    get_activities_for_sub_pattern,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator as ConcurrencyTreeOperator,
)
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequentActivitySets

OPERATORS = {
    ConcurrencyTreeOperator.Concurrent,
    ConcurrencyTreeOperator.Sequential,
    ConcurrencyTreeOperator.Fallthrough,
}


class RightmostExpansionCandidateGenerator:
    def __init__(
        self,
        pruning_sets: FrequentActivitySets,
        pruning_strategy: PruningStrategy,
        generate_ef_patterns: bool = True,
    ):
        self.pruning_sets = pruning_sets
        self.pruning_strategy = pruning_strategy
        self.generate_ef_patterns = generate_ef_patterns
        self.iteration = 1
        self.n_pruned = 0

        self.frequent_operators = set()

        self.frequent_real_ef_relationships = None
        self.frequent_operator_edges = None
        self.frequent_activity_edges = None
        self.frequent_right_siblings = None
        self.current_id = 0

    def generate_initial_candidates(self) -> List[EventuallyFollowsPattern]:
        patterns = []
        self.iteration = 1

        single_node_sub_patterns = self.__generate_single_node_sub_patterns()
        for sub_pattern in single_node_sub_patterns:
            sub_pattern.id = 0
            patterns.append(
                EventuallyFollowsPattern(
                    [sub_pattern],
                    rightmost_leaf=sub_pattern,
                    leftmost_occurrence_update_required=True,
                )
            )

        return self.set_ids(patterns)

    def set_frequent_1_patterns(self, frequent_1_patterns: List[SubPattern]):
        self.frequent_operators = set(
            [a.operator for a in frequent_1_patterns if a.operator is not None]
        )

    def set_frequent_2_patterns(
        self, frequent_2_patterns: Set[EventuallyFollowsPattern]
    ):
        self.frequent_real_ef_relationships = defaultdict(set)
        self.frequent_operator_edges = defaultdict(set)
        self.frequent_activity_edges = defaultdict(set)
        for pattern in frequent_2_patterns:
            if len(pattern) == 2:
                label_0 = pattern.sub_patterns[0].label
                label_1 = pattern.sub_patterns[1].label

                if label_0 is not None and label_1 is not None:
                    self.frequent_real_ef_relationships[label_0].add(label_1)
            else:
                child = pattern.sub_patterns[0].children[0]
                if child.label is not None:
                    self.frequent_activity_edges[pattern.sub_patterns[0].operator].add(
                        child.label
                    )
                else:
                    self.frequent_operator_edges[pattern.sub_patterns[0].operator].add(
                        child.operator
                    )

    def set_frequent_3_patterns(self, patterns: Set[EventuallyFollowsPattern]):
        self.frequent_right_siblings = {
            ConcurrencyTreeOperator.Concurrent: defaultdict(set),
            ConcurrencyTreeOperator.Sequential: defaultdict(set),
            ConcurrencyTreeOperator.Fallthrough: defaultdict(set),
        }

        for pattern in patterns:
            if len(pattern) != 1:
                continue

            root = pattern.sub_patterns[0]
            if len(root.children) != 2:
                continue

            if (
                root.children[0].label is not None
                and root.children[1].label is not None
            ):
                self.frequent_right_siblings[root.operator][root.children[0].label].add(
                    root.children[1].label
                )

    def generate_next_candidates(
        self, patterns: Set[EventuallyFollowsPattern], iteration: int
    ) -> List[EventuallyFollowsPattern]:
        self.n_pruned = 0
        self.iteration = iteration
        new_patterns = []
        for pattern in patterns:
            new_patterns += self.generate_candidates_from_current_pattern(pattern)

        return new_patterns

    def __generate_single_node_sub_patterns(self) -> List[SubPattern]:
        sub_patterns = []

        for operator in OPERATORS:
            sub_patterns.append(SubPattern(operator=operator))

        for activity in self.pruning_sets.fA:
            sub_patterns.append(SubPattern(label=activity))

        return sub_patterns

    def generate_candidates_from_current_pattern(
        self,
        pattern: EventuallyFollowsPattern,
        max_height_diff=None,
        create_new_sub_patterns=True,
    ) -> List[EventuallyFollowsPattern]:
        patterns = self.generate_right_expansion_candidates(pattern, max_height_diff)

        if self.generate_ef_patterns:
            patterns += self.generate_sequential_ef_extension_patterns(pattern)
            if create_new_sub_patterns:
                patterns += self.generate_new_candidates_with_additional_subpattern(
                    pattern
                )

        return self.set_ids(patterns)

    def generate_new_candidates_with_additional_subpattern(
        self, pattern: EventuallyFollowsPattern
    ) -> List[EventuallyFollowsPattern]:
        # do not create new subpattern if predecessor is not a valid subpattern
        # examples are ->()...a or ->(a, +())
        if pattern.rightmost_leaf.label is None:
            return []

        # don't add new sub-patterns if the current sub-pattern is incomplete
        # for example, don't generate ->(a)..a, ->(+(a), +(b,c))...a, etc.
        parent = pattern.rightmost_leaf.parent
        while parent is not None:
            if len(parent.children) <= 1:
                return []

            parent = parent.parent

        patterns = []

        label_candidates = self.get_label_candidates_for_new_ef_subpattern(pattern)
        operator_candidates = self.frequent_operators
        operator_candidates = set(
            [o for o in operator_candidates if o != ConcurrencyTreeOperator.Sequential]
        )

        for label_candidate in label_candidates:
            new_pattern = self.extend_pattern_by_new_sub_pattern(
                pattern,
                SubPattern(label=label_candidate, id=pattern.rightmost_leaf.id + 1),
            )
            if new_pattern is not None:
                patterns.append(new_pattern)

        for operator_candidate in operator_candidates:
            new_pattern = self.extend_pattern_by_new_sub_pattern(
                pattern,
                SubPattern(
                    operator=operator_candidate, id=pattern.rightmost_leaf.id + 1
                ),
            )
            if new_pattern is not None:
                patterns.append(new_pattern)

        return patterns

    def get_label_candidates_for_new_ef_subpattern(
        self, pattern: EventuallyFollowsPattern
    ) -> Set[str]:
        if self.iteration <= 2:
            return self.pruning_sets.fA

        activities_in_pattern = get_activities_for_pattern(pattern)
        label_candidates = None

        for activity_in_pattern in activities_in_pattern:
            if label_candidates is None:
                label_candidates = self.frequent_real_ef_relationships[
                    activity_in_pattern
                ]
            else:
                label_candidates = label_candidates.intersection(
                    self.frequent_real_ef_relationships[activity_in_pattern]
                )

        return label_candidates

    def generate_sequential_ef_extension_patterns(
        self, pattern: EventuallyFollowsPattern
    ) -> List[EventuallyFollowsPattern]:
        if len(pattern) == 1 or len(pattern.sub_patterns[-1].children) != 0:
            return []

        if (
            pattern.sub_patterns[-1].label is not None
            and pattern.sub_patterns[-1].label
            not in self.frequent_activity_edges[ConcurrencyTreeOperator.Sequential]
        ):
            return []

        if (
            pattern.sub_patterns[-1].operator is not None
            and pattern.sub_patterns[-1].operator
            not in self.frequent_operator_edges[ConcurrencyTreeOperator.Sequential]
        ):
            return []

        new_sp_root = SubPattern(
            operator=ConcurrencyTreeOperator.Sequential, id=pattern.rightmost_leaf.id
        )
        new_sp_child = copy.copy(pattern.sub_patterns[-1])
        new_sp_child.parent = new_sp_root
        new_sp_root.children = [new_sp_child]
        new_sp_child.id += 1
        new_pattern = pattern.copy()
        new_pattern.rightmost_leaf = new_sp_child
        new_pattern.sub_patterns[-1] = new_sp_root
        new_pattern.predecessor_pattern = pattern
        new_pattern.is_leftmost_occurrence_update_required = False

        if self.pruning_strategy.can_prune(new_pattern, self.iteration):
            self.n_pruned += 1
            return []

        return [new_pattern]

    def extend_pattern_by_new_sub_pattern(
        self, pattern: EventuallyFollowsPattern, sub_pattern: SubPattern
    ) -> Optional[EventuallyFollowsPattern]:
        new_pattern = pattern.copy()
        new_pattern.sub_patterns.append(sub_pattern)
        new_pattern.rightmost_leaf = sub_pattern
        new_pattern.predecessor_pattern = pattern
        new_pattern.is_leftmost_occurrence_update_required = False

        if self.pruning_strategy.can_prune(new_pattern, self.iteration):
            self.n_pruned += 1
            return None

        return new_pattern

    def generate_right_expansion_candidates(
        self, pattern: EventuallyFollowsPattern, max_height_diff=None
    ) -> List[EventuallyFollowsPattern]:
        patterns = []
        current_sub_pattern = pattern.rightmost_leaf
        height_diff = -1

        while current_sub_pattern is not None:
            if max_height_diff is not None and max_height_diff < height_diff:
                return patterns

            # for not operator nodes, semantics does not allow child nodes
            if current_sub_pattern.operator is None:
                height_diff += 1
                current_sub_pattern = current_sub_pattern.parent
                continue

            (
                new_patterns,
                early_stopping,
            ) = self.generate_right_expansion_candidates_for_current_sub_pattern(
                pattern, current_sub_pattern, height_diff
            )
            patterns += new_patterns

            if early_stopping:
                return patterns

            height_diff += 1
            current_sub_pattern = current_sub_pattern.parent

        return patterns

    def generate_right_expansion_candidates_for_current_sub_pattern(
        self,
        pattern: EventuallyFollowsPattern,
        current_sub_pattern: SubPattern,
        height_diff: int,
    ) -> Tuple[List[EventuallyFollowsPattern], bool]:
        patterns = []
        leftmost_leaf_update_required = self.is_leftmost_leaf_update_required(
            pattern, current_sub_pattern, height_diff
        )

        has_less_equal_one_child = len(current_sub_pattern.children) <= 1

        (
            candidate_labels,
            candidate_operators,
        ) = self.get_candidates_for_inner_node_extension(pattern, current_sub_pattern)
        if len(candidate_labels) == 0 and len(candidate_operators) == 0:
            return [], has_less_equal_one_child

        for candidate_label in candidate_labels:
            new_pattern = self.extend_current_pattern_by_label(
                pattern,
                current_sub_pattern,
                candidate_label,
                height_diff,
                leftmost_leaf_update_required,
            )
            if new_pattern is not None:
                patterns.append(new_pattern)

        for candidate_operator in candidate_operators:
            new_pattern = self.extend_current_pattern_by_operator(
                pattern,
                current_sub_pattern,
                candidate_operator,
                height_diff,
                leftmost_leaf_update_required,
            )
            if new_pattern is not None:
                patterns.append(new_pattern)

        # pruning strategy: dont generate new rightmost nodes if there are nodes with at most one child that would never
        # be changed again
        return patterns, has_less_equal_one_child

    def get_candidates_for_inner_node_extension(
        self, pattern: EventuallyFollowsPattern, current_sub_pattern: SubPattern
    ) -> Tuple[Set[str], Set[ConcurrencyTreeOperator]]:
        if self.pattern_is_invalid_from_iteration_2(pattern):
            return set(), set()
        if (
            self.iteration > 3
            and len(current_sub_pattern.children) > 0
            and current_sub_pattern.children[-1].label is not None
        ):
            label_candidates = self.frequent_right_siblings[
                current_sub_pattern.operator
            ][current_sub_pattern.children[-1].label]
            operator_candidates = self.frequent_operator_edges[
                current_sub_pattern.operator
            ]
        elif (
            self.iteration == 3
            and len(current_sub_pattern.children) > 0
            and current_sub_pattern.operator != ConcurrencyTreeOperator.Fallthrough
            and current_sub_pattern.children[0].label is not None
        ):
            if current_sub_pattern.operator == ConcurrencyTreeOperator.Sequential:
                label_candidates = self.pruning_sets.dfR[
                    current_sub_pattern.children[0].label
                ]
            else:
                label_candidates = self.pruning_sets.ccR[
                    current_sub_pattern.children[0].label
                ]
            label_candidates = label_candidates.intersection(
                self.frequent_activity_edges[current_sub_pattern.operator]
            )
            operator_candidates = self.frequent_operators
        elif self.iteration > 2:
            label_candidates = self.frequent_activity_edges[
                current_sub_pattern.operator
            ]
            operator_candidates = self.frequent_operator_edges[
                current_sub_pattern.operator
            ]
        else:
            label_candidates = self.pruning_sets.fA
            operator_candidates = self.frequent_operators

        if self.iteration > 2:
            label_candidates = self.relation_prune(
                current_sub_pattern, label_candidates
            )
        label_candidates = self.get_lexicographical_order_pruned_candidates(
            current_sub_pattern, label_candidates
        )
        operator_candidates = self.prune_operator_nodes_below_other_operator(
            current_sub_pattern, operator_candidates
        )

        return label_candidates, operator_candidates

    def relation_prune(
        self, current_sub_pattern: SubPattern, label_candidates: Set[str]
    ) -> Set[str]:
        if len(label_candidates) == 0:
            return label_candidates

        if current_sub_pattern.operator != ConcurrencyTreeOperator.Sequential:
            return label_candidates

        if (
            len(current_sub_pattern.children) == 0
            or current_sub_pattern.children[0].operator is None
        ):
            return label_candidates

        df_activities, ef_activities = self.get_relation_prune_df_ef_sets(
            current_sub_pattern
        )
        for df_act in df_activities:
            label_candidates = label_candidates.intersection(
                self.pruning_sets.dfR[df_act]
            )

        for ef_act in ef_activities:
            label_candidates = label_candidates.intersection(
                self.pruning_sets.efR[ef_act]
            )

        return label_candidates

    def get_relation_prune_df_ef_sets(self, current_sub_pattern: SubPattern):
        if current_sub_pattern.operator is None:
            return {current_sub_pattern.label}, set()

        df_activities = set()
        ef_activities = set()

        if current_sub_pattern.operator == ConcurrencyTreeOperator.Sequential:
            ef_children = current_sub_pattern.children[:-1]
            for ef_child in ef_children:
                ef_activities = ef_activities.union(
                    get_activities_for_sub_pattern(ef_child)
                )

            (
                inner_df_activities,
                inner_ef_activities,
            ) = self.get_relation_prune_df_ef_sets(current_sub_pattern.children[-1])
            df_activities = df_activities.union(inner_df_activities)
            ef_activities = ef_activities.union(inner_ef_activities)

            return df_activities, ef_activities

        for child in current_sub_pattern.children:
            (
                inner_df_activities,
                inner_ef_activities,
            ) = self.get_relation_prune_df_ef_sets(child)
            df_activities = df_activities.union(inner_df_activities)
            ef_activities = ef_activities.union(inner_ef_activities)

        return df_activities, ef_activities

    def pattern_is_invalid_from_iteration_2(
        self, pattern: EventuallyFollowsPattern
    ) -> bool:
        if self.iteration != 3:
            return False

        if pattern.sub_patterns[0].operator != ConcurrencyTreeOperator.Concurrent:
            return False

        if pattern.sub_patterns[0].children[0].label is not None:
            return False

        return True

    def get_lexicographical_order_pruned_candidates(
        self, current_sub_pattern: SubPattern, label_candidates: Set[str]
    ) -> Set[str]:
        if len(current_sub_pattern.children) == 0:
            return label_candidates

        operator = current_sub_pattern.operator

        if operator == ConcurrencyTreeOperator.Sequential:
            return label_candidates

        # apply pruning based on sorting, use that concurrent operators have at most a single operator child
        activity_label = current_sub_pattern.children[-1].label

        # concurrent node cannot be extended after operator node
        if activity_label is None:
            return set()

        return set([a for a in label_candidates if a >= activity_label])

    def prune_operator_nodes_below_other_operator(
        self,
        current_sub_pattern: SubPattern,
        operator_candidates: Set[ConcurrencyTreeOperator],
    ) -> Set[ConcurrencyTreeOperator]:
        # fallthrough operators have no operator children
        if current_sub_pattern.operator == ConcurrencyTreeOperator.Fallthrough:
            return set()

        # no valid concurrent subtree has an operator child at its first position
        if (
            current_sub_pattern.operator == ConcurrencyTreeOperator.Concurrent
            and len(current_sub_pattern.children) == 0
            and self.iteration >= 3
        ):
            return set()

        return set(
            [op for op in operator_candidates if op != current_sub_pattern.operator]
        )

    def extend_current_pattern_by_label(
        self,
        pattern: EventuallyFollowsPattern,
        current_sub_pattern: SubPattern,
        label: str,
        height_diff: int,
        leftmost_leaf_update_required: bool,
    ) -> EventuallyFollowsPattern:
        new_sub_pattern = copy.deepcopy(current_sub_pattern)
        new_child_sub_pattern = SubPattern(
            label=label, parent=new_sub_pattern, id=pattern.rightmost_leaf.id + 1
        )

        return self.extend_current_pattern_by_sub_pattern(
            pattern,
            new_sub_pattern,
            new_child_sub_pattern,
            height_diff,
            leftmost_leaf_update_required,
        )

    def extend_current_pattern_by_operator(
        self,
        pattern: EventuallyFollowsPattern,
        current_sub_pattern: SubPattern,
        operator: ConcurrencyTreeOperator,
        height_diff: int,
        leftmost_leaf_update_required: bool,
    ) -> EventuallyFollowsPattern:
        new_sub_pattern = copy.deepcopy(current_sub_pattern)
        new_child_sub_pattern = SubPattern(
            operator=operator, parent=new_sub_pattern, id=pattern.rightmost_leaf.id + 1
        )

        return self.extend_current_pattern_by_sub_pattern(
            pattern,
            new_sub_pattern,
            new_child_sub_pattern,
            height_diff,
            leftmost_leaf_update_required,
        )

    def extend_current_pattern_by_sub_pattern(
        self,
        pattern: EventuallyFollowsPattern,
        current_sub_pattern: SubPattern,
        child_sub_pattern: SubPattern,
        height_diff: int,
        leftmost_leaf_update_required: bool,
    ) -> Optional[EventuallyFollowsPattern]:
        current_sub_pattern.children.append(child_sub_pattern)
        new_pattern = pattern.copy()
        new_pattern.height_diff = height_diff
        new_pattern.rightmost_leaf = child_sub_pattern
        new_pattern.is_leftmost_occurrence_update_required = (
            leftmost_leaf_update_required
        )
        while current_sub_pattern.parent:
            current_sub_pattern = current_sub_pattern.parent
        new_pattern.sub_patterns[-1] = current_sub_pattern
        new_pattern.predecessor_pattern = pattern

        if self.pruning_strategy.can_prune(new_pattern, self.iteration):
            self.n_pruned += 1
            return None

        return new_pattern

    def is_leftmost_leaf_update_required(
        self,
        predecessor_pattern: EventuallyFollowsPattern,
        current_sub_pattern: SubPattern,
        height_diff: int,
    ) -> bool:
        if not predecessor_pattern.is_leftmost_occurrence_update_required:
            return False

        if height_diff != -1:
            return False

        node = current_sub_pattern

        while node is not None:
            if len(node.children) > 1:
                return False

            node = node.parent

        return True

    def set_ids(self, patterns):
        for pattern in patterns:
            pattern.id = self.current_id
            self.current_id += 1

        return patterns
