# ================================================================ 21 birth failure mechanism
def _stage_arr(ixs, arr, stage):
    """Like M18 _stage_vals but on an arbitrary daily array."""
    if stage == "PRECONDITION":
        return np.array([np.nanmean(arr[max(0, i - 7):i]) for i in ixs])
    if stage == "INITIATION":
        return arr[ixs]
    if stage == "COMMITMENT":
        return np.array([np.nanmean(arr[i + 1:min(ns, i + 4)]) for i in ixs])
    return np.array([np.nanmean(arr[min(ns - 1, i + 4):min(ns, i + 8)]) for i in ixs])

# entropy decomposition inputs at INITIATION
def _entropy_decomp(ixs):
    """Break exit entropy into: many live exits (k), route deformation (JS),
    dominant-share instability (rolling std of p1)."""
    n_live = k6; jsd = js_hist
    dom_stab = np.full(ns, np.nan)
    for t in range(8, ns):
        dom_stab[t] = np.nanstd(p16[t - 7:t])
    return _stage_arr(ixs, n_live, "INITIATION"), \
           _stage_arr(ixs, jsd, "INITIATION"), \
           _stage_arr(ixs, dom_stab, "INITIATION"), \
           _stage_arr(ixs, ent6, "INITIATION")

def birth_failure_mechanism():
    rows = []
    p1_std_vi = pd.Series(p16).rolling(7, min_periods=3).std().to_numpy()
    decomp = [("exit_entropy", ent6), ("n_live_exits", k6), ("route_deformation_js", js_hist),
              ("dominant_share_instability", p1_std_vi), ("exit_p1", p16)]
    for name, arr in decomp:
        vv = _stage_arr(vi_, arr, "INITIATION"); av = _stage_arr(ab_, arr, "INITIATION")
        vv = vv[~np.isnan(vv)]; av = av[~np.isnan(av)]
        if len(vv) < 15 or len(av) < 15:
            continue
        d = abs(np.mean(vv) - np.mean(av)) / max((np.std(vv) + np.std(av)) / 2, 1e-9)
        p = float(ranksums(vv, av).pvalue)
        rows.append(dict(coordinate=name, viable_mean=round(float(np.mean(vv)), 4),
                         aborted_mean=round(float(np.mean(av)), 4), cohens_d=round(d, 3),
                         p_value=round(p, 4),
                         direction="aborted_higher" if np.mean(av) > np.mean(vv) else "aborted_lower",
                         mechanism=("unresolved_route_set" if name in ("exit_entropy", "dominant_share_instability", "route_deformation_js")
                                    else "physical")) )
    # is high entropy driven by many-open vs unstable-probs?
    ent_hi = _stage_arr(ab_, ent6, "INITIATION") > np.nanquantile(_stage_arr(ab_, ent6, "INITIATION"), 0.5)
    if ent_hi.sum() >= 10:
        grab = ab_[ent_hi]
        a_live = np.nanmean(_stage_arr(grab, k6, "INITIATION"))
        a_stab = np.nanmean(_stage_arr(grab, p1_std_vi, "INITIATION"))
        rows.append(dict(coordinate="BOTH_OPEN_AND_UNSTABLE", viable_mean=np.nan,
                         aborted_mean=round(float(a_live), 3), cohens_d=np.nan, p_value=np.nan,
                         direction="n_live=%s std_p1=%s" % (round(float(a_live), 2), round(float(a_stab), 3)),
                         mechanism="diagnostic"))
    W("21_BIRTH_FAILURE_MECHANISM.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 22 load commitment mismatch
def load_commitment_mismatch():
    # load = incoming demand slope; commitment = persistence of dominant route (1-p(reopen in +/- horizon))
    # use p1 separation as commitment proxy normalized by demand
    rows = []
    demand_slope = np.full(ns, np.nan); demand_slope[1:] = np.diff(demand_arr)
    for st in STAGES18:
        vi_l = _stage_arr(vi_, demand_slope, st); ab_l = _stage_arr(ab_, demand_slope, st)
        # commitment: forward persistence of dominant share (p1 minus p2 gap)
        commit_arr = np.asarray(p16 - p26, dtype=float)
        vi_c = _stage_arr(vi_, commit_arr, st); ab_c = _stage_arr(ab_, commit_arr, st)
        vv = vi_l[~np.isnan(vi_l)]; av = ab_l[~np.isnan(ab_l)]
        vc = vi_c[~np.isnan(vi_c)]; ac = ab_c[~np.isnan(ab_c)]
        if min(len(vv), len(av), len(vc), len(ac)) < 15:
            continue
        rows.append(dict(stage=st,
                         demand_slope_viable=round(float(np.mean(vv)), 4),
                         demand_slope_aborted=round(float(np.mean(av)), 4),
                         commitment_gap_viable=round(float(np.mean(vc)), 3),
                         commitment_gap_aborted=round(float(np.mean(ac)), 3),
                         mismatch="DEMAND_OUTPACES_COMMITMENT" if np.mean(av) - np.mean(ac) > np.mean(vv) - np.mean(vc) else "BALANCED"))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("22_LOAD_COMMITMENT_MISMATCH.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    out["verdict"] = "LOCAL" if (out["mismatch"] == "DEMAND_OUTPACES_COMMITMENT").any() else "DISSOLVE"
    W("22_LOAD_COMMITMENT_MISMATCH.csv")(out.round(3))

# ================================================================ 23 birth recovery
def birth_recovery():
    rows = []
    for i in ab_:
        # next formation point after i
        cand = bp_[bp_ > i]
        if len(cand) == 0:
            continue
        r = int(cand[0])
        # is it viable (not aborted)?
        viable = False
        if (g6[r + 1:min(r + 8, ns)] != prev_[r]).any():
            viable = False
        else:
            viable = True
        same_state = g6[r] == g6[i]
        ent_collapsed = np.nanmean(ent6[i - 3:i]) > np.nanmean(ent6[r - 3:r])
        demand_cooled = np.nanmean(demand_arr[r - 3:r]) < np.nanmean(demand_arr[i - 3:i])
        thr_normalized = np.nanmean(thr_pos[r - 3:r]) - np.nanmean(thr_pos[i - 3:i])
        rows.append(dict(aborted_date=str(dates[i].date()), recovery_date=str(dates[r].date()),
                         days_to_recovery=int(r - i),
                         recovered_as_viable=viable, same_state_return=bool(same_state),
                         entropy_collapsed_first=bool(ent_collapsed),
                         demand_cooled_first=bool(demand_cooled),
                         threshold_delta=round(float(thr_normalized), 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("23_BIRTH_RECOVERY.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    W("23_BIRTH_RECOVERY.csv")(out.round(3))

# ================================================================ 24 potential realization constraints
_med = lambda a: np.nanmedian(a)
_c_met = {
    "DEMAND": demand_arr >= _med(demand_arr),
    "CAPACITY": cap_arr >= _med(cap_arr),
    "THRESHOLD": thr_pos >= _med(thr_pos),
    "EXIT_PRESSURE": p16 >= _med(p16),
    "TRANSFER": te_arr >= _med(te_arr),
    "NON_SATURATED": field_act <= np.nanquantile(field_act, 0.8),
}
_realize = prop7 >= 0.5          # prop7 is a 0/1 realized-propagation flag

def potential_realization_constraints():
    base = float(_realize.mean())
    rows = []
    for name, met in _c_met.items():
        mmet = met & np.isfinite(prop7); mn = (~met) & np.isfinite(prop7)
        if mmet.sum() < 60 or mn.sum() < 60:
            continue
        p_met = float(_realize[mmet].mean()); p_not = float(_realize[mn].mean())
        necessity = 1 - p_not               # high => unmet almost never delivers
        sufficiency = p_met                   # high => met usually delivers
        if necessity > 0.85:
            role = "NECESSARY_CANDIDATE"
        elif sufficiency > 0.7:
            role = "SUFFICIENT_LIKE"
        elif abs(p_met - p_not) < 0.05:
            role = "REDUNDANT"
        else:
            role = "SUBSTITUTABLE"
        rows.append(dict(constraint=name, n_met=int(mmet.sum()), n_unmet=int(mn.sum()),
                         p_realize_met=round(p_met, 3), p_realize_unmet=round(p_not, 3),
                         base_rate=round(base, 3), lift_met=round(p_met - base, 3),
                         role=role))
    W("24_POTENTIAL_REALIZATION_CONSTRAINTS.csv")(pd.DataFrame(rows).round(3))

# ================================================================ 25 constraint combination lattice
def constraint_combination_lattice():
    cnames = list(_c_met.keys())
    rows = []
    m_ok = np.isfinite(prop7)
    from itertools import combinations
    # single/2/3-way met-subsets with support
    for k in (1, 2, 3):
        for combo in combinations(cnames, k):
            m = np.ones(ns, dtype=bool)
            for c in combo:
                m &= _c_met[c]
            m &= m_ok
            if m.sum() < 40:
                continue
            rows.append(dict(n_constraints_met=k, subset="+".join(combo), n=int(m.sum()),
                             deliver_rate=round(float(_realize[m].mean()), 3),
                             stall_rate=round(float((prop7[m] <= np.nanquantile(prop7, 0.33)).mean()), 3),
                             sat_without_deliv=round(float(((field_act[m] >= np.quantile(field_act[m], 0.66)) & (prop7[m] <= np.nanquantile(prop7[m], 0.33))).mean()), 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("25_CONSTRAINT_COMBINATION_LATTICE.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    W("25_CONSTRAINT_COMBINATION_LATTICE.csv")(out.round(3))

# ================================================================ 26 failure motif decomposition
MOTIF_NAMES = ["HIGH_DEMAND_LOW_TRANSFER", "HIGH_DEMAND_OPEN_EXITS",
               "THRESHOLD_CROSSED_NO_RECRUITMENT", "CAPACITY_AVAILABLE_NO_COMMITMENT",
               "EXIT_CONCENTRATION_WITH_PROPAGATION", "SATURATION_WITHOUT_DELIVERY"]

def _motif_masks():
    q = lambda a: np.nanquantile(a, 0.67); q33 = lambda a: np.nanquantile(a, 0.33)
    d = demand_arr; util = demand_arr / np.where(cap_arr > 0, cap_arr, np.nan)
    return {
        "HIGH_DEMAND_LOW_TRANSFER": (d >= q(d)) & (te_arr <= q33(te_arr)),
        "HIGH_DEMAND_OPEN_EXITS": (d >= q(d)) & (ent6 >= q(ent6)),
        "THRESHOLD_CROSSED_NO_RECRUITMENT": (thr_pos >= q(thr_pos)) & (rank7 <= q33(rank7)),
        "CAPACITY_AVAILABLE_NO_COMMITMENT": (util >= q(util)) & (d >= q(d)),
        "EXIT_CONCENTRATION_WITH_PROPAGATION": (p16 >= q(p16)) & (prop7 >= q(prop7)),
        "SATURATION_WITHOUT_DELIVERY": (field_act >= np.nanquantile(field_act, 0.8)) & (prop7 <= q33(prop7)),
    }

def failure_motif_decomposition():
    mm = _motif_masks()
    feats = ["demand", "capacity", "thr_pos", "exit_pressure", "exit_entropy", "transfer", "sat", "rank7"]
    feat_maps = {"demand": demand_arr, "capacity": cap_arr, "thr_pos": thr_pos,
                 "exit_pressure": p16, "exit_entropy": ent6, "transfer": te_arr,
                 "sat": field_act, "rank7": rank7}
    prof = {}
    rows = []
    for name, mask in mm.items():
        m = mask & np.isfinite(prop7)
        v = [np.nanmean(feat_maps[F][m]) for F in feats]
        prof[name] = np.array(v)
        rows.append(dict(motif=name, n=int(m.sum()),
                         base_delivery=round(float(np.nanmean(prop7[m])), 3),
                         resolution_type=np.nan))
    names = list(prof.keys())
    sep = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            dist = float(np.linalg.norm(prof[a] - prof[b]))
            sep.append((a, b, dist))
    sep = [s for s in sep if np.isfinite(s[2])]
    ds = pd.DataFrame(sep, columns=["motif_a", "motif_b", "feature_profile_distance"]).round(3) if sep else pd.DataFrame()
    rows_df = pd.DataFrame(rows).round(3)
    W("26_FAILURE_MOTIF_DECOMPOSITION.csv")(rows_df)
    if len(ds):
        W("26b_FAILURE_MOTIF_SEPARATION.csv")(ds)

# ================================================================ 27 realization geometry
def realization_geometry():
    Xnames = ["demand", "capacity", "thr_pos", "exit_pressure", "transfer", "sat"]
    X = np.column_stack([demand_arr, cap_arr, thr_pos, p16, te_arr, field_act])
    m = np.isfinite(prop7) & np.all(np.isfinite(X), axis=1)
    y = (prop7 >= 0.5).astype(float)[m]; Xm = X[m]
    Xs = (Xm - Xm.mean(0)) / (Xm.std(0) + 1e-9)
    split = int(len(y) * 0.7)
    order = np.arange(len(y)); rng = np.random.RandomState(0); rng.shuffle(order)
    itr, ite = order[:split], order[split:]
    rows = []
    from sklearn.metrics import roc_auc_score
    # stratified split: force both classes into the training fold
    from sklearn.model_selection import train_test_split
    auc_one = np.nan
    for ncomp in (1, 2, 3, 6):
        from sklearn.decomposition import PCA
        try:
            itr2, ite2 = train_test_split(np.arange(len(y)), test_size=0.3, random_state=0, stratify=y)
            pca = PCA(n_components=min(ncomp, Xs.shape[1])).fit(Xs[itr2])
            Zr = pca.transform(Xs[itr2]); Ze = pca.transform(Xs[ite2])
            lr = LogisticRegression(max_iter=2000).fit(Zr, y[itr2])
            auc = roc_auc_score(y[ite2], lr.predict_proba(Ze)[:, 1])
        except Exception:
            auc = np.nan
        if ncomp == 1:
            auc_one = auc
        rows.append(dict(n_coordinates=ncomp, heldout_auc=round(float(auc), 3)))
    best = max((r["heldout_auc"] for r in rows if r["heldout_auc"] == r["heldout_auc"]), default=np.nan)
    if best > 0.02 and (auc_one == auc_one and best - auc_one < 0.02):
        verd = "MULTI_AXIS_GEOMETRY(1_DOMINANT)"
    elif best > 0.05:
        verd = "FEW_CONSTRAINT_COORDINATES"
    else:
        verd = "NO_CLEAN_GEOMETRY"
    rows.append(dict(n_coordinates=np.nan, heldout_auc=np.nan, verdict=verd))
    W("27_REALIZATION_GEOMETRY.csv")(pd.DataFrame(rows).round(3))