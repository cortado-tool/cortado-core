from enum import Enum

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree_pattern import (
    CMTreePattern,
)
from cortado_core.subprocess_discovery.subtree_mining.utilities import get_child_labels


class ExpansionDirection(Enum):
    """
    Expension Direction in the CM Algo
    """

    Left = "Left"
    Right = "Right"
    Top = "Top"
    Bottom = "Bottom"
    Between = "Between"

def check_occ_blanket(tp: CMTreePattern):

    # Creat an Iterator over the Occurence Lists
    occLists = iter(tp.tree.occList)

    # For the First Entry, compute the Candidate Expansions
    tid = next(occLists)

    # Compute the candidates starting at the root and from a single occurence
    (
        Left_occurence_blanket_not_empty,
        occurence_blanket_not_empty,
    ) = compute_blanket_occurence_candidates(tp, tp.tree, tid, outer=True)

    return Left_occurence_blanket_not_empty, occurence_blanket_not_empty

def check_concurrent_occurence_blanket_match(node, sibLabels, expDir):

    if expDir == ExpansionDirection.Left:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]

            # For every Occurence
            for occ in lOcc:

                # Find the Index of the current Child in the Tree compared to its parent
                lIndx = occ.parent.children.index(occ)

                if lIndx > 0:

                    lLabels = set(get_child_labels(occ.parent.children[:lIndx]))
                    sibLabels = sibLabels.intersection(lLabels)

                    if not sibLabels:
                        return False

                # Child has no left Siblings => Break
                else:
                    return False

    elif expDir == ExpansionDirection.Right:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]

            # For every Occurence
            for occ in lOcc:

                # Find the Index of the current Child in the Tree compared to its parent
                rIndx = occ.parent.children.index(occ)

                if rIndx < len(occ.parent.children) - 1:

                    rLabels = set(get_child_labels(occ.parent.children[rIndx + 1 :]))
                    sibLabels = sibLabels.intersection(rLabels)

                    if not sibLabels:
                        return False

                # Child has no right Siblings => Break
                else:
                    return False

    elif expDir == ExpansionDirection.Bottom:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]

            # For every Occurence
            for occ in lOcc:

                cLabels = set(get_child_labels(occ.children))
                sibLabels = sibLabels.intersection(cLabels)

                if not sibLabels:
                    return False

    elif expDir == ExpansionDirection.Between:

        for lid in node.occList:

            lOcc = node.occList[lid]
            lChild = node.children[0].occList[lid]
            rChild = node.children[-1].occList[lid]

            for idx, occ in enumerate(lOcc):

                lIndx = occ.children.index(lChild[idx])
                rIndx = occ.children.index(rChild[idx])

                betweenSiblings = get_child_labels(occ.children[lIndx + 1 : rIndx])
                

                for child in get_child_labels(node.children[1:-1]):
                    betweenSiblings.remove(child)

                sibLabels = sibLabels.intersection(betweenSiblings)

                if not sibLabels:
                    return False

    else:
        print("This should not happen")

    return True


def check_seq_occurence_blanket_match(node, sibLabels, expDir):

    if expDir == ExpansionDirection.Left:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]

            # For every Occurence
            for occ in lOcc:

                # Find the Index of the current Child in the Tree compared to its parent
                cIndx = occ.parent.children.index(occ)

                if cIndx > 0:

                    # Get its left Sibling
                    lSib = occ.parent.children[cIndx - 1]
                    if lSib.label:
                        sibLabels = sibLabels.intersection(set([lSib.label]))
                    
                        # If the sibling set is empty
                        if not sibLabels:
                            return False
                        
                    else: 
                        return False 


                # Child has no left Sibling
                else:
                    return False

    elif expDir == ExpansionDirection.Right:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]

            # For every Occurence
            for occ in lOcc:

                if occ.rSib: 
                    
                    
                    if occ.rSib.label:
                        sibLabels = sibLabels.intersection(
                            set([occ.rSib.label])
                        )
                    else: 
                        
                        return False

                    if not sibLabels:

                        return False
                else:
                    return False

    elif expDir == ExpansionDirection.Bottom:

        # For every Tree with an Occurence of the Child Node
        for lid in node.occList:

            lOcc = node.occList[lid]

            # For every Occurence
            for occ in lOcc:

                cLabels = set(get_child_labels(occ.children))
                sibLabels = sibLabels.intersection(cLabels)

                if not sibLabels:
                    return False

    else:
        print("This should not happen")

    return True


def compute_blanket_occurence_candidates(tp, tree, tid, outer=False):

    # Blankets are empty
    BlanketNotEmpty = False
    leftBlanketNotEmpty = False

    occurence = tree.occList[tid][0]


    """
    if tree.op == cTreeOperator.Sequential:

        # The Node has Left and Right Children
        if len(tree.children) > 0:
            lChild = tree.children[0]
            lidx = occurence.children.index(lChild.occList[tid][0])

            if lidx > 0:

                lSib = occurence.children[lidx - 1]
                
                if lSib.label: 
                    sibSet = set([lSib.label])
                    leftBlanketNotEmpty |= check_seq_occurence_blanket_match(
                        lChild, sibSet, expDir=ExpansionDirection.Left
                    )

            rChild = tree.children[-1]
            
            try: 
                ridx = occurence.children.index(rChild.occList[tid][0])

            except: 
                print(rChild)
                print(rChild.occList)
            
            if ridx < len(occurence.children) - 1:

                rSib = occurence.children[ridx + 1]
                
                if rSib.label: 
                    sibSet = set([rSib.label])
                    res = check_seq_occurence_blanket_match(
                        rChild, sibSet, expDir=ExpansionDirection.Right
                    )
    
                    if outer:
                        if res:
                            tp.rightBlanket = tree
                            BlanketNotEmpty |= res

                    else:
                        leftBlanketNotEmpty |= res

        # The Node doesn't have children
        # This is only the case if we are on the right most path, as those patterns would else not be valid
        elif outer:
            pass 
            sibSet = set([child.label for child in occurence.children if child.label])
            if res := check_seq_occurence_blanket_match(
                tree, sibSet, expDir=ExpansionDirection.Bottom
            ):
                tp.rightBlanket = tree
                BlanketNotEmpty |= res
    """

    if tree.op == cTreeOperator.Concurrent or tree.op == cTreeOperator.Fallthrough:

        # The Node has Left and Right Children
        if len(tree.children) > 0:
            lChild = tree.children[0]
            lidx = occurence.children.index(lChild.occList[tid][0])

            if lidx > 0:

                lSiblings = occurence.children[:lidx]
                sibSet = set(get_child_labels(lSiblings))

                leftBlanketNotEmpty |= check_concurrent_occurence_blanket_match(
                    lChild, sibSet, expDir=ExpansionDirection.Left
                )

            rChild = tree.children[-1]
            ridx = occurence.children.index(rChild.occList[tid][0])

            if ridx < len(occurence.children) - 1:

                rSiblings = occurence.children[ridx + 1 :]
                sibSet = set(get_child_labels(rSiblings))
                
                res = check_concurrent_occurence_blanket_match(
                    rChild, sibSet, expDir=ExpansionDirection.Right
                )

                if outer:
                    if res:
                        tp.rightBlanket = tree
                        BlanketNotEmpty |= res

                    else:
                        leftBlanketNotEmpty |= res

            if lidx != ridx:
                # Collect all children between the lidx and ridx
                betweenSiblings = get_child_labels(occurence.children[lidx + 1 : ridx])

                # Remove the nodes matched by the pattern
                try:
                    for child in get_child_labels(tree.children[1:-1]):
                        betweenSiblings.remove(child)

                except:
                    print()
                    print("Tree", tree)
                    print("Children", tree.children)
                    print("Inbetween Children", tree.children[1:-1])
                    print("Between Siblings Current", betweenSiblings)
                    print(
                        "Between Sibling Original",
                        get_child_labels(occurence.children[lidx + 1 : ridx]) 
                    )
                    print("Occurence", occurence)
                    print()

                    print()
                    test = occurence.children[lidx + 1 : ridx]
                    for child in tree.children[1:-1]:
                        print()
                        print("Cur Test", test)
                        print("Cur Child", child)
                        test.remove(child)
                        print("Remove Success")
                    raise

                sibSet = set(betweenSiblings)

                if sibSet:
                    leftBlanketNotEmpty |= check_concurrent_occurence_blanket_match(
                        tree, sibSet, expDir=ExpansionDirection.Between
                    )

        # The Node doesn't have children
        # This is only the case if we are on the right most path, as those patterns would else not be valid already and thus pruned
        elif outer:
            pass 
        
            """
            sibSet = set( get_child_labels(occurence.children))
            if res := check_concurrent_occurence_blanket_match(
                tree, sibSet, expDir=ExpansionDirection.Bottom
            ):
                tp.rightBlanket = tree
                BlanketNotEmpty |= res
            """

    # Break Early as we can prune
    if not leftBlanketNotEmpty:

        for child in tree.children:
            
            if child.op:  
                lBlanket, blanket = compute_blanket_occurence_candidates(
                    tp, child, tid, outer=(outer and child.rSib == None)
                )
                leftBlanketNotEmpty |= lBlanket
                BlanketNotEmpty |= blanket
                
                if leftBlanketNotEmpty: 
                    break

    BlanketNotEmpty |= leftBlanketNotEmpty

    return leftBlanketNotEmpty, BlanketNotEmpty