from typing import Dict, Set

from cortado_core.eventually_follows_pattern_mining.obj import (
    EventuallyFollowsPattern,
    SubPattern,
)


def filter_incomplete_patterns(
    patterns: Dict[int, Set[EventuallyFollowsPattern]],
) -> Dict[int, Set[EventuallyFollowsPattern]]:
    result = dict()

    for k in patterns:
        filtered_patterns = set()
        for pattern in patterns[k]:
            if is_pattern_valid(pattern):
                filtered_patterns.add(pattern)

        result[k] = filtered_patterns

    return result


def is_pattern_valid(pattern: EventuallyFollowsPattern) -> bool:
    # we only need to check the last sub-pattern; the enumeration guarantees the other sub-patterns to be valid
    return is_sub_pattern_valid(pattern.sub_patterns[-1])


def is_sub_pattern_valid(sub_pattern: SubPattern) -> bool:
    if sub_pattern.label is not None:
        return True

    if len(sub_pattern.children) < 2:
        return False

    for child in sub_pattern.children:
        if not is_sub_pattern_valid(child):
            return False

    return True
