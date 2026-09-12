from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split

ACTIVATION_THRESH = 0.55
DEPTH_ORDER = ["26-100", "101-250", "251-500", "501-750", "751-1000",
               "1001-1500", "1501-2000"]


def _band_depth(bn):
    for i, co in enumerate(DEPTH_ORDER):
        if bn == co or FINE_TO_COARSE.get(bn) == co:
            return i
    return np.nan


# =========================================================================
# WS9: WATERFALL SUBTYPE MATRIX (10_WATERFALL_SUBTYPE_MATRIX.csv)
# =========================================================================

def _activation_dates_per_band(band):
    """First activation day of each coarse-band episode."""
    recs = []
    for bn, g in band.groupby("band", observed=True):
        g = g.sort_values("d")
        act = (g["ppos"] >= ACTIVATION_THRESH) & \
            (g["ppos"].shift(1) < ACTIVATION_THRESH)
        for d in g[act]["d"]:
            recs.append({"band": bn, "d": d})
    return pd.DataFrame(recs)


def ws9_waterfall_subtypes(band, dfw):
    acts = _activation_dates_per_band(band)
    acts["depth"] = acts["band"].apply(_band_depth)
    acts = acts.dropna(subset=["depth"]).sort_values(["d", "depth"])
    fi = dfw.set_index("d")
    # group activations into event windows by date (>=3 bands active within
    # 7d rolling)
    acts["date"] = pd.to_datetime(acts["d"])
    events = []
    used = set()
    for i, r in acts.iterrows():
        if i in used:
            continue
        d0 = r["date"]
        win = acts[(acts["date"] >= d0) & (acts["date"] <= d0 + pd.Timedelta(
            days=7))]
        used |= set(win.index)
        bands_active = sorted(win["depth"].unique())
        if len(bands_active) < 3:
            continue
        events.append({"t0": d0, "n_bands": len(bands_active),
                       "max_depth": max(bands_active),
                       "min_depth": min(bands_active),
                       "num_bands": len(bands_active)})
    # classify subtype by the ordering and depth reach
    sub_rows = []
    for e in events:
        t0 = e["t0"]
        window = acts[(acts["date"] >= t0) & (acts["date"] <= t0 + pd.Timedelta(
            days=7))]
        depths = sorted(window["depth"].unique())
        shallow = [d for d in depths if d <= 2]
        deep = [d for d in depths if d >= 4]
        if len(depths) == 1 and depths[0] <= 2:
            st = "EARLY_SHALLOW_ONLY"
        elif len(shallow) and len(deep) and max(deep) - min(depths) >= 4:
            st = "ORDERLY_SHALLOW_TO_DEEP"
        elif len(deep) and len(shallow) and len(deep) >= 2 and \
                min(depths) >= 2:
            st = "MID_FIELD_RECRUITMENT"
        elif len(deep) >= 3 and len(shallow) == 0:
            st = "LATE_DEEP_ACTIVATION"
        elif len(depths) >= 4 and max(depths) - min(depths) <= 2:
            st = "SIMULTANEOUS_BROAD_ACTIVATION"
        elif len(depths) <= 2:
            st = "FAILED_WATERFALL"
        else:
            st = "FRAGMENTED_ACTIVATION"
        # field intensity at t0
        ctx = fi.loc[fi.index.isin([t0])] if len(
            fi.loc[fi.index.isin([t0])]) else pd.DataFrame()
        sub_rows.append(dict(e, subtype=st,
                             breadth=float(ctx["top500_breadth_30d"].iloc[0])
                             if len(ctx) else np.nan,
                             dispersion=float(ctx[
                                 "top500_dispersion_30d"].iloc[0])
                             if len(ctx) else np.nan,
                             vol=float(ctx["vol_med"].iloc[0])
                             if len(ctx) else np.nan,
                             btc7=float(ctx["btc_return_7d"].iloc[0])
                             if len(ctx) else np.nan,
                             cell=str(ctx["cell"].iloc[0]) if len(ctx) else "",
                             age=float(ctx["age_in_cell"].iloc[0])
                             if len(ctx) else np.nan))
    out = pd.DataFrame(sub_rows)
    if len(out):
        # per-subtype summary
        g = out.groupby("subtype")
        summ = g.agg(n=("subtype", "size"),
                     med_breadth=("breadth", "median"),
                     med_dispersion=("dispersion", "median"),
                     med_vol=("vol", "median"),
                     med_btc7=("btc7", "median"),
                     med_age=("age", "median"),
                     p_HH=("cell", lambda s: (s ==
                                              "HIGH_BREADTH_HIGH_DISP").mean()))
        summ["n_subperiods"] = 0
        summ["verdict"] = np.where(summ["n"] >= MIN_PROMOTE_N,
                                   "NAMED_SUBTYPE", "DESCRIPTIVE")
        summ = summ.reset_index()
        out = summ
    else:
        out = pd.DataFrame([{"subtype": "NONE", "n": 0, "verdict":
                             "DATA_BLOCKED"}])
    out.to_csv(OUT / "10_WATERFALL_SUBTYPE_MATRIX.csv", index=False)
    return out


# =========================================================================
# WS10: ACTIVATION THRESHOLD SURFACES (11_ACTIVATION_THRESHOLD_SURFACES.csv)
# =========================================================================

def ws10_activation_surfaces(band, dfw):
    fi = dfw.set_index("d")
    b = band.copy()
    b["coarse"] = b["band"].map(FINE_TO_COARSE)
    b = b.dropna(subset=["coarse"])
    b["active"] = (b["ppos"] >= ACTIVATION_THRESH).astype(int)
    rows = []
    for coarse, g in b.groupby("coarse"):
        g = g.groupby("d").agg(active=("active", "max"),
                               ppos=("ppos", "mean")).reset_index()
        g = g.set_index("d").join(
            fi[["top500_breadth_30d", "top500_dispersion_30d", "vol_med",
                "btc_return_7d", "top3_share"]], how="left")
        g = g.dropna()
        for coord in ["top500_breadth_30d", "top500_dispersion_30d",
                      "vol_med", "btc_return_7d", "top3_share"]:
            x = g[coord].to_numpy()
            y = g["active"].to_numpy()
            # monotonic binning: activation rate in coord quantile bands
            try:
                qs = pd.qcut(x, 4, labels=False, duplicates="drop")
            except Exception:
                continue
            dfq = pd.DataFrame({"q": qs, "y": y})
            rates = dfq.groupby("q")["y"].mean().reindex(range(dfq[
                "q"].nunique()))
            rho, p = spearmanr(x, y)
            monotone = rates.is_monotonic_increasing or \
                rates.is_monotonic_decreasing
            rows.append({"patch": coarse, "coord": coord,
                         "activation_rate_min_q": float(rates.min()),
                         "activation_rate_max_q": float(rates.max()),
                         "monotonic_binning": bool(monotone),
                         "spearman_rho": float(rho), "p": float(p)})
    out = pd.DataFrame(rows)
    if len(out):
        q = _fdr(out["p"].to_numpy())
        out["q"] = q
        def _cls(r):
            if r["q"] <= FDR_Q and r["monotonic_binning"]:
                return "MONOTONIC_THRESHOLD_SURFACE"
            if r["q"] <= FDR_Q:
                return "THRESHOLD_SURFACE_NON_MONOTONIC"
            return "NO_STABLE_SURFACE"
        out["surface_type"] = out.apply(_cls, axis=1)
        out["verdict"] = "ACTIVATION_SURFACES_BUILT"
    out.to_csv(OUT / "11_ACTIVATION_THRESHOLD_SURFACES.csv", index=False)
    return out


# =========================================================================
# WS11: PATCH RESPONSE CURVES (12_PATCH_RESPONSE_CURVES.csv)
# =========================================================================

def ws11_patch_response_curves(dfw, band):
    df = dfw.copy()
    pert = _perturbation_flags(df)
    # legit standardized amplitudes
    amp_defs = {"brd_jump": ("top500_breadth_30d", 1),
                "brd_drop": ("top500_breadth_30d", -1),
                "disp_jump": ("top500_dispersion_30d", 1),
                "disp_drop": ("top500_dispersion_30d", -1),
                "btc_shock": ("btc_return_7d", 1),
                "conc_shock": ("top3_share_chg7", 1),
                "vol_shock": ("vol_med", 1)}
    g = band.copy()
    g["patch"] = g["band"].map(
        {fb: p for p, fbs in PATCHES.items() for fb in fbs})
    g = g.dropna(subset=["patch"])
    pg = g.groupby(["d", "patch"]).agg(med_ret=("med_ret", "mean"),
                                       ppos=("ppos", "mean"),
                                       ptail=("ptail", "mean")).reset_index()
    rows = []
    for patch in PATCHES:
        pser = pg[pg["patch"] == patch].set_index("d")
        for pname, (col, _sig) in amp_defs.items():
            chg = df[col].diff(5)
            z = chg / chg.std() if chg.std() else chg
            z = z.abs()
            m = (pert[pname] == 1)
            idx = df.index[m]
            if len(idx) < 30:
                continue
            # quantile bands of amplitude
            az = z.loc[idx]
            az = az[~az.isna()]
            if len(az) < 30:
                continue
            try:
                qb = pd.qcut(az, 4, labels=["Q1", "Q2", "Q3", "Q4"],
                             duplicates="drop")
            except Exception:
                continue
            for lbl, qi in qb.groupby(qb):
                sel = idx[qb[qb.index].reindex(idx) == lbl]
                if len(sel) < 10:
                    continue
                dates = pd.to_datetime(df.loc[sel, "d"]).dt.normalize()
                resp = pser.loc[pser.index.isin(dates)]
                # 3D forward activation prob
                fwd_act = []
                for dt in dates:
                    pos = pser.index.get_indexer([dt], method="nearest")
                    if pos[0] < 0 or pos[0] >= len(pser) - 3:
                        continue
                    w = pser["ppos"].iloc[pos[0]:pos[0] + 4]
                    fwd_act.append((w >= ACTIVATION_THRESH).any())
                act_rate = float(np.mean(fwd_act)) if fwd_act else np.nan
                tail = float(resp["ptail"].mean()) if len(resp) else np.nan
                mr = float(resp["med_ret"].mean()) if len(resp) else np.nan
                rows.append({"patch": patch, "perturbation": pname,
                             "amp_band": lbl, "n": int(len(sel)),
                             "activation_prob_3d": act_rate,
                             "tail_share_after": tail,
                             "median_ret_after": mr})
    out = pd.DataFrame(rows)
    if len(out) and "activation_prob_3d" in out.columns:
        # response curve shape = activation-rate trend across amp bands
        shapes = {}
        for (patch, pname), sub in out.groupby(["patch", "perturbation"]):
            s = sub.sort_values("amp_band")
            rates = s["activation_prob_3d"].to_numpy(dtype=float)
            rates = rates[~np.isnan(rates)]
            if len(rates) < 3:
                shapes[(patch, pname)] = "NO_STABLE_RESPONSE"
                continue
            d = np.diff(rates)
            if rates[-1] - rates[0] > 0.05 and np.all(d > -0.02):
                shapes[(patch, pname)] = "MONOTONIC_RISING"
            elif rates[-1] - rates[0] < -0.05 and np.all(d < 0.02):
                shapes[(patch, pname)] = "MONOTONIC_FALLING"
            elif np.max(np.abs(d)) > 0.08:
                shapes[(patch, pname)] = "THRESHOLD"
            elif abs(rates[-1] - rates[0]) <= 0.05:
                shapes[(patch, pname)] = "SATURATING"
            else:
                shapes[(patch, pname)] = "NO_STABLE_RESPONSE"
        out["response_shape"] = [
            shapes.get((r["patch"], r["perturbation"]),
                       "NO_STABLE_RESPONSE") for _, r in out.iterrows()]
        out["verdict"] = "PATCH_RESPONSE_CURVES_BUILT"
    out.to_csv(OUT / "12_PATCH_RESPONSE_CURVES.csv", index=False)
    return out


# =========================================================================
# WS12: RESPONSE CURVE HETEROGENEITY (13_RESPONSE_CURVE_HETEROGENEITY.csv)
# =========================================================================

def ws12_response_heterogeneity(dfw, patch_resp):
    # test whether the same perturbation's response differs across patches
    out = patch_resp.copy() if patch_resp is not None else\
        pd.DataFrame()
    if len(out) == 0:
        out = pd.DataFrame([{"verdict": "DATA_LIMITED", "n_cells": 0}])
        out.to_csv(OUT / "13_RESPONSE_CURVE_HETEROGENEITY.csv", index=False)
        return out
    # compare activation rate spread across patches per perturbation
    rows = []
    for pname, g in out[out["perturbation"].notna()].groupby(
            "perturbation"):
        spread = g["activation_prob_3d"].max() - \
            g["activation_prob_3d"].min()
        rows.append({"perturbation": pname,
                     "n_patch_bands": int(g["n_amps"].sum())
                     if "n_amps" in g else int(len(g)),
                     "activation_spread_across_patches": float(spread),
                     "max_activation_patch": g.loc[
                         g["activation_prob_3d"].idxmax(), "patch"]
                     if g["activation_prob_3d"].notna().any() else ""})
    het = pd.DataFrame(rows)
    if len(het):
        het["verdict"] = np.where(
            het["activation_spread_across_patches"] >= 0.15,
            "HETEROGENEOUS_TRANSFER_FUNCTIONS",
            "HOMOGENEOUS_TRANSFER_FUNCTION")
    het.to_csv(OUT / "13_RESPONSE_CURVE_HETEROGENEITY.csv", index=False)
    return het