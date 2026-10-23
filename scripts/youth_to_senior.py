"""Youth-to-senior analysis: which U18 Premier League / Premier League 2 players
reached the senior Premier League, which youth stats separate them, which carry
over, and how standout youth players who did not make it compare.

Usage: python youth_to_senior.py DATA_DIR OUT_DIR
Needs the files written by fetch_pl_api.py and fetch_players.py.
"""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

DATA, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
N_BOOT = 2000

YOUTH_LEVEL = {568: "U18", 898: "PL2", 899: "PL2"}   # U18 PL Cup (893) left out: thin coverage
COHORT_SEASONS = ["2022-23", "2023-24", "2024-25"]   # youth seasons with at least two seasons of follow-up
MIN_YOUTH_MINS = 900
MIN_LEVEL_SEASON_MINS = 450
MIN_SENIOR_MINS = 450
ESTABLISHED_MINS = 1000
BORN_FROM = "2002-01-01"                              # U21 eligibility for 2022-23; drops over-age players
STANDOUT_BORN_BEFORE = "2005-09-01"                   # 21+ at the start of 2026-27, so they have had time

# per-90 counts (higher = more of it) and ratios built from two columns
RATE = ["goals", "goalAssist", "totalScoringAtt", "ontargetScoringAtt", "bigChanceCreated", "totalAttAssist",
        "touchesInOppBox", "penAreaEntries", "wonContest", "totalPass", "successfulFinalThirdPasses",
        "accurateLongBalls", "totalTackle", "wonTackle", "interception", "ballRecovery", "totalClearance",
        "outfielderBlock", "possLostAll", "dispossessed", "fouls", "wasFouled", "touches"]
RATIO = {"pass_pct": ("accuratePass", "totalPass"), "duel_pct": ("duelWon", ["duelWon", "duelLost"]),
         "aerial_pct": ("aerialWon", ["aerialWon", "aerialLost"]), "dribble_pct": ("wonContest", "totalContest"),
         "shot_on_target_pct": ("ontargetScoringAtt", "totalScoringAtt")}
LABEL = {"goals": "Goals", "goalAssist": "Assists", "totalScoringAtt": "Shots", "ontargetScoringAtt": "Shots on target",
         "bigChanceCreated": "Big chances created", "totalAttAssist": "Chances created (key passes)",
         "touchesInOppBox": "Touches in opposition box", "penAreaEntries": "Penalty-area entries",
         "wonContest": "Dribbles completed", "totalPass": "Passes attempted", "successfulFinalThirdPasses": "Completed final-third passes",
         "accurateLongBalls": "Accurate long balls", "totalTackle": "Tackles attempted", "wonTackle": "Tackles won",
         "interception": "Interceptions", "ballRecovery": "Ball recoveries", "totalClearance": "Clearances",
         "outfielderBlock": "Blocks", "possLostAll": "Possession lost", "dispossessed": "Dispossessed",
         "fouls": "Fouls committed", "wasFouled": "Fouls won", "touches": "Touches", "pass_pct": "Pass completion %",
         "duel_pct": "Duels won %", "aerial_pct": "Aerials won %", "dribble_pct": "Dribble success %",
         "shot_on_target_pct": "Shots on target %", "age": "Age at first youth season", "age_rel": "Age vs others at the same level (negative = younger)", "pl2_share": "Share of youth minutes in PL2 (playing up)"}
STATS = RATE + list(RATIO)
POS_SETS = {  # stats used for the youth "standout" composite, by position
    "Defender": ["pass_pct", "totalPass", "interception", "ballRecovery", "duel_pct", "aerial_pct", "wonTackle", "totalClearance"],
    "Midfielder": ["totalPass", "pass_pct", "successfulFinalThirdPasses", "bigChanceCreated", "totalAttAssist", "ballRecovery", "wonTackle", "wonContest"],
    "Forward": ["goals", "totalScoringAtt", "ontargetScoringAtt", "bigChanceCreated", "goalAssist", "wonContest", "touchesInOppBox", "penAreaEntries"]}
LOWER_IS_BETTER = {"possLostAll", "dispossessed", "fouls"}

def load(name):
    return pd.read_csv(os.path.join(DATA, f"{name}.csv.gz"), low_memory=False)

pms, tms, lu = load("player_match_stats"), load("team_match_stats"), load("lineups")
players = load("players")
for c in ("competition_id",): pms[c] = pms[c].astype(int); tms[c] = tms[c].astype(int); lu[c] = lu[c].astype(int)
for df in (pms, tms, lu): df["player_id" if "player_id" in df else "match_id"] = df["player_id" if "player_id" in df else "match_id"].astype(str)
pms["match_id"] = pms["match_id"].astype(str); tms["match_id"] = tms["match_id"].astype(str)

# a match counts as fully covered when both teams have passing data; others only give shots/cards
full = tms.assign(tp=pd.to_numeric(tms.get("totalPass"), errors="coerce").fillna(0)).groupby("match_id")["tp"].apply(lambda s: (s > 0).sum() == 2)
pms["full"] = pms["match_id"].map(full).fillna(False)
coverage = (pms.drop_duplicates("match_id").groupby(["competition", "season"])["full"].agg(["size", "mean"])
            .rename(columns={"size": "matches_with_player_stats", "mean": "share_full_coverage"}))
coverage.to_csv(os.path.join(OUT, "coverage_by_season.csv"))

num = [c for c in set(RATE) | {a for a, b in RATIO.values()} | {x for _, b in RATIO.values() for x in (b if isinstance(b, list) else [b])} | {"minsPlayed"}]
for c in num:
    pms[c] = pd.to_numeric(pms[c], errors="coerce").fillna(0) if c in pms else 0.0
pms = pms[pms["full"] & (pms["minsPlayed"] > 0)]

# modal listed position per player across all matches
# listed lineup position, ignoring "Substitute"; youth position from youth matches only
named = lu[lu["position"].isin(["Goalkeeper", "Defender", "Midfielder", "Forward"])]
pos = named[named["competition_id"].isin(YOUTH_LEVEL)].groupby("player_id")["position"].agg(lambda s: s.mode().iloc[0])
pl_lineup_pos = named[named["competition_id"] == 8].groupby("player_id")["position"].agg(lambda s: s.mode().iloc[0])
pms["pos"] = pms["player_id"].map(pos)

def per_level_season(agg, posmap=None, level_col="level"):
    agg = agg[agg["minsPlayed"] >= MIN_LEVEL_SEASON_MINS].copy()
    out = pd.DataFrame(index=agg.index)
    for c in RATE: out[c] = (agg[c] / agg["minsPlayed"] * 90).to_numpy()
    for k, (a, b) in RATIO.items():
        den = agg[b].sum(axis=1) if isinstance(b, list) else agg[b]
        out[k] = (agg[a] / den.where(den > 0)).to_numpy()
    out["mins"] = agg["minsPlayed"]
    out = out.reset_index()
    out["pos"] = out["player_id"].map(pos if posmap is None else posmap)
    # z-score within level, season and position, so U18 and PL2 numbers are comparable
    for c in STATS:
        grp = out.groupby([level_col, "season", "pos"])[c]
        out[c + "_z"] = (out[c] - grp.transform("mean")) / grp.transform("std")
    return out

def wavg(df, cols):
    w = df["mins"]
    return pd.Series({c: np.nansum(df[c] * w) / w[df[c].notna()].sum() if df[c].notna().any() else np.nan for c in cols} | {"mins": w.sum()})

youth = pms[pms["competition_id"].isin(YOUTH_LEVEL)].copy()
youth["level"] = youth["competition_id"].map(YOUTH_LEVEL)
yls = per_level_season(youth.groupby(["player_id", "level", "season"])[num].sum())

# senior Premier League: season totals, renamed to the match-level field names
SENIOR_MAP = {"goals": "goals", "goalAssist": "goalAssists", "totalScoringAtt": "totalShots", "ontargetScoringAtt": "shotsOnTargetIncGoals",
              "totalAttAssist": "keyPassesAttemptAssists", "touchesInOppBox": "totalTouchesInOppositionBox", "wonContest": "successfulDribbles",
              "totalPass": "totalPasses", "accurateLongBalls": "successfulLongPasses", "totalTackle": "totalTackles", "wonTackle": "tacklesWon",
              "interception": "interceptions", "ballRecovery": "recoveries", "totalClearance": "totalClearances", "outfielderBlock": "blocks",
              "possLostAll": "totalLossesOfPossession", "fouls": "totalFoulsConceded", "wasFouled": "totalFoulsWon", "touches": "touches",
              "duelWon": "duelsWon", "duelLost": "duelsLost", "aerialWon": "aerialDuelsWon", "aerialLost": "aerialDuelsLost", "minsPlayed": "timePlayed"}
pss = load("player_season_stats"); pss["player_id"] = pss["player_id"].astype(str)
sagg = pd.DataFrame({k: pd.to_numeric(pss[v], errors="coerce").fillna(0) for k, v in SENIOR_MAP.items()})
sagg["totalContest"] = sagg["wonContest"] + pd.to_numeric(pss["unsuccessfulDribbles"], errors="coerce").fillna(0)
sagg["accuratePass"] = pd.to_numeric(pss["totalPasses"], errors="coerce").fillna(0) - pd.to_numeric(pss["totalUnsuccessfulPassesExclCrossesAndCorners"], errors="coerce").fillna(0)
for c in num:
    if c not in sagg: sagg[c] = np.nan          # not available at season level (big chances, final-third passes, entries, dispossessed)
sagg["player_id"], sagg["level"], sagg["season"] = pss["player_id"], "PL", pss["season"]
# player-seasons whose season request failed (HTTP 500) are rebuilt from their match stats
fb = load("senior_fallback_match_stats"); fb["player_id"] = fb["player_id"].astype(str)
fagg = pd.DataFrame({c: pd.to_numeric(fb[c], errors="coerce").fillna(0) if c in fb else 0.0 for c in num})
fagg["player_id"], fagg["season"] = fb["player_id"], fb["season"]
fagg = fagg.groupby(["player_id", "season"])[num].sum().reset_index(); fagg["level"] = "PL"
for c in num:
    if sagg[c].isna().all(): fagg[c] = np.nan     # keep the same stat set as the season-level data
sagg = pd.concat([sagg[["player_id", "level", "season"] + num], fagg[["player_id", "level", "season"] + num]], ignore_index=True)
sagg = sagg.drop_duplicates(["player_id", "season"], keep="first")
senior_pos = pss.dropna(subset=["position"]).groupby("player_id")["position"].agg(lambda s: s.mode().iloc[0])
senior_pos = senior_pos.reindex(senior_pos.index.union(pl_lineup_pos.index)).fillna(pl_lineup_pos)
sls = per_level_season(sagg.set_index(["player_id", "level", "season"])[num], posmap=senior_pos)
yls.to_csv(os.path.join(OUT, "youth_player_seasons.csv"), index=False)

zc = [c + "_z" for c in STATS]
coh = yls[yls["season"].isin(COHORT_SEASONS)]
yprof = coh.groupby("player_id").apply(lambda d: wavg(d, zc + STATS), include_groups=False)
yprof["pl2_share"] = coh.assign(m2=np.where(coh["level"] == "PL2", coh["mins"], 0)).groupby("player_id")["m2"].sum() / yprof["mins"]
yprof["first_youth_season"] = coh.groupby("player_id")["season"].min()
yprof["pos"] = yprof.index.map(pos)

players["player_id"] = players["player_id"].astype(str)
birth = pd.to_datetime(players.set_index("player_id")["birth_date"], errors="coerce")
yprof["birth_date"] = yprof.index.map(birth)
# age at 1 September of the first cohort season
start = pd.to_datetime(yprof["first_youth_season"].str[:4] + "-09-01")
yprof["age"] = (start - yprof["birth_date"]).dt.days / 365.25
# age relative to the other players at the same level that season (negative = younger than usual, i.e. playing up)
c2 = coh.assign(bd=coh["player_id"].map(birth))
c2["age_s"] = (pd.to_datetime(c2["season"].str[:4] + "-09-01") - c2["bd"]).dt.days / 365.25
c2["age_rel"] = c2["age_s"] - c2.groupby(["level", "season"])["age_s"].transform("mean")
c2 = c2.dropna(subset=["age_rel"])
yprof["age_rel"] = (c2["age_rel"] * c2["mins"]).groupby(c2["player_id"]).sum() / c2.groupby("player_id")["mins"].sum()

# senior outcome: all PL minutes 2022-23 to 2026-27 (any match, any coverage)
fb_apps = fb.assign(m=pd.to_numeric(fb["minsPlayed"], errors="coerce").fillna(0)).query("m > 0").groupby(["player_id", "season"])["match_id"].nunique()
pl_all = sagg[["player_id", "season", "minsPlayed"]].copy()
season_apps = dict(zip(zip(pss["player_id"], pss["season"]), pd.to_numeric(pss["appearances"], errors="coerce").fillna(0)))
pl_all["apps"] = [fb_apps.get((p, se), season_apps.get((p, se), 0)) for p, se in zip(pl_all["player_id"], pl_all["season"])]
pl_all = pl_all[pl_all["minsPlayed"] > 0]
pl_mins = pl_all.groupby("player_id")["minsPlayed"].sum()
pl_apps = pl_all.groupby("player_id")["apps"].sum()
pl_first = pl_all.groupby("player_id")["season"].min()
name = players.set_index("player_id")["name"]

yprof["pl_minutes"] = yprof.index.map(pl_mins).fillna(0)
yprof["pl_apps"] = yprof.index.map(pl_apps).fillna(0).astype(int)
yprof["pl_first_season"] = yprof.index.map(pl_first)
yprof["name"] = yprof.index.map(name)
mt = load("matches")
team_names = dict(zip(mt["home_team_id"].astype(str), mt["home_team"])) | dict(zip(mt["away_team_id"].astype(str), mt["away_team"]))
yl = lu[lu["competition_id"].isin(YOUTH_LEVEL)]
yprof["academy"] = yprof.index.map(yl.groupby("player_id")["team_id"].agg(lambda s: s.astype(str).mode().iloc[0]).map(team_names)).str.replace(r" U(18|21|23)$", "", regex=True)
# drop over-age players and players already established in the PL before their cohort youth minutes
prior_est = pl_all.groupby(["player_id", "season"])["minsPlayed"].sum().reset_index()
prior_est = prior_est[prior_est["minsPlayed"] >= 900].groupby("player_id")["season"].min()
yprof["est_before"] = yprof.index.map(prior_est) < yprof["first_youth_season"]
cohort = yprof[(yprof["mins"] >= MIN_YOUTH_MINS) & (yprof["birth_date"] >= BORN_FROM) & (~yprof["est_before"].fillna(False).astype(bool))
               & yprof["pos"].isin(["Defender", "Midfielder", "Forward"])].copy()
cohort["debuted"] = cohort["pl_minutes"] > 0
cohort["established"] = cohort["pl_minutes"] >= ESTABLISHED_MINS
excluded = {"under_900_youth_mins": int((yprof["mins"] < MIN_YOUTH_MINS).sum()),
            "born_before_2002_or_unknown": int(((yprof["birth_date"] < BORN_FROM) | yprof["birth_date"].isna()).sum()),
            "goalkeepers": int((yprof["pos"] == "Goalkeeper").sum()),
            "established_in_PL_first": int(yprof["est_before"].fillna(False).astype(bool).sum())}

# composite standout score (mean z of the position's stat set; flipped where lower is better)
def composite(r):
    s = POS_SETS.get(r["pos"], [])
    v = [(-1 if c in LOWER_IS_BETTER else 1) * r[c + "_z"] for c in s if pd.notna(r[c + "_z"])]
    return np.mean(v) if v else np.nan
cohort["youth_score"] = cohort.apply(composite, axis=1)
cohort["youth_score_rank_in_pos"] = cohort.groupby("pos")["youth_score"].rank(ascending=False, pct=True)

# 1) who made it
made = cohort[cohort["debuted"]].sort_values("pl_minutes", ascending=False)
made_cols = ["name", "academy", "pos", "birth_date", "age", "first_youth_season", "mins", "pl2_share", "youth_score", "pl_apps", "pl_minutes", "pl_first_season", "established"]
made[made_cols].to_csv(os.path.join(OUT, "graduates.csv"))
cohort.to_csv(os.path.join(OUT, "cohort_profiles.csv"))

# 2) what separates players who reached the PL, by position
def boot_diff(a, b):
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) < 5 or len(b) < 5: return (np.nan,) * 4
    d = a.mean() - b.mean()
    bs = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(N_BOOT)]
    y = np.r_[np.ones(len(a)), np.zeros(len(b))]
    return d, np.percentile(bs, 2.5), np.percentile(bs, 97.5), roc_auc_score(y, np.r_[a, b])

def adj_diff(df, col, flag):
    """made-it coefficient from OLS col ~ flag + age + position dummies (age-adjusted gap)."""
    d = df[[col, flag, "age", "pos"]].dropna()
    if len(d) < 30 or d[flag].sum() < 5: return np.nan, np.nan, np.nan
    X = np.c_[np.ones(len(d)), d[flag].astype(float), d["age"], pd.get_dummies(d["pos"], drop_first=True).astype(float)]
    y = d[col].to_numpy()
    beta = np.linalg.lstsq(X, y, rcond=None)[0][1]
    bs = []
    for _ in range(500):
        i = rng.integers(0, len(d), len(d)); bs.append(np.linalg.lstsq(X[i], y[i], rcond=None)[0][1])
    return beta, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

rows = []
for flag in ("debuted", "established"):
    for p in ["All outfield", "Defender", "Midfielder", "Forward"]:
        d = cohort if p == "All outfield" else cohort[cohort["pos"] == p]
        for c in zc + ["age", "age_rel", "pl2_share"]:
            base = c[:-2] if c.endswith("_z") else c
            dd, lo, hi, auc = boot_diff(d.loc[d[flag], c].to_numpy(float), d.loc[~d[flag], c].to_numpy(float))
            row = dict(outcome=flag, position=p, stat=base, label=LABEL.get(base, base), n_made=int(d[flag].sum()), n_not=int((~d[flag]).sum()),
                       mean_made=d.loc[d[flag], c].mean(), mean_not=d.loc[~d[flag], c].mean(), diff=dd, ci_lo=lo, ci_hi=hi, auc=auc)
            if p == "All outfield" and c.endswith("_z"):
                row["age_adj_diff"], row["age_adj_lo"], row["age_adj_hi"] = adj_diff(d, c, flag)
            rows.append(row)
sep = pd.DataFrame(rows)
sep["clear"] = (sep["ci_lo"] > 0) | (sep["ci_hi"] < 0)
sep.to_csv(os.path.join(OUT, "what_separates_graduates.csv"), index=False)

# 3) carry-over: youth z vs senior z for graduates with enough PL minutes
sprof = sls.groupby("player_id").apply(lambda d: wavg(d, zc), include_groups=False)
g = cohort[cohort["pl_minutes"] > 0].join(sprof[zc].add_prefix("pl_"), how="inner")
g = g[g.index.map(sprof["mins"]) >= MIN_SENIOR_MINS]
carry = []
for c in STATS:
    a, b = g[c + "_z"].to_numpy(float), g["pl_" + c + "_z"].to_numpy(float)
    m = ~np.isnan(a) & ~np.isnan(b)
    if m.sum() < 8: continue
    a, b = a[m], b[m]
    rho = spearmanr(a, b).statistic
    bs = []
    for _ in range(N_BOOT):
        i = rng.integers(0, len(a), len(a)); bs.append(spearmanr(a[i], b[i]).statistic)
    carry.append(dict(stat=c, label=LABEL[c], n=int(m.sum()), spearman=rho, ci_lo=np.nanpercentile(bs, 2.5), ci_hi=np.nanpercentile(bs, 97.5),
                      youth_z_mean=a.mean(), senior_z_mean=b.mean(), change=b.mean() - a.mean()))
carry = pd.DataFrame(carry).sort_values("spearman", ascending=False)
carry.to_csv(os.path.join(OUT, "carry_over.csv"), index=False)
g[["name", "pos", "mins", "pl_minutes"] + [x for c in STATS for x in (c + "_z", "pl_" + c + "_z")]].to_csv(os.path.join(OUT, "graduates_youth_vs_senior.csv"))

# 4) standout youth players who have not reached the PL, versus graduates (any PL minutes) in their position
stand = cohort[(~cohort["debuted"]) & (cohort["birth_date"] < STANDOUT_BORN_BEFORE) & (cohort["youth_score_rank_in_pos"] <= 0.10)]
comp = []
for p, d in stand.groupby("pos"):
    est = cohort[(cohort["pos"] == p) & cohort["debuted"]]   # too few established players per position to compare against
    for c in zc + ["age", "age_rel", "pl2_share"]:
        base = c[:-2] if c.endswith("_z") else c
        comp.append(dict(position=p, stat=base, label=LABEL.get(base, base), n_standouts=len(d), n_graduates=len(est),
                         standouts_mean=d[c].mean(), graduates_mean=est[c].mean(), gap=d[c].mean() - est[c].mean()))
comp = pd.DataFrame(comp)
comp.to_csv(os.path.join(OUT, "standouts_vs_graduates.csv"), index=False)
stand.sort_values("youth_score", ascending=False)[["name", "academy", "pos", "birth_date", "age", "age_rel", "mins", "pl2_share", "youth_score", "youth_score_rank_in_pos"]].to_csv(os.path.join(OUT, "standouts_not_in_pl.csv"))

with open(os.path.join(OUT, "summary.txt"), "w") as f:
    print("coverage\n", coverage.to_string(), file=f)
    print("\nexcluded", excluded, file=f)
    print("\ncohort", len(cohort), cohort["pos"].value_counts().to_dict(), "debuted", int(cohort["debuted"].sum()), "established", int(cohort["established"].sum()), file=f)
    print("\nby first youth season\n", cohort.groupby("first_youth_season")[["debuted", "established"]].agg(["sum", "size"]).to_string(), file=f)
    print("\ngraduates\n", made[made_cols].head(60).to_string(), file=f)
    print("\nseparation (all outfield, debuted)\n", sep[(sep.position == "All outfield") & (sep.outcome == "debuted")].sort_values("diff").to_string(), file=f)
    print("\nseparation (all outfield, established)\n", sep[(sep.position == "All outfield") & (sep.outcome == "established")].sort_values("diff").to_string(), file=f)
    for p in ["Defender", "Midfielder", "Forward"]:
        print(f"\nseparation {p} debuted\n", sep[(sep.position == p) & (sep.outcome == "debuted")].sort_values("diff").to_string(), file=f)
    print("\ncarry-over\n", carry.to_string(), file=f)
    print("\nstandouts\n", stand.sort_values("youth_score", ascending=False)[["name", "pos", "birth_date", "mins", "pl2_share", "youth_score"]].to_string(), file=f)
    print("\nstandouts vs graduates\n", comp.to_string(), file=f)
print(open(os.path.join(OUT, "summary.txt")).read()[:3000])
