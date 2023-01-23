
from typing import Set
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree, cTreeOperator

def _foldUnaryLoops(tree : ConcurrencyTree, lmd : int) -> Set[str]  : 
    
    curLabel = ''
    occCount = 0 
    
    foldedLabels = set()
    
    loops = []
    
    
    if tree.op == cTreeOperator.Sequential: 
        
        for index, child in enumerate(tree.children): 
                
                
            if child.op: 
                
                if occCount > lmd: 
                    loops.append((index - 1, occCount))
                    foldedLabels.add(curLabel)
                    
                curLabel = ''
                occCount = 0
            
                foldedLabels = set.union(foldedLabels, _foldUnaryLoops(child, lmd))
            
            else: 
                
                if child.label == curLabel: 
                    
                    occCount += 1
                
                else: 
                    
                    if occCount > lmd: 
                        loops.append((index  - 1, occCount))
                        foldedLabels.add(curLabel)
                        
                    curLabel = child.label     
                    occCount = 1
                    
        lastRidx = -1
        newChildren = []
        
    else: 
        
        for child in tree.children: 
            if child.op: 
                foldedLabels = set.union(foldedLabels, _foldUnaryLoops(child, lmd))
                
    if len(loops) > 0:

        for i, loop in enumerate(loops): 

            lIdx = loop[0] - loop[1] + 1
            rIdx = loop[0]
            
            newChildren.extend(tree.children[lastRidx + 1:lIdx])
            
            
            lNode = tree.children[rIdx] 
            
            lNode.label = lNode.label + '_LOOP'    
            
            if len(newChildren) > 0: 
                
                newChildren[-1].rSib = lNode 
        
            newChildren.append(lNode)
            
            lastRidx = rIdx 
            
            # Last Loop 
            if i == len(loops) - 1:
                if rIdx + 1 < len(tree.children): 
                    newChildren.extend(tree.children[rIdx + 1:])
    
        #print(len(tree.children), tree.children)
        #print()
        #print(len(newChildren), newChildren)
        tree.children = newChildren

    return foldedLabels

def fold_loops(treebank, fold_loops):
    folded_labels = set()

    for entry in treebank.values():
        folded_labels.update(_foldUnaryLoops(entry.tree, fold_loops))