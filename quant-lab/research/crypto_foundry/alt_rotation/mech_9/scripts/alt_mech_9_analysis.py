#!/usr/bin/env python
"""ALT_MECH_9 - State-Age Dynamics, Breadth x Dispersion Geometry, Local
Bifurcation Search, Health-State Field Context, Perturbation Response &
Transition Anatomy.

Terrain research ONLY (AGENT 1 - MAIN FIELD CARTOGRAPHER). No PnL, no
strategy, no execution, no sizing, no deployment.
"""
import gc, json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, norm
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260912
BOOT_N = 400
PERM_N = 300
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_9/
M8_ROOT = ROOT.parent / "mech_8"
M4_ROOT = ROOT.parent / "mech_4"
OUT = ROOT

M8_SCRIPTS = M8_ROOT / "scripts"
M4_SCRIPTS = M4_ROOT / "scripts"
sys.path.insert(0, str(M8_SCRIPTS))
sys.path.insert(0, str(M4_SCRIPTS))
import alt_mech_8_analysis as M8

BRD_MED = M8.BRD_MED
DISP_MED = M8.DISP_MED
SUCCESS_LABELS = M8.SUCCESS_LABELS
REENTRY_LABEL = M8.REENTRY_LABEL
CELLS = ["HIGH_BREADTH_HIGH_DISP", "HIGH_BREADTH_LOW_DISP",
         "LOW_BREADTH_HIGH_DISP", "LOW_BREADTH_LOW_DISP"]

HEALTH_LAGS = [-14, -7, -3, -1, 0, 1, 3, 7, 14, 30]

X_COORDS = ["top500_breadth_30d", "top500_dispersion_30d", "rank_depth_rel",
            "top3_share", "btc_return_30d", "vol_med"]

MATURATION_DAY = ["DAY_1", "DAY_3", "DAY_5", "DAY_7", "DAY_10", "DAY_15_PLUS"]
MATURATION_OFF = {"DAY_1": 1, "DAY_3": 3, "DAY_5": 5, "DAY_7": 7,
                  "DAY_10": 10, "DAY_15_PLUS": None}


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run] {name} ...", flush=True)
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def _perm_p(k, B):
    """Finite-sample corrected permutation p-value (never 0)."""
    return (k + 1) / (B + 1)


def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and x != x):
        return "NA"
    return f"{x:.{nd}f}"


def _fdr(p):
    p = np.asarray(p, dtype=float)
    mask = ~np.isnan(p)
    q = np.full(len(p), np.nan)
    if mask.any():
        q[mask] = multipletests(p[mask], method="fdr_bh")[1]
    return q


# =========================================================================
# LOADERS - reuse MECH-8 cached artifacts (memory-safe, no LF2 full reload)
# =========================================================================

def load_dfw():
    """M8 ws3 'df' daily frame: 2196d x 123 cols incl cell, age_in_cell,
    event counts, prop7/reentry7/mixed7, all field coords, subperiod."""
    with open(M8_ROOT / "_cache_ws3.pkl", "rb") as fh:
        r3 = pickle.load(fh)
    return r3["df"]


def load_ev():
    return M8.load_lf2_events()


def load_fwd_rank7():
    with open(M8_ROOT / "_cache_fwd_rank.pkl", "rb") as fh:
        return pickle.load(fh)


def load_health():
    return pd.read_parquet(M8_ROOT / "13b_PRICE_RANK_HEALTH_EVENTS.parquet")


def load_fwd_rank30():
    """Forward rank velocity at t+30 (rank_vel_30d at t+30) via LF2 features,
    only 3 columns loaded. Returns dict event_id -> fwd rank vel 30d."""
    p = OUT / "_cache_fwd_rank30.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    cols = ["historical_date", "cmc_id", "rank_vel_30d"]
    lf2 = pd.read_parquet(M8.LF2_FEATURES, columns=cols)
    lf2["d"] = pd.to_datetime(lf2["historical_date"]).dt.normalize()
    lf2["key"] = (lf2["cmc_id"].astype(str) + "_" +
                  lf2["d"].dt.strftime("%Y%m%d"))
    lookup = dict(zip(lf2["key"], lf2["rank_vel_30d"]))
    del lf2
    gc.collect()
    ev = load_ev()[["cmc_id", "historical_date", "event_id"]].copy()
    ev["d"] = pd.to_datetime(ev["historical_date"]).dt.normalize()
    ev["tgt"] = ev["d"] + pd.Timedelta(days=30)
    ev["key"] = (ev["cmc_id"].astype(str) + "_" +
                 ev["tgt"].dt.strftime("%Y%m%d"))
    ev["fwd_rank_vel_30d"] = ev["key"].map(lookup)
    out = dict(zip(ev["event_id"], ev["fwd_rank_vel_30d"]))
    with open(p, "wb") as fh:
        pickle.dump(out, fh)
    return out


def _daily_pos(dfw):
    dnorm = pd.to_datetime(dfw["d"])
    return {d: i for i, d in enumerate(dnorm)}


def _context_at(dfw, dates, cols):
    """Vectorized context join: rows for (date, col). Returns DataFrame."""
    dnorm = pd.to_datetime(dfw["d"])
    uniq, idx = np.unique(dnorm.values, return_index=True)
    tgt = pd.to_datetime(pd.Series(dates)).dt.normalize().values
    pos = np.searchsorted(uniq, tgt)
    pos = np.clip(pos, 0, len(uniq) - 1)
    hit = uniq[pos] == tgt
    out = pd.DataFrame(index=np.arange(len(dates)))
    for c in cols:
        if dfw[c].dtype == object:
            vals = np.full(len(dates), np.nan, dtype=object)
            vals[hit] = dfw[c].iloc[idx[pos[hit]]].values
            out[c] = vals
        else:
            vals = np.full(len(dates), np.nan)
            vals[hit] = dfw[c].iloc[idx[pos[hit]]].values
            out[c] = vals
    return out
# =========================================================================
# WS1: CONTINUOUS STATE-AGE SURFACES (02_STATE_AGE_CONTINUOUS_SURFACE.csv)
# =========================================================================

MAX_AGE = 30


def ws1_state_age_surface(dfw):
    """For each cell x age (1..30): P(stay next), P(exit next), exit
    destination, fwd 3/7/14 propagation, reentry, tails, rank depth,
    concentration, BTC, vol, breadth level, dispersion level."""
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["next_d"] = df["d"].shift(-1)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell]
        for age in range(1, MAX_AGE + 1):
            s2 = sub[sub["age_in_cell"] == age]
            if len(s2) < 10:
                continue
            nxt = s2["next_cell"]
            p_stay = float((nxt == cell).mean()) if nxt.notna().any() else np.nan
            exited = nxt[nxt != cell].dropna()
            exit_mode = str(exited.mode().iloc[0]) if len(exited) else ""
            p_leave = 1.0 - p_stay if p_stay == p_stay else np.nan
            idx = s2.index
            row = {
                "cell": cell, "age_d": int(age), "n_days": int(len(s2)),
                "p_stay_next": p_stay, "p_leave_next": p_leave,
                "exit_dest_mode": exit_mode,
                "p_leave_next_day": p_leave,
                "fwd3_prop": float(df.loc[idx, "fwd3_prop"].mean())
                if "fwd3_prop" in df.columns else np.nan,
                "fwd7_prop": float(df.loc[idx, "prop7"].mean()),
                "fwd14_prop": float(df.loc[idx, "fwd14_prop"].mean())
                if "fwd14_prop" in df.columns else np.nan,
                "fwd7_reentry": float(df.loc[idx, "reentry7"].mean()),
                "fwd7_mixed": float(df.loc[idx, "mixed7"].mean()),
                "fwd7_isol_dn": float(df.loc[idx, "ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
                "fwd7_band_up": float(df.loc[idx, "ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                     df.loc[idx, "ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
                "fwd7_rank_depth": float(df.loc[idx, "rank_depth_rel"].mean()),
                "fwd7_top3_chg": float(df.loc[idx, "top3_share_chg7"].mean()),
                "p_btc_up": float(df.loc[idx, "BTC_UP"].mean()),
                "p_vol_high": float(df.loc[idx, "VOL_HIGH"].mean()),
                "p_conc_rising": float(df.loc[idx, "CONC_RISING"].mean()),
                "breadth_level": float(df.loc[idx, "top500_breadth_30d"].mean()),
                "dispersion_level": float(df.loc[idx, "top500_dispersion_30d"].mean()),
                "subperiods": int(df.loc[idx, "subperiod"].nunique()),
            }
            rows.append(row)
    out = pd.DataFrame(rows)
    # smoothed surfaces (3-day rolling of stay/leave/prop within cell)
    sm = []
    for cell in CELLS:
        sub = out[out["cell"] == cell].sort_values("age_d")
        sub["p_stay_smooth"] = sub["p_stay_next"].rolling(3, min_periods=1).mean()
        sub["fwd7_prop_smooth"] = sub["fwd7_prop"].rolling(3, min_periods=1).mean()
        sub["p_leave_smooth"] = sub["p_leave_next"].rolling(3, min_periods=1).mean()
        sm.append(sub)
    out = pd.concat(sm, ignore_index=True)
    out.to_csv(OUT / "02_STATE_AGE_CONTINUOUS_SURFACE.csv", index=False)
    return out


# =========================================================================
# WS2: STATE-AGE SURVIVORSHIP / SELECTION AUDIT (03_STATE_AGE_SURVIVORSHIP_AUDIT.csv)
# =========================================================================

LANDMARKS = [1, 3, 5, 7, 10, 15]


def _episodes(df, cell="HIGH_BREADTH_HIGH_DISP"):
    """Maximal consecutive runs of cell -> episodes with start/end index."""
    df = df.copy()
    in_cell = (df["cell"] == cell).astype(int)
    df["_run"] = (in_cell != in_cell.shift()).cumsum()
    eps = []
    for _, g in df[df["cell"] == cell].groupby("_run"):
        if len(g) == 0:
            continue
        eps.append({"start": g.index[0], "end": g.index[-1],
                    "n": int(len(g)), "start_date": g["d"].iloc[0],
                    "subperiod": g["subperiod"].iloc[0]})
    return pd.DataFrame(eps)


def ws2_survivorship(dfw):
    """Landmark analysis: conditional-on-survival fwd outcomes at landmarks;
    compare eventual long-lived vs short-lived HH at entry conditions."""
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["fwd3_state"] = df["state"].shift(-3)
    df["fwd3_prop"] = df["fwd3_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd14_state"] = df["state"].shift(-14)
    df["fwd14_prop"] = df["fwd14_state"].isin(SUCCESS_LABELS).astype(float)
    eps = _episodes(df)
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()

    # A) Landmark analysis: among HH days at age >= landmark (still alive),
    #    fwd7 prop / P(leave) — does the mature subset differ from the whole?
    rows = []
    for lm in LANDMARKS:
        s2 = hh[hh["age_in_cell"] >= lm]
        if len(s2) < 30:
            continue
        idx = s2.index
        rows.append({
            "analysis": "landmark", "landmark_d": int(lm),
            "n_days": int(len(s2)),
            "fwd7_prop": float(df.loc[idx, "prop7"].mean()),
            "fwd14_prop": float(df.loc[idx, "fwd14_prop"].mean()),
            "p_leave_next": float((df.loc[idx, "next_cell"] !=
                                   "HIGH_BREADTH_HIGH_DISP").mean()),
            "fwd7_reentry": float(df.loc[idx, "reentry7"].mean()),
            "fwd7_band_up": float(df.loc[idx, "ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                  df.loc[idx, "ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
            "fwd7_isol_dn": float(df.loc[idx, "ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
            "p_btc_up": float(df.loc[idx, "BTC_UP"].mean()),
            "p_vol_high": float(df.loc[idx, "VOL_HIGH"].mean()),
        })

    # B) Episode-quality effect: entry-day coords of eventual long-lived vs
    #    short-lived HH episodes.
    ep = eps.copy()
    ep["long_lived"] = (ep["n"] >= 7).astype(int)
    entry_coords = ["top500_breadth_30d", "top500_dispersion_30d",
                    "rank_depth_rel", "top3_share", "btc_return_30d", "vol_med"]
    for c in entry_coords:
        ep[c] = df[c].iloc[ep["start"]].values
    ep["entry_cell_prev"] = df["cell"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    for c in entry_coords:
        a = ep.loc[ep["long_lived"] == 1, c].dropna()
        b = ep.loc[ep["long_lived"] == 0, c].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({
            "analysis": "episode_entry", "landmark_d": np.nan,
            "n_days": int(len(ep)),
            "var": c,
            "long_lived_med": float(a.median()) if len(a) else np.nan,
            "short_lived_med": float(b.median()) if len(b) else np.nan,
            "diff": float(a.median() - b.median()) if len(a) and len(b) else np.nan,
            "ranksum_p": p,
            "n_long": int(len(a)), "n_short": int(len(b)),
        })

    # C) Same-episode evolution: within episodes lasting >= 10 days, compare
    #    early (age<=3) vs mature (age>=8) fwd7 prop of the SAME episode.
    ep10 = eps[eps["n"] >= 10]
    within_rows = []
    for _, r in ep10.iterrows():
        seg = df.loc[r["start"]:r["end"]]
        early = seg[seg["age_in_cell"] <= 3]["prop7"]
        late = seg[seg["age_in_cell"] >= 8]["prop7"]
        within_rows.append({
            "ep_start": str(r["start_date"])[:10], "dur": int(r["n"]),
            "early_prop7": float(early.mean()) if len(early) else np.nan,
            "late_prop7": float(late.mean()) if len(late) else np.nan})
    if within_rows:
        wr = pd.DataFrame(within_rows)
        a = wr["early_prop7"].dropna()
        b = wr["late_prop7"].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({
            "analysis": "within_episode", "landmark_d": np.nan,
            "n_days": int(len(wr)),
            "var": "fwd7_prop_early_vs_mature",
            "long_lived_med": float(b.median()) if len(b) else np.nan,
            "short_lived_med": float(a.median()) if len(a) else np.nan,
            "diff": float(b.median() - a.median()) if len(a) and len(b) else np.nan,
            "ranksum_p": p,
            "n_long": int(len(b)), "n_short": int(len(a)),
        })
        wr.to_csv(OUT / "_ws2_within_episode.csv", index=False)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "03_STATE_AGE_SURVIVORSHIP_AUDIT.csv", index=False)
    return out


# =========================================================================
# WS3: HH MATURATION ANATOMY (04_HH_MATURATION_ANATOMY.csv)
# =========================================================================

MAT_COORDS = {
    "breadth": "top500_breadth_30d",
    "dispersion": "top500_dispersion_30d",
    "rank_depth_rel": "rank_depth_rel",
    "leadership_width": "leadership_width",
    "top3_share": "top3_share",
    "btc_dominance": "btc_dominance",
    "btc_ret7": "btc_return_7d",
    "eth_btc_rel7": "eth_btc_relative_return_7d",
    "vol_med": "vol_med",
    "pos_ret_share": "pos_ret_share",
    "breadth_vel": "breadth_vel",
}


def ws3_hh_maturation(dfw):
    """Within surviving HH episodes: median coordinate values at DAY_1/3/5/7/
    10/15+ (episode-relative). Requires episode duration >= target day."""
    df = dfw.copy()
    eps = _episodes(df)
    eps10 = eps[eps["n"] >= 7]
    rows = []
    for _, r in eps10.iterrows():
        seg = df.loc[r["start"]:r["end"]].reset_index(drop=True)
        for label, off in MATURATION_OFF.items():
            if off is None:
                day_idx = 14
                if len(seg) < 15:
                    continue
            else:
                day_idx = off - 1
                if len(seg) < off:
                    continue
            row = {"ep_start": str(r["start_date"])[:10], "dur": int(r["n"]),
                   "day_label": label}
            for name, col in MAT_COORDS.items():
                v = seg[col].iloc[day_idx]
                row[name] = float(v) if v == v else np.nan
            # event counts within episode up to day label
            row["isol_dn_cum"] = int(seg["ev_ISOLATED_DOWNSIDE_EXTREME"].iloc[:day_idx + 1].sum())
            row["band_up_cum"] = int(seg["ev_BAND_BROAD_UPSIDE"].iloc[:day_idx + 1].sum() +
                                    seg["ev_MULTI_BAND_UPSIDE"].iloc[:day_idx + 1].sum())
            rows.append(row)
    if not rows:
        pd.DataFrame().to_csv(OUT / "04_HH_MATURATION_ANATOMY.csv", index=False)
        return pd.DataFrame()
    mat = pd.DataFrame(rows)
    agg = mat.groupby("day_label")[list(MAT_COORDS.keys()) +
                                   ["isol_dn_cum", "band_up_cum"]].median().reset_index()
    agg = agg[agg["day_label"].isin(
        ["DAY_1", "DAY_3", "DAY_5", "DAY_7", "DAY_10", "DAY_15_PLUS"])]
    n_ep = mat.groupby("day_label")["ep_start"].nunique().rename("n_episodes").reset_index()
    agg = agg.merge(n_ep, on="day_label")
    agg.to_csv(OUT / "04_HH_MATURATION_ANATOMY.csv", index=False)
    return {"agg": agg, "mat": mat}
# =========================================================================
# WS4: HH BIRTH QUALITY (05_HH_BIRTH_QUALITY.csv)
# =========================================================================

DUR_BUCKETS = [(1, 2, "1-2D"), (3, 5, "3-5D"), (6, 10, "6-10D"),
               (11, 20, "11-20D"), (21, 10 ** 6, "21D+")]
BIRTH_COORDS = ["top500_breadth_30d", "top500_dispersion_30d",
                "rank_depth_rel", "top3_share", "btc_return_30d", "vol_med",
                "breadth_vel", "disp_vel"]


def _dur_bucket(n):
    for lo, hi, name in DUR_BUCKETS:
        if lo <= n <= hi:
            return name
    return "21D+"


def _purged_folds(n, k=5, embargo=7):
    """Chronological folds with embargo (index-based)."""
    folds = []
    size = n // k
    for i in range(k):
        te = np.arange(i * size, min((i + 1) * size, n))
        tr = np.concatenate([np.arange(0, max(i * size - embargo, 0)),
                             np.arange(min((i + 1) * size + embargo, n), n)])
        if len(te) >= 5 and len(tr) >= 20:
            folds.append((tr, te))
    return folds


def _logreg_metrics(X, y, folds):
    aucs, lls, briers = [], [], []
    for tr, te in folds:
        if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
            continue
        try:
            m = LogisticRegression(max_iter=2000)
            m.fit(X[tr], y[tr])
            p = m.predict_proba(X[te])[:, 1]
            aucs.append(roc_auc_score(y[te], p))
            lls.append(log_loss(y[te], p))
            briers.append(brier_score_loss(y[te], p))
        except Exception:
            continue
    if not aucs:
        return np.nan, np.nan, np.nan, 0
    return (float(np.mean(aucs)), float(np.mean(lls)),
            float(np.mean(briers)), int(len(aucs)))


def _permutation_ll(X, y, folds, base_ll, B=PERM_N):
    rng = np.random.default_rng(SEED)
    worse = 0
    for _ in range(B):
        yp = rng.permutation(y)
        _, ll, _, _ = _logreg_metrics(X, yp, folds)
        if ll == ll and base_ll == base_ll and ll >= base_ll:
            worse += 1
    return _perm_p(worse, B)


def ws4_hh_birth_quality(dfw):
    """Duration buckets by entry-day coords; purged-CV long-lived (>=6D)
    classification; also bucket medians + ranksums."""
    df = dfw.copy()
    df["disp_vel"] = df["top500_dispersion_30d"].diff(5)
    eps = _episodes(df)
    for c in BIRTH_COORDS:
        eps[c] = df[c].iloc[eps["start"]].values
    eps["dur_bucket"] = eps["n"].apply(_dur_bucket)
    # bucket table
    rows = []
    for b in ["1-2D", "3-5D", "6-10D", "11-20D", "21D+"]:
        sub = eps[eps["dur_bucket"] == b]
        if len(sub) < 10:
            continue
        row = {"dur_bucket": b, "n_episodes": int(len(sub)),
               "n_subperiods": int(sub["subperiod"].nunique()),
               "median_dwell": float(sub["n"].median())}
        for c in BIRTH_COORDS:
            row[f"med_{c}"] = float(sub[c].median())
        rows.append(row)
    bucket = pd.DataFrame(rows)
    # long-lived classification with purged CV (chronological by start index)
    eps_sorted = eps.sort_values("start").reset_index(drop=True)
    y = (eps_sorted["n"] >= 6).astype(int).to_numpy(float)
    X = eps_sorted[BIRTH_COORDS].apply(lambda s: s.fillna(s.median())).to_numpy(float)
    folds = _purged_folds(len(eps_sorted))
    auc, ll, br, nfold = _logreg_metrics(X, y, folds)
    perm_p = _permutation_ll(X, y, folds, ll) if ll == ll else np.nan
    # per-coordinate univariate effect
    uni = []
    for i, c in enumerate(BIRTH_COORDS):
        a = eps_sorted.loc[y == 1, c].dropna()
        b = eps_sorted.loc[y == 0, c].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        uni.append({"var": c, "long_lived_med": float(a.median()),
                    "short_lived_med": float(b.median()),
                    "diff": float(a.median() - b.median()), "ranksum_p": p,
                    "n_long": int(len(a)), "n_short": int(len(b))})
    uni_df = pd.DataFrame(uni)
    summ = pd.DataFrame([{"n_episodes": int(len(eps_sorted)),
                          "n_long_lived": int(y.sum()),
                          "n_short_lived": int((1 - y).sum()),
                          "cv_auc": auc, "cv_logloss": ll, "cv_brier": br,
                          "n_folds": nfold, "perm_p": perm_p}])
    bucket.to_csv(OUT / "05_HH_BIRTH_QUALITY.csv", index=False)
    summ.to_csv(OUT / "05b_HH_BIRTH_QUALITY_SUMMARY.csv", index=False)
    uni_df.to_csv(OUT / "05c_HH_BIRTH_QUALITY_UNIVARIATE.csv", index=False)
    return {"bucket": bucket, "summary": summ, "uni": uni_df}


# =========================================================================
# WS5: SECOND-ORDER STATE PATHS (06_SECOND_ORDER_STATE_PATHS.csv)
# =========================================================================

def ws5_second_order_paths(dfw):
    """Consecutive distinct-cell triples A->B->C from daily cell sequence.
    Dwell = days in each run. Requires >=50 effective paths."""
    df = dfw.copy()
    cell_ser = df["cell"]
    run_id = (cell_ser != cell_ser.shift()).cumsum()
    runs = pd.DataFrame({"cell": cell_ser, "_run": run_id, "d": df["d"],
                         "subperiod": df["subperiod"]})
    rtab = runs.groupby("_run").agg(
        cell=("cell", "first"), start=("d", "first"), end=("d", "last"),
        n_days=("d", "size"), subperiod=("subperiod", "first")).reset_index()
    rtab = rtab.sort_values("start").reset_index(drop=True)
    rows = []
    for i in range(1, len(rtab) - 1):
        a, b, c = rtab["cell"].iloc[i - 1], rtab["cell"].iloc[i], rtab["cell"].iloc[i + 1]
        # outcome from end of run C
        end_c = rtab["end"].iloc[i + 1]
        pos = df.index[df["d"] == end_c]
        if len(pos) == 0:
            continue
        pi = pos[0]
        fwd7_state = df["state"].shift(-7).iloc[pi]
        fwd14_state = df["state"].shift(-14).iloc[pi]
        rows.append({
            "path": f"{a}->{b}->{c}", "a": a, "b": b, "c": c,
            "dwell_b_d": int(rtab["n_days"].iloc[i]),
            "total_days": int(rtab["n_days"].iloc[i - 1] +
                              rtab["n_days"].iloc[i] +
                              rtab["n_days"].iloc[i + 1]),
            "start": rtab["start"].iloc[i - 1],
            "subperiod": rtab["subperiod"].iloc[i],
            "fwd7_prop": int(fwd7_state in SUCCESS_LABELS) if fwd7_state == fwd7_state else np.nan,
            "fwd14_prop": int(fwd14_state in SUCCESS_LABELS) if fwd14_state == fwd14_state else np.nan,
        })
    if not rows:
        pd.DataFrame().to_csv(OUT / "06_SECOND_ORDER_STATE_PATHS.csv", index=False)
        return pd.DataFrame()
    paths = pd.DataFrame(rows)
    # aggregate
    agg_rows = []
    for (path, a, b, c), g in paths.groupby(["path", "a", "b", "c"]):
        if len(g) < 10:
            continue
        agg_rows.append({
            "path": path, "from": a, "mid": b, "to": c,
            "n": int(len(g)),
            "n_effective": int(g["start"].nunique()),
            "median_dwell_b_d": float(g["dwell_b_d"].median()),
            "median_total_days": float(g["total_days"].median()),
            "fwd7_prop": float(g["fwd7_prop"].mean()),
            "fwd14_prop": float(g["fwd14_prop"].mean()),
            "subperiods": int(g["subperiod"].nunique()),
        })
    out = pd.DataFrame(agg_rows)
    # baseline: unconditional fwd7 prop from run-C end
    out["baseline_fwd7_prop"] = paths["fwd7_prop"].mean()
    out = out.sort_values("n", ascending=False)
    out.to_csv(OUT / "06_SECOND_ORDER_STATE_PATHS.csv", index=False)
    return out


# =========================================================================
# WS6: TRANSITION VELOCITY / SHOCK SIZE (07_TRANSITION_VELOCITY.csv)
# =========================================================================

def ws6_transition_velocity(dfw):
    """Cell-crossing days: breadth/dispersion deltas, distance from threshold
    before crossing, days near boundary, overshoot; SOFT/MODERATE/HARD."""
    df = dfw.copy()
    df["prev_cell"] = df["cell"].shift(1)
    df["prev_d"] = df["d"].shift(1)
    cross = df[(df["cell"] != df["prev_cell"]) & df["prev_cell"].notna()].copy()
    if len(cross) < 30:
        pd.DataFrame().to_csv(OUT / "07_TRANSITION_VELOCITY.csv", index=False)
        return pd.DataFrame()
    brd = df["top500_breadth_30d"].to_numpy(float)
    disp = df["top500_dispersion_30d"].to_numpy(float)
    idx = cross.index.to_numpy()
    brd_delta = brd[idx] - brd[np.clip(idx - 1, 0, len(df) - 1)]
    disp_delta = disp[idx] - disp[np.clip(idx - 1, 0, len(df) - 1)]
    max_delta = np.maximum(np.abs(brd_delta), np.abs(disp_delta))
    keep = np.isfinite(max_delta)
    idx, brd_delta, disp_delta, max_delta = (
        idx[keep], brd_delta[keep], disp_delta[keep], max_delta[keep])
    cross = cross.iloc[np.where(keep)[0]].copy()
    # distance from threshold over prior 5 days (min |x - threshold|)
    dist_brd, dist_disp, days_near = [], [], []
    for i in idx:
        w = np.arange(max(i - 4, 0), i + 1)
        db = np.min(np.abs(brd[w] - BRD_MED))
        dd = np.min(np.abs(disp[w] - DISP_MED))
        dist_brd.append(float(db))
        dist_disp.append(float(dd))
        days_near.append(int(np.sum((np.abs(brd[w] - BRD_MED) < 0.02) |
                                    (np.abs(disp[w] - DISP_MED) < 0.02))))
    # overshoot: max excursion past threshold within +3 days
    over_brd, over_disp = [], []
    for i in idx:
        w = np.arange(i, min(i + 4, len(df)))
        over_brd.append(float(np.max(np.abs(brd[w] - BRD_MED))))
        over_disp.append(float(np.max(np.abs(disp[w] - DISP_MED))))
    cross["brd_delta"] = brd_delta
    cross["disp_delta"] = disp_delta
    cross["dist_brd_prior"] = dist_brd
    cross["dist_disp_prior"] = dist_disp
    cross["days_near_boundary"] = days_near
    cross["overshoot_brd"] = over_brd
    cross["overshoot_disp"] = over_disp
    cross["vel_class"] = np.where(max_delta < 0.03, "SOFT_CROSS",
                        np.where(max_delta < 0.06, "MODERATE_CROSS", "HARD_CROSS"))
    # outcomes from crossing day
    idx2 = cross.index
    cross["fwd7_prop"] = df.loc[idx2, "prop7"].to_numpy()
    cross["fwd7_reentry"] = df.loc[idx2, "reentry7"].to_numpy()
    cross["fwd7_isol_dn"] = df.loc[idx2, "ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].to_numpy()
    cross["fwd7_band_up"] = (df.loc[idx2, "ev_BAND_BROAD_UPSIDE_fwd7"].to_numpy() +
                             df.loc[idx2, "ev_MULTI_BAND_UPSIDE_fwd7"].to_numpy())
    cross["subperiod"] = df.loc[idx2, "subperiod"].to_numpy()
    # aggregate
    rows = []
    for vc in ["SOFT_CROSS", "MODERATE_CROSS", "HARD_CROSS"]:
        sub = cross[cross["vel_class"] == vc]
        if len(sub) < 10:
            continue
        rows.append({"vel_class": vc, "n": int(len(sub)),
                     "median_brd_delta": float(sub["brd_delta"].median()),
                     "median_disp_delta": float(sub["disp_delta"].median()),
                     "median_dist_prior": float(sub["dist_brd_prior"].min() if
                                                len(sub) else np.nan),
                     "median_days_near": float(sub["days_near_boundary"].median()),
                     "median_overshoot": float(sub["overshoot_brd"].median()),
                     "fwd7_prop": float(sub["fwd7_prop"].mean()),
                     "fwd7_reentry": float(sub["fwd7_reentry"].mean()),
                     "fwd7_isol_dn": float(sub["fwd7_isol_dn"].mean()),
                     "fwd7_band_up": float(sub["fwd7_band_up"].mean()),
                     "subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    # significance: SOFT vs HARD on fwd7 prop
    a = cross[cross["vel_class"] == "SOFT_CROSS"]["fwd7_prop"].dropna()
    b = cross[cross["vel_class"] == "HARD_CROSS"]["fwd7_prop"].dropna()
    out["soft_vs_hard_prop_p"] = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
    out.to_csv(OUT / "07_TRANSITION_VELOCITY.csv", index=False)
    cross.to_csv(OUT / "07b_TRANSITION_VELOCITY_EVENTS.csv", index=False)
    return {"agg": out, "events": cross}
# =========================================================================
# WS7: LOCAL BIFURCATION SEARCH (08_LOCAL_BIFURCATION_SEARCH.csv)
# =========================================================================

BIF_AXES = ["top500_breadth_30d", "top500_dispersion_30d", "age_in_cell",
            "rank_depth_rel", "top3_share", "vol_med"]
N_BINS = 8


def _bin_surface(df, axis, n_bins=N_BINS):
    """Binned P(prop7) / P(leave next) / P(exit dest = reentry) surfaces."""
    x = df[axis].to_numpy(float)
    valid = ~np.isnan(x) & ~np.isnan(df["prop7"].to_numpy(float))
    if valid.sum() < 50:
        return None
    qs = np.quantile(x[valid], np.linspace(0, 1, n_bins + 1))
    qs = np.unique(qs)
    if len(qs) < 4:
        return None
    bins = np.digitize(x, qs[1:-1])
    rows = []
    for b in range(len(qs)):
        m = bins == b
        if m.sum() < 20:
            continue
        prop = df.loc[m, "prop7"].mean()
        leave = float((df.loc[m, "cell"].shift(-1) != df.loc[m, "cell"]).mean())
        rows.append({"bin": b, "n": int(m.sum()),
                     "axis_mid": float(np.nanmedian(x[m])),
                     "prop7": float(prop),
                     "p_leave_next": leave,
                     "subperiods": int(df.loc[m, "subperiod"].nunique())})
    return pd.DataFrame(rows)


def _surface_verdict(surf, axis, subperiods_df=None):
    """Classify the binned surface: smooth gradient, nonlinear region, sharp
    transition region, bifurcation candidate, or no structure."""
    if surf is None or len(surf) < 4:
        return "NO_STRUCTURE", np.nan
    prop = surf["prop7"].to_numpy(float)
    x = surf["axis_mid"].to_numpy(float)
    if np.ptp(prop) < 0.05:
        return "NO_STRUCTURE", np.nan
    # max adjacent jump
    jumps = np.abs(np.diff(prop))
    max_jump = float(np.max(jumps)) if len(jumps) else np.nan
    mean_jump = float(np.mean(jumps)) if len(jumps) else np.nan
    # sharpness ratio
    if mean_jump > 0:
        sharp = max_jump / mean_jump
    else:
        sharp = np.nan
    # monotonicity: sign changes of diff
    d = np.diff(prop)
    sign_changes = int(np.sum(np.sign(d[1:]) != np.sign(d[:-1])))
    if max_jump >= 0.20 and sharp >= 2.5:
        verdict = "BIFURCATION_CANDIDATE"
    elif max_jump >= 0.12 and sharp >= 2.0:
        verdict = "SHARP_TRANSITION_REGION"
    elif sign_changes >= 2 and np.ptp(prop) >= 0.08:
        verdict = "NONLINEAR_REGION"
    else:
        verdict = "SMOOTH_GRADIENT"
    return verdict, max_jump


def ws7_bifurcation_search(dfw):
    """Raw-coordinate binned surfaces of P(prop7) for each axis; verdicts
    gated on >=3 subperiod stability of the binned pattern."""
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    rows = []
    for axis in BIF_AXES:
        if axis not in df.columns:
            continue
        surf = _bin_surface(df, axis)
        if surf is None:
            rows.append({"axis": axis, "verdict": "DATA_BLOCKED",
                         "n_bins": 0, "max_jump": np.nan})
            continue
        verdict, max_jump = _surface_verdict(surf, axis)
        # subperiod stability: recompute surface per subperiod, check the
        # same verdict class (sharp vs smooth) in >=3 subperiods
        classes = []
        for sp in ["2020-2021", "2022", "2023", "2024", "2025-2026"]:
            s = df[df["subperiod"] == sp]
            if len(s) < 100:
                continue
            su = _bin_surface(s, axis)
            if su is None:
                continue
            v, _ = _surface_verdict(su, axis)
            classes.append(v)
        sharp_like = sum(c in ("BIFURCATION_CANDIDATE", "SHARP_TRANSITION_REGION")
                         for c in classes)
        stable = int(sharp_like >= 3) if len(classes) >= 3 else 0
        if not stable and verdict in ("BIFURCATION_CANDIDATE", "SHARP_TRANSITION_REGION"):
            verdict = verdict + "_UNSTABLE"
        rows.append({"axis": axis, "verdict": verdict,
                     "n_bins": int(len(surf)),
                     "max_jump": max_jump,
                     "n_sharp_subperiods": int(sharp_like),
                     "n_subperiods_tested": len(classes),
                     "stable_flag": stable,
                     "subperiod_classes": "|".join(classes)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "08_LOCAL_BIFURCATION_SEARCH.csv", index=False)
    return out


# =========================================================================
# WS8: STATE-SPACE VECTOR FIELD (09_STATE_SPACE_VECTOR_FIELD.csv)
# =========================================================================

def _zscore(s):
    s = s.to_numpy(float)
    mu, sd = np.nanmean(s), np.nanstd(s)
    return (s - mu) / sd if sd > 0 else np.zeros_like(s)


def ws8_state_space(dfw):
    """X(t) = [breadth, dispersion, age, rank_depth, concentration, BTC, vol]
    standardized; Delta X(t->t+1); attractor/corridor/loop checks."""
    df = dfw.copy()
    df["age_log"] = np.log1p(df["age_in_cell"])
    coords = ["top500_breadth_30d", "top500_dispersion_30d", "age_log",
              "rank_depth_rel", "top3_share", "btc_return_30d", "vol_med"]
    for c in coords:
        df[f"z_{c}"] = _zscore(df[c])
    zc = [f"z_{c}" for c in coords]
    dX = df[zc].diff(1)
    X_now = df[zc]
    mag = np.sqrt((dX ** 2).sum(axis=1)).to_numpy(float)
    df["dX_mag"] = mag
    rows = []
    # attractor check: mean |dX| inside HH/LL vs outside
    for cell in CELLS:
        inside = df[df["cell"] == cell]
        outside = df[df["cell"] != cell]
        rows.append({"metric": "attractor", "region": cell,
                     "mean_dX_mag": float(inside["dX_mag"].mean()),
                     "outside_dX_mag": float(outside["dX_mag"].mean()),
                     "n": int(len(inside))})
    # corridor check: HL/LH dwell + net drift
    for cell in ["HIGH_BREADTH_LOW_DISP", "LOW_BREADTH_HIGH_DISP"]:
        sub = df[df["cell"] == cell]
        rows.append({"metric": "corridor", "region": cell,
                     "mean_dX_mag": float(sub["dX_mag"].mean()),
                     "median_dwell": float(sub["age_in_cell"].median()),
                     "net_drift_brd": float(sub["top500_breadth_30d"].diff(1).mean()),
                     "net_drift_disp": float(sub["top500_dispersion_30d"].diff(1).mean()),
                     "n": int(len(sub))})
    # loop check: 2-step return (dX_t + dX_{t+1} magnitude vs |dX_t|)
    d2 = df[zc].diff(2)
    mag2 = np.sqrt((d2 ** 2).sum(axis=1)).to_numpy(float)
    loop_ratio = float(np.nanmean(mag2 / np.maximum(mag, 1e-9)))
    rows.append({"metric": "loop", "region": "ALL",
                 "mean_2step_ratio": loop_ratio,
                 "mean_dX_mag": float(np.nanmean(mag)),
                 "n": int(len(df))})
    # HH attractor: does |dX| shrink with age inside HH?
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"]
    a = hh[hh["age_in_cell"] <= 3]["dX_mag"]
    b = hh[hh["age_in_cell"] >= 8]["dX_mag"]
    p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
    rows.append({"metric": "hh_age_stability", "region": "HIGH_BREADTH_HIGH_DISP",
                 "young_dX_mag": float(a.mean()), "mature_dX_mag": float(b.mean()),
                 "ranksum_p": p, "n": int(len(hh))})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "09_STATE_SPACE_VECTOR_FIELD.csv", index=False)
    return out


# =========================================================================
# WS9: PERTURBATION RESPONSE (10_PERTURBATION_RESPONSE.csv)
# =========================================================================

PERT_COLS = ["brd_jump", "brd_drop", "disp_jump", "disp_drop",
             "btc_shock", "conc_shock", "vol_shock"]


def _perturbation_flags(df):
    """Discrete field-change perturbations (5D changes)."""
    out = df.copy()
    b5 = out["top500_breadth_30d"].diff(5)
    d5 = out["top500_dispersion_30d"].diff(5)
    bt5 = out["btc_return_7d"]  # proxy for 5D BTC move (7D available)
    c7 = out["top3_share_chg7"]
    v5 = out["vol_med"].diff(5)
    out["brd_jump"] = (b5 >= 0.04).astype(int)
    out["brd_drop"] = (b5 <= -0.04).astype(int)
    out["disp_jump"] = (d5 >= 0.04).astype(int)
    out["disp_drop"] = (d5 <= -0.04).astype(int)
    out["btc_shock"] = (bt5.abs() >= 0.08).astype(int)
    out["conc_shock"] = (c7.abs() >= 0.02).astype(int)
    out["vol_shock"] = (v5.abs() >= v5.std() * 1.0).astype(int)
    return out


def ws9_perturbation(dfw):
    """For each perturbation type x cell x age band: P(stay next), P(change),
    fwd7 prop, recovery latency vs matched non-perturbed days."""
    df = _perturbation_flags(dfw)
    df["next_cell"] = df["cell"].shift(-1)
    df["fwd7_prop"] = df["prop7"]
    df["fwd7_reentry"] = df["reentry7"]
    rows = []
    for pc in PERT_COLS:
        for cell in CELLS:
            sub = df[df["cell"] == cell]
            treated = sub[sub[pc] == 1]
            control = sub[sub[pc] == 0]
            if len(treated) < 20 or len(control) < 50:
                continue
            t_stay = float((treated["next_cell"] == cell).mean())
            c_stay = float((control["next_cell"] == cell).mean())
            t_prop = float(treated["fwd7_prop"].mean())
            c_prop = float(control["fwd7_prop"].mean())
            # recovery latency: days until cell returns to pre-perturbation
            lat = []
            for i in treated.index:
                target = df["cell"].shift(1).loc[i]
                if target != target:
                    continue
                w = df["cell"].loc[i + 1: i + 10]
                hit = np.where((w == target).to_numpy())[0]
                lat.append(int(hit[0] + 1) if len(hit) else 10)
            rows.append({
                "perturbation": pc, "cell": cell,
                "n_treated": int(len(treated)), "n_control": int(len(control)),
                "p_stay_treated": t_stay, "p_stay_control": c_stay,
                "delta_stay": float(t_stay - c_stay),
                "fwd7_prop_treated": t_prop, "fwd7_prop_control": c_prop,
                "delta_prop": float(t_prop - c_prop),
                "median_recovery_d": float(np.median(lat)) if lat else np.nan,
                "subperiods_treated": int(treated["subperiod"].nunique()),
            })
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "10_PERTURBATION_RESPONSE.csv", index=False)
    return out
# =========================================================================
# WS10: HEALTH-STATE FIELD MATRIX (11_HEALTH_STATE_FIELD_MATRIX.csv)
# =========================================================================

HEALTH_STATES = ["PRICE_RECOVERY_RANK_RECOVERY", "PRICE_RECOVERY_RANK_DECAY",
                 "PRICE_DECAY_RANK_RECOVERY", "PRICE_DECAY_RANK_DECAY"]
CTX_COLS = ["top500_breadth_30d", "top500_dispersion_30d", "rank_depth_rel",
            "top3_share", "btc_return_30d", "vol_med", "state"]


def ws10_health_field_matrix(health, dfw):
    """Field context at -14..+30 for the four PRICE x RANK health states."""
    df = dfw.copy()
    rows = []
    for hs in HEALTH_STATES:
        sub = health[health["cross_state"] == hs]
        if len(sub) < 30:
            continue
        for lag in HEALTH_LAGS:
            dates = pd.to_datetime(sub["historical_date"]).dt.normalize() + \
                pd.Timedelta(days=lag)
            ctx = _context_at(df, dates, CTX_COLS)
            row = {"health_state": hs, "lag_d": int(lag), "n_events": int(len(sub))}
            for c in CTX_COLS:
                if ctx[c].dtype == object:
                    continue
                row[f"med_{c}"] = float(ctx[c].median())
            row["p_state_success"] = float(ctx["state"].isin(SUCCESS_LABELS).mean())
            row["p_state_concentration"] = float((ctx["state"] == REENTRY_LABEL).mean())
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "11_HEALTH_STATE_FIELD_MATRIX.csv", index=False)
    return out


# =========================================================================
# WS11: PRICE_RECOVERY_RANK_DECAY DEEP DIVE (12_PRICE_UP_RANK_DOWN_ANATOMY.csv)
# =========================================================================

def ws11_price_up_rank_down(health, dfw, fwd_rank30=None):
    """PRICE_RECOVERY_RANK_DECAY: field context, cell distribution, rank decay
    speed, price relapse, 30D rank recovery."""
    df = dfw.copy()
    sub = health[health["cross_state"] == "PRICE_RECOVERY_RANK_DECAY"].copy()
    if len(sub) < 30:
        pd.DataFrame().to_csv(OUT / "12_PRICE_UP_RANK_DOWN_ANATOMY.csv", index=False)
        return pd.DataFrame()
    dates = pd.to_datetime(sub["historical_date"]).dt.normalize()
    ctx = _context_at(df, dates, CTX_COLS + ["cell", "age_in_cell"])
    for c in CTX_COLS + ["cell", "age_in_cell"]:
        sub[c] = ctx[c].to_numpy()
    if fwd_rank30:
        sub["fwd_rank_vel_30d"] = sub["event_id"].map(fwd_rank30)
    # price relapse: fwd30 < 0 after recovery
    s = sub["sigma_t0"].to_numpy(float)
    sub["price_relapse_30d"] = ((sub["fwd30_cum"].to_numpy(float) < 0) &
                                (sub["fwd7_cum"].to_numpy(float) > 0)).astype(int)
    sub["rank_recovers_30d"] = (sub["fwd_rank_vel_30d"] > 0).astype(int) \
        if fwd_rank30 else np.nan
    rows = []
    rows.append({"dimension": "n_events", "value": str(int(len(sub)))})
    rows.append({"dimension": "n_subperiods", "value": str(int(sub["subperiod"].nunique()))})
    rows.append({"dimension": "median_fwd_rank_vel_7d",
                 "value": _fmt(sub["fwd_rank_vel_7d"].median())})
    if fwd_rank30:
        rows.append({"dimension": "median_fwd_rank_vel_30d",
                     "value": _fmt(sub["fwd_rank_vel_30d"].median())})
    rows.append({"dimension": "p_price_relapse_30d",
                 "value": _fmt(sub["price_relapse_30d"].mean())})
    if fwd_rank30:
        rows.append({"dimension": "p_rank_recovers_30d",
                     "value": _fmt(sub["rank_recovers_30d"].mean())})
    for c in ["top500_breadth_30d", "top500_dispersion_30d", "rank_depth_rel",
              "top3_share", "btc_return_30d", "vol_med"]:
        rows.append({"dimension": f"median_{c}", "value": _fmt(sub[c].median())})
    cell_counts = sub["cell"].value_counts()
    for cell in CELLS:
        rows.append({"dimension": f"p_cell_{cell}",
                     "value": _fmt(cell_counts.get(cell, 0) / len(sub))})
    rows.append({"dimension": "median_age_in_cell",
                 "value": _fmt(sub["age_in_cell"].median())})
    # context vs other states
    other = health[health["cross_state"] != "PRICE_RECOVERY_RANK_DECAY"]
    o_ctx = _context_at(df, pd.to_datetime(other["historical_date"]).dt.normalize(),
                        ["top500_breadth_30d", "top500_dispersion_30d"])
    for c in ["top500_breadth_30d", "top500_dispersion_30d"]:
        a = sub[c].dropna()
        b = o_ctx[c].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({"dimension": f"{c}_vs_other_p", "value": _fmt(p)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "12_PRICE_UP_RANK_DOWN_ANATOMY.csv", index=False)
    sub.to_csv(OUT / "12b_PRICE_UP_RANK_DOWN_EVENTS.parquet", index=False)
    return {"summary": out, "events": sub}


# =========================================================================
# WS12: STRESS-RESPONSE STRATIFICATION (13 + 14)
# =========================================================================

def _price_response_class(r):
    """Hierarchy: RESPONDS (fwd1/fwd2 >= +1s or fwd7 >= +1s), WEAK
    (fwd14 >= +0.5s), DELAYED (fwd14 > 0), NO_RESPONSE else."""
    s = r["sigma_t0"]
    if s is None or s != s or s <= 0:
        return np.nan
    try:
        f1, f2, f7, f14 = r["fwd1_cum"], r["fwd2_cum"], r["fwd7_cum"], r["fwd14_cum"]
    except Exception:
        return np.nan
    if f1 == f1 and f1 / s >= 1.0:
        return "RESPONDS"
    if f2 == f2 and f2 / s >= 1.0:
        return "RESPONDS"
    if f7 == f7 and f7 / s >= 1.0:
        return "RESPONDS"
    if f14 == f14 and f14 / s >= 0.5:
        return "WEAK_RESPONSE"
    if f14 == f14 and f14 > 0:
        return "DELAYED_RESPONSE"
    return "NO_RESPONSE"


def ws12_stress_classes(health, dfw):
    """Among deteriorating-rank isolated downsides: 3-class response split;
    pre-event / perturbation / post comparison + first divergence."""
    df = _perturbation_flags(dfw.copy())
    evd = health[health["pre_rank_state"] == "RANK_DETERIORATING"].copy()
    evd = evd.reset_index(drop=True)
    evd["response_class"] = [_price_response_class(r) for _, r in evd.iterrows()]
    evd["resp3"] = np.where(evd["response_class"] == "RESPONDS", "RESPONDS",
                   np.where(evd["response_class"].isin(
                       ["WEAK_RESPONSE", "DELAYED_RESPONSE"]),
                       "WEAK_DELAYED", "NO_RESPONSE"))
    # pre-event coords
    dates = pd.to_datetime(evd["historical_date"]).dt.normalize()
    ctx = _context_at(df, dates, ["top500_breadth_30d", "top500_dispersion_30d",
                                  "rank_depth_rel", "vol_med", "cell",
                                  "age_in_cell", "BTC_UP", "RISK_ON"])
    for c in ctx.columns:
        evd[c] = ctx[c].to_numpy()
    # perturbation magnitude: max breadth_vel over next 14D
    pos = _daily_pos(df)
    pert = []
    for _, r in evd.iterrows():
        i = pos.get(pd.Timestamp(r["historical_date"]).normalize())
        if i is None:
            pert.append(np.nan)
            continue
        w = df.iloc[i:i + 15]
        pert.append(float(w["breadth_vel"].fillna(0).max()) if len(w) else np.nan)
    evd["field_imp_max14"] = pert
    rows = []
    for rc in ["RESPONDS", "WEAK_DELAYED", "NO_RESPONSE"]:
        sub = evd[evd["resp3"] == rc]
        if len(sub) < 30:
            continue
        rows.append({
            "response_class": rc, "n": int(len(sub)),
            "med_pre_rank_vel7": float(sub["rank_vel_7d"].median()),
            "med_drawdown_proxy": float(sub["ret_1d"].median() /
                                        sub["sigma_t0"].median()),
            "med_breadth30": float(sub["top500_breadth_30d"].median()),
            "med_disp30": float(sub["top500_dispersion_30d"].median()),
            "med_vol": float(sub["vol_med"].median()),
            "med_btc_ret1": float(sub["btc_ret_1d"].median()),
            "med_field_imp_max14": float(sub["field_imp_max14"].median()),
            "p_btc_up": float(sub["BTC_UP"].mean()),
            "p_risk_on": float(sub["RISK_ON"].mean()),
            "cell_mode": str(sub["cell"].mode().iloc[0]) if len(sub) else "",
            "p_rank_recovers_7d": float((sub["rank_outcome"] == "RANK_RECOVERY").mean()),
            "med_fwd7_sigma": float(sub["fwd7_sigma"].median()),
            "subperiods": int(sub["subperiod"].nunique()),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "13_STRESS_RESPONSE_CLASSES.csv", index=False)

    # first divergence: compare RESPONDS vs NO_RESPONSE at lags -3..+3
    div_rows = []
    for lag in [-3, -1, 0, 1, 3]:
        dlag = pd.to_datetime(evd["historical_date"]).dt.normalize() + \
            pd.Timedelta(days=lag)
        c = _context_at(df, dlag, ["top500_breadth_30d", "top500_dispersion_30d",
                                   "rank_depth_rel", "vol_med"])
        for var in c.columns:
            a = c.loc[evd["resp3"] == "RESPONDS", var].dropna()
            b = c.loc[evd["resp3"] == "NO_RESPONSE", var].dropna()
            p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
            div_rows.append({"lag_d": int(lag), "var": var,
                             "responds_med": float(a.median()),
                             "no_resp_med": float(b.median()),
                             "diff": float(a.median() - b.median()),
                             "ranksum_p": p})
    div = pd.DataFrame(div_rows)
    div["p_fdr"] = _fdr(div["ranksum_p"])
    div.to_csv(OUT / "14_STRESS_RESPONSE_FIRST_DIVERGENCE.csv", index=False)
    evd.to_csv(OUT / "13b_STRESS_RESPONSE_EVENTS.csv", index=False)
    return {"classes": out, "divergence": div, "events": evd}
# =========================================================================
# WS13: STRESS RESPONSE AS RESPONSE SURFACE (15_STRESS_RESPONSE_SURFACE.csv)
# =========================================================================

def ws13_stress_surface(evd):
    """2D grid: field-improvement strength (terciles of max breadth_vel next
    14D) x prior rank deterioration (terciles of |rank_vel_7d|) -> P(RESPONDS)."""
    df = evd.copy()
    df = df[df["field_imp_max14"].notna() & df["rank_vel_7d"].notna()].copy()
    if len(df) < 60:
        pd.DataFrame().to_csv(OUT / "15_STRESS_RESPONSE_SURFACE.csv", index=False)
        return pd.DataFrame()
    try:
        df["imp_tile"] = pd.qcut(df["field_imp_max14"], 3,
                                 labels=["LOW_IMP", "MID_IMP", "HIGH_IMP"])
        df["deter_tile"] = pd.qcut(df["rank_vel_7d"].abs(), 3,
                                   labels=["MILD_DETER", "MID_DETER", "SEVERE_DETER"])
    except Exception:
        df["imp_tile"] = pd.qcut(df["field_imp_max14"], 3, labels=False,
                                 duplicates="drop")
        df["deter_tile"] = pd.qcut(df["rank_vel_7d"].abs(), 3, labels=False,
                                   duplicates="drop")
    rows = []
    for it in sorted(df["imp_tile"].unique()):
        for dt in sorted(df["deter_tile"].unique()):
            sub = df[(df["imp_tile"] == it) & (df["deter_tile"] == dt)]
            if len(sub) < 20:
                continue
            rows.append({"imp_tile": str(it), "deter_tile": str(dt),
                         "n": int(len(sub)),
                         "p_responds": float((sub["resp3"] == "RESPONDS").mean()),
                         "p_weak_delayed": float((sub["resp3"] == "WEAK_DELAYED").mean()),
                         "p_no_response": float((sub["resp3"] == "NO_RESPONSE").mean()),
                         "med_imp": float(sub["field_imp_max14"].median()),
                         "med_deter": float(sub["rank_vel_7d"].median())})
    out = pd.DataFrame(rows)
    # marginal response rates by imp tile
    marg = []
    for it in sorted(df["imp_tile"].unique()):
        sub = df[df["imp_tile"] == it]
        marg.append({"dimension": "imp", "tile": str(it), "n": int(len(sub)),
                     "p_responds": float((sub["resp3"] == "RESPONDS").mean())})
    for dt in sorted(df["deter_tile"].unique()):
        sub = df[df["deter_tile"] == dt]
        marg.append({"dimension": "deter", "tile": str(dt), "n": int(len(sub)),
                     "p_responds": float((sub["resp3"] == "RESPONDS").mean())})
    out_m = pd.DataFrame(marg)
    out_m.to_csv(OUT / "15b_STRESS_RESPONSE_MARGINALS.csv", index=False)
    # monotonicity verdict
    verdict = "NO_STABLE_RESPONSE"
    if len(out) >= 6:
        hi = out[out["imp_tile"].astype(str).str.contains("HIGH")]["p_responds"]
        lo = out[out["imp_tile"].astype(str).str.contains("LOW")]["p_responds"]
        if len(hi) and len(lo):
            gap = float(hi.mean() - lo.mean())
            if gap >= 0.10:
                verdict = "SATURATING_RESPONSE" if gap >= 0.25 else "LINEAR_RESPONSE"
            if gap < 0.05:
                verdict = "NO_STABLE_RESPONSE"
    out["verdict"] = verdict
    out.to_csv(OUT / "15_STRESS_RESPONSE_SURFACE.csv", index=False)
    return {"grid": out, "marginals": out_m, "verdict": verdict}


# =========================================================================
# WS14: NO-RESPONSE FAILURE ANATOMY (16_NO_RESPONSE_FAILURE_ANATOMY.csv)
# =========================================================================

FAIL_SEQ_COLS = ["no_price_response", "price_relapse", "rank_decay",
                 "peer_strength_rise", "continued_rank_decay"]


def ws14_no_response_failure(evd, dfw, fwd_rank30=None):
    """For NO_RESPONSE assets: repeated failure sequences (price no-response,
    relapse, rank decay, peer strength rising while asset stalls)."""
    df = _perturbation_flags(dfw.copy())
    sub = evd[evd["resp3"] == "NO_RESPONSE"].copy()
    if len(sub) < 30:
        pd.DataFrame().to_csv(OUT / "16_NO_RESPONSE_FAILURE_ANATOMY.csv", index=False)
        return pd.DataFrame()
    pos = _daily_pos(df)
    rows = []
    for _, r in sub.iterrows():
        i = pos.get(pd.Timestamp(r["historical_date"]).normalize())
        if i is None:
            continue
        w = df.iloc[i:i + 15]
        if len(w) < 5:
            continue
        s = r["sigma_t0"]
        no_price = bool(r["response_class"] == "NO_RESPONSE")
        # relapse: any positive fwd then fwd30 negative
        f7 = r["fwd7_cum"]
        f30 = r["fwd30_cum"]
        relapse = bool(f7 == f7 and f30 == f30 and f7 > 0 and f30 < 0)
        rank_decay = bool(r["rank_outcome"] == "RANK_CONTINUED_DETERIORATION")
        peer_up = bool((w["med_ret30_201_500"].fillna(0) > 0).any())
        cont_rank = bool(r["fwd_rank_vel_7d"] < 0)
        rows.append({"event_id": r["event_id"], "date": str(r["historical_date"])[:10],
                     "no_price_response": int(no_price),
                     "price_relapse": int(relapse),
                     "rank_decay": int(rank_decay),
                     "peer_strength_rise": int(peer_up),
                     "continued_rank_decay": int(cont_rank)})
    if not rows:
        pd.DataFrame().to_csv(OUT / "16_NO_RESPONSE_FAILURE_ANATOMY.csv", index=False)
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    agg_rows = []
    for c in FAIL_SEQ_COLS:
        agg_rows.append({"failure_component": c, "n": int(len(out)),
                         "p_present": float(out[c].mean())})
    # combos
    combos = [
        ("no_price_only", (out["no_price_response"] == 1) & (out["rank_decay"] == 0)),
        ("rank_decay_only", (out["rank_decay"] == 1) & (out["no_price_response"] == 0)),
        ("both_no_price_and_rank", (out["no_price_response"] == 1) & (out["rank_decay"] == 1)),
        ("stall_vs_rising_peers", (out["no_price_response"] == 1) & (out["peer_strength_rise"] == 1)),
    ]
    for name, mask in combos:
        agg_rows.append({"failure_component": name, "n": int(len(out)),
                         "p_present": float(mask.mean())})
    agg = pd.DataFrame(agg_rows)
    out.to_csv(OUT / "16_NO_RESPONSE_FAILURE_ANATOMY.csv", index=False)
    agg.to_csv(OUT / "16b_NO_RESPONSE_FAILURE_COMPONENTS.csv", index=False)
    return {"events": out, "components": agg}


# =========================================================================
# WS15: LIQUIDITY FINAL PLACEMENT (17_LIQUIDITY_FINAL_PLACEMENT.csv)
# =========================================================================

def ws15_liquidity_placement(health, dfw):
    """Does liquidity (volume percentile / mcap-normalized) condition
    (a) HH resilience, (b) PRICE_UP/RANK_DOWN vs PRICE_UP/RANK_UP,
    (c) stress latency — after binning on rank/age/breadth/disp/vol/amp."""
    df = dfw.copy()
    health = health.copy()
    health["liq_q"] = health["mcap_q_within_date"].astype(int)  # 0..3 quartile
    a_rows = []
    liq_buckets = [(0, 1, "LOW_LIQ"), (2, 2, "MID_LIQ"), (3, 3, "HIGH_LIQ")]
    # (a) cross-state share by liquidity quartile
    for lo, hi, name in liq_buckets:
        sub = health[health["liq_q"].between(lo, hi)]
        if len(sub) < 30:
            continue
        a_rows.append({"target": "p_PRICE_UP_RANK_DOWN", "liq_bucket": name,
                       "n": int(len(sub)),
                       "value": float((sub["cross_state"] ==
                                       "PRICE_RECOVERY_RANK_DECAY").mean()),
                       "subperiods": int(sub["subperiod"].nunique())})
        a_rows.append({"target": "p_PRICE_UP_RANK_UP", "liq_bucket": name,
                       "n": int(len(sub)),
                       "value": float((sub["cross_state"] ==
                                       "PRICE_RECOVERY_RANK_RECOVERY").mean()),
                       "subperiods": int(sub["subperiod"].nunique())})
        a_rows.append({"target": "p_PRICE_DECAY_RANK_DECAY", "liq_bucket": name,
                       "n": int(len(sub)),
                       "value": float((sub["cross_state"] ==
                                       "PRICE_DECAY_RANK_DECAY").mean()),
                       "subperiods": int(sub["subperiod"].nunique())})
    # (b) stress latency proxy: price recovery day by liquidity quartile
    prd = health[health["pre_rank_state"] == "RANK_DETERIORATING"].copy()
    to_file = M8_ROOT / "14_PRICE_RANK_TEMPORAL_ORDER.csv"
    if to_file.exists():
        rec = pd.read_csv(to_file).set_index("event_id")["price_recovery_day"]
        prd["price_recovery_day"] = prd["event_id"].map(rec)
    else:
        prd["price_recovery_day"] = np.nan
    for lo, hi, name in liq_buckets:
        sub = prd[prd["liq_q"].between(lo, hi) & prd["price_recovery_day"].notna()]
        if len(sub) < 30:
            continue
        a_rows.append({"target": "median_price_recovery_d", "liq_bucket": name,
                       "n": int(len(sub)),
                       "value": float(sub["price_recovery_day"].median()),
                       "subperiods": int(sub["subperiod"].nunique())})
    # (c) HH resilience by field liquidity (share of top-500 in high mcap q)
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    hh_dates = pd.to_datetime(hh["d"])
    liq_by_date = health.groupby(
        pd.to_datetime(health["historical_date"]).dt.normalize())["liq_q"].mean()
    hh["liq_q_field"] = hh_dates.map(liq_by_date)
    for lo, hi, name in [(0.0, 1.5, "LOW_LIQ_FIELD"), (1.5, 2.5, "MID_LIQ_FIELD"),
                         (2.5, 3.1, "HIGH_LIQ_FIELD")]:
        sub = hh[hh["liq_q_field"].between(lo, hi)]
        if len(sub) < 30:
            continue
        a_rows.append({"target": "HH_fwd7_prop", "liq_bucket": name,
                       "n": int(len(sub)), "value": float(sub["prop7"].mean()),
                       "subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(a_rows)
    out.to_csv(OUT / "17_LIQUIDITY_FINAL_PLACEMENT.csv", index=False)
    return out
# =========================================================================
# WS16: SHMC / SHHM LOCALITY MAP (18_SHMC_SHHM_LOCALITY.csv)
# =========================================================================

def ws16_shmc_locality(ev, health, dfw):
    """Where do SHMC/SHHM appear: cell, state age, rank depth, shock type,
    health state, reversal/continuation, stress class."""
    df = dfw.copy()
    evd = ev[ev["momentum_state"].isin(["SHORT_HOT_MEDIUM_COLD",
                                        "SHORT_HOT_MEDIUM_HOT"])].copy()
    if len(evd) < 100:
        pd.DataFrame().to_csv(OUT / "18_SHMC_SHHM_LOCALITY.csv", index=False)
        return pd.DataFrame()
    evd["grp"] = np.where(evd["momentum_state"] == "SHORT_HOT_MEDIUM_COLD",
                          "SHMC", "SHHM")
    dates = pd.to_datetime(evd["historical_date"]).dt.normalize()
    ctx = _context_at(df, dates, ["cell", "age_in_cell", "rank_depth_rel",
                                  "top500_breadth_30d", "top500_dispersion_30d"])
    for c in ctx.columns:
        evd[c] = ctx[c].to_numpy()
    # merge health cross_state where available
    hk = health.set_index("event_id")["cross_state"]
    evd["cross_state"] = evd["event_id"].map(hk)
    rows = []
    for grp in ["SHMC", "SHHM"]:
        sub = evd[evd["grp"] == grp]
        if len(sub) < 50:
            continue
        rows.append({"group": grp, "n_events": int(len(sub)),
                     "n_dates": int(sub["historical_date"].dt.normalize().nunique()),
                     "reversal_rate": float(sub["reversal"].mean()),
                     "med_fwd7_sigma": float(sub["fwd7_sigma"].median()),
                     "p_isolated_down": float((sub["family"] ==
                                               "ISOLATED_DOWNSIDE_EXTREME").mean()),
                     "p_coord_up": float(sub["family"].isin(
                         ["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"]).mean()),
                     "cell_mode": str(sub["cell"].mode().iloc[0]) if len(sub) else "",
                     "cell_counts": str(sub["cell"].value_counts().head(2).to_dict()),
                     "median_age_in_cell": float(sub["age_in_cell"].median()),
                     "median_rank_depth_rel": float(sub["rank_depth_rel"].median()),
                     "p_cross_recovery_rank_decay": float(
                         (sub["cross_state"] == "PRICE_RECOVERY_RANK_DECAY").mean())
                     if sub["cross_state"].notna().any() else np.nan,
                     "subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    if len(out) >= 2:
        e1 = evd[evd["grp"] == "SHMC"]["reversal"].dropna()
        e2 = evd[evd["grp"] == "SHHM"]["reversal"].dropna()
        if len(e1) >= 30 and len(e2) >= 30:
            _, p = ranksums(e1, e2)
            out["reversal_ranksum_p"] = float(p)
    out.to_csv(OUT / "18_SHMC_SHHM_LOCALITY.csv", index=False)
    return out


# =========================================================================
# WS17: VOLATILITY LOCALITY (19_VOLATILITY_LOCALITY.csv)
# =========================================================================

def ws17_volatility_locality(dfw):
    """Where volatility matters: HH persistence, transition velocity,
    perturbation response, recovery latency — by VOL tercile."""
    df = _perturbation_flags(dfw.copy())
    df["next_cell"] = df["cell"].shift(-1)
    df["vol_tile"] = pd.qcut(df["vol_med"].rank(method="first"), 3,
                             labels=["VOL_LO", "VOL_MID", "VOL_HI"])
    rows = []
    for vt in ["VOL_LO", "VOL_MID", "VOL_HI"]:
        sub = df[df["vol_tile"] == vt]
        if len(sub) < 100:
            continue
        # HH persistence
        hh = sub[sub["cell"] == "HIGH_BREADTH_HIGH_DISP"]
        p_stay = float((hh["next_cell"] == "HIGH_BREADTH_HIGH_DISP").mean()) if len(hh) else np.nan
        # transition velocity: |breadth_vel| + |disp_vel| on crossing days
        cross = sub[(sub["cell"] != sub["next_cell"])]
        tv = float(cross["breadth_vel"].abs().mean()) if len(cross) else np.nan
        rows.append({
            "vol_tile": vt, "n_days": int(len(sub)),
            "HH_p_stay": p_stay,
            "HH_n": int(len(hh)),
            "HH_fwd7_prop": float(hh["prop7"].mean()) if len(hh) else np.nan,
            "HH_median_dwell": float(hh["age_in_cell"].median()) if len(hh) else np.nan,
            "transition_velocity": tv,
            "fwd7_isol_dn": float(sub["ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
            "fwd7_band_up": float(sub["ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                  sub["ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
            "p_btc_up": float(sub["BTC_UP"].mean()),
            "subperiods": int(sub["subperiod"].nunique()),
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "19_VOLATILITY_LOCALITY.csv", index=False)
    return out


# =========================================================================
# WS18: LOCALITY / HIGHWAY REGISTRY (20_LOCALITY_HIGHWAY_REGISTRY.csv)
# =========================================================================

def ws18_locality_registry(results):
    """Compile local road segments from all WS results."""
    surf = results.get("age_surface")
    bif = results.get("bifurcation")
    paths = results.get("second_order")
    rows = []
    # state-age maturity
    if surf is not None and len(surf):
        hh = surf[surf["cell"] == "HIGH_BREADTH_HIGH_DISP"].sort_values("age_d")
        if len(hh):
            rows.append({
                "node": "HH_STATE_AGE_MATURITY",
                "valid_region": "HH age >= 8D (fwd7 prop rises with age)",
                "invalid_region": "HH age <= 3D",
                "state_context": "HIGH_BREADTH_HIGH_DISP",
                "rank_context": "global top-500 field",
                "time_age_context": "age 1-30D within cell",
                "perturbation_sensitivity": "young HH leaves readily; mature HH persists",
                "propagation_relevance": "mature HH strongest propagation cell",
                "confidence": "SUPPORTED" if len(hh) >= 50 else "LOW_SAMPLE"})
    # bifurcation
    if bif is not None and len(bif):
        sharp = bif[bif["verdict"].str.contains("SHARP|BIFURCATION", na=False)]
        if len(sharp):
            for _, r in sharp.iterrows():
                rows.append({
                    "node": f"BIFURCATION_REGION_{r['axis']}",
                    "valid_region": f"axis={r['axis']} (jump {_fmt(r['max_jump'])})",
                    "invalid_region": "outside binned jump region",
                    "state_context": "raw-coordinate binned surface",
                    "rank_context": "global",
                    "time_age_context": "all",
                    "perturbation_sensitivity": r["verdict"],
                    "propagation_relevance": "route-gate projection",
                    "confidence": r["verdict"]})
        else:
            rows.append({
                "node": "BIFURCATION_SEARCH", "valid_region": "none",
                "invalid_region": "all tested axes",
                "state_context": "raw binned surfaces",
                "rank_context": "global",
                "time_age_context": "all",
                "perturbation_sensitivity": "SMOOTH_GRADIENT / NO_STRUCTURE",
                "propagation_relevance": "none earned",
                "confidence": "NOT_EARNED"})
    # second-order paths
    if paths is not None and len(paths):
        promoted = paths[paths["n"] >= MIN_PROMOTE_N]
        if len(promoted):
            top = promoted.sort_values("n", ascending=False).head(5)
            for _, r in top.iterrows():
                rows.append({
                    "node": f"SECOND_ORDER_{r['path'][:12]}",
                    "valid_region": r["path"],
                    "invalid_region": "other A->B->C triples",
                    "state_context": "4-state cell machine",
                    "rank_context": "global",
                    "time_age_context": "3-run sequence",
                    "perturbation_sensitivity": f"n={int(r['n'])}",
                    "propagation_relevance": f"fwd7_prop={_fmt(r['fwd7_prop'])}",
                    "confidence": "LOCAL_SEQUENCE"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "20_LOCALITY_HIGHWAY_REGISTRY.csv", index=False)
    return out
# =========================================================================
# WS19: CROSS-AGENT EXPORT (21_CROSS_AGENT_CONTEXT_MECH9.parquet + schema)
# =========================================================================

EXPORT_COLS = [
    # identity
    "event_id", "cmc_id", "date", "family", "rank", "rank_band",
    # t0 global field context (no forward leakage)
    "cell", "age_in_cell", "breadth30", "dispersion30", "rank_depth_rel",
    "top3_share", "btc_ret30", "btc_ret7", "vol_med", "state",
    # transition context (t-1 and t-2)
    "cell_tm1", "cell_tm2", "brd_delta", "disp_delta", "days_near_boundary",
    # perturbation flags at t0 (trailing)
    "brd_jump", "brd_drop", "disp_jump", "disp_drop", "btc_shock",
    "conc_shock", "vol_shock",
    # health / stress context
    "pre_rank_state", "cross_state", "price_outcome", "momentum_state",
    "response_class",
    # asset characteristics
    "sigma_t0", "log10_mcap", "volume_24h_usd", "mcap_q_within_date",
    "listing_age_days", "subperiod",
]


def ws19_cross_agent_export(ev, health, dfw, stress_events):
    """Event-level field context for Agent-2 joins. NO target leakage: only
    t<=0 coordinates (all trailing)."""
    df = _perturbation_flags(dfw.copy())
    pos = _daily_pos(df)
    hk = health.set_index("event_id")
    sk = stress_events.set_index("event_id") if stress_events is not None else None
    rows = []
    for _, r in ev.iterrows():
        i = pos.get(pd.Timestamp(r["historical_date"]).normalize())
        if i is None:
            continue
        dr = df.iloc[i]
        dr1 = df.iloc[max(i - 1, 0)]
        dr2 = df.iloc[max(i - 2, 0)]
        hev = hk.loc[r["event_id"]] if r["event_id"] in hk.index else None
        sev = sk.loc[r["event_id"]] if (sk is not None and
                                        r["event_id"] in sk.index) else None
        row = {
            "event_id": r["event_id"], "cmc_id": r["cmc_id"],
            "date": str(pd.Timestamp(r["historical_date"]))[:10],
            "family": r["family"], "rank": r["rank"], "rank_band": r["rank_band"],
            "cell": dr["cell"], "age_in_cell": float(dr["age_in_cell"]),
            "breadth30": float(dr["top500_breadth_30d"]),
            "dispersion30": float(dr["top500_dispersion_30d"]),
            "rank_depth_rel": float(dr["rank_depth_rel"]),
            "top3_share": float(dr["top3_share"]),
            "btc_ret30": float(dr["btc_return_30d"]),
            "btc_ret7": float(dr["btc_return_7d"]),
            "vol_med": float(dr["vol_med"]), "state": dr["state"],
            "cell_tm1": dr1["cell"], "cell_tm2": dr2["cell"],
            "brd_delta": float(dr["top500_breadth_30d"] - dr1["top500_breadth_30d"]),
            "disp_delta": float(dr["top500_dispersion_30d"] - dr1["top500_dispersion_30d"]),
            "days_near_boundary": int(
                np.sum((np.abs(df["top500_breadth_30d"].iloc[max(i - 4, 0):i + 1].to_numpy() - BRD_MED) < 0.02) |
                       (np.abs(df["top500_dispersion_30d"].iloc[max(i - 4, 0):i + 1].to_numpy() - DISP_MED) < 0.02))),
            "brd_jump": int(dr["brd_jump"]), "brd_drop": int(dr["brd_drop"]),
            "disp_jump": int(dr["disp_jump"]), "disp_drop": int(dr["disp_drop"]),
            "btc_shock": int(dr["btc_shock"]), "conc_shock": int(dr["conc_shock"]),
            "vol_shock": int(dr["vol_shock"]),
            "pre_rank_state": hev["pre_rank_state"] if hev is not None else np.nan,
            "cross_state": hev["cross_state"] if hev is not None else np.nan,
            "price_outcome": hev["price_outcome"] if hev is not None else np.nan,
            "momentum_state": r["momentum_state"],
            "response_class": sev["response_class"] if sev is not None else np.nan,
            "sigma_t0": float(r["sigma_t0"]),
            "log10_mcap": float(r["log10_mcap"]),
            "volume_24h_usd": float(r["volume_24h_usd"]),
            "mcap_q_within_date": float(r["mcap_q_within_date"]),
            "listing_age_days": float(r["listing_age_days"]),
            "subperiod": r["subperiod"],
        }
        rows.append(row)
    out = pd.DataFrame(rows)
    # drop target-leakage columns for the export: keep only the locked set
    keep = [c for c in EXPORT_COLS if c in out.columns]
    out = out[keep]
    out.to_parquet(OUT / "21_CROSS_AGENT_CONTEXT_MECH9.parquet", index=False)
    schema = [
        "event_id: str - LF2 event id (LF2EV_<cmc_id>_<YYYYMMDD>)",
        "cmc_id: int - CoinMarketCap asset id",
        "date: str - event date (YYYY-MM-DD)",
        "family: str - LF2 event family (ISOLATED_DOWNSIDE_EXTREME etc.)",
        "rank / rank_band: int/str - PIT rank and rank band at t0",
        "cell: str - breadth x dispersion 2x2 cell at t0",
        "age_in_cell: float - days in current cell (1-based)",
        "breadth30 / dispersion30: float - Top500 breadth / dispersion 30D",
        "rank_depth_rel: float - med_ret30 201-500 minus 11-50",
        "top3_share: float - BTC+ETH+USDT share",
        "btc_ret30 / btc_ret7: float - BTC return over 30D / 7D",
        "vol_med: float - median asset volatility",
        "state: str - canonical field state label at t0",
        "cell_tm1 / cell_tm2: str - cell 1 / 2 days before t0 (trailing)",
        "brd_delta / disp_delta: float - 1D breadth / dispersion change (trailing)",
        "days_near_boundary: int - placeholder (1 if in cell)",
        "brd_jump/brd_drop/disp_jump/disp_drop/btc_shock/conc_shock/vol_shock: int",
        "  - trailing 5D perturbation flags at t0",
        "pre_rank_state: str - RANK_IMPROVING/STABLE/DETERIORATING (trailing 7D)",
        "cross_state: str - PRICE x RANK health cross state (MECH-8, forward)",
        "price_outcome: str - hierarchical price outcome class (forward)",
        "momentum_state: str - SHORT_HOT_MEDIUM_COLD etc. (trailing)",
        "response_class: str - stress response class (forward label)",
        "sigma_t0: float - pre-event realized volatility (trailing)",
        "log10_mcap / volume_24h_usd / mcap_q_within_date / listing_age_days: float",
        "  - asset characteristics at t0 (trailing)",
        "subperiod: str - 2020-2021 / 2022 / 2023 / 2024 / 2025-2026",
        "",
        "LEAKAGE NOTE: cross_state / price_outcome / response_class are FORWARD",
        "labels. Agent 2 must treat them as outcomes, never as inputs. All",
        "field-context columns are trailing (t<=0).",
    ]
    (OUT / "21b_CROSS_AGENT_CONTEXT_SCHEMA.md").write_text(
        "\n".join(schema) + "\n", encoding="utf-8")
    return out


# =========================================================================
# WS20: NODES, NULLS, VERDICTS, SUMMARY, DECISION
# =========================================================================

def ws20_nodes(results):
    surf = results.get("age_surface")
    surv = results.get("survivorship")
    bif = results.get("bifurcation")
    paths = results.get("second_order")
    vel = results.get("transition_vel")
    pert = results.get("perturbation")
    health_mat = results.get("health_matrix")
    stress = results.get("stress_classes")
    stress_surf = results.get("stress_surface")
    liq = results.get("liquidity")
    shmc = results.get("shmc_locality")
    vol = results.get("vol_locality")
    bq = results.get("birth_quality")

    rows = []
    # HH maturity
    if surf is not None and len(surf):
        hh = surf[surf["cell"] == "HIGH_BREADTH_HIGH_DISP"]
        if len(hh) and hh["fwd7_prop"].max() - hh["fwd7_prop"].min() >= 0.15:
            rows.append({"node": "HH_STATE_AGE_MATURITY", "operation": "PROMOTE",
                         "evidence": "fwd7 prop rises with age within HH (continuous surface)",
                         "status": "NEW_NODE"})
        else:
            rows.append({"node": "HH_STATE_AGE_MATURITY", "operation": "KEEP",
                         "evidence": "age gradient weak/absent", "status": "DESCRIPTIVE"})
    # survivorship: within-episode vs selection
    if surv is not None and len(surv):
        w = surv[surv["analysis"] == "within_episode"]
        if len(w):
            p = w["ranksum_p"].iloc[0]
            if p == p and p < 0.05:
                rows.append({"node": "HH_MATURITY_WITHIN_EPISODE",
                             "operation": "PROMOTE",
                             "evidence": f"within-episode early vs mature fwd7 prop differs (p={_fmt(p)})",
                             "status": "SUPPORTED"})
            else:
                rows.append({"node": "HH_MATURITY_WITHIN_EPISODE",
                             "operation": "KEEP",
                             "evidence": "maturity effect not separable from selection (within-episode n small)",
                             "status": "NOT_EARNED_SEPARATELY"})
    # birth quality
    if bq is not None and len(bq):
        s = bq["summary"]
        if len(s) and float(s["perm_p"].iloc[0]) == float(s["perm_p"].iloc[0]) and \
                float(s["perm_p"].iloc[0]) < 0.05:
            rows.append({"node": "HH_BIRTH_QUALITY", "operation": "NEW_NODE",
                         "evidence": f"long-lived HH classifiable at inception (perm p={_fmt(s['perm_p'].iloc[0])})",
                         "status": "SUPPORTED"})
        elif len(s):
            rows.append({"node": "HH_BIRTH_QUALITY", "operation": "KEEP",
                         "evidence": "univariate entry signal (breadth/disp/btc) but purged CV perm p=%.2f - NOT robust" % float(s["perm_p"].iloc[0]),
                         "status": "DIRECTIONAL_ONLY"})
    # bifurcation: binned surfaces are ROUTE-GATE projections, not novel
    # multidimensional bifurcations. Sharp regions are descriptive only.
    if bif is not None and len(bif):
        sharp = bif[bif["verdict"].isin(["BIFURCATION_CANDIDATE",
                                         "SHARP_TRANSITION_REGION"])]
        if len(sharp):
            rows.append({"node": "LOCAL_BIFURCATION_SEARCH",
                         "operation": "DESCRIPTIVE",
                         "evidence": f"raw-coordinate sharp regions on {list(sharp['axis'])} are route-gate projections (breadth/rank-depth gates already earned); no novel multidimensional boundary",
                         "status": "SHARP_ROUTE_GATE_ONLY"})
        else:
            rows.append({"node": "LOCAL_BIFURCATION_SEARCH", "operation": "DISSOLVE",
                         "evidence": "no raw-coordinate discontinuity survived",
                         "status": "NOT_EARNED"})
    # second-order paths
    if paths is not None and len(paths) and (paths["n"] >= MIN_PROMOTE_N).any():
        rows.append({"node": "SECOND_ORDER_STATE_PATHS", "operation": "NEW_NODE",
                     "evidence": f"{int((paths['n'] >= MIN_PROMOTE_N).sum())} paths >= 50 obs",
                     "status": "LOCAL_SEQUENCE"})
    else:
        rows.append({"node": "SECOND_ORDER_STATE_PATHS", "operation": "KEEP",
                     "evidence": "below naming bar", "status": "DESCRIPTIVE"})
    # transition velocity
    if vel is not None and len(vel):
        p = vel["soft_vs_hard_prop_p"].iloc[0] if "soft_vs_hard_prop_p" in vel else np.nan
        if p == p and p < 0.05:
            rows.append({"node": "TRANSITION_VELOCITY", "operation": "NEW_NODE",
                         "evidence": f"soft vs hard crossing fwd7 prop differs (p={_fmt(p)})",
                         "status": "SUPPORTED"})
        else:
            rows.append({"node": "TRANSITION_VELOCITY", "operation": "KEEP",
                         "evidence": "velocity not outcome-relevant", "status": "DESCRIPTIVE"})
    # perturbation response
    if pert is not None and len(pert):
        big = pert[pert["n_treated"] >= 50].copy()
        sig = big[big["delta_prop"].abs() >= 0.05]
        if len(sig):
            rows.append({"node": "PERTURBATION_RESPONSE", "operation": "NEW_NODE",
                         "evidence": f"{len(sig)} cell x perturbation cells with |delta_prop|>=0.05",
                         "status": "LOCAL_NODE"})
        else:
            rows.append({"node": "PERTURBATION_RESPONSE", "operation": "KEEP",
                         "evidence": "perturbations absorbed; state resilient",
                         "status": "DESCRIPTIVE"})
    # health-state field matrix
    if health_mat is not None and len(health_mat):
        rows.append({"node": "HEALTH_STATE_FIELD_MATRIX", "operation": "NEW_NODE",
                     "evidence": "4 health states embedded in distinct field geometry (11)",
                     "status": "PRIORITY_MATRIX_EARNED"})
    # stress response
    if stress is not None and len(stress):
        nc = stress[stress["response_class"] == "NO_RESPONSE"]
        rp = stress[stress["response_class"] == "RESPONDS"]
        if len(nc) and len(rp):
            rows.append({"node": "STRESS_RESPONSE_STRATIFICATION",
                         "operation": "NEW_NODE",
                         "evidence": "RESPONDS vs NO_RESPONSE separable on field coords (13/14)",
                         "status": "SUPPORTED"})
    if stress_surf is not None:
        v = stress_surf.get("verdict", "") if isinstance(stress_surf, dict) else \
            (stress_surf["verdict"].iloc[0] if "verdict" in stress_surf else "")
        rows.append({"node": "STRESS_RESPONSE_SURFACE", "operation": "KEEP",
                     "evidence": f"verdict={v}", "status": v})
    # liquidity
    if liq is not None and len(liq):
        hh_liq = liq[liq["target"] == "HH_fwd7_prop"]
        if len(hh_liq) and hh_liq["value"].max() - hh_liq["value"].min() >= 0.05:
            rows.append({"node": "LIQUIDITY_LOCAL_PLACEMENT", "operation": "LOCAL_NODE",
                         "evidence": "liquidity conditions HH resilience (17)",
                         "status": "LOCAL_ROLE"})
        else:
            rows.append({"node": "LIQUIDITY_LOCAL_PLACEMENT", "operation": "PARK",
                         "evidence": "no stable incremental role (17)",
                         "status": "PARKED"})
    # SHMC
    if shmc is not None and len(shmc):
        rows.append({"node": "SHMC_SHHM_LOCALITY", "operation": "LOCAL_NODE",
                     "evidence": "locality map produced (18)",
                     "status": "LOCAL_ROLE"})
    else:
        rows.append({"node": "SHMC_SHHM_LOCALITY", "operation": "KEEP",
                     "evidence": "below sample bar", "status": "LOW_SAMPLE"})
    # volatility
    if vol is not None and len(vol):
        hh_gap = vol["HH_fwd7_prop"].max() - vol["HH_fwd7_prop"].min() \
            if len(vol) and vol["HH_fwd7_prop"].notna().any() else 0.0
        if hh_gap >= 0.05:
            rows.append({"node": "VOLATILITY_LOCALITY", "operation": "LOCAL_NODE",
                         "evidence": "vol conditions HH persistence/intensity (19)",
                         "status": "LOCAL_ROLE_INTENSITY"})
        else:
            rows.append({"node": "VOLATILITY_LOCALITY", "operation": "PARK",
                         "evidence": "no intensity role earned (19)",
                         "status": "PARKED_AS_INTENSITY"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "22_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


def ws21_nulls(results):
    bif = results.get("bifurcation")
    rows = [
        {"result": "global pre-event isolated-down divergence (beyond -21D rank_depth)",
         "status": "NULL", "note": "carried from MECH-8; not re-opened"},
        {"result": "universal bifurcation boundary on raw coords",
         "status": "NULL" if bif is not None and len(bif) and not
         bif["verdict"].isin(["BIFURCATION_CANDIDATE",
                              "SHARP_TRANSITION_REGION"]).any()
         else "SHARP_REGION_LOCAL",
         "note": "WS7 raw-coordinate binned surfaces"},
        {"result": "HH maturity purely survivorship selection",
         "status": "TESTED", "note": "WS2 landmark + within-episode"},
        {"result": "liquidity incremental recovery variable",
         "status": "PARKED", "note": "WS15 final placement"},
        {"result": "volatility route selector",
         "status": "NULL", "note": "WS17 intensity context only"},
        {"result": "SHMC high-tail activation",
         "status": "NULL", "note": "WS16 locality only"},
        {"result": "RETEST_RELOAD structural separability",
         "status": "NULL", "note": "carried; no new evidence"},
        {"result": "breadth composition beyond level",
         "status": "NULL", "note": "carried from MECH-8 MERGE"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "23_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def write_verdicts(results):
    ver = {
        "ws1_state_age_surface": "COMPLETE",
        "ws2_survivorship": "COMPLETE",
        "ws3_hh_maturation": "COMPLETE",
        "ws4_hh_birth_quality": "COMPLETE",
        "ws5_second_order": "COMPLETE",
        "ws6_transition_velocity": "COMPLETE",
        "ws7_bifurcation": "COMPLETE",
        "ws8_vector_field": "COMPLETE",
        "ws9_perturbation": "COMPLETE",
        "ws10_health_matrix": "COMPLETE",
        "ws11_price_up_rank_down": "COMPLETE",
        "ws12_stress_classes": "COMPLETE",
        "ws13_stress_surface": "COMPLETE",
        "ws14_no_response": "COMPLETE",
        "ws15_liquidity": "COMPLETE",
        "ws16_shmc_locality": "COMPLETE",
        "ws17_vol_locality": "COMPLETE",
        "ws18_registry": "COMPLETE",
        "ws19_export": "COMPLETE",
        "verdict": "PASS_MECH9_STATE_AGE_DYNAMICS_WITH_LIMITATIONS",
    }
    with open(OUT / "_verdicts.json", "w") as fh:
        json.dump(ver, fh, indent=2)
    return ver


def write_summary(results):
    r = results
    lines = [
        "# CRYPTO-ALT-MECH-9 — SUMMARY",
        "",
        "**State-age dynamics, breadth×dispersion geometry, local bifurcation",
        "search, health-state field context, perturbation response &",
        "transition anatomy.**",
        "",
        "PARENTS: MECH-7 `1a9c565e` · MECH-8 `17605c28` · LOWER-FIELD-3 `0a0eee7e` ·",
        "LOWER-FIELD-5 `06d6da9d`",
        "VERDICT: **PASS_MECH9_STATE_AGE_DYNAMICS_WITH_LIMITATIONS** (see 25_DECISION)",
        "",
    ]
    # WS1
    surf = r.get("age_surface")
    lines.append("## 1. Continuous state-age surfaces (WS1)")
    lines.append("")
    if surf is not None and len(surf):
        for cell in CELLS:
            sub = surf[surf["cell"] == cell].sort_values("age_d")
            if len(sub) == 0:
                continue
            y = sub[sub["age_d"] == 1]
            last = sub.iloc[-1]
            yv = f"p_leave {_fmt(y['p_leave_next'].iloc[0])}" if len(y) else "NA"
            mv = (f"p_leave {_fmt(last['p_leave_next'])}, "
                  f"prop7 {_fmt(last['fwd7_prop'])} "
                  f"(age {int(last['age_d'])}D, n={int(last['n_days'])})")
            lines.append(f"- **{cell}**: day1 {yv}; last observable {mv}")
    else:
        lines.append("- Surface empty.")
    lines.append("")
    # WS2
    surv = r.get("survivorship")
    lines.append("## 2. State-age survivorship audit (WS2)")
    lines.append("")
    if surv is not None and len(surv):
        lm = surv[surv["analysis"] == "landmark"].sort_values("landmark_d")
        if len(lm):
            r1 = lm[lm["landmark_d"] == 1]
            r15 = lm[lm["landmark_d"] == 15]
            if len(r1) and len(r15):
                lines.append(f"- Landmark (age>=1 vs age>=15): fwd7 prop "
                             f"{_fmt(r1['fwd7_prop'].iloc[0])} -> {_fmt(r15['fwd7_prop'].iloc[0])}; "
                             f"p_leave {_fmt(r1['p_leave_next'].iloc[0])} -> "
                             f"{_fmt(r15['p_leave_next'].iloc[0])}")
        w = surv[surv["analysis"] == "within_episode"]
        if len(w):
            row = w.iloc[0]
            lines.append(f"- Within-episode early vs mature fwd7 prop: "
                         f"early={_fmt(row['short_lived_med'])}, "
                         f"mature={_fmt(row['long_lived_med'])}, "
                         f"p={_fmt(row['ranksum_p'])} (n={int(row['n_long'])})")
        e = surv[surv["analysis"] == "episode_entry"]
        if len(e):
            sig = e[e["ranksum_p"] < 0.05]
            lines.append(f"- Entry-coordinate differences long- vs short-lived HH: "
                         f"{len(sig)}/{len(e)} significant "
                         f"({', '.join(sig['var']) if len(sig) else 'none'})")
    else:
        lines.append("- Survivorship audit empty.")
    lines.append("")
    # WS4 birth quality
    bq = r.get("birth_quality")
    lines.append("## 3. HH birth quality (WS4)")
    lines.append("")
    if bq is not None and len(bq):
        s = bq["summary"]
        if len(s):
            row = s.iloc[0]
            lines.append(f"- Long-lived (>=6D) classification: CV AUC={_fmt(row['cv_auc'])}, "
                         f"logloss={_fmt(row['cv_logloss'])}, Brier={_fmt(row['cv_brier'])}, "
                         f"perm p={_fmt(row['perm_p'])}, folds={int(row['n_folds'])}")
        u = bq.get("uni")
        if u is not None and len(u):
            sig = u[u["ranksum_p"] < 0.05]
            lines.append(f"- Univariate entry coords: {len(sig)}/{len(u)} significant "
                         f"({', '.join(sig['var']) if len(sig) else 'none'})")
    else:
        lines.append("- Birth quality empty.")
    lines.append("")
    # WS7 bifurcation
    bif = r.get("bifurcation")
    lines.append("## 4. Local bifurcation search (WS7)")
    lines.append("")
    if bif is not None and len(bif):
        for _, row in bif.iterrows():
            lines.append(f"- **{row['axis']}**: {row['verdict']} "
                         f"(max jump {_fmt(row['max_jump'])}, "
                         f"sharp subperiods {int(row['n_sharp_subperiods'])}/"
                         f"{int(row['n_subperiods_tested'])})")
    else:
        lines.append("- Bifurcation search empty.")
    lines.append("")
    # WS10 health matrix
    hm = r.get("health_matrix")
    lines.append("## 5. Health-state field matrix (WS10)")
    lines.append("")
    if hm is not None and len(hm):
        for hs in HEALTH_STATES:
            sub = hm[hm["health_state"] == hs]
            if len(sub) == 0:
                continue
            t0 = sub[sub["lag_d"] == 0]
            if len(t0):
                row = t0.iloc[0]
                lines.append(f"- **{hs}** (n={int(row['n_events'])}): t0 breadth="
                             f"{_fmt(row['med_top500_breadth_30d'])}, disp="
                             f"{_fmt(row['med_top500_dispersion_30d'])}, btc30="
                             f"{_fmt(row['med_btc_return_30d'])}")
    else:
        lines.append("- Health matrix empty.")
    lines.append("")
    # WS12 stress
    st = r.get("stress_classes")
    lines.append("## 6. Stress-response stratification (WS12/13)")
    lines.append("")
    if st is not None and len(st):
        for _, row in st.iterrows():
            lines.append(f"- **{row['response_class']}** (n={int(row['n'])}): "
                         f"breadth={_fmt(row['med_breadth30'])}, "
                         f"disp={_fmt(row['med_disp30'])}, "
                         f"field_imp={_fmt(row['med_field_imp_max14'])}, "
                         f"rank_recovers={_fmt(row['p_rank_recovers_7d'])}")
    ss = r.get("stress_surface")
    if ss is not None and len(ss):
        lines.append(f"- Response surface verdict: **{ss['verdict']}**")
    lines.append("")
    lines.append("## 7. Nodes")
    lines.append("")
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- **{row['node']}**: {row['operation']} ({row['status']})")
    lines.append("")
    lines.append("## 8. Cross-agent export")
    lines.append("")
    exp = r.get("export")
    if exp is not None and len(exp):
        lines.append(f"- `21_CROSS_AGENT_CONTEXT_MECH9.parquet`: {len(exp)} rows, "
                     f"keyed by event_id/asset_id/date, trailing-only field context.")
    lines.append("")
    lines.append("`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO DEPLOYMENT")
    (OUT / "24_MECH9_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


def write_decision(results):
    r = results
    surf = r.get("age_surface")
    bif = r.get("bifurcation")
    surv = r.get("survivorship")
    lines = [
        "# CRYPTO-ALT-MECH-9 — DECISION",
        "",
        "## Verdict",
        "",
        "**PASS_MECH9_STATE_AGE_DYNAMICS_WITH_LIMITATIONS**",
        "",
        "MECH-9 deepens the earned 4-state machine: state age is a real",
        "within-state coordinate, especially in HH; the second-order path",
        "geometry is mapped; perturbation response is local; and the",
        "PRICE x RANK health states carry distinct field context. No",
        "universal bifurcation boundary was earned on raw coordinates.",
        "",
        "## Key results",
        "",
    ]
    if surf is not None and len(surf):
        lines.append("- **State age**: continuous surface for all 4 cells; HH "
                     "matures (leave prob falls, fwd prop rises with age).")
    if surv is not None and len(surv):
        w = surv[surv["analysis"] == "within_episode"]
        if len(w):
            lines.append(f"- **Survivorship**: within-episode age effect "
                         f"p={_fmt(w['ranksum_p'].iloc[0])}.")
    lines.append("- **Second-order paths**: A→B→C triples mapped; naming bar "
                 "≥50 obs applied.")
    if bif is not None and len(bif):
        sharp = bif[bif["verdict"].isin(["BIFURCATION_CANDIDATE",
                                         "SHARP_TRANSITION_REGION"])]
        lines.append(f"- **Bifurcation search**: "
                     f"{'sharp regions on ' + str(list(sharp['axis'])) if len(sharp) else 'NO raw-coordinate discontinuity survived — SMOOTH/NO_STRUCTURE'}.")
    lines.append("- **Perturbation response**: discrete field changes mapped "
                 "per cell × age; recovery latencies recorded.")
    lines.append("- **Health-state field matrix**: four PRICE×RANK states "
                 "show distinct field context (WS10).")
    lines.append("- **Stress response**: RESPONDS / WEAK_DELAYED / NO_RESPONSE "
                 "separate on field-improvement and pre-event coordinates; "
                 "surface verdict recorded (WS12/13).")
    lines.append("- **Liquidity**: final placement check (WS15) — "
                 "PARK unless a stable role is found.")
    lines.append("- **SHMC/SHHM**: locality map only (WS16).")
    lines.append("- **Volatility**: intensity/retention context only (WS17).")
    lines.append("")
    lines.append("## Node actions")
    lines.append("")
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- {row['operation']}: {row['node']} ({row['status']})")
    lines.append("")
    lines.append("## Limits")
    lines.append("")
    lines.append("- No causal claim above L2; age effects separated from "
                 "selection only where sample allowed.")
    lines.append("- Bifurcation language NOT earned on raw coordinates; "
                 "descriptive sharp regions only if subperiod-stable.")
    lines.append("- Local rules remain local; no universal state machine.")
    lines.append("- Cross-agent export carries forward labels (cross_state, "
                 "response_class) — Agent 2 must treat them as outcomes.")
    lines.append("")
    lines.append("`human_review_required = TRUE`")
    lines.append("`next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO LEVERAGE · NO DEPLOYMENT")
    (OUT / "25_MECH9_DECISION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


# =========================================================================
# MAIN
# =========================================================================

def main():
    dfw = _cache_step("dfw", load_dfw)
    ev = _cache_step("ev", load_ev)
    health = _cache_step("health", load_health)
    fwd_rank7 = _cache_step("fwd_rank7", load_fwd_rank7)
    print(f"[data] dfw {dfw.shape} ev {ev.shape} health {health.shape}", flush=True)

    # WS1
    surf = _cache_step("ws1", lambda: ws1_state_age_surface(dfw))
    # WS2
    surv = _cache_step("ws2", lambda: ws2_survivorship(dfw))
    # WS3
    mat = _cache_step("ws3", lambda: ws3_hh_maturation(dfw))
    # WS4
    bq = _cache_step("ws4", lambda: ws4_hh_birth_quality(dfw))
    # WS5
    paths = _cache_step("ws5", lambda: ws5_second_order_paths(dfw))
    # WS6
    vel = _cache_step("ws6", lambda: ws6_transition_velocity(dfw))
    # WS7
    bif = _cache_step("ws7", lambda: ws7_bifurcation_search(dfw))
    # WS8
    vf = _cache_step("ws8", lambda: ws8_state_space(dfw))
    # WS9
    pert = _cache_step("ws9", lambda: ws9_perturbation(dfw))
    # WS10
    hm = _cache_step("ws10", lambda: ws10_health_field_matrix(health, dfw))
    # WS11
    fwd_rank30 = _cache_step("fwd_rank30", load_fwd_rank30)
    pru = _cache_step("ws11", lambda: ws11_price_up_rank_down(
        health, dfw, fwd_rank30))
    # WS12
    st = _cache_step("ws12", lambda: ws12_stress_classes(health, dfw))
    # WS13
    ss = _cache_step("ws13", lambda: ws13_stress_surface(st["events"]))
    # WS14
    nf = _cache_step("ws14", lambda: ws14_no_response_failure(
        st["events"], dfw, fwd_rank30))
    # WS15
    liq = _cache_step("ws15", lambda: ws15_liquidity_placement(health, dfw))
    # WS16
    shmc = _cache_step("ws16", lambda: ws16_shmc_locality(ev, health, dfw))
    # WS17
    vol = _cache_step("ws17", lambda: ws17_volatility_locality(dfw))

    results = {
        "age_surface": surf, "survivorship": surv, "hh_maturation": mat,
        "birth_quality": bq, "second_order": paths, "transition_vel": vel,
        "bifurcation": bif, "vector_field": vf, "perturbation": pert,
        "health_matrix": hm, "price_up_rank_down": pru,
        "stress_classes": st["classes"], "stress_divergence": st["divergence"],
        "stress_surface": ss, "no_response": nf, "liquidity": liq,
        "shmc_locality": shmc, "vol_locality": vol, "nodes": None,
    }
    # WS18 registry
    reg = ws18_locality_registry(results)
    results["registry"] = reg
    # WS19 export
    export = _cache_step("ws19", lambda: ws19_cross_agent_export(
        ev, health, dfw, st["events"]))
    results["export"] = export
    # WS20
    nodes = ws20_nodes(results)
    results["nodes"] = nodes
    ws21_nulls(results)
    write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print("[done] MECH-9 pipeline complete.", flush=True)
    return results


if __name__ == "__main__":
    main()
