# ================================================================ 28 2022 unclamped repair
def _rolling_node_series2(fit=logistic_params_unc, win=180, step=30):
    """Rolling logistic response nodes using an arbitrary fit function."""
    dmin, dmax = dates.min(), dates.max()
    starts = pd.date_range(dmin, dmax - pd.Timedelta(days=win), freq=f"{step}D")
    rows = []
    for t0 in starts:
        mw = (dates >= t0) & (dates < t0 + pd.Timedelta(days=win))
        xw = fc_arr[mw]
        rec = {"date": t0}
        for p in RESP_NAMES:
            yw = act[p].to_numpy()[mw]
            m2 = ~(np.isnan(xw) | np.isnan(yw))
            if int(m2.sum()) < 60:
                rec[f"{p}_k"], rec[f"{p}_ceiling"], rec[f"{p}_x0"] = np.nan, np.nan, np.nan
                continue
            ceil, x0, k, _, _ = fit(xw[m2], yw[m2])
            rec[f"{p}_k"], rec[f"{p}_ceiling"], rec[f"{p}_x0"] = k, ceil, x0
        rows.append(rec)
    dfw = pd.DataFrame(rows).sort_values("date")
    dfd = pd.DataFrame({"date": pd.DatetimeIndex(dates)})
    merged = pd.merge_asof(dfd, dfw, on="date", direction="backward")
    return merged.drop(columns=["date"])

WIND22_PRE = (dates < pd.Timestamp("2021-10-01"))
WIND22_IN = (dates >= pd.Timestamp("2021-10-01")) & (dates < pd.Timestamp("2022-07-01"))
WIND22_POST = (dates >= pd.Timestamp("2022-07-01"))

def _fit_round(win_mask, p, fit):
    x = fc_arr[win_mask]; y = act[p].to_numpy()[win_mask]
    m2 = ~(np.isnan(x) | np.isnan(y))
    if m2.sum() < 60:
        return np.nan, np.nan, np.nan, np.nan
    ceil, x0, k, rmse, _ = fit(x[m2], y[m2])
    return k, ceil, x0, rmse

def unclamped_repair():
    fits = {"CLAMPED": M88.logistic_params, "UNCLAMPED": logistic_params_unc,
            "ROBUST_BOUNDED": lambda x, y: logistic_params_unc(x, y, ceil_hi=2.0)}
    winz = {"PRE2021": WIND22_PRE, "DURING_2022": WIND22_IN, "POST2022": WIND22_POST}
    rows = []
    for win_name, mask in winz.items():
        for p in RESP_NAMES:
            for fname, fit in fits.items():
                k, c, x0, rmse = _fit_round(mask, p, fit)
                rows.append(dict(window=win_name, response=p, fit=fname,
                                 slope=round(float(k), 4) if k == k else np.nan,
                                 ceiling=round(float(c), 4) if c == c else np.nan,
                                 half_sat=round(float(x0), 4) if x0 == x0 else np.nan,
                                 rmse=round(float(rmse), 4) if rmse == rmse else np.nan))
    W("28_2022_UNCLAMPED_REPAIR.csv")(pd.DataFrame(rows).round(4))

# ================================================================ event machinery (unclamped)
def _event_machinery2(fit=logistic_params_unc):
    nodes = _rolling_node_series2(fit)
    cols = {}
    for p in RESP_NAMES:
        cols[f"slope_{p}"] = nodes[f"{p}_k"].to_numpy()
        cols[f"ceiling_{p}"] = nodes[f"{p}_ceiling"].to_numpy()
        cols[f"onset_{p}"] = nodes[f"{p}_x0"].to_numpy()
    vdict = {"slope_FIELD": cols["slope_FIELD"], "ceiling_FIELD": cols["ceiling_FIELD"],
             "onset_FIELD": cols["onset_FIELD"],
             "slope_patch_mean": np.nanmean([cols[f"slope_{p}"] for p in DEPTH_ORDER], axis=0),
             "ceiling_patch_mean": np.nanmean([cols[f"ceiling_{p}"] for p in DEPTH_ORDER], axis=0),
             "onset_patch_mean": np.nanmean([cols[f"onset_{p}"] for p in DEPTH_ORDER], axis=0),
             "exit_entropy": ent6, "exit_p1": p16, "recruitment": rank7,
             "demand": demand_arr, "propagation": prop7, "reentry": ren7,
             "volatility": vol_med, "breadth": possh}
    Z = {}
    for name, v in vdict.items():
        v = np.asarray(v, dtype=float)
        m = pd.Series(v).rolling(30, min_periods=15).mean().to_numpy()
        med = np.nanmedian(m); mad = np.nanmedian(np.abs(m - med)) * 1.4826
        Z[name] = (m - med) / max(mad, 1e-9)
    Zdf = pd.DataFrame(Z)
    S = np.sqrt((Zdf ** 2).mean(axis=1)).to_numpy()
    n_dev = (np.abs(Zdf.to_numpy()) > 3).sum(axis=1)
    win_lo = np.datetime64("2021-11-01"); win_hi = np.datetime64("2023-06-30")
    in_block = (n_dev >= 4) & (dates >= win_lo) & (dates <= win_hi)
    blocks = []; i = 0
    while i < ns:
        if in_block[i]:
            j = i
            while j < ns and in_block[j]:
                j += 1
            if (j - i) >= 10:
                blocks.append((i, j - 1))
            i = j
        else:
            i += 1
    if not blocks:
        return dict(verdict="NO_EVENT_BLOCK_FOUND", Zdf=Zdf, S=S, n_dev=n_dev, dates=dates)
    best = max(blocks, key=lambda ab: float(np.nanmean(S[ab[0]:ab[1] + 1])))
    a, b = best
    t0 = a
    while t0 > 0 and n_dev[t0 - 1] >= 3 and dates[t0 - 1] >= win_lo:
        t0 -= 1
    peak = int(np.nanargmax(S[a:b + 1])) + a
    ev_mask = np.ones(ns, dtype=bool); ev_mask[a:b + 1] = False
    S_base = np.nanmedian(S[ev_mask]); S_mad = np.nanmedian(np.abs(S[ev_mask] - S_base)) * 1.4826
    def first_sustained(cond, dur, start):
        for t in range(start, ns - dur):
            if np.all(cond(t, dur)):
                return t
        return None
    snap = {}
    for dur in (14, 30, 60):
        snap[dur] = first_sustained(lambda tt, d=dur: (n_dev[tt:tt + d] <= 1) & (S[tt:tt + d] <= S_base + 3 * S_mad), dur, peak + 1)
    snap_base = snap[14]
    norm = first_sustained(lambda tt, _d: n_dev[tt:tt + 14] <= 2, 14, peak + 1)
    early = int(np.where(S[peak:] < 0.5 * S[peak])[0][0]) + peak if np.any(S[peak:] < 0.5 * S[peak]) else None
    return dict(verdict="EVENT_DETECTED", Zdf=Zdf, S=S, n_dev=n_dev, dates=dates,
                t0=t0, a=a, b=b, peak=peak, S_base=S_base, S_mad=S_mad,
                snap=snap, snap_base=snap_base, norm=norm, early=early,
                onset_date=str(dates[t0].date()), peak_date=str(dates[peak].date()),
                break_date=str(dates[a].date()),
                snap14_date=str(dates[snap[14]].date()) if snap[14] else None,
                snap30_date=str(dates[snap[30]].date()) if snap[30] else None,
                snap60_date=str(dates[snap[60]].date()) if snap[60] else None)

EV_UNC = _event_machinery2(logistic_params_unc)

def event_reestimate():
    d = EV_UNC["dates"]
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("29_2022_EVENT_REESTIMATE.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    rows = []
    for stage, idx in [("DEVIATION_ONSET", EV_UNC["t0"]), ("BREAK_CONFIRMATION", EV_UNC["a"]),
                       ("PEAK_DISTORTION", EV_UNC["peak"]), ("EARLY_RECOVERY", EV_UNC["early"]),
                       ("SHAPE_NORMALIZATION", EV_UNC["norm"])]:
        if idx is None:
            rows.append(dict(stage=stage, date=None)); continue
        rows.append(dict(stage=stage, date=str(d[idx].date()),
                         deviation_index=round(float(EV_UNC["S"][idx]), 3)))
    for dur in (14, 30, 60):
        t = EV_UNC["snap"][dur]
        rows.append(dict(stage=f"FULL_SNAPBACK_{dur}D", date=str(d[t].date()) if t is not None else None))
    W("29_2022_EVENT_REESTIMATE.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 29 -> shared Z (also write 30..34)
Zdf = EV_UNC["Zdf"] if EV_UNC["verdict"] != "NO_EVENT_BLOCK_FOUND" else pd.DataFrame()

def _norm_date(zvec, peak, sus_dur=14):
    n = len(zvec); absz = np.abs(zvec)
    for t in range(peak + 1, n - sus_dur):
        if np.all(absz[t:t + sus_dur] <= 3):
            return t
    return None

SURFACE_VARS = ["propagation", "reentry", "volatility", "breadth", "demand"]
LAW_VARS = ["slope_FIELD", "ceiling_FIELD", "onset_FIELD", "slope_patch_mean",
            "ceiling_patch_mean", "onset_patch_mean", "exit_entropy", "exit_p1", "recruitment"]

def surface_vs_law_recovery():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("30_SURFACE_VS_LAW_RECOVERY.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; peak = EV_UNC["peak"]
    rows = []
    for grp, names in (("SURFACE", SURFACE_VARS), ("LAW", LAW_VARS)):
        for name in names:
            if name not in Zdf.columns:
                continue
            z = Zdf[name].to_numpy()
            fn = _norm_date(z, peak)
            rows.append(dict(layer=grp, variable=name,
                             sustained_normalization=str(d[fn].date()) if fn is not None else None,
                             days_after_peak=(fn - peak) if fn is not None else np.nan))
    out = pd.DataFrame(rows)
    surf = out[out["layer"] == "SURFACE"]["days_after_peak"]
    law = out[out["layer"] == "LAW"]["days_after_peak"]
    if surf.notna().any() and law.notna().any():
        out["verdict"] = "SURFACE_PRECEDED_LAW" if surf.median() < law.median() else "COEVAL_OR_LAW_FIRST"
    W("30_SURFACE_VS_LAW_RECOVERY.csv")(out.round(2))

def structural_scar():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("31_STRUCTURAL_SCAR.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; sb = EV_UNC.get("snap_base") or EV_UNC["peak"]; peak = EV_UNC["peak"]
    rows = []
    post = (d > d[sb]) & (d <= d[sb] + pd.Timedelta(days=180))
    for name in LAW_VARS:
        if name not in Zdf.columns:
            continue
        z = Zdf[name].to_numpy(); absz = np.abs(z)
        if np.isfinite(absz).sum() < 60:
            continue
        pre = d < d[peak - 250] if peak - 250 > 0 else np.ones(len(d), bool)
        mp = absz[post & np.isfinite(absz)]; mpr = absz[pre & np.isfinite(absz)]
        if len(mp) == 0 or len(mpr) == 0:
            continue
        disp = float(np.nanmean(mp) - np.nanmean(mpr))
        breaches = float((mp > 3).sum())
        rows.append(dict(variable=name, n_post=int(len(mp)),
                         post_mean_absz=round(float(np.nanmean(mp)), 3),
                         pre_mean_absz=round(float(np.nanmean(mpr)), 3),
                         displacement=round(disp, 3),
                         post_breaches=breaches,
                         verbose_scar=bool(disp > 0.5 or breaches > 0)))
    out = pd.DataFrame(rows)
    if len(out) and (out["displacement"] > 0.5).any():
        out["verdict"] = "STRUCTURAL_SCAR"
    elif len(out) and (out["displacement"] > 0.25).any():
        out["verdict"] = "LONG_RELAXATION"
    elif len(out):
        out["verdict"] = "ARTIFACT"
    else:
        out["verdict"] = "DATA_LIMITED"
    W("31_STRUCTURAL_SCAR.csv")(out.round(3))

def reexcursions():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("32_2022_REEXCURSIONS.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; n_dev = EV_UNC["n_dev"]; sb = EV_UNC.get("snap_base") or EV_UNC["peak"]
    mask = np.zeros(ns, dtype=bool); mask[:sb + 1] = False; mask[sb + 1:] = True
    law_cols = [c for c in LAW_VARS if c in Zdf.columns]
    law_z = np.abs(Zdf[law_cols].to_numpy()) if law_cols else np.zeros((ns, 1)) * np.nan
    post_dev = (n_dev >= 2) & mask
    rows = []
    for (a, b) in run_episodes(post_dev):
        if (b - a + 1) < 5:
            continue
        rows.append(dict(start=str(d[a].date()), end=str(d[b].date()),
                         dur=int(b - a + 1),
                         peak_law_absz=round(float(np.nanmax(law_z[a:b + 1])), 3) if len(law_z) else np.nan,
                         forcing=round(float(np.nanmean(fc_arr[a:b + 1])), 3),
                         threshold_inversion=bool(False)))
    W("32_2022_REEXCURSIONS.csv")(pd.DataFrame(rows).round(3))

def event_end():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("33_2022_EVENT_END.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; peak = EV_UNC["peak"]; Z = Zdf
    sb = EV_UNC.get("snap_base") or peak
    def group_end(names, sus):
        z = np.abs(Z[[c for c in names if c in Z.columns]].to_numpy())
        for t in range(peak + 1, ns - sus):
            if np.all(z[t:t + sus].max(axis=1) <= 3, axis=None):
                return t
        return None
    rows = []
    for sus in (14, 30, 60):
        s_end = group_end(SURFACE_VARS, sus)
        l_end = group_end(LAW_VARS, sus)
        full = group_end(SURFACE_VARS + LAW_VARS, sus)
        rows.append(dict(persistence_days=sus,
                         surface_end=str(d[s_end].date()) if s_end is not None else None,
                         law_end=str(d[l_end].date()) if l_end is not None else None,
                         full_stability_end=str(d[full].date()) if full is not None else None))
    W("33_2022_EVENT_END.csv")(pd.DataFrame(rows))

def precedence_map():
    if EV_UNC["verdict"] == "NO_EVENT_BLOCK_FOUND":
        W("34_2022_PRECEDENCE_MAP.csv")(pd.DataFrame([dict(verdict="NO_EVENT_BLOCK_FOUND")]))
        return
    d = EV_UNC["dates"]; peak = EV_UNC["peak"]; sb = EV_UNC.get("snap_base") or peak
    rows = []
    for name in SURFACE_VARS + LAW_VARS:
        if name not in Zdf.columns:
            continue
        z = Zdf[name].to_numpy(); absz = np.abs(z)
        onset = np.nan
        for t in range(max(0, peak - 400), peak + 1):
            if absz[t] > 3:
                onset = t; break
        pk = int(np.nanargmax(absz[max(0, peak - 400):peak + 1])) + max(0, peak - 400)
        fn = _norm_date(z, peak)
        rel = "PRECEDED" if (fn is not None and (sb - fn) > 30) else ("COINCIDED" if (fn is not None and (sb - fn) >= 0) else "LAGGED_OR_NEVER")
        rows.append(dict(variable=name, layer="LAW" if name in LAW_VARS else "SURFACE",
                         onset_date=str(d[int(onset)].date()) if np.isfinite(onset) else None,
                         peak_date=str(d[pk].date()),
                         normalized_date=str(d[fn].date()) if fn is not None else None,
                         relation_to_snapback=rel))
    out = pd.DataFrame(rows)
    W("34_2022_PRECEDENCE_MAP.csv")(out.round(2))