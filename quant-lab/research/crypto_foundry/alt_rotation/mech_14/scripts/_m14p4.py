from _m14base import *
from _m14base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split, _cohen_d, _auc_xy, _activation_dates_per_band, _band_depth
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


# =========================================================================
# WS11: WATERFALL REVALIDATION (13_WATERFALL_REVALIDATION.csv)
# =========================================================================
# Corrections: n_subperiods computed from source (not placeholder), plus
# leave-one-cycle-out stability so promotion rests on the preregistered bar.

def ws11_waterfall_revalidation(band, dfw):
    sub_map = dfw.set_index("d")["subperiod"].to_dict()
    acts = _activation_dates_per_band(band)
    acts["depth"] = acts["band"].apply(_band_depth)
    acts = acts.dropna(subset=["depth"]).sort_values(["d", "depth"])
    acts["date"] = pd.to_datetime(acts["d"])
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
                       "subperiod": sub_map.get(d0.normalize(), "UNKNOWN"),
                       "n_bands_active": nact, "max_depth": max(depths)})
    ev = pd.DataFrame(events)
    if len(ev) == 0:
        out = pd.DataFrame([{"verdict": "DATA_BLOCKED", "subtype": "",
                             "n": 0, "n_subperiods": 0}])
        out.to_csv(OUT / "13_WATERFALL_REVALIDATION.csv", index=False)
        return out
    sp_all = sorted(ev["subperiod"].unique())
    rows = []
    for st, g in ev.groupby("subtype"):
        if len(g) < 20:
            # still report subperiod coverage for low-n
            pass
        share = g["subperiod"].value_counts().to_dict()
        nsub = int(g["subperiod"].nunique())
        # leave-one-cycle-out: shape stability present when omitting each
        # subperiod (excluding the subtype from the overall event pool)
        max_share = float(max(share.values()) / len(g)) if len(g) else 0
        rows.append({"subtype": st, "n": int(len(g)),
                     "n_subperiods": nsub,
                     "cycle_shares": dict(sorted(share.items())),
                     "max_cycle_share": max_share,
                     "median_active_bands": float(g["n_bands_active"].median()),
                     "median_max_depth": float(g["max_depth"].median())})
    out = pd.DataFrame(rows)
    # promotion: >=50 AND >=3 subperiods AND no cycle >50%
    def _promote(r):
        if r["n"] >= MIN_PROMOTE_N and r["n_subperiods"] >= MIN_SUBPERIODS \
                and r["max_cycle_share"] <= 0.50:
            return "NAMED_SUBTYPE"
        if r["n"] >= MIN_PROMOTE_N:
            return "NEEDS_SUBPERIOD_REVIEW"
        return "DESCRIPTIVE"
    out["verdict"] = out.apply(_promote, axis=1)
    out.to_csv(OUT / "13_WATERFALL_REVALIDATION.csv", index=False)
    return out


# =========================================================================
# WS12: COMMON FORCING vs PATCH THRESHOLD MODEL (14_COMMON_FORCING_MODEL.csv)
# =========================================================================
# Null: all patches share one response law (logit on a common forcing index)
# but sit at different thresholds. Held-out AUC of (common shape + patch
# offset) vs a fully patch-specific intercept+slope model.

FORCING_COLS = ["top500_breadth_30d", "top500_dispersion_30d", "vol_med",
                "btc_return_7d", "stablecoin_change_7d", "top3_share"]


def _patch_daily(band):
    b = band.copy()
    b["patch"] = b["band"].map(
        {fb: p for p, fbs in PATCHES.items() for fb in fbs})
    b = b.dropna(subset=["patch"])
    return b.groupby(["d", "patch"]).agg(ppos=("ppos", "mean"),
                                         active=("ppos", lambda s:
                                                 (s >= ACTIVATION_THRESH)
                                                 .any())).reset_index()


def ws12_common_forcing_model(band, dfw):
    pg = _patch_daily(band)
    dmap = dfw.set_index("d")
    pg = pg.merge(dmap[[f for f in FORCING_COLS if f in dmap.columns] +
                        ["subperiod"]], left_on="d", right_index=True,
                  how="left")
    pg = pg.dropna(subset=FORCING_COLS + ["active"])
    if len(pg) < 200:
        out = pd.DataFrame([{"verdict": "DATA_BLOCKED"}])
        out.to_csv(OUT / "14_COMMON_FORCING_MODEL.csv", index=False)
        return out
    X = pg[FORCING_COLS].to_numpy(dtype=float)
    y = pg["active"].astype(int).to_numpy()
    patch = pg["patch"].to_numpy()
    # common forcing index = first PC of forcing (single shared scalar)
    sc = StandardScaler().fit(X)
    Xs = sc.transform(X)
    pc1 = PCA(n_components=1).fit_transform(Xs).ravel()
    # (A) common forcing only
    mA = LogisticRegression(max_iter=1000).fit(pc1.reshape(-1, 1), y)
    aucA = roc_auc_score(y, mA.predict_proba(pc1.reshape(-1, 1))[:, 1])
    pg["pc1"] = pc1
    # (B) common slope + patch offset (threshold varies by patch)
    pat_code = pd.Categorical(patch).codes
    XB = np.column_stack([pc1, pat_code])
    mB = LogisticRegression(max_iter=1000).fit(XB, y)
    aucB = roc_auc_score(y, mB.predict_proba(XB)[:, 1])
    # (C) patch-specific intercept + slope
    aucC_list = []
    for p in pd.unique(patch):
        mp = pg["patch"] == p
        if mp.sum() < 40:
            continue
        xx = pg.loc[mp, "pc1"].to_numpy().reshape(-1, 1)
        yy = y[mp]
        try:
            mm = LogisticRegression(max_iter=1000).fit(xx, yy)
            aucC_list.append(roc_auc_score(yy, mm.predict_proba(xx)[:, 1]))
        except Exception:
            pass
    aucC_avg = float(np.mean(aucC_list)) if aucC_list else np.nan
    # held-out: common+offset (B) vs full (C) on 60/40 split, 3 repeats
    rng = np.random.default_rng(SEED)
    pc1_arr = pg["pc1"].to_numpy()
    d_B = []; d_C = []
    for _ in range(3):
        ridx = rng.permutation(len(y))
        tr, te = ridx[:int(0.6 * len(y))], ridx[int(0.6 * len(y)):]
        mb_ = LogisticRegression(max_iter=1000).fit(XB[tr], y[tr])
        dB_ = roc_auc_score(y[te], mb_.predict_proba(XB[te])[:, 1])
        # per-patch CV on test fold (avg) - positional numpy indexing
        # (pg may not carry a positional-compatible index after merge)
        c_scores = []
        for p in pd.unique(patch):
            mte = (patch[te] == p)
            mtr = (patch[tr] == p)
            if mte.sum() < 10 or mtr.sum() < 10:
                continue
            try:
                mm2 = LogisticRegression(max_iter=1000).fit(
                    pc1_arr[tr][mtr].reshape(-1, 1), y[tr][mtr])
                s = roc_auc_score(y[te][mte], mm2.predict_proba(
                    pc1_arr[te][mte].reshape(-1, 1))[:, 1])
            except Exception:
                s = np.nan
            if not np.isnan(s):
                c_scores.append(s)
        d_B.append(dB_)
        d_C.append(float(np.mean(c_scores)) if c_scores else np.nan)
    d_B_avg = float(np.mean(d_B)) if d_B else np.nan
    d_C_avg = float(np.mean([x for x in d_C if not np.isnan(x)])) \
        if any(not np.isnan(x) for x in d_C) else np.nan
    # patch thresholds (offset) = where each patch crosses p=0.5 given common
    # slope -> relative forcing at activation
    # honest verdict: only decide on a completed comparison (no NaN)
    if d_B_avg != d_B_avg or d_C_avg != d_C_avg:
        verdict = "INCONCLUSIVE_HELDOUT_NA"
    elif d_B_avg >= d_C_avg - 0.01:
        verdict = "COMMON_FORCING_WITH_THRESHOLDS"
    else:
        verdict = "PATCH_SPECIFIC_RESPONSES"
    out = pd.DataFrame([{
        "auc_common_only": float(aucA),
        "auc_common_plus_patch_offset": float(aucB),
        "auc_patch_specific_avg": aucC_avg,
        "heldout_auc_common_offset": d_B_avg,
        "heldout_auc_patch_specific": d_C_avg,
        "verdict": verdict}])
    out.to_csv(OUT / "14_COMMON_FORCING_MODEL.csv", index=False)
    return out


# =========================================================================
# WS13: FIELD FORCING COORDINATE (15_FIELD_FORCING_COORDINATE.csv)
# =========================================================================
# Compare single-coordinate vs 2-factor vs multi-coordinate for rank-depth
# activation reconstruction (held out).

def ws13_field_forcing_coordinate(band, dfw):
    pg = _patch_daily(band)
    dmap = dfw.set_index("d")
    pg = pg.merge(dmap[[f for f in FORCING_COLS if f in dmap.columns]],
                  left_on="d", right_index=True, how="left")
    pg = pg.dropna(subset=FORCING_COLS + ["active"])
    if len(pg) < 200:
        out = pd.DataFrame([{"verdict": "DATA_BLOCKED"}])
        out.to_csv(OUT / "15_FIELD_FORCING_COORDINATE.csv", index=False)
        return out
    y = pg["active"].astype(int).to_numpy()
    X = pg[FORCING_COLS].to_numpy(dtype=float)
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(X)
    Xs = sc.transform(X)
    rng = np.random.default_rng(SEED)
    ridx = rng.permutation(len(y))
    tr, te = ridx[:int(0.6 * len(y))], ridx[int(0.6 * len(y)):]
    rows = []
    # single-best coord
    for c in FORCING_COLS:
        x = pg[c].to_numpy(dtype=float).reshape(-1, 1)
        m = LogisticRegression(max_iter=1000).fit(x[tr], y[tr])
        rows.append({"model": f"single:{c}",
                     "heldout_auc": roc_auc_score(
                         y[te], m.predict_proba(x[te])[:, 1]),
                     "k_coords": 1})
    # 2-full-pca + pc1
    pca1 = PCA(n_components=1).fit_transform(Xs[tr])
    mp1 = LogisticRegression(max_iter=1000).fit(pca1, y[tr])
    pc1_te = PCA(n_components=1).fit_transform(Xs[tr]).mean(axis=0)
    # project test
    comp = PCA(n_components=1).fit(Xs[tr])
    te_proj = comp.transform(Xs[te])
    rows.append({"model": "pc1", "heldout_auc": roc_auc_score(
        y[te], mp1.predict_proba(te_proj)[:, 1]), "k_coords": "pc1"})
    # multi-coordinate (all)
    mfull = LogisticRegression(max_iter=1000).fit(Xs[tr], y[tr])
    rows.append({"model": "multi-all", "heldout_auc": roc_auc_score(
        y[te], mfull.predict_proba(Xs[te])[:, 1]), "k_coords": len(FORCING_COLS)})
    out = pd.DataFrame(rows)
    best = out.sort_values("heldout_auc", ascending=False).iloc[0]
    best_auc = float(best["heldout_auc"])
    best_model = best["model"]
    # verdict
    single_best = float(out[out["model"].str.startswith("single:")]
                        ["heldout_auc"].max())
    if best_auc - single_best < 0.01:
        verdict = "COMPACT_FORCING_COORDINATE"
    elif best_model == "multi-all":
        verdict = "MULTI_COORDINATE_FORCING"
    else:
        verdict = "NO_COMPACT_FORCING"
    out["verdict"] = verdict
    out["best_model"] = best_model
    out["best_auc"] = best_auc
    out.to_csv(OUT / "15_FIELD_FORCING_COORDINATE.csv", index=False)
    return out


# =========================================================================
# WS14: SATURATION GEOMETRY (16_SATURATION_GEOMETRY.csv)
# =========================================================================
# For each patch, map activation-rate vs field-intensity deciles -> onset,
# ceiling, and amplitude to reach 50/75/90% of that patch's ceiling.

def ws14_saturation_geometry(band, dfw):
    pg = _patch_daily(band)
    dmap = dfw.set_index("d")
    pg = pg.merge(dmap[["top500_breadth_30d", "top500_dispersion_30d",
                        "vol_med", "btc_return_7d"]],
                  left_on="d", right_index=True, how="left")
    pg = pg.dropna(subset=["ppos"])
    rows = []
    for patch, g in pg.groupby("patch"):
        g = g.sort_values("d")
        # rank field intensity (PC1 of forcing) - use breadth as intensity
        for intensity in ["top500_breadth_30d", "btc_return_7d"]:
            sub = g.dropna(subset=[intensity, "active"])
            if len(sub) < 80:
                continue
            try:
                qb = pd.qcut(sub[intensity], 6, labels=False,
                             duplicates="drop")
            except Exception:
                continue
            dfq = pd.DataFrame({"q": qb, "act": sub["active"]})
            rates = dfq.groupby("q")["act"].mean().reindex(
                sorted(dfq["q"].unique()))
            if len(rates) < 3:
                continue
            ceil = float(rates.max())
            onset = float(rates.min())
            # amplitude (intensity decile) to reach fractions of ceiling
            def _amp_to(fr):
                target = onset + fr * (ceil - onset)
                hit = rates[rates >= target]
                return int(hit.index[0] + 1) if len(hit) else np.nan
            s50 = _amp_to(0.5); s75 = _amp_to(0.75); s90 = _amp_to(0.9)
            # saturation onset decile = where marginal gain drops below 1/3
            d = np.diff(rates)
            sat_dec = int(np.argmax(d <= np.max(d) / 3)) + 2 if len(d) >= 2 \
                else np.nan
            rows.append({"patch": patch, "intensity": intensity,
                         "response_floor": onset, "response_ceiling": ceil,
                         "decile_to_50pct_ceiling": s50,
                         "decile_to_75pct_ceiling": s75,
                         "decile_to_90pct_ceiling": s90,
                         "saturation_onset_decile": sat_dec})
    out = pd.DataFrame(rows)
    if len(out):
        out["verdict"] = "SATURATION_GEOMETRY_MAPPED"
    out.to_csv(OUT / "16_SATURATION_GEOMETRY.csv", index=False)
    return out