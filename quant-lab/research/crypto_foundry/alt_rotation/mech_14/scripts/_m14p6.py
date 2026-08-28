from _m14base import *
from _m14base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split, _cohen_d, _auc_xy

MISSING = -1.0


def _unresolved_ratios(e):
    """Per-event unresolved-displacement ratio at horizons {1,3,7,14,30}D.

    unresolved(h) = |fwd_h_cum| / max(|ret_1d|, eps).  Absolute and sigma stay
    separate coordinates (governance).
    """
    init = e["ret_1d"].abs().replace(0, np.nan)
    out = {}
    for col, hc in [("fwd1_cum", 1), ("fwd3_cum", 3), ("fwd7_cum", 7),
                    ("fwd14_cum", 14), ("fwd30_cum", 30)]:
        if col in e.columns:
            ratio = e[col].abs() / init
            out[f"unresolved_{hc}d"] = ratio.clip(upper=10.0)
        else:
            out[f"unresolved_{hc}d"] = np.nan
    return out


# =========================================================================
# WS20: DISTURBANCE -> ABSORPTION -> RESIDUAL PILOT
#   (22_DISTURBANCE_ABSORPTION_RESIDUAL.csv)
# =========================================================================
# Framing:
#   DISTURBANCE = absolute move + sigma surprise  (contemporaneous shock size)
#   ABSORPTION  = reversal/recovery + normalization (claw-back in the near
#     window)
#   RESIDUAL    = unrecovered displacement + rank damage (what endures)
# Pilot:
#   * Durable-importance target measured at 14D (unresolved displacement AND
#     rank damage both above the event-level median).
#   * Features use information only through ~7D (shock at t0, absorption at
#     ~3D, residual at ~7D) so the 14D label is out-of-window.
#   * Purged chronological 80/20 held-out split: fit on the first 80% of
#     dates, evaluate on the last 20% (a 14-day buffer purges the boundary
#     so cumulative windows do not bleed label information across the split).
#   * Compare DISTURBANCE_ONLY vs FULL D->A->R held-out AUC.

def ws20_disturbance_absorption_residual(ev):
    e = ev.copy()
    e["d"] = pd.to_datetime(e["historical_date"]).dt.normalize()
    e = e.dropna(subset=["ret_1d", "z1", "reversal"]).copy()
    e["abs_move"] = e["ret_1d"].abs()
    e["sigma"] = e["z1"].abs()
    e["rev"] = (e["reversal"] == 1).astype(float)
    e["recovery3d"] = e["fwd3_cum"].clip(lower=0) if "fwd3_cum" in e else 0.0
    e["absorption"] = e["rev"] + e["recovery3d"] / (e["abs_move"] + 1e-9)
    r = _unresolved_ratios(e)
    e["unresolved7d"] = np.where(e["abs_move"] > 0,
                                 (e["fwd7_cum"].abs() / e["abs_move"]),
                                 np.nan)
    e["rank_damage_7"] = e["rank_vel_7d"].abs() if "rank_vel_7d" in e \
        else 0.0
    e["disp14"] = e["fwd14_cum"].abs()
    e["rank_damage_14"] = e["rank_vel_14d"].abs() if "rank_vel_14d" in e \
        else 0.0
    # durable importance at 14D
    med_d = float(e["disp14"].median())
    med_rd = float(e["rank_damage_14"].median())
    e["important"] = ((e["disp14"] > med_d) &
                      (e["rank_damage_14"] > med_rd)).astype(int)
    e = e.dropna(subset=["abs_move", "sigma", "important"]).copy()
    if e["important"].sum() < 50:
        out = pd.DataFrame([{"framing": "n/a",
                             "heldout_auc_durable_importance": np.nan,
                             "n_train": int(len(e)),
                             "n_test": int(len(e)),
                             "verdict": "DAR_PILOT_DATA_LIMITED"}])
        out.to_csv(OUT / "22_DISTURBANCE_ABSORPTION_RESIDUAL.csv",
                   index=False)
        return out
    e = e.sort_values("d").reset_index(drop=True)
    cut_date = e["d"].quantile(0.80)
    purge = pd.Timedelta(days=14)
    train = e[e["d"] < cut_date]
    test = e[(e["d"] >= cut_date + purge)]
    if len(train) < 200 or len(test) < 50 or test["important"].sum() < 30:
        out = pd.DataFrame([{"framing": "n/a",
                             "heldout_auc_durable_importance": np.nan,
                             "n_train": int(len(train)), "n_test": int(len(test)),
                             "verdict": "DAR_PILOT_DATA_LIMITED"}])
        out.to_csv(OUT / "22_DISTURBANCE_ABSORPTION_RESIDUAL.csv",
                   index=False)
        return out

    def _holdout(cols):
        ft = train[cols + ["important"]].replace([np.inf, -np.inf], np.nan)
        fe = test[cols + ["important"]].replace([np.inf, -np.inf], np.nan)
        ft = ft.dropna(); fe = fe.dropna()
        Xtr = ft[cols].to_numpy(dtype=float); ytr = ft["important"]
        Xte = fe[cols].to_numpy(dtype=float); yte = fe["important"]
        if len(Xtr) < 200 or len(Xte) < 50 or int(yte.sum()) < 30:
            return np.nan
        m = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
        return roc_auc_score(yte, m.predict_proba(Xte)[:, 1])

    DIST = ["abs_move", "sigma"]
    DAR_COLS = ["abs_move", "sigma", "absorption", "unresolved7d",
                "rank_damage_7"]
    auc_dist = float(_holdout(DIST))
    auc_dar = float(_holdout(DAR_COLS))
    rows = [
        {"framing": "DISTURBANCE_ONLY",
         "heldout_auc_durable_importance": auc_dist,
         "n_train": int(len(train)), "n_test": int(len(test)),
         "n_important_test": int(test["important"].sum())},
        {"framing": "DISTURBANCE_ABSORPTION_RESIDUAL",
         "heldout_auc_durable_importance": auc_dar,
         "n_train": int(len(train)), "n_test": int(len(test)),
         "n_important_test": int(test["important"].sum())},
    ]
    delta = auc_dar - auc_dist
    if delta >= 0.02:
        v = "DAR_FRAMING_BETTER_THAN_SHOCK_ALONE"
    elif delta >= 0:
        v = "DAR_FRAMING_COMPARABLE_TO_SHOCK_ALONE"
    elif auc_dist >= 0.56:
        v = "SHOCK_ALONE_STRONG_MATERIALITY"
    else:
        v = "DAR_PILOT_INCONCLUSIVE"
    rows.append({"framing": "DELTA",
                 "heldout_auc_durable_importance": delta,
                 "n_train": int(len(train)), "n_test": int(len(test)),
                 "verdict": v})
    out = pd.DataFrame(rows)
    if "verdict" not in out.columns:
        out["verdict"] = v
    out.to_csv(OUT / "22_DISTURBANCE_ABSORPTION_RESIDUAL.csv", index=False)
    return out


# =========================================================================
# WS21: RESIDUAL DISTURBANCE RATIO (23_RESIDUAL_DISTURBANCE.csv)
# =========================================================================
# Fraction of the initial disturbance still unresolved at 1/3/7/14/30D.
def ws21_residual_disturbance(ev):
    e = ev.copy().dropna(subset=["ret_1d"]).copy()
    r = _unresolved_ratios(e)
    for k, v in r.items():
        e[k] = v
    rows = []
    for hc in [1, 3, 7, 14, 30]:
        k = f"unresolved_{hc}d"
        col = e[k]
        q = col.quantile(0.25) if col.notna().any() else np.nan
        m = float(col.median()) if col.notna().any() else np.nan
        q3 = col.quantile(0.75) if col.notna().any() else np.nan
        rows.append({"horizon_days": hc, "median_unresolved_ratio": m,
                     "p25": float(q) if q == q else np.nan,
                     "p75": float(q3) if q3 == q3 else np.nan,
                     "RESIDUAL_DISTURBANCE_RATIO": m,
                     "n_events": int(col.notna().sum())})
    out = pd.DataFrame(rows)
    h1 = out["median_unresolved_ratio"].iloc[0]
    h14 = out["median_unresolved_ratio"].loc[out["horizon_days"] == 14].iloc[0]
    h30 = out["median_unresolved_ratio"].loc[out["horizon_days"] == 30].iloc[0]
    if (h1 == h1 and h30 == h30 and h30 < 0.5 * h1):
        out["verdict"] = "RESIDUAL_DECAYS_OVER_TIME"
    else:
        out["verdict"] = "RESIDUAL_PERSISTS"
    out.to_csv(OUT / "23_RESIDUAL_DISTURBANCE.csv", index=False)
    return out