from functools import partial
from typing import Set
from cortado_core.utils.split_graph import Group
from cortado_core.variant_query_language.query_tree import (
    AllGroup,
    BinaryExpressionLeaf,
    BinaryOperator,
    ExpressionLeaf,
    LOperator,
    OperatorNode,
    QuantifierOperator,
    QueryTree,
    UnaryExpressionLeaf,
    UnaryOperator,
)

from cortado_core.utils.cgroups_graph import ConcurrencyGroup



def check_query_tree(
    qT: QueryTree, graph: ConcurrencyGroup, activities: Set[str], root=False
) -> bool:
    def evaluate_expression_leaf(
        qT: ExpressionLeaf, graph: ConcurrencyGroup, activities: Set[str]
    ) -> bool:

        eVal = None

        if isinstance(qT, UnaryExpressionLeaf):
            eVal = evaluate_unary_leaf(qT, graph, activities)

        elif isinstance(qT, BinaryExpressionLeaf):
            eVal = evaluate_binary_leaf(qT, graph, activities)

        return eVal

    cVal: bool

    # Evaluate Inner Nodes
    if isinstance(qT, OperatorNode):

        cVal = False

        # AND Node, if any one is false, return False
        if qT.lOp == LOperator.AND:

            cVal = True

            for child in qT.children:

                if not check_query_tree(child, graph, activities):
                    cVal = False
                    break

        # OR Node, if any one is true, return True
        elif qT.lOp == LOperator.OR:

            cVal = False

            for child in qT.children:

                if check_query_tree(child, graph, activities):
                    cVal = True
                    break

    # Evaluate Expression Leaf
    elif isinstance(qT, ExpressionLeaf):

        cVal = evaluate_expression_leaf(qT, graph, activities)

    # Invert the result
    if qT.neg:
        cVal = not cVal

    return cVal


def evaluate_unary_leaf(
    qT: UnaryExpressionLeaf,
    graph: ConcurrencyGroup,
    activities: Set[str],
) -> bool:

    cActivities = qT.activities.getMembers(activities)

    any_activity = not isinstance(qT.activities, AllGroup)
    eVal: bool

    if qT.operator == UnaryOperator.contains:
        eVal = check_unary_groups(
            graph.events,
            cActivities,
            any_activity,
            quantifier=qT.qOp,
            occ=qT.number,
        )

    elif qT.operator == UnaryOperator.isStart:
        eVal = check_unary_groups(
            graph.start_activities,
            cActivities,
            any_activity,
            quantifier=qT.qOp,
            occ=qT.number,
        )

    elif qT.operator == UnaryOperator.isEnd:
        eVal = check_unary_groups(
            graph.end_activities,
            cActivities,
            any_activity,
            quantifier=qT.qOp,
            occ=qT.number,
        )

    return eVal


def evaluate_binary_leaf(
    qT: BinaryExpressionLeaf, graph: ConcurrencyGroup, activities: Set[str]
) -> bool:

    lactivities = qT.lactivities.getMembers(activities)
    ractivities = qT.ractivities.getMembers(activities)

    any = not (
        isinstance(qT.lactivities, AllGroup) or isinstance(qT.ractivities, AllGroup)
    )

    eVal: bool

    if qT.operator == BinaryOperator.DirectlyFollows:

        eVal = check_binary_expressions(
            graph.directly_follows,
            graph.events,
            lactivities,
            ractivities,
            any_activity=any,
            quantifier=qT.qOp,
            occ=qT.number,
        )

    elif qT.operator == BinaryOperator.EventualyFollows:

        eVal = check_binary_expressions(
            graph.follows,
            graph.events,
            lactivities,
            ractivities,
            any_activity=any,
            quantifier=qT.qOp,
            occ=qT.number,
        )

    elif qT.operator == BinaryOperator.Concurrent:

        eVal = check_concurrent(
            graph.concurrency_pairs,
            graph.events,
            lactivities,
            ractivities,
            any_activity=any,
            quantifier=qT.qOp,
            occ=qT.number,
        )

    return eVal


def get_accessor(lactivity, ractivity):
    """
    Returns an accessor to the lActivity for the Concurrency Elements
    """
        
    if lactivity <= ractivity: 
        return lambda x : x[0]
                    
    else: 
        return lambda x : x[1]
 

def get_lIDs(graph_elements, lAct, rAct, key = lambda x : x[0]): 
    
    return set(map(key, graph_elements.get((lAct, rAct), [])))  
    
def lex_order(x, y):
    
    if x > y: 
        return (y,x) 
    
    else: 
        return (x,y)    

def check_quantified_operator(obs_occ, quantifier, occ):

    if quantifier == QuantifierOperator.Equals:
        return obs_occ == occ

    elif quantifier == QuantifierOperator.Less:
        return obs_occ < occ

    elif quantifier == QuantifierOperator.Greater:
        return obs_occ > occ

def check_quantified_binary_expressions(graph_elements,
                                        lActivities: Set[str],
                                        rActivities: Set[str],
                                        any_activity: bool,
                                        quantifier: QuantifierOperator,
                                        occ): 
    
    
    # We have a group on the right side
    if len(rActivities) > 1: 
        
        lactivity = lActivities.pop()
            
        lIds = [get_lIDs(graph_elements, lactivity, ractivity) for ractivity in rActivities]

        if any_activity:
                
            # Compute the length of the set of lActivites followed ANY of the rActivities
            return check_quantified_operator(quantifier, len(set.union(*lIds)), occ) 
                
        else: 
                
            # Compute the length of the set of lActivites followed by All of the rActivities
            return check_quantified_operator(quantifier,  len(set.intersection(*lIds)), occ) 
            
    else:
            
        check_qant = partial(check_quantified_operator, quantifier = quantifier, occ = occ) 
        ractivity = rActivities.pop()
        
        for lactivity in lActivities: 
                
            # Compute the number of unique lActivity that are followed by rActivity and check it against the quantifier
            if check_qant(len(get_lIDs(graph_elements, lactivity, ractivity))): 
                    
                if any_activity:
                    return True
                    
            elif not any_activity: 
                return False 
                
        return not any_activity
   
         
def check_non_quantified_binary_expressions(graph_elements,
                                            events,
                                            lActivities: Set[str],
                                            rActivities: Set[str],
                                            any_activity: bool):
    
    
    if len(rActivities) > 1 and any_activity: 

        lactivity = lActivities.pop()
        
        if not lactivity in events: 
            return False
        
        lIds = [get_lIDs(graph_elements, lactivity, ractivity) for ractivity in rActivities]
        
        return set.union(*lIds) == events[lactivity]
        
    else: 
        
        if any_activity:
        
            for lactivity in lActivities:

                if lactivity not in events:
                    continue

                for ractivity in rActivities:

                    if (
                        lactivity,
                        ractivity,
                    ) not in graph_elements or ractivity not in events:
                        continue

                    if set(map(lambda x : x[0], graph_elements[(lactivity, ractivity)])) == events[lactivity]:
                        return True

        else:

            for lactivity in lActivities:

                if lactivity not in events:
                    return False

                for ractivity in rActivities:

                    if ractivity not in events:
                        return False

                    if (lactivity, ractivity) not in graph_elements or \
                       not set(map(lambda x : x[0], graph_elements[(lactivity, ractivity)])) == events[lactivity]:
    
                       return False

        return not any_activity

def check_binary_expressions(
    graph_elements,
    events,
    lActivities: Set[str],
    rActivities: Set[str],
    any_activity: bool,
    quantifier: QuantifierOperator = None,
    occ=None,
):

    if not occ is None:
        
        return check_quantified_binary_expressions( graph_elements,
                                                    lActivities,
                                                    rActivities,
                                                    any_activity,
                                                    quantifier,
                                                    occ)
        
    else:
        
        return check_non_quantified_binary_expressions(graph_elements,
                                                       events,
                                                       lActivities,
                                                       rActivities,
                                                       any_activity)
                
def check_quantified_concurrent(graph_elements,
                                lActivities: Set[str],
                                rActivities: Set[str],
                                any_activity: bool,
                                quantifier: QuantifierOperator,
                                occ): 
    
    # We have a group on the right side
    if len(rActivities) > 1: 
        
        lactivity = lActivities.pop()
            
        lIds = [get_lIDs(graph_elements, *lex_order(lactivity, ractivity), get_accessor(lactivity, ractivity)) for ractivity in rActivities]
        
        if any_activity:
            # Compute the length of the set of lActivites followed ANY of the rActivities
            return check_quantified_operator(len(set.union(*lIds)), quantifier, occ) 
                
        else: 
            # Compute the length of the set of lActivites followed by All of the rActivities
            return check_quantified_operator(len(set.intersection(*lIds)), quantifier, occ) 
            
    else:
         
        check_qant = partial(check_quantified_operator, quantifier = quantifier, occ = occ) 
        ractivity = rActivities.pop()
        
        for lactivity in lActivities:
                
            lIds = get_lIDs(graph_elements, *lex_order(lactivity, ractivity), get_accessor(lactivity, ractivity))    
            # Compute the number of unique lActivity that are followed by rActivity and check it against the quantifier
            
            if check_qant(len(lIds)): 
                    
                if any_activity: 
                    return True
                    
            elif not any_activity: 
                return False 
                
        return not any_activity



    
def check_non_quantified_concurrent(graph_elements,
                                    events,
                                    lActivities: Set[str],
                                    rActivities: Set[str],
                                    any_activity: bool):
    
    if any_activity and len(rActivities) > 1: 
        
        lactivity = lActivities.pop()
        
        if not lactivity in events: 
            return False
        
        

        lIds = [get_lIDs(graph_elements, *lex_order(lactivity, rActivity), get_accessor(lactivity, rActivity)) for rActivity in rActivities]
        
        return set.union(*lIds) == events[lactivity]
    
    elif any_activity:
        
        for lactivity in lActivities:

            if lactivity not in events:
                continue

            for ractivity in rActivities:
                
                l, r = lex_order(lactivity, ractivity)
                
                if ractivity not in events or (l, r) not in graph_elements:
                    continue

                getLID = get_accessor(lactivity, ractivity)
                
                if set(map(getLID, graph_elements[(l, r)])) == events[lactivity]: 
                    return True

    else:

        for lactivity in lActivities:

            if lactivity not in events:
                return False

            for ractivity in rActivities:
                
                l, r = lex_order(lactivity, ractivity)
                
                if ractivity not in events or (l, r) not in graph_elements:
                    return False

                getLID = get_accessor(lactivity, ractivity)
                
                if not set(map(getLID, graph_elements[(l, r)])) == events[lactivity]: 
                    return False
                
        return not any_activity
    
    
def check_concurrent(
    graph_elements,
    events,
    lActivities,
    rActivities,
    any_activity: bool,
    quantifier: QuantifierOperator = None,
    occ=None):

    

    if not occ is None:
        return check_quantified_concurrent( graph_elements,
                                            lActivities,
                                                    rActivities,
                                                    any_activity,
                                                    quantifier,
                                                    occ)

    else:

        return check_non_quantified_concurrent(graph_elements,
                                               events,
                                               lActivities,
                                               rActivities,
                                               any_activity)

def check_unary_groups(
    graph_elements,
    activties: Set[str],
    any_activity: bool,
    quantifier: QuantifierOperator = None,
    occ=None,
):

    if not occ is None:
        
        check_qant = partial(check_quantified_operator, quantifier = quantifier, occ = occ)
        res = map(check_qant, [len(graph_elements.get(act, [])) for act in activties])
        
        if any_activity: 
            return any(res)
        
        else: 
            return all(res) 

    else:

        if any_activity:
            return not set(graph_elements).isdisjoint(activties)

        else:

            return activties.issubset(set(graph_elements))
