from _m16base import *
from _m16base import _cache_step, _entropy, _fdr, _fmt, _slope_std, \
    _logit_slope, SUBPERIODS, AGE_BAND_ORDER
from scipy.stats import spearmanr, ranksums


# =========================================================================
# WS5: BIRTH GEOMETRY TRANSPORT (06_BIRTH_GEOMETRY_TRANSPORT.csv)
# =========================================================================
BIRTH_COORDS = {
    "breadth30": "top500_breadth_30d", "btc7": "btc_return_7d",
    "dispersion30": "top500_dispersion_30d",
    "eth_btc_rel7": "eth_btc_relative_return_7d",
    "concentration": "top3_share", "vol": "vol_med",
    "rank_depth": "rank_depth_rel", "leadership_width": "leadership_width",
    "breadth_vel": "breadth_vel",
}


def _auc_discrimination(x, y):
    """AUC of x>=median as discriminator of binary y (M14 convention)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 40 or y.sum() < 5 or (1 - y).sum() < 5:
        return np.nan
    try:
        clf = LogisticRegression(max_iter=1000).fit(x.reshape(-1, 1), y)
        return float(roc_auc_score(y, clf.predict_proba(x.reshape(-1, 1))
                                   [:, 1]))
    except Exception:
        return np.nan


def ws5_birth_geometry_transport(df):
    birth = df[df["age_in_cell"] == 1].copy()
    rows = []
    for cname, col in BIRTH_COORDS.items():
        aucs = {}
        for sp in SUBPERIODS:
            b = birth[birth["subperiod"] == sp]
            if len(b) < 40:
                aucs[sp] = np.nan
                continue
            aucs[sp] = _auc_discrimination(b[col].to_numpy(),
                                           b["prop7"].to_numpy())
        vals = np.array([aucs[sp] for sp in SUBPERIODS])
        vals = vals[~np.isnan(vals)]
        geom_drift = float(vals.max() - vals.min()) if len(vals) >= 3 \
            else np.nan
        # post-birth dynamics: top-quintile cohort success per subperiod
        q = birth[col].quantile(0.8) if birth[col].notna().sum() >= 80 \
            else np.nan
        post_rates = {}
        for sp in SUBPERIODS:
            b = birth[(birth["subperiod"] == sp) & (birth[col] >= q)] \
                if q == q else birth[birth["subperiod"] == sp]
            post_rates[sp] = float(b["prop7"].mean()) if len(b) >= 10 else \
                np.nan
        pv = np.array([post_rates[sp] for sp in SUBPERIODS])
        pv = pv[~np.isnan(pv)]
        post_drift = float(pv.max() - pv.min()) if len(pv) >= 3 else np.nan
        rows.append({"coordinate": cname, "column": col,
                     **{f"auc_{sp}": aucs[sp] for sp in SUBPERIODS},
                     "auc_range": geom_drift,
                     **{f"topQ_success_{sp}": post_rates[sp]
                        for sp in SUBPERIODS},
                     "post_drift_range": post_drift})
    out = pd.DataFrame(rows)
    # verdicts across all coordinates
    geom_ranges = out["auc_range"].dropna()
    post_ranges = out["post_drift_range"].dropna()
    geom_drifted = bool((geom_ranges >= 0.06).any()) if len(geom_ranges) \
        else False
    post_drifted = bool((post_ranges >= 0.06).any()) if len(post_ranges) \
        else False
    if geom_drifted and post_drifted:
        verdict = "BOTH"
    elif geom_drifted:
        verdict = "BIRTH_GEOMETRY_DRIFT"
    elif post_drifted:
        verdict = "POST_BIRTH_DYNAMICS_DRIFT"
    else:
        verdict = "NEITHER"
    out["verdict"] = verdict
    out["n_birth_days"] = int(len(birth))
    out.to_csv(OUT / "06_BIRTH_GEOMETRY_TRANSPORT.csv", index=False)
    return out


# =========================================================================
# WS6: STATE x AGE LAW TRANSPORTABILITY (07_STATE_AGE_TRANSPORT.csv)
# =========================================================================
def _age_trend(rates_by_band):
    """Rank correlation of rate vs age-band order. NaN if <3 bands valid."""
    idx = {b: i for i, b in enumerate(AGE_BAND_ORDER)}
    xs, ys = [], []
    for b, v in rates_by_band.items():
        if v == v and b in idx:
            xs.append(idx[b])
            ys.append(v)
    if len(xs) < 3 or np.std(ys) == 0:
        return np.nan
    return float(spearmanr(xs, ys)[0])


def ws6_state_age_transport(df):
    states = ["HH", "HL", "LH", "LL"]
    rows = []
    for st in states:
        sub = df[df["state_code"] == st]
        for ab in AGE_BAND_ORDER:
            g = sub[sub["ab"] == ab]
            for sp in SUBPERIODS:
                s = g[g["subperiod"] == sp]
                if len(s) < 15:
                    continue
                rows.append({"state": st, "age_band": ab, "subperiod": sp,
                             "n": int(len(s)),
                             "prop7": float(s["prop7"].mean()),
                             "ren7": float(s["ren7"].mean()),
                             "rank7": float(s["rank7"].mean()),
                             "exit_next": float((s["grp4s"] !=
                                                 s["grp4s_next"]).mean())
                             if s["grp4s_next"].notna().any() else np.nan,
                             "fbe": float(s["fbe"].mean())})
    out = pd.DataFrame(rows)
    # per-state age-trend sign per subperiod
    trend = []
    for st in states:
        sub = out[out["state"] == st]
        for sp in SUBPERIODS:
            s = sub[sub["subperiod"] == sp]
            if len(s) < 3:
                continue
            rb = dict(zip(s["age_band"], s["prop7"]))
            trend.append({"state": st, "subperiod": sp,
                          "age_prop_trend": _age_trend(rb),
                          "n_bands": int(len(s))})
    tr = pd.DataFrame(trend)
    # consistency per state: is the trend sign stable across subperiods?
    state_verdicts = []
    for st in states:
        t = tr[tr["state"] == st]["age_prop_trend"].dropna()
        if len(t) >= 3:
            pos = int((t > 0).sum())
            neg = int((t < 0).sum())
            frac = max(pos, neg) / len(t)
            sign = "POS" if pos > neg else "NEG" if neg > pos else "FLAT"
            stable = frac >= 0.8
        else:
            stable, sign, frac = False, "n/a", np.nan
        state_verdicts.append({"state": st, "trend_sign": sign,
                               "sign_consistent": stable,
                               "consistency_fraction": frac,
                               "mean_age_prop_trend": float(t.mean())
                               if len(t) else np.nan})
    sv = pd.DataFrame(state_verdicts)
    # global verdict
    n_consistent = int(sv["sign_consistent"].sum())
    signs = set(sv["trend_sign"])
    n_states_with_trend = int((sv["trend_sign"].isin(["POS", "NEG"])).sum())
    if n_states_with_trend < 3:
        verdict = "DATA_LIMITED_CLOCK"
    elif n_consistent >= max(3, int(0.8 * len(sv))) and len(signs) == 1 and \
            "n/a" not in signs:
        verdict = "INVARIANT_CLOCK"
    elif n_consistent >= max(3, int(0.8 * len(sv))) and len(signs) > 1:
        verdict = "STATE_LOCAL_CLOCK"
    elif n_consistent >= 2 and n_states_with_trend >= 2:
        verdict = "REGIME_MODULATED_CLOCK"
    else:
        verdict = "UNSTABLE_CLOCK"
    out["verdict"] = "STATE_AGE_TRANSPORT_DONE"
    sv["verdict"] = verdict
    full = pd.concat([out, tr.assign(age_band="", n=0),
                      sv.assign(age_band="", subperiod="", n=0)],
                     ignore_index=True)
    full.to_csv(OUT / "07_STATE_AGE_TRANSPORT.csv", index=False)
    return out, tr, sv, verdict


# =========================================================================
# WS7: SURVIVAL-CONDITIONED BRANCH CONTRACTION (08_SURVIVAL_BRANCH_CONTRACTION.csv)
# =========================================================================
SURVIVE_DAYS = [3, 5, 7, 10, 14, 21]


def ws7_survival_branch_contraction(df):
    rows = []
    for T in SURVIVE_DAYS:
        g = df[df["age_in_cell"] >= T]
        for sp in SUBPERIODS:
            s = g[g["subperiod"] == sp]
            if len(s) < 50:
                continue
            rows.append({"survival_days": T, "subperiod": sp,
                         "n": int(len(s)),
                         "mean_fbe": float(s["fbe"].mean()),
                         "mean_nbranch7": float(s["nbranch7"].dropna().mean()),
                         "median_age": float(s["age_in_cell"].median())})
    out = pd.DataFrame(rows)
    # per-subperiod slope of branch entropy vs survival threshold
    slopes = []
    for sp in SUBPERIODS:
        s = out[out["subperiod"] == sp].sort_values("survival_days")
        if len(s) < 4:
            continue
        x = s["survival_days"].to_numpy(dtype=float)
        y = s["mean_fbe"].to_numpy(dtype=float)
        m = ~(np.isnan(x) | np.isnan(y))
        if m.sum() < 3:
            continue
        c = np.polyfit(x[m], y[m], 1)
        slopes.append({"subperiod": sp, "fbe_vs_survival_slope":
                       float(c[0]), "n_thresholds": int(m.sum())})
    sl = pd.DataFrame(slopes)
    if len(sl):
        neg = int((sl["fbe_vs_survival_slope"] < 0).sum())
        frac = neg / len(sl)
        if frac == 1.0:
            verdict = "BRANCH_CONTRACTION_INVARIANT"
        elif frac >= 0.6:
            verdict = "BRANCH_CONTRACTION_PARTIAL"
        else:
            verdict = "BRANCH_CONTRACTION_NOT_INVARIANT"
    else:
        verdict = "DATA_LIMITED"
    out["verdict"] = "BRANCH_CONTRACTION_MAPPED"
    sl["verdict"] = verdict
    full = pd.concat([out, sl.assign(survival_days=0)], ignore_index=True)
    full.to_csv(OUT / "08_SURVIVAL_BRANCH_CONTRACTION.csv", index=False)
    return out, sl, verdict
