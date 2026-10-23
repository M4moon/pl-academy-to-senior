"""For PL player-seasons whose season-stats request returns HTTP 500, rebuild the
season from per-match player stats.
Usage: python fetch_senior_fallback.py DATA_DIR [FAILED_LIST]
FAILED_LIST defaults to DATA_DIR/failed_requests.txt, written by fetch_pl_api.py."""
import csv, gzip, os, sys, concurrent.futures as cf
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_pl_api import get

data = sys.argv[1]
failed = sys.argv[2] if len(sys.argv) > 2 else os.path.join(data, "failed_requests.txt")
want = set()
for p in open(failed).read().split():
    if "/seasons/" not in p or not p.startswith("/v1/competitions/8/"): continue
    x = p.split("/"); want.add((f"{x[5]}-{str(int(x[5]) + 1)[2:]}", x[7]))
lu = pd.read_csv(os.path.join(data, "lineups.csv.gz"), dtype=str)
ev = pd.read_csv(os.path.join(data, "events.csv.gz"), dtype=str)
lu = lu[lu["competition_id"] == "8"]
subs = ev[ev["event"] == "subs"]
on = set(zip(subs["match_id"], subs["playerOnId"]))
lu = lu[[(s, p) in want for s, p in zip(lu["season"], lu["player_id"])]]
lu = lu[(lu["starter"] == "True") | pd.Series([(m, p) in on for m, p in zip(lu["match_id"], lu["player_id"])], index=lu.index)]
jobs = list(zip(lu["season"], lu["match_id"], lu["player_id"]))
print(len(want), "player-seasons,", len(jobs), "player-matches", flush=True)
with cf.ThreadPoolExecutor(8) as ex:
    res = list(ex.map(lambda j: get(f"/v1/matches/{j[1]}/players/{j[2]}/stats", f"{data}/raw/8/fallback/{j[1]}/p_{j[2]}.json"), jobs))
rows = [{"competition_id": 8, "season": s, "match_id": m, "player_id": p, **(d.get("stats") or {})}
        for (s, m, p), d in zip(jobs, res) if d and d.get("stats")]
cols = []
for r in rows:
    for k in r:
        if k not in cols: cols.append(k)
with gzip.open(os.path.join(data, "senior_fallback_match_stats.csv.gz"), "wt", newline="") as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
print(len(rows), "rows written")
