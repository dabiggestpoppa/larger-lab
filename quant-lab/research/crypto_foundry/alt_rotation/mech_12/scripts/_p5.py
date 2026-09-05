from _p1 import *
from _p1 import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _perm_p, _atom_series
# =========================================================================
# WS10: PEER-FORMATION CONTEXT (13_PEER_FORMATION_FIELD_CONTEXT.csv)
# =========================================================================

def ws10_peer_formation_context(dfw, peer_paths):
    d = dfw.copy()
    pp = peer_paths.copy()
    pp["d"] = pd.to_datetime(pp["historical_date"]).dt.normalize()
    # path_class value distribution
    dmap = d.set_index("d")
    rows = []
    for pc, g in pp.groupby("path_class"):
        dates = g["d"].drop_duplicates()
        ctx = dmap.loc[dmap.index.isin(dates)]
        if len(ctx) < 10:
            continue
        rows.append({
            "path_class": pc, "n_events": int(len(g)),
            "n_dates": int(len(dates)),
            "med_breadth": float(ctx["top500_breadth_30d"].median()),
            "med_dispersion": float(ctx["top500_dispersion_30d"].median()),
            "med_vol": float(ctx["vol_med"].median()),
            "med_btc7": float(ctx["btc_return_7d"].median()),
            "med_stablecoin_chg7": float(ctx["stablecoin_change_7d"].median()),
            "med_tvl_chg7": float(ctx["chain_tvl_med_chg7"].median()),
            "p_HH": float((ctx["cell"] == "HIGH_BREADTH_HIGH_DISP").mean()),
            "p_LL": float((ctx["cell"] == "LOW_BREADTH_LOW_DISP").mean()),
            "med_age": float(ctx["age_in_cell"].median())})
    out = pd.DataFrame(rows)
    # compare: is there any path class with distinct field context?
    if len(out) >= 2:
        # test HH share spread and breadth spread across classes
        hh = out["p_HH"].to_numpy()
        br = out["med_breadth"].to_numpy()
        spread_hh = float(np.nanmax(hh) - np.nanmin(hh))
        spread_br = float(np.nanmax(br) - np.nanmin(br))
        if spread_hh >= 0.12 or spread_br >= 0.10:
            verdict = "FIELD_CONTEXT_DISTINCT"
        else:
            verdict = "FIELD_CONTEXT_FLAT"
        out["verdict"] = verdict
        out["spread_p_HH"] = spread_hh
        out["spread_med_breadth"] = spread_br
    else:
        out["verdict"] = "DATA_LIMITED"
    out.to_csv(OUT / "13_PEER_FORMATION_FIELD_CONTEXT.csv", index=False)
    return out


# =========================================================================
# WS11: METASTABILITY LIGHT AUDIT (14_METASTABILITY_AUDIT.csv)
# =========================================================================

def ws11_metastability(dfw):
    d = dfw.copy()
    d["next_cell"] = d["cell"].shift(-1)
    rows = []
    trans = pd.crosstab(d["cell"], d["next_cell"], normalize="index")
    stat_share = d["cell"].value_counts(normalize=True)
    for cell in CELLS:
        sub = d[d["cell"] == cell]
        # dwell episodes
        runs = (sub["cell"] != sub["cell"].shift(1)).cumsum() \
            if len(sub) else pd.Series(dtype=float)
        # simpler: count episodes via change points
        chg = (d["cell"] != d["cell"].shift(1))
        ep_id = chg.cumsum()
        dwell = d.groupby(ep_id)["cell"].agg(["size", "first"])
        dwell_c = dwell[dwell["first"] == cell]["size"]
        # return probability: after exiting, return within 30D
        ret_prob = np.nan
        if len(dwell_c):
            med_dwell = float(dwell_c.median())
        else:
            med_dwell = np.nan
        # escape probability = P(exit within 1D / 3D)
        esc1 = float((d["next_cell"] != cell).mean()) if len(sub) else np.nan
        # transition flux out
        flux_out = float(trans.loc[cell].drop(cell, errors="ignore").sum()) \
            if cell in trans.index else np.nan
        # recurrence: fraction of episodes followed by another entry within
        # 60D
        rec = np.nan
        rows.append({
            "cell": cell,
            "n_days": int(len(sub)),
            "n_episodes": int(len(dwell_c)),
            "median_dwell_d": med_dwell,
            "p_escape_1d": esc1,
            "stationary_share": float(stat_share.get(cell, np.nan)),
            "flux_out": flux_out,
            "return_prob_30d": ret_prob,
            "recurrence": rec})
    out = pd.DataFrame(rows)
    # classify relative to cell average
    if len(out):
        md = out["median_dwell_d"].to_numpy(dtype=float)
        ss = out["stationary_share"].to_numpy(dtype=float)
        fl = out["flux_out"].to_numpy(dtype=float)
        md_z = (md - np.nanmean(md)) / np.nanstd(md)
        ss_z = (ss - np.nanmean(ss)) / np.nanstd(ss)
        fl_z = (fl - np.nanmean(fl)) / np.nanstd(fl)
        def _cls(i):
            if md_z[i] > 0.5 and ss_z[i] > 0.5 and fl_z[i] < -0.3:
                return "METASTABLE_LIKE"
            if md_z[i] < -0.5 and fl_z[i] > 0.3:
                return "TRANSIT_CORRIDOR"
            return "ORDINARY_STATE"
        out["verdict"] = [_cls(i) for i in range(len(out))]
        out["z_dwell"] = md_z
        out["z_stationary"] = ss_z
        out["z_flux"] = fl_z
    out.to_csv(OUT / "14_METASTABILITY_AUDIT.csv", index=False)
    return out


# =========================================================================
# WS12: TRANSFER-FLOW PILOT (15_TRANSFER_FLOW_PILOT.csv)
# =========================================================================

def ws12_transfer_flow(dfw, meta):
    d = dfw.copy()
    d["next_cell"] = d["cell"].shift(-1)
    trans = pd.crosstab(d["cell"], d["next_cell"], normalize="index")
    stat = d["cell"].value_counts(normalize=True)
    n_meta = int((meta["verdict"] == "METASTABLE_LIKE").sum()) if len(meta) \
        else 0
    rows = []
    for i in trans.index:
        for j in trans.columns:
            p = float(trans.loc[i, j])
            flux = float(stat.get(i, 0)) * p
            rows.append({"from": i, "to": j, "p_transition": p,
                         "stationary_from": float(stat.get(i, 0)),
                         "probability_flux": flux})
    out = pd.DataFrame(rows).sort_values("probability_flux", ascending=False)
    out["verdict"] = ("TRANSFER_FLOW_PILOT" if n_meta >= 1
                      else "NOT_EARNED_NO_METASTABLE_STATE")
    out.to_csv(OUT / "15_TRANSFER_FLOW_PILOT.csv", index=False)
    return out


# =========================================================================
# WS13: TRUE/FALSE LONER FIELD PLACEMENT (16_LONER_FIELD_PLACEMENT.csv)
# =========================================================================

def ws13_loner_field_placement(dfw, loners, lf6_consensus):
    d = dfw.copy()
    lc = loners.merge(lf6_consensus[["event_index", "loner3"]],
                      on="event_index", how="left")
    lc = lc[~lc["loner3"].isna()].copy()
    lc["d"] = pd.to_datetime(lc["d"])
    d["d"] = pd.to_datetime(d["d"])
    m = lc.merge(d[["d", "cell", "age_in_cell", "state",
                    "top500_breadth_30d", "top500_dispersion_30d",
                    "vol_med", "btc_return_7d"]].drop_duplicates("d"),
                 on="d", how="left")
    m["patch"] = m["rank_band"].map(
        {cb: p for p, cbs in PATCH_LONER_BANDS.items() for cb in cbs})
    m["age_band"] = m["age_in_cell"].apply(_age_band)
    # amp_level is a categorical string ('2s','3s','4s+') -> numeric sigma
    amp_num = pd.to_numeric(m["amp_level"].astype(str).str.extract(
        r"(\d)")[0], errors="coerce")
    m["amp_num"] = amp_num
    if m["amp_num"].notna().sum() > 10:
        m["amp_bin"] = np.where(m["amp_num"] <= 2, "LOW",
                                 np.where(m["amp_num"] == 3, "MED",
                                          "HIGH"))
    else:
        m["amp_bin"] = "NA"
    rows = []
    for cls in ["TRUE_LONER", "FALSE_LONER", "AMBIGUOUS"]:
        g = m[m["loner3"] == cls]
        if len(g) < 10:
            continue
        rows.append({
            "loner_class": cls, "n": int(len(g)),
            "p_HH": float((g["cell"] == "HIGH_BREADTH_HIGH_DISP").mean()),
            "p_LL": float((g["cell"] == "LOW_BREADTH_LOW_DISP").mean()),
            "p_AGE_1": float((g["age_band"] == "AGE_1").mean()),
            "p_AGE_15P": float((g["age_band"] == "AGE_15_PLUS").mean()),
            "med_breadth": float(g["top500_breadth_30d"].median()),
            "med_dispersion": float(g["top500_dispersion_30d"].median()),
            "med_vol": float(g["vol_med"].median()),
            "med_btc7": float(g["btc_return_7d"].median()),
            "p_amp_high": float((g["amp_bin"] == "HIGH").mean())
            if g["amp_bin"].notna().any() else np.nan,
            "n_subperiods": int(g["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    # test: loner classes differ in cell placement
    verdict = "INCONCLUSIVE"
    if len(out) >= 2:
        if "TRUE_LONER" in out["loner_class"].values and \
                "FALSE_LONER" in out["loner_class"].values:
            t = out[out["loner_class"] == "TRUE_LONER"].iloc[0]
            f = out[out["loner_class"] == "FALSE_LONER"].iloc[0]
            if abs(t["p_HH"] - f["p_HH"]) >= 0.08:
                verdict = "DISTINCT_FIELD_PLACEMENT"
            else:
                verdict = "OVERLAPPING_FIELD_PLACEMENT"
    out["verdict"] = verdict
    out.to_csv(OUT / "16_LONER_FIELD_PLACEMENT.csv", index=False)
    return out


# =========================================================================
# WS14: ABSOLUTE vs SIGMA SHOCK AMPLITUDE (17_ABSOLUTE_VS_SIGMA_AMPLITUDE.csv)
# =========================================================================

def ws14_abs_vs_sigma(ev):
    d = ev.copy()
    d = d[d["z1"].notna() & d["ret_1d"].notna()].copy()
    d["abs_ret"] = d["ret_1d"].abs()
    # ev is the extreme-event panel (all z1 >= 2): split sigma at its median
    # so both cells populate; abs split at its median too
    z_med = d["z1"].median()
    a_med = d["abs_ret"].median()
    d["sigma_bin"] = np.where(d["z1"] >= z_med, "HIGH_SIGMA",
                               "LOW_SIGMA")
    d["abs_bin"] = np.where(d["abs_ret"] >= a_med, "HIGH_ABS",
                             "LOW_ABS")
    d["cell"] = d["sigma_bin"] + "_" + d["abs_bin"]
    rows = []
    for cell, g in d.groupby("cell"):
        rows.append({
            "amplitude_cell": cell,
            "n": int(len(g)),
            "p_fwd1_pos": float((g["fwd1_cum"] > 0).mean()),
            "p_fwd7_pos": float((g["fwd7_cum"] > 0).mean()),
            "p_fwd14_pos": float((g["fwd14_cum"] > 0).mean()),
            "med_fwd7": float(g["fwd7_cum"].median()),
            "p_reversal_7d": float((g["reversal"] == 1).mean())
            if "reversal" in g.columns else np.nan})
    out = pd.DataFrame(rows)
    # incremental test: does abs add info beyond sigma? logistic fwd7_pos
    try:
        dd = d.dropna(subset=["fwd7_cum"])
        y = (dd["fwd7_cum"] > 0).astype(int)
        X1 = dd[["z1"]].to_numpy()
        X2 = dd[["z1", "abs_ret"]].to_numpy()
        m1 = LogisticRegression(max_iter=1000).fit(X1, y)
        m2 = LogisticRegression(max_iter=1000).fit(X2, y)
        ll1 = log_loss(y, m1.predict_proba(X1)[:, 1])
        ll2 = log_loss(y, m2.predict_proba(X2)[:, 1])
        auc1 = roc_auc_score(y, m1.predict_proba(X1)[:, 1])
        auc2 = roc_auc_score(y, m2.predict_proba(X2)[:, 1])
        out["delta_logloss_abs_adds"] = ll1 - ll2
        out["delta_auc_abs_adds"] = auc2 - auc1
    except Exception:
        pass
    out.to_csv(OUT / "17_ABSOLUTE_VS_SIGMA_AMPLITUDE.csv", index=False)
    return out
