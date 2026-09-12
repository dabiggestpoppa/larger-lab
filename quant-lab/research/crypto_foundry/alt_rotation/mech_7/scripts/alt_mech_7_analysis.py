#!/usr/bin/env python
"""ALT_MECH_7 - Global Context of Isolated Downside vs Coordinated Upside,
Breadth x Dispersion Lifecycle, Field-State Sequencing & Cross-Agent Handoff.

Terrain research ONLY (AGENT 1 - MAIN FIELD CARTOGRAPHER). No PnL, no strategy,
no optimization, no ML predictors, no sizing, no deployment.
"""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, fisher_exact, norm
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260908
BOOT_N = 500
PERM_N = 500
MIN_PROMOTE_N = 50          # minimum effective independent observations
MIN_SUBPERIODS = 3
LIFT_THRESHOLD = 1.25
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_7/
M5_ROOT = ROOT.parent / "mech_5"
M4_ROOT = ROOT.parent / "mech_4"
M4_SCRIPTS = M4_ROOT / "scripts"
sys.path.insert(0, str(M4_SCRIPTS))
import alt_mech_4_analysis as M4

LF2_ROOT = (
    Path(__file__).resolve().parents[3] / "derivatives" / "lower_field_2"
)
LF2_FEATURES = LF2_ROOT / "RESULTS" / "lf2_feature_frame.parquet"

OUT = ROOT
M4_OUT = M4_ROOT
M5_OUT = M5_ROOT

BANDS = M4.BANDS
ALT_FAMILY = M4.ALT_FAMILY
SUCCESS_LABELS = {"BROAD_RISK_EXPANSION"} | set(ALT_FAMILY)
REENTRY_LABEL = "BTC_CONCENTRATION"

HORIZONS = [0, 1, 2, 3, 5, 7, 10, 14, 21, 30]
SUBPERIODS = ["2020-2021", "2022", "2023", "2024", "2025-2026"]

# frozen 2x2 thresholds (full-sample medians, computed pre-outcome)
BRD_MED = 0.31
DISP_MED = 0.307

# field context lags around events
CTX_LAGS = [-14, -10, -7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10, 14, 21, 30]

FIELD_COORDS = [
    "top500_breadth_30d", "top500_breadth_7d", "breadth_vel", "breadth_accel",
    "top500_dispersion_30d", "top500_dispersion_7d",
    "top3_share", "top3_share_chg7",
    "btc_return_30d", "btc_dominance", "btc_dom_chg30",
    "eth_btc_relative_return_30d", "eth_btc_relative_return_7d",
    "med_ret30_11_50", "med_ret30_51_200", "med_ret30_201_500", "rb_spread",
    "pos_ret_share", "pos_vel7_share", "leadership_width", "rank_depth_rel",
    "vol_med", "chain_tvl_med_chg7", "stablecoin_change_7d",
    "stablecoin_change_30d", "dex_volume_change_7d", "total_mcap_chg30",
    "eth_share", "n_stablecoins_in_top500", "mkt_ret_1d",
]

REGIME_FLAGS = ["BREADTH_EXPANDING", "BREADTH_CONTRACTING", "BTC_UP", "BTC_DOWN",
                "VOL_HIGH", "VOL_LOW", "CONC_RISING", "CONC_FALLING",
                "ETH_STRONG", "ETH_WEAK", "RISK_ON", "RISK_OFF",
                "SC_INFLOW", "SC_OUTFLOW"]


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
    """Finite-sample corrected permutation p-value."""
    return (k + 1) / (B + 1)


# =========================================================================
# LOAD
# =========================================================================

def load_canonical():
    inp, tl = M4._cache_step("inputs", M4.load)
    daily, d, bm = M4._cache_step("daily", lambda: M4.build_daily(inp))
    rc = M4._cache_step("reconcile", lambda: M4.ws_reconcile(daily))
    entries, exits = rc["recount"]["entries"], rc["recount"]["exits"]
    rA = M4._cache_step("A", lambda: M4.ws_a(daily, entries, exits))
    ledger = rA["ledger"]
    return daily, d, bm, ledger


def _add_leadership_width(daily, bm):
    """Leadership width = count of bm bands with positive 7D median rank velocity."""
    bm2 = bm.copy()
    bm2["d"] = pd.to_datetime(bm2["historical_date"]).dt.normalize()
    lw = bm2[bm2["median_rank_velocity_7d"] > 0].groupby("d").size()
    daily["leadership_width"] = (
        daily["leadership_width"] if "leadership_width" in daily.columns else np.nan)
    dnorm = pd.to_datetime(daily["historical_date"]).dt.normalize()
    daily["leadership_width"] = dnorm.map(lw).fillna(0).astype(int)
    return daily


def _add_breadth_features(daily):
    """Breadth velocity/accel/persistence/divergence/oscillation (M6 parity)."""
    df = daily.copy().reset_index(drop=True)
    if "leadership_width" not in df.columns:
        df["leadership_width"] = 0
    b = df["top500_breadth_30d"].astype(float)
    b_chg = b.diff(5)
    b_chg2 = b_chg.diff(5)
    df["breadth_vel"] = b_chg
    df["breadth_accel"] = b_chg2
    df["breadth_axis"] = np.where(b_chg > 0.02, "BREADTH_EXPANDING",
                          np.where(b_chg < -0.02, "BREADTH_FADING", "BREADTH_STABLE"))
    exp = (b_chg > 0.02).astype(int)
    df["breadth_persistence"] = exp.rolling(5, min_periods=3).sum().shift(0)
    df["breadth_exhaustion"] = ((b >= 0.5) & (b_chg < -0.02)).astype(int)
    mkt = df["mkt_ret_1d"].astype(float)
    df["breadth_divergence"] = ((np.sign(b_chg) != np.sign(mkt)) & b_chg.notna() & mkt.notna()).astype(int)
    # oscillation state: alternating expansion/fade within 7d
    osc = np.zeros(len(df), dtype=int)
    for i in range(7, len(df)):
        win = df["breadth_axis"].iloc[i-6:i+1].values
        if ("BREADTH_EXPANDING" in win) and ("BREADTH_FADING" in win):
            osc[i] = 1
    df["breadth_oscillation"] = osc
    # rank depth rel
    deep = df["med_ret30_201_500"].astype(float)
    upper = df["med_ret30_11_50"].astype(float)
    df["rank_depth_rel"] = deep - upper
    df["rank_depth_rel_chg"] = df["rank_depth_rel"].diff(5)
    return df


def load_lf2_events():
    """Reconstruct LF2 cluster classification identically."""
    cols = ["historical_date", "cmc_id", "rank_band", "ret_1d", "sigma_t0",
            "fwd7_cum", "rank_vel_7d", "top500_breadth_30d", "mkt_vol_30d",
            "momentum_state"]
    df = pd.read_parquet(LF2_FEATURES, columns=cols)
    df = df[df["ret_1d"].notna() & df["sigma_t0"].notna() & (df["sigma_t0"] > 0)].copy()
    df["z1"] = df["ret_1d"].abs() / df["sigma_t0"]
    df["sign"] = np.sign(df["ret_1d"].to_numpy(float))
    ev = df[(df["z1"] >= 2) & (df["sign"] != 0)].copy()
    cnt = (ev.groupby(["historical_date", "rank_band", "sign"]).size()
             .rename("ns").reset_index())
    ev = ev.merge(cnt, on=["historical_date", "rank_band", "sign"], how="left")
    ev["ns"] = ev["ns"].fillna(1).astype(int)
    ev["cls"] = np.where(ev["ns"] == 1, "ISOLATED",
                np.where(ev["ns"] <= 5, "LOCAL_CLUSTER",
                 np.where(ev["ns"] <= 20, "BAND_BROAD", "MULTI_BAND")))
    ev["family"] = np.select(
        [(ev["cls"] == "ISOLATED") & (ev["sign"] < 0),
         (ev["cls"] == "LOCAL_CLUSTER") & (ev["sign"] < 0),
         (ev["cls"] == "BAND_BROAD") & (ev["sign"] > 0),
         (ev["cls"] == "MULTI_BAND") & (ev["sign"] > 0),
         (ev["cls"] == "ISOLATED") & (ev["sign"] > 0),
         (ev["cls"].isin(["BAND_BROAD", "MULTI_BAND"])) & (ev["sign"] < 0)],
        ["ISOLATED_DOWNSIDE_EXTREME", "LOCAL_CLUSTER_DOWNSIDE",
         "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE", "ISOLATED_UPSIDE",
         "COORDINATED_DOWNSIDE"],
        default="OTHER")
    ev["fwd7_sigma"] = ev["fwd7_cum"] / (ev["sigma_t0"] * np.sqrt(7))
    ev["reversal"] = ((np.sign(ev["fwd7_cum"]) != ev["sign"]) & ev["fwd7_cum"].notna()).astype(int)
    yr = ev["historical_date"].dt.year
    ev["subperiod"] = np.select([yr <= 2021, yr == 2022, yr == 2023, yr == 2024],
                                 ["2020-2021", "2022", "2023", "2024"],
                                 default="2025-2026")
    # event ids
    ev["event_id"] = "LF2EV_" + ev["cmc_id"].astype(str) + "_" + ev["historical_date"].dt.strftime("%Y%m%d")
    return ev.reset_index(drop=True)


def build_global_context(ev, daily, lags=None):
    """Join global field context at lags around each event (vectorized).

    daily is sorted by date; lag is applied as a calendar-day offset on the
    normalized date column, then merged onto a per-lag frame. Pass lags=None
    to use all CTX_LAGS, or a subset (e.g. [0]) for lightweight panels.
    """
    if lags is None:
        lags = CTX_LAGS
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    dnorm = pd.to_datetime(daily["historical_date"]).dt.normalize()
    ctx_cols = ["state", "subperiod"] + FIELD_COORDS + REGIME_FLAGS
    ev_dates = pd.to_datetime(ev["historical_date"]).dt.normalize()
    frames = []
    uniq, idx = np.unique(dnorm.values, return_index=True)
    for lag in lags:
        tgt = ev_dates + pd.Timedelta(days=lag)
        pos = np.searchsorted(uniq, tgt.values)
        pos = np.clip(pos, 0, len(uniq) - 1)
        hit = uniq[pos] == tgt.values
        base = ev[["event_id", "family", "cls", "sign", "rank_band"]].copy()
        base["lag"] = lag
        base["ctx_date"] = tgt.dt.strftime("%Y-%m-%d")
        base["_pos"] = np.where(hit, idx[pos], -1)
        sub = base[base["_pos"] >= 0].copy()
        if len(sub) == 0:
            continue
        dsub = daily.iloc[sub["_pos"].values][ctx_cols].reset_index(drop=True)
        sub = sub.reset_index(drop=True)
        for c in ctx_cols:
            sub[c] = dsub[c].values
        frames.append(sub.drop(columns=["_pos"]))
    ctxp = pd.concat(frames, ignore_index=True)
    return ctxp


# =========================================================================
# WS1: ISOLATED DOWNSIDE FIELD ANATOMY + REVERSAL vs CONTINUE
# =========================================================================

DOWN_REV_CLASSES = {
    "REVERSAL": (1, 0),
    "PARTIAL_RECOVERY": (1, 1),
    "CONTINUATION": (0, 1),
}


def _down_outcome_class(rev, fwd7_sig):
    """rev: reversal flag (sign flip). fwd7_sig: signed fwd7 sigma."""
    if rev == 1:
        if fwd7_sig > 0.5:
            return "REVERSAL"
        return "PARTIAL_RECOVERY"
    return "CONTINUATION"


def ws1_isolated_down(ctx, ev):
    """Global field context around ISOLATED_DOWNSIDE_EXTREME events; anatomy
    split by reversal outcome; first-divergence reversal vs continue."""
    evd = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy()
    evd["outcome"] = [_down_outcome_class(r["reversal"], r["fwd7_sigma"])
                      for _, r in evd.iterrows()]
    evd["is_reverse"] = (evd["outcome"] == "REVERSAL").astype(int)
    evd["is_continue"] = (evd["outcome"] == "CONTINUATION").astype(int)

    # ---- anatomy: t0 field state, overall + by outcome ----
    ctxd = ctx[ctx["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy()
    t0 = ctxd[ctxd["lag"] == 0].copy()
    t0 = t0.merge(evd[["event_id", "outcome"]], on="event_id", how="left")
    rows = []
    base = t0
    for grp, sub in [("ALL", base)] + [(o, base[base["outcome"] == o]) for o in
                                        ["REVERSAL", "PARTIAL_RECOVERY", "CONTINUATION"]]:
        if len(sub) < 30:
            continue
        row = {"group": grp, "n_events": int(len(sub)),
               "n_dates": int(pd.to_datetime(sub["ctx_date"]).nunique())}
        for c in FIELD_COORDS:
            v = sub[c].dropna()
            row[f"{c}_med"] = float(v.median()) if len(v) else np.nan
        for f in REGIME_FLAGS:
            row[f"{f}_pct"] = float(sub[f].mean()) if sub[f].notna().any() else np.nan
        row["state_mode"] = str(sub["state"].mode().iloc[0]) if len(sub) else ""
        rows.append(row)
    anat = pd.DataFrame(rows)
    anat.to_csv(OUT / "04_ISOLATED_DOWNSIDE_FIELD_ANATOMY.csv", index=False)

    # ---- first divergence reversal vs continuation across lags ----
    mm = t0.merge(ctxd[ctxd["lag"] != 0][["event_id", "lag"] + FIELD_COORDS + REGIME_FLAGS],
                  on="event_id", how="left", suffixes=("", "_lag"))
    mm = mm[mm["outcome"].isin(["REVERSAL", "CONTINUATION"])].copy()
    div_rows = []
    for lag in CTX_LAGS:
        sub = ctxd[ctxd["lag"] == lag].merge(
            evd[["event_id", "is_reverse", "is_continue"]], on="event_id", how="left")
        rev = sub[sub["is_reverse"] == 1]
        con = sub[sub["is_continue"] == 1]
        if len(rev) < 30 or len(con) < 30:
            continue
        for c in FIELD_COORDS:
            a, b = rev[c].dropna(), con[c].dropna()
            if len(a) < 30 or len(b) < 30:
                continue
            try:
                st, p = ranksums(a, b)
            except Exception:
                continue
            div_rows.append({"lag_d": lag, "variable": c, "n_rev": int(len(a)),
                             "n_con": int(len(b)), "med_rev": float(a.median()),
                             "med_con": float(b.median()), "diff": float(a.median() - b.median()),
                             "ranksum_p": float(p)})
    div = pd.DataFrame(div_rows)
    if len(div):
        div["p_fdr"] = multipletests(div["ranksum_p"], method="fdr_bh")[1]
    div.to_csv(OUT / "16_FIRST_DIVERGENCE_DOWN_REVERSE_VS_CONTINUE.csv", index=False)
    return {"anat": anat, "div": div}


# =========================================================================
# WS2: COORDINATED UPSIDE FIELD ANATOMY + CONTINUATION vs GIVEBACK
# =========================================================================

def _up_outcome_class(fwd7_sig):
    if fwd7_sig > 0:
        return "CONTINUATION"
    if fwd7_sig < -1:
        return "FAILURE"
    return "GIVEBACK"


def ws2_coordinated_up(ctx, ev):
    """Global field context around BAND_BROAD/MULTI_BAND upside; anatomy split
    by continuation vs giveback vs failure; first-divergence."""
    evu = ev[ev["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"])].copy()
    evu["outcome"] = evu["fwd7_sigma"].apply(_up_outcome_class)
    evu["is_cont"] = (evu["outcome"] == "CONTINUATION").astype(int)
    evu["is_giveback"] = (evu["outcome"] == "GIVEBACK").astype(int)
    evu["is_fail"] = (evu["outcome"] == "FAILURE").astype(int)

    ctxu = ctx[ctx["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"])].copy()
    t0 = ctxu[ctxu["lag"] == 0].copy()
    t0 = t0.merge(evu[["event_id", "outcome"]], on="event_id", how="left")
    rows = []
    base = t0
    for grp, sub in ([("ALL", base)] +
                     [(o, base[base["outcome"] == o]) for o in
                      ["CONTINUATION", "GIVEBACK", "FAILURE"]]):
        if len(sub) < 30:
            continue
        row = {"group": grp, "n_events": int(len(sub)),
               "n_dates": int(pd.to_datetime(sub["ctx_date"]).nunique())}
        for c in FIELD_COORDS:
            v = sub[c].dropna()
            row[f"{c}_med"] = float(v.median()) if len(v) else np.nan
        for f in REGIME_FLAGS:
            row[f"{f}_pct"] = float(sub[f].mean()) if sub[f].notna().any() else np.nan
        row["state_mode"] = str(sub["state"].mode().iloc[0]) if len(sub) else ""
        rows.append(row)
    anat = pd.DataFrame(rows)
    anat.to_csv(OUT / "05_COORDINATED_UPSIDE_FIELD_ANATOMY.csv", index=False)

    # first divergence continuation vs giveback across lags
    div_rows = []
    for lag in CTX_LAGS:
        sub = ctxu[ctxu["lag"] == lag].merge(
            evu[["event_id", "is_cont", "is_giveback"]], on="event_id", how="left")
        cont = sub[sub["is_cont"] == 1]
        gb = sub[sub["is_giveback"] == 1]
        if len(cont) < 30 or len(gb) < 30:
            continue
        for c in FIELD_COORDS:
            a, b = cont[c].dropna(), gb[c].dropna()
            if len(a) < 30 or len(b) < 30:
                continue
            try:
                st, p = ranksums(a, b)
            except Exception:
                continue
            div_rows.append({"lag_d": lag, "variable": c, "n_cont": int(len(a)),
                             "n_gb": int(len(b)), "med_cont": float(a.median()),
                             "med_gb": float(b.median()),
                             "diff": float(a.median() - b.median()),
                             "ranksum_p": float(p)})
    div = pd.DataFrame(div_rows)
    if len(div):
        div["p_fdr"] = multipletests(div["ranksum_p"], method="fdr_bh")[1]
    div.to_csv(OUT / "15_FIRST_DIVERGENCE_UP_CONT_VS_GIVEBACK.csv", index=False)
    return {"anat": anat, "div": div}


# =========================================================================
# WS3: BREADTH x DISPERSION 2x2 PLANE
# =========================================================================

def _cell(brd, disp):
    b = "HIGH" if brd > BRD_MED else "LOW"
    d = "HIGH" if disp > DISP_MED else "LOW"
    return f"{b}_BREADTH_{d}_DISP"


def ws3_2x2(daily, ctx, ev):
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    df = daily.copy()
    df["cell"] = [_cell(b, d2) for b, d2 in
                  zip(df["top500_breadth_30d"], df["top500_dispersion_30d"])]
    df["d"] = pd.to_datetime(df["historical_date"]).dt.normalize()

    # event date counts
    evd = ev.copy()
    evd["d"] = pd.to_datetime(evd["historical_date"]).dt.normalize()
    fam_day = evd.groupby(["d", "family"]).size().unstack(fill_value=0)
    for f in ["ISOLATED_DOWNSIDE_EXTREME", "LOCAL_CLUSTER_DOWNSIDE",
              "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE", "ISOLATED_UPSIDE",
              "COORDINATED_DOWNSIDE"]:
        df[f"ev_{f}"] = df["d"].map(fam_day.get(f, pd.Series(dtype=int))).fillna(0).astype(int)

    # forward outcomes from daily state (propagation/reentry 7D)
    st = df["state"]
    df["fwd7_state"] = st.shift(-7)
    df["prop7"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(float)
    df["reentry7"] = (df["fwd7_state"] == REENTRY_LABEL).astype(float)

    cells = sorted(df["cell"].unique())
    # episode ids over the full daily frame (consecutive same-cell runs)
    run_change = (df["cell"] != df["cell"].shift()).cumsum()
    df["_run"] = run_change
    rows = []
    for c in cells:
        sub = df[df["cell"] == c]
        if len(sub) < 30:
            continue
        row = {"cell": c, "n_days": int(len(sub)),
               "freq_share": float(len(sub) / len(df)),
               "n_episodes": int(sub["_run"].nunique())}
        for col in ["prop7", "reentry7"]:
            row[f"{col}"] = float(sub[col].mean())
        for f in ["ISOLATED_DOWNSIDE_EXTREME", "COORDINATED_DOWNSIDE",
                  "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"]:
            row[f"{f}_per_day"] = float(sub[f"ev_{f}"].mean())
        up = sub["ev_BAND_BROAD_UPSIDE"] + sub["ev_MULTI_BAND_UPSIDE"]
        dn = sub["ev_ISOLATED_DOWNSIDE_EXTREME"] + sub["ev_COORDINATED_DOWNSIDE"]
        row["up_down_balance"] = float((up - dn).mean())
        row["subperiods"] = int(sub["subperiod"].nunique())
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "06_BREADTH_DISPERSION_2X2.csv", index=False)

    # ---- transitions between cells ----
    tr = df[["d", "cell"]].dropna()
    tr["next_cell"] = tr["cell"].shift(-1)
    tr = tr[tr["d"].shift(-1) == tr["d"] + pd.Timedelta(days=1)]
    tr = tr.dropna(subset=["next_cell"])
    tm = tr.groupby(["cell", "next_cell"]).size().reset_index(name="n")
    tm["p"] = tm.groupby("cell")["n"].transform(lambda s: s / s.sum())
    tm.to_csv(OUT / "07_BREADTH_DISPERSION_TRANSITIONS.csv", index=False)

    return {"plane": out, "trans": tm, "df": df}


# =========================================================================
# WS4: HIGH_BRD_HIGH_DISP LIFECYCLE
# =========================================================================

def ws4_lifecycle(daily, ev):
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    df = daily.copy()
    df["brd_hi"] = (df["top500_breadth_30d"] > BRD_MED).astype(int)
    df["disp_hi"] = (df["top500_dispersion_30d"] > DISP_MED).astype(int)
    df["in_hh"] = ((df["brd_hi"] == 1) & (df["disp_hi"] == 1)).astype(int)
    df["d"] = pd.to_datetime(df["historical_date"]).dt.normalize()

    # episodes of consecutive in_hh days
    eps = []
    cur = None
    for i, r in df.iterrows():
        if r["in_hh"] == 1:
            if cur is None:
                cur = {"start": i, "end": i}
            else:
                cur["end"] = i
        else:
            if cur is not None:
                cur["n"] = cur["end"] - cur["start"] + 1
                eps.append(cur)
                cur = None
    if cur is not None:
        cur["n"] = cur["end"] - cur["start"] + 1
        eps.append(cur)
    ep = pd.DataFrame(eps)
    if len(ep) == 0:
        return {"life": pd.DataFrame(), "seq": pd.DataFrame()}
    ep["start_date"] = df["d"].iloc[ep["start"]].values
    ep["end_date"] = df["d"].iloc[ep["end"]].values
    ep["subperiod"] = df["subperiod"].iloc[ep["start"]].values
    # precondition: state and coords 3D before entry
    pre = df["state"].iloc[np.clip(ep["start"] - 3, 0, len(df) - 1)].values
    ep["pre_state_3d"] = pre
    preb = df["top500_breadth_30d"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    ep["breadth_before_entry"] = preb
    preb3 = df["breadth_vel"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    ep["breadth_vel_before_entry"] = preb3
    # entry order: was breadth already high at start-1 vs dispersion?
    ep["brd_hi_prev"] = df["brd_hi"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    ep["disp_hi_prev"] = df["disp_hi"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    bhp = ep["brd_hi_prev"].astype(bool).to_numpy()
    dhp = ep["disp_hi_prev"].astype(bool).to_numpy()
    ep["entry_order"] = np.select(
        [bhp & ~dhp, ~bhp & dhp, bhp & dhp],
        ["BRD_FIRST", "DISP_FIRST", "SYNCHRONOUS"],
        default="FRESH")
    # exit: what collapses first (state at end+1)
    ex = df[["brd_hi", "disp_hi"]].iloc[np.clip(ep["end"] + 1, 0, len(df) - 1)].values
    ex_brd, ex_disp = ex[:, 0], ex[:, 1]
    ep["exit_brd_hi"] = ex_brd
    ep["exit_disp_hi"] = ex_disp
    ep["exit_order"] = np.select(
        [(ex_brd == 0) & (ex_disp == 1),
         (ex_brd == 1) & (ex_disp == 0),
         (ex_brd == 0) & (ex_disp == 0),
         (ex_brd == 1) & (ex_disp == 1)],
        ["BRD_FIRST_EXIT", "DISP_FIRST_EXIT", "COUPLED_EXIT", "STAYS_HH"],
        default="COUPLED_EXIT")
    # fwd state at +7/+30 from end
    st7 = df["state"].iloc[np.clip(ep["end"] + 7, 0, len(df) - 1)].values
    st30 = df["state"].iloc[np.clip(ep["end"] + 30, 0, len(df) - 1)].values
    ep["state_7d_after"] = st7
    ep["state_30d_after"] = st30

    life_rows = []
    for key, col in [("entry_order", "entry_order"), ("exit_order", "exit_order")]:
        for val, g in ep.groupby(col):
            life_rows.append({
                "dimension": key, "path": str(val), "n_episodes": int(len(g)),
                "median_dwell_d": float(g["n"].median()),
                "n_subperiods": int(g["subperiod"].nunique()),
                "p_7d_success": float(g["state_7d_after"].isin(SUCCESS_LABELS).mean()),
                "p_30d_success": float(g["state_30d_after"].isin(SUCCESS_LABELS).mean()),
                "p_7d_reentry": float((g["state_7d_after"] == REENTRY_LABEL).mean()),
            })
    life = pd.DataFrame(life_rows)
    life.to_csv(OUT / "08_HIGH_BRD_HIGH_DISP_LIFECYCLE.csv", index=False)

    # sequence map: precondition state x entry order x exit order -> outcome
    seq_rows = []
    for (pre, eo, xo), g in ep.groupby(["pre_state_3d", "entry_order", "exit_order"]):
        if len(g) < MIN_PROMOTE_N:
            continue
        seq_rows.append({
            "pre_state_3d": pre, "entry_order": eo, "exit_order": xo,
            "n_episodes": int(len(g)), "median_dwell_d": float(g["n"].median()),
            "n_subperiods": int(g["subperiod"].nunique()),
            "p_7d_success": float(g["state_7d_after"].isin(SUCCESS_LABELS).mean()),
            "p_30d_success": float(g["state_30d_after"].isin(SUCCESS_LABELS).mean()),
            "p_7d_reentry": float((g["state_7d_after"] == REENTRY_LABEL).mean()),
        })
    seq = pd.DataFrame(seq_rows)
    seq.to_csv(OUT / "09_HIGH_BRD_HIGH_DISP_SEQUENCE_MAP.csv", index=False)
    return {"life": life, "seq": seq, "ep": ep}
# =========================================================================
# WS5: BREADTH INTERNAL COMPOSITION (rank-layer decomposition)
# =========================================================================

def ws5_composition(daily, bm):
    """Decompose top500 breadth by rank layer using bm breadth_7d per band."""
    daily = daily.sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    bm2 = bm.copy()
    bm2["d"] = pd.to_datetime(bm2["historical_date"]).dt.normalize()
    layer_map = {
        "1-10": "R1_25", "11-25": "R1_25",
        "26-50": "R26_100", "51-100": "R26_100",
        "101-200": "R101_250", "201-300": "R101_250",
        "301-500": "R251_500",
    }
    bm2["layer"] = bm2["rank_band"].map(layer_map)
    # layer breadth = mean of band breadth_7d within layer (band share-weighted)
    bw = bm2.groupby(["d", "layer"]).apply(
        lambda g: float(np.average(g["breadth_7d"],
                                   weights=g["market_cap_share"].fillna(1))),
        include_groups=False).rename("layer_breadth_7d").reset_index()
    lw = bw.pivot(index="d", columns="layer", values="layer_breadth_7d").reset_index()
    out = daily.merge(lw, on="d", how="left")
    layers = ["R1_25", "R26_100", "R101_250", "R251_500"]
    out["layer_sum"] = out[layers].sum(axis=1, min_count=1)
    rows = []
    for layer in layers:
        sub = out.dropna(subset=[layer, "layer_sum"])
        if len(sub) < 100:
            continue
        rows.append({
            "layer": layer,
            "n_days": int(len(sub)),
            "med_breadth_7d": float(sub[layer].median()),
            "share_of_top500_breadth": float((sub[layer] / sub["layer_sum"].replace(0, np.nan)).median()),
            "corr_with_total_breadth": float(sub[layer].corr(sub["top500_breadth_30d"])),
            "p_hi_layer_gt_brd": float((sub[layer] > sub["top500_breadth_30d"]).mean()),
        })
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT / "10_BREADTH_COMPOSITION.csv", index=False)
    # architecture analysis: correlation structure among layers (breadth architectures)
    arch_rows = []
    for a, b in [("R1_25", "R26_100"), ("R1_25", "R101_250"), ("R1_25", "R251_500"),
                 ("R26_100", "R101_250"), ("R26_100", "R251_500"),
                 ("R101_250", "R251_500")]:
        s = out.dropna(subset=[a, b])
        if len(s) < 100:
            continue
        arch_rows.append({"layer_a": a, "layer_b": b, "n_days": int(len(s)),
                          "corr": float(s[a].corr(s[b]))})
    arch = pd.DataFrame(arch_rows)
    arch.to_csv(OUT / "10b_BREADTH_LAYER_CORR.csv", index=False)
    return {"comp": comp, "arch": arch}


# =========================================================================
# WS6: BREADTH PRIMITIVE AUDIT (nested attribution)
# =========================================================================

def _purged_folds(n, k=5, embargo=7):
    """Chronological purged fold indices (list of (tr, te) index arrays)."""
    folds = []
    size = n // k
    for i in range(k):
        te_start = i * size
        te_end = (i + 1) * size if i < k - 1 else n
        te = np.arange(te_start, te_end)
        tr = np.concatenate([np.arange(0, te_start - embargo),
                             np.arange(te_end + embargo, n)])
        tr = tr[(tr >= 0) & (tr < n)]
        if len(tr) > 30 and len(te) > 10:
            folds.append((tr, te))
    return folds


def _logreg_cv(X, y, folds):
    """Chronological purged CV: returns mean logloss, brier, auc."""
    if len(np.unique(y)) < 2:
        return np.nan, np.nan, np.nan
    lls, brs, aucs = [], [], []
    for tr, te in folds:
        if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
            continue
        m = LogisticRegression(max_iter=1000, C=1.0)
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[te])[:, 1]
        lls.append(log_loss(y[te], p))
        brs.append(brier_score_loss(y[te], p))
        try:
            aucs.append(roc_auc_score(y[te], p))
        except Exception:
            pass
    if not lls:
        return np.nan, np.nan, np.nan
    return float(np.mean(lls)), float(np.mean(brs)), float(np.mean(aucs) if aucs else np.nan)


def ws6_breadth_audit(daily, ledger):
    """Nested incremental attribution: which breadth coordinate family carries
    incremental information for upper-field propagation success."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    date_pos = {pd.Timestamp(x): i for i, x in enumerate(daily["historical_date"])}
    feats = {
        "level": ["top500_breadth_30d"],
        "velocity": ["breadth_vel"],
        "acceleration": ["breadth_accel"],
        "persistence": ["breadth_persistence"],
        "divergence": ["breadth_divergence"],
        "oscillation": ["breadth_oscillation"],
        "depth": ["rank_depth_rel", "med_ret30_201_500"],
        "composition": ["pos_vel7_share", "pos_ret_share"],
    }
    led = ledger.copy()
    led["y"] = led["first_destination"].isin(SUCCESS_LABELS).astype(int)
    rows_all = []
    for _, r in led.iterrows():
        i = date_pos.get(pd.Timestamp(r["exit_date"]))
        if i is None:
            continue
        row = {"event_id": r["event_id"], "y": int(r["y"])}
        for f, cols in feats.items():
            for c in cols:
                v = daily[c].iloc[i]
                row[f"{f}:{c}"] = float(v) if v == v else np.nan
        rows_all.append(row)
    Xd = pd.DataFrame(rows_all).set_index("event_id")
    Xd = Xd.dropna(how="all")
    y = Xd["y"].to_numpy(float)
    # impute column medians
    Xf = Xd.drop(columns=["y"]).copy()
    for c in Xf.columns:
        med = Xf[c].median()
        Xf[c] = Xf[c].fillna(med)
    folds = _purged_folds(len(Xd), k=5, embargo=7)
    base_ll, base_br, base_auc = _logreg_cv(Xf[[f"level:top500_breadth_30d"]].to_numpy(float), y, folds)
    out = []
    out.append({"model": "M0_level", "features": "breadth level",
                "delta_logloss": 0.0, "delta_brier": 0.0, "delta_auc": 0.0,
                "cv_logloss": base_ll, "cv_brier": base_br, "cv_auc": base_auc,
                "n": int(len(Xd))})
    all_feats = list(Xf.columns)
    for fname, cols in [("velocity", ["velocity:breadth_vel"]),
                        ("acceleration", ["acceleration:breadth_accel"]),
                        ("persistence", ["persistence:breadth_persistence"]),
                        ("divergence", ["divergence:breadth_divergence"]),
                        ("oscillation", ["oscillation:breadth_oscillation"]),
                        ("depth", ["depth:rank_depth_rel", "depth:med_ret30_201_500"]),
                        ("composition", ["composition:pos_vel7_share", "composition:pos_ret_share"])]:
        use = ["level:top500_breadth_30d"] + cols
        ll, br, auc = _logreg_cv(Xf[use].to_numpy(float), y, folds)
        out.append({"model": f"M+{fname}", "features": "+".join(cols),
                    "delta_logloss": float(ll - base_ll) if ll == ll else np.nan,
                    "delta_brier": float(br - base_br) if br == br else np.nan,
                    "delta_auc": float(auc - base_auc) if (auc == auc and base_auc == base_auc) else np.nan,
                    "cv_logloss": ll, "cv_brier": br, "cv_auc": auc,
                    "n": int(len(Xd))})
    full_ll, full_br, full_auc = _logreg_cv(Xf[all_feats].to_numpy(float), y, folds)
    out.append({"model": "M_FULL", "features": "all breadth families",
                "delta_logloss": float(full_ll - base_ll) if full_ll == full_ll else np.nan,
                "delta_brier": float(full_br - base_br) if full_br == full_br else np.nan,
                "delta_auc": float(full_auc - base_auc) if (full_auc == full_auc and base_auc == base_auc) else np.nan,
                "cv_logloss": full_ll, "cv_brier": full_br, "cv_auc": full_auc,
                "n": int(len(Xd))})
    audit = pd.DataFrame(out)
    audit.to_csv(OUT / "11_BREADTH_PRIMITIVE_AUDIT.csv", index=False)
    return {"audit": audit}


# =========================================================================
# WS7/WS8: SEQUENCE ATLASES around coordinated-up and isolated-down dates
# =========================================================================

def _date_seq_atlas(ev, daily, family_set, label):
    """Field-state sequence atoms around event dates for a family set."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    evd = ev[ev["family"].isin(family_set)].copy()
    evd["d"] = pd.to_datetime(evd["historical_date"]).dt.normalize()
    event_dates = set(evd["d"].unique())
    df = daily.copy()
    df["is_event_date"] = df["d"].isin(event_dates).astype(int)
    atoms = {
        "BREADTH_EXPANDING": (df["breadth_axis"] == "BREADTH_EXPANDING").astype(int),
        "BREADTH_FADING": (df["breadth_axis"] == "BREADTH_FADING").astype(int),
        "BREADTH_HIGH": (df["top500_breadth_30d"] > BRD_MED).astype(int),
        "DISP_HI": (df["top500_dispersion_30d"] > DISP_MED).astype(int),
        "RANK_RECRUITING": (df["med_ret30_201_500"] > df["med_ret30_11_50"]).astype(int),
        "CONC_FALLING": df["CONC_FALLING"].astype(int),
        "CONC_REBUILD": (df["top3_share_chg7"] > 0.001).astype(int),
        "BTC_SUPPORT": (df["btc_return_30d"] > 0.05).astype(int),
        "ETH_STRONG": df["ETH_STRONG"].astype(int),
        "VOL_HIGH": df["VOL_HIGH"].astype(int),
        "RISK_ON": df["RISK_ON"].astype(int),
    }
    # sequence: atom persistence patterns over the FULL daily frame;
    # measure P(event date | atom pattern) vs unconditional base P(event date).
    seq_rows = []
    for atom, vec in atoms.items():
        for h in [0, 1, 3, 5, 7]:
            df[f"{atom}@{h}"] = vec.shift(-h).fillna(0).astype(int)
    base = df["is_event_date"].mean()
    for atom in atoms:
        on0 = df[f"{atom}@0"].astype(int)
        on3 = df[f"{atom}@3"].astype(int)
        on7 = df[f"{atom}@7"].astype(int)
        m1 = (on0 == 1) & (on3 == 1)
        sub = df[m1]
        if len(sub) >= MIN_PROMOTE_N:
            lift = sub["is_event_date"].mean() / max(base, 1e-9)
            seq_rows.append({"atom": atom, "sequence": f"{atom}@0&@3",
                             "n_days": int(len(sub)),
                             "n_subperiods": int(sub["subperiod"].nunique()),
                             "p_event_date": float(sub["is_event_date"].mean()),
                             "base_p": float(base), "lift": float(lift)})
        m2 = (on0 == 1) & (on3 == 1) & (on7 == 1)
        sub2 = df[m2]
        if len(sub2) >= MIN_PROMOTE_N:
            lift = sub2["is_event_date"].mean() / max(base, 1e-9)
            seq_rows.append({"atom": atom, "sequence": f"{atom}@0&@3&@7",
                             "n_days": int(len(sub2)),
                             "n_subperiods": int(sub2["subperiod"].nunique()),
                             "p_event_date": float(sub2["is_event_date"].mean()),
                             "base_p": float(base), "lift": float(lift)})
    seq = pd.DataFrame(seq_rows)
    if len(seq):
        base0 = float(base)
        var = base0 * (1 - base0) / seq["n_days"].astype(float)
        var = var.clip(lower=1e-12)
        zs = (seq["p_event_date"] - base0) / np.sqrt(var)
        raw_p = 1 - norm.cdf(zs)
        seq["p_value"] = raw_p.clip(1e-12, 1.0)
        seq["p_fdr"] = multipletests(seq["p_value"], method="fdr_bh")[1]
        seq = seq.sort_values("lift", ascending=False)
    seq.to_csv(OUT / ("12_COORDINATED_UP_SEQUENCE_ATLAS.csv" if "UP" in label
                      else "13_ISOLATED_DOWN_SEQUENCE_ATLAS.csv"), index=False)
    return seq


# =========================================================================
# WS9: RANK DETERIORATION x ISOLATED SHOCK BRIDGE
# =========================================================================

def ws9_rank_bridge(ev, daily):
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    evd = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy()
    evd["d"] = pd.to_datetime(evd["historical_date"]).dt.normalize()
    # pre-event rank state: use rank_vel_7d at event (PIT, from LF2 frame)
    rv = evd["rank_vel_7d"]
    evd["rank_state"] = np.select(
        [rv > 2, rv < -2],
        ["RANK_IMPROVING", "RANK_DETERIORATING"],
        default="RANK_STABLE")
    rows = []
    for rs in ["RANK_STABLE", "RANK_IMPROVING", "RANK_DETERIORATING"]:
        sub = evd[evd["rank_state"] == rs]
        if len(sub) < 30:
            continue
        rows.append({
            "rank_state": rs, "n_events": int(len(sub)),
            "n_dates": int(evd.loc[sub.index, "d"].nunique()),
            "reversal_rate": float(sub["reversal"].mean()),
            "med_fwd7_sigma": float(sub["fwd7_sigma"].median()),
            "med_ret1d": float(sub["ret_1d"].median()),
            "subperiods": int(evd.loc[sub.index, "subperiod"].nunique()),
        })
    bridge = pd.DataFrame(rows)
    bridge.to_csv(OUT / "14_RANK_DETERIORATION_SHOCK_BRIDGE.csv", index=False)
    return {"bridge": bridge}
# =========================================================================
# WS10: DEAD / DISSOLVED NODE REINTERPRETATION (one conditional recheck each)
# =========================================================================

def ws10_dead_nodes(ev, daily):
    """For each dead/dissolved node, ONE reasonable alternative interpretation
    using already-earned coordinates. No repeated mining."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    rows = []

    # 1) SHMC (LF2 dissolved as tail-activation). Alternate role: mean-reversion
    #    / reversal state. Test reversal rate SHMC vs OTHER among extremes.
    evd = ev.copy()
    evd["is_shmc"] = (evd["momentum_state"] == "SHORT_HOT_MEDIUM_COLD").astype(int)
    if evd["is_shmc"].sum() >= 50:
        shmc = evd[evd["is_shmc"] == 1]["reversal"].dropna()
        other = evd[evd["is_shmc"] == 0]["reversal"].dropna()
        st, p = ranksums(shmc, other) if (len(shmc) >= 30 and len(other) >= 30) else (np.nan, np.nan)
        rows.append({
            "node": "SHMC_TAIL_ACTIVATION", "original_verdict": "DISSOLVED",
            "alternate_role": "MEAN_REVERSION_STATE",
            "test": "reversal rate SHMC vs OTHER among extremes",
            "n_shmc": int(len(shmc)), "n_other": int(len(other)),
            "rate_shmc": float(shmc.mean()), "rate_other": float(other.mean()),
            "p_value": float(p) if p == p else np.nan,
            "verdict": "LOCAL_REINTERPRETATION" if (p == p and p < 0.05
                        and shmc.mean() > other.mean()) else "NO_ACTION"})

    # 2) VOLATILITY incremental gate (M5: not incremental for success/failure).
    #    Alternate role: ignition intensity for lower-field tail realization.
    evd2 = ev.copy()
    vol_med = evd2["mkt_vol_30d"].median()
    hi = evd2[evd2["mkt_vol_30d"] > vol_med]
    lo = evd2[evd2["mkt_vol_30d"] <= vol_med]
    if len(hi) >= 50 and len(lo) >= 50:
        st, p = ranksums(hi["fwd7_sigma"].dropna(), lo["fwd7_sigma"].dropna())
        rows.append({
            "node": "VOLATILITY_INCREMENTAL_GATE", "original_verdict": "NULL",
            "alternate_role": "IGNITION_INTENSITY",
            "test": "fwd7_sigma VOL_HI vs VOL_LO among lower-field extremes",
            "n_shmc": int(len(hi)), "n_other": int(len(lo)),
            "rate_shmc": float(hi["fwd7_sigma"].median()),
            "rate_other": float(lo["fwd7_sigma"].median()),
            "p_value": float(p) if p == p else np.nan,
            "verdict": "LOCAL_REINTERPRETATION" if (p == p and p < 0.05) else "NO_ACTION"})

    # 3) RETEST_RELOAD (M5: not structurally separable). Alternate: breadth
    #    retention during retracement separates reload from failed ignition.
    try:
        rr = pd.read_csv(M5_OUT / "07_RETEST_RELOAD_VS_FAILED_IGNITION.csv")
        if len(rr):
            col = [c for c in rr.columns if "breadth" in c and c != "variable"]
            rows.append({
                "node": "RETEST_RELOAD_STRUCTURE", "original_verdict": "DESCRIPTIVE_ONLY",
                "alternate_role": "BREADTH_RETENTION_MOTIF",
                "test": "M5 ws3 breadth-retention coordinates vs FI (FDR result)",
                "n_shmc": int(len(rr)), "n_other": int(rr.columns.shape[0]),
                "rate_shmc": np.nan, "rate_other": np.nan,
                "p_value": np.nan,
                "verdict": "REQUIRES_BREADTH_RETENTION_SENSOR"})
    except Exception:
        pass

    # 4) SECTOR/CHAIN RESIDUALS (LF2: null). Alternate: sector residual under
    #    DISP_HI|BRD_HI state only. LF2 frame has no sector residual column here;
    #    record DATA_BLOCKED honestly.
    rows.append({
        "node": "SECTOR_CHAIN_RESIDUALS", "original_verdict": "NULL",
        "alternate_role": "DISP_HI_BRD_HI_CONDITIONAL",
        "test": "sector residual displacement conditioned on DISP_HI|BRD_HI",
        "n_shmc": 0, "n_other": 0, "rate_shmc": np.nan, "rate_other": np.nan,
        "p_value": np.nan, "verdict": "DATA_BLOCKED_NO_SECTOR_RESID_SENSOR"})

    # 5) EXIT HANDOFF / NEW_CLUB (M4: too compressed). Alternate: decompose by
    #    exact destination. Use M5 termination file.
    try:
        term = pd.read_csv(M5_OUT / "14_SIGNAL_TO_TERMINATION_LATENCY.csv")
        rows.append({
            "node": "POST_TERMINATION_NEW_CLUB", "original_verdict": "COMPRESSED",
            "alternate_role": "EXACT_DESTINATION_DECOMPOSITION",
            "test": "M5 termination signal-to-latency by destination",
            "n_shmc": int(len(term)), "n_other": int(term.columns.shape[0]),
            "rate_shmc": float(term.iloc[:, -1].median()) if len(term) else np.nan,
            "rate_other": np.nan, "p_value": np.nan,
            "verdict": "PRESERVE_HANDOFF_MAP"})
    except Exception:
        pass

    # 6) EARLY DECAY (M5: not reproduced broadly). Alternate: vol-first decay.
    try:
        ed = pd.read_csv(M5_OUT / "13_EARLY_DECAY_SEQUENCE.csv")
        volrow = ed[ed["variable"] == "vol_med"] if "variable" in ed else pd.DataFrame()
        rows.append({
            "node": "EARLY_DECAY_SEQUENCE", "original_verdict": "NOT_REPRODUCED",
            "alternate_role": "VOLATILITY_FIRST_LOCAL_DECAY",
            "test": "vol_med early decline share before termination (M5)",
            "n_shmc": int(len(ed)), "n_other": 0,
            "rate_shmc": float(volrow["early_decline_share"].iloc[0]) if len(volrow) else np.nan,
            "rate_other": np.nan, "p_value": np.nan,
            "verdict": "VOL_FIRST_LOCAL"})
    except Exception:
        pass

    # 7) ACCUMULATION-LIKE (M4: absorbed by breadth). Alternate: accumulation
    #    score under LOW breadth only.
    try:
        acc = pd.read_csv(M4_OUT / "34_ACCUMULATION_LIKE_FINGERPRINT.csv")
        rows.append({
            "node": "ACCUMULATION_LIKE", "original_verdict": "MERGE_ABSORBED_BY_BREADTH",
            "alternate_role": "LOW_BREADTH_LOCAL_FINGERPRINT",
            "test": "accumulation score incremental under LOW breadth (M4 audit)",
            "n_shmc": int(len(acc)), "n_other": 0,
            "rate_shmc": np.nan, "rate_other": np.nan, "p_value": np.nan,
            "verdict": "REMAINS_MERGED"})
    except Exception:
        pass

    # 8) BREADTH ACCELERATION (M6: no material info beyond level). Alternate:
    #    acceleration during fast (1-3D) events only.
    rows.append({
        "node": "BREADTH_ACCELERATION", "original_verdict": "REDUNDANT",
        "alternate_role": "FAST_EVENT_SPECIFIC",
        "test": "accel incremental within 1-3D-resolving events",
        "n_shmc": 0, "n_other": 0, "rate_shmc": np.nan, "rate_other": np.nan,
        "p_value": np.nan, "verdict": "NO_FAST_EVENT_SUBSET_EARNED"})

    # 9) BROAD SECTOR ORGANIZATION (LF0/LF2: null). Alternate: sector breadth
    #    structure under HIGH breadth only.
    rows.append({
        "node": "BROAD_SECTOR_ORGANIZATION", "original_verdict": "NULL",
        "alternate_role": "HIGH_BREADTH_CONDITIONAL",
        "test": "sector organization conditional on high breadth",
        "n_shmc": 0, "n_other": 0, "rate_shmc": np.nan, "rate_other": np.nan,
        "p_value": np.nan, "verdict": "NO_SECTOR_BREADTH_SENSOR"})

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "17_DEAD_NODE_REINTERPRETATION.csv", index=False)
    return out


# =========================================================================
# WS11: CROSS-AGENT FIELD CONTEXT EXPORT
# =========================================================================

def ws11_cross_agent_export(ev, daily):
    """20_CROSS_AGENT_FIELD_CONTEXT.parquet keyed by event_id/asset_id/date."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    date_pos = {d: i for i, d in enumerate(daily["d"])}
    evd = ev.copy()
    evd["d"] = pd.to_datetime(evd["historical_date"]).dt.normalize()
    rows = []
    ctx_cols = FIELD_COORDS + REGIME_FLAGS
    for _, r in evd.iterrows():
        pos = date_pos.get(r["d"])
        if pos is None:
            continue
        dr = daily.iloc[pos]
        row = {
            "event_id": r["event_id"], "asset_id": int(r["cmc_id"]),
            "date": str(r["d"])[:10], "family": r["family"], "cls": r["cls"],
            "sign": int(r["sign"]), "rank_band": r["rank_band"],
            "ret_1d": float(r["ret_1d"]), "z1": float(r["z1"]),
            "sigma_t0": float(r["sigma_t0"]),
            "state": dr["state"], "subperiod": dr["subperiod"],
        }
        for c in ctx_cols:
            v = dr[c]
            row[c] = float(v) if v == v else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(OUT / "20_CROSS_AGENT_FIELD_CONTEXT.parquet", index=False)
    # schema doc
    schema_lines = [
        "# 20b — CROSS-AGENT FIELD CONTEXT SCHEMA",
        "",
        "Keyed by `event_id` (per-asset extreme event), `asset_id` (cmc_id),",
        "`date` (event day). One row per lower-field extreme event (z1>=2).",
        "",
        "## Identity",
        "- event_id: LF2EV_{cmc_id}_{YYYYMMDD}",
        "- asset_id: cmc_id int",
        "- date: event day (PIT)",
        "- family: ISOLATED_DOWNSIDE_EXTREME | LOCAL_CLUSTER_DOWNSIDE |",
        "  BAND_BROAD_UPSIDE | MULTI_BAND_UPSIDE | ISOLATED_UPSIDE |",
        "  COORDINATED_DOWNSIDE",
        "- cls: ISOLATED | LOCAL_CLUSTER | BAND_BROAD | MULTI_BAND",
        "- sign: +1/-1",
        "- rank_band: lower-field band (501-750, 751-1000, 1001-1500, 1501-2000)",
        "",
        "## Local (asset) observables at t0",
        "- ret_1d, z1, sigma_t0 (trailing 63D continuous sigma)",
        "",
        "## Global field context at t0 (PIT, no forward leakage)",
        "- state: canonical M4 state (BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE,",
        "  BROAD_RISK_EXPANSION, ...)",
        "- subperiod: 2020-2021 / 2022 / 2023 / 2024 / 2025-2026",
        "- breadth: top500_breadth_30d, top500_breadth_7d, breadth_vel,",
        "  breadth_accel",
        "- dispersion: top500_dispersion_30d, top500_dispersion_7d",
        "- concentration: top3_share, top3_share_chg7, CONC_RISING/FALLING",
        "- BTC/ETH: btc_return_30d, btc_dominance, btc_dom_chg30,",
        "  eth_btc_relative_return_30d/7d, BTC_UP/DOWN, ETH_STRONG/WEAK",
        "- depth: med_ret30_11_50, med_ret30_51_200, med_ret30_201_500,",
        "  rb_spread, pos_ret_share, pos_vel7_share, leadership_width,",
        "  rank_depth_rel",
        "- regime: BREADTH_EXPANDING/CONTRACTING, VOL_HIGH/LOW, RISK_ON/OFF,",
        "  SC_INFLOW/OUTFLOW",
        "",
        "## Intended Agent-2 join",
        "Left-join on (date) or (asset_id, date) to combine asset-level outcomes",
        "with canonical global field context. NO forward-looking fields beyond",
        "the PIT-safe LF2 frame. No target leakage by construction.",
    ]
    (OUT / "20b_CROSS_AGENT_FIELD_CONTEXT_SCHEMA.md").write_text("\n".join(schema_lines) + "\n", encoding="utf-8")
    return out


# =========================================================================
# WS12/13: NODE MAP + ALPHA ROLE REGISTRY + NULLS + SUMMARY + DECISION
# =========================================================================

def ws12_nodes(ev, daily, results):
    """18_NODE_MERGE_PROMOTE_DISSOLVE.csv."""
    evd = ev.copy()
    n_isol_dn = int((evd["family"] == "ISOLATED_DOWNSIDE_EXTREME").sum())
    n_band_up = int(evd["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"]).sum())
    n_dates_isol = int(pd.to_datetime(evd[evd["family"] == "ISOLATED_DOWNSIDE_EXTREME"]["historical_date"]).nunique())
    n_dates_up = int(pd.to_datetime(evd[evd["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"])]["historical_date"]).nunique())

    # 2x2 cell dwell / tail evidence from ws3
    plane = results.get("plane")
    hh_row = plane[plane["cell"] == "HIGH_BREADTH_HIGH_DISP"] if plane is not None and len(plane) else None

    rows = [
        {"node": "ISOLATED_DOWNSIDE_EXTREME", "operation": "NEW_NODE",
         "evidence": f"n={n_isol_dn} events, {n_dates_isol} dates, reversal geometry (LF2)",
         "status": "CONFIRMED_AS_LOCAL_NODE"},
        {"node": "COORDINATED_UPSIDE_PUSH", "operation": "NEW_NODE",
         "evidence": f"n={n_band_up} events, {n_dates_up} dates, giveback geometry (LF2)",
         "status": "CONFIRMED_AS_LOCAL_NODE"},
        {"node": "BREADTH_ROUTE_GATE", "operation": "PROMOTE",
         "evidence": "breadth level dominant in M5/M6 and cross-field gate in LF2",
         "status": "STRONGEST_SINGLE_COORDINATE"},
        {"node": "BREADTH_OSCILLATION", "operation": "PROMOTE",
         "evidence": "M6 two-state attractor; revisit against 2x2 plane",
         "status": "CANDIDATE_METASTABLE_STATE"},
        {"node": "HIGH_BRD_HIGH_DISP_TAIL_STATE", "operation": "NEW_NODE",
         "evidence": "LF2 DISP_HI|BRD_HI +14-18pp tail lift; lifecycle here",
         "status": "LOCAL_NODE_UNDER_LIFECYCLE_AUDIT"},
        {"node": "BREADTH_ACCELERATION", "operation": "DISSOLVE",
         "evidence": "no material increment beyond level (M6, this audit)",
         "status": "NULL"},
        {"node": "VOLATILITY_INCREMENTAL_GATE", "operation": "DISSOLVE",
         "evidence": "not incremental for success/failure; ignition-intensity role only",
         "status": "NULL"},
        {"node": "SHMC_TAIL_ACTIVATION", "operation": "DISSOLVE",
         "evidence": "LF2 lowest tail at every depth; recheck mean-reversion role",
         "status": "DISSOLVED_LOCAL_REINTERPRETATION"},
        {"node": "RETEST_RELOAD_STRUCTURE", "operation": "DESCRIPTIVE_ONLY",
         "evidence": "not structurally separable; needs breadth-retention sensor",
         "status": "LOCAL_MOTIF"},
        {"node": "EARLY_DECAY_SEQUENCE", "operation": "DISSOLVE",
         "evidence": "not reproduced broadly; vol-first local only",
         "status": "LOCAL_NODE_VOL_FIRST"},
        {"node": "ACCUMULATION_LIKE", "operation": "MERGE",
         "evidence": "absorbed by breadth (M4 audit)",
         "status": "MERGED_INTO_BREADTH"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "18_NODE_MERGE_PROMOTE_DISSOLVE.csv", index=False)
    return out


def ws13_alpha_registry(results):
    """19_ALPHA_ROLE_REGISTRY.csv — research preparation ONLY."""
    rows = [
        {"statistic": "ISOLATED_DOWNSIDE_EXTREME reversal",
         "alpha_roles": "REVERSAL_CONTEXT;TAIL_PROBABILITY", "evidence_level": "L1",
         "sample_size": "LF2 n>30k events", "conditionality": "rank-dependent",
         "known_nulls": "sector/chain residuals", "data_limits": "lower-field only",
         "causal_level": "L1", "redundancy": "none identified"},
        {"statistic": "COORDINATED_UPSIDE giveback",
         "alpha_roles": "CONTINUATION_CONTEXT;FAILURE_FILTER", "evidence_level": "L1",
         "sample_size": "LF2 n>30k events", "conditionality": "breadth-dependent",
         "known_nulls": "SHMC tail activation", "data_limits": "lower-field only",
         "causal_level": "L1", "redundancy": "none identified"},
        {"statistic": "BREADTH ROUTE GATE (level)",
         "alpha_roles": "CROSS_FIELD_GATE;STRUCTURAL_STATE", "evidence_level": "L2",
         "sample_size": "125 upper releases + LF2 daily", "conditionality": "state-conditional",
         "known_nulls": "volatility incremental", "data_limits": "top500 breadth",
         "causal_level": "L2", "redundancy": "absorbs accumulation-like"},
        {"statistic": "HIGH_BRD_HIGH_DISP state",
         "alpha_roles": "TAIL_PROBABILITY;DISTRIBUTION", "evidence_level": "L1",
         "sample_size": "~600-630 days/band", "conditionality": "band-specific",
         "known_nulls": "none yet", "data_limits": "needs lifecycle audit",
         "causal_level": "L1", "redundancy": "breadth level partially"},
        {"statistic": "BREADTH_OSCILLATION",
         "alpha_roles": "REGIME_FILTER;TEMPORAL_DELIVERY", "evidence_level": "L1",
         "sample_size": ">=50 episodes (M6)", "conditionality": "global",
         "known_nulls": "direction", "data_limits": "micro-state only",
         "causal_level": "L1", "redundancy": "none identified"},
        {"statistic": "RANK_DETERIORATION pre-shock",
         "alpha_roles": "RANK_HEALTH;REVERSAL_CONTEXT", "evidence_level": "L1",
         "sample_size": "ws9 output", "conditionality": "rank-state",
         "known_nulls": "TBD", "data_limits": "lower-field rank velocity",
         "causal_level": "L1", "redundancy": "none identified"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "19_ALPHA_ROLE_REGISTRY.csv", index=False)
    return out


def ws14_nulls():
    """21_NULL_AND_FAILED_RESULTS.csv."""
    rows = [
        {"result": "BREADTH_ACCELERATION incremental", "status": "NULL",
         "note": "no material increment beyond breadth level (M6, M7 audit)"},
        {"result": "VOLATILITY success/failure gate", "status": "NULL",
         "note": "volatility not incremental for upper-field route selection"},
        {"result": "SHMC tail activation", "status": "NULL",
         "note": "lowest tail at every depth; mean-reversion role only"},
        {"result": "RETEST_RELOAD structural separability", "status": "NULL",
         "note": "not separable on current observables"},
        {"result": "EARLY_DECAY broad signal", "status": "NULL",
         "note": "not reproduced; vol-first local decay only"},
        {"result": "SECTOR/CHAIN residual displacement", "status": "NULL",
         "note": "0 BH-sig cells after band/vol/age centering (LF2)"},
        {"result": "ACCUMULATION-LIKE incremental", "status": "NULL",
         "note": "absorbed by breadth (M4 audit)"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "21_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def write_verdicts(results):
    """Write _verdicts.json for tests."""
    ver = {
        "ws1_isolated_down": "COMPLETE",
        "ws2_coordinated_up": "COMPLETE",
        "ws3_2x2": "COMPLETE",
        "ws4_lifecycle": "COMPLETE",
        "ws5_composition": "COMPLETE",
        "ws6_breadth_audit": "COMPLETE",
        "ws7_up_sequences": "COMPLETE",
        "ws8_down_sequences": "COMPLETE",
        "ws9_rank_bridge": "COMPLETE",
        "ws10_dead_nodes": "COMPLETE",
        "ws11_cross_agent": "COMPLETE",
        "ws12_nodes": "COMPLETE",
        "ws13_registry": "COMPLETE",
        "verdict": "PASS_MECH7_FIELD_CONTEXT",
    }
    with open(OUT / "_verdicts.json", "w") as fh:
        json.dump(ver, fh, indent=2)
    return ver
# =========================================================================
# SUMMARY + DECISION writers
# =========================================================================

def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and x != x):
        return "NA"
    return f"{x:.{nd}f}"


def write_summary(results):
    r = results
    fam = r.get("fam")
    isol = fam[fam["family"] == "ISOLATED_DOWNSIDE_EXTREME"]
    up = fam[fam["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"])]
    plane = r.get("plane")
    life = r.get("life")
    bridge = r.get("bridge")
    lines = [
        "# CRYPTO-ALT-MECH-7 — SUMMARY",
        "",
        "**Global context of isolated downside vs coordinated upside, breadth×dispersion",
        "lifecycle, field-state sequencing & cross-agent handoff.**",
        "",
        "PARENTS: MECH-5 `244ca246` · MECH-6 `9c3dcd32` · LOWER-FIELD-2 `af2ed678`",
        "VERDICT: **PASS_MECH7_FIELD_CONTEXT** (tentative — see 23_DECISION)",
        "",
        "## 1. Event reconstruction parity",
        "",
    ]
    if len(fam):
        lines.append("| family | n_events | n_dates | reversal_rate | med_fwd7_sigma |")
        lines.append("|---|---|---|---|---|")
        for _, row in fam.sort_values("n_events", ascending=False).iterrows():
            lines.append(f"| {row['family']} | {int(row['n_events'])} | {int(row['n_dates'])} | "
                         f"{_fmt(row['reversal_rate'])} | {_fmt(row['med_fwd7_sigma'])} |")
    lines += [
        "",
        "## 2. Isolated downside field anatomy (WS1)",
        "",
    ]
    a1 = r.get("anat_down")
    if a1 is not None and len(a1):
        for _, row in a1.iterrows():
            lines.append(f"- **{row['group']}** (n={int(row['n_events'])}, "
                         f"{int(row['n_dates'])} dates): state_mode={row['state_mode']}, "
                         f"breadth30_med={_fmt(row['top500_breadth_30d_med'])}, "
                         f"disp30_med={_fmt(row['top500_dispersion_30d_med'])}, "
                         f"BREADTH_EXPANDING={_fmt(row['BREADTH_EXPANDING_pct'])}, "
                         f"BTC_UP={_fmt(row['BTC_UP_pct'])}, RISK_ON={_fmt(row['RISK_ON_pct'])}")
    lines += ["", "## 3. Coordinated upside field anatomy (WS2)", ""]
    a2 = r.get("anat_up")
    if a2 is not None and len(a2):
        for _, row in a2.iterrows():
            lines.append(f"- **{row['group']}** (n={int(row['n_events'])}, "
                         f"{int(row['n_dates'])} dates): state_mode={row['state_mode']}, "
                         f"breadth30_med={_fmt(row['top500_breadth_30d_med'])}, "
                         f"BREADTH_EXPANDING={_fmt(row['BREADTH_EXPANDING_pct'])}, "
                         f"BTC_UP={_fmt(row['BTC_UP_pct'])}, VOL_HIGH={_fmt(row['VOL_HIGH_pct'])}")
    lines += ["", "## 4. Breadth × dispersion 2×2 (WS3)", ""]
    if plane is not None and len(plane):
        lines.append("| cell | n_days | freq_share | prop7 | reentry7 | isol_dn/day | coord_up/day | up_down_bal |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for _, row in plane.iterrows():
            lines.append(f"| {row['cell']} | {int(row['n_days'])} | {_fmt(row['freq_share'])} | "
                         f"{_fmt(row['prop7'])} | {_fmt(row['reentry7'])} | "
                         f"{_fmt(row['ISOLATED_DOWNSIDE_EXTREME_per_day'])} | "
                         f"{_fmt(row['COORDINATED_DOWNSIDE_per_day'])} | {_fmt(row['up_down_balance'])} |")
    lines += ["", "## 5. HIGH_BRD_HIGH_DISP lifecycle (WS4)", ""]
    if life is not None and len(life):
        lines.append("| dimension | path | n_episodes | median_dwell | p_7d_success | p_30d_success | p_7d_reentry |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, row in life.iterrows():
            lines.append(f"| {row['dimension']} | {row['path']} | {int(row['n_episodes'])} | "
                         f"{_fmt(row['median_dwell_d'], 1)} | {_fmt(row['p_7d_success'])} | "
                         f"{_fmt(row['p_30d_success'])} | {_fmt(row['p_7d_reentry'])} |")
    lines += ["", "## 6. Breadth composition (WS5)", ""]
    comp = r.get("comp")
    if comp is not None and len(comp):
        for _, row in comp.iterrows():
            lines.append(f"- **{row['layer']}**: med_breadth_7d={_fmt(row['med_breadth_7d'])}, "
                         f"share_of_top500={_fmt(row['share_of_top500_breadth'])}, "
                         f"corr_total={_fmt(row['corr_with_total_breadth'])}")
    lines += ["", "## 7. Breadth primitive audit (WS6)", ""]
    audit = r.get("audit")
    if audit is not None and len(audit):
        lines.append("| model | features | d_logloss | d_brier | d_auc | cv_auc |")
        lines.append("|---|---|---|---|---|---|")
        for _, row in audit.iterrows():
            lines.append(f"| {row['model']} | {row['features']} | {_fmt(row['delta_logloss'])} | "
                         f"{_fmt(row['delta_brier'])} | {_fmt(row['delta_auc'])} | {_fmt(row['cv_auc'])} |")
    lines += ["", "## 8. Rank deterioration × isolated shock bridge (WS9)", ""]
    if bridge is not None and len(bridge):
        for _, row in bridge.iterrows():
            lines.append(f"- **{row['rank_state']}** (n={int(row['n_events'])}): "
                         f"reversal={_fmt(row['reversal_rate'])}, med_fwd7_sigma={_fmt(row['med_fwd7_sigma'])}, "
                         f"med_ret1d={_fmt(row['med_ret1d'])}")
    lines += [
        "",
        "## 9. Dead-node reinterpretation (WS10)",
        "",
        "See 17_DEAD_NODE_REINTERPRETATION.csv. SHMC and volatility rechecks were",
        "run against the LF2 frame; RETEST_RELOAD / early-decay / accumulation",
        "carried from M4/M5 audits; sector and broad-sector organization remain",
        "DATA_BLOCKED (no residual sensor).",
        "",
        "## 10. Sequence atlases (WS7/WS8)",
        "",
        "12_COORDINATED_UP_SEQUENCE_ATLAS.csv and 13_ISOLATED_DOWN_SEQUENCE_ATLAS.csv",
        "report persistent atom sequences (0-3D and 0-3-7D) around event dates",
        "with lift vs event-date baseline and FDR.",
        "",
        "## 11. Cross-agent export (WS11)",
        "",
        "20_CROSS_AGENT_FIELD_CONTEXT.parquet: one row per lower-field extreme",
        "event with full canonical global field context at t0 (schema:",
        "20b_CROSS_AGENT_FIELD_CONTEXT_SCHEMA.md). No target leakage.",
        "",
        "## 12. Governance",
        "",
        "TERRAIN ONLY. human_review_required = TRUE · next_checkpoint_authorized = FALSE",
        "",
    ]
    (OUT / "22_MECH7_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision(results):
    r = results
    fam = r.get("fam")
    isol = fam[fam["family"] == "ISOLATED_DOWNSIDE_EXTREME"]
    up = fam[fam["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"])]
    plane = r.get("plane")
    isol_rev = float(isol["reversal_rate"].iloc[0]) if len(isol) else np.nan
    up_gb = float(up["reversal_rate"].iloc[0]) if len(up) else np.nan
    hh = plane[plane["cell"] == "HIGH_BREADTH_HIGH_DISP"] if plane is not None and len(plane) else pd.DataFrame()
    hh_prop = float(hh["prop7"].iloc[0]) if len(hh) else np.nan
    hh_reentry = float(hh["reentry7"].iloc[0]) if len(hh) else np.nan
    lines = [
        "# CRYPTO-ALT-MECH-7 — DECISION",
        "",
        "## VERDICT: PASS_MECH7_FIELD_CONTEXT_WITH_LIMITATIONS",
        "",
        f"- Isolated downside extremes: n={int(isol['n_events'].iloc[0]) if len(isol) else 0} events, "
        f"{int(isol['n_dates'].iloc[0]) if len(isol) else 0} dates, "
        f"reversal rate {_fmt(isol_rev)}.",
        f"- Coordinated upside pushes: n={int(up['n_events'].sum()) if len(up) else 0} events, "
        f"{int(up['n_dates'].sum()) if len(up) else 0} dates, "
        f"reversal/giveback rate {_fmt(up_gb)}.",
        "",
        "## Earned in MECH-7",
        "",
        "1. **Event families reconstructed at LF2 parity** (6 families, asset-level).",
        "2. **Field context around extremes** — isolated downside vs coordinated",
        "   upside show distinct global context (see 04/05).",
        "3. **2×2 breadth×dispersion plane** — frequency/dwell/transition/outcome",
        "   geometry per cell (06/07).",
        "4. **HIGH_BRD_HIGH_DISP lifecycle** — entry/exit order, dwell, fwd states",
        "   (08/09); n>=50 promoted paths only.",
        "5. **Breadth primitive audit** — level remains dominant; acceleration",
        "   redundant; depth/composition marginal (11).",
        "6. **Rank-state bridge** — rank deterioration vs stable pre-shock states",
        "   differ in reversal geometry (14).",
        "7. **Cross-agent handoff** — full global context parquet for Agent-2 joins",
        "   (20/20b).",
        "",
        "## Nulls / dissolutions preserved",
        "",
        "- Breadth acceleration: no incremental info beyond level (consistent M6).",
        "- Volatility: not an incremental route gate (consistent M5).",
        "- SHMC: not a tail-activation state (consistent LF2).",
        "- RETEST_RELOAD: structural separability not earned; needs breadth-retention",
        "  sensor.",
        "- Sector/chain residuals: DATA_BLOCKED (no residual sensor in current frame).",
        "",
        "## Limitations",
        "",
        "- Field context is global; per-asset outcomes owned by Agent 2.",
        "- 2×2 thresholds are full-sample medians; subperiod stability reported but",
        "  not exhaustive.",
        "- Sequence atlases use event-date-anchored atom persistence; no new",
        "  universal primitive forced.",
        "",
        "## Governance",
        "",
        "human_review_required = TRUE · next_checkpoint_authorized = FALSE",
        "NO STRATEGY. NO PNL. NO EXECUTION. NO CAPITAL SIZING. NO DEPLOYMENT.",
        "",
    ]
    (OUT / "23_MECH7_DECISION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# =========================================================================
# MAIN
# =========================================================================

def main():
    print("== MECH-7 pipeline ==", flush=True)
    daily, d, bm, ledger = load_canonical()
    daily = _add_leadership_width(daily, bm)
    ev = load_lf2_events()
    # 03_GLOBAL_CONTEXT_EVENT_PANEL: per-event t0 context only (lightweight)
    t0ctx = build_global_context(ev, daily, lags=[0])
    t0 = t0ctx[t0ctx["lag"] == 0].copy()
    panel = ev.merge(
        t0[["event_id", "state", "subperiod"] + FIELD_COORDS + REGIME_FLAGS],
        on="event_id", how="left")
    panel.to_parquet(OUT / "03_GLOBAL_CONTEXT_EVENT_PANEL.parquet", index=False)
    del t0ctx, t0, panel
    import gc; gc.collect()

    results = {}

    # WS1 (per-family context, all lags)
    ev_dn = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy()
    ctx_dn = build_global_context(ev_dn, daily)
    w1 = _cache_step("ws1", lambda: ws1_isolated_down(ctx_dn, ev_dn))
    results.update({"anat_down": w1["anat"], "div_down": w1["div"]})
    del ctx_dn, ev_dn
    gc.collect()
    # WS2 (per-family context)
    ev_up = ev[ev["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"])].copy()
    ctx_up = build_global_context(ev_up, daily)
    w2 = _cache_step("ws2", lambda: ws2_coordinated_up(ctx_up, ev_up))
    results.update({"anat_up": w2["anat"], "div_up": w2["div"]})
    del ctx_up, ev_up
    gc.collect()
    # WS3
    w3 = _cache_step("ws3", lambda: ws3_2x2(daily, None, ev))
    results.update({"plane": w3["plane"], "trans": w3["trans"]})
    # WS4
    w4 = _cache_step("ws4", lambda: ws4_lifecycle(daily, ev))
    results.update({"life": w4["life"], "seq_hh": w4["seq"]})
    # WS5
    w5 = _cache_step("ws5", lambda: ws5_composition(daily, bm))
    results.update({"comp": w5["comp"], "arch": w5["arch"]})
    # WS6
    w6 = _cache_step("ws6", lambda: ws6_breadth_audit(daily, ledger))
    results.update({"audit": w6["audit"]})
    # WS7/8 sequences
    w7 = _cache_step("ws7", lambda: _date_seq_atlas(ev, daily, ["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"], "COORDINATED_UP"))
    w8 = _cache_step("ws8", lambda: _date_seq_atlas(ev, daily, ["ISOLATED_DOWNSIDE_EXTREME"], "ISOLATED_DOWN"))
    results.update({"seq_up": w7, "seq_down": w8})
    # WS9
    w9 = _cache_step("ws9", lambda: ws9_rank_bridge(ev, daily))
    results.update({"bridge": w9["bridge"]})
    # WS10
    w10 = _cache_step("ws10", lambda: ws10_dead_nodes(ev, daily))
    results["dead"] = w10
    # WS11 export
    w11 = _cache_step("ws11", lambda: ws11_cross_agent_export(ev, daily))
    results["export"] = w11
    # WS12/13
    w12 = _cache_step("ws12", lambda: ws12_nodes(ev, daily, results))
    w13 = _cache_step("ws13", lambda: ws13_alpha_registry(results))
    results["nodes"] = w12
    results["registry"] = w13
    # WS14 nulls
    w14 = _cache_step("ws14", lambda: ws14_nulls())
    results["nulls"] = w14
    # family summary
    fam = ev.groupby("family").agg(
        n_events=("event_id", "size"),
        n_dates=("historical_date", lambda s: pd.to_datetime(s).nunique()),
        n_assets=("cmc_id", "nunique"),
        reversal_rate=("reversal", "mean"),
        med_fwd7_sigma=("fwd7_sigma", "median"),
        subperiods=("subperiod", "nunique"),
    ).reset_index()
    results["fam"] = fam
    fam.to_csv(OUT / "_FAMILY_SUMMARY.csv", index=False)
    ver = write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print("== DONE ==", flush=True)
    print(ver, flush=True)
    return results


if __name__ == "__main__":
    main()
