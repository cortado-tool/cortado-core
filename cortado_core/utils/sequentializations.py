import itertools
import math
import random
from copy import copy

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator, ConcurrencyTree, cTreeFromcGroup
from cortado_core.utils.split_graph import Group, SequenceGroup, ParallelGroup, LoopGroup

THRESHOLD = 1_000_000


def generate_sequentializations(variant: Group, n_sequentializations: int = -1):
    """ Calculates a given number of sequentializations for a given variant. In general, the algorithm creates the
        number of sequentializations by first calculating all sequentializations, followed by a sampling step. However,
        in rare cases, it might happen that the number of sequentializations is too large to be sequentialized (here:
        above THRESHOLD). In these cases, we first randomly change some concurrent and fallthrough to sequential
        operators, resulting in a single sequentialization for this operator. In rare cases, it might happen that
        the algorithm returns less sequentializations than requested, because the changing of operators removes too
        many sequentializations.
    :param variant:
    :param n_sequentializations: number of sequentializations to calculate. Default -1 calculates all sequentializations
    :return:
    """
    if n_sequentializations > -1:
        variant = preprocess_variant_to_undershoot_threshold(variant, max(THRESHOLD, n_sequentializations*10))

    sequentializations = generate_variants(variant)

    if -1 < n_sequentializations < len(sequentializations):
        sequentializations = random.sample(sequentializations, k=n_sequentializations)

    return sequentializations


def preprocess_variant_to_undershoot_threshold(variant: Group, threshold: int) -> Group:
    variant_tree = cTreeFromcGroup(variant)
    swapable_nodes = get_concurrent_fallthrough_operator_nodes(variant_tree)

    while get_number_of_sequentializations(variant_tree) > threshold:
        random_node = random.choice(swapable_nodes)
        swapable_nodes.remove(random_node)
        random_node.op = cTreeOperator.Sequential
        random.shuffle(random_node.children)

    return variant_tree.to_concurrency_group()


def get_concurrent_fallthrough_operator_nodes(variant_tree: ConcurrencyTree):
    if variant_tree.label is not None:
        return []

    result = []
    if variant_tree.op == cTreeOperator.Concurrent or variant_tree.op == cTreeOperator.Fallthrough:
        result.append(variant_tree)

    for child in variant_tree.children:
        result += get_concurrent_fallthrough_operator_nodes(child)

    return result


def get_number_of_sequentializations(variant_tree: ConcurrencyTree):
    n_seq, _ = get_number_of_sequentializations_and_leaves(variant_tree)
    return n_seq


def get_number_of_sequentializations_and_leaves(variant_tree: ConcurrencyTree):
    if variant_tree.op is None:
        return 1, 1

    if variant_tree.op == cTreeOperator.Fallthrough:
        # fallthrough group
        n_children = len(variant_tree.children)
        return math.factorial(n_children), n_children

    # by definition, loop groups are only defined for single-activity leafs
    # 2, because we sequentialize a loop *(a) as trace <a,a>
    if variant_tree.op == cTreeOperator.Loop:
        return 1, 2

    if variant_tree.op == cTreeOperator.Sequential:
        result_sequentialzations, result_leaves = 1, 0
        for child in variant_tree.children:
            result_seq_child, result_leaves_child = get_number_of_sequentializations_and_leaves(child)
            result_sequentialzations *= result_seq_child
            result_leaves += result_leaves_child
        return result_sequentialzations, result_leaves

    if variant_tree.op == cTreeOperator.Concurrent:
        group_numbers = [get_number_of_sequentializations_and_leaves(child) for child in variant_tree.children]
        groups_with_one_leaf = [(s, n) for s, n in group_numbers if n == 1]
        groups_with_more_leaves = [(s, n) for s, n in group_numbers if n > 1]

        # should hold because interval orders are a 2+2-free posets
        assert len(groups_with_more_leaves) <= 1

        result_sequentializations, result_leaves = 1, 0
        if len(groups_with_more_leaves) == 1:
            result_sequentializations, result_leaves = groups_with_more_leaves[0]

        for _ in groups_with_one_leaf:
            result_sequentializations *= result_leaves + 1
            result_leaves += 1

        return result_sequentializations, result_leaves

    raise Exception('group type is unknown')


def generate_variants(variant):
    if isinstance(variant, SequenceGroup):
        v = [generate_variants(v) for v in variant]
        v = itertools.product(*v)
        return [[a for g in vv for a in g] for vv in v]
    elif isinstance(variant, ParallelGroup):
        v = [generate_variants(vv) for vv in variant]
        # v = [[ee for e in vv for ee in e] for vv in v]
        v = itertools.product(*v)
        sequences = []
        for traces_tuple in v:
            sequences.extend(generate_parallel(traces_tuple))
        return sequences
    elif isinstance(variant, LoopGroup):
        v = variant[0][0]
        return [[v, v]]
    else:
        p = itertools.permutations(variant)
        p = [list(x) for x in p]
        return p


def generate_parallel(sub_traces, trace=[]):
    if len(sub_traces) == 0:
        return [trace]

    traces = []
    for x in sub_traces:
        x_copy = copy(x)
        t = copy(trace)

        t.append(x_copy.pop(0))
        if len(x_copy) > 0:
            lst_ = [l if l != x else x_copy for l in sub_traces]
        else:
            lst_ = [l for l in sub_traces if l != x]

        new_traces = generate_parallel(lst_, t)
        traces.extend(new_traces)
    return traces
