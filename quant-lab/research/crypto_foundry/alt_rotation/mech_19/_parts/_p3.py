# ================================================================ 12 saturation mechanism
def _node_feat_matrix(resps=None, mean_window=7):
    """Smoothed node-change features: d(slope), d(ceiling), d(onset) per response."""
    resps = resps or RESP_NAMES
    cols, data = [], []
    for p in resps:
        for node, arr in (("slope", f"slope_{p}"), ("ceiling", f"ceiling_{p}"), ("onset", f"onset_{p}")):
            v = np.asarray(NODE_ARR[arr], dtype=float)
            dv = np.diff(v, prepend=np.nan)
            dsm = pd.Series(np.where(dv == dv, dv, np.nan)).rolling(mean_window, min_periods=2).mean().to_numpy()
            cols.append(f"d{node}_{p}"); data.append(dsm)
    return np.column_stack(data), cols

def saturation_mechanism():
    X, cols = _node_feat_matrix(["FIELD"])
    m = np.isfinite(X).all(1)
    if m.sum() < 150:
        W("12_SATURATION_MECHANISM.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    Xc = X[m]; Xc = (Xc - Xc.mean(0)) / (Xc.std(0) + 1e-9)
    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=3).fit(Xc)
        ev = pca.explained_variance_ratio_
    except Exception:
        ev = np.ones(3) * np.nan
    rows = [dict(coordinate="d_slope_FIELD", explain=round(float(ev[0]), 3) if np.isfinite(ev[0]) else np.nan)]
    rows.append(dict(coordinate="d_ceiling_FIELD", explain=round(float(ev[1]), 3) if np.isfinite(ev[1]) else np.nan))
    rows.append(dict(coordinate="d_onset_FIELD", explain=round(float(ev[2]), 3) if np.isfinite(ev[2]) else np.nan))
    rows.append(dict(coordinate="cum2", explain=round(float(np.nansum(ev[:2])), 3)))
    rows.append(dict(coordinate="cum3", explain=round(float(np.nansum(ev)), 3)))
    rows.append(dict(coordinate="one_coordinate_capture", explain=float(ev[0])))
    W("12_SATURATION_MECHANISM.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 13 response node coupling
def response_node_coupling():
    X, cols = _node_feat_matrix(RESP_NAMES)
    m = np.isfinite(X).all(1)
    rows = []
    if m.sum() >= 120:
        Xc = X[m]; Xc = (Xc - Xc.mean(0)) / (Xc.std(0) + 1e-9)
        from sklearn.decomposition import PCA
        C = np.corrcoef(Xc.T)
        # pair avg abs correlations by node-type pair
        node_pairs = [("slope", "ceiling"), ("slope", "onset"), ("ceiling", "onset")]
        names = list(dict.fromkeys([c.split("_", 1)[0] for c in cols]))
        for na, nb in node_pairs:
            ia = [cols.index(f"d{na}_{p}") for p in RESP_NAMES]
            ib = [cols.index(f"d{nb}_{p}") for p in RESP_NAMES]
            vals = [C[i, j] for i in ia for j in ib if i < j or True]
            rows.append(dict(node_a=na, node_b=nb,
                             mean_abs_corr=round(float(np.nanmean(np.abs(vals))), 3),
                             n_pairs=len(vals)))
        pca = PCA(n_components=8).fit(Xc)
        ev = pca.explained_variance_ratio_
        rows.append(dict(node_a="PCA", node_b="all",
                         mean_abs_corr=round(float(ev[0]), 3), n_pairs=len(cols)))
        rows.append(dict(node_a="PCA", node_b="cum3",
                         mean_abs_corr=round(float(np.nansum(ev[:3])), 3), n_pairs=len(cols)))
    else:
        rows = [dict(node_a="FIELD", node_b="?", mean_abs_corr=np.nan, n_pairs=0)]
    W("13_RESPONSE_NODE_COUPLING.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 14 response coordinate pilot
def response_coordinate_pilot():
    # heldout reconstruction of FIELD saturation curve under 1/2/3-node parameterization
    from scipy.optimize import curve_fit
    dates_n = pd.to_datetime(dfc["d"])
    starts = pd.date_range(dates_n.min(), dates_n.max() - pd.Timedelta(days=180), freq="90D")
    fc = fc_arr
    y = field_act
    rows = []
    from _m19base import logistic_params_unc, logistic_params_unc as LPC2
    def sig(X, ceil, x0, k):
        return ceil / (1 + np.exp(-k * (X - x0)))
    meds = {}
    for node in ("x0", "k"):
        v = []
        for p in DEPTH_ORDER:
            x = fc; yy = act[p].to_numpy()
            m2 = ~(np.isnan(x) | np.isnan(yy))
            c2, x02, k2, _, _ = M88.logistic_params(x[m2], yy[m2])
            v.append({"x0": x02, "k": k2}[node])
        meds[node] = float(np.nanmedian(v))
    for i in range(len(starts)):
        t0 = starts[i]; t1 = t0 + pd.Timedelta(days=180)
        mw = (dates_n >= t0) & (dates_n < t1)
        if mw.sum() < 60:
            continue
        x = fc[mw]; yy = y[mw]
        m2 = ~(np.isnan(x) | np.isnan(yy)); x, yy = x[m2], yy[m2]
        if len(x) < 50:
            continue
        c, x0, k, _, _ = logistic_params_unc(x, yy)
        if not np.isfinite(c):
            continue
        pred3 = sig(x, c, x0, k)
        pred2 = sig(x, c, x0, meds["k"])
        s1 = 1 / (1 + np.exp(-meds["k"] * (x - meds["x0"])))
        c1 = np.sum(s1 * yy) / max(np.sum(s1 * s1), 1e-12)
        pred1 = c1 * s1
        rows.append(dict(win_start=str(t0.date()), n=len(x),
                         rmse_1param=rms(yy, pred1), rmse_2param=rms(yy, pred2),
                         rmse_3param=rms(yy, pred3),
                         naming_1=round(float(c1), 3), naming_3=round(float(c), 3)))
    out = pd.DataFrame(rows)
    if len(out):
        out["verdict_1d"] = np.where((out["rmse_1param"] - out["rmse_2param"]).abs().mean() < 0.02,
                                     "ONE_RESPONSE_COORDINATE", "TWO_REQUIRED")
    else:
        out["verdict_1d"] = "DATA_LIMITED"
    W("14_RESPONSE_COORDINATE_PILOT.csv")(out.round(4))

def rms(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return np.nan
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))

# ================================================================ 15 saturation by route
def saturation_by_route():
    rows = []
    sat = field_act
    for st in np.unique(g6):
        mk = g6 == st
        if mk.sum() < 60:
            continue
        sel = np.where(mk)[0]
        cnt = pd.Series(g6n[sel]).value_counts()
        dom = cnt.index[0] if len(cnt) else None
        if dom is None or dom == st:
            continue
        # forward 7d pressure to dominant exit among days in state
        press_all = np.full(ns, np.nan)
        for j in range(ns - 7):
            if g6[j] == st:
                press_all[j] = float((g6[j + 1:j + 8] == dom).mean())
        commit = press_all > 0.5
        pre = mk & (sat <= np.nanquantile(sat[mk], 0.33)) & np.isfinite(sat)
        near = mk & (sat >= np.nanquantile(sat[mk], 0.66)) & np.isfinite(sat)
        rows.append(dict(state=st, dominant=dom, n=int(mk.sum()),
                         commit_frac_pre_sat=round(float((commit & pre).sum() / pre.sum()), 3) if pre.sum() else np.nan,
                         commit_frac_near_ceiling=round(float((commit & near).sum() / near.sum()), 3) if near.sum() else np.nan,
                         median_sat_at_commit=round(float(np.nanmedian(sat[commit])), 3) if (commit == True).any() else np.nan,
                         sat_mean=round(float(np.nanmean(sat[mk])), 3),
                         sat_without_delivery=round(float(((sat[mk] >= np.nanquantile(sat[mk], 0.66)) & (prop7[mk] <= np.nanquantile(prop7, 0.33))).mean()), 3)))
    out = pd.DataFrame(rows)
    out["verdict"] = "MEASURED"
    return out

W15 = W("15_SATURATION_BY_ROUTE.csv", index=False)
W15(saturation_by_route().round(3))

# ================================================================ 16 saturation without delivery
def saturation_without_delivery():
    rows = []
    sat_hi = field_act >= np.nanquantile(field_act, 0.66)
    deliv = prop7 >= 0.5            # realized-propagation flag
    print("[16] sat_hi=%d delivered=%d no-delivery=%d" % (int(sat_hi.sum()), int((sat_hi & deliv).sum()), int((sat_hi & ~deliv).sum())))
    nod = sat_hi & (~deliv)
    d = sat_hi & deliv
    def _cmp(name, arr):
        a = arr[nod]; b = arr[d]
        a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
        if len(a) < 30 or len(b) < 30:
            return
        p = float(ranksums(a, b).pvalue)
        rows.append(dict(variable=name, n_without=int(len(a)), n_with= int(len(b)),
                         mean_without=round(float(np.nanmean(a)), 3),
                         mean_with=round(float(np.nanmean(b)), 3),
                         diff=round(float(np.nanmean(a) - np.nanmean(b)), 3),
                         ranksums_p=round(p, 4)))
    _cmp("exit_pressure_p1", p16)
    _cmp("exit_entropy", ent6)
    _cmp("route_deformation_js", js_hist)
    _cmp("transfer_efficiency", te_arr)
    _cmp("capacity", cap_arr)
    _cmp("threshold_position", thr_pos)
    _cmp("forcing", fc_arr)
    # unmatched baseline to compare broadly
    out = pd.DataFrame(rows)
    if len(out) > 0:
        out["pattern"] = "SATURATION_WITHOUT_DELIVERY_vs_WITH"
    else:
        out = pd.DataFrame([dict(variable="ALL", n_without=0, n_with=0, pattern="DATA_LIMITED")])
    W("16_SATURATION_WITHOUT_DELIVERY.csv")(out.round(3))