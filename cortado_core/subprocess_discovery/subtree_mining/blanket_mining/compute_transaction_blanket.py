from typing import Set
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree import CMConcurrencyTree
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree_pattern import (
    CMTreePattern,
)
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.compute_occurence_blanket import (
    ExpansionDirection,
)
from cortado_core.subprocess_discovery.subtree_mining.utilities import get_child_labels


def check_transaction_blanket(tp: CMTreePattern):

    # Creat an Iterator over the Occurence Lists
    occLists = iter(tp.tree.occList)

    # For the First Entry, compute the Candidate Expansions
    tid = next(occLists)

    # Compute the candidates starting at the root and from a single occurence
    return compute_blanket_transactions_candidates(tp, tp.tree, tid)

def check_concurrent_transaction_blanket_match(node : CMConcurrencyTree,  sibLabels : Set[str], expDir : ExpansionDirection):

    if expDir == ExpansionDirection.Left:

        lChild = node.children[0]

        # For every Tree with an Occurence of the Child Node
        for lid in lChild.occList:

            lOcc = lChild.occList[lid]
            occLabels = set()

            # For every Occurence
            for occ in lOcc:
                lIndx = occ.parent.children.index(occ)

                if lIndx > 0:
                    for lSib in occ.parent.children[:lIndx]:
                        if lSib.label:
                            occLabels.add(lSib.label)

            sibLabels = sibLabels.intersection(occLabels)

            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Right:

        rChild = node.children[-1]
        # For every Tree with an Occurence of the Child Node

        for lid in rChild.occList:

            lOcc = rChild.occList[lid]
            occLabels = set()

            # For every Occurence
            for occ in lOcc:

                rIndx = occ.parent.children.index(occ)

                if rIndx < len(occ.parent.children) - 1:

                    for rSib in occ.parent.children[rIndx + 1 :]:
                        if rSib.label: 
                            occLabels.add(rSib.label)

            sibLabels = sibLabels.intersection(occLabels)

            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Bottom:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]
            occLabels = set()

            # For every Occurence
            for occ in lOcc:

                # Search if we can find the extension in the Children
                for child in occ.children:
                    if child.label:
                        occLabels.add(child.label)

            # Check if they intersect
            sibLabels = sibLabels.intersection(occLabels)

            # if No intersection exists, break
            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Between:

        for lid in node.occList:

            lOcc = node.occList[lid]
            lChild = node.children[0].occList[lid]
            rChild = node.children[-1].occList[lid]

            betweenLabels = set()

            for idx, occ in enumerate(lOcc):

                lIndx = occ.children.index(lChild[idx])
                rIndx = occ.children.index(rChild[idx])

                betweenSiblings = get_child_labels(occ.children[lIndx + 1 : rIndx])
                

                for child in get_child_labels(node.children[1:-1]):
                    betweenSiblings.remove(child)

                betweenLabels = betweenLabels.union(set(betweenSiblings))

            sibLabels = sibLabels.intersection(betweenLabels)

            if not sibLabels:
                return False

    else:
        print("This should not happen")

    return True


def check_seq_transaction_blanket_match(node : CMConcurrencyTree,  sibLabels : Set[str], expDir : ExpansionDirection):

    if expDir == ExpansionDirection.Left:

        lChild = node.children[0]

        # For every Tree with an Occurence of the Child Node
        for lid in lChild.occList:

            lOcc = lChild.occList[lid]
            occLabels = set()

            # For every Occurence
            for occ in lOcc:

                # Find the Index of the current Child in the Tree compared to its parent
                cIndx = occ.parent.children.index(occ)

                if cIndx > 0:

                    # Get its left Sibling Labels / Op
                    lSib = occ.parent.children[cIndx - 1]
                    
                    if lSib.label:
                        occLabels.add(lSib.label)

            # Check if they intersect
            sibLabels = sibLabels.intersection(occLabels)

            # if No intersection exists, break
            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Right:

        rChild = node.children[-1]
        # For every Tree with an Occurence of the Child Node
        for lid in rChild.occList:

            lOcc = rChild.occList[lid]
            occLabels = set()

            # For every Occurence
            for occ in lOcc:

                if occ.rSib and occ.rSib.label:
                    occLabels.add(occ.rSib.label)

            # Check if they intersect
            sibLabels = sibLabels.intersection(occLabels)

            # if No intersection exists, break
            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Bottom:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]
            occLabels = set()

            # For every Occurence
            for occ in lOcc:

                occLabels.update(get_child_labels(occ.children))

            # Check if they intersect
            sibLabels = sibLabels.intersection(occLabels)

            # if No intersection exists, break
            if not sibLabels:
                return False

    else:
        print("This should not happen")

    return True


def compute_blanket_transactions_candidates(tp : CMTreePattern, tree : CMConcurrencyTree, tid : int):

    lBlanketNotEmpty = False

    occurences = tree.occList[tid]

    """
    if tree.op == cTreeOperator.Sequential:

        # The Node has Left and Right Children
        if len(tree.children) > 0:

            lSibLabels = set()
            rSibLabels = set()

            for idx, occurence in enumerate(occurences):

                lChild = tree.children[0]
                lIdx = occurence.children.index(lChild.occList[tid][idx])

                if lIdx > 0:

                    lSib = occurence.children[lIdx - 1]
                    
                    if lSib.label:
                        lSibLabels.add(lSib.label)

                rChild = tree.children[-1]
                ridx = occurence.children.index(rChild.occList[tid][idx])

                if ridx < len(occurence.children) - 1:

                    rSib = occurence.children[ridx + 1]
                    if rSib.label: 
                        rSibLabels.add(rSib.label)

            if lSibLabels:
                lBlanketNotEmpty |= check_seq_transaction_blanket_match(
                    tree, lSibLabels, expDir=ExpansionDirection.Left
                )

            if rSibLabels:
                
                lBlanketNotEmpty |= check_seq_transaction_blanket_match(
                    tree, rSibLabels, expDir=ExpansionDirection.Right
                )

        # The Node doesn't have children
        else:
            pass 

            bSibLabels = set()

            # Collect all child labels beneath the occurences
            for occurence in occurences:
                for child in occurence.children:
                    if child.label:
                        bSibLabels.add(child.label)

            lBlanketNotEmpty |= check_seq_transaction_blanket_match(
                tree, tid, bSibLabels, expDir=ExpansionDirection.Bottom
            )
    """ 
            
    if tree.op == cTreeOperator.Concurrent or tree.op == cTreeOperator.Fallthrough: 

        # The Node has Left and Right Children
        if len(tree.children) > 0:

            lSibLabels = set()
            rSibLabels = set()
            betweenSibLabels = set()

            for idx, occurence in enumerate(occurences):

                lChild = tree.children[0]
                lidx = occurence.children.index(lChild.occList[tid][idx])

                if lidx > 0:

                    lSibLabels.update(get_child_labels(occurence.children[:lidx]))

                rChild = tree.children[-1]
                ridx = occurence.children.index(rChild.occList[tid][idx])

                if ridx < len(occurence.children) - 1:

                    rSibLabels.update(get_child_labels(occurence.children[ridx + 1 :]))

                if lidx != ridx:

                    # Collect all children between the lidx and ridx
                    betweenSiblings = get_child_labels(occurence.children[lidx + 1 : ridx])
                    
                    # Remove the nodes matched by the pattern
                    for label in get_child_labels(tree.children[1:-1]): 
                        betweenSiblings.remove(label)
                        
                    betweenSibLabels = betweenSibLabels.union(set(betweenSiblings))

            if lSibLabels:
                lBlanketNotEmpty |= check_concurrent_transaction_blanket_match(
                    tree, lSibLabels, expDir=ExpansionDirection.Left
                )

            if rSibLabels:
                lBlanketNotEmpty |= check_concurrent_transaction_blanket_match(
                    tree, rSibLabels, expDir=ExpansionDirection.Right
                )

            if betweenSibLabels:
                lBlanketNotEmpty |= check_concurrent_transaction_blanket_match(
                    tree, betweenSibLabels, expDir=ExpansionDirection.Between
                )

        # The Node doesn't have children
        else:
            pass 
        
            """
            bSibLabels = set()

            # Collect all child labels beneath the occurences
            for occurence in occurences:

                bSibLabels.update(get_child_labels(occurence.children))

            lBlanketNotEmpty |= check_concurrent_transaction_blanket_match(
                tree, tid, bSibLabels, expDir=ExpansionDirection.Bottom
            )
            """




    # It is already true
    if not lBlanketNotEmpty:
        for child in tree.children:
            
            if child.op:  
                lBlanketNotEmpty |= compute_blanket_transactions_candidates(
                    tp, child, tid
                )
                
            if lBlanketNotEmpty: 
                break
        
    return lBlanketNotEmpty
