import unittest
from antlr4 import *
from cortado_core.variant_query_language.error_handling import (LexerError,
                                                                ParseError)
from cortado_core.variant_query_language.parse_query import parse_query_to_tree


class TestQueryParsing(unittest.TestCase):

    def test_valid_queries(self):
        
        valid_queries = [
                        "'A' isDF 'B';",
                        "(ANY {'A12 13412','A12 13412','A12 13412'} isDF 'B12yvbd 1324' OR 'A 1241 2' isEF 'C123') AND NOT ('G12412'isDF'1123 A' OR 'H' isDF 'A') AND 'G' isC AND 'X' isStart;",
                        "'A 1241 2 'isParallel 'C123' AND (NOT ('G12412' isDF '1123 A') OR 'H' isDF 'A') AND 'G' isC AND 'X' isStart;",
                        "'A 1241 2 'isParallel 'C123' AND (NOT ('G12412' isDF '1123 A') OR 'H' isDF 'A') AND 'G' isC AND NOT ('X' isStart);",
                        "(NOT ('G12412' isDF '1123 A') OR 'H' isDF 'A') AND 'G' isC AND 'X' isS;",
                        " NOT (~ ANY {'A12 13412', 'O', 'I'} isDF 'B12yvbd 1324' OR 'A 1241 2' isEF 'C123') AND 'G' isC;",
                        "( ANY {'A12 13412','A12 13412','A12 13412'} isDF 'B12yvbd 1324' OR 'A 1241 2' isEF 'C123') AND NOT (NOT ('G12412' isDirectlyFollowed '1123 A') OR 'H' isDirectlyFollowed 'A') AND 'G' isC AND 'X' isStart;",
                        "(~ ANY  {'A12 13412','A12 13412','A12 13412'} isDF 'B12yvbd 1324' OR 'A 1241 2' isEF 'C123') AND NOT (NOT ('G12412' isDirectlyFollowed '1123 A') OR 'H' isDirectlyFollowed 'A') AND 'G' isC AND 'X' isStart;",
                        " NOT ( ANY {'A12 13412','A12 13412','A12 13412'} isDF 'B12yvbd 1324' OR 'A 1241 2' isEF 'C123');",
                        " NOT ( ALL {'A12 13412','A12 13412','A12 13412'} isDF 'B12yvbd 1324' AND 'A 1241 2' isEF 'C123');",
                        "'A' isC;",
                        "('ACT1' isC OR 'ACT2' isC) -> ('ACT1' isDF 'ACT2' AND 'ACT2' isDF 'ACT3');",
                        "('ACT1' isC OR 'ACT2' isC) -> 'ACT2' isDF 'ACT3';",
                        "(('ACT1' isC OR 'ACT2' isC) -> 'ACT2' isDF 'ACT3') AND 'Act4' isC;",
                        "( NOT ('ACT1' isC OR 'ACT2' isC) -> 'ACT2' isDF 'ACT3') AND 'Act4' isC;",
                        "(('ACT1' isC OR 'ACT2' isC) -> 'ACT2' isDF 'ACT3') AND 'Act4' isC AND (('ACT1' isC OR 'ACT2' isC) -> 'ACT2' isDF 'ACT3');",
                        "'ACT1' isC -> 'ACT1' isDF 'ACT2';", 
                        "'1231245241234' isContained;",
                        "'I' isDF 'A';",
                        "'A' isDF 'D';",
                        "ALL {'B', 'C', 'D', 'E', 'B', 'C', 'D', 'E'} isDF 'A';",
                        " NOT ('A' isDF 'C');",
                        "'A' isParallel ALL {'B', 'C', 'D', 'E'};",
                        "ANY {'yadfgha435', '1241cdx41s'        , '1425 n'} isStart;",
                        "ALL {'yadfgha435', '1241cdx41s'        , '1425 n'} isEnd;",
                        "NOT ( ALL{'yadfgha435', '1241cdx41s'        , '1425 n'} isEnd);",
                        "NOT ('A' isC);",
                        "'1231245241234' isParallel '124';",
                        "'W_Completeren aanvraag' isContained;",
                        "'1231245241234' isParallel '124';", 
                        "'1231245241234' isParallel '124' > 4;", 
                        "'1231245241234' isParallel '124' = 2;", 
                        "'1231245241234' isParallel '124' < 2;", 
                        "'W_Completeren aanvraag <=> W_Accept' isContained; ",
                        "'W_Completeren aanvraag || W_Accept' isContained; ",
                        "'W_Completeren aanvraag --> W_Accept' isContained; ",
                        "'W_Completeren aanvraag (Incomplete)' isContained; ",
                        "'W_Completeren aanvraag <> W_Accept' isContained; ",
                        "'W_Completeren aanvraag ~~~ W_Accept' isContained;", 
                        "'W_Completeren aanvraag [10]' isContained > 4; ",
                        "'W_Completeren aanvraag \{ Unkown \}' isContained = 2; ",
                        "'W_Completeren aanvraag $payment pending$' isContained < 2; ",
                        ]
        
        for line in valid_queries: 
            parse_query_to_tree(line)
                
                
    
    def test_invalid_token_queries(self):
        
        invalid_queries = [
                            "'A' ----> 'B';",
                            "# 'I', 'H' isP ('A');",
                            "'H' ||| ('A');",
                            "!'H' isP 'A';",
                            "'B' | 'A';",
                            "* isDF 'A';"
                          ]

        for line in invalid_queries: 
                
            try: 
                    
                parse_query_to_tree(line)
                    
                self.assertFalse(True)
                    
            except Exception as LE: 
                self.assertIsInstance(LE, LexerError)
                    
                    
    def test_invalid_syntax_queries(self):
        
        
        invalid_queries = [ 
                            "NOT NOT ('A' isEF 'B');",
                            "isS 'A' isDF 'B';",
                            ";;;",
                            ";",
                            "{'A'} isC;", 
                            " ALL {'A'} isDF ALL {'B'};",
                            "ANY {'A'} isDF ANY {'B'};",
                            "ALL {} isDirectlyFollowed 'A';",
                            "'A' isC OR 'B' isC AND 'C' isC;", 
                            "('ACT1' isC OR 'ACT2' isC) -> ('ACT2' isDF 'ACT3');",
                            "'ACT1' isC OR 'ACT2' isC -> ('ACT1' isDF 'ACT2' AND 'ACT2' isDF 'ACT3');",
                          ]
            
        did_not_fail = False
            
        for line in invalid_queries: 
                
            try: 
                    
                parse_query_to_tree(line)
                    
                did_not_fail = True 
                msg = line
                break 
                
            except Exception as LE: 
                self.assertIsInstance(LE, ParseError)
                    
        if did_not_fail: 
            self.fail(msg = msg)

if __name__ == '__main__':
    unittest.main()
