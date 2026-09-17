from _m16base import *
from _m16base import _cache_step, _entropy, _fdr, _fmt, _js_distance, \
    _ztest_prop, _cohen_d, _slope_std, _logit_slope, SUBPERIODS


def _binned_entropy_slope(x, y):
    """Slope of entropy(y) across x-terciles (per 1 SD of x). Negative =
    more x reduces categorical entropy (more constraint)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y)
    m = ~np.isnan(x)
    x, y = x[m], y[m]
    if len(x) < 60:
        return np.nan, 0
    q = np.quantile(x, [1 / 3, 2 / 3])
    bins = np.digitize(x, q)
    xs = (x - x.mean()) / (x.std() + 1e-12)
    cents, ents = [], []
    for k in [0, 1, 2]:
        yy = y[bins == k]
        if len(yy) < 20:
            continue
        cents.append(xs[bins == k].mean())
        ents.append(_entropy(pd.Series(yy)))
    if len(cents) < 2:
        return np.nan, 0
    c = np.polyfit(np.array(cents), np.array(ents), 1)
    return float(c[0]), int(len(x))


# =========================================================================
# WS3: COVARIATE SHIFT vs CONDITIONAL SHIFT (04_COVARIATE_CONDITIONAL_SHIFT.csv)
# =========================================================================
COVARIATES = {
    "breadth": "top500_breadth_30d", "dispersion": "top500_dispersion_30d",
    "forcing": "forcing", "age": "age_in_cell", "entropy": "fbe",
    "vol": "vol_med", "btc7": "btc_return_7d",
    "rank_depth": "rank_depth_rel", "concentration": "top3_share",
    "stablecoin": "stablecoin_change_7d",
}


def ws3_covariate_conditional_shift(df):
    d = df.sort_values("d").reset_index(drop=True)
    cut = int(0.8 * len(d))
    early, late = d.iloc[:cut], d.iloc[cut:]
    rows = []
    n_cov_sig = 0
    for label, col in COVARIATES.items():
        a = early[col].to_numpy(dtype=float)
        b = late[col].to_numpy(dtype=float)
        a = a[~np.isnan(a)]
        b = b[~np.isnan(b)]
        if len(a) < 50 or len(b) < 50:
            rows.append({"object": "P(X)", "name": label, "metric":
                         "cohen_d", "value": np.nan, "n_early": len(a),
                         "n_late": len(b), "note": "insufficient"})
            continue
        dd = _cohen_d(a, b)
        _, p = ranksums(a, b) if (len(a) >= 10 and len(b) >= 10) else \
            (np.nan, np.nan)
        sig = (abs(dd) >= 0.3 and p < 0.05) if (dd == dd and p == p) else False
        n_cov_sig += int(sig)
        rows.append({"object": "P(X)", "name": label, "metric": "cohen_d",
                     "value": dd, "p": p, "n_early": len(a), "n_late":
                     len(b), "sig_shift": sig})
    # P(cell) on 6-cell surface
    ec = early["grp6"].value_counts(normalize=True)
    lc = late["grp6"].value_counts(normalize=True)
    js_cell = _js_distance(ec, lc)
    rows.append({"object": "P(cell)", "name": "grp6_occupancy", "metric":
                 "js_distance", "value": js_cell, "n_early": len(early),
                 "n_late": len(late)})
    # P(outcome) base rates
    for col, label in [("prop7", "propagation"), ("ren7", "reentry"),
                       ("rank7", "rank_recruitment"), ("tail7", "tail")]:
        pa, na = early[col].mean(), len(early)
        pb, nb = late[col].mean(), len(late)
        z, p = _ztest_prop(pa, na, pb, nb)
        rows.append({"object": "P(outcome)", "name": label, "metric":
                     "rate_early", "value": pa, "rate_late": pb, "p": p,
                     "n_early": na, "n_late": nb})
    # P(outcome | cell) per 6-cell group
    g6 = sorted(df["grp6"].dropna().unique())
    pvals = []
    deltas = []
    for g in g6:
        a = early.loc[early["grp6"] == g, "prop7"]
        b = late.loc[late["grp6"] == g, "prop7"]
        if len(a) < 30 or len(b) < 30:
            continue
        pa, pb = float(a.mean()), float(b.mean())
        _, p = _ztest_prop(pa, len(a), pb, len(b))
        pvals.append((g, pa, pb, p))
        deltas.append(abs(pa - pb))
    pvals.sort(key=lambda t: t[0])
    if pvals:
        padj = _fdr(np.array([t[3] for t in pvals]))
        n_sig = int((padj < FDR_Q).sum())
        mean_delta = float(np.mean(deltas))
        for (g, pa, pb, p), pa2 in zip(pvals, padj):
            rows.append({"object": "P(outcome|cell)", "name": f"grp6:{g}",
                         "metric": "prop7_early", "value": pa,
                         "prop7_late": pb, "p_raw": p, "p_fdr": pa2,
                         "sig": bool(pa2 < FDR_Q)})
    else:
        n_sig, mean_delta = 0, np.nan
    # verdict
    outcome_base_p = None
    for r in rows:
        if r.get("object") == "P(outcome)" and r.get("name") == \
                "propagation":
            outcome_base_p = r.get("p")
    if n_sig >= 3 or (mean_delta == mean_delta and mean_delta >= 0.05):
        if n_cov_sig >= 4 or js_cell >= 0.10:
            verdict = "MIXED_DRIFT"
        else:
            verdict = "TRANSFER_FUNCTION_DRIFT"
    elif n_cov_sig >= 4 or js_cell >= 0.10:
        verdict = "COVARIATE_SHIFT"
    elif outcome_base_p is not None and outcome_base_p < 0.05:
        verdict = "BASE_RATE_SHIFT"
    else:
        verdict = "NO_SHIFT"
    out = pd.DataFrame(rows)
    out["verdict"] = verdict
    out["n_covariate_shift_sig"] = n_cov_sig
    out["n_cell_transfer_sig"] = n_sig
    out["mean_cell_delta"] = mean_delta
    out.to_csv(OUT / "04_COVARIATE_CONDITIONAL_SHIFT.csv", index=False)
    return out


# =========================================================================
# WS4: STATE-LOCAL TRANSFER FUNCTIONS (05_STATE_LOCAL_TRANSFER_FUNCTIONS.csv)
# =========================================================================
MAPPINGS = [
    ("forcing_to_propagation", "forcing", "prop7", "LOGIT"),
    ("forcing_to_rank_recruitment", "forcing", "rank7", "LOGIT"),
    ("age_to_propagation", "age_in_cell", "prop7", "SLOPE"),
    ("age_to_reentry", "age_in_cell", "ren7", "SLOPE"),
    ("entropy_to_propagation", "fbe", "prop7", "SLOPE"),
    ("entropy_to_directional_constraint", "fbe", "next_dir", "ENT_SLOPE"),
    ("activation_depth_to_propagation", "spatial_activation", "prop7",
     "LOGIT"),
]


def ws4_state_local_transfer(df):
    g6 = sorted(df["grp6"].dropna().unique())
    rows = []
    for g in g6:
        sub = df[df["grp6"] == g]
        for mname, xcol, ycol, kind in MAPPINGS:
            slopes = {}
            for sp in SUBPERIODS:
                s = sub[sub["subperiod"] == sp]
                if len(s) < 50:
                    slopes[sp] = np.nan
                    continue
                if kind == "LOGIT":
                    v, _ = _logit_slope(s[xcol].to_numpy(),
                                        s[ycol].to_numpy())
                elif kind == "ENT_SLOPE":
                    v, _ = _binned_entropy_slope(s[xcol].to_numpy(),
                                                 s[ycol].to_numpy())
                else:
                    v, _ = _slope_std(s[xcol].to_numpy(), s[ycol].to_numpy())
                slopes[sp] = v
            vals = np.array([slopes[sp] for sp in SUBPERIODS])
            vals = vals[~np.isnan(vals)]
            if len(vals) >= 3:
                mean_s = float(vals.mean())
                sd_s = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
                same_sign = bool(np.all(vals > 0) or np.all(vals < 0))
                # sign consistency: same sign OR |mean| > 2*sd
                sign_consistent = same_sign or (
                    sd_s > 0 and abs(mean_s) > 2 * sd_s)
                law_verdict = "INVARIANT_SLOPE" if sign_consistent else \
                    "DRIFT_SLOPE"
            else:
                mean_s, sd_s, sign_consistent, law_verdict = \
                    np.nan, np.nan, False, "DATA_LIMITED"
            row = {"surface": "6_cell", "group": g, "mapping": mname,
                   "x": xcol, "y": ycol}
            for sp in SUBPERIODS:
                row[f"slope_{sp}"] = slopes[sp]
            row.update({"mean_slope": mean_s, "sd_slope": sd_s,
                        "sign_consistent": sign_consistent,
                        "n_valid_periods": int(len(vals)),
                        "law_verdict": law_verdict})
            rows.append(row)
    out = pd.DataFrame(rows)
    # mapping-level summary
    summ = []
    for mname, *_ in MAPPINGS:
        sub = out[out["mapping"] == mname]
        n_inv = int((sub["law_verdict"] == "INVARIANT_SLOPE").sum())
        n_dl = int((sub["law_verdict"] == "DATA_LIMITED").sum())
        summ.append({"mapping": mname, "n_groups": int(len(sub)),
                     "n_invariant": n_inv, "n_drift": int(len(sub) - n_inv -
                     n_dl), "n_data_limited": n_dl,
                     "invariant_fraction": float(n_inv / len(sub))
                     if len(sub) else np.nan})
    sm = pd.DataFrame(summ)
    sm["verdict"] = "TRANSFER_FUNCTION_MAP_DONE"
    out["verdict"] = "TRANSFER_FUNCTION_MAP_DONE"
    # append summary rows into the same CSV (as a block)
    full = pd.concat([out, sm.assign(group="", mapping=sm["mapping"])],
                     ignore_index=True)
    full.to_csv(OUT / "05_STATE_LOCAL_TRANSFER_FUNCTIONS.csv", index=False)
    return out, sm
