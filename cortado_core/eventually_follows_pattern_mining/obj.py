import uuid

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator
from cortado_core.utils.split_graph import (
    Group,
    SkipGroup,
    SequenceGroup,
    ParallelGroup,
    LoopGroup,
    LeafGroup,
)


class EventuallyFollowsPattern:
    def __init__(
        self,
        sub_patterns=None,
        predecessor_pattern=None,
        rightmost_leaf=None,
        height_diff=0,
        support=0,
        leftmost_occurrence_update_required=True,
    ):
        self.sub_patterns = sub_patterns
        self.predecessor_pattern = predecessor_pattern
        self.rightmost_leaf = rightmost_leaf
        self.height_diff = height_diff
        self.support = support
        self.is_leftmost_occurrence_update_required = (
            leftmost_occurrence_update_required
        )
        self.id = -1

        if self.sub_patterns is None:
            self.sub_patterns = []

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for i, sub_pattern in enumerate(self.sub_patterns):
            if sub_pattern != other.sub_patterns[i]:
                return False

        return True

    def __len__(self):
        return len(self.sub_patterns)

    def __repr__(self):
        return str(self) + " with support " + str(self.support)

    def __str__(self):
        return "...".join([str(sp) for sp in self.sub_patterns])

    def __hash__(self):
        return hash(self.__str__())

    def copy(self):
        new_pattern = EventuallyFollowsPattern(
            None,
            None,
            self.rightmost_leaf,
            self.height_diff,
            0,
            self.is_leftmost_occurrence_update_required,
        )
        new_pattern.sub_patterns = [p for p in self.sub_patterns]

        return new_pattern


class SubPattern:
    def __init__(
        self,
        label: str = None,
        operator=None,
        parent=None,
        children=None,
        depth=-1,
        id=0,
    ):
        self.label = label
        self.operator = operator
        self.parent = parent
        self.children = children
        self.id = id

        if self.children is None:
            self.children = []

    def __len__(self):
        return 1 + sum([len(c) for c in self.children])

    def __str__(self):
        if self.label:
            return self.label

        return (
            self.operator.value + "(" + ",".join([str(c) for c in self.children]) + ")"
        )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.label is not None:
            if self.label != other.label:
                return False

        if self.operator is not None:
            if self.operator != other.operator:
                return False

        if len(self.children) != len(other.children):
            return False

        for i in range(len(self.children)):
            if not self.children[i].__eq__(other.children[i]):
                return False

        return True

    def __hash__(self):
        return hash(self.__str__())


def group_to_ef_pattern(group: Group) -> EventuallyFollowsPattern:
    if isinstance(group, SkipGroup):
        return EventuallyFollowsPattern(
            sub_patterns=[group_to_sub_pattern(g) for g in group]
        )

    return EventuallyFollowsPattern(sub_patterns=[group_to_sub_pattern(group)])


def group_to_sub_pattern(group: Group, parent: SubPattern = None) -> SubPattern:
    sub_pattern = SubPattern(children=[], parent=parent, label=None, operator=None)
    has_children = False

    if isinstance(group, SequenceGroup):
        sub_pattern.operator = cTreeOperator.Sequential
        sub_pattern.label = None
        has_children = True

    elif isinstance(group, ParallelGroup):
        sub_pattern.operator = cTreeOperator.Concurrent
        sub_pattern.label = None
        has_children = True

    elif isinstance(group, LeafGroup):
        subgroups = sorted([subgroup for subgroup in group])

        if len(subgroups) == 1:
            sub_pattern.operator = None
            sub_pattern.label = subgroups[0]
        else:
            sub_pattern.operator = cTreeOperator.Fallthrough
            sub_pattern.label = None

            children = []

            for activity in subgroups:
                children.append(
                    SubPattern(
                        children=None, parent=sub_pattern, label=activity, operator=None
                    )
                )

            sub_pattern.children = children
    else:
        raise ValueError("other types of operators are not supported")

    if has_children:
        if isinstance(group, ParallelGroup):
            sub_pattern.children = []
            operator_child = None

            for child in group:
                sub_tree = group_to_sub_pattern(child, sub_pattern)

                if sub_tree.operator is not None:
                    operator_child = sub_tree
                else:
                    sub_pattern.children.append(sub_tree)

            if operator_child:
                sub_pattern.children.append(operator_child)

        else:
            sub_pattern.children = [
                group_to_sub_pattern(child, sub_pattern) for child in group
            ]

    return sub_pattern
