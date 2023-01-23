import unittest
from antlr4 import *
from cortado_core.tests.vql.query_example_log import create_example_log_1
from cortado_core.variant_query_language.check_query_tree_against_graph import check_query_tree
from cortado_core.variant_query_language.convert_parse_tree_to_query_tree import convertParseTreeToQueryTree

from cortado_core.variant_query_language.parse_query import parse_query_to_tree
from cortado_core.utils.cvariants import get_concurrency_variants

l = create_example_log_1()
variants = get_concurrency_variants(l)

activites = set()

for variant in variants: 
    for g in variant.graphs: 
        activites.update(g.events.keys())

print('Running Query')
pt = parse_query_to_tree("('A' isC OR 'H' isC) -> ('B' isP 'G' AND 'C' isP 'G');")
qt = convertParseTreeToQueryTree(pt)
print('Query', qt)
            
for id, variant in enumerate(variants): 
 
    print()
    matched = check_query_tree(qt, list(variant.graphs.keys())[0], activites)
    print("ID:", id, 'Matched: ', matched)  
    print(variant)
    
class TestQueryEval(unittest.TestCase):

    def test_evaluate_leafs_non_quantified(self):
        
        query_pairs = {
            "'A' isDF 'B';" : [0, 1, 3, 5, 6, 7],
            "'A' isEF 'B';" : [0, 1, 2, 3, 5, 6, 7],
            "ANY {'A', 'H'} isEF 'B';" : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "ALL {'A', 'H'} isEF 'B';" : [],
            "'A' isStart;" : [0, 1, 2, 3, 5, 6, 7],
            "NOT ('A' isStart);" : [4,8,9],
            "ANY {'A', 'H'} isStart;" : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "ALL {'B', 'C'} isEnd;" : [5,6,7],
            "ALL {'B', 'C', 'D'} isEnd;" : [6],
            "'G' isP ALL {'B', 'C'};" : [8,9],
            "'G' isP ANY {'B', 'C'};" : [8,9], 
            "ALL {'B', 'C'} isP 'D';" : [6], 
            "ANY {'B', 'D'} isP 'C';" : [5, 6, 7], 
            "'K' isC OR 'I' isC OR 'D' isC;" : [6,7,9],
            "'K' isC AND 'I' isC AND 'D' isC;" : [],
            "'C' isC AND 'D' isC;" : [6], 
            "'B' isP 'C' AND 'A' isDF ALL {'B', 'C'} ;" : [5, 6, 7],
            "'I' isP ALL {'A','B', 'C'};" : [7], 
            "'A' isC -> 'A' isDF 'B';" : [0,1,3,4,5,6,7,8,9], 
            "('A' isC -> 'A' isDF 'B') AND 'I' isP ALL {'A','B', 'C'};" : [7], 
            "('A' isC -> 'A' isDF 'B') OR 'I' isP ALL {'A','B', 'C'};" : [0,1,3,4,5,6,7,8,9], 
            "'A' isC -> 'C' isP 'B';" : [4,5,6,7,8,9],
            "NOT ('A' isC -> 'C' isP 'B');" : [0,1,2,3],
            "('A' isC OR 'H' isC) -> ('A' isDF 'B' OR 'H' isDF 'B');" : [0, 1,3,4,5,6,7,8,9],
            "('A' isC OR 'H' isC) -> ('B' isP 'G' AND 'C' isP 'G');" : [8, 9],
        }
        
        for query, ids in query_pairs.items(): 
            pt = parse_query_to_tree(query)
            qt = convertParseTreeToQueryTree(pt)
            
            res_ids = []
            
            for id, variant in enumerate(variants): 
                
                if check_query_tree(qt, list(variant.graphs.keys())[0], activites):
                        res_ids.append(id)
                         
            self.assertEqual(ids, res_ids, msg = query)
            
        
    def test_evaluate_leafs_quantified(self):
        
        query_pairs = {
            "'A' isDF 'B' = 1;" : [0, 2, 3, 5, 6, 7],
            "'A' isEF 'B' < 3;" : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "'A' isEF 'B' > 1;" : [1, 2],
            "'A' isEF 'B' > 0;" : [0, 1, 2, 3, 5, 6, 7],
            "'A' isDF 'B' > 0;" : [0, 1, 2, 3, 5, 6, 7],
            "ANY {'A', 'H'} isEF 'B' = 1;" : [0, 3, 4, 5, 6, 7, 8, 9],
            "ALL {'A', 'H'} isEF 'B' < 2;" : [0, 3, 4, 5, 6, 7, 8, 9],
            "'A' isStart = 1;" : [0, 1, 2, 3, 5, 6, 7],
            "'G' isP ALL {'B', 'C'} = 1;" : [8,9],
            "'G' isP ANY {'B', 'C'} = 1;" : [8,9],
        }
        
        for query, ids in query_pairs.items(): 
            pt = parse_query_to_tree(query)
            qt = convertParseTreeToQueryTree(pt)
            
            res_ids = []
            
            for id, variant in enumerate(variants): 
                
                if check_query_tree(qt, list(variant.graphs.keys())[0], activites):
                        res_ids.append(id)
                         
            self.assertEqual(ids, res_ids)       
            
if __name__ == '__main__':
    unittest.main()