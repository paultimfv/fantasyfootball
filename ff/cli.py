"""Command line entry point: python -m ff <command> --help"""

import argparse
import os
import sys
from pathlib import Path

from . import glossary, recap


def _load_dotenv() -> None:
    """Read KEY=value lines from fantasy/.env so cookies stay out of your shell history."""
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def _season_week(args) -> tuple[int, int]:
    if args.season and args.week:
        return args.season, args.week
    from . import stats

    season, week = stats.current()
    return args.season or season, args.week or week


def cmd_learn(args) -> None:
    print(glossary.show(args.term))


def cmd_explain(args) -> None:
    from . import stats

    season, week = _season_week(args)
    hits = stats.find(stats.load_week(season, week), args.player)
    if not hits:
        sys.exit(f"No stats for {args.player!r} in {season} week {week}. Did he play? Check spelling.")
    if len(hits) > 1:
        names = ", ".join(sorted({h.get("player_display_name") for h in hits}))
        sys.exit(f"Several matches, be more specific: {names}")
    print(stats.explain(hits[0], args.format))


def cmd_top(args) -> None:
    from . import stats

    season, week = _season_week(args)
    print(f"{season} week {week} top scorers, {args.format.upper()}\n")
    print(stats.leaders(stats.load_week(season, week), args.format, args.pos, args.n))


def cmd_espn(args) -> None:
    from . import espn

    league_id = args.league or os.environ.get("ESPN_LEAGUE_ID")
    if not league_id:
        sys.exit("Pass --league or set ESPN_LEAGUE_ID (the leagueId= number in your league's URL).")
    season = args.season or _season_week(args)[0]
    lg = espn.league(int(league_id), season)
    week = args.week or lg.current_week
    matchups, slots = espn.load_week(lg, week)
    print(f"{lg.settings.name}  |  scoring looks like {espn.scoring_format(lg).upper()}\n")
    print(recap.recap(matchups, slots, week))


def cmd_sleeper(args) -> None:
    from . import sleeper

    if args.find:
        season = args.season or int(sleeper.nfl_state()["season"])
        for lg in sleeper.find_leagues(args.find, season):
            print(f"{lg['league_id']}  {lg['name']}")
        return
    league_id = args.league or os.environ.get("SLEEPER_LEAGUE_ID")
    if not league_id:
        sys.exit("Pass --league, set SLEEPER_LEAGUE_ID, or use --find <username> to list leagues.")
    week = args.week or int(sleeper.nfl_state()["week"])
    matchups, slots, league = sleeper.load_week(league_id, week)
    print(f"{league['name']}\n")
    print(recap.recap(matchups, slots, week))


def cmd_trending(args) -> None:
    from . import sleeper

    db = sleeper.players()
    print(f"Most {'added' if args.kind == 'add' else 'dropped'} on Sleeper, last {args.hours}h:\n")
    for t in sleeper.trending(args.kind, args.hours, args.n):
        name, pos = sleeper.player_name(t["player_id"], db)
        team = (db.get(t["player_id"]) or {}).get("team") or ""
        print(f"  {t['count']:>7,}  {name} ({pos} {team})")


def cmd_site(args) -> None:
    from datetime import date

    from . import site

    if args.sport == "hockey":
        today = date.today()
        # NHL seasons start in October and are named by their starting year
        start = args.season or (today.year if today.month >= 9 else today.year - 1)
        payload = site.hockey_payload(start)
    else:
        payload = site.football(args.season or _season_week(args)[0])
    out = Path(args.out or ("public/index.html" if args.sport == "football" else f"public/{args.sport}/index.html"))
    print(f"wrote {site.build(payload, out, standalone=not args.fragment)}")


def main(argv=None) -> None:
    _load_dotenv()
    p = argparse.ArgumentParser(prog="ff", description="Learn fantasy football from real data.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_when(sp):
        sp.add_argument("--season", type=int)
        sp.add_argument("--week", type=int)

    def add_format(sp):
        sp.add_argument("--format", choices=["standard", "half", "ppr"], default="ppr")

    sp = sub.add_parser("learn", help="glossary of fantasy terms")
    sp.add_argument("term", nargs="?")
    sp.set_defaults(fn=cmd_learn)

    sp = sub.add_parser("explain", help="why a player scored what he did")
    sp.add_argument("player")
    add_when(sp)
    add_format(sp)
    sp.set_defaults(fn=cmd_explain)

    sp = sub.add_parser("top", help="top fantasy scorers of a week")
    sp.add_argument("--pos", choices=["QB", "RB", "WR", "TE"])
    sp.add_argument("-n", type=int, default=15)
    add_when(sp)
    add_format(sp)
    sp.set_defaults(fn=cmd_top)

    sp = sub.add_parser("espn", help="weekly recap of an ESPN league")
    sp.add_argument("--league")
    add_when(sp)
    sp.set_defaults(fn=cmd_espn)

    sp = sub.add_parser("sleeper", help="weekly recap of a Sleeper league")
    sp.add_argument("--league")
    sp.add_argument("--find", metavar="USERNAME", help="list a user's leagues to get the id")
    add_when(sp)
    sp.set_defaults(fn=cmd_sleeper)

    sp = sub.add_parser("trending", help="who people are adding or dropping (Sleeper)")
    sp.add_argument("kind", nargs="?", choices=["add", "drop"], default="add")
    sp.add_argument("--hours", type=int, default=24)
    sp.add_argument("-n", type=int, default=15)
    sp.set_defaults(fn=cmd_trending)

    sp = sub.add_parser("site", help="build the web page with the latest stats")
    sp.add_argument("--sport", choices=["football", "hockey"], default="football")
    sp.add_argument("--season", type=int, help="for hockey, the year the season starts")
    sp.add_argument("--week", type=int, help=argparse.SUPPRESS)
    sp.add_argument("--out", help="default: public/index.html, or public/<sport>/index.html (public/ is what Vercel serves)")
    sp.add_argument("--fragment", action="store_true", help="page body only, for hosts that add their own <html>")
    sp.set_defaults(fn=cmd_site)

    args = p.parse_args(argv)
    args.fn(args)
