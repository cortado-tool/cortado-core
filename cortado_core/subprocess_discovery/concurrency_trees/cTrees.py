
from enum import Enum
from itertools import zip_longest
from typing import List
from cortado_core.utils.cgroups_graph import ConcurrencyGroup
from cortado_core.utils.constants import ARTIFICAL_END_NAME, ARTIFICAL_START_NAME, BARROW
from cortado_core.utils.split_graph import LeafGroup, ParallelGroup, SequenceGroup, LoopGroup


class cTreeOperator(Enum):
    """
    Operators used in cTrees
    """
    Sequential = '\u2192'
    Concurrent = '\u2227'
    Fallthrough = '\u2715'
    Loop = '*'

class ConcurrencyTree():
    
    def __repr__(self) -> str:
        """
        Computes a DFS Encoding of the Tree
        """
        if self.label:
            return self.label
        else: 
            
            cString = ''
            
            if self.children:
                cString = "".join([(repr(child) + BARROW) for child in self.children])
            
            return self.op.value + cString


    def __str__(self) -> str:
        """
        Computes a BFS Encoding of the Tree
        """
        
        if self.label:
            return self.label
        else: 
            
            if self.children:
                cString = ", ".join([str(child) for child in self.children])
            else: 
                cString = " "
            
            return self.op.value + "(" + cString + ")"
        
    def __init__(self, children = None, rSib  = None, parent = None, label : str = None, op : cTreeOperator = None):
        self.label : str = label
        self.op : cTreeOperator = op            
        self.rSib : ConcurrencyTree = rSib
        self.parent : ConcurrencyTree = parent
        self.id : int = None
        
        if not children: 
            children = []
            
        self.children : List[ConcurrencyTree]= children
        
        if len(children) > 0:
            self.rmc : ConcurrencyTree = children[-1]
        else: 
            self.rmc : ConcurrencyTree = None
            
    def copy(self, child): 
        """
        Creates a copy of a concurrency tree, if a child paramenter is passed, returns the copy of that child in the new tree. 
        
        Args:
            child ([type]): [description]

        Returns:
            [type]: [description]
        """
        cChildren = []
        
        cChild = None
        
        for c in self.children: 
            cT, cc = c.copy(child)
            cChildren.append(cT)
                
            if cc is not None: 
                cChild = cc
                
        
        copy = ConcurrencyTree(cChildren, None, None, self.label, self.op)
        copy.id = self.id
        
        for c, rSib in zip_longest(cChildren, cChildren[1:], fillvalue=None): 
            c.rSib = rSib
            c.parent = copy
        
        if self == child: 
            cChild = copy
        
        return copy, cChild
        
        
    def to_concurrency_group(self):
        """

        """

        if self.label: 
            return LeafGroup([self.label])
            
        elif self.op == cTreeOperator.Sequential: 
            return SequenceGroup([child.to_concurrency_group() for child in self.children])
        
        elif self.op == cTreeOperator.Concurrent: 
            return ParallelGroup([child.to_concurrency_group() for child in self.children])
        
        elif self.op == cTreeOperator.Fallthrough: 
            return LeafGroup([child.label for child in self.children])

        elif self.op == cTreeOperator.Loop:
            return LoopGroup([child.label for child in self.children])
            
    def add_artifical_start_end(self): 
        """
        
        """ 
        
        if self.op == cTreeOperator.Concurrent or self.label: 
        
            artificialStart = ConcurrencyTree(None, self, None, ARTIFICAL_START_NAME, None)
            artificialEnd = ConcurrencyTree(None, None, None, ARTIFICAL_END_NAME, None)
            
            artificialRoot = ConcurrencyTree([artificialStart, self, artificialEnd], None, None, None, cTreeOperator.Sequential)

            self.parent = artificialRoot
            self.rSib = artificialEnd
            artificialStart.parent = artificialRoot
            artificialEnd.parent = artificialRoot
            
            return artificialRoot 
        
        else: 
            
            artificialStart = ConcurrencyTree(None, self.children[0], self, ARTIFICAL_START_NAME, None)
            artificialEnd = ConcurrencyTree(None, None, self, ARTIFICAL_END_NAME, None)
            
            self.children[-1].rSib = artificialEnd
            self.rmc = artificialEnd
            self.children = [artificialStart] + self.children + [artificialEnd]
            
            return self
    
    def assign_dfs_ids(self): 
        
        def __dfs_traversal(tree, offset): 
            
            tree.id = offset
            
            offset += 1 
            
            if tree.children: 
                for child in tree.children:         
                    offset = __dfs_traversal(child, offset)
                    
            return offset 
                    
        __dfs_traversal(self, 0) 
        

def cTreeFromcGroup(group : ConcurrencyGroup, parent : ConcurrencyTree = None):
    """
    Transforms a (sorted) Concurrency Group into a ConcurrencyTree recursivly
    """    

    cTree = ConcurrencyTree(children = None, parent = parent, rSib = None, label = None, op = None)
    hasChildren = False
    
    if isinstance(group, SequenceGroup):
        cTree.op = cTreeOperator.Sequential
        cTree.label = None
        hasChildren = True
        
        
    elif isinstance(group, ParallelGroup): 
        cTree.op = cTreeOperator.Concurrent
        cTree.label = None
        hasChildren = True

    elif isinstance(group, LoopGroup):
        cTree.op = cTreeOperator.Loop
        cTree.label = None
        hasChildren = True
        
    else: 
        
        activites = sorted([activity for activity in group])
        
        if len(activites) == 1: 
            cTree.op = None 
            cTree.label = activites[0]
        
        else: 
            cTree.op = cTreeOperator.Fallthrough
            cTree.label = None 
             
            children = []
            
            for activity in activites: 

                children.append(ConcurrencyTree(children = None, parent = cTree, rSib = None, label = activity, op = None))
            
            cTree.children = children 
                 
                
    if hasChildren:
        
        if isinstance(group, ParallelGroup): 
            cTree.children = []
            opChild = None 
            
            for child in group: 
                subTree = cTreeFromcGroup(child, cTree)
                
                if subTree.op: 
                    opChild = subTree
                
                else: 
                    cTree.children.append(subTree)     
            
            if opChild: 
                 cTree.children.append(opChild)     
            
        else:
            cTree.children = [cTreeFromcGroup(child, cTree) for child in group]    
        
    for child, rSib in zip_longest(cTree.children, cTree.children[1:], fillvalue=None):
        child.rSib = rSib
        
        
    return cTree



