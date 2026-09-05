# ================================================================ 17 potential-realization relations
def realization_relations():
    coords = {
        "DEMAND": demand_arr, "CAPACITY": cap_arr, "THRESHOLD": thr_pos,
        "TRANSFER": te_arr, "GAIN": GAIN_F, "CEILING": CEIL_F,
        "EXIT_PRESSURE": p16, "ROUTE_DEFORM": js_hist,
    }
    names = list(coords.keys())
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r = _rhoXY(coords[a], coords[b])
            # conditional dependency: partial corr controlling for DELIVERY-relevant set
            ctrl = np.nanmean([coords[c] for c in names if c not in (a, b)], axis=0)
            pr = _partial_rho(coords[a], coords[b], ctrl)[0]
            rows.append(dict(coord_a=a, coord_b=b,
                             rho=round(r, 3) if r == r else np.nan,
                             partial_rho=round(pr, 3) if pr == pr else np.nan,
                             relation=("AMPLIFICATION" if abs(r) > 0.4 and r > 0 else
                                       ("SUPPRESSION" if abs(r) > 0.4 and r < 0 else
                                        ("MODEST" if abs(r) > 0.15 else "WEAK/INDEPENDENT")))))
    # redundancy: high pair rho AND similar delivery association
    mm = np.isfinite(prop7)
    y = (prop7 >= 0.5).astype(float)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra = _rhoXY(coords[a], y)
            rb = _rhoXY(coords[b], y)
            if abs(ra - rb) < 0.05 and abs(_rhoXY(coords[a], coords[b])) > 0.5:
                rows.append(dict(coord_a=a, coord_b=b, rho=round(_rhoXY(coords[a], coords[b]), 3),
                                 relation="REDUNDANT_DOWNSTREAM"))
    out = pd.DataFrame(rows)
    # state localization: rho stability across subperiods for key pairs
    sp_rows = []
    for a, b in (("THRESHOLD", "TRANSFER"), ("THRESHOLD", "GAIN"), ("GAIN", "CEILING"),
                 ("EXIT_PRESSURE", "TRANSFER"), ("CAPACITY", "THRESHOLD")):
        for sp in SUBPERIODS:
            m = subp_arr == sp
            r = _rhoXY(coords[a][m], coords[b][m])
            sp_rows.append(dict(coord_a=a, coord_b=b, subperiod=sp,
                                rho=round(r, 3) if r == r else np.nan))
    spdf = pd.DataFrame(sp_rows)
    spdf["regime_modulated"] = spdf.groupby(["coord_a", "coord_b"])["rho"].transform(lambda s: float(np.nanstd(s)) > 0.25)
    W("17_REALIZATION_RELATIONS.csv")(out.round(3))
    W("17b_REALIZATION_RELATIONS_SUBPERIOD.csv")(spdf.round(3))


# ================================================================ 18 realization constraint network
def realization_constraint_network():
    coords = {
        "DEMAND": demand_arr, "CAPACITY": cap_arr, "THRESHOLD": thr_pos,
        "TRANSFER": te_arr, "GAIN": GAIN_F, "CEILING": CEIL_F,
        "EXIT_PRESSURE": p16, "ROUTE_DEFORM": js_hist,
        "FORCING": fc_arr,
    }
    names = list(coords.keys())
    rows = []
    ctrl = np.nanmean([coords[c] for c in names if c not in ("DEMAND", "CAPACITY", "THRESHOLD", "TRANSFER", "EXIT_PRESSURE")], axis=0)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r = _rhoXY(coords[a], coords[b])
            pr = _partial_rho(coords[a], coords[b], ctrl)[0]
            tag = "NULL"
            if abs(r) > 0.4:
                tag = "SUPPORTED"
            elif abs(r) > 0.2:
                # check subperiod stability
                rr = []
                for sp in SUBPERIODS:
                    m = subp_arr == sp
                    v = _rhoXY(coords[a][m], coords[b][m])
                    if v == v:
                        rr.append(v)
                tag = "REGIME_MODULATED" if (len(rr) >= 3 and np.nanstd(rr) > 0.2) else "STATE_LOCAL"
            elif abs(pr) > 0.2 and abs(r) <= 0.1:
                tag = "CONDITIONAL_ONLY"
            rows.append(dict(node_a=a, node_b=b, rho=round(r, 3) if r == r else np.nan,
                             partial_rho=round(pr, 3) if pr == pr else np.nan,
                             tag=tag))
    out = pd.DataFrame(rows)
    out["verdict"] = "DESCRIPTIVE_GRAPH"
    W("18_REALIZATION_CONSTRAINT_NETWORK.csv")(out.round(3))


# ================================================================ 19 realization minimal sets
def realization_minimal_sets():
    import itertools
    y = (prop7 >= 0.5).astype(float)
    mm = np.isfinite(prop7)
    c_met = {
        "DEMAND": demand_arr >= np.nanquantile(demand_arr, 0.67),
        "CAPACITY": cap_arr >= np.nanquantile(cap_arr, 0.67),
        "THRESHOLD": thr_pos >= np.nanquantile(thr_pos, 0.67),
        "TRANSFER": te_arr >= np.nanquantile(te_arr, 0.67),
        "EXIT_PRESSURE": p16 >= np.nanquantile(p16, 0.67),
        "NON_SATURATED": field_act <= np.nanquantile(field_act, 0.8),
        "GAIN_HI": GAIN_F >= np.nanquantile(GAIN_F, 0.67),
    }
    cnames = list(c_met.keys())
    rows = []
    base = float(y[mm].mean())
    rows.append(dict(k=0, subset="BASE", n=int(mm.sum()), deliver_rate=round(base, 3), target="DELIVERY"))
    # frequent minimal sets: all pairs and triples with support
    for k in (1, 2, 3):
        for combo in itertools.combinations(cnames, k):
            m = mm.copy()
            for c in combo:
                m = m & c_met[c]
            if m.sum() < 40:
                continue
            rows.append(dict(k=k, subset="+".join(combo), n=int(m.sum()),
                             deliver_rate=round(float(y[m].mean()), 3),
                             stall_rate=round(float((prop7[m] <= np.nanquantile(prop7, 0.33)).mean()), 3),
                             target="DELIVERY"))
    # stall / abort / sat-without-delivery target subsets
    stall = prop7 <= np.nanquantile(prop7, 0.33)
    swod = SAT_HI & (~DELIV)
    for target, tmask in (("STALL", stall), ("SAT_WITHOUT_DELIVERY", swod)):
        for k in (2, 3):
            for combo in itertools.combinations(cnames, k):
                m = mm.copy()
                for c in combo:
                    m = m & c_met[c]
                if m.sum() < 40:
                    continue
                rows.append(dict(k=k, subset="+".join(combo), n=int(m.sum()),
                                 target=target,
                                 rate=round(float(tmask[m].mean()), 3)))
    out = pd.DataFrame(rows)
    # minimal sets: for each target, smallest k whose max rate > 0.7
    summ = []
    for target in ("DELIVERY", "STALL", "SAT_WITHOUT_DELIVERY"):
        sub = out[out["target"] == target].copy()
        if len(sub) == 0:
            continue
        rate_col = "deliver_rate" if target == "DELIVERY" else "rate"
        for k in (1, 2, 3):
            ksub = sub[sub["k"] == k]
            if len(ksub) == 0:
                continue
            top = ksub.loc[ksub[rate_col].idxmax()]
            summ.append(dict(target=target, minimal_k=k,
                             best_subset=top["subset"], best_rate=round(float(top[rate_col]), 3)))
    sdf = pd.DataFrame(summ)
    W("19_REALIZATION_MINIMAL_SETS.csv")(out.round(3))
    W("19b_REALIZATION_MINIMAL_SETS_SUMMARY.csv")(sdf.round(3))


# ================================================================ 20 realization equifinality
def realization_equifinality():
    import itertools
    y = (prop7 >= 0.5).astype(float)
    mm = np.isfinite(prop7) & np.isfinite(GAIN_F)
    deliv = np.where(mm)[0][y[mm] >= 0.5]
    c_met = {
        "DEMAND": demand_arr, "CAPACITY": cap_arr, "THRESHOLD": thr_pos,
        "TRANSFER": te_arr, "EXIT_PRESSURE": p16, "GAIN": GAIN_F,
    }
    cnames = list(c_met.keys())
    # encode each delivery day as met/unmet pattern (above median)
    pat = np.zeros((len(deliv), len(cnames)), dtype=int)
    for j, c in enumerate(cnames):
        med = np.nanmedian(c_met[c])
        pat[:, j] = (c_met[c][deliv] >= med).astype(int)
    pat_key = ["".join(str(x) for x in row) for row in pat]
    from collections import Counter
    cnt = Counter(pat_key)
    n_patterns = len(cnt)
    top = cnt.most_common(8)
    rows = []
    for pk, c in top:
        mask = np.array([k == pk for k in pat_key])
        d = delivery_days = int(c)
        # characterize pattern
        on = [cnames[j] for j in range(len(cnames)) if pk[j] == "1"]
        rows.append(dict(pattern=pk, n_delivery_days=d, frac=round(c / len(deliv), 3),
                         constraints_met="+".join(on) if on else "NONE"))
    # distinctness: are top patterns spread across multiple constraint combos?
    rows.append(dict(pattern="TOTAL", n_delivery_days=int(len(deliv)),
                     frac=1.0, constraints_met=f"{n_patterns}_distinct_patterns"))
    out = pd.DataFrame(rows)
    # equifinality verdict
    top3_frac = float(sum(c for _, c in top[:3]) / max(len(deliv), 1))
    if n_patterns >= 8 and top3_frac < 0.6:
        verd = "MULTIPLE_REALIZATION_PATHS"
    elif top3_frac > 0.8:
        verd = "ONE_DOMINANT_CONSTRAINT_CORE"
    else:
        verd = "STATE_LOCAL_PATHS"
    out["verdict"] = verd
    W("20_REALIZATION_EQUIFINALITY.csv")(out.round(3))
