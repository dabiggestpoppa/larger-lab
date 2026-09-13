from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split


# =========================================================================
# WS7: ENTROPY PROPAGATION (08_ENTROPY_PROPAGATION.csv)
# =========================================================================
# If entropy collapses in one patch, does nearby structure become more
# constrained? Per-patch activation-entropy metric and lead-lag propagation.

def _patch_entropy_series(band):
    """Per-patch daily binary 'activation' (ppos>=0.55) -> rolling entropy."""
    b = band.copy()
    b["patch"] = b["band"].map(
        {fb: p for p, fbs in PATCHES.items() for fb in fbs})
    b = b.dropna(subset=["patch"])
    g = b.groupby(["d", "patch"]).agg(ppos=("ppos", "mean"),
                                      ptail=("ptail", "mean")).reset_index()
    g["active"] = (g["ppos"] >= 0.55).astype(int)
    # rolling window entropy of the binary active series over 7D
    out = {}
    for patch, pg in g.groupby("patch"):
        pg = pg.sort_values("d")
        act = pg["active"].to_numpy()
        ent = []
        for i in range(len(act)):
            w = act[max(0, i - 6):i + 1]
            p1 = w.mean()
            p0 = 1 - p1
            if 0 < p1 < 1:
                ent.append(-(p1 * np.log2(p1) + p0 * np.log2(p0)))
            else:
                ent.append(0.0)
        out[patch] = pg[["d"]].assign(ent=ent)
    return out


def ws7_entropy_propagation(band):
    series = _patch_entropy_series(band)
    patches = list(PATCHES.keys())
    # align on full date grid
    all_dates = None
    for p in patches:
        s = series[p][["d", "ent"]].set_index("d")
        all_dates = s if all_dates is None else all_dates.join(
            s, rsuffix=f"_{p}", how="outer")
    all_dates.columns = ["ent_" + p for p in patches]
    all_dates = all_dates.sort_index().ffill().dropna()
    rows = []
    for a in range(len(patches)):
        for b in range(a + 1, len(patches)):
            pa, pb = patches[a], patches[b]
            x = all_dates[f"ent_{pa}"].to_numpy()
            y = all_dates[f"ent_{pb}"].to_numpy()
            for lag in [0, 1, 3, 7]:
                if lag > len(x) // 2:
                    continue
                # correlation of pa's entropy at t with pb's entropy at t+lag
                if lag == 0:
                    rho, p = spearmanr(x, y)
                elif lag > 0:
                    rho, p = spearmanr(x[:-lag], y[lag:])
                else:
                    rho, p = spearmanr(x[-lag:], y[:lag])
                rows.append({"patch_a": pa, "patch_b": pb, "lag_d": lag,
                             "spearman_rho": float(rho), "p": float(p)})
    out = pd.DataFrame(rows)
    # propagation verdict: if same-day correlations are very high and lagged
    # positive -> synchronized/no true lead-lag; if nonzero lagged dominates
    same = out[out["lag_d"] == 0]["spearman_rho"] if len(out) else []
    lag1 = out[out["lag_d"] == 1]["spearman_rho"] if len(out) else []
    if len(same) and len(lag1):
        if np.nanmedian(abs(np.asarray(lag1))) > np.nanmedian(
                abs(np.asarray(same))) * 1.1:
            verdict = "PATCH_PROPAGATION"
        elif np.nanmedian(abs(np.asarray(same))) > 0.7:
            verdict = "SYNCHRONIZED_NO_LAG_PROPAGATION"
        elif np.nanmedian(abs(np.asarray(same))) > 0.4:
            verdict = "WEAK_LOCAL_COLLAPSE"
        else:
            verdict = "NO_PROPAGATION"
        out["verdict"] = verdict
    out.to_csv(OUT / "08_ENTROPY_PROPAGATION.csv", index=False)
    return out


# =========================================================================
# WS8: SPATIAL vs TEMPORAL CONSTRAINT MATRIX (09_SPATIAL_TEMPORAL_CONSTRAINT_MATRIX.csv)
# =========================================================================
# Axis 1 = spatial activation capacity (depth/number of activated patches)
# Axis 2 = temporal resolution entropy (next branch entropy at field level)

def _daily_patch_activation(band):
    b = band.copy()
    b["patch"] = b["band"].map(
        {fb: p for p, fbs in PATCHES.items() for fb in fbs})
    b = b.dropna(subset=["patch"])
    g = b.groupby(["d", "patch"]).agg(ppos=("ppos", "mean")).reset_index()
    g["active"] = (g["ppos"] >= 0.55)
    act = g.groupby("d")["active"].sum()
    return act.rename("spatial_activation")


def ws8_spatial_temporal_matrix(dfw, band):
    act = _daily_patch_activation(band)
    df = dfw.copy().set_index("d")
    df = df.join(act, how="left")
    df["spatial_activation"] = df["spatial_activation"].fillna(0)
    # forward propagation / reentry flags from STATE (not cell) at +7d
    df["fwd7_state"] = df["state"].shift(-7)
    df["p_prop_7d_ev"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(int)
    df["p_reentry_7d_ev"] = (df["fwd7_state"] == REENTRY_LABEL).astype(int)
    # field resolution entropy: entropy of the rolling 7D cell distribution
    field_ent = []
    cells_arr = df["cell"].to_numpy()
    n = len(df)
    for i in range(n):
        w = cells_arr[max(0, i - 6):i + 1]
        ent = _entropy(pd.Series(w))
        field_ent.append(ent)
    df["temporal_resolution_entropy"] = field_ent
    # 2x2: spatial HIGH = broad multi-patch activation (>=3 of 5 patches
    # active today); LOW otherwise. temporal HIGH/LOW by median entropy.
    df["spatial_ax"] = np.where(df["spatial_activation"] >= 3,
                                "HIGH_ACTIVATION", "LOW_ACTIVATION")
    # entropy is voice-bimodal (~53% days fully compressed at 0 bits); split
    # at >0 = resolution present vs compressed, so both cells populate.
    df["temporal_ax"] = np.where(
        df["temporal_resolution_entropy"] > 0,
        "HIGH_ENTROPY", "LOW_ENTROPY")
    df["constraint_cell"] = df["spatial_ax"] + "_" + df["temporal_ax"]
    rows = []
    for cc, g in df.groupby("constraint_cell"):
        rows.append({
            "constraint_cell": cc,
            "spatial_ax": g["spatial_ax"].iloc[0],
            "temporal_ax": g["temporal_ax"].iloc[0],
            "n_days": int(len(g)),
            "p_HH": float((g["cell"] ==
                           "HIGH_BREADTH_HIGH_DISP").mean()),
            "p_LL": float((g["cell"] ==
                           "LOW_BREADTH_LOW_DISP").mean()),
            "p_prop_7d": float(g["p_prop_7d_ev"].mean()),
            "p_reentry_7d": float(g["p_reentry_7d_ev"].mean()),
            "tail_share": float(g[[c for c in EVENT_COLS if
                                  c in g.columns]].sum(axis=1).mean()),
            "rank_recruit": float(g["rank_depth_rel_chg"].gt(0).mean()),
            "med_age": float(g["age_in_cell"].mean()),
            "n_subperiods": int(g["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    xs = df["spatial_activation"].to_numpy()
    ys = df["temporal_resolution_entropy"].to_numpy()
    rho, p = spearmanr(xs, ys)
    out["axis_spearman"] = float(rho)
    out["axis_p"] = float(p)
    out["verdict"] = ("INDEPENDENT_CONSTRAINT_DIMENSIONS" if abs(rho) < 0.3
                     else "COUPLED_CONSTRAINT_DIMENSIONS")
    out.to_csv(OUT / "09_SPATIAL_TEMPORAL_CONSTRAINT_MATRIX.csv", index=False)
    return out