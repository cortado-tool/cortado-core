
import unittest
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_grow import cm_min_sub_mining
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.compute_occurence_blanket import check_occ_blanket
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequencyCountingStrategy

from cortado_core.subprocess_discovery.subtree_mining.treebank import create_treebank_from_cv_variants
from cortado_core.tests.pattern_mining.example_log import create_example_log_1
from cortado_core.utils.cvariants import get_concurrency_variants

l = create_example_log_1()
variants = get_concurrency_variants(l)
treebank = create_treebank_from_cv_variants(variants, artifical_start = False)
   
class BlanketPruningMethods(unittest.TestCase):
    
    def test_Occurence_Matching(self):
        strat = FrequencyCountingStrategy.TraceTransaction
        
        k_patterns = cm_min_sub_mining(treebank, strat, 20, 1)
        
        for p in k_patterns[3]: 
            
            if str(p) == "∧(→(B)) with support: 6": 
                l, r = check_occ_blanket(p)
                self.assertTrue(l)
                self.assertTrue(r)
        
            if str(p) == "→(∧(O)) with support: 3": 
                l, r = check_occ_blanket(p)
                self.assertFalse(l)
                self.assertTrue(r)
                
            if str(p) == "→(∧(P)) with support: 3": 
                l, r = check_occ_blanket(p)
                self.assertTrue(l)
                self.assertTrue(r)
            
            if str(p) == "→(∧(→( )))": 
                l, r = check_occ_blanket(p)
                self.assertFalse(l)
                self.assertFalse(r)
                
            if str(p) == "→(∧(B)) with support: 3": 
                l, r = check_occ_blanket(p)
                self.assertFalse(l)
                self.assertTrue(r)
                
if __name__ == '__main__':     
    unittest.main()