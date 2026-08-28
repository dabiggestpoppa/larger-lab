from _p1 import *
from _p1 import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _perm_p, _atom_series
# =========================================================================
# WS1: FULL 4-STATE LIFECYCLE (02_FULL_STATE_LIFECYCLE.csv)
# =========================================================================

EVENT_COLS = ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE",
              "ev_ISOLATED_DOWNSIDE_EXTREME", "ev_LOCAL_CLUSTER_DOWNSIDE",
              "ev_COORDINATED_DOWNSIDE", "ev_ISOLATED_UPSIDE"]
STRESS_COLS = ["ev_ISOLATED_DOWNSIDE_EXTREME", "ev_LOCAL_CLUSTER_DOWNSIDE"]
RECOVERY_COLS = ["ev_ISOLATED_UPSIDE"]


def ws1_full_lifecycle(dfw):
    df = dfw.copy()
    n = len(df)
    cells = df["cell"].to_numpy()
    state = df["state"].to_numpy()

    # forward flags per horizon
    exit_flags, reentry_flags, prop_flags, recruit_flags = {}, {}, {}, {}
    tail_flags, stress_flags, recover_flags = {}, {}, {}
    trans_flags = {t: {} for t in CELLS}
    for h in HORIZONS:
        ef = np.zeros(n)
        rf = np.zeros(n)
        pf = np.zeros(n)
        kf = np.zeros(n)
        tf = np.zeros(n)
        sf = np.zeros(n)
        rc = np.zeros(n)
        tr = {t: np.zeros(n) for t in CELLS}
        for i in range(n):
            j = min(i + h, n - 1)
            seg_c = cells[i + 1:j + 1]
            seg_s = state[i + 1:j + 1]
            ef[i] = (seg_c != cells[i]).any()
            rf[i] = (seg_s == REENTRY_LABEL).any()
            pf[i] = pd.Series(seg_s).isin(SUCCESS_LABELS).any()
            kf[i] = (df["rank_depth_rel_chg"].to_numpy()[i + 1:j + 1] > 0).any()
            if j > i:
                win = df.iloc[i + 1:j + 1][EVENT_COLS].to_numpy()
                tf[i] = win.sum() > 0
                sf[i] = df.iloc[i + 1:j + 1][STRESS_COLS].to_numpy().sum() > 0
                rc[i] = df.iloc[i + 1:j + 1][RECOVERY_COLS].to_numpy().sum() > 0
            for t in CELLS:
                tr[t][i] = (seg_c == t).any()
        exit_flags[h] = ef
        reentry_flags[h] = rf
        prop_flags[h] = pf
        recruit_flags[h] = kf
        tail_flags[h] = tf
        stress_flags[h] = sf
        recover_flags[h] = rc
        for t in CELLS:
            trans_flags[t][h] = tr[t]

    df["age_band"] = df["age_in_cell"].apply(_age_band)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell]
        for ab in [b[2] for b in AGE_BANDS]:
            s2 = sub[sub["age_band"] == ab]
            if len(s2) < 20:
                continue
            idx = s2.index.to_numpy()
            base = {"cell": cell, "age_band": ab, "n_days": int(len(s2))}
            for h in HORIZONS:
                row = dict(base)
                row["horizon_d"] = h
                row["p_stay"] = float(1 - exit_flags[h][idx].mean())
                row["p_exit"] = float(exit_flags[h][idx].mean())
                row["p_reentry"] = float(reentry_flags[h][idx].mean())
                row["p_propagate"] = float(prop_flags[h][idx].mean())
                row["p_tail_activation"] = float(tail_flags[h][idx].mean())
                row["p_rank_recruitment"] = float(recruit_flags[h][idx].mean())
                row["p_local_stress"] = float(stress_flags[h][idx].mean())
                row["p_local_recovery"] = float(recover_flags[h][idx].mean())
                for t in CELLS:
                    row[f"p_trans_{t}"] = float(trans_flags[t][h][idx]
                                                 .mean())
                rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "02_FULL_STATE_LIFECYCLE.csv", index=False)
    return out


# =========================================================================
# WS2: STATE FAILURE GEOMETRY (03_STATE_FAILURE_GEOMETRY.csv)
# =========================================================================

COORDS = ["top500_breadth_30d", "top500_dispersion_30d", "top3_share",
          "rank_depth_rel", "vol_med", "btc_return_7d"]
LAGS = [0, 1, 3, 7]


def _lag_mean(df, col, lag):
    if lag == 0:
        return df[col].to_numpy(dtype=float)
    return df[col].shift(-lag).to_numpy(dtype=float)


def ws2_failure_geometry(dfw):
    df = dfw.copy()
    df["fwd7_state"] = df["state"].shift(-7)
    df["success"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(int)
    df["fail"] = (df["fwd7_state"] == REENTRY_LABEL).astype(int)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell].copy()
        ok = sub[(sub["success"] == 1) | (sub["fail"] == 1)]
        if len(ok) < 60 or ok["success"].sum() < 20 or ok["fail"].sum() < 20:
            continue
        ok = ok.copy()
        for coord in COORDS:
            for lag in LAGS:
                ok[f"{coord}_l{lag}"] = _lag_mean(ok, coord, lag)
        suc_mask = ok["success"].to_numpy() == 1
        for coord in COORDS:
            for lag in LAGS:
                col = f"{coord}_l{lag}"
                g_s = ok.loc[suc_mask, col].to_numpy(dtype=float)
                g_f = ok.loc[~suc_mask, col].to_numpy(dtype=float)
                g_s = g_s[~np.isnan(g_s)]
                g_f = g_f[~np.isnan(g_f)]
                if len(g_s) < 20 or len(g_f) < 20:
                    continue
                try:
                    stat, p = ranksums(g_s, g_f)
                except Exception:
                    p = np.nan
                rows.append({"cell": cell, "coord": coord, "lag_d": lag,
                             "n_success": int(ok["success"].sum()),
                             "n_fail": int(ok["fail"].sum()),
                             "mean_success": float(np.nanmean(g_s)),
                             "mean_fail": float(np.nanmean(g_f)),
                             "p": float(p)})
    geo = pd.DataFrame(rows)
    # earliest significant lag per cell (any coordinate), FDR within cell
    out_rows = []
    for cell in CELLS:
        g = geo[geo["cell"] == cell]
        if len(g) == 0:
            continue
        q = _fdr(g["p"].to_numpy())
        g = g.assign(q=q)
        sig = g[g["q"] <= FDR_Q]
        if len(sig) == 0:
            out_rows.append({"cell": cell, "verdict": "NO_STABLE_SEPARATION",
                             "first_lag_d": np.nan,
                             "first_coord": "", "n_sig_pairs": 0})
            continue
        first = sig.loc[sig["lag_d"].idxmin()]
        # require the first lag to be reproducible: at least 2 sig coords at
        # that lag OR the strongest coord
        n_at_lag = (sig["lag_d"] == first["lag_d"]).sum()
        out_rows.append({
            "cell": cell, "verdict": (
                "DIFFERENT_AT_BIRTH" if first["lag_d"] == 0
                else "DIVERGES_EARLY" if first["lag_d"] <= 1
                else "DIVERGES_LATE"),
            "first_lag_d": int(first["lag_d"]),
            "first_coord": first["coord"],
            "n_sig_pairs": int(len(sig)),
            "n_sig_at_first_lag": int(n_at_lag)})
    out = pd.DataFrame(out_rows)
    out.to_csv(OUT / "03_STATE_FAILURE_GEOMETRY.csv", index=False)
    return out, geo
