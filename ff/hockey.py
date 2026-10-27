"""Fantasy hockey from the NHL's own stats API (the one NHL.com uses, no key needed).

Each fantasy week runs Monday to Sunday, like ESPN and Yahoo head-to-head
matchups, so a player's week is the sum of however many games he played.
"""

import json
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

BASE = "https://api.nhle.com/stats/rest/en"

# (label, NHL API stat, points per format, luck?)
# "luck" marks points that swing a lot from week to week: goals ride on
# shooting percentage, wins and shutouts on the whole team in front of the goalie.
RULES = [
    ("goals", "goals", {"espn": 2, "nhl": 1}, True),
    ("assists", "assists", {"espn": 1, "nhl": 1}, False),
    ("power-play points", "ppPoints", {"espn": 0.5, "nhl": 0}, False),
    ("shorthanded points", "shPoints", {"espn": 0.5, "nhl": 0}, False),
    ("shots on goal", "shots", {"espn": 0.1, "nhl": 0}, False),
    ("hits", "hits", {"espn": 0.1, "nhl": 0}, False),
    ("blocked shots", "blockedShots", {"espn": 0.5, "nhl": 0}, False),
    ("goalie wins", "wins", {"espn": 4, "nhl": 0}, True),
    ("saves", "saves", {"espn": 0.2, "nhl": 0}, False),
    ("goals against", "goalsAgainst", {"espn": -2, "nhl": 0}, False),
    ("shutouts", "shutouts", {"espn": 3, "nhl": 0}, True),
    ("overtime losses", "otLosses", {"espn": 1, "nhl": 0}, True),
]
FORMATS = [("espn", "ESPN points"), ("nhl", "NHL points (G+A)")]
STAT_KEYS = [stat for _, stat, _, _ in RULES]
POSITIONS = {"C": "C", "L": "LW", "R": "RW", "D": "D", "G": "G"}


def season_id(start_year: int) -> str:
    return f"{start_year}{start_year + 1}"


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "sunday-scorebook"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2**attempt)


def fetch_report(report: str, start_year: int, page: int = 100) -> list[dict]:
    """Every per-game row of one NHL stats report for the regular season."""
    sort = json.dumps([{"property": "gameId", "direction": "ASC"}, {"property": "playerId", "direction": "ASC"}])
    where = f"seasonId={season_id(start_year)} and gameTypeId=2"
    rows: list[dict] = []
    while True:
        query = urllib.parse.urlencode(
            {"isAggregate": "false", "isGame": "true", "start": len(rows), "limit": page, "sort": sort, "cayenneExp": where}
        )
        batch = _get(f"{BASE}/{report}?{query}").get("data", [])
        rows += batch
        if len(batch) < page:
            return rows


def game_rows(start_year: int) -> list[dict]:
    """One row per player per game, skaters and goalies, in a common shape."""
    realtime = {(r["playerId"], r["gameId"]): r for r in fetch_report("skater/realtime", start_year)}
    out = []
    for r in fetch_report("skater/summary", start_year):
        extra = realtime.get((r["playerId"], r["gameId"]), {})
        out.append(_row(r, r.get("skaterFullName"), r.get("positionCode"), {**r, **{k: extra.get(k) for k in ("hits", "blockedShots")}}))
    for r in fetch_report("goalie/summary", start_year):
        out.append(_row(r, r.get("goalieFullName"), "G", r))
    return out


def _row(r: dict, name, pos, stats: dict) -> dict:
    return {
        "player_id": r["playerId"],
        "name": name or str(r["playerId"]),
        "position": POSITIONS.get(pos, pos or "?"),
        "team": r.get("teamAbbrev") or "",
        "date": r["gameDate"][:10],
        **{k: stats.get(k) or 0 for k in STAT_KEYS},
    }


def week_of(day: date, opening: date) -> int:
    """Fantasy week number. Weeks run Monday to Sunday; week 1 holds opening night."""
    first_monday = opening - timedelta(days=opening.weekday())
    return (day - first_monday).days // 7 + 1


def week_label(week: int, opening: date) -> str:
    monday = opening - timedelta(days=opening.weekday()) + timedelta(weeks=week - 1)
    sunday = monday + timedelta(days=6)
    return f"{monday:%b} {monday.day} to {sunday:%b} {sunday.day}"


def by_week(games: list[dict]) -> tuple[list[dict], date | None]:
    """Sum each player's games into fantasy weeks."""
    if not games:
        return [], None
    opening = min(date.fromisoformat(g["date"]) for g in games)
    weeks: dict[tuple, dict] = {}
    for g in sorted(games, key=lambda g: g["date"]):
        key = (g["player_id"], week_of(date.fromisoformat(g["date"]), opening))
        w = weeks.setdefault(key, {"player_id": g["player_id"], "name": g["name"], "position": g["position"],
                                   "week": key[1], "games": 0, **{k: 0 for k in STAT_KEYS}})
        w["games"] += 1
        w["team"] = g["team"]  # latest team, in case of a trade mid-week
        for k in STAT_KEYS:
            w[k] += g[k]
    return list(weeks.values()), opening


def points(row: dict, fmt: str = "espn") -> float:
    return round(sum(row.get(stat, 0) * pts[fmt] for _, stat, pts, _ in RULES), 2)
