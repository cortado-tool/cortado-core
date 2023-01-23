from typing import Mapping

from pandas import DataFrame
from cortado_core.subprocess_discovery.subtree_mining.metrics.confidence import child_parent_confidence, cross_support_confidence, subpattern_confidence
from cortado_core.subprocess_discovery.subtree_mining.maximal_connected_components.maximal_connected_check import check_if_valid_tree
from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import TreePattern


def dataframe_from_k_patterns(k_pattern : Mapping[int, TreePattern]) -> DataFrame: 

    entries = []

    for k in k_pattern:
            
        for tp in k_pattern[k]:
            
            if check_if_valid_tree(tp.tree):
                entries.append({"k" : k,
                                "obj" : tp,
                                "sup" : tp.support,
                                "child_parent_confidence" : None, 
                                "subpattern_confidence" : None, 
                                "cross_support_confidence" : None, 
                                "valid" : True,
                                "maximal" : tp.maximal,
                                "closed" : tp.closed
                                })
                      
    df = DataFrame.from_dict(entries)
     
    return df     


def add_confidence_information_to_df(k_pattern, df): 
    
    tp_sup_dict = {}

    for k in k_pattern:
        for tp in k_pattern[k]:
            tp_sup_dict[repr(tp.tree)] = tp.support
    
    df['child_parent_confidence'] =  df.obj.apply(lambda x : child_parent_confidence(x))
    df['subpattern_confidence'] =  df.obj.apply(lambda x : subpattern_confidence(x, tp_sup_dict))
    df['cross_support_confidence'] = df.obj.apply(lambda x : cross_support_confidence(x, tp_sup_dict))

    df = df.round({
        "child_parent_confidence" : 2,
        "subpattern_confidence" : 2,
        "cross_support_confidence" : 2, 
    })  
    
    return df