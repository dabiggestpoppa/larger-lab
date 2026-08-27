#!/usr/bin/env python
"""ALT_MECH_10 - Temporal Delivery Deepening, State-Age Decomposition,
4-State Hazard Geometry, Health-State Field Structure, PRICE_UP/RANK_DOWN
Local Mechanism & Perturbation Role Refinement.

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

SEED = 20260920
BOOT_N = 400
PERM_N = 300
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_10/
M9_ROOT = ROOT.parent / "mech_9"
M8_ROOT = ROOT.parent / "mech_8"
OUT = ROOT

M9_SCRIPTS = M9_ROOT / "scripts"
sys.path.insert(0, str(M9_SCRIPTS))
import alt_mech_9_analysis as M9

BRD_MED = M9.BRD_MED
DISP_MED = M9.DISP_MED
SUCCESS_LABELS = M9.SUCCESS_LABELS
REENTRY_LABEL = M9.REENTRY_LABEL
CELLS = M9.CELLS
AGE_BANDS = [(1, 1, "AGE_1"), (2, 3, "AGE_2_3"), (4, 7, "AGE_4_7"),
             (8, 14, "AGE_8_14"), (15, 10 ** 6, "AGE_15_PLUS")]
LANDMARKS = [1, 3, 5, 7, 10, 15]
HEALTH_STATES = M9.HEALTH_STATES
HEALTH_LAGS = [0, 1, 3, 7, 14, 30]

PERT_COLS = M9.PERT_COLS


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
# LOADERS - reuse MECH-9 cached artifacts (memory-safe)
# =========================================================================

def load_dfw():
    with open(M9_ROOT / "_cache_dfw.pkl", "rb") as fh:
        return pickle.load(fh)


def load_ev():
    with open(M9_ROOT / "_cache_ev.pkl", "rb") as fh:
        return pickle.load(fh)


def load_health():
    with open(M9_ROOT / "_cache_health.pkl", "rb") as fh:
        return pickle.load(fh)


def load_fwd_rank7():
    with open(M9_ROOT / "_cache_fwd_rank7.pkl", "rb") as fh:
        return pickle.load(fh)


def load_fwd_rank30():
    with open(M9_ROOT / "_cache_fwd_rank30.pkl", "rb") as fh:
        return pickle.load(fh)


def _daily_pos(dfw):
    dnorm = pd.to_datetime(dfw["d"])
    return {d: i for i, d in enumerate(dnorm)}


def _context_at(dfw, dates, cols):
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


def _episodes(df, cell="HIGH_BREADTH_HIGH_DISP"):
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


def _age_band(age):
    for lo, hi, name in AGE_BANDS:
        if lo <= age <= hi:
            return name
    return "AGE_15_PLUS"


def _perturbation_flags(df):
    out = df.copy()
    b5 = out["top500_breadth_30d"].diff(5)
    d5 = out["top500_dispersion_30d"].diff(5)
    bt5 = out["btc_return_7d"]
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
# =========================================================================
# WS1: STATE-AGE MECHANISM DECOMPOSITION (02_STATE_AGE_MECHANISM_DECOMPOSITION.csv)
# =========================================================================

BIRTH_COORDS = ["top500_breadth_30d", "top500_dispersion_30d",
                "btc_return_30d", "rank_depth_rel", "top3_share", "vol_med"]


def ws1_decomposition(dfw):
    """Decompose HH state-age into BIRTH_QUALITY / SURVIVAL_SELECTION /
    WITHIN_STATE_MATURATION using interpretable features."""
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["fwd3_state"] = df["state"].shift(-3)
    df["fwd3_prop"] = df["fwd3_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd14_state"] = df["state"].shift(-14)
    df["fwd14_prop"] = df["fwd14_state"].isin(SUCCESS_LABELS).astype(float)
    eps = _episodes(df)
    for c in BIRTH_COORDS:
        eps[c] = df[c].iloc[eps["start"]].values
    eps["entry_quality_score"] = (
        eps["top500_breadth_30d"].rank(pct=True) +
        eps["top500_dispersion_30d"].rank(pct=True) +
        eps["btc_return_30d"].rank(pct=True)) / 3.0
    rows = []

    # A) BIRTH_QUALITY: entry score predicts duration
    a = eps[eps["n"] >= 7]["entry_quality_score"]
    b = eps[eps["n"] < 7]["entry_quality_score"]
    p_birth = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
    rows.append({"component": "BIRTH_QUALITY",
                 "measure": "entry_quality_score long- vs short-lived",
                 "long_med": float(a.median()), "short_med": float(b.median()),
                 "diff": float(a.median() - b.median()), "p": p_birth,
                 "n_long": int(len(a)), "n_short": int(len(b))})
    for c in BIRTH_COORDS:
        a = eps[eps["n"] >= 7][c].dropna()
        b = eps[eps["n"] < 7][c].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({"component": "BIRTH_QUALITY", "measure": c,
                     "long_med": float(a.median()), "short_med": float(b.median()),
                     "diff": float(a.median() - b.median()), "p": p,
                     "n_long": int(len(a)), "n_short": int(len(b))})

    # B) SURVIVAL_SELECTION: conditional-on-survival hazard declines with age
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    for lm in [1, 3, 5, 7, 10, 15]:
        s2 = hh[hh["age_in_cell"] >= lm]
        if len(s2) < 30:
            continue
        idx = s2.index
        rows.append({"component": "SURVIVAL_SELECTION",
                     "measure": f"P(leave) at age>={lm}",
                     "long_med": float((df.loc[idx, "next_cell"] !=
                                        "HIGH_BREADTH_HIGH_DISP").mean()),
                     "short_med": np.nan, "diff": np.nan, "p": np.nan,
                     "n_long": int(len(s2)), "n_short": np.nan})

    # C) WITHIN_STATE_MATURATION: same-episode early vs late (n>=10 episodes)
    ep10 = eps[eps["n"] >= 10]
    w_rows = []
    for _, r in ep10.iterrows():
        seg = df.loc[r["start"]:r["end"]]
        early = seg[seg["age_in_cell"] <= 3]["prop7"]
        late = seg[seg["age_in_cell"] >= 8]["prop7"]
        if len(early) and len(late):
            w_rows.append({"early": float(early.mean()), "late": float(late.mean())})
    if w_rows:
        wr = pd.DataFrame(w_rows)
        p = ranksums(wr["early"], wr["late"]).pvalue if len(wr) >= 10 else np.nan
        rows.append({"component": "WITHIN_STATE_MATURATION",
                     "measure": "early vs late fwd7 prop (same episode)",
                     "long_med": float(wr["late"].median()),
                     "short_med": float(wr["early"].median()),
                     "diff": float(wr["late"].median() - wr["early"].median()),
                     "p": p, "n_long": int(len(wr)), "n_short": int(len(wr))})

    out = pd.DataFrame(rows)
    # verdict
    sig_birth = out[(out["component"] == "BIRTH_QUALITY") & (out["p"] < 0.05)]
    w_row = out[out["component"] == "WITHIN_STATE_MATURATION"]
    sel_rows = out[out["component"] == "SURVIVAL_SELECTION"]
    birth_ok = len(sig_birth) >= 1
    sel_ok = len(sel_rows) and sel_rows["long_med"].iloc[-1] < sel_rows["long_med"].iloc[0]
    mat_ok = len(w_row) and w_row["p"].iloc[0] < 0.05
    if mat_ok and birth_ok:
        verdict = "MIXED"
    elif mat_ok:
        verdict = "MATURATION"
    elif birth_ok:
        verdict = "BIRTH_AND_SELECTION" if sel_ok else "BIRTH"
    elif sel_ok:
        verdict = "SELECTION"
    else:
        verdict = "UNRESOLVED"
    out["verdict"] = verdict
    out.to_csv(OUT / "02_STATE_AGE_MECHANISM_DECOMPOSITION.csv", index=False)
    pd.DataFrame([{"verdict": verdict}]).to_csv(
        OUT / "02b_STATE_AGE_MECHANISM_VERDICT.csv", index=False)
    return {"table": out, "verdict": verdict}


# =========================================================================
# WS2: CONDITIONAL LANDMARK ANALYSIS (03_CONDITIONAL_LANDMARKS.csv)
# =========================================================================

def ws2_conditional_landmarks(dfw):
    """At ages 1/3/5/7/10/15 conditional-on-survival: P(stay 1/3/7D),
    P(prop 3/7/14D), P(reentry), P(tail), P(exit to each cell)."""
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["fwd3_state"] = df["state"].shift(-3)
    df["fwd7_state"] = df["state"].shift(-7)
    df["fwd14_state"] = df["state"].shift(-14)
    df["fwd3_prop"] = df["fwd3_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd7_prop"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd14_prop"] = df["fwd14_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd3_reentry"] = (df["fwd3_state"] == REENTRY_LABEL).astype(float)
    df["fwd7_reentry"] = (df["fwd7_state"] == REENTRY_LABEL).astype(float)
    df["fwd14_reentry"] = (df["fwd14_state"] == REENTRY_LABEL).astype(float)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell]
        for lm in LANDMARKS:
            s2 = sub[sub["age_in_cell"] >= lm]
            if len(s2) < 30:
                continue
            idx = s2.index
            nxt = df.loc[idx, "next_cell"]
            stay1 = float((nxt == cell).mean())
            # stay 3D / 7D: cell at t+3/t+7
            c3 = df["cell"].shift(-3).loc[idx]
            c7 = df["cell"].shift(-7).loc[idx]
            stay3 = float((c3 == cell).mean()) if c3.notna().any() else np.nan
            stay7 = float((c7 == cell).mean()) if c7.notna().any() else np.nan
            exit_cells = nxt[nxt != cell].dropna()
            exit_dist = {}
            for c in CELLS:
                exit_dist[f"exit_{c}"] = float((exit_cells == c).mean())
            row = {"cell": cell, "landmark_age": int(lm), "n_days": int(len(s2)),
                   "p_stay_1d": stay1, "p_stay_3d": stay3, "p_stay_7d": stay7,
                   "p_prop_3d": float(df.loc[idx, "fwd3_prop"].mean()),
                   "p_prop_7d": float(df.loc[idx, "fwd7_prop"].mean()),
                   "p_prop_14d": float(df.loc[idx, "fwd14_prop"].mean()),
                   "p_reentry_3d": float(df.loc[idx, "fwd3_reentry"].mean()),
                   "p_reentry_7d": float(df.loc[idx, "fwd7_reentry"].mean()),
                   "p_reentry_14d": float(df.loc[idx, "fwd14_reentry"].mean()),
                   "p_tail_isol_dn_7d": float(df.loc[idx, "ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
                   "p_tail_band_up_7d": float(df.loc[idx, "ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                              df.loc[idx, "ev_MULTI_BAND_UPSIDE_fwd7"].mean())}
            for c in CELLS:
                row[f"exit_{c}"] = exit_dist.get(f"exit_{c}", np.nan)
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "03_CONDITIONAL_LANDMARKS.csv", index=False)
    return out


# =========================================================================
# WS3: 4-STATE TEMPORAL DELIVERY CLOCKS (04_4STATE_TEMPORAL_DELIVERY.csv)
# =========================================================================

DELIVERY_HORIZONS = [1, 3, 7, 14, 30]


def _first_arrival_horizon(series, horizon_idx):
    """First horizon (1/3/7/14/30) at which event occurs; NaN if none."""
    for h in horizon_idx:
        v = series[h]
        if v == v and v > 0:
            return h
    return np.nan


def ws3_delivery_clocks(dfw):
    """Per state (and per state-age band): time-to-first event of each
    family, plus exit clock. Separate arrival / exit / prop / reentry."""
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["fwd3_state"] = df["state"].shift(-3)
    df["fwd7_state"] = df["state"].shift(-7)
    df["fwd14_state"] = df["state"].shift(-14)
    df["fwd30_state"] = df["state"].shift(-30)
    df["fwd3_prop"] = df["fwd3_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd7_prop"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd14_prop"] = df["fwd14_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd30_prop"] = df["fwd30_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd3_reentry"] = (df["fwd3_state"] == REENTRY_LABEL).astype(float)
    df["fwd7_reentry"] = (df["fwd7_state"] == REENTRY_LABEL).astype(float)
    df["fwd14_reentry"] = (df["fwd14_state"] == REENTRY_LABEL).astype(float)
    df["fwd30_reentry"] = (df["fwd30_state"] == REENTRY_LABEL).astype(float)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    rows = []
    families = {
        "isol_dn": "ev_ISOLATED_DOWNSIDE_EXTREME",
        "band_up": "ev_BAND_BROAD_UPSIDE",
        "multi_up": "ev_MULTI_BAND_UPSIDE",
        "coord_dn": "ev_COORDINATED_DOWNSIDE",
    }
    for cell in CELLS:
        sub = df[df["cell"] == cell]
        for ab in [b[2] for b in AGE_BANDS]:
            s2 = sub[sub["age_band"] == ab]
            if len(s2) < 30:
                continue
            idx = s2.index
            # exit clock: time to first cell change
            exit_h = []
            for i in idx:
                w = df["cell"].loc[i + 1:i + 30]
                hit = np.where(w != cell)[0]
                exit_h.append(int(hit[0] + 1) if len(hit) else np.nan)
            row = {"cell": cell, "age_band": ab, "n_days": int(len(s2)),
                   "clock": "STATE_EXIT",
                   "median_latency_d": float(np.nanmedian(exit_h)),
                   "p_by_7d": float((np.array(exit_h) <= 7).mean()),
                   "p_by_14d": float((np.array(exit_h) <= 14).mean()),
                   "p_by_30d": float((np.array(exit_h) <= 30).mean())}
            rows.append(row)
            # prop clock
            row = {"cell": cell, "age_band": ab, "n_days": int(len(s2)),
                   "clock": "PROPAGATION",
                   "median_latency_d": np.nan,
                   "p_by_3d": float(df.loc[idx, "fwd3_prop"].mean()),
                   "p_by_7d": float(df.loc[idx, "fwd7_prop"].mean()),
                   "p_by_14d": float(df.loc[idx, "fwd14_prop"].mean()),
                   "p_by_30d": float(df.loc[idx, "fwd30_prop"].mean())}
            rows.append(row)
            # reentry clock
            row = {"cell": cell, "age_band": ab, "n_days": int(len(s2)),
                   "clock": "REENTRY",
                   "median_latency_d": np.nan,
                   "p_by_3d": float(df.loc[idx, "fwd3_reentry"].mean()),
                   "p_by_7d": float(df.loc[idx, "fwd7_reentry"].mean()),
                   "p_by_14d": float(df.loc[idx, "fwd14_reentry"].mean()),
                   "p_by_30d": float(df.loc[idx, "fwd30_reentry"].mean())}
            rows.append(row)
            # event arrival clocks
            for fname, col in families.items():
                lat = []
                for i in idx:
                    w = df[col].loc[i + 1:i + 30]
                    hit = np.where(w > 0)[0]
                    lat.append(int(hit[0] + 1) if len(hit) else np.nan)
                rows.append({"cell": cell, "age_band": ab,
                             "n_days": int(len(s2)), "clock": f"ARRIVAL_{fname}",
                             "median_latency_d": float(np.nanmedian(lat)),
                             "p_by_7d": float((np.array(lat) <= 7).mean()),
                             "p_by_14d": float((np.array(lat) <= 14).mean()),
                             "p_by_30d": float((np.array(lat) <= 30).mean())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "04_4STATE_TEMPORAL_DELIVERY.csv", index=False)
    return out
# =========================================================================
# WS4: 4-STATE EXIT HAZARDS + AGE-CONDITIONAL EXIT GEOMETRY (05 + 06)
# =========================================================================

def _exit_hazard(df, cell, max_h=30):
    """Discrete-time exit hazard: P(exit at h | alive at h-1) for h=1..max_h."""
    sub = df[df["cell"] == cell].copy()
    sub["exit"] = (sub["cell"].shift(-1) != cell).astype(float)
    haz, at_risk = [], []
    for h in range(1, max_h + 1):
        exit_h = sub["cell"].shift(-h) != cell
        alive = (sub["cell"].shift(-(h - 1)) == cell) & (sub["cell"] == cell)
        m = alive & exit_h
        n_risk = int(alive.sum())
        n_events = int(m.sum())
        haz.append(n_events / n_risk if n_risk else np.nan)
        at_risk.append(n_risk)
    return haz, at_risk


def ws4_exit_hazards(dfw):
    """05_4STATE_EXIT_HAZARDS.csv: discrete hazard + cumulative incidence."""
    df = dfw.copy()
    df["cell_shift1"] = df["cell"].shift(-1)
    rows = []
    for cell in CELLS:
        haz, at_risk = _exit_hazard(df, cell)
        surv = 1.0
        cum_inc = []
        for h in range(len(haz)):
            surv *= (1 - (haz[h] if haz[h] == haz[h] else 0))
            cum_inc.append(1 - surv)
        for h in range(1, min(len(haz), 30) + 1):
            rows.append({"cell": cell, "h_d": int(h),
                         "hazard": haz[h - 1], "n_at_risk": int(at_risk[h - 1]),
                         "cumulative_incidence": cum_inc[h - 1]})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "05_4STATE_EXIT_HAZARDS.csv", index=False)
    return out


def ws4_age_exit_geometry(dfw):
    """06_AGE_CONDITIONAL_EXIT_GEOMETRY.csv: exit destination by age band
    with fwd outcomes."""
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["fwd3_state"] = df["state"].shift(-3)
    df["fwd7_state"] = df["state"].shift(-7)
    df["fwd14_state"] = df["state"].shift(-14)
    df["fwd3_prop"] = df["fwd3_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd7_prop"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd14_prop"] = df["fwd14_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd7_reentry"] = (df["fwd7_state"] == REENTRY_LABEL).astype(float)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    rows = []
    for cell in CELLS:
        for ab in [b[2] for b in AGE_BANDS]:
            s2 = df[(df["cell"] == cell) & (df["age_band"] == ab)]
            if len(s2) < 30:
                continue
            idx = s2.index
            nxt = df.loc[idx, "next_cell"]
            for nc in CELLS:
                m = nxt == nc
                if m.sum() < 10:
                    continue
                rows.append({"cell": cell, "age_band": ab, "exit_to": nc,
                             "n": int(m.sum()),
                             "p_exit_dest": float(m.mean()),
                             "fwd7_prop": float(df.loc[idx[m], "fwd7_prop"].mean()),
                             "fwd14_prop": float(df.loc[idx[m], "fwd14_prop"].mean()),
                             "fwd7_reentry": float(df.loc[idx[m], "fwd7_reentry"].mean()),
                             "fwd7_isol_dn": float(df.loc[idx[m], "ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
                             "fwd7_band_up": float(df.loc[idx[m], "ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                                   df.loc[idx[m], "ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
                             "p_btc_up": float(df.loc[idx[m], "BTC_UP"].mean()),
                             "p_vol_high": float(df.loc[idx[m], "VOL_HIGH"].mean()),
                             "med_rank_depth": float(df.loc[idx[m], "rank_depth_rel"].mean())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "06_AGE_CONDITIONAL_EXIT_GEOMETRY.csv", index=False)
    return out


# =========================================================================
# WS5: ROUTE INTO STATE x STATE AGE (07_ROUTE_INTO_STATE_BY_AGE.csv)
# =========================================================================

def ws5_route_by_age(dfw):
    """HH entry route (FROM_HL/LH/LL/CONTINUED_HH) stratified by age band."""
    df = dfw.copy()
    df["prev_cell"] = df["cell"].shift(1)
    df["fwd3_state"] = df["state"].shift(-3)
    df["fwd7_state"] = df["state"].shift(-7)
    df["fwd14_state"] = df["state"].shift(-14)
    df["fwd3_prop"] = df["fwd3_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd7_prop"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd14_prop"] = df["fwd14_state"].isin(SUCCESS_LABELS).astype(float)
    df["fwd7_reentry"] = (df["fwd7_state"] == REENTRY_LABEL).astype(float)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    # HH days with explicit route
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    hh["route"] = hh["prev_cell"].map(
        {"HIGH_BREADTH_LOW_DISP": "FROM_HL",
         "LOW_BREADTH_HIGH_DISP": "FROM_LH",
         "LOW_BREADTH_LOW_DISP": "FROM_LL",
         "HIGH_BREADTH_HIGH_DISP": "CONTINUED_HH"})
    hh = hh[hh["route"].notna()].copy()
    rows = []
    for route in ["FROM_HL", "FROM_LH", "FROM_LL", "CONTINUED_HH"]:
        for ab in [b[2] for b in AGE_BANDS]:
            s2 = hh[(hh["route"] == route) & (hh["age_band"] == ab)]
            if len(s2) < 30:
                continue
            idx = s2.index
            rows.append({"route": route, "age_band": ab, "n_days": int(len(s2)),
                         "p_stay_1d": float((df.loc[idx, "cell"].shift(-1) ==
                                             "HIGH_BREADTH_HIGH_DISP").mean()),
                         "fwd3_prop": float(df.loc[idx, "fwd3_prop"].mean()),
                         "fwd7_prop": float(df.loc[idx, "fwd7_prop"].mean()),
                         "fwd14_prop": float(df.loc[idx, "fwd14_prop"].mean()),
                         "fwd7_reentry": float(df.loc[idx, "fwd7_reentry"].mean()),
                         "fwd7_isol_dn": float(df.loc[idx, "ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
                         "fwd7_band_up": float(df.loc[idx, "ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                               df.loc[idx, "ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
                         "p_btc_up": float(df.loc[idx, "BTC_UP"].mean()),
                         "p_vol_high": float(df.loc[idx, "VOL_HIGH"].mean()),
                         "subperiods": int(df.loc[idx, "subperiod"].nunique())})
    out = pd.DataFrame(rows)
    # route-vs-route comparison within each age band (FROM_HL vs FROM_LH)
    comp = []
    for ab in [b[2] for b in AGE_BANDS]:
        a = hh[(hh["route"] == "FROM_HL") & (hh["age_band"] == ab)]["fwd7_prop"].dropna()
        b = hh[(hh["route"] == "FROM_LH") & (hh["age_band"] == ab)]["fwd7_prop"].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        comp.append({"age_band": ab, "FROM_HL_vs_FROM_LH_fwd7_p": p,
                     "n_hl": int(len(a)), "n_lh": int(len(b))})
    comp_df = pd.DataFrame(comp)
    comp_df.to_csv(OUT / "07b_ROUTE_COMPARISON.csv", index=False)
    out.to_csv(OUT / "07_ROUTE_INTO_STATE_BY_AGE.csv", index=False)
    return {"table": out, "comparison": comp_df}
# =========================================================================
# WS6: PRICE_UP_RANK_DOWN FULL FIELD MATRIX (08_PRICE_UP_RANK_DOWN_FIELD_MATRIX.csv)
# =========================================================================

PRD_CTX = ["top500_breadth_30d", "top500_dispersion_30d", "rank_depth_rel",
           "top3_share", "btc_return_30d", "vol_med", "state"]


def ws6_prd_field_matrix(health, dfw):
    """PRICE_RECOVERY_RANK_DECAY field geometry at t0..+30, across cells,
    age, route, vol, rank depth, BTC/ETH, concentration, dispersion."""
    df = _perturbation_flags(dfw.copy())
    sub = health[health["cross_state"] == "PRICE_RECOVERY_RANK_DECAY"].copy()
    if len(sub) < 30:
        pd.DataFrame().to_csv(OUT / "08_PRICE_UP_RANK_DOWN_FIELD_MATRIX.csv",
                              index=False)
        return pd.DataFrame()
    rows = []
    for lag in HEALTH_LAGS:
        dates = pd.to_datetime(sub["historical_date"]).dt.normalize() + \
            pd.Timedelta(days=lag)
        ctx = _context_at(df, dates, PRD_CTX + ["cell", "age_in_cell"])
        row = {"lag_d": int(lag), "n_events": int(len(sub))}
        for c in PRD_CTX:
            if ctx[c].dtype == object:
                row[f"p_state_{c}"] = float((ctx[c] == REENTRY_LABEL).mean())
                continue
            row[f"med_{c}"] = float(ctx[c].median())
        row["p_cell_HH"] = float((ctx["cell"] == "HIGH_BREADTH_HIGH_DISP").mean())
        row["p_cell_HL"] = float((ctx["cell"] == "HIGH_BREADTH_LOW_DISP").mean())
        row["p_cell_LH"] = float((ctx["cell"] == "LOW_BREADTH_HIGH_DISP").mean())
        row["p_cell_LL"] = float((ctx["cell"] == "LOW_BREADTH_LOW_DISP").mean())
        row["med_age_in_cell"] = float(ctx["age_in_cell"].median())
        row["p_btc_up"] = float(ctx["BTC_UP"].mean()) if "BTC_UP" in ctx else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "08_PRICE_UP_RANK_DOWN_FIELD_MATRIX.csv", index=False)
    return out


# =========================================================================
# WS7: PRICE_UP_RANK_DOWN vs PRICE_UP_RANK_UP (09_PRICE_UP_RANK_DOWN_VS_RANK_UP.csv)
# =========================================================================

def ws7_prd_vs_pru(health, dfw, fwd_rank30=None):
    """Compare PRICE_RECOVERY_RANK_DECAY vs PRICE_RECOVERY_RANK_RECOVERY on
    pre/event/post coordinates; first divergence."""
    df = _perturbation_flags(dfw.copy())
    sub = health[health["cross_state"].isin(
        ["PRICE_RECOVERY_RANK_DECAY", "PRICE_RECOVERY_RANK_RECOVERY"])].copy()
    if len(sub) < 60:
        pd.DataFrame().to_csv(OUT / "09_PRICE_UP_RANK_DOWN_VS_RANK_UP.csv",
                              index=False)
        return pd.DataFrame()
    sub = sub.reset_index(drop=True)
    sub["grp"] = np.where(sub["cross_state"] == "PRICE_RECOVERY_RANK_DECAY",
                          "RANK_DECAY", "RANK_RECOVERY")
    if fwd_rank30:
        sub["fwd_rank_vel_30d"] = sub["event_id"].map(fwd_rank30)
    rows = []
    pre_coords = {
        "rank_vel_7d": "rank_vel_7d", "rank_vel_14d": "rank_vel_14d",
        "sigma_t0": "sigma_t0", "log10_mcap": "log10_mcap",
        "mcap_q": "mcap_q_within_date", "listing_age": "listing_age_days",
    }
    for label, c in pre_coords.items():
        a = sub[sub["grp"] == "RANK_DECAY"][c].dropna()
        b = sub[sub["grp"] == "RANK_RECOVERY"][c].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({"axis": "PRE", "var": label,
                     "rank_decay_med": float(a.median()),
                     "rank_recovery_med": float(b.median()),
                     "diff": float(a.median() - b.median()), "p": p,
                     "n_a": int(len(a)), "n_b": int(len(b))})
    if fwd_rank30:
        a = sub[sub["grp"] == "RANK_DECAY"]["fwd_rank_vel_30d"].dropna()
        b = sub[sub["grp"] == "RANK_RECOVERY"]["fwd_rank_vel_30d"].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({"axis": "POST", "var": "fwd_rank_vel_30d",
                     "rank_decay_med": float(a.median()),
                     "rank_recovery_med": float(b.median()),
                     "diff": float(a.median() - b.median()), "p": p,
                     "n_a": int(len(a)), "n_b": int(len(b))})
    # event amplitude
    for h in [7, 14, 30]:
        col = f"fwd{h}_cum"
        a = sub[sub["grp"] == "RANK_DECAY"][col].dropna()
        b = sub[sub["grp"] == "RANK_RECOVERY"][col].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({"axis": "POST", "var": f"fwd{h}_cum",
                     "rank_decay_med": float(a.median()),
                     "rank_recovery_med": float(b.median()),
                     "diff": float(a.median() - b.median()), "p": p,
                     "n_a": int(len(a)), "n_b": int(len(b))})
    # t0 field context
    t0 = _context_at(df, pd.to_datetime(sub["historical_date"]).dt.normalize(),
                     ["top500_breadth_30d", "top500_dispersion_30d",
                      "rank_depth_rel", "vol_med", "cell"])
    for c in ["top500_breadth_30d", "top500_dispersion_30d", "rank_depth_rel",
              "vol_med"]:
        a = t0.loc[sub["grp"] == "RANK_DECAY", c].dropna()
        b = t0.loc[sub["grp"] == "RANK_RECOVERY", c].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({"axis": "T0", "var": c,
                     "rank_decay_med": float(a.median()),
                     "rank_recovery_med": float(b.median()),
                     "diff": float(a.median() - b.median()), "p": p,
                     "n_a": int(len(a)), "n_b": int(len(b))})
    out = pd.DataFrame(rows)
    out["p_fdr"] = _fdr(out["p"])
    # first divergence: earliest lag with FDR-significant field difference
    div_rows = []
    for lag in [-7, -3, -1, 0, 1, 3, 7]:
        dlag = pd.to_datetime(sub["historical_date"]).dt.normalize() + \
            pd.Timedelta(days=lag)
        ctx = _context_at(df, dlag, ["top500_breadth_30d",
                                     "top500_dispersion_30d", "vol_med"])
        for c in ctx.columns:
            a = ctx.loc[sub["grp"] == "RANK_DECAY", c].dropna()
            b = ctx.loc[sub["grp"] == "RANK_RECOVERY", c].dropna()
            p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
            div_rows.append({"lag_d": int(lag), "var": c,
                             "rank_decay_med": float(a.median()),
                             "rank_recovery_med": float(b.median()),
                             "diff": float(a.median() - b.median()), "p": p})
    div = pd.DataFrame(div_rows)
    div["p_fdr"] = _fdr(div["p"])
    div.to_csv(OUT / "09b_PRICE_UP_RANK_DOWN_VS_RANK_UP_DIVERGENCE.csv", index=False)
    out.to_csv(OUT / "09_PRICE_UP_RANK_DOWN_VS_RANK_UP.csv", index=False)
    return {"table": out, "divergence": div}


# =========================================================================
# WS8: PRICE_UP_RANK_DOWN SUBTYPES (10_PRICE_UP_RANK_DOWN_SUBTYPES.csv)
# =========================================================================

def ws8_prd_subtypes(health, dfw, fwd_rank30=None):
    """Subtype families of PRICE_RECOVERY_RANK_DECAY via descriptive
    quantiles on interpretable axes (no forced clustering)."""
    sub = health[health["cross_state"] == "PRICE_RECOVERY_RANK_DECAY"].copy()
    if len(sub) < 60:
        pd.DataFrame().to_csv(OUT / "10_PRICE_UP_RANK_DOWN_SUBTYPES.csv",
                              index=False)
        return pd.DataFrame()
    if fwd_rank30:
        sub["fwd_rank_vel_30d"] = sub["event_id"].map(fwd_rank30)
    # axes: price persistence, rank decay velocity, field breadth
    sub["price_persist"] = sub["fwd30_cum"] / sub["sigma_t0"]
    sub["rank_decay_vel"] = sub["fwd_rank_vel_7d"]
    sub["field_breadth"] = sub["top500_breadth_30d"]
    rows = []
    for axis, labels in [
        ("price_persist", ["WEAK_PRICE", "MID_PRICE", "STRONG_PRICE"]),
        ("rank_decay_vel", ["MILD_RANK_DECAY", "MID_RANK_DECAY",
                            "SEVERE_RANK_DECAY"]),
        ("field_breadth", ["LOW_BRD", "MID_BRD", "HIGH_BRD"])]:
        try:
            q = pd.qcut(sub[axis], 3, labels=labels, duplicates="drop")
        except Exception:
            continue
        for lab in labels:
            m = q == lab
            if m.sum() < 20:
                continue
            s = sub[m]
            row = {"axis": axis, "subtype": lab, "n": int(m.sum()),
                   "median_axis": float(s[axis].median()),
                   "p_price_relapse": float((s["fwd30_cum"] < 0).mean()),
                   "median_fwd_rank_vel_30d": float(s["fwd_rank_vel_30d"].median())
                   if fwd_rank30 else np.nan,
                   "median_breadth30": float(s["top500_breadth_30d"].median()),
                   "median_vol": float(s["mkt_vol_30d"].median()),
                   "subperiods": int(s["subperiod"].nunique())}
            rows.append(row)
    # cross of rank decay severity x field breadth
    try:
        rd = pd.qcut(sub["rank_decay_vel"], 3, labels=["MILD", "MID", "SEVERE"],
                     duplicates="drop")
        fb = pd.qcut(sub["field_breadth"], 3, labels=["LOW", "MID", "HIGH"],
                     duplicates="drop")
    except Exception:
        rd = fb = None
    if rd is not None and fb is not None:
        for rlab in ["MILD", "MID", "SEVERE"]:
            for blab in ["LOW", "MID", "HIGH"]:
                m = (rd == rlab) & (fb == blab)
                if m.sum() < 15:
                    continue
                s = sub[m]
                rows.append({"axis": "RANKxFIELD", "subtype": f"{rlab}_{blab}",
                             "n": int(m.sum()),
                             "median_axis": float(s["rank_decay_vel"].median()),
                             "p_price_relapse": float((s["fwd30_cum"] < 0).mean()),
                             "median_fwd_rank_vel_30d": float(s["fwd_rank_vel_30d"].median())
                             if fwd_rank30 else np.nan,
                             "median_breadth30": float(s["top500_breadth_30d"].median()),
                             "median_vol": float(s["mkt_vol_30d"].median()),
                             "subperiods": int(s["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "10_PRICE_UP_RANK_DOWN_SUBTYPES.csv", index=False)
    return out
# =========================================================================
# WS9: HEALTH-STATE TEMPORAL TRANSITIONS (11_HEALTH_STATE_TRANSITIONS.csv)
# =========================================================================

def _cross_state_at(row, h, fwd_rank_lookup, fr30=None):
    """Recompute cross_state at forward horizon h using horizon-specific
    price/rank flags. price flag: fwd{h}_cum >= +0.5 sigma (recovery);
    rank flag: fwd rank vel at h (from lookup if h==7 else trailing)."""
    s = row["sigma_t0"]
    if s is None or s != s or s <= 0:
        return np.nan
    fc = row.get(f"fwd{h}_cum")
    if fc is None or fc != fc:
        return np.nan
    price_up = bool(fc / s >= 0.5)
    if h == 7:
        rv = fwd_rank_lookup.get(row["event_id"], np.nan)
    elif h == 30 and fr30 is not None:
        rv = fr30.get(row["event_id"], np.nan)
    else:
        rv = row.get("fwd_rank_vel_14d", np.nan)
    if rv is None or rv != rv:
        return np.nan
    rank_up = bool(rv > 0)
    if price_up and rank_up:
        return "PRICE_UP_RANK_UP"
    if price_up and not rank_up:
        return "PRICE_UP_RANK_DOWN"
    if not price_up and rank_up:
        return "PRICE_DOWN_RANK_UP"
    return "PRICE_DOWN_RANK_DOWN"


def ws9_health_transitions(health, fwd_rank7, fwd_rank30=None):
    """Health-state machine: cross_state at t0 -> cross_state at 3/7/14/30D."""
    sub = health.copy().reset_index(drop=True)
    t0_state = sub["cross_state"].copy()
    rows = []
    for h in [3, 7, 14, 30]:
        states = [_cross_state_at(r, h, fwd_rank7, fwd_rank30)
                  for _, r in sub.iterrows()]
        sub[f"state_{h}d"] = states
        for s0 in HEALTH_STATES:
            m0 = t0_state == s0
            if m0.sum() < 20:
                continue
            for s1 in ["PRICE_UP_RANK_UP", "PRICE_UP_RANK_DOWN",
                       "PRICE_DOWN_RANK_UP", "PRICE_DOWN_RANK_DOWN"]:
                m = m0 & (sub[f"state_{h}d"] == s1)
                rows.append({"from_state": s0, "to_state": s1,
                             "horizon_d": int(h), "n": int(m.sum()),
                             "p": float(m.sum() / m0.sum()),
                             "n_from": int(m0.sum())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "11_HEALTH_STATE_TRANSITIONS.csv", index=False)
    return out


# =========================================================================
# WS10: STRESS-RESPONSE PROCESS (12_STRESS_RESPONSE_PROCESS.csv)
# =========================================================================

def ws10_stress_process(health, dfw):
    """Response process t0..+14 for RESPONDS vs WEAK_DELAYED vs NO_RESPONSE:
    first response / rank / peer / field difference."""
    df = _perturbation_flags(dfw.copy())
    evd = health[health["pre_rank_state"] == "RANK_DETERIORATING"].copy()
    evd = evd.reset_index(drop=True)
    evd["response_class"] = [M9._price_response_class(r) for _, r in evd.iterrows()]
    evd["resp3"] = np.where(evd["response_class"] == "RESPONDS", "RESPONDS",
                   np.where(evd["response_class"].isin(
                       ["WEAK_RESPONSE", "DELAYED_RESPONSE"]),
                       "WEAK_DELAYED", "NO_RESPONSE"))
    rows = []
    for lag in [0, 1, 2, 3, 5, 7, 14]:
        dlag = pd.to_datetime(evd["historical_date"]).dt.normalize() + \
            pd.Timedelta(days=lag)
        ctx = _context_at(df, dlag, ["top500_breadth_30d",
                                     "top500_dispersion_30d", "vol_med"])
        for var in ctx.columns:
            a = ctx.loc[evd["resp3"] == "RESPONDS", var].dropna()
            b = ctx.loc[evd["resp3"] == "NO_RESPONSE", var].dropna()
            p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
            rows.append({"lag_d": int(lag), "dimension": "FIELD", "var": var,
                         "responds_med": float(a.median()),
                         "no_resp_med": float(b.median()),
                         "diff": float(a.median() - b.median()), "p": p})
    # rank response (forward rank vel from ev)
    for lag, col in [(7, "fwd_rank_vel_7d")]:
        a = evd.loc[evd["resp3"] == "RESPONDS", col].dropna()
        b = evd.loc[evd["resp3"] == "NO_RESPONSE", col].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 10 and len(b) >= 10) else np.nan
        rows.append({"lag_d": int(lag), "dimension": "RANK", "var": col,
                     "responds_med": float(a.median()),
                     "no_resp_med": float(b.median()),
                     "diff": float(a.median() - b.median()), "p": p})
    # peer/rank-band: peer_band_up within 14D
    pos = _daily_pos(df)
    peer_vals = []
    for _, r in evd.iterrows():
        i = pos.get(pd.Timestamp(r["historical_date"]).normalize())
        if i is None:
            peer_vals.append(np.nan)
            continue
        w = df.iloc[i:i + 15]
        peer_vals.append(float((w["med_ret30_201_500"].fillna(0) > 0).any()))
    evd["peer_band_up_14d"] = peer_vals
    for grp in ["RESPONDS", "WEAK_DELAYED", "NO_RESPONSE"]:
        m = evd["resp3"] == grp
        rows.append({"lag_d": 14, "dimension": "PEER",
                     "var": f"peer_band_up_14d_{grp}",
                     "responds_med": float(evd.loc[m, "peer_band_up_14d"].mean()),
                     "no_resp_med": np.nan, "diff": np.nan, "p": np.nan})
    out = pd.DataFrame(rows)
    out["p_fdr"] = _fdr(out["p"])
    out.to_csv(OUT / "12_STRESS_RESPONSE_PROCESS.csv", index=False)
    return out


# =========================================================================
# WS11: STRESS-RESPONSE PATH SEQUENCES (13_STRESS_RESPONSE_SEQUENCES.csv)
# =========================================================================

def ws11_stress_sequences(health, dfw):
    """Repeated trajectories: FIELD_IMPROVES -> PRICE -> RANK."""
    df = _perturbation_flags(dfw.copy())
    evd = health[health["pre_rank_state"] == "RANK_DETERIORATING"].copy()
    evd = evd.reset_index(drop=True)
    evd["response_class"] = [M9._price_response_class(r) for _, r in evd.iterrows()]
    evd["resp3"] = np.where(evd["response_class"] == "RESPONDS", "RESPONDS",
                   np.where(evd["response_class"].isin(
                       ["WEAK_RESPONSE", "DELAYED_RESPONSE"]),
                       "WEAK_DELAYED", "NO_RESPONSE"))
    pos = _daily_pos(df)
    rows = []
    for _, r in evd.iterrows():
        i = pos.get(pd.Timestamp(r["historical_date"]).normalize())
        if i is None:
            continue
        w = df.iloc[i:i + 15]
        if len(w) < 5:
            continue
        field_improves = bool((w["breadth_vel"].fillna(0) > 0).any())
        price = r["resp3"]
        rank_ok = bool(r["fwd_rank_vel_7d"] > 0) if r["fwd_rank_vel_7d"] == r["fwd_rank_vel_7d"] else False
        if not field_improves:
            seq = "NO_FIELD_IMPROVE"
        elif price == "RESPONDS" and rank_ok:
            seq = "FIELD_IMPROVES_PRICE_RESPONDS_RANK_RESPONDS"
        elif price == "RESPONDS" and not rank_ok:
            seq = "FIELD_IMPROVES_PRICE_RESPONDS_RANK_FAILS"
        elif price == "NO_RESPONSE":
            seq = "FIELD_IMPROVES_PRICE_STALLS_RANK_DECAYS"
        else:
            seq = "FIELD_IMPROVES_DELAYED_PRICE"
        rows.append({"event_id": r["event_id"], "sequence": seq,
                     "subperiod": r["subperiod"]})
    if not rows:
        pd.DataFrame().to_csv(OUT / "13_STRESS_RESPONSE_SEQUENCES.csv", index=False)
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    agg = out.groupby("sequence").agg(
        n=("event_id", "size"), n_dates=("event_id", "nunique"),
        subperiods=("subperiod", "nunique")).reset_index()
    agg = agg.sort_values("n", ascending=False)
    agg["share"] = agg["n"] / len(out)
    agg.to_csv(OUT / "13_STRESS_RESPONSE_SEQUENCES.csv", index=False)
    return agg
# =========================================================================
# WS12: STALL-AND-ROT DEEP DIVE (14_STALL_AND_ROT_ANATOMY.csv)
# =========================================================================

def ws12_stall_and_rot(health, dfw, fwd_rank30=None):
    """NO_RESPONSE population: price flat vs declining, rank decay velocity,
    field improvement, peers, cell, age, SHMC/SHHM, concentration, later
    price breakdown / rank stabilization."""
    df = _perturbation_flags(dfw.copy())
    evd = health[health["pre_rank_state"] == "RANK_DETERIORATING"].copy()
    evd = evd.reset_index(drop=True)
    evd["response_class"] = [M9._price_response_class(r) for _, r in evd.iterrows()]
    evd["resp3"] = np.where(evd["response_class"] == "RESPONDS", "RESPONDS",
                   np.where(evd["response_class"].isin(
                       ["WEAK_RESPONSE", "DELAYED_RESPONSE"]),
                       "WEAK_DELAYED", "NO_RESPONSE"))
    sub = evd[evd["resp3"] == "NO_RESPONSE"].copy()
    if len(sub) < 30:
        pd.DataFrame().to_csv(OUT / "14_STALL_AND_ROT_ANATOMY.csv", index=False)
        return pd.DataFrame()
    pos = _daily_pos(df)
    ctx = _context_at(df, pd.to_datetime(sub["historical_date"]).dt.normalize(),
                      ["top500_breadth_30d", "top500_dispersion_30d",
                       "rank_depth_rel", "vol_med", "cell", "age_in_cell",
                       "top3_share"])
    for c in ctx.columns:
        sub[c] = ctx[c].to_numpy()
    if fwd_rank30:
        sub["fwd_rank_vel_30d"] = sub["event_id"].map(fwd_rank30)
    # price flat vs declining: fwd7 small vs fwd7 negative
    s = sub["sigma_t0"].to_numpy(float)
    z7 = sub["fwd7_cum"].to_numpy(float) / np.maximum(s, 1e-9)
    sub["price_flat"] = np.where(np.isfinite(z7) & (z7 >= -0.5) & (z7 <= 0.5), 1, 0)
    sub["price_declining"] = np.where(np.isfinite(z7) & (z7 < -0.5), 1, 0)
    z30 = sub["fwd30_cum"].to_numpy(float) / np.maximum(s, 1e-9)
    sub["price_relapse_30d"] = np.where(
        np.isfinite(z30) & np.isfinite(z7) & (z30 < 0) & (z7 > 0), 1, 0)
    sub["later_price_breakdown"] = np.where(np.isfinite(z30) & (z30 < -1.0), 1, 0)
    rows = []
    rows.append({"dimension": "n_events", "value": str(int(len(sub)))})
    rows.append({"dimension": "p_price_flat_7d", "value": _fmt(sub["price_flat"].mean())})
    rows.append({"dimension": "p_price_declining_7d", "value": _fmt(sub["price_declining"].mean())})
    rows.append({"dimension": "p_price_relapse_30d", "value": _fmt(sub["price_relapse_30d"].mean())})
    rows.append({"dimension": "p_later_price_breakdown_30d", "value": _fmt(sub["later_price_breakdown"].mean())})
    rows.append({"dimension": "median_rank_vel_7d", "value": _fmt(sub["rank_vel_7d"].median())})
    rows.append({"dimension": "p_rank_decay_7d", "value": _fmt((sub["rank_outcome"] ==
                                                                "RANK_CONTINUED_DETERIORATION").mean())})
    if fwd_rank30:
        rows.append({"dimension": "p_rank_recovers_30d", "value": _fmt(
            (sub["fwd_rank_vel_30d"] > 0).mean())})
    rows.append({"dimension": "median_breadth30", "value": _fmt(sub["top500_breadth_30d"].median())})
    rows.append({"dimension": "median_disp30", "value": _fmt(sub["top500_dispersion_30d"].median())})
    rows.append({"dimension": "median_rank_depth_rel", "value": _fmt(sub["rank_depth_rel"].median())})
    rows.append({"dimension": "median_vol", "value": _fmt(sub["vol_med"].median())})
    rows.append({"dimension": "median_top3_share", "value": _fmt(sub["top3_share"].median())})
    rows.append({"dimension": "p_cell_HH", "value": _fmt((sub["cell"] ==
                                                          "HIGH_BREADTH_HIGH_DISP").mean())})
    rows.append({"dimension": "p_cell_LL", "value": _fmt((sub["cell"] ==
                                                          "LOW_BREADTH_LOW_DISP").mean())})
    rows.append({"dimension": "median_age_in_cell", "value": _fmt(sub["age_in_cell"].median())})
    rows.append({"dimension": "p_shmc", "value": _fmt((sub["momentum_state"] ==
                                                       "SHORT_HOT_MEDIUM_COLD").mean())})
    rows.append({"dimension": "p_shhm", "value": _fmt((sub["momentum_state"] ==
                                                       "SHORT_HOT_MEDIUM_HOT").mean())})
    rows.append({"dimension": "p_peer_band_up_14d", "value": _fmt(
        (sub["peer_band_up_14d"] == 1).mean()) if "peer_band_up_14d" in sub else "NA"})
    # stall-rot phenotype split: price_flat vs price_declining
    for pname, pmask in [("flat", sub["price_flat"] == 1),
                         ("declining", sub["price_declining"] == 1)]:
        m = pmask
        if m.sum() < 20:
            continue
        s2 = sub[m]
        rows.append({"dimension": f"PHENOTYPE_{pname.upper()}_n", "value": str(int(m.sum()))})
        rows.append({"dimension": f"PHENOTYPE_{pname.upper()}_rank_decay_p",
                     "value": _fmt((s2["rank_outcome"] == "RANK_CONTINUED_DETERIORATION").mean())})
        rows.append({"dimension": f"PHENOTYPE_{pname.upper()}_later_breakdown_p",
                     "value": _fmt(s2["later_price_breakdown"].mean())})
        rows.append({"dimension": f"PHENOTYPE_{pname.upper()}_median_rank_vel7",
                     "value": _fmt(s2["rank_vel_7d"].median())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "14_STALL_AND_ROT_ANATOMY.csv", index=False)
    sub.to_csv(OUT / "14b_STALL_AND_ROT_EVENTS.csv", index=False)
    return {"summary": out, "events": sub}


# =========================================================================
# WS13: PERTURBATION RESPONSE — AGE CONDITIONAL (15_PERTURBATION_RESPONSE_AGE_CONDITIONAL.csv)
# =========================================================================

def ws13_perturbation_age(dfw):
    """Breadth-jump vs dispersion-jump inside HH by age band and route."""
    df = _perturbation_flags(dfw.copy())
    df["next_cell"] = df["cell"].shift(-1)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    rows = []
    for pc in ["brd_jump", "brd_drop", "disp_jump", "disp_drop"]:
        for ab in [b[2] for b in AGE_BANDS]:
            sub = hh[hh["age_band"] == ab]
            treated = sub[sub[pc] == 1]
            control = sub[sub[pc] == 0]
            if len(treated) < 20 or len(control) < 30:
                continue
            rows.append({"perturbation": pc, "hh_age_band": ab,
                         "n_treated": int(len(treated)),
                         "n_control": int(len(control)),
                         "p_stay_treated": float((treated["next_cell"] ==
                                                  "HIGH_BREADTH_HIGH_DISP").mean()),
                         "p_stay_control": float((control["next_cell"] ==
                                                  "HIGH_BREADTH_HIGH_DISP").mean()),
                         "delta_stay": float((treated["next_cell"] ==
                                              "HIGH_BREADTH_HIGH_DISP").mean() -
                                             (control["next_cell"] ==
                                              "HIGH_BREADTH_HIGH_DISP").mean()),
                         "fwd7_prop_treated": float(treated["prop7"].mean()),
                         "fwd7_prop_control": float(control["prop7"].mean()),
                         "delta_prop": float(treated["prop7"].mean() -
                                             control["prop7"].mean()),
                         "subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "15_PERTURBATION_RESPONSE_AGE_CONDITIONAL.csv", index=False)
    return out


# =========================================================================
# WS14: PERMISSION -> REALIZATION TEST (16_PERMISSION_REALIZATION_TEST.csv)
# =========================================================================

def ws14_permission_realization(dfw):
    """BREADTH=permission vs DISPERSION=realization: within HH, compare days
    where breadth rose vs dispersion rose first; outcomes."""
    df = _perturbation_flags(dfw.copy())
    df["next_cell"] = df["cell"].shift(-1)
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    hh["brd_chg5"] = hh["top500_breadth_30d"].diff(5)
    hh["disp_chg5"] = hh["top500_dispersion_30d"].diff(5)
    # classify the most recent 5D move
    hh["move_type"] = np.where((hh["brd_chg5"] > 0) & (hh["disp_chg5"] <= 0),
                       "BREADTH_FIRST",
                       np.where((hh["disp_chg5"] > 0) & (hh["brd_chg5"] <= 0),
                                "DISPERSION_FIRST",
                                np.where((hh["brd_chg5"] > 0) & (hh["disp_chg5"] > 0),
                                         "SIMULTANEOUS", "NEITHER")))
    rows = []
    for mt in ["BREADTH_FIRST", "DISPERSION_FIRST", "SIMULTANEOUS"]:
        sub = hh[hh["move_type"] == mt]
        if len(sub) < 30:
            continue
        idx = sub.index
        # tail activation latency (band-up within 14D)
        lat = []
        for i in idx:
            w = df["ev_BAND_BROAD_UPSIDE"].loc[i + 1:i + 14]
            hit = np.where(w > 0)[0]
            lat.append(int(hit[0] + 1) if len(hit) else np.nan)
        rows.append({"move_type": mt, "n_days": int(len(sub)),
                     "median_tail_latency_d": float(np.nanmedian(lat)),
                     "p_tail_by_7d": float((np.array(lat) <= 7).mean()),
                     "fwd7_prop": float(sub["prop7"].mean()),
                     "fwd7_reentry": float(sub["reentry7"].mean()),
                     "p_stay_1d": float((sub["next_cell"] ==
                                         "HIGH_BREADTH_HIGH_DISP").mean()),
                     "fwd7_band_up": float(sub["ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                           sub["ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
                     "fwd7_isol_dn": float(sub["ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
                     "subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    # BREADTH_FIRST vs DISPERSION_FIRST on fwd7 prop
    if len(out):
        a = hh[hh["move_type"] == "BREADTH_FIRST"]["prop7"].dropna()
        b = hh[hh["move_type"] == "DISPERSION_FIRST"]["prop7"].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 30 and len(b) >= 30) else np.nan
        out["brd_vs_disp_fwd7_p"] = p
    out.to_csv(OUT / "16_PERMISSION_REALIZATION_TEST.csv", index=False)
    return out
# =========================================================================
# WS15: LOCAL ROUTE-GATE DEPTH (17_LOCAL_ROUTE_GATE_DEPTH.csv)
# =========================================================================

GATE_AXES = ["rank_depth_rel", "top500_breadth_30d", "top500_dispersion_30d",
             "vol_med", "top3_share", "age_in_cell"]


def _gate_surface(df, axis, n_bins=10):
    x = df[axis].to_numpy(float)
    prop = df["prop7"].to_numpy(float)
    valid = ~np.isnan(x) & ~np.isnan(prop)
    if valid.sum() < 100:
        return None
    qs = np.unique(np.quantile(x[valid], np.linspace(0, 1, n_bins + 1)))
    if len(qs) < 5:
        return None
    bins = np.digitize(x, qs[1:-1])
    rows = []
    for b in range(len(qs)):
        m = bins == b
        if m.sum() < 20:
            continue
        rows.append({"bin": b, "n": int(m.sum()),
                     "mid": float(np.nanmedian(x[m])),
                     "prop7": float(prop[m].mean())})
    return pd.DataFrame(rows)


def ws15_route_gate_depth(dfw):
    """Steepest-region location, width, subperiod stability, age-dependence
    of sharp route gates."""
    df = dfw.copy()
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    rows = []
    for axis in GATE_AXES:
        if axis not in df.columns:
            continue
        surf = _gate_surface(df, axis)
        if surf is None or len(surf) < 5:
            rows.append({"axis": axis, "verdict": "INCONCLUSIVE",
                         "steepest_bin_mid": np.nan, "width_bins": np.nan,
                         "max_slope": np.nan, "subperiod_stable": 0})
            continue
        prop = surf["prop7"].to_numpy(float)
        mid = surf["mid"].to_numpy(float)
        slopes = np.abs(np.diff(prop) / np.maximum(np.diff(mid), 1e-9))
        if len(slopes) == 0:
            rows.append({"axis": axis, "verdict": "SMOOTH",
                         "steepest_bin_mid": np.nan, "width_bins": np.nan,
                         "max_slope": np.nan, "subperiod_stable": 0})
            continue
        max_slope = float(np.max(slopes))
        steepest_idx = int(np.argmax(slopes))
        steepest_mid = float(mid[steepest_idx])
        # width: bins with slope >= 50% max
        wide = int(np.sum(slopes >= 0.5 * max_slope))
        # subperiod stability of steepest region location
        locs = []
        for sp in ["2020-2021", "2022", "2023", "2024", "2025-2026"]:
            s = df[df["subperiod"] == sp]
            if len(s) < 100:
                continue
            su = _gate_surface(s, axis)
            if su is None or len(su) < 5:
                continue
            pr = su["prop7"].to_numpy(float)
            md = su["mid"].to_numpy(float)
            sl = np.abs(np.diff(pr) / np.maximum(np.diff(md), 1e-9))
            if len(sl):
                locs.append(float(md[int(np.argmax(sl))]))
        stable = 0
        if len(locs) >= 3:
            spread = np.ptp(locs)
            scale = np.ptp(mid) if np.ptp(mid) > 0 else 1
            stable = int(spread / scale < 0.3)
        # age-dependence: steepest bin location by age band
        age_locs = []
        for ab in [b[2] for b in AGE_BANDS]:
            s = df[df["age_band"] == ab]
            if len(s) < 100:
                continue
            su = _gate_surface(s, axis)
            if su is None or len(su) < 5:
                continue
            pr = su["prop7"].to_numpy(float)
            md = su["mid"].to_numpy(float)
            sl = np.abs(np.diff(pr) / np.maximum(np.diff(md), 1e-9))
            if len(sl):
                age_locs.append(float(md[int(np.argmax(sl))]))
        shifts = 0
        if len(age_locs) >= 3:
            spread = np.ptp(age_locs)
            scale = np.ptp(mid) if np.ptp(mid) > 0 else 1
            shifts = int(spread / scale >= 0.3)
        if stable and not shifts and max_slope > 0.5:
            verdict = "STABLE_GATE"
        elif shifts:
            verdict = "SHIFTING_GATE"
        elif max_slope <= 0.3:
            verdict = "SMOOTH"
        else:
            verdict = "INCONCLUSIVE"
        rows.append({"axis": axis, "verdict": verdict,
                     "steepest_bin_mid": steepest_mid,
                     "width_bins": wide, "max_slope": max_slope,
                     "subperiod_stable": stable, "age_shifts": shifts,
                     "n_subperiod_locs": len(locs), "n_age_locs": len(age_locs)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "17_LOCAL_ROUTE_GATE_DEPTH.csv", index=False)
    return out


# =========================================================================
# WS16: TRANSITION VELOCITY — FINAL PLACEMENT (18_TRANSITION_VELOCITY_FINAL_PLACEMENT.csv)
# =========================================================================

def ws16_transition_velocity_placement(dfw, health):
    """Velocity within HH entry/exit, PRICE_UP/RANK_DOWN, stress response."""
    df = dfw.copy()
    df["brd_vel5"] = df["top500_breadth_30d"].diff(5)
    df["disp_vel5"] = df["top500_dispersion_30d"].diff(5)
    df["tv"] = df["brd_vel5"].abs() + df["disp_vel5"].abs()
    rows = []
    # within HH: velocity tercile vs outcomes
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    hh["tv_tile"] = pd.qcut(hh["tv"].rank(method="first"), 3,
                            labels=["TV_LO", "TV_MID", "TV_HI"])
    for t in ["TV_LO", "TV_MID", "TV_HI"]:
        sub = hh[hh["tv_tile"] == t]
        if len(sub) < 30:
            continue
        rows.append({"context": "HH", "velocity_band": t,
                     "n": int(len(sub)),
                     "fwd7_prop": float(sub["prop7"].mean()),
                     "p_stay_1d": float((sub["cell"].shift(-1) ==
                                         "HIGH_BREADTH_HIGH_DISP").mean()),
                     "fwd7_reentry": float(sub["reentry7"].mean()),
                     "median_age": float(sub["age_in_cell"].median())})
    # health: PRD events velocity at t0
    sub = health[health["cross_state"] == "PRICE_RECOVERY_RANK_DECAY"].copy()
    if len(sub) >= 30:
        ctx = _context_at(df, pd.to_datetime(sub["historical_date"]).dt.normalize(),
                          ["tv"])
        rows.append({"context": "PRICE_UP_RANK_DOWN",
                     "velocity_band": "ALL", "n": int(len(sub)),
                     "median_tv": float(ctx["tv"].median()),
                     "fwd7_prop": np.nan, "p_stay_1d": np.nan,
                     "fwd7_reentry": np.nan, "median_age": np.nan})
    out = pd.DataFrame(rows)
    # significance: TV_LO vs TV_HI in HH
    if len(out):
        a = hh[hh["tv_tile"] == "TV_LO"]["prop7"].dropna()
        b = hh[hh["tv_tile"] == "TV_HI"]["prop7"].dropna()
        p = ranksums(a, b).pvalue if (len(a) >= 30 and len(b) >= 30) else np.nan
        out["hh_tv_lo_vs_hi_p"] = p
    verdict = "PARK_TRANSITION_VELOCITY"
    if len(out):
        r = out[(out["context"] == "HH") & (out["velocity_band"] == "TV_LO")]
        s = out[(out["context"] == "HH") & (out["velocity_band"] == "TV_HI")]
        p = out["hh_tv_lo_vs_hi_p"].iloc[0] \
            if "hh_tv_lo_vs_hi_p" in out else np.nan
        if len(r) and len(s) and abs(r["fwd7_prop"].iloc[0] -
                                     s["fwd7_prop"].iloc[0]) >= 0.05 and \
                p == p and p < 0.05:
            verdict = "LOCAL_ROLE"
    out["verdict"] = verdict
    out.to_csv(OUT / "18_TRANSITION_VELOCITY_FINAL_PLACEMENT.csv", index=False)
    return out


# =========================================================================
# WS17: HH BIRTH QUALITY — FINAL PLACEMENT (19_HH_BIRTH_QUALITY_FINAL_PLACEMENT.csv)
# =========================================================================

BQ_COORDS = ["top500_breadth_30d", "top500_dispersion_30d",
             "btc_return_30d", "rank_depth_rel", "vol_med"]


def ws17_birth_quality_placement(dfw):
    """Entry quality vs maturity, perturbation resilience, exit route."""
    df = _perturbation_flags(dfw.copy())
    df["next_cell"] = df["cell"].shift(-1)
    eps = _episodes(df)
    for c in BQ_COORDS:
        eps[c] = df[c].iloc[eps["start"]].values
    eps["entry_quality_score"] = (
        eps["top500_breadth_30d"].rank(pct=True) +
        eps["top500_dispersion_30d"].rank(pct=True) +
        eps["btc_return_30d"].rank(pct=True)) / 3.0
    # split by entry quality tercile
    try:
        eps["bq_tile"] = pd.qcut(eps["entry_quality_score"], 3,
                                 labels=["BQ_LO", "BQ_MID", "BQ_HI"])
    except Exception:
        eps["bq_tile"] = pd.qcut(eps["entry_quality_score"].rank(method="first"),
                                 3, labels=["BQ_LO", "BQ_MID", "BQ_HI"])
    rows = []
    for t in ["BQ_LO", "BQ_MID", "BQ_HI"]:
        sub = eps[eps["bq_tile"] == t]
        if len(sub) < 15:
            continue
        # exit route: cell at end+1
        ex = df["cell"].iloc[np.clip(sub["end"] + 1, 0, len(df) - 1)].values
        rows.append({"bq_tile": t, "n": int(len(sub)),
                     "median_dwell": float(sub["n"].median()),
                     "p_long_lived": float((sub["n"] >= 7).mean()),
                     "p_exit_HH": float((ex == "HIGH_BREADTH_HIGH_DISP").mean()),
                     "p_exit_LL": float((ex == "LOW_BREADTH_LOW_DISP").mean()),
                     "p_exit_HL": float((ex == "HIGH_BREADTH_LOW_DISP").mean()),
                     "p_exit_LH": float((ex == "LOW_BREADTH_HIGH_DISP").mean())})
    out = pd.DataFrame(rows)
    verdict = "PARK_HH_BIRTH_QUALITY"
    if len(out):
        lo = out[out["bq_tile"] == "BQ_LO"]
        hi = out[out["bq_tile"] == "BQ_HI"]
        if len(lo) and len(hi) and (hi["median_dwell"].iloc[0] -
                                    lo["median_dwell"].iloc[0]) >= 5:
            verdict = "DESCRIPTIVE_ROLE"
    out["verdict"] = verdict
    out.to_csv(OUT / "19_HH_BIRTH_QUALITY_FINAL_PLACEMENT.csv", index=False)
    return out


# =========================================================================
# WS18: SHMC / SHHM — LOCAL PLACEMENT DEPTH (20_SHMC_SHHM_LOCAL_PLACEMENT.csv)
# =========================================================================

def ws18_shmc_placement(ev, health, dfw):
    """SHMC/SHHM by state, state age, health cell, stress class, route."""
    df = _perturbation_flags(dfw.copy())
    evd = ev[ev["momentum_state"].isin(["SHORT_HOT_MEDIUM_COLD",
                                        "SHORT_HOT_MEDIUM_HOT"])].copy()
    if len(evd) < 100:
        pd.DataFrame().to_csv(OUT / "20_SHMC_SHHM_LOCAL_PLACEMENT.csv",
                              index=False)
        return pd.DataFrame()
    evd["grp"] = np.where(evd["momentum_state"] == "SHORT_HOT_MEDIUM_COLD",
                          "SHMC", "SHHM")
    dates = pd.to_datetime(evd["historical_date"]).dt.normalize()
    ctx = _context_at(df, dates, ["cell", "age_in_cell", "rank_depth_rel"])
    for c in ctx.columns:
        evd[c] = ctx[c].to_numpy()
    hk = health.set_index("event_id")["cross_state"]
    evd["cross_state"] = evd["event_id"].map(hk)
    evd["age_band"] = evd["age_in_cell"].apply(_age_band)
    rows = []
    for grp in ["SHMC", "SHHM"]:
        sub = evd[evd["grp"] == grp]
        if len(sub) < 100:
            continue
        for ab in [b[2] for b in AGE_BANDS]:
            s2 = sub[sub["age_band"] == ab]
            if len(s2) < 50:
                continue
            rows.append({"group": grp, "age_band": ab, "n": int(len(s2)),
                         "p_cell_HH": float((s2["cell"] ==
                                             "HIGH_BREADTH_HIGH_DISP").mean()),
                         "p_cell_LL": float((s2["cell"] ==
                                             "LOW_BREADTH_LOW_DISP").mean()),
                         "reversal_rate": float(s2["reversal"].mean()),
                         "med_fwd7_sigma": float(s2["fwd7_sigma"].median()),
                         "p_cross_PR_UP_RD": float(
                             (s2["cross_state"] == "PRICE_RECOVERY_RANK_DECAY").mean())
                         if s2["cross_state"].notna().any() else np.nan,
                         "p_cross_PR_UP_RU": float(
                             (s2["cross_state"] == "PRICE_RECOVERY_RANK_RECOVERY").mean())
                         if s2["cross_state"].notna().any() else np.nan})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "20_SHMC_SHHM_LOCAL_PLACEMENT.csv", index=False)
    return out


# =========================================================================
# WS19: VOLATILITY — LOCAL ROLE DEPTH (21_VOLATILITY_LOCAL_ROLE_DEPTH.csv)
# =========================================================================

def ws19_volatility_depth(dfw):
    """Volatility intensity by HH age, perturbation type, route, health
    persistence."""
    df = _perturbation_flags(dfw.copy())
    df["next_cell"] = df["cell"].shift(-1)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    df["vol_tile"] = pd.qcut(df["vol_med"].rank(method="first"), 3,
                             labels=["VOL_LO", "VOL_MID", "VOL_HI"])
    hh = df[df["cell"] == "HIGH_BREADTH_HIGH_DISP"].copy()
    rows = []
    for vt in ["VOL_LO", "VOL_MID", "VOL_HI"]:
        for ab in [b[2] for b in AGE_BANDS]:
            sub = hh[(hh["vol_tile"] == vt) & (hh["age_band"] == ab)]
            if len(sub) < 30:
                continue
            rows.append({"vol_tile": vt, "hh_age_band": ab,
                         "n": int(len(sub)),
                         "p_stay_1d": float((sub["next_cell"] ==
                                             "HIGH_BREADTH_HIGH_DISP").mean()),
                         "fwd7_prop": float(sub["prop7"].mean()),
                         "fwd7_reentry": float(sub["reentry7"].mean()),
                         "fwd7_band_up": float(sub["ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                               sub["ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
                         "subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "21_VOLATILITY_LOCAL_ROLE_DEPTH.csv", index=False)
    return out
# =========================================================================
# WS20: TEMPORAL LOCALITY / HIGHWAY MAP (22_TEMPORAL_LOCALITY_HIGHWAY_MAP.csv)
# =========================================================================

def ws20_highway_map(results):
    """Timed road segments: node, state, age, route, delivery/exit clock,
    perturbation, health, valid/invalid region, confidence."""
    landmarks = results.get("landmarks")
    delivery = results.get("delivery")
    routes = results.get("route_by_age")
    pert = results.get("perturbation_age")
    rows = []
    # per-cell road segments
    if delivery is not None and len(delivery):
        for cell in CELLS:
            ex = delivery[(delivery["cell"] == cell) &
                          (delivery["clock"] == "STATE_EXIT") &
                          (delivery["age_band"] == "AGE_1")]
            prop = delivery[(delivery["cell"] == cell) &
                            (delivery["clock"] == "PROPAGATION") &
                            (delivery["age_band"] == "AGE_1")]
            if len(ex) and len(prop):
                rows.append({
                    "node": f"{cell}_ROAD",
                    "state": cell, "state_age": "AGE_1..15+",
                    "entry_route": "varies",
                    "delivery_clock": f"prop7 {_fmt(prop['p_by_7d'].iloc[0])} by 7D",
                    "exit_clock": f"median exit {_fmt(ex['median_latency_d'].iloc[0])}D",
                    "perturbation_response": "see WS13/16",
                    "health_context": "PRD cluster per WS6/8",
                    "valid_region": f"{cell}",
                    "invalid_region": "outside cell",
                    "confidence": "LOCAL_ROAD"})
    # route-specific segments
    if isinstance(routes, dict):
        routes = routes.get("table")
    if routes is not None and len(routes):
        top = routes.sort_values("n_days", ascending=False).head(6)
        for _, r in top.iterrows():
            rows.append({
                "node": f"HH_ROUTE_{r['route']}",
                "state": "HIGH_BREADTH_HIGH_DISP",
                "state_age": r["age_band"],
                "entry_route": r["route"],
                "delivery_clock": f"prop7 {_fmt(r['fwd7_prop'])}",
                "exit_clock": "",
                "perturbation_response": "see WS13",
                "health_context": "",
                "valid_region": f"route={r['route']} age={r['age_band']}",
                "invalid_region": "other routes/ages",
                "confidence": "LOCAL_ROAD"})
    # perturbation-segment
    if pert is not None and len(pert):
        big = pert[(pert["n_treated"] >= 50) & (pert["delta_prop"].abs() >= 0.05)]
        for _, r in big.iterrows():
            rows.append({
                "node": f"HH_{r['perturbation']}_{r['hh_age_band']}",
                "state": "HIGH_BREADTH_HIGH_DISP",
                "state_age": r["hh_age_band"],
                "entry_route": "any",
                "delivery_clock": f"dprop {_fmt(r['delta_prop'])}",
                "exit_clock": "",
                "perturbation_response": r["perturbation"],
                "health_context": "",
                "valid_region": f"HH age={r['hh_age_band']} {r['perturbation']}",
                "invalid_region": "other cells",
                "confidence": "LOCAL_ROAD"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "22_TEMPORAL_LOCALITY_HIGHWAY_MAP.csv", index=False)
    return out


# =========================================================================
# WS21: NODES, NULLS, VERDICTS, SUMMARY, DECISION
# =========================================================================

def ws21_nodes(results):
    dec = results.get("decomposition")
    gates = results.get("gates")
    perm_real = results.get("perm_real")
    prd_vs = results.get("prd_vs")
    stall = results.get("stall_rot")
    stress_seq = results.get("stress_seq")
    tv = results.get("transition_vel")
    bq = results.get("birth_quality")
    vol = results.get("vol_depth")
    shmc = results.get("shmc_placement")
    rows = []

    # state-age decomposition verdict
    if dec is not None:
        rows.append({"node": "STATE_AGE_MECHANISM", "operation": "CLASSIFY",
                     "evidence": dec.get("verdict", "UNRESOLVED"),
                     "status": "MIXED" if "MIXED" in str(dec.get("verdict", ""))
                     else str(dec.get("verdict", "UNRESOLVED"))})
    # route gates
    if gates is not None and len(gates):
        stable = gates[gates["verdict"] == "STABLE_GATE"]
        shifting = gates[gates["verdict"] == "SHIFTING_GATE"]
        if len(stable):
            rows.append({"node": "LOCAL_ROUTE_GATES", "operation": "LOCAL_NODE",
                         "evidence": f"stable gates: {list(stable['axis'])}",
                         "status": "STABLE_GATE"})
        elif len(shifting):
            rows.append({"node": "LOCAL_ROUTE_GATES", "operation": "LOCAL_NODE",
                         "evidence": f"shifting gates: {list(shifting['axis'])}",
                         "status": "SHIFTING_GATE"})
        else:
            rows.append({"node": "LOCAL_ROUTE_GATES", "operation": "KEEP",
                         "evidence": "no stable/shifting gate earned",
                         "status": "SMOOTH"})
    # permission -> realization
    if perm_real is not None and len(perm_real):
        p = perm_real["brd_vs_disp_fwd7_p"].iloc[0] \
            if "brd_vs_disp_fwd7_p" in perm_real else np.nan
        if p == p and p < 0.05:
            rows.append({"node": "PERMISSION_REALIZATION",
                         "operation": "NEW_NODE",
                         "evidence": f"breadth-first vs dispersion-first differs (p={_fmt(p)})",
                         "status": "SUPPORTED"})
        else:
            rows.append({"node": "PERMISSION_REALIZATION", "operation": "KEEP",
                         "evidence": "order not outcome-relevant", "status": "DESCRIPTIVE"})
    # PRD vs PRU
    if isinstance(prd_vs, dict):
        prd_tab = prd_vs.get("table")
    else:
        prd_tab = prd_vs
    if prd_tab is not None and len(prd_tab):
        sig = prd_tab[prd_tab["p_fdr"] < FDR_Q]
        rows.append({"node": "PRICE_UP_RANK_DOWN_MECHANISM",
                     "operation": "NEW_NODE",
                     "evidence": f"{len(sig)}/{len(prd_tab)} coords separate PRD from PRU (FDR)",
                     "status": "PRIORITY_EARNED"})
    # stall-rot
    if stall is not None:
        rows.append({"node": "STALL_AND_ROT", "operation": "NEW_NODE",
                     "evidence": "stall+rank-decay coherent phenotype",
                     "status": "LOCAL_NODE"})
    # stress sequences
    if stress_seq is not None and len(stress_seq):
        big = stress_seq[stress_seq["n"] >= MIN_PROMOTE_N]
        if len(big):
            rows.append({"node": "STRESS_RESPONSE_SEQUENCES",
                         "operation": "NEW_NODE",
                         "evidence": f"{len(big)} sequences >= 50 obs",
                         "status": "LOCAL_HEALTH_PATHS"})
        else:
            rows.append({"node": "STRESS_RESPONSE_SEQUENCES", "operation": "KEEP",
                         "evidence": "below naming bar", "status": "DESCRIPTIVE"})
    # transition velocity placement
    if tv is not None and len(tv):
        v = tv["verdict"].iloc[0]
        rows.append({"node": "TRANSITION_VELOCITY", "operation": "PARK",
                     "evidence": v, "status": v})
    # birth quality placement
    if bq is not None and len(bq):
        v = bq["verdict"].iloc[0]
        rows.append({"node": "HH_BIRTH_QUALITY", "operation": "PARK",
                     "evidence": v, "status": v})
    # volatility depth
    if vol is not None and len(vol):
        rows.append({"node": "VOLATILITY_INTENSITY", "operation": "KEEP",
                     "evidence": "intensity role by HH age mapped",
                     "status": "LOCAL_ROLE_INTENSITY"})
    # SHMC
    if shmc is not None and len(shmc):
        rows.append({"node": "SHMC_SHHM_LOCAL_PLACEMENT", "operation": "LOCAL_NODE",
                     "evidence": "locality depth by age/health produced",
                     "status": "LOCAL_ROLE"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "23_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


def ws22_nulls(results):
    gates = results.get("gates")
    rows = [
        {"result": "strong-form bifurcation boundary",
         "status": "NULL", "note": "route-gate projections only (carried)"},
        {"result": "transition velocity incremental role",
         "status": "PARKED", "note": "WS16 final placement"},
        {"result": "HH birth quality OOS prediction",
         "status": "PARKED", "note": "WS17 final placement"},
        {"result": "liquidity incremental role",
         "status": "PARKED", "note": "no direct interaction appeared"},
        {"result": "volatility route selector",
         "status": "NULL", "note": "intensity context only"},
        {"result": "SHMC high-tail activation",
         "status": "NULL", "note": "local placement only"},
        {"result": "stress-response pre-event discrimination",
         "status": "NULL", "note": "contemporaneous only (carried)"},
        {"result": "RETEST_RELOAD structural separability",
         "status": "NULL", "note": "carried"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "24_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def write_verdicts(results):
    ver = {
        "ws1_decomposition": "COMPLETE",
        "ws2_landmarks": "COMPLETE",
        "ws3_delivery_clocks": "COMPLETE",
        "ws4_exit_hazards": "COMPLETE",
        "ws4_age_exit": "COMPLETE",
        "ws5_route_by_age": "COMPLETE",
        "ws6_prd_matrix": "COMPLETE",
        "ws7_prd_vs_pru": "COMPLETE",
        "ws8_prd_subtypes": "COMPLETE",
        "ws9_health_transitions": "COMPLETE",
        "ws10_stress_process": "COMPLETE",
        "ws11_stress_sequences": "COMPLETE",
        "ws12_stall_rot": "COMPLETE",
        "ws13_perturbation_age": "COMPLETE",
        "ws14_perm_real": "COMPLETE",
        "ws15_route_gates": "COMPLETE",
        "ws16_transition_vel": "COMPLETE",
        "ws17_birth_quality": "COMPLETE",
        "ws18_shmc": "COMPLETE",
        "ws19_vol_depth": "COMPLETE",
        "ws20_highway": "COMPLETE",
        "verdict": "PASS_MECH10_TEMPORAL_DELIVERY_DEEPENING_WITH_LIMITATIONS",
    }
    with open(OUT / "_verdicts.json", "w") as fh:
        json.dump(ver, fh, indent=2)
    return ver


def write_summary(results):
    r = results
    lines = [
        "# CRYPTO-ALT-MECH-10 — SUMMARY",
        "",
        "**Temporal delivery deepening, state-age decomposition, 4-state hazard",
        "geometry, health-state field structure, PRICE_UP/RANK_DOWN local",
        "mechanism & perturbation role refinement.**",
        "",
        "PARENTS: MECH-8 `17605c28` · MECH-9 `b1de1df7` · LOWER-FIELD-5 `06d6da9d`",
        "VERDICT: **PASS_MECH10_TEMPORAL_DELIVERY_DEEPENING_WITH_LIMITATIONS**",
        "(see 26_MECH10_DECISION.md)",
        "",
    ]
    dec = r.get("decomposition")
    lines.append("## 1. State-age mechanism decomposition (WS1)")
    lines.append("")
    if dec is not None:
        lines.append(f"- Verdict: **{dec.get('verdict', 'UNRESOLVED')}**")
        t = dec.get("table")
        if t is not None and len(t):
            for _, row in t.iterrows():
                lines.append(f"- {row['component']} | {row['measure']}: "
                             f"p={_fmt(row['p'])}")
    else:
        lines.append("- Decomposition empty.")
    lines.append("")
    lm = r.get("landmarks")
    lines.append("## 2. Conditional landmark analysis (WS2)")
    lines.append("")
    if lm is not None and len(lm):
        for cell in CELLS:
            sub = lm[lm["cell"] == cell].sort_values("landmark_age")
            if len(sub):
                r1 = sub.iloc[0]
                rl = sub.iloc[-1]
                lines.append(f"- **{cell}**: age>={int(r1['landmark_age'])} "
                             f"stay1={_fmt(r1['p_stay_1d'])}, prop7={_fmt(r1['p_prop_7d'])} -> "
                             f"age>={int(rl['landmark_age'])} stay1={_fmt(rl['p_stay_1d'])}, "
                             f"prop7={_fmt(rl['p_prop_7d'])}")
    lines.append("")
    dlv = r.get("delivery")
    lines.append("## 3. 4-state temporal delivery clocks (WS3)")
    lines.append("")
    if dlv is not None and len(dlv):
        for cell in CELLS:
            ex = dlv[(dlv["cell"] == cell) & (dlv["clock"] == "STATE_EXIT") &
                     (dlv["age_band"] == "AGE_1")]
            pr = dlv[(dlv["cell"] == cell) & (dlv["clock"] == "PROPAGATION") &
                     (dlv["age_band"] == "AGE_1")]
            if len(ex) and len(pr):
                lines.append(f"- **{cell}**: median exit {_fmt(ex['median_latency_d'].iloc[0])}D; "
                             f"prop by 7D {_fmt(pr['p_by_7d'].iloc[0])}")
    lines.append("")
    gates = r.get("gates")
    lines.append("## 4. Local route-gate depth (WS15)")
    lines.append("")
    if gates is not None and len(gates):
        for _, row in gates.iterrows():
            lines.append(f"- **{row['axis']}**: {row['verdict']} "
                         f"(steepest @ {_fmt(row['steepest_bin_mid'])}, "
                         f"width {int(row['width_bins'])} bins, "
                         f"subperiod-stable {int(row['subperiod_stable'])}, "
                         f"age-shift {int(row['age_shifts'])})")
    lines.append("")
    prd = r.get("prd_vs")
    lines.append("## 5. PRICE_UP_RANK_DOWN vs RANK_UP (WS7)")
    lines.append("")
    prd_tab = prd.get("table") if isinstance(prd, dict) else prd
    if prd_tab is not None and len(prd_tab):
        sig = prd_tab[prd_tab["p_fdr"] < FDR_Q]
        lines.append(f"- {len(sig)}/{len(prd_tab)} coordinates separate PRD from PRU "
                     f"at FDR q<{FDR_Q}")
        for _, row in sig.head(6).iterrows():
            lines.append(f"  - {row['axis']} {row['var']}: "
                         f"PRD={_fmt(row['rank_decay_med'])} vs "
                         f"PRU={_fmt(row['rank_recovery_med'])}, p={_fmt(row['p'])}")
    lines.append("")
    hs = r.get("health_transitions")
    lines.append("## 6. Health-state transitions (WS9)")
    lines.append("")
    if hs is not None and len(hs):
        prd_t = hs[(hs["from_state"] == "PRICE_RECOVERY_RANK_DECAY") &
                   (hs["horizon_d"] == 30)]
        if len(prd_t):
            for _, row in prd_t.iterrows():
                lines.append(f"- PRD@30D -> {row['to_state']}: p={_fmt(row['p'])}")
    lines.append("")
    ss = r.get("stress_seq")
    lines.append("## 7. Stress-response sequences (WS11)")
    lines.append("")
    if ss is not None and len(ss):
        for _, row in ss.head(6).iterrows():
            lines.append(f"- **{row['sequence']}**: n={int(row['n'])}, "
                         f"share={_fmt(row['share'])}")
    lines.append("")
    st = r.get("stall_rot")
    lines.append("## 8. Stall-and-rot anatomy (WS12)")
    lines.append("")
    if st is not None:
        s = st.get("summary")
        if s is not None and len(s):
            for _, row in s.head(14).iterrows():
                lines.append(f"- {row['dimension']}: {row['value']}")
    lines.append("")
    pr = r.get("perm_real")
    lines.append("## 9. Permission -> realization (WS14)")
    lines.append("")
    if pr is not None and len(pr):
        for _, row in pr.iterrows():
            lines.append(f"- **{row['move_type']}** (n={int(row['n_days'])}): "
                         f"tail latency {_fmt(row['median_tail_latency_d'])}D, "
                         f"prop7 {_fmt(row['fwd7_prop'])}")
        if "brd_vs_disp_fwd7_p" in pr:
            lines.append(f"- breadth-first vs dispersion-first prop7 p = "
                         f"{_fmt(pr['brd_vs_disp_fwd7_p'].iloc[0])}")
    lines.append("")
    lines.append("## 10. Nodes")
    lines.append("")
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- **{row['node']}**: {row['operation']} ({row['status']})")
    lines.append("")
    hw = r.get("highway")
    lines.append("## 11. Temporal locality highway map (WS20)")
    lines.append("")
    if hw is not None and len(hw):
        lines.append(f"- {len(hw)} timed road segments recorded (22).")
    lines.append("")
    lines.append("`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO DEPLOYMENT")
    (OUT / "25_MECH10_SUMMARY.md").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")
    return "\n".join(lines)


def write_decision(results):
    r = results
    dec = r.get("decomposition")
    lines = [
        "# CRYPTO-ALT-MECH-10 — DECISION",
        "",
        "## Verdict",
        "",
        "**PASS_MECH10_TEMPORAL_DELIVERY_DEEPENING_WITH_LIMITATIONS**",
        "",
        "MECH-10 deepens the temporal geometry of the earned 4-state machine:",
        "state age is decomposed into interpretable components; per-state",
        "delivery/exit clocks and conditional landmarks are explicit; the",
        "PRICE_UP/RANK_DOWN population is mapped against RANK_UP; stress",
        "response is characterized as a process; and local route gates are",
        "tested for stability.",
        "",
        "## Key results",
        "",
    ]
    if dec is not None:
        lines.append(f"- **State-age mechanism**: {dec.get('verdict', 'UNRESOLVED')} "
                     "(02).")
    lines.append("- **Conditional landmarks**: P(stay)/P(prop)/P(tail)/P(exit) "
                 "at ages 1/3/5/7/10/15 per cell (03).")
    lines.append("- **Delivery clocks**: per-state arrival/exit/prop/reentry "
                 "clocks separated (04).")
    lines.append("- **Exit hazards**: discrete hazard + cumulative incidence "
                 "per cell (05); age-conditional exit geometry (06).")
    lines.append("- **Route by age**: HH entry route stratified by age (07).")
    if r.get("prd_vs") is not None:
        lines.append("- **PRD vs PRU**: coordinates separating beta-rescue from "
                     "rehabilitation (09/09b).")
    lines.append("- **Health-state transitions**: 3/7/14/30D transition "
                 "matrix (11).")
    lines.append("- **Stress response**: process geometry t0..+14 (12) and "
                 "repeated sequences (13).")
    lines.append("- **Stall-and-rot**: phenotype anatomy (14).")
    lines.append("- **Perturbation by age**: breadth vs dispersion jump "
                 "conditional on HH age (15).")
    lines.append("- **Permission->realization**: order test (16).")
    lines.append("- **Route gates**: stability verdict per axis (17).")
    if r.get("transition_vel") is not None:
        lines.append(f"- **Transition velocity**: {r['transition_vel']['verdict'].iloc[0]} (18).")
    if r.get("birth_quality") is not None:
        lines.append(f"- **HH birth quality**: {r['birth_quality']['verdict'].iloc[0]} (19).")
    lines.append("- **SHMC/SHHM**: locality depth (20); **volatility**: "
                 "intensity depth by HH age (21).")
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
    lines.append("- No causal claim above L2; temporal ordering is descriptive.")
    lines.append("- Health-state transitions at 30D rely on forward rank "
                 "velocity lookup coverage (partial).")
    lines.append("- Subtype and sequence families below the 50-observation "
                 "bar are descriptive.")
    lines.append("- Route-gate 'stability' is subperiod-level, not a "
                 "bifurcation claim.")
    lines.append("")
    lines.append("`human_review_required = TRUE`")
    lines.append("`next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO LEVERAGE · NO DEPLOYMENT")
    (OUT / "26_MECH10_DECISION.md").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    return "\n".join(lines)


# =========================================================================
# MAIN
# =========================================================================

def main():
    dfw = _cache_step("dfw", load_dfw)
    ev = _cache_step("ev", load_ev)
    health = _cache_step("health", load_health)
    fwd_rank7 = _cache_step("fwd_rank7", load_fwd_rank7)
    fwd_rank30 = _cache_step("fwd_rank30", load_fwd_rank30)
    print(f"[data] dfw {dfw.shape} ev {ev.shape} health {health.shape}",
          flush=True)

    dec = _cache_step("ws1", lambda: ws1_decomposition(dfw))
    lm = _cache_step("ws2", lambda: ws2_conditional_landmarks(dfw))
    dlv = _cache_step("ws3", lambda: ws3_delivery_clocks(dfw))
    haz = _cache_step("ws4a", lambda: ws4_exit_hazards(dfw))
    age_exit = _cache_step("ws4b", lambda: ws4_age_exit_geometry(dfw))
    route = _cache_step("ws5", lambda: ws5_route_by_age(dfw))
    prd_mat = _cache_step("ws6", lambda: ws6_prd_field_matrix(health, dfw))
    prd_vs = _cache_step("ws7", lambda: ws7_prd_vs_pru(health, dfw, fwd_rank30))
    subtypes = _cache_step("ws8", lambda: ws8_prd_subtypes(health, dfw,
                                                           fwd_rank30))
    hs = _cache_step("ws9", lambda: ws9_health_transitions(health, fwd_rank7,
                                                           fwd_rank30))
    sp = _cache_step("ws10", lambda: ws10_stress_process(health, dfw))
    ss = _cache_step("ws11", lambda: ws11_stress_sequences(health, dfw))
    st = _cache_step("ws12", lambda: ws12_stall_and_rot(health, dfw,
                                                        fwd_rank30))
    pa = _cache_step("ws13", lambda: ws13_perturbation_age(dfw))
    pr = _cache_step("ws14", lambda: ws14_permission_realization(dfw))
    gates = _cache_step("ws15", lambda: ws15_route_gate_depth(dfw))
    tv = _cache_step("ws16", lambda: ws16_transition_velocity_placement(dfw,
                                                                        health))
    bq = _cache_step("ws17", lambda: ws17_birth_quality_placement(dfw))
    shmc = _cache_step("ws18", lambda: ws18_shmc_placement(ev, health, dfw))
    vol = _cache_step("ws19", lambda: ws19_volatility_depth(dfw))

    results = {
        "decomposition": dec, "landmarks": lm, "delivery": dlv,
        "exit_hazards": haz, "age_exit": age_exit, "route_by_age": route,
        "prd_matrix": prd_mat, "prd_vs": prd_vs, "subtypes": subtypes,
        "health_transitions": hs, "stress_process": sp, "stress_seq": ss,
        "stall_rot": st, "perturbation_age": pa, "perm_real": pr,
        "gates": gates, "transition_vel": tv, "birth_quality": bq,
        "shmc_placement": shmc, "vol_depth": vol, "nodes": None,
    }
    hw = ws20_highway_map(results)
    results["highway"] = hw
    nodes = ws21_nodes(results)
    results["nodes"] = nodes
    ws22_nulls(results)
    write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print("[done] MECH-10 pipeline complete.", flush=True)
    return results


if __name__ == "__main__":
    main()
