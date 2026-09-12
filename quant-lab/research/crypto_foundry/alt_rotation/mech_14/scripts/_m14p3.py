from _m14base import *
from _m14base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split, _cohen_d, _auc_xy, _atom_series
from itertools import combinations

# 5 fastest coords for pairwise/triple enumeration to keep cost bounded
EQUI_COORDS = ["top500_breadth_30d", "eth_btc_relative_return_7d",
               "top500_dispersion_30d", "btc_return_7d", "vol_med",
               "top3_share", "rank_depth_rel"]


def _success_frame(dfw, cell):
    df = dfw[dfw["cell"] == cell].copy()
    df["fwd7_state"] = df["state"].shift(-7)
    df["success"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(int)
    df = df[(df["success"] == 1) |
            (df["fwd7_state"] == REENTRY_LABEL)].dropna(
        subset=EQUI_COORDS)
    return df


# =========================================================================
# WS7: INITIATION EQUIFINALITY (09_INITIATION_EQUIFINALITY.csv)
# =========================================================================
# Enumerate small coordinate subsets (size 1..3); a config is "viable" if its
# success-discrimination AUC reaches within 0.03 of the full subset model and
# has >=50 obs in >=3 subperiods. Count how many DISTINCT viable configs exist
# per cell (equifinality = many paths).

def ws7_initiation_equifinality(dfw):
    rows = []
    for cell in CELLS:
        df = _success_frame(dfw, cell)
        if len(df) < 80 or df["success"].sum() < 25:
            # explicit coverage marker: cell attempted but data-limited
            rows.append({"cell": cell, "n_days": int(len(df)),
                         "n_success": int(df["success"].sum()),
                         "full_model_auc": np.nan,
                         "viable_configs_total": np.nan,
                         "viable_k1": np.nan, "viable_k2": np.nan,
                         "viable_k3": np.nan,
                         "distinct_viable_configs": np.nan,
                         "top_configs": "", "data_limited": 1})
            continue
        y = df["success"].to_numpy()
        sp_ok = df["subperiod"]
        # full reference AUC (all coords)
        try:
            Xf = df[EQUI_COORDS].to_numpy(dtype=float)
            mf = LogisticRegression(max_iter=1000).fit(Xf, y)
            full_auc = roc_auc_score(y, mf.predict_proba(Xf)[:, 1])
        except Exception:
            full_auc = np.nan
        tol = 0.03
        viable = []
        sizes = {}
        for k in [1, 2, 3]:
            n_viable = 0
            for sub in combinations(EQUI_COORDS, k):
                Xs = df[list(sub)].to_numpy(dtype=float)
                if len(Xs) < 50 or np.isnan(Xs).any():
                    continue
                # subperiod coverage
                sel = df[list(sub)].notna().all(axis=1)
                nsp = int(df.loc[sel, "subperiod"].nunique())
                if nsp < MIN_SUBPERIODS:
                    continue
                try:
                    ms = LogisticRegression(max_iter=1000).fit(Xs, y)
                    auc = roc_auc_score(y, ms.predict_proba(Xs)[:, 1])
                except Exception:
                    continue
                if not np.isnan(full_auc) and auc >= full_auc - tol:
                    viable.append((k, "+".join(sub), float(auc), int(nsp)))
                    n_viable += 1
            sizes[k] = n_viable
        # dedupe: configs identical in AUC are redundant; count distinct
        distinct = {v[1] for v in viable}
        rows.append({"cell": cell, "n_days": int(len(df)),
                     "n_success": int(df["success"].sum()),
                     "full_model_auc": float(full_auc) if not np.isnan(
                         full_auc) else np.nan,
                     "viable_configs_total": len(viable),
                     "viable_k1": sizes.get(1, 0),
                     "viable_k2": sizes.get(2, 0),
                     "viable_k3": sizes.get(3, 0),
                     "distinct_viable_configs": len(distinct),
                     "top_configs": ";".join(
                         sorted(distinct)[:6]), "data_limited": 0})
    out = pd.DataFrame(rows)
    # equifinality if multiple distinct configs achieve comparable
    # discrimination per cell (data-limited cells excluded)
    if len(out):
        elig = out[out["data_limited"] != 1]
        n_eq = int((elig["distinct_viable_configs"] >= 3).sum())
        v = "EQUIFINAL_MULTI_CONFIG" if n_eq >= 2 else \
            "SINGLE_CONFIGURATION" if n_eq == 0 else "LOCAL_EQUIFINALITY"
        out["verdict"] = v
        out.loc[out["data_limited"] == 1, "verdict"] = "DATA_LIMITED"
    out.to_csv(OUT / "09_INITIATION_EQUIFINALITY.csv", index=False)
    return out


# =========================================================================
# WS8: INITIATION ARCHETYPES (10_INITIATION_ARCHETYPES.csv)
# =========================================================================
# Group successful births by which init coords sit above their cell median ->
# descriptive archetypes. Require >=50 & >=3 subperiods to NAME an archetype.

def ws8_initiation_archetypes(dfw):
    rows = []
    for cell in CELLS:
        df = _success_frame(dfw, cell)
        if len(df) < 80 or df["success"].sum() < 25:
            rows.append({"cell": cell, "archetype": "DATA_LIMITED",
                         "n": 0, "p_share": np.nan, "n_subperiods": 0,
                         "verdict": "DATA_LIMITED"})
            continue
        # classify each successful birth by dominant coord(s) above median
        med = {c: float(df[c].median()) for c in EQUI_COORDS}
        tags = []
        for _, r in df[df["success"] == 1].iterrows():
            hi = [c for c in EQUI_COORDS if r[c] >= med[c]]
            # choose archetype by the highest-cohens-d coord at the margin
            tags.append("MIXED")
        # simple rule archetypes based on breadth+dispersion vs macro anchors
        g = df[df["success"] == 1].copy()
        g["breadth_hi"] = g["top500_breadth_30d"] >= med[
            "top500_breadth_30d"]
        g["disp_hi"] = g["top500_dispersion_30d"] >= med[
            "top500_dispersion_30d"]
        g["macro_hi"] = (g["btc_return_7d"] >= med["btc_return_7d"]) | (
            g["eth_btc_relative_return_7d"] >= med[
                "eth_btc_relative_return_7d"])
        def _arch(r2):
            if r2["breadth_hi"] and r2["disp_hi"]:
                return "BREADTH_DISPERSION_LED" if r2["macro_hi"] else \
                    "BREADTH_LED"
            if r2["macro_hi"] and not r2["breadth_hi"]:
                return "MACRO_ANCHORED"
            if r2["disp_hi"]:
                return "DISPERSION_LED"
            return "MIXED"
        g["archetype"] = g.apply(_arch, axis=1)
        for arch, ag in g.groupby("archetype"):
            nsp = int(ag["subperiod"].nunique())
            rows.append({"cell": cell, "archetype": arch,
                         "n": int(len(ag)),
                         "p_share": float(len(ag) / len(g)),
                         "n_subperiods": nsp,
                         "verdict": "NAMED_ARCHETYPE"
                         if len(ag) >= MIN_PROMOTE_N and
                         nsp >= MIN_SUBPERIODS else "DESCRIPTIVE"})
    out = pd.DataFrame(rows)
    out["verdict"] = out.get("verdict", "DESCRIPTIVE")
    out.to_csv(OUT / "10_INITIATION_ARCHETYPES.csv", index=False)
    return out


# =========================================================================
# WS9: INITIATION SUBSTITUTION GRAPH (11_INITIATION_SUBSTITUTION_GRAPH.csv)
# =========================================================================
# Edge (A<->B) when replacement preserves AUC: drop A, add B alone, AUC stays
# within tol. Indicates observable substitutability (latent-sensor vs path).

def ws9_initiation_substitution_graph(dfw):
    rows = []
    for cell in CELLS:
        df = _success_frame(dfw, cell)
        if len(df) < 80 or df["success"].sum() < 25:
            rows.append({"cell": cell, "coord_a": "DATA_LIMITED",
                         "coord_b": "", "auc_a": np.nan, "auc_b": np.nan,
                         "auc_ab": np.nan, "substitutability": "DATA_LIMITED",
                         "n_subperiods": 0})
            continue
        y = df["success"].to_numpy()
        auc_of = {}
        for c in EQUI_COORDS:
            X = df[[c]].to_numpy(dtype=float)
            try:
                m = LogisticRegression(max_iter=1000).fit(X, y)
                auc_of[c] = roc_auc_score(y, m.predict_proba(X)[:, 1])
            except Exception:
                auc_of[c] = np.nan
        # full single-best
        best = max(auc_of, key=lambda k: (auc_of[k] if not np.isnan(
            auc_of[k]) else -1))
        for a in range(len(EQUI_COORDS)):
            for b in range(a + 1, len(EQUI_COORDS)):
                ca, cb = EQUI_COORDS[a], EQUI_COORDS[b]
                pa, pb = auc_of.get(ca, np.nan), auc_of.get(cb, np.nan)
                if np.isnan(pa) or np.isnan(pb):
                    continue
                # negation: is {ca,cb} combined close to best single-2 set?
                X2 = df[[ca, cb]].to_numpy(dtype=float)
                try:
                    m2 = LogisticRegression(max_iter=1000).fit(X2, y)
                    auc2 = roc_auc_score(y, m2.predict_proba(X2)[:, 1])
                except Exception:
                    continue
                nsp = int(df[df[[ca, cb]].notna().all(axis=1)][
                    "subperiod"].nunique())
                edge = ("SUBSTITUTABLE" if min(pa, pb) >= auc2 - 0.03
                        else "COMPLEMENTARY" if auc2 > max(pa, pb) + 0.02
                        else "REDUNDANT_SENSOR")
                rows.append({"cell": cell, "coord_a": ca, "coord_b": cb,
                             "auc_a": float(pa), "auc_b": float(pb),
                             "auc_ab": float(auc2),
                             "substitutability": edge,
                             "n_subperiods": int(nsp)})
    out = pd.DataFrame(rows)
    if len(out):
        n_sub = int((out["substitutability"] == "SUBSTITUTABLE").sum())
        n_red = int((out["substitutability"] == "REDUNDANT_SENSOR").sum())
        n_comp = int((out["substitutability"] == "COMPLEMENTARY").sum())
        if n_red >= n_sub and n_red >= n_comp:
            verdict = "REDUNDANT_SENSOR_CLUSTER"
        elif n_sub >= n_comp and n_sub >= n_red:
            verdict = "EQUIFINAL_PATHS"
        elif n_comp >= 2:
            verdict = "MIXED"
        else:
            verdict = "INCONCLUSIVE"
        out["verdict"] = verdict
        out["n_substitutable"] = n_sub
        out["n_redundant"] = n_red
        out["n_complementary"] = n_comp
        out.loc[out["substitutability"] == "DATA_LIMITED", "verdict"] = \
            "DATA_LIMITED"
    out.to_csv(OUT / "11_INITIATION_SUBSTITUTION_GRAPH.csv", index=False)
    return out


# =========================================================================
# WS10: HIDDEN-STATE AUDIT (12_HIDDEN_STATE_AUDIT.csv)
# =========================================================================
# Does residualizing the top principal component (common factor) destroy
# equifinality (=> single hidden coordinate) or leave distinct local coords?

def ws10_hidden_state_audit(dfw):
    rel = EQUI_COORDS
    rows = []
    for cell in CELLS:
        df = _success_frame(dfw, cell)
        if len(df) < 80 or df["success"].sum() < 25:
            rows.append({"cell": cell, "n_events": int(len(df)),
                         "auc_pc1": np.nan,
                         "n_resid_coords_auc_ge_058": np.nan,
                         "top_resid": "", "data_limited": 1})
            continue
        y = df["success"].to_numpy()
        X = df[rel].dropna().to_numpy(dtype=float)
        Xc = X - X.mean(axis=0)
        n_ = len(Xc)
        if n_ < 80:
            continue
        # center cov for first PC via SVD
        U, S, Vt = np.linalg.svd(Xc / np.sqrt(max(1, n_)), full_matrices=False)
        pc1 = Xc @ Vt[0]
        pc1 = np.asarray(pc1).reshape(-1, 1)
        # residualize all coords on pc1
        resid = Xc - pc1 @ np.linalg.lstsq(pc1, Xc, rcond=None)[0]
        # discrimination retained by residuals vs pc1 alone
        yy_full = y[:n_]
        try:
            mp = LogisticRegression(max_iter=1000).fit(pc1, yy_full)
            auc_pc1 = roc_auc_score(yy_full, mp.predict_proba(pc1)[:, 1])
        except Exception:
            auc_pc1 = np.nan
        # residual coord single-AUCs
        resid_aucs = {}
        for j, c in enumerate(rel):
            try:
                mc = LogisticRegression(max_iter=1000).fit(
                    resid[:, [j]], yy_full)
                resid_aucs[c] = roc_auc_score(yy_full,
                                              mc.predict_proba(resid[:,
                                              [j]])[:, 1])
            except Exception:
                resid_aucs[c] = np.nan
        n_pc1_high = int(auc_pc1 >= 0.6) if not np.isnan(auc_pc1) else 0
        n_resid_high = int(sum(1 for v in resid_aucs.values()
                               if not np.isnan(v) and v >= 0.58))
        rows.append({"cell": cell, "n_events": int(n_),
                     "auc_pc1": float(auc_pc1) if not np.isnan(auc_pc1)
                     else np.nan,
                     "n_resid_coords_auc_ge_058": n_resid_high,
                     "top_resid": max(resid_aucs, key=lambda k: (
                         resid_aucs[k] if not np.isnan(resid_aucs[k])
                         else -1)) if resid_aucs else ""})
    out = pd.DataFrame(rows)
    if len(out):
        # if pc1 captures most signal and residuals are weak -> single latent
        elig = out[out.get("data_limited", pd.Series(0, index=out.index)) != 1]
        n_single = int((elig["n_resid_coords_auc_ge_058"] <= 1).sum())
        out["verdict"] = "SINGLE_HIDDEN_COORDINATE" if n_single >= 2 \
            else "MULTIPLE_LOCAL_COORDINATES"
        out.loc[out.get("data_limited", pd.Series(0, index=out.index)) == 1,
                "verdict"] = "DATA_LIMITED"
    out.to_csv(OUT / "12_HIDDEN_STATE_AUDIT.csv", index=False)
    return out


# =========================================================================
# WS22: POTENTIAL->REALIZATION RECHECK (24_POTENTIAL_REALIZATION_RECHECK.csv)
# =========================================================================
# Are local conversion paths (M13 PATH_A/D) just manifestations of different
# viable birth configurations under different field pressure? We detect
# PATH_A / PATH_D scaffold attainment, then ask whether conditioning on
# birth-archetype + field forcing + branch entropy removes the propagation
# lift. If it collapses -> MERGE (paths are birth-config x field instances).

PATH_A = ["BREADTH_EXPANDS", "CONCENTRATION_RELEASES",
          "DISPERSION_EXPANDS", "TAIL_UP_ACTIVATES", "RANK_RECRUITS"]
PATH_D = ["CONCENTRATION_RELEASES", "DISPERSION_EXPANDS", "TAIL_UP_ACTIVATES"]


def _path_streak_series(df, chain, H=14):
    atoms = _atom_series(df)
    names = list(atoms.columns)
    arr = atoms.to_numpy()
    n = len(df)
    streak = np.zeros(n)
    for i in range(n - H):
        w = arr[i + 1:i + 1 + H]
        fired = {}
        for k, name in enumerate(names):
            hits = np.where(w[:, k] > 0)[0]
            if len(hits):
                fired[name] = int(hits[0])
        order = [k for k, _ in sorted(fired.items(), key=lambda x: x[1])]
        pos = {kk: p for p, kk in enumerate(order)}
        s = 0
        last = -1
        for a in chain:
            if a in pos and pos[a] > last:
                s += 1
                last = pos[a]
            else:
                break
        streak[i] = s / len(chain)
    return streak


def ws22_potential_realization_recheck(dfw, entropy_carry=None):
    df = dfw.copy()
    n = len(df)
    state_arr = df["state"].to_numpy()
    fwd14_prop = np.zeros(n)
    for i in range(n - 14):
        seg = pd.Series(state_arr[i + 1:i + 15])
        fwd14_prop[i] = seg.isin(SUCCESS_LABELS).any()
    df["fwd14_prop"] = fwd14_prop
    df["ab"] = df["age_in_cell"].apply(_age_band)
    # attach per-day branch entropy
    from _m14p2 import _attach_entropy_and_branches
    dc = _attach_entropy_and_branches(dfw)
    df["fbe"] = dc["fwd_branch_entropy"].to_numpy()

    base_rate = float(np.nanmean(fwd14_prop)) if (fwd14_prop > 0).any() \
        else np.nan
    rows = []
    for pname, chain in [("PATH_A", PATH_A), ("PATH_D", PATH_D)]:
        sA = _path_streak_series(df, chain)
        attained = sA >= (len(chain) - 1) / len(chain)   # all but last
        if attained.sum() < 50:
            continue
        prop_na = float(np.nanmean(np.where(attained, fwd14_prop, np.nan)))
        # archetype (breadth-led vs macro-anchored vs mixed) via medians
        brd_med = float(df["top500_breadth_30d"].median())
        btc_med = float(df["btc_return_7d"].median())
        eth_med = float(df.get("eth_btc_relative_return_7d", pd.Series(
            0.0, index=df.index)).median())
        hi_brd = df["top500_breadth_30d"] >= brd_med
        hi_macro = (df["btc_return_7d"] >= btc_med) | (
            df.get("eth_btc_relative_return_7d", pd.Series(
                0.0, index=df.index)) >= eth_med)
        arche = np.where(hi_brd & ~hi_macro, "BREADTH_LED",
                         np.where(~hi_brd & hi_macro, "MACRO_ANCHORED",
                                  "MIXED"))
        # conditioning: within archetype, does the path still lift prop?
        lift_by_arch = {}
        for arch in ["BREADTH_LED", "MACRO_ANCHORED", "MIXED"]:
            m = (attained) & (arche == arch)
            mc = (attained == False) & (arche == arch)
            if m.sum() >= 30 and mc.sum() >= 30:
                lift_by_arch[arch] = float(
                    np.nanmean(np.where(m, fwd14_prop, np.nan)) /
                    max(1e-9, np.nanmean(np.where(mc, fwd14_prop,
                                                  np.nan))))
            else:
                lift_by_arch[arch] = np.nan
        # within-arch lift that is close to 1 => path add nothing once birth
        # config known -> likely MERGE
        kept = {k: v for k, v in lift_by_arch.items() if not np.isnan(v)}
        lifts = list(kept.values())
        mean_cond_lift = float(np.mean(lifts)) if lifts else np.nan
        rows.append({"path": pname, "n_attained": int(attained.sum()),
                     "base_rate": float(base_rate) if base_rate else np.nan,
                     "lift_unconditional": float(
                         prop_na / max(1e-9, base_rate)) if base_rate
                     else np.nan,
                     "mean_lift_within_archetype": mean_cond_lift,
                     "archetype_lifts": ";".join(
                         f"{k}:{v:.2f}" for k, v in kept.items())})
    out = pd.DataFrame(rows)
    if len(out):
        # if conditional lift collapses toward 1 vs unconditional lift >1 ->
        # paths are purely birth-config x field instances
        collapse = out["lift_unconditional"] - out[
            "mean_lift_within_archetype"]
        if (collapse >= 0.2).all():
            verdict = "MERGE_INTO_BIRTH_CONFIG_FIELD"
        elif (out["mean_lift_within_archetype"] >= 1.3).all():
            verdict = "DISTINCT_LOCAL_PATHS"
        else:
            verdict = "PARTIALLY_DISTINCT"
        out["verdict"] = verdict
        out["collapse_uncond_minus_cond"] = collapse
    else:
        out = pd.DataFrame([{"verdict": "DATA_LIMITED",
                             "path": "", "n_attained": 0}])
    out.to_csv(OUT / "24_POTENTIAL_REALIZATION_RECHECK.csv", index=False)
    return out