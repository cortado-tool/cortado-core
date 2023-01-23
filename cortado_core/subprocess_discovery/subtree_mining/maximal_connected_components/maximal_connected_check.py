from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_tree_pattern import CMTreePattern
from cortado_core.subprocess_discovery.subtree_mining.maximal_connected_components.valid_subpatterns import (
_compute_subtree_eliminated_children,
_get_root_enclosed_subtrees,
compute_valid_leaf_eliminated_children,
_compute_left_most_path_eliminated_leafs,
_compute_left_most_path_eliminated_subtree, 
_compute_right_most_path_eliminated_leafs,
_compute_right_most_path_eliminated_subtree
)

def check_if_valid_tree(tree : ConcurrencyTree) -> bool:
    
    # Just a leaf label node is valid
    if tree.label: 
        return True 
    
    else: 
        
        if len(tree.children) >= 2: 
            
            for child in tree.children:
                if not check_if_valid_tree(child):
                    return False
            
            # Returns True if all children are valid
            return True
        
        else: 
            return False
                
def check_maximality_closed_patterns(tp, k, level_to_go): 
        """

        """
        
        
        eSubtrees = []
        tSubtrees = [] 
         
        if isinstance(tp, CMTreePattern):
            
            eSubtrees += [(k-1, sub) for sub in _compute_left_most_path_eliminated_leafs(tp.tree)]
            eSubtrees += [(k-1, sub) for sub in _compute_right_most_path_eliminated_leafs(tp.tree)]
            
        else: 
            
            eSubtrees += [(k-1, sub) for sub in compute_valid_leaf_eliminated_children(tp.tree)]
            eSubtrees += [(k-1, sub) for sub in _compute_left_most_path_eliminated_leafs(tp.tree)]
            eSubtrees += [(k-1, sub) for sub in _compute_right_most_path_eliminated_leafs(tp.tree)]
            
           
       
        tSubtrees += _compute_subtree_eliminated_children(tp.tree)
        tSubtrees += _get_root_enclosed_subtrees(tp.tree, isinstance(tp, CMTreePattern))
        tSubtrees += _compute_left_most_path_eliminated_subtree(tp.tree)  
        tSubtrees += _compute_right_most_path_eliminated_subtree(tp.tree)
    
        for level, sub in eSubtrees:
            try: 
                ancestor = level_to_go[level][sub]
                ancestor.maximal = False

                if tp.support >= ancestor.support:
                    ancestor.closed = False
            except: 
                print()
                print('Error in Leaf Elemination Case')
                print(tp)
                print(level, sub)
                for s in level_to_go[level]: 
                    print(s)
   
        for level, sub in tSubtrees:
            
            try: 
                ancestor = level_to_go[level][sub]
                ancestor.maximal = False

                if tp.support >= ancestor.support:
                    ancestor.closed = False
                    
            except: 
                print()
                print('Error in Subtree Elemination Case')
                print(tp)
                print(level, sub)
                for s in level_to_go[level]: 
                    print(s)

def set_maximaly_closed_patterns(k_pattern):
    """
    Interate over the set of frequent patterns in reverse order, checking relationship between k and k-1 patterns, if 
    one of the k patterns is a superset of a k-1 pattern check if maximality and closedness are violated and set it accordingly in the pattern
    """

    k_pattern_strings = dict() 

    for k in k_pattern: 
        string_gm_dict = dict() 

        for tp in k_pattern[k]: 
            if check_if_valid_tree(tp.tree):
                string_gm_dict[repr(tp.tree)] = tp

        k_pattern_strings[k] = string_gm_dict
        
    ks = list(k_pattern)
    ks.reverse()
    
    for k in ks: 
        
        if k > 2:
            for tp in k_pattern[k]: 
                
                if check_if_valid_tree(tp.tree):
                    check_maximality_closed_patterns(tp, k, k_pattern_strings)
                
        else:
            break