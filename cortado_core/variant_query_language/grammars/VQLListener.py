# Generated from c:\Users\49171\Desktop\cortado-core\cortado_core\variant_query_language\grammars\vql.g4 by ANTLR 4.9.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .vqlParser import vqlParser
else:
    from vqlParser import vqlParser

# This class defines a complete listener for a parse tree produced by vqlParser.
class vqlListener(ParseTreeListener):

    # Enter a parse tree produced by vqlParser#start.
    def enterStart(self, ctx:vqlParser.StartContext):
        pass

    # Exit a parse tree produced by vqlParser#start.
    def exitStart(self, ctx:vqlParser.StartContext):
        pass


    # Enter a parse tree produced by vqlParser#query.
    def enterQuery(self, ctx:vqlParser.QueryContext):
        pass

    # Exit a parse tree produced by vqlParser#query.
    def exitQuery(self, ctx:vqlParser.QueryContext):
        pass


    # Enter a parse tree produced by vqlParser#logicBlock.
    def enterLogicBlock(self, ctx:vqlParser.LogicBlockContext):
        pass

    # Exit a parse tree produced by vqlParser#logicBlock.
    def exitLogicBlock(self, ctx:vqlParser.LogicBlockContext):
        pass


    # Enter a parse tree produced by vqlParser#DIRECTLYFOLLOWSOP.
    def enterDIRECTLYFOLLOWSOP(self, ctx:vqlParser.DIRECTLYFOLLOWSOPContext):
        pass

    # Exit a parse tree produced by vqlParser#DIRECTLYFOLLOWSOP.
    def exitDIRECTLYFOLLOWSOP(self, ctx:vqlParser.DIRECTLYFOLLOWSOPContext):
        pass


    # Enter a parse tree produced by vqlParser#EVENTUALLYFOLLOWSOP.
    def enterEVENTUALLYFOLLOWSOP(self, ctx:vqlParser.EVENTUALLYFOLLOWSOPContext):
        pass

    # Exit a parse tree produced by vqlParser#EVENTUALLYFOLLOWSOP.
    def exitEVENTUALLYFOLLOWSOP(self, ctx:vqlParser.EVENTUALLYFOLLOWSOPContext):
        pass


    # Enter a parse tree produced by vqlParser#CONCURRENTOP.
    def enterCONCURRENTOP(self, ctx:vqlParser.CONCURRENTOPContext):
        pass

    # Exit a parse tree produced by vqlParser#CONCURRENTOP.
    def exitCONCURRENTOP(self, ctx:vqlParser.CONCURRENTOPContext):
        pass


    # Enter a parse tree produced by vqlParser#CONTAINSOP.
    def enterCONTAINSOP(self, ctx:vqlParser.CONTAINSOPContext):
        pass

    # Exit a parse tree produced by vqlParser#CONTAINSOP.
    def exitCONTAINSOP(self, ctx:vqlParser.CONTAINSOPContext):
        pass


    # Enter a parse tree produced by vqlParser#STARTOP.
    def enterSTARTOP(self, ctx:vqlParser.STARTOPContext):
        pass

    # Exit a parse tree produced by vqlParser#STARTOP.
    def exitSTARTOP(self, ctx:vqlParser.STARTOPContext):
        pass


    # Enter a parse tree produced by vqlParser#ENDOP.
    def enterENDOP(self, ctx:vqlParser.ENDOPContext):
        pass

    # Exit a parse tree produced by vqlParser#ENDOP.
    def exitENDOP(self, ctx:vqlParser.ENDOPContext):
        pass


    # Enter a parse tree produced by vqlParser#EQUALSOP.
    def enterEQUALSOP(self, ctx:vqlParser.EQUALSOPContext):
        pass

    # Exit a parse tree produced by vqlParser#EQUALSOP.
    def exitEQUALSOP(self, ctx:vqlParser.EQUALSOPContext):
        pass


    # Enter a parse tree produced by vqlParser#LESSOP.
    def enterLESSOP(self, ctx:vqlParser.LESSOPContext):
        pass

    # Exit a parse tree produced by vqlParser#LESSOP.
    def exitLESSOP(self, ctx:vqlParser.LESSOPContext):
        pass


    # Enter a parse tree produced by vqlParser#GREATEROP.
    def enterGREATEROP(self, ctx:vqlParser.GREATEROPContext):
        pass

    # Exit a parse tree produced by vqlParser#GREATEROP.
    def exitGREATEROP(self, ctx:vqlParser.GREATEROPContext):
        pass


    # Enter a parse tree produced by vqlParser#quantifier.
    def enterQuantifier(self, ctx:vqlParser.QuantifierContext):
        pass

    # Exit a parse tree produced by vqlParser#quantifier.
    def exitQuantifier(self, ctx:vqlParser.QuantifierContext):
        pass


    # Enter a parse tree produced by vqlParser#UnaryExpression.
    def enterUnaryExpression(self, ctx:vqlParser.UnaryExpressionContext):
        pass

    # Exit a parse tree produced by vqlParser#UnaryExpression.
    def exitUnaryExpression(self, ctx:vqlParser.UnaryExpressionContext):
        pass


    # Enter a parse tree produced by vqlParser#BinaryExpression.
    def enterBinaryExpression(self, ctx:vqlParser.BinaryExpressionContext):
        pass

    # Exit a parse tree produced by vqlParser#BinaryExpression.
    def exitBinaryExpression(self, ctx:vqlParser.BinaryExpressionContext):
        pass


    # Enter a parse tree produced by vqlParser#SimpleExpression.
    def enterSimpleExpression(self, ctx:vqlParser.SimpleExpressionContext):
        pass

    # Exit a parse tree produced by vqlParser#SimpleExpression.
    def exitSimpleExpression(self, ctx:vqlParser.SimpleExpressionContext):
        pass


    # Enter a parse tree produced by vqlParser#QuantifiedExpression.
    def enterQuantifiedExpression(self, ctx:vqlParser.QuantifiedExpressionContext):
        pass

    # Exit a parse tree produced by vqlParser#QuantifiedExpression.
    def exitQuantifiedExpression(self, ctx:vqlParser.QuantifiedExpressionContext):
        pass


    # Enter a parse tree produced by vqlParser#implyBlock.
    def enterImplyBlock(self, ctx:vqlParser.ImplyBlockContext):
        pass

    # Exit a parse tree produced by vqlParser#implyBlock.
    def exitImplyBlock(self, ctx:vqlParser.ImplyBlockContext):
        pass


    # Enter a parse tree produced by vqlParser#impliesClause.
    def enterImpliesClause(self, ctx:vqlParser.ImpliesClauseContext):
        pass

    # Exit a parse tree produced by vqlParser#impliesClause.
    def exitImpliesClause(self, ctx:vqlParser.ImpliesClauseContext):
        pass


    # Enter a parse tree produced by vqlParser#dnfClause.
    def enterDnfClause(self, ctx:vqlParser.DnfClauseContext):
        pass

    # Exit a parse tree produced by vqlParser#dnfClause.
    def exitDnfClause(self, ctx:vqlParser.DnfClauseContext):
        pass


    # Enter a parse tree produced by vqlParser#cnfClause.
    def enterCnfClause(self, ctx:vqlParser.CnfClauseContext):
        pass

    # Exit a parse tree produced by vqlParser#cnfClause.
    def exitCnfClause(self, ctx:vqlParser.CnfClauseContext):
        pass


    # Enter a parse tree produced by vqlParser#AnyGroup.
    def enterAnyGroup(self, ctx:vqlParser.AnyGroupContext):
        pass

    # Exit a parse tree produced by vqlParser#AnyGroup.
    def exitAnyGroup(self, ctx:vqlParser.AnyGroupContext):
        pass


    # Enter a parse tree produced by vqlParser#InvertedAnyGroup.
    def enterInvertedAnyGroup(self, ctx:vqlParser.InvertedAnyGroupContext):
        pass

    # Exit a parse tree produced by vqlParser#InvertedAnyGroup.
    def exitInvertedAnyGroup(self, ctx:vqlParser.InvertedAnyGroupContext):
        pass


    # Enter a parse tree produced by vqlParser#AllGroup.
    def enterAllGroup(self, ctx:vqlParser.AllGroupContext):
        pass

    # Exit a parse tree produced by vqlParser#AllGroup.
    def exitAllGroup(self, ctx:vqlParser.AllGroupContext):
        pass


    # Enter a parse tree produced by vqlParser#InvertedAllGroup.
    def enterInvertedAllGroup(self, ctx:vqlParser.InvertedAllGroupContext):
        pass

    # Exit a parse tree produced by vqlParser#InvertedAllGroup.
    def exitInvertedAllGroup(self, ctx:vqlParser.InvertedAllGroupContext):
        pass



del vqlParser