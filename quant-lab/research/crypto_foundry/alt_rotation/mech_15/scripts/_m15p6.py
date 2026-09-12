from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, _proportion_and_n, _ztest_prop, MC, cell_stats

PERM_COORDS = ["top500_breadth_30d", "top500_dispersion_30d",
               "btc_return_7d", "eth_btc_relative_return_7d", "vol_med",
               "top3_share"]


# =========================================================================
# WS17: UPSIDE PERMISSION CELLS (18_UPSIDE_PERMISSION_CELLS.csv)
# =========================================================================
def ws17_upside_permission_cells(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            rows.append({"mcell": mc, "n": int(len(g)),
                         "p_broad_up_today": np.nan,
                         "p_broad_up_1d_fwd": np.nan,
                         "n_subperiods": int(g["subperiod"].replace(
                             "UNKNOWN", np.nan).dropna().nunique()),
                         "permission_region": False,
                         "verdict": "DATA_LIMITED"})
            continue
        rows.append({"mcell": mc, "n": int(len(g)),
                     "p_broad_up_today": float(g["fam_broad_up"].mean()),
                     "p_broad_up_1d_fwd": float(
                         (g["fam_broad_up"].shift(-1) == 1).mean()),
                     "n_subperiods": int(g["subperiod"].replace("UNKNOWN",
                         np.nan).dropna().nunique()),
                     "permission_region": False,
                     "verdict": "MAPPED"})
    out = pd.DataFrame(rows)
    usable = out[out["verdict"] != "DATA_LIMITED"]
    spread = float(usable["p_broad_up_1d_fwd"].max() -
                   usable["p_broad_up_1d_fwd"].min()) if len(usable) else 0
    med = float(usable["p_broad_up_1d_fwd"].median()) if len(usable) else 1
    # permission region only if the 1d-fwd broad-up rate genuinely separates
    # cells (the ev_* flags are near-saturated; require a real gap)
    perm = usable[usable["p_broad_up_1d_fwd"] >= med + 0.10] if \
        spread >= 0.15 else usable.iloc[0:0]
    out["permission_region"] = out["mcell"].isin(perm["mcell"])
    if len(perm):
        # coordinate necessity/sufficiency inside permission cells vs rest
        perm_cells = set(perm["mcell"])
        gp = df[df["mcell"].isin(perm_cells)]
        gr = df[~df["mcell"].isin(perm_cells)]
        for c in PERM_COORDS:
            xp = gp[c].to_numpy(dtype=float)
            xr = gr[c].to_numpy(dtype=float)
            medc = float(np.nanmedian(df[c]))
            cov_p = float((xp >= medc).mean()) if len(xp) else np.nan
            cov_r = float((xr >= medc).mean()) if len(xr) else np.nan
            out = pd.concat([out, pd.DataFrame([{
                "mcell": f"coord:{c}", "n": int(len(gp)),
                "p_broad_up_today": np.nan, "p_broad_up_1d_fwd": np.nan,
                "n_subperiods": np.nan, "permission_region": True,
                "verdict": "COORDINATE",
                "coverage_perm_cells": cov_p, "coverage_rest": cov_r,
                "coverage_gap": float(cov_p - cov_r) if cov_p == cov_p
                and cov_r == cov_r else np.nan}])], ignore_index=True)
    else:
        out["coverage_perm_cells"] = np.nan
        out["coverage_rest"] = np.nan
        out["coverage_gap"] = np.nan
    out["verdict"] = "UPSIDE_PERMISSION_REGION" if len(perm) else \
        "NO_PERMISSION_REGION"
    out["rate_spread"] = spread
    out.to_csv(OUT / "18_UPSIDE_PERMISSION_CELLS.csv", index=False)
    return out


# =========================================================================
# WS18: DOWNSIDE LOCALIZATION CELLS (19_DOWNSIDE_LOCALIZATION_CELLS.csv)
# =========================================================================
def ws18_downside_localization_cells(df, ev):
    e = ev.copy()
    e["d"] = pd.to_datetime(e["historical_date"]).dt.normalize()
    e["abs_ret"] = e["ret_1d"].abs()
    e["rev"] = (e["reversal"] == 1).astype(int)
    e["rank_damage"] = e["rank_vel_7d"].abs() if "rank_vel_7d" in e else 0.0
    dmap = df.set_index("d")[["mcell", "age_in_cell", "ent_resid"]]
    e = e.join(dmap, on="d", how="left")
    rows = []
    for mc in MC:
        g = e[e["mcell"] == mc]
        if len(g) < 100:
            rows.append({"mcell": mc, "n_events": int(len(g)),
                         "verdict": "DATA_LIMITED"})
            continue
        rows.append({"mcell": mc, "n_events": int(len(g)),
                     "p_reversal": float(g["rev"].mean()),
                     "median_abs_ret": float(g["abs_ret"].median()),
                     "median_sigma": float(g["z1"].abs().median()),
                     "median_rank_damage_7d": float(g["rank_damage"].median()),
                     "median_age": float(g["age_in_cell"].median()),
                     "median_ent_resid": float(g["ent_resid"].median()),
                     "verdict": "MAPPED"})
    out = pd.DataFrame(rows)
    usable = out[out["verdict"] != "DATA_LIMITED"]
    if len(usable):
        rev_med = float(usable["p_reversal"].median())
        # reversal-structured cells: reversal rate materially above median
        high = usable[usable["p_reversal"] >= rev_med * 1.2]
        if len(high) and len(high) <= len(usable) * 0.5:
            out["local_downside_cell"] = out["mcell"].isin(high["mcell"])
            out["verdict"] = "LOCAL_DOWNSIDE_CELLS_IDENTIFIED"
        else:
            out["local_downside_cell"] = False
            out["verdict"] = "DOWNSIDE_NOT_CELL_STRUCTURED"
    out.to_csv(OUT / "19_DOWNSIDE_LOCALIZATION_CELLS.csv", index=False)
    return out


# =========================================================================
# WS19: TAIL ACTIVATION SURFACE (20_TAIL_ACTIVATION_SURFACE.csv)
# =========================================================================
def ws19_tail_activation_surface(df, band):
    UP_TAIL = ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE",
               "ev_ISOLATED_UPSIDE"]
    DN_TAIL = ["ev_ISOLATED_DOWNSIDE_EXTREME", "ev_LOCAL_CLUSTER_DOWNSIDE",
               "ev_COORDINATED_DOWNSIDE"]
    # band panel tail share per day
    b = band.copy()
    b["d"] = pd.to_datetime(b["d"]).dt.normalize()
    daily_tail = b.groupby("d")["ptail"].mean().rename("ptail_daily")
    df = df.join(daily_tail, on="d", how="left")
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            rows.append({"mcell": mc, "n": int(len(g)),
                         "verdict": "DATA_LIMITED"})
            continue
        rows.append({"mcell": mc, "n": int(len(g)),
                     "upper_tail_rate": float(
                         (g[UP_TAIL].sum(axis=1) > 0).mean()),
                     "lower_tail_rate": float(
                         (g[DN_TAIL].sum(axis=1) > 0).mean()),
                     "tail_share_daily": float(g["ptail_daily"].mean()),
                     "tail_amplitude_abs": float(
                         g["btc_return_7d"].abs().mean()),
                     "tail_amplitude_sigma": float(g["vol_med"].mean())})
    out = pd.DataFrame(rows)
    out["verdict"] = "TAIL_ACTIVATION_SURFACE_BUILT"
    out.to_csv(OUT / "20_TAIL_ACTIVATION_SURFACE.csv", index=False)
    return out


# =========================================================================
# WS20: RANK RECRUITMENT SURFACE (21_RANK_RECRUITMENT_SURFACE.csv)
# =========================================================================
def ws20_rank_recruitment_surface(df, band):
    b = band.copy()
    b["coarse"] = b["band"].map(FINE_TO_COARSE)
    b = b.dropna(subset=["coarse"])
    b["active"] = (b["ppos"] >= ACTIVATION_THRESH).astype(int)
    pg = b.groupby(["d", "coarse"])["active"].max().reset_index()
    pg["d"] = pd.to_datetime(pg["d"]).dt.normalize()
    shallow = pg[pg["coarse"].isin(["26-100", "101-250", "251-500"])] \
        .groupby("d")["active"].max().rename("shallow_act")
    mid = pg[pg["coarse"].isin(["501-750", "751-1000"])] \
        .groupby("d")["active"].max().rename("mid_act")
    deep = pg[pg["coarse"].isin(["1001-1500", "1501-2000"])] \
        .groupby("d")["active"].max().rename("deep_act")
    df = df.merge(shallow.rename("shallow_act"), left_on="d",
                  right_index=True, how="left")
    df = df.merge(mid.rename("mid_act"), left_on="d", right_index=True,
                  how="left")
    df = df.merge(deep.rename("deep_act"), left_on="d", right_index=True,
                  how="left")
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 50:
            rows.append({"mcell": mc, "n": int(len(g)),
                         "verdict": "DATA_LIMITED"})
            continue
        rows.append({"mcell": mc, "n": int(len(g)),
                     "shallow_activation": float(g["shallow_act"].fillna(0)
                                                 .mean()),
                     "mid_activation": float(g["mid_act"].fillna(0).mean()),
                     "deep_activation": float(g["deep_act"].fillna(0).mean()),
                     "rank_recruit_rate": float(g["rank7"].mean()),
                     "rank_depth_rel": float(g["rank_depth_rel"].mean()),
                     "n_subperiods": int(g["subperiod"].replace("UNKNOWN",
                         np.nan).dropna().nunique())})
    out = pd.DataFrame(rows)
    out["verdict"] = "RANK_RECRUITMENT_SURFACE_BUILT"
    out.to_csv(OUT / "21_RANK_RECRUITMENT_SURFACE.csv", index=False)
    return out
