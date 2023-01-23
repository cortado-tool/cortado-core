from collections import Counter
from typing import List, Mapping
import networkx as nx
from functools import cmp_to_key

from cortado_core.utils.cgroups_graph import ConcurrencyGroup
from cortado_core.utils.constants import ARTIFICAL_END_NAME, ARTIFICAL_START_NAME
from cortado_core.models.infix_type import InfixType
from cortado_core.utils.collection_utils import count_ordererd_sub_list_occurrences, count_unordered_sub_list_occurrences


class Group(list):

    def __init__(self, lst=()):
        super().__init__(lst)
        self.graphs: Mapping[ConcurrencyGroup, int] = {}
        self.performance = {
            'wait_time': None,
            'service_time': None
        }

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
        if 'follows' in serialized and isinstance(serialized['follows'], List):
            return SequenceGroup(lst=[Group.deserialize(group) for group in serialized['follows']])

        if 'parallel' in serialized and isinstance(serialized['parallel'], List):
            return ParallelGroup(lst=[Group.deserialize(group) for group in serialized['parallel']])

        if 'leaf' in serialized and isinstance(serialized['leaf'], List):
            return LeafGroup(lst=serialized['leaf'])

        if 'loop' in serialized and isinstance(serialized['loop']. List):
            return LoopGroup(lst=serialized['leaf'])

        return SequenceGroup(lst=[])

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __lt__(self, other):
        return str(self) < str(other)

    def list_length(self):
        return len([0 for _ in self])

    def toHashSet(self):
        res = set()
        for group in self:
            res.add(hash(group))
        return res

    def __len__(self) -> int:
        return 0

    def number_of_activities(self) -> int:
        return 0


class SequenceGroup(Group):

    def serialize(self, include_performance=True):
        if include_performance:
            return {'follows': [e.serialize(include_performance=include_performance) for e in self],
                    'performance': self.performance}
        else:
            return {'follows': [e.serialize(include_performance=include_performance) for e in self]}

    def __hash__(self):
        return tuple(self).__hash__()

    # Already in sorted order
    def sort(self):
        return SequenceGroup([g.sort() for g in self])

    def countInfixOccurrences(self, fragment: Group, infixType: InfixType = InfixType.PROPER_INFIX, isRootNode = False):
        # note that fragment is always of type SequenceGroup currently 
        # even if the length of the Sequence is only 1, thus we can 
        # do the check for prefix/postfix as follows 
        isPrefix = isRootNode and list(fragment) == self[0:fragment.list_length()]
        isPostfix = isRootNode and list(fragment) == self[-fragment.list_length():]

        if infixType == InfixType.PREFIX:
            return 1 if isPrefix else 0

        if infixType == InfixType.POSTFIX:
            return 1 if isPostfix else 0

        if infixType == InfixType.PROPER_INFIX:
            return self.countProperInfixOccurrences(fragment, isRootNode, isPrefix, isPostfix)
            
    
    def countProperInfixOccurrences(self, fragment: Group, isRootNode: bool, isPrefix: bool, isPostfix: bool):
        count = 0
        # initially consider the complete group
        group = self

        # if the fragment is a prefix and self is the root node 
        # we dont consider the prefix for the count (as we are 
        # looking for proper infixes)
        if isPrefix and isRootNode:
            group = group[fragment.list_length():]

        # if the fragment is a postfix and self is the root node 
        # we dont consider the postfix for the count (as we are 
        # looking for proper infixes)
        if isPostfix and isRootNode:
            group = group[:group.list_length()-fragment.list_length()]

        # if the fragment SequenceGroup has only length 1, we extract the Group and reassign 
        # the fragment. Otherwise the recursion would not work 
        if isinstance(fragment, SequenceGroup) and fragment.list_length() == 1:
            fragment = fragment[0]
        
        # if the fragment is a SequenceGroup with length > 1 we check if 
        # the fragment is an ordered sub sequence of the group
        if isinstance(fragment, SequenceGroup):
            sub_group_count = count_ordererd_sub_list_occurrences(
                list(group), list(fragment))

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
            return {'parallel': [e.serialize(include_performance=include_performance) for e in sorted(self)],
                    'performance': self.performance}
        else:
            return {'parallel': [e.serialize(include_performance=include_performance) for e in sorted(self)]}

    def __hash__(self):
        return tuple(sorted(self)).__hash__()

    def sort(self):
        return ParallelGroup(sorted([x.sort() for x in self], key=lambda x: repr(x)))

    def countInfixOccurrences(self, fragment: Group):
        count = 0
        group = self

        # if the fragment is a ParallelGroup, we count the number of occurrences of the
        # fragment while ignoring the order 
        if isinstance(fragment, ParallelGroup):

            sub_group_count = count_unordered_sub_list_occurrences(
                self, fragment)
                
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
    def serialize(self, include_performance=True):
        if include_performance:
            return {'loop': [e.serialize(include_performance=include_performance) for e in sorted(self)],
                    'performance': self.performance}
        else:
            return {'loop': [e.serialize(include_performance=include_performance) for e in sorted(self)]}

    def __hash__(self):
        return tuple(self).__hash__()

    def sort(self):
        return self

    def __len__(self) -> int:
        return len(self[0])

    def number_of_activities(self) -> int:
        return sum([e.number_of_activities() for e in self])


class LeafGroup(Group):
    def serialize(self, include_performance=True):
        
        if self[0] == ARTIFICAL_END_NAME:
            return {'end' : True}
        
        elif self[0] == ARTIFICAL_START_NAME: 
            return {'start' : True} 
        
        if include_performance:
            return {'leaf': sorted(self), 'performance': self.performance if include_performance else None}
        else:
            return {'leaf': sorted(self)}

    def __hash__(self):
        return tuple(sorted(self)).__hash__()

    # Sorted by default
    def sort(self):
        return LeafGroup(self)


    def countInfixOccurrences(self, fragment: Group):
        if isinstance(fragment, LeafGroup) and fragment == self:
            return 1
        return 0

    def __len__(self) -> int:
        return 1

    def number_of_activities(self) -> int:
        # leaf groups contain more than one activity in the case of fallthroughs
        return len([x for x in self])


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
    connected_components = list(
        nx.connected_components(G_split_target.to_undirected()))
    if len(connected_components) > 1:
        if G_split_target == G_parallel:
            connected_components = sorted(
                connected_components, key=cmp_to_key(get_compare(G_follows)))
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
