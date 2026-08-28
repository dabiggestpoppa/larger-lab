from _m14base import *
from _m14base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split, _cohen_d, _auc_xy


def _attach_entropy_and_branches(dfw):
    """Return df with: next_cell, ab, cell_age_entropy (stratum constant),
    per-day fwd_branch_entropy / fwd_nbranch / fwd_dominant_share, and
    fwd7_prop / fwd7_ren outcome flags."""
    df = dfw.copy()
    n = len(df)
    df["next_cell"] = df["cell"].shift(-1)
    df["ab"] = df["age_in_cell"].apply(_age_band)
    state_arr = df["state"].to_numpy()
    fwd7_prop = np.zeros(n); fwd7_ren = np.zeros(n)
    for i in range(n - 7):
        seg = pd.Series(state_arr[i + 1:i + 8])
        fwd7_prop[i] = seg.isin(SUCCESS_LABELS).any()
        fwd7_ren[i] = (seg == REENTRY_LABEL).any()
    df["fwd7_prop"] = fwd7_prop
    df["fwd7_ren"] = fwd7_ren
    # per-day forward branch entropy (varies within a stratum)
    cells_list = df["cell"].to_list()
    fe = []; fn = []; fd = []
    for i in range(n):
        w = cells_list[i + 1:i + 8]
        if len(w) < 3:
            fe.append(np.nan); fn.append(np.nan); fd.append(np.nan)
            continue
        vc = pd.Series(w).value_counts(normalize=True)
        e = float(-(vc * np.log2(vc)).sum())
        fe.append(e); fn.append(int(len(vc))); fd.append(float(vc.max()))
    df["fwd_branch_entropy"] = fe
    df["fwd_nbranch"] = fn
    df["fwd_dominant_share"] = fd
    # stratum-constant cell-ag entropy (reference carrier of age)
    ent_by = {}
    for cell in CELLS:
        for abn in [b[2] for b in AGE_BANDS]:
            g = df[(df["cell"] == cell) & (df["ab"] == abn)].dropna(
                subset=["next_cell"])
            if len(g) >= 20:
                ent_by[(cell, abn)] = _entropy(g["next_cell"])
    df["cell_age_entropy"] = [ent_by.get((c, a), np.nan)
                              for c, a in zip(df["cell"], df["ab"])]
    return df


# =========================================================================
# WS4: AGE-RESIDUALIZED CONSTRAINT ENTROPY (06_AGE_RESIDUALIZED_ENTROPY.csv)
# =========================================================================
# Uses PER-DAY fwd_branch_entropy (varies within a state-age stratum). Three
# tests: (A) within-stratum entropy mediates outcomes, (B) incremental AUC of
# entropy over age, (C) age-residualized (entropy minus age-stratum mean).

def ws4_age_residualized_entropy(dfw):
    df = _attach_entropy_and_branches(dfw)
    df["ab"] = df["age_in_cell"].apply(_age_band)
    rows = []
    # (A) within (cell,age) stratum: does higher per-day branch entropy move
    # fwd7 propagation?
    for cell in CELLS:
        for abn in [b[2] for b in AGE_BANDS]:
            g = df[(df["cell"] == cell) & (df["ab"] == abn)].dropna(
                subset=["fwd_branch_entropy", "fwd7_prop"])
            if len(g) < 60:
                continue
            e = g["fwd_branch_entropy"].to_numpy(dtype=float)
            med = float(np.nanmedian(e))
            hi = g[e >= med]; lo = g[e < med]
            if len(hi) < 15 or len(lo) < 15:
                continue
            dp = float(hi["fwd7_prop"].mean() - lo["fwd7_prop"].mean())
            dr = float(hi["fwd7_ren"].mean() - lo["fwd7_ren"].mean())
            rows.append({"cell": cell, "age_band": abn,
                         "n_hi": int(len(hi)), "n_lo": int(len(lo)),
                         "delta_prop_hi_minus_lo": dp,
                         "delta_reentry_hi_minus_lo": dr})
    within = pd.DataFrame(rows)
    out = within.copy()
    n_strata = len(within)
    n_strata_prop_up = int((within["delta_prop_hi_minus_lo"] > 0).sum())
    mean_dp = float(within["delta_prop_hi_minus_lo"].mean()) if n_strata \
        else np.nan

    # (B) residualize per-day entropy on age strata -> logistic prop7
    df2 = df.dropna(subset=["fwd7_prop", "fwd_branch_entropy"]).copy()
    mean_fbe = df2.groupby(["cell", "ab"])["fwd_branch_entropy"].transform(
        "mean")
    df2["fbe_resid"] = df2["fwd_branch_entropy"] - mean_fbe
    y = df2["fwd7_prop"].astype(int).to_numpy()
    cell_code = df2["cell"].astype("category").cat.codes.to_numpy()
    ab_code = df2["ab"].astype("category").cat.codes.to_numpy()
    try:
        X_age = ab_code.reshape(-1, 1)
        X_age_ent = np.column_stack([ab_code, df2["fbe_resid"].to_numpy()])
        X_age_cell_ent = np.column_stack([cell_code, ab_code,
                                          df2["fbe_resid"].to_numpy()])
        ma = LogisticRegression(max_iter=1000).fit(X_age, y)
        mae = LogisticRegression(max_iter=1000).fit(X_age_ent, y)
        mace = LogisticRegression(max_iter=1000).fit(X_age_cell_ent, y)
        auc_age = roc_auc_score(y, ma.predict_proba(X_age)[:, 1])
        auc_age_ent = roc_auc_score(y, mae.predict_proba(X_age_ent)[:, 1])
        auc_cell_age_ent = roc_auc_score(y,
                                         mace.predict_proba(
                                             X_age_cell_ent)[:, 1])
        ll_age = log_loss(y, ma.predict_proba(X_age)[:, 1])
        ll_age_ent = log_loss(y, mae.predict_proba(X_age_ent)[:, 1])
    except Exception:
        auc_age = auc_age_ent = auc_cell_age_ent = np.nan
        ll_age = ll_age_ent = np.nan
    delta_auc_ent_over_age = float(auc_age_ent - auc_age) if \
        not np.isnan(auc_age) else np.nan
    delta_ll_ent_over_age = float(ll_age - ll_age_ent) if not np.isnan(
        ll_age) else np.nan

    if n_strata >= 4 and abs(delta_auc_ent_over_age) >= 0.01 and \
            not np.isnan(delta_auc_ent_over_age):
        verdict = "ENTROPY_INDEPENDENT_COORDINATE"
    elif n_strata >= 4 and abs(delta_auc_ent_over_age) < 0.005 and \
            abs(float(mean_dp)) < 0.01:
        verdict = "ENTROPY_REDUNDANT_WITH_LIFECYCLE"
    else:
        verdict = "ENTROPY_PARTIAL_CARRIER_OF_AGE"
    out["verdict"] = verdict
    out["n_strata"] = n_strata
    out["n_strata_prop_up"] = n_strata_prop_up
    out["mean_delta_prop_hi_lo"] = mean_dp
    out["delta_auc_ent_over_age"] = delta_auc_ent_over_age
    out["delta_ll_ent_over_age"] = delta_ll_ent_over_age
    out["auc_age"] = float(auc_age) if not np.isnan(auc_age) else np.nan
    out["auc_age_ent"] = float(auc_age_ent) if not np.isnan(
        auc_age_ent) else np.nan
    # per-cell carrier breakdown
    cell_carrier = []
    for cell in CELLS:
        gc = within[within["cell"] == cell]
        cell_carrier.append({"cell": cell,
                             "n_strata": int(len(gc)),
                             "mean_dp": float(gc["delta_prop_hi_minus_lo"]
                                              .mean()) if len(gc) else np.nan})
    cc = pd.DataFrame(cell_carrier)
    out.to_csv(OUT / "06_AGE_RESIDUALIZED_ENTROPY.csv", index=False)
    cc.to_csv(OUT / "06b_AGE_RESIDUALIZED_PER_CELL.csv", index=False)
    return out, cc


# =========================================================================
# WS5: ENTROPY FLOOR / BRANCH CLOSURE (07_ENTROPY_BRANCH_CLOSURE.csv)
# =========================================================================

def ws5_entropy_branch_closure(dfw):
    df = _attach_entropy_and_branches(dfw)
    rows = []
    for cell in CELLS:
        g = df[df["cell"] == cell]
        ag = g.groupby("ab").agg(
            n=("fwd_branch_entropy", "size"),
            ent=("fwd_branch_entropy", "mean"),
            nbranch=("fwd_nbranch", "mean"),
            dom=("fwd_dominant_share", "mean")).reindex(
            ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"])
        ag = ag.dropna()
        if len(ag) < 3:
            continue
        ent = ag["ent"].to_numpy()
        d = np.diff(ent)
        e_first, e_last = ent[0], ent[-1]
        if e_last < e_first * 0.4 and np.all(np.abs(d) <= 0.0001):
            shape = "SMOOTH_COLLAPSE"
        elif e_last < e_first * 0.4:
            n_step = int((np.abs(np.diff(d)) > 0.05).sum())
            shape = "STEPWISE_CLOSURE" if n_step >= 1 else "ABRUPT_CLOSURE"
        else:
            shape = "NO_CLOSURE"
        mature = df[(df["cell"] == cell) & (df["ab"] == "AGE_15_PLUS")] \
            .dropna(subset=["next_cell"])["next_cell"]
        fin = mature.mode().iloc[0] if len(mature) else ""
        rows.append({"cell": cell,
                     "entropy_fraction_retained": float(
                         e_last / e_first) if e_first else np.nan,
                     "n_branch_fraction_retained": float(
                         ag["nbranch"].iloc[-1] / ag["nbranch"].iloc[0]),
                     "dominant_share_last": float(ag["dom"].iloc[-1]),
                     "closure_shape": shape,
                     "final_dominant_branch": fin,
                     "n_bins": int(len(ag))})
    out = pd.DataFrame(rows)
    out["verdict"] = "BRANCH_CLOSURE_MAPPED"
    out.to_csv(OUT / "07_ENTROPY_BRANCH_CLOSURE.csv", index=False)
    return out


# =========================================================================
# WS6: SURVIVAL-CONDITIONED BRANCHES (08_SURVIVAL_CONDITIONED_BRANCHES.csv)
# =========================================================================

def ws6_survival_conditioned_branches(dfw):
    df = dfw.copy()
    n = len(df)
    cell_arr = df["cell"].to_numpy()
    state_arr = df["state"].to_numpy()
    chg = (df["cell"] != df["cell"].shift(1)).to_numpy()
    ep = np.cumsum(chg)
    ep_cell = df.groupby(ep)["cell"].first()
    horizon = [3, 5, 7, 10, 14, 21]
    rows = []
    for cell in CELLS:
        cell_eps = [e for e, c in ep_cell.items() if c == cell]
        for h in horizon:
            idx = []
            for e in cell_eps:
                pos = np.where(ep == e)[0]
                # days with at least h more days within same episode
                surv_ok = pos[np.searchsorted(pos,
                                              np.array(pos) + h,
                                              side="right") > 0]
                # equivalently: keep i where exists j in pos with j-i>=h
                for i in pos:
                    later = pos[pos > i]
                    if len(later) and later[-1] - i >= h:
                        idx.append(i)
            if len(idx) < 50:
                continue
            fwd_props = []
            for i in idx:
                j = min(i + h + 7, n - 1)
                if i + h < n:
                    seg = pd.Series(state_arr[i + h:min(j + 1, n)])
                    fwd_props.append(seg.isin(SUCCESS_LABELS).any())
            prop_rate = float(np.mean(fwd_props)) if fwd_props else np.nan
            # exit destination after survival window
            exits = []
            for i in idx:
                later = np.where(ep == ep[i])[0]
                later = later[later >= i + h]
                if len(later) == 0:
                    exits.append("STAY")
                else:
                    # find first day in this episode that exits
                    # (next-day cell differs) starting at i+h
                    k = i + h
                    while k < n and ep[k] == ep[i]:
                        k += 1
                    exits.append(cell_arr[min(k, n - 1)] if k < n else "END")
            dom = pd.Series(exits).mode().iloc[0] if exits else ""
            rows.append({"cell": cell, "survive_to_d": h,
                         "n_events": int(len(idx)),
                         "p_prop7_after_survival": prop_rate,
                         "dominant_post_survival": dom})
    out = pd.DataFrame(rows)
    out["verdict"] = "SURVIVAL_CONDITIONED_BRANCHES_MAPPED"
    out.to_csv(OUT / "08_SURVIVAL_CONDITIONED_BRANCHES.csv", index=False)
    return out


# =========================================================================
# WS15: SPATIAL x TEMPORAL CONSTRAINT RECHECK (17_SPATIAL_TEMPORAL_CONSTRAINT_RECHECK.csv)
# =========================================================================

def ws15_spatial_temporal_recheck(band, dfw):
    # reuse M13 daily patch activation
    from _m13p5 import _daily_patch_activation as _dpa
    act = _dpa(band)
    df = dfw.copy().set_index("d")
    df = df.join(act.rename("spatial_activation"), how="left")
    df["spatial_activation"] = df["spatial_activation"].fillna(0)
    df["fwd7_state"] = df["state"].shift(-7)
    df["p_prop7"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(int)
    df["p_ren7"] = (df["fwd7_state"] == REENTRY_LABEL).astype(int)
    df = df.reset_index()
    df["next_cell"] = df["cell"].shift(-1)
    df["ab"] = df["age_in_cell"].apply(_age_band)
    # per-day forward branch entropy
    cells_list = df["cell"].to_list()
    n = len(df)
    fe = []
    for i in range(n):
        w = cells_list[i + 1:i + 8]
        if len(w) < 3:
            fe.append(np.nan)
            continue
        vc = pd.Series(w).value_counts(normalize=True)
        fe.append(float(-(vc * np.log2(vc)).sum()))
    df["fbe"] = fe
    mean_fbe = df.groupby(["cell", "ab"])["fbe"].transform("mean")
    df["ent_resid"] = df["fbe"] - mean_fbe  # age-residualized entropy
    df["spatial_ax"] = np.where(df["spatial_activation"] >= 3,
                                "HIGH_ACT", "LOW_ACT")
    df["temporal_ax"] = np.where(df["ent_resid"] >= 0,
                                 "HIGH_ENT", "LOW_ENT")
    df["cc"] = df["spatial_ax"] + "_" + df["temporal_ax"]
    rows = []
    for cc, g in df.groupby("cc"):
        rows.append({"constraint_cell": cc, "n_days": int(len(g)),
                     "p_prop7": float(g["p_prop7"].mean()),
                     "p_ren7": float(g["p_ren7"].mean()),
                     "med_age": float(g["age_in_cell"].median()),
                     "p_HH": float((g["cell"] ==
                                    "HIGH_BREADTH_HIGH_DISP").mean()),
                     "n_subperiods": int(g["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    xs = df["spatial_activation"].to_numpy()
    ys = df["ent_resid"].to_numpy()
    # spearmanr returns NaN if any pair is missing (tail windows) - compute
    # on complete pairs only so the axis verdict rests on a real statistic
    ok = ~(np.isnan(xs) | np.isnan(ys))
    if ok.sum() >= 30:
        rho, p = spearmanr(xs[ok], ys[ok])
    else:
        rho, p = np.nan, np.nan
    out["axis_spearman"] = float(rho)
    out["axis_p"] = float(p)
    out["n_complete_pairs"] = int(ok.sum())
    if np.isnan(rho):
        verdict = "DATA_LIMITED_AXIS_UNAVAILABLE"
    elif abs(rho) < 0.3:
        verdict = "INDEPENDENT_CONSTRAINT_DIMENSIONS"
    else:
        verdict = "COUPLED_CONSTRAINT_DIMENSIONS"
    out["verdict"] = verdict
    out.to_csv(OUT / "17_SPATIAL_TEMPORAL_CONSTRAINT_RECHECK.csv", index=False)
    return out