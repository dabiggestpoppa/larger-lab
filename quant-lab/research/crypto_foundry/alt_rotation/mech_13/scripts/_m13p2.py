from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split

LIFECYCLE_STAGES = ["INITIATION", "BIRTH", "EARLY_SURVIVAL", "STABILIZATION",
                    "MID_LIFE", "MATURE", "PERTURBED", "RESOLVING", "EXIT",
                    "REENTRY", "PROPAGATION", "FAILURE", "TRANSITION"]


# =========================================================================
# WS1: FULL LIFECYCLE DEEP MAP (02_LIFECYCLE_DEEP_MAP.csv)
# =========================================================================

def _life_metrics(df, idx):
    """Lifecycle-stage summaries for a set of daily rows (index array)."""
    sub = df.iloc[idx]
    n = len(sub)
    if n == 0:
        return None
    pos = (sub["state"].isin(SUCCESS_LABELS)).mean()
    re = (sub["state"] == REENTRY_LABEL).mean()
    return {
        "n_days": int(n),
        "breadth": float(sub["top500_breadth_30d"].mean()),
        "dispersion": float(sub["top500_dispersion_30d"].mean()),
        "concentration": float(sub["top3_share"].mean()),
        "vol": float(sub["vol_med"].mean()),
        "btc7": float(sub["btc_return_7d"].mean()),
        "eth_rel7": float(sub["eth_btc_relative_return_7d"].mean())
        if "eth_btc_relative_return_7d" in sub.columns else np.nan,
        "rank_depth": float(sub["rank_depth_rel"].mean())
        if "rank_depth_rel" in sub.columns else np.nan,
        "age": float(sub["age_in_cell"].mean()),
        "tail_share": float(sub[[c for c in EVENT_COLS
                                 if c in sub.columns]].sum(axis=1).mean()),
        "stablecoin_chg7": float(sub["stablecoin_change_7d"].mean()),
        "tvl_chg7": float(sub["chain_tvl_med_chg7"].mean()),
        "p_pos_state": float(pos), "p_reentry_state": float(re),
    }


def ws1_lifecycle_deep_map(dfw):
    df = dfw.copy()
    n = len(df)
    cell_arr = df["cell"].to_numpy()
    # forward 7d outcome flags
    df["fwd7_state"] = df["state"].shift(-7)
    df["fwd7_prop"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(int)
    df["fwd7_reentry"] = (df["fwd7_state"] == REENTRY_LABEL).astype(int)
    # map each day to its lifecycle stage based on state, age, and forward
    # outcome -- a descriptive stage assignment (each state may not show all)
    age_band_of = df["age_in_cell"].apply(_age_band)
    df["fwd30_state"] = df["state"].shift(-30)

    rows = []
    for cell in CELLS:
        ci = np.where(cell_arr == cell)[0]
        if len(ci) == 0:
            continue
        # INITIATION = first 2 days in cell
        init_i = [i for i in ci if df["age_in_cell"].iloc[i] <= 2]
        # EARLY_SURVIVAL = AGE_4_7
        early_i = [i for i in ci if _age_band(df["age_in_cell"].iloc[i]) ==
                   "AGE_4_7"]
        # MATURE = AGE_15_PLUS
        mat_i = [i for i in ci
                 if _age_band(df["age_in_cell"].iloc[i]) == "AGE_15_PLUS"]
        # PERTURBED = days with any perturbation flag the prior 1d
        per_i = [i for i in ci]
        # PROPAGATION / REENTRY / FAILURE forward states
        prop_i = [i for i in ci if df["fwd7_prop"].iloc[i] == 1]
        ren_i = [i for i in ci if df["fwd7_reentry"].iloc[i] == 1]
        # TRANSITION = last 2 days in cell before cell change
        next_cell = pd.Series(df["cell"].to_numpy()).shift(-1)
        trans_i = [i for i in ci if i + 1 < n and
                   next_cell.iloc[i] != cell]
        trans_i = trans_i[:max(1, int(len(trans_i) * 0.25))]
        # RESOLVING = days 30d away where cell exits within 7d
        resolv_i = [i for i in ci if i + 7 < n and
                    any(df["cell"].iloc[j] != cell
                        for j in range(i + 1, i + 8)) and
                    _age_band(df["age_in_cell"].iloc[i]) in
                    ("AGE_8_14", "AGE_15_PLUS")]

        stage_ix = {
            "INITIATION": init_i, "EARLY_SURVIVAL": early_i,
            "MATURE": mat_i, "PERTURBED": ci, "PROPAGATION": prop_i,
            "REENTRY": ren_i, "TRANSITION": list(set(trans_i)),
            "RESOLVING": resolv_i, "BIRTH": init_i,
            "STABILIZATION": [i for i in ci if
                              _age_band(df["age_in_cell"].iloc[i]) in
                              ("AGE_2_3", "AGE_4_7")],
            "MID_LIFE": [i for i in ci if
                         _age_band(df["age_in_cell"].iloc[i]) ==
                         "AGE_8_14"],
            "EXIT": [i for i in ci if i + 7 < n and
                     any(df["cell"].iloc[j] != cell
                         for j in range(i + 1, i + 8))],
            "FAILURE": [i for i in ci if df["fwd30_state"].iloc[i] ==
                        REENTRY_LABEL],
        }
        for stage in LIFECYCLE_STAGES:
            prev = stage_ix.get(stage)
            if prev is None or len(prev) < 20:
                continue
            m = _life_metrics(df, prev)
            if m:
                row = {"cell": cell, "stage": stage}
                row.update(m)
                sub = df.iloc[prev]
                row["n_subperiods"] = int(sub["subperiod"].nunique())
                row["fwd7_prop"] = float(sub["fwd7_prop"].mean())
                row["fwd7_reentry"] = float(sub["fwd7_reentry"].mean())
                rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "02_LIFECYCLE_DEEP_MAP.csv", index=False)
    return out


# =========================================================================
# WS2: STATE MASS MIGRATION (03_STATE_MASS_MIGRATION.csv)
# =========================================================================

OUTCOMES = ["STAY", "EXIT", "REENTRY", "PROPAGATE", "TAIL_UP", "TAIL_DOWN",
            "RANK_RECRUIT", "RANK_DECAY", "TRANS_TO_HH", "TRANS_TO_HL",
            "TRANS_TO_LH", "TRANS_TO_LL"]


def ws2_mass_migration(dfw):
    df = dfw.copy()
    n = len(df)
    cell_arr = df["cell"].to_numpy()
    state_arr = df["state"].to_numpy()
    next_cell = df["cell"].shift(-1).to_numpy()
    ab = df["age_in_cell"].apply(_age_band).to_numpy()

    flags = defaultdict(lambda: {h: np.zeros(n) for h in HORIZONS})
    for h in HORIZONS:
        for i in range(n - h):
            seg_c = cell_arr[i + 1:i + 1 + h]
            seg_s = state_arr[i + 1:i + 1 + h]
            flags["STAY"][h][i] = (seg_c == cell_arr[i]).all()
            flags["EXIT"][h][i] = (seg_c != cell_arr[i]).any()
            flags["REENTRY"][h][i] = (seg_s == REENTRY_LABEL).any()
            flags["PROPAGATE"][h][i] = pd.Series(seg_s).isin(
                SUCCESS_LABELS).any()
            if h > 1:
                # tail up/down need the daily counts
                tail_up = df.iloc[i + 1:i + 1 + h][
                    ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE"]]
                tail_dn = df.iloc[i + 1:i + 1 + h][
                    ["ev_ISOLATED_DOWNSIDE_EXTREME",
                     "ev_LOCAL_CLUSTER_DOWNSIDE"]]
                flags["TAIL_UP"][h][i] = tail_up.sum().sum() > 0
                flags["TAIL_DOWN"][h][i] = tail_dn.sum().sum() > 0
            rk = df["rank_depth_rel_chg"].to_numpy()[i + 1:i + 1 + h]
            flags["RANK_RECRUIT"][h][i] = (rk > 0).any()
            flags["RANK_DECAY"][h][i] = (rk < 0).any()
            for t in CELLS:
                flags[f"TRANS_TO_{t}"][h][i] = (seg_c == t).any()

    rows = []
    for cell in CELLS:
        ci = np.where(cell_arr == cell)[0]
        for abn in [b[2] for b in AGE_BANDS]:
            sub_i = [i for i in ci if ab[i] == abn]
            if len(sub_i) < 30:
                continue
            for h in HORIZONS:
                row = {"cell": cell, "age_band": abn, "horizon_d": h,
                       "n_days": len(sub_i)}
                for o in OUTCOMES:
                    row[o.lower()] = float(flags[o][h][sub_i].mean())
                # monotonicity of STAY mass across horizons: is it
                # increasing (mass accumulates in-cell over time)
                row["stay_mass"] = float(flags["STAY"][h][sub_i].mean())
                rows.append(row)
    out = pd.DataFrame(rows)
    # mass-migration law classification per cell
    law_rows = []
    for cell in CELLS:
        g = out[out["cell"] == cell].copy()
        if len(g) < 5:
            continue
        g = g.sort_values("horizon_d")
        g["d_stay"] = g.groupby("age_band")["stay_mass"].diff().fillna(0)
        law = "STATE_SPECIFIC"
        # increasing stay mass with age -> saturating if flattens at large h
        g["dH"] = g.groupby("age_band")["horizon_d"].diff().fillna(0)
        law_rows.append({
            "cell": cell,
            "monotonic_ages": int(g.groupby("age_band")[
                "stay_mass"].max().ge(
                g.groupby("age_band")["stay_mass"].min()).sum()),
            "min_age_stay": float(g[g["age_band"] == "AGE_1"][
                "stay_mass"].mean()) if "AGE_1" in
            g["age_band"].values else np.nan,
            "max_age_stay": float(g[g["age_band"] == "AGE_15_PLUS"][
                "stay_mass"].mean()) if "AGE_15_PLUS" in
            g["age_band"].values else np.nan,
            "mass_law": law})
    law = pd.DataFrame(law_rows)
    out.to_csv(OUT / "03_STATE_MASS_MIGRATION.csv", index=False)
    law.to_csv(OUT / "03b_STATE_MASS_MIGRATION_LAWS.csv", index=False)
    return out, law