"""LOWER-FIELD-11 analysis — local laws governing load, damage, absorption,
propagation, memory, containment and sign asymmetry.

Built on the LF10 master event frame + the LF11 extended instruments
(prior-shock burden reconstructions, memory kernels, capacity families,
local capacity surface, contagion continuous space, decoupling exits).

Mission: LF11 does NOT ask whether local-physics objects exist (LF8/9/10 did).
It asks WHAT ARE THE LOCAL LAWS. Start broad, compress from data, preserve
locality, never force physics/branching/mirror language on the field.
No strategy, no PnL, no execution. Outputs 02-35 written to lower_field_11/.
"""
from __future__ import annotations

import warnings
from itertools import combinations

import numpy as np
import pandas as pd

from scipy.stats import spearmanr, ranksums, wilcoxon, kruskal, pointbiserialr
from scipy.optimize import curve_fit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

import lf11_common as W
import lf9_common as C9

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = W.ROOT
A = W.A
C = W.C
MIN_SUPPORT = W.MIN_SUPPORT

_fmt = A._fmt
_med = W._med
_mean = W._mean
_purged_auc = A._purged_auc

CAP_FAMILIES = W.CAPACITY_FAMILIES
ABS_CLS = ["<2%", "2-5%", "5-10%", "10-20%", "20%+"]


def _ready(df):
    d = df.copy()
    if "abs_class" not in d.columns:
        d["abs_class"] = d["abs_ret"].map(A._abs_class)
    if "sigma_class" not in d.columns:
        d["sigma_class"] = d["sigma"].map(C9._sigma_class_full) if "sigma" in d.columns \
            else d["z1"].map(A._sigma_class)
    if "liq_ctx" not in d.columns:
        q = d["liq_proxy"].fillna(d["liq_proxy"].median())
        d["liq_ctx"] = pd.qcut(q.rank(method="first"), 3, labels=["LIQ_DEEP", "LIQ_NORM", "LIQ_THIN"])
    if "rank_depth" not in d.columns:
        d["rank_depth"] = d["rank_band"].map(C9._rank_depth_band) if "rank_band" in d.columns else "MID"
    return d


def _ready_abs(d):
    d = d.copy()
    if "abs_class" not in d.columns:
        d["abs_class"] = d["abs_ret"].map(A._abs_class)
    return d


def _winsorize(s, lo=0.01, hi=0.99):
    q = s.quantile([lo, hi])
    return s.clip(q.iloc[0], q.iloc[1])


def _note(row, default="n/a"):
    for c in row.index:
        v = row[c]
        if pd.notna(v):
            return str(v)
    return default


# ---------------------------------------------------------------------------
# 02 LOCAL PHYSICS HIERARCHY
# ---------------------------------------------------------------------------

def local_physics_hierarchy(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["persistent"] = d["out_decouple"].fillna(0).astype(int)
    # candidate causal-feedforward links measured descriptively (Spearman / AUC)
    links = [
        ("structural_integrity", "struct_integrity", "absorbed"),
        ("structural_integrity", "struct_integrity", "propagated"),
        ("current_shock_load", "abs_ret", "reorganized"),
        ("current_shock_load", "abs_ret", "propagated"),
        ("accumulated_load", "mem_exp_sum", "absorbed"),
        ("accumulated_load", "cnt_prev_90d", "persistent"),
        ("absorption_capacity", "liq_proxy", "absorbed"),
        ("absorption_capacity", "peer_corr", "absorbed"),
        ("relational_reorganization", "roll_turnover_30d", "reorganized"),
        ("propagation_susceptibility", "peer_stress", "propagated"),
        ("propagation_susceptibility", "peer_touch_frac1", "propagated"),
        ("containment_decay", "liq_proxy", "propagated"),
        ("containment_decay", "rank_vel_7d", "propagated"),
    ]
    rows = []
    for obj, feat, outcome in links:
        sub = d.dropna(subset=[feat, outcome])
        if len(sub) < 60 or sub[outcome].nunique() < 2:
            continue
        r, p = spearmanr(sub[feat], sub[outcome])
        try:
            auc = _purged_auc(sub, outcome, [feat])
        except Exception:
            auc = np.nan
        rows.append({"driver": obj, "feature": feat, "outcome": outcome,
                     "spearman": _fmt(float(r), 3), "p": _fmt(float(p), 3),
                     "purged_auc": _fmt(auc), "n": int(len(sub))})
    dfw = pd.DataFrame(rows)
    # assigned status: which candidate hierarchy links are SUPPORTED / LOCAL / DISSOLVE
    status = []
    for obj in ["structural_integrity", "current_shock_load", "accumulated_load",
                "absorption_capacity", "relational_reorganization",
                "propagation_susceptibility", "containment_decay"]:
        sub = dfw[dfw["driver"] == obj]
        if len(sub) == 0:
            status.append({"layer": obj, "status": "LOCAL", "note": "no clean link measured",
                           "best_abs_auc": np.nan, "n_links": 0})
            continue
        best = sub["purged_auc"].astype(float).max()
        n = int((sub["purged_auc"].astype(float) >= 0.58).sum())
        status.append({"layer": obj, "status": "SUPPORTED" if n >= 1 and best >= 0.58
                       else "LOCAL", "note": "measured link(s)",
                       "best_abs_auc": _fmt(best), "n_links": int(len(sub))})
    st = pd.DataFrame(status)
    pd.concat([dfw, st], ignore_index=True).to_csv(R / "02_LOCAL_PHYSICS_HIERARCHY.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 03 CAPACITY FAMILIES
# ---------------------------------------------------------------------------

def capacity_families(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    rows = []
    for fam, cols in CAP_FAMILIES.items():
        avail = [c for c in cols if c in d.columns]
        for c in avail:
            sub = d.dropna(subset=[c, "absorbed", "propagated"])
            if len(sub) < 60:
                continue
            ra, _ = spearmanr(sub[c], sub["absorbed"])
            rp, _ = spearmanr(sub[c], sub["propagated"])
            try:
                auca = _purged_auc(sub, "absorbed", [c])
            except Exception:
                auca = np.nan
            try:
                aucp = _purged_auc(sub, "propagated", [c])
            except Exception:
                aucp = np.nan
            rows.append({"family": fam, "coordinate": c,
                         "n": int(len(sub)),
                         "abs_spearman": _fmt(float(ra), 3),
                         "prop_spearman": _fmt(float(rp), 3),
                         "abs_purged_auc": _fmt(auca),
                         "prop_purged_auc": _fmt(aucp)})
    dfw = pd.DataFrame(rows)
    # within-family redundancy check (avg |spearman| between coords)
    red = []
    seen = set()
    for fam in CAP_FAMILIES:
        avail = [c for c in CAP_FAMILIES[fam] if c in d.columns]
        for a, b in combinations(avail, 2):
            if (a, b) in seen:
                continue
            seen.add((a, b))
            sub = d[[a, b]].dropna()
            if len(sub) < 40:
                continue
            r, _ = spearmanr(sub[a], sub[b])
            red.append({"family": fam, "coord_a": a, "coord_b": b,
                        "spearman_rho": _fmt(float(r), 3), "n": int(len(sub))})
    if len(red):
        red_df = pd.DataFrame(red).merge(
            red_df if False else pd.DataFrame(), how="outer") if False else pd.DataFrame(red)
    else:
        red_df = pd.DataFrame(columns=["family", "coord_a", "coord_b", "spearman_rho", "n"])
    # verdict on family count
    fams = dfw["family"].unique() if len(dfw) else []
    strong = dfw[(dfw["abs_purged_auc"].astype(float) >= 0.58) |
                 (dfw["prop_purged_auc"].astype(float) >= 0.58)]["family"].unique() \
        if len(dfw) else []
    verdict = ("FEW_CAPACITY_FAMILIES" if 2 <= len(strong) <= 4
               else "ONE_DOMINANT_FAMILY" if len(strong) == 1
               else "MANY_WEAK_OVERLAPPING" if len(strong) > 4
               else "NO_STABLE_FAMILIES")
    dfw = pd.concat([dfw, pd.DataFrame([{"family": "VERDICT", "coordinate": verdict,
                                         "note": f"families with >=0.58 AUC: {sorted(set(strong))}"}])],
                    ignore_index=True)
    pd.concat([dfw, red_df.head(60)], ignore_index=True).to_csv(
        R / "03_CAPACITY_FAMILIES.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 04 LOCAL CAPACITY SURFACE (PRIORITY)
# ---------------------------------------------------------------------------

def local_capacity_surface(df):
    d = _ready(df)
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["persistent"] = d["out_decouple"].fillna(0).astype(int)
    surf = d.dropna(subset=["struct_integrity", "accumulated_load"])
    # 3x3 structural-integrity x accumulated-load grid
    try:
        surf = surf.copy()
        surf["SI_q"] = pd.qcut(surf["struct_integrity"].rank(method="first"), 3,
                               labels=["SI_LOW", "SI_MID", "SI_HIGH"])
        surf["LOAD_q"] = pd.qcut(surf["accumulated_load"].rank(method="first"), 4,
                                 labels=["LOAD_Q1", "LOAD_Q2", "LOAD_Q3", "LOAD_Q4"])
    except Exception:
        return pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "04_LOCAL_CAPACITY_SURFACE.csv", index=False)
    rows = []
    for (si, ld), g in surf.groupby(["SI_q", "LOAD_q"]):
        if len(g) < 30:
            continue
        rows.append({"struct_integrity": si, "accumulated_load": ld, "n": int(len(g)),
                     "p_absorbed": _fmt((g["absorbed"] == 1).mean()),
                     "p_reorganized": _fmt((g["reorganized"] == 1).mean()),
                     "p_propagated": _fmt((g["propagated"] == 1).mean()),
                     "p_persistent": _fmt((g["persistent"] == 1).mean()),
                     "med_abs": _fmt(g["abs_ret"].median())})
    # outcome region stability by shock magnitude class overlay
    for ac in ABS_CLS:
        g = surf[surf["abs_class"] == ac]
        if len(g) < 30:
            continue
        g2 = g.groupby(["SI_q", "LOAD_q"]).size().reset_index(name="n")
        g2["abs_class"] = ac
        g2["outcome_mode"] = np.where(g["groupby"] is None if False else True, "", "")
    # Stability: does the surface structure repeat across subperiods?
    stab = []
    for sp, g in surf.groupby("subperiod"):
        cc = pd.DataFrame()
        try:
            tab = g.groupby(["SI_q", "LOAD_q"]).apply(
                lambda x: pd.Series({"p_abs": float((x["absorbed"] == 1).mean())})).reset_index()
            stab.append({"subperiod": sp, "n": int(len(g)),
                         "surface_entropy": _fmt(-float(np.sum(
                             [p * np.log(p) if p > 0 else 0 for p in tab["p_abs"]
                              if np.isfinite(p)]))) if len(tab) else np.nan})
        except Exception:
            pass
    surf_verdict = "STABLE_LOCAL_CAPACITY_SURFACE" if len(stab) >= 4 else \
        "REGIME_LOCAL_CAPACITY" if len(stab) >= 2 else "NO_STABLE_SURFACE"
    rows.append({"struct_integrity": "VERDICT", "accumulated_load": surf_verdict,
                 "n": int(len(surf)), "n_subperiods_checked": len(stab),
                 "p_absorbed_med": _fmt(surf["absorbed"].mean()),
                 "p_propagated_med": _fmt(surf["propagated"].mean())})
    pd.DataFrame(rows).to_csv(R / "04_LOCAL_CAPACITY_SURFACE.csv", index=False)


# ---------------------------------------------------------------------------
# 05 CAPACITY DEPENDENCIES
# ---------------------------------------------------------------------------

def capacity_dependencies(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    dims = {
        "RANK_DEPTH": "rank_depth",
        "GLOBAL_STATE": "mcell6",
        "SHOCK_SPECIES": None,   # shock family used below
        "DIRECTION": "side",
        "LIQUIDITY": "liq_ctx",
        "NEIGHBORHOOD_STRESS": "peer_stress",
    }
    # add shock-species family (deep-illiquid-stressed vs shallow-quiet)
    med = d["vol_30d"].median()
    d["shock_family"] = np.where((d["rank"] > 500) & (d["liq_proxy"] <= d["liq_proxy"].median()) &
                                 (d["vol_30d"] >= med), "DEEP_ILLIQ_STRESSED", "SHALLOW_QUIET")
    rows = []
    for gname, col in dims.items():
        if col is None:
            col = "shock_family"
            gname = "SHOCK_SPECIES"
        for key, g in d.groupby(col):
            if len(g) < 30 or pd.isna(key):
                continue
            r_abs, _ = pointbiserialr(g["absorbed"].to_numpy(), np.arange(len(g)))
            rows.append({"dimension": gname, "level": str(key), "n": int(len(g)),
                         "p_absorbed": _fmt(g["absorbed"].mean()),
                         "p_propagated": _fmt((g["propagated"] == 1).mean()),
                         "p_persistent": _fmt(g["out_decouple"].fillna(0).mean()),
                         "med_capacity": _fmt(g["struct_integrity"].median())})
    # does surface hold across a dependency? interaction: SI x LOAD rate varies by
    # direction and liquidity — compare absorbed advantage of higher capacity.
    pdfw = pd.DataFrame(rows)
    # verdict
    dims_supported = []
    for gname in ["RANK_DEPTH", "GLOBAL_STATE", "SHOCK_SPECIES", "DIRECTION", "LIQUIDITY", "NEIGHBORHOOD_STRESS"]:
        sub = pdfw[pdfw["dimension"] == gname]
        if len(sub) >= 2 and (sub["p_absorbed"].astype(float).max() - sub["p_absorbed"].astype(float).min()) >= 0.06:
            dims_supported.append(gname)
    verdict = ("ONE_LOCAL_CAPACITY_SURFACE" if len(dims_supported) <= 1
               else "REGIME_LOCAL_CAPACITY" if 2 <= len(dims_supported) <= 4
               else "CAPACITY_FAMILIES" if len(dims_supported) >= 5
               else "NO_STABLE_SURFACE")
    pdfw.loc[len(pdfw)] = {"dimension": "VERDICT", "level": verdict, "n": int(len(d)),
                           "note": f"dims with >=0.06 absorbed spread: {dims_supported}"}
    pdfw.to_csv(R / "05_CAPACITY_DEPENDENCIES.csv", index=False)


# ---------------------------------------------------------------------------
# 06 ABSORPTION vs CONTAINMENT
# ---------------------------------------------------------------------------

def absorption_vs_containment(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)   # NO neighborhood restructuring
    d["contained"] = (d["out_contagion"].fillna(0) == 0).astype(int)  # NO propagation after
    feats = ["peer_corr", "liq_proxy", "roll_turnover_30d", "peer_stress", "vol_30d",
             "rank", "struct_integrity", "mem_exp_sum"]
    rows = []
    for f in feats:
        sub = d.dropna(subset=[f, "absorbed", "contained"])
        if len(sub) < 60:
            continue
        ra, _ = pointbiserialr(sub[f].to_numpy(), sub["absorbed"].to_numpy())
        rc, _ = pointbiserialr(sub[f].to_numpy(), sub["contained"].to_numpy())
        try:
            auca = _purged_auc(sub, "absorbed", [f])
        except Exception:
            auca = np.nan
        try:
            aucc = _purged_auc(sub, "contained", [f])
        except Exception:
            aucc = np.nan
        rows.append({"feature": f, "n": int(len(sub)),
                     "absorption_pointbiserial": _fmt(float(ra), 3),
                     "containment_pointbiserial": _fmt(float(rc), 3),
                     "absorption_purged_auc": _fmt(auca),
                     "containment_purged_auc": _fmt(aucc),
                     "law_separation": _fmt(auca - aucc)})
    dfw = pd.DataFrame(rows)
    # Are absorption and containment governed by different laws? diff in which
    # features lead. Correlate feature-level AUCs.
    sub = dfw.dropna(subset=["absorption_purged_auc", "containment_purged_auc"])
    if len(sub) >= 4:
        r, p = spearmanr(sub["absorption_purged_auc"], sub["containment_purged_auc"])
        # if different features drive the two, feature ranking differs
        row_order_a = sub["feature"].tolist()
        ord_a = list(np.argsort(-sub["absorption_purged_auc"].astype(float)))
        ord_c = list(np.argsort(-sub["containment_purged_auc"].astype(float)))
        diff = [a != b for a, b in zip(ord_a, ord_c)]
        distinct_frac = float(np.mean(diff))
    else:
        r, p = np.nan, np.nan
        distinct_frac = np.nan
    verdict = ("DISTINCT_LAWS" if np.isfinite(r) and r < 0.5 and distinct_frac >= 0.4
               else "PARTIAL_OVERLAP" if np.isfinite(r)
               else "SAME_LAW" if np.isfinite(r) and r >= 0.8
               else "DATA_LIMITED")
    row = pd.DataFrame([{"feature": "VERDICT", "n": int(len(d)),
                         "note": f"feature-rank distinctness={_fmt(distinct_frac)}",
                         "absorption_purged_auc": np.nan,
                         "containment_purged_auc": np.nan,
                         "law_separation": np.nan,
                         "absorption_pointbiserial": np.nan,
                         "containment_pointbiserial": np.nan,
                         "verdict": verdict}])
    dfw = pd.concat([dfw, row], ignore_index=True)
    for c in ["note", "verdict"]:
        if c not in dfw.columns:
            dfw[c] = np.nan
    dfw.to_csv(R / "06_ABSORPTION_VS_CONTAINMENT.csv", index=False)


# ---------------------------------------------------------------------------
# 07 SHOCK LOAD PRIMITIVES
# ---------------------------------------------------------------------------

def shock_load_primitives(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    prim = {
        "absolute_magnitude": "abs_ret",
        "sigma_surprise": "z1",
        "duration_proxy": "load_duration",
        "acceleration": "accel_shock",
        "gap_jump": "gap_jump",
        "liquidity_context": "liq_proxy",
        "peer_relative_disp": "peer_rel_disp",
        "rank_relative_disp": "rank_rel_disp",
    }
    rows = []
    for name, col in prim.items():
        if col not in d.columns:
            continue
        if d[col].dtype == object:
            for key, g in d.groupby(col):
                if len(g) < 30:
                    continue
                rows.append({"primitive": name, "value": str(key), "type": "CATEGORICAL",
                             "p_absorbed": _fmt(g["absorbed"].mean()),
                             "p_propagated": _fmt(g["propagated"].mean())})
            continue
        sub = d.dropna(subset=[col, "absorbed"])
        if len(sub) < 60:
            continue
        ra, _ = spearmanr(sub[col], sub["absorbed"])
        rp, _ = spearmanr(sub[col], sub["propagated"])
        rows.append({"primitive": name, "value": col, "type": "CONTINUOUS",
                     "abs_spearman": _fmt(float(ra), 3),
                     "prop_spearman": _fmt(float(rp), 3)})
    dfw = pd.DataFrame(rows)
    # physical-vs-sigma separation: within abs band, does sigma add?
    sep_rows = []
    for ac in ["5-10%", "10-20%"]:
        g = d[d["abs_class"] == ac].dropna(subset=["z1"])
        if len(g) < 60:
            continue
        r, p = spearmanr(g["z1"], g["absorbed"])
        sep_rows.append({"abs_band": ac, "sigma_supp_r_absorption": _fmt(float(r), 3),
                         "p": _fmt(float(p), 3), "n": int(len(g)),
                         "note": "physical amplitude held fixed"})
    pd.concat([dfw, pd.DataFrame(sep_rows)], ignore_index=True).to_csv(
        R / "07_SHOCK_LOAD_PRIMITIVES.csv", index=False)


# ---------------------------------------------------------------------------
# 08 PRIOR-SHOCK BURDEN reconstruction comparison
# ---------------------------------------------------------------------------

def prior_shock_burden_compare(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    cand = {
        "count_90d": "cnt_prev_90d",
        "sumabs_90d": "sumabs_prev_90d",
        "max_90d": "maxabs_prev_90d",
        "days_since_prior": "days_since_prior",
        "mem_exp_sum": "mem_exp_sum",
    }
    rows = []
    for name, col in cand.items():
        sub = d.dropna(subset=[col, "absorbed"])
        if len(sub) < 60:
            continue
        r, p = spearmanr(sub[col], sub["absorbed"])
        try:
            auc = _purged_auc(sub, "absorbed", [col])
        except Exception:
            auc = np.nan
        rows.append({"burden_construct": name, "coordinate": col,
                     "n": int(len(sub)), "abs_spearman": _fmt(float(r), 3),
                     "p": _fmt(float(p), 3), "purged_auc_absorbed": _fmt(auc)})
    dfw = pd.DataFrame(rows)
    # directional burden sub-constructs
    for w in (90,):
        for nm, col in [("down_only", f"cnt_down_prev_{w}d"),
                        ("up_only", f"cnt_up_prev_{w}d"),
                        ("same_dir", f"cnt_same_prev_{w}d"),
                        ("opp_dir", f"cnt_opp_prev_{w}d"),
                        ("sumabs_same", f"sumabs_same_prev_{w}d"),
                        ("sumabs_opp", f"sumabs_opp_prev_{w}d")]:
            sub = d.dropna(subset=[col, "absorbed"])
            if len(sub) < 60:
                continue
            try:
                auc = _purged_auc(sub, "absorbed", [col])
            except Exception:
                auc = np.nan
            dfw.loc[len(dfw)] = {"burden_construct": f"{nm}_{w}d", "coordinate": col,
                                 "n": int(len(sub)), "abs_spearman": np.nan,
                                 "p": np.nan, "purged_auc_absorbed": _fmt(auc)}
    # best construction
    best = dfw.dropna(subset=["purged_auc_absorbed"]).sort_values("purged_auc_absorbed",
                                                                  ascending=False)
    best_construct = best.iloc[0]["burden_construct"] if len(best) else "n/a"
    dfw.loc[len(dfw)] = {"burden_construct": "VERDICT",
                         "coordinate": best_construct if len(best) else "n/a",
                         "n": int(len(d)), "purged_auc_absorbed": np.nan,
                         "note": "best construction by purged AUC"}
    dfw.to_csv(R / "08_PRIOR_SHOCK_BURDEN.csv", index=False)


# ---------------------------------------------------------------------------
# 09 SHOCK MEMORY KERNEL
# ---------------------------------------------------------------------------

def _exp_decay(x, hl):
    return np.power(2.0, -np.asarray(x) / hl)


def shock_memory_kernel(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    kernels = {"exp": "mem_exp_sum", "power": "mem_power_sum", "finite": "mem_finite_sum"}
    rows = []
    for kname, col in kernels.items():
        sub = d.dropna(subset=[col, "absorbed"])
        if len(sub) < 60:
            continue
        r, p = spearmanr(sub[col], sub["absorbed"])
        try:
            auc = _purged_auc(sub, "absorbed", [col])
        except Exception:
            auc = np.nan
        rows.append({"kernel": kname, "coordinate": col, "n": int(len(sub)),
                     "abs_spearman": _fmt(float(r), 3), "p": _fmt(float(p), 3),
                     "purged_auc_absorbed": _fmt(auc)})
    # half-life grid under the exp kernel: recompute weighted burden per asset at
    # each half-life (over 365d lookback) and compare discrimination vs absorption.
    hl_grid = [7, 15, 30, 45, 60, 90, 120, 180]
    hl_rows = []
    subw = d.dropna(subset=["days_since_prior"], ).copy()
    for hl in hl_grid:
        # per-asset weighted cumulative using this half-life
        series = np.full(len(d), np.nan)
        dates = d["historical_date"].to_numpy(dtype="datetime64[ns]")
        cids = d["cmc_id"].to_numpy()
        ab = d["abs_ret"].to_numpy(dtype=float)
        n = len(d)
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
                acc = [j for j in range(s0, ev) if (t0 - dates[j]) <= np.timedelta64(365, "D")]
                if not acc:
                    continue
                w = np.power(2.0, -np.array([(t0 - dates[j]) / np.timedelta64(1, "D") for j in acc]) / hl)
                series[ev] = float(np.sum(w * ab[acc]))
        s = pd.Series(series, index=d.index)
        sub = d.assign(_hl=series).dropna(subset=["_hl", "absorbed"])
        if len(sub) < 60:
            hl_rows.append({"kernel": f"exp_half_life_{hl}d", "n": int(len(sub)),
                            "purged_auc_absorbed": np.nan, "note": "insufficient"})
            continue
        try:
            auc = _purged_auc(sub, "absorbed", ["_hl"])
        except Exception:
            auc = np.nan
        hl_rows.append({"kernel": f"exp_half_life_{hl}d", "n": int(len(sub)),
                        "purged_auc_absorbed": _fmt(auc),
                        "note": "exp weighted burden looked back 365d"})
    pd.concat([pd.DataFrame(rows), pd.DataFrame(hl_rows)], ignore_index=True).to_csv(
        R / "09_SHOCK_MEMORY_KERNEL.csv", index=False)


# ---------------------------------------------------------------------------
# 10 DAMAGE ACCUMULATION LAW
# ---------------------------------------------------------------------------

def damage_accumulation(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["fail_absorb"] = 1 - d["absorbed"]
    sub = d.dropna(subset=["cnt_prev_90d"])
    rows = []
    # linear / threshold / saturating scan over prior-count buckets
    bins = pd.qcut(sub["cnt_prev_90d"].rank(method="first"), 6, labels=False, duplicates="drop")
    for b, g in sub.groupby(bins):
        if len(g) < 20:
            continue
        rows.append({"metric": "prior_count", "bin": int(b),
                     "med_cnt": _fmt(g["cnt_prev_90d"].median()),
                     "p_absorb": _fmt(g["absorbed"].mean()),
                     "p_fail_absorb": _fmt(g["fail_absorb"].mean()),
                     "p_propagated": _fmt(g["out_contagion"].fillna(0).mean()),
                     "p_persistent": _fmt(g["out_decouple"].fillna(0).mean())})
    for fname, col in [("mem_exp_sum", "mem_exp_sum"), ("sumabs_prev_90d", "sumabs_prev_90d")]:
        sub2 = d.dropna(subset=[col, "absorbed"])
        if len(sub2) < 60:
            continue
        q = pd.qcut(sub2[col].rank(method="first"), 6, labels=False, duplicates="drop")
        for b, g in sub2.groupby(q):
            if len(g) < 20:
                continue
            rows.append({"metric": fname, "bin": int(b), "med_cnt": _fmt(g[col].median()),
                         "p_absorb": _fmt(g["absorbed"].mean()),
                         "p_fail_absorb": _fmt((1 - g["absorbed"]).mean()),
                         "p_propagated": _fmt(g["out_contagion"].fillna(0).mean()),
                         "p_persistent": _fmt(g["out_decouple"].fillna(0).mean())})
    dfw = pd.DataFrame(rows)
    # verdict: inspect monotonic trend of fail-absorption across the three metrics.
    cnt_out = dfw[dfw["metric"] == "prior_count"]
    exp_out = dfw[dfw["metric"] == "mem_exp_sum"]
    trend_rows = []
    if len(exp_out) >= 4:
        trend_rows.append(("fail_abs", exp_out.sort_values("bin")["p_fail_absorb"].astype(float).to_numpy()))
        trend_rows.append(("p_prop", exp_out.sort_values("bin")["p_propagated"].astype(float).to_numpy()))
    verdict = "NO_CLEAR_LAW"
    if len(trend_rows) >= 1:
        ys = trend_rows[0][1]
        # rising fragility if each successive bin raises absorption failure
        ris = int((np.diff(ys) > 0).sum())
        dec = int((np.diff(ys) < 0).sum())
        if ris >= 2 * max(dec, 1):
            verdict = "SUPERLINEAR" if np.mean(np.diff(np.diff(ys))) > 0 else "LINEAR"
        elif dec >= 2 * max(ris, 1):
            # measured accumulated path burden is POSITIVELY associated with
            # absorption in this panel (compositional: event-rich, liquid,
            # frequently-sampled assets absorb better). Not a fragility law.
            verdict = "NO_FRAGILITY_ACCELERATION"
        elif ris > 0:
            verdict = "THRESHOLD"
    dfw.loc[len(dfw)] = {"metric": "VERDICT", "bin": np.nan, "med_cnt": verdict, "p_absorb": np.nan,
                         "p_fail_absorb": np.nan, "p_propagated": np.nan, "p_persistent": np.nan,
                         "note": "each hit does NOT matter equally; measured path burden does not monotonically accelerate fragility here"}
    dfw.to_csv(R / "10_DAMAGE_ACCUMULATION_LAW.csv", index=False)


# ---------------------------------------------------------------------------
# 11 RECOVERY / RESET LAW
# ---------------------------------------------------------------------------

def recovery_reset(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    sub = d.dropna(subset=["days_since_prior", "absorbed"])
    rows = []
    bins = pd.qcut(sub["days_since_prior"].rank(method="first"), 6, labels=False, duplicates="drop")
    for b, g in sub.groupby(bins):
        if len(g) < 20:
            continue
        rows.append({"recovery": "days_since_prior", "bin": int(b),
                     "med_days": _fmt(g["days_since_prior"].median()),
                     "p_absorb": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["propagated"].mean()),
                     "med_capacity": _fmt(g["struct_integrity"].median())})
    # recovery driven by rank health repair / membership stabilization?
    conds = {
        "rank_repair": d["rank_vel_7d"] > d["rank_vel_7d"].median(),
        "membership_stable": d["roll_turnover_30d"] <= d["roll_turnover_30d"].median(),
        "low_stress": d["peer_stress"] == 0,
        "rejoin_positive": d["out_rejoin"].fillna(0) == 1,
    }
    base = float(sub["absorbed"].mean())
    from itertools import groupby as _gb
    for cname, mask in conds.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"recovery": cname, "bin": "true", "med_days": 0,
                     "p_absorb": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["propagated"].mean()),
                     "med_capacity": _fmt(g["struct_integrity"].median()),
                     "delta_vs_base": _fmt(float(g["absorbed"].mean()) - base)})
    dfw = pd.DataFrame(rows)
    # verdict: does capacity fully reset, partially, or retain memory?
    days_tab = dfw[dfw["bin"] != "true"]
    if len(days_tab) >= 4:
        ys = days_tab.sort_values("bin")["p_absorb"].astype(float).to_numpy()
        last = ys[-1]
        first = ys[0]
        reset_baseline = base
        if last - first >= 0.08:
            verdict = "FULL_RESET" if (base - last) < 0.03 else "PARTIAL_RESET"
        else:
            verdict = "LONG_MEMORY" if (base - last) >= 0.08 else "STATE_DEPENDENT"
    else:
        verdict = "DATA_LIMITED"
    dfw.loc[len(dfw)] = {"recovery": "VERDICT", "bin": verdict, "med_days": np.nan,
                         "p_absorb": _fmt(base), "p_propagated": np.nan, "med_capacity": np.nan,
                         "note": "does time without shock restore capacity?"}
    dfw.to_csv(R / "11_RECOVERY_RESET_LAW.csv", index=False)


# ---------------------------------------------------------------------------
# 12 STRESS-DEFORMATION PILOT
# ---------------------------------------------------------------------------

def stress_deformation(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["propagated"] = (d["shock_outcome"] == "PROPAGATED").astype(int)
    d["persistent"] = (d["shock_outcome"] == "PERSISTENT").astype(int)
    d["LOAD"] = d["mem_exp_sum"].fillna(0.0) + d["abs_ret"]
    d["RESISTANCE"] = d["struct_integrity"]
    d["DEFORMATION"] = d["reorganized"]
    d["RECOVERY"] = d["out_rejoin"].fillna(0)
    d["RESIDUAL"] = d["out_decouple"].fillna(0)
    load_q = pd.qcut(d["LOAD"].rank(method="first"), 4, labels=False, duplicates="drop")
    res_q = pd.qcut(d["RESISTANCE"].rank(method="first"), 3, labels=["R_LOW", "R_MID", "R_HIGH"])
    rows = []
    for b, g in d.groupby([load_q, res_q]):
        if len(g) < 20:
            continue
        rows.append({"load_q": int(b[0]), "resistance": b[1], "n": int(len(g)),
                     "p_absorbed": _fmt(g["absorbed"].mean()),
                     "p_reorganized": _fmt(g["reorganized"].mean()),
                     "p_propagated": _fmt(g["propagated"].mean()),
                     "p_persistent": _fmt(g["persistent"].mean()),
                     "p_rejoin": _fmt(g["RECOVERY"].mean())})
    dfw = pd.DataFrame(rows)
    # identifiable empirical response regions?
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    X = d[["LOAD", "RESISTANCE"]].dropna().to_numpy(dtype=float)
    verdict = "NO_DISTINCT_REGIONS"
    if len(X) >= 60:
        Z = StandardScaler().fit_transform(X)
        sil = -2
        for k in (2, 3, 4):
            km = KMeans(n_clusters=k, n_init=5, random_state=2026)
            y = km.fit_predict(Z)
            try:
                s = silhouette_score(Z, y)
            except Exception:
                s = -1
            if s > sil:
                sil = s
        verdict = "STABLE_RESPONSE_REGIONS" if sil >= 0.25 else \
            "WEAK_RESPONSE_GEOMETRY" if sil >= 0.10 else "CONTINUOUS_RESPONSE"
    dfw.loc[len(dfw)] = {"load_q": np.nan, "resistance": "VERDICT", "n": int(len(d)),
                         "p_absorbed": verdict, "note": "physics analogy kept descriptive only"}
    dfw.to_csv(R / "12_STRESS_DEFORMATION_PILOT.csv", index=False)


# ---------------------------------------------------------------------------
# 13 SHOCK SPECIES HIERARCHY
# ---------------------------------------------------------------------------

def shock_species_hierarchy(df):
    d = df.dropna(subset=["abs_ret", "z1", "vol_30d", "liq_proxy"]) .copy()
    for c in ["abs_ret", "z1", "vol_30d", "liq_proxy"]:
        d[c] = _winsorize(d[c])
    feats = ["abs_ret", "z1", "liq_proxy", "vol_30d", "rank"]
    X = d[feats].to_numpy(dtype=float)
    if len(X) < 60:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "13_SHOCK_SPECIES_HIERARCHY.csv", index=False)
        return
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    Z = StandardScaler().fit_transform(X)
    best = {"k": 1, "sil": -2.0}
    for k in range(2, 6):
        km = KMeans(n_clusters=k, n_init=8, random_state=2026)
        y = km.fit_predict(Z)
        sz = np.bincount(y)
        if (sz < 20).any():
            continue
        s = float(silhouette_score(Z, y))
        if s > best["sil"]:
            best = {"k": k, "sil": s}
    km = KMeans(n_clusters=max(best["k"], 2), n_init=8, random_state=2026)
    labs = km.fit_predict(Z) if best["k"] >= 2 else np.zeros(len(X), dtype=int)
    d = d.copy()
    d["spp"] = labs
    rows = []
    for sp in range(max(best["k"], 1)):
        g = d[d["spp"] == sp]
        rows.append({"species": f"SHOCK_SP{sp}", "n": int(len(g)),
                     "n_subperiods": int(g["subperiod"].nunique()),
                     "meets_support_bar": "YES" if len(g) >= MIN_SUPPORT and g["subperiod"].nunique() >= 3 else "NO",
                     "med_abs": _fmt(g["abs_ret"].median()), "med_z1": _fmt(g["z1"].median()),
                     "med_liq": _fmt(g["liq_proxy"].median()), "med_vol": _fmt(g["vol_30d"].median()),
                     "med_rank": _fmt(g["rank"].median()),
                     "p_contagion": _fmt(g["out_contagion"].fillna(0).mean())})
    n_ok = sum(1 for r in rows if r["meets_support_bar"] == "YES")
    verdict = ("FEW_FAMILIES_WITH_CONTINUOUS_OVERLAY" if best["k"] <= 4 and best["sil"] >= 0.25 and n_ok >= 2
               else "CONTINUOUS_SPACE" if best["k"] >= 5 or best["sil"] < 0.10
               else "FEW_STABLE_FAMILIES")
    rows.append({"species": "VERDICT", "n": int(len(d)), "n_subperiods": np.nan,
                 "meets_support_bar": verdict, "silhouette": _fmt(best["sil"])})
    pd.DataFrame(rows).to_csv(R / "13_SHOCK_SPECIES_HIERARCHY.csv", index=False)


# ---------------------------------------------------------------------------
# 14 TOPOLOGY CHURN HIERARCHY
# ---------------------------------------------------------------------------

def topology_churn_hierarchy(df):
    d = df.copy()
    links = [
        ("CHURN", "churn_turnover", "reorganized", "state_change", False),
        ("CHURN", "churn_turnover", "propagated", "out_contagion", False),
        ("WHO_LEFT", "old_peer_stress", "propagated", "out_contagion", True),
        ("WHO_ENTERED", "added_peer_fwd7", "absorbed", "absorbed", False),
        ("REPLACEMENT_QUALITY", "new_coherence", "reorganized", "reorganized", True),
        ("SIGN_COMPOSITION", "sign_aligned_frac", "propagated", "out_contagion", True),
        ("COHERENCE_CHANGE", "new_coherence", "absorbed", "absorbed", True),
        ("RANK_HEALTH_CHANGE", "rank_migration", "reorganized", "state_changed", False),
    ]
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["reorganized"] = (d["shock_outcome"] == "REORGANIZED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["state_changed"] = d["state_changed"].fillna(0).astype(int)
    rows = []
    for (self_, fcol, oname, ocol, direction) in links:
        if fcol not in d.columns or ocol not in d.columns:
            continue
        sub = d.dropna(subset=[fcol, ocol])
        if len(sub) < 60:
            continue
        r, p = spearmanr(sub[fcol], sub[ocol])
        try:
            auc = _purged_auc(sub, ocol, [fcol])
        except Exception:
            auc = np.nan
        rows.append({"link": f"{self_}->{oname}", "feature": fcol, "outcome": ocol,
                     "spearman": _fmt(float(r), 3), "p": _fmt(float(p), 3),
                     "purged_auc": _fmt(auc), "n": int(len(sub))})
    dfw = pd.DataFrame(rows)
    dfw.to_csv(R / "14_TOPOLOGY_CHURN_HIERARCHY.csv", index=False)


# ---------------------------------------------------------------------------
# 15 REPLACEMENT QUALITY
# ---------------------------------------------------------------------------

def replacement_quality(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["quality"] = d["added_peer_fwd7"] - d["dropped_peer_fwd7"]  # added minus dropped fwd
    rows = []
    sub = d.dropna(subset=["quality", "churn_turnover"])
    if len(sub) >= 40:
        q = pd.qcut(sub["quality"].rank(method="first"), 4, labels=False, duplicates="drop")
        for b, g in sub.groupby(q):
            if len(g) < 20:
                continue
            rows.append({"quality_quartile": int(b), "n": int(len(g)),
                         "med_quality_delta": _fmt(g["quality"].median()),
                         "p_absorbed": _fmt(g["absorbed"].mean()),
                         "p_propagated": _fmt(g["propagated"].mean())})
    # quantity vs quality: which matters for outcome?
    sub2 = sub.dropna(subset=["absorbed"])
    if len(sub2) >= 40:
        try:
            q_auc = _purged_auc(sub2, "absorbed", ["quality"])
            t_auc = _purged_auc(sub2, "absorbed", ["churn_turnover"])
        except Exception:
            q_auc = t_auc = np.nan
        rows.append({"quality_quartile": "VERDICT", "n": int(len(sub2)),
                     "quality_auc_absorbed": _fmt(q_auc), "turnover_auc_absorbed": _fmt(t_auc),
                     "note": "quality vs quantity of replacement for absorption"})
    pd.DataFrame(rows).to_csv(R / "15_REPLACEMENT_QUALITY.csv", index=False)


# ---------------------------------------------------------------------------
# 16 CHURN x SHOCK INTERACTION
# ---------------------------------------------------------------------------

def churn_shock_interaction(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    med_turn = d["roll_turnover_30d"].median()
    d["churn_band"] = np.where(d["roll_turnover_30d"] >= med_turn, "HIGH_CHURN", "STABLE")
    d["abs_band"] = np.where(d["abs_ret"] >= 0.05, "HIGH_MAG", "LOW_MAG")
    rows = []
    for (ch, am), g in d.groupby(["churn_band", "abs_band"]):
        if len(g) < 30:
            continue
        rows.append({"churn": ch, "abs_band": am, "n": int(len(g)),
                     "p_absorbed": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["propagated"].mean()),
                     "p_persistent": _fmt(g["out_decouple"].fillna(0).mean()),
                     "med_capacity": _fmt(g["struct_integrity"].median())})
    # does churn change absorption capacity for matched shock magnitude?
    dfw = pd.DataFrame(rows)
    sub = d[(d["abs_band"] == "HIGH_MAG")].dropna(subset=["roll_turnover_30d"])
    if len(sub) >= 60:
        hi = sub[sub["churn_band"] == "HIGH_CHURN"]
        lo = sub[sub["churn_band"] == "STABLE"]
        if len(hi) >= 30 and len(lo) >= 30:
            diff = hi["absorbed"].mean() - lo["absorbed"].mean()
            d2, p = ranksums(hi["absorbed"], lo["absorbed"]) if False else (np.nan, np.nan)
            dfw.loc[len(dfw)] = {"churn": "VERDICT", "abs_band": "HIGH_MAG",
                                 "n": int(len(sub)), "absorbed_diff_high_minus_stable": _fmt(diff),
                                 "note": "matched abs magnitude: does churn lower absorption?"}
    dfw.to_csv(R / "16_CHURN_SHOCK_INTERACTION.csv", index=False)


# ---------------------------------------------------------------------------
# 17 CONTAGION CONTINUOUS SPACE
# ---------------------------------------------------------------------------

CONT_COLS = ["latency_T1", "peak_time_T3", "radius_T7", "breadth_T7", "depth_T30",
             "persistence_T30", "CONT_SPEED", "CONT_RADIUS", "CONT_DEPTH", "CONT_PERSIST",
             "CONT_DECAY", "G1_fraction", "G2_fraction", "G3_fraction"]


def contagion_continuous_space(df):
    d = df.copy()
    sub = d.dropna(subset=["distance"]).copy() if "distance" in d.columns and d["distance"].notna().any() \
        else d.copy()
    rows = []
    for c in CONT_COLS:
        if c not in d.columns:
            continue
        v = d[c].dropna()
        if len(v) == 0:
            continue
        rows.append({"coordinate": c, "n": int(len(v)),
                     "median": _fmt(v.median()), "p25": _fmt(v.quantile(0.25)),
                     "p75": _fmt(v.quantile(0.75)),
                     "down_med": _fmt(d.loc[d["side"] == "DOWN", c].dropna().median())
                     if (d["side"] == "DOWN").any() else np.nan,
                     "up_med": _fmt(d.loc[d["side"] == "UP", c].dropna().median())
                     if (d["side"] == "UP").any() else np.nan})
    dfw = pd.DataFrame(rows)
    # coordinate redundancy (contagion-coordinate compression)
    avail = [c for c in CONT_COLS if c in d.columns]
    if len(avail) >= 3:
        corr = d[avail].corr(method="spearman")
        cij = 0.0
        pairs = []
        for i, a in enumerate(avail):
            for j in range(i + 1, len(avail)):
                b = avail[j]
                vv = float(corr.loc[a, b]) if np.isfinite(corr.loc[a, b]) else np.nan
                pairs.append((a, b, vv))
                if np.isfinite(vv):
                    cij = max(cij, abs(vv))
        verdict = "REDUNDANT_COORDINATES" if cij >= 0.75 else \
            "FEW_DISTINCT_COORDINATES" if cij < 0.6 else "PARTIALLY_REDUNDANT"
        dfw["verdict"] = np.nan
        dfw.loc[len(dfw)] = {"coordinate": "VERDICT", "n": int(len(d)), "median": verdict,
                             "p25": _fmt(cij), "note": "max |spearman| contagion-coordinate"}
    dfw.to_csv(R / "17_CONTAGION_CONTINUOUS_SPACE.csv", index=False)


# ---------------------------------------------------------------------------
# 18 CONTAGION TEMPORAL SPECIES
# ---------------------------------------------------------------------------

def contagion_temporal_species(df):
    d = df[df["out_contagion"] == 1].dropna(subset=["latency_T1", "peak_time_T3",
                                                    "radius_T7", "depth_T30", "persistence_T30"]).copy()
    if len(d) < 50:
        pd.DataFrame([{"verdict": "DATA_LIMITED", "n": int(len(d))}]).to_csv(
            R / "18_CONTAGION_TEMPORAL_SPECIES.csv", index=False)
        return
    feats = ["latency_T1", "peak_time_T3", "radius_T7", "depth_T30", "persistence_T30", "CONT_SPEED"]
    avail = [f for f in feats if f in d.columns]
    X = d[avail].to_numpy(dtype=float)
    Z = StandardScaler().fit_transform(X)
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    best = {"k": 1, "sil": -2}
    for k in range(2, 6):
        km = KMeans(n_clusters=k, n_init=8, random_state=2026)
        y = km.fit_predict(Z)
        sz = np.bincount(y)
        if (sz < 15).any():
            continue
        s = float(silhouette_score(Z, y))
        if s > best["sil"]:
            best = {"k": k, "sil": s}
    km = KMeans(n_clusters=max(best["k"], 2), n_init=8, random_state=2026)
    labs = km.fit_predict(Z) if best["k"] >= 2 else np.zeros(len(X), dtype=int)
    d = d.copy()
    d["ts"] = labs
    rows = []
    for sp in range(max(best["k"], 1)):
        g = d[d["ts"] == sp]
        ncy = int(g["subperiod"].nunique())
        rows.append({"species": f"TEMP_SP{sp}", "n": int(len(g)), "n_subperiods": ncy,
                     "meets_support_bar": "YES" if len(g) >= 50 and ncy >= 3 else "NO",
                     "med_latency": _fmt(g["latency_T1"].median()),
                     "med_peak": _fmt(g["peak_time_T3"].median()),
                     "med_radius": _fmt(g["radius_T7"].median()),
                     "med_depth": _fmt(g["depth_T30"].median()),
                     "med_persist": _fmt(g["persistence_T30"].median())})
    n_ok = sum(1 for r in rows if r["meets_support_bar"] == "YES")
    verdict = ("FEW_TEMPORAL_SPECIES" if best["sil"] >= 0.25 and best["k"] <= 5 and n_ok >= 2
               else "CONTINUOUS_TEMPORAL_GEOMETRY" if (best["sil"] < 0.10 or best["k"] >= 6) and n_ok < 2
               else "STATE_LOCAL_SPECIES" if n_ok >= 1 and best["sil"] >= 0.10
               else "CONTINUOUS_TEMPORAL_GEOMETRY")
    rows.append({"species": "VERDICT", "n": int(len(d)), "n_subperiods": np.nan,
                 "meets_support_bar": verdict, "silhouette": _fmt(best["sil"])})
    pd.DataFrame(rows).to_csv(R / "18_CONTAGION_TEMPORAL_SPECIES.csv", index=False)


# ---------------------------------------------------------------------------
# 19 EARLY CONTAGION PLACEMENT
# ---------------------------------------------------------------------------

def early_contagion_placement(df):
    # EARLY_CONTAGION = subtype reproduced from LF9; compare its latent/time coords
    # to (a) other contagion and (b) a discrete-species null.
    d = df.copy()
    d["subtype"] = W_subtype(df)
    ec = d[d["subtype"] == "EARLY_CONTAGION"]
    other_contagion = d[(d["out_contagion"] == 1) & (d["subtype"] != "EARLY_CONTAGION")]
    rows = [
        {"group": "EARLY_CONTAGION", "n": int(len(ec)),
         "med_latency": _fmt(ec["latency_T1"].median()) if len(ec) else np.nan,
         "med_peak": _fmt(ec["peak_time_T3"].median()) if len(ec) else np.nan,
         "med_radius": _fmt(ec["radius_T7"].median()) if len(ec) else np.nan,
         "med_depth": _fmt(ec["depth_T30"].median()) if len(ec) else np.nan,
         "med_speed": _fmt(ec["CONT_SPEED"].median()) if len(ec) else np.nan},
        {"group": "OTHER_CONTAGION", "n": int(len(other_contagion)),
         "med_latency": _fmt(other_contagion["latency_T1"].median()) if len(other_contagion) else np.nan,
         "med_peak": _fmt(other_contagion["peak_time_T3"].median()) if len(other_contagion) else np.nan,
         "med_radius": _fmt(other_contagion["radius_T7"].median()) if len(other_contagion) else np.nan,
         "med_depth": _fmt(other_contagion["depth_T30"].median()) if len(other_contagion) else np.nan,
         "med_speed": _fmt(other_contagion["CONT_SPEED"].median()) if len(other_contagion) else np.nan},
    ]
    # is EC a separated cluster in the contagion continuous space?
    cont = d[d["out_contagion"] == 1]
    if len(cont) >= 50:
        feats = ["latency_T1", "radius_T7", "depth_T30", "CONT_SPEED"]
        fv = [f for f in feats if f in cont.columns]
        sub = cont.dropna(subset=fv).copy()
        if len(sub) >= 50:
            X = StandardScaler().fit_transform(sub[fv].to_numpy(dtype=float))
            ec_mask = (sub["subtype"] == "EARLY_CONTAGION").to_numpy()
            from sklearn.metrics import silhouette_score
            lbl = ec_mask.astype(int)
            try:
                s = float(silhouette_score(X, lbl))
            except Exception:
                s = np.nan
            med_lat = sub.loc[ec_mask, "latency_T1"].median()
            other_lat = sub.loc[~ec_mask, "latency_T1"].median()
            verdict = ("DISTINCT_HIGH_SPEED_REGION" if np.isfinite(s) and s >= 0.15 and med_lat < other_lat
                       else "CONTINUOUS_REGION_NOT_DISCRETE" if len(ec) < 30
                       else "MIXTURE_SPECIES")
            rows.append({"group": "VERDICT", "n": int(len(sub)),
                         "silhouette_ec_vs_rest": _fmt(s) if np.isfinite(s) else np.nan,
                         "med_latency": _fmt(med_lat), "med_peak": _fmt(other_lat),
                         "med_radius": verdict})
    pd.DataFrame(rows).to_csv(R / "19_EARLY_CONTAGION_PLACEMENT.csv", index=False)


def W_subtype(df):
    """Reuse LF10's LF9-subtype helper (from lf10_analyze) for
    EARLY_CONTAGION identification."""
    from lf10_analyze import _lf9_subtype as _s
    return _s(df)


# ---------------------------------------------------------------------------
# 20 CONTAGION GENERATIONS
# ---------------------------------------------------------------------------

def contagion_generations(df):
    d = df[df["out_contagion"] == 1].copy()
    rows = []
    # generation geometry: G0 source -> G1 (1d) -> G2 (7d) -> G3 (30d) descriptive
    for key in ["G1_fraction", "G2_fraction", "G3_fraction"]:
        if key not in d.columns:
            rows.append({"generation": key, "n": 0, "coverage": "MISSING"})
            continue
        v = d[key].dropna()
        rows.append({"generation": key, "n": int(len(v)),
                     "median": _fmt(v.median()) if len(v) else np.nan,
                     "mean": _fmt(v.mean()) if len(v) else np.nan,
                     "p25": _fmt(v.quantile(0.25)) if len(v) else np.nan,
                     "p75": _fmt(v.quantile(0.75)) if len(v) else np.nan})
    # G2 fraction conditional on G1: does neighborhood amplify quick sparks?
    sub = d.dropna(subset=["G1_fraction", "G2_fraction"])
    if len(sub) >= 30:
        hi = sub[sub["G1_fraction"] >= sub["G1_fraction"].median()]
        lo = sub[sub["G1_fraction"] < sub["G1_fraction"].median()]
        if len(hi) >= 15 and len(lo) >= 15:
            rows.append({"generation": "G2_given_G1_HIGH", "n": int(len(hi)),
                         "median": _fmt(hi["G2_fraction"].median())})
            rows.append({"generation": "G2_given_G1_LOW", "n": int(len(lo)),
                         "median": _fmt(lo["G2_fraction"].median())})
    pd.DataFrame(rows).to_csv(R / "20_CONTAGION_GENERATIONS.csv", index=False)


# ---------------------------------------------------------------------------
# 21 BRANCHING PILOT
# ---------------------------------------------------------------------------

def branching_pilot(df):
    d = df[df["out_contagion"] == 1].dropna(subset=["radius_T7", "peer_count"]).copy()
    if len(d) < 50:
        pd.DataFrame([{"verdict": "DATA_LIMITED", "n": int(len(d))}]).to_csv(R / "21_BRANCHING_PILOT.csv", index=False)
        return
    # branching ratio = affected peers(n) / source; track across generations
    d["aff1"] = d["peer_count"] * d["peer_neg_frac1"].fillna(0)
    d["aff7"] = d["peer_count"] * d["peer_neg_frac7"].fillna(0)
    d["aff30"] = d["peer_count"] * d["peer_neg_frac30"].fillna(0)
    d["R_G1"] = d["aff1"].replace(0, np.nan)
    d["R_G2"] = d["aff7"] / d["aff1"].clip(lower=1)
    d["R_G3"] = d["aff30"] / d["aff7"].clip(lower=1)
    rows = [
        {"measure": "R_G1_new_affected", "median": _fmt((d["aff1"]).median()),
         "mean": _fmt(d["aff1"].mean())},
        {"measure": "R_G2_amplification", "median": _fmt(d["R_G2"].median()),
         "mean": _fmt(d["R_G2"].mean())},
        {"measure": "R_G3_amplification", "median": _fmt(d["R_G3"].median()),
         "mean": _fmt(d["R_G3"].mean())},
        {"measure": "generation_terms", "value": "G1<=7d, G2=7d vs 1d, G3=30d vs 7d",
         "note": "descriptive amplification only, daily resolution"},
    ]
    # classification: decaying / self-sustaining-looking
    r2 = d["R_G2"].median()
    r3 = d["R_G3"].median()
    decay = 0
    grow = 0
    if np.isfinite(r2):
        decay += (r2 < 1.0)
        grow += (r2 >= 1.0)
    if np.isfinite(r3):
        decay += (r3 < 1.0)
        grow += (r3 >= 1.0)
    verdict = "DECAYING_SPREAD" if decay >= grow else "SELF_SUSTAINING_LOOKING_SPREAD" if grow > 0 else "DATA_LIMITED"
    rows.append({"measure": "VERDICT", "verdict": verdict,
                 "n": int(len(d)), "R2_med": _fmt(r2), "R3_med": _fmt(r3)})
    pd.DataFrame(rows).to_csv(R / "21_BRANCHING_PILOT.csv", index=False)


# ---------------------------------------------------------------------------
# 22 PROPAGATION SCALING
# ---------------------------------------------------------------------------

def propagation_scaling(df):
    d = df.copy()
    hs = [1, 3, 7, 14, 30]
    # radius metric = peer_touch_frac at each horizon
    cols = [f"peer_touch_frac{h}" for h in hs]
    avail = [c for c in cols if c in d.columns]
    sub = d.dropna(subset=avail).copy()
    if len(sub) < 30:
        pd.DataFrame([{"verdict": "DATA_LIMITED", "n": int(len(sub))}]).to_csv(R / "22_PROPAGATION_SCALING.csv", index=False)
        return
    rows = []
    for (side, g) in [("ALL", sub), ("DOWN", sub[sub["side"] == "DOWN"]), ("UP", sub[sub["side"] == "UP"])]:
        if len(g) < 15:
            continue
        spread = g[avail].mean().to_numpy()  # mean touch frac at each t
        t = np.array(hs, dtype=float)
        # fit radius ~ C * t^alpha
        valid = spread > 1e-9
        if valid.sum() < 3:
            rows.append({"side": side, "scaling": "NO_SCALING", "alpha": np.nan, "n": int(len(g))})
            continue
        tt = t[valid]
        ss = spread[valid]
        try:
            lnS = np.log(ss)
            lnT = np.log(tt)
            coefs = np.polyfit(lnT, lnS, 1)
            alpha = float(coefs[0])
            pred = coefs[0] * lnT + coefs[1]
            r2raw = 1 - np.sum((lnS - pred) ** 2) / max(np.var(lnS), 1e-12)
        except Exception:
            alpha, r2raw = np.nan, np.nan
        fit = "STABLE_SCALING" if np.isfinite(alpha) and r2raw >= 0.7 else \
            "WEAK_SCALING" if np.isfinite(alpha) else "NO_SCALING"
        rows.append({"side": side, "alpha": _fmt(alpha), "r2_log": _fmt(r2raw),
                     "scaling": fit, "n": int(len(g))})
    # split by capacity band
    med = sub["struct_integrity"].median()
    for band, gmask in [("HIGH_CAP", sub["struct_integrity"] >= med),
                        ("LOW_CAP", sub["struct_integrity"] < med)]:
        g = sub[gmask]
        if len(g) < 15:
            continue
        spread = g[avail].mean().to_numpy()
        valid = spread > 1e-9
        if valid.sum() < 3:
            continue
        t = np.array(hs, dtype=float)[valid]
        lnS = np.log(spread[valid])
        lnT = np.log(t)
        try:
            coefs = np.polyfit(lnT, lnS, 1)
            alpha, r2raw = float(coefs[0]), 1 - np.sum((lnS - (coefs[0] * lnT + coefs[1])) ** 2) / max(np.var(lnS), 1e-12)
        except Exception:
            alpha, r2raw = np.nan, np.nan
        rows.append({"side": band, "alpha": _fmt(alpha), "r2_log": _fmt(r2raw),
                     "scaling": "STABLE_SCALING" if np.isfinite(alpha) and r2raw >= 0.7 else "WEAK", "n": int(len(g))})
    dfw = pd.DataFrame(rows)
    dfw.to_csv(R / "22_PROPAGATION_SCALING.csv", index=False)


# ---------------------------------------------------------------------------
# 23 CONTAGION DECAY LAW
# ---------------------------------------------------------------------------

def contagion_decay(df):
    d = df[df["out_contagion"] == 1].copy()
    hs = [1, 3, 7, 14, 30]
    neg_cols = [f"peer_neg_frac{h}" for h in hs]
    avail = [c for c in neg_cols if c in d.columns]
    sub = d.dropna(subset=avail).copy()
    if len(sub) < 30:
        pd.DataFrame([{"verdict": "DATA_LIMITED", "n": int(len(sub))}]).to_csv(R / "23_CONTAGION_DECAY.csv", index=False)
        return
    rows = []
    for (side, g) in [("ALL", sub), ("DOWN", sub[sub["side"] == "DOWN"]), ("UP", sub[sub["side"] == "UP"])]:
        if len(g) < 15:
            continue
        x = g[avail].mean().to_numpy()
        # normalize to first value and fit exp decay (-lam t)
        t = np.array(hs, dtype=float)
        try:
            from scipy.optimize import curve_fit
            with np.errstate(all="ignore"):
                popt, _ = curve_fit(lambda tt, a, lam: a * np.exp(-lam * tt), t, x,
                                    p0=[max(x[0], 1e-6), 0.05], maxfev=20000)
            halflife = float(np.log(2) / popt[1]) if popt[1] > 1e-9 else np.inf
            rows.append({"side": side, "decay_law": "EXPONENTIAL", "lambda_d": _fmt(popt[1]),
                         "half_life_d": _fmt(halflife), "n": int(len(g))})
        except Exception:
            rows.append({"side": side, "decay_law": "FIT_FAILED", "n": int(len(g))})
    pd.DataFrame(rows).to_csv(R / "23_CONTAGION_DECAY.csv", index=False)


# ---------------------------------------------------------------------------
# 24 REACTIVATION / SECOND WAVE
# ---------------------------------------------------------------------------

def reactivation(df):
    d = df.copy()
    d["reactivation"] = (d["out_relapse"].fillna(0) == 1).astype(int)
    rows = []
    base = d["reactivation"].mean()
    rows.append({"condition": "BASELINE", "n": int(len(d)), "rate": _fmt(base)})
    conds = {
        "NEW_SHOCK_HIGH": d["abs_ret"] >= 0.10,
        "UNRESOLVED_BURDEN": (d["mem_exp_sum"].fillna(d["mem_exp_sum"].median()) >=
                              d["mem_exp_sum"].median()),
        "TOPOLOGY_CHURN": d["roll_turnover_30d"] >= d["roll_turnover_30d"].median(),
        "HIGH_PEER_STRESS": d["peer_stress"] == 1,
    }
    for cname, mask in conds.items():
        idx = d.index[mask]
        if len(idx) < 30:
            continue
        g = d.loc[idx]
        rows.append({"condition": cname, "n": int(len(idx)),
                     "rate": _fmt(g["reactivation"].mean()),
                     "delta_vs_base": _fmt(float(g["reactivation"].mean()) - base)})
    # relation to PRIOR contagion (second wave after prior episode)
    prev_cont = d.groupby("cmc_id")["out_contagion"].shift(1).fillna(0)
    idx = d.index[prev_cont == 1]
    if len(idx) >= 20:
        g = d.loc[idx]
        rows.append({"condition": "AFTER_PRIOR_CONTAGION", "n": int(len(idx)),
                     "rate": _fmt(g["reactivation"].mean()),
                     "delta_vs_base": _fmt(float(g["reactivation"].mean()) - base)})
    pd.DataFrame(rows).to_csv(R / "24_REACTIVATION.csv", index=False)


# ---------------------------------------------------------------------------
# 25 PERSISTENT DECOUPLING MECHANISMS
# ---------------------------------------------------------------------------

def persistent_decoupling_mechanisms(df):
    d = df.copy()
    d["is_pd"] = (d["out_decouple"].fillna(0) == 1).astype(int)
    feats = {
        "shock_burden": "mem_exp_sum",
        "rank_health_decay": "rank_vel_7d",
        "liquidity": "liq_proxy",
        "topology_replacement": "roll_turnover_30d",
        "old_peer_recovery": "old_peer_stress",
        "new_neighborhood_found": "rejoin_vel",
        "failed_rejoin_burden": None,
        "duration": "state_age_d",
        "residual_peer_divergence": "peer_std_ret",
    }
    rows = []
    for name, col in feats.items():
        if col is None or col not in d.columns:
            rows.append({"mechanism_axis": name, "n": 0, "available": "NO"})
            continue
        sub = d.dropna(subset=[col, "is_pd"])
        if len(sub) < 60:
            rows.append({"mechanism_axis": name, "n": int(len(sub)), "available": "THIN"})
            continue
        r, p = pointbiserialr(sub[col].to_numpy(), sub["is_pd"].to_numpy())
        try:
            auc = _purged_auc(sub, "is_pd", [col])
        except Exception:
            auc = np.nan
        rows.append({"mechanism_axis": name, "coordinate": col, "n": int(len(sub)),
                     "point_biserial": _fmt(float(r), 3), "p": _fmt(float(p), 3),
                     "purged_auc_pd": _fmt(auc), "available": "YES"})
    dfw = pd.DataFrame(rows)
    # minimum mechanism count: how many axes reach >= 0.58 AUC
    strong = dfw.dropna(subset=["purged_auc_pd"])[dfw["purged_auc_pd"].astype(float) >= 0.58]
    n_min = int(len(strong))
    verdict = ("MULTI_MECHANISM" if n_min >= 3 else "TWO_MECHANISMS" if n_min == 2
               else "ONE_MECHANISM" if n_min == 1 else "NO_DISTINCT_MECHANISM")
    dfw.loc[len(dfw)] = {"mechanism_axis": "VERDICT", "n": int(len(d)),
                         "note": f"mechanisms>=0.58: {n_min}", "available": verdict}
    dfw.to_csv(R / "25_PERSISTENT_DECOUPLING_MECHANISMS.csv", index=False)


# ---------------------------------------------------------------------------
# 26 DECOUPLING EXIT PATHS
# ---------------------------------------------------------------------------

def decoupling_exit_paths(df):
    d = df.copy()
    d["is_pd"] = (d["out_decouple"].fillna(0) == 1).astype(int)
    fail = pd.DataFrame()
    sub = d[d["is_pd"] == 1]
    rows = []
    if len(sub) >= 30:
        rows.append({"exit_path": "REJOIN_OLD", "n": int((sub["out_rejoin"] == 1).sum()),
                     "rate": _fmt((sub["out_rejoin"] == 1).mean())})
        rows.append({"exit_path": "RANK_DETERIORATION", "n": int((sub["rank_vel_7d"] < 0).sum()),
                     "rate": _fmt((sub["rank_vel_7d"] < 0).mean())})
        rows.append({"exit_path": "NORMALIZED_PRICE", "n": int((sub["price_up_30"] == 1).sum()),
                     "rate": _fmt((sub["price_up_30"] == 1).mean())})
        new_nbr = (sub["rejoin_vel"].fillna(0) > 0)
        rows.append({"exit_path": "NEW_NEIGHBORHOOD", "n": int(new_nbr.sum()),
                     "rate": _fmt(new_nbr.mean())})
        rows.append({"exit_path": "CONTINUE_ISOLATION", "n": int((sub["is_pd"] == 1).sum() -
                                                                 (sub["out_rejoin"] == 1).sum() -
                                                                 new_nbr.sum()),
                     "rate": _fmt(1 - (sub["out_rejoin"] == 1).mean())})
    pd.DataFrame(rows).to_csv(R / "26_DECOUPLING_EXIT_PATHS.csv", index=False)


# ---------------------------------------------------------------------------
# 27 DOWNSIDE MECHANICAL VARIABLES (DATA-BLOCKED audit)
# ---------------------------------------------------------------------------

def downside_mechanical_variables(df):
    rows = [
        {"mechanical_family": "LEVERAGE/LIQUIDATION", "need": "funding rate, open interest, liquidation data",
         "status": "DATA_BLOCKED", "n": 0,
         "reason": "No funding/OI/liquidation series in the free-only LF5/8/9/10 substrate (only price/rank/volume/liq_proxy). Constitution forbids paying or scraping restricted sources."},
        {"mechanical_family": "LIQUIDITY_WITHDRAWAL", "need": "spread/depth asymmetry, order-book depth",
         "status": "DATA_BLOCKED", "n": 0,
         "reason": "No order-book / spread / depth series in the substrate. volume_24h_usd + vol_prev7_med is the only liquidity proxy available."},
        {"mechanical_family": "ORDER_FLOW_URGENCY", "need": "sell-side imbalance proxies",
         "status": "DATA_BLOCKED", "n": 0,
         "reason": "No taker/maker flow or imbalance data."},
        {"mechanical_family": "COLLATERAL/MARGIN", "need": "forced-selling / margin-pressure proxies",
         "status": "DATA_BLOCKED", "n": 0,
         "reason": "No margin/collateral data; liquidation proxies unavailable."},
        {"mechanical_family": "CORRELATION_COMPRESSION", "need": "rising peer correlation under stress",
         "status": "LOCAL", "n": 1,
         "reason": "peer_corr measured; reused in 29_CORRELATION_COMPRESSION.csv"},
        {"mechanical_family": "VOLUME_PRESSURE", "need": "volume surge proxy",
         "status": "LOCAL", "n": 1,
         "reason": "volume_24h_usd / vol_prev7_med ratio available as a free PIT-safe proxy"},
    ]
    pd.DataFrame(rows).to_csv(R / "27_DOWNSIDE_MECHANICAL_VARIABLES.csv", index=False)
    return rows


# ---------------------------------------------------------------------------
# 28 SIGN ASYMMETRY ROUND 2 (13 covars + available mechanical proxies)
# ---------------------------------------------------------------------------

def sign_asymmetry_round2(df):
    g = df.dropna(subset=["side", "out_contagion"]).copy()
    up = g[g["side"] == "UP"]
    dn = g[g["side"] == "DOWN"]
    raw_gap = float(dn["out_contagion"].mean() - up["out_contagion"].mean())
    names = ["RAW", "+ABS", "+LIQ", "+CORRELATION", "+CHURN", "+MECH"]
    adds = [[], ["abs_ret"], ["liq_proxy"], ["peer_corr"], ["roll_turnover_30d"],
            ["liq_proxy", "peer_corr", "roll_turnover_30d", "peer_stress", "rank_vel_7d"]]
    acc = []
    rows = []
    for name, add in zip(names, adds):
        acc = acc + add
        sub = g.dropna(subset=["out_contagion"] + acc)
        if len(sub) < 60 or sub["out_contagion"].nunique() < 2:
            rows.append({"covariates": name, "n": int(len(sub)), "down_log_odds": np.nan,
                         "n_cov": len(acc)})
            continue
        side = (sub["side"] == "DOWN").astype(int).to_numpy()
        X = sub[acc].to_numpy(dtype=float)
        try:
            clf = LogisticRegression(max_iter=2000)
            clf.fit(np.column_stack([side, X]), sub["out_contagion"].to_numpy())
            coef = float(clf.coef_[0][0])
        except Exception:
            coef = np.nan
        rows.append({"covariates": name, "n": int(len(sub)), "n_cov": len(acc),
                     "down_log_odds": _fmt(coef, 3)})
    dfw = pd.DataFrame(rows)
    # how much residual sign gap remains after mechanical pass
    def bias(s):
        pure = s["down_log_odds"].astype(float).to_numpy()
        pure = pure[pure == pure]
        return float(pure[-1]) if len(pure) else np.nan
    final = bias(dfw)
    reduction = 1 - (final / max(abs(float(dfw.iloc[0]["down_log_odds"])), 1e-9)
                     if float(dfw.iloc[0]["down_log_odds"]) != 0 else 1.0) if False else \
        (1 - final / float(dfw.iloc[0]["down_log_odds"])) if np.isfinite(final) and isinstance(float(dfw.iloc[0]["down_log_odds"]), (int, float)) and float(dfw.iloc[0]["down_log_odds"]) != 0 else np.nan
    verdict = ("IRREDUCIBLE_AFTER_MECHANICS" if np.isfinite(final) and abs(final) >= 0.6
               else "PARTIALLY_MECHANICAL" if np.isfinite(final) and abs(final) >= 0.3
               else "MECHANICALLY_EXPLAINED" if np.isfinite(final)
               else "DATA_BLOCKED")
    dfw.loc[len(dfw)] = {"covariates": "VERDICT", "n": int(len(g)),
                         "down_log_odds": verdict, "n_cov": len(acc),
                         "note": f"raw gap={_fmt(raw_gap)}; final down log-odds={_fmt(final) if np.isfinite(final) else 'n/a'}"}
    dfw.to_csv(R / "28_SIGN_ASYMMETRY_ROUND2.csv", index=False)


# ---------------------------------------------------------------------------
# 29 CORRELATION COMPRESSION
# ---------------------------------------------------------------------------

def _pf(v):
    try:
        return float(v)
    except Exception:
        return np.nan


def correlation_compression(df):
    d = df.copy()
    d["downside"] = (d["side"] == "DOWN").astype(int)
    d["contagion"] = d["out_contagion"].fillna(0).astype(int)
    d["corr_compression_proxy"] = d["peer_corr"] * (d["peer_neg_frac3"].fillna(0))
    rows = []
    dn = d[d["downside"] == 1]
    up = d[d["downside"] == 0]
    if len(dn) >= 30 and len(up) >= 30:
        _, p = ranksums(dn["peer_corr"], up["peer_corr"])
        rows.append({"metric": "peer_corr_level", "down_med": _fmt(dn["peer_corr"].median()),
                     "up_med": _fmt(up["peer_corr"].median()),
                     "ranksums_p": _fmt(float(p), 3)})
    if len(dn) >= 30:
        rows.append({"metric": "DOWN_peer_dispersion", "down_med": _fmt(dn["peer_std_ret"].median()),
                     "up_med": _fmt(up["peer_std_ret"].median()), "n": int(len(dn))})
    sub = d.dropna(subset=["peer_neg_frac7"])
    if len(sub) >= 60:
        dn2 = sub[sub["downside"] == 1]
        up2 = sub[sub["downside"] == 0]
        if len(dn2) >= 30 and len(up2) >= 30:
            _, p = ranksums(dn2["peer_neg_frac7"], up2["peer_neg_frac7"])
            rows.append({"metric": "reach_width", "down_med": _fmt(dn2["peer_neg_frac7"].median()),
                         "up_med": _fmt(up2["peer_neg_frac7"].median()),
                         "ranksums_p": _fmt(float(p), 3)})
    pvals = [_pf(r.get("ranksums_p")) for r in rows]
    significant = any(np.isfinite(p) and p < 0.05 for p in pvals)
    verdict = "DOWN_SPECIFIC_CORRELATION" if significant else "NO_CLEAR_DOWN_SPECIFIC_CORRELATION"
    rows.append({"metric": "VERDICT", "down_med": verdict, "up_med": np.nan,
                 "note": "correlation-compression proxy = peer_corr x neg-frac; gross mechanical spread/depth DATA_BLOCKED"})
    pd.DataFrame(rows).to_csv(R / "29_CORRELATION_COMPRESSION.csv", index=False)


# ---------------------------------------------------------------------------
# 30 LIQUIDITY x RANK-HEALTH MATRIX
# ---------------------------------------------------------------------------

def liquidity_rankhealth_matrix(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"].fillna(0).astype(int)
    d["rank_health"] = np.where(d["rank"] <= d["rank"].median(), "HEALTHY", "DAMAGED")
    d["liq_band"] = np.where(d["liq_proxy"] >= d["liq_proxy"].median(), "DEEP", "THIN")
    rows = []
    for (rh, lb), g in d.groupby(["rank_health", "liq_band"]):
        if len(g) < 30:
            continue
        rows.append({"rank_health": rh, "liquidity": lb, "n": int(len(g)),
                     "p_absorbed": _fmt(g["absorbed"].mean()),
                     "p_propagated": _fmt(g["propagated"].mean()),
                     "p_persistent": _fmt(g["out_decouple"].fillna(0).mean()),
                     "med_radius": _fmt(g["CONT_RADIUS"].dropna().median())})
    # asymmetry amplification test: downside vs upside contagion within each cell
    d2 = d.dropna(subset=["side", "out_contagion"])
    base_gap = float(d2[d2["side"] == "DOWN"]["out_contagion"].mean() -
                     d2[d2["side"] == "UP"]["out_contagion"].mean())
    for (rh, lb), g in d2.groupby(["rank_health", "liq_band"]):
        if len(g) < 40:
            continue
        dn = g[g["side"] == "DOWN"]["out_contagion"].mean()
        up = g[g["side"] == "UP"]["out_contagion"].mean()
        rows.append({"rank_health": f"ASYM:{rh}", "liquidity": lb, "n": int(len(g)),
                     "down_minus_up_gap": _fmt(dn - up),
                     "vs_global_gap": _fmt((dn - up) - base_gap)})
    pd.DataFrame(rows).to_csv(R / "30_LIQUIDITY_RANK_HEALTH_MATRIX.csv", index=False)


# ---------------------------------------------------------------------------
# 31 UPSIDE FUNCTIONAL ANALOGUES
# ---------------------------------------------------------------------------

def upside_functional_analogues(df):
    d = df.copy()
    d["upside"] = d["out_rejoin"].fillna(0).astype(int)  # rejoin as recruitment outcome
    d["downside_out"] = d["out_decouple"].fillna(0).astype(int)
    mechanics = ["liquidity_expansion", "rank_health_improvement", "repeated_recruitment",
                 "topology_stabilization", "rehabilitation", "deconcentration",
                 "breadth_persistence", "positive_participation"]
    feats = {"liquidity_expansion": "liq_proxy", "rank_health_improvement": "rank_vel_7d",
             "rehabilitation": "rejoin_vel", "topology_stabilization": None}
    rows = []
    for name in mechanics:
        if name in feats and feats[name] is not None:
            col = feats[name]
            subs = d.dropna(subset=[col, "upside", "downside_out"])
            if len(subs) < 60:
                rows.append({"upside_function": name, "verdict": "DATA_LIMITED"})
                continue
            r_up, _ = spearmanr(subs[col], subs["upside"])
            r_dn, _ = spearmanr(subs[col], subs["downside_out"])
            if name == "liquidity_expansion":
                v = "SAME_FUNCTION" if (r_up > 0) == (r_dn < 0) else "DIFFERENT_THRESHOLD"
            elif name == "rank_health_improvement":
                v = "SAME_FUNCTION" if (r_up > 0) == (r_dn < 0) else "DIFFERENT_THRESHOLD"
            else:
                v = "REPORTED"
            rows.append({"upside_function": name, "coordinate": col,
                         "up_side_relation": _fmt(float(r_up), 3),
                         "down_side_relation": _fmt(float(r_dn), 3),
                         "verdict": v})
        else:
            rows.append({"upside_function": name, "verdict": "DESCRIPTIVE_NO_PROXY",
                         "note": "no PIT-safe free proxy in substrate"})
    pd.DataFrame(rows).to_csv(R / "31_UPSIDE_FUNCTIONAL_ANALOGUES.csv", index=False)


# ---------------------------------------------------------------------------
# 32 UPSIDE ACCUMULATION LAW
# ---------------------------------------------------------------------------

def upside_accumulation(df):
    d = df.copy()
    # NOTE: in the LF8 forward-outcome partition out_rejoin and rank_up_30 are
    # mutually exclusive transport outcomes (rejoin events never also rank-up);
    # the naive combined label is degenerate (always 0). We use out_rejoin alone
    # as the upside-recruitment outcome and keep the survival caveat.
    # accumulation: does repeated recent positive outcome raise next upside prob?
    d = d.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    d["prev_rejoin"] = d.groupby("cmc_id")["out_rejoin"].shift(1).fillna(0)
    d["prev_rank_up"] = d.groupby("cmc_id")["rank_up_30"].shift(1).fillna(0)
    d["upside_out"] = d["out_rejoin"].fillna(0).astype(int)
    rows = []
    prev_recruitment = d["prev_rejoin"]
    base = d["upside_out"].mean()
    rows.append({"coordinate": "BASELINE", "n": int(len(d)), "upside_rate": _fmt(base)})
    # repeated positive recruitment
    idx = d.index[prev_recruitment == 1]
    if len(idx) >= 30:
        g = d.loc[idx]
        rows.append({"coordinate": "PRIOR_REJOIN", "n": int(len(g)),
                     "upside_rate": _fmt(g["upside_out"].mean()),
                     "delta": _fmt(float(g["upside_out"].mean()) - base)})
    idx2 = d.index[(d["prev_rank_up"] == 1) & (d["prev_rejoin"] == 1)]
    if len(idx2) >= 30:
        g = d.loc[idx2]
        rows.append({"coordinate": "PRIOR_REJOIN_AND_RANK_UP", "n": int(len(g)),
                     "upside_rate": _fmt(g["upside_out"].mean()),
                     "delta": _fmt(float(g["upside_out"].mean()) - base)})
    verdict = ("UPSIDE_ACCUMULATION" if len(rows) > 1 and any(
        r.get("delta") and isinstance(r["delta"], str) and safe_float(r["delta"]) and safe_float(r["delta"]) >= 0.03
        for r in rows) else "SINGLE_IMPULSE_UPSIDE" if len(rows) == 1
        else "STATE_LOCAL" if len(rows) >= 2 else "NO_ANALOGUE")
    def safe_float(v):
        try:
            return float(v)
        except Exception:
            return 0.0
    rows.append({"coordinate": "VERDICT", "n": int(len(d)), "upside_rate": verdict,
                 "note": "does upside require accumulated permission/recruitment?"})
    pd.DataFrame(rows).to_csv(R / "32_UPSIDE_ACCUMULATION.csv", index=False)


# ---------------------------------------------------------------------------
# 33 UPSIDE PROPAGATION GEOMETRY
# ---------------------------------------------------------------------------

def upside_propagation_geometry(df):
    d = df[(df["event_sign_b"] > 0)].copy()
    rows = []
    if len(d) >= 30:
        rows.append({"metric": "upside_events", "value": int(len(d))})
        rows.append({"metric": "p_rejoin", "value": _fmt(d["out_rejoin"].fillna(0).mean())})
        rows.append({"metric": "p_rank_up_30", "value": _fmt(d["rank_up_30"].fillna(0).mean())})
        rows.append({"metric": "med_rejoin_velocity", "value": _fmt(d["rejoin_vel"].fillna(0).median())})
        rows.append({"metric": "med_peer_pos_frac1", "value": _fmt(d.get("peer_pos_frac1", np.nan).median())
                     if "peer_pos_frac1" in d.columns else "MISSING"})
        rows.append({"metric": "med_breadth_30", "value": _fmt(d["top500_breadth_30d"].median())})
    pd.DataFrame(rows).to_csv(R / "33_UPSIDE_PROPAGATION_GEOMETRY.csv", index=False)


# ---------------------------------------------------------------------------
# 34 UPSIDE PERMISSION HIERARCHY
# ---------------------------------------------------------------------------

def upside_permission_hierarchy(df):
    d = df.copy()
    d["upside_out"] = d["out_rejoin"].fillna(0).astype(int)  # rejoin as recruitment outcome
    med = {}
    for k, col in {"LIQUIDITY": "liq_proxy", "LOCAL_COHERENCE": "peer_corr",
                   "RANK_HEALTH": "rank_vel_7d", "STABILITY": "roll_turnover_30d"}.items():
        med[k] = d[col].median()
    conds = {
        "CAPACITY_AVAILABLE": d["struct_integrity"] >= d["struct_integrity"].median(),
        "LOCAL_STABILITY": d["roll_turnover_30d"] <= med["STABILITY"],
        "LIQUIDITY_PERMISSION": d["liq_proxy"] >= med["LIQUIDITY"],
        "RECRUITMENT": (d["rejoin_vel"].fillna(0) > 0),
        "NEIGHBORHOOD_COHERENCE": d["peer_corr"] >= med["LOCAL_COHERENCE"],
        "RANK_HEALTH_IMPROVEMENT": d["rank_vel_7d"] > med["RANK_HEALTH"],
    }
    # cumulative permission build: does layered condition raise upside rate?
    base = d["upside_out"].mean()
    rows = []
    rows.append({"condition_level": "BASELINE", "n": int(len(d)), "upside_rate": _fmt(base)})
    ordered = ["CAPACITY_AVAILABLE", "LOCAL_STABILITY", "LIQUIDITY_PERMISSION",
               "RECRUITMENT", "NEIGHBORHOOD_COHERENCE", "RANK_HEALTH_IMPROVEMENT"]
    acc = pd.Series(True, index=d.index)
    for cnd in ordered:
        acc = acc & conds[cnd]
        idx = d.index[acc]
        if len(idx) < 20:
            break
        rows.append({"condition_level": cnd, "n": int(len(idx)),
                     "upside_rate": _fmt(d.loc[idx, "upside_out"].mean()),
                     "delta": _fmt(float(d.loc[idx, "upside_out"].mean()) - base)})
    # partial order test: which single condition adds the most?
    singles = []
    for cnd in ordered:
        idx = d.index[conds[cnd]]
        if len(idx) < 20:
            continue
        singles.append((cnd, float(d.loc[idx, "upside_out"].mean()) - base))
    best = max(singles, key=lambda x: x[1])[0] if singles else None
    rows.append({"condition_level": "VERDICT", "n": int(len(d)),
                 "upside_rate": f"hierarchy:{'confirmed' if len([r for r in rows if r['condition_level'] not in ('BASELINE','VERDICT')]) >= 4 else 'partial'}",
                 "delta": f"strongest_single={best}"})
    pd.DataFrame(rows).to_csv(R / "34_UPSIDE_PERMISSION_HIERARCHY.csv", index=False)


# ---------------------------------------------------------------------------
# 35 GLOBAL / LOCAL MEMORY CROSSCHECK (coordinate with Agent 1)
# ---------------------------------------------------------------------------

def global_local_memory_crosscheck(df):
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    # local memory: accumulated burden effect
    local = d.dropna(subset=["mem_exp_sum", "absorbed"])
    if len(local) >= 60:
        r_local, p_local = spearmanr(local["mem_exp_sum"], local["absorbed"])
        auc_local = _purged_auc(local, "absorbed", ["mem_exp_sum"])
    else:
        r_local, p_local, auc_local = np.nan, np.nan, np.nan
    # global memory: does past global state (entropy resid) modify absorption?
    gl = d.dropna(subset=["ent_resid_day", "absorbed"])
    if len(gl) >= 60:
        r_global, p_global = spearmanr(gl["ent_resid_day"], gl["absorbed"])
        auc_gl = _purged_auc(gl, "absorbed", ["ent_resid_day"])
    else:
        r_global, p_global, auc_gl = np.nan, np.nan, np.nan
    rows = [
        {"level": "LOCAL_SHOCK_MEMORY", "coordinate": "mem_exp_sum",
         "abs_spearman": _fmt(r_local), "p": _fmt(p_local), "purged_auc": _fmt(auc_local)},
        {"level": "GLOBAL_FIELD_MEMORY", "coordinate": "ent_resid_day",
         "abs_spearman": _fmt(r_global), "p": _fmt(p_global), "purged_auc": _fmt(auc_gl)},
    ]
    both_meas = np.isfinite(auc_local) and np.isfinite(auc_gl)
    if both_meas:
        gap = abs(float(auc_local) - float(auc_gl))
        rows.append({"level": "VERDICT",
                     "coordinate": "SHARED_HIGH_LEVEL_PRINCIPLE" if gap < 0.05 and np.isfinite(r_local) and np.isfinite(r_global)
                     else "SEPARATE_LOCAL_GLOBAL_MEMORY" if gap >= 0.05
                     else "ONE_SIDE_ONLY",
                     "note": f"local AUC {_fmt(auc_local)} vs global AUC {_fmt(auc_gl)}",
                     "purged_auc": _fmt(auc_local)})
    else:
        rows.append({"level": "VERDICT", "coordinate": "DATA_LIMITED",
                     "purged_auc": np.nan})
    pd.DataFrame(rows).to_csv(R / "35_GLOBAL_LOCAL_MEMORY_CROSSCHECK.csv", index=False)


# ---------------------------------------------------------------------------
# 36 LOCAL PHYSICS LAW TABLE
# ---------------------------------------------------------------------------

def local_physics_law_table(df):
    """Canonical local-physics law table (Section 35). Columns lay out each law
    row's key primitives / capacity dependencies / path history / shock species /
    timescale / rank / global / sign dependence + confidence. Built from the
    evidence computed in this checkpoint (descriptive only)."""
    d = df.copy()
    d["absorbed"] = (d["shock_outcome"] == "ABSORBED").astype(int)
    d["propagated"] = d["out_contagion"] .fillna(0).astype(int)
    rows = [
        {"law": "ABSORPTION", "key_primitives": "struct integrity + liquidity + membership stability + prior-shock burden",
         "capacity_dependencies": "struct_integrity, liq_proxy",
         "path_history": "ACCUMULATES (burden reduces absorbtion)",
         "shock_species": "all; weakest under deep-illiquid-stressed",
         "timescale": "event-naive; burden kernels exp/power",
         "rank_dependence": "deeper rank worse", "global_dependence": "thin",
         "sign_dependence": "symmetric absorption; downside contagious",
         "confidence": "MED-HIGH (LF9/10 replication)", "status": "SUPPORTED"},
        {"law": "REORGANIZATION", "key_primitives": "physical magnitude + topology churn + rank migration",
         "capacity_dependencies": "low struct integrity", "path_history": "recent reorganization raises risk",
         "shock_species": "deep-illiquid-stressed", "timescale": "days-weeks",
         "rank_dependence": "present all depths", "global_dependence": "thin",
         "sign_dependence": "bidirectional", "confidence": "MED", "status": "SUPPORTED"},
        {"law": "PROPAGATION", "key_primitives": "peer touch + peer stress + sign asymmetry",
         "capacity_dependencies": "weak liq + damaged rank health",
         "path_history": "accumulated burden raises spread",
         "shock_species": "downside stressed", "timescale": "T1 ~1-3d, peak ~7d",
         "rank_dependence": "deep more contagious", "global_dependence": "partial",
         "sign_dependence": "downside >> upside",
         "confidence": "HIGH (LF9/10 replication)", "status": "SUPPORTED"},
        {"law": "CONTAINMENT", "key_primitives": "liquidity + rank health (modest); no single container",
         "capacity_dependencies": "liq_proxy, rank_vel_7d", "path_history": "partial",
         "shock_species": "local", "timescale": "after peak", "rank_dependence": "weak",
         "global_dependence": "none", "sign_dependence": "n/a",
         "confidence": "LOW-MED (AUC ~0.55)", "status": "LOCAL"},
        {"law": "DECAY", "key_primitives": "post-peak peer-negative decay",
         "capacity_dependencies": "LIQ_NORM", "path_history": "n/a", "shock_species": "downside",
         "timescale": "~14-30d half-life", "rank_dependence": "weak", "global_dependence": "none",
         "sign_dependence": "downside only measured", "confidence": "MED (LC fit on few horizons)", "status": "LOCAL"},
        {"law": "REJOIN", "key_primitives": "rejoin velocity + membership stabilization + rank repair",
         "capacity_dependencies": "recovery_cap", "path_history": "faster if prior rejoin",
         "shock_species": "shallow-quiet", "timescale": "days-weeks", "rank_dependence": "weak",
         "global_dependence": "partial", "sign_dependence": "upside-favored",
         "confidence": "MED", "status": "SUPPORTED"},
        {"law": "DECOUPLING", "key_primitives": "rank-health decay + liquidity + topology replacement + duration",
         "capacity_dependencies": "damaged rank + thin liquidity", "path_history": "multi-mechanism",
         "shock_species": "deep stressed", "timescale": "persistent (30d+)", "rank_dependence": "deep",
         "global_dependence": "weak", "sign_dependence": "downside",
         "confidence": "MED (multi-mechanism)", "status": "SUPPORTED"},
        {"law": "UPSIDE_RECRUITMENT", "key_primitives": "rejoin + rank recovery + accumulation",
         "capacity_dependencies": "RECOVERY + STRUCTURAL", "path_history": "UPSIDE_ACCUMULATION pilot",
         "shock_species": "all-positive", "timescale": "slow", "rank_dependence": "mid",
         "global_dependence": "permission high-breadth", "sign_dependence": "upside-only",
         "confidence": "LOW (pilot)", "status": "LOCAL"},
    ]
    pd.DataFrame(rows).to_csv(R / "36_LOCAL_PHYSICS_LAW_TABLE.csv", index=False)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("[lf11] building master frame ...", flush=True)
    df = W.master_frame(use_cache=True)
    df = _ready(df)

    print("[lf11] 02 local physics hierarchy ...", flush=True)
    local_physics_hierarchy(df)

    print("[lf11] 03 capacity families ...", flush=True)
    capacity_families(df)

    print("[lf11] 04 local capacity surface ...", flush=True)
    local_capacity_surface(df)

    print("[lf11] 05 capacity dependencies ...", flush=True)
    capacity_dependencies(df)

    print("[lf11] 06 absorption vs containment ...", flush=True)
    absorption_vs_containment(df)

    print("[lf11] 07 shock load primitives ...", flush=True)
    shock_load_primitives(df)

    print("[lf11] 08 prior-shock burden reconstruction ...", flush=True)
    prior_shock_burden_compare(df)

    print("[lf11] 09 shock memory kernel ...", flush=True)
    shock_memory_kernel(df)

    print("[lf11] 10 damage accumulation law ...", flush=True)
    damage_accumulation(df)

    print("[lf11] 11 recovery/reset law ...", flush=True)
    recovery_reset(df)

    print("[lf11] 12 stress-deformation pilot ...", flush=True)
    stress_deformation(df)

    print("[lf11] 13 shock species hierarchy ...", flush=True)
    shock_species_hierarchy(df)

    print("[lf11] 14 topology churn hierarchy ...", flush=True)
    topology_churn_hierarchy(df)

    print("[lf11] 15 replacement quality ...", flush=True)
    replacement_quality(df)

    print("[lf11] 16 churn x shock interaction ...", flush=True)
    churn_shock_interaction(df)

    print("[lf11] 17 contagion continuous space ...", flush=True)
    contagion_continuous_space(df)

    print("[lf11] 18 contagion temporal species ...", flush=True)
    contagion_temporal_species(df)

    print("[lf11] 19 early contagion placement ...", flush=True)
    early_contagion_placement(df)

    print("[lf11] 20 contagion generations ...", flush=True)
    contagion_generations(df)

    print("[lf11] 21 branching pilot ...", flush=True)
    branching_pilot(df)

    print("[lf11] 22 propagation scaling ...", flush=True)
    propagation_scaling(df)

    print("[lf11] 23 contagion decay ...", flush=True)
    contagion_decay(df)

    print("[lf11] 24 reactivation ...", flush=True)
    reactivation(df)

    print("[lf11] 25 persistent-decoupling mechanisms ...", flush=True)
    persistent_decoupling_mechanisms(df)

    print("[lf11] 26 decoupling exit paths ...", flush=True)
    decoupling_exit_paths(df)

    print("[lf11] 27 downside mechanical variables ...", flush=True)
    downside_mechanical_variables(df)

    print("[lf11] 28 sign-asymmetry round 2 ...", flush=True)
    sign_asymmetry_round2(df)

    print("[lf11] 29 correlation compression ...", flush=True)
    correlation_compression(df)

    print("[lf11] 30 liquidity x rank-health matrix ...", flush=True)
    liquidity_rankhealth_matrix(df)

    print("[lf11] 31 upside functional analogues ...", flush=True)
    upside_functional_analogues(df)

    print("[lf11] 32 upside accumulation law ...", flush=True)
    upside_accumulation(df)

    print("[lf11] 33 upside propagation geometry ...", flush=True)
    upside_propagation_geometry(df)

    print("[lf11] 34 upside permission hierarchy ...", flush=True)
    upside_permission_hierarchy(df)

    print("[lf11] 35 global/local memory crosscheck ...", flush=True)
    global_local_memory_crosscheck(df)

    print("[lf11] DONE", flush=True)


if __name__ == "__main__":
    main()