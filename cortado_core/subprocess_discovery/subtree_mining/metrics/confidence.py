from typing import Mapping
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree_pattern import CMTreePattern
from cortado_core.subprocess_discovery.subtree_mining.maximal_connected_components.maximal_connected_check import check_if_valid_tree
from cortado_core.subprocess_discovery.subtree_mining.maximal_connected_components.valid_subpatterns import _compute_left_out_subtree_strings, _compute_subtree_eliminated_children, _get_root_enclosed_subtrees, compute_valid_leaf_eliminated_children
from cortado_core.subprocess_discovery.subtree_mining.tree_pattern import TreePattern


def child_parent_confidence(tp : TreePattern):
    """
    
    """
    # TODO Evaluate if keeping the direct parent reference could be dropped (Shouldn't however waste all to much memory)
    if tp.parent: 
        return tp.support / tp.parent.support
    
    else: 
        return None


def subpattern_confidence(tp : TreePattern, tp_support : Mapping[str, int]):
    """
    
    """
    
    # No inforamtion for pattern of Size 2
    if tp.size == 2 or not check_if_valid_tree(tp.tree): 
        return None
    
    sub_patterns = []
    
    sub_patterns += compute_valid_leaf_eliminated_children(tp.tree)
    sub_patterns += [ x for _, x in _compute_subtree_eliminated_children(tp.tree)]
    sub_patterns += [ x for _, x in _get_root_enclosed_subtrees(tp.tree, isinstance(tp, CMTreePattern))] 
    
    if isinstance(tp, CMTreePattern): 
        sub_patterns +=_compute_left_out_subtree_strings(tp.tree)
        
    support_sub = []
    
    for sub in sub_patterns:
        
        if sub in tp_support:
            support_sub.append(tp_support[sub])
        else:
            print()
            print("Pattern", tp)
            print("Pattern", repr(tp.tree))
            print("Subpattern", sub)
    
    if len(support_sub) > 0:     
        return tp.support / max(support_sub)

    else: 
        return None
    

def cross_support_confidence(tp : TreePattern, tp_support : Mapping[str, int]):
    """
    
    """
    pass


    """
    sub_patterns = compute_all_valid_substrings(tp.tree)
    
    if tp.size == 2: 
        return None
    
    support_sub = []
    
    for sub in sub_patterns: 
        
        if sub in tp_support:
            support_sub.append(tp_support[sub])
        else:
            print()
            print("Pattern", tp)
            print("Pattern", repr(tp.tree))
            print("Subpattern", sub)
    
    return min(support_sub) / max(support_sub)
    
    """
    
