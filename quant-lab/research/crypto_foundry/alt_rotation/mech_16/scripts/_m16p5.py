from _m16base import *
from _m16base import _cache_step, _entropy, _fdr, _fmt, _logit_slope, \
    _slope_std, _js_distance, SUBPERIODS, DEPTH_ORDER, \
    forcing_threshold_per_patch
from scipy.stats import ttest_ind, spearmanr, rankdata
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score


# =========================================================================
# WS12: FIELD-LAW CHANGEPOINT SCAN (13_CHANGEPOINT_SCAN.csv)
# =========================================================================
def _rolling_daily_series(df, fn, step=ROLL_STEP, win=ROLL_WIN):
    """Compute fn(window) on rolling windows; returns (dates, values)."""
    d = df.sort_values("d").reset_index(drop=True)
    n = len(d)
    dates, vals = [], []
    for i in range(win, n + 1, step):
        w = d.iloc[i - win:i]
        v = fn(w)
        if v == v:
            dates.append(d["d"].iloc[i - 1])
            vals.append(v)
    return np.array(dates, dtype="datetime64[D]"), np.array(vals, float)


def _two_segment_break(x, dates):
    """Grid-search two-segment t-test; returns dict or None."""
    n = len(x)
    if n < 20:
        return None
    best = None
    for b in range(8, n - 8, 2):
        a, c = x[:b], x[b:]
        if a.std() == 0 and c.std() == 0:
            continue
        t, p = ttest_ind(a, c, equal_var=False)
        if np.isnan(t):
            continue
        if best is None or abs(t) > best[0]:
            best = (abs(t), t, p, b)
    if best is None:
        return None
    _, t, p, b = best
    return {"date": str(dates[b - 1])[:10], "t": float(t), "p": float(p),
            "n_early": int(b), "n_late": int(n - b),
            "mean_early": float(x[:b].mean()), "mean_late": float(x[b:].mean())}


def _cusum_break(x, dates):
    n = len(x)
    if n < 20:
        return None
    mu = x.mean()
    sd = x.std(ddof=1)
    if sd == 0:
        return None
    S = np.cumsum(x - mu)
    b = int(np.argmax(np.abs(S)))
    z = float(np.abs(S[b]) / (sd * np.sqrt(n)))
    return {"date": str(dates[b])[:10], "max_cusum": float(S[b]),
            "z": z, "sig": z >= 1.5}


def _crossing_date(x, dates):
    """First point after which a 12-pt rolling mean stays on the other side
    of the full mean for >= 8 consecutive points."""
    n = len(x)
    if n < 30:
        return None
    mu = x.mean()
    rm = pd.Series(x).rolling(12, min_periods=6).mean().to_numpy()
    side = np.where(rm > mu, 1, np.where(rm < mu, -1, 0))
    for i in range(30, n):
        if side[i] != 0 and side[i - 12:i].sum() == side[i] * 12:
            return str(dates[i - 6])[:10]
    return None


def ws12_changepoint_scan(df, pact, ev):
    d = df.sort_values("d").reset_index(drop=True).copy()
    d["d"] = pd.to_datetime(d["d"])
    # coordinate series builders
    def _coord_prop_state(w):
        return float(w["prop7"].mean())
    def _coord_rank_thr(w):
        thr, _, _, _ = forcing_threshold_per_patch(
            pact, w.set_index("d")["forcing"], "1001-1500", prob=0.5,
            min_n=40)
        return thr
    def _coord_age_hazard(w):
        old = w[w["age_in_cell"] >= 14]["prop7"].mean() if \
            (w["age_in_cell"] >= 14).sum() >= 20 else np.nan
        young = w[w["age_in_cell"] <= 3]["prop7"].mean() if \
            (w["age_in_cell"] <= 3).sum() >= 20 else np.nan
        return old - young if (old == old and young == young) else np.nan
    def _coord_entropy_resp(w):
        v, _ = _logit_slope(w["fbe"].to_numpy(), w["prop7"].to_numpy())
        return v
    def _coord_forcing_resp(w):
        v, _ = _logit_slope(w["forcing"].to_numpy(), w["prop7"].to_numpy())
        return v
    coords = {
        "state_propagation": _coord_prop_state,
        "rank_threshold_deep": _coord_rank_thr,
        "state_age_hazard_gap": _coord_age_hazard,
        "entropy_response_slope": _coord_entropy_resp,
        "forcing_response_slope": _coord_forcing_resp,
    }
    rows = []
    tsegs = {}
    for cname, fn in coords.items():
        dates, x = _rolling_daily_series(d, fn)
        if len(x) < 20:
            rows.append({"coordinate": cname, "candidate": False,
                         "note": "insufficient windows"})
            continue
        tseg = _two_segment_break(x, dates)
        cus = _cusum_break(x, dates)
        crs = _crossing_date(x, dates)
        tsegs[cname] = tseg
        rows.append({
            "coordinate": cname,
            "two_seg_break_date": tseg["date"] if tseg else None,
            "two_seg_t": tseg["t"] if tseg else np.nan,
            "two_seg_p": tseg["p"] if tseg else np.nan,
            "two_seg_n_early_pts": tseg["n_early"] if tseg else 0,
            "two_seg_n_late_pts": tseg["n_late"] if tseg else 0,
            "cusum_break_date": cus["date"] if cus else None,
            "cusum_z": cus["z"] if cus else np.nan,
            "cusum_sig": bool(cus["sig"]) if cus else False,
            "crossing_date": crs,
            "candidate": False,
        })
    # candidate: strong two-segment break supported by its own CUSUM/crossing
    # within 120d OR by another coordinate's two-segment break within 120d
    for cname, tseg in tsegs.items():
        if tseg is None or tseg["n_early"] < 8 or tseg["n_late"] < 8 or \
                tseg["p"] >= 0.05:
            continue
        tb = pd.Timestamp(tseg["date"])
        row = next(r for r in rows if r["coordinate"] == cname)
        support = False
        if row["cusum_sig"] and row["cusum_break_date"] is not None and \
                abs((tb - pd.Timestamp(row["cusum_break_date"])).days) <= 120:
            support = True
        if not support and row["crossing_date"] is not None and \
                abs((tb - pd.Timestamp(row["crossing_date"])).days) <= 120:
            support = True
        if not support:
            for other, ot in tsegs.items():
                if other == cname or ot is None:
                    continue
                if abs((tb - pd.Timestamp(ot["date"])).days) <= 120:
                    support = True
                    break
        row["candidate"] = support
    out = pd.DataFrame(rows)
    # alignment: candidates within 120 days of each other
    cands = [(pd.Timestamp(r["two_seg_break_date"]), r["coordinate"])
             for r in rows if r["candidate"]]
    aligned = []
    if len(cands) >= 2:
        cands.sort()
        groups = []
        cur = [cands[0]]
        for c in cands[1:]:
            if (c[0] - cur[-1][0]).days <= 120:
                cur.append(c)
            else:
                groups.append(cur)
                cur = [c]
        groups.append(cur)
        for g in groups:
            if len(g) >= 2:
                aligned.append({
                    "window_start": str(min(c[0] for c in g))[:10],
                    "window_end": str(max(c[0] for c in g))[:10],
                    "n_coordinates": len(g),
                    "coordinates": ";".join(sorted(set(c[1] for c in g))),
                })
    al = pd.DataFrame(aligned) if aligned else pd.DataFrame(
        columns=["window_start", "window_end", "n_coordinates",
                 "coordinates"])
    al["verdict"] = "CHANGEPOINT_SCAN_DONE"
    out["verdict"] = "CHANGEPOINT_SCAN_DONE"
    full = pd.concat([out, al.assign(coordinate="")], ignore_index=True)
    full.to_csv(OUT / "13_CHANGEPOINT_SCAN.csv", index=False)
    return out, al


# =========================================================================
# WS13: LAW REGIME CANDIDATES (14_LAW_REGIME_CANDIDATES.csv)
# =========================================================================
def ws13_law_regime_candidates(transfer, rank_drift, state_age):
    # signature per subperiod
    sig_cols = {
        "forcing_to_propagation": "forcing_to_propagation",
        "age_to_propagation": "age_to_propagation",
        "entropy_to_propagation": "entropy_to_propagation",
        "activation_depth_to_propagation": "activation_depth_to_propagation",
    }
    rows = []
    for sp in SUBPERIODS:
        sig = {}
        for mname in sig_cols:
            grp_rows = transfer[(transfer["mapping"] == mname) &
                                (transfer["group"] != "")]
            v = grp_rows[f"slope_{sp}"].dropna().mean() if len(grp_rows) \
                else np.nan
            sig[mname] = v
        # rank threshold: mean f50 across patches at 50% activation
        rt = rank_drift[(rank_drift["subperiod"] == sp) &
                        (rank_drift["prob"] == 0.50)]
        sig["rank_f50_mean"] = rt["forcing_threshold"].dropna().mean() \
            if len(rt) else np.nan
        # state-age trend
        sa = state_age[(state_age["subperiod"] == sp)]
        sig["age_prop_trend_mean"] = sa["age_prop_trend"].dropna().mean() \
            if len(sa) else np.nan
        rows.append({"subperiod": sp, **sig})
    sigdf = pd.DataFrame(rows).set_index("subperiod")
    X = sigdf.dropna(axis=1)
    if X.shape[1] < 3:
        out = pd.DataFrame({"subperiod": SUBPERIODS,
                            "law_regime": ["n/a"] * len(SUBPERIODS),
                            "verdict": "NO_NAMED_REGIMES"})
        out.to_csv(OUT / "14_LAW_REGIME_CANDIDATES.csv", index=False)
        return out, "NO_NAMED_REGIMES"
    Z = (X - X.mean()) / (X.std() + 1e-12)
    best = None
    for k in [2, 3]:
        if k >= len(Z):
            continue
        cl = AgglomerativeClustering(n_clusters=k, linkage="average").fit(Z)
        labels = cl.labels_
        if len(set(labels)) < 2:
            continue
        sil = silhouette_score(Z, labels)
        if best is None or sil > best[0]:
            best = (sil, k, labels)
    if best is None or best[0] < 0.30:
        out = pd.DataFrame({"subperiod": SUBPERIODS,
                            "law_regime": ["n/a"] * len(SUBPERIODS),
                            "verdict": "NO_NAMED_REGIMES"})
        out.to_csv(OUT / "14_LAW_REGIME_CANDIDATES.csv", index=False)
        return out, "NO_NAMED_REGIMES"
    sil, k, labels = best
    sps = list(X.index)
    # name regimes by position: first-occurring label = A
    lab2name = {}
    for sp, lab in zip(sps, labels):
        if lab not in lab2name:
            lab2name[lab] = f"LAW_REGIME_{chr(65 + len(lab2name))}"
    out = pd.DataFrame({"subperiod": sps,
                        "law_regime": [lab2name[l] for l in labels],
                        "silhouette": sil, "k": k,
                        "verdict": "LAW_REGIMES_NAMED"})
    out.to_csv(OUT / "14_LAW_REGIME_CANDIDATES.csv", index=False)
    return out, "LAW_REGIMES_NAMED"


# =========================================================================
# WS14: INVARIANT NODE AUDIT (15_INVARIANT_NODE_AUDIT.csv)
# =========================================================================
def _ha_la_gap_sign(df):
    """Sign of (mean prop7 HA - mean prop7 LA) per subperiod."""
    out = {}
    for sp in SUBPERIODS:
        s = df[df["subperiod"] == sp]
        if len(s) < 100:
            continue
        ha = s.loc[s["spatial_ax"] == "HA", "prop7"].mean()
        la = s.loc[s["spatial_ax"] == "LA", "prop7"].mean()
        if ha == ha and la == la and abs(ha - la) > 1e-9:
            out[sp] = 1 if ha > la else -1
    return out


def _threshold_order_stability(df, pact):
    """Rank correlation of patch f50 ordering per subperiod vs full sample."""
    dfx = df.copy()
    dfx["d"] = pd.to_datetime(dfx["d"]).dt.normalize()
    fx_all = dfx.set_index("d")["forcing"]
    order_full = []
    for p in DEPTH_ORDER:
        thr, *_ = forcing_threshold_per_patch(pact, fx_all, p, prob=0.5,
                                              min_n=60)
        order_full.append(thr)
    rhos = []
    for sp in SUBPERIODS:
        s = dfx[dfx["subperiod"] == sp]
        if len(s) < 100:
            continue
        ord_sp = []
        for p in DEPTH_ORDER:
            thr, *_ = forcing_threshold_per_patch(pact,
                                                  s.set_index("d")[
                                                      "forcing"], p,
                                                  prob=0.5, min_n=40)
            ord_sp.append(thr)
        m = ~(np.isnan(order_full) | np.isnan(ord_sp))
        if m.sum() >= 5:
            rhos.append(float(spearmanr(np.array(order_full)[m],
                                        np.array(ord_sp)[m])[0]))
    return rhos


def _physical_sigma_separation(ev):
    """Physical (|ret_1d|) vs sigma (sigma_t0): per-subperiod correlation and
    physical-vs-standardized rank divergence."""
    e = ev.copy()
    e["d"] = pd.to_datetime(e["historical_date"]).dt.normalize()
    e["sp"] = np.select(
        [e["d"] < "2022-01-01", e["d"] < "2023-01-01", e["d"] < "2024-01-01",
         e["d"] < "2025-01-01"], SUBPERIODS[:4], SUBPERIODS[4])
    rows = []
    for sp in SUBPERIODS:
        s = e[e["sp"] == sp]
        s = s[["ret_1d", "sigma_t0"]].dropna()
        if len(s) < 500:
            continue
        corr = float(np.corrcoef(np.abs(s["ret_1d"]), s["sigma_t0"])[0, 1])
        std_ret = s["ret_1d"] / (s["sigma_t0"] + 1e-12)
        rho_phys_std = float(spearmanr(s["ret_1d"], std_ret)[0])
        rows.append({"subperiod": sp, "corr_abs_ret_sigma": corr,
                     "rho_phys_vs_std": rho_phys_std, "n": int(len(s))})
    return pd.DataFrame(rows)


def ws14_invariant_audit(df, pact, ev, ws1_res, ws6_verdict, ws8_verdict,
                         ws9_verdict, ws16_verdict, thr_rhos):
    rows = []
    # 1. breadth x dispersion state topology
    sub = ws1_res[ws1_res["surface_label"] == "4_state"]
    rhos = sub["rho"].dropna()
    mean_rho = float(rhos.mean()) if len(rhos) else np.nan
    rows.append({"node": "BREADTH_X_DISPERSION_STATE_TOPOLOGY",
                 "verdict": "INVARIANT" if mean_rho >= 0.7 else
                 "REGIME_MODULATED" if mean_rho >= 0.4 else "LOCAL_ONLY",
                 "evidence": f"4-state ordering mean rho={mean_rho:.3f} "
                             f"({len(rhos)} tests)"})
    # 2. state x age
    v6map = {"INVARIANT_CLOCK": "INVARIANT",
             "STATE_LOCAL_CLOCK": "REGIME_MODULATED",
             "REGIME_MODULATED_CLOCK": "REGIME_MODULATED",
             "UNSTABLE_CLOCK": "DISSOLVE",
             "DATA_LIMITED_CLOCK": "LOCAL_ONLY"}
    rows.append({"node": "STATE_X_AGE_INTERACTION",
                 "verdict": v6map.get(ws6_verdict, "LOCAL_ONLY"),
                 "evidence": f"WS6={ws6_verdict}: no transportable age law "
                             f"across subperiods; interaction remains "
                             f"descriptive, not freezeable as a clock"})
    # 3. spatial activation coordinate
    gaps = _ha_la_gap_sign(df)
    if len(gaps) >= 4 and len(set(gaps.values())) == 1:
        v3 = "INVARIANT"
    elif len(gaps) >= 4:
        v3 = "REGIME_MODULATED"
    else:
        v3 = "LOCAL_ONLY"
    rows.append({"node": "SPATIAL_ACTIVATION_COORDINATE", "verdict": v3,
                 "evidence": f"HA-vs-LA prop7 gap sign per subperiod: "
                             f"{dict(gaps)}"})
    # 4. age-residualized entropy
    v8map = {"ENTROPY_TOPOLOGY_INVARIANT": "INVARIANT",
             "ENTROPY_RESPONSE_DRIFT": "REGIME_MODULATED",
             "ENTROPY_FULL_DRIFT": "DISSOLVE"}
    rows.append({"node": "AGE_RESIDUALIZED_ENTROPY",
                 "verdict": v8map.get(ws8_verdict, "LOCAL_ONLY"),
                 "evidence": f"WS8={ws8_verdict}"})
    # 5. common forcing coordinate
    v9map = {"COMMON_FORCING_INVARIANT": "INVARIANT",
             "THRESHOLD_DRIFT": "REGIME_MODULATED",
             "GAIN_DRIFT": "REGIME_MODULATED",
             "FULL_FORCING_DRIFT": "REGIME_MODULATED"}
    rows.append({"node": "COMMON_FORCING_COORDINATE",
                 "verdict": v9map.get(ws9_verdict, "LOCAL_ONLY"),
                 "evidence": f"WS9={ws9_verdict}"})
    # 6. threshold hierarchy
    if len(thr_rhos) >= 4 and np.mean(thr_rhos) >= 0.8:
        v6 = "INVARIANT"
    elif len(thr_rhos) >= 4:
        v6 = "REGIME_MODULATED"
    else:
        v6 = "LOCAL_ONLY"
    rows.append({"node": "THRESHOLD_HIERARCHY", "verdict": v6,
                 "evidence": f"patch f50-order rho vs full: "
                             f"mean={np.mean(thr_rhos):.3f} n={len(thr_rhos)}"
                             if thr_rhos else "only deep patches have "
                             "estimable thresholds (shallow always-on); "
                             "hierarchy not fully testable"})
    # 7. physical-vs-sigma separation
    ps = _physical_sigma_separation(ev)
    if len(ps) >= 4:
        corrs = ps["corr_abs_ret_sigma"].dropna()
        rhos2 = ps["rho_phys_vs_std"].dropna()
        corr_stable = bool(corrs.std() < 0.15) if len(corrs) else False
        axes_distinct = bool(rhos2.max() < 0.999) if len(rhos2) else False
        v7 = "INVARIANT" if corr_stable and axes_distinct else \
            "REGIME_MODULATED"
        evid = (f"corr(|ret|,sigma) mean={corrs.mean():.2f} sd="
                f"{corrs.std():.2f}; rho(phys,std) max={rhos2.max():.2f}")
    else:
        v7, evid = "LOCAL_ONLY", "insufficient ev coverage"
    rows.append({"node": "PHYSICAL_VS_SIGMA_SEPARATION", "verdict": v7,
                 "evidence": evid})
    # 8. local highways / exits
    v16map = {"TOPOLOGY_STABLE_RATES_DRIFT": "INVARIANT",
              "FULL_STABILITY": "INVARIANT",
              "TOPOLOGY_DRIFT": "REGIME_MODULATED",
              "NO_STABLE_STRUCTURE": "DISSOLVE"}
    rows.append({"node": "LOCAL_HIGHWAYS_EXITS",
                 "verdict": v16map.get(ws16_verdict, "LOCAL_ONLY"),
                 "evidence": f"WS16={ws16_verdict}"})
    out = pd.DataFrame(rows)
    out["audit_status"] = "INVARIANT_AUDIT_DONE"
    out.to_csv(OUT / "15_INVARIANT_NODE_AUDIT.csv", index=False)
    return out
