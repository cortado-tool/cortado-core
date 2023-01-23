
from typing import List, Mapping, Tuple
import operator
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree, cTreeOperator
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequencyCountingStrategy

def flatten(t):
    """
    Creates a flat list from a nested iterable data structure in python 
    Based on a Python Idiom
    """
    
    return [item for sublist in t for item in sublist]

def _get_label_or_op(tree : ConcurrencyTree): 
    
    if tree.label:
        return tree.label
    else: 
        return str(tree.op)
    
def get_child_labels(children): 
    return [child.label for child in children if child.label]
    
def _compute_unique_roots(rmo_entries : Tuple[int, ConcurrencyTree]) -> int:
    return len(set(map(operator.itemgetter(0), rmo_entries)))

def _getLabel(child : ConcurrencyTree): 
    return child.label or child.op 

def _isTransactionSetting(strategy : FrequencyCountingStrategy):
    return strategy == FrequencyCountingStrategy.VariantTransaction or strategy == FrequencyCountingStrategy.TraceTransaction

def _contains_fallthrough(tree): 
    
    if tree.op: 
        
        if tree.op == cTreeOperator.Fallthrough: 
            
            return True
    
        else: 
            
            return any([ _contains_fallthrough(child) for child in tree.children])
        
    else: 
        return False


def compute_occurence_list_size(occ_list : Mapping[int, List[Tuple[int, ConcurrencyTree]]]): 
    return sum([len(occ) for occ in occ_list.values()])
    

def _update_subToGain(treeBank, freq_strat, supToGain, oc, occ):
    if freq_strat == FrequencyCountingStrategy.TraceTransaction:
        supToGain -= treeBank[oc].nTraces

    if freq_strat == FrequencyCountingStrategy.VariantTransaction:
        supToGain -= 1
        
    if freq_strat == FrequencyCountingStrategy.TraceOccurence:
        supToGain -= (treeBank[oc].nTraces * _compute_unique_roots(occ))

    if freq_strat == FrequencyCountingStrategy.VariantOccurence:
        supToGain -= _compute_unique_roots(occ)
        
    return supToGain

def _update_current_sup(treeBank, freq_strat, cur_sup, oc, occ):
    
    if freq_strat == FrequencyCountingStrategy.TraceTransaction:
        cur_sup += treeBank[oc].nTraces

    if freq_strat == FrequencyCountingStrategy.VariantTransaction:
        cur_sup += 1 

    if freq_strat == FrequencyCountingStrategy.TraceOccurence:
        cur_sup += treeBank[oc].nTraces * occ

    if freq_strat == FrequencyCountingStrategy.VariantOccurence:
        cur_sup += (occ)
    return cur_sup