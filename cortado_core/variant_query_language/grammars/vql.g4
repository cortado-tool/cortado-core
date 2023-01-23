// A first definition of VQL 
grammar vql;
options {language=Python3; tokenVocab=VQLLexer;}

start : (query)* EOF; 

query : ( logicBlock
        ) SEMICOLON; 

logicBlock :
          leaf 
        | dnfClause 
        | cnfClause 
        | impliesClause
        | neg = NOT LPAR leaf RPAR 
        | neg = NOT LPAR dnfClause RPAR 
        | neg = NOT LPAR cnfClause RPAR
        | neg = NOT LPAR impliesClause RPAR; 

bQueryOp: ISDIRECTLYFOLLOWED # DIRECTLYFOLLOWSOP
        | ISEVENTUALLYFOLLOWED # EVENTUALLYFOLLOWSOP
        | ISCONCURRENT # CONCURRENTOP; 

uQueryOp : ISCONTAINED # CONTAINSOP
         | ISSTARTTOKEN # STARTOP
         | ISENDTOKEN # ENDOP;

qOp : EQUALS # EQUALSOP
    | LT # LESSOP
    | GT # GREATEROP; 

quantifier : op = qOp number = NUMBER;

/* 
    A Leaf is either a unary or binary operator applied to activities
    either left or around the operator respectivitly
    A Leaf can be negated and the activites and op are then nested in paranthesis ()
*/

expression: activity = group  op = uQueryOp # UnaryExpression
          | activity = ACTIVITY op = uQueryOp # UnaryExpression
          | left = ACTIVITY op = bQueryOp right = group # BinaryExpression
          | left = group op = bQueryOp right = ACTIVITY # BinaryExpression 
          | left = ACTIVITY op = bQueryOp right = ACTIVITY # BinaryExpression;

leaf : exp = expression # SimpleExpression 
     | exp = expression quant = quantifier #QuantifiedExpression;
     
/* 
    A clause is either Leafs conjoined Wby the respective logical Operator 
    or a nested clause of the other type written in Paranthesis ()
*/

implyBlock : 
    leaf 
    | LPAR dnfClause RPAR
    | LPAR cnfClause RPAR
    | LPAR impliesClause RPAR
    | neg = NOT LPAR leaf RPAR 
    | neg = NOT LPAR dnfClause RPAR 
    | neg = NOT LPAR cnfClause RPAR ; 

impliesClause : 
( 
  lBlock = implyBlock
) IMPLIES 
( 
  rBlock= implyBlock
); 

dnfClause : ( leafs+=leaf
            | NOT LPAR negleafs+= leaf RPAR 
            | LPAR clauses+=cnfClause RPAR 
            | LPAR implyClauses+=impliesClause RPAR 
            | NOT LPAR negclauses+=cnfClause RPAR 
            | NOT LPAR negimplyClauses+=impliesClause RPAR
            ) 
            (OR  (( leafs+=leaf
                  | NOT LPAR negleafs+= leaf RPAR 
                  | LPAR clauses+=cnfClause RPAR 
                  | LPAR implyClauses+=impliesClause RPAR 
                  | NOT LPAR negclauses+=cnfClause RPAR
                  | NOT LPAR negimplyClauses+=impliesClause RPAR
                  ))
            )+;

cnfClause : ( leafs+=leaf 
            | NOT LPAR negleafs+= leaf RPAR
            | LPAR clauses+=dnfClause RPAR 
            | LPAR implyClauses+=impliesClause RPAR 
            | NOT LPAR negclauses+=dnfClause RPAR
            | NOT LPAR negimplyClauses+=impliesClause RPAR
            )
            (AND (( leafs+=leaf 
                  | NOT LPAR negleafs += leaf RPAR
                  | LPAR clauses+=dnfClause RPAR 
                  | LPAR implyClauses+=impliesClause RPAR 
                  | NOT LPAR negclauses+=dnfClause RPAR 
                  | NOT LPAR negimplyClauses+=impliesClause RPAR
                  ))
            )+;  

/* 
    An Activity is a identifier written in '' or a Activity Group
    An ActivityGroup is a list of Activities written inside Brackets [] / {}
*/

group : ANY LCBRACKET activityList+=ACTIVITY (COMMA activityList+=ACTIVITY)* RCBRACKET #AnyGroup
      | GROUPINVERSE ANY LCBRACKET activityList+=ACTIVITY (COMMA activityList+=ACTIVITY)* RCBRACKET # InvertedAnyGroup
      | ALL LCBRACKET activityList+=ACTIVITY (COMMA activityList+=ACTIVITY)* RCBRACKET # AllGroup
      | GROUPINVERSE ALL LCBRACKET activityList+=ACTIVITY (COMMA activityList+=ACTIVITY)* RCBRACKET # InvertedAllGroup; 

