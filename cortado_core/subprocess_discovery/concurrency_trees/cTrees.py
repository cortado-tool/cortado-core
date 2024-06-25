from enum import Enum
from itertools import zip_longest
from typing import List

from cortado_core.models.infix_type import InfixType
from cortado_core.utils.cgroups_graph import ConcurrencyGroup
from cortado_core.utils.constants import (
    ARTIFICAL_END_NAME,
    ARTIFICAL_START_NAME,
    BARROW,
)
from cortado_core.utils.split_graph import (
    LeafGroup,
    ParallelGroup,
    SequenceGroup,
    LoopGroup,
)


class cTreeOperator(Enum):
    """
    Operators used in cTrees
    """

    Sequential = "\u2192"
    Concurrent = "\u2227"
    Fallthrough = "\u2715"
    Loop = "*"


class ConcurrencyTree:
    def __repr__(self) -> str:
        """
        Computes a DFS Encoding of the Tree
        """
        if self.label:
            return self.label
        else:
            cString = ""

            if self.children:
                cString = "".join([(repr(child) + BARROW) for child in self.children])

            return self.op.value + cString

    def __str__(self) -> str:
        """
        Computes a BFS Encoding of the Tree
        """

        if self.label:
            return self.label
        else:
            if self.children:
                cString = ("," + " ").join([str(child) for child in self.children])
            else:
                cString = " "

            return self.op.value + "(" + cString + ")"

    def __init__(
        self,
        children: list = None,
        rSib=None,
        parent=None,
        label: str = None,
        op: cTreeOperator = None,
        infix_type: InfixType = InfixType.NOT_AN_INFIX,
        leaf_nodes=None,
        dfsid: int = None,
    ):
        self.label: str = label
        self.op: cTreeOperator = op
        self.rSib: ConcurrencyTree = rSib
        self.parent: ConcurrencyTree = parent
        self.id: int = dfsid
        self.bfsid: int = -1
        self.n_traces = 0
        self.infix_type: InfixType = infix_type
        self.leaf_nodes: list = leaf_nodes or []

        if not children:
            children = []

        self.children: List[ConcurrencyTree] = children

        if len(children) > 0:
            self.rmc: ConcurrencyTree = children[-1]
        else:
            self.rmc: ConcurrencyTree | None = None

    def copy(self, child):
        """
        Creates a copy of a concurrency tree, if a child paramenter is passed, returns the copy of that child in the new tree.

        Args:
            child ([type]): [description]

        Returns:
            [type]: [description]
        """
        cChildren = []

        cChild = None

        for c in self.children:
            cT, cc = c.copy(child)
            cChildren.append(cT)

            if cc is not None:
                cChild = cc

        copy = ConcurrencyTree(cChildren, None, None, self.label, self.op)
        copy.id = self.id
        copy.bfsid = self.bfsid

        for c, rSib in zip_longest(cChildren, cChildren[1:], fillvalue=None):
            c.rSib = rSib
            c.parent = copy

        if self == child:
            cChild = copy

        return copy, cChild

    def to_concurrency_group(self):
        """ """

        if self.label:
            return LeafGroup((self.label,), self.infix_type)

        elif self.op == cTreeOperator.Sequential:
            return SequenceGroup(
                tuple([child.to_concurrency_group() for child in self.children]),
                self.infix_type,
            )

        elif self.op == cTreeOperator.Concurrent:
            return ParallelGroup(
                tuple([child.to_concurrency_group() for child in self.children]),
                self.infix_type,
            )

        elif self.op == cTreeOperator.Fallthrough:
            return LeafGroup(
                tuple([child.label for child in self.children]), self.infix_type
            )

        elif self.op == cTreeOperator.Loop:
            return LoopGroup(
                tuple([LeafGroup((child.label,)) for child in self.children]),
                self.infix_type,
            )

    def add_artifical_start_end(self):
        """ """

        if self.op == cTreeOperator.Concurrent or self.label:
            artificialStart = ConcurrencyTree(
                None, self, None, ARTIFICAL_START_NAME, None
            )
            artificialEnd = ConcurrencyTree(None, None, None, ARTIFICAL_END_NAME, None)

            artificialRoot = ConcurrencyTree(
                [artificialStart, self, artificialEnd],
                None,
                None,
                None,
                cTreeOperator.Sequential,
            )

            self.parent = artificialRoot
            self.rSib = artificialEnd
            artificialStart.parent = artificialRoot
            artificialEnd.parent = artificialRoot

            return artificialRoot

        else:
            artificialStart = ConcurrencyTree(
                None, self.children[0], self, ARTIFICAL_START_NAME, None
            )
            artificialEnd = ConcurrencyTree(None, None, self, ARTIFICAL_END_NAME, None)

            self.children[-1].rSib = artificialEnd
            self.rmc = artificialEnd
            self.children = [artificialStart] + self.children + [artificialEnd]

            return self

    def get_node_by_dfsid(self, dfsid: int):
        if self.id == dfsid:
            return self

        for child in self.children:
            node = child.get_node_by_dfsid(dfsid)

            if node:
                return node

        return None

    def get_rml(self):
        try:
            if self.children[-1].label is not None:
                return self.children[-1]
            return self.children[-1].get_rml()
        except IndexError:
            return self

    def set_leaf_nodes(self):
        if self.label:
            self.leaf_nodes.append(self.label)
        else:
            for child in self.children:
                child.set_leaf_nodes()
                self.leaf_nodes.extend(child.leaf_nodes)


def cTreeFromcGroup(
    group: ConcurrencyGroup,
    parent: ConcurrencyTree = None,
    infix_type=InfixType.NOT_AN_INFIX,
):
    """
    Transforms a (sorted) Concurrency Group into a ConcurrencyTree recursivly
    """
    cTree = ConcurrencyTree(
        children=None,
        parent=parent,
        rSib=None,
        label=None,
        op=None,
        infix_type=infix_type,
        dfsid=group.id,
    )
    hasChildren = False

    if isinstance(group, SequenceGroup):
        cTree.op = cTreeOperator.Sequential
        cTree.label = None
        hasChildren = True

    elif isinstance(group, ParallelGroup):
        cTree.op = cTreeOperator.Concurrent
        cTree.label = None
        hasChildren = True

    elif isinstance(group, LoopGroup):
        cTree.op = cTreeOperator.Loop
        cTree.label = None
        hasChildren = True

    elif isinstance(group, list):
        activites = sorted([activity for activity in group])

        if len(activites) == 1:
            cTree.op = None
            cTree.label = activites[0]

        else:
            cTree.op = cTreeOperator.Fallthrough
            cTree.label = None

            children = []

            for activity in activites:
                children.append(
                    ConcurrencyTree(
                        children=None,
                        parent=cTree,
                        rSib=None,
                        label=activity,
                        op=None,
                        dfsid=None,
                    )
                )

            cTree.children = children

    if hasChildren:
        if isinstance(group, ParallelGroup):
            cTree.children = []
            opChild = None

            for child in group:
                subTree = cTreeFromcGroup(child, cTree)

                if subTree.op:
                    opChild = subTree

                else:
                    cTree.children.append(subTree)

            if opChild:
                cTree.children.append(opChild)

        else:
            cTree.children = [cTreeFromcGroup(child, cTree) for child in group]

    for child, rSib in zip_longest(cTree.children, cTree.children[1:], fillvalue=None):
        child.rSib = rSib

    return cTree
