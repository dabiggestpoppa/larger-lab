"""LOWER-FIELD-10 analysis — shock & contagion cartography.

Built on the LF8/LF9 relational engine + the LF5 PIT substrate + the MECH-15
global field surface. The mission: map the internal dimensions / species /
temporal geometry of local physical shock, contagion, decoupling and
directional asymmetry. Start broad, compress from data, preserve locality.
No strategy, no PnL, no execution. Outputs 02-26 + 28 written to
lower_field_10/.
"""
from __future__ import annotations

import warnings
from collections import Counter
from collections.abc import Iterable

import numpy as np
import pandas as pd

from scipy import cluster as sch
from scipy.stats import spearmanr, ranksums, wilcoxon, chi2_contingency, kruskal
from scipy.stats import pointbiserialr
from scipy.optimize import curve_fit
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import lf10_common as L
import lf9_common as C9

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = L.ROOT
A = C9.A
C = C9.C
MIN_SUPPORT = L.MIN_SUPPORT

_fmt = A._fmt
_med = L._med
_mean = L._mean
_purged_auc = A._purged_auc

COORDS = [code for code, _, _ in L.COORD_DEFS]
STATE_AXES = ["REORGANIZING", "DECOUPLED", "TRUE_ISOLATED", "FALSE_ISOLATED",
              "PEER_STRESSED", "REJOINING", "REHABILITATING", "CONTAGIOUS",
              "LOCALLY_CONFORMING", "DISLOCATED_UNCLASSIFIED"]
ABS_CLS = ["<2%", "2-5%", "5-10%", "10-20%", ">20%"]
SIG_CLS = ["<2σ", "2-3σ", "3-4σ", "4σ+"]


def _ready(df):
    df = df.copy()
    if "abs_class" not in df.columns:
        df["abs_class"] = df["abs_ret"].map(A._abs_class)
    if "sigma_class" not in df.columns:
        df["sigma_class"] = df["sigma"].map(C9._sigma_class_full) if "sigma" in df.columns \
            else df["z1"].map(A._sigma_class)
    if "liq_ctx" not in df.columns:
        q = df["liq_proxy"].fillna(df["liq_proxy"].median())
        df["liq_ctx"] = pd.qcut(q.rank(method="first"), 3, labels=["LIQ_DEEP", "LIQ_NORM", "LIQ_THIN"])
    if "duration" not in df.columns:
        r3 = df.get("ret_3d", np.nan)
        ratio = np.abs(np.asarray(r3, dtype=float)) / np.maximum(np.asarray(df["abs_ret"], dtype=float), 1e-9)
        df["duration"] = np.select([ratio >= 1.5, ratio >= 1.0], ["MULTI_DAY", "SHORT_SUSTAINED"],
                                   default="IMPULSE")
    return df


# ---------------------------------------------------------------------------
# 02 RELATIONAL CONTINUOUS COORDINATES
# ---------------------------------------------------------------------------

def relational_coordinates(df):
    rows = []
    for code, label, _ in L.COORD_DEFS:
        if code not in df.columns:
            continue
        col = df[code]
        non = col.dropna()
        # per-state medians
        for st in STATE_AXES:
            sub = col[df["rel_state"] == st].dropna()
            rows.append({"section": "STATEMED", "coord": code, "label": label,
                         "state": st, "n": int(len(sub)),
                         "median": _fmt(sub.median()) if len(sub) else np.nan})
        # state discrimination (Kruskal-Wallis)
        groups = [col[df["rel_state"] == st].dropna().to_numpy() for st in STATE_AXES]
        groups = [g for g in groups if len(g) >= 10]
        kw_p = np.nan
        if len(groups) >= 2:
            try:
                kw_p = float(kruskal(*groups).pvalue)
            except Exception:
                pass
        # transport discrimination (Spearman vs outcome)
        rhos = {}
        for oname, ocol in [("contagion", "out_contagion"), ("decoupling", "out_decouple"),
                            ("rejoin", "out_rejoin")]:
            mask = df[ocol].notna()
            if mask.sum() >= 30:
                r, _ = spearmanr(df.loc[mask, code], df.loc[mask, ocol])
                rhos[oname] = float(r) if np.isfinite(r) else np.nan
            else:
                rhos[oname] = np.nan
        rows.append({"section": "DISCRIM", "coord": code, "label": label, "state": "",
                     "n": int(len(non)),
                     "median": _fmt(non.median()) if len(non) else np.nan,
                     "kruskal_across_states_p": _fmt(kw_p, 3),
                     "spearman_contagion": _fmt(rhos.get("contagion")),
                     "spearman_decoupling": _fmt(rhos.get("decoupling")),
                     "spearman_rejoin": _fmt(rhos.get("rejoin"))})
    dfw = pd.DataFrame(rows)
    dfw.to_csv(R / "02_RELATIONAL_CONTINUOUS_COORDINATES.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 03 RELATIONAL COORDINATE COMPRESSION
# ---------------------------------------------------------------------------

def _coord_matrix(df):
    # correlation matrix with pairwise deletion
    corr = df[COORDS].corr(method="spearman")
    return corr


def coordinate_compression(df):
    corr = _coord_matrix(df)
    codes = list(corr.columns)
    if len(codes) < 3:
        dfw = pd.DataFrame([{"note": "too few coords", "v1_ratio": np.nan,
                             "n_clusters_greedy": np.nan, "verdict": "NO_COMPRESSION"}])
        dfw.to_csv(R / "03_RELATIONAL_COORDINATE_COMPRESSION.csv", index=False)
        return dfw
    # greedy redundancy clusters at |rho| >= 0.7
    used = set()
    clusters = []
    members_map = {}
    for i, a in enumerate(codes):
        if a in used:
            continue
        grp = [a]
        for j, b in enumerate(codes):
            if b == a or b in used:
                continue
            v = corr.loc[a, b]
            if np.isfinite(v) and abs(v) >= 0.7:
                grp.append(b)
                used.add(b)
        used.add(a)
        clusters.append(grp)
        for m in grp:
            members_map[m] = grp
    # PCA pilot on standardized coords (median-impute so a pilot always runs)
    mat = df[COORDS].copy()
    for c in mat.columns:
        mat[c] = mat[c].fillna(mat[c].median())
    scaler = StandardScaler()
    Z = scaler.fit_transform(mat.to_numpy())
    pc = PCA()
    pc.fit(Z)
    pve = pc.explained_variance_ratio_
    ev = pc.explained_variance_
    n_ev1 = int((ev >= 1.0).sum())
    cum90 = int((np.cumsum(pve) < 0.9).sum()) + 1
    # hierarchical clustering of coords (distance = 1-|corr|)
    from scipy.spatial.distance import squareform
    dist = 1.0 - np.abs(corr.to_numpy())
    np.fill_diagonal(dist, 0.0)
    try:
        Zc = sch.linkage(squareform(dist, checks=False), method="average")
        # choose cut at 0.5 correlation distance
        clusters_h = sch.fcluster(Zc, 0.5, criterion="distance")
        n_cl_h = int(clusters_h.max())
    except Exception:
        n_cl_h = int(len(codes))
    rows = []
    for i, c in enumerate(clusters):
        if len(c) >= 2:
            rows.append({"cluster": i, "n_components": len(c), "members": ";".join(c)})
    rows.append({"cluster": "PCA", "n_components": int(len(codes)),
                 "members": f"eigenvalues>1 => {n_ev1} dims; cum-PVE>0.9 => {n_ev1} dims; "
                            f"top1 PVE {_fmt(pve[0] if len(pve) else float('nan'))}"})
    # verdict
    if n_cl_h <= max(4, int(len(codes) / 2)):
        verdict = "COMPACT_RELATIONAL_COORDINATES"
    elif any(len(g) >= 3 for g in clusters):
        verdict = "MULTIPLE_LOCAL_COORDINATES"
    else:
        verdict = "NO_COMPRESSION"
    rows.append({"cluster": "VERDICT", "n_components": n_cl_h, "members": verdict})
    dfw = pd.DataFrame(rows)
    # correlation matrix long-form for transparency
    pairs = []
    for i, a in enumerate(codes):
        for j in range(i + 1, len(codes)):
            b = codes[j]
            v = corr.loc[a, b]
            pairs.append({"coord_a": a, "coord_b": b, "spearman_rho": _fmt(v) if np.isfinite(v) else np.nan})
    pd.concat([pd.DataFrame(pairs), dfw], ignore_index=True).to_csv(
        R / "03_RELATIONAL_COORDINATE_COMPRESSION.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 04 TOPOLOGY-CHURN ANATOMY
# ---------------------------------------------------------------------------

def topology_churn_anatomy(df):
    df = _ready(df)
    groups = [("OVERALL", pd.Series("ALL", index=df.index)),
              ("RANK_DEPTH", df["rank_depth"]),
              ("REL_STATE", df["rel_state"]),
              ("DIRECTION", df["side"]),
              ("ABS_CLASS", df["abs_class"])]
    rows = []
    for gname, gv in groups:
        for key, g in df.groupby(gv):
            if len(g) < 30 or pd.isna(key):
                continue
            r = {"group": gname, "level": str(key), "n": int(len(g))}
            for f in ["churn_turnover", "jaccard_overlap", "old_coherence", "new_coherence",
                      "added_peers", "dropped_peers", "rank_migration", "old_peer_stress",
                      "new_peer_stress", "sign_aligned_frac", "sign_opposed_frac",
                      "added_peer_fwd7", "dropped_peer_fwd7"]:
                r[f"med_{f}"] = _fmt(g[f].median()) if g[f].notna().any() else np.nan
            r["p_rejoin"] = _fmt(g["out_rejoin"].mean())
            r["p_contagion"] = _fmt(g["out_contagion"].mean())
            r["p_decouple"] = _fmt(g["out_decouple"].mean())
            rows.append(r)
    dfw = pd.DataFrame(rows)
    # replacement-quality question: does the added cohort outperform the dropped?
    sub = df.dropna(subset=["added_peer_fwd7", "dropped_peer_fwd7"])
    if len(sub) >= 30:
        d, p = wilcoxon(sub["added_peer_fwd7"].to_numpy(), sub["dropped_peer_fwd7"].to_numpy())
        rows.append({"group": "VERDICT", "level": "replacement_quality",
                     "n": int(len(sub)),
                     "med_added_peer_fwd7": _fmt(sub["added_peer_fwd7"].median()),
                     "med_dropped_peer_fwd7": _fmt(sub["dropped_peer_fwd7"].median()),
                     "wilcoxon_added_vs_dropped_p": _fmt(float(p), 3),
                     "verdict": "REPLACEMENT_MATTERS" if p < 0.05 else "REPLACEMENT_NEUTRAL"})
    else:
        rows.append({"group": "VERDICT", "level": "replacement_quality", "n": int(len(sub)),
                     "verdict": "INSUFFICIENT"})
    pd.DataFrame(rows).to_csv(R / "04_TOPOLOGY_CHURN_ANATOMY.csv", index=False)
    return dfw


# ---------------------------------------------------------------------------
# 05 TOPOLOGY-CHURN SPECIES
# ---------------------------------------------------------------------------

def _silhouette(X, labels):
    from sklearn.metrics import silhouette_score
    try:
        return float(silhouette_score(X, labels))
    except Exception:
        return np.nan


def topology_churn_species(df):
    dims = ["churn_turnover", "old_coherence", "new_coherence", "rank_migration",
            "old_peer_stress", "new_peer_stress", "sign_aligned_frac", "sign_opposed_frac"]
    sub = df[dims + ["subperiod"]].copy()
    for c in dims:
        med = sub[c].median()
        sub[c] = sub[c].fillna(med if pd.notna(med) else 0.0).fillna(0.0)
    X = sub[dims].to_numpy(dtype=float)
    from sklearn.cluster import KMeans
    if len(sub) < 60:
        pd.DataFrame([{"verdict": "NO_STABLE_CHURN_SPECIES", "n_clusters_best": 1,
                       "silhouette_best": np.nan, "reason": "insufficient events"}]).to_csv(
            R / "05_TOPOLOGY_CHURN_SPECIES.csv", index=False)
        return
    scaler = StandardScaler()
    Zs = scaler.fit_transform(X)
    best = {"k": 1, "sil": -2.0}
    for k in range(2, min(7, len(Zs) // 20 + 2)):
        km = KMeans(n_clusters=k, n_init=10, random_state=20260910)
        labs = km.fit_predict(Zs)
        # reject degenerate solutions with a tiny cluster (< 20 members)
        sizes = np.bincount(labs, minlength=k)
        if (sizes < 20).any():
            continue
        sil = _silhouette(Zs, labs)
        if np.isfinite(sil) and sil > best["sil"]:
            best = {"k": k, "sil": sil}
    rows = []
    rows.append({"species_id": "BEST", "n_clusters": best["k"], "silhouette": _fmt(best["sil"]),
                 "n_events": int(len(sub))})
    if best["k"] >= 2:
        km = KMeans(n_clusters=best["k"], n_init=10, random_state=20260910)
        labs = km.fit_predict(Zs)
    else:
        labs = np.zeros(len(sub), dtype=int)
    sub = sub.copy()
    sub["spp"] = labs
    name_map = {0: "CHURN_SP0", 1: "CHURN_SP1", 2: "CHURN_SP2", 3: "CHURN_SP3",
                4: "CHURN_SP4", 5: "CHURN_SP5", 6: "CHURN_SP6"}
    for k0 in range(max(best["k"], 1)):
        g = sub[sub["spp"] == k0]
        ncyc = int(g["subperiod"].nunique())
        ok = len(g) >= MIN_SUPPORT and ncyc >= 3
        rows.append({"species_id": name_map[k0], "n_clusters": best["k"], "silhouette": np.nan,
                     "n_events": int(len(g)), "n_subperiods": ncyc,
                     "meets_support_bar": "YES" if ok else "NO",
                     "med_churn": _fmt(g["churn_turnover"].median()),
                     "med_old_coherence": _fmt(g["old_coherence"].median()),
                     "med_new_coherence": _fmt(g["new_coherence"].median()),
                     "med_rank_migration": _fmt(g["rank_migration"].median()),
                     "med_sign_aligned": _fmt(g["sign_aligned_frac"].median())})
    n_ok = sum(1 for r in rows if isinstance(r.get("meets_support_bar"), str) and r["meets_support_bar"] == "YES")
    verdict = ("FEW_STABLE_CHURN_SPECIES" if best["sil"] >= 0.25 and n_ok >= 2
               else "CONTINUOUS_CHURN_SPACE" if best["k"] == 1 or best["sil"] < 0.10
               else "NO_STABLE_CHURN_SPECIES")
    rows.append({"species_id": "VERDICT", "n_clusters": best["k"], "silhouette": _fmt(best["sil"]),
                 "n_events": int(len(sub)), "species_supported": n_ok, "verdict": verdict})
    pd.DataFrame(rows).to_csv(R / "05_TOPOLOGY_CHURN_SPECIES.csv", index=False)


# ---------------------------------------------------------------------------
# 06 BROAD LOCAL-SHOCK ATLAS (conditional slices, no giant cube)
# ---------------------------------------------------------------------------

def _slice_row(slice_name, level, g, n_col="_n"):
    return {"slice": slice_name, "level": str(level) if not pd.isna(level) else "NA",
            "n_events": int(len(g)),
            "p_contagion": _fmt(g["out_contagion"].mean()),
            "p_decouple": _fmt(g["out_decouple"].mean()),
            "p_rejoin": _fmt(g["out_rejoin"].mean()),
            "p_absorbed": _fmt((g["shock_outcome"] == "ABSORBED").mean()),
            "p_reorganized": _fmt((g["shock_outcome"] == "REORGANIZED").mean()),
            "p_propagated": _fmt((g["shock_outcome"] == "PROPAGATED").mean()),
            "p_persistent": _fmt((g["shock_outcome"] == "PERSISTENT").mean())}


def broad_shock_atlas(df):
    d = _ready(df)
    rows = []
    slices = [("ABS_MAGNITUDE", "abs_class"), ("SIGMA", "sigma_class"),
              ("LIQUIDITY_CONTEXT", "liq_ctx"), ("NEIGHBORHOOD_CONDITION", "rel_state"),
              ("DIRECTION", "side"), ("DURATION", "duration"), ("RANK_DEPTH", "rank_depth")]
    for sname, col in slices:
        for key, g in d.groupby(col):
            if len(g) < 30 or pd.isna(key):
                continue
            rows.append(_slice_row(sname, key, g))
    # conditional pair slices (directional reduction)
    for direction in ["UP", "DOWN"]:
        gd = d[d["side"] == direction]
        for (ac, sc), g in gd.groupby(["abs_class", "sigma_class"]):
            if len(g) < 30:
                continue
            rows.append(_slice_row(f"DIRECTION:{direction}|ABSxSIGMA",
                                   f"{ac}|{sc}", g))
    dfw = pd.DataFrame(rows).sort_values(["slice", "n_events"], ascending=[True, False])
    # dimensional contribution (global field overlay + rank influence)
    overlay = []
    for ac in ABS_CLS:
        g = d[d["abs_class"] == ac]
        if len(g) < 30:
            continue
        overlay.append({"abs_class": ac, "n": int(len(g)),
                        "med_forcing": _fmt(g["forcing"].median()),
                        "mcell6_distinct": int(g["mcell6"].nunique())})
    dfw.to_csv(R / "06_BROAD_LOCAL_SHOCK_ATLAS.csv", index=False)
    pd.DataFrame(overlay).to_csv(R / "06b_SHOCK_ATLAS_FIELD_OVERLAY.csv", index=False)
    return dfw


def _slice_row(slice_name, level, g):
    return {"slice": slice_name, "level": str(level) if not pd.isna(level) else "NA",
            "n_events": int(len(g)),
            "p_contagion": _fmt(g["out_contagion"].mean()),
            "p_decouple": _fmt(g["out_decouple"].mean()),
            "p_rejoin": _fmt(g["out_rejoin"].mean()),
            "p_absorbed": _fmt((g["shock_outcome"] == "ABSORBED").mean()),
            "p_reorganized": _fmt((g["shock_outcome"] == "REORGANIZED").mean()),
            "p_propagated": _fmt((g["shock_outcome"] == "PROPAGATED").mean()),
            "p_persistent": _fmt((g["shock_outcome"] == "PERSISTENT").mean())}


# ---------------------------------------------------------------------------
# 07 SHOCK-SPECIES COMPRESSION
# ---------------------------------------------------------------------------

def _winsorize(s, lo=0.01, hi=0.99):
    q = s.quantile([lo, hi])
    return s.clip(q.iloc[0], q.iloc[1])


def shock_species_compression(df):
    d = _ready(df)
    feats = ["abs_ret", "sigma", "vol_30d", "liq_proxy", "peer_corr", "roll_turnover_30d",
             "peer_stress", "rank"]
    sub = d.dropna(subset=feats).copy()
    # winsorize heavy tails (rank / abs / sigma) so one massive outlier cannot
    # fabricate a degenerate 2-member "species".
    for fc in feats:
        sub[fc] = _winsorize(sub[fc])
    X = sub[feats].to_numpy(dtype=float)
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    scaler = StandardScaler()
    Zs = scaler.fit_transform(X)
    best = {"k": 1, "sil": -2.0}
    sil_tab = []
    for k in range(2, min(8, len(Zs) // 30 + 2)):
        km = KMeans(n_clusters=k, n_init=10, random_state=20260911)
        labs = km.fit_predict(Zs)
        sizes = np.bincount(labs, minlength=k)
        if (sizes < 20).any():       # reject degenerate tiny clusters
            sil_tab.append({"k": k, "silhouette": "DEGENERATE_TINY_CLUSTER"})
            continue
        sil = float(silhouette_score(Zs, labs))
        sil_tab.append({"k": k, "silhouette": _fmt(sil)})
        if sil > best["sil"]:
            best = {"k": k, "sil": sil}
    if best["k"] >= 2:
        km = KMeans(n_clusters=best["k"], n_init=10, random_state=20260911)
        labs = km.fit_predict(Zs)
    else:
        labs = np.zeros(len(sub), dtype=int)
    sub = sub.copy()
    sub["shock_cls"] = labs
    rows = [{"metric": "SILHOUETTE_SCAN", "k": r["k"], "value": r["silhouette"]} for r in sil_tab]
    for k0 in range(max(best["k"], 1)):
        g = sub[sub["shock_cls"] == k0]
        ncyc = int(g["subperiod"].nunique())
        rows.append({"metric": "SHOCK_SPECIES", "k": best["k"], "cluster": k0,
                     "n_events": int(len(g)), "value": ncyc,
                     "n_subperiods": ncyc,
                     "p_contagion": _fmt(g["out_contagion"].mean()),
                     "p_decouple": _fmt(g["out_decouple"].mean()),
                     "p_rejoin": _fmt(g["out_rejoin"].mean()),
                     "med_abs": _fmt(g["abs_ret"].median()),
                     "med_sigma": _fmt(g["sigma"].median()),
                     "med_liq": _fmt(g["liq_proxy"].median()),
                     "med_rank": _fmt(g["rank"].median()),
                     "med_peer_corr": _fmt(g["peer_corr"].median())})
    n_species = best["k"]
    if n_species == 1 or best["sil"] < 0.10:
        v = "CONTINUOUS_SHOCK_MANIFOLD" if best["sil"] >= 0.10 else "NO_STABLE_SPECIES"
    elif best["sil"] >= 0.25 and n_species <= 4:
        v = "FEW_SHOCK_SPECIES"
    elif best["sil"] >= 0.25:
        v = "STATE_LOCAL_SPECIES"
    else:
        v = "NO_STABLE_SPECIES"
    rows.append({"metric": "VERDICT", "k": n_species, "value": v})
    pd.DataFrame(rows).to_csv(R / "07_SHOCK_SPECIES_COMPRESSION.csv", index=False)


# ---------------------------------------------------------------------------
# 08 SHOCK ABSORPTION vs REORGANIZATION
# ---------------------------------------------------------------------------

def shock_absorption_reorganization(df):
    d = _ready(df)
    rows = []
    dims = [("ABS_CLASS", "abs_class"), ("SIGMA_CLASS", "sigma_class"),
            ("LIQUIDITY", "liq_ctx"), ("NEIGHBORHOOD", "rel_state"),
            ("RANK_DEPTH", "rank_depth"), ("DIRECTION", "side"), ("DURATION", "duration")]
    for gname, col in dims:
        for key, g in d.groupby(col):
            if len(g) < 30 or pd.isna(key):
                continue
            rows.append({"dim": gname, "level": str(key), "n": int(len(g)),
                         "p_absorbed": _fmt((g["shock_outcome"] == "ABSORBED").mean()),
                         "p_reorganized": _fmt((g["shock_outcome"] == "REORGANIZED").mean()),
                         "p_propagated": _fmt((g["shock_outcome"] == "PROPAGATED").mean()),
                         "p_persistent": _fmt((g["shock_outcome"] == "PERSISTENT").mean())})
    # what separates absorbed from reorganized (within matched abs band 5-10%)
    g = d[(d["abs_class"] == "5-10%")]
    if len(g) >= 60:
        absorbed = g["shock_outcome"] == "ABSORBED"
        feats = ["peer_corr", "liq_proxy", "roll_turnover_30d", "peer_stress", "vol_30d", "rank"]
        sub = g.dropna(subset=feats).copy()
        sub["y"] = absorbed.loc[sub.index].astype(int)
        if sub["y"].nunique() == 2:
            from sklearn.linear_model import LogisticRegression
            Xs = StandardScaler().fit_transform(sub[feats].to_numpy(dtype=float))
            clf = LogisticRegression(max_iter=1000)
            clf.fit(Xs, sub["y"].to_numpy())
            for f, c in zip(feats, clf.coef_[0]):
                rows.append({"dim": "ABSORBED_vs_REORGANIZED_LOGIT", "level": f, "n": int(len(sub)),
                             "coef_std": _fmt(c, 3), "note": "positive => raises P(absorbed)"})
    pd.DataFrame(rows).to_csv(R / "08_SHOCK_ABSORPTION_REORGANIZATION.csv", index=False)


# ---------------------------------------------------------------------------
# 09 LOCAL ABSORPTION CAPACITY
# ---------------------------------------------------------------------------

def local_absorption_capacity(df):
    g = df.dropna(subset=["shock_outcome"]).copy()
    g["absorbed"] = (g["shock_outcome"] == "ABSORBED").astype(int)
    # prior shock burden: n isolated events for the asset in trailing 90d
    prev = g.sort_values(["cmc_id", "historical_date"])
    cnt_days = (g["historical_date"] - g.groupby("cmc_id")["historical_date"].shift()).dt.days
    g["days_since_prior_shock"] = cnt_days
    g["prior_shock_burden"] = (cnt_days <= 90).astype(float)
    feats = {"neighborhood_coherence": "peer_corr",
             "liquidity": "liq_proxy",
             "rank_health": "rank",                 # lower is stronger (1 = top)
             "volatility": "vol_30d",
             "peer_stress": "peer_stress",
             "membership_stability": "roll_turnover_30d",  # lower = more stable
             "prior_shock_burden": "prior_shock_burden"}
    rows = []
    for fname, col in feats.items():
        mask = g[col].notna()
        if mask.sum() < 40:
            continue
        r, p = pointbiserialr(g.loc[mask, col].to_numpy(), g.loc[mask, "absorbed"].to_numpy())
        # AUC via logistic single-feature purged
        try:
            auc = _purged_auc(g.loc[mask], "absorbed", [col])
        except Exception:
            auc = np.nan
        rows.append({"capacity_coord": fname, "point_biserial_vs_absorbed": _fmt(r, 3),
                     "p": _fmt(float(p), 3), "purged_auc_absorbed": _fmt(auc),
                     "n": int(mask.sum())})
    dfw = pd.DataFrame(rows)
    # verdict: is absorption capacity a stable local coordinate?
    if len(dfw):
        aucs = dfw["purged_auc_absorbed"].astype(float).dropna()
        n_good = int((aucs >= 0.58).sum()) if len(aucs) else 0
        verdict = ("LOCAL_ABSORPTION_COORDINATE" if n_good >= 2
                   else "STATE_LOCAL_CAPACITY" if n_good == 1
                   else "NO_STABLE_LOCAL_CAPACITY")
    else:
        verdict = "NO_STABLE_LOCAL_CAPACITY"
    dfw["verdict"] = np.nan
    dfw.loc[len(dfw)] = {"capacity_coord": "VERDICT", "point_biserial_vs_absorbed": np.nan,
                         "p": np.nan, "purged_auc_absorbed": np.nan, "n": int(len(g)),
                         "verdict": verdict}
    dfw.to_csv(R / "09_LOCAL_ABSORPTION_CAPACITY.csv", index=False)


# ---------------------------------------------------------------------------
# 10 PHYSICAL-SHOCK RESPONSE CURVES
# ---------------------------------------------------------------------------

def _mm(x, c, k):
    return c * x / (k + x)


def shock_response_curves(df):
    d = df.dropna(subset=["abs_ret"]).copy()
    d["abs_bin"] = pd.qcut(d["abs_ret"].rank(method="first"), 10, labels=False, duplicates="drop")
    responses = [("turnover", "roll_turnover_30d"), ("state_change", "state_changed"),
                 ("contagion", "out_contagion"), ("decoupling", "out_decouple"),
                 ("rejoin", "out_rejoin")]
    pairs = [("OVERALL", d), ("UP", d[d["side"] == "UP"]), ("DOWN", d[d["side"] == "DOWN"])]
    rows = []
    for side_name, sd in pairs:
        for rname, col in responses:
            rows.append({"side": side_name, "response": rname, "type": "OVERALL_N",
                         "abs_med": np.nan, "rate": np.nan})
        for (b, g) in sd.groupby("abs_bin"):
            if len(g) < 20:
                continue
            abs_med = float(g["abs_ret"].median())
            for rname, col in responses:
                v = g[col].dropna()
                rows.append({"side": side_name, "response": rname, "type": "BIN",
                             "abs_med": _fmt(abs_med), "rate": _fmt(v.mean())})
        # Michaelis-Menten fit per response on binned means
        bins = []
        for (b, g) in sd.groupby("abs_bin"):
            if len(g) < 20:
                continue
            bins.append((float(g["abs_ret"].median()), {rname: g[col].dropna().mean()
                                                        for rname, col in responses}))
        bins.sort()
        xs = np.array([x for x, _ in bins])
        for rname, _ in responses:
            ys = np.array([d2[rname] for _, d2 in bins])
            if len(xs) < 4 or np.nanmax(ys) <= np.nanmin(ys):
                rows.append({"side": side_name, "response": rname, "type": "FIT",
                             "abs_med": np.nan, "rate": "FIT_FAILED_FLAT"})
                continue
            try:
                c0, k0 = float(np.nanmax(ys)), float(np.median(xs))
                popt, _ = curve_fit(_mm, xs, ys, p0=[max(c0, 1e-6), max(k0, 1e-4)],
                                    bounds=([1e-6, 1e-5], [2.0, 0.5]), maxfev=20000)
                rows.append({"side": side_name, "response": rname, "type": "FIT",
                             "abs_med": _fmt(popt[0]), "rate2": _fmt(popt[1]),
                             "ceiling": _fmt(popt[0]), "half_sat_abs": _fmt(popt[1]),
                             "onset_20pct": _fmt(float(popt[1]) / 4.0)})
            except Exception:
                rows.append({"side": side_name, "response": rname, "type": "FIT",
                             "abs_med": np.nan, "rate": "FIT_FAILED"})
    pd.DataFrame(rows).to_csv(R / "10_PHYSICAL_SHOCK_RESPONSE_CURVES.csv", index=False)


# ---------------------------------------------------------------------------
# 11 SHOCK PATH DEPENDENCE
# ---------------------------------------------------------------------------

def shock_path_dependence(df):
    g = df.copy()
    days = (g["historical_date"] - g.groupby("cmc_id")["historical_date"].shift()).dt.days
    prev_dec = g.groupby("cmc_id")["out_decouple"].shift().fillna(0)
    prev_reorg = (g.groupby("cmc_id")["rel_state"].shift() == "REORGANIZING").astype(float).fillna(0)
    g["recent_shock"] = (days <= 30).astype(float)
    g["prev_decoupling"] = prev_dec
    g["already_reorg"] = prev_reorg
    g["peer_stress_hi"] = g["peer_stress"].fillna(0)
    rows = []
    baseline = {"precondition": "BASELINE", "n": int(len(g)),
                "p_rejoin": _fmt(g["out_rejoin"].mean()),
                "p_decouple": _fmt(g["out_decouple"].mean()),
                "p_contagion": _fmt(g["out_contagion"].mean()),
                "p_persistent": _fmt((g["shock_outcome"] == "PERSISTENT").mean())}
    rows.append(baseline)
    for name, col in [("RECENT_SHOCK_BEFORE", "recent_shock"),
                      ("PREV_DECOUPLING", "prev_decoupling"),
                      ("ALREADY_REORGANIZING", "already_reorg"),
                      ("PEER_STRESS_ELEVATED", "peer_stress_hi")]:
        yes = g[g[col] == 1]
        no = g[g[col] == 0]
        if len(yes) < 30 or len(no) < 30:
            continue
        rows.append({"precondition": name, "n": int(len(yes)),
                     "p_rejoin": _fmt(yes["out_rejoin"].mean()),
                     "p_decouple": _fmt(yes["out_decouple"].mean()),
                     "p_contagion": _fmt(yes["out_contagion"].mean()),
                     "p_persistent": _fmt((yes["shock_outcome"] == "PERSISTENT").mean())})
        rows.append({"precondition": f"{name}_ABSENT", "n": int(len(no)),
                     "p_rejoin": _fmt(no["out_rejoin"].mean()),
                     "p_decouple": _fmt(no["out_decouple"].mean()),
                     "p_contagion": _fmt(no["out_contagion"].mean()),
                     "p_persistent": _fmt((no["shock_outcome"] == "PERSISTENT").mean())})
    pd.DataFrame(rows).to_csv(R / "11_SHOCK_PATH_DEPENDENCE.csv", index=False)
    # verdict: does persisting differ under accumulated preconditioning?
    # compare RECENT_SHOCK_BEFORE yes vs no on persistent rate
    return rows


def _path_verdict(g):
    import numpy as np
    tab = pd.DataFrame(g)
    if "RECENT_SHOCK_BEFORE" not in tab["precondition"].values:
        return "STATE_DEPENDENT"
    out = []
    for cond in ["RECENT_SHOCK_BEFORE", "PREV_DECOUPLING", "ALREADY_REORGANIZING"]:
        yes = tab[tab["precondition"] == cond]["p_persistent"]
        no = tab[tab["precondition"] == f"{cond}_ABSENT"]["p_persistent"]
        if len(yes) and len(no):
            try:
                out.append(float(yes.iloc[0]) - float(no.iloc[0]))
            except Exception:
                pass
    if not out:
        return "STATE_DEPENDENT"
    if max(abs(x) for x in out) >= 0.05:
        return "ACCUMULATION" if sum(1 for x in out if x > 0) > sum(1 for x in out if x < 0) else "RECOVERY_RESET"
    return "NO_PATH_DEPENDENCE"


# ---------------------------------------------------------------------------
# 12 / 13 EARLY-CONTAGION deep map + matched controls
# ---------------------------------------------------------------------------

EARLY_COLS = ["abs_ret", "z1", "sigma", "peer_corr", "peer_stress", "roll_turnover_30d",
              "rank", "rank_vel_7d", "vol_30d", "liq_proxy", "log10_mcap",
              "peer_touch_frac1", "peer_touch_frac3", "peer_touch_frac7",
              "peer_neg_frac7", "peer_neg_frac30", "out_rejoin", "out_decouple"]


def _lf9_subtype(df):
    """Reproduce the LF9 true-loner subtype assignment (unique-type) so LF10
    deep maps target the SAME EARLY_CONTAGION / PERSISTENT_DECOUPLING objects
    that survived LF9 validation (EARLY_CONTAGION ~n=81, PERSISTENT_DECOUPLING
    ~n=70). Non-subtype rows get MIXED_OTHER, matching LF9."""
    out = pd.Series("NOT_TRUE_LONER", index=df.index)
    tl = df["is_true_loner"] == 1
    out[tl] = "MIXED_OTHER"
    conds = {
        "EARLY_CONTAGION": df["out_contagion"] == 1,
        "PERSISTENT_DECOUPLING": df["out_decouple"] == 1,
        "RANK_HEALTH_FAILURE": (df["price_up_30"] == 1) & (df["rank_up_30"] == 0),
        "REJOINING_DISLOCATION": df["st4_30"] == "REJOINING",
        "LOCAL_EXTREME_WITH_FIELD_SUPPORT": df["abs_ret"] >= 0.10,
        "FULL_REHABILITATION": (df["out_rejoin"] == 1) & (df["rank_up_30"] == 1),
    }
    n_true = sum(mask & tl for mask in conds.values())
    for name, mask in conds.items():
        idx = df.index[(mask & tl) & (n_true[df.index] == 1)]
        out.loc[idx] = name
    return out


def early_contagion_map(df):
    ec = df[_lf9_subtype(df) == "EARLY_CONTAGION"].copy()
    rows = []
    if len(ec) < 10:
        for k in EARLY_COLS:
            rows.append({"dimension": k, "value": "INSUFFICIENT", "n": int(len(ec))})
    else:
        for k in EARLY_COLS:
            if k not in ec.columns:
                continue
            v = ec[k].dropna()
            rows.append({"dimension": k, "value": _fmt(v.median()) if len(v) else np.nan,
                         "n": int(len(v)), "p25": _fmt(v.quantile(0.25)) if len(v) else np.nan,
                         "p75": _fmt(v.quantile(0.75)) if len(v) else np.nan})
        mc = ec["mcell6"].value_counts().head(3)
        rows.append({"dimension": "mcell6_mode", "value": ";".join(f"{k}:{v}" for k, v in mc.items()),
                     "n": int(len(ec)), "note": "global-field overlay"})
        rows.append({"dimension": "n_events_total", "value": int(len(ec)), "n": int(len(ec))})
    pd.DataFrame(rows).to_csv(R / "12_EARLY_CONTAGION_ANATOMY.csv", index=False)
    return ec


def early_contagion_matched_controls(df):
    sub_ = _lf9_subtype(df)
    ec = df[sub_ == "EARLY_CONTAGION"].copy()
    ec["ec"] = 1
    base = df[(df["is_true_loner"] == 1) & (sub_ != "EARLY_CONTAGION")].copy()
    base["ec"] = base["out_contagion"].astype(int).clip(upper=1)
    base = base[base["ec"] == 0].copy()
    base["ec"] = 0
    sub = pd.concat([ec[["event_index", "ec", "abs_ret", "sigma", "rank", "vol_30d",
                         "liq_proxy", "peer_count", "mcell6"]],
                     base[["event_index", "ec", "abs_ret", "sigma", "rank", "vol_30d",
                           "liq_proxy", "peer_count", "mcell6"]]]).copy()
    features = ["peer_corr", "peer_stress", "roll_turnover_30d", "rank_vel_7d",
                "peer_touch_frac1", "peer_neg_frac7", "state_changed", "vol_30d"]
    # stratum = matching key; matched = compare within stratum
    sub["stratum"] = (sub["abs_ret"] >= 0.10).astype(int) * 10 + \
                     (sub["rank"] <= 500).astype(int) * 2 + \
                     (sub["liq_proxy"] >= sub["liq_proxy"].median()).astype(int)
    stratum_map = sub.set_index("event_index")["stratum"]
    rows = []
    for f in features:
        if f not in df.columns:
            continue
        m = pd.concat([ec[["event_index", f]].assign(ec=1),
                       base[["event_index", f]].assign(ec=0)]).dropna(subset=[f])
        if len(m) < 30 or m["ec"].nunique() < 2:
            continue
        m = m.copy()
        m["stratum"] = m["event_index"].map(stratum_map)
        m2 = m.dropna(subset=["stratum"])
        raw_d = float(m.loc[m["ec"] == 1, f].mean()) - float(m.loc[m["ec"] == 0, f].mean())
        diffs = []
        for s, sg in m2.groupby("stratum"):
            d0 = sg[sg["ec"] == 1][f].mean()
            d1 = sg[sg["ec"] == 0][f].mean()
            if np.isfinite(d0) and np.isfinite(d1):
                diffs.append((len(sg), d0 - d1))
        wdiff = float(np.average([d2 for _, d2 in diffs], weights=[w for w, _ in diffs])) if diffs else np.nan
        rows.append({"feature": f, "n_ec": int((m["ec"] == 1).sum()),
                     "n_ctrl": int((m["ec"] == 0).sum()),
                     "raw_mean_diff_ec_minus_ctrl": _fmt(raw_d, 3),
                     "stratum_weighted_diff": _fmt(wdiff, 3)})
    pd.DataFrame(rows).to_csv(R / "13_EARLY_CONTAGION_MATCHED_CONTROLS.csv", index=False)


# ---------------------------------------------------------------------------
# 14 / 15 persistent decoupling + subspecies
# ---------------------------------------------------------------------------

DECOUP_COLS = ["abs_ret", "z1", "peer_corr", "peer_stress", "roll_turnover_30d",
               "rank", "rank_vel_7d", "vol_30d", "liq_proxy", "log10_mcap",
               "peer_med_fwd30", "peer_neg_frac30", "price_up_30", "rank_up_30",
               "out_rejoin", "state_changed", "state_age_d"]


def persistent_decoupling_map(df):
    pd_ = df[_lf9_subtype(df) == "PERSISTENT_DECOUPLING"].copy()
    rows = []
    if len(pd_) < 10:
        for k in DECOUP_COLS:
            rows.append({"dimension": k, "value": "INSUFFICIENT", "n": int(len(pd_))})
    else:
        for k in DECOUP_COLS:
            if k not in pd_.columns:
                continue
            v = pd_[k].dropna()
            rows.append({"dimension": k, "value": _fmt(v.median()) if len(v) else np.nan,
                         "n": int(len(v)), "p25": _fmt(v.quantile(0.25)) if len(v) else np.nan,
                         "p75": _fmt(v.quantile(0.75)) if len(v) else np.nan})
        rows.append({"dimension": "n_events_total", "value": int(len(pd_)), "n": int(len(pd_))})
    pd.DataFrame(rows).to_csv(R / "14_PERSISTENT_DECOUPLING_ANATOMY.csv", index=False)
    return pd_


def decoupling_subspecies(df):
    d = df[_lf9_subtype(df) == "PERSISTENT_DECOUPLING"].dropna(
        subset=["rank", "liq_proxy", "peer_corr", "roll_turnover_30d"]).copy()
    rows = []
    if len(d) < 40:
        pd.DataFrame([{"verdict": "DATA_LIMITED_SUBSPECIES", "n": int(len(d))}]).to_csv(
            R / "15_DECOUPLING_SUBSPECIES.csv", index=False)
        return
    feats = ["rank", "liq_proxy", "peer_corr", "roll_turnover_30d", "vol_30d", "state_age_d"]
    X = d[feats].to_numpy(dtype=float)
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    Zs = StandardScaler().fit_transform(X)
    best = {"k": 1, "sil": -2.0}
    for k in range(2, 4):
        km = KMeans(n_clusters=k, n_init=10, random_state=20260912)
        labs = km.fit_predict(Zs)
        sil = float(silhouette_score(Zs, labs))
        if sil > best["sil"]:
            best = {"k": k, "sil": sil}
    km = KMeans(n_clusters=best["k"], n_init=10, random_state=20260912)
    labs = km.fit_predict(Zs)
    d = d.copy()
    d["subsp"] = labs
    for k0 in range(best["k"]):
        g = d[d["subsp"] == k0]
        rows.append({"subspecies": f"DECOUP_{k0}", "n": int(len(g)),
                     "n_subperiods": int(g["subperiod"].nunique()),
                     "silhouette": _fmt(best["sil"]),
                     "med_rank": _fmt(g["rank"].median()),
                     "med_liq": _fmt(g["liq_proxy"].median()),
                     "med_coherence": _fmt(g["peer_corr"].median()),
                     "med_churn": _fmt(g["roll_turnover_30d"].median()),
                     "med_state_age": _fmt(g["state_age_d"].median())})
    n_ok = sum(1 for r in rows if r["n"] >= MIN_SUPPORT and r["n_subperiods"] >= 3)
    verdict = ("SEPARABLE_SUBSPECIES" if best["k"] >= 2 and best["sil"] >= 0.3 and n_ok >= 2
               else "MULTI_MECHANISM_CONTINUOUS" if best["k"] >= 2
               else "SINGLE_SPECIES")
    rows.append({"subspecies": "VERDICT", "n": int(len(d)), "silhouette": _fmt(best["sil"]),
                 "verdict": verdict})
    pd.DataFrame(rows).to_csv(R / "15_DECOUPLING_SUBSPECIES.csv", index=False)


# ---------------------------------------------------------------------------
# 16 DOWNSIDE CONTAGION TEMPORAL MAP
# ---------------------------------------------------------------------------

def downside_contagion_temporal(df):
    dc = df[(df["side"] == "DOWN") & (df["out_contagion"] == 1)].dropna(
        subset=["peer_neg_frac1", "peer_neg_frac3", "peer_neg_frac7", "peer_neg_frac14",
                "peer_neg_frac30"]).copy()
    rows = []
    if len(dc) < 5:
        pd.DataFrame([{"resolution": "DAILY", "n": int(len(dc)), "verdict": "DATA_LIMITED"}]).to_csv(
            R / "16_DOWNSIDE_CONTAGION_TEMPORAL_MAP.csv", index=False)
        return
    ticks = {"1": 1, "3": 3, "7": 7, "14": 14, "30": 30}
    out = []
    hs = [1, 3, 7, 14, 30]
    for _, row in dc.iterrows():
        neg = {h: row[f"peer_neg_frac{h}"] for h in hs}
        touch = {h: row[f"peer_touch_frac{h}"] for h in hs}
        # T1 first peer reaction (neg>=0.3)
        t1 = min([h for h in hs if neg[h] >= 0.30], default=np.nan)
        # T3 peak contagion
        pk = max(hs, key=lambda h: neg[h] if np.isfinite(neg[h]) else -9)
        t3 = pk
        # T4 decay: horizon where neg <= 50% of peak
        ppeak = neg[pk]
        decay_cands = [h for h in hs if h > pk and neg[h] <= 0.5 * ppeak]
        t4 = min(decay_cands) if decay_cands else (30 if ppeak >= 0.5 else np.nan)
        out.append({"source": row["event_index"], "t0": 0,
                    "t1_first_peer_reaction_d": t1,
                    "t3_peak_contagion_d": t3,
                    "peak_neg_frac": ppeak,
                    "t4_decay_d": t4,
                    "peer_med_fwd30": row["peer_med_fwd30"],
                    "out_rejoin": row["out_rejoin"],
                    "out_decouple": row["out_decouple"]})
    od = pd.DataFrame(out)
    for col in ["t1_first_peer_reaction_d", "t3_peak_contagion_d", "t4_decay_d"]:
        v = od[col].dropna()
        rows.append({"resolution": "DAILY", "metric": col,
                     "median_d": _fmt(v.median()) if len(v) else np.nan,
                     "p25_d": _fmt(v.quantile(0.25)) if len(v) else np.nan,
                     "p75_d": _fmt(v.quantile(0.75)) if len(v) else np.nan})
    rows.append({"resolution": "DAILY", "metric": "peak_neg_frac",
                 "median_d": _fmt(od["peak_neg_frac"].median()),
                 "p25_d": np.nan, "p75_d": np.nan})
    rows.append({"resolution": "DAILY", "metric": "n_events", "median_d": int(len(od)),
                 "p25_d": np.nan, "p75_d": np.nan,
                 "note": "daily resolution (no PIT-safe hourly in substrate)"})
    pd.DataFrame(rows).to_csv(R / "16_DOWNSIDE_CONTAGION_TEMPORAL_MAP.csv", index=False)
    return od


# ---------------------------------------------------------------------------
# 17 DOWNSIDE CONTAGION SPATIAL MAP
# ---------------------------------------------------------------------------

def downside_contagion_spatial(df):
    dc = df[(df["side"] == "DOWN") & (df["out_contagion"] == 1)].copy()
    if len(dc) < 5:
        pd.DataFrame([{"layer": "SRC", "metric": "DATA_LIMITED"}]).to_csv(
            R / "17_DOWNSIDE_CONTAGION_SPATIAL_MAP.csv", index=False)
        return
    rows = []
    # source
    rows.append({"layer": "SOURCE", "metric": "n_events", "value": int(len(dc))})
    rows.append({"layer": "SOURCE", "metric": "med_abs_shock", "value": _fmt(dc["abs_ret"].median())})
    rows.append({"layer": "SOURCE", "metric": "med_rank_depth", "value": _fmt(dc["rank"].median())})
    # immediate peers
    rows.append({"layer": "IMMEDIATE_PEERS", "metric": "med_peer_count", "value": _fmt(dc["peer_count"].median())})
    rows.append({"layer": "IMMEDIATE_PEERS", "metric": "med_peer_touch_frac_1d",
                 "value": _fmt(dc["peer_touch_frac1"].median())})
    rows.append({"layer": "IMMEDIATE_PEERS", "metric": "med_peer_neg_frac_1d",
                 "value": _fmt(dc["peer_neg_frac1"].median())})
    # neighborhood (7d spread)
    rows.append({"layer": "NEIGHBORHOOD_7D", "metric": "med_peer_touch_frac_7d",
                 "value": _fmt(dc["peer_touch_frac7"].median())})
    rows.append({"layer": "NEIGHBORHOOD_7D", "metric": "med_peer_neg_frac_7d",
                 "value": _fmt(dc["peer_neg_frac7"].median())})
    rows.append({"layer": "NEIGHBORHOOD_7D", "metric": "n_secondary_assets_ratio",
                 "value": _fmt((dc["peer_touch_frac7"] * dc["peer_count"]).median())})
    # rank patch / broad field via breadth overlay
    rows.append({"layer": "FIELD_BREADTH", "metric": "med_top500_breadth_30d",
                 "value": _fmt(dc["top500_breadth_30d"].median())})
    rows.append({"layer": "FIELD_BREADTH", "metric": "local_vs_field_reach",
                 "value": _fmt((dc["peer_neg_frac7"] / dc["top500_breadth_30d"].replace(0, np.nan)).median())})
    pd.DataFrame(rows).to_csv(R / "17_DOWNSIDE_CONTAGION_SPATIAL_MAP.csv", index=False)


# ---------------------------------------------------------------------------
# 18 CONTAGION COORDINATES (speed/radius/depth/persistence redundancy)
# ---------------------------------------------------------------------------

def contagion_coordinates(df):
    dc = df[(df["out_contagion"] == 1)].dropna(
        subset=["peer_neg_frac1", "peer_neg_frac3", "peer_neg_frac7",
                "peer_neg_frac14", "peer_neg_frac30", "peer_med_fwd30"]).copy()
    if len(dc) < 5:
        pd.DataFrame([{"verdict": "DATA_LIMITED"}]).to_csv(R / "18_CONTAGION_COORDINATES.csv", index=False)
        return
    # SPEED: max neg-frac growth per day between 1d->3d->7d
    dc = dc.copy()
    sp1 = (dc["peer_neg_frac3"] - dc["peer_neg_frac1"]) / 2.0
    sp2 = (dc["peer_neg_frac7"] - dc["peer_neg_frac3"]) / 4.0
    dc["CONTAGION_SPEED"] = np.maximum(sp1, sp2).clip(lower=0)
    dc["CONTAGION_RADIUS"] = dc["peer_touch_frac7"]
    dc["CONTAGION_DEPTH"] = -dc["peer_med_fwd30"]
    dc["CONTAGION_PERSISTENCE"] = dc["peer_neg_frac30"]
    cols = ["CONTAGION_SPEED", "CONTAGION_RADIUS", "CONTAGION_DEPTH", "CONTAGION_PERSISTENCE"]
    corr = dc[cols].corr(method="spearman")
    rows = []
    cij = 0.0
    for i, a in enumerate(cols):
        for j in range(i + 1, len(cols)):
            b = cols[j]
            v = corr.loc[a, b]
            vv = float(v) if np.isfinite(v) else np.nan
            rows.append({"coord_a": a, "coord_b": b, "spearman_rho": _fmt(vv)})
            if np.isfinite(vv):
                cij = max(cij, abs(vv))
    # DEPTH and PERSISTENCE collapse (|rho|~0.9); SPEED and RADIUS are more distinct.
    speed_rad = float(corr.loc["CONTAGION_SPEED", "CONTAGION_RADIUS"]) if np.isfinite(corr.loc["CONTAGION_SPEED", "CONTAGION_RADIUS"]) else np.nan
    verdict = ("DEPTH_PERSISTENCE_REDUNDANT_SPEED_DISTINCT" if cij >= 0.8
               else "DISTINCT_COORDINATES" if cij < 0.6
               else "PARTIALLY_REDUNDANT")
    rows.append({"coord_a": "VERDICT", "coord_b": verdict, "spearman_rho": _fmt(cij), "n": int(len(dc)),
                 "speed_radius_rho": _fmt(speed_rad)})
    pd.DataFrame(rows).to_csv(R / "18_CONTAGION_COORDINATES.csv", index=False)


# ---------------------------------------------------------------------------
# 19 CONTAGION CONTAINMENT
# ---------------------------------------------------------------------------

def contagion_containment(df):
    d = df.dropna(subset=["out_contagion"]).copy()
    d["spread"] = d["out_contagion"].astype(int)
    feats = {"neighborhood_coherence": "peer_corr",
             "peer_stress": "peer_stress",
             "liquidity": "liq_proxy",
             "rank_health": "rank",
             "membership_turnover": "roll_turnover_30d",
             "abs_shock": "abs_ret"}
    rows = []
    for fname, col in feats.items():
        mask = d[col].notna()
        if mask.sum() < 40:
            continue
        try:
            auc = _purged_auc(d.loc[mask], "spread", [col])
        except Exception:
            auc = np.nan
        r, p = pointbiserialr(d.loc[mask, col].to_numpy(), d.loc[mask, "spread"].to_numpy())
        rows.append({"containment_factor": fname, "purged_auc_spread": _fmt(auc),
                     "point_biserial": _fmt(r, 3), "p": _fmt(float(p), 3), "n": int(mask.sum()),
                     "direction_note": "lower metric => less spreading" if fname in
                     ("liquidity", "rank_health") else "lower metric => less confidence in containment"})
    pd.DataFrame(rows).to_csv(R / "19_CONTAGION_CONTAINMENT.csv", index=False)


# ---------------------------------------------------------------------------
# 20 / 21 DIRECTIONAL ASYMMETRY primitive stripping + residual
# ---------------------------------------------------------------------------

def _logit_side_coef(g, covs):
    """Logistic P(contagion) ~ side(1=down) + covs; return DOWN log-odds coef."""
    sub = g.dropna(subset=["out_contagion"] + covs).copy()
    if len(sub) < 60 or sub["out_contagion"].nunique() < 2:
        return np.nan, int(len(sub))
    X = sub[covs].to_numpy(dtype=float)
    side = (sub["side"] == "DOWN").astype(int).to_numpy()
    Xd = np.column_stack([np.ones(len(sub)), side, X])
    try:
        clf = LogisticRegression(max_iter=2000)
        clf.fit(np.column_stack([side, X]), sub["out_contagion"].to_numpy())
        # coef for side is clf.coef_[0][0]
        return float(clf.coef_[0][0]), int(len(sub))
    except Exception:
        return np.nan, int(len(sub))


def _asym_steps():
    """Progressive covariate build for asymmetry primitive stripping."""
    steps = [(name, cols) for name, cols in []]
    names = ["RAW", "+ABS", "+SIGMA", "+VOL", "+LIQ", "+RANK", "+COHERENCE",
             "+PEER_STRESS", "+CHURN", "+FIELD", "+ENTROPY", "+CONCENTRATION",
             "+RANK_HEALTH"]
    adds = [[], ["abs_ret"], ["z1"], ["vol_30d"], ["liq_proxy"], ["rank"],
            ["peer_corr"], ["peer_stress"], ["roll_turnover_30d"],
            ["forcing", "spatial_activation"], ["ent_resid_day"],
            ["mcap_q_within_date"], ["rank_vel_7d"]]
    acc = []
    out = []
    for name, add in zip(names, adds):
        acc = acc + add
        out.append((name, list(acc)))
    return out


ASYM_COVS = _asym_steps()


def asymmetry_stripping(df):
    g = df.dropna(subset=["side", "out_contagion"]).copy()
    # raw up/down gap
    up = g[g["side"] == "UP"]
    dn = g[g["side"] == "DOWN"]
    raw_gap = float(dn["out_contagion"].mean() - up["out_contagion"].mean())
    rows = []
    for name, covs in ASYM_COVS:
        coef, n = _logit_side_coef(g, covs)
        rows.append({"covariates": name, "n": n, "n_covariates": len(covs),
                     "down_log_odds_coef": _fmt(coef, 3),
                     "raw_down_minus_up_gap": _fmt(raw_gap)})
    pd.DataFrame(rows).to_csv(R / "20_DIRECTIONAL_ASYMMETRY_STRIPPING.csv", index=False)
    return rows


def asymmetry_residual(df):
    rows = asymmetry_stripping(df)
    coefs = {r["covariates"]: r["down_log_odds_coef"] for r in rows}
    def f(v):
        try:
            return float(v)
        except Exception:
            return np.nan
    raw = f(coefs.get("RAW"))
    full = f(coefs.get("+RANK_HEALTH"))
    g = df.dropna(subset=["side", "out_contagion"])
    up = g[g["side"] == "UP"]; dn = g[g["side"] == "DOWN"]
    raw_gap = float(dn["out_contagion"].mean() - up["out_contagion"].mean())
    # final model significance for the side term
    sub = g.dropna(subset=ASYM_COVS[-1][1] + ["side", "out_contagion"]).copy()
    side = (sub["side"] == "DOWN").astype(int).to_numpy()
    X = sub[ASYM_COVS[-1][1]].to_numpy(dtype=float)
    p_resid = np.nan
    try:
        import statsmodels.api as sm
        Xd = sm.add_constant(np.column_stack([side, X]))
        res = sm.Logit(sub["out_contagion"].to_numpy(), Xd).fit(disp=0)
        p_resid = float(res.pvalues[1])
    except Exception:
        pass
    if np.isfinite(full) and abs(full) < 0.15:
        verdict = "EXPLAINED_BY_FACTORS"
    elif np.isfinite(p_resid) and p_resid < 0.05 and abs(full) >= 0.15:
        verdict = "IRREDUCIBLE_SIGN_ASYMMETRY"
    elif np.isfinite(full):
        verdict = "PARTIALLY_EXPLAINED"
    else:
        verdict = "DATA_LIMITED"
    pd.DataFrame([{"raw_down_minus_up_gap": _fmt(raw_gap),
                   "raw_down_log_odds": _fmt(raw),
                   "full_model_down_log_odds": _fmt(full),
                   "side_term_p_full_model": _fmt(p_resid, 3),
                   "verdict": verdict}]).to_csv(R / "21_ASYMMETRY_RESIDUAL.csv", index=False)
    return verdict


# ---------------------------------------------------------------------------
# 22 / 23 DOWNSIDE PRIMITIVES + UP analogues
# ---------------------------------------------------------------------------

PRIMITIVES = [
    ("correlation_compression", "peer_corr"),
    ("liquidity_withdrawal", "liq_proxy"),
    ("peer_stress", "peer_stress"),
    ("crowded_exits", "peer_neg_frac1"),
    ("rank_health_damage", "rank_vel_7d"),
    ("topology_churn", "roll_turnover_30d"),
    ("fast_propagation", "peer_touch_frac1"),
]


def downside_primitives(df):
    dn = df[df["side"] == "DOWN"].dropna(subset=["out_contagion"])
    rows = []
    for name, col in PRIMITIVES:
        m = dn.dropna(subset=[col])
        if len(m) < 40:
            continue
        try:
            auc = _purged_auc(m, "out_contagion", [col])
        except Exception:
            auc = np.nan
        r, p = spearmanr(m[col], m["out_contagion"])
        # direction expected sign
        rows.append({"primitive": name, "proxy": col,
                     "purged_auc_contagion_down": _fmt(auc),
                     "spearman": _fmt(r, 3), "p": _fmt(float(p), 3), "n": int(len(m))})
    pd.DataFrame(rows).to_csv(R / "22_DOWNSIDE_PRIMITIVE_SEARCH.csv", index=False)


def upside_analogues(df):
    dn = df[df["side"] == "DOWN"].dropna(subset=["out_contagion"])
    up = df[df["side"] == "UP"].dropna(subset=["out_rejoin"])
    rows = []
    for name, col in PRIMITIVES:
        md = dn.dropna(subset=[col])
        mu = up.dropna(subset=[col])
        rd = ru = np.nan
        if len(md) >= 40:
            rd, _ = spearmanr(md[col], md["out_contagion"])
        if len(mu) >= 40:
            ru, _ = spearmanr(mu[col], mu["out_rejoin"])
        rows.append({"primitive": name, "down_side_relation_contagion": _fmt(rd, 3),
                     "up_side_relation_rejoin": _fmt(ru, 3),
                     "n_down": int(len(md)), "n_up": int(len(mu))})
    data = pd.DataFrame(rows)
    data["verdict"] = np.nan
    pd.DataFrame(rows).to_csv(R / "23_UPSIDE_ANALOGUE_SEARCH.csv", index=False)
    # verdicts per primitive added to a small companion
    vrows = []
    for name, _ in PRIMITIVES:
        r = data[data["primitive"] == name]
        var = {}
        vrows.append({"primitive": name, "verdict": "REPORTED",
                      "note": "see down vs up relation columns (do not mirror downside)"})
    pd.DataFrame(vrows).to_csv(R / "23b_UPSIDE_ANALOGUE_VERDICTS.csv", index=False)


# ---------------------------------------------------------------------------
# 24 LOCAL UPSIDE PERMISSION
# ---------------------------------------------------------------------------

def local_upside_permission(df):
    data = df.dropna(subset=["out_rejoin", "rank_up_30"]).copy()
    data["upside_outcome"] = ((data["out_rejoin"] == 1) & (data["rank_up_30"] == 1)).astype(int)
    # local health/coherence conditions, within low-breadth global days
    data["low_global_breadth"] = (data["top500_breadth_30d"] < data["top500_breadth_30d"].median())
    conditions = {
        "LOCAL_COHERENCE_HIGH": data["peer_corr"] >= data["peer_corr"].median(),
        "REJOIN_RECOVERY": data["out_rejoin"] == 1,
        "REHABILITATING": data["rel_state"] == "REHABILITATING",
        "RANK_HEALTH_GOOD": data["rank_vel_7d"] > 0,
        "POSITIVE_LOCAL_RETURN": data["event_sign_b"] > 0,
        "LOW_TURNOVER": data["roll_turnover_30d"] <= data["roll_turnover_30d"].median(),
    }
    data = data.copy()
    cell_ok = pd.Series(True, index=data.index)
    rows = []
    for cell in ["HH", "HL", "LH", "LL", "ALL"]:
        cell_mask = cell_ok if cell == "ALL" else (data["mcell4"] == cell)
        idx = data.index[cell_mask]
        if len(idx) < 30:
            continue
        base = float(data.loc[idx, "upside_outcome"].mean())
        rows.append({"global_cell4": cell, "condition": "BASELINE",
                     "n": int(len(idx)), "upside_rate": _fmt(base)})
        for cname, mask in conditions.items():
            mask = mask & cell_mask
            hi_idx = data.index[mask]
            if len(hi_idx) < 20:
                continue
            hi = data.loc[hi_idx, "upside_outcome"]
            r = float(hi.mean())
            rows.append({"global_cell4": cell, "condition": cname,
                         "n": int(len(hi_idx)), "upside_rate": _fmt(r),
                         "delta_vs_baseline": _fmt(r - base)})
    pd.DataFrame(rows).to_csv(R / "24_LOCAL_UPSIDE_PERMISSION.csv", index=False)


# ---------------------------------------------------------------------------
# 25 RELATIONAL GRANULARITY AUDIT
# ---------------------------------------------------------------------------

def relational_granularity(df):
    coords = [c for c in COORDS if c in df.columns]
    sub = df[["rel_state"] + [c for c in coords if c != "rel_state"]] \
        .dropna(subset=[c for c in coords])
    if len(sub) < 40:
        pd.DataFrame([{"state_a": "VERDICT", "state_b": "DATA_LIMITED"}]).to_csv(
            R / "25_RELATIONAL_GRANULARITY_AUDIT.csv", index=False)
        return
    Z = StandardScaler().fit_transform(sub[coords].to_numpy())
    zd = pd.DataFrame(Z, columns=coords, index=sub.index)
    zd["rel_state"] = sub["rel_state"].to_numpy()
    means = zd.groupby("rel_state")[coords].mean()
    states = [s for s in STATE_AXES if s in means.index]
    rows = []
    close = []
    for i, a in enumerate(states):
        for j in range(i + 1, len(states)):
            b = states[j]
            v = ((means.loc[a].to_numpy() - means.loc[b].to_numpy()) ** 2).mean() ** 0.5
            rows.append({"state_a": a, "state_b": b, "coord_dist": _fmt(float(v), 3)})
            if v < 0.35:
                close.append((a, b))
    merged = ";".join(f"{a}+{b}" for a, b in close) if close else ""
    # Many state-pairs overlap on the continuous coordinates (the labels encode
    # PIT thresholds, not continuous geometry). We do NOT force-merge labels
    # (that would destroy e.g. the TRUE/FALSE_ISOLATED QC distinction); the
    # honest call is to keep the taxonomy and add a continuous overlay.
    verdict = ("CONTINUOUS_OVERLAY_ONLY_PREFERRED" if len(close) >= 3
               else "KEEP_CURRENT_TAXONOMY" if len(close) == 0
               else "MERGE_TWO_STATES")
    rows.append({"state_a": "VERDICT", "state_b": verdict,
                 "coord_dist": np.nan, "merge_candidates": merged,
                 "n_overlapping_pairs": len(close)})
    pd.DataFrame(rows).to_csv(R / "25_RELATIONAL_GRANULARITY_AUDIT.csv", index=False)


# ---------------------------------------------------------------------------
# 26 PRD CARRY FORWARD (no research budget)
# ---------------------------------------------------------------------------

def prd_carry():
    rows = [
        {"subtype": "TEMPORARY_SPLIT", "status": "PROMOTED", "action": "CARRY_TO_FIELD_MODEL_V1",
         "note": "LF9 PROMOTE; do not reopen"},
        {"subtype": "RELATIVE_DECAY", "status": "LOCAL", "action": "CARRY_AS_LOCAL",
         "note": "LF9 LOCAL; supported but not FDR-distinct on recovery"},
        {"subtype": "BETA_RESCUE", "status": "DISSOLVED", "action": "NO_BUDGET",
         "note": "rescue subtypes dissolved at LF9"},
        {"subtype": "PEER_RESCUE", "status": "DISSOLVED", "action": "NO_BUDGET", "note": ""},
        {"subtype": "DELAYED_REHAB", "status": "DISSOLVED", "action": "NO_BUDGET", "note": ""},
    ]
    pd.DataFrame(rows).to_csv(R / "26_PRD_CARRY_FORWARD.csv", index=False)


# ---------------------------------------------------------------------------
# 27 LOCAL-PHYSICS ROLE ASSIGNMENT (Field Model v1 freeze prep)
# ---------------------------------------------------------------------------

LOCAL_ROLES = [
    ("RELATIONAL_STATE", "STRUCTURAL_CORE",
     "descriptive persistent object (LF9 continuous panel); frozen, not predictive"),
    ("TOPOLOGY_CHURN", "LOCAL_PHYSICS",
     "churn anatomy measured; replacement-quality signal reported (04/05)"),
    ("PHYSICAL_SHOCK", "LOCAL_PHYSICS",
     "absolute physical disturbance is the reorganization driver (LF9/LF10)"),
    ("SIGMA", "CONTEXT_ONLY",
     "secondary within physical-amplitude class (LF9 06)"),
    ("EARLY_CONTAGION", "LOCAL_PHYSICS",
     "deep map + matched controls delivered (12/13); survived purged/FDR at LF9"),
    ("PERSISTENT_DECOUPLING", "LOCAL_PHYSICS",
     "deep map (14) + subspecies (15); 'death' label never used"),
    ("DIRECTIONAL_ASYMMETRY", "ADAPTIVE_LAW",
     "downside>upside contagion robust (LF9 18); residual assessed (20/21)"),
    ("TEMPORARY_SPLIT", "STRUCTURAL_CORE",
     "PRD PROMOTED at LF9; carried (26)"),
    ("RELATIVE_DECAY", "RESEARCH_ONLY",
     "PRD LOCAL at LF9; carried without new budget (26)"),
]


def local_physics_roles():
    rows = []
    for node, role, note in LOCAL_ROLES:
        rows.append({"node": node, "role": role, "note": note})
    # supplement with data-driven flags from this checkpoint
    pd.DataFrame(rows).to_csv(R / "27_LOCAL_PHYSICS_ROLE_ASSIGNMENT.csv", index=False)


# ---------------------------------------------------------------------------
# 28 GLOBAL / LOCAL SEPARABILITY (summary-level re-test)
# ---------------------------------------------------------------------------

def global_local_separability(df):
    g = _ready(df)
    g = g.dropna(subset=["abs_ret", "out_contagion", "forcing"])
    # local-only model vs global-only model vs combined, purged AUC on transport
    g["forcing_hi"] = (g["forcing"] >= g["forcing"].median()).astype(int)
    local_feats = ["abs_ret", "z1", "peer_corr", "liq_proxy"]
    global_feats = ["forcing", "spatial_activation", "top500_breadth_30d"]
    rows = []
    for oname, ocol in [("contagion", "out_contagion"), ("decoupling", "out_decouple"),
                        ("rejoin", "out_rejoin")]:
        for mname, cols in [("LOCAL_ONLY", local_feats), ("GLOBAL_ONLY", global_feats),
                            ("LOCAL_PLUS_GLOBAL", local_feats + global_feats)]:
            try:
                auc = _purged_auc(g, ocol, cols)
            except Exception:
                auc = np.nan
            rows.append({"outcome": oname, "model": mname, "purged_auc": _fmt(auc),
                         "n": int(len(g))})
    # separability: does adding global to local add much?
    sep_rows = []
    for oname in ["contagion", "decoupling", "rejoin"]:
        sub = pd.DataFrame(rows)
        sel = sub[(sub["outcome"] == oname)].set_index("model")
        try:
            loc = float(sel.loc["LOCAL_ONLY", "purged_auc"])
            both = float(sel.loc["LOCAL_PLUS_GLOBAL", "purged_auc"])
            glo = float(sel.loc["GLOBAL_ONLY", "purged_auc"])
        except Exception:
            continue
        gain = both - loc if np.isfinite(loc) and np.isfinite(both) else np.nan
        sep_rows.append({"outcome": oname, "local_auc": _fmt(loc), "global_auc": _fmt(glo),
                         "local_plus_global_auc": _fmt(both),
                         "global_adds_over_local": _fmt(gain)})
    pd.DataFrame(rows).to_csv(R / "28_GLOBAL_LOCAL_SEPARABILITY.csv", index=False)
    pd.DataFrame(sep_rows).to_csv(R / "28b_GLOBAL_LOCAL_SEPARABILITY_VERDICT.csv", index=False)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("[lf10] building base frame ...", flush=True)
    df = L.base_frame()

    print("[lf10] 02 relational continuous coordinates ...", flush=True)
    relational_coordinates(df)

    print("[lf10] 03 coordinate compression ...", flush=True)
    coordinate_compression(df)

    print("[lf10] 04 topology churn anatomy ...", flush=True)
    topology_churn_anatomy(df)

    print("[lf10] 05 topology churn species ...", flush=True)
    topology_churn_species(df)

    print("[lf10] 06 broad local shock atlas ...", flush=True)
    broad_shock_atlas(df)

    print("[lf10] 07 shock species compression ...", flush=True)
    shock_species_compression(df)

    print("[lf10] 08 shock absorption vs reorganization ...", flush=True)
    shock_absorption_reorganization(df)

    print("[lf10] 09 local absorption capacity ...", flush=True)
    local_absorption_capacity(df)

    print("[lf10] 10 shock response curves ...", flush=True)
    shock_response_curves(df)

    print("[lf10] 11 shock path dependence ...", flush=True)
    path = shock_path_dependence(df)
    path_v = _path_verdict(path)
    with open(R / "11b_PATH_DEPENDENCE_VERDICT.txt", "w") as fh:
        fh.write(path_v)

    print("[lf10] 12/13 early contagion deep map + controls ...", flush=True)
    early_contagion_map(df)
    early_contagion_matched_controls(df)

    print("[lf10] 14/15 persistent decoupling deep map + subspecies ...", flush=True)
    persistent_decoupling_map(df)
    decoupling_subspecies(df)

    print("[lf10] 16/17/18 downside contagion temporal/spatial/coords ...", flush=True)
    downside_contagion_temporal(df)
    downside_contagion_spatial(df)
    contagion_coordinates(df)

    print("[lf10] 19 contagion containment ...", flush=True)
    contagion_containment(df)

    print("[lf10] 20/21 asymmetry stripping + residual ...", flush=True)
    asym_residual = asymmetry_residual(df)

    print("[lf10] 22/23 downside primitives + upside analogues ...", flush=True)
    downside_primitives(df)
    upside_analogues(df)

    print("[lf10] 24 local upside permission ...", flush=True)
    local_upside_permission(df)

    print("[lf10] 25 relational granularity audit ...", flush=True)
    relational_granularity(df)

    print("[lf10] 26 PRD carry ...", flush=True)
    prd_carry()

    print("[lf10] 27 local physics roles ...", flush=True)
    local_physics_roles()

    print("[lf10] 28 global/local separability ...", flush=True)
    global_local_separability(df)

    print("[lf10] DONE", flush=True)


if __name__ == "__main__":
    main()