"""Real NFL weekly stats from nflverse (via nflreadpy), plus explanations.

nflverse data: https://github.com/nflverse/nflverse-data
nflreadpy:     https://github.com/nflverse/nflreadpy
"""

from . import scoring

FANTASY_POSITIONS = {"QB", "RB", "WR", "TE"}


def load_week(season: int, week: int) -> list[dict]:
    import nflreadpy as nfl
    from nflreadpy.config import update_config

    update_config(cache_mode="filesystem")  # keep downloads on disk between runs
    df = nfl.load_player_stats(season, summary_level="week")
    return [r for r in df.to_dicts() if r.get("week") == week and r.get("season_type", "REG") in ("REG", "POST")]


def current() -> tuple[int, int]:
    import nflreadpy as nfl

    return nfl.get_current_season(), nfl.get_current_week()


def find(rows: list[dict], query: str) -> list[dict]:
    q = query.lower()
    exact = [r for r in rows if (r.get("player_display_name") or "").lower() == q]
    return exact or [r for r in rows if q in (r.get("player_display_name") or "").lower()]


def _fmt_count(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.1f}"


def explain(row: dict, fmt: str = "ppr") -> str:
    name = row.get("player_display_name") or row.get("player_name")
    out = [
        f"{name} ({row.get('position')}, {row.get('team')}) vs {row.get('opponent_team')}"
        f"  |  {row.get('season')} week {row.get('week')}  |  {fmt.upper()} scoring",
        "",
    ]
    lines = scoring.breakdown(row, fmt)
    for line in lines:
        out.append(f"  {_fmt_count(line.count):>5} {line.label:<28} x {line.per_unit:<5g} = {line.points:6.1f}")
    pts = scoring.total(row, fmt)
    out.append(f"  {'':>5} {'TOTAL':<28}           {pts:6.1f}")

    # Self-check against nflverse's own numbers, so you can trust the math.
    reference = {"standard": row.get("fantasy_points"), "ppr": row.get("fantasy_points_ppr")}.get(fmt)
    if reference is not None:
        mark = "matches" if abs(reference - pts) < 0.05 else "DIFFERS from"
        out.append(f"  ({mark} nflverse's {reference:.1f})")

    out.append("")
    out.append("  Usage (the part that predicts next week):")
    usage = []
    if row.get("attempts"):
        usage.append(f"{_fmt_count(row['completions'] or 0)}/{_fmt_count(row['attempts'])} passing")
    if row.get("carries"):
        usage.append(f"{_fmt_count(row['carries'])} carries")
    if row.get("targets"):
        share = row.get("target_share")
        share_txt = f" ({share:.0%} of team targets)" if share else ""
        usage.append(f"{_fmt_count(row['targets'])} targets{share_txt}")
    out.append("    " + (", ".join(usage) if usage else "no touches recorded"))

    share = scoring.td_share(row, fmt)
    if pts > 0:
        if share >= 0.5:
            verdict = "more than half from TDs: a boom week that is hard to repeat"
        elif share == 0:
            verdict = "zero TDs: all volume, the repeatable kind of production"
        else:
            verdict = "a mix of volume and TDs"
        out.append(f"    {share:.0%} of points from touchdowns, {verdict}")
    return "\n".join(out)


def leaders(rows: list[dict], fmt: str = "ppr", position: str | None = None, n: int = 10) -> str:
    pool = [r for r in rows if r.get("position") in FANTASY_POSITIONS]
    if position:
        pool = [r for r in pool if r.get("position") == position.upper()]
    ranked = sorted(pool, key=lambda r: scoring.total(r, fmt), reverse=True)[:n]
    out = [f"{'#':>2}  {'player':<26}{'pos':<4}{'team':<5}{'pts':>6}  {'TD share':>8}"]
    for i, r in enumerate(ranked, 1):
        out.append(
            f"{i:>2}  {r.get('player_display_name', '?'):<26}{r.get('position') or '':<4}{r.get('team') or '':<5}"
            f"{scoring.total(r, fmt):>6.1f}  {scoring.td_share(r, fmt):>8.0%}"
        )
    return "\n".join(out)
