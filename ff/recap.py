"""Provider-neutral weekly league recap.

ESPN and Sleeper adapters both turn their data into Matchup objects, and
everything here works the same regardless of where the league lives.
"""

from dataclasses import dataclass, field

from .lineup import RosterPlayer, optimal_points


@dataclass
class TeamWeek:
    name: str
    score: float
    roster: list[RosterPlayer]
    projected: float | None = None

    def starters(self) -> list[RosterPlayer]:
        return [p for p in self.roster if p.started]

    def bench(self) -> list[RosterPlayer]:
        return [p for p in self.roster if not p.started]


@dataclass
class Matchup:
    a: TeamWeek
    b: TeamWeek


@dataclass
class WeekRecap:
    week: int
    lines: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(self.lines)


def _best(players: list[RosterPlayer]) -> RosterPlayer | None:
    return max(players, key=lambda p: p.points, default=None)


def recap(matchups: list[Matchup], slots: list[str], week: int) -> WeekRecap:
    out = WeekRecap(week)
    out.lines.append(f"Week {week} recap")
    out.lines.append("=" * 40)
    left_on_bench = []
    all_teams = []
    for m in matchups:
        winner, loser = (m.a, m.b) if m.a.score >= m.b.score else (m.b, m.a)
        margin = winner.score - loser.score
        out.lines.append("")
        out.lines.append(f"{winner.name} {winner.score:.1f}  beat  {loser.name} {loser.score:.1f}  (by {margin:.1f})")
        for team in (winner, loser):
            all_teams.append(team)
            star = _best(team.starters())
            if star:
                out.lines.append(f"  {team.name}: best starter {star.name} ({star.position}) {star.points:.1f}")
            if team.projected is not None:
                diff = team.score - team.projected
                word = "beat" if diff >= 0 else "fell short of"
                out.lines.append(f"    {word} projection by {abs(diff):.1f}")
            missed = optimal_points(team.roster, slots) - team.score
            if missed > 0.05:
                left_on_bench.append((missed, team))
                bench_star = _best(team.bench())
                extra = f", e.g. {bench_star.name} scored {bench_star.points:.1f} on the bench" if bench_star else ""
                out.lines.append(f"    left {missed:.1f} pts on the bench{extra}")
        # A loser whose best lineup would have won is the classic group-chat roast.
        if optimal_points(loser.roster, slots) > winner.score:
            out.lines.append(f"  -> {loser.name} would have WON with their best lineup")

    if all_teams:
        top = max(all_teams, key=lambda t: t.score)
        low = min(all_teams, key=lambda t: t.score)
        out.lines.append("")
        out.lines.append(f"High score of the week: {top.name} {top.score:.1f}")
        out.lines.append(f"Low score of the week:  {low.name} {low.score:.1f}")
    if left_on_bench:
        missed, team = max(left_on_bench, key=lambda x: x[0])
        out.lines.append(f"Worst lineup decisions: {team.name}, {missed:.1f} pts left on the bench")
    return out
