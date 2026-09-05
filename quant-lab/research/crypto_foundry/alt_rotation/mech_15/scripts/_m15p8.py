from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, MC


def _matrix_stats(df):
    """Scalar stats describing matrix structure (higher = more structured)."""
    g = df.dropna(subset=["mcell", "mcell_next"]).copy()
    g = g[g["mcell"].isin(MC) & g["mcell_next"].isin(MC)]
    # 1. propagation differentiation: between-cell variance of prop7
    rows = []
    for mc in MC:
        gg = df[df["mcell"] == mc]
        if len(gg) >= 20:
            rows.append((len(gg), float(gg["prop7"].mean())))
    if len(rows) >= 2:
        tot = sum(w for w, _ in rows)
        mu = sum(w * v for w, v in rows) / tot
        prop_bv = sum(w * (v - mu) ** 2 for w, v in rows) / tot
    else:
        prop_bv = np.nan
    # 2. directional entropy reduction vs unconditional
    base = _entropy(df["next_dir"].dropna())
    ent_red = 0.0
    cnt = 0
    for mc in MC:
        gg = df[df["mcell"] == mc]
        if len(gg) >= 50 and gg["next_dir"].notna().sum() >= 20:
            ent_red += base - _entropy(gg["next_dir"].dropna())
            cnt += 1
    ent_red = ent_red / cnt if cnt else np.nan
    # 3. rank recruitment differentiation
    rows = []
    for mc in MC:
        gg = df[df["mcell"] == mc]
        if len(gg) >= 20:
            rows.append((len(gg), float(gg["rank7"].mean())))
    if len(rows) >= 2:
        tot = sum(w for w, _ in rows)
        mu = sum(w * v for w, v in rows) / tot
        rank_bv = sum(w * (v - mu) ** 2 for w, v in rows) / tot
    else:
        rank_bv = np.nan
    # 4. transition self-concentration
    ct = pd.crosstab(g["mcell"], g["mcell_next"])
    self_share = 0.0
    cnt = 0
    for a in MC:
        if a in ct.index and ct.loc[a].sum() >= 50:
            self_share += ct.loc[a, a] / ct.loc[a].sum() if a in ct.columns \
                else 0.0
            cnt += 1
    self_share = self_share / cnt if cnt else np.nan
    return {"prop_between_var": prop_bv, "dir_entropy_reduction": ent_red,
            "rank_between_var": rank_bv, "transition_self_share": self_share}


# =========================================================================
# WS25: SHUFFLE / LABEL NULL (26_MATRIX_NULL_TEST.csv)
# =========================================================================
def ws25_matrix_null_test(df):
    rng = np.random.default_rng(SEED)
    obs = _matrix_stats(df)
    nulls = {"prop_between_var": [], "dir_entropy_reduction": [],
             "rank_between_var": [], "transition_self_share": []}
    for perm in range(PERM_N):
        d = df.copy()
        mode = perm % 3
        if mode == 0:
            # permute constraint labels within state
            for st in ["HH", "HL", "LH", "LL"]:
                m = d["state_code"] == st
                labs = d.loc[m, "constraint"].to_numpy()
                d.loc[m, "constraint"] = rng.permutation(labs)
            d["mcell"] = d["state_code"] + "_" + d["constraint"]
        elif mode == 1:
            # permute state labels within constraint
            for cc in ["HA_HE", "HA_LE", "LA_HE", "LA_LE"]:
                m = d["constraint"] == cc
                labs = d.loc[m, "state_code"].to_numpy()
                d.loc[m, "state_code"] = rng.permutation(labs)
            d["mcell"] = d["state_code"] + "_" + d["constraint"]
        else:
            # full matrix labels (mcell re-pairing) - do NOT rebuild
            labs = d["mcell"].to_numpy()
            d["mcell"] = rng.permutation(labs)
        d["mcell_next"] = d["mcell"].shift(-1)
        s = _matrix_stats(d)
        for k in nulls:
            if s[k] == s[k]:
                nulls[k].append(s[k])
    rows = []
    for k, label in [("prop_between_var", "propagation_differentiation"),
                     ("dir_entropy_reduction", "directional_entropy"),
                     ("rank_between_var", "rank_recruitment"),
                     ("transition_self_share", "transition_structure")]:
        o = obs[k]
        n = np.asarray(nulls[k])
        if np.isnan(o) or len(n) < 30:
            rows.append({"statistic": label, "observed": o, "null_mean":
                         np.nan, "null_sd": np.nan, "z": np.nan,
                         "p_perm": np.nan, "verdict": "DATA_LIMITED"})
            continue
        # one-sided: is observed ABOVE null? (+1 pseudo-count convention)
        p = float((np.sum(n >= o) + 1) / (len(n) + 1))
        z = float((o - n.mean()) / (n.std() + 1e-12))
        rows.append({"statistic": label, "observed": o,
                     "null_mean": float(n.mean()), "null_sd": float(n.std()),
                     "z": z, "p_perm": p,
                     "verdict": "REAL_BEATS_NULL" if p <= 0.05 else
                     "NULL_COMPATIBLE"})
    out = pd.DataFrame(rows)
    n_real = int((out["verdict"] == "REAL_BEATS_NULL").sum())
    out["matrix_verdict"] = ("MATRIX_SURVIVES_FALSIFICATION"
                             if n_real >= 3 else
                             "MATRIX_DECORATIVE" if n_real <= 1 else
                             "MATRIX_PARTIALLY_STRUCTURED")
    out.to_csv(OUT / "26_MATRIX_NULL_TEST.csv", index=False)
    return out


# =========================================================================
# WS26: HELD-OUT STABILITY (27_HELDOUT_STABILITY.csv)
# =========================================================================
def _cell_order_profile(df):
    """Rank of cells by prop7 and by dir_entropy (for stability comparison)."""
    p = {}
    e = {}
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) >= 30:
            p[mc] = float(g["prop7"].mean())
            nd = g["next_dir"].dropna()
            if len(nd) >= 20:
                e[mc] = _entropy(nd)
    return p, e


def _rank_corr(p1, p2):
    ks = [k for k in p1 if k in p2]
    if len(ks) < 3:
        return np.nan
    a = np.array([p1[k] for k in ks])
    b = np.array([p2[k] for k in ks])
    return float(spearmanr(a, b)[0])


def ws26_heldout_stability(df):
    df = df.sort_values("d").reset_index(drop=True)
    n = len(df)
    cut = int(0.8 * n)
    early, late = df.iloc[:cut], df.iloc[cut:]
    p_early, e_early = _cell_order_profile(early)
    p_late, e_late = _cell_order_profile(late)
    rho_prop_chrono = _rank_corr(p_early, p_late)
    rho_ent_chrono = _rank_corr(e_early, e_late)
    # leave-one-subperiod-out: prop7 order correlation against full-sample
    p_full, e_full = _cell_order_profile(df)
    loso_rhos = []
    for sp, _ in _subperiod_split(df):
        rest = df[df["subperiod"] != sp]
        p_rest, _ = _cell_order_profile(rest)
        loso_rhos.append(_rank_corr(p_full, p_rest))
    loso_rhos = [r for r in loso_rhos if r == r]
    rho_prop_loso = float(np.mean(loso_rhos)) if loso_rhos else np.nan
    # early vs late sample (first vs second half of the FULL period)
    half = n // 2
    first_half, second_half = df.iloc[:half], df.iloc[half:]
    p_first, _ = _cell_order_profile(first_half)
    p_second, _ = _cell_order_profile(second_half)
    rho_prop_halves = _rank_corr(p_first, p_second)
    out = pd.DataFrame([{
        "test": "chronological_80_20", "rho_prop_order": rho_prop_chrono,
        "rho_dir_entropy_order": rho_ent_chrono,
        "n_early": int(len(early)), "n_late": int(len(late))},
        {"test": "leave_one_subperiod_out",
         "rho_prop_order": rho_prop_loso, "n_folds": len(loso_rhos)},
        {"test": "early_vs_late_half", "rho_prop_order": rho_prop_halves,
         "n_early": half, "n_late": n - half}])
    rhos = [r for r in out["rho_prop_order"] if r == r]
    if rhos and float(np.nanmean(rhos)) >= 0.7:
        verdict = "STABLE_MATRIX"
    elif rhos and float(np.nanmean(rhos)) >= 0.4:
        verdict = "PARTIAL_MATRIX"
    elif rhos:
        verdict = "LOCAL_MATRIX"
    else:
        verdict = "NO_STABLE_MATRIX"
    out["verdict"] = verdict
    out.to_csv(OUT / "27_HELDOUT_STABILITY.csv", index=False)
    return out
