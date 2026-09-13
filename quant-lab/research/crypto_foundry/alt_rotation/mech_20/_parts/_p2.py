# ================================================================ shared sat-with/without masks
SAT_HI = field_act >= np.nanquantile(field_act, 0.66)
DELIV = prop7 >= 0.5
NOD = SAT_HI & (~DELIV) & np.isfinite(prop7)
WITH = SAT_HI & DELIV & np.isfinite(prop7)

# ================================================================ 08 saturation failure matched
def _mean_diff(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) < 20 or len(b) < 20:
        return np.nan, np.nan, np.nan
    p = float(ranksums(a, b).pvalue)
    return float(np.nanmean(a)), float(np.nanmean(b)), p


def saturation_failure_matched():
    rows = []
    # matching covariates: state, gain, ceiling, demand, saturation position
    feat = np.column_stack([GAIN_F, CEIL_F, demand_arr, field_act])
    feat = np.where(np.isfinite(feat), feat, np.nan)
    idx_from = np.where(NOD & np.all(np.isfinite(feat), 1))[0]
    idx_to = np.where(WITH & np.all(np.isfinite(feat), 1))[0]
    if len(idx_from) < 30 or len(idx_to) < 30:
        W("08_SATURATION_FAILURE_MATCHED.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    # greedy nearest-neighbour within same 6-cell state
    matched = {}
    for st in np.unique(g6):
        f_ = idx_from[g6[idx_from] == st]
        t_ = idx_to[g6[idx_to] == st]
        if len(f_) < 10 or len(t_) < 10:
            continue
        sub_feat = feat[np.concatenate([f_, t_])]
        # per-state standardization
        mu = np.nanmean(sub_feat, axis=0); sd = np.nanstd(sub_feat, axis=0) + 1e-9
        fX = (feat[f_] - mu) / sd; tX = (feat[t_] - mu) / sd
        for jj, i in enumerate(f_):
            d = np.nansum((tX - fX[jj]) ** 2, axis=1)
            d = np.where(np.isfinite(d), d, np.inf)
            matched[i] = int(t_[np.argmin(d)])
    if len(matched) < 25:
        W("08_SATURATION_FAILURE_MATCHED.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED", n_matched=len(matched))]))
        return
    f_idx = np.array(list(matched.keys()), dtype=int)
    t_idx = np.array(list(matched.values()), dtype=int)
    comp = {"threshold_position": thr_pos, "transfer": te_arr, "forcing": fc_arr,
            "route_deformation": js_hist, "exit_pressure": p16, "exit_entropy": ent6,
            "volatility": vol_med, "stablecoin": stable, "btc_anchor": btc,
            "participation": possh, "capacity": cap_arr, "gain": GAIN_F, "ceiling": CEIL_F}
    for name, arr in comp.items():
        a, b, p = _mean_diff(arr[f_idx], arr[t_idx])
        rows.append(dict(variable=name, n_matched=int(len(f_idx)),
                         mean_without=round(a, 4) if a == a else np.nan,
                         mean_with=round(b, 4) if b == b else np.nan,
                         diff=round(a - b, 4) if (a == a and b == b) else np.nan,
                         ranksums_p=round(p, 4) if p == p else np.nan))
    # resolution mechanism split (from M18 04)
    dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
    dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
    mech_nod = [dr6.get(g6[i]) for i in f_idx]
    mech_wit = [dr6.get(g6[i]) for i in t_idx]
    rows.append(dict(variable="resolution_mechanism_prune_frac",
                     n_matched=int(len(f_idx)),
                     mean_without=round(float(np.mean([m == "EDGE_PRUNING" for m in mech_nod])), 3),
                     mean_with=round(float(np.mean([m == "EDGE_PRUNING" for m in mech_wit])), 3),
                     diff=round(float(np.mean([m == "EDGE_PRUNING" for m in mech_nod]) - np.mean([m == "EDGE_PRUNING" for m in mech_wit])), 3)))
    # forcing-family composition comparison
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        a, b, p = _mean_diff(f[f_idx], f[t_idx])
        rows.append(dict(variable=f"forcing_{fam}", n_matched=int(len(f_idx)),
                         mean_without=round(a, 4) if a == a else np.nan,
                         mean_with=round(b, 4) if b == b else np.nan,
                         diff=round(a - b, 4) if (a == a and b == b) else np.nan,
                         ranksums_p=round(p, 4) if p == p else np.nan))
    out = pd.DataFrame(rows)
    W("08_SATURATION_FAILURE_MATCHED.csv")(out.round(4))


# ================================================================ 09 saturation failure transitions
def saturation_failure_transitions():
    ep = run_episodes(NOD)
    rows = []
    for (a, b) in ep:
        if (b - a + 1) < 2:
            continue
        end = b + 1
        rec = {"start": str(dates[a].date()), "end": str(dates[b].date()), "dur": int(b - a + 1)}
        for hz, hzn in ((1, 1), (3, 3), (7, 7), (14, 14), (30, 30)):
            w = slice(min(end, ns - 1), min(end + hz, ns))
            if w.start >= w.stop:
                continue
            rec[f"forcing_strengthens_{hz}d"] = bool(np.nanmean(fc_arr[w]) > np.nanmean(fc_arr[a:b + 1]) + 0.1 * np.nanstd(fc_arr))
            rec[f"threshold_satisfied_{hz}d"] = bool(np.nanmean(thr_pos[w]) > np.nanquantile(thr_pos, 0.67))
            rec[f"transfer_repairs_{hz}d"] = bool(np.nanmean(te_arr[w]) > np.nanmean(te_arr[a:b + 1]) + 0.1 * np.nanstd(te_arr))
            rec[f"state_changed_{hz}d"] = bool(np.any(g6[w] != g6[a]))
            rec[f"saturation_decayed_{hz}d"] = bool(np.nanmean(field_act[w]) < np.nanmean(field_act[a:b + 1]) - 0.1 * np.nanstd(field_act))
            rec[f"realization_occurs_{hz}d"] = bool(np.any(prop7[w] >= 0.5))
            rec[f"exits_reopen_or_prune_{hz}d"] = bool(np.nanmean(ent6[w]) > np.nanmean(ent6[a:b + 1]) + 0.05 or np.nanmean(k6[w]) < np.nanmean(k6[a:b + 1]) - 0.05)
        rows.append(rec)
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("09_SATURATION_FAILURE_TRANSITIONS.csv")(pd.DataFrame([dict(verdict="NONE")]))
        return
    # aggregate: fraction of episodes with each event at each horizon
    agg = []
    for hz in (1, 3, 7, 14, 30):
        for ev in ("forcing_strengthens", "threshold_satisfied", "transfer_repairs",
                   "state_changed", "saturation_decayed", "realization_occurs", "exits_reopen_or_prune"):
            col = f"{ev}_{hz}d"
            if col not in out.columns:
                continue
            agg.append(dict(horizon=hz, event=ev, frac_episodes=round(float(out[col].mean()), 3)))
    ag = pd.DataFrame(agg)
    W("09_SATURATION_FAILURE_TRANSITIONS.csv")(out.round(3))
    W("09b_SATURATION_FAILURE_TRANSITION_AGG.csv")(ag.round(3))


# ================================================================ 10 saturation failure -> delivery conversion
def saturation_to_delivery():
    # episodes of NOD that later see delivery within 30d -> which variable changes first?
    ep = run_episodes(NOD)
    rows = []
    var_changes = {"transfer": te_arr, "threshold": thr_pos, "forcing": fc_arr,
                   "gain": GAIN_F, "ceiling": CEIL_F, "exit_pressure": p16,
                   "route_deformation": js_hist}
    for (a, b) in ep:
        end = b + 1
        conv = np.where(prop7[min(end, ns):min(end + 30, ns)] >= 0.5)[0]
        if len(conv) == 0:
            continue
        t_conv = end + int(conv[0])
        base = a  # pre-episode baseline
        deltas = {}
        for name, arr in var_changes.items():
            pre = np.nanmean(arr[max(0, base - 5):base])
            post = np.nanmean(arr[t_conv - 2:t_conv + 3])
            if np.isfinite(pre) and np.isfinite(post):
                deltas[name] = post - pre
        if not deltas:
            continue
        first = max(deltas, key=lambda k: abs(deltas[k]))
        rows.append(dict(ep_start=str(dates[a].date()), ep_end=str(dates[b].date()),
                         conv_date=str(dates[t_conv].date()), days_to_conv=int(t_conv - end),
                         first_changed=first,
                         delta_first=round(float(deltas[first]), 4),
                         relation="PRECEDES" if int(t_conv - end) > 3 else "COINCIDES"))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("10_SATURATION_TO_DELIVERY.csv")(pd.DataFrame([dict(verdict="NO_CONVERSIONS")]))
        return
    agg = out["first_changed"].value_counts().reset_index()
    agg.columns = ["first_changed", "n_episodes"]
    agg["frac"] = round(agg["n_episodes"] / len(out), 3)
    W("10_SATURATION_TO_DELIVERY.csv")(out.round(4))
    W("10b_SATURATION_TO_DELIVERY_AGG.csv")(agg)
