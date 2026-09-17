# ================================================================ 21 birth failure deep
def birth_failure_deep():
    rows = []
    coords = {
        "live_exits": k6, "entropy": ent6, "dominant_share": p16,
        "pressure_concentration": p16 - p26, "forcing": fc_arr,
        "gain": GAIN_F, "ceiling": CEIL_F, "threshold": thr_pos,
        "transfer": te_arr, "capacity": cap_arr, "demand_slope": np.concatenate([[np.nan], np.diff(demand_arr)]),
    }
    p1_std = pd.Series(p16).rolling(7, min_periods=3).std().to_numpy()
    coords["dominant_instability"] = p1_std
    # pruning indicator at INITIATION: live exits dropping over prior 7d
    prun = np.full(ns, np.nan); prun[7:] = k6[7:] - k6[:-7]
    coords["pruning_rate"] = prun
    for stage in STAGES18:
        for name, arr in coords.items():
            vv = _stage_arr(vi_, arr, stage); av = _stage_arr(ab_, arr, stage)
            vv = vv[~np.isnan(vv)]; av = av[~np.isnan(av)]
            if len(vv) < 15 or len(av) < 15:
                continue
            d = abs(np.mean(vv) - np.mean(av)) / max((np.std(vv) + np.std(av)) / 2, 1e-9)
            p = float(ranksums(vv, av).pvalue)
            rows.append(dict(stage=stage, coordinate=name,
                             viable_mean=round(float(np.mean(vv)), 4),
                             aborted_mean=round(float(np.mean(av)), 4),
                             cohens_d=round(d, 3), p_value=round(p, 4)))
    out = pd.DataFrame(rows)
    # top discriminators per stage
    out["abs_d"] = out["cohens_d"].abs()
    top = out.loc[out.groupby("stage")["abs_d"].idxmax(), ["stage", "coordinate", "cohens_d"]]
    out["verdict"] = "MEASURED"
    W("21_BIRTH_FAILURE_DEEP.csv")(out.round(4))
    W("21b_BIRTH_FAILURE_TOP_DISCRIMINATORS.csv")(top.round(3))


# ================================================================ 22 load-resolution mismatch
def load_resolution_mismatch():
    # LOAD_ARRIVAL_RATE = d(demand)/dt + d(forcing)/dt (smoothed)
    load_rate = pd.Series(demand_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    load_rate = load_rate + pd.Series(fc_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    # ROUTE_RESOLUTION_RATE = -d(entropy)/dt (positive = resolving) and -d(live exits)/dt
    res_rate = -pd.Series(ent6).diff().rolling(3, min_periods=2).mean().to_numpy()
    res_rate = res_rate + (-pd.Series(k6).diff().rolling(3, min_periods=2).mean().to_numpy())
    rows = []
    for stage in STAGES18:
        vl = _stage_arr(vi_, load_rate, stage); al = _stage_arr(ab_, load_rate, stage)
        vr = _stage_arr(vi_, res_rate, stage); ar = _stage_arr(ab_, res_rate, stage)
        vl = vl[~np.isnan(vl)]; al = al[~np.isnan(al)]
        vr = vr[~np.isnan(vr)]; ar = ar[~np.isnan(ar)]
        if min(len(vl), len(al), len(vr), len(ar)) < 12:
            continue
        rows.append(dict(stage=stage,
                         load_rate_viable=round(float(np.mean(vl)), 4),
                         load_rate_aborted=round(float(np.mean(al)), 4),
                         resolution_rate_viable=round(float(np.mean(vr)), 4),
                         resolution_rate_aborted=round(float(np.mean(ar)), 4),
                         mismatch_d=round(float(abs(np.mean(al) - np.mean(vl)) / max((np.std(al) + np.std(vl)) / 2, 1e-9)), 3),
                         resolution_d=round(float(abs(np.mean(ar) - np.mean(vr)) / max((np.std(ar) + np.std(vr)) / 2, 1e-9)), 3),
                         load_vs_resolve=("LOAD_OUTPACES_RESOLUTION" if np.mean(al) - np.mean(ar) > np.mean(vl) - np.mean(vr) else "BALANCED")))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("22_LOAD_RESOLUTION_MISMATCH.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    promotable = (out["load_vs_resolve"] == "LOAD_OUTPACES_RESOLUTION").any()
    out["verdict"] = "PROMOTE" if promotable else "LOCAL"
    W("22_LOAD_RESOLUTION_MISMATCH.csv")(out.round(4))


# ================================================================ 23 birth failure surface
def birth_failure_surface():
    load_rate = pd.Series(demand_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    load_rate = load_rate + pd.Series(fc_arr).diff().rolling(3, min_periods=2).mean().to_numpy()
    res_rate = -pd.Series(ent6).diff().rolling(3, min_periods=2).mean().to_numpy()
    res_rate = res_rate + (-pd.Series(k6).diff().rolling(3, min_periods=2).mean().to_numpy())
    # at INITIATION only
    lr = _stage_arr(bp_, load_rate, "INITIATION")
    rr = _stage_arr(bp_, res_rate, "INITIATION")
    out_bin = np.array([1 if i in ab_ else 0 for i in bp_])
    m = np.isfinite(lr) & np.isfinite(rr)
    if m.sum() < 40:
        W("23_BIRTH_FAILURE_SURFACE.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED", n=int(m.sum()))]))
        return
    rows = []
    lq = np.nanquantile(lr[m], np.linspace(0, 1, 4))
    rq = np.nanquantile(rr[m], np.linspace(0, 1, 4))
    for li in range(3):
        for ri in range(3):
            cell = m & (lr >= lq[li]) & (lr < lq[li + 1]) & (rr >= rq[ri]) & (rr < rq[ri + 1])
            if cell.sum() < 5:
                continue
            rows.append(dict(load_band=f"L{li+1}", resolve_band=f"R{ri+1}",
                             n=int(cell.sum()),
                             abort_rate=round(float(out_bin[cell].mean()), 3)))
    out = pd.DataFrame(rows)
    if len(out):
        # gradient check: abort rate increases with load and decreases with resolution?
        hi_ab = out[(out["load_band"] == "L3")]["abort_rate"].mean()
        lo_ab = out[(out["load_band"] == "L1")]["abort_rate"].mean()
        hi_res = out[(out["resolve_band"] == "R3")]["abort_rate"].mean()
        lo_res = out[(out["resolve_band"] == "R1")]["abort_rate"].mean()
        out["verdict"] = (f"SURFACE(load_d={round(hi_ab-lo_ab,3)},resolve_d={round(lo_res-hi_res,3)})"
                          if (hi_ab - lo_ab > 0.05 or lo_res - hi_res > 0.05) else "FLAT_OR_DATA_LIMITED")
    else:
        out["verdict"] = "DATA_LIMITED"
    W("23_BIRTH_FAILURE_SURFACE.csv")(out.round(3))


# ================================================================ 24 birth recovery path
def birth_recovery_path():
    rows = []
    varmap = {"demand": demand_arr, "routes_prune": k6, "pressure_concentrates": p16,
              "transfer_repairs": te_arr, "threshold_normalizes": thr_pos,
              "gain_changes": GAIN_F, "entropy_collapses": ent6}
    for i in ab_:
        cand = bp_[bp_ > i]
        if len(cand) == 0:
            continue
        r = int(cand[0])
        viable = not (g6[r + 1:min(r + 8, ns)] == prev_[r]).any()
        if not viable:
            continue
        changes = {}
        for name, arr in varmap.items():
            pre = np.nanmean(arr[max(0, i - 5):i]); post = np.nanmean(arr[max(0, r - 5):r])
            if np.isfinite(pre) and np.isfinite(post):
                changes[name] = post - pre
        if not changes:
            continue
        first = max(changes, key=lambda k: abs(changes[k]))
        rows.append(dict(aborted_date=str(dates[i].date()), recovery_date=str(dates[r].date()),
                         days_to_recovery=int(r - i),
                         first_change=first,
                         delta_first=round(float(changes[first]), 4),
                         demand_cooled=bool(changes.get("demand", 0) < 0),
                         routes_pruned=bool(changes.get("routes_prune", 0) < 0),
                         pressure_concentrated=bool(changes.get("pressure_concentrates", 0) > 0),
                         transfer_repaired=bool(changes.get("transfer_repairs", 0) > 0),
                         threshold_normalized=bool(changes.get("threshold_normalizes", 0) > 0),
                         gain_changed=bool(abs(changes.get("gain_changes", 0)) > 0.05)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("24_BIRTH_RECOVERY_PATH.csv")(pd.DataFrame([dict(verdict="NO_VIABLE_RECOVERIES")]))
        return
    agg = out["first_change"].value_counts().reset_index()
    agg.columns = ["first_change", "n_episodes"]
    agg["frac"] = round(agg["n_episodes"] / len(out), 3)
    W("24_BIRTH_RECOVERY_PATH.csv")(out.round(4))
    W("24b_BIRTH_RECOVERY_ORDER_AGG.csv")(agg.round(3))
