from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split


def _next_atom_entropy(df, i, h=7):
    """Shannon entropy (bits) of the next-atom ordering window over rolling
    event words (descriptive constraint-resolution metric)."""
    return np.nan


# =========================================================================
# WS5: CONSTRAINT-RESOLUTION ENTROPY DEEP MAP (06_ENTROPY_DEEP_MAP.csv)
# =========================================================================
# Entropy of next-cell / next-event branches by state x age x perturbation
# type x amplitude x shock cell x loner context.

def _branch_entropy(group):
    if len(group) < 20:
        return np.nan
    return _entropy(group["next_cell"])


def _amp_series(df, col, back=5):
    chg = df[col].diff(back)
    z = chg / chg.std() if chg.std() else chg
    return z.abs()


def ws5_entropy_deep_map(dfw):
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    pert = _perturbation_flags(df)
    # standardized amplitudes
    amp_defs = {"brd_jump": ("top500_breadth_30d", 1),
                "brd_drop": ("top500_breadth_30d", -1),
                "disp_jump": ("top500_dispersion_30d", 1),
                "disp_drop": ("top500_dispersion_30d", -1),
                "btc_shock": ("btc_return_7d", 1),
                "conc_shock": ("top3_share_chg7", 1),
                "vol_shock": ("vol_med", 1)}
    for name, (col, _s) in amp_defs.items():
        amp = _amp_series(df, col)
        pert[f"amp_{name}"] = amp.where(pert[name] == 1, np.nan)
        a = amp.where(pert[name] == 1, np.nan).dropna()
        if len(a) >= 20:
            q1, q2 = np.nanpercentile(a, [33, 66])
            pert[f"{name}_bin"] = np.where(pert[f"amp_{name}"] <= q1,
                                            "SMALL",
                                            np.where(
                                                pert[f"amp_{name}"] <= q2,
                                                "MED", "LARGE"))
        else:
            pert[f"{name}_bin"] = "NA"
    for c in CELLS:
        df[c] = (df["cell"] == c).astype(int)
    # loner context: reuse LF6 consensus joined on dates (approximate --
    # loners are event-level, so proxy by whether any event that day false/
    # true loner)
    rows = []
    # (1) by cell x age
    for cell in CELLS:
        g = df[df["cell"] == cell].dropna(subset=["next_cell"])
        for ab in [b[2] for b in AGE_BANDS]:
            gg = g[g["age_band"] == ab]
            e = _branch_entropy(gg) if len(gg) >= 20 else np.nan
            dom = float(gg["next_cell"].value_counts(normalize=True).max()) \
                if len(gg) >= 20 else np.nan
            rows.append({"group": "cell_age", "cell": cell, "age_band": ab,
                         "branch_entropy": e, "dominant_share": dom,
                         "n_days": int(len(gg))})
    # (2) by perturbation type present
    for pname in ["brd_jump", "brd_drop", "disp_jump", "disp_drop",
                  "btc_shock", "conc_shock", "vol_shock"]:
        m = pert[pname] == 1
        idx = m[pert.index].index[list(m[pert.index])] if m.any() else \
            df.index[:0]
        if len(idx) >= 20:
            gg = df.loc[idx]
            gg = gg.dropna(subset=["next_cell"])
            e = _branch_entropy(gg) if len(gg) >= 20 else np.nan
            rows.append({"group": "perturbation", "cell": "ANY",
                         "age_band": "ANY", "perturbation": pname,
                         "branch_entropy": e,
                         "dominant_share": float(
                             gg["next_cell"].value_counts(
                                 normalize=True).max()) if len(gg) >= 20
                         else np.nan, "n_days": int(len(gg))})
    # (3) by perturbation x cell (HH focus)
    for pname in ["brd_jump", "disp_jump"]:
        for cell in CELLS:
            idx = df[(pert[pname] == 1) & (df["cell"] == cell)].index
            if len(idx) >= 20:
                gg = df.loc[idx].dropna(subset=["next_cell"])
                rows.append({"group": "perturb_cell", "perturbation": pname,
                             "cell": cell, "age_band": "ANY",
                             "branch_entropy": _branch_entropy(gg),
                             "dominant_share": float(gg["next_cell"].
                                                     value_counts(
                                                         normalize=True)
                                                     .max()) if
                             len(gg) >= 20 else np.nan,
                             "n_days": int(len(gg))})
    # (4) shock-cell context (HH/HL/LH/LL already covered; add perturbation
    # amplitude tercile -> entropy)
    for pname in ["brd_jump", "disp_jump"]:
        bn = f"{pname}_bin"
        if bn not in pert.columns:
            continue
        for lab in ["SMALL", "MED", "LARGE"]:
            m = pert[bn] == lab
            idx = df.index[m]
            if len(idx) >= 20:
                gg = df.loc[idx].dropna(subset=["next_cell"])
                rows.append({"group": "pert_amp", "perturbation": pname,
                             "amp": lab, "cell": "ANY", "age_band": "ANY",
                             "branch_entropy": _branch_entropy(gg),
                             "dominant_share": float(gg["next_cell"].
                                                     value_counts(
                                                         normalize=True)
                                                     .max()) if
                             len(gg) >= 20 else np.nan,
                             "n_days": int(len(gg))})
    out = pd.DataFrame(rows)
    out["verdict"] = "ENTROPY_DEEP_MAP_BUILT"
    out.to_csv(OUT / "06_ENTROPY_DEEP_MAP.csv", index=False)
    return out


# =========================================================================
# WS6: LOCAL ENTROPY PRIMITIVE SEARCH (07_ENTROPY_PRIMITIVE_AUDIT.csv)
# =========================================================================
# Which coordinates reliably precede entropy collapse (low next-cell entropy)

def ws6_entropy_primitive(dfw):
    df = dfw.copy()
    df["next_cell"] = df["cell"].shift(-1)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    # call a row "LOW_ENTROPY" if its age-band next-cell entropy is below
    # the cell median (entropy collapse region)
    ent_map = {}
    for cell in CELLS:
        for ab in [b[2] for b in AGE_BANDS]:
            g = df[(df["cell"] == cell) & (df["age_band"] == ab)].dropna(
                subset=["next_cell"])
            if len(g) >= 20:
                ent_map[(cell, ab)] = _entropy(g["next_cell"])
    df["cell_age_entropy"] = [ent_map.get((c, a), np.nan) for c, a in
                              zip(df["cell"], df["age_band"])]
    med = df.groupby("cell")["cell_age_entropy"].transform("median")
    df["low_entropy"] = (df["cell_age_entropy"] <= med).astype(int)
    cand = ["top500_breadth_30d", "top500_dispersion_30d", "vol_med",
            "top3_share_chg7", "rank_depth_rel_chg", "btc_return_7d",
            "broad_activation_depth" if "broad_activation_depth" in
            df.columns else "rank_depth_rel"]
    rows = []
    for coord in cand:
        if coord not in df.columns:
            continue
        x = df[coord].to_numpy(dtype=float)
        y = df["low_entropy"].to_numpy()
        good = ~np.isnan(x)
        if good.sum() < 200:
            continue
        rho, p = spearmanr(x[good], y[good])
        med_hi = float(np.nanmedian(x[y == 1])) if (y == 1).any() else np.nan
        med_lo = float(np.nanmedian(x[y == 0])) if (y == 0).any() else np.nan
        rows.append({"coord": coord, "spearman_rho": float(rho),
                     "p": float(p), "median_low_entropy": med_hi,
                     "median_high_entropy": med_lo,
                     "direction": "HIGH_assoc_low_entropy" if rho > 0
                     else "LOW_assoc_low_entropy"})
    out = pd.DataFrame(rows)
    if len(out):
        q = _fdr(out["p"].to_numpy())
        out["q"] = q
        n_sig = int((out["q"] <= FDR_Q).sum())
        out["verdict"] = ("GLOBAL_ENTROPY_COORDINATE" if n_sig >= 2 else
                         "LOCAL_ENTROPY_COORDINATE" if n_sig >= 1 else
                         "NO_STABLE_DRIVER")
        out.attrs = {"n_sig": n_sig}
    out.to_csv(OUT / "07_ENTROPY_PRIMITIVE_AUDIT.csv", index=False)
    return out