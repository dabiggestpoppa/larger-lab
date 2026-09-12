# ================================================================ shared rolling thr50 (reuse M19 compute)
THR50_ROLL = M99.THR50_ROLL
THR50 = {p: THR50_ROLL[p].to_numpy() for p in DEPTH_ORDER}


def _inversion_days(margin=0.15):
    """Daily inversion indicator: deeper patch activates earlier than shallower
    by a threshold-margin (thr50 shallow - thr50 deep > margin)."""
    invs = np.zeros(ns, dtype=bool)
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (THR50[a] - THR50[b]) > margin
            g = np.where(np.isnan(THR50[a]) | np.isnan(THR50[b]), False, g)
            invs = invs | g
    return invs


# ================================================================ 25 threshold inversion materiality
def threshold_inversion_materiality():
    invs = _inversion_days()
    rows = []
    # 1) absolute physical response size: activation gap between inverted patches
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (THR50[a] - THR50[b]) > 0.15
            g = np.where(np.isnan(THR50[a]) | np.isnan(THR50[b]), False, g)
            if g.sum() < 20:
                continue
            act_gap = np.nanmean(act[a].to_numpy()[g] - act[b].to_numpy()[g])
            thr_gap = np.nanmean(THR50[a][g] - THR50[b][g])
            rows.append(dict(probe=f"pair_{a}_vs_{b}", n_inversion_days=int(g.sum()),
                             thr50_gap=round(float(thr_gap), 4),
                             activation_gap_shallow_minus_deep=round(float(act_gap), 4),
                             absolute_response_size=round(float(abs(act_gap)), 4)))
    out = pd.DataFrame(rows)
    # overall materiality: mean |activation gap| during inversions
    gaps = []
    for i, a in enumerate(DEPTH_ORDER):
        for b in DEPTH_ORDER[i + 1:]:
            g = (THR50[a] - THR50[b]) > 0.15
            g = np.where(np.isnan(THR50[a]) | np.isnan(THR50[b]), False, g)
            gaps.append(np.abs(np.nanmean(act[a].to_numpy()[g] - act[b].to_numpy()[g])))
    gaps = [x for x in gaps if x == x]
    mean_gap = float(np.nanmean(gaps)) if gaps else np.nan
    # standardized: relative to typical activation spread within patches
    act_std = float(np.nanmean([np.nanstd(act[p].to_numpy()) for p in DEPTH_ORDER]))
    std_gap = mean_gap / max(act_std, 1e-9) if mean_gap == mean_gap else np.nan
    # volatility normalization: is inversion more likely in high-vol?
    m = np.isfinite(vol_med)
    rows.append(dict(probe="OVERALL", n_inversion_days=int(invs.sum()),
                     mean_abs_activation_gap=round(mean_gap, 4) if mean_gap == mean_gap else np.nan,
                     standardized_gap_z=round(std_gap, 3) if std_gap == std_gap else np.nan,
                     vol_during_inversion=round(float(np.nanmean(vol_med[invs])), 4),
                     vol_baseline=round(float(np.nanmean(vol_med[m])), 4),
                     stablecoin_during_inversion=round(float(np.nanmean(stable[invs])), 4),
                     stablecoin_baseline=round(float(np.nanmean(stable[m])), 4),
                     n_assets_patch="DATA_BLOCKED(panel-aggregate)",
                     constituent_turnover="DATA_BLOCKED",
                     liquidity="DATA_BLOCKED",
                     asset_age="DATA_BLOCKED",
                     missingness_act=round(float(np.mean(np.isnan(act[g6 == g6[invs][0] if np.any(invs) else 0].to_numpy()))), 4)))
    # survivorship / rank migration proxy: rank7 recruitment during inversions
    rows.append(dict(probe="RANK_MIGRATION_PROXY", n_inversion_days=int(invs.sum()),
                     rank7_during=round(float(np.nanmean(rank7[invs])), 3),
                     rank7_baseline=round(float(np.nanmean(rank7[m])), 3)))
    out = pd.DataFrame(rows)
    if len(out) and std_gap == std_gap:
        out["verdict"] = ("MATERIAL" if std_gap > 0.5 else ("MARGINAL" if std_gap > 0.25 else "COMPOSITION_ARTIFACT"))
    else:
        out["verdict"] = "DATA_LIMITED"
    W("25_THRESHOLD_INVERSION_MATERIALITY.csv")(out.round(4))


# ================================================================ 26 threshold inversion post audit
def threshold_inversion_post_audit():
    mat = pd.read_csv(OUT / "25_THRESHOLD_INVERSION_MATERIALITY.csv")
    verd = mat["verdict"].iloc[0] if len(mat) else "DATA_LIMITED"
    rows = []
    if verd in ("COMPOSITION_ARTIFACT", "DATA_LIMITED"):
        W("26_THRESHOLD_INVERSION_POST_AUDIT.csv")(
            pd.DataFrame([dict(verdict=f"NOT_APPLICABLE_{verd}", note="materiality gate not passed; mechanism analysis demoted")]))
        return
    invs = _inversion_days()
    ep = run_episodes(invs)
    eps = [(a, b) for (a, b) in ep if (b - a + 1) >= 3]
    if len(eps) == 0:
        W("26_THRESHOLD_INVERSION_POST_AUDIT.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    for (a, b) in eps:
        rows.append(dict(start=str(dates[a].date()), end=str(dates[b].date()), dur=int(b - a + 1),
                         state=str(g6[a]),
                         exit_pressure=round(float(np.nanmean(p16[a:b + 1])), 3),
                         exit_entropy=round(float(np.nanmean(ent6[a:b + 1])), 3),
                         forcing=round(float(np.nanmean(fc_arr[a:b + 1])), 3),
                         gain=round(float(np.nanmean(GAIN_F[a:b + 1])), 3),
                         capacity=round(float(np.nanmean(cap_arr[a:b + 1])), 3),
                         physical_disturbance=round(float(np.nanmean(mc30[a:b + 1])), 3),
                         rank_recruitment=round(float(np.nanmean(rank7[a:b + 1])), 3),
                         concentration_release=round(float(np.nanmean(np.asarray(fams["CONCENTRATION_RELEASE_FORCING"], dtype=float)[a:b + 1])), 3)))
    out = pd.DataFrame(rows)
    out["verdict"] = f"MATERIALITY_PASSED_{verd}"
    W("26_THRESHOLD_INVERSION_POST_AUDIT.csv")(out.round(3))


# ================================================================ 27 threshold inversion function
def threshold_inversion_function():
    mat = pd.read_csv(OUT / "25_THRESHOLD_INVERSION_MATERIALITY.csv")
    verd = mat["verdict"].iloc[0] if len(mat) else "DATA_LIMITED"
    if verd in ("COMPOSITION_ARTIFACT", "DATA_LIMITED"):
        W("27_THRESHOLD_INVERSION_FUNCTION.csv")(
            pd.DataFrame([dict(verdict=f"DEMOTED_{verd}", function="NONE_ARTIFACT")]))
        return
    invs = _inversion_days()
    ep = run_episodes(invs)
    eps = [(a, b) for (a, b) in ep if (b - a + 1) >= 3]
    rows = []
    for (a, b) in eps:
        # which bands inverted
        pairs = []
        for i, aa in enumerate(DEPTH_ORDER):
            for bb in DEPTH_ORDER[i + 1:]:
                seg = (THR50[aa][a:b + 1] - THR50[bb][a:b + 1]) > 0.15
                if np.nanmean(seg) > 0.5:
                    pairs.append(f"{aa}<{bb}")
        deep_pair = any(p.startswith("751-1000") or p.startswith("1001-1500") or p.startswith("1501-2000") for p in pairs)
        shallow_pair = any(p.startswith("26-100") or p.startswith("101-250") for p in pairs)
        # context classification
        d = int(b - a + 1)
        f = float(np.nanmean(fc_arr[a:b + 1]))
        qf = np.nanquantile(fc_arr, [0.33, 0.67])
        rec = float(np.nanmean(rank7[a:b + 1]))
        if deep_pair and shallow_pair:
            func = "PATCH_BYPASS"
        elif deep_pair and f >= qf[1]:
            func = "DEEP_EARLY_ACTIVATION"
        elif deep_pair:
            func = "ROUTE_SPECIFIC_RECRUITMENT"
        elif not deep_pair:
            func = "SHALLOW_SUPPRESSION"
        else:
            func = "OTHER"
        rows.append(dict(start=str(dates[a].date()), end=str(dates[b].date()), dur=d,
                         pairs="|".join(pairs), function=func,
                         forcing_tier="HIGH" if f >= qf[1] else ("LOW" if f <= qf[0] else "MID"),
                         rank_recruitment=round(rec, 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("27_THRESHOLD_INVERSION_FUNCTION.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    vc = out["function"].value_counts()
    if len(vc) == 1:
        out["verdict"] = f"FEW_INVERSION_MECHANISMS_({vc.index[0]}_dominant)"
    elif len(vc) <= 3:
        out["verdict"] = "FEW_INVERSION_MECHANISMS"
    else:
        out["verdict"] = "CONTINUOUS_INVERSION_GEOMETRY"
    W("27_THRESHOLD_INVERSION_FUNCTION.csv")(out.round(3))
