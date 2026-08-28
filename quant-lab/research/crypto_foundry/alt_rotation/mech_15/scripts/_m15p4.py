from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, MC, cell_stats, ACTIVATION_THRESH

DEPTH_RANGES = {"SHALLOW": ["26-100", "101-250", "251-500"],
                "MID": ["501-750", "751-1000"],
                "DEEP": ["1001-1500", "1501-2000"]}


# =========================================================================
# WS10: FORCING POSITION (11_FORCING_POSITION.csv)
# =========================================================================
def ws10_forcing_position(df, band):
    # per-patch active days (coarse bands)
    b = band.copy()
    b["coarse"] = b["band"].map(FINE_TO_COARSE)
    b = b.dropna(subset=["coarse"])
    b["active"] = (b["ppos"] >= ACTIVATION_THRESH).astype(int)
    pg = b.groupby(["d", "coarse"])["active"].max().reset_index()
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 20:
            continue
        f = g["forcing"].dropna()
        q = f.quantile([0.25, 0.5, 0.75])
        dates = g["d"].dt.normalize()
        act = pg[pg["d"].dt.normalize().isin(set(dates))]
        n_active = act[act["active"] == 1].groupby("d")["coarse"].nunique()
        max_depth = []
        for d in set(dates):
            dd = act[act["d"].dt.normalize() == d]
            acts = dd[dd["active"] == 1]["coarse"]
            if len(acts):
                max_depth.append(max(DEPTH_ORDER.index(c) for c in acts
                                     if c in DEPTH_ORDER))
        # saturation fraction: share of days at max active patches
        n_patch_days = act.groupby("d")["coarse"].nunique()
        sat_frac = float((n_patch_days >= 4).mean()) if len(n_patch_days) \
            else np.nan
        rows.append({"mcell": mc, "n": int(len(g)),
                     "forcing_median": float(q[0.5]) if len(f) else np.nan,
                     "forcing_p25": float(q[0.25]) if len(f) else np.nan,
                     "forcing_p75": float(q[0.75]) if len(f) else np.nan,
                     "n_active_patches_median": float(
                         n_active.median()) if len(n_active) else np.nan,
                     "max_depth_index_median": float(
                         np.median(max_depth)) if max_depth else np.nan,
                     "max_depth_band": DEPTH_ORDER[int(np.median(max_depth))]
                     if max_depth and not np.isnan(np.median(max_depth))
                     else "",
                     "saturation_fraction": sat_frac,
                     "n_subperiods": int(g["subperiod"].replace("UNKNOWN",
                         np.nan).dropna().nunique())})
    out = pd.DataFrame(rows)
    out["verdict"] = "FORCING_POSITION_MAPPED"
    out.to_csv(OUT / "11_FORCING_POSITION.csv", index=False)
    return out


# =========================================================================
# WS11: ACTIVATION-DEPTH PROFILE (12_ACTIVATION_DEPTH_PROFILE.csv)
# =========================================================================
def ws11_activation_depth_profile(df, band):
    b = band.copy()
    b["coarse"] = b["band"].map(FINE_TO_COARSE)
    b = b.dropna(subset=["coarse"])
    b["active"] = (b["ppos"] >= ACTIVATION_THRESH).astype(int)
    pg = b.groupby(["d", "coarse"])["active"].max().reset_index()
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) < 20:
            continue
        dates = set(g["d"].dt.normalize())
        act = pg[pg["d"].dt.normalize().isin(dates)]
        row = {"mcell": mc, "n_days": int(len(g))}
        for depth in DEPTH_ORDER:
            a = act[(act["coarse"] == depth) & (act["active"] == 1)]
            row[f"act_{depth}"] = float(len(a) / len(g)) if len(g) else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    # profile classification (stable across >=3 subperiods)
    labels = []
    for mc in out["mcell"]:
        g = df[df["mcell"] == mc]
        sp_labels = {}
        for sp, sg in g.groupby("subperiod"):
            if sp == "UNKNOWN" or len(sg) < 15:
                continue
            dates = set(sg["d"].dt.normalize())
            act = pg[pg["d"].dt.normalize().isin(dates)]
            shallow = (act[(act["coarse"].isin(DEPTH_RANGES["SHALLOW"])) &
                           (act["active"] == 1)]["d"].nunique() / len(sg))
            mid = (act[(act["coarse"].isin(DEPTH_RANGES["MID"])) &
                       (act["active"] == 1)]["d"].nunique() / len(sg))
            deep = (act[(act["coarse"].isin(DEPTH_RANGES["DEEP"])) &
                        (act["active"] == 1)]["d"].nunique() / len(sg))
            if deep >= 0.3:
                sp_labels[sp] = "BROAD_FULL_FIELD" if shallow >= 0.3 else \
                    "DEEP_FIELD"
            elif mid >= 0.3:
                sp_labels[sp] = "MIDFIELD"
            elif shallow >= 0.3:
                sp_labels[sp] = "SHALLOW_ONLY"
            else:
                sp_labels[sp] = "LOW_ACTIVATION"
        if len(sp_labels) >= MIN_SUBPERIODS:
            vc = pd.Series(sp_labels).value_counts()
            labels.append(vc.index[0])
        else:
            labels.append("DATA_LIMITED")
    out["depth_profile"] = labels
    out["verdict"] = "ACTIVATION_DEPTH_PROFILE_BUILT"
    out.to_csv(OUT / "12_ACTIVATION_DEPTH_PROFILE.csv", index=False)
    return out


# =========================================================================
# WS12: WATERFALL CELL PLACEMENT (13_WATERFALL_CELL_PLACEMENT.csv)
# =========================================================================
def ws12_waterfall_cell_placement(df, band):
    # rebuild activation events exactly as M14 WS11
    from _m14p4 import _activation_dates_per_band, _band_depth
    acts = _activation_dates_per_band(band)
    acts["depth"] = acts["band"].apply(_band_depth)
    acts = acts.dropna(subset=["depth"]).sort_values(["d", "depth"])
    acts["date"] = pd.to_datetime(acts["d"]).dt.normalize()
    events = []
    used = set()
    for i, r in acts.iterrows():
        if i in used:
            continue
        d0 = r["date"]
        win = acts[(acts["date"] >= d0) &
                   (acts["date"] <= d0 + pd.Timedelta(days=7))]
        used |= set(win.index)
        depths = sorted(win["depth"].unique())
        if len(depths) < 3:
            continue
        shallow = [d for d in depths if d <= 2]
        deep = [d for d in depths if d >= 4]
        nact = len(depths)
        if len(depths) == 1 and depths[0] <= 2:
            st = "EARLY_SHALLOW_ONLY"
        elif len(shallow) and len(deep) and max(deep) - min(depths) >= 4:
            st = "ORDERLY_SHALLOW_TO_DEEP"
        elif len(deep) and len(shallow) and len(deep) >= 2 and \
                min(depths) >= 2:
            st = "MID_FIELD_RECRUITMENT"
        elif len(deep) >= 3 and len(shallow) == 0:
            st = "LATE_DEEP_ACTIVATION"
        elif nact >= 4 and max(depths) - min(depths) <= 2:
            st = "SIMULTANEOUS_BROAD_ACTIVATION"
        elif nact <= 2:
            st = "FAILED_WATERFALL"
        else:
            st = "FRAGMENTED_ACTIVATION"
        events.append({"t0": d0, "subtype": st,
                       "max_depth_index": max(depths)})
    ev = pd.DataFrame(events)
    dmap = df.set_index("d")
    ROLE_BY_SUBTYPE = {"EARLY_SHALLOW_ONLY": "FAILURE_NONRESPONSE",
                       "FAILED_WATERFALL": "FAILURE_NONRESPONSE",
                       "SIMULTANEOUS_BROAD_ACTIVATION": "SIMULTANEOUS",
                       "ORDERLY_SHALLOW_TO_DEEP": "PROGRESSION",
                       "MID_FIELD_RECRUITMENT": "MIDFIELD",
                       "LATE_DEEP_ACTIVATION": "DEEP_ACTIVATION",
                       "FRAGMENTED_ACTIVATION": "FRAGMENTED"}
    rows = []
    for _, e in ev.iterrows():
        t0 = e["t0"]
        mc = "UNMAPPED"
        if t0 in dmap.index:
            mc = dmap.loc[t0, "mcell"]
        rows.append({"t0": t0, "subtype": e["subtype"], "mcell": mc,
                     "role": ROLE_BY_SUBTYPE.get(e["subtype"], "OTHER")})
    out = pd.DataFrame(rows)
    summ = out.groupby(["mcell", "subtype"]).size().reset_index(name="n")
    piv = summ.pivot_table(index="mcell", columns="subtype", values="n",
                           fill_value=0)
    piv = piv.reindex(index=MC).fillna(0).astype(int)
    piv["n_events_total"] = piv.sum(axis=1)
    role_piv = out.groupby("mcell")["role"].value_counts().unstack(
        fill_value=0).reindex(index=MC).fillna(0).astype(int)
    for c in ["INITIATION", "PROGRESSION", "DEEP_ACTIVATION",
              "FAILURE_NONRESPONSE", "SIMULTANEOUS", "MIDFIELD",
              "FRAGMENTED"]:
        if c not in role_piv.columns:
            role_piv[c] = 0
    piv = piv.join(role_piv[["INITIATION", "PROGRESSION", "DEEP_ACTIVATION",
                             "FAILURE_NONRESPONSE", "SIMULTANEOUS",
                             "MIDFIELD", "FRAGMENTED"]])
    piv["verdict"] = "WATERFALL_CELL_PLACEMENT_MAPPED"
    piv.to_csv(OUT / "13_WATERFALL_CELL_PLACEMENT.csv")
    return piv.reset_index()
