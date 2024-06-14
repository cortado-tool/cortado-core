import copy
import uuid

from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.occurrence_store.rightmost_occurence_store import (
    RightmostOccurrenceStore,
)
from cortado_core.eventually_follows_pattern_mining.util.tree import (
    get_root,
    get_rightmost_leaf,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)

from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)


def is_superpattern(
    ef_preserving_tree: ConcurrencyTree, pattern: EventuallyFollowsPattern, ef_dict
):
    occ_store = RightmostOccurrenceStore(
        [ef_preserving_tree], VariantTransactionCountingStrategy(), 1, ef_dict
    )

    pid, are_all_1_patterns_frequent = init_ef_1_patterns(pattern, occ_store)

    if not are_all_1_patterns_frequent:
        return False

    for p in enumerate_pattern(pattern, pid):
        if p.predecessor_pattern is not None:
            p.predecessor_pattern.support = 1
        occ_store.update_occurrence_lists([p])
        if p.support != 1:
            return False

    return True


def init_ef_1_patterns(pattern, occ_store):
    idx = 0
    labels_to_initialize = set()
    operators_to_initialize = set()
    for infix_pattern in pattern.sub_patterns[1:]:
        if infix_pattern.operator is not None:
            if infix_pattern.operator != cTreeOperator.Sequential:
                operators_to_initialize.add(infix_pattern.operator)
            else:
                child = infix_pattern.children[0]
                if child.operator is not None:
                    operators_to_initialize.add(child.operator)
                else:
                    labels_to_initialize.add(child.label)
        else:
            labels_to_initialize.add(infix_pattern.label)

    patterns_to_initialize = []
    for label in labels_to_initialize:
        ip = SubPattern(label=label, id=0, depth=0)
        p = EventuallyFollowsPattern(sub_patterns=[ip], rightmost_leaf=ip)
        p.id = idx
        idx += 1
        patterns_to_initialize.append(p)

    for op in operators_to_initialize:
        ip = SubPattern(operator=op, id=0, depth=0)
        p = EventuallyFollowsPattern(sub_patterns=[ip], rightmost_leaf=ip)
        p.id = idx
        idx += 1
        patterns_to_initialize.append(p)

    occ_store.update_occurrence_lists(patterns_to_initialize)

    for pattern in patterns_to_initialize:
        if pattern.support <= 0:
            return idx, False

    occ_store.set_frequent_1_patterns(patterns_to_initialize)

    return idx, True


def get_ef_preserving_concurrency_tree(
    pattern: EventuallyFollowsPattern, ef_node_label=None
) -> ConcurrencyTree:
    current_id = 1
    root = ConcurrencyTree(op=cTreeOperator.Sequential)
    root.id = 0
    if ef_node_label is None:
        ef_node_label = str(uuid.uuid4())
    last_ef_node = None

    n_infix_patterns = len(pattern.sub_patterns)

    for i, infix_pattern in enumerate(pattern.sub_patterns):
        trees, current_id = get_ef_preserving_trees_for_infix_pattern(
            infix_pattern, current_id, root
        )
        root.children += trees

        if last_ef_node is not None:
            last_ef_node.rSib = trees[0]

        if i < n_infix_patterns - 1:
            ef_node = ConcurrencyTree(parent=root, label=ef_node_label)
            ef_node.id = current_id
            root.children.append(ef_node)
            current_id += 1
            last_ef_node = ef_node
            trees[-1].rSib = ef_node

    return root


def get_ef_preserving_trees_for_infix_pattern(
    infix_pattern: SubPattern, current_id: int, parent: ConcurrencyTree
):
    node = None

    if (
        infix_pattern.operator != cTreeOperator.Sequential
        or infix_pattern.parent is not None
    ):
        node = ConcurrencyTree(
            parent=parent, label=infix_pattern.label, op=infix_pattern.operator
        )
        node.id = current_id
        current_id += 1

    children = []
    for child in infix_pattern.children:
        ts, current_id = get_ef_preserving_trees_for_infix_pattern(
            child, current_id, node
        )
        children.append(ts[0])

    for i in range(len(children) - 1):
        children[i].rSib = children[i + 1]

    if node is not None:
        node.children = children
        return [node], current_id

    for child in children:
        child.parent = parent

    return children, current_id


def enumerate_pattern(pattern: EventuallyFollowsPattern, pid):
    new_pattern = EventuallyFollowsPattern()
    predecessor = None

    for idx, infix_pattern in enumerate(pattern.sub_patterns):
        new_pattern.sub_patterns.append(None)
        infix_pattern_enumeration, _, _, _ = enumerate_infix_pattern(infix_pattern)

        if (
            idx > 0
            and infix_pattern_enumeration[0][0].operator == cTreeOperator.Sequential
        ):
            infix_pattern_enumeration[0] = (
                SubPattern(
                    label=infix_pattern_enumeration[1][0].children[0].label,
                    operator=infix_pattern_enumeration[1][0].children[0].operator,
                ),
                0,
            )
            infix_pattern_enumeration[1] = infix_pattern_enumeration[1][0], 1

        for infix_pattern, height_diff in infix_pattern_enumeration:
            new_pattern.sub_patterns[-1] = infix_pattern
            new_pattern.id = pid
            new_pattern.predecessor_pattern = predecessor
            new_pattern.rightmost_leaf = get_rightmost_leaf(infix_pattern)
            new_pattern.is_leftmost_occurrence_update_required = False
            new_pattern.support = 0
            new_pattern.height_diff = height_diff

            pid += 1
            yield new_pattern

            predecessor = new_pattern.copy()
            predecessor.id = new_pattern.id


def enumerate_infix_pattern(
    infix_pattern: SubPattern,
    parent=None,
    current_id=0,
    current_height=0,
    last_height=0,
):
    patterns = []
    if parent is None:
        parent = SubPattern(
            label=infix_pattern.label, operator=infix_pattern.operator, id=current_id
        )
        patterns.append((parent, 0))
        child_parent = parent
    else:
        parent = copy.deepcopy(parent)
        p = SubPattern(
            label=infix_pattern.label,
            operator=infix_pattern.operator,
            parent=parent,
            id=current_id,
        )
        parent.children.append(p)
        height_diff = last_height - current_height
        last_height = current_height
        patterns.append((get_root(parent), height_diff))
        child_parent = p

    current_id += 1

    for idx, child in enumerate(infix_pattern.children):
        child_patterns, current_id, child_parent, last_height = enumerate_infix_pattern(
            child, child_parent, current_id, current_height + 1, last_height
        )
        patterns += child_patterns

    return patterns, current_id, child_parent.parent, last_height
