"""Sleeper's free, read-only API. No login or key needed.

Docs: https://docs.sleeper.com  (keep under 1000 calls a minute)
"""

import json
import time
import urllib.request
from pathlib import Path

from .lineup import RosterPlayer
from .recap import Matchup, TeamWeek

BASE = "https://api.sleeper.app/v1"
CACHE = Path.home() / ".cache" / "ff"


def get(path: str):
    req = urllib.request.Request(f"{BASE}{path}", headers={"User-Agent": "ff-learner"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def nfl_state() -> dict:
    """Current season and week according to Sleeper."""
    return get("/state/nfl")


def players() -> dict:
    """Every NFL player keyed by Sleeper player id. About 5 MB, so it is
    cached for a day as Sleeper asks."""
    path = CACHE / "sleeper_players.json"
    if path.exists() and time.time() - path.stat().st_mtime < 86400:
        return json.loads(path.read_text())
    data = get("/players/nfl")
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def trending(kind: str = "add", hours: int = 24, limit: int = 15) -> list[dict]:
    """Who everyone on Sleeper is adding or dropping right now."""
    return get(f"/players/nfl/trending/{kind}?lookback_hours={hours}&limit={limit}")


def player_name(pid: str, db: dict) -> tuple[str, str]:
    p = db.get(pid)
    if p is None:  # team defenses use the team abbreviation as their id
        return (f"{pid} D/ST", "DEF")
    name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
    return (name or pid, p.get("position") or "?")


def build_matchups(raw_matchups: list[dict], rosters: list[dict], users: list[dict], db: dict) -> list[Matchup]:
    """Turn Sleeper's /matchups, /rosters and /users responses into Matchups."""
    owner_of_roster = {r["roster_id"]: r.get("owner_id") for r in rosters}
    team_of_user = {}
    for u in users:
        meta = u.get("metadata") or {}
        team_of_user[u["user_id"]] = meta.get("team_name") or u.get("display_name") or u["user_id"]

    teams_by_matchup: dict[int, list[TeamWeek]] = {}
    for m in raw_matchups:
        if m.get("matchup_id") is None:  # bye week or eliminated in playoffs
            continue
        starters = set(m.get("starters") or [])
        points = m.get("players_points") or {}
        roster = []
        for pid in m.get("players") or []:
            name, pos = player_name(pid, db)
            roster.append(RosterPlayer(name, pos, "START" if pid in starters else "BN", float(points.get(pid, 0))))
        owner = owner_of_roster.get(m["roster_id"])
        name = team_of_user.get(owner, f"Team {m['roster_id']}")
        teams_by_matchup.setdefault(m["matchup_id"], []).append(TeamWeek(name, float(m.get("points") or 0), roster))

    return [Matchup(*pair) for pair in teams_by_matchup.values() if len(pair) == 2]


def load_week(league_id: str, week: int) -> tuple[list[Matchup], list[str], dict]:
    league = get(f"/league/{league_id}")
    raw = get(f"/league/{league_id}/matchups/{week}")
    rosters = get(f"/league/{league_id}/rosters")
    users = get(f"/league/{league_id}/users")
    return build_matchups(raw, rosters, users, players()), league["roster_positions"], league


def find_leagues(username: str, season: int) -> list[dict]:
    user = get(f"/user/{username}")
    if not user:
        raise SystemExit(f"no Sleeper user called {username!r}")
    return get(f"/user/{user['user_id']}/leagues/nfl/{season}")
