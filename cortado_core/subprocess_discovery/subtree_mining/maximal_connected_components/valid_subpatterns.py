from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    BARROW,
    cTreeOperator,
)


def __compute_size_of_tree(tree) -> int:
    size = 1

    if tree.op:
        for child in tree.children:
            size += __compute_size_of_tree(child)

    return size


def compute_valid_leaf_eliminated_children(tree):
    valid_substrings = []
    full_rep = [(repr(child) + BARROW) for child in tree.children]

    if len(tree.children) > 2:
        if tree.op != cTreeOperator.Sequential:
            for index, child in enumerate(tree.children):
                if child.label:
                    cString = "".join(full_rep[:index] + full_rep[index + 1 :])
                    valid_substrings.append(tree.op.value + cString)

    for index, child in enumerate(tree.children):
        if child.op:
            for sString in compute_valid_leaf_eliminated_children(child):
                cString = "".join(
                    full_rep[:index] + [sString + BARROW] + full_rep[index + 1 :]
                )
                valid_substrings.append(tree.op.value + cString)

    return valid_substrings


def _compute_subtree_eliminated_children(tree):
    valid_substrings = []
    tSize = __compute_size_of_tree(tree)
    full_rep = [(repr(child) + BARROW) for child in tree.children]

    if len(tree.children) > 2:
        if tree.op != cTreeOperator.Sequential:
            for index, child in enumerate(tree.children):
                # All op nodes in the left tree have at least 2 children
                if child.op:
                    # Add the string of the child left-out
                    cString = "".join(full_rep[:index] + full_rep[index + 1 :])
                    cSize = tSize - __compute_size_of_tree(child)

                    valid_substrings.append((cSize, tree.op.value + cString))

    for index, child in enumerate(tree.children):
        cSize = __compute_size_of_tree(child)

        for iSize, sString in _compute_subtree_eliminated_children(child):
            sSize = tSize - (cSize - iSize)
            cString = "".join(
                full_rep[:index] + [sString + BARROW] + full_rep[index + 1 :]
            )
            valid_substrings.append((sSize, tree.op.value + cString))

    return valid_substrings


# Computes valid subtree nested under the Root
def _get_root_enclosed_subtrees(root, full):
    valid_substrings = []

    if full or len(root.children) == 2:
        for child in root.children:
            if child.op:
                cSize = __compute_size_of_tree(child)
                valid_substrings.append((cSize, repr(child)))

    return valid_substrings


def _compute_left_out_subtree_strings(tree):
    valid_substrings = []
    tSize = __compute_size_of_tree(tree)
    tmpSize = 0

    full_rep = [(repr(child) + BARROW) for child in tree.children]

    for cIdx, child in enumerate(tree.children):
        cSize = __compute_size_of_tree(child)

        if child.op:
            sStrings = _compute_left_out_subtree_strings(child)

            if 0 < cIdx < len(tree.children) - 1:
                cString = "".join(full_rep[cIdx + 1 :])
                cString = str(tree.op.value) + cString
                valid_substrings.append((tSize - tmpSize - cSize, cString))

                for sSize, sString in sStrings:
                    cString = "".join(full_rep[cIdx + 1 :])
                    cString = str(tree.op.value) + sString + BARROW + cString
                    valid_substrings.append(
                        (tSize - tmpSize - (cSize - sSize), cString)
                    )

            for sSize, sString in sStrings:
                cString = "".join(
                    full_rep[:cIdx] + [sString + BARROW] + full_rep[cIdx + 1 :]
                )
                cString = str(tree.op.value) + cString
                valid_substrings.append((tSize - (cSize - sSize), cString))

        tmpSize += cSize

    return valid_substrings


# Move along the left-most path and eleiminate left-most activity leafs in sequential groups
def _compute_left_most_path_eliminated_leafs(tree):
    valid_substrings = []

    if len(tree.children) > 0:
        full_rep = [(repr(child) + BARROW) for child in tree.children]
        lmc = tree.children[0]

        if len(tree.children) > 2:
            if tree.op == cTreeOperator.Sequential:
                if lmc.label:
                    cString = "".join(full_rep[1:])
                    valid_substrings.append(tree.op.value + cString)

        if tree.op == cTreeOperator.Sequential:
            if lmc.op:
                for sString in _compute_left_most_path_eliminated_leafs(lmc):
                    cString = "".join([sString + BARROW] + full_rep[1:])
                    valid_substrings.append(tree.op.value + cString)
        else:
            for index, child in enumerate(tree.children):
                if child.op:
                    for sString in _compute_left_most_path_eliminated_leafs(child):
                        cString = "".join(
                            full_rep[:index]
                            + [sString + BARROW]
                            + full_rep[index + 1 :]
                        )
                        valid_substrings.append(tree.op.value + cString)

    return valid_substrings


# Move along the right-most path and eleminate right-most activity leafs in sequential groups
def _compute_right_most_path_eliminated_leafs(tree):
    valid_substrings = []

    if len(tree.children) > 0:
        full_rep = [(repr(child) + BARROW) for child in tree.children]
        rmc = tree.children[-1]

        if len(tree.children) > 2:
            if tree.op == cTreeOperator.Sequential:
                if rmc.label:
                    cString = "".join(full_rep[:-1])
                    valid_substrings.append(tree.op.value + cString)

        if tree.op == cTreeOperator.Sequential:
            if rmc.op:
                for sString in _compute_right_most_path_eliminated_leafs(rmc):
                    cString = "".join(full_rep[:-1] + [sString + BARROW])
                    valid_substrings.append(tree.op.value + cString)
        else:
            for index, child in enumerate(tree.children):
                if child.op:
                    for sString in _compute_right_most_path_eliminated_leafs(child):
                        cString = "".join(
                            full_rep[:index]
                            + [sString + BARROW]
                            + full_rep[index + 1 :]
                        )
                        valid_substrings.append(tree.op.value + cString)

    return valid_substrings


# Move along the right-most path and eleminate right-most subtrees
def _compute_right_most_path_eliminated_subtree(tree):
    valid_substrings = []

    if len(tree.children) > 0:
        tSize = __compute_size_of_tree(tree)
        full_rep = [(repr(child) + BARROW) for child in tree.children]

        rmc = tree.children[-1]
        rSize = __compute_size_of_tree(rmc)
        if len(tree.children) > 2:
            if tree.op == cTreeOperator.Sequential:
                if rmc.op:
                    cString = "".join(full_rep[:-1])
                    cSize = tSize - rSize
                    valid_substrings.append((cSize, tree.op.value + cString))

        if tree.op == cTreeOperator.Sequential:
            if rmc.op:
                for iSize, sString in _compute_right_most_path_eliminated_subtree(rmc):
                    sSize = tSize - (rSize - iSize)
                    cString = "".join(full_rep[:-1] + [sString + BARROW])
                    valid_substrings.append((sSize, tree.op.value + cString))

        else:
            for index, child in enumerate(tree.children):
                cSize = __compute_size_of_tree(child)
                for iSize, sString in _compute_right_most_path_eliminated_subtree(
                    child
                ):
                    sSize = tSize - (cSize - iSize)
                    cString = "".join(
                        full_rep[:index] + [sString + BARROW] + full_rep[index + 1 :]
                    )
                    valid_substrings.append((sSize, tree.op.value + cString))

    return valid_substrings


# Move along the left-most path and eliminate left-most subtrees
def _compute_left_most_path_eliminated_subtree(tree):
    valid_substrings = []

    if len(tree.children) > 0:
        tSize = __compute_size_of_tree(tree)
        full_rep = [(repr(child) + BARROW) for child in tree.children]

        lmc = tree.children[0]
        lSize = __compute_size_of_tree(lmc)

        if len(tree.children) > 2:
            if tree.op == cTreeOperator.Sequential:
                if lmc.op:
                    cString = "".join(full_rep[1:])
                    cSize = tSize - lSize
                    valid_substrings.append((cSize, tree.op.value + cString))

        if tree.op == cTreeOperator.Sequential:
            if lmc.op:
                for iSize, sString in _compute_left_most_path_eliminated_subtree(lmc):
                    sSize = tSize - (lSize - iSize)
                    cString = "".join([sString + BARROW] + full_rep[1:])
                    valid_substrings.append((sSize, tree.op.value + cString))

        else:
            for index, child in enumerate(tree.children):
                cSize = __compute_size_of_tree(child)
                for iSize, sString in _compute_left_most_path_eliminated_subtree(child):
                    sSize = tSize - (cSize - iSize)
                    cString = "".join(
                        full_rep[:index] + [sString + BARROW] + full_rep[index + 1 :]
                    )
                    valid_substrings.append((sSize, tree.op.value + cString))

    return valid_substrings
