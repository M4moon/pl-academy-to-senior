# Free stats for Premier League academy and senior players, 2022-23 to 2026-27

Checked 22 October 2026. Every source below was tested from the cloud sandbox. "Works" means a real request returned real data, not just that the site loaded.

## Short answer

- **Academy (U18 Premier League, Premier League 2):** the Premier League's own website API is free, needs no key, and has full player-by-player match stats for every season from 2022-23 to the current 2026-27. These are Opta-style counts: passes (by direction and zone), long balls, tackles, interceptions, recoveries, duels, aerials, clearances, dribbles, shots by zone and foot, big chances, touches, fouls and cards. There is **no xG for youth matches**.
- **U16 and U17:** results only. The U17 Premier League Cup has fixtures and scores but no lineups or stats. The U16 Premier League Cup has only 15 played matches listed (2024-25 and 2025-26), a few with lineups and none with player stats.
- **U15:** I found no public U15 data from any source. U15 games are part of the Premier League's non-competitive Games Programme, with no published tables or stats.
- **Senior Premier League:** the same API has the same depth, plus xG and xA from 2024-25 onward. FPL, Understat and football-data.co.uk also work and fill the gaps (Understat has xG and shot locations for every season).

## Academy sources

| Source | What it has | 2022-23 to 2026-27 | Access from sandbox |
|---|---|---|---|
| Premier League site API, `sdp-prem-prod.premier-league-prod.pulselive.com/api` | Matches, lineups and formations, goals/cards/subs, team match stats, **player match stats (50 to 100 fields)**, player season stats, player profiles with birth date | U18 PL, PL2, PL2 Division 2 (2022-23 only, it was then dropped), U18 PL Cup (patchy stats) | **Works**, no key. Rate-limits bursts above about 60 requests a second (HTTP 429) |
| Old Premier League API, `footballapi.pulselive.com/football` | Same kind of data, older ids | Youth only to 2024-25, player passing and defending stats have gaps | Works, but superseded |
| Transfermarkt | Youth lineups, goals, minutes, market values | Yes | **Blocked** (HTTP 405), needs your laptop |
| FBref | Doesn't cover PL2 or U18 PL | n/a | Blocked (403) |
| Sofascore | PL2 and U18 PL with player ratings | Yes | **Blocked** (403), needs your laptop |
| FotMob | PL2 coverage | Not tested in depth | Site loads, the old API path returns 404 |
| worldfootball.net, soccerway, playmakerstats | Results, scorers, lineups | Yes | Blocked or redirected |
| Flashscore | Results and lineups | Yes | Loads, but the page is built in JavaScript, so it's hard to scrape |

### Coverage checked match by match (Premier League site API)

Filled in from the full download. The table below counts matches that have player stats, and the share with full passing and defending data (both teams have pass counts). In the other matches only shots, goals and cards were recorded.

| Competition | Season | Matches with player stats | Full passing/defending data |
|---|---|---|---|
| U18 Premier League | 2022-23 | 289 | 99.7% |
| U18 Premier League | 2023-24 | 313 | 98.1% |
| U18 Premier League | 2024-25 | 313 | 99.4% |
| U18 Premier League | 2025-26 | 393 | 95.2% |
| U18 Premier League | 2026-27 (to 17 Oct) | 103 | 98.1% |
| Premier League 2 | 2022-23 | 182 | 99.5% |
| PL2 Division 2 | 2022-23 | 110 | 100% |
| Premier League 2 | 2023-24 | 275 | 98.9% |
| Premier League 2 | 2024-25 | 275 | 99.6% |
| Premier League 2 | 2025-26 | 305 | 99.7% |
| Premier League 2 | 2026-27 (to 19 Oct) | 70 | 97.1% |
| U18 Premier League Cup | 2022-23 to 2026-27 | 205 | 0% to 22% (mostly shots, goals and cards only) |

The senior Premier League has all 380 matches in each season from 2022-23 to 2025-26, plus 70 so far in 2026-27 (to 19 October). For senior players I used season totals (one request per player-season) rather than match-by-match stats, to stay under the rate limit. For 101 player-seasons the season request kept returning a server error (HTTP 500), so those were rebuilt from the player's match stats instead.

### Endpoints used

- `/v2/matches?competition={id}&season={year}&_limit=100` (page through with `_next`)
- `/v3/matches/{matchId}/stats` (team match stats)
- `/v3/matches/{matchId}/lineups` (starting XI by line, subs, positions)
- `/v1/matches/{matchId}/events` (goals, cards, substitutions with minute)
- `/v1/matches/{matchId}/players/{playerId}/stats` (player match stats)
- `/v1/competitions/{id}/seasons/{year}/players/{playerId}/stats` (player season totals)
- `/v1/players/{playerId}` (birth date, and which competitions and seasons the player is listed in)

Send the header `Origin: https://www.premierleague.com`. The season id is the starting year (2022 = 2022-23). Competition ids: 8 Premier League, 568 U18 Premier League, 898 Premier League 2, 899 PL2 Division 2, 893 U18 PL Cup, 1114 U17 PL Cup, 894 U16 PL Cup, 569 FA Youth Cup, 678 Premier League Cup, 7 EFL Trophy. Player ids are the same across youth and senior competitions, so a U18 player can be followed into the first team.

This is an undocumented API behind a public website. It could change without notice, and its terms are the Premier League's. It's fine for personal research and a portfolio, but check the terms before republishing the raw data.

## Senior Premier League sources

| Source | What it has | Access from sandbox |
|---|---|---|
| Premier League site API (above) | Player match stats, 60 to 90 fields; xG and xA from 2024-25 | **Works** |
| FPL API, `fantasy.premierleague.com/api` | Live 2026-27: minutes, goals, assists, xG, xA, xGC, tackles, recoveries, defensive contribution, BPS | **Works** |
| vaastav/Fantasy-Premier-League (GitHub raw) | FPL gameweek history, 2016-17 to 2025-26 | **Works** (2026-27 not posted yet) |
| Understat | xG, xA, xGChain, xGBuildup per player; every shot with x/y location and xG | **Works** (send `X-Requested-With: XMLHttpRequest` and accept gzip); all 380 matches 2022-23 to 2025-26, 70 so far in 2026-27 |
| football-data.co.uk | Results, shots, corners, cards, referee, betting odds, and now team xG columns | **Works**, including 2026-27 |
| StatsBomb open data | Only 2003-04 and 2015-16 for the PL | Works, but out of range |
| FBref | Lost all advanced Opta stats in January 2026 (Opta ended its feed). Only basic stats remain | Blocked (403) |
| WhoScored, Sofascore | Ratings, event data | Blocked (403) |

## Files in this folder

- `scripts/fetch_pl_api.py` downloads matches, lineups, events, team match stats and youth player match stats from the Premier League site API (U18 PL, PL2, PL2 Div 2, U18 PL Cup and the Premier League, 2022-23 to 2026-27), plus senior player season totals. It caches the raw JSON, so a rerun resumes. A full run takes about 90 minutes because of the rate limit.
- `scripts/fetch_players.py` downloads birth dates and competition history for every youth player.
- `scripts/fetch_senior_fallback.py` rebuilds the senior player-seasons whose season request failed.
- `data/` (created by the scripts, not committed to git) holds the tables as gzipped CSVs: `matches` (4,450), `team_match_stats` (8,846), `lineups` (155,606 rows), `events` (66,063), `player_match_stats` (91,549 youth player-matches), `player_season_stats` (3,213 senior player-seasons), `senior_fallback_match_stats`, `players` (4,144 youth players with birth dates) and `player_history`.
- `youth-to-senior.md` and `results-explained.md` cover the analysis built on this data.
