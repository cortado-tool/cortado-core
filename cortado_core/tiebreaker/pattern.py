from typing import List, Union

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator

WILDCARD_MATCH = '...'


class TiebreakerPattern:
    def __init__(self, labels: List[str] = None, operator: Union[cTreeOperator, WILDCARD_MATCH] = None,
                 children: List = None, parent=None, id=-1, match_multiple=False):
        self.labels = labels
        if self.labels is None:
            self.labels = []
        self.operator = operator
        self.children = children
        if self.children is None:
            self.children = []

        self.match_multiple = match_multiple
        self.parent = parent
        self.id = id

    def __str__(self):
        if len(self.labels) == 1:
            return self.labels[0]

        if len(self.labels) > 0:
            return '{' + ','.join([str(c) for c in self.labels]) + '}'

        if self.operator == WILDCARD_MATCH:
            return WILDCARD_MATCH

        return self.operator.value + '(' + ','.join([str(c) for c in self.children]) + ')'


def set_preorder_ids(pattern: TiebreakerPattern, current_id=0):
    pattern.id = current_id
    current_id += 1

    for child in pattern.children:
        current_id = set_preorder_ids(child, current_id)

    return current_id


def parse_tiebreaker_pattern(string_rep):
    depth_cache = dict()
    depth = 0
    return parse_pattern_recursive(string_rep, depth_cache, depth)


def parse_pattern_recursive(string_rep, depth_cache, depth):
    string_rep = string_rep.strip()
    operator = None
    node = None
    if string_rep.startswith(cTreeOperator.Sequential.value):
        operator = cTreeOperator.Sequential
        string_rep = string_rep[len(cTreeOperator.Sequential.value):]
    elif string_rep.startswith('->'):
        operator = cTreeOperator.Sequential
        string_rep = string_rep[len('->'):]
    elif string_rep.startswith(cTreeOperator.Concurrent.value):
        operator = cTreeOperator.Concurrent
        string_rep = string_rep[len(cTreeOperator.Concurrent.value):]
    elif string_rep.startswith('+'):
        operator = cTreeOperator.Concurrent
        string_rep = string_rep[len('+'):]
    elif string_rep.startswith(cTreeOperator.Fallthrough.value):
        operator = cTreeOperator.Fallthrough
        string_rep = string_rep[len(cTreeOperator.Fallthrough.value):]
    elif string_rep.startswith('x'):
        operator = cTreeOperator.Fallthrough
        string_rep = string_rep[len('x'):]
    elif string_rep.startswith('...'):
        operator = WILDCARD_MATCH
        string_rep = string_rep[len('...'):]

    if operator is not None and operator != WILDCARD_MATCH:
        parent = None if depth == 0 else depth_cache[depth - 1]
        node = TiebreakerPattern(operator=operator, parent=parent, children=None)
        depth_cache[depth] = node
        if parent is not None:
            parent.children.append(node)
        depth += 1
        string_rep = string_rep.strip()
        assert (string_rep[0] == '(')
        parse_pattern_recursive(string_rep[1:], depth_cache, depth)
    elif operator is not None and operator == WILDCARD_MATCH:
        parent = None if depth == 0 else depth_cache[depth - 1]
        node = TiebreakerPattern(operator=operator, parent=parent, children=None)
        if parent is not None:
            parent.children.append(node)
        while string_rep.strip().startswith(')'):
            depth -= 1
            string_rep = (string_rep.strip())[1:]
        if len(string_rep.strip()) > 0:
            parse_pattern_recursive((string_rep.strip())[1:], depth_cache, depth)
    else:
        labels = []
        match_multiple = False
        if string_rep.startswith('\''):
            string_rep = string_rep[1:]
            escape_ext = string_rep.find('\'')
            labels = [string_rep[0:escape_ext]]
            string_rep = string_rep[escape_ext + 1:]
            match_multiple = False
        elif string_rep.startswith('{'):
            string_rep = string_rep[1:]
            escape_ext = string_rep.find('}')
            labels = [l for l in string_rep[0:escape_ext].split(',')]
            labels = [l[1:-1] for l in labels]
            string_rep = string_rep[escape_ext + 1:]
            match_multiple = True

        parent = None if depth == 0 else depth_cache[depth - 1]
        node = TiebreakerPattern(labels=labels, parent=parent, match_multiple=match_multiple)
        if parent is not None:
            parent.children.append(node)

        while string_rep.strip().startswith(')'):
            depth -= 1
            string_rep = (string_rep.strip())[1:]
        if len(string_rep.strip()) > 0:
            parse_pattern_recursive((string_rep.strip())[1:], depth_cache, depth)

    return node
