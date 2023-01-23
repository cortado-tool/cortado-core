
import unittest
from cortado_core.subprocess_discovery.subtree_mining.blanket_mining.cm_grow import cm_min_sub_mining
from cortado_core.subprocess_discovery.subtree_mining.obj import FrequencyCountingStrategy
from cortado_core.subprocess_discovery.subtree_mining.treebank import create_treebank_from_cv_variants
from cortado_core.tests.pattern_mining.example_log import create_example_log_2
from cortado_core.utils.cvariants import get_concurrency_variants

l = create_example_log_2()
variants = get_concurrency_variants(l)
treebank = create_treebank_from_cv_variants(variants, artifical_start = False)
class BlanketMining(unittest.TestCase):
    
    def test_TraceTransaction_Mining(self):
        strat = FrequencyCountingStrategy.TraceTransaction
        
        k_patterns = cm_min_sub_mining(treebank, strat, 20, 2)
    
        self.assertEqual(len(k_patterns.keys()), 10, 'Max Pattern Size')
        self.assertEqual(len(k_patterns[2]), 11, 'Patterns of Size 2')
        self.assertEqual(len(k_patterns[3]), 17, 'Patterns of Size 3')
        self.assertEqual(len(k_patterns[4]), 9, 'Patterns of Size 4')
        self.assertEqual(len(k_patterns[5]), 6, 'Patterns of Size 5')
        self.assertEqual(len(k_patterns[6]), 2, 'Patterns of Size 6')
        self.assertEqual(len(k_patterns[7]), 2, 'Patterns of Size 7')
        
        patterns_3 = [str(x) for x in k_patterns[3]]
        
        self.assertIn('→(B, C) with support: 9', patterns_3, '→(B, C) with support: 9')
        self.assertIn('∧(B, C) with support: 3', patterns_3, '∧(B, C) with support: 3')
        self.assertIn('→(A, B) with support: 5', patterns_3, '→(A, B) with support: 5')
        self.assertIn('∧(G, →( )) with support: 6', patterns_3, '∧(G, →( )) with support: 6')
        
        patterns_4 = [str(x) for x in k_patterns[4]]
        
        self.assertIn('→(∧(B, C)) with support: 3', patterns_4)
        self.assertIn('→(A, ∧(B)) with support: 3', patterns_4)
        self.assertIn('→(H, ∧(G)) with support: 6', patterns_4)
        self.assertIn('∧(G, →(B)) with support: 6', patterns_4)
        
        patterns_5 =  [str(x) for x in k_patterns[5]]
        
        self.assertNotIn('∧(→(B, C)) with support: 6', patterns_5, '∧(→(B, C)) with support: 6')
        self.assertNotIn('→(H, ∧(→(B))) with support: 6', patterns_5, '→(H, ∧(→(B))) with support: 6')
        
        self.assertIn('→(A, ∧(B, C)) with support: 3', patterns_5)
        self.assertIn('→(∧(G, →(B))) with support: 6', patterns_5)
        
        patterns_6 =  [str(x) for x in k_patterns[6]]
        
        self.assertNotIn('→(H, ∧(→(B, C))) with support: 6', patterns_6, '→(H, ∧(→(B, C))) with support: 6')
        self.assertIn('→(H, ∧(G, →(B))) with support: 6', patterns_6)
        self.assertIn('→(∧(G, →(B, C))) with support: 6', patterns_6)
                
                
    def test_TraceOccurences_Mining(self):
        strat = FrequencyCountingStrategy.TraceOccurence
        
        k_patterns = cm_min_sub_mining(treebank, strat, 20, 2)
         
        patterns_3 = [str(x) for x in k_patterns[3]]
        
        self.assertEqual(len(k_patterns.keys()), 10, 'Max Pattern Size')
        
        self.assertIn('→(A, B) with support: 5', patterns_3, '→(B, C) with support: 6')
        self.assertIn('∧(B, C) with support: 3', patterns_3, '∧(B, C) with support: 3')
        self.assertIn('∧(G, →( )) with support: 6', patterns_3, '∧(G, →( )) with support: 6')
        
        patterns_5 =  [str(x) for x in k_patterns[5]]
        
        self.assertNotIn('∧(→(B, C)) with support: 6', patterns_5, '∧(→(B, C)) with support: 6')
        self.assertNotIn('→(H, ∧(→(B))) with support: 6', patterns_5, '→(H, ∧(→(B))) with support: 6')
        
        patterns_6 =  [str(x) for x in k_patterns[6]]
        
        self.assertNotIn('→(H, ∧(→(B, C))) with support: 6', patterns_6, '→(H, ∧(→(B, C))) with support: 6')

    def test_VariantTransaction_Mining(self):
        strat = FrequencyCountingStrategy.VariantTransaction
        
        k_patterns = cm_min_sub_mining(treebank, strat, 20, 2)
         
        self.assertEqual(len(k_patterns.keys()), 6, 'Max Pattern Size')
        patterns_3 = [str(x) for x in k_patterns[3]]
        
        self.assertIn('→(A, B) with support: 4', patterns_3, '→(B, C) with support: 6')
        self.assertIn('→(B, C) with support: 6', patterns_3, '∧(B, C) with support: 3')
        
        patterns_4 = [str(x) for x in k_patterns[4]]
        
        self.assertIn('→(∧(B, C)) with support: 3', patterns_4, '→(B, C) with support: 6')

        patterns_5 = [str(x) for x in k_patterns[5]]
        
        self.assertIn('→(A, ∧(B, C)) with support: 3' , patterns_5, '→(A, ∧(B, C)) with support: 3')
        
        self.assertNotIn('∧(→(B, C)) with support: 4', patterns_5, '∧(→(B, C)) with support: 4')
        self.assertNotIn('→(H, ∧(→(B))) with support: 4', patterns_5, '→(H, ∧(→(B))) with support: 4')
        
        patterns_6 =  [str(x) for x in k_patterns[6]]
        
        self.assertNotIn('→(H, ∧(→(B, C))) with support: 4', patterns_6, '→(H, ∧(→(B, C))) with support: 4')
    
    def test_VariantOccurence_Mining(self):
        
        strat = FrequencyCountingStrategy.VariantOccurence
        k_patterns = cm_min_sub_mining(treebank, strat, 20, 2)
         
        self.assertEqual(len(k_patterns.keys()), 6, 'Max Pattern Size')
        patterns_3 = [str(x) for x in k_patterns[3]]
        
        self.assertIn('→(A, B) with support: 4', patterns_3, '→(B, C) with support: 4')
        self.assertIn('→(B, C) with support: 6', patterns_3, '∧(B, C) with support: 6')
        
        patterns_4 = [str(x) for x in k_patterns[4]]
        
        self.assertIn('→(∧(B, C)) with support: 3', patterns_4, '→(B, C) with support: 3')

        patterns_5 = [str(x) for x in k_patterns[5]]
        
        self.assertIn('→(A, ∧(B, C)) with support: 3' , patterns_5, '→(A, ∧(B, C)) with support: 3')
        
        self.assertNotIn('∧(→(B, C)) with support: 4', patterns_5, '∧(→(B, C)) with support: 4')
        self.assertNotIn('→(H, ∧(→(B))) with support: 4', patterns_5, '→(H, ∧(→(B))) with support: 4')
        
        patterns_6 =  [str(x) for x in k_patterns[6]]
        
        self.assertNotIn('→(H, ∧(→(B, C))) with support: 4', patterns_6, '→(H, ∧(→(B, C))) with support: 4')
        
if __name__ == '__main__':
            
    unittest.main()
