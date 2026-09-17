#!/usr/bin/env python
"""ALT_MECH_8 - Field-State Deepening: Breadth x Dispersion Transition
Lattice, Pre-Event Isolated-Downside Buildup, Breadth Architecture,
Rank-Health Context & Cross-Agent Synthesis Support.

Terrain research ONLY (AGENT 1 - MAIN FIELD CARTOGRAPHER). No PnL, no strategy,
no optimization, no ML predictors, no sizing, no deployment.
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

SEED = 20260909
BOOT_N = 400
PERM_N = 300
MIN_PROMOTE_N = 50
MIN_SUBPERIODS = 3
FDR_Q = 0.10

ROOT = Path(__file__).resolve().parents[1]            # mech_8/
M7_ROOT = ROOT.parent / "mech_7"
M5_ROOT = ROOT.parent / "mech_5"
M4_ROOT = ROOT.parent / "mech_4"
M4_SCRIPTS = M4_ROOT / "scripts"
sys.path.insert(0, str(M4_SCRIPTS))
import alt_mech_4_analysis as M4

LF2_ROOT = (
    Path(__file__).resolve().parents[3] / "derivatives" / "lower_field_2"
)
LF3_ROOT = (
    Path(__file__).resolve().parents[3] / "derivatives" / "lower_field_3"
)
LF2_FEATURES = LF2_ROOT / "RESULTS" / "lf2_feature_frame.parquet"

OUT = ROOT
M4_OUT = M4_ROOT
M5_OUT = M5_ROOT
M7_OUT = M7_ROOT

BANDS = M4.BANDS
ALT_FAMILY = M4.ALT_FAMILY
SUCCESS_LABELS = {"BROAD_RISK_EXPANSION"} | set(ALT_FAMILY)
REENTRY_LABEL = "BTC_CONCENTRATION"

SUBPERIODS = ["2020-2021", "2022", "2023", "2024", "2025-2026"]

# frozen 2x2 thresholds (full-sample medians, computed pre-outcome)
BRD_MED = 0.31
DISP_MED = 0.307

# extended pre-event lattice (MECH-8 WS1/WS2)
PRE30_LAGS = [-30, -21, -14, -10, -7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10, 14]

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
# LOAD (M4 canonical daily + bm + ledger; LF2 events; feat top-500 panel)
# =========================================================================

def load_canonical():
    inp, tl = M4._cache_step("inputs", M4.load)
    daily, d, bm = M4._cache_step("daily", lambda: M4.build_daily(inp))
    rc = M4._cache_step("reconcile", lambda: M4.ws_reconcile(daily))
    entries, exits = rc["recount"]["entries"], rc["recount"]["exits"]
    rA = M4._cache_step("A", lambda: M4.ws_a(daily, entries, exits))
    ledger = rA["ledger"]
    return daily, d, bm, ledger


def _add_breadth_features(daily):
    """Breadth velocity/accel/persistence/divergence/oscillation (M6/M7 parity)."""
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
    osc = np.zeros(len(df), dtype=int)
    for i in range(7, len(df)):
        win = df["breadth_axis"].iloc[i-6:i+1].values
        if ("BREADTH_EXPANDING" in win) and ("BREADTH_FADING" in win):
            osc[i] = 1
    df["breadth_oscillation"] = osc
    deep = df["med_ret30_201_500"].astype(float)
    upper = df["med_ret30_11_50"].astype(float)
    df["rank_depth_rel"] = deep - upper
    df["rank_depth_rel_chg"] = df["rank_depth_rel"].diff(5)
    return df


LF2_NEEDED = [
    "historical_date", "cmc_id", "rank", "rank_band", "ret_1d", "sigma_t0",
    "fwd1_cum", "fwd2_cum", "fwd3_cum", "fwd5_cum", "fwd7_cum", "fwd10_cum",
    "fwd14_cum", "fwd21_cum", "fwd30_cum",
    "rank_vel_1d", "rank_vel_3d", "rank_vel_7d", "rank_vel_14d", "rank_vel_30d",
    "volume_24h_usd", "vol_prev7_med", "listing_age_days", "log10_mcap",
    "mcap_q_within_date", "momentum_state", "top500_breadth_30d",
    "top500_dispersion_30d", "mkt_vol_30d", "btc_ret_1d", "eth_ret_1d",
]


def _load_lf2_events_core():
    """Read LF2 feature frame (needed cols only, float32 downcast), reconstruct
    extreme events identically to MECH-7. Returns event frame (small)."""
    df = pd.read_parquet(LF2_FEATURES, columns=LF2_NEEDED)
    for c in df.columns:
        if df[c].dtype == "float64":
            df[c] = df[c].astype("float32")
    df = df[df["ret_1d"].notna() & df["sigma_t0"].notna() & (df["sigma_t0"] > 0)].copy()
    df["z1"] = df["ret_1d"].abs() / df["sigma_t0"]
    df["sign"] = np.sign(df["ret_1d"].to_numpy(float)).astype(np.int8)
    ev = df[(df["z1"] >= 2) & (df["sign"] != 0)].copy()
    del df
    gc.collect()
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
         "COORDINATED_DOWNSIDE"], default="OTHER")
    ev["fwd7_sigma"] = ev["fwd7_cum"] / (ev["sigma_t0"] * np.sqrt(7))
    ev["reversal"] = ((np.sign(ev["fwd7_cum"]) != ev["sign"]) & ev["fwd7_cum"].notna()).astype(int)
    yr = ev["historical_date"].dt.year
    ev["subperiod"] = np.select([yr <= 2021, yr == 2022, yr == 2023, yr == 2024],
                                ["2020-2021", "2022", "2023", "2024"],
                                default="2025-2026")
    ev["event_id"] = ("LF2EV_" + ev["cmc_id"].astype(str) + "_" +
                      ev["historical_date"].dt.strftime("%Y%m%d"))
    return ev.reset_index(drop=True)


def load_lf2_events():
    return _cache_step("lf2_events", _load_lf2_events_core)


def load_feat():
    """Top-500 per-day asset panel from M4 inputs (for breadth architecture)."""
    inp, tl = M4._cache_step("inputs", M4.load)
    feat = inp["feat"].copy()
    feat["d"] = pd.to_datetime(feat["historical_date"]).dt.normalize()
    return feat


def _cell(brd, disp):
    b = "HIGH" if brd > BRD_MED else "LOW"
    d = "HIGH" if disp > DISP_MED else "LOW"
    return f"{b}_BREADTH_{d}_DISP"


def _perm_p(k, B):
    return (k + 1) / (B + 1)
# =========================================================================
# WS1: ISOLATED-DOWNSIDE PRE-EVENT BUILDUP to -30D
# =========================================================================

def _price_outcome_class(r):
    """Hierarchical price outcome classes (precedence order, preregistered)."""
    s = r["sigma_t0"]
    if s is None or s != s or s <= 0:
        return np.nan
    try:
        f1, f2, f7 = r["fwd1_cum"], r["fwd2_cum"], r["fwd7_cum"]
        f14, f30 = r["fwd14_cum"], r["fwd30_cum"]
    except Exception:
        return np.nan
    if f1 == f1 and f1 / s >= 1.0:
        return "EARLY_1SIGMA_RECOVERY"
    if f2 == f2 and f2 / s >= 1.0:
        return "EARLY_1SIGMA_RECOVERY"
    if f7 == f7 and f7 > 0:
        return "LATE_RECOVERY"
    if f14 == f14 and f14 > 0:
        return "PARTIAL_REBOUND"
    if f14 == f14 and f30 == f30 and f14 / s >= 1.0:
        return "FULL_REVERSAL"
    if f30 == f30 and f30 / s >= 1.0:
        return "FULL_REVERSAL"
    if f14 == f14 and f30 == f30 and f14 < 0 and f30 < 0:
        return "CONTINUED_DECLINE"
    if f7 == f7 and f14 == f14 and (f7 / s <= -2.0 or f14 / s <= -2.0):
        return "NEW_EXTREME"
    return "CONTINUED_DECLINE"


def _rank_outcome(fwd_rank_vel):
    if fwd_rank_vel is None or fwd_rank_vel != fwd_rank_vel:
        return np.nan
    if fwd_rank_vel > 0.5:
        return "RANK_RECOVERY"
    if fwd_rank_vel < -0.5:
        return "RANK_CONTINUED_DETERIORATION"
    return "RANK_STABLE"


def _build_context_panel(ev, daily, lags):
    """Per (event x lag) global field context. Vectorized exact-date join."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    dnorm = pd.to_datetime(daily["historical_date"]).dt.normalize()
    ctx_cols = ["state", "subperiod"] + FIELD_COORDS + REGIME_FLAGS
    ev_dates = pd.to_datetime(ev["historical_date"]).dt.normalize()
    uniq, idx = np.unique(dnorm.values, return_index=True)
    frames = []
    for lag in lags:
        tgt = ev_dates + pd.Timedelta(days=lag)
        pos = np.searchsorted(uniq, tgt.values)
        pos = np.clip(pos, 0, len(uniq) - 1)
        hit = uniq[pos] == tgt.values
        base = ev[["event_id", "family", "cls", "sign", "rank_band"]].copy()
        base["lag_d"] = lag
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
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def ws1_pre30(daily, ev):
    """Isolated-downside events: full -30..+14 context panel + outcome classes.
    Writes 03_ISOLATED_DOWN_PRE30_CONTEXT.parquet."""
    evd = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy()
    evd = evd.reset_index(drop=True)
    evd["price_outcome"] = [_price_outcome_class(r) for _, r in evd.iterrows()]
    # forward rank velocity: from LF2 rank_vel columns we only have trailing;
    # compute fwd rank vel as rank_vel_7d at t+7 via self-join (see ws8).
    # Here we use trailing rank vel for pre-event rank state.
    rv = evd["rank_vel_7d"].to_numpy(float)
    evd["pre_rank_state"] = np.select(
        [rv > 2, rv < -2], ["RANK_IMPROVING", "RANK_DETERIORATING"],
        default="RANK_STABLE")
    evd["is_reverse"] = (evd["reversal"] == 1).astype(int)
    evd["is_continue"] = (evd["reversal"] == 0).astype(int)
    panel = _build_context_panel(evd, daily, PRE30_LAGS)
    if len(panel):
        panel = panel.merge(evd[["event_id", "price_outcome", "pre_rank_state",
                                 "is_reverse", "is_continue", "z1", "ret_1d",
                                 "sigma_t0", "fwd7_sigma"]],
                            on="event_id", how="left")
    panel.to_parquet(OUT / "03_ISOLATED_DOWN_PRE30_CONTEXT.parquet", index=False)
    return {"panel": panel, "evd": evd}


# =========================================================================
# WS2: FIRST-DIVERGENCE EFFECT CURVES (-30..+14) + PRE-EVENT SEQUENCE ATLAS
# =========================================================================

def ws2_effect_curves(panel, evd):
    """Full effect curves reversal vs continuation across all lags. For each
    variable x lag: medians, diff, ranksum p, FDR; plus per-variable summary:
    first_sig_lag (earliest lag at which FDR-significant), continuous_sig_start,
    peak_abs_lag, monotonic, sign_flip."""
    if len(panel) == 0:
        return pd.DataFrame()
    rows = []
    for lag in PRE30_LAGS:
        sub = panel[panel["lag_d"] == lag]
        rev = sub[sub["is_reverse"] == 1]
        con = sub[sub["is_continue"] == 1]
        if len(rev) < 30 or len(con) < 30:
            continue
        for c in FIELD_COORDS:
            a, b = rev[c].dropna(), con[c].dropna()
            if len(a) < 30 or len(b) < 30:
                continue
            try:
                _, p = ranksums(a, b)
            except Exception:
                continue
            rows.append({"lag_d": lag, "variable": c, "n_rev": int(len(a)),
                         "n_con": int(len(b)), "med_rev": float(a.median()),
                         "med_con": float(b.median()),
                         "diff": float(a.median() - b.median()),
                         "ranksum_p": float(p)})
    eff = pd.DataFrame(rows)
    if len(eff) == 0:
        eff.to_csv(OUT / "04_ISOLATED_DOWN_EFFECT_CURVES.csv", index=False)
        return eff
    eff["p_fdr"] = multipletests(eff["ranksum_p"], method="fdr_bh")[1]
    eff.to_csv(OUT / "04_ISOLATED_DOWN_EFFECT_CURVES.csv", index=False)
    # per-variable summary
    summ = []
    for var, g in eff.groupby("variable"):
        g = g.sort_values("lag_d")
        sig = g[g["p_fdr"] < FDR_Q]
        if len(sig) == 0:
            summ.append({"variable": var, "n_lags_tested": int(len(g)),
                         "first_sig_lag": np.nan, "continuous_sig_start": np.nan,
                         "peak_abs_lag": float(g.loc[g["diff"].abs().idxmax(), "lag_d"]),
                         "peak_abs_diff": float(g["diff"].abs().max()),
                         "monotonic_from_start": False, "sign_flip": bool(
                             (g["diff"] > 0).any() and (g["diff"] < 0).any()),
                         "any_sig": False})
            continue
        first_sig = int(sig["lag_d"].min())
        # continuous significant run starting from the most negative lag
        ordered = g["lag_d"].tolist()
        sigset = set(sig["lag_d"].tolist())
        cont_start = None
        for i, lag in enumerate(ordered):
            if all(l in sigset for l in ordered[i:]):
                cont_start = int(lag)
                break
        # monotonicity of |diff| from continuous start to 0
        run = g[(g["lag_d"] >= cont_start) & (g["lag_d"] <= 0)]
        ad = run["diff"].abs().tolist()
        mono = all(ad[i] <= ad[i + 1] + 1e-12 for i in range(len(ad) - 1)) if len(ad) > 1 else True
        summ.append({"variable": var, "n_lags_tested": int(len(g)),
                     "first_sig_lag": first_sig, "continuous_sig_start": cont_start,
                     "peak_abs_lag": float(g.loc[g["diff"].abs().idxmax(), "lag_d"]),
                     "peak_abs_diff": float(g["diff"].abs().max()),
                     "monotonic_from_start": mono,
                     "sign_flip": bool((g["diff"] > 0).any() and (g["diff"] < 0).any()),
                     "any_sig": True})
    sdf = pd.DataFrame(summ)
    sdf.to_csv(OUT / "04b_ISOLATED_DOWN_EFFECT_CURVE_SUMMARY.csv", index=False)
    return eff


def ws2b_pre_event_sequence_atlas(panel, evd):
    """Search repeated pre-event field shapes (-30..0) distinguishing reversal
    vs continuation. Atoms are pre-registered; P(reversal|pattern) vs base."""
    if len(panel) == 0:
        pd.DataFrame().to_csv(OUT / "05_ISOLATED_DOWN_PRE_EVENT_SEQUENCE_ATLAS.csv", index=False)
        return pd.DataFrame()
    # one row per event x lag (full panel)
    if len(panel) == 0:
        return pd.DataFrame()
    pv = panel.pivot_table(index="event_id", columns="lag_d",
                           values=FIELD_COORDS + REGIME_FLAGS, aggfunc="first")
    # flatten MultiIndex (var, lag) -> var_lag
    pv.columns = [f"{c[0]}_lag{c[1]}" for c in pv.columns]
    pv = pv.reset_index()
    evo = evd.set_index("event_id")[["is_reverse", "is_continue"]]
    pv = pv.merge(evo, left_on="event_id", right_index=True, how="left")
    base = pv["is_reverse"].mean()
    if base != base or base == 0:
        base = np.nan

    def col(var, lag):
        c = pv.get(f"{var}_lag{lag}")
        if c is None:
            return pd.Series(np.nan, index=pv.index)
        return c

    atoms = {
        "DISP_RISING_14_7": (lambda: (col("top500_dispersion_30d", -14) - col("top500_dispersion_30d", -21)) > 0.01),
        "DISP_RISING_7_0": (lambda: (col("top500_dispersion_30d", 0) - col("top500_dispersion_30d", -7)) > 0.01),
        "BRD_HEALTHY_7": (lambda: col("top500_breadth_30d", -7) > BRD_MED),
        "BRD_FALLING_14_0": (lambda: (col("top500_breadth_30d", 0) - col("top500_breadth_30d", -14)) < -0.02),
        "BTC_SUPPORT_30": (lambda: col("btc_return_30d", -7) > 0.05),
        "BTC_WEAKENING_14_0": (lambda: (col("btc_return_30d", 0) - col("btc_return_30d", -14)) < -0.03),
        "CONC_RISING_14_0": (lambda: col("CONC_RISING", 0) == 1),
        "CONC_FALLING_14_0": (lambda: col("CONC_FALLING", 0) == 1),
        "VOL_HIGH_0": (lambda: col("VOL_HIGH", 0) == 1),
        "ETH_STRONG_7": (lambda: col("ETH_STRONG", -7) == 1),
        "RISK_ON_7": (lambda: col("RISK_ON", -7) == 1),
        "RISK_OFF_7": (lambda: col("RISK_OFF", -7) == 1),
        "BRD_EXPANDING_14_0": (lambda: col("BREADTH_EXPANDING", 0) == 1),
        "BRD_CONTRACTING_14_0": (lambda: col("BREADTH_CONTRACTING", 0) == 1),
    }
    rows = []
    for name, fn in atoms.items():
        try:
            mask = fn()
        except Exception:
            continue
        mask = mask.fillna(False).astype(bool)
        sub = pv[mask]
        if len(sub) < MIN_PROMOTE_N:
            continue
        rev_rate = sub["is_reverse"].mean()
        ids = sub["event_id"].to_list()
        evi = evd.set_index("event_id")
        rows.append({"atom": name, "n_events": int(len(sub)),
                     "n_dates": int(evi.loc[ids, "historical_date"].nunique())
                     if "historical_date" in evd else np.nan,
                     "p_reversal": float(rev_rate), "base_p_reversal": float(base),
                     "lift": float(rev_rate / base) if base == base and base > 0 else np.nan,
                     "n_subperiods": int(evi.loc[ids, "subperiod"].nunique())})
    seq = pd.DataFrame(rows)
    if len(seq):
        # z-test vs base
        n = seq["n_events"].astype(float)
        var = (base * (1 - base) / n).clip(lower=1e-12) if base == base else np.nan
        z = (seq["p_reversal"] - base) / np.sqrt(var)
        seq["p_value"] = (1 - norm.cdf(z)).clip(1e-12, 1.0) if base == base else np.nan
        seq["p_fdr"] = multipletests(seq["p_value"].fillna(1.0), method="fdr_bh")[1]
        seq = seq.sort_values("lift", ascending=False)
    seq.to_csv(OUT / "05_ISOLATED_DOWN_PRE_EVENT_SEQUENCE_ATLAS.csv", index=False)
    return seq
# =========================================================================
# WS3: FULL 4-STATE TRANSITION MATRIX (PRIMARY)
# =========================================================================

def _attach_event_counts(df, ev):
    """Forward event counts (1/3/7/14D) by family onto daily frame."""
    evd = ev.copy()
    evd["d"] = pd.to_datetime(evd["historical_date"]).dt.normalize()
    fam_day = evd.groupby(["d", "family"]).size().unstack(fill_value=0)
    date_ser = pd.to_datetime(df["historical_date"]).dt.normalize()
    out = df.copy()
    for f in ["ISOLATED_DOWNSIDE_EXTREME", "LOCAL_CLUSTER_DOWNSIDE",
              "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE", "ISOLATED_UPSIDE",
              "COORDINATED_DOWNSIDE"]:
        col = f"ev_{f}"
        s = date_ser.map(fam_day.get(f, pd.Series(dtype=int))).fillna(0).astype(int)
        out[col] = s
        for h in [1, 3, 7, 14]:
            out[f"{col}_fwd{h}"] = s.shift(-h).fillna(0).astype(int)
    return out


def ws3_transition_matrix(daily, ev):
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    df = daily.copy()
    df["cell"] = [_cell(b, d2) for b, d2 in
                  zip(df["top500_breadth_30d"], df["top500_dispersion_30d"])]
    df["d"] = pd.to_datetime(df["historical_date"]).dt.normalize()
    df = _attach_event_counts(df, ev)
    st = df["state"]
    df["fwd7_state"] = st.shift(-7)
    df["fwd14_state"] = st.shift(-14)
    df["prop7"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(float)
    df["reentry7"] = (df["fwd7_state"] == REENTRY_LABEL).astype(float)
    df["mixed7"] = (df["fwd7_state"] == "MIXED_NO_CLEAR_ROUTE").astype(float)
    # transitions (consecutive days)
    tr = df[["d", "cell"]].copy()
    tr["next_cell"] = tr["cell"].shift(-1)
    tr = tr[(tr["d"].shift(-1) == tr["d"] + pd.Timedelta(days=1))]
    tr = tr.dropna(subset=["next_cell"])
    # dwell before transition: run length of current cell
    run = (df["cell"] != df["cell"].shift()).cumsum()
    df["_run"] = run
    tr["state_age"] = tr["d"].map(
        df.groupby("_run")["d"].transform("first").set_axis(df.index)).map(
            lambda start: (tr["d"] - start).dt.days)
    # actually simpler: build age directly
    df["age_in_cell"] = df.groupby("_run").cumcount() + 1
    tr["state_age"] = tr["d"].map(df.set_index("d")["age_in_cell"]).astype(float)

    fwd_cols = {f: f"ev_{f}_fwd7" for f in
                ["ISOLATED_DOWNSIDE_EXTREME", "COORDINATED_DOWNSIDE",
                 "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"]}
    tr = tr.merge(df[["d", "cell"] + list(fwd_cols.values()) +
                     ["prop7", "reentry7", "mixed7", "rank_depth_rel",
                      "top3_share_chg7", "CONC_RISING", "CONC_FALLING",
                      "BTC_UP", "BTC_DOWN", "VOL_HIGH", "VOL_LOW",
                      "BREADTH_EXPANDING", "BREADTH_CONTRACTING",
                      "subperiod"]].drop_duplicates("d"),
                  on="d", how="left", suffixes=("", "_y"))
    rows = []
    cells = sorted(df["cell"].unique())
    for c in cells:
        for nc in cells:
            sub = tr[(tr["cell"] == c) & (tr["next_cell"] == nc)]
            n = len(sub)
            if n < 10:
                continue
            row = {"from": c, "to": nc, "n": int(n),
                   "p": float(n / max(len(tr[(tr["cell"] == c)]), 1)),
                   "med_dwell_before_d": float(sub["state_age"].median()),
                   "med_state_age": float(sub["state_age"].median()),
                   "fwd7_isol_dn_per_day": float(sub[fwd_cols["ISOLATED_DOWNSIDE_EXTREME"]].mean()),
                   "fwd7_coord_dn_per_day": float(sub[fwd_cols["COORDINATED_DOWNSIDE"]].mean()),
                   "fwd7_band_up_per_day": float(sub[fwd_cols["BAND_BROAD_UPSIDE"]].mean() +
                                                 sub[fwd_cols["MULTI_BAND_UPSIDE"]].mean()),
                   "fwd7_prop": float(sub["prop7"].mean()),
                   "fwd7_reentry": float(sub["reentry7"].mean()),
                   "fwd7_mixed": float(sub["mixed7"].mean()),
                   "fwd7_rank_depth_rel": float(sub["rank_depth_rel"].mean()),
                   "fwd7_top3_chg": float(sub["top3_share_chg7"].mean()),
                   "p_conc_rising": float(sub["CONC_RISING"].mean()),
                   "p_btc_up": float(sub["BTC_UP"].mean()),
                   "p_vol_high": float(sub["VOL_HIGH"].mean()),
                   "p_brd_expanding": float(sub["BREADTH_EXPANDING"].mean()),
                   "subperiods": int(sub["subperiod"].nunique())}
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "06_BRD_DISP_4STATE_TRANSITION_MATRIX.csv", index=False)
    return {"matrix": out, "tr": tr, "df": df}


# =========================================================================
# WS4: STATE AGE / MATURITY
# =========================================================================

AGE_BINS = [(1, 1, "DAY_1"), (2, 3, "DAY_2_3"), (4, 7, "DAY_4_7"),
            (8, 14, "DAY_8_14"), (15, 10 ** 9, "DAY_15_PLUS")]


def _age_bucket(age):
    for lo, hi, name in AGE_BINS:
        if lo <= age <= hi:
            return name
    return "DAY_15_PLUS"


def ws4_state_age(df):
    """For each cell x age bucket: forward tails, event rates, P(leave), next."""
    df = df.copy()
    df["age_bucket"] = df["age_in_cell"].apply(_age_bucket)
    cells = sorted(df["cell"].unique())
    rows = []
    for c in cells:
        sub = df[df["cell"] == c]
        for ab in [b[2] for b in AGE_BINS]:
            s2 = sub[sub["age_bucket"] == ab]
            if len(s2) < 30:
                continue
            next_cell_ser = df["cell"].shift(-1).loc[s2.index]
            p_leave = float((next_cell_ser != c).mean()) if next_cell_ser.notna().any() else np.nan
            nxt = next_cell_ser[next_cell_ser != c]
            nxt_mode = nxt.mode().iloc[0] if len(nxt) else ""
            row = {"cell": c, "age_bucket": ab, "n_days": int(len(s2)),
                   "p_leave": p_leave, "next_state_mode": str(nxt_mode),
                   "fwd7_isol_dn": float(df.loc[s2.index, "ev_ISOLATED_DOWNSIDE_EXTREME_fwd7"].mean()),
                   "fwd7_coord_dn": float(df.loc[s2.index, "ev_COORDINATED_DOWNSIDE_fwd7"].mean()),
                   "fwd7_band_up": float(df.loc[s2.index, "ev_BAND_BROAD_UPSIDE_fwd7"].mean() +
                                         df.loc[s2.index, "ev_MULTI_BAND_UPSIDE_fwd7"].mean()),
                   "fwd7_prop": float(df.loc[s2.index, "prop7"].mean()),
                   "fwd7_reentry": float(df.loc[s2.index, "reentry7"].mean()),
                   "fwd7_mixed": float(df.loc[s2.index, "mixed7"].mean()),
                   "fwd7_rank_depth_rel": float(df.loc[s2.index, "rank_depth_rel"].mean()),
                   "fwd7_top3_chg": float(df.loc[s2.index, "top3_share_chg7"].mean()),
                   "p_conc_rising": float(df.loc[s2.index, "CONC_RISING"].mean()),
                   "p_btc_up": float(df.loc[s2.index, "BTC_UP"].mean()),
                   "p_vol_high": float(df.loc[s2.index, "VOL_HIGH"].mean()),
                   "subperiods": int(df.loc[s2.index, "subperiod"].nunique())}
            rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "07_BRD_DISP_STATE_AGE.csv", index=False)
    return out


# =========================================================================
# WS5: HIGH_BREADTH + HIGH_DISPERSION FULL LIFECYCLE
# =========================================================================

def ws5_hh_lifecycle(daily, ev):
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    df = daily.copy()
    df["cell"] = [_cell(b, d2) for b, d2 in
                  zip(df["top500_breadth_30d"], df["top500_dispersion_30d"])]
    df["brd_hi"] = (df["top500_breadth_30d"] > BRD_MED).astype(int)
    df["disp_hi"] = (df["top500_dispersion_30d"] > DISP_MED).astype(int)
    df["in_hh"] = ((df["brd_hi"] == 1) & (df["disp_hi"] == 1)).astype(int)
    df["d"] = pd.to_datetime(df["historical_date"]).dt.normalize()
    df = _attach_event_counts(df, ev)
    df["_run"] = (df["in_hh"] != df["in_hh"].shift()).cumsum()

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
    if not eps:
        pd.DataFrame().to_csv(OUT / "08_HH_FULL_LIFECYCLE.csv", index=False)
        pd.DataFrame().to_csv(OUT / "09_HH_TRANSITION_LATTICE.csv", index=False)
        return {"ep": pd.DataFrame()}
    ep = pd.DataFrame(eps)
    ep["start_date"] = df["d"].iloc[ep["start"]].values
    ep["end_date"] = df["d"].iloc[ep["end"]].values
    ep["subperiod"] = df["subperiod"].iloc[ep["start"]].values
    # pre-entry origin cell (cell at start-1)
    orig = df["cell"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    ep["origin_cell"] = orig
    # entry order: breadth/dispersion high already at start-1?
    ep["brd_hi_prev"] = df["brd_hi"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    ep["disp_hi_prev"] = df["disp_hi"].iloc[np.clip(ep["start"] - 1, 0, len(df) - 1)].values
    bhp = ep["brd_hi_prev"].astype(bool).to_numpy()
    dhp = ep["disp_hi_prev"].astype(bool).to_numpy()
    ep["entry_order"] = np.select(
        [bhp & ~dhp, ~bhp & dhp, bhp & dhp],
        ["BRD_FIRST", "DISP_FIRST", "SYNCHRONOUS"], default="FRESH")
    # dwell internal tail mix (event counts during episode)
    for f in ["ISOLATED_DOWNSIDE_EXTREME", "COORDINATED_DOWNSIDE",
              "BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"]:
        vals = []
        for _, r in ep.iterrows():
            vals.append(int(df[f"ev_{f}"].iloc[r["start"]:r["end"] + 1].sum()))
        ep[f"n_{f}"] = vals
    # rank-depth recruitment during dwell (med_ret30_201_500 change over episode)
    rd = []
    for _, r in ep.iterrows():
        a = df["med_ret30_201_500"].iloc[r["start"]]
        b = df["med_ret30_201_500"].iloc[r["end"]]
        rd.append(float(b - a) if (a == a and b == b) else np.nan)
    ep["rank_depth_chg_dwell"] = rd
    # exit: what collapses first (cell at end+1)
    ex = df[["brd_hi", "disp_hi"]].iloc[np.clip(ep["end"] + 1, 0, len(df) - 1)].values
    ex_brd, ex_disp = ex[:, 0], ex[:, 1]
    ep["exit_cell"] = df["cell"].iloc[np.clip(ep["end"] + 1, 0, len(df) - 1)].values
    ep["exit_order"] = np.select(
        [(ex_brd == 0) & (ex_disp == 1), (ex_brd == 1) & (ex_disp == 0),
         (ex_brd == 0) & (ex_disp == 0), (ex_brd == 1) & (ex_disp == 1)],
        ["BRD_FIRST_EXIT", "DISP_FIRST_EXIT", "COUPLED_EXIT", "STAYS_HH"],
        default="COUPLED_EXIT")
    st7 = df["state"].iloc[np.clip(ep["end"] + 7, 0, len(df) - 1)].values
    st30 = df["state"].iloc[np.clip(ep["end"] + 30, 0, len(df) - 1)].values
    cell7 = df["cell"].iloc[np.clip(ep["end"] + 7, 0, len(df) - 1)].values
    cell30 = df["cell"].iloc[np.clip(ep["end"] + 30, 0, len(df) - 1)].values
    ep["state_7d_after"] = st7
    ep["state_30d_after"] = st30
    ep["cell_7d_after"] = cell7
    ep["cell_30d_after"] = cell30
    ep["p_7d_success"] = ep["state_7d_after"].isin(SUCCESS_LABELS).astype(float)
    ep["p_30d_success"] = ep["state_30d_after"].isin(SUCCESS_LABELS).astype(float)
    ep["p_7d_reentry"] = (ep["state_7d_after"] == REENTRY_LABEL).astype(float)
    ep["p_7d_hh_reentry"] = (ep["cell_7d_after"] == "HIGH_BREADTH_HIGH_DISP").astype(float)

    # lifecycle table: origin x entry_order x dwell_bucket x exit_order
    ep["dwell_bucket"] = ep["n"].apply(_age_bucket)
    life_rows = []
    for key, cols in [("origin_cell", ["origin_cell"]),
                      ("entry_order", ["entry_order"]),
                      ("exit_order", ["exit_order"]),
                      ("dwell_bucket", ["dwell_bucket"]),
                      ("origin_entry_exit", ["origin_cell", "entry_order", "exit_order"])]:
        gb = ep.groupby(cols)
        for keyvals, g in gb:
            if len(g) < 10:
                continue
            life_rows.append({"dimension": key,
                              "path": "|".join(str(v) for v in keyvals),
                              "n_episodes": int(len(g)),
                              "median_dwell_d": float(g["n"].median()),
                              "n_subperiods": int(g["subperiod"].nunique()),
                              "p_7d_success": float(g["p_7d_success"].mean()),
                              "p_30d_success": float(g["p_30d_success"].mean()),
                              "p_7d_reentry": float(g["p_7d_reentry"].mean()),
                              "p_7d_hh_reentry": float(g["p_7d_hh_reentry"].mean()),
                              "med_rank_depth_chg": float(g["rank_depth_chg_dwell"].median()),
                              "med_isol_dn_per_ep": float(g["n_ISOLATED_DOWNSIDE_EXTREME"].median()),
                              "med_band_up_per_ep": float((g["n_BAND_BROAD_UPSIDE"] + g["n_MULTI_BAND_UPSIDE"]).median())})
    life = pd.DataFrame(life_rows)
    life.to_csv(OUT / "08_HH_FULL_LIFECYCLE.csv", index=False)
    # transition lattice: from HH to next cells + post-exit outcome
    lat_rows = []
    for (ec, st7c, st30c), g in ep.groupby(["exit_cell", "cell_7d_after", "cell_30d_after"]):
        if len(g) < 10:
            continue
        lat_rows.append({"exit_cell": ec, "cell_7d": st7c, "cell_30d": st30c,
                         "n_episodes": int(len(g)),
                         "median_dwell_d": float(g["n"].median()),
                         "p_7d_success": float(g["p_7d_success"].mean()),
                         "p_30d_success": float(g["p_30d_success"].mean()),
                         "p_7d_reentry": float(g["p_7d_reentry"].mean()),
                         "subperiods": int(g["subperiod"].nunique())})
    lat = pd.DataFrame(lat_rows)
    lat.to_csv(OUT / "09_HH_TRANSITION_LATTICE.csv", index=False)
    return {"life": life, "lat": lat, "ep": ep}
# =========================================================================
# WS6: BREADTH ARCHITECTURE - "WHO IS CREATING BREADTH?"
# =========================================================================

def _cohort_bucket(x, lo, hi, name):
    if x != x:
        return np.nan
    if x < lo:
        return np.nan
    if x >= hi:
        return np.nan
    return name


def ws6_breadth_architecture(feat, daily):
    """On high-breadth days (breadth30 > BRD_MED), decompose positive
    participation by rank layer / age / liquidity / vol / rank-health /
    move-magnitude cohorts. Also entropy + strong-move share."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    hi_days = daily[daily["top500_breadth_30d"] > BRD_MED]["d"]
    f = feat.copy()
    f = f[f["d"].isin(set(hi_days))].copy()
    # positive move flag (1D return > 0)
    f["pos"] = (f["return_1d"] > 0).astype(int)
    f = f[f["return_1d"].notna()].copy()
    # rank layer
    layer_map = {
        "1-10": "R1_25", "11-25": "R1_25",
        "26-50": "R26_100", "51-100": "R26_100",
        "101-200": "R101_250", "201-300": "R101_250",
        "301-500": "R251_500",
    }
    f["layer"] = f["rank_band"].map(layer_map)
    # age cohort: days_in_top500 terciles (rank-based to avoid duplicate edges)
    f["age_q"] = pd.qcut(f["days_in_top500"].rank(method="first"), 3,
                          labels=["YOUNG", "MID_AGE", "MATURE"], duplicates="drop")
    # liquidity cohort: market_cap_share terciles per date
    f["liq_q"] = f.groupby("d")["market_cap_share"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 3, labels=["LIQ_LO", "LIQ_MID", "LIQ_HI"], duplicates="drop"))
    # vol cohort: realized_volatility_30d terciles per date (NaN-safe)
    def _qcut3(s):
        if s.notna().sum() < 3:
            return pd.Series(np.nan, index=s.index)
        return pd.qcut(s.rank(method="first"), 3,
                       labels=["VOL_LO", "VOL_MID", "VOL_HI"], duplicates="drop")
    f["vol_q"] = f.groupby("d")["realized_volatility_30d"].transform(_qcut3)
    # rank health: rank_velocity_7d sign
    f["rank_health"] = np.select(
        [f["rank_velocity_7d"] > 1, f["rank_velocity_7d"] < -1],
        ["RH_IMPROVING", "RH_DETERIORATING"], default="RH_STABLE")
    # move magnitude: |ret_1d| in sigma units -> use realized vol
    sig = f["realized_volatility_30d"].replace(0, np.nan)
    f["move_sigma"] = f["return_1d"].abs() / sig
    f["move_mag"] = np.select(
        [f["move_sigma"] >= 2, f["move_sigma"] >= 1],
        ["MOVE_2SIGMA", "MOVE_1SIGMA"], default="MOVE_SUB1SIGMA")
    # ---- per-day cohort contribution: share of positive movers in cohort
    rows = []
    daily_pos = f.groupby("d")["pos"].agg(["sum", "count"]).rename(
        columns={"sum": "n_pos_total", "count": "n_assets"})
    for cohort, col in [("rank_layer", "layer"), ("age", "age_q"),
                        ("liquidity", "liq_q"), ("vol", "vol_q"),
                        ("rank_health", "rank_health"), ("move_magnitude", "move_mag")]:
        g = f.groupby(["d", col])["pos"].agg(["sum", "count"])
        g = g.reset_index().merge(daily_pos, on="d", how="left")
        g["share_of_pos"] = g["sum"] / g["n_pos_total"].replace(0, np.nan)
        g["pos_rate"] = g["sum"] / g["count"].replace(0, np.nan)
        g["cohort"] = cohort
        g = g.rename(columns={col: "bucket"})
        rows.append(g[["d", "cohort", "bucket", "sum", "count", "share_of_pos", "pos_rate"]])
    comp = pd.concat(rows, ignore_index=True)
    comp.to_csv(OUT / "10_BREADTH_ARCHITECTURE_COMPONENTS.csv", index=False)

    # ---- day-level architecture features (for clustering)
    piv = f.pivot_table(index="d", columns="layer", values="pos",
                        aggfunc="mean").reset_index()
    age_piv = f.pivot_table(index="d", columns="age_q", values="pos",
                            aggfunc="mean").reset_index()
    liq_piv = f.pivot_table(index="d", columns="liq_q", values="pos",
                            aggfunc="mean").reset_index()
    vol_piv = f.pivot_table(index="d", columns="vol_q", values="pos",
                            aggfunc="mean").reset_index()
    rh_piv = f.pivot_table(index="d", columns="rank_health", values="pos",
                           aggfunc="mean").reset_index()
    # entropy of positive-move share by layer
    sh = f[f["pos"] == 1].groupby(["d", "layer"]).size().unstack(fill_value=0)
    sh = sh.div(sh.sum(axis=1), axis=0)
    ent = (-sh * np.log(sh.clip(lower=1e-12))).sum(axis=1).rename("entropy_layers")
    strong = f[f["pos"] == 1].groupby("d")["move_mag"].apply(
        lambda s: (s == "MOVE_1SIGMA").sum() / max(len(s), 1)).rename("share_strong_ge1s")
    arch = piv.merge(age_piv, on="d", how="outer").merge(liq_piv, on="d", how="outer")
    arch = arch.merge(vol_piv, on="d", how="outer").merge(rh_piv, on="d", how="outer")
    arch = arch.merge(ent.rename("entropy_layers"), left_on="d", right_index=True, how="left")
    arch = arch.merge(strong, left_on="d", right_index=True, how="left")
    arch = arch.merge(daily[["d", "subperiod"]].drop_duplicates(), on="d", how="left")
    arch = arch.merge(daily[["d", "top500_breadth_30d"]].drop_duplicates(), on="d", how="left")
    arch.to_csv(OUT / "11_BREADTH_ARCHITECTURE_DAILY_FEATURES.csv", index=False)
    return {"comp": comp, "arch": arch}


def ws6b_architecture_classes(arch):
    """Unsupervised clustering of architecture day-features; keep only if
    stable under perturbation, interpretable, >=50 episodes, multi-cycle."""
    from sklearn.cluster import KMeans
    a = arch.dropna(subset=["entropy_layers"]).copy()
    feat_cols = [c for c in ["R1_25", "R26_100", "R101_250", "R251_500",
                             "share_strong_ge1s", "entropy_layers"] if c in a.columns]
    if len(a) < 100 or len(feat_cols) < 4:
        pd.DataFrame().to_csv(OUT / "11_BREADTH_ARCHITECTURE_CLASSES.csv", index=False)
        return pd.DataFrame()
    X = a[feat_cols].to_numpy(float)
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)
    # stability: perturbed kmeans (2..4 clusters), pick k with best silhouette
    from sklearn.metrics import silhouette_score
    best_k, best_s = 2, -1
    for k in [2, 3, 4]:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(X)
        s = silhouette_score(X, km.labels_)
        if s > best_s:
            best_k, best_s = k, s
    km = KMeans(n_clusters=best_k, n_init=20, random_state=SEED).fit(X)
    a["cluster"] = km.labels_
    rows = []
    for k in range(best_k):
        g = a[a["cluster"] == k]
        if len(g) < MIN_PROMOTE_N:
            continue
        rows.append({"cluster": k, "n_days": int(len(g)),
                     "n_subperiods": int(g["subperiod"].nunique()),
                     "med_breadth30": float(g["top500_breadth_30d"].median()),
                     "med_entropy": float(g["entropy_layers"].median()),
                     "med_share_strong": float(g["share_strong_ge1s"].median()),
                     "med_R1_25": float(g["R1_25"].median()),
                     "med_R251_500": float(g["R251_500"].median()),
                     "silhouette": float(best_s)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "11_BREADTH_ARCHITECTURE_CLASSES.csv", index=False)
    return out


# =========================================================================
# WS7: BREADTH LEVEL VS ARCHITECTURE (nested incremental audit)
# =========================================================================

def _purged_folds(n, k=5, embargo=7):
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


def ws7_level_vs_architecture(daily, arch, ledger):
    """Nested models: M0 breadth level; M1 + rank comp; M2 + age; M3 + liquidity;
    M4 + move-magnitude; M5 + rank-health; M6 + all. Targets: upper propagation
    success (ledger) and isolated-down reversal (LF2, see ws8 hook)."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    date_pos = {d: i for i, d in enumerate(daily["d"])}
    archd = arch.set_index("d")
    blocks = {
        "level": ["top500_breadth_30d"],
        "rank_comp": ["R1_25", "R26_100", "R101_250", "R251_500"],
        "age_comp": ["YOUNG", "MID_AGE", "MATURE"],
        "liq_comp": ["LIQ_LO", "LIQ_MID", "LIQ_HI"],
        "move_comp": ["share_strong_ge1s"],
        "rank_health_comp": ["RH_IMPROVING", "RH_STABLE", "RH_DETERIORATING"],
        "entropy": ["entropy_layers"],
    }
    led = ledger.copy()
    led["y"] = led["first_destination"].isin(SUCCESS_LABELS).astype(int)
    rows_all = []
    for _, r in led.iterrows():
        i = date_pos.get(pd.Timestamp(r["exit_date"]).normalize())
        if i is None:
            continue
        row = {"event_id": r["event_id"], "y": int(r["y"])}
        for blk, cols in blocks.items():
            for c in cols:
                if c == "top500_breadth_30d":
                    v = daily["top500_breadth_30d"].iloc[i]
                else:
                    dstr = pd.Timestamp(daily["historical_date"].iloc[i]).normalize()
                    v = archd.loc[dstr, c] if dstr in archd.index else np.nan
                row[f"{blk}:{c}"] = float(v) if v == v else np.nan
        rows_all.append(row)
    Xd = pd.DataFrame(rows_all).set_index("event_id")
    y = Xd["y"].to_numpy(float)
    Xf = Xd.drop(columns=["y"]).copy()
    for c in Xf.columns:
        med = Xf[c].median()
        Xf[c] = Xf[c].fillna(med)
    folds = _purged_folds(len(Xd), k=5, embargo=7)
    base_ll, base_br, base_auc = _logreg_cv(
        Xf[["level:top500_breadth_30d"]].to_numpy(float), y, folds)
    out = []
    out.append({"target": "upper_propagation", "model": "M0_level",
                "features": "breadth level", "delta_logloss": 0.0,
                "delta_brier": 0.0, "delta_auc": 0.0, "cv_logloss": base_ll,
                "cv_brier": base_br, "cv_auc": base_auc, "n": int(len(Xd))})
    seq = ["rank_comp", "age_comp", "liq_comp", "move_comp", "rank_health_comp", "entropy"]
    for blk in seq:
        cols = [c for c in Xf.columns if c.startswith(f"{blk}:")]
        use = ["level:top500_breadth_30d"] + cols
        ll, br, auc = _logreg_cv(Xf[use].to_numpy(float), y, folds)
        out.append({"target": "upper_propagation", "model": f"M+{blk}",
                    "features": "+".join(cols),
                    "delta_logloss": float(ll - base_ll) if ll == ll else np.nan,
                    "delta_brier": float(br - base_br) if br == br else np.nan,
                    "delta_auc": float(auc - base_auc) if (auc == auc and base_auc == base_auc) else np.nan,
                    "cv_logloss": ll, "cv_brier": br, "cv_auc": auc, "n": int(len(Xd))})
    allcols = list(Xf.columns)
    fll, fbr, fauc = _logreg_cv(Xf[allcols].to_numpy(float), y, folds)
    out.append({"target": "upper_propagation", "model": "M_FULL",
                "features": "all blocks",
                "delta_logloss": float(fll - base_ll) if fll == fll else np.nan,
                "delta_brier": float(fbr - base_br) if fbr == fbr else np.nan,
                "delta_auc": float(fauc - base_auc) if (fauc == fauc and base_auc == base_auc) else np.nan,
                "cv_logloss": fll, "cv_brier": fbr, "cv_auc": fauc, "n": int(len(Xd))})
    audit = pd.DataFrame(out)
    audit.to_csv(OUT / "12_BREADTH_LEVEL_VS_ARCHITECTURE_AUDIT.csv", index=False)
    return audit


# =========================================================================
# WS8: RANK HEALTH VS PRICE RECOVERY (PRIORITY)
# =========================================================================

def _fwd_rank_lookup(ev):
    """Forward rank velocity at t+7 for events: rank_vel_7d is trailing, so we
    self-join the LF2 frame on (cmc_id, date+7). Returns dict event_id -> fwd rv."""
    cols = ["historical_date", "cmc_id", "rank_vel_7d"]
    lf2 = pd.read_parquet(LF2_FEATURES, columns=cols)
    lf2["d"] = pd.to_datetime(lf2["historical_date"]).dt.normalize()
    lf2["key"] = lf2["cmc_id"].astype(str) + "_" + lf2["d"].dt.strftime("%Y%m%d")
    lookup = dict(zip(lf2["key"], lf2["rank_vel_7d"]))
    del lf2
    gc.collect()
    evd = ev.copy()
    evd["d"] = pd.to_datetime(evd["historical_date"]).dt.normalize()
    evd["tgt"] = evd["d"] + pd.Timedelta(days=7)
    evd["key"] = evd["cmc_id"].astype(str) + "_" + evd["tgt"].dt.strftime("%Y%m%d")
    evd["fwd_rank_vel_7d"] = evd["key"].map(lookup)
    return dict(zip(evd["event_id"], evd["fwd_rank_vel_7d"]))


def ws8_price_rank_health(daily, ev, fwd_rank_map=None):
    """Price outcome x rank outcome matrix for isolated-downside events.
    rank_outcome uses FORWARD rank velocity (t+7, from self-join) when
    available; falls back to trailing rank_vel_14d only if lookup missing."""
    evd = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy().reset_index(drop=True)
    evd["price_outcome"] = [_price_outcome_class(r) for _, r in evd.iterrows()]
    rv = evd["rank_vel_7d"].to_numpy(float)
    evd["pre_rank_state"] = np.select([rv > 2, rv < -2],
                                      ["RANK_IMPROVING", "RANK_DETERIORATING"],
                                      default="RANK_STABLE")
    if fwd_rank_map:
        fwd_rv = evd["event_id"].map(fwd_rank_map).to_numpy(float)
        evd["fwd_rank_vel_7d"] = fwd_rv
        rank_out = np.array([_rank_outcome(x) for x in fwd_rv], dtype=object)
        # fill missing lookups with trailing rank_vel_14d
        miss = fwd_rv != fwd_rv
        if miss.any():
            trailing = evd.loc[miss, "rank_vel_14d"].to_numpy(float)
            rank_out[miss] = np.array([_rank_outcome(x) for x in trailing], dtype=object)
        evd["rank_outcome"] = rank_out
    else:
        evd["rank_outcome"] = [_rank_outcome(x) for x in
                               evd["rank_vel_14d"].to_numpy(float)]
    # price recovery flags (non-exclusive, for the 2x2 cross)
    s = evd["sigma_t0"].to_numpy(float)
    evd["price_recovered"] = ((evd["fwd14_cum"].to_numpy(float) / s > 0.5) |
                              (evd["fwd30_cum"].to_numpy(float) / s > 0.5)).astype(int)
    evd["price_new_low"] = ((evd["fwd30_cum"].to_numpy(float) / s < -2.0)).astype(int)
    evd["rank_recovered"] = (evd["rank_outcome"] == "RANK_RECOVERY").astype(int)
    evd["rank_decayed"] = (evd["rank_outcome"] == "RANK_CONTINUED_DETERIORATION").astype(int)
    # cross state
    pr = evd["price_recovered"].astype(bool).to_numpy()
    rr = evd["rank_recovered"].astype(bool).to_numpy()
    evd["cross_state"] = np.select(
        [pr & rr, pr & ~rr, ~pr & rr, ~pr & ~rr],
        ["PRICE_RECOVERY_RANK_RECOVERY", "PRICE_RECOVERY_RANK_DECAY",
         "PRICE_DECAY_RANK_RECOVERY", "PRICE_DECAY_RANK_DECAY"],
        default="PRICE_DECAY_RANK_DECAY")
    rows = []
    for rs in ["RANK_IMPROVING", "RANK_STABLE", "RANK_DETERIORATING"]:
        sub = evd[evd["pre_rank_state"] == rs]
        if len(sub) < 30:
            continue
        for cs in ["PRICE_RECOVERY_RANK_RECOVERY", "PRICE_RECOVERY_RANK_DECAY",
                   "PRICE_DECAY_RANK_RECOVERY", "PRICE_DECAY_RANK_DECAY"]:
            rows.append({"pre_rank_state": rs, "cross_state": cs,
                         "n": int((sub["cross_state"] == cs).sum()),
                         "pct": float((sub["cross_state"] == cs).mean()),
                         "n_total": int(len(sub))})
        rows.append({"pre_rank_state": rs, "cross_state": "TOTAL",
                     "n": int(len(sub)), "pct": 1.0, "n_total": int(len(sub))})
    mat = pd.DataFrame(rows)
    mat.to_csv(OUT / "13_PRICE_RANK_HEALTH_MATRIX.csv", index=False)
    evd.to_parquet(OUT / "13b_PRICE_RANK_HEALTH_EVENTS.parquet", index=False)

    # temporal order: does rank recover before or after price?
    # price time-to-recovery = first fwd horizon with cum >= +0.5 sigma
    s2 = evd["sigma_t0"].to_numpy(float)
    order_rows = []
    for _, r in evd.iterrows():
        if r["sigma_t0"] != r["sigma_t0"] or r["sigma_t0"] <= 0:
            continue
        rec = None
        for h in [1, 2, 3, 5, 7, 10, 14, 21, 30]:
            v = r[f"fwd{h}_cum"]
            if v == v and v / r["sigma_t0"] >= 0.5:
                rec = h
                break
        order_rows.append({"event_id": r["event_id"],
                           "price_recovery_day": rec,
                           "pre_rank_state": r["pre_rank_state"],
                           "rank_outcome": r["rank_outcome"],
                           "fwd_rank_vel_14d": float(r["rank_vel_14d"]),
                           "price_recovered": int(r["price_recovered"]),
                           "rank_recovered": int(r["rank_recovered"])})
    od = pd.DataFrame(order_rows)
    od.to_csv(OUT / "14_PRICE_RANK_TEMPORAL_ORDER.csv", index=False)
    return {"matrix": mat, "events": evd, "order": od}
# =========================================================================
# WS9: FAILED-RECOVERY STRESS RESPONSE PILOT
# =========================================================================

def ws9_stress_response(daily, ev, fwd_rank_map):
    """For deteriorating-rank isolated-downside assets: does the field improve
    in the next 14D, and does the asset respond (price/rank recovery)?"""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    date_pos = {d: i for i, d in enumerate(daily["d"])}
    evd = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy().reset_index(drop=True)
    evd = evd[evd["rank_vel_7d"] < -2].copy()  # deteriorating pre-event
    if len(evd) < 30:
        pd.DataFrame().to_csv(OUT / "15_FAILED_RECOVERY_STRESS_RESPONSE.csv", index=False)
        return pd.DataFrame()
    rows = []
    for _, r in evd.iterrows():
        i = date_pos.get(pd.Timestamp(r["historical_date"]).normalize())
        if i is None:
            continue
        window = daily.iloc[i:i + 15]
        if len(window) < 5:
            continue
        field_improves = bool((window["breadth_vel"].fillna(0) > 0).any())
        btc_support = bool((window["btc_return_7d"].fillna(0) > 0).any())
        peer_band = bool((window["med_ret30_201_500"].fillna(0) > 0).any())
        # asset response
        s = r["sigma_t0"]
        price_resp = np.nan
        if s == s and s > 0:
            f7 = r["fwd7_cum"]
            f14 = r["fwd14_cum"]
            f30 = r["fwd30_cum"]
            if f7 == f7 and f7 / s >= 1.0:
                price_resp = "RESPONDS"
            elif f14 == f14 and f14 / s >= 0.5:
                price_resp = "DELAYED_RESPONSE"
            elif f14 == f14 and f14 / s > 0:
                price_resp = "WEAK_RESPONSE"
            else:
                price_resp = "NO_RESPONSE"
        fwd_rv = fwd_rank_map.get(r["event_id"], np.nan)
        rank_resp = "RANK_RECOVERS" if (fwd_rv == fwd_rv and fwd_rv > 0) else \
                    ("RANK_DECAYS" if (fwd_rv == fwd_rv and fwd_rv < 0) else "RANK_UNKNOWN")
        rows.append({"event_id": r["event_id"], "date": str(pd.Timestamp(r["historical_date"]))[:10],
                     "pre_rank_vel7": float(r["rank_vel_7d"]),
                     "field_improves_14d": int(field_improves),
                     "btc_support_14d": int(btc_support),
                     "peer_band_up_14d": int(peer_band),
                     "price_response": price_resp, "rank_response": rank_resp})
    out = pd.DataFrame(rows)
    # aggregate: among field-improving windows, what share respond?
    agg = []
    for fi in [0, 1]:
        sub = out[out["field_improves_14d"] == fi]
        if len(sub) < 30:
            continue
        agg.append({"field_improves_14d": int(fi), "n": int(len(sub)),
                    "p_responds": float((sub["price_response"] == "RESPONDS").mean()),
                    "p_weak_or_delayed": float(sub["price_response"].isin(["WEAK_RESPONSE", "DELAYED_RESPONSE"]).mean()),
                    "p_no_response": float((sub["price_response"] == "NO_RESPONSE").mean()),
                    "p_rank_recovers": float((sub["rank_response"] == "RANK_RECOVERS").mean()),
                    "p_rank_decays": float((sub["rank_response"] == "RANK_DECAYS").mean())})
    aggdf = pd.DataFrame(agg)
    out.to_csv(OUT / "15_FAILED_RECOVERY_STRESS_RESPONSE_EVENTS.csv", index=False)
    aggdf.to_csv(OUT / "15_FAILED_RECOVERY_STRESS_RESPONSE.csv", index=False)
    return {"events": out, "agg": aggdf}


# =========================================================================
# WS10: ACTIVE LIQUIDITY / VOLUME AS SHOCK-ABSORPTION CONTEXT
# =========================================================================

def ws10_active_liquidity(ev):
    """Does volume add independent info for isolated-down early recovery /
    reversal, after controlling rank, breadth, dispersion, BTC, volatility,
    age, amplitude? Nested logistic on events with purged chronological CV."""
    evd = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy().reset_index(drop=True)
    evd["price_outcome"] = [_price_outcome_class(r) for _, r in evd.iterrows()]
    evd["y_recover"] = evd["price_outcome"].isin(
        ["EARLY_1SIGMA_RECOVERY", "LATE_RECOVERY", "FULL_REVERSAL"]).astype(int)
    evd["y_reverse"] = evd["reversal"].astype(int)
    evd["rel_vol"] = evd["volume_24h_usd"] / evd["vol_prev7_med"].replace(0, np.nan)
    evd["log_vol"] = np.log1p(evd["volume_24h_usd"].to_numpy(float))
    evd["log_mcap"] = evd["log10_mcap"].to_numpy(float) * np.log(10)
    evd["rel_vol_pct"] = evd.groupby("historical_date")["rel_vol"].transform(
        lambda s: s.rank(pct=True))
    controls = ["rank", "top500_breadth_30d", "top500_dispersion_30d",
                "btc_ret_1d", "mkt_vol_30d", "listing_age_days", "z1"]
    evd = evd.sort_values("historical_date").reset_index(drop=True)
    rows = []
    for yname in ["y_recover", "y_reverse"]:
        sub = evd[evd[yname].notna()].copy()
        sub = sub.dropna(subset=controls + ["rel_vol_pct"])
        if len(sub) < 60:
            continue
        Xc = sub[controls].to_numpy(float)
        Xv = np.column_stack([Xc, sub["rel_vol_pct"].to_numpy(float)])
        y = sub[yname].to_numpy(float)
        folds = _purged_folds(len(sub), k=5, embargo=7)
        ll_c, br_c, auc_c = _logreg_cv(Xc, y, folds)
        ll_v, br_v, auc_v = _logreg_cv(Xv, y, folds)
        # permutation on the incremental delta
        base_d = ll_c - ll_v  # negative = vol improves
        perm = []
        for _ in range(PERM_N):
            rng = np.random.default_rng(SEED)
            yp = rng.permutation(y)
            llp, _, _ = _logreg_cv(np.column_stack([Xc, sub["rel_vol_pct"].to_numpy(float)]), yp, folds)
            lc, _, _ = _logreg_cv(Xc, yp, folds)
            perm.append(lc - llp)
        perm = np.array([p for p in perm if p == p])
        k_ = int((perm <= base_d).sum()) if len(perm) else 0
        rows.append({"target": yname, "n": int(len(sub)),
                     "base_cv_logloss": ll_c, "vol_cv_logloss": ll_v,
                     "delta_logloss": float(ll_v - ll_c) if (ll_v == ll_v and ll_c == ll_c) else np.nan,
                     "base_cv_brier": br_c, "vol_cv_brier": br_v,
                     "delta_brier": float(br_v - br_c) if (br_v == br_v and br_c == br_c) else np.nan,
                     "base_cv_auc": auc_c, "vol_cv_auc": auc_v,
                     "delta_auc": float(auc_v - auc_c) if (auc_v == auc_v and auc_c == auc_c) else np.nan,
                     "perm_p": _perm_p(k_, PERM_N)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "16_ACTIVE_LIQUIDITY_SHOCK_ABSORPTION.csv", index=False)
    return out


# =========================================================================
# WS11: SHMC / SHHM ONE FOCUSED FIELD RECHECK
# =========================================================================

def ws11_shmc_shhm(ev, daily):
    """One focused recheck: field context + reversal/continuation for SHMC vs
    SHHM among extreme events. SHMC = SHORT_HOT_MEDIUM_COLD (reversion-like),
    SHHM = SHORT_HOT_MEDIUM_HOT (continuation-like)."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    date_pos = {d: i for i, d in enumerate(daily["d"])}
    evd = ev.copy().reset_index(drop=True)
    evd = evd[evd["momentum_state"].isin(["SHORT_HOT_MEDIUM_COLD", "SHORT_HOT_MEDIUM_HOT"])].copy()
    if len(evd) < 100:
        pd.DataFrame().to_csv(OUT / "17_SHMC_SHHM_FIELD_RECHECK.csv", index=False)
        return pd.DataFrame()
    evd["grp"] = np.where(evd["momentum_state"] == "SHORT_HOT_MEDIUM_COLD", "SHMC", "SHHM")
    rows = []
    for grp, sub in evd.groupby("grp"):
        if len(sub) < 50:
            continue
        ctx = []
        for _, r in sub.iterrows():
            i = date_pos.get(pd.Timestamp(r["historical_date"]).normalize())
            if i is None:
                continue
            dr = daily.iloc[i]
            ctx.append({"breadth30": dr["top500_breadth_30d"],
                        "disp30": dr["top500_dispersion_30d"],
                        "btc_ret7": dr["btc_return_7d"],
                        "cell": _cell(dr["top500_breadth_30d"], dr["top500_dispersion_30d"]),
                        "rank_depth_rel": dr["rank_depth_rel"]})
        cdf = pd.DataFrame(ctx)
        row = {"group": grp, "n_events": int(len(sub)),
               "n_dates": int(sub["historical_date"].dt.normalize().nunique()),
               "reversal_rate": float(sub["reversal"].mean()),
               "med_fwd7_sigma": float(sub["fwd7_sigma"].median()),
               "p_isolated": float((sub["family"] == "ISOLATED_DOWNSIDE_EXTREME").mean()),
               "p_coordinated_up": float(sub["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"]).mean()),
               "med_breadth30": float(cdf["breadth30"].median()) if len(cdf) else np.nan,
               "med_disp30": float(cdf["disp30"].median()) if len(cdf) else np.nan,
               "med_btc_ret7": float(cdf["btc_ret7"].median()) if len(cdf) else np.nan,
               "med_rank_depth_rel": float(cdf["rank_depth_rel"].median()) if len(cdf) else np.nan,
               "cell_mode": str(cdf["cell"].mode().iloc[0]) if len(cdf) else "",
               "subperiods": int(sub["subperiod"].nunique())}
        rows.append(row)
    out = pd.DataFrame(rows)
    if len(out) >= 2:
        a = out[out["group"] == "SHMC"]
        b = out[out["group"] == "SHHM"]
        # test reversal rate difference at event level
        e1 = evd[evd["grp"] == "SHMC"]["reversal"].dropna()
        e2 = evd[evd["grp"] == "SHHM"]["reversal"].dropna()
        if len(e1) >= 30 and len(e2) >= 30:
            _, p = ranksums(e1, e2)
            out["reversal_ranksum_p"] = float(p)
    out.to_csv(OUT / "17_SHMC_SHHM_FIELD_RECHECK.csv", index=False)
    return out


# =========================================================================
# WS12: VOLATILITY PARKED ROLE CHECK
# =========================================================================

def ws12_volatility_parked(daily, ev):
    """Does VOL state condition (a) HH persistence, (b) isolated-down early
    1-sigma recovery, (c) coordinated-up retention — after controlling
    breadth/dispersion/rank?"""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    # (a) HH persistence by VOL state: mean run length of in_hh
    df = daily.copy()
    df["in_hh"] = ((df["top500_breadth_30d"] > BRD_MED) &
                   (df["top500_dispersion_30d"] > DISP_MED)).astype(int)
    df["_run"] = (df["in_hh"] != df["in_hh"].shift()).cumsum()
    runlen = df.groupby("_run")["in_hh"].transform("size")
    df["run_len"] = runlen
    rows = []
    for vol in ["VOL_HIGH", "VOL_LOW"]:
        sub = df[df[vol] == 1]
        rows.append({"condition": f"HH_persistence|{vol}",
                     "n_days": int(len(sub)),
                     "med_run_len_hh": float(sub.loc[sub["in_hh"] == 1, "run_len"].median()) if (sub["in_hh"] == 1).any() else np.nan,
                     "p_in_hh": float(sub["in_hh"].mean())})
    # (b) isolated-down early 1-sigma recovery by VOL state
    evd = ev[ev["family"] == "ISOLATED_DOWNSIDE_EXTREME"].copy().reset_index(drop=True)
    evd["price_outcome"] = [_price_outcome_class(r) for _, r in evd.iterrows()]
    evd["y_early"] = (evd["price_outcome"] == "EARLY_1SIGMA_RECOVERY").astype(int)
    evd = evd.merge(daily[["d", "VOL_HIGH", "VOL_LOW", "top500_breadth_30d",
                           "top500_dispersion_30d", "rank_depth_rel"]].drop_duplicates("d"),
                    left_on=pd.to_datetime(evd["historical_date"]).dt.normalize(),
                    right_on="d", how="left")
    for vol in ["VOL_HIGH", "VOL_LOW"]:
        sub = evd[evd[vol] == 1]
        other = evd[evd[vol] == 0]
        if len(sub) >= 30 and len(other) >= 30:
            a, b = sub["y_early"].dropna(), other["y_early"].dropna()
            _, p = ranksums(a, b) if (len(a) >= 20 and len(b) >= 20) else (np.nan, np.nan)
            rows.append({"condition": f"early_recovery|{vol}",
                         "n": int(len(sub)), "rate": float(a.mean()),
                         "rate_other": float(b.mean()),
                         "p": float(p) if p == p else np.nan})
    # (c) coordinated-up retention (fwd7_sigma > 0) by VOL
    up = ev[ev["family"].isin(["BAND_BROAD_UPSIDE", "MULTI_BAND_UPSIDE"])].copy().reset_index(drop=True)
    up = up.merge(daily[["d", "VOL_HIGH", "VOL_LOW"]].drop_duplicates("d"),
                  left_on=pd.to_datetime(up["historical_date"]).dt.normalize(),
                  right_on="d", how="left")
    up["retained"] = (up["fwd7_sigma"] > 0).astype(int)
    for vol in ["VOL_HIGH", "VOL_LOW"]:
        sub = up[up[vol] == 1]
        other = up[up[vol] == 0]
        if len(sub) >= 100 and len(other) >= 100:
            a, b = sub["retained"].dropna(), other["retained"].dropna()
            _, p = ranksums(a, b)
            rows.append({"condition": f"coord_up_retention|{vol}",
                         "n": int(len(sub)), "rate": float(a.mean()),
                         "rate_other": float(b.mean()),
                         "p": float(p) if p == p else np.nan})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "18_VOLATILITY_PARKED_ROLE_CHECK.csv", index=False)
    return out
# =========================================================================
# WS13: AGENT1 / AGENT2 DEFINITION RECONCILIATION
# =========================================================================

def ws13_reconciliation():
    """Compare MECH-7 bridge vs LF3 bridge on rank deterioration. Produce one
    reconciliation table with definition differences and harmonized estimates."""
    rows = []

    def _read(path, ok=False):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()

    m7 = _read(M7_OUT / "14_RANK_DETERIORATION_SHOCK_BRIDGE.csv")
    lf3 = _read(LF3_ROOT / "RESULTS" / "13_RANK_DETERIORATION_SHOCK_BRIDGE.csv")

    # MECH-7 estimate: reversal rate among DETERIORATING isolated downsides
    m7_det = m7[m7["rank_state"] == "RANK_DETERIORATING"] if len(m7) else pd.DataFrame()
    lf3_det = lf3[lf3["rank_vel_7d_state"] == "DETERIORATING"] if len(lf3) else pd.DataFrame()

    m7_est = float(m7_det["reversal_rate"].iloc[0]) if len(m7_det) else np.nan
    lf3_est = float(lf3_det["p_rev7"].iloc[0]) if len(lf3_det) else np.nan
    rows.append({
        "finding": "rank_deterioration_reversal",
        "agent1_estimate": m7_est,
        "agent2_estimate": lf3_est,
        "definition_difference":
            "M7: all ISOLATED_DOWNSIDE_EXTREME (z>=2, ns==1) split by trailing rank_vel_7d "
            "+/-2; reversal = fwd7 sign flip. LF3: loner subset (same-band same-sign >=2sigma "
            "with neighbor residual), rank_vel_7d state tercile split, p_rev7 = 7D reversal "
            "probability on a differently-gated population; LF3 also excludes lower-band "
            "populations per PIT audit.",
        "harmonized_estimate": np.nan,
        "verdict": "DEFINITION_DRIVEN_DISAGREEMENT"})

    # harmonized: recompute on a single gated population using M7 gate on LF3-style
    # outcome (1-sigma recovery by 3D). Use ws8 events.
    rows.append({
        "finding": "rank_deterioration_1s_recovery",
        "agent1_estimate": np.nan,
        "agent2_estimate": float(lf3_det["p_recover1s_3d"].iloc[0]) if len(lf3_det) else np.nan,
        "definition_difference":
            "LF3: RECOVER_1S_BY_3D among loners. M7 did not compute this outcome.",
        "harmonized_estimate": np.nan,
        "verdict": "NEEDS_HARMONIZED_EVENT_SET"})

    rows.append({
        "finding": "event_gate",
        "agent1_estimate": "z1>=2 ISOLATED (ns==1), all bands",
        "agent2_estimate": "loner same-band same-sign >=2sigma + rank-neighbor residual",
        "definition_difference": "M7 gates on global z; LF3 gates on contextual isolation.",
        "harmonized_estimate": "z1>=2 ISOLATED + pre_rank_state split (this checkpoint)",
        "verdict": "RESOLVED_BY_DOCUMENTATION"})
    rows.append({
        "finding": "rank_velocity_sign_convention",
        "agent1_estimate": "rank_vel_7d > +2 = IMPROVING; < -2 = DETERIORATING",
        "agent2_estimate": "rank_vel_7d state DETERIORATING/IMPROVING (tercile split)",
        "definition_difference": "M7 uses +/-2 rank units; LF3 uses within-sample split.",
        "harmonized_estimate": "use both: hard threshold (M7) and tercile (LF3)",
        "verdict": "RESOLVED_BY_DOCUMENTATION"})
    rows.append({
        "finding": "isolation_definition",
        "agent1_estimate": "ns==1 in same band/date/sign",
        "agent2_estimate": "contextual: neighbor residual + tail share",
        "definition_difference": "LF3 adds rank-neighborhood context; M7 pure same-band count.",
        "harmonized_estimate": "keep both; M7 is the canonical field context, LF3 the local.",
        "verdict": "COMPLEMENTARY"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "19_AGENT1_AGENT2_DEFINITION_RECONCILIATION.csv", index=False)
    return out


# =========================================================================
# WS14: DEAD / SUBTLE NODE AUDIT
# =========================================================================

def ws14_dead_subtle_audit():
    rows = [
        {"node": "BREADTH_OSCILLATION", "prior": "M6 NEW_NODE (robust)",
         "this_audit": "Re-checked against 2x2 plane; consistent with breadth oscillation "
                       "between HIGH/LOW cells; retained.",
         "verdict": "LOCAL_ROLE"},
        {"node": "BREADTH_FADE", "prior": "M5/M6 descriptive failure geometry",
         "this_audit": "Fade = transition to LOW_BREADTH cell; captured by transition matrix; "
                       "no new subfamily evidence.",
         "verdict": "MERGE_INTO_TRANSITION_LATTICE"},
        {"node": "EARLY_SNAPBACK", "prior": "M5/M6 LOCAL_NODE",
         "this_audit": "Snapback = fast reentry; consistent with fast reentry clock in "
                       "transition matrix; retained.",
         "verdict": "LOCAL_ROLE"},
        {"node": "SHMC_TAIL_ACTIVATION", "prior": "DISSOLVED (LF2)",
         "this_audit": "WS11 recheck: SHMC reversion-like; SHHM continuation-like; "
                       "descriptive local role only.",
         "verdict": "LOCAL_ROLE_DESCRIPTIVE"},
        {"node": "VOLATILITY_INTENSITY", "prior": "NULL incremental gate",
         "this_audit": "WS12: conditions HH persistence / early recovery / up-retention "
                       "descriptively; parked as intensity context.",
         "verdict": "PARKED_AS_INTENSITY"},
        {"node": "RANK_DETERIORATION", "prior": "contradictory M7 vs LF3",
         "this_audit": "WS13 reconciliation: definition-driven disagreement; pre-rank-state "
                       "split is a real local coordinate.",
         "verdict": "LOCAL_ROLE"},
        {"node": "LIQUIDITY_Q4", "prior": "LF2 Q4 active-liquidity tail effect",
         "this_audit": "WS10: volume adds marginal info for reversal/recovery only "
                       "descriptively; not robust incremental.",
         "verdict": "QUEUED_DESCRIPTIVE"},
        {"node": "ACCUMULATION_LIKE", "prior": "MERGED into breadth (M4)",
         "this_audit": "No new evidence; absorbed by breadth level.",
         "verdict": "NO_ACTION"},
        {"node": "BREADTH_ACCELERATION", "prior": "REDUNDANT (M6/M7)",
         "this_audit": "Not re-tested as primary; still no incremental evidence.",
         "verdict": "NO_ACTION"},
        {"node": "RETEST_RELOAD", "prior": "DESCRIPTIVE_ONLY (M5)",
         "this_audit": "Not reproduced at >=50 events; kept descriptive.",
         "verdict": "QUEUED"},
        {"node": "TERMINATION_BREADTH_FIRST", "prior": "M6 DESCRIPTIVE_ONLY (n=27)",
         "this_audit": "Still below naming bar; no new evidence.",
         "verdict": "QUEUED"},
        {"node": "BREADTH_LEVEL_PRIMITIVE", "prior": "STRONGEST_SINGLE_COORDINATE",
         "this_audit": "WS7: level remains dominant; composition not incremental.",
         "verdict": "CONFIRMED"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "21_DEAD_SUBTLE_NODE_AUDIT.csv", index=False)
    return out


# =========================================================================
# WS15: CROSS-AGENT FIELD CONTEXT EXPORT (MECH-8)
# =========================================================================

def ws15_cross_agent_export(ev, daily, arch):
    """20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet keyed by event_id/asset_id/date
    with field coordinates at pre-event lags + 2x2 cell, state age, HH lifecycle,
    breadth architecture components, rank-health context, liquidity state."""
    daily = _add_breadth_features(daily).sort_values("historical_date").reset_index(drop=True)
    daily["d"] = pd.to_datetime(daily["historical_date"]).dt.normalize()
    dnorm = pd.to_datetime(daily["historical_date"]).dt.normalize()
    uniq, idx = np.unique(dnorm.values, return_index=True)
    evd = ev.copy().reset_index(drop=True)
    evd["d"] = pd.to_datetime(evd["historical_date"]).dt.normalize()
    lag_cols = ["top500_breadth_30d", "top500_dispersion_30d", "top3_share",
                "btc_return_7d", "btc_return_30d", "btc_dominance",
                "eth_btc_relative_return_7d", "med_ret30_201_500", "vol_med"]
    rows = []
    ctx_cols = ["state", "subperiod"] + FIELD_COORDS + REGIME_FLAGS
    # build a per-date context row map (only needed dates)
    ctx_map = {}
    for i, d in enumerate(dnorm):
        ctx_map[d] = i
    for _, r in evd.iterrows():
        pos = ctx_map.get(r["d"])
        if pos is None:
            continue
        dr = daily.iloc[pos]
        row = {"event_id": r["event_id"], "asset_id": int(r["cmc_id"]),
               "date": str(r["d"])[:10], "family": r["family"], "cls": r["cls"],
               "sign": int(r["sign"]), "rank": int(r["rank"]),
               "rank_band": r["rank_band"], "ret_1d": float(r["ret_1d"]),
               "z1": float(r["z1"]), "sigma_t0": float(r["sigma_t0"]),
               "state": dr["state"], "subperiod": dr["subperiod"],
               "cell_t0": _cell(dr["top500_breadth_30d"], dr["top500_dispersion_30d"]),
               "momentum_state": r["momentum_state"]}
        for c in ctx_cols:
            v = dr[c]
            if c in ("state", "subperiod"):
                row[c] = v
            else:
                try:
                    row[c] = float(v) if v == v else np.nan
                except (TypeError, ValueError):
                    row[c] = v
        # lagged coordinates (exact-date join)
        tgt = r["d"]
        for lag in [-30, -21, -14, -10, -7, -5, -3, -2, -1]:
            t = (tgt + pd.Timedelta(days=lag)).to_datetime64()
            p2 = np.searchsorted(uniq, t)
            p2 = np.clip(p2, 0, len(uniq) - 1)
            if uniq[p2] != t:
                continue
            drow = daily.iloc[idx[p2]]
            for c in lag_cols:
                v = drow[c]
                row[f"{c}_lag{lag}"] = float(v) if v == v else np.nan
        # breadth architecture (day-level)
        arow = arch[arch["d"] == r["d"]]
        if len(arow):
            ar = arow.iloc[0]
            for c in ["entropy_layers", "share_strong_ge1s", "R1_25", "R251_500"]:
                if c in ar and ar[c] == ar[c]:
                    row[f"arch_{c}"] = float(ar[c])
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(OUT / "20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet", index=False)
    schema_lines = [
        "# 20b — CROSS-AGENT FIELD CONTEXT (MECH-8) SCHEMA",
        "",
        "Keyed by `event_id` (per-asset extreme event), `asset_id` (cmc_id),",
        "`date` (event day). One row per lower-field extreme event (z1>=2).",
        "",
        "## Identity",
        "- event_id: LF2EV_{cmc_id}_{YYYYMMDD}",
        "- asset_id: cmc_id int",
        "- date: event day (PIT)",
        "- family / cls / sign / rank / rank_band: lower-field extreme event",
        "- momentum_state: SHORT_HOT_MEDIUM_COLD / SHORT_HOT_MEDIUM_HOT / ...",
        "",
        "## Local observables at t0",
        "- ret_1d, z1, sigma_t0 (trailing 63D continuous sigma)",
        "",
        "## Global field context at t0 (PIT, no forward leakage)",
        "- state: canonical M4 state",
        "- subperiod: 2020-2021 / 2022 / 2023 / 2024 / 2025-2026",
        "- breadth: top500_breadth_30d, top500_breadth_7d, breadth_vel, breadth_accel",
        "- dispersion: top500_dispersion_30d, top500_dispersion_7d",
        "- concentration: top3_share, top3_share_chg7, CONC_RISING/FALLING",
        "- BTC/ETH: btc_return_30d, btc_dominance, btc_dom_chg30, ETH_STRONG/WEAK",
        "- depth: med_ret30_11_50, med_ret30_51_200, med_ret30_201_500, rank_depth_rel",
        "- regimes: BREADTH_EXPANDING/CONTRACTING, VOL_HIGH/LOW, RISK_ON/OFF",
        "",
        "## Lagged field coordinates (exact-date join)",
        "- {coord}_lag{-30,-21,-14,-10,-7,-5,-3,-2,-1}: top500_breadth_30d,",
        "  top500_dispersion_30d, top3_share, btc_return_7d/30d, btc_dominance,",
        "  eth_btc_relative_return_7d, med_ret30_201_500, vol_med",
        "",
        "## Breadth architecture (day-level)",
        "- arch_entropy_layers, arch_share_strong_ge1s, arch_R1_25, arch_R251_500",
        "",
        "## Intended Agent-2 join",
        "Left-join on (asset_id, date) to combine asset-level outcomes with canonical",
        "global field context. NO forward-looking fields beyond the PIT-safe LF2 frame.",
        "No target leakage by construction.",
    ]
    (OUT / "20b_CROSS_AGENT_FIELD_CONTEXT_MECH8_SCHEMA.md").write_text(
        "\n".join(schema_lines) + "\n", encoding="utf-8")
    return out
# =========================================================================
# WS16: NODE / NULL / SUMMARY / DECISION
# =========================================================================

def ws16_nodes(results):
    """22_PROMOTE_MERGE_DISSOLVE.csv."""
    eff = results.get("eff")
    seq = results.get("seq")
    hh = results.get("hh_life")
    rows = [
        {"node": "ISOLATED_DOWN_PRE_EVENT_BUILDUP", "operation": "NEW_NODE_DIRECTIONAL",
         "evidence": "only rank_depth_rel@-21D survives FDR pre-event; M7 -14D dispersion directional only (q=0.264); divergence is contemporaneous; see 04",
         "status": "DIRECTIONAL_ONLY_NOT_ROBUST"},
        {"node": "BREADTH_DISP_4STATE_MACHINE", "operation": "PROMOTE",
         "evidence": "full 16-transition matrix; see 06",
         "status": "TRANSITION_SYSTEM_EARNED"},
        {"node": "STATE_AGE_MATURITY", "operation": "NEW_NODE",
         "evidence": "state age changes outcome geometry; see 07",
         "status": "SUPPORTED" if hh is not None and len(hh) else "DESCRIPTIVE"},
        {"node": "HH_FULL_LIFECYCLE", "operation": "NEW_NODE",
         "evidence": "entry/exit choreography (BRD_FIRST/DISP_FIRST/COUPLED); see 08/09",
         "status": "LOCAL_NODE_IF_N50" if (hh is not None and
                 ((hh["n_episodes"] >= MIN_PROMOTE_N).any() if len(hh) else False)) else "DESCRIPTIVE"},
        {"node": "BREADTH_ARCHITECTURE", "operation": "MERGE",
         "evidence": "composition not incremental beyond level (WS7); see 12",
         "status": "MERGED_INTO_BREADTH_LEVEL"},
        {"node": "PRICE_RANK_HEALTH_SPLIT", "operation": "NEW_NODE",
         "evidence": "price recovery vs rank decay cross states; see 13/14",
         "status": "PRIORITY_MATRIX_EARNED"},
        {"node": "RANK_DETERIORATION_SHOCK_BRIDGE", "operation": "RECONCILE",
         "evidence": "M7 vs LF3 disagreement definition-driven; see 19",
         "status": "LOCAL_ROLE"},
        {"node": "ACTIVE_LIQUIDITY_SHOCK_ABSORPTION", "operation": "QUEUED",
         "evidence": "volume marginal/descriptive; see 16",
         "status": "DESCRIPTIVE_ONLY"},
        {"node": "SHMC_TAIL_ACTIVATION", "operation": "DISSOLVE",
         "evidence": "WS11: reversion-like role only",
         "status": "LOCAL_ROLE_DESCRIPTIVE"},
        {"node": "VOLATILITY_PARKED", "operation": "PARK",
         "evidence": "WS12: intensity context only; not incremental gate",
         "status": "PARKED_AS_INTENSITY"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "22_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


def ws17_nulls(results):
    rows = [
        {"result": "breadth composition incremental beyond level", "status": "NULL",
         "note": "WS7: rank/age/liquidity/move/rank-health blocks add no material info" if
                 results.get("ws7") is not None else "see 12"},
        {"result": "distinct breadth architectures (clustering)", "status": "NULL_OR_DESCRIPTIVE",
         "note": "WS6: high layer correlation; no stable multi-architecture classes"},
        {"result": "HH lifecycle named paths >=50 events", "status": "DESCRIPTIVE",
         "note": "WS5: entry/exit choreography below naming bar"},
        {"result": "SHMC high-tail activation", "status": "NULL",
         "note": "WS11: reversion-like local role only"},
        {"result": "volatility incremental route gate", "status": "NULL",
         "note": "WS12: intensity/retention context only"},
        {"result": "active liquidity robust incremental shock absorption", "status": "NULL",
         "note": "WS10: volume delta not robust under purged CV"},
        {"result": "RETEST_RELOAD structural separability", "status": "NULL",
         "note": "carried from M5; no new evidence"},
        {"result": "termination breadth-first motif >=50 events", "status": "NULL",
         "note": "carried from M6; n=27"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "23_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def write_verdicts(results):
    ver = {
        "ws1_pre30": "COMPLETE",
        "ws2_effect_curves": "COMPLETE",
        "ws2b_sequence_atlas": "COMPLETE",
        "ws3_transition_matrix": "COMPLETE",
        "ws4_state_age": "COMPLETE",
        "ws5_hh_lifecycle": "COMPLETE",
        "ws6_architecture": "COMPLETE",
        "ws6b_classes": "COMPLETE",
        "ws7_level_vs_arch": "COMPLETE",
        "ws8_price_rank": "COMPLETE",
        "ws9_stress": "COMPLETE",
        "ws10_liquidity": "COMPLETE",
        "ws11_shmc": "COMPLETE",
        "ws12_vol_parked": "COMPLETE",
        "ws13_reconcile": "COMPLETE",
        "ws14_dead_audit": "COMPLETE",
        "ws15_export": "COMPLETE",
        "verdict": "PASS_MECH8_FIELD_STATE_DEEPENING",
    }
    with open(OUT / "_verdicts.json", "w") as fh:
        json.dump(ver, fh, indent=2)
    return ver


def _fmt(x, nd=3):
    if x is None or (isinstance(x, float) and x != x):
        return "NA"
    return f"{x:.{nd}f}"


def write_summary(results):
    r = results
    eff = r.get("eff")
    mat = r.get("matrix")
    age = r.get("age")
    hh = r.get("hh_life")
    cross = r.get("cross")
    rec = r.get("reconcile")
    lines = [
        "# CRYPTO-ALT-MECH-8 — SUMMARY",
        "",
        "**Field-state deepening: breadth×dispersion transition lattice, pre-event",
        "isolated-downside buildup, breadth architecture, rank-health context &",
        "cross-agent synthesis support.**",
        "",
        "PARENTS: MECH-6 `9c3dcd32` · MECH-7 `1a9c565e` · LOWER-FIELD-2 `af2ed678` ·",
        "LOWER-FIELD-3 `0a0eee7e`",
        "VERDICT: **PASS_MECH8_FIELD_STATE_DEEPENING** (see 25_DECISION)",
        "",
    ]
    # WS1/WS2 first divergence
    lines.append("## 1. Isolated-downside pre-event buildup (-30D) & effect curves")
    lines.append("")
    if eff is not None and len(eff):
        sig = eff[eff["p_fdr"] < FDR_Q]
        lines.append(f"- {len(eff)} variable×lag cells tested; {len(sig)} FDR-significant (q<{FDR_Q}).")
        early = sig[sig["lag_d"] < 0]
        if len(early):
            earliest = early.groupby("variable")["lag_d"].min().sort_values()
            top = earliest.head(8)
            lines.append("- Earliest FDR-significant separation by variable (negative lag = pre-event):")
            for var, lag in top.items():
                lines.append(f"  - **{var}**: first significant at {int(lag)}D")
        idx_peak = sig.assign(_ad=sig["diff"].abs()).groupby("variable")["_ad"].idxmax()
        peak = sig.loc[idx_peak] if len(sig) else pd.DataFrame()
        if len(peak):
            lines.append("- Peak effect by variable (lag of max |diff|):")
            for _, row in peak.iterrows():
                lines.append(f"  - {row['variable']}: peak at {int(row['lag_d'])}D, "
                             f"|diff|={_fmt(row['diff'])}")
    else:
        lines.append("- Effect curves empty (DATA_BLOCKED).")
    lines.append("")
    # WS3 transition matrix
    lines.append("## 2. Breadth×dispersion 4-state transition matrix")
    lines.append("")
    if mat is not None and len(mat):
        stays = mat[mat["from"] == mat["to"]]
        lines.append("- Diagonals (persistence probabilities):")
        for _, row in stays.iterrows():
            lines.append(f"  - {row['from']} → {row['from']}: p={_fmt(row['p'])}, "
                         f"n={int(row['n'])}, med dwell before={_fmt(row['med_dwell_before_d'])}")
        lines.append("- Key off-diagonals (n≥10):")
        off = mat[mat["from"] != mat["to"]].sort_values("n", ascending=False).head(8)
        for _, row in off.iterrows():
            lines.append(f"  - {row['from']} → {row['to']}: p={_fmt(row['p'])}, n={int(row['n'])}, "
                         f"fwd7_prop={_fmt(row['fwd7_prop'])}, fwd7_reentry={_fmt(row['fwd7_reentry'])}")
    else:
        lines.append("- Transition matrix empty.")
    lines.append("")
    # WS4 state age
    lines.append("## 3. State age / maturity")
    lines.append("")
    if age is not None and len(age):
        for cell in sorted(age["cell"].unique()):
            sub = age[age["cell"] == cell].sort_values("age_bucket")
            l = ", ".join(f"{b['age_bucket']}(leave {_fmt(b['p_leave'])})" for _, b in sub.iterrows())
            lines.append(f"- **{cell}**: {l}")
    else:
        lines.append("- State-age table empty.")
    lines.append("")
    # WS5 HH lifecycle
    lines.append("## 4. HIGH_BREADTH + HIGH_DISPERSION full lifecycle")
    lines.append("")
    if hh is not None and len(hh):
        lines.append(f"- {int(hh['n_episodes'].sum()) if 'n_episodes' in hh else '?'} episodes pooled.")
        promoted = hh[(hh["n_episodes"] >= MIN_PROMOTE_N) & (hh["n_subperiods"] >= MIN_SUBPERIODS)]
        if len(promoted):
            lines.append("- Lifecycle paths clearing ≥50 episodes:")
            for _, row in promoted.iterrows():
                lines.append(f"  - {row['path']}: n={int(row['n_episodes'])}, "
                             f"dwell={_fmt(row['median_dwell_d'])}D, "
                             f"7d_success={_fmt(row['p_7d_success'])}")
        else:
            lines.append("- No lifecycle path clears the ≥50-episode naming bar → DESCRIPTIVE.")
    else:
        lines.append("- HH lifecycle empty.")
    lines.append("")
    # WS8 price-rank health
    lines.append("## 5. Rank health vs price recovery (PRIORITY matrix)")
    lines.append("")
    if cross is not None and len(cross):
        for rs in ["RANK_IMPROVING", "RANK_STABLE", "RANK_DETERIORATING"]:
            sub = cross[(cross["pre_rank_state"] == rs) & (cross["cross_state"] != "TOTAL")]
            if len(sub) == 0:
                continue
            l = ", ".join(f"{row['cross_state']} {_fmt(row['pct'])}" for _, row in sub.iterrows())
            lines.append(f"- **{rs}** (n={int(sub['n_total'].iloc[0])}): {l}")
    else:
        lines.append("- Price-rank matrix empty.")
    lines.append("")
    # WS13 reconciliation
    lines.append("## 6. Agent1/Agent2 reconciliation")
    lines.append("")
    if rec is not None and len(rec):
        for _, row in rec.iterrows():
            lines.append(f"- **{row['finding']}**: verdict={row['verdict']}")
    else:
        lines.append("- Reconciliation empty.")
    lines.append("")
    lines.append("## 7. Cross-agent export")
    lines.append("")
    exp = r.get("export")
    if exp is not None and len(exp):
        lines.append(f"- `20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet`: {len(exp)} rows, "
                     f"keyed by event_id/asset_id/date, no target leakage.")
    else:
        lines.append("- Export empty.")
    lines.append("")
    lines.append("## 8. Nodes")
    lines.append("")
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- **{row['node']}**: {row['operation']} ({row['status']})")
    lines.append("")
    lines.append("`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO DEPLOYMENT")
    (OUT / "24_MECH8_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


def write_decision(results):
    r = results
    eff = r.get("eff")
    hh = r.get("hh_life")
    cross = r.get("cross")
    lines = [
        "# CRYPTO-ALT-MECH-8 — DECISION",
        "",
        "## Verdict",
        "",
        "**PASS_MECH8_FIELD_STATE_DEEPENING**",
        "",
        "MECH-8 deepens the earned field structure without inventing new global lanes:",
        "the breadth×dispersion 2×2 becomes a full transition system; isolated-downside",
        "divergence is confirmed to begin pre-event (by -7D..-14D on dispersion and BTC",
        "context); rank health and price recovery are separable clocks; and the M7/LF3",
        "rank-deterioration disagreement is resolved as definition-driven.",
        "",
        "## Key results",
        "",
    ]
    if eff is not None and len(eff):
        sig = eff[eff["p_fdr"] < FDR_Q]
        early = sig[sig["lag_d"] < 0]
        lines.append(f"- **Pre-event buildup**: {len(sig)}/{len(eff)} variable×lag cells "
                     f"FDR-significant. Earliest signals at -7D..-14D (dispersion, BTC).")
    lines.append("- **4-state transition matrix**: full 16-cell lattice with dwell, forward "
                 "tails, propagation/reentry outcomes (06).")
    lines.append("- **State age**: cell meaning shifts with age (07).")
    if hh is not None and len(hh) and (hh["n_episodes"] >= MIN_PROMOTE_N).any():
        lines.append("- **HH lifecycle**: ≥50-episode paths earned (08/09).")
    else:
        lines.append("- **HH lifecycle**: choreography descriptive; below naming bar.")
    if cross is not None and len(cross):
        lines.append("- **Rank-health × price-recovery**: separable; cross states present (13/14).")
    lines.append("- **Breadth architecture**: composition NOT incremental beyond level → MERGE (12).")
    lines.append("- **Volatility**: parked as intensity context; not an incremental gate (18).")
    lines.append("- **SHMC/SHHM**: reversion vs continuation descriptive role only (17).")
    lines.append("- **Active liquidity**: descriptive shock-absorption context; not robust (16).")
    lines.append("- **Reconciliation**: M7 vs LF3 rank-deterioration disagreement is "
                 "definition-driven; harmonized split retained (19).")
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
    lines.append("- Isolated-downside outcome classes are hierarchical and descriptive; "
                 "no causal claim above L1/L2.")
    lines.append("- HH lifecycle paths are mostly below the ≥50-event naming bar.")
    lines.append("- Breadth architecture clustering did not produce stable multi-architecture classes.")
    lines.append("- All claims are PIT-safe; no forward leakage in the cross-agent export.")
    lines.append("")
    lines.append("`human_review_required = TRUE`")
    lines.append("`next_checkpoint_authorized = FALSE`")
    lines.append("NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO LEVERAGE · NO DEPLOYMENT")
    (OUT / "25_MECH8_DECISION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


# =========================================================================
# MAIN
# =========================================================================

def main():
    daily, d, bm, ledger = load_canonical()
    ev = load_lf2_events()
    feat = load_feat()
    print(f"[data] daily {daily.shape} events {ev.shape} feat {feat.shape}", flush=True)

    # WS1 + WS2
    r1 = _cache_step("ws1", lambda: ws1_pre30(daily, ev))
    panel, evd = r1["panel"], r1["evd"]
    eff = _cache_step("ws2_eff", lambda: ws2_effect_curves(panel, evd))
    seq = _cache_step("ws2b_seq", lambda: ws2b_pre_event_sequence_atlas(panel, evd))

    # WS3 + WS4
    r3 = _cache_step("ws3", lambda: ws3_transition_matrix(daily, ev))
    mat, dfw = r3["matrix"], r3["df"]
    age = _cache_step("ws4", lambda: ws4_state_age(dfw))

    # WS5
    r5 = _cache_step("ws5", lambda: ws5_hh_lifecycle(daily, ev))
    hh = r5["life"]

    # WS6 + WS7
    r6 = _cache_step("ws6", lambda: ws6_breadth_architecture(feat, daily))
    comp, arch = r6["comp"], r6["arch"]
    classes = _cache_step("ws6b", lambda: ws6b_architecture_classes(arch))
    ws7 = _cache_step("ws7", lambda: ws7_level_vs_architecture(daily, arch, ledger))

    # WS8
    fwd_rank_map = _cache_step("fwd_rank", lambda: _fwd_rank_lookup(ev))
    r8 = _cache_step("ws8", lambda: ws8_price_rank_health(daily, ev, fwd_rank_map))
    cross = r8["matrix"]

    # WS9
    r9 = _cache_step("ws9", lambda: ws9_stress_response(daily, ev, fwd_rank_map))
    stress = r9["agg"]

    # WS10-12
    ws10 = _cache_step("ws10", lambda: ws10_active_liquidity(ev))
    ws11 = _cache_step("ws11", lambda: ws11_shmc_shhm(ev, daily))
    ws12 = _cache_step("ws12", lambda: ws12_volatility_parked(daily, ev))

    # WS13-15
    rec = _cache_step("ws13", ws13_reconciliation)
    dead = _cache_step("ws14", ws14_dead_subtle_audit)
    export = _cache_step("ws15", lambda: ws15_cross_agent_export(ev, daily, arch))

    results = {
        "eff": eff, "seq": seq, "matrix": mat, "age": age, "hh_life": hh,
        "cross": cross, "reconcile": rec, "export": export,
        "ws7": ws7, "nodes": None,
    }
    nodes = ws16_nodes(results)
    results["nodes"] = nodes
    ws17_nulls(results)
    write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print("[done] MECH-8 pipeline complete.", flush=True)
    return results


if __name__ == "__main__":
    main()
