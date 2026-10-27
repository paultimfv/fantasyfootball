"""Build the web version: real stats packed into self-contained HTML pages.

One template serves every sport. Each payload carries the sport's scoring
rules, wording and stats, and the page scores in the browser, so switching
formats needs no reload.
"""

import json
from datetime import date
from pathlib import Path

from . import glossary, hockey, scoring
from .stats import FANTASY_POSITIONS

TEMPLATE = Path(__file__).resolve().parent.parent / "web" / "template.html"
NAV = [("Football", "football"), ("Hockey", "hockey")]

# The template is a page body. Hosts like Vercel serve the file as-is, so it
# needs a real document around it, or browsers render it in quirks mode.
_DOC_START = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>body{margin:0}[hidden]{display:none!important}</style>
"""


def _nav(active: str) -> list:
    # football lives at the site root, every other sport in its own folder
    root = "./" if active == "football" else "../"
    return [[label, root if key == "football" else f"{root}{key}/", key == active] for label, key in NAV]


def football(season: int) -> dict:
    import nflreadpy as nfl
    from nflreadpy.config import update_config

    update_config(cache_mode="filesystem")
    rows = nfl.load_player_stats(season, summary_level="week").to_dicts()
    labels = [label for label, _, _ in scoring.FORMATS["ppr"]]
    per_fmt = {fmt: {label: pts for label, _, pts in rules} for fmt, rules in scoring.FORMATS.items()}
    rules = [{"label": l, "pts": {f: per_fmt[f].get(l, 0) for f in scoring.FORMATS}, "luck": "TD" in l} for l in labels]
    usage = [
        {"key": "attempts", "label": "pass attempts", "avg": True},
        {"key": "carries", "label": "carries", "avg": True},
        {"key": "targets", "label": "targets", "avg": True},
        {"key": "target_share", "label": "of team targets", "pct": True},
    ]
    players: dict[str, list] = {}
    out_rows = []
    weeks = set()
    for r in rows:
        if r.get("position") not in FANTASY_POSITIONS or r.get("season_type") not in ("REG", "POST"):
            continue
        counts = {line.label: line.count for line in scoring.breakdown(r, "ppr")}
        if not counts and not any(r.get(k) for k in ("targets", "carries", "attempts")):
            continue
        pid = r["player_id"]
        if pid not in players:
            players[pid] = [len(players), r.get("player_display_name") or r.get("player_name"), r["position"]]
        weeks.add(r["week"])
        out_rows.append(
            [players[pid][0], r["week"], r.get("team") or "", f"vs {r.get('opponent_team') or '?'}"]
            + [counts.get(l, 0) for l in labels]
            + [round(r[u["key"]], 3) if isinstance(r.get(u["key"]), float) else (r.get(u["key"]) or 0) for u in usage]
        )
    return {
        "sport": "football",
        "title": "Sunday Scorebook",
        "season_label": f"{season} season",
        "lede": "Every fantasy point from real NFL games, explained. Pick a week and a scoring format, then click "
        "any player to see exactly how his points added up and whether they came from volume (repeatable) or "
        "touchdowns (luck-heavy).",
        "luck_label": "touchdown points",
        "vol_label": "volume points",
        "luck_word": "touchdowns",
        "boom": "That's a boom week, and touchdowns are the hardest thing to repeat. Expect less next week unless "
        "his usage backs it up.",
        "zero": "No touchdowns: every point came from volume. That's the repeatable kind. If he scores a TD next "
        "week, he jumps.",
        "rule_intro": "Points per unit in each format. Your friends' league uses one of these, possibly with "
        "tweaks. The only difference between formats is catches.",
        "rule_note": "Rule of thumb: <b>targets and carries repeat week to week, touchdowns don't.</b> A player "
        "whose points are mostly orange had a lucky week. Mostly green means the opportunity is real.",
        "footnote": "Kickers and team defenses aren't included yet.",
        "source": ["nflverse", "https://github.com/nflverse/nflverse-data"],
        "formats": [["standard", "Standard"], ["half", "Half PPR"], ["ppr", "PPR"]],
        "default_fmt": "ppr",
        "positions": ["All", "QB", "RB", "WR", "TE"],
        "week_labels": {w: f"Week {w}" for w in sorted(weeks)},
        "rules": rules,
        "usage": usage,
        "players": [[name, pos] for _, name, pos in sorted(players.values())],
        "rows": out_rows,
        "glossary": glossary.TERMS,
        "nav": _nav("football"),
    }


def hockey_payload(start_year: int) -> dict:
    weekly, opening = hockey.by_week(hockey.game_rows(start_year))
    players: dict[int, list] = {}
    out_rows = []
    for w in weekly:
        pid = w["player_id"]
        if pid not in players:
            players[pid] = [len(players), w["name"], w["position"]]
        out_rows.append(
            [players[pid][0], w["week"], w["team"], f"{w['games']} game{'s' if w['games'] != 1 else ''}"]
            + [w[stat] for _, stat, _, _ in hockey.RULES]
            + [w["games"], w["shots"]]
        )
    weeks = sorted({w["week"] for w in weekly})
    return {
        "sport": "hockey",
        "title": "Saturday Night Scorebook",
        "season_label": f"{start_year}-{str(start_year + 1)[2:]} season",
        "lede": "Every fantasy point from real NHL games, explained. Fantasy hockey weeks run Monday to Sunday, so "
        "a player's week adds up all his games. Click anyone to see where the points came from: steady work "
        "(shots, assists, hits, blocks, saves) or the streaky stuff (goals and goalie wins).",
        "luck_label": "goal & win points",
        "vol_label": "shots, assists, hits, blocks, saves",
        "luck_word": "goals and wins",
        "boom": "Goals ride on shooting percentage, which swings a lot over a few games, and wins depend on the "
        "whole team. Expect some of this to fade unless the shots keep coming.",
        "zero": "No goals or wins: every point came from steady work. That's the repeatable kind, and the goals "
        "usually follow the shots.",
        "rule_intro": "Points per unit. ESPN's default is the most common points setup. The NHL column is "
        "plain hockey points (goals plus assists), the scoring you already know.",
        "rule_note": "Rule of thumb: <b>shots repeat, shooting percentage doesn't.</b> A forward scoring on 25% "
        "of his shots will cool off. One getting 4 shots a night with no goals is due.",
        "footnote": "Regular season only. Many hockey leagues use categories instead of points: see the glossary.",
        "source": ["NHL stats API", "https://www.nhl.com/stats/"],
        "formats": [[k, label] for k, label in hockey.FORMATS],
        "default_fmt": "espn",
        "positions": ["All", "C", "LW", "RW", "D", "G"],
        "week_labels": {w: hockey.week_label(w, opening) for w in weeks} if opening else {},
        "rules": [{"label": l, "pts": pts, "luck": luck} for l, _, pts, luck in hockey.RULES],
        "usage": [{"key": "games", "label": "games", "games": True}, {"key": "shots", "label": "shots", "avg": True}],
        "players": [[name, pos] for _, name, pos in sorted(players.values())],
        "rows": out_rows,
        "glossary": glossary.HOCKEY_TERMS,
        "nav": _nav("hockey"),
    }


def build(payload: dict, out: Path, standalone: bool = True) -> Path:
    payload = {**payload, "built": date.today().isoformat()}
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    html = html.replace("<title>Sunday Scorebook</title>", f"<title>{payload['title']}</title>", 1)
    if standalone:
        html = _DOC_START + html + "\n</html>\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out
