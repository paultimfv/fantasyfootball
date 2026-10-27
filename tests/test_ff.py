import pytest

from ff import glossary, scoring
from ff.espn import slots_from_counts
from ff.lineup import RosterPlayer, optimal_points
from ff.recap import Matchup, TeamWeek, recap
from ff.sleeper import build_matchups

WR_LINE = {"receptions": 6, "receiving_yards": 84, "receiving_tds": 1}


@pytest.mark.parametrize("fmt,expected", [("standard", 14.4), ("half", 17.4), ("ppr", 20.4)])
def test_wr_scoring_by_format(fmt, expected):
    assert scoring.total(WR_LINE, fmt) == expected


def test_qb_scoring():
    qb = {"passing_yards": 300, "passing_tds": 2, "passing_interceptions": 1, "rushing_yards": 20}
    # 300/25 + 2*4 - 2 + 20/10
    assert scoring.total(qb, "ppr") == 20.0


def test_old_and_new_interception_columns_not_double_counted():
    assert scoring.total({"passing_interceptions": 1, "interceptions": 1}) == -2


def test_fumbles_from_every_source_count():
    row = {"rushing_fumbles_lost": 1, "receiving_fumbles_lost": 1, "sack_fumbles_lost": 1}
    assert scoring.total(row) == -6


def test_missing_and_null_stats_are_zero():
    assert scoring.total({"receptions": None}) == 0
    assert scoring.breakdown({}) == []


def test_td_share():
    # 6 of 20.4 PPR points came from the TD
    assert scoring.td_share(WR_LINE, "ppr") == pytest.approx(6 / 20.4)
    assert scoring.td_share({}, "ppr") == 0


def test_unknown_format():
    with pytest.raises(ValueError):
        scoring.total(WR_LINE, "six-point-passing")


def p(name, pos, pts, slot="BN"):
    return RosterPlayer(name, pos, slot, pts)


def test_optimal_lineup_uses_flex_for_best_leftover():
    roster = [p("rb1", "RB", 20), p("rb2", "RB", 5), p("wr1", "WR", 10), p("wr2", "WR", 8)]
    # RB 20 + WR 10 + FLEX takes WR 8 over RB 5
    assert optimal_points(roster, ["RB", "WR", "FLEX", "BN", "BN"]) == 38


def test_optimal_lineup_handles_overlapping_flex_slots():
    # A greedy fill that puts the WR in RB/WR first only gets 25. The real best is 35.
    roster = [p("wr", "WR", 20), p("te", "TE", 5), p("rb", "RB", 15)]
    assert optimal_points(roster, ["RB/WR", "WR/TE"]) == 35


def test_optimal_lineup_maps_espn_and_sleeper_defense_names():
    assert optimal_points([p("Bears", "D/ST", 9)], ["DEF"]) == 9
    assert optimal_points([p("CHI", "DEF", 9)], ["D/ST"]) == 9


def test_optimal_lineup_leaves_slot_empty_rather_than_negative():
    assert optimal_points([p("k", "K", -3)], ["K"]) == 0


def _team(name, starters, bench):
    roster = [p(n, pos, pts, "START") for n, pos, pts in starters] + [p(n, pos, pts) for n, pos, pts in bench]
    return TeamWeek(name, sum(pts for *_, pts in starters), roster)


def test_recap_flags_a_loser_who_benched_the_win():
    slots = ["QB", "RB", "WR"]
    alice = _team("Alice", [("q", "QB", 20), ("r", "RB", 15), ("w", "WR", 10)], [])
    bob = _team("Bob", [("q", "QB", 18), ("r", "RB", 2), ("w", "WR", 12)], [("bench rb", "RB", 25)])
    text = str(recap([Matchup(alice, bob)], slots, week=8))
    assert "Alice 45.0  beat  Bob 32.0" in text
    assert "left 23.0 pts on the bench" in text
    assert "Bob would have WON" in text
    assert "Worst lineup decisions: Bob" in text


def test_sleeper_matchups_are_paired_and_named():
    db = {"1": {"full_name": "Star RB", "position": "RB"}, "2": {"full_name": "Bench WR", "position": "WR"}}
    raw = [
        {"roster_id": 1, "matchup_id": 1, "points": 30.5, "starters": ["1", "CHI"], "players": ["1", "2", "CHI"],
         "players_points": {"1": 22.5, "2": 14, "CHI": 8}},
        {"roster_id": 2, "matchup_id": 1, "points": 28, "starters": [], "players": [], "players_points": {}},
        {"roster_id": 3, "matchup_id": None, "points": 0},  # bye
    ]
    rosters = [{"roster_id": 1, "owner_id": "u1"}, {"roster_id": 2, "owner_id": "u2"}]
    users = [{"user_id": "u1", "display_name": "pt", "metadata": {"team_name": "Paul's Picks"}},
             {"user_id": "u2", "display_name": "friend"}]
    [m] = build_matchups(raw, rosters, users, db)
    assert (m.a.name, m.b.name) == ("Paul's Picks", "friend")
    by_name = {r.name: r for r in m.a.roster}
    assert by_name["Star RB"].started and not by_name["Bench WR"].started
    assert by_name["CHI D/ST"].position == "DEF"


def test_espn_slot_counts_expand():
    assert slots_from_counts({"QB": 1, "RB": 2, "BE": 1, "TE": 0}) == ["QB", "RB", "RB", "BE"]


def test_glossary_lookup():
    assert "Reception" in glossary.show("ppr")
    assert "No entry" in glossary.show("zzz")


# hockey

from datetime import date

from ff import hockey


def test_hockey_espn_and_nhl_points():
    skater = {"goals": 1, "assists": 2, "ppPoints": 1, "shots": 5, "hits": 3, "blockedShots": 2}
    # 2 + 2 + 0.5 + 0.5 + 0.3 + 1.0
    assert hockey.points(skater, "espn") == 6.3
    assert hockey.points(skater, "nhl") == 3  # plain goals + assists


def test_hockey_goalie_points():
    goalie = {"wins": 1, "saves": 30, "goalsAgainst": 2, "shutouts": 0}
    assert hockey.points(goalie, "espn") == 4 + 6 - 4
    assert hockey.points(goalie, "nhl") == 0


def test_fantasy_weeks_run_monday_to_sunday():
    opening = date(2026, 10, 7)  # a Wednesday
    assert hockey.week_of(date(2026, 10, 11), opening) == 1  # Sunday, same week
    assert hockey.week_of(date(2026, 10, 12), opening) == 2  # Monday starts week 2
    assert hockey.week_label(1, opening) == "Oct 5 to Oct 11"


def _game(pid, day, **stats):
    return {"player_id": pid, "name": f"P{pid}", "position": "C", "team": "TOR", "date": day,
            **{k: stats.get(k, 0) for k in hockey.STAT_KEYS}}


def test_games_are_summed_into_weeks():
    games = [_game(1, "2026-10-07", goals=1, shots=3), _game(1, "2026-10-09", shots=4),
             _game(1, "2026-10-13", assists=1), _game(2, "2026-10-08", hits=5)]
    weekly, opening = hockey.by_week(games)
    assert opening == date(2026, 10, 7)
    w1 = next(w for w in weekly if w["player_id"] == 1 and w["week"] == 1)
    assert (w1["games"], w1["goals"], w1["shots"]) == (2, 1, 7)
    assert next(w for w in weekly if w["player_id"] == 1 and w["week"] == 2)["assists"] == 1
    assert hockey.by_week([]) == ([], None)


def test_hockey_api_rows_are_normalized():
    api = {"playerId": 8478402, "gameId": 2026020001, "gameDate": "2026-10-07", "teamAbbrev": "EDM",
           "goals": 2, "assists": None}
    row = hockey._row(api, "Connor McDavid", "C", api)
    assert row["position"] == "C" and row["assists"] == 0 and row["goals"] == 2 and row["date"] == "2026-10-07"
    assert hockey._row(api, None, "L", api)["position"] == "LW"
