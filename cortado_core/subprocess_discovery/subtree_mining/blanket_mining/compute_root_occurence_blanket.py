from typing import Set
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree import (
    CMConcurrencyTree,
)

from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree_pattern import (
    CMTreePattern,
)

from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.compute_occurence_blanket import (
    ExpansionDirection,
)

from cortado_core.subprocess_discovery.subtree_mining.utilities import get_child_labels

def check_root_occurence_blanket(tp: CMTreePattern):

    # Creat an Iterator over the Occurence Lists
    occLists = iter(tp.tree.occList)

    # For the First Entry, compute the Candidate Expansions
    tid = next(occLists)

    # Compute the candidates starting at the root and from a single occurence
    return compute_blanket_root_occurence_candidates(tp, tp.tree, tid)

def check_concurrent_root_occurence_blanket_match(tp : CMTreePattern, node : CMConcurrencyTree, sibLabels : Set[str], expDir : ExpansionDirection):

    if expDir == ExpansionDirection.Left:

        lChild = node.children[0]

        # For every Tree with an Occurence of the Child Node
        for lid in lChild.occList:

            lOcc = lChild.occList[lid]
            
            rootIds = [e[0] for e in tp.rmo[lid]]
            label_root_dict = {label :  set(rootIds) for label in sibLabels}

            # For every Occurence
            for root, occ in zip(rootIds, lOcc):
                lIndx = occ.parent.children.index(occ)

                if lIndx > 0:
                    for lSib in occ.parent.children[:lIndx]:
                        if lSib.label and lSib.label in label_root_dict:
                            label_root_dict[lSib.label].discard(root)


            for label, roots in label_root_dict.items(): 
                if len(roots) > 0: 
                    sibLabels.remove(label)

            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Right:

        rChild = node.children[-1]
        # For every Tree with an Occurence of the Child Node

        for lid in rChild.occList:

            lOcc = rChild.occList[lid]
            rootIds = [e[0] for e in tp.rmo[lid]]
            label_root_dict = {label :  set(rootIds) for label in sibLabels}

            # For every Occurence
            for root, occ in zip(rootIds, lOcc):

                rIndx = occ.parent.children.index(occ)

                if rIndx < len(occ.parent.children) - 1:

                    for rSib in occ.parent.children[rIndx + 1 :]:
                        if rSib.label and rSib.label in label_root_dict: 
                            label_root_dict[rSib.label].discard(root)


            for label, roots in label_root_dict.items(): 
                if len(roots) > 0: 
                    sibLabels.remove(label)

            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Bottom:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]
            rootIds = [e[0] for e in tp.rmo[lid]]
            label_root_dict = {label :  set(rootIds) for label in sibLabels}
            
            # For every Occurence
            for root, occ in zip(rootIds, lOcc):

                # Search if we can find the extension in the Children
                for child in occ.children:
                    if child.label and child.label in label_root_dict:
                            label_root_dict[child.label].discard(child.label)
                        
            # Check if they intersect
            for label, roots in label_root_dict.items(): 
                if len(roots) > 0: 
                    sibLabels.remove(label)

            # if No intersection exists, break
            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Between:

        node_children = get_child_labels(node.children[1:-1])
        
        for lid in node.occList:

            lOcc = node.occList[lid]
            lChild = node.children[0].occList[lid]
            rChild = node.children[-1].occList[lid]
            
            rootIds = [e[0] for e in tp.rmo[lid]]
            label_root_dict = {label :  set(rootIds) for label in sibLabels}

            for idx, (root, occ) in enumerate(zip(rootIds, lOcc)):

                lIndx = occ.children.index(lChild[idx])
                rIndx = occ.children.index(rChild[idx])

                betweenSiblings = get_child_labels(occ.children[lIndx + 1 : rIndx])
            
                for child in node_children:
                    betweenSiblings.remove(child)

                for betweenSib in betweenSiblings: 
                    if betweenSib in label_root_dict: 
                        label_root_dict[betweenSib].discard(root)

            
            # Check if they intersect
            for label, roots in label_root_dict.items(): 
                if len(roots) > 0: 
                    sibLabels.remove(label)

            if not sibLabels:
                return False

    else:
        print("This should not happen")

    return True


def check_seq_root_occurence_blanket_match(tp : CMTreePattern, node : CMConcurrencyTree, sibLabels : Set[str], expDir : ExpansionDirection):
    
    if expDir == ExpansionDirection.Left:

        lChild = node.children[0]

        # For every Tree with an Occurence of the Child Node
        for lid in lChild.occList:

            lOcc = lChild.occList[lid]

            rootIds = [e[0] for e in tp.rmo[lid]]
            label_root_dict = {label :  set(rootIds) for label in sibLabels}
            
            # For every Occurence
            for root, occ in zip(rootIds, lOcc):

                # Find the Index of the current Child in the Tree compared to its parent
                cIndx = occ.parent.children.index(occ)

                if cIndx > 0:

                    # Get its left Sibling Labels / Op
                    lSib = occ.parent.children[cIndx - 1]
                    
                    if lSib.label and lSib.label in label_root_dict:
                        label_root_dict[lSib.label].discard(root)


            # Check if they intersect
            for label, roots in label_root_dict.items(): 
                if len(roots) > 0: 
                    sibLabels.remove(label)
                    
            # if No intersection exists, break
            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Right:

        rChild = node.children[-1]
        # For every Tree with an Occurence of the Child Node
        for lid in rChild.occList:

            lOcc = rChild.occList[lid]

            rootIds = [e[0] for e in tp.rmo[lid]]
            label_root_dict = {label :  set(rootIds) for label in sibLabels}
            
            # For every Occurence
            for root, occ in zip(rootIds, lOcc):

                if occ.rSib and occ.rSib.label and occ.rSib.label in label_root_dict:
                    label_root_dict[occ.rSib.label].discard(root)

            # Check if they intersect
            for label, roots in label_root_dict.items(): 
                if len(roots) > 0: 
                    sibLabels.remove(label)
                    
            # if No intersection exists, break
            if not sibLabels:
                return False

    elif expDir == ExpansionDirection.Bottom:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]
            
            rootIds = [e[0] for e in tp.rmo[lid]]
            label_root_dict = {label :  set(rootIds) for label in sibLabels}

            # For every Occurence
            for root, occ in zip(rootIds, lOcc):

                for label in get_child_labels(occ.children): 
                    if label in label_root_dict: 
                        label_root_dict[label].discard(root)

            # Check if they intersect
            for label, roots in label_root_dict.items(): 
                if len(roots) > 0: 
                    sibLabels.remove(label)
    	            
                 
            # if No intersection exists, break
            if not sibLabels:
                return False

    else:
        print("This should not happen")

    return True


def compute_blanket_root_occurence_candidates(tp : CMTreePattern, tree : CMTreePattern, tid : int):

    blanketNotEmpty = False
    
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
                blanketNotEmpty |= check_seq_root_occurence_blanket_match(
                    tp, tree, lSibLabels, expDir=ExpansionDirection.Left
                )

            if rSibLabels:
                
                blanketNotEmpty |= check_seq_root_occurence_blanket_match(
                    tp, tree, rSibLabels, expDir=ExpansionDirection.Right
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

            lBlanketNotEmpty |= check_seq_root_occurence_blanket_match(
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
                blanketNotEmpty |= check_concurrent_root_occurence_blanket_match(
                    tp, tree, lSibLabels, expDir=ExpansionDirection.Left
                )

            if rSibLabels:
                
                blanketNotEmpty |= check_concurrent_root_occurence_blanket_match(
                    tp, tree, rSibLabels, expDir=ExpansionDirection.Right
                )

            if betweenSibLabels:
                blanketNotEmpty |= check_concurrent_root_occurence_blanket_match(
                    tp, tree, betweenSibLabels, expDir=ExpansionDirection.Between
                )

        # The Node doesn't have children
        else:
            pass 
        
            """
            bSibLabels = set()

            # Collect all child labels beneath the occurences
            for occurence in occurences:

                bSibLabels.update(get_child_labels(occurence.children))

            lBlanketNotEmpty |= check_concurrent_root_occurence_blanket_match(
                tree, tid, bSibLabels, expDir=ExpansionDirection.Bottom
            )
            """

    # It is already true
    if not blanketNotEmpty:
        
        for child in tree.children:
            
            if child.op:  
                blanketNotEmpty |= compute_blanket_root_occurence_candidates(
                    tp = tp, tree = child, tid = tid
                )
                
                if blanketNotEmpty: 
                    break


    return blanketNotEmpty
