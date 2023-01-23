import unittest

# https://stackoverflow.com/questions/46374185/does-python-have-a-function-which-computes-_multinomial-coefficients
# Multinomial coefficient of a list [a1, ... ,an]. It is the number of interleaved sequences of n sequences, of which lengths are a1,...,an respectively
from cortado_core.utils.sequentializations import generate_variants
from cortado_core.utils.split_graph import Group


def _multinomial(lst):
    res, i = 1, sum(lst)
    i0 = lst.index(max(lst))
    for a in lst[:i0] + lst[i0+1:]:
        for j in range(1,a+1):
            res *= i
            res //= j
            i -= 1
    return res

# Count number of leaves of the process tree
def _num_leaves(variant):
    if 'leaf' in variant:
        return len(variant['leaf'])
    else:
        res = 0
        children = list(variant.items())[0][1]
        for child in children:
            res += _num_leaves(child)
        return res

# Count number of sequentializations of a concurrency variant
# Only for a tree, of which all leaves are different
def _num_sequences(variant):
    if 'leaf' in variant:
        return len(variant['leaf'])
    elif 'follows' in variant:
        res = 1
        for child in variant['follows']:
            res *= _num_sequences(child)
        return res
    else: # parallel
        res = 1
        num_leaves_children = []
        for child in variant['parallel']:
            num_leaves_children.append(_num_leaves(child))
            res *= _num_sequences(child)
        res *= _multinomial(num_leaves_children)
        return res

test_variant_1 = { # A part of Daniel's troublesome variant
    'parallel': [
        {
            'follows': [
                {'leaf': ['aa']},
                {
                    'parallel': [
                        {'leaf': ['bb']},
                        {'leaf': ['cc']}
                    ]
                },
                {'leaf': ['dd']},
                {'leaf': ['ee']}
            ]
        },
        {'leaf': ['ff']}
    ]
}

test_variant_2 = { # A child of test_variant_1
    'follows': [
        {'leaf': ['aa']},
        {
            'parallel': [
                {'leaf': ['bb']},
                {'leaf': ['cc']}
            ]
        },
        {'leaf': ['dd']},
        {'leaf': ['ee']}
    ]
}

test_variant_3 = { # Simple sequential tree
    'follows': [
        {'leaf': ['x1']},
        {'leaf': ['x2']},
        {'leaf': ['x3']},
        {'leaf': ['x4']},
        {'leaf': ['x5']}
    ]
}

test_variant_4 = { # Simple parallel tree
    'parallel': [
        {'leaf': ['x1']},
        {'leaf': ['x2']},
        {'leaf': ['x3']},
        {'leaf': ['x4']}
    ]
}

test_variant_5 = { # follows with parallel children
    'follows': [
        {
            'parallel': [
                {'leaf': ['aa']},
                {'leaf': ['bb']}
            ]
        },
        {
            'parallel': [
                {'leaf': ['cc']},
                {'leaf': ['dd']},
                {'leaf': ['ee']}
            ]
        },
        {
            'parallel': [
                {'leaf': ['ff']},
                {'leaf': ['gg']},
                {'leaf': ['hh']},
                {'leaf': ['ii']}
            ]
        },
        {
            'parallel': [
                {'leaf': ['jj']}
            ]
        },
    ]
}

test_variant_6 = { # parallel with follows children
    'parallel': [
        {
            'follows': [
                {'leaf': ['aa']},
                {'leaf': ['bb']}
            ]
        },
        {
            'follows': [
                {'leaf': ['cc']},
                {'leaf': ['dd']},
                {'leaf': ['ee']}
            ]
        },
        {
            'follows': [
                {'leaf': ['ff']}
            ]
        }
    ]
}

test_variant_7 = { # Nested operators
    'parallel': [
        {
            'follows': [
                {
                    'parallel': [
                        {'leaf': ['aa']},
                        {'leaf': ['bb']}
                    ]
                },
                {
                    'parallel': [
                        {'leaf': ['cc']},
                        {'leaf': ['dd']}
                    ]
                }
            ]
        },
        {'leaf': ['ee']},
    ]
}

test_variant_8 = { # Nested operators
    'follows': [
        {
            'parallel': [
                {'leaf': ['aa']},
                {'leaf': ['bb']},
                {
                    'follows': [
                        {'leaf': ['cc']},
                        {'leaf': ['dd']}
                    ]
                }
            ]
        },
        {
            'parallel': [
                {
                    'follows': [
                        {'leaf': ['ee']},
                        {'leaf': ['ff']}
                    ]
                },
                {'leaf': ['gg']}
            ]
        },
        {'leaf': ['hhs']}
    ]
}

test_variant_9 = { # Attempting to recreate the problem with test case 1 and 7
    'parallel': [
        {
            'follows': [
                {'leaf': ['aa']},
                {
                    'parallel': [
                        {'leaf': ['bb']},
                        {'leaf': ['cc']}
                    ]
                },
                {'leaf': ['dd']}
            ]
        },
        {
            'follows': [
                {'leaf': ['ee']},
                {'leaf': ['ff']}
            ]
        }
    ]
}

test_cases = [
    test_variant_1,
    test_variant_2,
    test_variant_3,
    test_variant_4,
    test_variant_5,
    test_variant_6,
    test_variant_7,
    test_variant_8,
    test_variant_9,
]    

class TestGenerateVariants(unittest.TestCase):
    def test_generate_n_variants(self):
        for cvariant in test_cases:
            with self.subTest():
                variants = generate_variants(Group.deserialize(cvariant))
                self.assertEqual(len(variants), _num_sequences(cvariant))

if __name__ == '__main__':
    unittest.main()