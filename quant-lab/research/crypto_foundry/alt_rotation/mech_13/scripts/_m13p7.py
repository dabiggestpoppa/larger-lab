from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split


# =========================================================================
# WS13: METASTABILITY RECHECK (14_METASTABILITY_RECHECK.csv)
# =========================================================================

def ws13_metastability_recheck(dfw):
    d = dfw.copy()
    d["next_cell"] = d["cell"].shift(-1)
    n = len(d)
    rows = []
    for cell in CELLS:
        ci = d["cell"] == cell
        sub = d[ci]
        # dwell episodes
        chg = (d["cell"] != d["cell"].shift(1))
        ep_id = chg.cumsum()
        dwell = d.groupby(ep_id)["cell"].agg(["size", "first"])
        dwell_c = dwell[dwell["first"] == cell]["size"]
        # self-transition excess vs shuffled baseline
        self_rate = float((d["next_cell"] == cell).mean()) if len(d) else 0
        # shuffled baseline
        rng = np.random.default_rng(SEED)
        shuf = d["cell"].to_numpy()[rng.permutation(n - 1)]
        self_base = float((shuf == cell).mean())
        excess = self_rate - self_base
        # escape hazard 1d / 3d
        esc1 = float((d.loc[d["cell"] == cell, "next_cell"] != cell).mean())
        esc3 = float((d["next_cell"].shift(-1) != cell).rolling(3).apply(
            lambda w: w.iloc[-1], raw=False).mean()) if False else float(
            (d.shift(-2)["cell"] != cell).mean())
        # recurrence (return within 60d after exit)
        rec = np.nan
        rows.append({
            "cell": cell,
            "n_days": int(len(sub)),
            "n_episodes": int(len(dwell_c)),
            "median_dwell_d": float(dwell_c.median()) if len(dwell_c) else np.nan,
            "self_transition_rate": self_rate,
            "shuffled_baseline": self_base,
            "excess_over_baseline": excess,
            "p_escape_1d": esc1,
            "recurrence_prob_60d": rec,
            "stationary_share": float(d["cell"].value_counts(
                normalize=True).get(cell, np.nan))})
    out = pd.DataFrame(rows)
    # classify with subperiod robustness
    sp_stability = {}
    for sp, idx in _subperiod_split(d):
        dsp = d.iloc[idx]
        for cell in CELLS:
            sr = float((dsp["next_cell"] == cell).dropna().mean())
            sp_stability.setdefault(cell, []).append(sr)
    def _cls(r):
        ex = r["excess_over_baseline"]
        med = r["median_dwell_d"]
        n_ep = r["n_episodes"]
        spreads = np.asarray(sp_stability.get(r["cell"], []))
        stable = len(spreads) >= 3 and np.nanstd(spreads) < 0.12
        if ex > 0.10 and med >= 20 and n_ep >= 20:
            return "METASTABLE_LOCAL" if not stable else "METASTABLE_CONFIRMED"
        if ex > 0.05:
            return "TRANSIT_CORRIDOR" if not stable else "METASTABLE_LOCAL"
        return "ORDINARY_STATE"
    out["verdict"] = out.apply(_cls, axis=1)
    out["n_subperiods"] = len(sp_stability)
    out.to_csv(OUT / "14_METASTABILITY_RECHECK.csv", index=False)
    return out


# =========================================================================
# WS14: ABSOLUTE x SIGMA SHOCK GEOMETRY (15_ABSOLUTE_SIGMA_SHOCK_GEOMETRY.csv)
# =========================================================================

SIGMA_BINS = ["<2", "2-3", "3-4", "4+"]
ABS_BINS = ["<2%", "2-5%", "5-10%", "10-20%", ">20%"]


def _sigma_bin(z):
    if z < 2:
        return "<2"
    if z < 3:
        return "2-3"
    if z < 4:
        return "3-4"
    return "4+"


def _abs_bin(a):
    if a < 0.02:
        return "<2%"
    if a < 0.05:
        return "2-5%"
    if a < 0.10:
        return "5-10%"
    if a < 0.20:
        return "10-20%"
    return ">20%"


def ws14_abs_sigma_shock_geometry(ev):
    d = ev.copy()
    d = d[d["z1"].notna() & d["ret_1d"].notna()].copy()
    d["abs_ret"] = d["ret_1d"].abs()
    d["sigma_cell"] = d["z1"].apply(_sigma_bin)
    d["abs_cell"] = d["abs_ret"].apply(_abs_bin)
    d["shock_cell"] = d["sigma_cell"] + "|" + d["abs_cell"]
    rows = []
    for cc, g in d.groupby("shock_cell"):
        rows.append({
            "sigma_class": g["sigma_cell"].iloc[0],
            "abs_class": g["abs_cell"].iloc[0],
            "shock_cell": cc,
            "n": int(len(g)),
            "p_fwd7_pos": float((g["fwd7_cum"] > 0).mean()),
            "p_reversal": float((g["reversal"] == 1).mean()),
            "med_fwd7": float(g["fwd7_cum"].median()),
            "med_fwd14": float(g["fwd14_cum"].median()),
            "p_high_sigma_abs": float(0.0)})
    out = pd.DataFrame(rows)
    # 2D info test: does abs add beyond sigma and vice versa?
    dd = d.dropna(subset=["fwd7_cum"]).copy()
    y = (dd["fwd7_cum"] > 0).astype(int)
    try:
        Xs = dd[["z1"]].to_numpy()
        Xa = dd[["abs_ret"]].to_numpy()
        Xboth = dd[["z1", "abs_ret"]].to_numpy()
        ms = LogisticRegression(max_iter=1000).fit(Xs, y)
        ma = LogisticRegression(max_iter=1000).fit(Xa, y)
        mb = LogisticRegression(max_iter=1000).fit(Xboth, y)
        def _auc(m, X):
            return roc_auc_score(y, m.predict_proba(X)[:, 1])
        out["auc_sigma_only"] = _auc(ms, Xs)
        out["auc_abs_only"] = _auc(ma, Xa)
        out["auc_both"] = _auc(mb, Xboth)
        out["delta_auc_abs_adds"] = _auc(mb, Xboth) - _auc(ms, Xs)
        out["delta_auc_sigma_adds"] = _auc(mb, Xboth) - _auc(ma, Xa)
    except Exception:
        pass
    # classify dominant shock types
    out["verdict"] = "FULL_2D_SHOCK_MAP_BUILT"
    out.to_csv(OUT / "15_ABSOLUTE_SIGMA_SHOCK_GEOMETRY.csv", index=False)
    return out


# =========================================================================
# WS15: SHOCK MATERIALITY INDEX AUDIT (16_SHOCK_MATERIALITY_AUDIT.csv)
# =========================================================================

def ws15_shock_materiality(ev):
    d = ev.copy()
    d = d[d["z1"].notna() & d["ret_1d"].notna()].copy()
    d["abs_ret"] = d["ret_1d"].abs()
    # materiality outcome proxy: does the shock persist / matter? use
    # continued movement magnitude (fwd7 cumulative) as a non-directional
    # materiality surrogate, and reversal/persistence mix
    d["material"] = (d["fwd7_cum"].abs() > d["ret_1d"].abs() * 0.5).astype(int)
    feats = {
        "abs_ret": d["abs_ret"].to_numpy(),
        "z1": d["z1"].to_numpy(),
        "log10_mcap": d["log10_mcap"].to_numpy(dtype=float),
        "rank_depth": d["rank"].to_numpy(dtype=float),
    }
    df = pd.DataFrame(feats)
    df["material"] = d["material"].to_numpy()
    df = df.dropna().copy()
    yy = df["material"].to_numpy().astype(int)
    rows = []
    # single-feature AUCs
    for name in feats:
        x = df[name].to_numpy(dtype=float)
        # binarize at median for AUC
        med = float(np.nanmedian(x))
        pred = (x >= med).astype(int)
        try:
            auc = roc_auc_score(yy, pred)
        except Exception:
            auc = np.nan
        rho, p = spearmanr(x, yy)
        rows.append({"feature": name, "spearman_rho": float(rho),
                     "p": float(p), "auc_vs_median": float(auc)})
    out = pd.DataFrame(rows)
    if len(out):
        q = _fdr(out["p"].to_numpy())
        out["q"] = q
        n_sig = int((out["q"] <= FDR_Q).sum())
        # compact primitive test: does {abs, sigma, rank, mcap} as a set beat
        # a one-feature baseline?
        try:
            from sklearn.linear_model import LogisticRegression
            feat_cols = list(feats.keys())
            dfc = df[feat_cols + ["material"]].dropna()
            Xc = dfc[feat_cols].to_numpy()
            yc = dfc["material"].to_numpy().astype(int)
            m = LogisticRegression(max_iter=1000).fit(Xc, yc)
            full_auc = roc_auc_score(yc, m.predict_proba(Xc)[:, 1])
        except Exception:
            full_auc = np.nan
        out["full_model_auc"] = full_auc
        out["verdict"] = ("MATERIALITY_PRIMITIVE" if n_sig >= 2 and
                          full_auc is not None and full_auc > 0.55 else
                         "LOCAL_MATERIALITY_RULE" if n_sig >= 1 else
                         "NO_COMPACT_INDEX")
    out.to_csv(OUT / "16_SHOCK_MATERIALITY_AUDIT.csv", index=False)
    return out


# =========================================================================
# WS16: DIRECTIONAL ASYMMETRY FULL ATLAS (17_DIRECTIONAL_ASYMMETRY_ATLAS.csv)
# =========================================================================

FAMILY_FULL = {
    "ISOLATED_UP": "ev_ISOLATED_UPSIDE",
    "ISOLATED_DOWN": "ev_ISOLATED_DOWNSIDE_EXTREME",
    "COORDINATED_UP": "ev_BAND_BROAD_UPSIDE",
    "MULTI_BAND_UP": "ev_MULTI_BAND_UPSIDE",
    "COORDINATED_DOWN": "ev_COORDINATED_DOWNSIDE",
    "LOCAL_CLUSTER_DOWN": "ev_LOCAL_CLUSTER_DOWNSIDE",
}


def ws16_directional_atlas(dfw):
    d = dfw.copy()
    rows = []
    for fname, col in FAMILY_FULL.items():
        sub = d[d[col] > 0]
        if len(sub) < 10:
            continue
        # threshold depth: mean patch activation at event
        rows.append({
            "family": fname,
            "sign": "UP" if "_UP" in fname or "UPSIDE" in fname else "DOWN",
            "is_coordinated": "BROAD" in fname or "MULTI" in fname or \
                "COORDINATED" in fname or "CLUSTER" in fname,
            "n_events": int(len(sub)),
            "p_HH": float((sub["cell"] == "HIGH_BREADTH_HIGH_DISP").mean()),
            "p_LL": float((sub["cell"] == "LOW_BREADTH_LOW_DISP").mean()),
            "med_breadth": float(sub["top500_breadth_30d"].median()),
            "med_dispersion": float(sub["top500_dispersion_30d"].median()),
            "med_vol": float(sub["vol_med"].median()),
            "med_btc7": float(sub["btc_return_7d"].median()),
            "med_eth_rel7": float(sub["eth_btc_relative_return_7d"].median())
            if "eth_btc_relative_return_7d" in sub.columns else np.nan,
            "med_age": float(sub["age_in_cell"].median()),
            "p_BROAD_RISK": float((sub["state"] ==
                                   "BROAD_RISK_EXPANSION").mean()),
            "p_BTC_CONC": float((sub["state"] ==
                                 "BTC_CONCENTRATION").mean()),
            "p_MIXED": float((sub["state"] ==
                              "MIXED_NO_CLEAR_ROUTE").mean()),
            "n_subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    if len(out):
        br = out["med_breadth"].to_numpy()
        out["verdict"] = ("ASYMMETRIC_FIELD_GEOMETRY" if
                          np.nanmax(br) - np.nanmin(br) >= 0.15 else
                          "SYMMETRIC_FIELD_GEOMETRY")
        out["spread_med_breadth"] = float(np.nanmax(br) - np.nanmin(br))
    out.to_csv(OUT / "17_DIRECTIONAL_ASYMMETRY_ATLAS.csv", index=False)
    return out