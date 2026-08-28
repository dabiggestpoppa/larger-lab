from _m16base import *
from _m16base import _cache_step, _entropy, _fdr, _fmt, _js_distance, \
    SURFACE_GROUP_COLS, ORDERING_METRICS, rank_order_rho, group_order_profile, \
    _subperiod_split


# =========================================================================
# WS1: HOLDOUT FAILURE REPRODUCTION (02_HOLDOUT_FAILURE_REPRO.csv)
# =========================================================================
def _ordering_snapshot(df, group_col, metric):
    """Ordering profile of a surface within one period slice."""
    return group_order_profile(df, group_col, metric, min_n=30)


def _surface_stability(df, group_col):
    """Return dict of stability rho per test mode, averaged over metrics."""
    d = df.sort_values("d").reset_index(drop=True)
    n = len(d)
    rows = []
    # chronological 80/20
    cut = int(0.8 * n)
    early, late = d.iloc[:cut], d.iloc[cut:]
    for metric in ORDERING_METRICS:
        p1 = _ordering_snapshot(early, group_col, metric)
        p2 = _ordering_snapshot(late, group_col, metric)
        rho, nk = rank_order_rho(p1, p2)
        rows.append({"test": "chronological_80_20", "surface": group_col,
                     "metric": metric, "rho": rho, "n_groups_common": nk,
                     "n_early": int(len(early)), "n_late": int(len(late))})
    # early/late halves
    half = n // 2
    first, second = d.iloc[:half], d.iloc[half:]
    for metric in ORDERING_METRICS:
        p1 = _ordering_snapshot(first, group_col, metric)
        p2 = _ordering_snapshot(second, group_col, metric)
        rho, nk = rank_order_rho(p1, p2)
        rows.append({"test": "early_vs_late_half", "surface": group_col,
                     "metric": metric, "rho": rho, "n_groups_common": nk,
                     "n_early": half, "n_late": n - half})
    # LOSO: leave-one-subperiod-out vs full sample
    full = {m: _ordering_snapshot(d, group_col, m) for m in ORDERING_METRICS}
    d = d.reset_index(drop=True)
    for sp, idx in _subperiod_split(d):
        if sp == "UNKNOWN":
            continue
        keep = np.ones(len(d), dtype=bool)
        keep[np.asarray(idx, dtype=int)] = False
        rest = d[keep]
        for metric in ORDERING_METRICS:
            pr = _ordering_snapshot(rest, group_col, metric)
            rho, nk = rank_order_rho(full[metric], pr)
            rows.append({"test": "leave_one_subperiod_out", "surface":
                         group_col, "metric": metric, "rho": rho,
                         "n_groups_common": nk, "fold": sp})
    return pd.DataFrame(rows)


def ws1_holdout_repro(df):
    out = []
    for label, gc in SURFACE_GROUP_COLS.items():
        st = _surface_stability(df, gc)
        st["surface_label"] = label
        out.append(st)
    res = pd.concat(out, ignore_index=True)
    # artifact diagnosis on the 16-cell prop ordering: robust-cell restriction
    d = df.sort_values("d").reset_index(drop=True)
    cut = int(0.8 * len(d))
    early, late = d.iloc[:cut], d.iloc[cut:]
    p1 = group_order_profile(early, "grp16", "prop", min_n=100)
    p2 = group_order_profile(late, "grp16", "prop", min_n=100)
    rho_robust, nk = rank_order_rho(p1, p2)
    # same restriction on reduced surfaces
    diag = {"test": "chronological_80_20_robust_only",
            "surface_label": "16_cell", "metric": "prop",
            "rho": rho_robust, "n_groups_common": nk,
            "note": "min_n=100 per period per cell (ROBUST support)"}
    res = pd.concat([res, pd.DataFrame([diag])], ignore_index=True)
    res["verdict"] = "HOLDOUT_REPRO_DONE"
    # per-surface mean chronological rho (the headline)
    surf_mean = []
    for label, gc in SURFACE_GROUP_COLS.items():
        sub = res[(res["surface_label"] == label) &
                  (res["test"] == "chronological_80_20")]
        m = sub["rho"].dropna()
        surf_mean.append({"surface_label": label, "surface_col": gc,
                          "mean_chrono_rho": float(m.mean()) if len(m) else
                          np.nan,
                          "prop_chrono_rho": float(sub.loc[
                              sub["metric"] == "prop", "rho"].iloc[0])
                          if (sub["metric"] == "prop").any() else np.nan})
    sm = pd.DataFrame(surf_mean)
    sm["verdict"] = "SURFACE_LEVEL_REPRO"
    res.to_csv(OUT / "02_HOLDOUT_FAILURE_REPRO.csv", index=False)
    return res, sm


# =========================================================================
# WS2: 6-CELL vs 8-CELL FREEZE AUDIT (03_SURFACE_6_VS_8_AUDIT.csv)
# =========================================================================
def _between_group_var(df, group_col, col):
    rows = []
    for _, g in df.groupby(group_col):
        if len(g) < 20:
            continue
        if col == "next_dir":
            v = _entropy(g["next_dir"].dropna())
        elif col == "fbe":
            v = g["fbe"].dropna().mean()
        else:
            v = float(g[col].mean())
        if v == v:
            rows.append((len(g), v))
    if len(rows) < 2:
        return np.nan
    tot = sum(w for w, _ in rows)
    mu = sum(w * v for w, v in rows) / tot
    return sum(w * (v - mu) ** 2 for w, v in rows) / tot


def ws2_surface_6_vs_8(df, holdout, ret15):
    """Compare 6 vs 8 cell across stability + structure + retention."""
    rows = []
    stab = {}
    for label in ["6_cell", "8_cell"]:
        gc = SURFACE_GROUP_COLS[label]
        sub = holdout[holdout["surface_label"] == label]
        chrono = sub[sub["test"] == "chronological_80_20"]["rho"].dropna()
        loso = sub[sub["test"] == "leave_one_subperiod_out"]["rho"].dropna()
        half = sub[sub["test"] == "early_vs_late_half"]["rho"].dropna()
        stab[label] = {
            "chrono_mean": float(chrono.mean()) if len(chrono) else np.nan,
            "loso_mean": float(loso.mean()) if len(loso) else np.nan,
            "half_mean": float(half.mean()) if len(half) else np.nan,
        }
        g = df[df[gc].notna()]
        rows.append({
            "surface": label, "n_groups": int(g[gc].nunique()),
            "n_days": int(len(g)),
            "chrono_stability": stab[label]["chrono_mean"],
            "loso_stability": stab[label]["loso_mean"],
            "half_stability": stab[label]["half_mean"],
            "rank_between_var": _between_group_var(g, gc, "rank7"),
            "prop_between_var": _between_group_var(g, gc, "prop7"),
            "dir_entropy_between_var": _between_group_var(g, gc, "next_dir"),
            "branch_entropy_between_var": _between_group_var(g, gc, "fbe"),
            "mean_self_transition": float(g[
                g[gc] == g[gc + "_next"]].shape[0] / max(1, len(g))),
            "forcing_range": float(g["forcing"].max() - g["forcing"].min()),
        })
    # retention from MECH-15 (deterministic cache of ws6)
    ret = ret15[ret15["n_cells"].isin([6, 8])].set_index("n_cells")
    for cut in [6, 8]:
        rr = float(ret.loc[cut, "rank_recruitment"])
        rows.append({"surface": f"retention_{cut}", "n_groups": cut,
                     "rank_retention": rr})
    out = pd.DataFrame(rows)
    # verdict
    s6 = stab["6_cell"]
    s8 = stab["8_cell"]
    rank6 = float(ret.loc[6, "rank_recruitment"])
    rank8 = float(ret.loc[8, "rank_recruitment"])
    rank_gap = rank8 - rank6
    stab_gap = (s8["chrono_mean"] - s6["chrono_mean"]) if \
        (s8["chrono_mean"] == s8["chrono_mean"] and
         s6["chrono_mean"] == s6["chrono_mean"]) else 0.0
    if rank_gap >= 0.10 and stab_gap >= 0.05:
        verdict = "FREEZE_8"
    elif rank_gap >= 0.10 and stab_gap >= -0.03:
        verdict = "DUAL_RESOLUTION"
    elif stab_gap < -0.05:
        verdict = "FREEZE_6"
    else:
        verdict = "FREEZE_6"
    out["verdict"] = "SURFACE_6_VS_8_AUDIT_DONE"
    out["freeze_recommendation"] = verdict
    out["rank_gap_8_minus_6"] = rank_gap
    out["chrono_stability_gap_8_minus_6"] = stab_gap
    out.to_csv(OUT / "03_SURFACE_6_VS_8_AUDIT.csv", index=False)
    return out, verdict
