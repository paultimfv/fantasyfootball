"""Build the web version: real stats packed into one self-contained HTML page.

The page does its own scoring in the browser, from the same rules as scoring.py,
so switching between standard / half / PPR needs no reload.
"""

import json
from datetime import date
from pathlib import Path

from . import glossary, scoring
from .stats import FANTASY_POSITIONS

TEMPLATE = Path(__file__).resolve().parent.parent / "web" / "template.html"
USAGE = ["targets", "target_share", "carries", "attempts", "completions"]


def _rules() -> list[dict]:
    """One entry per scoring line, with its points in each format."""
    labels = [label for label, _, _ in scoring.FORMATS["ppr"]]
    per_fmt = {fmt: {label: pts for label, _, pts in rules} for fmt, rules in scoring.FORMATS.items()}
    return [{"label": label, "pts": {fmt: per_fmt[fmt].get(label, 0) for fmt in scoring.FORMATS}} for label in labels]


def payload(season: int) -> dict:
    import nflreadpy as nfl
    from nflreadpy.config import update_config

    update_config(cache_mode="filesystem")
    rows = nfl.load_player_stats(season, summary_level="week").to_dicts()
    rules = _rules()
    players: dict[str, list] = {}
    out_rows = []
    for r in rows:
        if r.get("position") not in FANTASY_POSITIONS or r.get("season_type") not in ("REG", "POST"):
            continue
        counts = {line.label: line.count for line in scoring.breakdown(r, "ppr")}
        touches = any(r.get(k) for k in ("targets", "carries", "attempts"))
        if not counts and not touches:
            continue
        pid = r["player_id"]
        if pid not in players:
            players[pid] = [len(players), r.get("player_display_name") or r.get("player_name"), r["position"]]
        usage = [round(r[k], 3) if isinstance(r.get(k), float) else (r.get(k) or 0) for k in USAGE]
        out_rows.append(
            [players[pid][0], r["week"], r.get("team") or "", r.get("opponent_team") or ""]
            + [counts.get(rule["label"], 0) for rule in rules]
            + usage
        )
    return {
        "season": season,
        "built": date.today().isoformat(),
        "rules": rules,
        "usage": USAGE,
        "players": [[name, pos] for _, name, pos in sorted(players.values())],
        "rows": out_rows,
        "glossary": glossary.TERMS,
    }


def build(season: int, out: Path) -> Path:
    data = json.dumps(payload(season), separators=(",", ":"))
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return out
