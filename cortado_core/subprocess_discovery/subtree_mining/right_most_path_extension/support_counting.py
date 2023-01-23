
from typing import Mapping
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequencyCountingStrategy
from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import TreePattern
from cortado_core.subprocess_discovery.subtree_mining.treebank import TreeBankEntry
from cortado_core.subprocess_discovery.subtree_mining.utilities import _compute_unique_roots

def check_min_sup(tp : TreePattern, freq_strat : FrequencyCountingStrategy, treebank : Mapping[int, TreeBankEntry], min_sup : int) -> bool:     
    """
    Checks if the support of a tree pattern given a freq_strat is above the given threshold
    """
    
    if freq_strat == FrequencyCountingStrategy.TraceTransaction: 
            
        tp.support = sum([treebank[tid].nTraces for tid in tp.rmo])
        return (tp.support > min_sup)
    
    if freq_strat == FrequencyCountingStrategy.TraceOccurence: 
        tp.support = sum([treebank[tid].nTraces * _compute_unique_roots(tp.rmo[tid]) for tid in tp.rmo])
        return tp.support > min_sup
    
    if freq_strat == FrequencyCountingStrategy.VariantTransaction: 
        
        tp.support = len(tp.rmo)
        return  (tp.support > min_sup)
        
    if freq_strat == FrequencyCountingStrategy.VariantOccurence:
        
        tp.support = sum([_compute_unique_roots(tp.rmo[tid]) for tid in tp.rmo])
        return (tp.support > min_sup)
    



