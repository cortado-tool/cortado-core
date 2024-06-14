from typing import Tuple, Set

from cortado_core.subprocess_discovery.concurrency_trees.cTrees import ConcurrencyTree


class Positions:
    def __init__(self, dfs_positions: Tuple, bfs_positions: Tuple):
        self.dfs = dfs_positions
        self.bfs = bfs_positions

    def __repr__(self):
        return f"Positions(dfs:{self.dfs}, bfs:{self.bfs})"

    def __eq__(self, other):
        return self.dfs, self.bfs == other.dfs, other.bfs

    def __hash__(self):
        return hash((self.dfs, self.bfs))

    def serialize(self):
        return {"dfs": list(self.dfs), "bfs": list(self.bfs)}


class Pair:
    def __init__(
        self,
        positions: Positions,
        pattern: ConcurrencyTree | str = None,
        matches: Set = None,
        length: int = 1,
        activities=None,
    ):
        self.positions = positions  # starting positions in concurrency tree
        # self.length = len(pattern.children) if pattern and pattern.op == cTreeOperator.Sequential else length # number of activities in repetition
        self.length = length
        self.pattern = repr(pattern)
        self.matches = (
            set(positions.dfs) if matches is None else matches
        )  # dfs ids of matches
        self.activities = activities
        self.size = len(activities)

    def __eq__(self, other):
        return (
            self.length == other.length
            and self.positions.__eq__(other.positions)
            and self.matches == other.matches
            and self.activities == other.activities
        )
        # return check_range_contains(tuple([x, x + self.length - 1] for x in self.positions), tuple([x, x + other.length - 1] for x in other.positions))

    def __hash__(self):
        return hash((self.positions, self.length))

    def __repr__(self):
        return f"Pair(positions:{self.positions}, length:{self.length}, matches:{self.matches}, pattern:{self.pattern})"

    def __equivalent__(self, other):
        return check_range_contains(
            tuple([x, x + self.length - 1] for x in self.positions.bfs),
            tuple([x, x + other.length - 1] for x in other.positions.bfs),
        )

    def __overlapping__(self):
        return self.positions.bfs[1] < self.positions.bfs[0] + self.length

    def serialize(self):
        return {
            "positions": self.positions.serialize(),
            "length": self.length,
            "matches": list(self.matches),
            "pattern": self.pattern,
            "activities": list(self.activities),
        }


def check_range_contains(range1: Tuple, range2: Tuple):
    """Checks if range2 contains range1 or vice versa"""
    for i in range(2):
        if range1[i][0] < range2[i][0] or range1[i][1] > range2[i][1]:
            for i in range(2):
                if range2[i][0] < range1[i][0] or range2[i][1] > range1[i][1]:
                    return False
    return True
