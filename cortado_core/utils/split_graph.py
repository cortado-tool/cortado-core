from collections import Counter
from copy import deepcopy
from functools import cmp_to_key
from itertools import pairwise, product, combinations
from typing import List, Mapping

import networkx as nx

from cortado_core.models.infix_type import InfixType
from cortado_core.utils.cgroups_graph import ConcurrencyGroup
from cortado_core.utils.collection_utils import (
    count_ordererd_sub_list_occurrences,
    count_unordered_sub_list_occurrences,
)
from cortado_core.utils.constants import ARTIFICAL_END_NAME, ARTIFICAL_START_NAME


class Group(list):
    list_length = list.__len__

    def __init__(
        self,
        lst: tuple = (),
        infix_type: InfixType = InfixType.NOT_AN_INFIX,
        id: int = None,
    ):
        """

        :param lst:
        :type lst:
        :param infix_type:
        :type infix_type:
        :param id: dfs id of the group node
        :type id: int
        """
        super().__init__(lst)
        self.graphs: Mapping[ConcurrencyGroup, int] = {}
        self.performance = {"wait_time": None, "service_time": None}
        self.infix_type: InfixType = infix_type
        self.id: int = id

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.print()

    def print(self, i=0):
        s = "-" * i

        if not isinstance(self, LeafGroup):
            s += f"{type(self).__name__}:\n"

        for e in self:
            if isinstance(e, Group):
                s += e.print(i + 2)
            else:
                s += str(e)
                s += "\n"
        return s

    def serialize(self, include_performance=True):
        return ""

    @staticmethod
    def deserialize(serialized):
        if "follows" in serialized and isinstance(serialized["follows"], List):
            return SequenceGroup(
                lst=[Group.deserialize(group) for group in serialized["follows"]]
            )

        if "parallel" in serialized and isinstance(serialized["parallel"], List):
            return ParallelGroup(
                lst=[Group.deserialize(group) for group in serialized["parallel"]]
            )

        if "choice" in serialized and isinstance(serialized["choice"], List):
            return ChoiceGroup(
                lst=[Group.deserialize(group) for group in serialized["choice"]]
            )

        if "fallthrough" in serialized and isinstance(serialized["fallthrough"], List):
            return FallthroughGroup(
                lst=[Group.deserialize(group) for group in serialized["fallthrough"]]
            )

        if "leaf" in serialized and isinstance(serialized["leaf"], List):
            return LeafGroup(lst=serialized["leaf"])

        if "loop" in serialized and isinstance(serialized["loop"], List):
            repeat_count_min = serialized.get("repeat_count_min", None)
            repeat_count_max = serialized.get("repeat_count_max", None)
            return LoopGroup(
                lst=[Group.deserialize(group) for group in serialized["loop"]],
                min_count=repeat_count_min,
                max_count=repeat_count_max,
            )

        if "optional" in serialized and isinstance(serialized["optional"], list):
            return OptionalGroup(
                lst=[Group.deserialize(group) for group in serialized["optional"]]
            )

        if "skip" in serialized and isinstance(serialized["skip"], List):
            return SkipGroup(
                lst=[Group.deserialize(group) for group in serialized["skip"]]
            )

        if "start" in serialized:
            return StartGroup(lst=[])

        if "end" in serialized:
            return EndGroup(lst=[])

        if "wildcard" in serialized:
            return WildcardGroup(lst=[])

        if "anything" in serialized:
            return AnythingGroup(lst=[])

        return SequenceGroup(lst=[])

    def checkGroupType(self):
        # ensure there is no choiceGroup outside sequentializer. If there is, return False
        for group in self:
            if isinstance(group, Group):
                if isinstance(group, ChoiceGroup):
                    return False
                elif not group.checkGroupType():
                    return False
        return True

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __lt__(self, other):
        return str(self) < str(other)

    def toHashSet(self):
        res = set()
        for group in self:
            res.add(hash(group))
        return res

    def __len__(self) -> int:
        return 0

    def number_of_activities(self) -> int:
        return 0

    def assign_dfs_ids(self):
        def __dfs_traversal(group, offset):
            group.id = offset

            offset += 1

            if not isinstance(group, LeafGroup):
                for member in group:
                    offset = __dfs_traversal(member, offset)

            return offset

        __dfs_traversal(self, 0)


class SequenceGroup(Group):
    def serialize(self, include_performance=True):
        if include_performance:
            return {
                "follows": [
                    e.serialize(include_performance=include_performance) for e in self
                ],
                "performance": self.performance,
                "infix_type": self.infix_type,
                "id": self.id,
            }
        else:
            return {
                "follows": [
                    e.serialize(include_performance=include_performance) for e in self
                ],
                "infix_type": self.infix_type,
                "id": self.id,
            }

    def __hash__(self):
        temp_tuple_with_infix = tuple(self) + (self.infix_type,)
        return temp_tuple_with_infix.__hash__()

    # Already in sorted order
    def sort(self):
        return SequenceGroup([g.sort() for g in self], self.infix_type, self.id)

    def countInfixOccurrences(
        self,
        fragment: Group,
        infixType: InfixType = InfixType.PROPER_INFIX,
        isRootNode=False,
    ):
        # note that fragment is always of type SequenceGroup currently
        # even if the length of the Sequence is only 1, thus we can
        # do the check for prefix/postfix as follows
        isPrefix = isRootNode and list(fragment) == self[0 : fragment.list_length()]
        isPostfix = isRootNode and list(fragment) == self[-fragment.list_length() :]

        if infixType == InfixType.PREFIX:
            return 1 if isPrefix else 0

        if infixType == InfixType.POSTFIX:
            return 1 if isPostfix else 0

        if infixType == InfixType.PROPER_INFIX:
            return self.countProperInfixOccurrences(
                fragment, isRootNode, isPrefix, isPostfix
            )

    def countProperInfixOccurrences(
        self, fragment: Group, isRootNode: bool, isPrefix: bool, isPostfix: bool
    ):
        # calculate proper infixes as well as prefix and postfix occurences

        count = 0
        # initially consider the complete group
        group = self

        # if the fragment SequenceGroup has only length 1, we extract the Group and reassign
        # the fragment. Otherwise the recursion would not work
        if isinstance(fragment, SequenceGroup) and fragment.list_length() == 1:
            fragment = fragment[0]

        # if the fragment is a SequenceGroup with length > 1 we check if
        # the fragment is an ordered sub sequence of the group
        if isinstance(fragment, SequenceGroup):
            sub_group_count = count_ordererd_sub_list_occurrences(
                list(group), list(fragment)
            )

            # if the fragment is contained in group, increase the counter
            # and remove the nodes contained in the fragment from group
            if sub_group_count > 0:
                count += sub_group_count
                s = set(fragment)
                group = [x for x in self if x not in s]

        # recursively call countInfixOccurrences on the elements in group
        for sub_group in group:
            count += sub_group.countInfixOccurrences(fragment)

        return count

    def __len__(self) -> int:
        l = [len(e) for e in self]

        if len(l) > 0:
            return sum(l)
        else:
            return 1

    def number_of_activities(self) -> int:
        return sum([e.number_of_activities() for e in self])


class ParallelGroup(Group):
    def serialize(self, include_performance=True):
        if include_performance:
            return {
                "parallel": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ],
                "performance": self.performance,
                "infix_type": self.infix_type,
                "id": self.id,
            }
        else:
            return {
                "parallel": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ],
                "infix_type": self.infix_type,
                "id": self.id,
            }

    def __hash__(self):
        temp_tuple_with_infix = tuple(sorted(self)) + (self.infix_type,)
        return temp_tuple_with_infix.__hash__()

    def sort(self):
        return ParallelGroup(
            sorted([x.sort() for x in self], key=lambda x: repr(x)), id=self.id
        )

    def countInfixOccurrences(self, fragment: Group):
        count = 0
        group = self

        # if the fragment is a ParallelGroup, we count the number of occurrences of the
        # fragment while ignoring the order
        if isinstance(fragment, ParallelGroup):
            sub_group_count = count_unordered_sub_list_occurrences(self, fragment)

            if sub_group_count > 0:
                # fragment is subgroup of the parallel group
                count += sub_group_count
                # compute remaining nodes in the parallel group and count recursively
                s = set(fragment)
                group = [x for x in self if x not in s]

        # call countInfixOccurrences recursively for the remaining nodes
        for sub_group in group:
            count += sub_group.countInfixOccurrences(fragment)

        return count

    def __len__(self) -> int:
        l = [len(e) for e in self]

        if len(l) > 0:
            return max(l)
        else:
            return 1

    def isSubGroupOf(self, group: Group):
        filtered = [x for x in group if x in self]
        counted = Counter(filtered)
        return min(counted.values())

    def number_of_activities(self) -> int:
        return sum([e.number_of_activities() for e in self])


class ChoiceGroup(Group):
    def serialize(self, include_performance=True):
        if include_performance:
            return {
                "choice": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ],
                "performance": self.performance,
            }
        else:
            return {
                "choice": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ]
            }

    def __hash__(self):
        return tuple(sorted(self)).__hash__()

    def sort(self):
        return ChoiceGroup(
            sorted([x.sort() for x in self], key=lambda x: repr(x)), id=self.id
        )

    def countInfixOccurrences(self, fragment: Group):
        count = 0
        group = self

        # if the fragment is a ParallelGroup, we count the number of occurrences of the
        # fragment while ignoring the order
        if isinstance(fragment, ChoiceGroup):
            sub_group_count = count_unordered_sub_list_occurrences(self, fragment)

            if sub_group_count > 0:
                # fragment is subgroup of the parallel group
                count += sub_group_count
                # compute remaining nodes in the parallel group and count recursively
                s = set(fragment)
                group = [x for x in self if x not in s]

        # call countInfixOccurrences recursively for the remaining nodes
        for sub_group in group:
            count += sub_group.countInfixOccurrences(fragment)

        return count

    def __len__(self) -> int:
        l = [len(e) for e in self]

        if len(l) > 0:
            return max(l)
        else:
            return 1

    def isSubGroupOf(self, group: Group):
        filtered = [x for x in group if x in self]
        counted = Counter(filtered)
        return min(counted.values())

    def number_of_activities(self) -> int:
        return sum([e.number_of_activities() for e in self])


class FallthroughGroup(Group):
    def serialize(self, include_performance=True):
        if include_performance:
            return {
                "fallthrough": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ],
                "performance": self.performance,
            }
        else:
            return {
                "fallthrough": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ]
            }

    def __hash__(self):
        return tuple(sorted(self)).__hash__()

    def sort(self):
        return FallthroughGroup(
            sorted([x.sort() for x in self], key=lambda x: repr(x)), id=self.id
        )

    def countInfixOccurrences(self, fragment: Group):
        count = 0
        group = self

        # if the fragment is a ParallelGroup, we count the number of occurrences of the
        # fragment while ignoring the order
        if isinstance(fragment, FallthroughGroup):
            sub_group_count = count_unordered_sub_list_occurrences(self, fragment)

            if sub_group_count > 0:
                # fragment is subgroup of the parallel group
                count += sub_group_count
                # compute remaining nodes in the parallel group and count recursively
                s = set(fragment)
                group = [x for x in self if x not in s]

        # call countInfixOccurrences recursively for the remaining nodes
        for sub_group in group:
            count += sub_group.countInfixOccurrences(fragment)

        return count

    def __len__(self) -> int:
        l = [len(e) for e in self]

        if len(l) > 0:
            return max(l)
        else:
            return 1

    def isSubGroupOf(self, group: Group):
        filtered = [x for x in group if x in self]
        counted = Counter(filtered)
        return min(counted.values())

    def number_of_activities(self) -> int:
        return sum([e.number_of_activities() for e in self])


class LoopGroup(Group):
    def __init__(self, *args, **kwargs):
        self.min_count = kwargs.pop("min_count", None)
        self.max_count = kwargs.pop("max_count", None)

        super().__init__(*args, **kwargs)

    def serialize(self, include_performance=True):
        if include_performance:
            return {
                "loop": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ],
                "performance": self.performance,
                "infix_type": self.infix_type,
            }
        else:
            return {
                "loop": [
                    e.serialize(include_performance=include_performance)
                    for e in sorted(self)
                ],
                "infix_type": self.infix_type,
            }

    def __hash__(self):
        temp_tuple_with_infix = tuple(self) + (self.infix_type,)
        return temp_tuple_with_infix.__hash__()

    def sort(self):
        return self

    def __len__(self) -> int:
        return len(self[0])

    def number_of_activities(self) -> int:
        return sum([e.number_of_activities() for e in self])


class SkipGroup(Group):
    """
    Used to indicate skips in eventually follows patterns
    """

    def serialize(self, include_performance=True):
        return {
            "skip": [
                e.serialize(include_performance=include_performance) for e in self
            ],
            "infix_type": self.infix_type,
        }

    def __hash__(self):
        temp_tuple_with_infix = tuple(self) + (self.infix_type,)
        return temp_tuple_with_infix.__hash__()

    def sort(self):
        return self

    def __len__(self) -> int:
        l = [len(e) for e in self]

        if len(l) > 0:
            return max(l)
        else:
            return 1

    def number_of_activities(self) -> int:
        return sum([e.number_of_activities() for e in self])


class LeafGroup(Group):
    def serialize(self, include_performance=True):
        if self[0] == ARTIFICAL_END_NAME:
            return {"end": True}

        elif self[0] == ARTIFICAL_START_NAME:
            return {"start": True}

        if include_performance:
            return {
                "leaf": sorted(self),
                "performance": self.performance if include_performance else None,
                "infix_type": self.infix_type,
                "id": self.id,
            }
        else:
            return {"leaf": sorted(self), "infix_type": self.infix_type, "id": self.id}

    def __hash__(self):
        temp_tuple_with_infix = tuple(sorted(self)) + (self.infix_type,)
        return temp_tuple_with_infix.__hash__()

    # Sorted by default
    def sort(self):
        return LeafGroup(self, id=self.id)

    def countInfixOccurrences(self, fragment: Group):
        if isinstance(fragment, LeafGroup) and fragment == self:
            return 1
        return 0

    def __len__(self) -> int:
        return 1

    def number_of_activities(self) -> int:
        # leaf groups contain more than one activity in the case of fallthroughs
        return len([x for x in self])


class AnythingGroup(Group):
    """Meant to used as a leaf"""

    pass


class OptionalGroup(Group):
    pass


class StartGroup(Group):
    """Meant to used as a leaf"""

    pass


class EndGroup(Group):
    """Meant to used as a leaf"""

    pass


class WildcardGroup(Group):
    """Meant to used as a leaf"""

    pass


def get_compare(G_follows):
    def compare(p1, p2):
        e1 = next(iter(p1))
        e2 = next(iter(p2))
        if (e1, e2) in G_follows.edges:
            return -1
        else:
            return 1

    return compare


def cut(G_follows, G_parallel, G_split_target):
    connected_components = list(nx.connected_components(G_split_target.to_undirected()))
    if len(connected_components) > 1:
        if G_split_target == G_parallel:
            connected_components = sorted(
                connected_components, key=cmp_to_key(get_compare(G_follows))
            )
            group = SequenceGroup()
        else:
            group = ParallelGroup()

        for connected_component in connected_components:
            G_parallel_cut = G_parallel.subgraph(connected_component)
            G_follows_cut = G_follows.subgraph(connected_component)

            split = split_graph(G_follows_cut, G_parallel_cut)
            group.append(split)
        return group
    else:
        return None


def sequence_cut(G_follows, G_parallel):
    return cut(G_follows, G_parallel, G_parallel)


def parallel_cut(G_follows, G_parallel):
    return cut(G_follows, G_parallel, G_follows)


def split_graph(G_follows, G_parallel):
    if len(G_follows.nodes) == 1:
        return LeafGroup(list(G_follows.nodes))
    groups = sequence_cut(G_follows, G_parallel)
    if groups == None:
        groups = parallel_cut(G_follows, G_parallel)

    if groups == None:
        groups = LeafGroup([e for e in G_follows.nodes])
        # groups = FallthroughGroup([LeafGroup([n]) for n in G_follows.nodes])

    return groups


def split_group(g):
    G_follows = nx.DiGraph()
    G_follows.add_nodes_from(g.events)
    G_follows.add_edges_from(g.follows)

    G_parallel = nx.Graph()
    G_parallel.add_nodes_from(g.events)
    for edge in g.concurrency_pairs:
        if len(edge) == 1:
            G_parallel.add_edge(next(iter(edge)), next(iter(edge)))
        else:
            edge = list(edge)
            G_parallel.add_edge(edge[0], edge[1])

    v = split_graph(G_follows, G_parallel)
    return v


def create_graph_for_cvariant(cvariant):
    cvariant_renamed = deepcopy(cvariant)
    activity_map = rename_cvariant_inplace(cvariant_renamed)
    id_name_map = {name: id for id, name in enumerate(activity_map.keys())}
    graph = _create_graph_for_cvariant(cvariant_renamed)
    graph.restore_names(activity_map, id_name_map)
    return graph


def rename_cvariant_inplace(cvariant, c=Counter(), activity_names={}):
    if isinstance(cvariant, LeafGroup):
        for i in range(len(cvariant)):
            old_name = cvariant[i]
            new_name = old_name + str(c[old_name])
            cvariant[i] = new_name
            activity_names[new_name] = old_name
            c[old_name] += 1
    else:
        for child in cvariant:
            rename_cvariant_inplace(child, c, activity_names)

    return activity_names


def _create_graph_for_cvariant(cvariant):
    new_graph = ConcurrencyGroup()
    if isinstance(cvariant, LeafGroup):
        new_graph.events.update(cvariant)
        new_graph.start_activities.update(cvariant)
        new_graph.end_activities.update(cvariant)
        return new_graph

    child_graphs = list(map(_create_graph_for_cvariant, cvariant))
    new_graph.events.update(*map(lambda child: child.events, child_graphs))
    new_graph.follows.update(*map(lambda child: child.follows, child_graphs))
    new_graph.directly_follows.update(
        *map(lambda child: child.directly_follows, child_graphs)
    )
    new_graph.concurrency_pairs.update(
        *map(lambda child: child.concurrency_pairs, child_graphs)
    )

    following_events = set()
    for child in reversed(child_graphs):
        for e1, e2 in product(child.events, following_events):
            new_graph.follows.add((e1, e2))
        following_events.update(child.events)

    if isinstance(cvariant, SequenceGroup):
        new_graph.start_activities = child_graphs[0].start_activities
        new_graph.end_activities = child_graphs[-1].end_activities

        for current, next in pairwise(child_graphs):
            for e1, e2 in product(current.end_activities, next.start_activities):
                new_graph.directly_follows.add((e1, e2))

    elif isinstance(cvariant, ParallelGroup):
        new_graph.start_activities = set.union(
            *map(lambda child: child.start_activities, child_graphs)
        )
        new_graph.end_activities = set.union(
            *map(lambda child: child.end_activities, child_graphs)
        )

        for c1, c2 in combinations(child_graphs, 2):
            for e1, e2 in product(c1.events, c2.events):
                new_graph.directly_follows.add((e1, e2))
                new_graph.directly_follows.add((e2, e1))
                new_graph.concurrency_pairs.add((e1, e2))
                # Not needed as the pair is only necessary once and the right order is set on restoring names
                # new_graph.concurrency_pairs.add((e2, e1))
    else:
        raise ValueError(
            "Can only build graphs for LeafGroup, SequenceGroup or ParallelGroup"
        )

    return new_graph
