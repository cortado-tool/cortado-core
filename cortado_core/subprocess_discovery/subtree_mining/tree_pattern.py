from typing import Mapping, Tuple
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import (
    ConcurrencyTree,
    cTreeOperator,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree import CMConcurrencyTree
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequencyCountingStrategy, PruningSets

from cortado_core.subprocess_discovery.subtree_mining.operator_leaf_closures import _computeSeqOperatorClosure
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry
from cortado_core.subprocess_discovery.subtree_mining.utilities import (
    _compute_unique_roots,
    _getLabel,
    _update_current_sup,
    _update_subToGain,
)

class TreePattern:
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

    def __str__(self):
        """ """
        return str(self.tree) + " with support: " + str(self.support)

    def add_rmo(self, rmo: Tuple[int, int, ConcurrencyTree]):
        """ """
        self.rmo[rmo[0]] = self.rmo.get(rmo[0], []) + [(rmo[1], rmo[2])]

    def to_concurrency_group(self):
        """ """
        return self.tree.to_concurrency_group()

    def right_most_path_extension(
        self,
        pSets : PruningSets
    ):
        """ """

        extended_motifes = []

        # The extension_position as an offset in height from the rml/rmo Node in the pattern / tree
        currentNode = self.rml
        extensionOffset = 0

        # If the node is not closed, we can terminate early as we will only extend at the node until it has at least 2 children
        # Skipped to get the full set of 3 Patterns
        if currentNode.op and len(currentNode.children) < 2:

            extended_motifes = extend_node(
                self,
                currentNode,
                extensionOffset,
                pSets,
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
                            pSets
                        )
                    )

                    # If the current Operator Node isn't closed, break early
                    if len(currentNode.children) < 2:
                        break

                currentNode = currentNode.parent
                extensionOffset += 1

        return extended_motifes

    def update_rmo_list(
        self,
        treeBank: Mapping[int, TreeBankEntry],
        min_sup: int,
        freq_strat: FrequencyCountingStrategy,
        supToGain: int,
    ):
        """
        Updates the List of Right Most Occurences in the Treebank
        """

        rmo = {}
        cur_sup = 0

        # Check if there is no sequential predecessor, allow then matching all children of a nested Sequential Operator Node
        no_seq_predecessor = _check_no_seq_predecessor(self)
        
        for oc in self.rmo:

            occurences = []
            check = None

            for entry in self.rmo[oc]:

                offsetHeight = self.heightDiff
                rid, eNode = entry
                skipped_right = False 

                # Go back to find the parent node
                while offsetHeight != 0:

                    eChild = eNode
                    eNode = eNode.parent
                    
                    offsetHeight -= 1
                    
                    # Remaining offset too walk is larger 1, and we have a sequential operator that does not cover all siblings
                    if offsetHeight != 0 and eNode.op == cTreeOperator.Sequential and eChild != eNode.children[-1]:
                        skipped_right = True
                        break
                    
                if skipped_right: 
                    continue 

                # We extended somewhere along the right-most path
                if self.heightDiff > 0:

                    # Skip the eNode as it has already been covered
                    # TODO Currently only full range select on C Group,
                    # so possibly left out occurence on Seq Op

                    if check == eNode and (
                        eNode.op == cTreeOperator.Concurrent
                        or eNode.op == cTreeOperator.Fallthrough
                    ):
                        # print('Duplicate Eliminated')
                        continue

                    check = eNode

                    # There exists a right sibling
                    if eChild.rSib:

                        if eNode.op == cTreeOperator.Sequential:

                            right_sibling = eChild.rSib

                            # Check if the siblings label is the same as the label of the rml
                            if (
                                self.rml.label is not None
                                and right_sibling.label == self.rml.label
                            ) or (
                                self.rml.op is not None
                                and right_sibling.op == self.rml.op
                            ):
                                occurences.append((rid, right_sibling))

                            # Right sibling does not match the newly added rml of the motif
                            else:
                                continue

                        else:

                            right_sibling = eChild.rSib

                            while right_sibling is not None:

                                if (
                                    self.rml.op is not None
                                    and self.rml.op == right_sibling.op
                                ):
                                    occurences.append((rid, right_sibling))

                                elif (
                                    self.rml.label is not None
                                    and self.rml.label == right_sibling.label
                                ):
                                    occurences.append((rid, right_sibling))
                                    break  # Stop early on the Left most child, TODO Consider the Case of an S Label

                                right_sibling = right_sibling.rSib

                    # No right siblings, thus no pattern match
                    else:
                        continue

                # We extened the "leaf node", thus we need to check all the children of the rmo in the tree, if they match the
                # newly added node under the "leaf node"
                else:

                    if no_seq_predecessor or eNode.op != cTreeOperator.Sequential: 
                        for child in eNode.children:
                            if (
                                self.rml.label is not None and child.label == self.rml.label
                            ) or (self.rml.op is not None and child.op == self.rml.op):
                                occurences.append((rid, child))

                            else:
                                continue
                    else: 
                        lmc = eNode.children[0] 
                        if (
                                self.rml.label is not None and lmc.label == self.rml.label
                            ) or (self.rml.op is not None and lmc.op == self.rml.op):
                                occurences.append((rid, lmc))
                   
            # Add to the rmo dict the occurences:
            if len(occurences) > 0:
                rmo[oc] = occurences

                cur_sup = _update_current_sup(
                    treeBank, freq_strat, cur_sup, oc, _compute_unique_roots(occurences)
                )

            # If the support to gain is smaller than the gap between current support and min_sup we can stop early

            supToGain = _update_subToGain(
                treeBank, freq_strat, supToGain, oc, self.rmo[oc]
            )

            if min_sup > (supToGain + cur_sup):
                del self
                return False

        # Keep the pattern
        if cur_sup > min_sup:
            self.rmo = rmo
            self.support = cur_sup

            return self

        else:
            del self
            return False

def _check_no_seq_predecessor(t : TreePattern): 
        
    node = t.rml
    
    while node.parent != None: 
        
        if node.parent.op == cTreeOperator.Sequential: 
            if node.parent.children[0] != node:
                     return False

        node = node.parent 
        
    return True


def extend_node(
    tp: TreePattern,
    eNode: ConcurrencyTree,
    eOffset: int,
    pSets : PruningSets,
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

        if eNode.op == cTreeOperator.Sequential and eNode.rmc.op:
        
                    # Compute Closure over the Operator Label
                    closure_labels = _computeSeqOperatorClosure(
                        eNode.rmc,
                        pSets.dfFollowsPrune,
                        pSets.efFollowsPrune,
                        eNode.rmc.op == cTreeOperator.Concurrent,
                    )
                    
                    closure_labels = closure_labels.intersection(pSets.sibPrune[(eNode.op, eNode.rmc.op)])

                    # Compute Closure over the Operator Label
                    for activity in closure_labels:
                        extended_motifes.append(
                            extend_motif_on_operator_node(
                                tp, eNode, eOffset, op=None, label=activity
                            )
                        )
                    
                    if cTreeOperator.Concurrent in pSets.sibPrune[(eNode.op, eNode.rmc.op)]: 
                        extended_motifes.append(
                                extend_motif_on_operator_node(
                                    tp, eNode, eOffset, op=cTreeOperator.Concurrent, label=None
                                )
                            ) 
            
                    if cTreeOperator.Fallthrough in pSets.sibPrune[(eNode.op, eNode.rmc.op)]:   
                        extended_motifes.append(
                                extend_motif_on_operator_node(
                                    tp, eNode, eOffset, op=cTreeOperator.Fallthrough, label=None ) 
                            ) 

        else: 

            for l in pSets.sibPrune[(eNode.op, _getLabel(eNode.rmc))]:
                if isinstance(l, cTreeOperator): 
                
                    extended_motifes.append(
                                    extend_motif_on_operator_node(
                                        tp, eNode, eOffset, op=l, label=None
                                    )
                                )
                else: 
                    extended_motifes.append(
                        extend_motif_on_operator_node(
                            tp, eNode, eOffset, op=None, label=l
                        )
                    )

    # Operator node doesn't have a Child
    else:
        
        for l in pSets.nestPrune[(eNode.parent.op, eNode.op)]:
            if isinstance(l, cTreeOperator): 
                extended_motifes.append(
                                extend_motif_on_operator_node(
                                    tp, eNode, eOffset, op=l, label=None
                                )
                            )
            else: 

                extended_motifes.append(
                    extend_motif_on_operator_node(
                        tp, eNode, eOffset, op=None, label=l
                    )
                )
                
    return extended_motifes

def extend_motif_on_operator_node(
    tp: TreePattern,
    eNode: ConcurrencyTree,
    eHeight: int,
    op: cTreeOperator = None,
    label: str = None,
) -> TreePattern:
    """ """

    # Copy the tree and get the Node, where we extend
    ccTree, eNode = tp.tree.copy(eNode)

    # Create our new Node
    newNode = type(eNode)(children=None, rSib=None, parent=eNode, label=label, op=op)

    
    # Fix the right sibling relationship
    if len(eNode.children) > 0:
        eNode.children[-1].rSib = newNode

        if isinstance(eNode, CMConcurrencyTree):
            
            if eNode.rmc.label and len(eNode.children) > 1: 
                eNode.rmc.occList = {}

    # Add the newNode to the children:
    eNode.children.append(newNode)
    eNode.rmc = newNode

    # Create a new TreePattern
    tp_e = type(tp)(ccTree, newNode, eHeight)
    tp_e.rmo = tp.rmo
    tp_e.parent = tp

    # Keep Track of the Size
    tp_e.size = tp.size
    tp_e.size += 1

    return tp_e
