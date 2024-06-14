from typing import List

from cortado_core.eventually_follows_pattern_mining.frequency_counting.counting_strategy import (
    CountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_occurrence_counting_strategy import (
    TraceOccurrenceCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.trace_transaction_counting_strategy import (
    TraceTransactionCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_occurrence_counting_strategy import (
    VariantOccurrenceCountingStrategy,
)
from cortado_core.eventually_follows_pattern_mining.frequency_counting.variant_transaction_counting_strategy import (
    VariantTransactionCountingStrategy,
)
from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree
from cortado_core.subprocess_discovery.subtree_mining.obj import (
    FrequencyCountingStrategy,
)


def get_counting_strategy(
    count_strategy: FrequencyCountingStrategy, trees: List[ConcurrencyTree]
) -> CountingStrategy:
    if count_strategy == FrequencyCountingStrategy.TraceTransaction:
        return TraceTransactionCountingStrategy(trees)
    if count_strategy == FrequencyCountingStrategy.VariantTransaction:
        return VariantTransactionCountingStrategy()
    if count_strategy == FrequencyCountingStrategy.TraceOccurence:
        return TraceOccurrenceCountingStrategy(trees)

    return VariantOccurrenceCountingStrategy()
