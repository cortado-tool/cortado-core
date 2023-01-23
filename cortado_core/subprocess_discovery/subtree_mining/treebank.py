from typing import List, Mapping
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree, cTreeFromcGroup
from cortado_core.utils.split_graph import Group
from pm4py.objects.log.obj import Trace


class TreeBankEntry():

    def __init__(self):
        self.tree: ConcurrencyTree = None
        self.uid: int = None

    def __init__(self, tree: ConcurrencyTree, tid: int, nTraces: int, traces=None):
        self.tree: ConcurrencyTree = tree
        self.uid: int = tid
        self.nTraces: int = nTraces
        self.traces = traces
        # self.activities = activities Consider adding activities, so a quick set disjointness between pattern and tree can allow a quick skip

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return ("Tree with UID: " + str(self.uid) + " representing " + str(self.nTraces) + " traces")


def create_treebank_from_cv_variants(variants: Mapping[Group, List[Trace]], artifical_start=False, add_traces=False) -> \
        Mapping[int, TreeBankEntry]:
    """
    From a cgraph dict, generate a trace-number sorted Treebank.  
    """

    treeBank = {}

    for i, group in enumerate(sorted(list(variants.keys()), key=lambda x: len(variants[x]), reverse=True)):

        # Bring the Variant groups in sorted order
        group = group.sort()

        # Compute the number of Traces
        nTraces = len(variants[group])

        # Convert the VariantGroup to a cTree
        tree = cTreeFromcGroup(group)

        if artifical_start:
            tree = tree.add_artifical_start_end()

            # Assign dfs ids to the tree nodes
        tree.assign_dfs_ids()

        traces = None if not add_traces else variants[group]

        treeBank[i] = TreeBankEntry(tree, i, nTraces, traces)

    return treeBank
