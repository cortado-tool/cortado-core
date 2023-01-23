from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


def apply_reduction_rules(variant: ConcurrencyTree) -> ConcurrencyTree:
    if variant.op is None:
        return variant

    if len(variant.children) == 1 and variant.parent is not None:
        child = variant.children[0]
        child_pos = get_child_position(variant.parent, variant)
        variant.parent.children[child_pos] = child
        child.parent = variant.parent

        return apply_reduction_rules(child)
    op = variant.op

    new_children = []
    for child in variant.children:
        new_child = apply_reduction_rules(child)
        if new_child.op == op:
            new_children += new_child.children
            for child_child in new_child.children:
                child_child.parent = variant
        else:
            new_children.append(new_child)
            new_child.parent = variant

    variant.children = new_children

    return variant


def get_child_position(parent: ConcurrencyTree, compare_child: ConcurrencyTree):
    if parent is None:
        return -1

    for i, child in enumerate(parent.children):
        if id(child) == id(compare_child):
            return i

    return -1
