# ================================================================ hysteresis helpers
def _hys_gap2(y, fc, gm=None):
    """Controlled hysteresis gap: mean(y|rising) - mean(y|falling) at matched
    forcing levels, optionally within each level of control array gm."""
    y = np.asarray(y, dtype=float); fc = np.asarray(fc, dtype=float)
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
    if gm is None:
        return gap, gap
    gc = []
    for lv in np.unique(gm):
        ms = gm == lv
        for i in range(10):
            mb = ms & (fc >= qs[i]) & (fc < qs[i + 1]) & np.isfinite(y)
            mr = mb & (direc == "rising"); mf = mb & (direc == "falling")
            if mr.sum() >= 6 and mf.sum() >= 6:
                gc.append(float(np.mean(y[mr]) - np.mean(y[mf])))
    return gap, float(np.nanmean(gc)) if gc else np.nan


# ================================================================ 28 hysteresis reconciliation
def hysteresis_reconciliation():
    rows = []
    fams_sel = ["PARTICIPATION_FORCING", "VOLATILITY_FORCING", "BTC_ANCHOR_FORCING",
                "DISPERSION_FORCING", "STABLECOIN_CAPITAL_FORCING"]
    for idx, patch in enumerate(DEPTH_ORDER):
        y = act[patch].to_numpy()
        for st in np.unique(g6):
            m = g6 == st
            if m.sum() < 90:
                continue
            gap, gap_c = _hys_gap2(y[m], fc_arr[m])
            for fam in fams_sel:
                f = np.asarray(fams[fam], dtype=float)
                gf = np.full(ns, np.nan)
                gf[1:] = f[1:] - f[:-1]
                tier = np.where(gf[m] > 0, "up", np.where(gf[m] < 0, "dn", "flat"))
                gap_f, gap_fc = _hys_gap2(y[m], fc_arr[m], gm=tier)
                rows.append(dict(patch=patch, state=str(st), n=int(m.sum()),
                                 gap_raw=round(gap, 3) if gap == gap else np.nan,
                                 gap_ctl_state=round(gap_c, 3) if gap_c == gap_c else np.nan,
                                 forcing_family=fam,
                                 gap_ctl_family=round(gap_fc, 3) if gap_fc == gap_fc else np.nan))
    out = pd.DataFrame(rows)
    W("28_HYSTERESIS_RECONCILIATION.csv")(out.round(3))


# ================================================================ 29 hysteresis survival map
def hysteresis_survival_map():
    rec = pd.read_csv(OUT / "28_HYSTERESIS_RECONCILIATION.csv")
    if len(rec) == 0:
        W("29_HYSTERESIS_SURVIVAL_MAP.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    rows = []
    from scipy.stats import ranksums
    for patch in DEPTH_ORDER:
        for st in np.unique(g6):
            sub = rec[(rec["patch"] == patch) & (rec["state"] == st)]
            if len(sub) == 0:
                continue
            g = sub["gap_ctl_state"].to_numpy()
            g = g[~np.isnan(g)]
            if len(g) == 0:
                continue
            # subperiod stability of the state-level gap
            sp_vals = []
            y = act[patch].to_numpy(); m = g6 == st
            for sp in SUBPERIODS:
                msp = m & (subp_arr == sp)
                if msp.sum() < 60:
                    continue
                gap, _ = _hys_gap2(y[msp], fc_arr[msp])
                if gap == gap:
                    sp_vals.append(gap)
            fam_sens = float(np.nanstd(rec[(rec["patch"] == patch) & (rec["state"] == st)]["gap_ctl_family"].dropna())) if rec[(rec["patch"] == patch) & (rec["state"] == st)]["gap_ctl_family"].notna().any() else np.nan
            rows.append(dict(patch=patch, state=str(st),
                             gap_ctl_mean=round(float(np.nanmean(g)), 3),
                             gap_ctl_max=round(float(np.nanmax(g)), 3),
                             n_cells=len(g),
                             subperiod_std=round(float(np.nanstd(sp_vals)), 3) if len(sp_vals) >= 3 else np.nan,
                             forcing_family_sensitivity=round(fam_sens, 3) if fam_sens == fam_sens else np.nan))
    out = pd.DataFrame(rows)
    strong = out[out["gap_ctl_max"] >= 0.05]
    if len(strong) == 0:
        out["verdict"] = "WEAK_LOCAL_HYSTERESIS"
    elif strong["subperiod_std"].notna().any() and strong["subperiod_std"].max() > 0.03:
        out["verdict"] = "INTERACTION_HYSTERESIS(state_x_depth_x_regime)"
    else:
        # which dominates: state spread vs depth spread
        depth_spread = out.groupby("patch")["gap_ctl_mean"].mean().std()
        state_spread = out.groupby("state")["gap_ctl_mean"].mean().std()
        out["verdict"] = ("STATE_DOMINANT_HYSTERESIS" if state_spread > depth_spread else "DEPTH_DOMINANT_HYSTERESIS")
    W("29_HYSTERESIS_SURVIVAL_MAP.csv")(out.round(3))


# ================================================================ 30 forcing functional dimensions
def forcing_functional_dimensions():
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        fv = f[~np.isnan(f)]
        ac1 = float(np.corrcoef(fv[:-1], fv[1:])[0, 1]) if len(fv) > 30 else np.nan
        burst = float(np.nanquantile(f, 0.9) / max(abs(np.nanquantile(f, 0.5)), 1e-9)) if np.isfinite(np.nanquantile(f, 0.5)) else np.nan
        temporal = "PERSISTENT" if (ac1 == ac1 and ac1 > 0.6) else ("BURSTY" if (burst == burst and burst > 2.0) else "MIXED")
        # spatial: broad vs rank-local = std of |corr with each patch|
        patch_c = [abs(_rhoXY(f, act[p].to_numpy())) for p in DEPTH_ORDER]
        spatial = "RANK_LOCAL" if (len(patch_c) and float(np.std(patch_c)) > 0.12) else "BROAD"
        # route function: load/suppress from M19 11 map
        rsf = pd.read_csv(RETRO / "10_ROUTE_SPECIFIC_FORCING.csv")
        fsub = rsf[rsf["forcing_family"] == fam].dropna(subset=["rho"])
        loads = int((fsub["rho"] > 0.15).sum()); supps = int((fsub["rho"] < -0.15).sum())
        route_fn = "LOAD_ROUTE" if loads > supps * 2 else ("SUPPRESS_ROUTE" if supps > loads * 2 else "MIXED")
        # response function: which node moves most
        node_c = {k: abs(_rhoXY(f, PATCHM[f"{k}"])) for k in ("slope", "ceiling", "onset")}
        resp_fn = max(node_c, key=node_c.get) if any(v == v for v in node_c.values()) else "none"
        resp_mag = node_c[resp_fn] if resp_fn != "none" else np.nan
        # resolution function: pruning vs concentration (per-state mechanism association)
        dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
        dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
        pr = [np.nanmean(f[g6 == s]) for s, m in dr6.items() if m == "EDGE_PRUNING"]
        co = [np.nanmean(f[g6 == s]) for s, m in dr6.items() if m == "PRESSURE_CONCENTRATION"]
        res_fn = "FAVOR_PRUNING" if (len(pr) and len(co) and np.nanmean(pr) > np.nanmean(co)) else "FAVOR_CONCENTRATION" if (len(pr) and len(co)) else "NEUTRAL"
        rows.append(dict(family=fam,
                         temporal_character=temporal, autocorr1=round(ac1, 3) if ac1 == ac1 else np.nan,
                         burstiness=round(burst, 3) if burst == burst else np.nan,
                         spatial_character=spatial, patch_corr_spread=round(float(np.std(patch_c)), 3),
                         route_function=route_fn, n_routes_loaded=loads, n_routes_suppressed=supps,
                         response_function=f"MOVE_{resp_fn.upper()}", response_mag=round(float(resp_mag), 3) if resp_mag == resp_mag else np.nan,
                         resolution_function=res_fn))
    W("30_FORCING_FUNCTIONAL_DIMENSIONS.csv")(pd.DataFrame(rows).round(3))


# ================================================================ 31 forcing functional map
def forcing_functional_map():
    fd = pd.read_csv(OUT / "30_FORCING_FUNCTIONAL_DIMENSIONS.csv")
    # 2D map: temporal (autocorr) x spatial (patch spread)
    rows = []
    for _, r in fd.iterrows():
        rows.append(dict(family=r["family"],
                         temporal_axis=round(float(r["autocorr1"]), 3) if r["autocorr1"] == r["autocorr1"] else np.nan,
                         spatial_axis=round(float(r["patch_corr_spread"]), 3),
                         route_function=r["route_function"], response_function=r["response_function"],
                         resolution_function=r["resolution_function"],
                         quadrant=("PERSISTENT_BROAD" if (r["autocorr1"] or 0) > 0.5 and r["patch_corr_spread"] <= 0.12 else
                                   "PERSISTENT_RANKLOCAL" if (r["autocorr1"] or 0) > 0.5 else
                                   "IMPULSE_BROAD" if r["patch_corr_spread"] <= 0.12 else "IMPULSE_RANKLOCAL")))
    out = pd.DataFrame(rows)
    W("31_FORCING_FUNCTIONAL_MAP.csv")(out.round(3))


# ================================================================ 32 forcing temporal scales
def forcing_temporal_scales():
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        fv = f[~np.isnan(f)]
        acs = []
        for lag in (1, 3, 5, 10, 20):
            if len(fv) > lag + 10:
                acs.append(float(np.corrcoef(fv[:-lag], fv[lag:])[0, 1]))
            else:
                acs.append(np.nan)
        # half-life: first lag where autocorr < 0.5
        half = next((lag for lag, a in zip((1, 3, 5, 10, 20), acs) if a == a and a < 0.5), None)
        # burst duration: mean length of above-median runs
        med = np.nanmedian(f)
        runs = run_episodes(f >= med)
        burst_len = float(np.mean([b - a + 1 for (a, b) in runs])) if runs else np.nan
        # lead/lag vs route pressure: cross-correlation of family with forward exit pressure
        from scipy.signal import correlate
        ff = np.nan_to_num(f); pp = np.nan_to_num(p16)
        ff = (ff - ff.mean()) / (ff.std() + 1e-9); pp = (pp - pp.mean()) / (pp.std() + 1e-9)
        lags = np.arange(-10, 11)
        xc = [float(np.corrcoef(ff[:len(ff) - abs(l)] if l >= 0 else ff[abs(l):],
                                pp[abs(l):] if l >= 0 else pp[:len(pp) - abs(l)])[0, 1]) if len(ff) > abs(l) + 20 else np.nan for l in lags]
        best_lag = int(lags[int(np.nanargmax(np.abs(xc)))]) if any(x == x for x in xc) else np.nan
        gain_c = _rhoXY(f, GAIN_F)
        rows.append(dict(family=fam,
                         ac_lag1=round(acs[0], 3) if acs[0] == acs[0] else np.nan,
                         ac_lag5=round(acs[2], 3) if acs[2] == acs[2] else np.nan,
                         ac_lag20=round(acs[4], 3) if acs[4] == acs[4] else np.nan,
                         half_life_lag=half,
                         mean_burst_days=round(burst_len, 2) if burst_len == burst_len else np.nan,
                         best_lag_vs_route_pressure=int(best_lag) if best_lag == best_lag else np.nan,
                         rho_with_gain=round(gain_c, 3) if gain_c == gain_c else np.nan,
                         temporal_class=("BACKGROUND_FIELD" if (acs[0] == acs[0] and acs[0] > 0.6 and (half or 99) >= 10)
                                         else "IMPULSE" if (acs[0] == acs[0] and acs[0] < 0.4)
                                         else "MIXED")))
    W("32_FORCING_TEMPORAL_SCALES.csv")(pd.DataFrame(rows).round(3))


# ================================================================ 33 forcing interaction deep
def forcing_interaction_deep():
    it = pd.read_csv(RETRO19 / "10_FORCING_INTERACTIONS.csv")
    sel = it[it["classification"].isin(["SYNERGISTIC_LIKE", "ANTAGONISTIC_LIKE", "ROUTE_SPECIFIC"])]
    outcomes = {"route_pressure": p16, "transfer": te_arr, "threshold": thr_pos,
                "gain": GAIN_F, "ceiling": CEIL_F, "rank_recruitment": rank7}
    rows = []
    for _, r in sel.iterrows():
        a, b = r["family_a"], r["family_b"]
        fa = np.asarray(fams[a], dtype=float); fb = np.asarray(fams[b], dtype=float)
        hi_a = fa >= np.nanquantile(fa, 0.7); hi_b = fb >= np.nanquantile(fb, 0.7)
        for oname, oarr in outcomes.items():
            both = hi_a & hi_b & np.isfinite(oarr)
            only_a = hi_a & (~hi_b) & np.isfinite(oarr)
            only_b = (~hi_a) & hi_b & np.isfinite(oarr)
            neither = (~hi_a) & (~hi_b) & np.isfinite(oarr)
            if min(both.sum(), only_a.sum(), only_b.sum(), neither.sum()) < 30:
                continue
            # interaction effect beyond additivity
            exp_add = float(np.nanmean(oarr[only_a]) + np.nanmean(oarr[only_b]) - np.nanmean(oarr[neither]))
            obs_both = float(np.nanmean(oarr[both]))
            delta = obs_both - exp_add
            rows.append(dict(family_a=a, family_b=b, interaction_type=r["classification"],
                             outcome=oname, n_both=int(both.sum()),
                             observed_both=round(obs_both, 4),
                             additive_expectation=round(exp_add, 4),
                             interaction_delta=round(delta, 4),
                             alters_outcome=bool(abs(delta) > 0.1 * max(abs(obs_both), 1e-6))))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("33_FORCING_INTERACTION_DEEP.csv")(pd.DataFrame([dict(verdict="NO_SUPPORTED_INTERACTIONS")]))
        return
    W("33_FORCING_INTERACTION_DEEP.csv")(out.round(4))
