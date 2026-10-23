"""Download match, lineup, event, team-stat and player-stat data from the
Premier League's public site API (sdp-prem-prod.premier-league-prod.pulselive.com).

Usage: python fetch_pl_api.py OUT_DIR [comp_id ...]
Default comps: 568 U18 Premier League, 898 Premier League 2, 899 PL2 Div 2,
893 U18 PL Cup, 8 Premier League. Seasons 2022..2026 (2022 = 2022-23).
Raw JSON is cached under OUT_DIR/raw so reruns resume.
"""
import json, os, sys, time, csv, gzip, urllib.request, concurrent.futures as cf

B = "https://sdp-prem-prod.premier-league-prod.pulselive.com/api"
HDR = {"User-Agent": "Mozilla/5.0", "Origin": "https://www.premierleague.com"}
COMPS = {568: "U18 Premier League", 898: "Premier League 2", 899: "PL2 Division 2",
         893: "U18 Premier League Cup", 8: "Premier League"}
SEASONS = [2022, 2023, 2024, 2025, 2026]

FAILED = []

def get(path, cache=None):
    if cache and os.path.exists(cache):
        with open(cache) as f: return json.load(f)
    err = None
    for i in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(B + path, headers=HDR), timeout=40) as r:
                d = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): d = None; break
            err = e
            if e.code == 429: time.sleep(15 * (i + 1)); continue
        except Exception as e:
            err = e
        time.sleep(2 ** i)
    else:
        print("FAILED", path, err, flush=True)
        FAILED.append(path)
        return None
    if cache:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w") as f: json.dump(d, f)
    return d

def matches(c, s):
    out, nxt = [], None
    while True:
        d = get(f"/v2/matches?competition={c}&season={s}&_limit=100" + (f"&_next={nxt}" if nxt else ""))
        out += d["data"]; nxt = d["pagination"].get("_next")
        if not nxt: return out

# competitions where player stats are taken per season instead of per match
# (the API rate-limits, and per-match senior stats would be ~50k extra requests)
SEASON_ONLY = {int(x) for x in os.environ.get("SEASON_ONLY", "8").split(",") if x}

def one_match(m, raw):
    mid = m["matchId"]; base = f"{raw}/{m['competitionId']}/{m['seasonId'] if 'seasonId' in m else m['season']}/{mid}"
    stats = get(f"/v3/matches/{mid}/stats", f"{base}/stats.json")
    lu = get(f"/v3/matches/{mid}/lineups", f"{base}/lineups.json")
    ev = get(f"/v1/matches/{mid}/events", f"{base}/events.json")
    if int(m["competitionId"]) in SEASON_ONLY:
        return m, stats, lu, ev, {}
    pids = [p["id"] for side in ("home_team", "away_team") for p in ((lu or {}).get(side) or {}).get("players", [])]
    with cf.ThreadPoolExecutor(4) as ex:
        res = ex.map(lambda pid: get(f"/v1/matches/{mid}/players/{pid}/stats", f"{base}/p_{pid}.json"), pids)
        pstats = dict(zip(pids, res))
    return m, stats, lu, ev, pstats

def main():
    out = sys.argv[1]; comps = [int(x) for x in sys.argv[2:]] or list(COMPS)
    raw = os.path.join(out, "raw"); os.makedirs(out, exist_ok=True)
    rows = {k: [] for k in ("matches", "team_match_stats", "lineups", "events", "player_match_stats")}
    for c in comps:
        for s in SEASONS:
            ms = [m for m in matches(c, s) if m.get("period") == "FullTime"]
            print(COMPS.get(c, c), s, len(ms), "played matches", flush=True)
            with cf.ThreadPoolExecutor(8) as ex:
                for m, stats, lu, ev, pstats in ex.map(lambda m: one_match(m, raw), ms):
                    mid = m["matchId"]; key = dict(competition_id=c, competition=COMPS.get(c, c), season=f"{s}-{str(s+1)[2:]}", match_id=mid)
                    rows["matches"].append({**key, "kickoff": m.get("kickoff"), "matchweek": m.get("matchWeek"),
                        "home_team_id": m["homeTeam"]["id"], "home_team": m["homeTeam"]["name"], "home_score": m["homeTeam"].get("score"),
                        "away_team_id": m["awayTeam"]["id"], "away_team": m["awayTeam"]["name"], "away_score": m["awayTeam"].get("score"),
                        "ground": m.get("ground"), "has_team_stats": bool(stats), "has_lineups": bool(lu and lu.get("home_team", {}).get("players"))})
                    for t in stats or []:
                        rows["team_match_stats"].append({**key, "side": t.get("side"), "team_id": t.get("teamId"), **t.get("stats", {})})
                    for side in ("home_team", "away_team"):
                        t = (lu or {}).get(side) or {}
                        f = t.get("formation") or {}
                        starters = {pid for line in f.get("lineup", []) for pid in line}
                        for p in t.get("players", []):
                            rows["lineups"].append({**key, "side": side[:4], "team_id": t.get("teamId"), "player_id": p["id"],
                                "first_name": p.get("firstName"), "last_name": p.get("lastName"), "position": p.get("position"),
                                "shirt": p.get("shirtNum"), "captain": p.get("isCaptain"), "starter": p["id"] in starters,
                                "formation": f.get("formation")})
                            ps = pstats.get(p["id"])
                            if ps and ps.get("stats"):
                                rows["player_match_stats"].append({**key, "team_id": t.get("teamId"), "player_id": p["id"],
                                    "player": f"{p.get('firstName','')} {p.get('lastName','')}".strip(), "position": p.get("position"), **ps["stats"]})
                    for side in ("homeTeam", "awayTeam"):
                        for kind in ("goals", "cards", "subs"):
                            for e in ((ev or {}).get(side) or {}).get(kind, []) or []:
                                rows["events"].append({**key, "side": side[:4], "event": kind, **{k: v for k, v in e.items() if not isinstance(v, (dict, list))}})
    rows["player_season_stats"] = []
    for c in comps:
        if c not in SEASON_ONLY: continue
        for s in SEASONS:
            season = f"{s}-{str(s+1)[2:]}"
            pids = sorted({r["player_id"] for r in rows["lineups"] if r["competition_id"] == c and r["season"] == season})
            print(COMPS.get(c, c), s, len(pids), "players for season stats", flush=True)
            with cf.ThreadPoolExecutor(8) as ex:
                res = ex.map(lambda pid: get(f"/v1/competitions/{c}/seasons/{s}/players/{pid}/stats", f"{raw}/season/{c}/{s}/{pid}.json"), pids)
                for pid, d in zip(pids, res):
                    if d and d.get("stats"):
                        rows["player_season_stats"].append({"competition_id": c, "competition": COMPS.get(c, c), "season": season, "player_id": pid,
                            "player": ((d.get("player") or {}).get("name") or {}).get("display") if isinstance((d.get("player") or {}).get("name"), dict) else (d.get("player") or {}).get("name"),
                            "position": (d.get("player") or {}).get("position"), **d["stats"]})
    with open(os.path.join(out, "failed_requests.txt"), "w") as f:
        f.write("\n".join(FAILED))
    for name, rs in rows.items():
        cols = []
        for r in rs:
            for k in r:
                if k not in cols: cols.append(k)
        with gzip.open(os.path.join(out, f"{name}.csv.gz"), "wt", newline="") as f:
            w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rs)
        print(name, len(rs), "rows", flush=True)

if __name__ == "__main__":
    main()
