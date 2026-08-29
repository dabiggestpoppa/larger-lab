# ================================================================ 11 capacity interpretation
def capacity_interpretation():
    rows = []
    cap_hi = cap_arr >= np.nanquantile(cap_arr, 0.67); cap_lo = cap_arr <= np.nanquantile(cap_arr, 0.33)
    mm = np.isfinite(cap_arr) & np.isfinite(prop7)
    # H1 ENABLEMENT: high capacity -> more realization
    rows.append(dict(hypothesis="H1_ENABLEMENT",
                     delivery_high_cap=round(float(np.nanmean(prop7[mm & cap_hi] >= 0.5)), 3),
                     delivery_low_cap=round(float(np.nanmean(prop7[mm & cap_lo] >= 0.5)), 3)))
    # H2 ABSORPTION: high capacity + high forcing -> pressure absorbed without delivery
    f_hi = fc_arr >= np.nanquantile(fc_arr, 0.67)
    rows.append(dict(hypothesis="H2_ABSORPTION",
                     prop_high_cap_high_forcing=round(float(np.nanmean(prop7[mm & cap_hi & f_hi] >= 0.5)), 3),
                     prop_low_cap_high_forcing=round(float(np.nanmean(prop7[mm & cap_lo & f_hi] >= 0.5)), 3),
                     sat_without_delivery_high_cap=round(float(np.nanmean((field_act[cap_hi] >= np.nanquantile(field_act, 0.8)) & (prop7[cap_hi] <= np.nanquantile(prop7, 0.33)))), 3),
                     sat_without_delivery_low_cap=round(float(np.nanmean((field_act[cap_lo] >= np.nanquantile(field_act, 0.8)) & (prop7[cap_lo] <= np.nanquantile(prop7, 0.33)))), 3)))
    # H3 STATE_DEPENDENT: capacity vs delivery corr within states
    st_rhos = []
    for st in np.unique(g6):
        m = (g6 == st) & np.isfinite(cap_arr) & np.isfinite(prop7)
        if m.sum() < 60:
            continue
        st_rhos.append(_rhoXY(cap_arr[m], prop7[m]))
    rows.append(dict(hypothesis="H3_STATE_DEPENDENT",
                     median_state_rho=round(float(np.nanmedian(st_rhos)), 3) if st_rhos else np.nan,
                     n_states=int(len(st_rhos)),
                     positive_states=int(np.sum(np.array(st_rhos) > 0.05)),
                     negative_states=int(np.sum(np.array(st_rhos) < -0.05))))
    # conditional on threshold/transfer/gain/ceiling
    cond = {"threshold_hi": thr_pos >= np.nanquantile(thr_pos, 0.67),
            "threshold_lo": thr_pos <= np.nanquantile(thr_pos, 0.33),
            "transfer_hi": te_arr >= np.nanquantile(te_arr, 0.67),
            "transfer_lo": te_arr <= np.nanquantile(te_arr, 0.33),
            "gain_hi": GAIN_F >= np.nanquantile(GAIN_F, 0.67),
            "gain_lo": GAIN_F <= np.nanquantile(GAIN_F, 0.33),
            "ceiling_hi": CEIL_F >= np.nanquantile(CEIL_F, 0.67),
            "ceiling_lo": CEIL_F <= np.nanquantile(CEIL_F, 0.33)}
    for name, cm in cond.items():
        m = cm & np.isfinite(cap_arr) & np.isfinite(prop7)
        if m.sum() < 60:
            continue
        rows.append(dict(hypothesis="H3_CONDITIONAL", condition=name,
                         rho_cap_prop=round(_rhoXY(cap_arr[m], prop7[m]), 3), n=int(m.sum())))
    out = pd.DataFrame(rows)
    W("11_CAPACITY_INTERPRETATION.csv")(out.round(3))


# ================================================================ 12 capacity response law
def capacity_response_law():
    rows = []
    load_lo = fc_arr <= np.nanquantile(fc_arr, 0.33)
    load_mid = (fc_arr > np.nanquantile(fc_arr, 0.33)) & (fc_arr < np.nanquantile(fc_arr, 0.67))
    load_hi = fc_arr >= np.nanquantile(fc_arr, 0.67)
    cap_bins = np.nanquantile(cap_arr, np.linspace(0, 1, 5))
    for load_name, load_mk in (("LOW_LOAD", load_lo), ("MID_LOAD", load_mid), ("HIGH_LOAD", load_hi)):
        for k in range(4):
            cb = (cap_arr >= cap_bins[k]) & (cap_arr < cap_bins[k + 1]) & load_mk & np.isfinite(prop7)
            if cb.sum() < 30:
                continue
            rows.append(dict(load_band=load_name, capacity_band=f"Q{k+1}",
                             cap_mid=round(float(np.nanmedian(cap_arr[cb])), 3),
                             n=int(cb.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[cb] >= 0.5)), 3),
                             propagation=round(float(np.nanmean(prop7[cb])), 3)))
    out = pd.DataFrame(rows)
    # nonlinearity: within HIGH_LOAD does delivery rise then fall with capacity?
    try:
        hi = out[out["load_band"] == "HIGH_LOAD"].sort_values("capacity_band")
        d = hi["delivery_rate"].to_numpy()
        mono_up = bool(np.all(np.diff(d) >= -0.02))
        mono_dn = bool(np.all(np.diff(d) <= 0.02))
        if mono_up:
            verd = "ENABLING_CAPACITY"
        elif mono_dn:
            verd = "ABSORPTIVE_CAPACITY"
        elif len(d) >= 3 and d[0] < d[1] > d[2]:
            verd = "DUAL_ROLE_CAPACITY(enable_then_absorb)"
        else:
            verd = "STATE_LOCAL_CAPACITY"
    except Exception:
        verd = "STATE_LOCAL_CAPACITY"
    out["verdict"] = verd
    W("12_CAPACITY_RESPONSE_LAW.csv")(out.round(3))


# ================================================================ 14 threshold x transfer 2x2
def threshold_transfer_2x2():
    thr_hi = thr_pos >= np.nanquantile(thr_pos, 0.67); thr_lo = thr_pos <= np.nanquantile(thr_pos, 0.33)
    te_hi = te_arr >= np.nanquantile(te_arr, 0.67); te_lo = te_arr <= np.nanquantile(te_arr, 0.33)
    cells = {"THR_LO_TE_LO": thr_lo & te_lo, "THR_HI_TE_LO": thr_hi & te_lo,
             "THR_LO_TE_HI": thr_lo & te_hi, "THR_HI_TE_HI": thr_hi & te_hi}
    rows = []
    for name, mk in cells.items():
        m = mk & np.isfinite(prop7)
        if m.sum() < 40:
            continue
        rows.append(dict(cell=name, n=int(m.sum()),
                         delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3),
                         base_lift=round(float(np.nanmean(prop7[m] >= 0.5) - np.nanmean(prop7 >= 0.5)), 3)))
    # by 6-cell state
    for st in np.unique(g6):
        mst = g6 == st
        if mst.sum() < 60:
            continue
        for name, mk in cells.items():
            m = mst & mk & np.isfinite(prop7)
            if m.sum() < 10:
                continue
            rows.append(dict(cell=f"{name}_6C_{st}", n=int(m.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3)))
    # by 8-cell state
    for st in np.unique(g8):
        mst = g8 == st
        if mst.sum() < 60:
            continue
        for name, mk in cells.items():
            m = mst & mk & np.isfinite(prop7)
            if m.sum() < 10:
                continue
            rows.append(dict(cell=f"{name}_8C_{st}", n=int(m.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3)))
    # by rank depth: per-patch activation under each cell
    for p in DEPTH_ORDER:
        for name, mk in cells.items():
            m = mk & np.isfinite(prop7)
            if m.sum() < 20:
                continue
            rows.append(dict(cell=f"{name}_patch_{p}", n=int(m.sum()),
                             patch_activation=round(float(np.nanmean(act[p].to_numpy()[m])), 3)))
    # by gain band
    g_hi = GAIN_F >= np.nanquantile(GAIN_F, 0.67); g_lo = GAIN_F <= np.nanquantile(GAIN_F, 0.33)
    for g_name, gm in (("GAIN_LO", g_lo), ("GAIN_HI", g_hi)):
        for name, mk in cells.items():
            m = gm & mk & np.isfinite(prop7)
            if m.sum() < 20:
                continue
            rows.append(dict(cell=f"{name}_{g_name}", n=int(m.sum()),
                             delivery_rate=round(float(np.nanmean(prop7[m] >= 0.5)), 3)))
    out = pd.DataFrame(rows)
    W("14_THRESHOLD_TRANSFER_2X2.csv")(out.round(3))


# ================================================================ 15 complementarity / substitution test
def threshold_transfer_interaction():
    rows = []
    y = (prop7 >= 0.5).astype(float)
    tb = _bin(thr_pos); ub = _bin(te_arr)
    m = np.isfinite(thr_pos) & np.isfinite(te_arr) & np.isfinite(prop7)
    # information decomposition on binned variables
    mi_t, n1 = discrete_mi(tb[m], y[m])
    mi_u, n2 = discrete_mi(ub[m], y[m])
    # joint MI via 2D binning (threshold x transfer x y)
    xy = tb[m].astype(float) * 10 + ub[m].astype(float)
    mi_tu, n3 = discrete_mi(xy, y[m])
    rows.append(dict(probe="MI_threshold_delivery", value=round(mi_t, 4) if mi_t == mi_t else np.nan))
    rows.append(dict(probe="MI_transfer_delivery", value=round(mi_u, 4) if mi_u == mi_u else np.nan))
    rows.append(dict(probe="MI_threshold_transfer_delivery", value=round(mi_tu, 4) if mi_tu == mi_tu else np.nan))
    sum_ = (mi_t + mi_u) if (mi_t == mi_t and mi_u == mi_u) else np.nan
    rows.append(dict(probe="MI_sum_individual", value=round(sum_, 4) if sum_ == sum_ else np.nan))
    # interaction logistic: y ~ thr + te + thr*te
    X = np.column_stack([thr_pos[m], te_arr[m], thr_pos[m] * te_arr[m]])
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
    try:
        lr = LogisticRegression(max_iter=2000).fit(Xs, y[m])
        c_thr, c_te, c_int = lr.coef_[0]
        rows.append(dict(probe="logit_coef_threshold", value=round(float(c_thr), 4)))
        rows.append(dict(probe="logit_coef_transfer", value=round(float(c_te), 4)))
        rows.append(dict(probe="logit_coef_interaction", value=round(float(c_int), 4)))
        # classify
        base_eff = abs(c_thr) * np.nanstd(thr_pos[m]) + abs(c_te) * np.nanstd(te_arr[m])
        int_eff = abs(c_int) * np.nanstd(thr_pos[m]) * np.nanstd(te_arr[m])
        if int_eff < 0.1 * max(base_eff, 1e-6):
            kind = "INDEPENDENT_OR_ADDITIVE"
        elif np.sign(c_int) == np.sign(c_thr) == np.sign(c_te):
            kind = "COMPLEMENTS(SYNERGISTIC)"
        elif np.sign(c_int) != np.sign(c_thr) and np.sign(c_int) != np.sign(c_te):
            kind = "SUBSTITUTES"
        else:
            kind = "CONDITIONAL_MIXTURE"
        rows.append(dict(probe="classification", value=kind))
    except Exception:
        rows.append(dict(probe="classification", value="DATA_LIMITED"))
    # conditional complementarity probe: does threshold matter MORE when transfer low?
    te_lo = te_arr <= np.nanquantile(te_arr, 0.33); te_hi = te_arr >= np.nanquantile(te_arr, 0.67)
    thr_hi = thr_pos >= np.nanquantile(thr_pos, 0.67); thr_lo = thr_pos <= np.nanquantile(thr_pos, 0.33)
    mm = np.isfinite(prop7)
    d_te_lo = float(np.nanmean(prop7[mm & te_lo & thr_hi] >= 0.5)) - float(np.nanmean(prop7[mm & te_lo & thr_lo] >= 0.5))
    d_te_hi = float(np.nanmean(prop7[mm & te_hi & thr_hi] >= 0.5)) - float(np.nanmean(prop7[mm & te_hi & thr_lo] >= 0.5))
    rows.append(dict(probe="threshold_lift_when_transfer_low", value=round(d_te_lo, 3)))
    rows.append(dict(probe="threshold_lift_when_transfer_high", value=round(d_te_hi, 3)))
    out = pd.DataFrame(rows)
    W("15_THRESHOLD_TRANSFER_INTERACTION.csv")(out.round(4))


# ================================================================ 16 realization core
def realization_core():
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    y = (prop7 >= 0.5).astype(float)
    coords = {"THRESHOLD": thr_pos, "TRANSFER": te_arr, "GAIN": GAIN_F, "CAPACITY": cap_arr}
    m0 = np.isfinite(prop7)
    rows = []
    for k in (1, 2, 3, 4):
        import itertools
        best_combo, best_auc = None, -1.0
        for combo in itertools.combinations(coords.keys(), k):
            X = np.column_stack([coords[c] for c in combo])
            m = m0 & np.all(np.isfinite(X), 1) & np.isfinite(GAIN_F)
            if m.sum() < 400:
                continue
            Xm = X[m]; ym = y[m]
            Xs = (Xm - Xm.mean(0)) / (Xm.std(0) + 1e-9)
            try:
                tr, te = train_test_split(np.arange(len(ym)), test_size=0.3, random_state=0, stratify=ym)
                lr = LogisticRegression(max_iter=2000).fit(Xs[tr], ym[tr])
                auc = float(roc_auc_score(ym[te], lr.predict_proba(Xs[te])[:, 1]))
            except Exception:
                auc = np.nan
            if auc == auc and auc > best_auc:
                best_auc, best_combo = auc, combo
        if best_combo is not None:
            rows.append(dict(n_coords=k, best_combo="+".join(best_combo),
                             heldout_auc=round(float(best_auc), 3)))
    # individual coordinate AUCs
    for c in coords:
        X = np.column_stack([coords[c]])
        m = m0 & np.all(np.isfinite(X), 1)
        if m.sum() < 400:
            continue
        Xm = X[m]; ym = y[m]
        Xs = (Xm - Xm.mean(0)) / (Xm.std(0) + 1e-9)
        try:
            tr, te = train_test_split(np.arange(len(ym)), test_size=0.3, random_state=0, stratify=ym)
            lr = LogisticRegression(max_iter=2000).fit(Xs[tr], ym[tr])
            auc = float(roc_auc_score(ym[te], lr.predict_proba(Xs[te])[:, 1]))
            rows.append(dict(n_coords=1, best_combo=c, heldout_auc=round(auc, 3), single=True))
        except Exception:
            pass
    out = pd.DataFrame(rows)
    if len(out):
        core = out[(out["n_coords"] == 2)].sort_values("heldout_auc", ascending=False)
        if len(core):
            out["verdict"] = f"CORE_2={core.iloc[0]['best_combo']}"
        else:
            out["verdict"] = "NO_CLEAN_CORE"
    else:
        out = pd.DataFrame([dict(verdict="DATA_LIMITED")])
    W("16_REALIZATION_CORE.csv")(out.round(3))
