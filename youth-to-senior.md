# From the academy to the Premier League: what the youth stats say

Data: U18 Premier League and Premier League 2, 2022-23 to 2024-25, followed into the senior Premier League up to 19 October 2026. All data comes from the Premier League's own stats API (see `data-sources.md`). Built 22 October 2026.

## The question

1. Which academy players made it into the Premier League?
2. Which youth stats separate the players who made it from the ones who didn't?
3. Which youth stats carry over to the Premier League, and which fade?
4. Which players were very good at youth level but haven't made it, what did they share with the players who did, and what were they missing?

## Who is in the study

- **Cohort:** outfield players with at least 900 minutes in fully covered U18 PL or PL2 matches during 2022-23, 2023-24 or 2024-25, born on or after 1 January 2002. Players born earlier are PL2's over-age players, so they're left out. Goalkeepers are left out too, since there are too few of them.
- That leaves **1,092 players**: 425 defenders, 495 midfielders and 172 forwards. Positions are the labels in the match lineups, taken as the most common one each player had in youth games.
- 2025-26 and 2026-27 youth seasons are left out of the cohort, because those players haven't had time to break through yet.
- **"Made it" has two levels.**
  - **Debuted:** at least one minute in the Premier League between 2022-23 and 19 October 2026, for any club. That's **120 players (11%)**.
  - **Established:** at least 1,000 Premier League minutes in that window. That's **19 players (1.7%)**: 14 midfielders, 3 defenders and 2 forwards.
- Youth players who reached the Championship or lower count as "not made it". This study only measures the Premier League.

| First youth season in the cohort | Players | Debuted | Established |
|---|---|---|---|
| 2022-23 | 656 | 91 | 15 |
| 2023-24 | 261 | 21 | 3 |
| 2024-25 | 175 | 8 | 1 |

The later groups have had less time, so their lower rates are partly just that.

**Established graduates (1,000+ PL minutes):** Lewis Hall (Chelsea academy, 6,432 minutes), Kobbie Mainoo (Man United, 5,703), Jack Hinshelwood (Brighton, 4,550), Omari Hutchinson (Chelsea, 4,296), Lewis Miley (Newcastle, 3,565), Nico O'Reilly (Man City, 3,467), Myles Lewis-Skelly (Arsenal, 2,404), Tyler Dibling (Southampton, 2,251), Josh King (Fulham, 2,011), Oscar Bobb (Man City, 1,848), Mateus Mané (Wolves, 1,791), Jarell Quansah (Liverpool, 1,677), Ollie Scarles (West Ham, 1,321), Justin Devenny (Crystal Palace, 1,285), Josh Acheampong (Chelsea, 1,238), Ayden Heaven (Arsenal, 1,185), Harrison Armstrong (Everton, 1,184), Freddie Potts (West Ham, 1,167) and Ethan Nwaneri (Arsenal, 1,068). The full list of 120 is in `results/graduates.csv`.

## Method

1. **Youth stats per 90 minutes** for 23 counting stats, plus five rates: pass completion, duels won, aerials won, dribble success and shots on target. Only fully covered matches are used (both teams have passing data), which is 95% to 100% of matches in every season.
2. **Each number is compared with peers.** It becomes a z-score within its level (U18 or PL2), season and position. A z-score of +1 means one standard deviation above the average player in the same position at the same level that season. A player's profile is the minutes-weighted average over his level-seasons with at least 450 minutes.
3. **Age** is measured two ways: age on 1 September of the first cohort season, and **age compared with the other players at the same level**, in years, minutes-weighted. A negative value means younger than usual, which is playing up. Separately, the share of youth minutes that came in PL2 rather than U18.
4. **Separation:** for each stat, the gap between the average z of the players who made it and of those who didn't, with a 95% bootstrap interval (2,000 resamples) and the AUC. An AUC of 0.5 means the stat can't tell the two groups apart; 1.0 would separate them perfectly. For all outfield players there is also an age-adjusted gap (OLS with age and position), which barely changes anything.
5. **Carry-over:** for the 21 graduates with at least 450 minutes in Premier League seasons that have full stats, the Spearman correlation between their youth z and their Premier League z for the same stat. Premier League z-scores are computed against all PL players in the same position and season. Four youth stats (big chances, final-third passes, penalty-area entries and dispossessed) aren't in the senior season totals, so they're left out of this step.
6. **Standouts who didn't make it:** a position-specific youth score, the average z of eight stats chosen for that position (listed in `scripts/youth_to_senior.py`). I took the top 10% in each position, kept those with no Premier League minutes who were born before 1 September 2005 (so 21 or older at the start of 2026-27), and compared them with the graduates in the same position.

## 1. What separates the players who made it

**The strongest signal isn't a stat. It's being young for your level.**

| Factor (all outfield, debuted vs not) | Made it | Didn't | 95% interval of the gap | AUC |
|---|---|---|---|---|
| Age compared with others at the same level | 0.65 years younger | about average | 0.46 to 0.79 years younger | 0.71 |
| Share of youth minutes in PL2 | 67% | 43% | +17 to +31 points | 0.66 |
| Age at first youth season | 17.3 | 17.4 | no clear gap | 0.49 |

Raw age tells you nothing. What matters is whether a player was younger than the players around him, which usually means he'd been moved up a level early. The pattern holds in every position, and it's strongest for midfielders (0.8 years younger, AUC 0.75) and for the established group (0.74 years younger).

**Youth stats, all outfield players, debuted vs not** (gap in z-scores):

| Youth stat (per 90 unless a %) | Gap | 95% interval | AUC |
|---|---|---|---|
| Shots | +0.66 | +0.46 to +0.86 | 0.68 |
| Shots on target | +0.61 | +0.42 to +0.82 | 0.68 |
| Dribbles completed | +0.58 | +0.36 to +0.82 | 0.65 |
| Touches in opposition box | +0.57 | +0.38 to +0.77 | 0.66 |
| Goals | +0.50 | +0.32 to +0.68 | 0.65 |
| Completed final-third passes | +0.49 | +0.30 to +0.68 | 0.64 |
| Chances created (key passes) | +0.47 | +0.28 to +0.67 | 0.64 |
| Touches | +0.43 | +0.24 to +0.61 | 0.62 |
| Big chances created | +0.37 | +0.19 to +0.56 | 0.61 |
| Assists | +0.34 | +0.18 to +0.50 | 0.62 |
| Duels won % | +0.28 | +0.13 to +0.43 | 0.60 |
| Pass completion % | +0.28 | +0.12 to +0.44 | 0.59 |
| Passes attempted | +0.28 | +0.08 to +0.47 | 0.57 |
| Tackles won | -0.07 | -0.23 to +0.08 | 0.47 |
| Interceptions | -0.10 | -0.25 to +0.05 | 0.46 |
| Clearances | -0.18 | -0.33 to -0.02 | 0.43 |

- The players who made it did more on the ball in the final third: they shot, dribbled, got into the box, made chances and scored.
- Defensive volume (tackles, interceptions, clearances, blocks) doesn't separate them at all. Clearances are slightly *lower* for the players who made it. A plausible reading, not tested here, is that the teams they play for have the ball more.
- **For the established group (19 players)** the order changes. Touches (+0.76, AUC 0.77), completed final-third passes (+0.74), passes attempted (+0.62), pass completion (+0.63) and duels won % (+0.62) lead, ahead of shooting. That fits a group that is mostly midfielders, but with 19 players the intervals are wide (about ±0.3 to ±0.5).
- **By position** (debuted, all in `results/what_separates_graduates.csv`):
  - **Defenders (30 made it, 395 didn't):** duels won % (+0.59, AUC 0.71), aerials won % (+0.40), pass completion (+0.50), final-third passes (+0.55) and touches (+0.63). Tackles, interceptions and clearances don't separate.
  - **Midfielders (63 vs 432):** shots (+0.76, AUC 0.70), touches in the box (+0.73), shots on target (+0.70), dribbles (+0.67) and key passes (+0.64). Tackles and interceptions run slightly negative.
  - **Forwards (27 vs 145):** shots on target (+0.79, AUC 0.73), touches in the box (+0.75), shots (+0.75) and goals (+0.64).

None of these stats separate the groups well on its own. The best single youth stat reaches an AUC of about 0.7, so many players with great youth numbers didn't make it, and some with ordinary numbers did.

## 2. Which youth stats carry over (21 graduates)

The question here is whether the graduates who ranked high among youth players on a stat also rank high among Premier League players on it. "Edge" is how far above their peers they were, in z-scores, at each level.

| Stat | Correlation, youth vs PL | 95% interval | Youth edge | PL edge |
|---|---|---|---|---|
| Fouls won | 0.70 | 0.32 to 0.92 | +0.40 | +0.31 |
| Goals | 0.62 | 0.11 to 0.89 | +0.22 | +0.04 |
| Dribbles completed | 0.61 | 0.22 to 0.84 | +0.74 | **+0.88** |
| Tackles won | 0.59 | 0.14 to 0.85 | -0.10 | +0.14 |
| Chances created (key passes) | 0.56 | 0.14 to 0.76 | +0.45 | +0.03 |
| Shots on target | 0.55 | 0.12 to 0.84 | +0.45 | -0.02 |
| Aerials won % | 0.51 | 0.09 to 0.79 | +0.30 | -0.43 |
| Pass completion % | 0.43 | -0.03 to 0.73 | +0.69 | +0.48 |
| Shots | 0.25 | -0.26 to 0.66 | +0.61 | **-0.24** |
| Touches | 0.26 | -0.26 to 0.71 | +0.85 | +0.17 |
| Passes attempted | 0.19 | -0.34 to 0.69 | +0.71 | +0.03 |
| Dribble success % | 0.01 | -0.42 to 0.48 | +0.33 | +0.01 |

- **Carries over:** dribbling. The graduates were better dribblers than their youth peers and are still better than other Premier League players in their position. Winning fouls, goals and tackling also keep their order fairly well.
- **Fades:** volume. In youth football the graduates took more shots, made more passes and had more touches than their peers. In the Premier League they're about average on all three, and on shots slightly below. Being on the ball a lot as a teenager doesn't mean you'll be on it a lot among senior pros. Shot-taking also fails to carry over by rank (correlation 0.25).
- Pass completion keeps its edge (+0.69 to +0.48), but the ranking is only loosely kept.
- With 21 players, most intervals are very wide. Treat these as leads to check, not findings.

## 3. Standouts who didn't make it

31 players were in the top 10% of their position on the youth score, have no Premier League minutes, and are 21 or older: 17 defenders, 12 midfielders and 2 forwards. The list is in `results/standouts_not_in_pl.csv`. The top of it: Adedire Mebude (Man City, forward), Bradley Ibrahim (Arsenal), Cameron Bragg (Southampton), Jack Spong (Brighton), Matt Dibley-Dias (Fulham), Salah-Eddine Oulad M'hand (Arsenal), Jeremiah Chilokoa-Mullen (Leeds), Josh Robertson (Sunderland), Charlie McArthur (Newcastle) and Delano McCoy-Splatt (Fulham). Some of them may be playing senior football in the EFL or abroad. This study only checks the Premier League.

**What they shared with the graduates:**

- They often played PL2 (95% of defenders' youth minutes, 79% of midfielders').
- Pass completion was as good or better (defenders +0.66 vs +0.50, midfielders +0.56 vs +0.26).
- Duels and aerials: standout defenders won more duels (+0.96 vs +0.54) and more aerials (+0.82 vs +0.37).
- Standout midfielders created as many big chances and made more key passes than the midfield graduates.

**What they lacked:**

| | Standouts | Graduates (debuted) |
|---|---|---|
| Age at first youth season, defenders | 18.7 | 17.4 |
| Age at first youth season, midfielders | 18.8 | 17.1 |
| Age vs others at the same level, defenders | +0.14 years (older) | -0.46 (younger) |
| Age vs others at the same level, midfielders | +0.60 years (older) | -0.80 (younger) |
| Defenders: completed final-third passes (z) | -0.38 | +0.54 |
| Defenders: dribbles completed | -0.26 | +0.56 |
| Defenders: key passes | -0.52 | +0.26 |
| Midfielders: touches in opposition box | -0.12 | +0.65 |
| Midfielders: dribbles completed | +0.12 | +0.61 |
| Midfielders: goals | +0.12 | +0.47 |

- **The biggest difference is age.** The standouts were 1.3 to 1.7 years older when they started the cohort, and older than the players around them, while the graduates were younger. Part of why they looked so good is that they were playing against younger opponents.
- **Their numbers came from defensive and passing volume** (clearances, recoveries, long balls, passes attempted). The graduates' edge was in carrying the ball forward and in the final third.
- There are only 2 forward standouts, too few to say anything about forwards.
- **A caution about my own score:** the youth score gives weight to defensive volume for defenders (recoveries, interceptions, clearances). Section 1 shows those stats don't predict making it, so part of why these players rank as standouts is my choice of score. A score built from the stats that do separate the groups would rank them lower.

## Limitations

- **Small numbers.** 120 debutants and 19 established players across all positions. Results by position for the established group (3 defenders, 2 forwards) aren't usable.
- **Short follow-up.** The data stops on 19 October 2026. A 2024-25 youth player has had at most two seasons to break through.
- **Making it isn't only about ability.** Club pathway (a Man City academy player faces a much harder first team than a Southampton one), loans, injuries, manager choices and transfers abroad all play a part and aren't modelled. Making it is measured in the Premier League only.
- **Correlation, not cause.** Being moved up early is probably partly a *result* of coaches already rating a player. The age signal partly captures the club's own judgement.
- **Positions are lineup labels** (for example, Lewis Hall is listed as a midfielder in most of his youth games). Wide players are often labelled midfielders.
- **No xG for youth games**, so finishing quality can't be separated from shot volume.
- **The data definitions differ slightly** between youth match stats and senior season totals (pass completion especially). z-scores remove constant differences, but not every difference.
- **Undocumented API.** The source is the Premier League's public website backend. Numbers are Opta-style counts as published there, and I haven't checked them against another provider.

## Files

- `scripts/youth_to_senior.py` runs the whole analysis (about a minute).
- `results/graduates.csv` lists the 120 players who debuted, with academy, PL minutes and youth profile.
- `results/cohort_profiles.csv` has all 1,092 cohort players with every youth z-score.
- `results/what_separates_graduates.csv` has every stat by position and outcome, with intervals and AUC.
- `results/carry_over.csv` and `results/graduates_youth_vs_senior.csv` cover the carry-over step.
- `results/standouts_not_in_pl.csv` and `results/standouts_vs_graduates.csv` cover the standouts.
- `results/summary.txt` has the printed tables.
