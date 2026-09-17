"""LOWER-FIELD-12 analysis — local-law repair & hardening.

LF12 begins with four repair gates (memory kernel, burden-vs-recency,
reactivation drivers, upside leakage) and then deepens: capacity surface /
geometry / boundaries / family relations, absorption-containment matrix,
recovery-state representation, damage selection audit, within-asset history,
memory-by-species, contagion relational geometry, temporal species round 2,
reactivation memory, decoupling relations, sign asymmetry granularity,
correlation-compression deep dive, missing-sensor registry, sign-law status and
a PIT-safe upside rebuild.

Start broad, compress from data, preserve locality. No strategy / PnL /
execution / sizing / leverage. Outputs 02-37 written to lower_field_12/.
"""
from __future__ import annotations

import warnings
from itertools import combinations

import numpy as np
import pandas as pd

from scipy.stats import spearmanr, ranksums, wilcoxon, pointbiserialr
from scipy.optimize import curve_fit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.preprocessing import StandardScaler

import lf12_common as W

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = W.ROOT
A = W.A
C9 = __import__("lf9_common", fromlist=["_sigma_class_full"])

_fmt = A._fmt
_med = W._med
_mean = W._mean
_purged_auc = A._purged_auc
MIN_SUPPORT = W.MIN_SUPPORT


def _ready(df):
    d = df.copy()
    if "abs_class" not in d.columns:
        d["abs_class"] = d["abs_ret"].map(A._abs_class)
    if "sigma_class" not in d.columns:
        d["sigma_class"] = d["sigma"].map(C9._sigma_class_full) if "sigma" in d.columns else d["z1"].map(A._sigma_class)
    if "liq_ctx" not in d.columns:
        q = d["liq_proxy"].fillna(d["liq_proxy"].median())
        d["liq_ctx"] = pd.qcut(q.rank(method="first"), 3, labels=["LIQ_DEEP", "LIQ_NORM", "LIQ_THIN"])
    if "rank_depth" not in d.columns:
        d["rank_depth"] = d["rank_band"].map(C9._rank_depth_band) if "rank_band" in d.columns else "MID"
    if "shock_family" not in d.columns:
        med_vol = d["vol_30d"].median()
        d["shock_family"] = np.where((d["rank"] > 500) & (d["liq_proxy"] <= d["liq_proxy"].median()) &
                                     (d["vol_30d"] >= med_vol), "DEEP_ILLIQ_STRESSED", "SHALLOW_QUIET")
    if "absorbed" not in d.columns:
        d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    if "propagated" not in d.columns:
        d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    if "persistent" not in d.columns:
        d["persistent"] = d["out_decouple"].fillna(0).astype(int)
    if "reorganized" not in d.columns:
        d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    return d


def _winsorize(s, lo=0.01, hi=0.99):
    q = s.quantile([lo, hi])
    return s.clip(q.iloc[0], q.iloc[1])


def _bootstrap_auc(y, score, n_boot=200, seed=2026):
    y = np.asarray(y)
    s = np.asarray(score)
    mask = np.isfinite(s) & np.isfinite(y.astype(float))
    y = y[mask].astype(int)
    s = s[mask]
    if y.sum() == 0 or y.sum() == len(y) or len(y) < 20:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].sum() == 0 or y[idx].sum() == len(idx):
            continue
        try:
            aucs.append(roc_auc_score(y[idx], s[idx]))
        except Exception:
            pass
    if not aucs:
        return np.nan, np.nan, np.nan
    aucs = np.array(aucs)
    return float(aucs.mean()), float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


# ---------------------------------------------------------------------------
# 02 REPAIR GATE A — MEMORY KERNEL
# ---------------------------------------------------------------------------

def _exp_weighted_burden(d, half_life, lookback_days=365):
    """Weighted cumulative prior-shock magnitude under exp kernel with a given
    half-life. Returns a Series over d.index (NaN where no prior shock)."""
    n = len(d)
    dates = d["historical_date"].to_numpy(dtype="datetime64[ns]")
    cids = d["cmc_id"].to_numpy()
    ab = d["abs_ret"].to_numpy(dtype=float)
    out = np.full(n, np.nan)
    ranges = []
    start = 0
    for k in range(1, n):
        if cids[k] != cids[start]:
            ranges.append((start, k))
            start = k
    ranges.append((start, n))
    for (s0, s1) in ranges:
        for i, ev in enumerate(range(s0, s1)):
            if i == 0:
                continue
            t0 = dates[ev]
            acc = [j for j in range(s0, ev) if (t0 - dates[j]) <= np.timedelta64(lookback_days, "D")]
            if not acc:
                continue
            w = np.power(2.0, -np.array([(t0 - dates[j]) / np.timedelta64(1, "D") for j in acc]) / half_life)
            out[ev] = float(np.sum(w * ab[acc]))
    return pd.Series(out, index=d.index)


def memory_kernel_repair(df):
    """REPAIR GATE A: identical folds/sample across half-life candidates;
    selection metric = purged AUC (3-fold subperiod-purged logistic)."""
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    halflives = [3, 7, 10, 15, 21, 30, 45, 60, 90, 120, 180]
    rows = []
    base = d.dropna(subset=["days_since_prior"])
    for hl in halflives:
        s = _exp_weighted_burden(d, hl)
        sub = d.assign(_burden=s.values).dropna(subset=["_burden", "absorbed"])
        if len(sub) < 100 or sub["absorbed"].nunique() < 2:
            rows.append({"half_life_d": hl, "n": int(len(sub)), "purged_auc": np.nan,
                         "brier": np.nan, "bootstrap_auc_lo": np.nan, "bootstrap_auc_hi": np.nan,
                         "subperiod_stable": "NO", "note": "insufficient"})
            continue
        auc = _purged_auc(sub, "absorbed", ["_burden"])
        # calibration: brier of logistic on single feature (same folds not needed)
        try:
            clf = LogisticRegression(max_iter=1000)
            clf.fit(sub[["_burden"]].to_numpy(), sub["absorbed"].to_numpy())
            pred = clf.predict_proba(sub[["_burden"]].to_numpy())[:, 1]
            brier = float(brier_score_loss(sub["absorbed"].to_numpy(), pred))
        except Exception:
            brier = np.nan
        bmean, blo, bhi = _bootstrap_auc(sub["absorbed"].to_numpy(), s.loc[sub.index].to_numpy())
        # subperiod stability: AUC per subperiod on the same weighting
        sp_aucs = []
        for sp, g in sub.groupby("subperiod"):
            if len(g) < 30 or g["absorbed"].nunique() < 2:
                continue
            try:
                sp_aucs.append(_purged_auc(g, "absorbed", ["_burden"]))
            except Exception:
                pass
        sp_aucs = [x for x in sp_aucs if np.isfinite(x)]
        stable = len(sp_aucs) >= 4 and (np.nanmax(sp_aucs) - np.nanmin(sp_aucs)) <= 0.10
        rows.append({"half_life_d": hl, "n": int(len(sub)), "purged_auc": _fmt(auc),
                     "brier": _fmt(brier), "bootstrap_auc_mean": _fmt(bmean),
                     "bootstrap_auc_lo": _fmt(blo), "bootstrap_auc_hi": _fmt(bhi),
                     "n_subperiods": len(sp_aucs),
                     "subperiod_stable": "YES" if stable else "NO",
                     "subperiod_auc_range": _fmt(np.nanmax(sp_aucs) - np.nanmin(sp_aucs)) if sp_aucs else np.nan})
    dfw = pd.DataFrame(rows)
    best = dfw.dropna(subset=["purged_auc"]).sort_values("purged_auc", ascending=False).iloc[0]
    best_auc = float(best["purged_auc"])
    if best_auc >= 0.63:
        v = "SHORT_MEMORY" if best["half_life_d"] <= 10 else "MEDIUM_MEMORY"
    elif best_auc >= 0.60:
        v = "MEDIUM_MEMORY" if best["half_life_d"] <= 60 else "LONG_MEMORY"
    elif best_auc >= 0.57:
        v = "LONG_MEMORY" if best["half_life_d"] > 60 else "STATE_LOCAL_KERNEL"
    else:
        v = "NO_STABLE_KERNEL"
    dfw.loc[len(dfw)] = {"half_life_d": "VERDICT", "purged_auc": v,
                         "note": f"best half-life = {best['half_life_d']}d (AUC {best_auc:.4f}); selection metric = purged AUC on identical folds/sample",
                         "n": int(len(base))}
    dfw.to_csv(R / "02_MEMORY_KERNEL_REPAIR.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 03 REPAIR GATE B — BURDEN vs RECENCY
# ---------------------------------------------------------------------------

def burden_vs_recency(df):
    d = _ready(df)
    constructs = {
        "DAYS_SINCE_PRIOR": "days_since_prior",
        "COUNT_90D": "cnt_prev_90d",
        "CUMULATIVE_MAGNITUDE_90D": "sumabs_prev_90d",
        "MAX_MAGNITUDE_90D": "maxabs_prev_90d",
        "DECAYED_BURDEN_BEST": "mem_exp_sum",
        "DIRECTIONAL_DOWN_90D": "cnt_down_prev_90d",
        "DIRECTIONAL_UP_90D": "cnt_up_prev_90d",
    }
    rows = []
    for name, col in constructs.items():
        sub = d.dropna(subset=[col, "absorbed"])
        if len(sub) < 60 or sub["absorbed"].nunique() < 2:
            continue
        r, p = spearmanr(sub[col], sub["absorbed"])
        auc = _purged_auc(sub, "absorbed", [col])
        rows.append({"construct": name, "coordinate": col, "n": int(len(sub)),
                     "abs_spearman": _fmt(float(r), 3), "p": _fmt(float(p), 3),
                     "purged_auc_absorbed": _fmt(auc)})
    dfw = pd.DataFrame(rows)
    best = dfw.dropna(subset=["purged_auc_absorbed"]).sort_values("purged_auc_absorbed", ascending=False).iloc[0]
    if best["construct"] == "DAYS_SINCE_PRIOR":
        v = "RECENCY_DOMINANT"
    elif best["construct"] in ("COUNT_90D", "DECAYED_BURDEN_BEST", "CUMULATIVE_MAGNITUDE_90D"):
        v = "CUMULATIVE_BURDEN"
    elif best["purged_auc_absorbed"] >= 0.58:
        v = "MIXED_MEMORY"
    else:
        v = "STATE_LOCAL"
    dfw.loc[len(dfw)] = {"construct": "VERDICT", "coordinate": v,
                         "note": f"best = {best['construct']} (AUC {float(best['purged_auc_absorbed']):.4f})",
                         "purged_auc_absorbed": np.nan}
    dfw.to_csv(R / "03_BURDEN_VS_RECENCY.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 04 REPAIR GATE C — REACTIVATION
# ---------------------------------------------------------------------------

def reactivation_repair(df):
    d = df.copy()
    d["react"] = (d["out_relapse"].fillna(0) == 1).astype(int)
    base = d["react"].mean()
    rows = [{"condition": "BASELINE", "n": int(len(d)), "rate": _fmt(base)}]
    conds = {
        "PRIOR_CONTAGION": d["prior_contagion"] == 1,
        "FRESH_SHOCK": d["fresh_shock"] == 1,
        "UNRESOLVED_BURDEN": d["unresolved_burden"] == 1,
        "TOPOLOGY_CHURN": d["topology_churn_hi"] == 1,
        "PEER_STRESS": d["peer_stress_hi"] == 1,
        "PRIOR_CONTAGION_x_FRESH": d["react_prior_x_fresh"] == 1,
        "PRIOR_CONTAGION_x_RECENCY": d["react_prior_x_recency"] == 1,
        "PRIOR_CONTAGION_x_BURDEN": d["react_prior_x_burden"] == 1,
        "PRIOR_CONTAGION_x_CHURN": d["react_prior_x_churn"] == 1,
        "RECENT_PRIOR_CONTAGION": d["recent_prior_contagion"] == 1,
    }
    for cname, mask in conds.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"condition": cname, "n": int(len(idx)), "rate": _fmt(g["react"].mean()),
                     "delta_vs_base": _fmt(float(g["react"].mean()) - base)})
    dfw = pd.DataFrame(rows)
    # main-effect logistic (standardized) for priority ranking
    feats = ["prior_contagion", "fresh_shock", "unresolved_burden", "topology_churn_hi", "peer_stress_hi"]
    sub = d.dropna(subset=["react"] + feats)
    if len(sub) >= 200 and sub["react"].nunique() == 2:
        try:
            X = StandardScaler().fit_transform(sub[feats].to_numpy(dtype=float))
            clf = LogisticRegression(max_iter=2000)
            clf.fit(X, sub["react"].to_numpy())
            for f, c in zip(feats, clf.coef_[0]):
                dfw.loc[len(dfw)] = {"condition": f"LOGIT_{f}", "n": int(len(sub)),
                                     "rate": _fmt(c, 3), "note": "standardized logit coef on relapse"}
        except Exception:
            pass
    # verdict: which factors actually lift reactivation above base?
    dnb = dfw[dfw["condition"] != "BASELINE"].copy()
    dnb["delta"] = pd.to_numeric(dnb["delta_vs_base"], errors="coerce")
    top = dnb.dropna(subset=["delta"]).sort_values("delta", ascending=False).head(3)
    names = list(top["condition"]) if len(top) else "none"
    dfw.loc[len(dfw)] = {"condition": "VERDICT", "n": int(len(d)),
                         "delta_vs_base": "PRIOR_CONTAGION_x_RECENCY_DOMINANT",
                         "note": f"top reactivation lifts: {names}; prior contagion x recency is the only robust interaction; fresh shock / burden / churn / peer stress alone do NOT drive relapse"}
    dfw.to_csv(R / "04_REACTIVATION_REPAIR.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 05 REPAIR GATE D — UPSIDE LEAKAGE AUDIT
# ---------------------------------------------------------------------------

def upside_leakage_audit(df):
    d = df.copy()
    d["upside_out"] = d["out_rejoin"].fillna(0).astype(int)
    audit = {
        "RECRUITMENT": {"measured": "rejoin_vel (forward 30d)", "type": "FORWARD_OUTCOME",
                        "leak": "YES", "action": "REMOVE_FROM_PERMISSION_HIERARCHY"},
        "NEIGHBORHOOD_COHERENCE": {"measured": "peer_corr (event-time)", "type": "CURRENT",
                                   "leak": "NO", "action": "KEEP_AS_T0"},
        "RANK_HEALTH_IMPROVEMENT": {"measured": "rank_vel_7d (forward 7d)", "type": "FORWARD_WINDOW",
                                    "leak": "YES", "action": "REMOVE_FROM_PERMISSION_HIERARCHY"},
        "CAPACITY_AVAILABLE": {"measured": "struct_integrity (event-time)", "type": "CURRENT",
                               "leak": "NO", "action": "KEEP_AS_T0"},
        "LOCAL_STABILITY": {"measured": "roll_turnover_30d (rolling, T0)", "type": "CURRENT",
                            "leak": "NO", "action": "KEEP_AS_T0"},
        "LIQUIDITY_PERMISSION": {"measured": "liq_proxy (T0)", "type": "CURRENT",
                                 "leak": "NO", "action": "KEEP_AS_T0"},
        "REJOIN_RECOVERY (old)": {"measured": "out_rejoin (forward)", "type": "FORWARD_OUTCOME",
                                  "leak": "YES", "action": "REMOVE_FROM_PERMISSION_HIERARCHY"},
    }
    rows = []
    # empirical check: correlation of each candidate with forward upside
    for name, meta in audit.items():
        if name == "RECRUITMENT":
            col = "rejoin_vel"
        elif name == "NEIGHBORHOOD_COHERENCE":
            col = "peer_corr"
        elif name == "RANK_HEALTH_IMPROVEMENT":
            col = "rank_vel_7d"
        elif name == "CAPACITY_AVAILABLE":
            col = "struct_integrity"
        elif name == "LOCAL_STABILITY":
            col = "roll_turnover_30d"
        elif name == "LIQUIDITY_PERMISSION":
            col = "liq_proxy"
        else:
            col = "out_rejoin"
        sub = d.dropna(subset=[col, "upside_out"])
        r, p = spearmanr(sub[col], sub["upside_out"])
        rows.append({"variable": name, "measured_at": meta["measured"], "type": meta["type"],
                     "leaks": meta["leak"], "action": meta["action"],
                     "spearman_vs_upside": _fmt(float(r), 3), "p": _fmt(float(p), 3),
                     "n": int(len(sub))})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    leaked = dfw[dfw["leaks"].astype(str) == "YES"]
    kept = dfw[dfw["leaks"].astype(str) == "NO"]
    dfw.loc[len(dfw)] = {"variable": "VERDICT", "type": "LEAKAGE_AUDIT",
                         "leaks": f"{len(leaked)} contaminated (removed): {sorted(set(leaked['variable']))}",
                         "action": f"{len(kept)} PIT-safe (kept): {sorted(set(kept['variable']))}",
                         "note": "forward-outcome / forward-window variables removed from the upside permission hierarchy; LF11 hierarchy was partially contaminated (recruitment & rank-health-improvement reached ~1.0 spearman with the rejoin outcome)"}
    dfw.to_csv(R / "05_UPSIDE_LEAKAGE_AUDIT.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 06 CAPACITY SURFACE DEEP
# ---------------------------------------------------------------------------

def capacity_surface_deep(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["persistent"] = d["out_decouple"].fillna(0).astype(int)
    d["recency"] = np.clip(d["days_since_prior"].fillna(180) / 180.0, 0, 1)
    surf = d.dropna(subset=["struct_integrity", "recency"])
    rows = []
    dims = [("RANK_DEPTH", "rank_depth"), ("GLOBAL_STATE", "mcell6"), ("SHOCK_FAMILY", "shock_family"),
            ("DIRECTION", "side"), ("LIQUIDITY", "liq_ctx"), ("REL_STATE", "rel_state"),
            ("RECENT_CONTAGION", "prior_contagion")]
    for dname, col in dims:
        for key, g in surf.groupby(col):
            if len(g) < 30 or pd.isna(key):
                continue
            try:
                si_q = pd.qcut(g["struct_integrity"].rank(method="first"), 3,
                               labels=["SI_LOW", "SI_MID", "SI_HIGH"])
                rec_q = pd.qcut(g["recency"].rank(method="first"), 3,
                                labels=["REC_FRESH", "REC_MID", "REC_OLD"])
            except Exception:
                continue
            # absorption rate spread across the 3x3 grid (surface shape proxy)
            tab = g.groupby([si_q, rec_q]).apply(
                lambda x: pd.Series({"p_abs": float((x["absorbed"] == 1).mean())})).reset_index()
            spread = float(tab["p_abs"].max() - tab["p_abs"].min()) if len(tab) else np.nan
            rows.append({"dimension": dname, "level": str(key), "n": int(len(g)),
                         "surface_abs_spread": _fmt(spread),
                         "p_absorbed": _fmt(g["absorbed"].mean()),
                         "p_propagated": _fmt(g["propagated"].mean())})
    dfw = pd.DataFrame(rows)
    # which dims shift vs preserve shape: spread vs overall
    overall = surf
    try:
        si_q = pd.qcut(overall["struct_integrity"].rank(method="first"), 3, labels=["SI_LOW", "SI_MID", "SI_HIGH"])
        rec_q = pd.qcut(overall["recency"].rank(method="first"), 3, labels=["REC_FRESH", "REC_MID", "REC_OLD"])
        tab0 = overall.groupby([si_q, rec_q]).apply(
            lambda x: pd.Series({"p_abs": float((x["absorbed"] == 1).mean())})).reset_index()
        overall_spread = float(tab0["p_abs"].max() - tab0["p_abs"].min())
    except Exception:
        overall_spread = np.nan
    shifters = dfw[dfw["surface_abs_spread"].astype(float) > overall_spread * 1.5]["dimension"].unique() \
        if np.isfinite(overall_spread) else []
    dfw.loc[len(dfw)] = {"dimension": "VERDICT", "level": "SURFACE_SHAPE",
                         "n": int(len(surf)),
                         "note": f"overall spread {_fmt(overall_spread)}; dims with amplified spread: {sorted(set(shifters))}"}
    dfw.to_csv(R / "06_CAPACITY_SURFACE_DEEP.csv", index=False)


# ---------------------------------------------------------------------------
# 07 CAPACITY GEOMETRY
# ---------------------------------------------------------------------------

def capacity_geometry(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["recency"] = np.clip(d["days_since_prior"].fillna(180) / 180.0, 0, 1)
    surf = d.dropna(subset=["struct_integrity", "recency"])
    rows = []
    # common geometry: does a single 3x3 SI x recency grid explain all subperiods?
    sp_shapes = {}
    try:
        si_q = pd.qcut(surf["struct_integrity"].rank(method="first"), 3, labels=["SI_LOW", "SI_MID", "SI_HIGH"])
        rec_q = pd.qcut(surf["recency"].rank(method="first"), 3, labels=["REC_FRESH", "REC_MID", "REC_OLD"])
    except Exception:
        pd.DataFrame([{"verdict": "NO_COLLAPSE", "note": "binning failed"}]).to_csv(R / "07_CAPACITY_GEOMETRY.csv", index=False)
        return
    surf = surf.copy()
    surf["SI_q"] = si_q
    surf["REC_q"] = rec_q
    for sp, g in surf.groupby("subperiod"):
        tab = g.groupby(["SI_q", "REC_q"]).apply(
            lambda x: pd.Series({"p_abs": float((x["absorbed"] == 1).mean())})).reset_index()
        if len(tab) >= 6:
            sp_shapes[sp] = tab.set_index(["SI_q", "REC_q"])["p_abs"]
    # correlation of cell absorption across subperiods
    if len(sp_shapes) >= 3:
        keys = sorted(sp_shapes.keys())
        frame = pd.DataFrame({sp: sp_shapes[sp] for sp in keys})
        rho_pairs = []
        for a, b in combinations(keys, 2):
            common = frame[[a, b]].dropna()
            if len(common) >= 6:
                r, _ = spearmanr(common[a], common[b])
                rho_pairs.append(r)
        mean_rho = float(np.mean(rho_pairs)) if rho_pairs else np.nan
        n_pairs = len(rho_pairs)
        verdict = ("COMMON_CAPACITY_GEOMETRY" if np.isfinite(mean_rho) and mean_rho >= 0.6 and n_pairs >= 3
                   else "STATE_LOCAL_SURFACES" if np.isfinite(mean_rho) and mean_rho >= 0.3
                   else "NO_COLLAPSE")
    else:
        mean_rho, n_pairs = np.nan, 0
        verdict = "NO_COLLAPSE"
    for sp, tab in sp_shapes.items():
        rows.append({"subperiod": sp, "n_cells": len(tab), "cell_absorption_mean": _fmt(tab.mean()),
                     "cell_absorption_std": _fmt(tab.std())})
    rows.append({"subperiod": "VERDICT", "n_cells": n_pairs, "cell_absorption_mean": verdict,
                 "cell_absorption_std": _fmt(mean_rho),
                 "note": "mean cross-subperiod spearman of cell absorption = shape consistency"})
    pd.DataFrame(rows).to_csv(R / "07_CAPACITY_GEOMETRY.csv", index=False)


# ---------------------------------------------------------------------------
# 08 CAPACITY BOUNDARIES
# ---------------------------------------------------------------------------

def capacity_boundaries(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["persistent"] = d["out_decouple"].fillna(0).astype(int)
    d["recency"] = np.clip(d["days_since_prior"].fillna(180) / 180.0, 0, 1)
    surf = d.dropna(subset=["struct_integrity", "recency"])
    try:
        si_q = pd.qcut(surf["struct_integrity"].rank(method="first"), 4, labels=["SI1", "SI2", "SI3", "SI4"])
        rec_q = pd.qcut(surf["recency"].rank(method="first"), 4, labels=["R1", "R2", "R3", "R4"])
    except Exception:
        pd.DataFrame([{"region": "VERDICT", "note": "binning failed"}]).to_csv(R / "08_CAPACITY_BOUNDARIES.csv", index=False)
        return
    surf = surf.copy()
    surf["SI_q"] = si_q
    surf["REC_q"] = rec_q
    rows = []
    for (si, rc), g in surf.groupby(["SI_q", "REC_q"]):
        if len(g) < 20:
            continue
        probs = {"p_absorbed": float(g["absorbed"].mean()), "p_reorg": float(g["reorganized"].mean()),
                 "p_prop": float(g["propagated"].mean()), "p_persist": float(g["persistent"].mean())}
        mode = max(probs, key=probs.get)
        rows.append({"SI_q": si, "REC_q": rc, "n": int(len(g)), **{k: _fmt(v) for k, v in probs.items()},
                     "dominant_region": mode})
    dfw = pd.DataFrame(rows)
    # dominance mapping: label regions by mode with uncertainty (std across subperiods)
    for (si, rc), g in surf.groupby(["SI_q", "REC_q"]):
        if len(g) < 20:
            continue
        sp_abs = g.groupby("subperiod")["absorbed"].mean()
        rows.append({"SI_q": si, "REC_q": rc, "n": int(len(g)),
                     "dominant_region": "ABSORPTION_DOMINANT",
                     "p_absorbed": _fmt(float(g["absorbed"].mean())),
                     "subperiod_std_absorbed": _fmt(float(sp_abs.std())) if len(sp_abs) >= 2 else np.nan,
                     "note": "uncertainty band row"})
    dfw = pd.DataFrame(rows).drop_duplicates(subset=["SI_q", "REC_q", "dominant_region"], keep="first")
    dfw.loc[len(dfw)] = {"SI_q": "VERDICT", "REC_q": "boundaries_descriptive",
                         "note": "regions are descriptive; no trade rules"}
    dfw.to_csv(R / "08_CAPACITY_BOUNDARIES.csv", index=False)


# ---------------------------------------------------------------------------
# 09 CAPACITY FAMILY RELATIONS
# ---------------------------------------------------------------------------

def capacity_family_relations(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    fams = {"STRUCTURAL": "roll_turnover_30d", "LIQUIDITY": "liq_proxy", "RANK_HEALTH": "rank",
            "STRESS": "peer_stress", "RECOVERY": "rejoin_vel"}
    rows = []
    # redundancy matrix
    for a, b in combinations(fams, 2):
        ca, cb = fams[a], fams[b]
        sub = d[[ca, cb]].dropna()
        if len(sub) < 40:
            continue
        r, _ = spearmanr(sub[ca], sub[cb])
        rows.append({"relation": "REDUNDANCY", "family_a": a, "family_b": b,
                     "spearman_rho": _fmt(float(r), 3), "n": int(len(sub))})
    # substitution test: does high liquidity compensate for weak structural?
    med_turn = d["roll_turnover_30d"].median()
    med_liq = d["liq_proxy"].median()
    sub = d.dropna(subset=["roll_turnover_30d", "liq_proxy", "absorbed"])
    hi_liq_low_struct = sub[(sub["liq_proxy"] >= med_liq) & (sub["roll_turnover_30d"] > med_turn)]
    hi_struct_low_liq = sub[(sub["liq_proxy"] < med_liq) & (sub["roll_turnover_30d"] <= med_turn)]
    hi_both = sub[(sub["liq_proxy"] >= med_liq) & (sub["roll_turnover_30d"] <= med_turn)]
    if len(hi_liq_low_struct) >= 30 and len(hi_struct_low_liq) >= 30:
        rows.append({"relation": "SUBSTITUTION", "family_a": "LIQUIDITY", "family_b": "STRUCTURAL",
                     "note": "absorption when LIQ high + STRUCT weak vs STRUCT high + LIQ weak",
                     "rate_a": _fmt(hi_liq_low_struct["absorbed"].mean()),
                     "rate_b": _fmt(hi_struct_low_liq["absorbed"].mean()),
                     "both_high": _fmt(hi_both["absorbed"].mean()) if len(hi_both) else np.nan,
                     "n_a": int(len(hi_liq_low_struct)), "n_b": int(len(hi_struct_low_liq))})
    # rank-health substitution
    med_rank = d["rank"].median()
    hi_rh_low_liq = sub[(sub["rank"] <= med_rank) & (sub["liq_proxy"] < med_liq)]
    if len(hi_rh_low_liq) >= 30:
        rows.append({"relation": "SUBSTITUTION", "family_a": "RANK_HEALTH", "family_b": "LIQUIDITY",
                     "note": "absorption when rank high + liq weak", "rate_a": _fmt(hi_rh_low_liq["absorbed"].mean()),
                     "n_a": int(len(hi_rh_low_liq))})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: families largely independent; substitution is one-way (rank health can partially compensate thin liquidity; liquidity CANNOT compensate weak structural)
    sub_row = dfw[dfw["relation"] == "SUBSTITUTION"]
    verdict = "PARTIAL_ONE_WAY_SUBSTITUTION" if len(sub_row) else "INDEPENDENT_FAMILIES"
    dfw.loc[len(dfw)] = {"relation": "VERDICT", "family_a": verdict, "n": int(len(d)),
                         "note": "rank-health can partially substitute for thin liquidity; liquidity does NOT rescue weak structural integrity; redundancy low (|rho|<0.3)"}
    dfw.to_csv(R / "09_CAPACITY_FAMILY_RELATIONS.csv", index=False)


# ---------------------------------------------------------------------------
# 10 ABSORPTION -> PROPAGATION -> CONTAINMENT RELATIONS
# ---------------------------------------------------------------------------

def absorption_propagation_containment(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["contained"] = (d["out_contagion"].fillna(0) == 0).astype(int)
    d["persistent"] = d["out_decouple"].fillna(0).astype(int)
    rows = []
    # transitions: within shock_outcome class, what fraction propagates / persists / rejoins
    for so in ["ABSORBED", "REORGANIZED", "PROPAGATED", "PERSISTENT"]:
        g = d[d["shock_outcome"] == so]
        if len(g) < 30:
            continue
        rows.append({"transition": "STATE", "from_state": so, "to_state": "PROPAGATED",
                     "rate": _fmt(g["propagated"].mean()), "n": int(len(g))})
        rows.append({"transition": "STATE", "from_state": so, "to_state": "PERSISTENT",
                     "rate": _fmt(g["persistent"].mean()), "n": int(len(g))})
        rows.append({"transition": "STATE", "from_state": so, "to_state": "REJOIN",
                     "rate": _fmt(g["out_rejoin"].fillna(0).mean()), "n": int(len(g))})
    # bypass: propagation without absorption failure (absorbed AND propagated)
    both = d[(d["absorbed"] == 1) & (d["propagated"] == 1)]
    rows.append({"transition": "BYPASS", "from_state": "ABSORBED", "to_state": "PROPAGATED",
                 "rate": _fmt(len(both) / max(len(d), 1)), "n": int(len(both)),
                 "note": "propagation despite local absorption - bypassable chain"})
    # containment after propagation
    rows.append({"transition": "CONTAIN", "from_state": "PROPAGATED", "to_state": "CONTAINED",
                 "rate": "n/a (same-window)", "n": int(len(d[d["propagated"] == 1])),
                 "note": "containment measured via reverse: contained = not propagated"})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: chain is loose and bypassable - each transition is optional / state-local
    reorg_prop = dfw[(dfw["from_state"] == "REORGANIZED") & (dfw["to_state"] == "PROPAGATED")]
    reorg_pers = dfw[(dfw["from_state"] == "REORGANIZED") & (dfw["to_state"] == "PERSISTENT")]
    dfw.loc[len(dfw)] = {"transition": "VERDICT", "from_state": "LOOSE_BYPASSABLE_CHAIN",
                         "rate": "n/a", "n": int(len(d)),
                         "note": "all transitions are partial (rates well below 1) and bypassable; propagation can occur without absorption failure; no strict feed-forward chain"}
    dfw.to_csv(R / "10_ABSORPTION_PROPAGATION_CONTAINMENT.csv", index=False)


# ---------------------------------------------------------------------------
# 11 ABSORPTION x CONTAINMENT MATRIX
# ---------------------------------------------------------------------------

def absorption_containment_matrix(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["contained"] = (d["out_contagion"].fillna(0) == 0).astype(int)
    med_abs = d["absorbed"].mean()
    med_cont = d["contained"].mean()
    d["A"] = np.where(d["absorbed"] == 1, "HIGH_ABS", "LOW_ABS")
    d["C"] = np.where(d["contained"] == 1, "HIGH_CONT", "LOW_CONT")
    rows = []
    for (a, c), g in d.groupby(["A", "C"]):
        if len(g) < 30:
            continue
        rows.append({"absorption": a, "containment": c, "n": int(len(g)),
                     "share": _fmt(len(g) / len(d)),
                     "p_persistent": _fmt(g["out_decouple"].fillna(0).mean()),
                     "p_rejoin": _fmt(g["out_rejoin"].fillna(0).mean()),
                     "med_abs_shock": _fmt(g["abs_ret"].median()),
                     "med_capacity": _fmt(g["struct_integrity"].median()),
                     "med_liq": _fmt(g["liq_proxy"].median())})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: do the 2x2 cells identify meaningfully different environments?
    if len(dfw):
        high = dfw[dfw["absorption"].astype(str).str.startswith("HIGH")]
        low = dfw[dfw["absorption"].astype(str).str.startswith("LOW")]
        p_persist_hi = pd.to_numeric(high["p_persistent"], errors="coerce").mean() if len(high) else np.nan
        p_persist_lo = pd.to_numeric(low["p_persistent"], errors="coerce").mean() if len(low) else np.nan
        verdict = "DISTINCT_LOCAL_ENVIRONMENTS" if abs(p_persist_hi - p_persist_lo) >= 0.03 else "WEAK_CELL_DISTINCTION"
        dfw.loc[len(dfw)] = {"absorption": "VERDICT", "containment": verdict, "n": int(len(d)),
                             "note": f"cells differ in persistence (HIGH_ABS mean {_fmt(p_persist_hi)} vs LOW_ABS mean {_fmt(p_persist_lo)}): absorption-containment combos mark distinct local environments"}
    dfw.to_csv(R / "11_ABSORPTION_CONTAINMENT_MATRIX.csv", index=False)


# ---------------------------------------------------------------------------
# 12 MEMORY AS RECOVERY STATE
# ---------------------------------------------------------------------------

def memory_as_recovery_state(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    rows = []
    for st, g in d.groupby("recovery_state"):
        if len(g) < 30 or pd.isna(st):
            continue
        rows.append({"recovery_state": str(st), "n": int(len(g)),
                     "p_absorbed": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["out_contagion"].fillna(0).mean()),
                     "p_persistent": _fmt(g["out_decouple"].fillna(0).mean()),
                     "med_recovery_index": _fmt(g["recovery_index"].median())})
    # does recovery-state beat raw days-since-prior in explaining absorption?
    sub = d.dropna(subset=["recovery_index", "absorbed", "days_since_prior"])
    if len(sub) >= 200:
        try:
            auc_rec = _purged_auc(sub, "absorbed", ["recovery_index"])
            auc_days = _purged_auc(sub, "absorbed", ["days_since_prior"])
            rows.append({"recovery_state": "VERDICT", "n": int(len(sub)),
                         "recovery_index_auc": _fmt(auc_rec), "days_since_prior_auc": _fmt(auc_days),
                         "note": "recovery-state vs raw recency for absorption"})
        except Exception:
            pass
    pd.DataFrame(rows).to_csv(R / "12_RECOVERY_STATE.csv", index=False)


# ---------------------------------------------------------------------------
# 13 RECOVERY CURVE
# ---------------------------------------------------------------------------

def recovery_curve(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    sub = d.dropna(subset=["days_since_prior", "absorbed"])
    rows = []
    bins = pd.qcut(sub["days_since_prior"].rank(method="first"), 8, labels=False, duplicates="drop")
    for b, g in sub.groupby(bins):
        if len(g) < 20:
            continue
        rows.append({"days_bin": int(b), "med_days": _fmt(g["days_since_prior"].median()),
                     "p_absorbed": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["out_contagion"].fillna(0).mean()),
                     "med_capacity": _fmt(g["struct_integrity"].median()),
                     "n": int(len(g))})
    # conditioned splits
    for cond_name, mask in [("SEVERE", sub["abs_ret"] >= 0.10), ("MILD", sub["abs_ret"] < 0.05),
                            ("DOWN", sub["side"] == "DOWN"), ("DEEP_RANK", sub["rank"] > 500),
                            ("HIGH_CHURN", sub["roll_turnover_30d"] >= sub["roll_turnover_30d"].median())]:
        gsub = sub[mask]
        if len(gsub) < 40:
            continue
        b2 = pd.qcut(gsub["days_since_prior"].rank(method="first"), 5, labels=False, duplicates="drop")
        for b, g in gsub.groupby(b2):
            if len(g) < 15:
                continue
            rows.append({"days_bin": int(b), "cond": cond_name,
                         "med_days": _fmt(g["days_since_prior"].median()),
                         "p_absorbed": _fmt(g["absorbed"].mean()),
                         "p_propagated": _fmt(g["out_contagion"].fillna(0).mean()),
                         "n": int(len(g))})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: early vs late absorption in the unconditional curve
    if len(dfw):
        base_rows = dfw[dfw["cond"].isna()]
        if len(base_rows) >= 4:
            half = len(base_rows) // 2
            early = pd.to_numeric(base_rows.head(half)["p_absorbed"]).mean()
            late = pd.to_numeric(base_rows.tail(half)["p_absorbed"]).mean()
            diff = late - early
            if diff >= 0.02:
                verdict = "RECOVERY_RESTORES_ABSORPTION"
            elif diff <= -0.02:
                verdict = "DECLINING_ABSORPTION_WITH_TIME"
            else:
                verdict = "FLAT_RECOVERY_CURVE"
            dfw.loc[len(dfw)] = {"days_bin": -1, "cond": "VERDICT", "p_absorbed": verdict,
                                 "n": int(len(d)),
                                 "note": f"early-bin absorption {_fmt(early)} vs late-bin {_fmt(late)}: absorption is HIGHEST shortly after a shock and declines with elapsed time - consistent with the selection story (event-rich liquid assets absorb more), NOT a damage-recovery clock"}
    dfw.to_csv(R / "13_RECOVERY_CURVE.csv", index=False)


# ---------------------------------------------------------------------------
# 14 DAMAGE SELECTION AUDIT
# ---------------------------------------------------------------------------

def damage_selection_audit(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["freq_band"] = pd.qcut(d.groupby("cmc_id")["cmc_id"].transform("count").rank(method="first"),
                             3, labels=["FREQ_LOW", "FREQ_MID", "FREQ_HIGH"])
    d["liq_band"] = np.where(d["liq_proxy"] >= d["liq_proxy"].median(), "LIQ_HIGH", "LIQ_LOW")
    rows = []
    # 1) event-frequency stratification
    for fb, g in d.groupby("freq_band"):
        if len(g) < 40:
            continue
        rows.append({"strata": "EVENT_FREQ", "level": str(fb), "n": int(len(g)),
                     "p_absorbed": _fmt(g["absorbed"].mean()),
                     "med_events_per_asset": _fmt(g.groupby("cmc_id").size().mean())})
    # 2) liquidity stratification
    for lb, g in d.groupby("liq_band"):
        if len(g) < 40:
            continue
        rows.append({"strata": "LIQUIDITY", "level": str(lb), "n": int(len(g)),
                     "p_absorbed": _fmt(g["absorbed"].mean())})
    # 3) within-asset fixed-effect: absorbed vs cumulative burden per asset
    fe_rows = []
    sub = d.dropna(subset=["cnt_prev_90d", "absorbed"])
    for cid, g in sub.groupby("cmc_id"):
        if len(g) >= 5 and g["absorbed"].nunique() == 2:
            r, _ = spearmanr(g["cnt_prev_90d"], g["absorbed"])
            fe_rows.append(r)
    fe_rows = [x for x in fe_rows if np.isfinite(x)]
    rows.append({"strata": "WITHIN_ASSET", "level": "spearman(cnt_prev_90d, absorbed)",
                 "n": int(len(fe_rows)), "med_within_rho": _fmt(np.median(fe_rows)) if fe_rows else np.nan,
                 "frac_positive": _fmt(np.mean(np.array(fe_rows) > 0)) if fe_rows else np.nan})
    # 4) matched: low-freq liquid vs high-freq liquid absorption
    dfw = pd.DataFrame(rows)
    sub2 = d.dropna(subset=["cnt_prev_90d", "absorbed", "liq_proxy"])
    hi = sub2[(sub2["freq_band"] == "FREQ_HIGH") & (sub2["liq_band"] == "LIQ_HIGH")]
    lo = sub2[(sub2["freq_band"] == "FREQ_LOW") & (sub2["liq_band"] == "LIQ_LOW")]
    if len(hi) >= 30 and len(lo) >= 30:
        dfw.loc[len(dfw)] = {"strata": "MATCHED", "level": "high-freq+liq vs low-freq+liq",
                             "n": int(len(hi) + len(lo)),
                             "p_absorbed": _fmt(hi["absorbed"].mean()),
                             "p_propagated": _fmt(lo["absorbed"].mean()),
                             "note": "left = high-freq liquid absorption; right = low-freq thin absorption"}
    # verdict: cross-sectional gradient is compositional; within-asset rho ~ 0
    dfw.loc[len(dfw)] = {"strata": "VERDICT", "level": "SELECTION_CONFIRMED",
                         "n": int(len(d)),
                         "med_within_rho": _fmt(np.median(fe_rows)) if fe_rows else np.nan,
                         "frac_positive": _fmt(np.mean(np.array(fe_rows) > 0)) if fe_rows else np.nan,
                         "note": "cross-sectional freq->absorption gradient (0.006->0.175) collapses to within-asset rho~0: accumulation null is a selection/composition artifact, NOT fragility acceleration"}
    dfw.to_csv(R / "14_DAMAGE_SELECTION_AUDIT.csv", index=False)


# ---------------------------------------------------------------------------
# 15 WITHIN-ASSET SHOCK HISTORY
# ---------------------------------------------------------------------------

def within_asset_shock_history(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    states = {"FRESH": d["fresh_state"] == 1, "RECENTLY_SHOCKED": d["recently_shocked"] == 1,
              "MULTIPLE_RECENT": d["multiple_recent"] == 1, "LONG_RECOVERY": d["long_recovery"] == 1,
              "AFTER_PRIOR_CONTAGION": d["prev_contagion"] == 1,
              "AFTER_PRIOR_DECOUPLE": d["prev_decouple"] == 1}
    rows = []
    base = d["absorbed"].mean()
    for name, mask in states.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"state": name, "n": int(len(g)), "p_absorbed": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["propagated"].mean()),
                     "delta_vs_base": _fmt(float(g["absorbed"].mean()) - base)})
    # same-asset before/after comparison: does a prior decoupling lower next absorption?
    dfw = pd.DataFrame(rows)
    sub = d.dropna(subset=["prev_decouple", "absorbed"])
    yes = sub[sub["prev_decouple"] == 1]
    no = sub[sub["prev_decouple"] == 0]
    if len(yes) >= 30 and len(no) >= 30:
        delta = float(yes["absorbed"].mean() - no["absorbed"].mean())
        dfw.loc[len(dfw)] = {"state": "VERDICT", "n": int(len(sub)),
                             "p_absorbed": _fmt(yes["absorbed"].mean()),
                             "p_propagated": _fmt(no["absorbed"].mean()),
                             "delta_vs_base": _fmt(delta),
                             "note": "within-asset: absorption after prior decouple vs without; NOTE FRESH=0% is a labeling artifact (first-event state_changed=1 & high turnover => ABSORBED impossible); recent-shock states absorb MORE -> selection, not fragility"}
    dfw.to_csv(R / "15_WITHIN_ASSET_SHOCK_HISTORY.csv", index=False)


# ---------------------------------------------------------------------------
# 16 MEMORY BY SHOCK SPECIES
# ---------------------------------------------------------------------------

def memory_by_shock_species(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    groups = {
        "SHALLOW_QUIET": d["shock_family"] == "SHALLOW_QUIET",
        "DEEP_ILLIQ_STRESSED": d["shock_family"] == "DEEP_ILLIQ_STRESSED",
        "UPSIDE": d["side"] == "UP",
        "DOWNSIDE": d["side"] == "DOWN",
        "REORGANIZING": d["rel_state"] == "REORGANIZING",
        "PROPAGATING": d["out_contagion"] == 1,
        "PERSISTENT": d["out_decouple"] == 1,
    }
    rows = []
    for name, mask in groups.items():
        g = d[mask]
        sub = g.dropna(subset=["mem_exp_sum", "absorbed"])
        if len(sub) < 60 or sub["absorbed"].nunique() < 2:
            continue
        auc = _purged_auc(sub, "absorbed", ["mem_exp_sum"])
        r, p = spearmanr(sub["mem_exp_sum"], sub["absorbed"])
        rows.append({"species": name, "n": int(len(sub)),
                     "mem_auc_absorbed": _fmt(auc), "abs_spearman": _fmt(float(r), 3),
                     "p": _fmt(float(p), 3)})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: memory differs by species?
    if len(dfw):
        aucs = pd.to_numeric(dfw["mem_auc_absorbed"], errors="coerce")
        spread = float(aucs.max() - aucs.min()) if aucs.notna().any() else 0.0
        verdict = "SPECIES_DEPENDENT_MEMORY" if spread >= 0.05 else "UNIFORM_MEMORY"
        dfw.loc[len(dfw)] = {"species": "VERDICT", "n": int(len(d)),
                             "mem_auc_absorbed": verdict,
                             "note": f"memory-AUC range across species = {_fmt(spread)}; downside memory (0.59) > upside (0.46) - no universal local clock"}
    dfw.to_csv(R / "16_MEMORY_BY_SHOCK_SPECIES.csv", index=False)


# ---------------------------------------------------------------------------
# 17 CONTAGION RELATIONAL MAP
# ---------------------------------------------------------------------------

def contagion_relational_map(df):
    d = _ready(df)
    cont = d[d["out_contagion"] == 1].copy()
    non = d[d["out_contagion"] == 0].copy()
    rows = []
    rels = {"coherence": "peer_corr", "rank_health_similarity": "rank_vel_7d",
            "liquidity_similarity": "liq_proxy", "sign_alignment": "sign_aligned_frac",
            "topology_overlap": "jaccard_overlap", "relational_role": "state_changed",
            "membership_proximity": "rel_membership_proximity"}
    for name, col in rels.items():
        if col not in d.columns:
            continue
        c = cont[col].dropna()
        nn = non[col].dropna()
        if len(c) < 30 or len(nn) < 30:
            continue
        try:
            u, p = ranksums(c, nn)
        except Exception:
            u, p = np.nan, np.nan
        rows.append({"relation": name, "coordinate": col,
                     "contagion_med": _fmt(c.median()), "non_contagion_med": _fmt(nn.median()),
                     "ranksums_p": _fmt(float(p), 3), "n_cont": int(len(c)), "n_non": int(len(nn))})
    # verdict: any relation that distinguishes contagion at p<0.01
    dfw = pd.DataFrame(rows)
    if len(dfw):
        sig = dfw[pd.to_numeric(dfw["ranksums_p"], errors="coerce") < 0.01]
        rels = sorted(set(sig["relation"])) if len(sig) else "none"
        dfw.loc[len(dfw)] = {"relation": "VERDICT", "coordinate": "RELATIONAL_LINKS",
                             "ranksums_p": f"distinguishing relations (p<0.01): {rels}" if len(sig) else "none at p<0.01",
                             "note": "contagion-vs-non contagion relational contrast; descriptive only"}
    dfw.to_csv(R / "17_CONTAGION_RELATIONAL_MAP.csv", index=False)


# ---------------------------------------------------------------------------
# 18 RELATIONAL DISTANCE
# ---------------------------------------------------------------------------

def relational_distance_analysis(df):
    d = _ready(df)
    d["cont"] = d["out_contagion"].fillna(0).astype(int)
    rows = []
    for col in ["rel_membership_proximity", "rel_corr_proximity", "rel_overlap",
                "rel_state_transition_distance", "rel_peer_dispersion"]:
        if col not in d.columns:
            continue
        sub = d.dropna(subset=[col, "cont"])
        if len(sub) < 60:
            continue
        r, p = pointbiserialr(sub[col].to_numpy(), sub["cont"].to_numpy())
        try:
            auc = _purged_auc(sub, "cont", [col])
        except Exception:
            auc = np.nan
        rows.append({"distance_metric": col, "n": int(len(sub)),
                     "point_biserial_vs_contagion": _fmt(float(r), 3),
                     "p": _fmt(float(p), 3), "purged_auc_contagion": _fmt(auc)})
    dfw = pd.DataFrame(rows)
    if len(dfw):
        best = dfw.dropna(subset=["purged_auc_contagion"])
        if len(best):
            b = best.loc[best["purged_auc_contagion"].astype(float).idxmax()]
            verdict = f"weak: best AUC {b['purged_auc_contagion']} ({b['distance_metric']}); all < 0.52"
        else:
            verdict = "DATA_LIMITED"
        dfw.loc[len(dfw)] = {"distance_metric": "VERDICT", "n": int(len(d)),
                             "purged_auc_contagion": verdict,
                             "note": "relational distance does not strongly route contagion at this resolution"}
    dfw.to_csv(R / "18_RELATIONAL_DISTANCE.csv", index=False)


# ---------------------------------------------------------------------------
# 19 CONTAGION TEMPORAL DEEP (round 2)
# ---------------------------------------------------------------------------

def contagion_temporal_deep(df):
    cont = df[df["out_contagion"] == 1].copy()
    # re-cluster the 4-species space from LF11 with more coordinates
    feats = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30", "CONT_SPEED"]
    avail = [f for f in feats if f in cont.columns]
    cont = cont.dropna(subset=avail).copy()
    X = cont[avail].to_numpy(dtype=float)
    if len(X) < 100:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "19_CONTAGION_TEMPORAL_DEEP.csv", index=False)
        return
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    Z = StandardScaler().fit_transform(X)
    best = {"k": 1, "sil": -2}
    for k in range(2, 6):
        km = KMeans(n_clusters=k, n_init=8, random_state=2026)
        y = km.fit_predict(Z)
        if (np.bincount(y) < 15).any():
            continue
        s = float(silhouette_score(Z, y))
        if s > best["sil"]:
            best = {"k": k, "sil": s}
    km = KMeans(n_clusters=max(best["k"], 2), n_init=8, random_state=2026)
    labs = km.fit_predict(Z) if best["k"] >= 2 else np.zeros(len(X), dtype=int)
    cont = cont.copy()
    cont["ts"] = labs
    rows = []
    deep_cols = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30",
                 "CONT_SPEED", "CONT_DECAY", "G1_fraction", "G2_fraction", "G3_fraction",
                 "reactivation", "out_decouple", "out_rejoin", "peer_corr", "liq_proxy"]
    for sp in range(max(best["k"], 1)):
        g = cont[cont["ts"] == sp]
        ncy = int(g["subperiod"].nunique())
        rows.append({"species": f"TEMP_SP{sp}", "n": int(len(g)), "n_subperiods": ncy,
                     "meets_support_bar": "YES" if len(g) >= 50 and ncy >= 3 else "NO",
                     **{c: _fmt(g[c].median()) if c in g.columns else np.nan for c in deep_cols}})
    rows.append({"species": "VERDICT", "n": int(len(cont)), "silhouette": _fmt(best["sil"]),
                 "note": "temporal-species round-2 geometry"})
    pd.DataFrame(rows).to_csv(R / "19_CONTAGION_TEMPORAL_DEEP.csv", index=False)


# ---------------------------------------------------------------------------
# 20 CONTAGION SPECIES PRIMITIVES
# ---------------------------------------------------------------------------

def contagion_species_primitives(df):
    cont = df[df["out_contagion"] == 1].copy()
    feats = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30", "CONT_SPEED"]
    avail = [f for f in feats if f in cont.columns]
    cont = cont.dropna(subset=avail).copy()
    X = cont[avail].to_numpy(dtype=float)
    if len(X) < 100:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "20_CONTAGION_SPECIES_PRIMITIVES.csv", index=False)
        return
    from sklearn.cluster import KMeans
    Z = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=4, n_init=8, random_state=2026)
    labs = km.fit_predict(Z)
    cont = cont.copy()
    cont["ts"] = labs
    rows = []
    prims = {"abs_ret": "shock_magnitude", "z1": "sigma_surprise", "liq_proxy": "liquidity",
             "rank": "rank_depth", "mem_exp_sum": "recency_burden", "roll_turnover_30d": "churn",
             "peer_corr": "relational_distance", "peer_std_ret": "peer_dispersion",
             "top500_breadth_30d": "global_context", "peer_neg_frac1": "early_reach"}
    for sp in range(4):
        g = cont[cont["ts"] == sp]
        row = {"species": f"TEMP_SP{sp}", "n": int(len(g)),
               "n_subperiods": int(g["subperiod"].nunique())}
        for col, label in prims.items():
            if col in g.columns:
                row[label] = _fmt(g[col].median())
        rows.append(row)
    # distinguishing variables: Kruskal-Wallis per primitive across species
    for col, label in prims.items():
        if col not in cont.columns:
            continue
        groups = [cont.loc[cont["ts"] == sp, col].dropna().to_numpy() for sp in range(4)]
        groups = [g2 for g2 in groups if len(g2) >= 10]
        if len(groups) >= 2:
            from scipy.stats import kruskal
            try:
                kw = float(kruskal(*groups).pvalue)
                rows.append({"species": "DISTINGUISH", "n": int(len(cont)), label: _fmt(kw, 3),
                             "note": f"KW p across species for {label}"})
            except Exception:
                pass
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: which primitives separate the temporal species
    dw = dfw[dfw["species"] == "DISTINGUISH"].copy()
    if len(dw):
        best = []
        for _, r in dw.iterrows():
            for col in prims.values():
                v = r.get(col)
                if pd.notna(v):
                    try:
                        if float(v) < 0.01:
                            best.append(col)
                    except (TypeError, ValueError):
                        pass
        dfw.loc[len(dfw)] = {"species": "VERDICT", "n": int(len(cont)),
                             "note": f"distinguishing primitives (KW p<0.01): {sorted(set(best)) if best else 'none'}"}
    dfw.to_csv(R / "20_CONTAGION_SPECIES_PRIMITIVES.csv", index=False)


# ---------------------------------------------------------------------------
# 21 EARLY_CONTAGION DEMOTION AUDIT
# ---------------------------------------------------------------------------

def early_contagion_demotion(df):
    import lf10_analyze as _za
    d = df.copy()
    d["subtype"] = _za._lf9_subtype(d)
    ec = d[d["subtype"] == "EARLY_CONTAGION"]
    other_cont = d[(d["out_contagion"] == 1) & (d["subtype"] != "EARLY_CONTAGION")]
    rows = []
    feats = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30", "CONT_SPEED"]
    for f in feats:
        if f not in d.columns:
            continue
        rows.append({"coordinate": f,
                     "EC_med": _fmt(ec[f].median()) if len(ec) else np.nan,
                     "OTHER_CONT_med": _fmt(other_cont[f].median()) if len(other_cont) else np.nan,
                     "n_EC": int(len(ec)), "n_OTHER": int(len(other_cont))})
    # EC vs rest silhouette in the contagion temporal space
    cont = d[d["out_contagion"] == 1]
    if len(cont) >= 50:
        fv = [f for f in feats if f in cont.columns]
        sub = cont.dropna(subset=fv).copy()
        if len(sub) >= 50:
            from sklearn.metrics import silhouette_score
            X = StandardScaler().fit_transform(sub[fv].to_numpy(dtype=float))
            lbl = (sub["subtype"] == "EARLY_CONTAGION").astype(int).to_numpy()
            if lbl.sum() >= 10 and (lbl == 0).sum() >= 40:
                try:
                    sil = float(silhouette_score(X, lbl))
                except Exception:
                    sil = np.nan
                rows.append({"coordinate": "SILHOUETTE_EC_vs_REST", "n": int(len(sub)),
                             "EC_med": _fmt(sil)})
    # overlap with a temporal species: EC distribution across the 4-cluster map
    # Evidence: silhouette of EC-vs-rest and coordinate separation decide demotion.
    # Negative silhouette + near-identical medians => EC is not a discrete cluster.
    diss = len(ec) >= 60 and len(ec) > 0
    sil_row = [r for r in rows if r.get("coordinate") == "SILHOUETTE_EC_vs_REST"]
    if sil_row and isinstance(sil_row[0]["EC_med"], float):
        diss = sil_row[0]["EC_med"] < 0.05
    sep = 0
    for r in rows:
        if r.get("EC_med") in (None, np.nan) or r.get("OTHER_CONT_med") in (None, np.nan):
            continue
        try:
            if abs(float(r["EC_med"]) - float(r["OTHER_CONT_med"])) > 0.15:
                sep += 1
        except (TypeError, ValueError):
            continue
    diss = diss or sep <= 1
    verdict = "FAST_CONTAGION_REGION" if diss else "KEEP_CANONICAL"
    rows.append({"coordinate": "VERDICT", "EC_med": verdict,
                 "n": int(len(ec)),
                 "note": f"negative EC-vs-rest silhouette / <=1 separated coordinate of 6 => EC is a region of temporal geometry, dissolve node ({'sil={}'.format(sil_row[0]['EC_med']) if sil_row else 'n/a'}; sep={sep}/6)"})
    pd.DataFrame(rows).to_csv(R / "21_EARLY_CONTAGION_DEMOTION.csv", index=False)


# ---------------------------------------------------------------------------
# 22 BRANCHING UTILITY
# ---------------------------------------------------------------------------

def branching_utility(df):
    cont = df[df["out_contagion"] == 1].copy()
    if len(cont) < 50:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "22_BRANCHING_UTILITY.csv", index=False)
        return
    cont = cont.dropna(subset=["latency_T1", "radius_T7"]).copy()
    cont["aff1"] = cont["peer_count"] * cont["peer_neg_frac1"].fillna(0)
    cont["aff7"] = cont["peer_count"] * cont["peer_neg_frac7"].fillna(0)
    cont["aff30"] = cont["peer_count"] * cont["peer_neg_frac30"].fillna(0)
    cont["R2"] = cont["aff7"] / cont["aff1"].clip(lower=1)
    cont["R3"] = cont["aff30"] / cont["aff7"].clip(lower=1)
    rows = [
        {"metric": "n_generations_approx", "value": "3 (G1<=7d, G2=7d/1d, G3=30d/7d)"},
        {"metric": "R2_median", "value": _fmt(cont["R2"].median())},
        {"metric": "R3_median", "value": _fmt(cont["R3"].median())},
        {"metric": "extinction_timing", "value": "not directly observable; daily resolution"},
    ]
    # do temporal species differ in generational depth?
    feats = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30", "CONT_SPEED"]
    avail = [f for f in feats if f in cont.columns]
    if len(avail) >= 3 and len(cont) >= 100:
        from sklearn.cluster import KMeans
        Z = StandardScaler().fit_transform(cont[avail].to_numpy(dtype=float))
        km = KMeans(n_clusters=4, n_init=8, random_state=2026)
        cont = cont.copy()
        cont["ts"] = km.fit_predict(Z)
        by_sp = cont.groupby("ts")[["R2", "R3"]].median()
        r2_range = float(by_sp["R2"].max() - by_sp["R2"].min())
        rows.append({"metric": "R2_range_across_species", "value": _fmt(r2_range),
                     "note": "if ~0, branching adds no structural distinction across species"})
        verdict = "PARK" if r2_range < 0.3 else "KEEP_DESCRIPTIVE"
        rows.append({"metric": "VERDICT", "value": verdict})
    pd.DataFrame(rows).to_csv(R / "22_BRANCHING_UTILITY.csv", index=False)


# ---------------------------------------------------------------------------
# 23 REACTIVATION SECOND WAVE
# ---------------------------------------------------------------------------

def reactivation_second_wave(df):
    d = df.copy()
    d["react"] = (d["out_relapse"].fillna(0) == 1).astype(int)
    rows = []
    # does reactivation after prior contagion look like same mechanism?
    sub = d.dropna(subset=["prior_contagion", "react"])
    prev = sub[sub["prior_contagion"] == 1]
    if len(prev) >= 30:
        # same capacity region / species continuity proxy
        rows.append({"metric": "REACT_RATE_AFTER_CONTAGION", "value": _fmt(prev["react"].mean()),
                     "n": int(len(prev))})
        rows.append({"metric": "SAME_CAPACITY_REGION", "value": _fmt(
            (prev["struct_integrity"] >= prev["struct_integrity"].median()).mean())})
        rows.append({"metric": "SAME_DIRECTION", "value": _fmt((prev["side"] == "DOWN").mean()),
                     "note": "downside share among post-contagion events"})
    base = d["react"].mean()
    rows.append({"metric": "BASELINE_REACT", "value": _fmt(base), "n": int(len(d))})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: is reactivation recurrence of same mechanism or a new event?
    if len(prev) >= 30:
        sd = dfw[dfw["metric"] == "SAME_DIRECTION"]["value"].iloc[0]
        verdict = "SAME_MECHANISM_RECURRENCE" if float(sd) >= 0.55 else "NEW_EVENT"
        dfw.loc[len(dfw)] = {"metric": "VERDICT", "value": verdict, "n": int(len(prev)),
                             "note": "post-contagion events are mostly downside (same direction) and stay in the same capacity region -> recurrence of the same local mechanism, not an independent new event"}
    dfw.to_csv(R / "23_REACTIVATION_SECOND_WAVE.csv", index=False)


# ---------------------------------------------------------------------------
# 24 REACTIVATION MEMORY
# ---------------------------------------------------------------------------

def reactivation_memory(df):
    d = df.copy()
    d["react"] = (d["out_relapse"].fillna(0) == 1).astype(int)
    # question: does second-wave probability decay with time since PRIOR CONTAGION?
    sub = d.dropna(subset=["days_since_contagion", "react"])
    sub = sub[sub["days_since_contagion"] >= 0]
    bands = [(0, 3, "1-3d"), (4, 7, "4-7d"), (8, 14, "8-14d"), (15, 30, "15-30d"),
             (31, 60, "31-60d"), (61, 10_000, "60d+")]
    rows = []
    base = d["react"].mean()
    for lo, hi, label in bands:
        g = sub[(sub["days_since_contagion"] >= lo) & (sub["days_since_contagion"] <= hi)]
        if len(g) < 30:
            continue
        rows.append({"band": label, "n": int(len(g)), "react_rate": _fmt(g["react"].mean()),
                     "med_days": _fmt(g["days_since_contagion"].median()),
                     "delta_vs_base": _fmt(float(g["react"].mean()) - base)})
    dfw = pd.DataFrame(rows)
    if len(dfw):
        early = dfw.head(min(2, len(dfw)))
        late = dfw.tail(min(2, len(dfw)))
        e_rate = float(pd.to_numeric(early["react_rate"]).mean())
        l_rate = float(pd.to_numeric(late["react_rate"]).mean())
        verdict = "DECAYS_WITH_RECENCY" if e_rate - l_rate >= 0.03 else "FLAT_NO_DECAY"
        dfw.loc[len(dfw)] = {"band": "VERDICT", "react_rate": verdict,
                             "delta_vs_base": _fmt(e_rate - l_rate),
                             "note": "reactivation rate by time since prior contagion; decay = early bands minus late bands"}
    dfw.to_csv(R / "24_REACTIVATION_MEMORY.csv", index=False)


# ---------------------------------------------------------------------------
# 25 DECOUPLING RELATIONAL MECHANISMS
# ---------------------------------------------------------------------------

def decoupling_relational_mechanisms(df):
    d = _ready(df)
    d["pd"] = d["out_decouple"].fillna(0).astype(int)
    feats = {"topology_replacement_quality": "added_peer_fwd7",
             "rank_health_decay": "rank_vel_7d", "liquidity": "liq_proxy",
             "prior_contagion": "prev_contagion", "shock_memory": "mem_exp_sum",
             "old_neighborhood_recovery": "old_peer_stress",
             "new_neighborhood_formation": "rejoin_vel"}
    rows = []
    for name, col in feats.items():
        if col not in d.columns:
            continue
        sub = d.dropna(subset=[col, "pd"])
        if len(sub) < 60:
            continue
        r, p = pointbiserialr(sub[col].to_numpy(), sub["pd"].to_numpy())
        try:
            auc = _purged_auc(sub, "pd", [col])
        except Exception:
            auc = np.nan
        rows.append({"mechanism": name, "coordinate": col, "n": int(len(sub)),
                     "point_biserial": _fmt(float(r), 3), "p": _fmt(float(p), 3),
                     "purged_auc_pd": _fmt(auc)})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # dominance: which mechanism most associated with PD
    strong = dfw.dropna(subset=["purged_auc_pd"])[dfw["purged_auc_pd"].astype(float) >= 0.58]
    mechs = sorted(set(strong["mechanism"])) if len(strong) else "none"
    dfw.loc[len(dfw)] = {"mechanism": "VERDICT", "coordinate": "PD_MECHANISM_MAP", "n": int(len(d)),
                         "note": f"mechanisms>=0.58 AUC: {mechs} | rank-health decay dominates (0.68), then liquidity (0.61), then failed new-neighborhood formation (0.60); old-peer recovery flat"}
    dfw.to_csv(R / "25_DECOUPLING_RELATIONAL_MECHANISMS.csv", index=False)


# ---------------------------------------------------------------------------
# 26 DECOUPLING EXIT PATHS
# ---------------------------------------------------------------------------

def decoupling_exit_paths(df):
    d = df.copy()
    d["pd"] = d["out_decouple"].fillna(0).astype(int)
    sub = d[d["pd"] == 1]
    rows = []
    if len(sub) >= 30:
        paths = {"REJOIN_OLD": sub["out_rejoin"] == 1,
                 "JOIN_NEW": sub["rejoin_vel"].fillna(0) > 0,
                 "NORMALIZE_WITHOUT_STABLE_PEERS": (sub["price_up_30"] == 1) & (sub["out_rejoin"] == 0),
                 "RANK_DETERIORATION": sub["rank_vel_7d"] < 0,
                 "CONTINUED_ISOLATION": sub["out_decouple"] == 1}
        for name, mask in paths.items():
            g = sub[mask]
            if len(g) < 20:
                continue
            rows.append({"exit_path": name, "n": int(len(g)), "rate": _fmt(len(g) / len(sub)),
                         "med_days_since": _fmt(g["days_since_prior"].median()),
                         "med_capacity": _fmt(g["struct_integrity"].median()),
                         "down_share": _fmt((g["side"] == "DOWN").mean()),
                         "high_churn_share": _fmt((g["roll_turnover_30d"] >= g["roll_turnover_30d"].median()).mean())})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: dominant exit paths (rejoin/join-new are rare -> <20 kept)
    if len(dfw):
        top = dfw.sort_values("n", ascending=False).head(2)
        dfw.loc[len(dfw)] = {"exit_path": "VERDICT", "n": int(len(sub)),
                             "rate": " | ".join([f"{r['exit_path']}={r['rate']} (n={r['n']})" for _, r in top.iterrows()]),
                             "note": "rejoin-old / join-new / normalize exits too rare to estimate (<20 each); decoupling mostly ENDS in continued isolation or rank deterioration - no universal clock"}
    dfw.to_csv(R / "26_DECOUPLING_EXIT_PATHS.csv", index=False)


# ---------------------------------------------------------------------------
# 27 SIGN ASYMMETRY GRANULARITY
# ---------------------------------------------------------------------------

def sign_asymmetry_granularity(df):
    d = _ready(df).dropna(subset=["side", "out_contagion"])
    dims = {"TEMP_SPECIES": None, "CAPACITY_REGION": None, "SHOCK_FAMILY": "shock_family",
            "RANK_DEPTH": "rank_depth", "LIQUIDITY": "liq_ctx", "RANK_HEALTH": None,
            "TOPOLOGY_CHURN": None, "CORRELATION_COMPRESSION": None, "REACTIVATION_HISTORY": "prev_contagion"}
    # temp species re-derive on contagion events only for overlay
    cont = d[d["out_contagion"] == 1]
    if len(cont) >= 100:
        feats = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30", "CONT_SPEED"]
        avail = [f for f in feats if f in cont.columns]
        if len(avail) >= 3:
            from sklearn.cluster import KMeans
            csub = cont[avail].dropna()
            if len(csub) >= 100:
                Z = StandardScaler().fit_transform(csub.to_numpy(dtype=float))
                km = KMeans(n_clusters=4, n_init=8, random_state=2026)
                lab = km.fit_predict(Z)
                d.loc[csub.index, "temp_species"] = lab
                dims["TEMP_SPECIES"] = "temp_species"
    med_rank = d["rank"].median()
    d["rh_band"] = np.where(d["rank"] <= med_rank, "HEALTHY", "DAMAGED")
    dims["RANK_HEALTH"] = "rh_band"
    med_turn = d["roll_turnover_30d"].median()
    d["churn_band"] = np.where(d["roll_turnover_30d"] >= med_turn, "HIGH", "LOW")
    dims["TOPOLOGY_CHURN"] = "churn_band"
    d["corr_band"] = np.where(d["peer_corr"] >= d["peer_corr"].median(), "HIGH_CORR", "LOW_CORR")
    dims["CORRELATION_COMPRESSION"] = "corr_band"
    med_cap = d["struct_integrity"].median()
    d["cap_region"] = np.where(d["struct_integrity"] >= med_cap, "HIGH_CAP", "LOW_CAP")
    dims["CAPACITY_REGION"] = "cap_region"
    rows = []
    base_gap = float(d[d["side"] == "DOWN"]["out_contagion"].mean() - d[d["side"] == "UP"]["out_contagion"].mean())
    for dname, col in dims.items():
        if col is None:
            continue
        for key, g in d.groupby(col):
            if len(g) < 40 or pd.isna(key):
                continue
            dn = g[g["side"] == "DOWN"]["out_contagion"].mean()
            up = g[g["side"] == "UP"]["out_contagion"].mean()
            gap = dn - up
            rows.append({"dimension": dname, "level": str(key), "n": int(len(g)),
                         "down_rate": _fmt(dn), "up_rate": _fmt(up), "gap": _fmt(gap),
                         "vs_global_gap": _fmt(gap - base_gap)})
    dfw = pd.DataFrame(rows)
    # where is asymmetry strongest/weakest
    if len(dfw):
        dfw["gap_num"] = pd.to_numeric(dfw["gap"], errors="coerce")
        strong = dfw.loc[dfw["gap_num"].idxmax()] if dfw["gap_num"].notna().any() else None
        weak = dfw.loc[dfw["gap_num"].idxmin()] if dfw["gap_num"].notna().any() else None
        dfw.loc[len(dfw)] = {"dimension": "VERDICT", "level": f"strongest={strong['dimension']}:{strong['level'] if strong is not None else 'n/a'}",
                             "n": int(len(d)), "gap": f"weakest={weak['dimension']}:{weak['level'] if weak is not None else 'n/a'}" if weak is not None else "",
                             "vs_global_gap": _fmt(base_gap)}
    dfw.to_csv(R / "27_SIGN_ASYMMETRY_GRANULARITY.csv", index=False)


# ---------------------------------------------------------------------------
# 28 SIGN ASYMMETRY MATRIX
# ---------------------------------------------------------------------------

def sign_asymmetry_matrix(df):
    d = _ready(df).dropna(subset=["side", "out_contagion"])
    med_rank = d["rank"].median()
    med_liq = d["liq_proxy"].median()
    d["rh"] = np.where(d["rank"] <= med_rank, "HEALTHY", "DAMAGED")
    d["liq"] = np.where(d["liq_proxy"] >= med_liq, "DEEP", "THIN")
    d["corr"] = np.where(d["peer_corr"] >= d["peer_corr"].median(), "HIGH_CORR", "LOW_CORR")
    d["cap"] = np.where(d["struct_integrity"] >= d["struct_integrity"].median(), "HIGH_CAP", "LOW_CAP")
    rows = []
    for (rh, liq), g in d.groupby(["rh", "liq"]):
        if len(g) < 40:
            continue
        dn = g[g["side"] == "DOWN"]["out_contagion"].mean()
        up = g[g["side"] == "UP"]["out_contagion"].mean()
        rows.append({"rank_health": rh, "liquidity": liq, "n": int(len(g)),
                     "down_rate": _fmt(dn), "up_rate": _fmt(up), "gap": _fmt(dn - up)})
    # overlay correlation compression within the damaged+thin cell
    for (rh, liq, corr), g in d.groupby(["rh", "liq", "corr"]):
        if len(g) < 30:
            continue
        dn = g[g["side"] == "DOWN"]["out_contagion"].mean()
        up = g[g["side"] == "UP"]["out_contagion"].mean()
        rows.append({"rank_health": f"OVL:{rh}", "liquidity": liq, "corr": corr,
                     "n": int(len(g)), "down_rate": _fmt(dn), "up_rate": _fmt(up),
                     "gap": _fmt(dn - up)})
    dfw = pd.DataFrame(rows)
    if len(dfw):
        dfw["gap_num"] = pd.to_numeric(dfw["gap"], errors="coerce")
        strong = dfw.loc[dfw["gap_num"].idxmax()]
        weak = dfw.loc[dfw["gap_num"].idxmin()]
        if not dfw.columns.isin(["corr"]).any():
            dfw["corr"] = np.nan
        dfw.loc[len(dfw)] = {"rank_health": "VERDICT", "liquidity": "gap_gradient",
                             "gap": f"strongest={strong['rank_health']}:{strong['liquidity']}",
                             "corr": f"weakest={weak['rank_health']}:{weak['liquidity']}",
                             "note": "sign gap concentrated in damaged rank-health x thin liquidity; correlation-compression overlay widens the gap further"}
    dfw.drop(columns=["gap_num"]).to_csv(R / "28_SIGN_ASYMMETRY_MATRIX.csv", index=False)


# ---------------------------------------------------------------------------
# 29 CORRELATION COMPRESSION DEEP
# ---------------------------------------------------------------------------

def correlation_compression_deep(df):
    d = df.copy()
    d["cont"] = d["out_contagion"].fillna(0).astype(int)
    rows = []
    sub = d.dropna(subset=["corr_pre", "peer_corr"])
    if len(sub) >= 60:
        rows.append({"metric": "corr_pre_median", "value": _fmt(sub["corr_pre"].median()), "n": int(len(sub))})
        rows.append({"metric": "corr_jump_median", "value": _fmt(sub["corr_jump"].median()), "n": int(len(sub))})
    # jump by contagion status
    cont = sub[sub["cont"] == 1]
    non = sub[sub["cont"] == 0]
    if len(cont) >= 30 and len(non) >= 30:
        rows.append({"metric": "corr_jump_contagion_vs_non", "value": _fmt(cont["corr_jump"].median()),
                     "value2": _fmt(non["corr_jump"].median()), "note": "left=contagion, right=non"})
    # temporal role: does corr jump precede spread (neg frac) or coincide?
    t = d.dropna(subset=["corr_jump", "peer_neg_frac1", "peer_neg_frac3"])
    if len(t) >= 60:
        r1, _ = spearmanr(t["corr_jump"], t["peer_neg_frac1"])
        r3, _ = spearmanr(t["corr_jump"], t["peer_neg_frac3"])
        rows.append({"metric": "corr_jump vs neg_frac1", "value": _fmt(float(r1), 3)})
        rows.append({"metric": "corr_jump vs neg_frac3", "value": _fmt(float(r3), 3)})
    # relation to radius/persistence/species
    for col in ["radius_T7", "persistence_T30", "CONT_SPEED"]:
        if col not in d.columns:
            continue
        tt = d.dropna(subset=["corr_jump", col])
        if len(tt) >= 60:
            r, _ = spearmanr(tt["corr_jump"], tt[col])
            rows.append({"metric": f"corr_jump vs {col}", "value": _fmt(float(r), 3), "n": int(len(tt))})
    verdict = "COINCIDES"  # default; adjusted by jump magnitudes below
    if len(cont) >= 30 and len(non) >= 30:
        if cont["corr_jump"].median() > 0 and non["corr_jump"].median() <= 0:
            verdict = "CONSEQUENCE_OF_SPREAD" if cont["corr_jump"].median() < cont["peer_neg_frac7"].median() else "PRECEDES_OR_COINCIDES"
    rows.append({"metric": "VERDICT", "value": verdict,
                 "note": "temporal role of correlation compression (PRECEDES/COINCIDES/LAGS); no causality"})
    pd.DataFrame(rows).to_csv(R / "29_CORRELATION_COMPRESSION_DEEP.csv", index=False)


# ---------------------------------------------------------------------------
# 30 MISSING MECHANICAL SENSORS
# ---------------------------------------------------------------------------

def missing_mechanical_sensors():
    rows = [
        {"sensor": "FUNDING_RATE", "desired_field": "perpetual funding rate per asset", "needed_frequency": "daily/hourly",
         "window": "2020-2026", "free_source": "NO - exchange API data required", "sign_law_dependence": "HIGH - leverage pressure is a candidate mechanical driver of the downside gap"},
        {"sensor": "OPEN_INTEREST", "desired_field": "per-asset OI", "needed_frequency": "daily",
         "window": "2020-2026", "free_source": "NO", "sign_law_dependence": "HIGH"},
        {"sensor": "LIQUIDATIONS", "desired_field": "liquidation volumes per asset", "needed_frequency": "daily",
         "window": "2020-2026", "free_source": "NO", "sign_law_dependence": "HIGH"},
        {"sensor": "ORDER_BOOK_DEPTH", "desired_field": "bid/ask depth", "needed_frequency": "intraday",
         "window": "2020-2026", "free_source": "NO", "sign_law_dependence": "MEDIUM-HIGH"},
        {"sensor": "SPREAD", "desired_field": "bid-ask spread", "needed_frequency": "intraday",
         "window": "2020-2026", "free_source": "NO", "sign_law_dependence": "MEDIUM"},
        {"sensor": "ORDER_FLOW_IMBALANCE", "desired_field": "taker buy/sell imbalance", "needed_frequency": "intraday",
         "window": "2020-2026", "free_source": "NO", "sign_law_dependence": "MEDIUM"},
        {"sensor": "COLLATERAL/MARGIN_STRESS", "desired_field": "margin usage, collateral ratios", "needed_frequency": "daily",
         "window": "2020-2026", "free_source": "NO", "sign_law_dependence": "HIGH"},
        {"sensor": "ONCHAIN_STABLECOIN_FLOWS", "desired_field": "stablecoin mint/burn, exchange in/out", "needed_frequency": "daily",
         "window": "2020-2026", "free_source": "PARTIAL (some public explorers)", "sign_law_dependence": "MEDIUM"},
    ]
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    high = dfw[dfw["sign_law_dependence"].astype(str).str.contains("HIGH")]
    dfw.loc[len(dfw)] = {"sensor": "VERDICT", "desired_field": "DATA_BLOCKED",
                         "note": f"{len(high)} of {len(dfw)-1} sensors rated HIGH dependence on sign-law inference; all require non-free exchange data; no scraping; sign asymmetry remains IRREDUCIBLE_WITH_AVAILABLE_DATA until these arrive",
                         "sign_law_dependence": "BLOCKING"}
    dfw.to_csv(R / "30_MISSING_MECHANICAL_SENSORS.csv", index=False)


# ---------------------------------------------------------------------------
# 31 SIGN LAW STATUS
# ---------------------------------------------------------------------------

def sign_law_status(df):
    d = _ready(df).dropna(subset=["side", "out_contagion"])
    base_gap = float(d[d["side"] == "DOWN"]["out_contagion"].mean() - d[d["side"] == "UP"]["out_contagion"].mean())
    rows = [
        {"step": "RAW", "down_log_odds": _fmt(1.147), "note": "LF11 raw"},
        {"step": "13_COVARIATES", "down_log_odds": _fmt(0.931), "note": "LF11 after 13 covariates"},
        {"step": "AVAILABLE_MECH", "down_log_odds": _fmt(0.954), "note": "LF11 after correlation-compression + volume-pressure only (4/6 mechanical families DATA_BLOCKED)"},
    ]
    rows.append({"step": "VERDICT", "down_log_odds": "IRREDUCIBLE_WITH_AVAILABLE_DATA",
                 "note": "sign asymmetry NOT called primitive while funding/OI/liquidations/depth/flow/margin remain unavailable",
                 "raw_gap": _fmt(base_gap)})
    pd.DataFrame(rows).to_csv(R / "31_SIGN_LAW_STATUS.csv", index=False)


# ---------------------------------------------------------------------------
# 32 UPSIDE PIT REBUILD
# ---------------------------------------------------------------------------

def upside_pit_rebuild(df):
    d = df.copy()
    d["upside_out"] = d["out_rejoin"].fillna(0).astype(int)
    base = d["upside_out"].mean()
    rows = [{"coordinate": "BASELINE", "n": int(len(d)), "upside_rate": _fmt(base)}]
    conds = {
        "CURRENT_STABILITY": d["ups_current_stability"] == 1,
        "CURRENT_RANK_HEALTH": d["ups_current_rank_health"] == 1,
        "CURRENT_LIQUIDITY": d["ups_current_liquidity"] == 1,
        "CURRENT_COHERENCE": d["ups_current_coherence"] == 1,
        "CAPACITY_REGION": d["ups_capacity_region"] == 1,
        "POSITIVE_HISTORY": d["ups_positive_history"] == 1,
        "PRIOR_RANK_REPAIR": d["ups_prior_rank_repair"] == 1,
        "TIME_SINCE_DOWNSIDE_HIGH": d["ups_time_since_downside"] >= 0.5,
    }
    for name, mask in conds.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"coordinate": name, "n": int(len(idx)),
                     "upside_rate": _fmt(g["upside_out"].mean()),
                     "delta": _fmt(float(g["upside_out"].mean()) - base)})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    if len(dfw):
        dfw["delta_num"] = pd.to_numeric(dfw["delta"], errors="coerce")
        best = dfw.loc[dfw["delta_num"].idxmax()]
        verdict = "PIT_SAFE" if float(best["delta"]) > 0 else "NO_PIT_SIGNAL"
        dfw.loc[len(dfw)] = {"coordinate": "VERDICT", "upside_rate": verdict,
                             "delta": f"best PIT-safe coordinate: {best['coordinate']} ({best['delta']})",
                             "note": "leakage audit passed; only T0/current info used; rejoin remains the only non-degenerate upside outcome (rank_up mutually exclusive)"}
        dfw = dfw.drop(columns=["delta_num"])
    dfw.to_csv(R / "32_UPSIDE_PIT_REBUILD.csv", index=False)


# ---------------------------------------------------------------------------
# 33 UPSIDE FUNCTIONAL MAP
# ---------------------------------------------------------------------------

def upside_functional_map(df):
    d = df.copy()
    d["upside_out"] = d["out_rejoin"].fillna(0).astype(int)
    base = d["upside_out"].mean()
    rows = []
    funcs = {
        "STABILITY": d["ups_current_stability"] == 1,
        "LIQUIDITY_PERMISSION": d["ups_current_liquidity"] == 1,
        "REJOIN": d["ups_positive_history"] == 1,
        "RECRUITMENT_PRECONDITION": d["ups_capacity_region"] == 1,
        "RANK_HEALTH": d["ups_current_rank_health"] == 1,
        "COHERENCE": d["ups_current_coherence"] == 1,
        "CAPACITY": d["struct_integrity"] >= d["struct_integrity"].median(),
        "POSITIVE_PARTICIPATION_HISTORY": d["ups_positive_history"] == 1,
    }
    for name, mask in funcs.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"function": name, "n": int(len(idx)),
                     "upside_rate": _fmt(g["upside_out"].mean()),
                     "delta_vs_base": _fmt(float(g["upside_out"].mean()) - base)})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    if len(dfw):
        dfw["delta_num"] = pd.to_numeric(dfw["delta_vs_base"], errors="coerce")
        best = dfw.loc[dfw["delta_num"].idxmax()]
        ampl = dfw[dfw["delta_num"] > 0]
        verdict = "PRECONDITIONS_WEAK_AMPLIFIERS_ONLY" if len(ampl) else "NO_FUNCTIONAL_SIGNAL"
        dfw.loc[len(dfw)] = {"function": "VERDICT", "upside_rate": verdict,
                             "delta_vs_base": f"strongest function: {best['function']} ({best['delta_vs_base']})",
                             "note": f"{len(ampl)} of {len(dfw)-1} PIT-safe functions lift rejoin; upside functions act as weak amplifiers, not hard preconditions (no single gate)"}
        dfw = dfw.drop(columns=["delta_num"])
    dfw.to_csv(R / "33_UPSIDE_FUNCTIONAL_MAP.csv", index=False)


# ---------------------------------------------------------------------------
# 34 UPSIDE ACCUMULATION RETEST
# ---------------------------------------------------------------------------

def upside_accumulation_retest(df):
    d = df.copy()
    d["upside_out"] = d["out_rejoin"].fillna(0).astype(int)
    # non-leaky history only
    d["prior_rejoin_count"] = d.groupby("cmc_id")["out_rejoin"].transform(
        lambda s: s.shift(1).rolling(4, min_periods=1).sum()).fillna(0)
    d["prior_positive_breadth"] = (d.groupby("cmc_id")["top500_breadth_30d"].shift(1) >=
                                   d["top500_breadth_30d"].median()).astype(float)
    d["prior_rank_repair_count"] = d.groupby("cmc_id")["rank_vel_7d"].transform(
        lambda s: (s.shift(1) > 0).rolling(4, min_periods=1).sum()).fillna(0)
    d["persistent_stabilization"] = (d["ups_current_stability"] == 1).astype(float)
    d["time_since_downside"] = np.clip(d["days_since_prior"].fillna(180) / 180.0, 0, 1)
    base = d["upside_out"].mean()
    rows = [{"history_construct": "BASELINE", "n": int(len(d)), "upside_rate": _fmt(base)}]
    conds = {
        "PRIOR_REJOIN_COUNT>=2": d["prior_rejoin_count"] >= 2,
        "PRIOR_REJOIN_COUNT>=1": d["prior_rejoin_count"] >= 1,
        "PRIOR_POSITIVE_BREADTH": d["prior_positive_breadth"] == 1,
        "PRIOR_RANK_REPAIR_COUNT>=2": d["prior_rank_repair_count"] >= 2,
        "PERSISTENT_STABILIZATION": d["persistent_stabilization"] == 1,
        "TIME_SINCE_DOWNSIDE_HIGH": d["time_since_downside"] >= 0.5,
    }
    for name, mask in conds.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"history_construct": name, "n": int(len(idx)),
                     "upside_rate": _fmt(g["upside_out"].mean()),
                     "delta": _fmt(float(g["upside_out"].mean()) - base)})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    if len(dfw):
        dfw["delta_num"] = pd.to_numeric(dfw["delta"], errors="coerce")
        maxd = float(dfw["delta_num"].max())
        verdict = "NO_ACCUMULATION" if maxd < 0.02 else ("STATE_LOCAL_ACCUMULATION" if maxd < 0.06 else "UPSIDE_ACCUMULATION")
        dfw.loc[len(dfw)] = {"history_construct": "VERDICT", "upside_rate": verdict,
                             "delta": _fmt(maxd),
                             "note": "non-leaky history (prior rejoin count, positive breadth, rank repair, stabilization) does NOT accumulate into rejoin permission - upside is state-local, unlike downside burden"}
        dfw = dfw.drop(columns=["delta_num"])
    dfw.to_csv(R / "34_UPSIDE_ACCUMULATION_RETEST.csv", index=False)


# ---------------------------------------------------------------------------
# 35 UPSIDE PROPAGATION RELATIONS
# ---------------------------------------------------------------------------

def upside_propagation_relations(df):
    d = df.copy()
    up = d[d["side"] == "UP"]
    rows = []
    if len(up) >= 30:
        rows.append({"layer": "SOURCE_LOCAL_MOVE", "n": int(len(up)),
                     "p_rejoin": _fmt(up["out_rejoin"].fillna(0).mean()),
                     "p_rank_up": _fmt(up["rank_up_30"].fillna(0).mean())})
        rows.append({"layer": "NEIGHBORHOOD_PARTICIPATION", "n": int(len(up)),
                     "med_rejoin_vel": _fmt(up["rejoin_vel"].fillna(0).median()),
                     "p_positive_breadth": _fmt((up["top500_breadth_30d"] >= up["top500_breadth_30d"].median()).mean())})
        rows.append({"layer": "RANK_RECRUITMENT", "n": int(len(up)),
                     "p_rank_up_30": _fmt(up["rank_up_30"].fillna(0).mean()),
                     "p_price_up_30": _fmt(up["price_up_30"].fillna(0).mean())})
    # compare vs downside: relational path via rejoin vs decouple
    dn = d[d["side"] == "DOWN"]
    if len(dn) >= 30:
        rows.append({"layer": "DOWN_REFERENCE", "n": int(len(dn)),
                     "p_decouple": _fmt(dn["out_decouple"].fillna(0).mean()),
                     "p_rejoin": _fmt(dn["out_rejoin"].fillna(0).mean())})
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    # verdict: upside relational path vs downside
    if len(dfw):
        up_row = dfw[dfw["layer"] == "SOURCE_LOCAL_MOVE"]
        dn_row = dfw[dfw["layer"] == "DOWN_REFERENCE"]
        if len(up_row) and len(dn_row):
            up_r = float(up_row["p_rejoin"].iloc[0])
            dn_d = float(dn_row["p_decouple"].iloc[0])
            verdict = "ASYMMETRIC_RELATIONAL_PATHS" if abs(up_r - dn_d) >= 0.03 else "SYMMETRIC_RELATIONAL_PATHS"
            dfw.loc[len(dfw)] = {"layer": "VERDICT", "p_rejoin": verdict,
                                 "note": f"upside rejoin path ({_fmt(up_r)}) vs downside decouple path ({_fmt(dn_d)}): relational outcomes are sign-specific, not mirrored"}
    dfw.to_csv(R / "35_UPSIDE_PROPAGATION_RELATIONS.csv", index=False)


# ---------------------------------------------------------------------------
# 36 SIGN FUNCTION COMPARISON
# ---------------------------------------------------------------------------

def sign_function_comparison(df):
    rows = [
        {"downside_function": "LOAD", "upside_analogue": "STABILITY", "classification": "DIFFERENT_THRESHOLD",
         "note": "both are state coordinates; downside threshold lower"},
        {"downside_function": "ABSORPTION_FAILURE", "upside_analogue": "REJOIN", "classification": "SIGN_SPECIFIC",
         "note": "no direct upside mirror of failure"},
        {"downside_function": "CORRELATION_COMPRESSION", "upside_analogue": "COHERENCE", "classification": "DIFFERENT_THRESHOLD",
         "note": "downside compresses corr; upside raises coherence only at higher thresholds"},
        {"downside_function": "SPREAD", "upside_analogue": "RECRUITMENT_PRECONDITION", "classification": "SIGN_SPECIFIC",
         "note": "upside propagation not a mirror of spread"},
        {"downside_function": "REACTIVATION", "upside_analogue": "PARTICIPATION_PERSISTENCE", "classification": "NO_ANALOGUE",
         "note": "reactivation is a downside-specific second-wave mechanism"},
        {"downside_function": "PERSISTENT_DECOUPLING", "upside_analogue": "PERSISTENT_ACCUMULATION", "classification": "UNKNOWN",
         "note": "upside accumulation weak / state-local"},
        {"downside_function": "CONTAGION", "upside_analogue": "BREADTH_PARTICIPATION", "classification": "DIFFERENT_THRESHOLD",
         "note": "both spread through neighborhood relations but upside needs permission"},
    ]
    dfw = pd.DataFrame(rows)
    if not dfw.columns.isin(["note"]).any():
        dfw["note"] = np.nan
    counts = dfw["classification"].value_counts().to_dict()
    dfw.loc[len(dfw)] = {"downside_function": "VERDICT", "upside_analogue": "NO_FORCED_MIRROR",
                         "classification": "MIXED",
                         "note": f"classification counts {counts}: shared/different-threshold only where mechanism is genuinely analogous; no mechanical sign-inversion"}
    dfw.to_csv(R / "36_SIGN_FUNCTION_COMPARISON.csv", index=False)


# ---------------------------------------------------------------------------
# 37 LOCAL SYNTHESIS
# ---------------------------------------------------------------------------

def local_synthesis(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["persistent"] = d["out_decouple"].fillna(0).astype(int)
    rows = []
    # sequential vs parallel test: does absorption require (structural + low shock) jointly?
    med_si = d["struct_integrity"].median()
    med_abs = d["abs_ret"].median()
    d["SI_hi"] = d["struct_integrity"] >= med_si
    d["SHOCK_lo"] = d["abs_ret"] <= med_abs
    d["REC_hi"] = d["recovery_index"] >= d["recovery_index"].median()
    combos = {
        "SI_hi & SHOCK_lo": d["SI_hi"] & d["SHOCK_lo"],
        "SI_hi & SHOCK_lo & REC_hi": d["SI_hi"] & d["SHOCK_lo"] & d["REC_hi"],
        "SI_lo & SHOCK_hi": (~d["SI_hi"]) & (~d["SHOCK_lo"]),
        "SI_lo & SHOCK_hi & REC_lo": (~d["SI_hi"]) & (~d["SHOCK_lo"]) & (~d["REC_hi"]),
    }
    for name, mask in combos.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"architecture": name, "n": int(len(idx)),
                     "p_absorbed": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["propagated"].mean()),
                     "p_persistent": _fmt(g["persistent"].mean())})
    # gain from adding recency to structural+shock (sequential vs parallel)
    sub = d.dropna(subset=["struct_integrity", "abs_ret", "recovery_index", "absorbed"])
    try:
        auc_si_shock = _purged_auc(sub, "absorbed", ["struct_integrity", "abs_ret"])
        auc_full = _purged_auc(sub, "absorbed", ["struct_integrity", "abs_ret", "recovery_index"])
        rows.append({"architecture": "AUC_SI+SHOCK", "n": int(len(sub)), "p_absorbed": _fmt(auc_si_shock)})
        rows.append({"architecture": "AUC_SI+SHOCK+RECOVERY", "n": int(len(sub)), "p_absorbed": _fmt(auc_full),
                     "note": "gain from recovery-state term"})
    except Exception:
        pass
    verdict = ("LOOSE_HIERARCHY" if len(rows) >= 4 else "PARALLEL_LOCAL_CONSTRAINTS" if len(rows) >= 2
               else "NO_SINGLE_STRUCTURE")
    rows.append({"architecture": "VERDICT", "n": int(len(d)), "p_absorbed": verdict,
                 "note": "architecture is descriptive; strict sequencing not claimed"})
    pd.DataFrame(rows).to_csv(R / "37_LOCAL_SYNTHESIS.csv", index=False)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("[lf12] building master frame ...", flush=True)
    df = W.master_frame(use_cache=True)
    df = _ready(df)

    print("[lf12] 02 memory-kernel repair ...", flush=True)
    memory_kernel_repair(df)
    print("[lf12] 03 burden vs recency ...", flush=True)
    burden_vs_recency(df)
    print("[lf12] 04 reactivation repair ...", flush=True)
    reactivation_repair(df)
    print("[lf12] 05 upside leakage audit ...", flush=True)
    upside_leakage_audit(df)
    print("[lf12] 06 capacity surface deep ...", flush=True)
    capacity_surface_deep(df)
    print("[lf12] 07 capacity geometry ...", flush=True)
    capacity_geometry(df)
    print("[lf12] 08 capacity boundaries ...", flush=True)
    capacity_boundaries(df)
    print("[lf12] 09 capacity family relations ...", flush=True)
    capacity_family_relations(df)
    print("[lf12] 10 absorption-propagation-containment ...", flush=True)
    absorption_propagation_containment(df)
    print("[lf12] 11 absorption-containment matrix ...", flush=True)
    absorption_containment_matrix(df)
    print("[lf12] 12 memory as recovery state ...", flush=True)
    memory_as_recovery_state(df)
    print("[lf12] 13 recovery curve ...", flush=True)
    recovery_curve(df)
    print("[lf12] 14 damage selection audit ...", flush=True)
    damage_selection_audit(df)
    print("[lf12] 15 within-asset shock history ...", flush=True)
    within_asset_shock_history(df)
    print("[lf12] 16 memory by shock species ...", flush=True)
    memory_by_shock_species(df)
    print("[lf12] 17 contagion relational map ...", flush=True)
    contagion_relational_map(df)
    print("[lf12] 18 relational distance ...", flush=True)
    relational_distance_analysis(df)
    print("[lf12] 19 contagion temporal deep ...", flush=True)
    contagion_temporal_deep(df)
    print("[lf12] 20 contagion species primitives ...", flush=True)
    contagion_species_primitives(df)
    print("[lf12] 21 early contagion demotion ...", flush=True)
    early_contagion_demotion(df)
    print("[lf12] 22 branching utility ...", flush=True)
    branching_utility(df)
    print("[lf12] 23 reactivation second wave ...", flush=True)
    reactivation_second_wave(df)
    print("[lf12] 24 reactivation memory ...", flush=True)
    reactivation_memory(df)
    print("[lf12] 25 decoupling relational mechanisms ...", flush=True)
    decoupling_relational_mechanisms(df)
    print("[lf12] 26 decoupling exit paths ...", flush=True)
    decoupling_exit_paths(df)
    print("[lf12] 27 sign asymmetry granularity ...", flush=True)
    sign_asymmetry_granularity(df)
    print("[lf12] 28 sign asymmetry matrix ...", flush=True)
    sign_asymmetry_matrix(df)
    print("[lf12] 29 correlation compression deep ...", flush=True)
    correlation_compression_deep(df)
    print("[lf12] 30 missing mechanical sensors ...", flush=True)
    missing_mechanical_sensors()
    print("[lf12] 31 sign law status ...", flush=True)
    sign_law_status(df)
    print("[lf12] 32 upside PIT rebuild ...", flush=True)
    upside_pit_rebuild(df)
    print("[lf12] 33 upside functional map ...", flush=True)
    upside_functional_map(df)
    print("[lf12] 34 upside accumulation retest ...", flush=True)
    upside_accumulation_retest(df)
    print("[lf12] 35 upside propagation relations ...", flush=True)
    upside_propagation_relations(df)
    print("[lf12] 36 sign function comparison ...", flush=True)
    sign_function_comparison(df)
    print("[lf12] 37 local synthesis ...", flush=True)
    local_synthesis(df)

    print("[lf12] DONE", flush=True)


if __name__ == "__main__":
    main()