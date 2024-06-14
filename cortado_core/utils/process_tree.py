from collections import Counter, UserString

from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.objects.process_tree.utils.generic import is_leaf


class LabelWithIndex(UserString):
    """
    Combines the label, i.e. a string, with an additional index for differentiating between multiple occurences within a process tree.
    Mostly treated like a string but with the additional index attribute being exposed.
    """

    def __init__(self, label, index):
        self.data = label
        self.index = index

    def __bool__(self):
        return bool(self.data)

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data, self.index)
        elif isinstance(other, str):
            return self.__class__(self.data + other, self.index)
        return self.__class__(self.data + str(other), self.index)

    def __radd__(self, other):
        if isinstance(other, UserString):
            return self.__class__(other.data + self.data, self.index)
        elif isinstance(other, str):
            return self.__class__(other + self.data, self.index)
        return self.__class__(str(other) + self.data, self.index)

    def __contains__(self, key):
        if self.data is None:
            return False
        return key in self.data

    def __hash__(self):
        return hash(self.data)

    @property
    def full(self):
        return f'{self.data if self.data is not None else "tau"}_{self.index}'


class CortadoProcessTree(ProcessTree):
    _hash = None

    def __hash__(self):
        if self._hash is not None:
            return self._hash
        str_repr = str(self)
        self._hash = hash(str_repr)
        return self._hash

    def __eq__(self, other):
        if isinstance(other, ProcessTree):
            if self.label is not None:
                return other.label == self.label
            elif len(self.children) == 0:
                return other.label is None and len(other.children) == 0
            else:
                return super().__eq__(other)
        return False

    def __repr__(self):
        if is_leaf(self):
            if not isinstance(self.label, LabelWithIndex):
                index_leaf_labels(self.get_root())
            return self.label.full
        else:
            return super().__repr__()

    def get_node_position(self, p=None):
        if p is None:
            p = []
        if self.parent is None:
            return p
        else:
            self_index = self.parent.children.index(self)
            return self.parent.get_node_position(p + [self_index])

    def get_root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.get_root()


def index_leaf_labels(tree: ProcessTree, counter=None):
    if counter is None:
        counter = Counter()
    if is_leaf(tree):
        counter[tree.label] += 1
        tree.label = LabelWithIndex(tree.label, counter[tree.label])
    else:
        for child in tree.children:
            child = index_leaf_labels(child, counter)
    return tree


def convert_tree(tree: ProcessTree):
    cortado_tree = convert_tree_rec(tree)
    index_leaf_labels(cortado_tree)
    return cortado_tree


def convert_tree_rec(tree: ProcessTree, parent=None):
    new_tree = CortadoProcessTree(
        operator=tree.operator, label=tree.label, parent=parent
    )
    children = [convert_tree_rec(t, parent=new_tree) for t in tree.children]
    new_tree._children = children
    return new_tree
