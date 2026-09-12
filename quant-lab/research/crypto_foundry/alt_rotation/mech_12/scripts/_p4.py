from _p1 import *
from _p1 import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _perm_p, _atom_series
# =========================================================================
# WS7: WATERFALL AS THRESHOLD HIERARCHY (09_WATERFALL_THRESHOLD_HIERARCHY.csv)
# =========================================================================

def _band_field_intensity(dfw):
    """Field intensity coordinates indexed by date."""
    d = dfw.copy()
    d = d.rename(columns={"d": "date"})
    cols = ["date", "top500_breadth_30d", "top500_dispersion_30d",
            "vol_med", "btc_return_7d", "stablecoin_change_7d",
            "chain_tvl_med_chg7", "top3_share", "top3_share_chg7",
            "pos_ret_share", "cell", "state"]
    return d[cols]


def ws7_waterfall_thresholds(dfw, band):
    fi = _band_field_intensity(dfw)
    b = band.copy()
    b["date"] = b["d"]
    # activation: ppos crossing above 0.55 = first day of an episode
    act_rows = []
    for band_name, g in b.groupby("band", observed=True):
        g = g.sort_values("date").reset_index(drop=True)
        prev = g["ppos"].shift(1)
        first_act = (g["ppos"] >= 0.55) & (prev < 0.55)
        ep = g[first_act]
        if len(ep) == 0:
            continue
        m = ep.merge(fi, on="date", how="left")
        m = m.dropna(subset=["top500_breadth_30d"])
        if len(m) == 0:
            continue
        act_rows.append({
            "band": band_name,
            "n_episodes": int(len(m)),
            "med_breadth": float(m["top500_breadth_30d"].median()),
            "med_dispersion": float(m["top500_dispersion_30d"].median()),
            "med_vol": float(m["vol_med"].median()),
            "med_btc7": float(m["btc_return_7d"].median()),
            "med_stablecoin_chg7": float(m["stablecoin_change_7d"].median()),
            "med_tvl_chg7": float(m["chain_tvl_med_chg7"].median()),
            "med_top3_share": float(m["top3_share"].median()),
            "med_pos_ret_share": float(m["pos_ret_share"].median()),
        })
    out = pd.DataFrame(act_rows)
    # rank correlation between band depth and field intensity
    depth_map = {bn: i for i, bn in enumerate(BANDS_COARSE)}
    def _depth(bn):
        for k in depth_map:
            if bn == k or (bn in FINE_TO_COARSE and FINE_TO_COARSE[bn] == k):
                return depth_map[k]
        return np.nan
    if len(out):
        out["depth_idx"] = out["band"].apply(_depth)
        out = out.dropna(subset=["depth_idx"]).sort_values("depth_idx")
        for c in ["med_breadth", "med_dispersion", "med_vol", "med_btc7",
                  "med_stablecoin_chg7", "med_tvl_chg7", "med_top3_share"]:
            rho, p = spearmanr(out["depth_idx"], out[c])
            out[f"rho_{c}"] = rho
            out[f"p_{c}"] = p
        # verdict: deeper bands require stronger field if rho>0 on breadth/
        # dispersion/vol/btc with p<0.1
        sig_pos = sum(1 for c in ["med_breadth", "med_dispersion", "med_vol",
                                  "med_btc7"]
                      if out[f"rho_{c}"].iloc[0] > 0.3 and
                      out[f"p_{c}"].iloc[0] < 0.10)
        sig_neg = sum(1 for c in ["med_breadth", "med_dispersion", "med_vol",
                                  "med_btc7"]
                      if out[f"rho_{c}"].iloc[0] < -0.3 and
                      out[f"p_{c}"].iloc[0] < 0.10)
        if sig_pos >= 2:
            verdict = "THRESHOLD_HIERARCHY_EARNED"
        elif sig_neg >= 2:
            verdict = "INVERSE_HIERARCHY"
        else:
            verdict = "FLAT_THRESHOLDS"
        out["verdict"] = verdict
    else:
        out["verdict"] = "DATA_BLOCKED"
    out.to_csv(OUT / "09_WATERFALL_THRESHOLD_HIERARCHY.csv", index=False)
    return out


# =========================================================================
# WS8: RANK-PATCH GRAPH (10_RANK_PATCH_GRAPH_NODES.csv,
#       11_RANK_PATCH_GRAPH_EDGES.csv)
# =========================================================================

def _patch_series(band):
    """Daily med_ret / ppos series per patch."""
    b = band.copy()
    b["patch"] = b["band"].map(
        {fb: p for p, fbs in PATCHES.items() for fb in fbs})
    b = b.dropna(subset=["patch"])
    g = b.groupby(["d", "patch"]).agg(
        med_ret=("med_ret", "mean"),
        ppos=("ppos", "mean"),
        ptail=("ptail", "mean"),
        n=("n", "sum")).reset_index()
    return g


def ws8_patch_graph(band, loners, lf6_consensus):
    g = _patch_series(band)
    # loner densities by coarse band -> patch
    lc = loners.merge(lf6_consensus[["event_index", "loner3"]],
                      on="event_index", how="left")
    lc["patch"] = lc["rank_band"].map(
        {cb: p for p, cbs in PATCH_LONER_BANDS.items() for cb in cbs})
    lc = lc.dropna(subset=["patch"])
    node_rows = []
    piv = g.pivot(index="d", columns="patch", values="med_ret")
    for patch, fbs in PATCHES.items():
        sub = band[band["band"].isin(fbs)]
        # internal coherence = mean pairwise corr of fine-band med_ret
        pv = sub.pivot(index="d", columns="band", values="med_ret")
        corr = pv.corr()
        np.fill_diagonal(corr.values, np.nan)
        coherence = float(corr.stack().mean()) if corr.shape[0] > 1 else np.nan
        tail_share = float(sub["ptail"].mean())
        med_abs = float(sub["med_ret"].abs().mean())
        disp = float(sub["med_ret"].std())
        lp = lc[lc["patch"] == patch]
        false_rate = float((lp["loner3"] == "FALSE_LONER").mean()) \
            if len(lp) else np.nan
        true_rate = float((lp["loner3"] == "TRUE_LONER").mean()) \
            if len(lp) else np.nan
        node_rows.append({
            "patch": patch, "bands": ";".join(fbs),
            "n_days": int(sub["d"].nunique()),
            "internal_coherence": coherence,
            "false_loner_rate": false_rate,
            "true_loner_rate": true_rate,
            "tail_share": tail_share,
            "median_abs_ret": med_abs,
            "med_ret_dispersion": disp,
            "mean_ppos": float(sub["ppos"].mean())})
    nodes = pd.DataFrame(node_rows)
    nodes.to_csv(OUT / "10_RANK_PATCH_GRAPH_NODES.csv", index=False)

    # edges
    patches = list(PATCHES.keys())
    edge_rows = []
    for a in range(len(patches)):
        for b in range(a + 1, len(patches)):
            pa, pb = patches[a], patches[b]
            x = g[g["patch"] == pa].set_index("d")["med_ret"]
            y = g[g["patch"] == pb].set_index("d")["med_ret"]
            j = pd.concat([x, y], axis=1, join="inner").dropna()
            if len(j) < 60:
                continue
            same, _ = spearmanr(j.iloc[:, 0], j.iloc[:, 1])
            lag1, _ = spearmanr(j.iloc[:-1, 0], j.iloc[1:, 1])
            lag1r, _ = spearmanr(j.iloc[:-1, 1], j.iloc[1:, 0])
            edge_rows.append({
                "patch_a": pa, "patch_b": pb, "n_days": int(len(j)),
                "same_day_spearman": float(same),
                "lag1_a_leads_b": float(lag1),
                "lag1_b_leads_a": float(lag1r)})
    edges = pd.DataFrame(edge_rows)
    edges.to_csv(OUT / "11_RANK_PATCH_GRAPH_EDGES.csv", index=False)
    return nodes, edges


# =========================================================================
# WS9: LOCAL PATCH RESPONSE TO PERTURBATION (12_PATCH_PERTURBATION_RESPONSE.csv)
# =========================================================================

def ws9_patch_perturbation(dfw, band):
    d = dfw.copy()
    pert = _perturbation_flags(d)
    # amplitude: standardized change size for each perturbation
    for name, col in [("brd_jump", "top500_breadth_30d"),
                      ("brd_drop", "top500_breadth_30d"),
                      ("disp_jump", "top500_dispersion_30d"),
                      ("disp_drop", "top500_dispersion_30d"),
                      ("btc_shock", "btc_return_7d"),
                      ("conc_shock", "top3_share_chg7"),
                      ("vol_shock", "vol_med")]:
        chg = d[col].diff(5)
        z = chg / chg.std() if chg.std() else chg
        sign = 1 if "jump" in name or "shock" in name else -1
        # for drop-type, magnitude of (negative) change
        mag = z.abs()
        pert[f"amp_{name}"] = mag.where(pert[name] == 1, np.nan)
    g = _patch_series(band)
    rows = []
    for patch in PATCHES:
        pg = g[g["patch"] == patch].set_index("d")
        for pname in ["brd_jump", "brd_drop", "disp_jump", "disp_drop",
                      "btc_shock", "conc_shock", "vol_shock"]:
            idx = d[pd.notna(pert[f"amp_{pname}"]) &
                    (pert[pname] == 1)].index
            if len(idx) < 20:
                continue
            amp = pert.loc[idx, f"amp_{pname}"].to_numpy()
            amp = np.asarray(amp, dtype=float)
            good = ~np.isnan(amp)
            idx_g = idx[good]
            amp_g = amp[good]
            if len(idx_g) < 20:
                continue
            q1, q2 = np.nanpercentile(amp_g, [33, 66])
            for label, lo, hi in [("SMALL", -np.inf, q1),
                                  ("MEDIUM", q1, q2), ("LARGE", q2, np.inf)]:
                m = (amp_g >= lo) & (amp_g < hi)
                sel = idx_g[m]
                if len(sel) < 10:
                    continue
                dates = pd.to_datetime(d.loc[sel, "d"]).dt.normalize()
                resp = pg.loc[pg.index.isin(dates)]
                if len(resp) < 5:
                    continue
                # activation prob within 3D: ppos >= 0.55 any day
                fwd_ppos = []
                for dt in dates:
                    pos = pg.index.get_indexer([dt], method="nearest")
                    if pos[0] < 0 or pos[0] >= len(pg) - 3:
                        continue
                    window = pg["ppos"].iloc[pos[0]:pos[0] + 4]
                    fwd_ppos.append((window >= 0.55).any())
                act_rate = float(np.mean(fwd_ppos)) if fwd_ppos else np.nan
                tail_after = float(resp["ptail"].mean()) if len(resp) else \
                    np.nan
                rows.append({"patch": patch, "perturbation": pname,
                             "amplitude": label, "n_events": int(len(sel)),
                             "activation_prob_3d": act_rate,
                             "tail_share_after": tail_after,
                             "med_ret_after": float(resp["med_ret"].mean())
                             if len(resp) else np.nan})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "12_PATCH_PERTURBATION_RESPONSE.csv", index=False)
    return out
