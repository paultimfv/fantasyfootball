"""ESPN fantasy leagues, through the community espn-api package.

ESPN has no official public API. espn-api wraps the endpoints the ESPN site
itself calls. Public leagues need only the league id. Private leagues also
need two cookies from a logged-in browser: espn_s2 and SWID (see README).
"""

import os

from .lineup import RosterPlayer
from .recap import Matchup, TeamWeek


def league(league_id: int, season: int):
    from espn_api.football import League

    return League(
        league_id=league_id,
        year=season,
        espn_s2=os.environ.get("ESPN_S2"),
        swid=os.environ.get("ESPN_SWID"),
    )


def slots_from_counts(counts: dict[str, int]) -> list[str]:
    """ESPN gives {'QB': 1, 'RB': 2, 'RB/WR/TE': 1, 'BE': 7, ...}."""
    return [slot for slot, n in counts.items() for _ in range(n)]


def _team(team, score, projected, lineup) -> TeamWeek:
    name = getattr(team, "team_name", None) or str(team)
    roster = [RosterPlayer(p.name, p.position, p.slot_position, float(p.points or 0), p.projected_points) for p in lineup]
    return TeamWeek(name, float(score or 0), roster, projected)


def load_week(lg, week: int) -> tuple[list[Matchup], list[str]]:
    out = []
    for box in lg.box_scores(week):
        if not box.away_team:  # playoff bye
            continue
        out.append(
            Matchup(
                _team(box.home_team, box.home_score, box.home_projected, box.home_lineup),
                _team(box.away_team, box.away_score, box.away_projected, box.away_lineup),
            )
        )
    return out, slots_from_counts(lg.settings.position_slot_counts)


def scoring_format(lg) -> str:
    """Best guess at standard / half / ppr from the league's reception points."""
    for item in lg.settings.scoring_format:
        if item.get("abbr") == "REC":
            return {0.5: "half", 1.0: "ppr"}.get(float(item["points"]), "standard")
    return "standard"
