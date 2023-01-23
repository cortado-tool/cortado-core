from typing import Iterable, List, Union
from antlr4 import *
from cortado_core.variant_query_language.grammars.vqlParser import vqlParser
from cortado_core.variant_query_language.query_tree import AllGroup, AnyGroup, BinaryExpressionLeaf, BinaryOperator, LOperator, OperatorNode, QuantifierOperator, QueryTree, UnaryExpressionLeaf, UnaryOperator

def convertParseTreeToQueryTree(context : ParserRuleContext, negated : bool = False) -> QueryTree:
    
    qTree = None
            
    if isinstance(context, vqlParser.CnfClauseContext) or isinstance(context, vqlParser.DnfClauseContext):  
                
        children = []
                
        lOp = LOperator.OR if isinstance(context, vqlParser.DnfClauseContext) else LOperator.AND
                
        for leaf in context.leafs:
            children.append(convertLeafNode(leaf, negated = False))
                
        for leaf in context.negleafs:
            children.append(convertLeafNode(leaf, negated = True))
                    
        for clause in context.clauses:
            children.append(convertParseTreeToQueryTree(clause,  negated = False))
                
        for clause in context.negclauses: 
            children.append(convertParseTreeToQueryTree(clause, negated = True))
            
        for clause in context.negimplyClauses:
                children.append(convertParseTreeToQueryTree(clause,  negated = True))
                
        for clause in context.implyClauses: 
            children.append(convertParseTreeToQueryTree(clause, negated = False))
                
        qTree = OperatorNode(lOp=lOp, children = children, neg = negated)
                
    elif isinstance(context, vqlParser.LeafContext): 
        qTree = convertLeafNode(context, negated=negated)
      
    ## Quick default along the tree to find first query content         
    elif isinstance(context, vqlParser.StartContext):
    
         qTree = convertParseTreeToQueryTree(context.getChild(0))
    
    
    elif isinstance(context, vqlParser.ImplyBlockContext): 
        
        if context.neg: 
            qTree = convertParseTreeToQueryTree(context.getChild(2), negated = True); 
            
        elif len(context.children) == 1: 
            qTree = convertParseTreeToQueryTree(context.getChild(0), negated = False); 
        
        else: 
            qTree = convertParseTreeToQueryTree(context.getChild(1), negated = False); 
            
    elif isinstance(context, vqlParser.LogicBlockContext) or isinstance(context, vqlParser.QueryContext):
        
        if not isinstance(context, vqlParser.QueryContext) and context.neg: 
            qTree = convertParseTreeToQueryTree(context.getChild(2), negated = True); 
            
        else: 
        
            qTree = convertParseTreeToQueryTree(context.getChild(0), negated = False); 
             
    elif isinstance(context, vqlParser.ImpliesClauseContext):
        lOp = LOperator.OR
                
        lChild = convertParseTreeToQueryTree(context.lBlock)  
        lChild.neg = ~lChild.neg
        
        rChild =  convertParseTreeToQueryTree(context.rBlock)  
                
        qTree = OperatorNode(lOp=lOp, children = [lChild, rChild], neg = negated)
          
    else:
        print("Unkown Context found", context)
                
    return qTree
                
    
def convertLeafNode(context : ParserRuleContext, negated : bool = False) -> QueryTree : 
    
    """
    _summary_

    Returns:
        _type_: _description_
    """
    
    if isinstance(context, vqlParser.SimpleExpressionContext):
        
        context = context.exp
        
        if isinstance(context, vqlParser.BinaryExpressionContext):
            
            lAct = convertActivity(context.left)
            rAct = convertActivity(context.right)
            
            return BinaryExpressionLeaf(lActivities = lAct,
                                        rActivities = rAct,
                                        operator = convertOperator(context.op),
                                        negated = negated,
                                    )
            
        elif isinstance(context, vqlParser.UnaryExpressionContext): 

            
            act = convertActivity(context.activity)
            
            return UnaryExpressionLeaf(activities = act,
                                       operator = convertOperator(context.op),
                                       negated = negated,
                                      )

    if isinstance(context,  vqlParser.QuantifiedExpressionContext):
        
        quantifier = context.quant

        
        qOp = convertqOperator(quantifier.op)
        number = int(quantifier.number.text) 
        
        quantifier = context.quant
        
        context = context.exp
        
        if isinstance(context, vqlParser.BinaryExpressionContext):
                
            lAct = convertActivity(context.left)
            rAct = convertActivity(context.right)
            
            return BinaryExpressionLeaf(lActivities = lAct,
                                        rActivities = rAct,
                                        operator = convertOperator(context.op),
                                        negated = negated,
                                        qOp = qOp,
                                        number = number
                                    )
            
        elif isinstance(context, vqlParser.UnaryExpressionContext): 

            
            act = convertActivity(context.activity)
            
            return UnaryExpressionLeaf(activities = act,
                                       operator = convertOperator(context.op),
                                       negated = negated,
                                       qOp = qOp,
                                       number = number
                                      )  
        
def strip_outer(l : Iterable[str]):
    return set([s[1:-1] for s in l])
          
def convertActivity(context : ParserRuleContext) -> List[str]: 
    activities = []

    if isinstance(context, Token): 
        
        activities = AnyGroup(strip_outer([context.text]), inv=False)
        
    elif isinstance(context, vqlParser.AnyGroupContext): 

        activities = strip_outer([a.text for a in context.activityList]) 
        activities = AnyGroup(list(activities), inv=False)
            
    elif isinstance(context, vqlParser.InvertedAnyGroupContext): 
    
        activities = strip_outer([a.text for a in context.activityList]) 
        activities = AnyGroup(activities, inv=True)
        
             
    elif isinstance(context, vqlParser.AllGroupContext): 
         
        activities = strip_outer([a.text for a in context.activityList])       
        activities = AllGroup(activities, inv=False)
             
    elif isinstance(context, vqlParser.InvertedAllGroupContext): 

        activities = strip_outer([a.text for a in context.activityList])      
        activities = AllGroup(activities, inv=True)

    return activities
    
def convertOperator(context : ParserRuleContext) -> Union[BinaryOperator, UnaryOperator]: 
    
    if isinstance(context, vqlParser.CONTAINSOPContext): 
        return UnaryOperator.contains
    
    elif isinstance(context, vqlParser.STARTOPContext): 
        return UnaryOperator.isStart
        
    elif isinstance(context, vqlParser.ENDOPContext): 
        return UnaryOperator.isEnd
        
    elif isinstance(context, vqlParser.DIRECTLYFOLLOWSOPContext): 
        return BinaryOperator.DirectlyFollows
    
    elif isinstance(context, vqlParser.EVENTUALLYFOLLOWSOPContext): 
        return BinaryOperator.EventualyFollows
    
    elif isinstance(context, vqlParser.CONCURRENTOPContext): 
        return BinaryOperator.Concurrent



def convertqOperator(context : ParserRuleContext) -> QuantifierOperator: 

    if isinstance(context, vqlParser.EQUALSOPContext): 
        return QuantifierOperator.Equals
    
    elif isinstance(context, vqlParser.LESSOPContext): 
        return QuantifierOperator.Less
        
    elif isinstance(context, vqlParser.GREATEROPContext): 
        return QuantifierOperator.Greater
    
    