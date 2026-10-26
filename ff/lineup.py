"""Lineup slots and the best possible lineup in hindsight.

"He left 30 points on his bench" means: the optimal lineup from the same
roster would have scored 30 more than what was actually started.
"""

from dataclasses import dataclass

# Which real positions can fill each slot. Covers ESPN and Sleeper slot names.
SLOT_ELIGIBILITY = {
    "QB": {"QB"},
    "RB": {"RB"},
    "WR": {"WR"},
    "TE": {"TE"},
    "K": {"K"},
    "DEF": {"DEF"},
    "D/ST": {"DEF"},
    "FLEX": {"RB", "WR", "TE"},
    "RB/WR/TE": {"RB", "WR", "TE"},
    "RB/WR": {"RB", "WR"},
    "WRRB_FLEX": {"RB", "WR"},
    "WR/TE": {"WR", "TE"},
    "REC_FLEX": {"WR", "TE"},
    "OP": {"QB", "RB", "WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
}

BENCH_SLOTS = {"BE", "BN", "IR", "TAXI"}


def normalize_position(pos: str) -> str:
    return "DEF" if pos in {"D/ST", "DST", "DEF"} else pos


@dataclass
class RosterPlayer:
    name: str
    position: str
    slot: str  # where the manager actually put him this week
    points: float
    projected: float | None = None

    @property
    def started(self) -> bool:
        return self.slot not in BENCH_SLOTS


def optimal_points(players: list[RosterPlayer], slots: list[str]) -> float:
    """Highest score this roster could have put up with the given starting slots.

    Exact search, not a greedy fill: greedy can go wrong when flex slots overlap
    (a WR/TE and an RB/WR slot competing for the same WR). It stays small
    because only the top N players eligible for some slot can ever start,
    where N is the number of starting slots.
    """
    starting = [s for s in slots if s not in BENCH_SLOTS and s in SLOT_ELIGIBILITY]
    n = len(starting)
    pool: list[RosterPlayer] = []
    for allowed in {frozenset(SLOT_ELIGIBILITY[s]) for s in starting}:
        eligible = [p for p in players if normalize_position(p.position) in allowed]
        for p in sorted(eligible, key=lambda p: p.points, reverse=True)[:n]:
            if not any(p is q for q in pool):
                pool.append(p)

    memo: dict[tuple[int, int], float] = {}

    def best(slot_i: int, used: int) -> float:
        if slot_i == n:
            return 0.0
        key = (slot_i, used)
        if key not in memo:
            allowed = SLOT_ELIGIBILITY[starting[slot_i]]
            result = best(slot_i + 1, used)  # slot left empty
            for j, p in enumerate(pool):
                if not used >> j & 1 and normalize_position(p.position) in allowed:
                    result = max(result, p.points + best(slot_i + 1, used | 1 << j))
            memo[key] = result
        return memo[key]

    return round(best(0, 0), 2)
