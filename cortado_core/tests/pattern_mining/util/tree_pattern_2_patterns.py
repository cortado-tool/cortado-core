from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)

from cortado_core.subprocess_discovery.subtree_mining.obj import PruningSets
from cortado_core.subprocess_discovery.subtree_mining.operator_leaf_closures import (
    _computeSeqOperatorClosure,
)
from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import (
    TreePattern,
    extend_motif_on_operator_node,
)


class TreePattern_2_patterns(TreePattern):
    def __init__(self, T: ConcurrencyTree, rml: ConcurrencyTree, heightDiff: int):
        """ """
        self.tree = T
        self.rml = rml
        self.heightDiff = heightDiff
        self.parent = None
        self.support = None
        self.size = None
        self.maximal = True
        self.closed = True
        self.rmo = {}

    def to_concurrency_group(self):
        """ """
        return self.tree.to_concurrency_group()

    def right_most_path_extension(
        self,
        pSets: PruningSets,
        skipPrune: bool,
        has_fallthroughs: bool,
    ):
        """ """

        # print('Right Blanket', self.rightBlanket)

        extended_motifes = []

        # The extension_position as an offset in height from the rml/rmo Node in the pattern / tree
        currentNode = self.rml
        extensionOffset = 0

        # If the node is not closed, we can terminate early as we will only extend at the node until it has at least 2 children
        if currentNode.op and (not skipPrune) and len(currentNode.children) < 2:
            extended_motifes = extend_node(
                self,
                currentNode,
                extensionOffset,
                pSets,
                skipPrune,
                has_fallthroughs,
            )

            # Backtrack from the rmo to the root along the right-most path, but only if the bottom node is closed, i.e it has at least 2 operators
        else:
            while currentNode is not None:
                # Only append to operator Nodes
                if currentNode.op:
                    extended_motifes.extend(
                        extend_node(
                            self,
                            currentNode,
                            extensionOffset,
                            pSets,
                            skipPrune,
                            has_fallthroughs,
                        )
                    )

                    # If the current Operator Node isn't closed, break early
                    if (not skipPrune) and len(currentNode.children) < 2:
                        break

                currentNode = currentNode.parent
                extensionOffset += 1

        return extended_motifes


def extend_node(
    tp: TreePattern_2_patterns,
    eNode: ConcurrencyTree,
    eOffset: int,
    pSets: PruningSets,
    skipPrune: bool,
    has_fallthroughs,
):
    """
    [summary]

    Args:
        tp (TreePattern): [description]
        eNode (ConcurrencyTree): [description]
        eOffset (int): [description]
        parallel_activities ([type]): [description]
        parallel_relations ([type]): [description]
        directly_follows_pairs ([type]): [description]
        directly_follows_activitites ([type]): [description]
        activities ([type]): [description]

    Returns:
        [type]: [description]
    """

    extended_motifes = []

    # Node has a Child
    if len(eNode.children) > 0:
        if eNode.op == cTreeOperator.Sequential:
            # The Right Most Sibling of the Node is an Activity, only append frequent directly follows pairs for it
            if eNode.rmc.label:
                # Expand if the label is in the frequent directly follows case, default case could cause a non frequent left hand side
                if eNode.rmc.label in pSets.dfLabelPrune:
                    for activity in pSets.dfLabelPrune[eNode.rmc.label]:
                        extended_motifes.append(
                            extend_motif_on_operator_node(
                                tp, eNode, eOffset, op=None, label=activity
                            )
                        )

                for op in pSets.operatorPrune[eNode.rmc.label]:
                    extended_motifes.append(
                        extend_motif_on_operator_node(
                            tp, eNode, eOffset, op=op, label=None
                        )
                    )

            # Compute Closure over Operator Children
            else:
                if not skipPrune:
                    # Compute Closure over the Operator Label
                    closure_labels = _computeSeqOperatorClosure(
                        eNode.rmc,
                        pSets.dfFollowsPrune,
                        pSets.efFollowsPrune,
                        eNode.rmc.op == cTreeOperator.Concurrent,
                    )

                    closure_labels = closure_labels.intersection(
                        pSets.operatorActivityPrune[eNode.rmc.op]
                    )

                    # Compute Closure over the Operator Label
                    for activity in closure_labels:
                        extended_motifes.append(
                            extend_motif_on_operator_node(
                                tp, eNode, eOffset, op=None, label=activity
                            )
                        )

                else:
                    for activity in pSets.operatorActivityPrune[eNode.rmc.op]:
                        extended_motifes.append(
                            extend_motif_on_operator_node(
                                tp, eNode, eOffset, op=None, label=activity
                            )
                        )

                for op in pSets.operatorOperatorPrune[eNode.rmc.op]:
                    extended_motifes.append(
                        extend_motif_on_operator_node(
                            tp, eNode, eOffset, op=op, label=None
                        )
                    )

        elif eNode.op == cTreeOperator.Fallthrough:
            for activity in pSets.ftLabelPrune[eNode.rmc.label]:
                if eNode.rmc.label <= activity:  # Perform an in-order check
                    extended_motifes.append(
                        extend_motif_on_operator_node(
                            tp, eNode, eOffset, op=None, label=activity
                        )
                    )

        elif eNode.op == cTreeOperator.Concurrent:
            # If we have a known left leave, we only append activities lexicographically larger than it
            # No further extensions after operator nodes
            if eNode.rmc.label:
                if eNode.rmc.label in pSets.ccLabelPrune:
                    for activity in pSets.ccLabelPrune[eNode.rmc.label]:
                        # If the activity is larger or equal to the leaf label and the pair is frequent
                        if activity >= eNode.rmc.label:
                            extended_motifes.append(
                                extend_motif_on_operator_node(
                                    tp, eNode, eOffset, op=None, label=activity
                                )
                            )

                for op in pSets.operatorPrune[eNode.rmc.label]:
                    extended_motifes.append(
                        extend_motif_on_operator_node(
                            tp, eNode, eOffset, op=op, label=None
                        )
                    )

        else:
            print("Not an matched op", eNode.op)

    # Operator node doesn't have a Child
    else:
        if eNode.op == cTreeOperator.Sequential:
            extended_motifes.append(
                extend_motif_on_operator_node(
                    tp, eNode, eOffset, op=cTreeOperator.Concurrent, label=None
                )
            )

            for activity in pSets.dfNestPrune:
                extended_motifes.append(
                    extend_motif_on_operator_node(
                        tp, eNode, eOffset, op=None, label=activity
                    )
                )

            if has_fallthroughs:
                extended_motifes.append(
                    extend_motif_on_operator_node(
                        tp, eNode, eOffset, op=cTreeOperator.Fallthrough, label=None
                    )
                )

        elif eNode.op == cTreeOperator.Fallthrough:
            for activity in pSets.ftNestPrune:
                extended_motifes.append(
                    extend_motif_on_operator_node(
                        tp, eNode, eOffset, op=None, label=activity
                    )
                )

        else:
            extended_motifes.append(
                extend_motif_on_operator_node(
                    tp, eNode, eOffset, op=cTreeOperator.Sequential, label=None
                )
            )

            if has_fallthroughs:
                extended_motifes.append(
                    extend_motif_on_operator_node(
                        tp, eNode, eOffset, op=cTreeOperator.Fallthrough, label=None
                    )
                )

            for activity in pSets.ccNestPrune:
                extended_motifes.append(
                    extend_motif_on_operator_node(
                        tp, eNode, eOffset, op=None, label=activity
                    )
                )

    return extended_motifes
