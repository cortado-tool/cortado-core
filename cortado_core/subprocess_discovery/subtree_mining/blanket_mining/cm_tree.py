from itertools import zip_longest
from typing import Tuple
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree, cTreeOperator


class CMConcurrencyTree(ConcurrencyTree): 
    
    def __init__(self, children = None, rSib  = None, parent = None, label : str = None, op : cTreeOperator = None, occList = {}):
        super().__init__(children, rSib, parent, label, op)
        self.occList = occList
        
    def add_occ_list(self, occ : Tuple):
        """
        
        """

        if occ[0] in self.occList:                   
            self.occList[occ[0]].append(occ[1])
        else: 
            self.occList[occ[0]] = [occ[1]]
            
            
    def copy(self, child): 
        
        cChildren = []
        cChild = None
        
        for c in self.children: 
            cT, cc = c.copy(child)
            cChildren.append(cT)
                
            if cc is not None: 
                cChild = cc
        
        copy = CMConcurrencyTree(cChildren, None, None, self.label, self.op, self.occList)
        
        for c, rSib in zip_longest(cChildren, cChildren[1:], fillvalue=None): 
            c.rSib = rSib
            c.parent = copy
        
        if self == child: 
            cChild = copy
        
        return copy, cChild
    
    def clean_occurence_list(self): 
        del self.occList
        
        for child in self.children: 
            child.clean_occurence_list()
        