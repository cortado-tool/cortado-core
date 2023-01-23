from collections import defaultdict
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequentActivitySets, PruningSets, PruningSets_2Patterns
from cortado_core.subprocess_discovery.subtree_mining.utilities import _getLabel


def _get_prune_sets(fSets: FrequentActivitySets, F) -> PruningSets:
    
    # Define the initial Prune Sets
    ftNestPrune, dfNestPrune, ccNestPrune = compute_f2_pruned_set_2_patterns(F)

    ccLabelPrune = fSets.ccR
    ccFollowsPrune = fSets.ccR

    dfLabelPrune = fSets.dfR
    dfFollowsPrune = fSets.dfR

    efFollowsPrune = fSets.efR

    ftLabelPrune = {a: ftNestPrune for a in ftNestPrune}
    operatorPrune = {
        a: set(
            [
                cTreeOperator.Sequential,
                cTreeOperator.Concurrent,
                cTreeOperator.Fallthrough,
            ]
        )
        for a in fSets.fA 
    }
    
    operatorActivityPrune = {}
    operatorActivityPrune[cTreeOperator.Sequential] = fSets.fA # Use fA as dfNest does not take into account leafs only following
    operatorActivityPrune[cTreeOperator.Fallthrough] = fSets.fA
    operatorActivityPrune[cTreeOperator.Concurrent] = fSets.fA

    operatorOperatorPrune = {}
    operatorOperatorPrune[cTreeOperator.Sequential] = set([cTreeOperator.Fallthrough])
    operatorOperatorPrune[cTreeOperator.Fallthrough] = set([cTreeOperator.Sequential, cTreeOperator.Concurrent, cTreeOperator.Fallthrough])
    operatorOperatorPrune[cTreeOperator.Concurrent] = set([cTreeOperator.Concurrent, cTreeOperator.Fallthrough])
    
    
    return PruningSets_2Patterns(
        ftNestPrune=ftNestPrune,
        dfNestPrune=dfNestPrune,
        ccNestPrune=ccNestPrune,
        ccLabelPrune=ccLabelPrune,
        ccFollowsPrune=ccFollowsPrune,
        dfLabelPrune=dfLabelPrune,
        dfFollowsPrune=dfFollowsPrune,
        efFollowsPrune=efFollowsPrune,
        ftLabelPrune=ftLabelPrune,
        operatorPrune=operatorPrune,
        operatorOperatorPrune=operatorOperatorPrune,
        operatorActivityPrune = operatorActivityPrune,
    )



def compute_f2_pruned_set_2_patterns(F):
    
    fA = set()
    fDF = set()
    fCC = set()  
    
    for f in F: 
        child = f.tree.children[0]
        
        if f.tree.op == cTreeOperator.Sequential:
            if child.label:
                fDF.add(child.label)
    
        elif f.tree.op == cTreeOperator.Concurrent:
            if child.label:
                fCC.add(child.label)
                
        elif f.tree.op == cTreeOperator.Fallthrough:
            if child.label:
                fA.add(child.label)
                
    return fA, fDF, fCC

def compute_f3_pruned_set_2_patterns(pSets : PruningSets_2Patterns, F):
    
    # TODO Delete the invalid f3 patterns 
    
    fA = defaultdict(set)
    fDF = defaultdict(set)
    fCC = defaultdict(set)
    fOP = defaultdict(set)
    fOPOP = defaultdict(set)
    fOPACT = defaultdict(set)
    
    valid_F = set()
    
    defaultdict()
    
    for f in F:
        if len(f.tree.children) > 1: 
            
            lChild = f.tree.children[0]
            rChild = f.tree.children[1]
            
            if f.tree.op == cTreeOperator.Sequential:
                if lChild.label:
                    
                    if rChild.label:
                        fDF[lChild.label].add(rChild.label)
                    else: 
                        fOP[lChild.label].add(rChild.op)
                    
                    valid_F.add(f)

            elif f.tree.op == cTreeOperator.Concurrent:
                if lChild.label:
                    
                    if rChild.label:
                        fCC[lChild.label].add(rChild.label)
                    else: 
                        fOP[lChild.label].add(rChild.op)
                        
                    valid_F.add(f)
                
            elif f.tree.op == cTreeOperator.Fallthrough:
                if lChild.label:
                    
                    if rChild.label:
                        fA[lChild.label].add(rChild.label)
                    else: 
                        fOP[lChild.label].add(rChild.op)
                        
                    valid_F.add(f)
                 
            if lChild.op and rChild.op: 
                fOPOP[lChild.op].add(rChild.op)
                
            if lChild.op and rChild.label: 
                fOPACT[lChild.op].add(rChild.label)
                
        else: 
            valid_F.add(f)
                
    pSets.ftLabelPrune = fA
    pSets.dfLabelPrune = fDF
    pSets.ccLabelPrune = fCC
    pSets.operatorPrune = fOP
    pSets.operatorActivityPrune = fOPACT
    pSets.operatorOperatorPrune = fOPOP

    return pSets, valid_F


def compute_f3_pruned_set(fSets : FrequentActivitySets, F):
    
    # TODO Delete the invalid f3 patterns 
    
    valid_F = set()
    nestPrune = defaultdict(set)
    sibPrune = defaultdict(set)
    
    for f in F:
        
        if len(f.tree.children) > 1: 
            
            lChild = f.tree.children[0]
            rChild = f.tree.children[1]
            
            sibPrune[(f.tree.op, _getLabel(lChild))].add(_getLabel(rChild))
            
            if lChild.label: 
                valid_F.add(f)
        else: 
            
            valid_F.add(f)
            
            gp = f.tree 
            p = gp.children[0]
            c = p.children[0]
            
            nestPrune[(gp.op, p.op)].add(_getLabel(c)) 
    
    pSets = PruningSets(fSets.dfR, fSets.efR, sibPrune, nestPrune)

    return pSets, valid_F