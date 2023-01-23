
import unittest
from cortado_core.subprocess_discovery.subtree_mining.treebank import create_treebank_from_cv_variants
from cortado_core.tests.pattern_mining.example_log import create_example_log_1
from cortado_core.utils.cvariants import get_concurrency_variants


l = create_example_log_1()
        
class TreeBank(unittest.TestCase):

    def test_generate_treebank(self): 

        variants = get_concurrency_variants(l)
        treebank = create_treebank_from_cv_variants(variants, artifical_start = False)
        
        treebank_dict = {}
        
        for tid in treebank:     
            treebank_dict[str(treebank[tid].tree)] = treebank[tid].nTraces
        
        self.assertTrue(len(list(treebank)) == 10)
        self.assertTrue(treebank_dict['→(A, B)'] == 2)
        self.assertTrue(treebank_dict['→(H, ∧(G, →(B, C)))'] == 2)
        self.assertTrue(treebank_dict['→(H, ∧(G, →(B, C)), K)'] == 1)
        self.assertTrue(treebank_dict['→(A, B, A, B)'] == 1)
        self.assertTrue(treebank_dict['∧(I, →(A, ∧(B, C)))'] == 1)
        self.assertTrue(treebank_dict['→(A, ∧(B, C, D))'] == 1)
        
        
    def test_generate_art_start_treebank(self): 

        variants = get_concurrency_variants(l)
        treebank = create_treebank_from_cv_variants(variants, artifical_start = True)
        
        treebank_dict = {}
        
        for tid in treebank:     
            treebank_dict[str(treebank[tid].tree)] = treebank[tid].nTraces
        
        self.assertTrue(len(list(treebank)) == 10)
        self.assertTrue(treebank_dict['→(CT_ARTIFICAL_START_NAME, A, B, CT_ARTIFICAL_END_NAME)'] == 2)
        self.assertTrue(treebank_dict['→(CT_ARTIFICAL_START_NAME, H, ∧(G, →(B, C)), CT_ARTIFICAL_END_NAME)'] == 2)
        self.assertTrue(treebank_dict['→(CT_ARTIFICAL_START_NAME, H, ∧(G, →(B, C)), K, CT_ARTIFICAL_END_NAME)'] == 1)
        self.assertTrue(treebank_dict['→(CT_ARTIFICAL_START_NAME, A, B, A, B, CT_ARTIFICAL_END_NAME)'] == 1)
        self.assertTrue(treebank_dict['→(CT_ARTIFICAL_START_NAME, ∧(I, →(A, ∧(B, C))), CT_ARTIFICAL_END_NAME)'] == 1)
        self.assertTrue(treebank_dict['→(CT_ARTIFICAL_START_NAME, A, ∧(B, C, D), CT_ARTIFICAL_END_NAME)'] == 1)
        
if __name__ == '__main__':     
    
    unittest.main()