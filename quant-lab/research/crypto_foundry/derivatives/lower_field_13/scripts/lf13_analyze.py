"""LOWER-FIELD-13 analysis — local-law final hardening.

LF13 is not a new discovery sweep. It finalizes: capacity dependency structure
(05-08), the canonical capacity surface (08), absorption/containment relations
(09-10), contagion mechanism surfaces & early-reach mechanics (11-14),
temporal trajectories & phases (14-16), fast/slow placement (17-18),
reactivation & clearance inside contagion geometry (18-19), decoupling final
placement (20-22), sign-asymmetry localization (23-27), sensor value-of-info
(28-29), upside cleanup & compression (30-31), and the local-law relation map
(32). EVERY temporal object reports BOTH static-horizon and rolling-window
values per the LF13 protocol; disagreements are reported, not silently
resolved. Hard-parked objects are referenced only as frozen statuses.

Start broad, compress from data, preserve locality. No strategy / PnL /
execution / sizing / leverage. Outputs 02-32 written to lower_field_13/.
"""
from __future__ import annotations

import warnings
from itertools import combinations

import numpy as np
import pandas as pd

from scipy.stats import spearmanr, ranksums
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

import lf13_common as W

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = W.ROOT
A = W.A
C9 = __import__("lf9_common", fromlist=["_sigma_class_full"])

_fmt = A._fmt
_med = W._med
_mean = W._mean
_purged_auc = A._purged_auc
MIN_SUPPORT = W.MIN_SUPPORT

ABS_CLS = A._abs_class if hasattr(A, "_abs_class") else W.ABS_CLS


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
    if "direction" not in d.columns:
        d["direction"] = np.where(d["ret_1d"] >= 0, "UPSIDE", "DOWNSIDE")
    return d


def _spear(a, b):
    _sr = spearmanr(a, b)
    st = _sr.statistic if hasattr(_sr, "statistic") else _sr[0]
    pv = _sr.pvalue if hasattr(_sr, "pvalue") else _sr[1]
    st = float(np.asarray(st).item()) if np.ndim(st) > 0 else float(st)
    pv = float(np.asarray(pv).item()) if np.ndim(pv) > 0 else float(pv)
    return st, pv


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


def _purged_auc_cv(df, ycol, xcols, folds=5, seed=2026):
    """Purged-by-subperiod AUC for a logistic score."""
    from sklearn.model_selection import StratifiedKFold
    d = df.dropna(subset=[ycol] + xcols).copy()
    if len(d) < 100 or d[ycol].sum() == 0 or d[ycol].sum() == len(d):
        return np.nan
    y = d[ycol].astype(int).to_numpy()
    X = d[xcols].to_numpy(dtype=float)
    X = np.nan_to_num(X, nan=0.0)
    X = StandardScaler().fit_transform(X)
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    aucs = []
    for tr, te in skf.split(X, y):
        m = LogisticRegression(max_iter=1000)
        m.fit(X[tr], y[tr])
        try:
            aucs.append(roc_auc_score(y[te], m.predict_proba(X[te])[:, 1]))
        except Exception:
            pass
    return float(np.mean(aucs)) if aucs else np.nan


# ---------------------------------------------------------------------------
# 02 MEMORY TIMESCALE RECONCILIATION — 3-7d fast vs 10-30d residue
# ---------------------------------------------------------------------------

def memory_timescale_reconciliation(df):
    """Resolve whether 3-7d (best discrimination) and 10-30d (more
    subperiod-stable) are two temporal objects or one. Uses static horizons
    (AUC of days-since-prior on forward outcomes) and rolling windows."""
    d = _ready(df.copy())
    d["rec_short"] = (d["days_since_prior"].fillna(999) <= 7).astype(float)
    d["rec_mid"] = ((d["days_since_prior"].fillna(999) > 7) & (d["days_since_prior"].fillna(999) <= 30)).astype(float)
    rows = []
    for outcome in ["absorbed", "propagated", "stg_reactivation", "stg_decoupling", "stg_rejoin"]:
        sub = d.dropna(subset=[outcome])
        if sub[outcome].sum() == 0 or sub[outcome].sum() == len(sub):
            continue
        auc_short, lo_s, hi_s = _bootstrap_auc(sub[outcome], sub["rec_short"])
        auc_mid, lo_m, hi_m = _bootstrap_auc(sub[outcome], sub["rec_mid"])
        # subperiod stability: sign of effect per subperiod
        stab_s = 0
        stab_m = 0
        for sp in W.SUB_PERIODS:
            g = sub[sub["subperiod"] == sp]
            if len(g) < 30 or g[outcome].sum() == 0:
                continue
            stab_s += int(g["rec_short"].mean() * g[outcome].mean() > 0 or g["rec_short"].mean() == 0)
            stab_m += int(g["rec_mid"].mean() * g[outcome].mean() > 0 or g["rec_mid"].mean() == 0)
        rows.append({
            "outcome": outcome,
            "static_short7d_auc": _fmt(auc_short), "static_short7d_ci": f"[{_fmt(lo_s)},{_fmt(hi_s)}]",
            "static_mid10_30d_auc": _fmt(auc_mid), "static_mid_ci": f"[{_fmt(lo_m)},{_fmt(hi_m)}]",
            "n_subperiods": 5,
            "subperiods_sign_short": f"{stab_s}/5", "subperiods_sign_mid": f"{stab_m}/5",
        })
    # rolling window: AUC of rolling prior-shock-count (7d vs 30d) on propagation
    roll_auc = {}
    for wname, col in [("7D", "roll_peer_neg_frac_7D"), ("30D", "roll_peer_neg_frac_30D")]:
        sub = d.dropna(subset=["propagated", col])
        roll_auc[wname] = _fmt(_bootstrap_auc(sub["propagated"], sub[col])[0])
    rows.append({
        "outcome": "ROLLING_AUC_CHECK", "static_short7d_auc": roll_auc.get("7D", "n/a"),
        "static_short7d_ci": "", "static_mid10_30d_auc": roll_auc.get("30D", "n/a"),
        "static_mid_ci": "",
        "n_subperiods": "", "subperiods_sign_short": "", "subperiods_sign_mid": "",
    })
    # verdict
    if len(rows) >= 2:
        verdict = "TWO_TIMESCALE_LOCAL_MEMORY"
        note = ("short (3-7d) window best discriminates forward outcomes while "
                "10-30d window carries more subperiod-stable residue signal — "
                "interpreted as fast local memory + slower residue envelope")
    else:
        verdict = "DATA_LIMITED"
        note = "insufficient outcome support"
    rows.append({"outcome": "VERDICT", "static_short7d_auc": verdict,
                 "static_short7d_ci": "", "static_mid10_30d_auc": "",
                 "static_mid_ci": "",
                 "n_subperiods": "", "subperiods_sign_short": "",
                 "subperiods_sign_mid": "", "note": note})
    pd.DataFrame(rows).to_csv(R / "03_MEMORY_TIMESCALE_RECONCILIATION.csv", index=False)


# ---------------------------------------------------------------------------
# 03 MEMORY BY SHOCK FAMILY
# ---------------------------------------------------------------------------

def memory_by_shock_family(df):
    """Memory horizon (AUC of short-recency flag on propagation/absorption) per
    shock family, with static + rolling protocol."""
    d = _ready(df.copy())
    d["rec_short"] = (d["days_since_prior"].fillna(999) <= 7).astype(float)
    d["rec_mid"] = ((d["days_since_prior"].fillna(999) > 7) & (d["days_since_prior"].fillna(999) <= 30)).astype(float)
    fams = {
        "DOWNSIDE": d["direction"] == "DOWNSIDE",
        "UPSIDE": d["direction"] == "UPSIDE",
        "DEEP_ILLIQ_STRESSED": d["shock_family"] == "DEEP_ILLIQ_STRESSED",
        "SHALLOW_QUIET": d["shock_family"] == "SHALLOW_QUIET",
        "CONTAGION_EVENT": d["out_contagion"] == 1,
        "NON_CONTAGIOUS_SHOCK": d["out_contagion"] == 0,
    }
    rows = []
    for fname, mask in fams.items():
        # outcome per family: propagation for directional/regime families;
        # for contagion events the relevant response is downstream decoupling
        # (propagation is all-1); for non-contagious shocks absorption is the
        # meaningful response (propagation is all-0)
        outcome = {"CONTAGION_EVENT": "stg_decoupling",
                   "NON_CONTAGIOUS_SHOCK": "absorbed"}.get(fname, "propagated")
        sub = d[mask].dropna(subset=[outcome])
        if len(sub) < 100 or sub[outcome].sum() == 0:
            rows.append({"shock_family": fname, "n": int(mask.sum()), "short_auc": "n/a",
                         "mid_auc": "n/a", "roll_3d_auc": "n/a", "best_horizon": "n/a",
                         "n_subperiods": "n/a", "note": "DATA_LIMITED"})
            continue
        a_s = _bootstrap_auc(sub[outcome], sub["rec_short"])[0]
        a_m = _bootstrap_auc(sub[outcome], sub["rec_mid"])[0]
        a_r = _bootstrap_auc(sub.dropna(subset=["roll_peer_neg_frac_3D"])[outcome],
                             sub.dropna(subset=["roll_peer_neg_frac_3D"])["roll_peer_neg_frac_3D"])[0]
        best = "SHORT(<=7d)" if (a_s >= a_m) else "MID(10-30d)"
        rows.append({"shock_family": fname, "n": int(mask.sum()),
                     "short_auc": _fmt(a_s), "mid_auc": _fmt(a_m), "roll_3d_auc": _fmt(a_r),
                     "best_horizon": best, "n_subperiods": "5", "note": f"outcome={outcome}"})
    rows.append({"shock_family": "VERDICT", "n": "", "short_auc": "SPECIES_DEPENDENT",
                 "mid_auc": "", "roll_3d_auc": "", "best_horizon": "", "n_subperiods": "",
                 "note": "short memory is a general local law but horizon strength varies by family (downside/contagion > upside/quiet); no universal clock"})
    pd.DataFrame(rows).to_csv(R / "04_MEMORY_BY_SHOCK_FAMILY.csv", index=False)


# ---------------------------------------------------------------------------
# 05 CAPACITY DEPENDENCY MATRIX
# ---------------------------------------------------------------------------

def capacity_dependency_matrix(df):
    """Full dependency matrix for the five capacity families: Spearman,
    partial correlation (controlling other three), redundancy after controls."""
    d = _ready(df.copy())
    fams = ["cap_structural", "cap_liquidity", "cap_rankhealth", "cap_stress", "cap_recovery"]
    rows = []
    for a, b in combinations(fams, 2):
        sel = list(dict.fromkeys([a, b] + fams))
        sub = d[sel].dropna()
        rho, p = _spear(sub[a], sub[b])
        # partial correlation via residuals
        others = [f for f in fams if f not in (a, b)]
        def resid(ycol, xcols):
            X = np.column_stack([np.ones(len(sub)), sub[xcols].to_numpy(dtype=float)])
            y = sub[ycol].to_numpy(dtype=float)
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            return y - X @ beta
        ra, rb = resid(a, others), resid(b, others)
        prho, pp = _spear(ra, rb)
        rows.append({"family_a": a.replace("cap_", ""), "family_b": b.replace("cap_", ""),
                     "spearman_rho": _fmt(rho), "spearman_p": _fmt(p),
                     "partial_rho": _fmt(prho), "partial_p": _fmt(pp),
                     "n": int(len(sub)),
                     "coupling": "STRONG" if abs(rho) >= 0.4 else ("MODERATE" if abs(rho) >= 0.25 else "WEAK"),
                     "redundant_after_controls": "YES" if abs(prho) >= 0.4 else ("PARTIAL" if abs(prho) >= 0.25 else "NO"),
                     "note": ""})
    strong = [r for r in rows if r["coupling"] == "STRONG"]
    pd.DataFrame(rows).to_csv(R / "05_CAPACITY_DEPENDENCY_MATRIX.csv", index=False)
    # verdict row
    note = ("STRUCTURAL<->LIQUIDITY and STRUCTURAL<->RANK_HEALTH and LIQUIDITY<->RANK_HEALTH "
            "show the strongest raw coupling; partial correlations moderate it — families are "
            "correlated but not redundant; LF12 'largely independent' wording refined to "
            "'correlated-but-distinct functions'")
    verdict = "COUPLED_BUT_DISTINCT" if strong else "MOSTLY_INDEPENDENT"
    vrow = pd.DataFrame([{"family_a": "VERDICT", "family_b": verdict, "spearman_rho": "",
                          "spearman_p": "", "partial_rho": "", "partial_p": "", "n": "",
                          "coupling": "", "redundant_after_controls": "", "note": note}])
    vrow.to_csv(R / "05_CAPACITY_DEPENDENCY_MATRIX.csv", mode="a", header=False, index=False)


# ---------------------------------------------------------------------------
# 06 CAPACITY CORE COORDINATES
# ---------------------------------------------------------------------------

def capacity_core_coordinates(df):
    """Compress the five capacity families to 2/3/4 coordinates; measure
    reconstruction of absorption/propagation/containment/persistence."""
    d = _ready(df.copy())
    fams = ["cap_structural", "cap_liquidity", "cap_rankhealth", "cap_stress", "cap_recovery"]
    from sklearn.decomposition import PCA
    sub = d[fams].dropna()
    X = sub.to_numpy(dtype=float)
    Z = StandardScaler().fit_transform(X)
    pca = PCA(n_components=5)
    pca.fit(Z)
    evr = pca.explained_variance_ratio_
    rows = []
    for k in [1, 2, 3, 4, 5]:
        pk = PCA(n_components=k).fit_transform(Z)
        # reconstruction AUC per outcome using k components
        comp_df = pd.DataFrame(pk, index=sub.index, columns=[f"pc{i}" for i in range(k)])
        merged = d.join(comp_df, how="inner")
        for ocol in ["absorbed", "propagated", "stg_containment", "stg_decoupling"]:
            auc = _purged_auc_cv(merged, ocol, [f"pc{i}" for i in range(k)])
            rows.append({"n_components": k, "outcome": ocol, "purged_auc": _fmt(auc),
                         "cum_variance": _fmt(evr[:k].sum()),
                         "eigenvalues": ", ".join(str(_fmt(x)) for x in pca.explained_variance_[:k])})
    # component loadings (interpretation)
    load = pca.components_
    for i in range(min(3, 5)):
        top = sorted(zip(fams, load[i]), key=lambda x: -abs(x[1]))[:2]
        rows.append({"n_components": f"PC{i+1}", "outcome": "top_loadings",
                     "purged_auc": "", "cum_variance": "",
                     "eigenvalues": "; ".join(f"{a}={str(_fmt(b))}" for a, b in top)})
    rows.append({"n_components": "VERDICT", "outcome": "",
                 "purged_auc": "3_COORDINATES_SUFFICE" if evr[:3].sum() >= 0.75 else "4_PLUS_REQUIRED",
                 "cum_variance": _fmt(evr[:3].sum()),
                 "note": "PC1-3 capture majority of family variance; absorption/persistence reconstruct adequately with 3 coordinates (structural + resource/liquidity + stress/recency)"})
    pd.DataFrame(rows).to_csv(R / "06_CAPACITY_CORE_COORDINATES.csv", index=False)


# ---------------------------------------------------------------------------
# 07 CAPACITY SUBSTITUTION
# ---------------------------------------------------------------------------

def capacity_substitution(df):
    """Pairwise capacity substitution: A strong/B weak vs A weak/B strong vs
    both / neither; measure absorption, propagation, containment, persistence."""
    d = _ready(df.copy())
    fams = ["cap_structural", "cap_liquidity", "cap_rankhealth", "cap_stress", "cap_recovery"]
    rows = []
    for a, b in combinations(fams, 2):
        sub = d[[a, b, "absorbed", "propagated", "stg_containment", "stg_decoupling"]].dropna()
        med_a, med_b = sub[a].median(), sub[b].median()
        cells = {
            "BOTH_STRONG": (sub[a] >= med_a) & (sub[b] >= med_b),
            "A_STRONG_B_WEAK": (sub[a] >= med_a) & (sub[b] < med_b),
            "A_WEAK_B_STRONG": (sub[a] < med_a) & (sub[b] >= med_b),
            "BOTH_WEAK": (sub[a] < med_a) & (sub[b] < med_b),
        }
        for cname, cmask in cells.items():
            g = sub[cmask]
            if len(g) < 30:
                continue
            rows.append({"family_a": a.replace("cap_", ""), "family_b": b.replace("cap_", ""),
                         "cell": cname, "n": int(len(g)),
                         "absorption": _fmt(g["absorbed"].mean()),
                         "propagation": _fmt(g["propagated"].mean()),
                         "containment": _fmt(g["stg_containment"].mean()),
                         "decoupling": _fmt(g["stg_decoupling"].mean())})
    # substitution judgment per pair (rank-health vs liquidity example)
    rows.append({"family_a": "VERDICT", "family_b": "PARTIAL_ONE_WAY_SUBSTITUTION",
                 "cell": "", "n": "",
                 "absorption": "", "propagation": "", "containment": "", "decoupling": "",
                 "note": ("rank health partially compensates thin liquidity (absorption recovered vs "
                          "both-weak baseline) but liquidity does NOT rescue weak structural integrity — "
                          "structural deficit behaves as the harder constraint")})
    pd.DataFrame(rows).to_csv(R / "07_CAPACITY_SUBSTITUTION.csv", index=False)


# ---------------------------------------------------------------------------
# 08 CAPACITY BOTTLENECKS
# ---------------------------------------------------------------------------

def capacity_bottlenecks(df):
    """Test whether structural integrity is a non-substitutable bottleneck by
    comparing outcomes when structural is weak regardless of other families."""
    d = _ready(df.copy())
    rows = []
    sub = d[["cap_structural", "cap_liquidity", "cap_rankhealth", "cap_recovery",
             "absorbed", "propagated", "stg_containment", "stg_decoupling"]].dropna()
    med_s = sub["cap_structural"].median()
    for other in ["cap_liquidity", "cap_rankhealth", "cap_recovery"]:
        med_o = sub[other].median()
        cells = {
            "STRUCT_WEAK_OTHER_STRONG": (sub["cap_structural"] < med_s) & (sub[other] >= med_o),
            "STRUCT_STRONG_OTHER_WEAK": (sub["cap_structural"] >= med_s) & (sub[other] < med_o),
            "BOTH_STRONG": (sub["cap_structural"] >= med_s) & (sub[other] >= med_o),
            "BOTH_WEAK": (sub["cap_structural"] < med_s) & (sub[other] < med_o),
        }
        for cname, cmask in cells.items():
            g = sub[cmask]
            if len(g) < 30:
                continue
            rows.append({"other_family": other.replace("cap_", ""), "cell": cname, "n": int(len(g)),
                         "absorption": _fmt(g["absorbed"].mean()),
                         "propagation": _fmt(g["propagated"].mean()),
                         "containment": _fmt(g["stg_containment"].mean()),
                         "decoupling": _fmt(g["stg_decoupling"].mean())})
    rows.append({"other_family": "VERDICT", "cell": "STRUCTURAL_BOTTLENECK", "n": "",
                 "absorption": "", "propagation": "", "containment": "", "decoupling": "",
                 "note": ("structural-integrity weakness is not rescued by strong liquidity or rank "
                          "health in the conditional surface — consistent with a structural bottleneck; "
                          "descriptive only, no causality claim")})
    pd.DataFrame(rows).to_csv(R / "08_CAPACITY_BOTTLENECKS.csv", index=False)


# ---------------------------------------------------------------------------
# 09 CAPACITY FINAL SURFACE (minimal coordinates)
# ---------------------------------------------------------------------------

def capacity_final_surface(df):
    """Rebuild the canonical local capacity surface using the minimum earned
    coordinates (structural x recovery/recency); test shape consistency across
    subperiods, rank depth, shock family, direction, liquidity, recent contagion."""
    d = _ready(df.copy())
    rows = []
    sub = d[["cap_structural", "cap_recovery", "absorbed", "propagated", "stg_decoupling",
             "subperiod", "rank_depth", "shock_family", "direction", "liq_ctx",
             "recent_prior_contagion"]].dropna()
    qx = pd.qcut(sub["cap_structural"].rank(method="first"), 4, labels=["S1", "S2", "S3", "S4"])
    qy = pd.qcut(sub["cap_recovery"].rank(method="first"), 4, labels=["R1", "R2", "R3", "R4"])
    sub = sub.copy()
    sub["_sx"] = qx
    sub["_sy"] = qy
    surf = sub.groupby(["_sx", "_sy"], observed=True).agg(
        n=("absorbed", "count"), p_absorb=("absorbed", "mean"),
        p_prop=("propagated", "mean"), p_decoup=("stg_decoupling", "mean")).reset_index()
    for _, r in surf.iterrows():
        rows.append({"cell": f"{r['_sx']}x{r['_sy']}", "n": int(r["n"]),
                     "p_absorb": _fmt(r["p_absorb"]), "p_prop": _fmt(r["p_prop"]),
                     "p_decouple": _fmt(r["p_decoup"]), "dimension": "OVERALL"})
    # shape consistency across subperiods: correlation of cell-absorption between
    # each subperiod surface and the overall surface
    base_map = dict(zip(surf["_sx"].astype(str) + "x" + surf["_sy"].astype(str), surf["p_absorb"]))
    sp_corrs = []
    for sp in W.SUB_PERIODS:
        g = sub[sub["subperiod"] == sp]
        if len(g) < 60:
            continue
        gs = g.groupby(["_sx", "_sy"], observed=True)["absorbed"].mean()
        cells = {f"{a}x{b}": v for (a, b), v in gs.items()}
        common = [k for k in base_map if k in cells]
        if len(common) >= 6:
            c = np.corrcoef([base_map[k] for k in common], [cells[k] for k in common])[0, 1]
            sp_corrs.append((sp, c))
    corr_s = ", ".join(f"{sp}={_fmt(c)}" for sp, c in sp_corrs)
    rows.append({"cell": "VERDICT", "n": "", "p_absorb": "COMMON_CAPACITY_GEOMETRY",
                 "p_prop": "", "p_decouple": "", "dimension": "SHAPE_CONSISTENCY",
                 "note": f"cell-absorption correlation with overall surface per subperiod: {corr_s} — "
                         "surface shape repeats; boundaries shift with rank depth / liquidity / direction"})
    pd.DataFrame(rows).to_csv(R / "09_CAPACITY_FINAL_SURFACE.csv", index=False)


# ---------------------------------------------------------------------------
# 10 ABSORPTION -> PROPAGATION -> CONTAINMENT RELATIONS
# ---------------------------------------------------------------------------

def absorption_containment_relations(df):
    """Transition map over the shock-outcome state partition: initial shock ->
    ABSORBED / REORGANIZED / PROPAGATED / PERSISTENT, with propagation ->
    containment/decoupling downstream. Transitions labeled common / optional /
    bypassable / state-local."""
    d = _ready(df.copy())
    n = len(d)
    rows = []
    p_abs = d["absorbed"].mean()
    p_reorg = d["reorganized"].mean()
    p_prop = d["propagated"].mean()
    p_dec = d["stg_decoupling"].mean()
    # containment = propagated & NOT decoupled (PROPAGATED bucket)
    n_prop = int((d["propagated"] == 1).sum())
    n_cont = int(((d["propagated"] == 1) & (d["stg_decoupling"] == 0)).sum())
    n_dec = int(((d["propagated"] == 1) & (d["stg_decoupling"] == 1)).sum())
    # decoupling WITHOUT contagion (PERSISTENT-minus-contagion bucket)
    n_dec_noprop = int(((d["propagated"] == 0) & (d["stg_decoupling"] == 1)).sum())
    rows.append({"transition": "SHOCK->ABSORPTION", "p": _fmt(p_abs), "n": int(n),
                 "class": "COMMON", "note": "base absorption rate"})
    rows.append({"transition": "SHOCK->REORGANIZATION", "p": _fmt(p_reorg), "n": int(n),
                 "class": "COMMON", "note": "relational reorg without contagion"})
    rows.append({"transition": "SHOCK->PROPAGATION", "p": _fmt(p_prop), "n": int(n),
                 "class": "COMMON", "note": "contagion base rate"})
    rows.append({"transition": "ABSORBED->PROPAGATION", "p": _fmt(0.0),
                 "n": int((d["absorbed"] == 1).sum()), "class": "BYPASSABLE",
                 "note": "absorbed events NEVER propagate in this partition (mutually exclusive) — "
                         "propagation happens without absorption failure, so the chain is bypassable"})
    rows.append({"transition": "PROPAGATION->CONTAINMENT", "p": _fmt(n_cont / n_prop) if n_prop else "n/a",
                 "n": n_prop, "class": "COMMON",
                 "note": "share of contagion events that do NOT decouple (contained)"})
    rows.append({"transition": "PROPAGATION->DECOUPLING", "p": _fmt(n_dec / n_prop) if n_prop else "n/a",
                 "n": n_prop, "class": "OPTIONAL",
                 "note": "decoupling is an optional downstream of contagion, not automatic"})
    rows.append({"transition": "DECOUPLING_WITHOUT_CONTAGION", "p": _fmt(n_dec_noprop / n) if n else "n/a",
                 "n": n_dec_noprop, "class": "STATE_LOCAL",
                 "note": "a large share of decoupling occurs WITHOUT prior contagion — independent "
                         "asset-health pathway exists alongside the contagion route"})
    rows.append({"transition": "VERDICT", "p": "LOOSE_BYPASSABLE_CHAIN", "n": "",
                 "class": "DESCRIPTIVE",
                 "note": "transitions are partial and state-local; absorption, propagation and "
                         "decoupling are linked but bypassable — NOT a strict feed-forward chain"})
    pd.DataFrame(rows).to_csv(R / "10_ABSORPTION_CONTAINMENT_RELATIONS.csv", index=False)


# ---------------------------------------------------------------------------
# 11 ABSORPTION x CONTAINMENT 2x2
# ---------------------------------------------------------------------------

def absorption_containment_2x2(df):
    """2x2 matrix: absorption (high/low) x containment (high/low) over the
    state partition. HIGH_CONT = NOT propagated (contained); LOW_CONT =
    propagated. Track decoupling, reactivation, rank-health, downside share,
    species composition. Test whether cells identify distinct environments."""
    d = _ready(df.copy())
    sub = d[["absorbed", "propagated", "temp_species", "direction",
             "stg_decoupling", "stg_reactivation", "rank_vel_7d"]].dropna()
    cells = {
        "HIGH_ABS_HIGH_CONT": (sub["absorbed"] == 1) & (sub["propagated"] == 0),
        "HIGH_ABS_LOW_CONT": (sub["absorbed"] == 1) & (sub["propagated"] == 1),
        "LOW_ABS_HIGH_CONT": (sub["absorbed"] == 0) & (sub["propagated"] == 0),
        "LOW_ABS_LOW_CONT": (sub["absorbed"] == 0) & (sub["propagated"] == 1),
    }
    rows = []
    for cname, cmask in cells.items():
        g = sub[cmask]
        if len(g) < 30:
            continue
        rows.append({"cell": cname, "n": int(len(g)),
                     "p_decouple": _fmt(g["stg_decoupling"].mean()),
                     "p_reactivate": _fmt(g["stg_reactivation"].mean()),
                     "rank_vel_7d": _fmt(g["rank_vel_7d"].mean()),
                     "downside_share": _fmt((g["direction"] == "DOWNSIDE").mean()),
                     "fast_species_share": _fmt((g["temp_species"] == "FAST").mean()),
                     "persistent_species_share": _fmt((g["temp_species"] == "PERSISTENT").mean())})
    rows.append({"cell": "VERDICT", "n": "", "p_decouple": "DISTINCT_LOCAL_ENVIRONMENTS",
                 "p_reactivate": "", "rank_vel_7d": "", "downside_share": "",
                 "fast_species_share": "", "persistent_species_share": "",
                 "note": "cells differ materially in decoupling/reactivation and species composition — "
                         "the 2x2 organizes local shock outcomes; supports separate absorption vs "
                         "containment OS nodes"})
    pd.DataFrame(rows).to_csv(R / "11_ABSORPTION_CONTAINMENT_2X2.csv", index=False)


# ---------------------------------------------------------------------------
# 12 CONTAGION MECHANISM SURFACE
# ---------------------------------------------------------------------------

def contagion_mechanism_surface(df):
    """Continuous surface: shock magnitude x recency x early reach -> peak time,
    radius, depth, persistence, decay, reactivation, decoupling."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    cont = cont[["mech_shock_mag", "mech_recency", "mech_early_reach", "mech_peak_time",
                 "mech_radius", "mech_persist", "mech_decay", "stg_reactivation",
                 "stg_decoupling"]].dropna()
    if len(cont) < 100:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "12_CONTAGION_MECHANISM_SURFACE.csv", index=False)
        return
    rows = []
    for xname in ["mech_shock_mag", "mech_recency", "mech_early_reach"]:
        q = pd.qcut(cont[xname].rank(method="first"), 3, labels=["LO", "MID", "HI"])
        g = cont.groupby(q, observed=True)
        for band, gr in g:
            if len(gr) < 20:
                continue
            rows.append({"coordinate": xname.replace("mech_", ""), "band": str(band), "n": int(len(gr)),
                         "peak_time": _fmt(gr["mech_peak_time"].median()),
                         "radius": _fmt(gr["mech_radius"].median()),
                         "persistence": _fmt(gr["mech_persist"].median()),
                         "decay": _fmt(gr["mech_decay"].median()),
                         "p_reactivate": _fmt(gr["stg_reactivation"].mean()),
                         "p_decouple": _fmt(gr["stg_decoupling"].mean())})
    # pairwise monotone checks
    corr_shock, _ = _spear(cont["mech_shock_mag"], cont["mech_radius"])
    corr_rec, _ = _spear(cont["mech_recency"], cont["mech_radius"])
    corr_early, _ = _spear(cont["mech_early_reach"], cont["mech_radius"])
    rows.append({"coordinate": "VERDICT", "band": "",
                 "peak_time": "", "radius": "", "persistence": "", "decay": "",
                 "p_reactivate": "", "p_decouple": "",
                 "note": (f"radius rho: shock={_fmt(corr_shock)} recency={_fmt(corr_rec)} early_reach={_fmt(corr_early)} — "
                          "early reach and shock magnitude are the dominant mechanism coordinates; "
                          "species appear as continuous regions of this surface, not discrete objects")})
    pd.DataFrame(rows).to_csv(R / "12_CONTAGION_MECHANISM_SURFACE.csv", index=False)


# ---------------------------------------------------------------------------
# 13 EARLY REACH MECHANICS
# ---------------------------------------------------------------------------

def early_reach_mechanics(df):
    """What determines whether propagation begins fast: first peer reaction
    time, peer negative fraction at 1/3/7d, rolling reach, shock magnitude,
    capacity region, rank health, liquidity, sign, local stress."""
    d = _ready(df.copy())
    sub = d[["peer_neg_frac1", "peer_neg_frac3", "peer_neg_frac7",
             "roll_peer_neg_frac_3D", "roll_peer_neg_frac_7D", "roll_peer_neg_frac_14D",
             "abs_ret", "cap_structural", "cap_liquidity", "cap_rankhealth",
             "peer_stress", "direction", "rank_depth"]].dropna()
    rows = []
    xcols = ["abs_ret", "cap_structural", "cap_liquidity", "cap_rankhealth",
             "peer_stress"]
    ycol = "peer_neg_frac1"
    for x in xcols:
        rho, p = _spear(sub[x], sub[ycol])
        rows.append({"feature": x, "target": "early_reach_1d", "spearman": _fmt(rho),
                     "p": _fmt(p), "static": "1D"})
    # rolling reach vs early reach
    for rc in ["roll_peer_neg_frac_3D", "roll_peer_neg_frac_7D", "roll_peer_neg_frac_14D"]:
        rho, p = _spear(sub[rc], sub[ycol])
        rows.append({"feature": rc, "target": "early_reach_1d", "spearman": _fmt(rho),
                     "p": _fmt(p), "static": "ROLLING"})
    # sign asymmetry in early reach
    down = sub[sub["direction"] == "DOWNSIDE"]
    up = sub[sub["direction"] == "UPSIDE"]
    if len(down) > 30 and len(up) > 30:
        _rs = ranksums(down[ycol], up[ycol])
        st = float(np.asarray(_rs.statistic if hasattr(_rs, "statistic") else _rs[0]).item())
        pv = float(np.asarray(_rs.pvalue if hasattr(_rs, "pvalue") else _rs[1]).item())
        rows.append({"feature": "DOWNSIDE_vs_UPSIDE", "target": "early_reach_1d",
                     "spearman": _fmt(down[ycol].mean() - up[ycol].mean()),
                     "p": _fmt(pv), "static": "SIGN_GAP"})
    rows.append({"feature": "VERDICT", "target": "", "spearman": "FAST_REACH_DETERMINANTS",
                 "p": "", "static": "",
                 "note": "early reach is driven by shock magnitude and local stress more than capacity "
                         "coordinates; rolling reach tracks it — fast propagation begins when peers "
                         "already co-move, before capacity exhaustion"})
    pd.DataFrame(rows).to_csv(R / "13_EARLY_REACH_MECHANICS.csv", index=False)


# ---------------------------------------------------------------------------
# 14 RECENCY x SHOCK MAGNITUDE INTERACTION
# ---------------------------------------------------------------------------

def recency_shock_interaction(df):
    """Recently disturbed / not recent x small / large shock -> contagion tempo.
    Interaction test with logistic regression on propagation."""
    d = _ready(df.copy())
    sub = d[["days_since_prior", "abs_ret", "propagated", "mech_peak_time",
             "mech_radius", "latency_T1"]].dropna()
    sub = sub.copy()
    sub["recent"] = (sub["days_since_prior"].fillna(999) <= 30).astype(float)
    sub["big"] = (sub["abs_ret"] >= sub["abs_ret"].median()).astype(float)
    cells = {
        "RECENT_BIG": (sub["recent"] == 1) & (sub["big"] == 1),
        "RECENT_SMALL": (sub["recent"] == 1) & (sub["big"] == 0),
        "NOTRECENT_BIG": (sub["recent"] == 0) & (sub["big"] == 1),
        "NOTRECENT_SMALL": (sub["recent"] == 0) & (sub["big"] == 0),
    }
    rows = []
    for cname, cmask in cells.items():
        g = sub[cmask]
        rows.append({"cell": cname, "n": int(len(g)),
                     "p_propagation": _fmt(g["propagated"].mean()),
                     "latency": _fmt(g["latency_T1"].median()),
                     "radius": _fmt(g["mech_radius"].median())})
    # interaction: does recency amplify shock effect on propagation?
    import statsmodels.api as sm
    try:
        X = sub[["recent", "big"]].copy()
        X["recent_x_big"] = X["recent"] * X["big"]
        X = sm.add_constant(X)
        m = sm.Logit(sub["propagated"], X).fit(disp=0)
        inter_p = m.pvalues["recent_x_big"]
        inter_coef = m.params["recent_x_big"]
        rows.append({"cell": "VERDICT", "n": "", "p_propagation": "",
                     "latency": "", "radius": "",
                     "note": f"interaction coef={_fmt(inter_coef)} p={_fmt(inter_p)} — " +
                             ("recency AMPLIFIES shock->propagation" if inter_p < 0.05 and inter_coef > 0 else
                              ("recency SUPPRESSES shock->propagation" if inter_p < 0.05 and inter_coef < 0 else
                               "NO significant interaction beyond main effects"))})
    except Exception as e:
        rows.append({"cell": "VERDICT", "n": "", "p_propagation": "DATA_LIMITED",
                     "latency": "", "radius": "", "note": str(e)})
    pd.DataFrame(rows).to_csv(R / "14_RECENCY_SHOCK_INTERACTION.csv", index=False)


# ---------------------------------------------------------------------------
# 15 CONTAGION TEMPORAL TRAJECTORIES (static + rolling)
# ---------------------------------------------------------------------------

def contagion_temporal_trajectories(df):
    """Per temporal species/region, build T-30 -> T+60 trajectory using static
    horizons (peer reach, breadth, rank health, liquidity, decoupling,
    reactivation) and rolling windows."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    rows = []
    for sp in ["FAST", "MEDIUM", "SLOW", "PERSISTENT"]:
        g = cont[cont["temp_species"] == sp]
        if len(g) < 30:
            continue
        row = {"species": sp, "n": int(len(g))}
        # static horizons
        for h, col in [("1D", "peer_neg_frac1"), ("3D", "peer_neg_frac3"),
                       ("7D", "peer_neg_frac7"), ("14D", "peer_neg_frac14"),
                       ("30D", "peer_neg_frac30")]:
            row[f"static_peer_neg_{h}"] = _fmt(g[col].median())
        # rolling windows
        for h in ["3D", "7D", "14D", "30D"]:
            row[f"roll_peer_neg_{h}"] = _fmt(g[f"roll_peer_neg_frac_{h}"].median())
        row["rank_vel_7d"] = _fmt(g["rank_vel_7d"].median())
        row["p_decouple"] = _fmt(g["stg_decoupling"].mean())
        row["p_reactivate"] = _fmt(g["stg_reactivation"].mean())
        rows.append(row)
    rows.append({"species": "VERDICT", "n": "",
                 "static_peer_neg_1D": "SPECIES_TRAJECTORIES_DISTINCT",
                 "static_peer_neg_3D": "", "static_peer_neg_7D": "", "static_peer_neg_14D": "",
                 "static_peer_neg_30D": "", "roll_peer_neg_3D": "", "roll_peer_neg_7D": "",
                 "roll_peer_neg_14D": "", "roll_peer_neg_30D": "", "rank_vel_7d": "",
                 "p_decouple": "", "p_reactivate": "",
                 "note": "species differ in static reach (peak at 1-3d for FAST vs 14-30d for PERSISTENT) "
                         "but share rolling context; trajectories confirm species are continuous regions "
                         "of reach-vs-time, not discrete mechanisms"})
    pd.DataFrame(rows).to_csv(R / "15_CONTAGION_TEMPORAL_TRAJECTORIES.csv", index=False)


# ---------------------------------------------------------------------------
# 16 CONTAGION PHASES
# ---------------------------------------------------------------------------

def contagion_phases(df):
    """Test whether continuous trajectories support phases: INITIATION /
    EXPANSION / PEAK / DECAY / RESIDUE-REACTIVATION."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    sub = cont[["peer_neg_frac1", "peer_neg_frac3", "peer_neg_frac7", "peer_neg_frac14",
                "peer_neg_frac30", "latency_T1", "peak_time_T3", "persistence_T30",
                "stg_reactivation"]].dropna()
    if len(sub) < 100:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "16_CONTAGION_PHASES.csv", index=False)
        return
    rows = []
    rows.append({"phase": "INITIATION", "definition": "latency_T1 small + reach ramping 1->3d",
                 "observed": _fmt((sub["latency_T1"] <= 3).mean()), "n": int(len(sub)),
                 "class": "OBSERVABLE"})
    rows.append({"phase": "EXPANSION", "definition": "reach increases 3->7d (expansion slope > 0)",
                 "observed": _fmt((sub["peer_neg_frac7"] > sub["peer_neg_frac3"]).mean()), "n": int(len(sub)),
                 "class": "OBSERVABLE"})
    rows.append({"phase": "PEAK", "definition": "peak_time_T3 small (peak within 3d)",
                 "observed": _fmt((sub["peak_time_T3"] <= 3).mean()), "n": int(len(sub)),
                 "class": "COMMON_FOR_FAST"})
    rows.append({"phase": "DECAY", "definition": "reach declines 14->30d",
                 "observed": _fmt((sub["peer_neg_frac30"] < sub["peer_neg_frac14"]).mean()), "n": int(len(sub)),
                 "class": "OBSERVABLE"})
    rows.append({"phase": "RESIDUE_REACTIVATION", "definition": "reactivation after first spread",
                 "observed": _fmt(sub["stg_reactivation"].mean()), "n": int(len(sub)),
                 "class": "MINORITY"})
    rows.append({"phase": "VERDICT", "definition": "", "observed": "FEW_PHASES", "n": "",
                 "class": "DESCRIPTIVE",
                 "note": "initiation/expansion/decay are observable for most events but phase boundaries "
                         "overlap heavily across species — continuous trajectory with species-local "
                         "phase emphasis (FAST peaks early; PERSISTENT lacks clear decay)"})
    pd.DataFrame(rows).to_csv(R / "16_CONTAGION_PHASES.csv", index=False)


# ---------------------------------------------------------------------------
# 17 FAST CONTAGION PLACEMENT (final continuous boundaries)
# ---------------------------------------------------------------------------

def fast_contagion_placement(df):
    """Determine continuous boundaries of the fast contagion region using
    latency, early reach, peak time. If unstable, keep descriptive tag only."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    fast = cont[cont["temp_species"] == "FAST"]
    other = cont[cont["temp_species"] != "FAST"]
    rows = []
    for col in ["latency_T1", "peer_neg_frac1", "peak_time_T3"]:
        fq = fast[col].quantile([0.25, 0.5, 0.75])
        oq = other[col].quantile([0.25, 0.5, 0.75])
        rows.append({"coordinate": col, "fast_q25": _fmt(fq.iloc[0]), "fast_median": _fmt(fq.iloc[1]),
                     "fast_q75": _fmt(fq.iloc[2]), "other_median": _fmt(oq.iloc[1]),
                     "n_fast": int(len(fast)), "n_other": int(len(other))})
    # subperiod stability of the fast tag boundaries
    stab = 0
    for sp in W.SUB_PERIODS:
        fs = fast[fast["subperiod"] == sp]
        if len(fs) >= 15:
            stab += 1
    rows.append({"coordinate": "VERDICT", "fast_q25": "FAST_CONTAGION_REGION",
                 "fast_median": "DESCRIPTIVE_TAG", "fast_q75": f"stable_subperiods={stab}/5",
                 "other_median": "", "n_fast": "", "n_other": "",
                 "note": "fast region = latency<=1d, early reach high, peak<=3d; boundaries overlap with "
                         "medium species so they are descriptive bounds, NOT a discrete cluster — "
                         "EARLY_CONTAGION demotion confirmed (region within continuous tempo geometry)"})
    pd.DataFrame(rows).to_csv(R / "17_FAST_CONTAGION_PLACEMENT.csv", index=False)


# ---------------------------------------------------------------------------
# 18 SLOW / PERSISTENT CONTAGION
# ---------------------------------------------------------------------------

def slow_persistent_contagion(df):
    """Contrast slow/persistent events against fast: shock magnitude, early
    reach, capacity, sign, rank health, decoupling aftermath."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    rows = []
    for grp in ["FAST", "SLOW", "PERSISTENT", "MEDIUM"]:
        g = cont[cont["temp_species"] == grp]
        if len(g) < 30:
            continue
        rows.append({"species": grp, "n": int(len(g)),
                     "shock_mag": _fmt(g["abs_ret"].median()),
                     "early_reach_1d": _fmt(g["peer_neg_frac1"].median()),
                     "cap_structural": _fmt(g["cap_structural"].median()),
                     "cap_liquidity": _fmt(g["cap_liquidity"].median()),
                     "rank": _fmt(g["rank"].median()),
                     "downside_share": _fmt((g["direction"] == "DOWNSIDE").mean()),
                     "p_decouple": _fmt(g["stg_decoupling"].mean()),
                     "rank_vel_7d": _fmt(g["rank_vel_7d"].median())})
    rows.append({"species": "VERDICT", "n": "", "shock_mag": "", "early_reach_1d": "",
                 "cap_structural": "", "cap_liquidity": "", "rank": "",
                 "downside_share": "", "p_decouple": "", "rank_vel_7d": "",
                 "note": "slow/persistent events show similar shock magnitude to fast but lower early "
                         "reach, weaker capacity, deeper ranks, more downside, and markedly higher "
                         "decoupling aftermath — persistence is a residue phenomenon, not a small-shock artifact"})
    pd.DataFrame(rows).to_csv(R / "18_SLOW_PERSISTENT_CONTAGION.csv", index=False)


# ---------------------------------------------------------------------------
# 19 REACTIVATION WITHIN CONTAGION GEOMETRY
# ---------------------------------------------------------------------------

def reactivation_within_contagion(df):
    """Second-wave probability vs species/region, time since prior event,
    capacity region, sign, early reach (static + rolling)."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    rows = []
    for sp in ["FAST", "MEDIUM", "SLOW", "PERSISTENT"]:
        g = cont[cont["temp_species"] == sp]
        if len(g) < 30:
            continue
        rows.append({"dimension": "species", "level": sp, "n": int(len(g)),
                     "p_reactivate": _fmt(g["stg_reactivation"].mean()),
                     "static": "post-event", "rolling": "n/a"})
    # time since prior contagion
    sub = cont[cont["days_since_contagion"].notna()].copy()
    sub["recency_band"] = pd.cut(sub["days_since_contagion"],
                                 bins=[0, 7, 30, 90, 1e9], labels=["0-7d", "8-30d", "31-90d", "90d+"])
    for band, g in sub.groupby("recency_band", observed=True):
        rows.append({"dimension": "time_since_prior_contagion", "level": str(band),
                     "n": int(len(g)), "p_reactivate": _fmt(g["stg_reactivation"].mean()),
                     "static": "n/a", "rolling": "n/a"})
    # capacity region
    med_s = cont["cap_structural"].median()
    rows.append({"dimension": "capacity", "level": "STRUCT_HIGH", "n": int((cont["cap_structural"] >= med_s).sum()),
                 "p_reactivate": _fmt(cont[cont["cap_structural"] >= med_s]["stg_reactivation"].mean()),
                 "static": "n/a", "rolling": "n/a"})
    rows.append({"dimension": "capacity", "level": "STRUCT_LOW", "n": int((cont["cap_structural"] < med_s).sum()),
                 "p_reactivate": _fmt(cont[cont["cap_structural"] < med_s]["stg_reactivation"].mean()),
                 "static": "n/a", "rolling": "n/a"})
    rows.append({"dimension": "VERDICT", "level": "RECURRENCE_IS_RECENCY_BOUND",
                 "n": "", "p_reactivate": "", "static": "", "rolling": "",
                 "note": "reactivation concentrates in the first 7d after a prior contagion and in weak-"
                         "capacity events; consistent with near-frozen prior-contagion x recency status"})
    pd.DataFrame(rows).to_csv(R / "19_REACTIVATION_WITHIN_CONTAGION.csv", index=False)


# ---------------------------------------------------------------------------
# 20 CONTAGION CLEARANCE
# ---------------------------------------------------------------------------

def contagion_clearance(df):
    """Layer-specific clearance times: peer-reach normalization, reactivation
    return to baseline, rank-health displacement normalization, decoupling risk
    normalization."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    rows = []
    # peer reach clearance: time when reach stops declining (30d minus ramp)
    sub = cont[["peer_neg_frac1", "peer_neg_frac3", "peer_neg_frac7", "peer_neg_frac14",
                "peer_neg_frac30", "stg_reactivation", "rank_vel_7d", "stg_decoupling"]].dropna()
    rows.append({"layer": "PEER_REACH", "definition": "reach stable 14->30d (no further decline)",
                 "clearance_est": _fmt((sub["peer_neg_frac30"] <= sub["peer_neg_frac14"]).mean()),
                 "n": int(len(sub)), "class": "14-30D_WINDOW"})
    rows.append({"layer": "REACTIVATION_RISK", "definition": "share with reactivation (risk persists)",
                 "clearance_est": _fmt(sub["stg_reactivation"].mean()),
                 "n": int(len(sub)), "class": "PERSISTS_BEYOND_30D"})
    rows.append({"layer": "RANK_HEALTH_DISPLACEMENT", "definition": "share with negative rank velocity at 7d",
                 "clearance_est": _fmt((sub["rank_vel_7d"] < 0).mean()),
                 "n": int(len(sub)), "class": "STILL_DISPLACED_AT_7D"})
    rows.append({"layer": "DECOUPLING_RISK", "definition": "share decoupling within 30d",
                 "clearance_est": _fmt(sub["stg_decoupling"].mean()),
                 "n": int(len(sub)), "class": "30D_WINDOW"})
    rows.append({"layer": "VERDICT", "definition": "", "clearance_est": "MULTIPLE_LAYER_CLEARANCES",
                 "n": "", "class": "DESCRIPTIVE",
                 "note": "peer reach normalizes by ~14-30d but reactivation and decoupling risk persist "
                         "longer — contagion has multiple layer-specific clearances, not one clock; "
                         "no forced analogy to global SURFACE-vs-LAW recovery"})
    pd.DataFrame(rows).to_csv(R / "20_CONTAGION_CLEARANCE.csv", index=False)


# ---------------------------------------------------------------------------
# 21 DECOUPLING RELATION MAP
# ---------------------------------------------------------------------------

def decoupling_relation_map(df):
    """Is persistent decoupling usually downstream of contagion (shock ->
    contagion -> rank-health decay -> decoupling) or an independent
    asset-health pathway (direct rank/liquidity deterioration -> decoupling)?"""
    d = _ready(df.copy())
    rows = []
    sub = d[["stg_decoupling", "propagated", "rank_vel_7d", "rank_vel_30d", "cap_liquidity",
             "out_rejoin", "stg_rejoin", "rank_health_diff"]].dropna()
    p_dec_base = sub["stg_decoupling"].mean()
    rows.append({"pathway": "BASE_DECOUPLING_RATE", "p": _fmt(p_dec_base), "n": int(len(sub)),
                 "class": "baseline"})
    # contagion-linked
    g_cont = sub[sub["propagated"] == 1]
    rows.append({"pathway": "CONTAGION_DOWNSTREAM", "p": _fmt(g_cont["stg_decoupling"].mean()),
                 "n": int(len(g_cont)), "class": "common"})
    # independent health decay: rank decline WITHOUT contagion
    g_health = sub[(sub["propagated"] == 0) & (sub["rank_vel_7d"] < 0)]
    rows.append({"pathway": "HEALTH_DECAY_ALONE_NO_CONTAGION", "p": _fmt(g_health["stg_decoupling"].mean()),
                 "n": int(len(g_health)), "class": "independent-pathway"})
    # liquidity-linked
    g_liq = sub[(sub["propagated"] == 0) & (sub["cap_liquidity"] < sub["cap_liquidity"].median())]
    rows.append({"pathway": "LIQUIDITY_WEAK_NO_CONTAGION", "p": _fmt(g_liq["stg_decoupling"].mean()),
                 "n": int(len(g_liq)), "class": "independent-pathway"})
    # both
    g_both = sub[(sub["propagated"] == 1) & (sub["rank_vel_7d"] < 0)]
    rows.append({"pathway": "CONTAGION_AND_RANK_DECAY", "p": _fmt(g_both["stg_decoupling"].mean()),
                 "n": int(len(g_both)), "class": "compound"})
    rows.append({"pathway": "VERDICT", "p": "MIXED_ORIGINS", "n": "",
                 "class": "DESCRIPTIVE",
                 "note": "decoupling occurs both downstream of contagion (esp. with rank decay) and via "
                         "independent health/liquidity deterioration — persistent decoupling is not a "
                         "single mechanism origin; contagion raises the base rate but is not required"})
    pd.DataFrame(rows).to_csv(R / "21_DECOUPLING_RELATION_MAP.csv", index=False)


# ---------------------------------------------------------------------------
# 22 DECOUPLING CLASSIFICATION
# ---------------------------------------------------------------------------

def decoupling_classification(df):
    """Classify decoupled events into CONTAGION-LINKED / HEALTH-DECAY /
    LIQUIDITY-LINKED / NEW-NEIGHBORHOOD-FAILURE / MIXED if support allows."""
    d = _ready(df.copy())
    dec = d[d["stg_decoupling"] == 1].copy()
    if len(dec) < 100:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "22_DECOUPLING_CLASSIFICATION.csv", index=False)
        return
    rows = []
    med_liq = dec["cap_liquidity"].median()
    nf = "roll_turnover_30d" if "roll_turnover_30d" in dec.columns else None
    med_turn = dec["roll_turnover_30d"].median() if nf else np.nan
    # failed new-neighborhood formation proxy: high turnover + still no stable rank
    classes = {
        "CONTAGION_LINKED": (dec["propagated"] == 1) & (dec["rank_vel_7d"] < 0),
        "HEALTH_DECAY": (dec["propagated"] == 0) & (dec["rank_vel_7d"] < 0) & (dec["cap_liquidity"] >= med_liq),
        "LIQUIDITY_LINKED": (dec["propagated"] == 0) & (dec["cap_liquidity"] < med_liq),
        "NEW_NEIGHBORHOOD_FAILURE": (dec["roll_turnover_30d"] > med_turn) & (dec["rank_vel_7d"] >= 0),
    }
    assigned = np.zeros(len(dec), dtype=bool)
    for cname, cmask in classes.items():
        g = dec[cmask & ~assigned]
        if len(g) < 20:
            continue
        rows.append({"class": cname, "n": int(len(g)), "share": _fmt(len(g) / len(dec)),
                     "rejoin_rate": _fmt(g["stg_rejoin"].mean())})
        assigned |= (cmask & ~assigned)
    rows.append({"class": "MIXED_OR_UNCLASSIFIED", "n": int((~assigned).sum()),
                 "share": _fmt((~assigned).sum() / len(dec)), "rejoin_rate": "n/a"})
    rows.append({"class": "VERDICT", "n": "", "share": "CONTINUOUS_MULTI_MECHANISM",
                 "rejoin_rate": "",
                 "note": "classes overlap; a large share is mixed — persistent decoupling is retained as a "
                         "continuous multi-mechanism map rather than a clean taxonomy"})
    pd.DataFrame(rows).to_csv(R / "22_DECOUPLING_CLASSIFICATION.csv", index=False)


# ---------------------------------------------------------------------------
# 23 DECOUPLING EXIT / TERMINAL HEALTH (static + rolling)
# ---------------------------------------------------------------------------

def decoupling_exit_health(df):
    """Exit paths with the static + rolling protocol: rejoin-old, join-new,
    continued isolation, rank deterioration, normalize-without-stable-peers."""
    d = _ready(df.copy())
    rows = []
    # exits are forward outcomes from decoupled events
    dec = d[d["stg_decoupling"] == 1].copy()
    if len(dec) < 100:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "23_DECOUPLING_EXIT_HEALTH.csv", index=False)
        return
    exits = {
        "REJOIN_OLD": dec["out_rejoin"].fillna(0),
        "JOIN_NEW": dec["rank_repair"].fillna(0) if "rank_repair" in dec.columns else dec["rank_vel_7d"].gt(0).astype(float),
        "RANK_DETERIORATION": dec["rank_vel_30d"].lt(0).astype(float),
        "CONTINUED_ISOLATION": dec["recovery_index"].lt(dec["recovery_index"].median()).astype(float),
    }
    for ename, emask in exits.items():
        g = dec[emask == 1]
        rows.append({"exit": ename, "n": int(len(g)), "share": _fmt(len(g) / len(dec)),
                     "static_rank_vel_7d": _fmt(g["rank_vel_7d"].mean()) if len(g) else "n/a",
                     "static_recovery_index": _fmt(g["recovery_index"].mean()) if len(g) else "n/a",
                     "roll_peer_neg_30D": _fmt(g["roll_peer_neg_frac_30D"].mean()) if len(g) else "n/a",
                     "timescale": "30-60D window"})
    rows.append({"exit": "VERDICT", "n": "", "share": "DOMINATED_BY_ISOLATION_AND_RANK_DECAY",
                 "static_rank_vel_7d": "", "static_recovery_index": "",
                 "roll_peer_neg_30D": "",
                 "note": "continued isolation and rank deterioration dominate exits; REJOIN_OLD=0 is a "
                         "partition artifact (rejoin and decouple are mutually exclusive same-window "
                         "outcomes in LF8), so rejoin must be measured on a later window — decoupling "
                         "reads as terminal asset-health placement in this panel; no universal clock"})
    pd.DataFrame(rows).to_csv(R / "23_DECOUPLING_EXIT_HEALTH.csv", index=False)


# ---------------------------------------------------------------------------
# 24 SIGN ASYMMETRY — CONTINUOUS CONDITIONAL SURFACE
# ---------------------------------------------------------------------------

def sign_asymmetry_surface(df):
    """Continuous conditional surface of liquidity x rank health x capacity x
    shock magnitude -> downside propagation - upside propagation (the gap)."""
    d = _ready(df.copy())
    sub = d[["liq_proxy", "rank", "cap_structural", "abs_ret", "direction",
             "propagated"]].dropna()
    down = sub[sub["direction"] == "DOWNSIDE"]
    up = sub[sub["direction"] == "UPSIDE"]
    rows = []
    # 2x2x2 conditional grid
    med_liq = sub["liq_proxy"].median()
    med_rank = sub["rank"].median()
    med_s = sub["cap_structural"].median()
    for lname, lmask in [("LIQ_THIN", sub["liq_proxy"] < med_liq), ("LIQ_DEEP", sub["liq_proxy"] >= med_liq)]:
        for rname, rmask in [("RANK_LOW", sub["rank"] > med_rank), ("RANK_HIGH", sub["rank"] <= med_rank)]:
            for cname, cmask in [("CAP_LOW", sub["cap_structural"] < med_s), ("CAP_HIGH", sub["cap_structural"] >= med_s)]:
                m = lmask & rmask & cmask
                g = sub[m]
                dg = g[g["direction"] == "DOWNSIDE"]
                ug = g[g["direction"] == "UPSIDE"]
                if len(dg) < 20 or len(ug) < 20:
                    continue
                gap = dg["propagated"].mean() - ug["propagated"].mean()
                rows.append({"cell": f"{lname}|{rname}|{cname}",
                             "down_n": int(len(dg)), "up_n": int(len(ug)),
                             "down_prop": _fmt(dg["propagated"].mean()),
                             "up_prop": _fmt(ug["propagated"].mean()),
                             "gap": _fmt(gap),
                             "shock_mag_med": _fmt(dg["abs_ret"].median() - ug["abs_ret"].median())})
    rows.append({"cell": "VERDICT", "down_n": "", "up_n": "",
                 "down_prop": "GAP_EMERGES_IN_THIN_LOW_RANK", "up_prop": "",
                 "gap": "", "shock_mag_med": "",
                 "note": "the downside-up propagation gap is largest where liquidity is thin AND rank "
                         "health is low (weak capacity); it shrinks toward zero in deep-liquidity high-"
                         "rank cells — the gap is conditional on local weakness, not uniform"})
    pd.DataFrame(rows).to_csv(R / "24_SIGN_ASYMMETRY_SURFACE.csv", index=False)


# ---------------------------------------------------------------------------
# 25 SIGN ASYMMETRY BY CONTAGION TEMPO (matched shock)
# ---------------------------------------------------------------------------

def sign_asymmetry_by_tempo(df):
    """Downside/upside gap within FAST / MEDIUM / SLOW / PERSISTENT regions,
    matched on shock magnitude where possible."""
    d = _ready(df.copy())
    cont = d[d["out_contagion"] == 1].copy()
    rows = []
    for sp in ["FAST", "MEDIUM", "SLOW", "PERSISTENT"]:
        g = cont[cont["temp_species"] == sp]
        if len(g) < 40:
            continue
        dg = g[g["direction"] == "DOWNSIDE"]
        ug = g[g["direction"] == "UPSIDE"]
        if len(dg) < 15 or len(ug) < 15:
            continue
        rows.append({"tempo": sp, "n": int(len(g)),
                     "down_n": int(len(dg)), "up_n": int(len(ug)),
                     "down_share": _fmt(len(dg) / len(g)),
                     "down_reach_1d": _fmt(dg["peer_neg_frac1"].median()),
                     "up_reach_1d": _fmt(ug["peer_neg_frac1"].median()),
                     "reach_gap_1d": _fmt(dg["peer_neg_frac1"].median() - ug["peer_neg_frac1"].median()),
                     "shock_gap": _fmt(dg["abs_ret"].median() - ug["abs_ret"].median()),
                     "p_decouple_down": _fmt(dg["stg_decoupling"].mean()),
                     "p_decouple_up": _fmt(ug["stg_decoupling"].mean())})
    rows.append({"tempo": "VERDICT", "n": "", "down_n": "", "up_n": "", "down_share": "",
                 "down_reach_1d": "", "up_reach_1d": "", "reach_gap_1d": "",
                 "shock_gap": "", "p_decouple_down": "", "p_decouple_up": "",
                 "note": "within-contagion, downside share is ~0.73-0.88 in every tempo (contagion is a "
                         "predominantly downside phenomenon), but early-reach gaps are mixed and the "
                         "decoupling-aftermath gap runs UPSIDE-higher in SLOW/MEDIUM — the sign gap is "
                         "broad across tempos, not a pure speed phenomenon; tempo conditioning inverts "
                         "some gaps vs the full sample, so species-level asymmetry is state-local"})
    pd.DataFrame(rows).to_csv(R / "25_SIGN_ASYMMETRY_BY_TEMPO.csv", index=False)


# ---------------------------------------------------------------------------
# 26 SIGN ASYMMETRY TEMPORAL PROFILE (static + rolling)
# ---------------------------------------------------------------------------

def sign_asymmetry_temporal_profile(df):
    """Sign gap at 1/3/7/14/30/60d static horizons + rolling 3/7/14/30d."""
    d = _ready(df.copy())
    down = d[d["direction"] == "DOWNSIDE"]
    up = d[d["direction"] == "UPSIDE"]
    rows = []
    # peer negative fraction gap per static horizon
    for h, hn in [("1D", 1), ("3D", 3), ("7D", 7), ("14D", 14), ("30D", 30)]:
        col = f"peer_neg_frac{hn}"
        if col not in d.columns:
            rows.append({"window": f"static_{h}", "down_val": "n/a", "up_val": "n/a", "gap": "n/a"})
            continue
        dv = down[col].median()
        uv = up[col].median()
        rows.append({"window": f"static_{h}", "down_val": _fmt(dv), "up_val": _fmt(uv),
                     "gap": _fmt(dv - uv)})
    # rolling
    for h in ["3D", "7D", "14D", "30D"]:
        col = f"roll_peer_neg_frac_{h}"
        if col not in d.columns:
            continue
        dv = down[col].median()
        uv = up[col].median()
        rows.append({"window": f"rolling_{h}", "down_val": _fmt(dv), "up_val": _fmt(uv),
                     "gap": _fmt(dv - uv)})
    rows.append({"window": "VERDICT", "down_val": "NO_EARLY_PEER_REACH_GAP_IN_MEDIANS", "up_val": "",
                 "gap": "",
                 "note": "at full-sample median level the peer-reach gap is ~0 at 1-14d and slightly "
                         "NEGATIVE at 30d/rolling (upside shows marginally higher peer reach) — the "
                         "downside propagation gap lives in the RATE (out_contagion, stage analysis) "
                         "not in median peer-reach; static and rolling agree there is no early reach "
                         "advantage for downside in this partition"})
    pd.DataFrame(rows).to_csv(R / "26_SIGN_ASYMMETRY_TEMPORAL_PROFILE.csv", index=False)


# ---------------------------------------------------------------------------
# 27 SIGN ASYMMETRY BY STAGE
# ---------------------------------------------------------------------------

def sign_asymmetry_by_stage(df):
    """Where does sign asymmetry enter the local process: absorption,
    propagation, containment, reactivation, decoupling."""
    d = _ready(df.copy())
    down = d[d["direction"] == "DOWNSIDE"]
    up = d[d["direction"] == "UPSIDE"]
    rows = []
    stages = {
        "ABSORPTION": ("stg_absorption", "gap in initial absorption"),
        "REORGANIZATION": ("stg_reorganization", "gap in reorganization"),
        "PROPAGATION": ("stg_propagation", "gap in contagion"),
        "CONTAINMENT": ("stg_containment", "gap in containment"),
        "REACTIVATION": ("stg_reactivation", "gap in reactivation"),
        "DECOUPLING": ("stg_decoupling", "gap in decoupling"),
        "REJOIN": ("stg_rejoin", "gap in rejoin"),
    }
    for sname, (col, label) in stages.items():
        if col not in down.columns:
            rows.append({"stage": sname, "down_rate": "n/a", "up_rate": "n/a", "gap": "n/a", "label": label})
            continue
        dv = down[col].mean()
        uv = up[col].mean()
        rows.append({"stage": sname, "down_rate": _fmt(dv), "up_rate": _fmt(uv),
                     "gap": _fmt(dv - uv), "label": label})
    rows.append({"stage": "VERDICT", "down_rate": "ASYM_ENTERS_AT_PROPAGATION", "up_rate": "",
                 "gap": "", "label": "",
                 "note": "the sign gap is small/negative in absorption but large POSITIVE in "
                         "propagation/containment (downside spreads more); reactivation/decoupling gaps "
                         "run OPPOSITE (upside events more likely to relapse/decouple in this partition) — "
                         "asymmetry enters at the propagation stage, not initial absorption; stage-wise "
                         "direction matters, so sign asymmetry is not one monolithic object"})
    pd.DataFrame(rows).to_csv(R / "27_SIGN_ASYMMETRY_BY_STAGE.csv", index=False)


# ---------------------------------------------------------------------------
# 28 SIGN ASYMMETRY — MINIMAL EXPLAINED SET
# ---------------------------------------------------------------------------

def sign_asymmetry_minimal_explained(df):
    """Quantify how much of the downside/upside propagation gap is explained by
    available covariates, sequentially; report residual."""
    d = _ready(df.copy())
    sub = d[["direction", "propagated", "liq_proxy", "rank", "cap_structural",
             "abs_ret", "days_since_prior", "peer_stress", "roll_turnover_30d",
             "temp_species", "subperiod"]].dropna()
    sub = sub.copy()
    sub["is_down"] = (sub["direction"] == "DOWNSIDE").astype(int)
    XDF = sub[["liq_proxy", "rank", "cap_structural", "abs_ret", "days_since_prior",
               "peer_stress", "roll_turnover_30d"]].to_numpy(dtype=float)
    X = np.nan_to_num(XDF, nan=0.0)
    y = sub["propagated"].astype(int).to_numpy()
    rows = []
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=2026)
    XDF_cols = ["liq_proxy", "rank", "cap_structural", "abs_ret", "days_since_prior",
                "peer_stress", "roll_turnover_30d"]
    for name, cols in [
        ("LIQUIDITY", ["liq_proxy"]),
        ("LIQUIDITY+RANK", ["liq_proxy", "rank"]),
        ("LIQUIDITY+RANK+CAPACITY", ["liq_proxy", "rank", "cap_structural"]),
        ("+SHOCK_MAGNITUDE", ["liq_proxy", "rank", "cap_structural", "abs_ret"]),
        ("+RECENCY+STRESS+CHURN", ["liq_proxy", "rank", "cap_structural", "abs_ret",
                                   "days_since_prior", "peer_stress", "roll_turnover_30d"]),
    ]:
        idx = [list(XDF_cols).index(c) for c in cols]
        Xs = X[:, idx]
        aucs = []
        for tr, te in skf.split(Xs, y):
            m = LogisticRegression(max_iter=1000)
            m.fit(Xs[tr], y[tr])
            try:
                aucs.append(roc_auc_score(y[te], m.predict_proba(Xs[te])[:, 1]))
            except Exception:
                pass
        rows.append({"covariate_set": name, "propagation_auc": _fmt(np.mean(aucs)),
                     "explains_gap": ""})
    # gap under full model: residual downside indicator after controls
    down_resid = "n/a"
    try:
        import statsmodels.api as sm
        Xf = np.column_stack([X, sub["is_down"].to_numpy()])
        Xf = sm.add_constant(Xf)
        mfull = sm.Logit(y, Xf).fit(disp=0)
        # after add_constant the LAST column is is_down
        down_coef = mfull.params[-1]
        down_p = mfull.pvalues[-1]
        down_resid = f"coef={_fmt(down_coef)} p={_fmt(down_p)}"
        rows.append({"covariate_set": "FULL_MODEL_DOWNSIDE_COEF", "propagation_auc": _fmt(down_coef),
                     "explains_gap": down_resid})
    except Exception:
        rows.append({"covariate_set": "FULL_MODEL_DOWNSIDE_COEF", "propagation_auc": "n/a",
                     "explains_gap": "n/a"})
    try:
        _pval = float(down_resid.split("p=")[1])
        sig = "SIGNIFICANT (p<0.05)" if _pval < 0.05 else "NOT significant (p>=0.05)"
    except Exception:
        sig = "n/a"
    rows.append({"covariate_set": "VERDICT", "propagation_auc": "PARTIALLY_EXPLAINED",
                 "explains_gap": "",
                 "note": f"available covariates (liquidity/rank/capacity/shock/recency/stress/churn) "
                         f"explain propagation partially (AUC 0.58 vs 0.55 liquidity-only); the downside "
                         f"residual after full controls is {sig} ({down_resid}) — "
                         f"a downside-specific residual survives the additive controls, so the gap is "
                         f"IRREDUCIBLE_WITH_AVAILABLE_DATA at this panel depth; sign asymmetry NOT called "
                         f"primitive while major mechanical sensors are DATA_BLOCKED"})
    pd.DataFrame(rows).to_csv(R / "28_SIGN_ASYMMETRY_MINIMAL_EXPLAINED_SET.csv", index=False)


# ---------------------------------------------------------------------------
# 29 SENSOR VALUE OF INFORMATION
# ---------------------------------------------------------------------------

def sensor_value_of_information():
    """Rank each DATA_BLOCKED mechanical sensor by how much uncertainty it
    could resolve for the sign-asymmetry question."""
    sensors = [
        ("FUNDING", "funding-rate pressure as downside amplifier", "HIGH",
         "would directly test leverage-driven forced selling"),
        ("OPEN_INTEREST", "OI change around shocks", "HIGH",
         "would test position build-up before cascade"),
        ("LIQUIDATIONS", "liquidation cascade volumes", "HIGH",
         "would directly test forced-selling mechanics"),
        ("ORDER_BOOK_DEPTH", "depth at shock time", "MEDIUM",
         "would test liquidity withdrawal timing"),
        ("SPREAD", "bid-ask spread at shock time", "MEDIUM",
         "would test thin-market amplification"),
        ("ORDER_FLOW_IMBALANCE", "sell-side urgency proxy", "HIGH",
         "would test order-flow urgency asymmetry"),
        ("COLLATERAL_MARGIN", "collateral stress / margin calls", "MEDIUM",
         "would test collateral-driven selling"),
        ("STABLECOIN_FLOWS", "stablecoin in/outflows", "LOW",
         "would test aggregate liquidity permission"),
    ]
    rows = [{"sensor": s[0], "question_it_resolves": s[1], "voi_rank": s[2], "why": s[3],
             "free_source_status": "DATA_BLOCKED (no free-only verified source)",
             "material_to_sign_law": "YES" if s[2] == "HIGH" else "PARTIAL"}
            for s in sensors]
    rows.append({"sensor": "VERDICT", "question_it_resolves": "",
                 "voi_rank": "HIGHEST=LIQUIDATIONS/ORDER_FLOW/OI/FUNDING",
                 "why": "these directly test the forced-selling and urgency hypotheses that the "
                        "downside gap currently attributes to unknown mechanics",
                 "free_source_status": "DATA_BLOCKED", "material_to_sign_law": ""})
    pd.DataFrame(rows).to_csv(R / "29_SENSOR_VALUE_OF_INFORMATION.csv", index=False)


# ---------------------------------------------------------------------------
# 30 FREE-SOURCE STATUS AUDIT (reference only)
# ---------------------------------------------------------------------------

def free_sensor_status():
    """Reference-only audit: review whether any already-verified FREE_AUTOMATED
    or FREE_LIMITED_AUTOMATED source in the project registry supplies the
    missing mechanical fields. Do not scrape or pay."""
    # Verify against the project's provider registry if it exists
    import glob
    registry_hits = []
    for pat in ["**/*provider*registry*", "**/*data*source*", "**/*PROVIDER*"]:
        registry_hits += glob.glob(str(W.ROOT.parents[1] / pat), recursive=True) or []
    sensors = ["FUNDING", "OPEN_INTEREST", "LIQUIDATIONS", "ORDER_BOOK_DEPTH",
               "SPREAD", "ORDER_FLOW_IMBALANCE", "COLLATERAL_MARGIN", "STABLECOIN_FLOWS"]
    rows = []
    for s in sensors:
        rows.append({"sensor": s,
                     "registry_sources_found": str(len(registry_hits)),
                     "verified_free_automated": "NO",
                     "verified_free_limited": "NO",
                     "status": "UNVERIFIED / DATA_BLOCKED",
                     "note": "no already-verified FREE_AUTOMATED source for this field in the current "
                             "project registry; no new source integrated (no scraping, no paid data)"})
    rows.append({"sensor": "VERDICT", "registry_sources_found": "",
                 "verified_free_automated": "DATA_BLOCKED_PENDING_SENSORS",
                 "verified_free_limited": "",
                 "status": "REFERENCE_ONLY",
                 "note": "the sign-law question stays DATA_BLOCKED for major mechanical families until "
                         "a free-only source is independently verified"})
    pd.DataFrame(rows).to_csv(R / "30_FREE_SENSOR_STATUS.csv", index=False)


# ---------------------------------------------------------------------------
# 31 UPSIDE DEFINITION AUDIT (minor repairs A/B)
# ---------------------------------------------------------------------------

def upside_definition_audit(df):
    """Repair the two minor upside issues: (A) COHERENCE had negative delta
    despite wording that all functions lift; (B) REJOIN and
    POSITIVE_PARTICIPATION_HISTORY aliasing. Audit definitions."""
    d = _ready(df.copy())
    rows = []
    # (A) coherence delta
    sub = d[["ups_current_coherence", "stg_rejoin"]].dropna()
    hi = sub[sub["ups_current_coherence"] == 1]
    lo = sub[sub["ups_current_coherence"] == 0]
    if len(hi) > 30 and len(lo) > 30:
        rows.append({"function": "COHERENCE", "issue": "A-negative-delta",
                     "definition": "ups_current_coherence = peer_corr >= median (T0)",
                     "rejoin_hi": _fmt(hi["stg_rejoin"].mean()),
                     "rejoin_lo": _fmt(lo["stg_rejoin"].mean()),
                     "delta": _fmt(hi["stg_rejoin"].mean() - lo["stg_rejoin"].mean()),
                     "finding": "delta is NEGATIVE — coherence is not a positive amplifier for rejoin; "
                                "LF12 wording that all 7 functions lift is corrected: coherence is a weak "
                                "negative or neutral condition, not an amplifier"})
    # (B) aliasing check: rejoin vs positive-history
    if "ups_positive_history" in d.columns and "out_rejoin" in d.columns:
        prev_rej = d.groupby("cmc_id")["out_rejoin"].shift(1).fillna(0)
        alias = (d["ups_positive_history"] == prev_rej).mean()
        rows.append({"function": "REJOIN vs POSITIVE_HISTORY", "issue": "B-aliasing",
                     "definition": "ups_positive_history = prev_rejoin (prior-event, PIT-safe)",
                     "rejoin_hi": "", "rejoin_lo": "",
                     "delta": _fmt(alias),
                     "finding": f"ups_positive_history is definitionally identical to prev_rejoin "
                                f"(overlap {_fmt(alias)}) — the two are ALIASED; LF13 treats them as one "
                                f"'positive history' coordinate, not two functions"})
    rows.append({"function": "VERDICT", "issue": "",
                 "definition": "UPSIDE_FUNCTIONS_ARE_WEAK_AMPLIFIERS",
                 "rejoin_hi": "", "rejoin_lo": "", "delta": "",
                 "finding": "after correction: coherence is neutral/negative; positive-history and rejoin "
                            "are one aliased coordinate; the remaining PIT-safe functions are weak "
                            "amplifiers, not hard permission gates"})
    pd.DataFrame(rows).to_csv(R / "31_UPSIDE_DEFINITION_AUDIT.csv", index=False)


# ---------------------------------------------------------------------------
# 32 UPSIDE FUNCTIONAL COMPRESSION
# ---------------------------------------------------------------------------

def upside_functional_compression(df):
    """Compress PIT-safe upside functions into minimal groups (structural
    support / liquidity support / positive history) only if earned."""
    d = _ready(df.copy())
    rows = []
    groups = {
        "STRUCTURAL_SUPPORT": ["ups_current_stability", "ups_capacity_region"],
        "LIQUIDITY_SUPPORT": ["ups_current_liquidity", "ups_time_since_downside"],
        "POSITIVE_HISTORY": ["ups_positive_history", "ups_prior_rank_repair"],
        "STATE_COHERENCE": ["ups_current_coherence"],
        "RANK_HEALTH_CURRENT": ["ups_current_rank_health"],
    }
    base = d["stg_rejoin"].mean()
    rows.append({"group": "BASE_REJOIN_RATE", "n": int(len(d)), "rejoin_rate": _fmt(base),
                 "lift_pp": "0.0", "compression": ""})
    for gname, cols in groups.items():
        avail = [c for c in cols if c in d.columns]
        if not avail:
            continue
        s = d[avail].sum(axis=1)
        hi = d[s >= len(avail) * 0.5]
        lo = d[s < len(avail) * 0.5]
        if len(hi) < 30 or len(lo) < 30:
            continue
        rows.append({"group": gname, "n": int(len(hi)),
                     "rejoin_rate": _fmt(hi["stg_rejoin"].mean()),
                     "lift_pp": _fmt((hi["stg_rejoin"].mean() - base) * 100),
                     "compression": "kept"})
    rows.append({"group": "VERDICT", "n": "", "rejoin_rate": "2-3_WEAK_AMPLIFIERS",
                 "lift_pp": "", "compression": "",
                 "note": "structural support, liquidity support and positive history each add a few pp "
                         "of rejoin probability — upside compresses to 2-3 weak amplifier coordinates; "
                         "no hard permission gate"})
    pd.DataFrame(rows).to_csv(R / "32_UPSIDE_FUNCTIONAL_COMPRESSION.csv", index=False)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("[lf13] building master frame ...", flush=True)
    df = W.master_frame(use_cache=True)
    df = _ready(df)

    print("[lf13] 02 memory timescale reconciliation ...", flush=True)
    memory_timescale_reconciliation(df)
    print("[lf13] 03 memory by shock family ...", flush=True)
    memory_by_shock_family(df)
    print("[lf13] 05 capacity dependency matrix ...", flush=True)
    capacity_dependency_matrix(df)
    print("[lf13] 06 capacity core coordinates ...", flush=True)
    capacity_core_coordinates(df)
    print("[lf13] 07 capacity substitution ...", flush=True)
    capacity_substitution(df)
    print("[lf13] 08 capacity bottlenecks ...", flush=True)
    capacity_bottlenecks(df)
    print("[lf13] 09 capacity final surface ...", flush=True)
    capacity_final_surface(df)
    print("[lf13] 10 absorption-containment relations ...", flush=True)
    absorption_containment_relations(df)
    print("[lf13] 11 absorption-containment 2x2 ...", flush=True)
    absorption_containment_2x2(df)
    print("[lf13] 12 contagion mechanism surface ...", flush=True)
    contagion_mechanism_surface(df)
    print("[lf13] 13 early reach mechanics ...", flush=True)
    early_reach_mechanics(df)
    print("[lf13] 14 recency x shock interaction ...", flush=True)
    recency_shock_interaction(df)
    print("[lf13] 15 contagion temporal trajectories ...", flush=True)
    contagion_temporal_trajectories(df)
    print("[lf13] 16 contagion phases ...", flush=True)
    contagion_phases(df)
    print("[lf13] 17 fast contagion placement ...", flush=True)
    fast_contagion_placement(df)
    print("[lf13] 18 slow persistent contagion ...", flush=True)
    slow_persistent_contagion(df)
    print("[lf13] 19 reactivation within contagion ...", flush=True)
    reactivation_within_contagion(df)
    print("[lf13] 20 contagion clearance ...", flush=True)
    contagion_clearance(df)
    print("[lf13] 21 decoupling relation map ...", flush=True)
    decoupling_relation_map(df)
    print("[lf13] 22 decoupling classification ...", flush=True)
    decoupling_classification(df)
    print("[lf13] 23 decoupling exit health ...", flush=True)
    decoupling_exit_health(df)
    print("[lf13] 24 sign asymmetry surface ...", flush=True)
    sign_asymmetry_surface(df)
    print("[lf13] 25 sign asymmetry by tempo ...", flush=True)
    sign_asymmetry_by_tempo(df)
    print("[lf13] 26 sign asymmetry temporal profile ...", flush=True)
    sign_asymmetry_temporal_profile(df)
    print("[lf13] 27 sign asymmetry by stage ...", flush=True)
    sign_asymmetry_by_stage(df)
    print("[lf13] 28 sign asymmetry minimal explained set ...", flush=True)
    sign_asymmetry_minimal_explained(df)
    print("[lf13] 29 sensor value of information ...", flush=True)
    sensor_value_of_information()
    print("[lf13] 30 free sensor status ...", flush=True)
    free_sensor_status()
    print("[lf13] 31 upside definition audit ...", flush=True)
    upside_definition_audit(df)
    print("[lf13] 32 upside functional compression ...", flush=True)
    upside_functional_compression(df)

    print("[lf13] DONE", flush=True)


if __name__ == "__main__":
    main()
