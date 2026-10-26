"""Fantasy scoring rules and a line-by-line points breakdown.

Stat names follow nflverse weekly player stats, which is also what most
fantasy apps use under the hood. A rule is (label, stat columns, points per unit).
Several columns can feed one rule, e.g. fumbles lost on runs, catches and sacks.
"""

from dataclasses import dataclass

# Standard scoring, the base every format starts from (ESPN's defaults match).
_BASE = [
    ("passing yards", ["passing_yards"], 0.04),  # 1 pt per 25 yards
    ("passing TDs", ["passing_tds"], 4),
    ("interceptions thrown", ["passing_interceptions", "interceptions"], -2),
    ("rushing yards", ["rushing_yards"], 0.1),  # 1 pt per 10 yards
    ("rushing TDs", ["rushing_tds"], 6),
    ("receiving yards", ["receiving_yards"], 0.1),
    ("receiving TDs", ["receiving_tds"], 6),
    ("fumbles lost", ["rushing_fumbles_lost", "receiving_fumbles_lost", "sack_fumbles_lost"], -2),
    ("2-pt conversions", ["passing_2pt_conversions", "rushing_2pt_conversions", "receiving_2pt_conversions"], 2),
    ("return / special teams TDs", ["special_teams_tds"], 6),
]

FORMATS = {
    "standard": _BASE,
    "half": _BASE + [("receptions", ["receptions"], 0.5)],
    "ppr": _BASE + [("receptions", ["receptions"], 1.0)],
}

# Columns where an old nflverse name and a new one mean the same thing:
# only count the first one present so a row never gets double-counted.
_ALIASES = {"passing_interceptions", "interceptions"}


@dataclass
class Line:
    label: str
    count: float
    per_unit: float

    @property
    def points(self) -> float:
        return self.count * self.per_unit


def _stat(row: dict, col: str) -> float:
    value = row.get(col)
    return float(value) if value is not None else 0.0


def breakdown(row: dict, fmt: str = "ppr") -> list[Line]:
    """Every scoring rule that produced points for this stat row."""
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}, pick one of {', '.join(FORMATS)}")
    lines = []
    for label, cols, per_unit in FORMATS[fmt]:
        if set(cols) <= _ALIASES:
            present = [c for c in cols if row.get(c) is not None]
            count = _stat(row, present[0]) if present else 0.0
        else:
            count = sum(_stat(row, c) for c in cols)
        if count:
            lines.append(Line(label, count, per_unit))
    return lines


def total(row: dict, fmt: str = "ppr") -> float:
    return round(sum(line.points for line in breakdown(row, fmt)), 2)


def td_share(row: dict, fmt: str = "ppr") -> float:
    """Fraction of a player's points that came from touchdowns.

    High TD share means the week was driven by the noisiest stat in football,
    so it is a weak signal for next week. Volume (catches, yards) repeats more.
    """
    lines = breakdown(row, fmt)
    pts = sum(line.points for line in lines)
    if pts <= 0:
        return 0.0
    td_pts = sum(line.points for line in lines if "TD" in line.label)
    return td_pts / pts
