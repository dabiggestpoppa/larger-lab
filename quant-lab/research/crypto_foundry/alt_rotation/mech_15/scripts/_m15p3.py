from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, MC, cell_stats

AB_ORDER = ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]


# =========================================================================
# WS7: STATE x AGE OVERLAY (08_STATE_AGE_OVERLAY.csv)
# =========================================================================
def ws7_state_age_overlay(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            continue
        for abn in AB_ORDER:
            gg = g[g["ab"] == abn]
            if len(gg) < 20:
                continue
            rows.append({
                "mcell": mc, "age_band": abn, "n": int(len(gg)),
                "p_prop7": float(gg["prop7"].mean()),
                "p_ren7": float(gg["ren7"].mean()),
                "dir_entropy": float(_entropy(gg["next_dir"].dropna())) if
                gg["next_dir"].notna().sum() >= 20 else np.nan,
                "next_cell_entropy": float(_entropy(
                    gg["next_cell"].dropna())) if
                gg["next_cell"].notna().sum() >= 20 else np.nan,
                "rank_recruit": float(gg["rank7"].mean()),
                "n_subperiods": int(gg["subperiod"].replace("UNKNOWN",
                    np.nan).dropna().nunique())})
    out = pd.DataFrame(rows)
    # does age refine within cells? compare within-cell age spread of prop7
    # vs between-cell spread (over usable cells)
    cells_ok = out["mcell"].unique()
    between = []
    for mc in cells_ok:
        sub = out[out["mcell"] == mc]
        if len(sub) >= 2:
            between.append(float(sub["p_prop7"].max() -
                                 sub["p_prop7"].min()))
    cell_spread = float(np.mean(between)) if between else np.nan
    overall = out["p_prop7"].dropna()
    global_spread = float(overall.max() - overall.min()) if len(overall) \
        else np.nan
    if cell_spread == cell_spread and global_spread == global_spread:
        if cell_spread >= 0.5 * global_spread:
            verdict = "AGE_REQUIRED_OVERLAY"
        elif cell_spread >= 0.25 * global_spread:
            verdict = "AGE_PARTIAL_OVERLAY"
        else:
            verdict = "AGE_REDUNDANT_INSIDE_MATRIX"
    else:
        verdict = "DATA_LIMITED"
    out["mean_within_cell_age_spread"] = cell_spread
    out["global_prop_spread"] = global_spread
    out["verdict"] = verdict
    out.to_csv(OUT / "08_STATE_AGE_OVERLAY.csv", index=False)
    return out


# =========================================================================
# WS8: AGE EFFECT CONSISTENCY (09_AGE_EFFECT_CONSISTENCY.csv)
# =========================================================================
def ws8_age_effect_consistency(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            continue
        ab = g["ab"].to_numpy()
        for col, mname in [("prop7", "propagation"),
                           ("ren7", "reentry"),
                           ("rank7", "rank_recruitment"),
                           ("next_dir", "dir_entropy")]:
            vals = g[col].to_numpy(dtype=float)
            young = vals[ab == "AGE_1"]
            mature = vals[np.isin(ab, ["AGE_8_14", "AGE_15_PLUS"])]
            if len(young) < 10 or len(mature) < 10:
                sign = np.nan
            else:
                sign = float(np.sign(np.nanmean(mature) - np.nanmean(young)))
            rows.append({"mcell": mc, "metric": mname,
                         "age_effect_sign": sign,
                         "n_young": int(len(young)),
                         "n_mature": int(len(mature))})
    out = pd.DataFrame(rows)
    signs = out.dropna(subset=["age_effect_sign"])
    for metric, g in signs.groupby("metric"):
        s = g["age_effect_sign"]
        n_same = max(int((s == 1).sum()), int((s == -1).sum()))
        frac = n_same / len(s) if len(s) else np.nan
        out.loc[out["metric"] == metric, "frac_same_sign"] = frac
        if frac is not None and frac >= 0.8:
            lab = "GLOBAL_MONOTONIC"
        elif frac >= 0.65:
            lab = "CONSTRAINT_LOCAL"
        elif frac >= 0.55:
            lab = "STATE_LOCAL"
        elif len(s) >= 4:
            lab = "CELL_SPECIFIC"
        else:
            lab = "NO_STABLE_AGE_LAW"
        out.loc[out["metric"] == metric, "consistency"] = lab
    out["verdict"] = "AGE_CONSISTENCY_MAPPED"
    out.to_csv(OUT / "09_AGE_EFFECT_CONSISTENCY.csv", index=False)
    return out


# =========================================================================
# WS9: BRANCH-CLOSURE GEOMETRY (10_BRANCH_CLOSURE_SURFACE.csv)
# =========================================================================
def ws9_branch_closure_surface(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            continue
        nc = g["next_cell"].dropna()
        if len(nc) < 20:
            continue
        ent = _entropy(nc)
        vc = nc.value_counts()
        dom_share = float(vc.iloc[0] / vc.sum())
        nbranch = int(vc.nunique())
        # reopening frequency: share of days whose next_cell appeared earlier
        # in a different cell spell (approximate via spell crossings)
        cells_arr = g["cell"].to_numpy()
        reopen = 0
        cnt = 0
        for i in range(1, len(g)):
            if cells_arr[i] != cells_arr[i - 1]:
                cnt += 1
                prev = set(cells_arr[:i])
                if cells_arr[i] in prev:
                    reopen += 1
        reopen_freq = float(reopen / cnt) if cnt else np.nan
        rows.append({"mcell": mc, "n": int(len(g)),
                     "branch_count_7d": nbranch,
                     "next_state_entropy": ent,
                     "dominant_branch_share": dom_share,
                     "reopening_frequency": reopen_freq})
    out = pd.DataFrame(rows)
    # descriptive labels only where behavior is resolved/stable
    def _label(r):
        e = r["next_state_entropy"]
        if e == e:
            if e <= 0.4:
                return "LOCKED_BRANCH"
            if e <= 0.8:
                return "CONSTRAINED_FIELD"
            if e <= 1.2:
                return "RESOLVING_FIELD"
            return "OPEN_FIELD"
        return "DATA_LIMITED"
    out["closure_label"] = out.apply(_label, axis=1)
    # label stability across subperiods (>=3 subperiods with same label)
    sub_labels = []
    for mc in out["mcell"]:
        g = df[df["mcell"] == mc]
        labels = {}
        for sp, sg in g.groupby("subperiod"):
            if sp == "UNKNOWN" or len(sg) < 15:
                continue
            e = _entropy(sg["next_cell"].dropna())
            if np.isnan(e):
                continue
            labels[sp] = ("LOCKED_BRANCH" if e <= 0.4 else
                          "CONSTRAINED_FIELD" if e <= 0.8 else
                          "RESOLVING_FIELD" if e <= 1.2 else "OPEN_FIELD")
        vc2 = pd.Series(labels).value_counts()
        nsp = int(pd.Series(labels).nunique() - 1) if len(labels) else 0
        # dominant label share across subperiods
        dom_share_sp = float(vc2.iloc[0] / len(labels)) if len(vc2) else np.nan
        sub_labels.append(dom_share_sp)
    out["label_subperiod_consistency"] = sub_labels
    out["verdict"] = "BRANCH_CLOSURE_SURFACE_MAPPED"
    out.to_csv(OUT / "10_BRANCH_CLOSURE_SURFACE.csv", index=False)
    return out
