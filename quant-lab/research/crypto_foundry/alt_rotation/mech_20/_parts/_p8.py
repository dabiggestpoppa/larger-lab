# ================================================================ shared era windows
EV_UNC = M99.EV_UNC
ZDF = EV_UNC["Zdf"] if isinstance(EV_UNC, dict) and EV_UNC.get("verdict") == "EVENT_DETECTED" else pd.DataFrame()
ONSET_DT = pd.Timestamp("2021-12-16")
SNAPBACK_DT = pd.Timestamp("2022-06-28")
PRE_ERA = dates < pd.Timestamp("2021-10-01")
TRANS_ERA = (dates >= pd.Timestamp("2021-10-01")) & (dates < pd.Timestamp("2022-07-01"))
POST_ERA = dates >= pd.Timestamp("2023-07-01")


# ================================================================ 34 2022 era hypotheses
def _gain_monthly():
    s = pd.Series(GAIN_F, index=dates)
    return s.resample("MS").mean().dropna()


def _regime_of(m, lo=0.35, hi=0.9):
    return np.where(m <= lo, "LOW", np.where(m >= hi, "HIGH", "MID"))


def era_hypotheses():
    rows = []
    g = GAIN_F
    gm = _gain_monthly()
    pre_m_ = gm[gm.index < pd.Timestamp("2021-10-01")]
    post_m_ = gm[gm.index >= pd.Timestamp("2023-07-01")]
    pre_mean = float(pre_m_.mean()); post_mean = float(post_m_.mean())
    pre_sd = float(pre_m_.std())
    # H1: does the LOW-GAIN regime frequency return to pre levels? (bimodal-safe)
    lo_pre = float((_regime_of(pre_m_.to_numpy()) == "LOW").mean())
    lo_post = float((_regime_of(post_m_.to_numpy()) == "LOW").mean())
    rows.append(dict(hypothesis="H1_TEMPORARY_SCAR",
                     pre_gain_mean=round(pre_mean, 4), post_gain_mean=round(post_mean, 4),
                     low_gain_regime_frac_pre=round(lo_pre, 3),
                     low_gain_regime_frac_post=round(lo_post, 3),
                     test="post recovers pre low-regime frequency" if abs(lo_post - lo_pre) < 0.2 else "post low-regime frequency differs"))
    # H2: stability of post-2023 by year (does a single baseline exist?)
    for yr in (2023, 2024, 2025, 2026):
        m = (dates.dt.year == yr) & np.isfinite(g)
        rows.append(dict(hypothesis="H2_ERA_TRANSITION", year=yr,
                         gain_mean=round(float(np.nanmean(g[m])), 4),
                         gain_std=round(float(np.nanstd(g[m])), 4),
                         n_days=int(m.sum())))
    # H3: count regime transitions (LOW<->HIGH excursions) on monthly grid, full panel
    reg = _regime_of(gm.to_numpy())
    trans = int(np.sum(reg[1:] != reg[:-1]))
    n_lo_runs = len(run_episodes(reg == "LOW"))
    n_hi_runs = len(run_episodes(reg == "HIGH"))
    rows.append(dict(hypothesis="H3_MULTIPLE_MODULATIONS",
                     monthly_regime_transitions=int(trans),
                     n_low_gain_runs=int(n_lo_runs), n_high_gain_runs=int(n_hi_runs),
                     post_frac_low_regime=round(lo_post, 3)))
    out = pd.DataFrame(rows)
    # verdict: bimodal structure -> repeated modulations unless post is uniformly low/high
    if n_lo_runs >= 2 and n_hi_runs >= 2:
        out["verdict"] = "H3_MULTIPLE_REGIME_MODULATIONS"
    elif abs(lo_post - lo_pre) < 0.2 and n_lo_runs <= 1:
        out["verdict"] = "H1_TEMPORARY_SCAR"
    else:
        out["verdict"] = "H2_ERA_TRANSITION"
    W("34_2022_ERA_HYPOTHESES.csv")(out.round(4))


# ================================================================ 35 response gain changepoints
def response_gain_changepoints():
    # operate on the MONTHLY gain grid (73 observations) - matches the 30d fit cadence
    gm = _gain_monthly()
    gv = gm.to_numpy()
    n = len(gv)
    min_seg = 6  # months
    # CUSUM on monthly grid
    cb = [k for k in cusum_breaks(gv, min_seg=min_seg) if k < n - 1]
    # segmented regression on monthly grid
    sb = segfit_breaks(gv, cand_step=2, min_seg=min_seg, max_breaks=3)
    # distribution shift on monthly grid
    ds = dist_shift_breaks(gv, base_win=12, ref_win=3)
    rows = []
    for k in cb:
        rows.append(dict(method="CUSUM", break_index=int(k), break_date=str(gm.index[k].date())))
    for k in sb:
        rows.append(dict(method="SEGMENTED_REGRESSION", break_index=int(k), break_date=str(gm.index[k].date())))
    for k in ds:
        rows.append(dict(method="DISTRIBUTION_SHIFT", break_index=int(k), break_date=str(gm.index[k].date())))
    out = pd.DataFrame(rows)
    # agreement within +-2 months across >=2 methods
    all_breaks = sorted(cb + sb + ds)
    agree = []
    for k in all_breaks:
        near = [x for x in all_breaks if abs(x - k) <= 2]
        if len(near) >= 2 and k not in agree:
            agree.append(int(np.mean(near)))
    agree = sorted(set(agree))
    first_break = agree[0] if agree else None
    if first_break is not None:
        pre_level = float(np.nanmean(gv[:first_break]))
        post_level = float(np.nanmean(gv[first_break:]))
    else:
        pre_level = post_level = np.nan
    rows2 = [dict(method="AGREED_BREAK", break_index=k, break_date=str(gm.index[k].date())) for k in agree]
    out = pd.concat([out, pd.DataFrame(rows2)], ignore_index=True)
    out["first_break_date"] = str(gm.index[first_break].date()) if first_break is not None else None
    out["pre_level"] = round(pre_level, 4) if pre_level == pre_level else np.nan
    out["post_level"] = round(post_level, 4) if post_level == post_level else np.nan
    out["verdict"] = "CHANGEPOINTS_AGREED" if len(agree) >= 1 else "NO_AGREED_CHANGEPOINT"
    W("35_RESPONSE_GAIN_CHANGEPOINTS.csv")(out.round(4))


# ================================================================ 36 pre transition post law
def pre_transition_post_law():
    rows = []
    eras = {"PRE2022": PRE_ERA, "TRANSITION": TRANS_ERA, "POST2022": POST_ERA}
    # gain / ceiling / transfer / route deformation
    for e_name, em in eras.items():
        rows.append(dict(era=e_name, variable="gain",
                         mean=round(float(np.nanmean(GAIN_F[em])), 4),
                         q50=round(float(np.nanquantile(GAIN_F[em], 0.5)), 4)))
        rows.append(dict(era=e_name, variable="ceiling",
                         mean=round(float(np.nanmean(CEIL_F[em])), 4)))
        rows.append(dict(era=e_name, variable="transfer",
                         mean=round(float(np.nanmean(te_arr[em])), 4)))
        rows.append(dict(era=e_name, variable="route_deformation",
                         mean=round(float(np.nanmean(js_hist[em])), 4)))
        rows.append(dict(era=e_name, variable="birth_abort_rate",
                         mean=round(float(np.mean([1 if i in ab_ else 0 for i in bp_ if em[i]])), 3)))
        rows.append(dict(era=e_name, variable="realization_rate",
                         mean=round(float(np.nanmean(prop7[em] >= 0.5)), 3)))
    # threshold hierarchy per era: per-patch thr50 mean
    for p in DEPTH_ORDER:
        for e_name, em in eras.items():
            rows.append(dict(era=e_name, variable=f"thr50_{p}",
                             mean=round(float(np.nanmean(THR50[p][em])), 4)))
    # forcing-route relationships per era: corr(forcing, exit pressure) per family
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        for e_name, em in eras.items():
            r = _rhoXY(f[em], p16[em])
            rows.append(dict(era=e_name, variable=f"route_load_{fam}",
                             mean=round(r, 3) if r == r else np.nan))
    # pruning vs concentration mix per era
    dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
    dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
    for e_name, em in eras.items():
        mechs = [dr6.get(s) for s in g6[em]]
        rows.append(dict(era=e_name, variable="prune_frac",
                         mean=round(float(np.mean([m == "EDGE_PRUNING" for m in mechs if m])), 3)))
    W("36_PRE_TRANSITION_POST_LAW.csv")(pd.DataFrame(rows).round(4))


# ================================================================ 37 new baseline vs scar
def new_baseline_vs_scar():
    rows = []
    g = GAIN_F
    gm = _gain_monthly()
    for yr in (2023, 2024, 2025, 2026):
        m = (dates.dt.year == yr) & np.isfinite(g)
        if m.sum() < 60:
            continue
        ym = gm[gm.index.year == yr]
        reg = _regime_of(ym.to_numpy())
        rows.append(dict(year=yr, n_days=int(m.sum()),
                         gain_mean=round(float(np.nanmean(g[m])), 4),
                         gain_std=round(float(np.nanstd(g[m])), 4),
                         low_regime_months=int((reg == "LOW").sum()),
                         high_regime_months=int((reg == "HIGH").sum()),
                         regime_transitions=len(run_episodes(reg[1:] != reg[:-1])) if len(reg) > 1 else 0))
    out = pd.DataFrame(rows)
    if len(out):
        year_means = out["gain_mean"].to_numpy()
        drift = float(np.nanmax(year_means) - np.nanmin(year_means))
        low_months_total = int(out["low_regime_months"].sum())
        hi_months_total = int(out["high_regime_months"].sum())
        if drift < 0.2 and low_months_total <= 2 and hi_months_total <= 2:
            verd = "NEW_BASELINE"
        elif low_months_total >= 3 and hi_months_total >= 3:
            verd = "REPEATED_SCAR(bimodal)"
        elif low_months_total >= 6 or hi_months_total >= 6:
            verd = "LONG_RECOVERY"
        else:
            verd = "MIXED"
    else:
        verd = "DATA_LIMITED"
    out["verdict"] = verd
    W("37_NEW_BASELINE_VS_SCAR.csv")(out.round(4))


# ================================================================ 38 reexcursion anatomy
def reexcursion_anatomy():
    rex = pd.read_csv(RETRO19 / "32_2022_REEXCURSIONS.csv")
    if len(rex) == 0 or "start" not in rex.columns:
        W("38_REEXCURSION_ANATOMY.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    rows = []
    for _, r in rex.iterrows():
        try:
            a = int(np.where(dates == pd.Timestamp(r["start"]))[0][0])
            b = int(np.where(dates == pd.Timestamp(r["end"]))[0][0])
        except Exception:
            continue
        rows.append(dict(start=r["start"], end=r["end"], dur=int(b - a + 1),
                         state=str(g6[a]),
                         gain=round(float(np.nanmean(GAIN_F[a:b + 1])), 3),
                         ceiling=round(float(np.nanmean(CEIL_F[a:b + 1])), 3),
                         transfer=round(float(np.nanmean(te_arr[a:b + 1])), 3),
                         threshold=round(float(np.nanmean(thr_pos[a:b + 1])), 3),
                         surface_propagation=round(float(np.nanmean(prop7[a:b + 1])), 3),
                         surface_volatility=round(float(np.nanmean(vol_med[a:b + 1])), 3),
                         dominant_forcing=max(fam_cols, key=lambda f: abs(_rhoXY(np.asarray(fams[f], dtype=float)[a:b + 1], p16[a:b + 1]))),
                         threshold_inversion=bool(np.any(_inversion_days()[a:b + 1]))))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("38_REEXCURSION_ANATOMY.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    W("38_REEXCURSION_ANATOMY.csv")(out.round(3))


# ================================================================ 39 surface vs law generalization
def surface_vs_law_generalization():
    if len(ZDF) == 0:
        W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(pd.DataFrame([dict(verdict="NO_EVENT_MACHINERY")]))
        return
    SURFACE_VARS = ["propagation", "reentry", "volatility", "breadth", "demand"]
    LAW_VARS = ["slope_FIELD", "ceiling_FIELD", "onset_FIELD", "slope_patch_mean",
                "ceiling_patch_mean", "onset_patch_mean", "exit_entropy", "exit_p1", "recruitment"]
    surf = [c for c in SURFACE_VARS if c in ZDF.columns]
    law = [c for c in LAW_VARS if c in ZDF.columns]
    if not surf or not law:
        W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    rex = pd.read_csv(RETRO19 / "32_2022_REEXCURSIONS.csv")
    rows = []
    for _, r in rex.iterrows():
        try:
            a = int(np.where(dates == pd.Timestamp(r["start"]))[0][0])
        except Exception:
            continue
        b = min(int(np.where(dates == pd.Timestamp(r["end"]))[0][0]) if np.any(dates == pd.Timestamp(r["end"])) else a + 30, ns - 1)
        end_norm = min(b + 60, ns - 1)
        if b - a < 5 or end_norm - b < 14:
            continue
        # peak abs z during episode vs 30d after
        def decay(cols):
            z = np.abs(ZDF[cols].to_numpy())
            pk = float(np.nanmax(z[a:b + 1]))
            post = float(np.nanmean(z[b + 1:end_norm]))
            return pk, post
        spk, spos = decay(surf)
        lpk, lpos = decay(law)
        rows.append(dict(start=r["start"], end=r["end"],
                         surface_peak_absz=round(spk, 2), surface_post_absz=round(spos, 2),
                         law_peak_absz=round(lpk, 2), law_post_absz=round(lpos, 2),
                         surface_decay=round(spk - spos, 2), law_decay=round(lpk - lpos, 2),
                         surface_precedes=bool(lpos > spos)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    n_pre = int(out["surface_precedes"].sum())
    if n_pre >= max(2, 0.6 * len(out)):
        out["verdict"] = "SURFACE_VS_LAW_CLOCKS_GENERALIZE"
    elif n_pre >= 1:
        out["verdict"] = "PARTIAL_GENERALIZATION"
    else:
        out["verdict"] = "SURFACE_VS_LAW_2022_LOCAL"
    W("39_SURFACE_VS_LAW_GENERALIZATION.csv")(out.round(3))
