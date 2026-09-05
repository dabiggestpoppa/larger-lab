from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split

INIT_COORDS = ["top500_breadth_30d", "top500_dispersion_30d", "top3_share",
               "rank_depth_rel", "vol_med", "btc_return_7d",
               "eth_btc_relative_return_7d"]


# =========================================================================
# WS3: FAILURE GEOMETRY -> INITIATION GEOMETRY (04_INITIATION_GEOMETRY.csv)
# =========================================================================

def ws3_initiation_geometry(dfw):
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
        suc = ok["success"].to_numpy() == 1
        for coord in INIT_COORDS:
            if coord not in ok.columns:
                continue
            g_s = ok.loc[suc, coord].to_numpy(dtype=float)
            g_f = ok.loc[~suc, coord].to_numpy(dtype=float)
            g_s = g_s[~np.isnan(g_s)]
            g_f = g_f[~np.isnan(g_f)]
            if len(g_s) < 20 or len(g_f) < 20:
                continue
            try:
                stat, p = ranksums(g_s, g_f)
            except Exception:
                p = np.nan
            # effect: mean-standardized difference
            pool = np.concatenate([g_s, g_f])
            sd = float(pool.std()) if pool.std() > 0 else 1.0
            rows.append({"cell": cell, "coord": coord,
                         "n_success": int(ok["success"].sum()),
                         "n_fail": int(ok["fail"].sum()),
                         "mean_success": float(np.nanmean(g_s)),
                         "mean_fail": float(np.nanmean(g_f)),
                         "effect_success_fail": float(np.nanmean(g_s) -
                                                      np.nanmean(g_f)),
                         "cohens_d": float((np.nanmean(g_s) -
                                            np.nanmean(g_f)) / sd),
                         "p": float(p)})
    out = pd.DataFrame(rows)
    if len(out):
        q = _fdr(out["p"].to_numpy())
        out["q"] = q
        n_sig = (out["q"] <= FDR_Q).sum()
        out["verdict"] = ("MULTI_COORDINATE_INITIATION" if n_sig >= 3 else
                         "CONDITIONAL_INITIATION_RULE" if n_sig >= 1 else
                         "NO_STABLE_INITIATION")
        # per-cell verdict
        out = out.assign(
            cell_verdict=out.groupby("cell")["q"].transform(
                lambda qs: "INITIATION_PRIMITIVE" if (qs <= FDR_Q).sum() >= 2
                else "CONDITIONAL_INITIATION_RULE"
                if (qs <= FDR_Q).sum() >= 1 else "NO_STABLE_INITIATION"))
        # global signature row
        sig = out[out["q"] <= FDR_Q]
        top = sig.sort_values("cohens_d", key=lambda s: s.abs(),
                              ascending=False).head(3)["coord"].tolist() \
            if len(sig) else []
        out.attrs["verdict"] = (
            f"n_significant={n_sig} top={top}")
    out.to_csv(OUT / "04_INITIATION_GEOMETRY.csv", index=False)
    return out


# =========================================================================
# WS4: INITIATION NECESSITY / SUFFICIENCY AUDIT (05_INITIATION_PRIMITIVE_AUDIT.csv)
# =========================================================================

def ws4_initiation_primitive_audit(dfw, init_geom):
    df = dfw.copy()
    df["fwd7_state"] = df["state"].shift(-7)
    df["success"] = df["fwd7_state"].isin(SUCCESS_LABELS).astype(int)
    df["fail"] = (df["fwd7_state"] == REENTRY_LABEL).astype(int)
    rows = []
    for cell in CELLS:
        sub = df[df["cell"] == cell].copy()
        ok = sub[(sub["success"] == 1) | (sub["fail"] == 1)].dropna(
            subset=INIT_COORDS)
        if len(ok) < 60 or ok["success"].sum() < 20:
            continue
        ok = ok.copy()
        y = ok["success"].to_numpy()
        X_all = ok[INIT_COORDS].to_numpy(dtype=float)
        try:
            mfull = LogisticRegression(max_iter=1000).fit(X_all, y)
            full_auc = roc_auc_score(y, mfull.predict_proba(X_all)[:, 1])
        except Exception:
            full_auc = np.nan
        for coord in INIT_COORDS:
            x = ok[coord].to_numpy(dtype=float)
            med = float(np.nanmedian(x))
            above = (x >= med)
            cov_suc = float(above[y == 1].mean())
            cov_fail = float(above[y == 0].mean())
            # leave-one-coordinate-out logistic (fwd7 success)
            x_extras = [c for c in INIT_COORDS if c != coord]
            loo_auc = np.nan
            try:
                Xb = ok[x_extras].to_numpy(dtype=float)
                mb = LogisticRegression(max_iter=1000).fit(Xb, y)
                loo_auc = roc_auc_score(y, mb.predict_proba(Xb)[:, 1])
            except Exception:
                loo_auc = np.nan
            delta = (full_auc - loo_auc) if (full_auc not in (None, np.nan)
                     and loo_auc not in (None, np.nan)) else np.nan
            rows.append({"cell": cell, "coord": coord, "median": med,
                         "coverage_among_success": float(cov_suc),
                         "coverage_among_fail": float(cov_fail),
                         "full_model_auc": float(full_auc)
                         if full_auc is not None else np.nan,
                         "auc_without": loo_auc,
                         "delta_auc_remove": delta,
                         "n_success": int(y.sum()),
                         "n_fail": int((1 - y).sum())})
    out = pd.DataFrame(rows)
    if len(out):
        def _cls(r):
            cov = r["coverage_among_success"]
            cov_f = r["coverage_among_fail"]
            d = r["delta_auc_remove"]
            # NECESSARY: near-universal among successes, rare among failures
            if cov >= 0.85 and cov_f < 0.70:
                return "NECESSARY_LOCAL"
            # STRONG DISCRIMINATOR: high delta (removing it hurts a lot)
            if d is not None and not np.isnan(d) and d >= 0.03:
                return "CONDITIONAL"
            if cov - cov_f >= 0.15:
                return "SUFFICIENT_LOCAL"
            if d is not None and not np.isnan(d) and d >= 0.01:
                return "SUBSTITUTABLE"
            return "REDUNDANT"
        out["necessity"] = out.apply(_cls, axis=1)
        out["verdict"] = "INITIATION_PRIMITIVE_AUDIT_BUILT"
    out.to_csv(OUT / "05_INITIATION_PRIMITIVE_AUDIT.csv", index=False)
    return out