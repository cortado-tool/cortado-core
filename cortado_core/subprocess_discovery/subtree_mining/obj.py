from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Set

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import cTreeOperator

class FrequencyCountingStrategy(Enum):
    """
    Defines the different Frequency Counting Strategies supported by the model
    """

    TraceTransaction = 1
    TraceOccurence = 2
    VariantTransaction = 3
    VariantOccurence = 4
    
@dataclass
class FrequentActivitySets:
    fA: Set[str]
    efR: Mapping[str, str]
    dfR: Mapping[str, str]
    ccR: Mapping[str, str]
@dataclass
class PruningSets_2Patterns:
    ftNestPrune: Set[str]
    dfNestPrune: Set[str]
    ccNestPrune: Set[str]
    ccLabelPrune: Mapping[str, Set[str]]
    ccFollowsPrune: Mapping[str, Set[str]]
    dfLabelPrune: Mapping[str, Set[str]]
    dfFollowsPrune: Mapping[str, Set[str]]
    efFollowsPrune: Mapping[str, Set[str]]
    ftLabelPrune: Mapping[str, Set[str]]
    operatorPrune: Mapping[str, Set[str]]
    operatorOperatorPrune : Mapping[cTreeOperator, Set[cTreeOperator]]
    operatorActivityPrune : Mapping[cTreeOperator, Set[str]]
@dataclass
class PruningSets:
    dfFollowsPrune: Mapping[str, Set[str]]
    efFollowsPrune: Mapping[str, Set[str]]
    sibPrune: Mapping[tuple, Set]
    nestPrune: Mapping[tuple, Set]