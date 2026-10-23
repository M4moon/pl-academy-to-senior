# From the academy to the Premier League

Which Premier League academy players make it into the first team, and what did their youth stats look like?

This project follows **1,092 outfield players** from the U18 Premier League and Premier League 2 (2022-23 to 2024-25) into the senior Premier League, up to 19 October 2026. It uses full player-by-player match stats (passes, duels, dribbles, shots, touches and more) from the Premier League's own public stats API, and tests which youth numbers separate the players who made it, which carry over to senior football, and how standout youth players who haven't made it differ.

Start here:

- **[results-explained.md](results-explained.md)**: the plain-English version of the findings
- **[youth-to-senior.md](youth-to-senior.md)**: full method, tables and limitations
- **[data-sources.md](data-sources.md)**: which free sources exist for academy and senior stats, what each covers, and what is blocked

## Headline results

- **120 of 1,092 (11%)** played at least one Premier League minute. **19 (1.7%)** played 1,000 minutes or more, among them Kobbie Mainoo, Lewis Hall, Myles Lewis-Skelly, Nico O'Reilly, Lewis Miley, Tyler Dibling and Ethan Nwaneri.
- **The strongest signal is being young for your level.** The players who made it were on average 0.65 years younger than the other players at the same level (95% interval 0.46 to 0.79, AUC 0.71). Raw age made no difference (AUC 0.49).
- **Attacking and on-ball youth stats separate the groups:** shots (+0.66 SD, AUC 0.68), shots on target, dribbles completed, touches in the opposition box, goals and chances created. **Defensive volume doesn't:** tackles, interceptions and clearances show no gap, or a slightly negative one.
- **Carry-over** (21 graduates with enough Premier League minutes): dribbling stays above Premier League peers. The graduates' youth edge in shots, passes and touches fades to about Premier League average.
- **31 standout youth players with no Premier League minutes** (aged 21+) were about 1.5 years older than the graduates and older than their level peers. Their numbers came from defensive and passing volume, not from carrying the ball forward.

The sample is small (19 established players), the follow-up is short, and club pathway, loans and injuries aren't modelled. See the limitations section in [youth-to-senior.md](youth-to-senior.md).

## Reproduce

```bash
pip install -r requirements.txt
python scripts/fetch_pl_api.py data             # about 90 minutes: the API rate-limits; raw JSON is cached so reruns resume
python scripts/fetch_players.py data            # birth dates and competition history for youth players
python scripts/fetch_senior_fallback.py data    # rebuilds senior player-seasons whose season request returned HTTP 500
python scripts/youth_to_senior.py data results  # the analysis, about a minute
```

The downloaded data (`data/`, about 13 MB of gzipped CSVs) isn't committed. It comes from an undocumented API behind premierleague.com, so the repo holds the code to fetch it rather than a copy. Because the 2026-27 season is still being played, a fresh download will include more recent matches than the results here (data to 19 October 2026).

## Results files

| File | Contents |
|---|---|
| `results/graduates.csv` | The 120 cohort players with Premier League minutes: academy, position, birth date, youth profile, PL appearances and minutes |
| `results/cohort_profiles.csv` | All 1,092 cohort players with every youth z-score |
| `results/what_separates_graduates.csv` | Every stat by position and outcome (debuted / established): gap, 95% bootstrap interval, AUC, age-adjusted gap |
| `results/carry_over.csv` | Youth vs Premier League rank correlation per stat, with intervals |
| `results/graduates_youth_vs_senior.csv` | Youth and senior z-scores side by side for the 21 carry-over players |
| `results/standouts_not_in_pl.csv`, `results/standouts_vs_graduates.csv` | Top-10% youth players with no PL minutes, and how they compare with graduates |
| `results/youth_player_seasons.csv` | Per-90 youth stats and z-scores for every player-level-season with 450+ minutes |
| `results/coverage_by_season.csv` | Matches with player stats, and the share with full passing and defending data |
| `results/summary.txt` | Printed tables from the last run |
