# Sunday Scorebook

Learn fantasy football from real data. A small command line tool (`ff`) and a web page for learning how fantasy football works using real NFL stats,
and for following a real league (ESPN or Sleeper) week by week.

## Setup

```bash
git clone https://github.com/paultimfv/fantasyfootball.git && cd fantasyfootball
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest            # 17 tests, all offline
```

## Commands

```bash
python -m ff learn                     # the whole glossary
python -m ff learn faab                # one term

python -m ff top                       # this week's top scorers (PPR)
python -m ff top --pos WR --format half
python -m ff explain "Jaxon Smith-Njigba"           # why he scored what he did
python -m ff explain "Tony Pollard" --season 2026 --week 7 --format standard

python -m ff espn --league 123456      # weekly recap of an ESPN league
python -m ff sleeper --find someusername   # list a Sleeper user's league ids
python -m ff sleeper --league 1234567890   # weekly recap of a Sleeper league
python -m ff trending                  # who everyone is adding on waivers right now
python -m ff trending drop
```

`explain` shows every scoring line, checks the total against nflverse's own fantasy points,
and tells you how much of the score came from touchdowns. That last number matters most:
TDs are the noisiest stat in football, while targets and carries repeat week to week.

The recap shows each matchup, the best starter on each team, points left on the bench
(the best lineup in hindsight minus what was actually started), and whether a loser
would have won with their best lineup. That's most of what a group chat argues about on Monday.

## Web page

```bash
python -m ff site                  # football page: public/index.html
python -m ff site --sport hockey   # hockey page:   public/hockey/index.html (NHL stats API)
```

One self-contained HTML file: weekly leaders split into volume vs touchdown points,
a per-player scoring breakdown and season chart, the rulebook and the glossary.
Open it in a browser. It scores in the browser from the same rules as `ff/scoring.py`,
so switching formats needs no rebuild.

## Hosting (Vercel)

`public/index.html` is committed, and `vercel.json` tells Vercel to serve `public/` as a
static site with no build step. Import this repo at vercel.com/new, name the project
`fantasy-league`, and every push to `main` redeploys.

The stats refresh themselves: `.github/workflows/refresh.yml` rebuilds the pages every
morning and commits them when anything changed, which triggers a redeploy. Run it by hand from the repo's Actions tab ("Refresh stats", Run workflow).

## Getting your friends' ESPN league

1. **League id**: the `leagueId=` number in the league's URL on fantasy.espn.com.
2. **Public league**: that's all you need.
3. **Private league** (the default): ESPN wants two cookies from a logged-in browser of
   someone *in* the league. Either ask the commissioner to make the league viewable to
   the public in the league settings, or get a league member to send you these from
   browser dev tools (Application > Cookies > espn.com):
   - `espn_s2`
   - `SWID` (including the curly braces)

   Put them in a `.env` file at the repo root (git ignores it):

   ```
   ESPN_LEAGUE_ID=123456
   ESPN_S2=AEB...long string...
   ESPN_SWID={XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
   ```

   Those cookies act as that person's ESPN login, so treat them like a password.

## Where the data comes from

| Source | What | Notes |
|---|---|---|
| [nflverse](https://github.com/nflverse/nflverse-data) via [nflreadpy](https://github.com/nflverse/nflreadpy) | Real weekly NFL player stats | Free, updated after games, cached on disk for 24h |
| [Sleeper API](https://docs.sleeper.com) | Sleeper leagues, trending adds/drops | Free, read-only, no key. Stay under 1000 calls/min |
| [espn-api](https://github.com/cwendt94/espn-api) | ESPN leagues | Community wrapper around ESPN's unofficial endpoints, can break if ESPN changes them |

## Layout

```
ff/scoring.py   scoring rules (standard, half, PPR) and the line-by-line breakdown
ff/stats.py     loads nflverse stats, explain + leaderboards
ff/lineup.py    slot rules and the optimal-lineup search
ff/recap.py     provider-neutral weekly recap
ff/espn.py      ESPN adapter
ff/sleeper.py   Sleeper adapter
ff/glossary.py  the vocabulary
ff/hockey.py    NHL stats API, ESPN hockey scoring, Monday-Sunday fantasy weeks
ff/site.py      builds the web pages (one template, a payload per sport)
ff/cli.py       commands
web/template.html  the web page (data is injected by site.py)
```

## Roadmap

- **Phase 2, analytics**: rolling target share and snap share, points vs projection,
  "sell high / buy low" flags for players whose TDs run ahead of or behind their volume.
- **Phase 3, simulator**: model each player's week as a distribution and run a Monte Carlo
  of every matchup for win probability, then the rest of the season for playoff odds.
- **Later**: a shareable, hosted version of the web page.
