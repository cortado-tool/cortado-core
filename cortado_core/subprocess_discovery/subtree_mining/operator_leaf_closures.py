from typing import Iterable
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree, cTreeOperator

def _computeSeqOperatorClosure(
    node: ConcurrencyTree, dfR, efR, rmc=False
) -> Iterable[str]:

    first_child = node.children[0]

    if rmc and node.op == cTreeOperator.Concurrent:
        labels = set(dfR.get(first_child.label, []))

    else:
        if first_child.label: 
            labels = set(efR.get(first_child.label, []))
        else: 
            labels = _computeSeqOperatorClosure(first_child, dfR, efR, False)

    for child in node.children[1:-1]:
        
        if node.op == cTreeOperator.Concurrent:
            
            if child.label:
    
                if rmc:
                    labels = labels.intersection(dfR.get(child.label, []))

                else:
                    labels = labels.intersection(efR.get(child.label, []))

            else:
                labels = labels.intersection(_computeSeqOperatorClosure(child, dfR, efR, rmc)) # RMC remains preserved for 

            if not labels:
                break
            
        else: 
            
            if child.label:
                labels = labels.intersection(efR.get(child.label, []))

            else:
                labels = labels.intersection(_computeSeqOperatorClosure(child, dfR, efR, False))

            if not labels:
                break
    
    # Recursion along the right-most path
    if node.children[-1].label:
        if rmc and node.op != cTreeOperator.Fallthrough:
            labels = labels.intersection(dfR.get(node.children[-1].label, []))

        else:
            labels = labels.intersection(efR.get(node.children[-1].label, []))

    else:
        labels = labels.intersection(_computeSeqOperatorClosure(node.children[-1], dfR, efR, rmc))

    return labels