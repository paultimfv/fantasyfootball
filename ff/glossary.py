"""The words your friends use, in plain terms."""

TERMS = {
    "PPR": "Points Per Reception. Every catch is worth 1 point on top of yards and TDs. "
    "Makes pass-catching RBs and high-volume WRs more valuable. Half-PPR gives 0.5.",
    "standard": "No points for catches, only yards and TDs. Old-school, rarer now.",
    "FLEX": "A starting slot any RB, WR or TE can fill. SUPER_FLEX (ESPN: OP) also allows a QB.",
    "waivers": "Claiming a player nobody owns. Claims process in priority order, usually "
    "overnight Tuesday/Wednesday, so you can't just grab whoever broke out on Sunday.",
    "FAAB": "Free Agent Acquisition Budget. Everyone gets a pretend budget (often $100) and "
    "bids blind on free agents. Highest bid wins. 'I spent $40 on him' is FAAB talk.",
    "bye week": "Each NFL team sits out one week. Their players score 0, so you need backups.",
    "start/sit": "The weekly decision of who goes in your lineup versus your bench.",
    "projection": "What a site expects a player to score this week. Actual minus projected is "
    "how 'boom' or 'bust' a week was.",
    "boom/bust": "Boom: way above projection. Bust: way below. Players who depend on TDs swing hardest.",
    "target share": "Percent of a team's passes thrown at a player. Above ~25% is elite. "
    "One of the most stable stats week to week, so it predicts future points well.",
    "snap share": "Percent of offensive plays a player was on the field. You can't score from the sideline.",
    "red zone": "Inside the opponent's 20-yard line. Touches there turn into TDs.",
    "handcuff": "The backup to your star RB, rostered as insurance in case the starter gets hurt.",
    "sell high / buy low": "Trade a player after a lucky (TD-heavy) stretch, or trade for one whose "
    "volume is strong but TDs haven't come yet. Regression to the mean is the whole idea.",
    "regression": "Unusually good or bad results drifting back toward normal. TD rates regress hard.",
    "stack": "Starting a QB and his own WR together, so a big passing day pays twice.",
    "D/ST": "Team defense and special teams as one fantasy 'player'. Scores on sacks, turnovers, "
    "and points allowed.",
    "dynasty / keeper": "Leagues where you keep some or all players next season, instead of redrafting.",
    "snake draft": "Draft order reverses every round, so the last pick of round 1 gets the first of round 2.",
    "IR": "Injured reserve slot: stash an injured player without using a bench spot.",
    "left points on the bench": "Your bench players outscored the starters they could have replaced.",
}


def show(term: str | None = None) -> str:
    if term:
        hits = {k: v for k, v in TERMS.items() if term.lower() in k.lower()}
        if not hits:
            return f"No entry for {term!r}. Try: {', '.join(TERMS)}"
    else:
        hits = TERMS
    return "\n\n".join(f"{k}\n  {v}" for k, v in hits.items())


HOCKEY_TERMS = {
    "points league": "Every stat is worth fantasy points (a goal 2, a shot 0.1...) and the higher total "
    "wins the week. ESPN's default. Easiest way to start.",
    "categories (H2H cats)": "Instead of one points total, you compete in separate stats: goals, assists, "
    "shots, hits, wins, save %... Win more categories than your opponent and you win the week. Yahoo's default.",
    "roto": "Season-long categories. You're ranked in each stat across the whole league, no weekly matchups.",
    "PPP": "Power-play points: goals and assists scored with the man advantage. Being on a team's first "
    "power-play unit (PP1) is one of the best fantasy signals there is.",
    "SOG": "Shots on goal. The best predictor of future goals, and worth points on their own in most leagues.",
    "HIT / BLK": "Hits and blocked shots. Grinders and stay-at-home defensemen who barely score can still "
    "be valuable in leagues that count these. Fantasy players call them 'bangers'.",
    "shooting %": "Goals divided by shots. League average is around 10%. A forward at 25% over a few weeks "
    "will cool off; one with lots of shots and no goals is 'due'. This is the hockey version of TD luck.",
    "games played / schedule": "Players only score when their team plays. Some weeks a team plays 4 games, "
    "others 2. Picking players with more games that week is a big, legal edge.",
    "streaming": "Picking up a player (often a goalie) just for his games this week, then dropping him. "
    "Common with goalies who have favorable starts.",
    "goalie starts": "Goalies only score when they start. Backups play maybe 1 game in 3, and teams often "
    "rest the starter on the second night of a back-to-back.",
    "back-to-back": "A team playing two days in a row. The starting goalie usually sits one of them.",
    "multi-position eligibility": "A player listed as C/LW can fill either slot. Flexibility makes "
    "lineups easier to set, so it adds value.",
    "deployment": "How a coach uses a player: line (top-6 or bottom-6), power-play unit, ice time. "
    "Deployment changes are early warnings of value going up or down.",
    "waivers": "Same as any fantasy sport: claiming players nobody owns. In hockey this happens all season "
    "because hot streaks and injuries come fast.",
    "IR": "Injured reserve slot. Stash a hurt player without using a bench spot.",
    "PDO": "Team shooting % plus save %. Hovers near 100 in the long run. A team far above 100 is "
    "probably getting lucky and its players' production may fade.",
}
