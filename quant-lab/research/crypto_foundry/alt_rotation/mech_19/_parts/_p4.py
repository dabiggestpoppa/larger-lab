# ================================================================ 17 threshold inversion anatomy
def _rolling_thr50(win=180, step=30):
    """Rolling half-saturation threshold (x0) per patch, asof-filled daily."""
    dts = dates
    dmin, dmax = dts.min(), dts.max()
    starts = pd.date_range(dmin, dmax - pd.Timedelta(days=win), freq=f"{step}D")
    rows = []
    for t0 in starts:
        mw = (dts >= t0) & (dts < t0 + pd.Timedelta(days=win))
        rec = {"date": t0}
        for p in DEPTH_ORDER:
            x = fc_arr[mw]
            yb = (act[p].to_numpy()[mw] >= 0.55).astype(float)
            m2 = ~(np.isnan(x) | np.isnan(yb)) & np.isfinite(x)
            if m2.sum() < 60:
                rec[p] = np.nan; continue
            par = logit_fit(x[m2], yb[m2])
            rec[p] = thr_at(par, 0.5) if par else np.nan
        rows.append(rec)
    dfw = pd.DataFrame(rows).sort_values("date")
    dfd = pd.DataFrame({"date": pd.DatetimeIndex(dts)})
    merged = pd.merge_asof(dfd, dfw, on="date", direction="backward")
    return merged.drop(columns=["date"])

THR50_ROLL = _rolling_thr50()

def threshold_inversion_anatomy():
    # inversion: shallow patch has HIGHER thr50 than a deeper patch (deeper activates earlier)
    thr = {p: THR50_ROLL[p].to_numpy() for p in DEPTH_ORDER}
    invs = np.zeros(ns, dtype=bool)
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (thr[a] - thr[b]) > 0.15      # deep earlier by a margin
            invs = invs | np.where(np.isnan(thr[a]) | np.isnan(thr[b]), False, g)
    rows = []
    for (aa, bb) in run_episodes(invs):
        dur = bb - aa + 1
        if dur < 3:
            continue
        # which band pairs inverted
        pair = []
        for i, a in enumerate(DEPTH_ORDER):
            for b in DEPTH_ORDER[i + 1:]:
                seg = (thr[a][aa:bb + 1] - thr[b][aa:bb + 1]) > 0.15
                if seg.mean() > 0.5:
                    pair.append(f"{a}<{b}")
        rows.append(dict(start=str(dates[aa].date()), end=str(dates[bb].date()),
                         dur=dur, pairs="|".join(pair),
                         state=str(g6[aa]),
                         forcing=round(float(np.nanmean(fc_arr[aa:bb + 1])), 3),
                         exit_pressure=round(float(np.nanmean(p16[aa:bb + 1])), 3),
                         exit_entropy=round(float(np.nanmean(ent6[aa:bb + 1])), 3),
                         route_deform=round(float(np.nanmean(js_hist[aa:bb + 1])), 3),
                         saturation=round(float(np.nanmean(field_act[aa:bb + 1])), 3),
                         subperiod=str(subp_arr[aa]) if np.ndim(subp_arr) else ""))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("17_THRESHOLD_INVERSION_ANATOMY.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    return out

W17 = W("17_THRESHOLD_INVERSION_ANATOMY.csv", index=False)
W17(threshold_inversion_anatomy().round(3))

# ================================================================ 18 threshold inversion species
def threshold_inversion_species():
    inv = pd.read_csv(OUT / "17_THRESHOLD_INVERSION_ANATOMY.csv")
    if len(inv) < 12 or "forcing" not in inv.columns:
        W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    f_ = inv[["forcing", "exit_pressure", "exit_entropy", "route_deform", "saturation"]].apply(pd.to_numeric, errors="coerce")
    mm = f_.notna().all(1)
    if mm.sum() < 12:
        W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    X = f_[mm].to_numpy()
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
    from sklearn.cluster import KMeans
    k = min(4, mm.sum() // 4)
    if k < 2:
        W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Xs)
    inv["cluster"] = np.nan
    inv.loc[mm, "cluster"] = km.labels_
    cols = ["forcing", "exit_pressure", "exit_entropy", "route_deform", "saturation"]
    rows = []
    for cl in range(k):
        g = inv[inv["cluster"] == cl]
        if len(g) == 0:
            continue
        d = {c: round(float(np.nanmean(g[c])), 3) for c in cols}
        d.update(cluster=int(cl), n=len(g),
                 label=f"INVERSION_SPECIES_{int(cl)}")
        rows.append(d)
    W("18_THRESHOLD_INVERSION_SPECIES.csv")(pd.DataFrame(rows).round(3))

# ================================================================ hysteresis helpers
def _hys_gap(y, fc, gm):
    """Controlled-ratio hysteresis gap for activation y over forcing levels,
    slicing on controls mask array gm (factor). Returns (gap, gap_ctl)."""
    d3 = np.full(len(fc), np.nan); d3[3:] = fc[3:] - fc[:-3]
    thr = np.nanstd(d3) * 0.25
    direc = np.where(d3 > thr, "rising", np.where(d3 < -thr, "falling", "flat"))
    qs = np.nanquantile(fc, np.linspace(0, 1, 11))
    gaps = []
    for i in range(10):
        mb = (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
        mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
        if mr.sum() >= 10 and mf.sum() >= 10:
            gaps.append(float(np.mean(y[mr]) - np.mean(y[mf])))
    gap = float(np.nanmean(gaps)) if gaps else np.nan
    # controlled within each level of gm
    gg = np.asarray(gm)
    gc = []
    for lv in np.unique(gg):
        ms = gg == lv
        for i in range(10):
            mb = ms & (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
            mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
            if mr.sum() >= 6 and mf.sum() >= 6:
                gc.append(float(np.mean(y[mr]) - np.mean(y[mf])))
    gc_g = float(np.nanmean(gc)) if gc else np.nan
    return gap, gc_g

# ================================================================ 19 deep hysteresis map
def deep_hysteresis_map():
    rows = []
    for idx, patch in enumerate(DEPTH_ORDER):
        y = act[patch].to_numpy()
        fc = fc_arr
        # state-sliced
        for s in np.unique(g6):
            gm = np.where(g6 == s, "A", "B")
            m = g6 == s
            if m.sum() < 60:
                continue
            gap, gc = _hys_gap(y[m], fc[m], gm[m.astype(float) if m.dtype.kind in "fi" else m])
            rows.append(dict(patch=patch, layer="state", label=str(s), n=int(m.sum()),
                             gap_raw=round(gap, 3) if gap == gap else np.nan,
                             gap_controlled=round(gc, 3) if gc == gc else np.nan))
    W("19_DEEP_HYSTERESIS_MAP.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 20 hysteresis boundaries
def hysteresis_boundaries():
    rows = []
    for idx, patch in enumerate(DEPTH_ORDER):
        y = act[patch].to_numpy(); fc = fc_arr
        gap, gc = _hys_gap(y, fc, np.zeros(len(fc)))
        rows.append(dict(rank_band=patch, index=idx,
                         gap_raw=round(gap, 3) if gap == gap else np.nan,
                         gap_controlled_gvarsingleton=round(gc, 3) if gc == gc else np.nan))
    dfb = pd.DataFrame(rows)
    gs = pd.to_numeric(dfb["gap_controlled_gvarsingleton"], errors="coerce")
    dfb["strength_band"] = pd.cut(gs, bins=[-np.inf, 0.02, 0.06, 0.12, np.inf],
                                  labels=["ABSENT", "WEAK", "MODERATE", "STRONG"])
    dfb["verdict"] = "RANK_LOCAL_HYSTERESIS" if (abs(gs) >= 0.03).any() else "LEVEL_SUFFICIENT"
    W("20_HYSTERESIS_BOUNDARIES.csv")(dfb.round(3))