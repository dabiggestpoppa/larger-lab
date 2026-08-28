from _m16base import *
from _m16base import _cache_step, _entropy, _fdr, _fmt, _slope_std, \
    _logit_slope, SUBPERIODS, DEPTH_ORDER, patch_activation_daily, \
    forcing_threshold_per_patch
from _m16p2 import _binned_entropy_slope
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


# =========================================================================
# WS8: ENTROPY LAW TRANSPORTABILITY (09_ENTROPY_TRANSPORT.csv)
# =========================================================================
def ws8_entropy_transport(df):
    maps = [("entropy_to_branch_closure", "fbe", "nbranch7", "SLOPE"),
            ("entropy_to_propagation", "fbe", "prop7", "SLOPE"),
            ("entropy_to_directional_constraint", "fbe", "next_dir",
             "ENT_SLOPE")]
    rows = []
    for mname, xcol, ycol, kind in maps:
        for sp in SUBPERIODS:
            s = df[df["subperiod"] == sp]
            if len(s) < 120:
                continue
            if kind == "ENT_SLOPE":
                v, n = _binned_entropy_slope(s[xcol].to_numpy(),
                                             s[ycol].to_numpy())
            else:
                v, n = _slope_std(s[xcol].to_numpy(), s[ycol].to_numpy())
            rows.append({"mapping": mname, "subperiod": sp, "slope": v,
                         "n": n})
    out = pd.DataFrame(rows)
    # sign consistency per mapping
    verdicts = []
    for mname, *_ in maps:
        s = out[out["mapping"] == mname]["slope"].dropna()
        if len(s) >= 3:
            pos, neg = int((s > 0).sum()), int((s < 0).sum())
            sign = "POS" if pos > neg else "NEG" if neg > pos else "FLAT"
            frac = max(pos, neg) / len(s)
            consistent = frac >= 0.8
        else:
            sign, frac, consistent = "n/a", np.nan, False
        verdicts.append({"mapping": mname, "sign": sign,
                         "sign_consistent": consistent,
                         "consistency_fraction": frac,
                         "mean_slope": float(s.mean()) if len(s) else np.nan})
    vd = pd.DataFrame(verdicts)
    n_cons = int(vd["sign_consistent"].sum())
    if n_cons == len(vd):
        verdict = "ENTROPY_TOPOLOGY_INVARIANT"
    elif n_cons >= 1:
        verdict = "ENTROPY_RESPONSE_DRIFT"
    else:
        verdict = "ENTROPY_FULL_DRIFT"
    out["verdict"] = "ENTROPY_TRANSPORT_DONE"
    vd["verdict"] = verdict
    full = pd.concat([out, vd.assign(subperiod="")], ignore_index=True)
    full.to_csv(OUT / "09_ENTROPY_TRANSPORT.csv", index=False)
    return out, vd, verdict


# =========================================================================
# WS9: COMMON-FORCING LAW TRANSPORTABILITY (10_COMMON_FORCING_TRANSPORT.csv)
# =========================================================================
FORCING_COLS = ["top500_breadth_30d", "top500_dispersion_30d", "vol_med",
                "btc_return_7d", "stablecoin_change_7d", "top3_share"]


def _loading_corr(v1, v2):
    if v1 is None or v2 is None:
        return np.nan
    a = np.asarray(v1, dtype=float)
    b = np.asarray(v2, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return np.nan
    return float(abs(np.corrcoef(a, b)[0, 1]))


def ws9_common_forcing_transport(df, pact):
    d = df.copy()
    d["d"] = pd.to_datetime(d["d"]).dt.normalize()
    # full-sample loadings
    def _loadings(sub):
        cc = [c for c in FORCING_COLS if c in sub.columns]
        X = sub[cc].to_numpy(dtype=float)
        m = ~np.isnan(X).any(axis=1)
        if m.sum() < 100:
            return None, None, 0
        sc = StandardScaler().fit(X[m])
        comp = PCA(n_components=1).fit(sc.transform(X[m]))
        return comp.components_[0], comp, int(m.sum())
    full_load, _, _ = _loadings(d)
    rows = []
    load_corrs = []
    for sp in SUBPERIODS:
        s = d[d["subperiod"] == sp]
        ld, _, nn = _loadings(s)
        c = _loading_corr(ld, full_load)
        if c == c:
            load_corrs.append(c)
        rows.append({"subperiod": sp, "loading_corr_full": c,
                     "n_complete": nn})
    coord_stable = bool(np.mean(load_corrs) >= 0.8) if load_corrs else False
    # per-patch thresholds + gains + ceilings per subperiod
    thr_rows = []
    for sp in SUBPERIODS:
        s = d[d["subperiod"] == sp]
        fx = s.set_index("d")["forcing"]
        for p in DEPTH_ORDER:
            thr, gain, nn, ceil = forcing_threshold_per_patch(
                pact, fx, p, prob=0.5, min_n=60)
            thr_rows.append({"subperiod": sp, "patch": p, "f50": thr,
                             "gain": gain, "ceiling": ceil, "n": nn})
    tr = pd.DataFrame(thr_rows)
    # stability of thresholds/gains/ceilings (in SD units / absolute)
    thr_sd_units = []
    gain_cvs = []
    ceil_ranges = []
    for p in DEPTH_ORDER:
        t = tr[tr["patch"] == p]
        f50 = t["f50"].dropna()
        g = t["gain"].dropna()
        c = t["ceiling"].dropna()
        if len(f50) >= 3:
            fx = d["forcing"].dropna()
            thr_sd_units.append(float(f50.std() / (fx.std() + 1e-12)))
        if len(g) >= 3:
            gain_cvs.append(float(g.std() / (abs(g.mean()) + 1e-12)))
        if len(c) >= 3:
            ceil_ranges.append(float(c.max() - c.min()))
    mean_thr_sd = float(np.mean(thr_sd_units)) if thr_sd_units else np.nan
    mean_gain_cv = float(np.mean(gain_cvs)) if gain_cvs else np.nan
    mean_ceil_range = float(np.mean(ceil_ranges)) if ceil_ranges else np.nan
    thr_drift = mean_thr_sd >= 0.5
    gain_drift = mean_gain_cv >= 0.30
    ceil_drift = mean_ceil_range >= 0.08
    if coord_stable and not thr_drift and not gain_drift:
        verdict = "COMMON_FORCING_INVARIANT"
    elif coord_stable and thr_drift and not gain_drift:
        verdict = "THRESHOLD_DRIFT"
    elif coord_stable and gain_drift and not thr_drift:
        verdict = "GAIN_DRIFT"
    else:
        verdict = "FULL_FORCING_DRIFT"
    summ = pd.DataFrame([{
        "item": "forcing_coordinate_loading_corr", "value": float(
            np.mean(load_corrs)) if load_corrs else np.nan,
        "stable": coord_stable},
        {"item": "threshold_sd_units", "value": mean_thr_sd,
         "stable": not thr_drift},
        {"item": "gain_cv", "value": mean_gain_cv, "stable": not gain_drift},
        {"item": "ceiling_range", "value": mean_ceil_range,
         "stable": not ceil_drift}])
    summ["verdict"] = verdict
    out = pd.concat([tr.assign(verdict="COMMON_FORCING_TRANSPORT_DONE"),
                     summ.assign(subperiod="", patch="")], ignore_index=True)
    out.to_csv(OUT / "10_COMMON_FORCING_TRANSPORT.csv", index=False)
    return out, tr, verdict


# =========================================================================
# WS10: RANK-THRESHOLD DRIFT (11_RANK_THRESHOLD_DRIFT.csv)
# =========================================================================
def _activation_rate(pact, dates, patch):
    idx = pd.DatetimeIndex(pd.to_datetime(pd.Series(dates)).dt.normalize())
    y = pact.reindex(idx)[patch].to_numpy(dtype=float)
    y = y[~np.isnan(y)]
    return float(y.mean()) if len(y) else np.nan


def ws10_rank_threshold_drift(df, pact):
    d = df.copy()
    rows = []
    for p in DEPTH_ORDER:
        for prob in [0.25, 0.50, 0.75]:
            for sp in SUBPERIODS:
                s = d[d["subperiod"] == sp]
                if len(s) < 80:
                    continue
                thr, gain, nn, ceil = forcing_threshold_per_patch(
                    pact, s.set_index("d")["forcing"], p, prob=prob,
                    min_n=60)
                rate = _activation_rate(pact, s["d"], p)
                sat = "SATURATED_ON" if (rate == rate and rate >= 0.95) \
                    else "SATURATED_OFF" if (rate == rate and rate <= 0.05) \
                    else ""
                rows.append({"patch": p, "prob": prob, "subperiod": sp,
                             "forcing_threshold": thr, "gain": gain,
                             "ceiling": ceil, "n": nn,
                             "activation_rate": rate, "saturation": sat})
    out = pd.DataFrame(rows)
    # stationarity per patch: SD of 50% threshold in SD units; saturated
    # patches (always-on / never-on) have no threshold to move -> STATIONARY
    fx = d["forcing"].dropna()
    fx_sd = fx.std() + 1e-12
    verdicts = []
    for p in DEPTH_ORDER:
        sub = out[(out["patch"] == p) & (out["prob"] == 0.50)]
        sats = sub["saturation"].replace("", np.nan).dropna()
        t = sub["forcing_threshold"].dropna()
        if len(sats) >= 3 and (sats == sats.iloc[0]).all():
            sd_u = np.nan
            v = "STATIONARY_SATURATED"
        elif len(t) >= 3:
            sd_u = float(t.std() / fx_sd)
            v = "STATIONARY" if sd_u < 0.5 else "DRIFT"
        else:
            sd_u, v = np.nan, "DATA_LIMITED"
        verdicts.append({"patch": p, "f50_sd_units": sd_u,
                         "patch_verdict": v})
    vd = pd.DataFrame(verdicts)
    n_drift = int((vd["patch_verdict"] == "DRIFT").sum())
    n_stat = int((vd["patch_verdict"].isin(
        ["STATIONARY", "STATIONARY_SATURATED"])).sum())
    if n_drift == 0:
        verdict = "THRESHOLDS_STATIONARY"
    elif n_stat >= 1:
        verdict = "DEEP_THRESHOLDS_DRIFT"
    else:
        verdict = "THRESHOLDS_DRIFT"
    out["verdict"] = "RANK_THRESHOLD_DRIFT_DONE"
    vd["verdict"] = verdict
    full = pd.concat([out, vd.assign(prob=np.nan, subperiod="")],
                     ignore_index=True)
    full.to_csv(OUT / "11_RANK_THRESHOLD_DRIFT.csv", index=False)
    return out, vd, verdict


# =========================================================================
# WS11: SATURATION-LAW DRIFT (12_SATURATION_LAW_DRIFT.csv)
# =========================================================================
def ws11_saturation_law_drift(df, pact):
    d = df.copy()
    rows = []
    for sp in SUBPERIODS:
        s = d[d["subperiod"] == sp]
        if len(s) < 80:
            continue
        for p in DEPTH_ORDER:
            thr, gain, nn, ceil = forcing_threshold_per_patch(
                pact, s.set_index("d")["forcing"], p, prob=0.5, min_n=60)
            rate = _activation_rate(pact, s["d"], p)
            sat = "SATURATED_ON" if (rate == rate and rate >= 0.95) \
                else "SATURATED_OFF" if (rate == rate and rate <= 0.05) \
                else ""
            rows.append({"subperiod": sp, "patch": p, "f50": thr,
                         "gain": gain, "ceiling": ceil, "n": nn,
                         "activation_rate": rate, "saturation": sat})
    out = pd.DataFrame(rows)
    fx = d["forcing"].dropna()
    fx_sd = fx.std() + 1e-12
    verdicts = []
    for p in DEPTH_ORDER:
        sub = out[out["patch"] == p]
        sats = sub["saturation"].replace("", np.nan).dropna()
        f50 = sub["f50"].dropna()
        g = sub["gain"].dropna()
        c = sub["ceiling"].dropna()
        if len(sats) >= 3 and (sats == sats.iloc[0]).all():
            verdicts.append({"patch": p, "f50_sd_units": np.nan,
                             "gain_cv": np.nan, "ceiling_range": np.nan,
                             "saturation_verdict": "SATURATED_STABLE"})
            continue
        if len(f50) < 3:
            verdicts.append({"patch": p, "f50_sd_units": np.nan,
                             "gain_cv": np.nan, "ceiling_range": np.nan,
                             "saturation_verdict": "DATA_LIMITED"})
            continue
        sd_u = float(f50.std() / fx_sd)
        gain_cv = float(g.std() / (abs(g.mean()) + 1e-12)) if len(g) >= 3 \
            else np.nan
        ceil_r = float(c.max() - c.min()) if len(c) >= 3 else np.nan
        moved_thr = sd_u >= 0.5
        changed_gain = gain_cv >= 0.30 if gain_cv == gain_cv else False
        shape_change = ceil_r >= 0.08 if ceil_r == ceil_r else False
        if shape_change:
            v = "SHAPE_CHANGE"
        elif moved_thr:
            v = "SAME_SHAPE_MOVED_THRESHOLD"
        elif changed_gain:
            v = "SAME_THRESHOLD_CHANGED_GAIN"
        else:
            v = "STABLE"
        verdicts.append({"patch": p, "f50_sd_units": sd_u, "gain_cv":
                         gain_cv, "ceiling_range": ceil_r,
                         "saturation_verdict": v})
    vd = pd.DataFrame(verdicts)
    counts = vd["saturation_verdict"].value_counts()
    if "DATA_LIMITED" in counts and counts["DATA_LIMITED"] >= 5:
        verdict = "DATA_LIMITED"
    else:
        vc = vd[vd["saturation_verdict"] != "DATA_LIMITED"]
        verdict = str(vc["saturation_verdict"].mode().iloc[0]) if len(vc) \
            else "DATA_LIMITED"
    out["verdict"] = "SATURATION_LAW_DRIFT_DONE"
    vd["verdict"] = verdict
    full = pd.concat([out, vd.assign(subperiod="", patch="")],
                     ignore_index=True)
    full.to_csv(OUT / "12_SATURATION_LAW_DRIFT.csv", index=False)
    return out, vd, verdict
