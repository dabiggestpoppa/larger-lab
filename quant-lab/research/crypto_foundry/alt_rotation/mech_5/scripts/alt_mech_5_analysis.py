#!/usr/bin/env python
"""ALT_MECH_5 - Failure Anatomy, Rotation Survival, Temporal Divergence & Termination Precursors.

Terrain research ONLY (AGENT 1 - MAIN FIELD CARTOGRAPHER). No PnL, no strategy,
no optimization, no ML predictors, no sizing, no deployment.
"""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums, chi2_contingency, fisher_exact, kruskal
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260901
PERM_N = 500
BOOT_N = 500

ROOT = Path(__file__).resolve().parents[1]  # mech_5/
M4_ROOT = ROOT.parent / "mech_4"
M4_SCRIPTS = M4_ROOT / "scripts"
for p in ("mech_1", "mech_2", "mech_3"):
    sys.path.insert(0, str(ROOT.parent.parent / p / "scripts"))
sys.path.insert(0, str(M4_SCRIPTS))
import alt_mech_4_analysis as M4

OUT = ROOT
M4_OUT = M4_ROOT

BANDS = M4.BANDS
ALT_FAMILY = M4.ALT_FAMILY
PROP_FAMILY = M4.PROP_FAMILY
CONC_STATE = M4.CONC_STATE
STATE_FEATURES = M4.STATE_FEATURES

# map MECH-4 short feature names -> actual daily frame columns
STATE_FEATURE_MAP = {
    "btc_ret30": "btc_return_30d", "btc_ret7": "btc_return_7d",
    "top3_share": "top3_share", "top3_share_chg7": "top3_share_chg7",
    "breadth30": "top500_breadth_30d", "disp30": "top500_dispersion_30d",
    "sc_chg30": "stablecoin_change_30d", "eth_rel30": "eth_btc_relative_return_30d",
    "vol_med": "vol_med", "chain_tvl_med_chg7": "chain_tvl_med_chg7",
}
STATE_FEATURE_DAILY = [STATE_FEATURE_MAP[f] for f in STATE_FEATURES]

# broad outcome families
FAILURE_LABELS = {"BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE"}
SUCCESS_LABELS = {"BROAD_RISK_EXPANSION"} | ALT_FAMILY
# first-move classes from 33_FIRST_MOVE_TRUE_DELIVERY.csv
FM_CLASSES = ["IMMEDIATE_DELIVERY", "RETEST_RELOAD", "FAILED_IGNITION", "FULL_FAILURE"]

HORIZONS = [0, 1, 2, 3, 5, 7, 10, 14, 21, 30]

# divergence variables (daily-frame columns or computed)
DIVERGE_VARS = [
    "top500_breadth_30d", "top500_breadth_7d",
    "top500_dispersion_30d", "top500_dispersion_7d",
    "btc_return_7d", "btc_return_30d", "btc_return_1d",
    "eth_btc_relative_return_7d", "eth_btc_relative_return_30d",
    "vol_med", "top3_share", "top3_share_chg7",
    "med_ret30_11_50", "med_ret30_51_200", "med_ret30_201_500",
    "total_mcap_chg30", "btc_dom_chg30",
    "stablecoin_change_30d", "chain_tvl_med_chg7",
]


def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    print(f"[run] {name} ...")
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


def load_data():
    """Load MECH-4 cached data + rebuild what we need."""
    inp, tl = M4._cache_step("inputs", M4.load)
    daily, d, bm = M4._cache_step("daily", lambda: M4.build_daily(inp))
    m, top = M4._cache_step("chainframe", lambda: M4.build_chainframe(inp))
    rc = M4._cache_step("reconcile", lambda: M4.ws_reconcile(daily))
    entries, exits = rc["recount"]["entries"], rc["recount"]["exits"]
    rA = M4._cache_step("A", lambda: M4.ws_a(daily, entries, exits))
    ledger = rA["ledger"]
    X, feat_df = M4._cache_step("feats", lambda: M4._exit_features(ledger, daily))
    return daily, ledger, entries, exits, m, top, bm, X, feat_df


# =========================================================================
# WS1: FIRST-DIVERGENCE ANALYSIS
# =========================================================================

def _event_series_at(daily, exit_idx, var, horizons=HORIZONS):
    """Return value of `var` at exit_idx + h for each h in horizons."""
    n = len(daily)
    vals = {}
    for h in horizons:
        j = exit_idx + h
        if 0 <= j < n:
            v = daily[var].iloc[j]
            vals[h] = float(v) if v == v else np.nan
        else:
            vals[h] = np.nan
    return vals


def ws1_first_divergence(daily, ledger):
    """First-divergence panel: compare success vs failure at each horizon."""
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    # label success/failure
    ledger = ledger.copy()
    ledger["is_success"] = ledger.first_destination.isin(SUCCESS_LABELS)
    ledger["is_failure"] = ledger.first_destination.isin(FAILURE_LABELS)
    # exclude CAPITAL_EXIT, STABLECOIN_PARKING from primary comparison (n=2)
    primary = ledger[ledger.first_destination.isin(
        list(SUCCESS_LABELS | FAILURE_LABELS))].copy()

    rows = []
    for _, r in primary.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        row = {"event_id": r.event_id, "exit_date": r.exit_date,
               "first_destination": r.first_destination,
               "is_success": int(r.is_success)}
        for var in DIVERGE_VARS:
            if var not in daily.columns:
                continue
            vals = _event_series_at(daily, i, var)
            for h, v in vals.items():
                row[f"{var}_tp{h}"] = v
        rows.append(row)
    panel = pd.DataFrame(rows)
    panel.to_parquet(OUT / "03_FIRST_DIVERGENCE_PANEL.parquet", index=False)

    # summary: rank-sum test at each horizon for each variable
    summary_rows = []
    for var in DIVERGE_VARS:
        if var not in daily.columns:
            continue
        for h in HORIZONS:
            col = f"{var}_tp{h}"
            if col not in panel.columns:
                continue
            suc = panel.loc[panel.is_success == 1, col].dropna()
            fail = panel.loc[panel.is_success == 0, col].dropna()
            if len(suc) < 5 or len(fail) < 5:
                continue
            stat, p = ranksums(suc, fail)
            # effect size: Cliff's delta
            n1, n2 = len(suc), len(fail)
            m, r = ranksums(suc, fail)
            # use rank-biserial r = z / sqrt(N)
            from scipy.stats import norm
            z = norm.ppf(1 - p / 2) * (1 if stat > 0 else -1)
            r_eff = z / np.sqrt(n1 + n2)
            median_suc = float(suc.median())
            median_fail = float(fail.median())
            summary_rows.append({
                "variable": var, "horizon_d": h,
                "n_success": n1, "n_failure": n2,
                "median_success": round(median_suc, 5),
                "median_failure": round(median_fail, 5),
                "delta": round(median_suc - median_fail, 5),
                "rank_biserial_r": round(float(r_eff), 4),
                "p_raw": round(float(p), 6),
            })
    summary = pd.DataFrame(summary_rows)
    if len(summary) == 0:
        summary.to_csv(OUT / "04_FIRST_DIVERGENCE_SUMMARY.csv", index=False)
        return {"panel": panel, "summary": summary}
    # BH-FDR
    from statsmodels.stats.multitest import multipletests
    reject, p_adj, _, _ = multipletests(summary.p_raw.values, method="fdr_bh")
    summary["p_fdr"] = np.round(p_adj, 6)
    summary["significant_fdr"] = reject
    # earliest significant divergence per variable
    sig = summary[summary.significant_fdr].sort_values("variable")
    earliest = sig.groupby("variable").first().reset_index()
    earliest.to_csv(OUT / "04_FIRST_DIVERGENCE_SUMMARY.csv", index=False)
    summary.to_csv(OUT / "04b_FIRST_DIVERGENCE_FULL.csv", index=False)
    return {"panel": panel, "summary": summary, "earliest": earliest}


# =========================================================================
# WS2: SUCCESS vs FAILURE INCREMENTAL MAP
# =========================================================================

def _logloss_safe(y, p):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return float(log_loss(y, p))


def _brier(y, p):
    return float(brier_score_loss(y, p))


def _auc_safe(y, p):
    if len(set(y)) < 2:
        return np.nan
    return float(roc_auc_score(y, p))




def ws2_incremental_map(daily, ledger, feat_df):
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    ledger = ledger.copy()
    ledger["is_success"] = ledger.first_destination.isin(SUCCESS_LABELS).astype(int)
    primary = ledger[ledger.first_destination.isin(
        list(SUCCESS_LABELS | FAILURE_LABELS))].copy()
    feature_groups = [
        ("M0_current_state", STATE_FEATURE_DAILY),
        ("M1_breadth", ["top500_breadth_30d", "top500_breadth_7d",
                        "top500_dispersion_30d", "top500_dispersion_7d"]),
        ("M2_volatility", ["vol_med"]),
        ("M3_rank_participation", ["med_ret30_11_50", "med_ret30_51_200",
                                   "med_ret30_201_500"]),
        ("M4_conc_btc_eth", ["top3_share", "top3_share_chg7",
                             "btc_return_7d", "btc_return_30d",
                             "eth_btc_relative_return_7d"]),
        ("M5_timing", ["state_age_d"]),
        ("M6_chain_sector", ["chain_tvl_med_chg7", "stablecoin_change_30d"]),
    ]
    rows = []
    for _, r in primary.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        row = {"event_id": r.event_id, "is_success": r.is_success}
        for _, vars_ in feature_groups:
            for v in vars_:
                if v in daily.columns:
                    val = daily[v].iloc[i]
                    row[v] = float(val) if val == val else np.nan
                elif v == "state_age_d":
                    row[v] = float(r.state_age_d) if r.state_age_d == r.state_age_d else np.nan
                else:
                    row[v] = np.nan
        rows.append(row)
    df = pd.DataFrame(rows)
    y = df.is_success.values
    results = []
    used_features = []
    for grp_name, vars_ in feature_groups:
        new_feats = [v for v in vars_ if v in df.columns]
        for v in list(new_feats):
            if df[v].notna().sum() < 5:
                new_feats.remove(v)
        used_features.extend(new_feats)
        if not used_features:
            continue
        Xmat = df[used_features].values.copy()
        for j in range(Xmat.shape[1]):
            ii = ~np.isnan(Xmat[:, j])
            if ii.sum() == 0:
                Xmat[:, j] = 0.0
                continue
            med = float(np.median(Xmat[ii, j]))
            Xmat[:, j] = np.where(np.isnan(Xmat[:, j]), med, Xmat[:, j])
        if len(set(y)) < 2:
            continue
        kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        ll_scores, brier_scores, auc_scores = [], [], []
        for tr, te in kf.split(Xmat, y):
            model = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
            model.fit(Xmat[tr], y[tr])
            p = model.predict_proba(Xmat[te])[:, 1]
            ll_scores.append(_logloss_safe(y[te], p))
            brier_scores.append(_brier(y[te], p))
            auc_scores.append(_auc_safe(y[te], p))
        mean_ll = np.mean(ll_scores)
        mean_brier = np.mean(brier_scores)
        mean_auc = np.nanmean(auc_scores)
        full_model = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
        full_model.fit(Xmat, y)
        p_full = full_model.predict_proba(Xmat)[:, 1]
        base_ll = _logloss_safe(y, p_full)
        rng = np.random.RandomState(SEED)
        perm_lls = []
        for _ in range(PERM_N):
            yp = rng.permutation(y)
            m = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
            m.fit(Xmat, yp)
            pp = m.predict_proba(Xmat)[:, 1]
            perm_lls.append(_logloss_safe(yp, pp))
        perm_p = (np.sum(np.array(perm_lls) <= base_ll) + 1) / (PERM_N + 1)
        results.append({
            "model": grp_name, "n_features": len(used_features),
            "cv_logloss": round(mean_ll, 5), "cv_brier": round(mean_brier, 5),
            "cv_auc": round(mean_auc, 4), "full_logloss": round(base_ll, 5),
            "perm_p": round(perm_p, 4),
        })
    df_results = pd.DataFrame(results)
    df_results["delta_logloss"] = np.nan
    df_results["delta_brier"] = np.nan
    df_results["delta_auc"] = np.nan
    for i in range(1, len(df_results)):
        df_results.loc[i, "delta_logloss"] = round(
            df_results.cv_logloss.iloc[i - 1] - df_results.cv_logloss.iloc[i], 5)
        df_results.loc[i, "delta_brier"] = round(
            df_results.cv_brier.iloc[i - 1] - df_results.cv_brier.iloc[i], 5)
        df_results.loc[i, "delta_auc"] = round(
            df_results.cv_auc.iloc[i] - df_results.cv_auc.iloc[i - 1], 4)
    df_results.to_csv(OUT / "05_SUCCESS_FAILURE_INCREMENTAL_MAP.csv", index=False)
    return {"models": df_results}


def ws3_retest_reload(daily, ledger):
    fm = pd.read_csv(M4_OUT / "33_FIRST_MOVE_TRUE_DELIVERY.csv")
    ledger = ledger.copy()
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    rr_events = set(fm[fm.classification == "RETEST_RELOAD"].event_id.tolist())
    fi_events = set(fm[fm.classification == "FAILED_IGNITION"].event_id.tolist())
    compare_vars = [
        "top500_breadth_30d", "top500_breadth_7d",
        "top500_dispersion_30d", "vol_med",
        "top3_share_chg7", "eth_btc_relative_return_7d",
        "btc_return_7d", "med_ret30_51_200",
    ]
    rows = []
    for _, r in ledger.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        cls = "RETEST_RELOAD" if r.event_id in rr_events else \
              "FAILED_IGNITION" if r.event_id in fi_events else None
        if cls is None:
            continue
        row = {"event_id": r.event_id, "class": cls}
        for v in compare_vars:
            if v not in daily.columns:
                continue
            vals_r = []
            for h in range(1, 6):
                j = i + h
                if 0 <= j < len(daily):
                    val = daily[v].iloc[j]
                    if val == val:
                        vals_r.append(float(val))
            row[f"{v}_retrace_median"] = round(float(np.median(vals_r)), 5) if vals_r else np.nan
            j5 = i + 5
            if 0 <= j5 < len(daily):
                v5 = daily[v].iloc[j5]
                v0 = daily[v].iloc[i]
                if v5 == v5 and v0 == v0 and abs(v0) > 1e-10:
                    row[f"{v}_retention_5d"] = round(float(v5 / v0), 4)
                else:
                    row[f"{v}_retention_5d"] = np.nan
            else:
                row[f"{v}_retention_5d"] = np.nan
        rows.append(row)
    anatomy = pd.DataFrame(rows)
    anatomy.to_csv(OUT / "06_RETEST_RELOAD_INTERNAL_ANATOMY.csv", index=False)
    summary_rows = []
    for v in compare_vars:
        col = f"{v}_retention_5d"
        if col not in anatomy.columns:
            continue
        rr = anatomy.loc[anatomy["class"] == "RETEST_RELOAD", col].dropna()
        fi = anatomy.loc[anatomy["class"] == "FAILED_IGNITION", col].dropna()
        if len(rr) < 3 or len(fi) < 3:
            continue
        stat, p = ranksums(rr, fi)
        summary_rows.append({
            "variable": v, "metric": "retention_5d",
            "n_rr": len(rr), "n_fi": len(fi),
            "median_rr": round(float(rr.median()), 4),
            "median_fi": round(float(fi.median()), 4),
            "p_raw": round(float(p), 6),
        })
    comp = pd.DataFrame(summary_rows)
    if len(comp) > 0:
        reject, p_adj, _, _ = multipletests(comp.p_raw.values, method="fdr_bh")
        comp["p_fdr"] = np.round(p_adj, 6)
    comp.to_csv(OUT / "07_RETEST_RELOAD_VS_FAILED_IGNITION.csv", index=False)
    return {"anatomy": anatomy, "comparison": comp, "n_rr": len(rr_events), "n_fi": len(fi_events)}


def ws4_two_clock(daily, ledger):
    ledger = ledger.copy()
    ledger["is_success"] = ledger.first_destination.isin(SUCCESS_LABELS).astype(int)
    ledger["is_reentry"] = (ledger.first_destination == "BTC_CONCENTRATION").astype(int)
    horizons = [1, 2, 3, 5, 7, 10, 14, 21, 30]
    escape_rows = []
    for h in horizons:
        n = len(ledger)
        reentered = ((ledger.is_reentry == 1) & (ledger.days_to_destination_d <= h)).sum()
        escape_rows.append({"horizon_d": h, "n_total": n, "n_reentered": int(reentered),
                            "p_escape": round(1 - reentered / max(n, 1), 4)})
    escape = pd.DataFrame(escape_rows)
    escape.to_csv(OUT / "08_ESCAPE_HAZARD.csv", index=False)
    succ = ledger[ledger.is_success == 1]
    prop_rows = []
    for h in horizons:
        n = len(succ)
        if n == 0:
            continue
        sustained = (succ.days_to_destination_d <= h).sum()
        prop_rows.append({"horizon_d": h, "n_success": n,
                          "n_sustained_within_h": int(sustained),
                          "p_sustained_within_h": round(sustained / max(n, 1), 4)})
    prop = pd.DataFrame(prop_rows)
    prop.to_csv(OUT / "09_PROPAGATION_HAZARD.csv", index=False)
    fail = ledger[ledger.is_success == 0]
    fail_rows = []
    for h in horizons:
        n = len(fail)
        if n == 0:
            continue
        reentered = ((fail.is_reentry == 1) & (fail.days_to_destination_d <= h)).sum()
        fail_rows.append({"horizon_d": h, "n_failure": n,
                          "n_reentered_within_h": int(reentered),
                          "p_reentry_within_h": round(reentered / max(n, 1), 4)})
    fail_haz = pd.DataFrame(fail_rows)
    fail_haz.to_csv(OUT / "10_FAILURE_HAZARD.csv", index=False)
    window_defs = [(0, 1, "0-1D"), (1, 3, "1-3D"), (3, 7, "3-7D"), (7, 14, "7-14D"), (14, 30, "14-30D")]
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    wrows = []
    for w_lo, w_hi, w_label in window_defs:
        for var in ["top500_breadth_30d", "vol_med", "btc_return_7d"]:
            if var not in daily.columns:
                continue
            s_vals, f_vals = [], []
            for _, r in ledger.iterrows():
                i = date_idx.get(pd.Timestamp(r.exit_date))
                if i is None:
                    continue
                j_start = i + w_lo
                j_end = i + w_hi
                if j_start < 0 or j_end >= len(daily):
                    continue
                v0 = daily[var].iloc[j_start]
                v1 = daily[var].iloc[j_end]
                if v0 == v0 and v1 == v1:
                    delta = float(v1 - v0)
                    if r.first_destination in SUCCESS_LABELS:
                        s_vals.append(delta)
                    elif r.first_destination in FAILURE_LABELS:
                        f_vals.append(delta)
            if len(s_vals) >= 5 and len(f_vals) >= 5:
                stat, p = ranksums(s_vals, f_vals)
                wrows.append({"window": w_label, "variable": var,
                              "n_suc": len(s_vals), "n_fail": len(f_vals),
                              "median_suc": round(np.median(s_vals), 5),
                              "median_fail": round(np.median(f_vals), 5),
                              "p_raw": round(float(p), 6)})
    window_df = pd.DataFrame(wrows)
    if len(window_df) > 0:
        reject, p_adj, _, _ = multipletests(window_df.p_raw.values, method="fdr_bh")
        window_df["p_fdr"] = np.round(p_adj, 6)
    window_df.to_csv(OUT / "11_TEMPORAL_WINDOW_REFINEMENT.csv", index=False)
    return {"escape": escape, "propagation": prop, "failure": fail_haz, "windows": window_df}


def ws5_termination(daily, ledger):
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    succ = ledger[ledger.first_destination.isin(SUCCESS_LABELS)].copy()
    decay_vars = ["top500_breadth_30d", "top500_breadth_7d", "top500_dispersion_30d",
                  "vol_med", "top3_share_chg7", "eth_btc_relative_return_7d",
                  "btc_return_7d", "med_ret30_51_200"]
    rows = []
    for _, r in succ.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        ttd = r.days_to_destination_d
        if ttd != ttd or ttd < 1:
            continue
        term_idx = i + int(ttd)
        row = {"event_id": r.event_id, "exit_date": str(r.exit_date)[:10],
               "first_destination": r.first_destination,
               "days_to_destination": int(ttd)}
        for v in decay_vars:
            if v not in daily.columns:
                continue
            for offset in [-7, -3, 0, 3, 7]:
                j = term_idx + offset
                if 0 <= j < len(daily):
                    val = daily[v].iloc[j]
                    row[f"{v}_term{offset:+d}"] = round(float(val), 5) if val == val else np.nan
                else:
                    row[f"{v}_term{offset:+d}"] = np.nan
            vals_before = []
            for lookback in range(1, 15):
                j = term_idx - lookback
                if 0 <= j < len(daily):
                    val = daily[v].iloc[j]
                    if val == val:
                        vals_before.append((lookback, float(val)))
            if len(vals_before) >= 3:
                vals_before.reverse()
                baseline = vals_before[0][1]
                decline_start = None
                for lb, val in vals_before[1:]:
                    if val < baseline * 0.95:
                        decline_start = lb
                        break
                row[f"{v}_first_decline_days_before_term"] = decline_start
            else:
                row[f"{v}_first_decline_days_before_term"] = np.nan
        rows.append(row)
    panel = pd.DataFrame(rows)
    panel.to_csv(OUT / "12_TERMINATION_MATCHED_CONTROLS.csv", index=False)
    summary_rows = []
    for v in decay_vars:
        col = f"{v}_first_decline_days_before_term"
        if col not in panel.columns:
            continue
        vals = panel[col].dropna()
        n_sig = int((vals <= 7).sum())
        n_total = len(vals)
        if n_total > 0:
            summary_rows.append({
                "variable": v, "n_total": n_total,
                "n_decline_within_7d": n_sig,
                "pct_decline": round(n_sig / n_total, 3),
                "median_decline_start": round(float(vals.median()), 1),
            })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "13_EARLY_DECAY_SEQUENCE.csv", index=False)
    lat_rows = []
    for v in decay_vars:
        col = f"{v}_first_decline_days_before_term"
        if col not in panel.columns:
            continue
        vals = panel[col].dropna()
        if len(vals) > 0:
            lat_rows.append({
                "variable": v, "median_latency_d": round(float(vals.median()), 1),
                "p25_latency_d": round(float(vals.quantile(0.25)), 1),
                "p75_latency_d": round(float(vals.quantile(0.75)), 1),
                "n_observed": len(vals),
            })
    latency = pd.DataFrame(lat_rows)
    latency.to_csv(OUT / "14_SIGNAL_TO_TERMINATION_LATENCY.csv", index=False)
    return {"panel": panel, "summary": summary, "latency": latency}


def ws6_failure_sequences(daily, ledger):
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(daily.historical_date.values)}
    rows = []
    for _, r in ledger.iterrows():
        i = date_idx.get(pd.Timestamp(r.exit_date))
        if i is None:
            continue
        states = {}
        for h in [1, 3, 5, 7, 14, 30]:
            j = i + h
            states[f"state_tp{h}"] = daily.state.iloc[j] if 0 <= j < len(daily) else "OUT_OF_RANGE"
        metrics = {}
        for v in ["top500_breadth_30d", "vol_med", "top3_share_chg7", "btc_return_7d", "med_ret30_51_200"]:
            if v not in daily.columns:
                continue
            for h in [1, 3, 5, 7, 14, 30]:
                j = i + h
                if 0 <= j < len(daily):
                    val = daily[v].iloc[j]
                    metrics[f"{v}_tp{h}"] = round(float(val), 5) if val == val else np.nan
                else:
                    metrics[f"{v}_tp{h}"] = np.nan
        dest = r.first_destination
        motif = "UNCLASSIFIED"
        if dest == "BTC_CONCENTRATION":
            ttd = r.days_to_destination_d
            if ttd == ttd:
                motif = "EARLY_SNAPBACK" if ttd <= 3 else "MID_SNAPBACK" if ttd <= 7 else "LATE_SNAPBACK"
        elif dest == "MIXED_NO_CLEAR_ROUTE":
            b0 = daily["top500_breadth_30d"].iloc[i] if i < len(daily) else np.nan
            b7 = daily["top500_breadth_30d"].iloc[i + 7] if i + 7 < len(daily) else np.nan
            if b0 == b0 and b7 == b7:
                motif = "BREADTH_FADE" if b7 < b0 * 0.9 else "BREADTH_DIVERSITY_NO_ROUTE" if b7 > b0 * 1.1 else "STABLE_NO_ROUTE"
            else:
                motif = "STABLE_NO_ROUTE"
        elif dest in SUCCESS_LABELS:
            motif = "SUCCESS"
        rows.append({"event_id": r.event_id, "exit_date": str(r.exit_date)[:10],
                     "first_destination": dest, "days_to_destination": r.days_to_destination_d,
                     "motif": motif, **states, **metrics})
    seq = pd.DataFrame(rows)
    seq.to_csv(OUT / "15_FAILURE_SEQUENCE_MAP.csv", index=False)
    motif_counts = seq.motif.value_counts().reset_index()
    motif_counts.columns = ["motif", "count"]
    motif_counts["pct"] = round(motif_counts["count"] / len(seq), 3)
    motif_counts.to_csv(OUT / "16_FAILURE_MOTIF_AUDIT.csv", index=False)
    return {"sequences": seq, "motifs": motif_counts}


def ws7_conditional_rescue(daily, ledger):
    conditions = ["BTC_UP", "BTC_DOWN", "VOL_HIGH", "VOL_LOW",
                  "BREADTH_EXPANDING", "BREADTH_CONTRACTING",
                  "ETH_STRONG", "ETH_WEAK", "RISK_ON", "RISK_OFF"]
    rows = []
    for cond in conditions:
        mask = daily[cond].values
        cond_dates = set(daily.historical_date.values[mask])
        sub = ledger[ledger.exit_date.isin(cond_dates)]
        if len(sub) < 10:
            continue
        n_suc = int(sub.first_destination.isin(SUCCESS_LABELS).sum())
        n_total = len(sub)
        p_suc = n_suc / max(n_total, 1)
        n_suc_all = int(ledger.first_destination.isin(SUCCESS_LABELS).sum())
        p_suc_all = n_suc_all / len(ledger)
        table = [[n_suc, n_total - n_suc], [n_suc_all, len(ledger) - n_suc_all]]
        _, p_fisher = fisher_exact(table)
        rows.append({"condition": cond, "n_events": n_total, "n_success": n_suc,
                     "p_success": round(p_suc, 4), "p_success_overall": round(p_suc_all, 4),
                     "p_fisher": round(float(p_fisher), 6)})
    rescue = pd.DataFrame(rows)
    if len(rescue) > 0:
        reject, p_adj, _, _ = multipletests(rescue.p_fisher.values, method="fdr_bh")
        rescue["p_fdr"] = np.round(p_adj, 6)
    rescue.to_csv(OUT / "17_CONDITIONAL_RESCUE_AUDIT.csv", index=False)
    return {"rescue": rescue}


def ws8_causality(w1, w2, w3, w4, w5, w6, w7):
    rows = []
    if w1.get("earliest") is not None and len(w1["earliest"]) > 0:
        for _, r in w1["earliest"].iterrows():
            rows.append({"result": f"first_divergence_{r['variable']}", "workstream": "WS1",
                         "causality_level": "L1_TEMPORAL_ORDERING",
                         "note": f"earliest at +{r['horizon_d']}D, p_fdr={r.get('p_fdr', 'N/A')}"})
    if w2.get("models") is not None and len(w2["models"]) > 0:
        best = w2["models"].iloc[-1]
        rows.append({"result": "success_failure_incremental_map", "workstream": "WS2",
                     "causality_level": "L0_DESCRIPTIVE_CO_MOVEMENT",
                     "note": f"best AUC={best.cv_auc}, perm_p={best.perm_p}"})
    n_sig_rr = len(w3["comparison"][w3["comparison"].p_fdr < 0.1]) if len(w3["comparison"]) > 0 else 0
    rows.append({"result": "retest_reload_vs_failed_ignition", "workstream": "WS3",
                 "causality_level": "L1_TEMPORAL_ORDERING" if n_sig_rr > 0 else "L0_NULL",
                 "note": f"{n_sig_rr}/{len(w3['comparison'])} vars sig after FDR"})
    rows.append({"result": "escape_hazard", "workstream": "WS4",
                 "causality_level": "L1_TEMPORAL_ORDERING",
                 "note": "descriptive hazard by horizon"})
    if w5.get("summary") is not None and len(w5["summary"]) > 0:
        n_early = int((w5["summary"]["pct_decline"] > 0.3).sum())
        rows.append({"result": "early_decay_sequence", "workstream": "WS5",
                     "causality_level": "L1_TEMPORAL_ORDERING" if n_early > 0 else "L0_NULL",
                     "note": f"{n_early}/{len(w5['summary'])} vars show early decline"})
    rows.append({"result": "failure_motif_classification", "workstream": "WS6",
                 "causality_level": "L0_DESCRIPTIVE_CO_MOVEMENT", "note": "descriptive motifs"})
    if w7.get("rescue") is not None and len(w7["rescue"]) > 0:
        n_rescue = len(w7["rescue"][w7["rescue"].p_fdr < 0.1])
        rows.append({"result": "conditional_rescue", "workstream": "WS7",
                     "causality_level": "L2_CONDITIONAL_LEAD_LAG" if n_rescue > 0 else "L0_NULL",
                     "note": f"{n_rescue}/{len(w7['rescue'])} conditions sig after FDR"})
    lad = pd.DataFrame(rows)
    lad.to_csv(OUT / "18_CAUSALITY_LADDER.csv", index=False)
    return {"ladder": lad}


def main():
    print("=" * 72)
    print("ALT_MECH_5 :: FAILURE ANATOMY / ROTATION SURVIVAL / TEMPORAL DIVERGENCE")
    print("=" * 72)
    OUT.mkdir(parents=True, exist_ok=True)
    daily, ledger, entries, exits, m, top, bm, X, feat_df = load_data()
    n_succ = int(ledger.first_destination.isin(SUCCESS_LABELS).sum())
    n_fail = int(ledger.first_destination.isin(FAILURE_LABELS).sum())
    print(f"[data] daily={daily.shape}, ledger={len(ledger)}, success={n_succ}, failure={n_fail}")
    r1 = _cache_step("WS1", lambda: ws1_first_divergence(daily, ledger))
    n_earliest = len(r1.get("earliest", [])) if isinstance(r1.get("earliest"), pd.DataFrame) else 0
    print(f"[WS1] earliest divergences: {n_earliest}")
    r2 = _cache_step("WS2", lambda: ws2_incremental_map(daily, ledger, feat_df))
    print(f"[WS2] models: {len(r2['models'])}")
    r3 = _cache_step("WS3", lambda: ws3_retest_reload(daily, ledger))
    print(f"[WS3] RR={r3['n_rr']}, FI={r3['n_fi']}")
    r4 = _cache_step("WS4", lambda: ws4_two_clock(daily, ledger))
    print(f"[WS4] hazards computed")
    r5 = _cache_step("WS5", lambda: ws5_termination(daily, ledger))
    print(f"[WS5] termination panel: {len(r5['panel'])} events")
    r6 = _cache_step("WS6", lambda: ws6_failure_sequences(daily, ledger))
    print(f"[WS6] motifs: {len(r6['motifs'])}")
    r7 = _cache_step("WS7", lambda: ws7_conditional_rescue(daily, ledger))
    print(f"[WS7] conditions: {len(r7['rescue'])}")
    r8 = _cache_step("WS8", lambda: ws8_causality(r1, r2, r3, r4, r5, r6, r7))
    # nulls
    nulls = [row.to_dict() for _, row in r8["ladder"].iterrows() if "NULL" in str(row.causality_level)]
    pd.DataFrame(nulls).to_csv(OUT / "20_NULL_AND_FAILED_RESULTS.csv", index=False)
    # new nodes
    nodes = []
    if isinstance(r1.get("earliest"), pd.DataFrame) and len(r1["earliest"]) > 0:
        for _, er in r1["earliest"].iterrows():
            nodes.append({"node": f"DIVERGENCE_{er['variable']}", "operation": "NEW_NODE",
                         "strength": "ROBUST" if er.get("p_fdr", 1) < 0.05 else "LOCAL_NODE",
                         "source": "WS1", "note": f"earliest at +{er['horizon_d']}D"})
    n_sig_rr = len(r3["comparison"][r3["comparison"].p_fdr < 0.1]) if len(r3["comparison"]) > 0 else 0
    nodes.append({"node": "RETEST_RELOAD_STRUCTURE", "operation": "LOCAL_NODE" if n_sig_rr > 0 else "DESCRIPTIVE_ONLY",
                  "strength": f"{n_sig_rr}_vars_sig", "source": "WS3"})
    n_decay = int((r5["summary"]["pct_decline"] > 0.3).sum()) if len(r5["summary"]) > 0 else 0
    nodes.append({"node": "EARLY_DECAY_SEQUENCE", "operation": "NEW_NODE" if n_decay >= 3 else "DESCRIPTIVE_ONLY",
                  "strength": f"{n_decay}_vars_early_decline", "source": "WS5"})
    pd.DataFrame(nodes).to_csv(OUT / "19_NEW_NODE_MERGE_DISSOLVE.csv", index=False)
    # summary
    best_model = r2["models"].iloc[-1] if len(r2["models"]) > 0 else None
    n_rescue = len(r7["rescue"][r7["rescue"].p_fdr < 0.1]) if len(r7["rescue"]) > 0 else 0
    lines = ["# MECH-5 SUMMARY", "",
             "## First Divergence", f"- Variables with earliest significant divergence: {n_earliest}"]
    if isinstance(r1.get("earliest"), pd.DataFrame) and len(r1["earliest"]) > 0:
        for _, er in r1["earliest"].iterrows():
            lines.append(f"  - {er['variable']}: earliest at +{er['horizon_d']}D (r={er['rank_biserial_r']}, p_fdr={er.get('p_fdr', 'N/A')})")
    lines += ["", "## Success vs Failure Weight Map"]
    if best_model is not None:
        lines.append(f"- Best model: {best_model.model} AUC={best_model.cv_auc}, perm_p={best_model.perm_p}")
    lines += ["", f"## RETEST_RELOAD vs FAILED_IGNITION", f"- RR={r3['n_rr']}, FI={r3['n_fi']}",
              f"- Significant after FDR: {n_sig_rr}", "", "## Two-Clock Mechanism",
              "- Escape/propagation/failure hazards computed", "",
              "## Termination Precursors", f"- Early decline >30%: {n_decay}/{len(r5['summary'])}",
              "", "## Failure Motifs"]
    for _, mr in r6["motifs"].iterrows():
        lines.append(f"- {mr['motif']}: {mr['count']} ({mr['pct']:.1%})")
    lines += ["", f"## Conditional Rescue", f"- Significant after FDR: {n_rescue}/{len(r7['rescue'])}",
              "", "## Causality Classification"]
    for _, lr in r8["ladder"].iterrows():
        lines.append(f"- {lr.result}: {lr.causality_level}")
    with open(OUT / "21_MECH5_SUMMARY.md", "w") as f:
        f.write("\n".join(lines))
    # decision
    best_auc = best_model.cv_auc if best_model is not None else 0.5
    n_passed = sum([n_earliest > 0, n_sig_rr > 0, n_decay >= 3, n_rescue > 0, best_auc > 0.65])
    verdict = "PASS_MECH5_FAILURE_ANATOMY" if n_passed >= 3 else "PASS_MECH5_WITH_LIMITATIONS" if n_passed >= 1 else "FAIL_MECH5_NO_DIVERGENCE_STRUCTURE"
    dlines = ["# MECH-5 DECISION", "", f"## VERDICT: {verdict}", "",
              "### Key findings:",
              f"- First divergence variables: {n_earliest}",
              f"- Best success/failure AUC: {best_auc}",
              f"- RETEST_RELOAD structure: {n_sig_rr} vars",
              f"- Early decay signals: {n_decay} vars",
              f"- Conditional rescue significant: {n_rescue}",
              "", "### human_review_required = TRUE",
              "### next_checkpoint_authorized = FALSE", "",
              "No strategy. No PnL. No deployment."]
    with open(OUT / "22_MECH5_DECISION.md", "w") as f:
        f.write("\n".join(dlines))
    print(f"\n[VERDICT] {verdict}")
    n_csv = len(list(OUT.glob("*.csv")))
    n_md = len(list(OUT.glob("*.md")))
    print(f"[DONE] {n_csv} CSV + {n_md} MD")


if __name__ == "__main__":
    main()
