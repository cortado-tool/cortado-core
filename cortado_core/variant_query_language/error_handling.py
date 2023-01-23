import sys
from antlr4.error.ErrorListener import ErrorListener


class VQLLexerErrorListener(ErrorListener): 
    
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print("line " + str(line) + ":" + str(column) + " " + msg, file=sys.stderr)
        raise LexerError(column, offendingSymbol, msg)
        
class ParseErrorListener(ErrorListener): 
    
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print("line " + str(line) + ":" + str(column) + " " + msg, file=sys.stderr)
        raise ParseError(column, offendingSymbol, msg)
    
    
    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
        print("Index " + str(startIndex) + ":" + str(stopIndex) + " " + recognizer, file=sys.stderr)
        
    
class LexerError(Exception): 
    
    def __init__(self, column, offendingSymbol, msg): 
        self.msg = msg
        self.column = column
        self.offendingSymbol = offendingSymbol
        
class ParseError(Exception): 
    
    def __init__(self, column, offendingSymbol, msg): 
        self.msg = msg
        self.column = column
        self.offendingSymbol = offendingSymbol