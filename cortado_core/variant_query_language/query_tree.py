from enum import Enum
from typing import List, Set


class LOperator(Enum):

    AND = "AND"
    OR = "OR"


class UnaryOperator(Enum):

    contains = "has"
    isStart = "startsWith"
    isEnd = "endsWith"


class BinaryOperator(Enum):
    EventualyFollows = "-->"
    DirectlyFollows = "->"
    Concurrent = "||"


class QuantifierOperator(Enum):
    Equals = "="
    Less = "<"
    Greater = ">"


class QueryTree:
    def __init__(self, lst=(), height=None):
        self.height = height
        self.nChildren = 0

    def __str__(self) -> str:
        return self.print()

    def sort(self):

        if isinstance(self, OperatorNode):
            self.sort()

        return self

    def set_height(self):

        if isinstance(self, OperatorNode):
            self.height = max([e.set_height() for e in self.children]) + 1

        else:
            self.height = 1

        return self.height

    def print(self, i=0):
        s = "-" * i

        if isinstance(self, OperatorNode):
            if self.neg:
                s += " NOT "
            s += f" {self.lOp.value}:\n"

            for e in self.children:
                s += e.print(i + 2)

        elif isinstance(self, ExpressionLeaf):
            s += " " + str(self)
            s += "\n"

        return s

    def get_nLeafs(self):

        if isinstance(self, OperatorNode):
            return sum([e.get_nLeafs() for e in self.children])

        if isinstance(self, ExpressionLeaf):
            return self.get_nLeafs()

    def get_nNodes(self):

        if isinstance(self, OperatorNode):
            return sum([e.get_nNodes() for e in self.children])

        if isinstance(self, ExpressionLeaf):
            return self.get_nNodes()

    def get_nExpressions(self):

        if isinstance(self, OperatorNode):
            return sum([e.get_nExpressions() for e in self.children])

        if isinstance(self, ExpressionLeaf):
            return self.get_nExpressions()


class OperatorNode(QueryTree):
    def __init__(self, lOp: LOperator, children: List[QueryTree], neg: bool):
        self.lOp = lOp
        self.children = children
        self.neg = neg
        self.nChildren = len(children)

    def sort(self):
        self.children = sorted(
            [c.sort() for c in self.children], key=lambda x: (x.height, x.nChildren)
        )

        return self


class ExpressionLeaf(QueryTree):
    def __init__(self):
        super()

    def __str__(self):

        if isinstance(self, UnaryExpressionLeaf):
            return str(self)

        elif isinstance(self, BinaryExpressionLeaf):
            return str(self)

    def get_nLeafs(self):
        return 1

    def get_nNodes(self):
        return 1

    def get_nExpressions(self):

        if isinstance(self, UnaryExpressionLeaf):
            return len(self.activities)

        elif isinstance(self, BinaryExpressionLeaf):
            return max(len(self.lactivities), len(self.ractivities))


class ExpressionGroup(List):
    def __init__(self, lst=[]):
        super().__init__(lst)

    def getMembers(self, activities: Set[str]):
        return activities.difference(self) if self.inv else set(self)


class AnyGroup(ExpressionGroup):
    def __init__(self, lst=[], inv=False):
        super().__init__(lst)
        self.inv = inv

    def __str__(self):

        res = "[" + ", ".join(self) + "]"

        if self.inv:
            res = "~ " + res

        return res

    def copy(self):

        return AnyGroup(self, self.inv)


class AllGroup(ExpressionGroup):
    def __init__(self, lst=[], inv=False):
        super().__init__(lst)
        self.inv = inv

    def __str__(self):

        res = "{" + ", ".join(self) + "}"

        if self.inv:
            res = "~ " + res

        return res

    def copy(self):

        return AllGroup(self, self.inv)


class UnaryExpressionLeaf(ExpressionLeaf):
    def __init__(
        self,
        activities: ExpressionGroup,
        operator: UnaryOperator,
        negated: bool = False,
        qOp=None,
        number=None,
    ):

        self.operator = operator
        self.activities = activities
        self.neg = negated
        self.nChildren = 0
        self.qOp = qOp
        self.number = number

    def __hash__(self) -> int:
        return (
            str(self.operator).__hash__()
            + str(self.activities).__hash__()
            + str(self.neg).__hash__()
        )

    def copy(self):
        return UnaryExpressionLeaf(self.activities, self.operator, self.neg)

    def __str__(self):

        s = ""

        if self.neg:
            s += "NOT "

        s += str(self.operator.value) + " "

        s += str(self.activities)

        return s


class BinaryExpressionLeaf(ExpressionLeaf):
    def __init__(
        self,
        lActivities: ExpressionGroup,
        rActivities: ExpressionGroup,
        operator: BinaryOperator,
        negated: bool = False,
        qOp=None,
        number=None,
    ):

        self.operator = operator
        self.lactivities = lActivities
        self.ractivities = rActivities
        self.neg = negated
        self.nChildren = 0
        self.qOp = qOp
        self.number = number

    def __hash__(self) -> int:
        return (
            str(self.operator).__hash__()
            + str(self.lactivities).__hash__()
            + str(self.ractivities).__hash__()
            + str(self.neg).__hash__()
        )

    def __str__(self):
        s = ""

        if self.neg:
            s += "NOT "

        s += str(self.lactivities)

        s += " " + str(self.operator.value) + " "

        s += str(self.ractivities)

        return s

    def copy(self):
        return BinaryExpressionLeaf(
            self.lactivities, self.ractivities, self.operator, self.neg
        )
