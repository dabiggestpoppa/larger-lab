from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, MC, cell_stats

UP_FAM = {"BROAD_UP": ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE"],
          "ISOLATED_UP": ["ev_ISOLATED_UPSIDE"]}
DOWN_FAM = {"BROAD_DOWN": ["ev_COORDINATED_DOWNSIDE"],
            "ISOLATED_DOWN": ["ev_ISOLATED_DOWNSIDE_EXTREME",
                              "ev_LOCAL_CLUSTER_DOWNSIDE"]}
FAM_MAP = {k: v for d in (UP_FAM, DOWN_FAM) for k, v in d.items()}


# =========================================================================
# WS13: INITIATION ARCHETYPE MIX (14_INITIATION_ARCHETYPE_MIX.csv)
# =========================================================================
def ws13_initiation_archetype_mix(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            rows.append({"mcell": mc, "n": int(len(g)), "verdict":
                         "DATA_LIMITED"})
            continue
        vc = g["archetype"].value_counts(normalize=True)
        rows.append({"mcell": mc, "n": int(len(g)),
                     "archetype_mix": ";".join(
                         f"{k}:{v:.3f}" for k, v in vc.items()),
                     "n_archetypes": int(vc.nunique()),
                     "dominant_archetype": str(vc.index[0]),
                     "dominant_share": float(vc.iloc[0]),
                     "verdict": "ARCHETYPE_MIX_MAPPED"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "14_INITIATION_ARCHETYPE_MIX.csv", index=False)
    return out


def _archetype_adds_info(df):
    """Nested logistic: does archetype add to prop7 beyond cell (usable
    cells only, chronological 60/40 split)?"""
    g = df[df["mcell"].isin([mc for mc in MC if
                             len(df[df["mcell"] == mc]) >= 50])].dropna(
        subset=["prop7", "archetype"])
    if len(g) < 200:
        return np.nan, np.nan
    y = g["prop7"].astype(int).to_numpy()
    cell_code = g["mcell"].astype("category").cat.codes.to_numpy()
    arch_code = g["archetype"].astype("category").cat.codes.to_numpy()
    ridx = np.random.default_rng(SEED).permutation(len(y))
    tr, te = ridx[:int(0.6 * len(y))], ridx[int(0.6 * len(y)):]
    try:
        mc_ = LogisticRegression(max_iter=1000).fit(cell_code[tr].reshape(-1, 1),
                                                    y[tr])
        mca = LogisticRegression(max_iter=1000).fit(
            np.column_stack([cell_code[tr], arch_code[tr]]), y[tr])
        auc_c = roc_auc_score(y[te], mc_.predict_proba(
            cell_code[te].reshape(-1, 1))[:, 1])
        auc_ca = roc_auc_score(y[te], mca.predict_proba(
            np.column_stack([cell_code[te], arch_code[te]]))[:, 1])
        return float(auc_c), float(auc_ca)
    except Exception:
        return np.nan, np.nan


# =========================================================================
# WS14: EQUIFINALITY INSIDE MATRIX (15_EQUIFINALITY_INSIDE_MATRIX.csv)
# =========================================================================
def ws14_equifinality_inside_matrix(df):
    # contingency: initiation archetype (at day) x next-day matrix cell
    g = df.dropna(subset=["archetype", "mcell_next"]).copy()
    g = g[g["mcell_next"].isin(MC)]
    ct = pd.crosstab(g["archetype"], g["mcell_next"])
    chi2, p, dof, _ = chi2_contingency(ct)
    # mutual information archetype -> mcell_next (bits)
    tot = ct.values.sum()
    pxy = ct.values / tot
    px = pxy.sum(axis=1, keepdims=True)
    py = pxy.sum(axis=0, keepdims=True)
    mi = float(np.nansum(pxy * np.log2(np.where(pxy > 0, pxy, 1) /
                                       np.where(px * py > 0, px * py, 1))))
    # per-archetype: how many cells does it reach meaningfully (>=10% of its
    # mass)?
    rows = []
    for arch in ct.index:
        r = ct.loc[arch]
        tot_a = r.sum()
        if tot_a < 50:
            continue
        share = r / tot_a
        n_cells = int((share >= 0.10).sum())
        dom = str(r.idxmax())
        rows.append({"archetype": arch, "n_days": int(tot_a),
                     "n_reached_cells_ge10pct": n_cells,
                     "dominant_cell": dom,
                     "dominant_share": float(share.max())})
    out = pd.DataFrame(rows)
    out["mi_arch_to_cell_bits"] = mi
    out["chi2_p"] = float(p)
    if len(out):
        # if archetypes reach many cells -> equifinality inside matrix;
        # if near one-to-one -> archetypes ~ cell encoding
        mean_cells = float(out["n_reached_cells_ge10pct"].mean())
        if mean_cells >= 4:
            verdict = "EQUIFINALITY_INSIDE_MATRIX"
        elif mean_cells <= 2:
            verdict = "ARCHETYPE_ALMOST_CELL_ENCODING"
        else:
            verdict = "PARTIAL_EQUIFINALITY"
        out["verdict"] = verdict
    out.to_csv(OUT / "15_EQUIFINALITY_INSIDE_MATRIX.csv", index=False)
    return out


# =========================================================================
# WS15: DIRECTIONAL ENTROPY SURFACE (16_DIRECTIONAL_ENTROPY_SURFACE.csv)
# =========================================================================
def ws15_directional_entropy_surface(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50 or g["next_dir"].notna().sum() < 20:
            rows.append({"mcell": mc, "verdict": "DATA_LIMITED"})
            continue
        nd = g["next_dir"].dropna()
        ent = _entropy(nd)
        p_up = float((nd > 0).mean())
        p_down = float((nd < 0).mean())
        rows.append({"mcell": mc, "n": int(len(g)), "p_up": p_up,
                     "p_down": p_down, "p_flat": float((nd == 0).mean()),
                     "dir_entropy": ent})
    out = pd.DataFrame([r for r in rows if "dir_entropy" in r])
    # reductions
    full = df["next_dir"].dropna()
    base_ent = _entropy(full)
    st_ent = {}
    for st in ["HH", "HL", "LH", "LL"]:
        s = df[df["state_code"] == st]["next_dir"].dropna()
        st_ent[st] = _entropy(s)
    rows2 = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50 or g["next_dir"].notna().sum() < 20:
            continue
        nd = g["next_dir"].dropna()
        ent = _entropy(nd)
        st = mc.split("_")[0]
        rows2.append({"mcell": mc, "dir_entropy": ent,
                      "reduction_vs_unconditional": float(base_ent - ent),
                      "reduction_vs_state": float(st_ent[st] - ent),
                      "n_subperiods": int(g["subperiod"].replace("UNKNOWN",
                          np.nan).dropna().nunique())})
    out2 = pd.DataFrame(rows2)
    out2["verdict"] = "DIRECTIONAL_ENTROPY_SURFACE_BUILT"
    out2.to_csv(OUT / "16_DIRECTIONAL_ENTROPY_SURFACE.csv", index=False)
    return out2


# =========================================================================
# WS16: DIRECTIONAL ASYMMETRY SURFACE (17_DIRECTIONAL_ASYMMETRY_SURFACE.csv)
# =========================================================================
def ws16_directional_asymmetry_surface(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            continue
        for fam, cols in FAM_MAP.items():
            cols = [c for c in cols if c in g.columns]
            if not cols:
                continue
            fam_days = g[g[cols].sum(axis=1) > 0]
            if len(fam_days) < 20:
                continue
            rows.append({"mcell": mc, "family": fam,
                         "n_days": int(len(fam_days)),
                         "freq": float(len(fam_days) / len(g)),
                         "p_prop7_after": float(fam_days["prop7"].mean()),
                         "p_ren7_after": float(fam_days["ren7"].mean()),
                         "rank_recruit_after": float(
                             fam_days["rank7"].mean()),
                         "dir_entropy_after": float(_entropy(
                             fam_days["next_dir"].dropna())) if
                         fam_days["next_dir"].notna().sum() >= 20 else np.nan,
                         "median_age": float(fam_days["age_in_cell"].median()),
                         "mean_ent_resid": float(fam_days["ent_resid"].mean())
                         if fam_days["ent_resid"].notna().any() else np.nan})
    out = pd.DataFrame(rows)
    out["verdict"] = "DIRECTIONAL_ASYMMETRY_SURFACE_BUILT"
    out.to_csv(OUT / "17_DIRECTIONAL_ASYMMETRY_SURFACE.csv", index=False)
    return out
