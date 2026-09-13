from _m14base import *
from _m14base import _age_band, _entropy, _fdr, _fmt, _cohen_d


# Direction families map to the ev_* event flags on dfw.
UP_FAM = {"BROAD_UP": ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE"],
          "ISOLATED_UP": ["ev_ISOLATED_UPSIDE"]}
DOWN_FAM = {"BROAD_DOWN": ["ev_COORDINATED_DOWNSIDE"],
            "ISOLATED_DOWN": ["ev_ISOLATED_DOWNSIDE_EXTREME",
                              "ev_LOCAL_CLUSTER_DOWNSIDE"]}
FAM_MAP = {k: v for d in (UP_FAM, DOWN_FAM) for k, v in d.items()}
PERM_COORDS = ["top500_breadth_30d", "top500_dispersion_30d",
               "btc_return_7d", "eth_btc_relative_return_7d", "vol_med",
               "top3_share"]
AB_EDGE = ["AGE_1", "AGE_15_PLUS"]


def _attach_branch(dfw):
    from _m14p2 import _attach_entropy_and_branches
    return _attach_entropy_and_branches(dfw)


def _dir_df(dfw):
    """Daily frame with per-family flags plus a signed dir_today / next_dir.

    next_dir collapses up(+1) / down(-1) / flat(0) one day forward.
    """
    dc = _attach_branch(dfw)
    dc["ab"] = dc["age_in_cell"].apply(_age_band)
    upcols = [c for d in UP_FAM.values() for c in d if c in dc.columns]
    dncols = [c for d in DOWN_FAM.values() for c in d if c in dc.columns]
    dc["dir_today"] = np.sign(dc[upcols].sum(axis=1) - dc[dncols].sum(axis=1))
    dc["next_dir"] = dc["dir_today"].shift(-1)
    for fam, cols in FAM_MAP.items():
        cols = [c for c in cols if c in dc.columns]
        dc[f"fam_{fam}"] = (dc[cols].sum(axis=1) > 0).astype(int)
    return dc


# =========================================================================
# WS16: DIRECTIONAL ASYMMETRY DEEP MAP (18_DIRECTIONAL_ASYMMETRY_DEEP_MAP.csv)
# =========================================================================
def ws16_directional_deep_map(dfw):
    df = _dir_df(dfw)
    df["fbe_q"] = pd.qcut(df["fwd_branch_entropy"].rank(method="first"), 3,
                          labels=["ENT_LOW", "ENT_MID", "ENT_HIGH"])
    rows = []
    for fam, cols in FAM_MAP.items():
        fam_days = df[df[f"fam_{fam}"] == 1]
        for cell in CELLS:
            g = fam_days[fam_days["cell"] == cell]
            if len(g) < 30:
                continue
            for abn in AB_EDGE:
                gg = g[g["ab"] == abn]
                if len(gg) < 20 or gg["next_dir"].notna().sum() < 20:
                    continue
                for ent in ["ENT_LOW", "ENT_MID", "ENT_HIGH"]:
                    gg2 = gg[gg["fbe_q"] == ent]
                    if len(gg2) < 15:
                        continue
                    rows.append({
                        "family": fam, "cell": cell, "age_band": abn,
                        "entropy_tercile": ent, "n": int(len(gg2)),
                        "med_fbe": float(gg2["fwd_branch_entropy"].mean()),
                        "p_up_next": float((gg2["next_dir"] > 0).mean()),
                        "p_down_next": float((gg2["next_dir"] < 0).mean()),
                        "dir_entropy": float(_entropy(gg2["next_dir"]))})
    out = pd.DataFrame(rows)
    if len(out):
        bias = out["p_up_next"].fillna(0) - out["p_down_next"].fillna(0)
        n_biased = int((bias.abs() >= 0.25).sum())
        n_structured = int((out["dir_entropy"] <= 0.8).sum())
        out["verdict"] = ("DIRECTION_DECOMPOSED" if n_structured >= 4 else
                          "DIRECTION_LOCALLY_CONSTRAINED" if n_structured >= 1
                          else "DIRECTION_WEAKLY_CONSTRAINED")
        out["n_biased_strata"] = n_biased
        out["n_low_entropy_strata"] = n_structured
    else:
        out = pd.DataFrame([{"verdict": "DATA_LIMITED"}])
    out.to_csv(OUT / "18_DIRECTIONAL_ASYMMETRY_DEEP_MAP.csv", index=False)
    return out


# =========================================================================
# WS17: UPSIDE PERMISSION GEOMETRY (19_UPSIDE_PERMISSION_GEOMETRY.csv)
# =========================================================================
def ws17_upside_permission_geometry(dfw):
    df = dfw.copy()
    for c in ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE"]:
        if c not in df.columns:
            df[c] = 0
    df["broad_up_next"] = (df["ev_BAND_BROAD_UPSIDE"].shift(-1) +
                           df["ev_MULTI_BAND_UPSIDE"].shift(-1) > 0).astype(int)
    df = df.dropna(subset=PERM_COORDS + ["broad_up_next"]).copy()
    y = df["broad_up_next"].to_numpy()
    if y.sum() < 50:
        out = pd.DataFrame([{"verdict": "DATA_LIMITED"}])
        out.to_csv(OUT / "19_UPSIDE_PERMISSION_GEOMETRY.csv", index=False)
        return out
    Xf = df[PERM_COORDS].to_numpy(dtype=float)
    full = LogisticRegression(max_iter=1000).fit(Xf, y)
    full_auc = roc_auc_score(y, full.predict_proba(Xf)[:, 1])
    rows = []
    for coord in PERM_COORDS:
        x = df[coord].to_numpy(dtype=float)
        med = float(np.nanmedian(x))
        cov_hi = float((x >= med)[y == 1].mean())
        cov_lo = float((x >= med)[y == 0].mean())
        loo = np.nan
        try:
            Xb = df[[c for c in PERM_COORDS if c != coord]].to_numpy(
                dtype=float)
            mb = LogisticRegression(max_iter=1000).fit(Xb, y)
            loo = roc_auc_score(y, mb.predict_proba(Xb)[:, 1])
        except Exception:
            pass
        delta = (full_auc - loo) if not np.isnan(loo) else np.nan
        rows.append({"coord": coord, "coverage_among_broad_up": cov_hi,
                     "coverage_among_rest": cov_lo, "delta_auc_remove": delta,
                     "full_model_auc": float(full_auc)})
    out = pd.DataFrame(rows)

    def _cls(r):
        if not np.isnan(r["coverage_among_broad_up"]) and \
                r["coverage_among_broad_up"] >= 0.85 and \
                r["coverage_among_broad_up"] - r["coverage_among_rest"] >= 0.15:
            return "NECESSARY_FOR_BROAD_UP"
        if not np.isnan(r["delta_auc_remove"]) and r["delta_auc_remove"] >= 0.03:
            return "CONDITIONAL_GATE"
        if not np.isnan(r["coverage_among_broad_up"]) and \
                r["coverage_among_broad_up"] - r["coverage_among_rest"] >= 0.20:
            return "SUFFICIENT_LOCAL"
        return "REDUNDANT"
    out["necessity"] = out.apply(_cls, axis=1)
    n_nec = int((out["necessity"] == "NECESSARY_FOR_BROAD_UP").sum())
    out["verdict"] = ("PERMISSION_SINGLE_GATE" if n_nec >= 1 else
                      "PERMISSION_MULTI_COORDINATE")
    out.to_csv(OUT / "19_UPSIDE_PERMISSION_GEOMETRY.csv", index=False)
    return out


# =========================================================================
# WS18: DOWNSIDE LOCALIZATION (20_DOWNSIDE_LOCALIZATION.csv)
# =========================================================================
def ws18_downside_localization(ev):
    e = ev.copy()
    e["d"] = pd.to_datetime(e["historical_date"]).dt.normalize()
    e["abs_ret"] = e["ret_1d"].abs()
    e["rev"] = (e["reversal"] == 1).astype(int)
    med_rank = float(e["rank"].median())
    med_z1 = float(e["z1"].median())
    med_abs = float(e["abs_ret"].median())
    e["rank_hi"] = (e["rank"] >= med_rank).astype(int)
    e["sigma_hi"] = (e["z1"] >= med_z1).astype(int)
    e["abs_hi"] = (e["abs_ret"] >= med_abs).astype(int)
    rows = []
    axes = [("rank_depth", "rank_hi"), ("sigma_magnitude", "sigma_hi"),
            ("abs_move", "abs_hi")]
    structured = 0
    for label, ax in axes:
        for v in [0, 1]:
            g = e[e[ax] == v]
            if len(g) < 30:
                continue
            rows.append({"axis": label, "value": str(v), "n": int(len(g)),
                         "p_reversal": float(g["rev"].mean())})
    out = pd.DataFrame(rows)
    if len(out):
        for label, ax in axes:
            gg = out[out["axis"] == label]
            if len(gg) == 2 and abs(float(gg["p_reversal"].diff().iloc[1])) >= 0.05:
                structured += 1
        out["verdict"] = ("MULTIPLE_DOWNSIDE_SPECIES" if structured >= 2 else
                          "LOCAL_DOWNSIDE_GEOMETRY" if structured >= 1 else
                          "TRULY_UNSTRUCTURED")
        out["n_structured_axes"] = structured
    else:
        out = pd.DataFrame([{"verdict": "DATA_LIMITED"}])
    out.to_csv(OUT / "20_DOWNSIDE_LOCALIZATION.csv", index=False)
    return out


# =========================================================================
# WS19: DIRECTIONAL BRANCH ENTROPY LADDER (21_DIRECTIONAL_BRANCH_ENTROPY.csv)
# =========================================================================
CONSTRAINT_COLS = [
    ("STATE", "cell"), ("AGE", "ab"), ("ENTROPY", "fbe"),
    ("BREADTH", "top500_breadth_30d"), ("ACTIVATION_DEPTH", "rank_depth_rel"),
]


def ws19_directional_branch_entropy(dfw):
    df = _dir_df(dfw)
    df["fbe"] = df["fwd_branch_entropy"]
    g = df.dropna(subset=["next_dir"]).copy()
    base_ent = float(_entropy(g["next_dir"]))
    rows = [{"constraint_set": "GLOBAL", "n": int(len(g)),
             "dir_entropy": base_ent}]
    cols_used = []
    labels = []
    for name, coln in CONSTRAINT_COLS:
        if coln not in g.columns or g[coln].isna().all():
            continue
        cols_used = cols_used + [coln]
        labels = labels + [name]
        ent = []
        for _, sub in g.groupby(cols_used, observed=True):
            ent.append(_entropy(sub["next_dir"]))
        ent = [x for x in ent if not np.isnan(x)]
        cond_ent = float(np.mean(ent)) if ent else np.nan
        rows.append({"constraint_set": " + ".join(labels), "n": int(len(g)),
                     "dir_entropy": cond_ent})
    out = pd.DataFrame(rows)
    drops = []
    for i in range(1, len(rows)):
        a = rows[i - 1]["dir_entropy"]
        b = rows[i]["dir_entropy"]
        if a == a and b == b:
            drops.append((rows[i]["constraint_set"], float(a - b)))
    largest = max(drops, key=lambda x: x[1]) if drops else ("", 0.0)
    out["largest_drop_set"] = largest[0]
    out["largest_drop"] = largest[1]
    out["verdict"] = (f"DIRECTION_CONSTRAINED_MOSTLY_AT_{largest[0].strip()}"
                      if largest[1] >= 0.06 else
                      "DIRECTION_WEAKLY_CONSTRAINED")
    out.to_csv(OUT / "21_DIRECTIONAL_BRANCH_ENTROPY.csv", index=False)
    return out