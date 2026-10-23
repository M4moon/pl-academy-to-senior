"""Fetch player profiles (birth date, competition history) for every player in
the youth lineups downloaded by fetch_pl_api.py.

Usage: python fetch_players.py DATA_DIR
Writes DATA_DIR/players.csv.gz and DATA_DIR/player_history.csv.gz.
"""
import csv, gzip, os, sys, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_pl_api import get

YOUTH = {"568", "898", "899", "893"}

def main():
    out = sys.argv[1]
    ids = set()
    with gzip.open(os.path.join(out, "lineups.csv.gz"), "rt") as f:
        for r in csv.DictReader(f):
            if r["competition_id"] in YOUTH: ids.add(r["player_id"])
    ids = sorted(ids)
    print(len(ids), "youth players", flush=True)
    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda pid: get(f"/v1/players/{pid}", f"{out}/raw/players/{pid}.json"), ids))
    prof, hist = [], []
    for pid, recs in zip(ids, res):
        recs = recs or []
        births = sorted({(r.get("dates") or {}).get("birth") for r in recs} - {None, "Unknown"})
        name = next(((r.get("name") or {}).get("display") for r in recs if r.get("name")), None)
        prof.append({"player_id": pid, "name": name, "birth_date": births[0] if births else "",
                     "birth_dates_seen": "|".join(births)})
        for r in recs:
            i = r.get("id") or {}
            hist.append({"player_id": pid, "competition_id": i.get("competitionId"), "season": i.get("seasonId"),
                         "team": (r.get("currentTeam") or {}).get("name"), "loan": (r.get("currentTeam") or {}).get("loan")})
    for name, rows in (("players", prof), ("player_history", hist)):
        with gzip.open(os.path.join(out, f"{name}.csv.gz"), "wt", newline="") as f:
            w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
        print(name, len(rows), flush=True)

if __name__ == "__main__":
    main()
