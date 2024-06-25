from cortado_core.eventually_follows_pattern_mining.obj import (
    SubPattern,
    EventuallyFollowsPattern,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import set_tree_attributes
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    cTreeOperator,
    ConcurrencyTree,
)


def parse_pattern(string_rep) -> EventuallyFollowsPattern:
    subpattern_reps = string_rep.split("...")
    subpatterns = [parse_sub_pattern(s) for s in subpattern_reps]
    pattern = EventuallyFollowsPattern(subpatterns)
    set_rightmost_leaf(pattern)
    set_preorder_ids(pattern)

    return pattern


def parse_concurrency_tree(string_rep) -> ConcurrencyTree:
    depth_cache = dict()
    depth = 0
    tree = parse_ctree_recursive(string_rep, depth_cache, depth)
    set_tree_attributes(tree)
    set_right_siblings(tree)

    return tree


def set_right_siblings(tree: ConcurrencyTree):
    for i, child in enumerate(tree.children[:-1]):
        child.rSib = tree.children[i + 1]

    for child in tree.children:
        set_right_siblings(child)


def set_rightmost_leaf(pattern):
    child = pattern.sub_patterns[-1]

    while len(child.children) != 0:
        child = child.children[-1]

    pattern.rightmost_leaf = child


def parse_sub_pattern(string_rep):
    depth_cache = dict()
    depth = 0
    return parse_recursive(string_rep, depth_cache, depth)


def parse_recursive(string_rep, depth_cache, depth):
    string_rep = string_rep.strip()
    operator = None
    node = None
    if string_rep.startswith(cTreeOperator.Sequential.value):
        operator = cTreeOperator.Sequential
        string_rep = string_rep[len(cTreeOperator.Sequential.value) :]
    elif string_rep.startswith(cTreeOperator.Concurrent.value):
        operator = cTreeOperator.Concurrent
        string_rep = string_rep[len(cTreeOperator.Concurrent.value) :]
    elif string_rep.startswith(cTreeOperator.Fallthrough.value):
        operator = cTreeOperator.Fallthrough
        string_rep = string_rep[len(cTreeOperator.Fallthrough.value) :]

    if operator is not None:
        parent = None if depth == 0 else depth_cache[depth - 1]
        node = SubPattern(operator=operator, parent=parent, depth=depth)
        depth_cache[depth] = node
        if parent is not None:
            parent.children.append(node)
        depth += 1
        string_rep = string_rep.strip()
        assert string_rep[0] == "("
        parse_recursive(string_rep[1:], depth_cache, depth)
    else:
        label = None
        if string_rep.startswith("'"):
            string_rep = string_rep[1:]
            escape_ext = string_rep.find("'")
            label = string_rep[0:escape_ext]
            string_rep = string_rep[escape_ext + 1 :]

        if label is not None:
            parent = None if depth == 0 else depth_cache[depth - 1]
            node = SubPattern(label=label, parent=parent, depth=depth)
            if parent is not None:
                parent.children.append(node)

        while string_rep.strip().startswith(")"):
            depth -= 1
            string_rep = (string_rep.strip())[1:]
        if len(string_rep.strip()) > 0:
            parse_recursive((string_rep.strip())[1:], depth_cache, depth)

    return node


def parse_ctree_recursive(string_rep, depth_cache, depth):
    string_rep = string_rep.strip()
    operator = None
    node = None
    if string_rep.startswith(cTreeOperator.Sequential.value):
        operator = cTreeOperator.Sequential
        string_rep = string_rep[len(cTreeOperator.Sequential.value) :]
    elif string_rep.startswith(cTreeOperator.Concurrent.value):
        operator = cTreeOperator.Concurrent
        string_rep = string_rep[len(cTreeOperator.Concurrent.value) :]
    elif string_rep.startswith(cTreeOperator.Fallthrough.value):
        operator = cTreeOperator.Fallthrough
        string_rep = string_rep[len(cTreeOperator.Fallthrough.value) :]

    if operator is not None:
        parent = None if depth == 0 else depth_cache[depth - 1]
        node = ConcurrencyTree(op=operator, parent=parent)
        depth_cache[depth] = node
        if parent is not None:
            parent.children.append(node)
        depth += 1
        string_rep = string_rep.strip()
        assert string_rep[0] == "("
        parse_ctree_recursive(string_rep[1:], depth_cache, depth)
    else:
        label = None
        if string_rep.startswith("'"):
            string_rep = string_rep[1:]
            escape_ext = string_rep.find("'")
            label = string_rep[0:escape_ext]
            string_rep = string_rep[escape_ext + 1 :]

        if label is not None:
            parent = None if depth == 0 else depth_cache[depth - 1]
            node = ConcurrencyTree(label=label, parent=parent)
            if parent is not None:
                parent.children.append(node)

        while string_rep.strip().startswith(")"):
            depth -= 1
            string_rep = (string_rep.strip())[1:]
        if len(string_rep.strip()) > 0:
            parse_ctree_recursive((string_rep.strip())[1:], depth_cache, depth)

    return node


def set_preorder_ids(pattern: EventuallyFollowsPattern):
    idx = 0
    for sub_patterns in pattern.sub_patterns:
        idx = set_ids_sub_pattern(sub_patterns, idx)


def set_ids_sub_pattern(sub_pattern: SubPattern, start_idx=0) -> int:
    idx = start_idx
    sub_pattern.id = idx
    idx += 1

    for child in sub_pattern.children:
        idx = set_ids_sub_pattern(child, idx)

    return idx
