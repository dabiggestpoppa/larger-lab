# ================================================================ shared rolling nodes
NODES_ROLL = _rolling_node_series()          # daily asof-filled response nodes
NODE_D_T = np.arange(ns)
# per-response slope/ceiling/onset arrays
NODE_ARR = {}
for p in RESP_NAMES:
    NODE_ARR[f"slope_{p}"] = NODES_ROLL[f"{p}_k"].to_numpy()
    NODE_ARR[f"ceiling_{p}"] = NODES_ROLL[f"{p}_ceiling"].to_numpy()
    NODE_ARR[f"onset_{p}"] = NODES_ROLL[f"{p}_x0"].to_numpy()
# compact: FIELD + patch means
PATCHM = {k: np.nanmean([NODE_ARR[f"{k}_{p}"] for p in DEPTH_ORDER], axis=0) for k in ("slope", "ceiling", "onset")}
NODE_PATCH_MEAN = {f"{k}_patch_mean": PATCHM[k] for k in ("slope", "ceiling", "onset")}

# ================================================================ 07 forcing primitives deep
def forcing_primitives_deep():
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        cons_ = CONSTIT.get(fam, [])
        cvals = []
        for c in cons_:
            if c in dfc.columns:
                cvals.append(pd.to_numeric(dfc[c], errors="coerce").to_numpy())
        red = np.nanmean([abs(_rho(f, cv)) for cv in cvals]) if cvals else np.nan
        amp = float(np.nanstd(f)); slope = float(np.nanmean(np.abs(np.diff(f))))
        fv = f[~np.isnan(f)]
        pers = float(np.corrcoef(fv[:-1], fv[1:])[0, 1]) if len(fv) > 30 else np.nan
        burst = float(np.nanquantile(f, 0.9) / max(abs(np.nanquantile(f, 0.5)), 1e-9)) if np.isfinite(np.nanquantile(f, 0.5)) else np.nan
        # state dependence: std of family mean across 6-cell states
        sm = [np.nanmean(f[g6 == s]) for s in np.unique(g6)]
        state_dep = float(np.nanstd(sm)) if len(sm) >= 3 else np.nan
        # rank dependence: corr with each patch activation
        rank_int = np.nanmean([abs(_rho(f, act[p].to_numpy())) for p in DEPTH_ORDER])
        # route dependence: abs corr with forward-7d route pressure to dominant exits
        # saturation-node dependence
        node_int = np.nanmean([abs(_rho(f, NODE_ARR[f"slope_{p}"])) for p in ["FIELD"]] + [abs(_rho(f, k)) for k in ("slope_patch_mean", "ceiling_patch_mean")] if False else [abs(_rho(f, NODE_PATCH_MEAN["slope_patch_mean"])), abs(_rho(f, NODE_PATCH_MEAN["ceiling_patch_mean"]))])
        thr_int = abs(_rho(f, thr_pos))
        exit_int = np.nanmean([abs(_rho(f, p16)), abs(_rho(f, ent6))])
        cross = np.nanmean([abs(_rho(f, np.asarray(fams[o], dtype=float))) for o in fam_cols if o != fam])
        rows.append(dict(family=fam, constituents="|".join(cons_),
                         amplitude_std=round(amp, 4), slope_mean_abs_diff=round(slope, 4),
                         persistence_autocorr=round(pers, 3) if pers == pers else np.nan,
                         burstiness_p90p50=round(burst, 3) if burst == burst else np.nan,
                         state_dependence_std=round(state_dep, 4) if state_dep == state_dep else np.nan,
                         rank_patch_assoc=round(rank_int, 3),
                         saturation_node_assoc=round(node_int, 3),
                         threshold_assoc=round(thr_int, 3),
                         exit_pressure_assoc=round(exit_int, 3),
                         within_family_redundancy=round(red, 3) if red == red else np.nan,
                         cross_family_corr=round(cross, 3)))
    return pd.DataFrame(rows)

W07 = W("07_FORCING_PRIMITIVES_DEEP.csv", index=False)
W07(forcing_primitives_deep().round(3))

# ================================================================ 08 forcing signatures
def forcing_signatures():
    rsf = pd.read_csv(RETRO / "10_ROUTE_SPECIFIC_FORCING.csv")
    rows = []
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        # where it acts: top states by family mean
        sm = pd.Series({s: np.nanmean(f[g6 == s]) for s in np.unique(g6)}).sort_values(ascending=False)
        top_states = "|".join(str(x) for x in sm.head(2).index)
        low_states = "|".join(str(x) for x in sm.tail(2).index)
        # routes loaded/suppressed from M18 route-specific forcing
        fsub = rsf[rsf["forcing_family"] == fam].dropna(subset=["rho"])
        if len(fsub):
            fsub = fsub.reindex(fsub["rho"].abs().sort_values(ascending=False).index)
            loaded = fsub.iloc[0] if len(fsub) else None
            supp = fsub[fsub["rho"] < 0]
            supp = supp.reindex(supp["rho"].abs().sort_values(ascending=False).index)
            suppressed = supp.iloc[0] if len(supp) else None
            loaded_edge = f"{loaded['edge']}({loaded['rho']:+.2f})" if loaded is not None else None
            suppressed_edge = f"{suppressed['edge']}({suppressed['rho']:+.2f})" if suppressed is not None else None
        else:
            loaded_edge = suppressed_edge = None
        # rank depths responding
        resp_rank = [p for p in DEPTH_ORDER if abs(_rho(f, act[p].to_numpy())) > 0.1]
        # nodes moved
        node_c = {}
        for k in ("slope", "ceiling", "onset"):
            node_c[k] = abs(_rho(f, NODE_PATCH_MEAN[f"{k}_patch_mean"]))
        nodes_moved = "|".join([k for k, v in node_c.items() if v > 0.1])
        # persistence: lag-1 autocorr half-life as descriptor
        fv = f[~np.isnan(f)]
        pers = float(np.corrcoef(fv[:-1], fv[1:])[0, 1]) if len(fv) > 30 else np.nan
        # regime alteration: std of family mean across subperiods
        reg_std = float(np.nanstd([np.nanmean(f[subp_arr == sp]) for sp in SUBPERIODS]))
        rows.append(dict(family=fam,
                         top_states_2=top_states, low_states_2=low_states,
                         top_loaded_route=loaded_edge, top_suppressed_route=suppressed_edge,
                         rank_depths_responding="|".join(resp_rank),
                         nodes_moved=nodes_moved,
                         persistence_autocorr=round(pers, 3) if pers == pers else np.nan,
                         regime_alteration_std=round(reg_std, 4) if reg_std == reg_std else np.nan,
                         signature= "|".join([str(x) for x in [top_states[:12], loaded_edge or "n/a"]])))
    return pd.DataFrame(rows)

W08 = W("08_FORCING_SIGNATURES.csv", index=False)
W08(forcing_signatures().round(3))

# ================================================================ 09 forcing co-occurrence
def forcing_cooccurrence():
    qhi = np.nanquantile(np.asarray(fams[d], float), 0.7) if False else None
    hi = {}
    for fam in fam_cols:
        f = np.asarray(fams[fam], dtype=float)
        hi[fam] = f >= (np.nanquantile(f, 0.7) if np.isfinite(np.nanquantile(f, 0.7)) else 1e9)
    rows = []
    for i, a in enumerate(fam_cols):
        for b in fam_cols[i + 1:]:
            both = hi[a] & hi[b]
            n = int(both.sum())
            if n < 30:
                continue
            rows.append(dict(family_a=a, family_b=b, n_cooccur_high=int(both.sum()),
                             frac_cooccur=round(float(both.mean()), 3),
                             mean_sat_under_comb=round(float(np.nanmean(field_act[both])), 3),
                             mean_p1_under_comb=round(float(np.nanmean(p16[both])), 3),
                             mean_recruit_under_comb=round(float(np.nanmean(rank7[both])), 3),
                             mean_prop_under_comb=round(float(np.nanmean(prop7[both])), 3),
                             thr_pos_mean=round(float(np.nanmean(thr_pos[both])), 3)))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("09_FORCING_COOCCURRENCE.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    return out

W09 = W("09_FORCING_COOCCURRENCE.csv", index=False)
W09(forcing_cooccurrence().round(3))

# ================================================================ 10 forcing interactions
def forcing_interactions():
    # classify pair interaction on FIELD activation via linear model w/ interaction term
    y = field_act
    rows = []
    for i, a in enumerate(fam_cols):
        fa = np.asarray(fams[a], dtype=float)
        for b in fam_cols[i + 1:]:
            fb = np.asarray(fams[b], dtype=float)
            m = np.isfinite(fa) & np.isfinite(fb) & np.isfinite(y)
            if m.sum() < 150:
                continue
            X = np.column_stack([fa[m], fb[m], fa[m] * fb[m]])
            lr = LinearRegression().fit(X, y[m])
            c_a, c_b, c_ab = lr.coef_[0], lr.coef_[1], lr.coef_[2]
            base = c_a * np.nanstd(fa) ; baseb = c_b * np.nanstd(fb)
            intg = c_ab * (np.nanstd(fa) * np.nanstd(fb))
            # classify
            if abs(intg) < 0.1 * max(abs(base), abs(baseb), 1e-6):
                kind = "ADDITIVE_LIKE"
            elif np.sign(c_ab) == np.sign(c_a) == np.sign(c_b):
                kind = "SYNERGISTIC_LIKE"
            elif np.sign(c_ab) != np.sign(c_a) and np.sign(c_ab) != np.sign(c_b):
                kind = "ANTAGONISTIC_LIKE"
            elif abs(c_a * c_b) > abs(c_ab):
                kind = "ADDITIVE_LIKE"
            else:
                kind = "ROUTE_SPECIFIC"
            rows.append(dict(family_a=a, family_b=b, n=int(m.sum()),
                             coef_a=round(c_a, 4), coef_b=round(c_b, 4),
                             coef_interaction=round(c_ab, 4),
                             interaction_abs_std_units=round(float(abs(intg)), 4),
                             classification=kind))
    out = pd.DataFrame(rows)
    if len(out) == 0:
        W("10_FORCING_INTERACTIONS.csv")(pd.DataFrame([dict(verdict="DATA_LIMITED")]))
        return
    return out

W10 = W("10_FORCING_INTERACTIONS.csv", index=False)
W10(forcing_interactions().round(4))

# ================================================================ 11 forcing route map
def forcing_route_map():
    rsf = pd.read_csv(RETRO / "10_ROUTE_SPECIFIC_FORCING.csv")
    et = pd.read_csv(RETRO / "02_EDGE_REGISTRY.csv")
    et6 = et[et["resolution"] == "6CELL"]
    dr = pd.read_csv(RETRO / "04_EXIT_AVAILABILITY_PRESSURE.csv")
    dr6 = dr[dr["resolution"] == "6CELL"].set_index("state")["resolution_driver"].to_dict()
    rows = []
    for _, r in rsf.iterrows():
        if pd.isna(r["rho"]):
            continue
        s, t = r["edge"].split("->")
        rows.append(dict(forcing_family=r["forcing_family"],
                         state=s, edge=r["edge"],
                         pressure_change=round(r["rho"], 3),
                         pressure_sign="+LOAD" if r["rho"] > 0.15 else ("-SUPPRESS" if r["rho"] < -0.15 else "NEUTRAL"),
                         resolution_mechanism=dr6.get(s, "DATA_LIMITED")))
    out = pd.DataFrame(rows)
    # top loading per family/state
    return out

W11 = W("11_FORCING_ROUTE_MAP.csv", index=False)
W11(forcing_route_map().round(3))