from antlr4 import *
from antlr4.InputStream import InputStream
from antlr4.CommonTokenStream import CommonTokenStream

from cortado_core.variant_query_language.convert_parse_tree_to_query_tree import (
    convertParseTreeToQueryTree,
)
from cortado_core.variant_query_language.error_handling import (
    ParseErrorListener,
    VQLLexerErrorListener,
)
from cortado_core.variant_query_language.grammars.VQLLexer import VQLLexer
from cortado_core.variant_query_language.grammars.vqlParser import vqlParser


def parse_query_to_tree(query: str):
    input_stream = InputStream(query)
    lexer = VQLLexer(input=input_stream)

    lexer.removeErrorListeners()
    lexer.addErrorListener(VQLLexerErrorListener())

    stream = CommonTokenStream(lexer)
    parser = vqlParser(stream)

    parser.removeErrorListeners()
    parser.addErrorListener(ParseErrorListener())

    pT = parser.start()

    return pT


def parse_query_to_query_tree(query: str):

    pT = parse_query_to_tree(query)

    qT = convertParseTreeToQueryTree(pT.getRuleContext())

    return qT
