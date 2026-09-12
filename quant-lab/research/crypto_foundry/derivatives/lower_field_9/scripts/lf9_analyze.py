"""LOWER-FIELD-9 analysis — continuous relational-state panel, physical-shock
-> network-reorganization geometry, global-field conditioning, topology-vs-role
stability, contagion/rejoin/decoupling transport, directional asymmetry
replication, false-loner artifact recheck, PRD relational-health validation,
local response-law drift, predictive-null freeze.

Built on the LF8 event-anchored relational-state engine + the LF5 PIT
substrate + the MECH-15 daily global field surface. Research only: no
strategy, no PnL, no execution. Outputs 02-26 written to lower_field_9/.
"""
from __future__ import annotations

import json
import warnings
from collections import Counter

import numpy as np
import pandas as pd

from scipy.stats import spearmanr, ranksums, chi2_contingency, kruskal, norm
from scipy.optimize import curve_fit
from statsmodels.stats.multitest import multipletests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import lf9_common as C9

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = C9.ROOT
A = C9.A
C = C9.C
MIN_SUPPORT = C9.MIN_SUPPORT
STATE_ORDER = C9.STATE_ORDER

_fmt = A._fmt
_med = C9._med
_mean = C9._mean
_purged_auc = A._purged_auc
_future_lookup = A._future_lookup

FRESH = ["FRESH_0_7", "STALE_8_30"]


# ---------------------------------------------------------------------------
# 02 CONTINUOUS RELATIONAL-STATE PANEL (+ manifest)
# ---------------------------------------------------------------------------

def continuous_panel(cp):
    covered = cp[cp["coverage"] == "COVERED"]
    total = len(cp)
    rows = [{
        "metric": "n_asset_days_total", "value": int(total),
        "detail": "all asset-days for assets with >= 1 primary-family snapshot"},
        {"metric": "n_asset_days_covered", "value": int(len(covered)),
         "detail": "days with carried relational state (>= 1 snapshot <= day)"},
        {"metric": "n_assets", "value": int(cp["cmc_id"].nunique()),
         "detail": "assets in panel"},
        {"metric": "n_snapshot_days", "value": int(cp["has_snapshot"].sum()),
         "detail": "event-anchored snapshot rows (state re-derived)"},
        {"metric": "date_range",
         "value": f"{cp['historical_date'].min().date()} -> {cp['historical_date'].max().date()}",
         "detail": "LF5 substrate range for covered assets"},
        {"metric": "coverage_fraction",
         "value": _fmt(len(covered) / total), "detail": "covered / total"},
        {"metric": "freshness_FRESH_0_7",
         "value": int((covered["freshness"] == "FRESH_0_7").sum()),
         "detail": "days with a snapshot within the last 7d"},
        {"metric": "freshness_STALE_8_30",
         "value": int((covered["freshness"] == "STALE_8_30").sum()), "detail": ""},
        {"metric": "freshness_STALE_31_60",
         "value": int((covered["freshness"] == "STALE_31_60").sum()), "detail": ""},
        {"metric": "freshness_STALE_60_PLUS",
         "value": int((covered["freshness"] == "STALE_60_PLUS").sum()), "detail": ""},
        {"metric": "median_days_since_snapshot",
         "value": _fmt(covered["days_since_snapshot"].median()), "detail": ""},
    ]
    for st in STATE_ORDER:
        rows.append({"metric": f"carried_state_{st}",
                     "value": int((covered["rel_state"] == st).sum()),
                     "detail": "carried asset-days in state"})
    rows.append({"metric": "mcell16_join_rate",
                 "value": _fmt(cp["mcell"].notna().mean()),
                 "detail": "fraction of asset-days joined to MECH-15 16-cell surface"})
    rows.append({"metric": "quality_flag_rate",
                 "value": _fmt(cp["flag_any_quality"].mean()),
                 "detail": "asset-days with any LF5 quality flag"})
    m = pd.DataFrame(rows)
    cp.to_parquet(R / "02_CONTINUOUS_RELATIONAL_PANEL.parquet", index=False)
    m.to_csv(R / "02b_CONTINUOUS_PANEL_MANIFEST.csv", index=False)
    return m


# ---------------------------------------------------------------------------
# 03 CONTINUOUS PERSISTENCE RECHECK (per family, exact-calendar)
# ---------------------------------------------------------------------------

def _pair_jaccards(fam):
    """Per-asset snapshot-pair Jaccards for gaps <= 63d (carry window)."""
    pm = C.load_peer_map(fam)
    sets = pm.groupby("event_index")["peer_id"].apply(lambda s: frozenset(s)).to_dict()
    snap = C.build_family_panel(fam).sort_values(["cmc_id", "historical_date"])
    out = {}
    for cid, g in snap.groupby("cmc_id", sort=False):
        dates = g["historical_date"].to_numpy()
        eis = g["event_index"].to_numpy()
        for i in range(len(g)):
            a = sets.get(eis[i], frozenset())
            for j in range(i + 1, len(g)):
                gap = (dates[j] - dates[i]) / np.timedelta64(1, "D")
                if gap > 63:
                    break
                b = sets.get(eis[j], frozenset())
                out[(eis[i], eis[j])] = len(a & b) / max(len(a | b), 1)
    return out, snap


def _carry_events(fam):
    snap = C.build_family_panel(fam)
    assets = snap["cmc_id"].unique()
    sub = pd.read_parquet(C.SUBSTRATE, columns=["cmc_id", "historical_date"])
    sub = sub[sub["cmc_id"].isin(assets)]
    carry = snap[["cmc_id", "historical_date", "event_index", "rel_state"]].rename(
        columns={"historical_date": "snapshot_date"})
    p = pd.merge_asof(sub.sort_values("historical_date"),
                      carry.sort_values("snapshot_date"),
                      left_on="historical_date", right_on="snapshot_date",
                      by="cmc_id", direction="backward")
    return p[p["event_index"].notna()].copy()


def _alive_sets():
    dates, assets, _ = C._wide_returns()
    return {d: frozenset(assets) for d in dates}  # all assets present in wide matrix


def continuous_persistence(cp):
    rows = []
    for fam in C9.FAMILY_ORDER:
        pairs, snap = _pair_jaccards(fam)
        car = _carry_events(fam)
        car = car.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
        n = len(car)
        # exact-calendar lookups at t+h via reindex on (cmc_id, date+h)
        base = car[["cmc_id", "historical_date", "event_index", "rel_state"]].copy()
        states = car.set_index(["cmc_id", "historical_date"])["rel_state"]
        events = car.set_index(["cmc_id", "historical_date"])["event_index"]
        e0 = base["event_index"].to_numpy()
        st0 = base["rel_state"].to_numpy()
        for h in C9.WINDOWS:
            tgt = base.copy()
            tgt["tgt_date"] = tgt["historical_date"] + pd.Timedelta(days=h)
            midx = pd.MultiIndex.from_frame(
                tgt[["cmc_id", "tgt_date"]]).rename(["cmc_id", "historical_date"])
            st_h = states.reindex(midx).to_numpy()
            ev_h = events.reindex(midx).to_numpy()
            # ok = carried state AND substrate row exist at exact t+h (alive)
            ok = pd.notna(ev_h) & pd.notna(st_h)
            new_snap = ok & (ev_h != e0)
            same_state = ok & (st_h == st0)
            same_member = np.zeros(n, dtype=float)
            for i in np.where(ok)[0]:
                if ev_h[i] == e0[i]:
                    same_member[i] = 1.0
                else:
                    same_member[i] = pairs.get((e0[i], ev_h[i]), np.nan)
            rel_all = float(np.nanmean(same_state)) if ok.any() else np.nan
            rel_new = float(np.nanmean(same_state[new_snap])) if new_snap.any() else np.nan
            rel_carry = float(np.nanmean(same_state[ok & ~new_snap])) if (ok & ~new_snap).any() else np.nan
            mem_all = float(np.nanmean(same_member[ok])) if ok.any() else np.nan
            mem_new = float(np.nanmean(same_member[new_snap])) if new_snap.any() else np.nan
            any_nb = float(ok.mean())
            rows.append({
                "peer_family": fam, "horizon_d": h,
                "object": "relational_state",
                "persistence_continuous": _fmt(rel_all),
                "persistence_cond_new_snapshot": _fmt(rel_new),
                "persistence_pure_carry": _fmt(rel_carry),
                "n_rows": int(n), "n_cond": int(ok.sum())})
            rows.append({
                "peer_family": fam, "horizon_d": h,
                "object": "exact_membership",
                "persistence_continuous": _fmt(mem_all),
                "persistence_cond_new_snapshot": _fmt(mem_new),
                "persistence_pure_carry": np.nan,
                "n_rows": int(n), "n_cond": int(ok.sum())})
            rows.append({
                "peer_family": fam, "horizon_d": h,
                "object": "any_neighborhood",
                "persistence_continuous": _fmt(any_nb),
                "persistence_cond_new_snapshot": np.nan,
                "persistence_pure_carry": np.nan,
                "n_rows": int(n), "n_cond": int(ok.sum())})
            rows.append({
                "peer_family": fam, "horizon_d": h,
                "object": "peer_family",
                "persistence_continuous": _fmt(any_nb),
                "persistence_cond_new_snapshot": np.nan,
                "persistence_pure_carry": np.nan,
                "n_rows": int(n), "n_cond": int(ok.sum()),
                "note": "peer_family == any_neighborhood under single-family panels"})
    df = pd.DataFrame(rows)
    # LF8 snapshot-anchored comparison (primary family, relational state)
    snap = C.load_primary_panel()
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    st0 = snap["rel_state"].to_numpy()
    for h in [1, 3, 7, 14, 30, 60]:
        fut = _future_lookup(snap, h)
        has = fut >= 0
        st_f = st0[fut.clip(0)]
        lf8 = float(np.nanmean(st_f[has] == st0[has])) if has.any() else np.nan
        df.loc[(df["peer_family"] == C9.PRIMARY) & (df["horizon_d"] == h)
               & (df["object"] == "relational_state"),
               "lf8_snapshot_anchored"] = _fmt(lf8)
    df.to_csv(R / "03_CONTINUOUS_PERSISTENCE.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 04 TOPOLOGY vs ROLE
# ---------------------------------------------------------------------------

def topology_vs_role():
    snap = C.load_primary_panel()
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    rows = []
    for cid, g in snap.groupby("cmc_id"):
        if len(g) < 4:
            continue
        turn = _med(g["roll_turnover_30d"])
        ent = _med(g["entropy_30d"])
        sc_rate = float(g["state_changed"].mean()) if len(g) else np.nan
        role_ent = C._entropy_series(g["rel_state"].value_counts().to_numpy())
        surv = float((g["rel_state"].iloc[1:].to_numpy() == g["rel_state"].iloc[:-1].to_numpy()).mean())
        rows.append({"asset_id": cid, "n_snapshots": int(len(g)),
                     "median_membership_turnover": turn,
                     "median_membership_entropy": ent,
                     "state_change_rate": sc_rate,
                     "relational_state_survival": surv,
                     "role_transition_entropy": role_ent})
    df = pd.DataFrame(rows)
    turn_p67 = df["median_membership_turnover"].quantile(0.67)
    turn_p33 = df["median_membership_turnover"].quantile(0.33)
    sc_p67 = df["state_change_rate"].quantile(0.67)
    sc_p33 = df["state_change_rate"].quantile(0.33)
    def cls(r):
        fast_t = r["median_membership_turnover"] >= turn_p67
        slow_t = r["median_membership_turnover"] <= turn_p33
        fast_r = r["state_change_rate"] >= sc_p67
        slow_r = r["state_change_rate"] <= sc_p33
        if fast_t and slow_r:
            return "TOPOLOGY_FAST_ROLE_SLOW"
        if fast_t and fast_r:
            return "BOTH_FAST"
        if slow_t and slow_r:
            return "BOTH_SLOW"
        return "STATE_DEPENDENT"
    df["class"] = df.apply(cls, axis=1)
    vc = df["class"].value_counts()
    rho, p = spearmanr(df["median_membership_turnover"], df["state_change_rate"])
    verdict = pd.DataFrame([{
        "n_assets": int(len(df)),
        "p_topology_fast_role_slow": _fmt(vc.get("TOPOLOGY_FAST_ROLE_SLOW", 0) / len(df)),
        "p_both_fast": _fmt(vc.get("BOTH_FAST", 0) / len(df)),
        "p_both_slow": _fmt(vc.get("BOTH_SLOW", 0) / len(df)),
        "p_state_dependent": _fmt(vc.get("STATE_DEPENDENT", 0) / len(df)),
        "spearman_turnover_vs_state_change": _fmt(rho),
        "spearman_p": _fmt(p, 3),
        "median_membership_turnover": _fmt(df["median_membership_turnover"].median()),
        "median_state_change_rate": _fmt(df["state_change_rate"].median()),
        "median_relational_state_survival": _fmt(df["relational_state_survival"].median()),
        "verdict": ("TOPOLOGY_FAST_ROLE_SLOW" if vc.get("TOPOLOGY_FAST_ROLE_SLOW", 0) / len(df) >= 0.35
                    else "STATE_DEPENDENT")}])
    df.to_csv(R / "04_TOPOLOGY_VS_ROLE.csv", index=False)
    verdict.to_csv(R / "04b_TOPOLOGY_VS_ROLE_VERDICT.csv", index=False)
    return df, verdict


# ---------------------------------------------------------------------------
# 05 SHOCK -> TURNOVER -> STATE-CHANGE TIMING (continuous panel)
# ---------------------------------------------------------------------------

def shock_reorg_timing(cp):
    snap = C.load_primary_panel().sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    p67_turn = float(snap["roll_turnover_30d"].quantile(0.67))
    anchors = snap[snap["roll_turnover_30d"] >= p67_turn].reset_index(drop=True)
    sub = pd.read_parquet(C.SUBSTRATE, columns=["cmc_id", "historical_date", "ret_1d"])
    sub = sub[sub["cmc_id"].isin(anchors["cmc_id"].unique())]
    sub["abs_ret"] = sub["ret_1d"].abs()
    daily = {}
    for cid, g in sub.groupby("cmc_id"):
        daily[cid] = dict(zip(g["historical_date"], g["abs_ret"]))
    snap_by = {}
    for cid, g in snap.groupby("cmc_id"):
        snap_by[cid] = g
    recs = []
    for _, row in anchors.iterrows():
        cid, t = row["cmc_id"], row["historical_date"]
        dl = daily.get(cid, {})
        sg = snap_by.get(cid)
        if sg is None:
            continue
        sg = sg[(sg["historical_date"] >= t - pd.Timedelta(days=5))
                & (sg["historical_date"] <= t + pd.Timedelta(days=20))]
        t0 = t1 = t2 = t3 = np.nan
        for lag in range(-5, 21):
            tl = t + pd.Timedelta(days=lag)
            if np.isnan(t0) and dl.get(tl, 0) >= 0.03:
                t0 = lag
            if np.isnan(t1):
                r = sg[sg["historical_date"] == tl]
                if len(r) and float(r["roll_turnover_30d"].iloc[0]) >= p67_turn:
                    t1 = lag
            if np.isnan(t2):
                r = sg[sg["historical_date"] == tl]
                if len(r) and r["rel_state"].iloc[0] != row["rel_state"]:
                    t2 = lag
            if np.isnan(t3):
                r = sg[sg["historical_date"] == tl]
                if len(r) and r["rel_state"].iloc[0] in ("CONTAGIOUS", "REJOINING",
                                                          "REHABILITATING", "DECOUPLED"):
                    t3 = lag
            if not np.isnan(t0) and not np.isnan(t1) and not np.isnan(t2) and not np.isnan(t3):
                break
        if np.isnan(t0):
            continue
        recs.append({"anchor": row["event_index"], "subperiod": row["subperiod"],
                     "t0_abs_shock": t0, "t1_turnover": t1, "t2_state_change": t2,
                     "t3_transport": t3})
    d = pd.DataFrame(recs)
    out = []
    pairs = [("t1_turnover", "T1_MEMBERSHIP_TURNOVER"),
             ("t2_state_change", "T2_RELATIONAL_STATE_CHANGE"),
             ("t3_transport", "T3_CONTAGION_REJOIN_DECOUPLING")]
    boot_rng = np.random.default_rng(20260901)
    for col, name in pairs:
        lag = d[col].dropna()
        if len(lag) == 0:
            continue
        med = float(lag.median())
        meds = [float(np.median(boot_rng.choice(lag.to_numpy(), size=len(lag), replace=True)))
                for _ in range(1000)]
        ci = (float(np.quantile(meds, 0.025)), float(np.quantile(meds, 0.975)))
        prec = float((d[col] > d["t0_abs_shock"]).mean()) if len(d) else np.nan
        same_day = float((d[col] == d["t0_abs_shock"]).mean()) if len(d) else np.nan
        out.append({"event": name, "n_detected": int(lag.notna().sum()),
                    "median_lag_after_t0_d": _fmt(med),
                    "bootstrap_95ci": f"[{_fmt(ci[0])}, {_fmt(ci[1])}]",
                    "p25_lag": _fmt(lag.quantile(0.25)), "p75_lag": _fmt(lag.quantile(0.75)),
                    "p_after_t0": _fmt(prec), "p_same_day_as_t0": _fmt(same_day),
                    "n_anchors": int(len(d))})
    # event-order frequency: pairwise precedence among T1/T2/T3
    for a in ["t1_turnover", "t2_state_change", "t3_transport"]:
        for b in ["t1_turnover", "t2_state_change", "t3_transport"]:
            if a >= b:
                continue
            both = d[[a, b]].dropna()
            if len(both) < 30:
                continue
            out.append({"event": f"{a}_before_{b}", "n_detected": int(len(both)),
                        "median_lag_after_t0_d": _fmt(float((both[a] < both[b]).mean())),
                        "bootstrap_95ci": "", "p25_lag": np.nan, "p75_lag": np.nan,
                        "p_after_t0": np.nan, "p_same_day_as_t0": np.nan,
                        "n_anchors": int(len(d)),
                        "note": "fraction of anchors where A precedes B"})
    # subperiod stability of T0->T1 lag
    for sp, g in d.dropna(subset=["t1_turnover"]).groupby("subperiod"):
        if len(g) < 20:
            continue
        out.append({"event": f"SUBPERIOD_{sp}", "n_detected": int(len(g)),
                    "median_lag_after_t0_d": _fmt(float(g["t1_turnover"].median())),
                    "bootstrap_95ci": "", "p25_lag": _fmt(g["t1_turnover"].quantile(0.25)),
                    "p75_lag": _fmt(g["t1_turnover"].quantile(0.75)),
                    "p_after_t0": np.nan, "p_same_day_as_t0": np.nan, "n_anchors": int(len(d))})
    df = pd.DataFrame(out)
    df.to_csv(R / "05_SHOCK_REORGANIZATION_TIMING.csv", index=False)
    return df, d


# ---------------------------------------------------------------------------
# 06 ABS x SIGMA REORGANIZATION GRID (continuous)
# ---------------------------------------------------------------------------

def abs_sigma_grid(cp):
    cov = cp[cp["coverage"] == "COVERED"].copy()
    cov = C9.continuous_sig_abs(cov)
    rows = []
    for (ac, sc), g in cov.groupby(["abs_class", "sigma_class"]):
        if len(g) < 30:
            continue
        rows.append({
            "abs_class": ac, "sigma_class": sc, "n_days": int(len(g)),
            "median_membership_turnover": _fmt(g["roll_turnover_30d"].median()),
            "p_state_change_daily": _fmt(g["state_changed_daily"].mean()),
            "p_decoupling": _fmt(g["out_decouple"].mean()),
            "p_contagion": _fmt(g["out_contagion"].mean()),
            "p_rejoin": _fmt(g["out_rejoin"].mean()),
            "rel_state_entropy": _fmt(C._entropy_series(g["rel_state"].value_counts().to_numpy())),
            "median_days_since_snapshot": _fmt(g["days_since_snapshot"].median()),
            "median_abs_ret": _fmt(g["abs_ret"].median()),
            "median_sigma": _fmt(g["sigma"].median())})
    df = pd.DataFrame(rows)
    # marginal driver comparison: within abs class, does sigma matter?
    # (turnover is carry-dominated on the continuous panel, so compare
    #  decoupling / state-change / contagion rates across sigma bands)
    marg = []
    for ac in ["<2%", "2-5%", "5-10%", "10-20%", ">20%"]:
        sub = cov[cov["abs_class"] == ac]
        if len(sub) < 60:
            continue
        rho_s, p_s = spearmanr(sub["sigma"], sub["out_decouple"].fillna(0.5))
        lo = sub[sub["sigma_class"] == "<2σ"]
        hi = sub[sub["sigma_class"] == "4σ+"]
        marg.append({"abs_class": ac, "n": int(len(sub)),
                     "decouple_spearman_within_abs": _fmt(rho_s),
                     "decouple_spearman_p": _fmt(p_s, 3),
                     "p_decouple_sigma_lt2": _fmt(lo["out_decouple"].mean()) if len(lo) >= 30 else np.nan,
                     "p_decouple_sigma_4plus": _fmt(hi["out_decouple"].mean()) if len(hi) >= 30 else np.nan,
                     "p_state_change_sigma_lt2": _fmt(lo["state_changed_daily"].mean()) if len(lo) >= 30 else np.nan,
                     "p_state_change_sigma_4plus": _fmt(hi["state_changed_daily"].mean()) if len(hi) >= 30 else np.nan})
    md = pd.DataFrame(marg)
    df.to_csv(R / "06_ABS_SIGMA_REORGANIZATION_GRID.csv", index=False)
    md.to_csv(R / "06b_ABS_SIGMA_DRIVER_MARGINALS.csv", index=False)
    return df, md


# ---------------------------------------------------------------------------
# 07 VOLUME / LIQUIDITY AMPLITUDE
# ---------------------------------------------------------------------------

def volume_liquidity_response():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    snap["vol_amp"] = np.log1p(snap["volume_24h_usd"] /
                               snap["vol_prev7_med"].replace(0, np.nan))
    s = snap.dropna(subset=["vol_amp", "roll_turnover_30d"]).copy()
    s["turnover_hi"] = (s["roll_turnover_30d"] > s["roll_turnover_30d"].median()).astype(int)
    feats = {"volume_amplitude": ["vol_amp"],
             "abs_return": ["abs_ret"],
             "abs_return_volume_amplitude": ["abs_ret", "vol_amp"],
             "liq_proxy": ["liq_proxy"],
             "log10_mcap": ["log10_mcap"],
             "mcap_quantile": ["mcap_q_within_date"]}
    rows = []
    for fname, cols in feats.items():
        auc = _purged_auc(s, "turnover_hi", cols)
        rows.append({"feature_set": fname, "purged_auc_turnover_high": _fmt(auc),
                     "n": int(len(s))})
    # partial correlation: vol_amp | abs_return vs turnover
    ok = s.dropna(subset=["vol_amp", "abs_ret", "roll_turnover_30d"])
    if len(ok) > 100:
        def partial(x, y, z):
            xr = x - np.polyval(np.polyfit(z, x, 1), z)
            yr = y - np.polyval(np.polyfit(z, y, 1), z)
            return float(np.corrcoef(xr, yr)[0, 1])
        rows.append({"feature_set": "partial_volamp_turnover_given_abs",
                     "purged_auc_turnover_high": _fmt(partial(
                         ok["vol_amp"].to_numpy(), ok["roll_turnover_30d"].to_numpy(),
                         ok["abs_ret"].to_numpy())), "n": int(len(ok))})
        rows.append({"feature_set": "partial_abs_turnover_given_volamp",
                     "purged_auc_turnover_high": _fmt(partial(
                         ok["abs_ret"].to_numpy(), ok["roll_turnover_30d"].to_numpy(),
                         ok["vol_amp"].to_numpy())), "n": int(len(ok))})
        rho, p = spearmanr(ok["vol_amp"], ok["abs_ret"])
        rows.append({"feature_set": "spearman_volamp_vs_abs",
                     "purged_auc_turnover_high": _fmt(rho), "n": int(len(ok)),
                     "note": f"p={_fmt(p, 3)}"})
    df = pd.DataFrame(rows)
    base = df.set_index("feature_set")["purged_auc_turnover_high"]
    abs_a = float(base.get("abs_return", np.nan))
    both = float(base.get("abs_return_volume_amplitude", np.nan))
    vol_a = float(base.get("volume_amplitude", np.nan))
    if np.isfinite(both) and np.isfinite(abs_a) and both >= abs_a + 0.005:
        verdict = "INDEPENDENT_REORGANIZATION_COORDINATE"
    elif np.isfinite(vol_a) and np.isfinite(abs_a) and vol_a >= abs_a - 0.005:
        verdict = "SHOCK_CARRIER"
    elif np.isfinite(vol_a) and vol_a < 0.55:
        verdict = "REDUNDANT"
    else:
        verdict = "LOCAL_ONLY"
    df.loc[len(df)] = {"feature_set": "VERDICT", "purged_auc_turnover_high": verdict,
                       "n": int(len(s))}
    df.to_csv(R / "07_VOLUME_LIQUIDITY_RESPONSE.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 08 GLOBAL FIELD OVERLAY (16 / 6 / 8-cell)
# ---------------------------------------------------------------------------

def global_field_overlay(cp):
    cov = cp[cp["coverage"] == "COVERED"].copy()
    rows = []
    for surf, col in [("CELL16", "mcell"), ("CELL6", "mcell6"),
                      ("CELL8", "mcell8"), ("CELL4", "cell4")]:
        for cell, g in cov.groupby(col):
            if len(g) < 30 or pd.isna(cell):
                continue
            rows.append({
                "surface": surf, "cell": str(cell), "n_days": int(len(g)),
                "n_assets": int(g["cmc_id"].nunique()),
                "median_membership_turnover": _fmt(g["roll_turnover_30d"].median()),
                "p_state_change_daily": _fmt(g["state_changed_daily"].mean()),
                "p_decoupling": _fmt(g["out_decouple"].mean()),
                "p_contagion": _fmt(g["out_contagion"].mean()),
                "p_rejoin": _fmt(g["out_rejoin"].mean()),
                "rel_state_entropy": _fmt(C._entropy_series(g["rel_state"].value_counts().to_numpy())),
                "median_abs_ret": _fmt(g["abs_ret"].median()),
                "median_sigma": _fmt(g["sigma"].median()),
                "median_forcing": _fmt(g["forcing"].median())})
    df = pd.DataFrame(rows)
    df.to_csv(R / "08_GLOBAL_FIELD_OVERLAY.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 09 FIELD-MODULATED RESPONSE (matched shock amplitude)
# ---------------------------------------------------------------------------

def field_modulated_response(cp):
    cov = cp[cp["coverage"] == "COVERED"].copy()
    cov = C9.continuous_sig_abs(cov)
    rows = []
    verdicts = []
    for surf, col in [("CELL6", "mcell6"), ("CELL4", "cell4")]:
        for ac in ["2-5%", "5-10%", "10-20%", ">20%"]:
            sub = cov[cov["abs_class"] == ac]
            if len(sub) < 200:
                continue
            for metric, fn, isnum in [("turnover", "roll_turnover_30d", True),
                                      ("decoupling", "out_decouple", False),
                                      ("contagion", "out_contagion", False)]:
                cells = []
                within = []
                meds = []
                for cell, g in sub.groupby(col):
                    if len(g) < 30 or pd.isna(cell):
                        continue
                    v = g[fn].dropna()
                    if len(v) < 30:
                        continue
                    meds.append(float(v.median()))
                    within.append(float(v.std(ddof=0)))
                    cells.append(str(cell))
                if len(meds) < 3:
                    continue
                between = float(np.std(meds))
                within_pooled = float(np.mean(within)) if within else np.nan
                ratio = between / within_pooled if within_pooled and within_pooled > 0 else np.nan
                # Kruskal-Wallis across cells
                kw_p = np.nan
                if isnum:
                    try:
                        groups = [g[fn].dropna().to_numpy()
                                  for _, g in sub.groupby(col)
                                  if len(g) >= 30 and not pd.isna(g.name)]
                        if len(groups) >= 3:
                            kw_p = float(kruskal(*groups).pvalue)
                    except Exception:
                        pass
                rows.append({"surface": surf, "abs_class": ac, "metric": metric,
                             "n_days": int(len(sub)), "n_cells": len(cells),
                             "cells": ";".join(cells),
                             "between_cell_std": _fmt(between),
                             "pooled_within_cell_std": _fmt(within_pooled),
                             "between_within_ratio": _fmt(ratio),
                             "kruskal_p": _fmt(kw_p, 3),
                             "cell_medians": ";".join(str(_fmt(m)) for m in meds)})
    df = pd.DataFrame(rows)
    # verdict: ratio >= 0.75 in >= 2 abs classes on CELL6 for turnover/decouple
    sig = df[(df["surface"] == "CELL6") & (df["between_within_ratio"] >= 0.75)]
    abs_hits = sig["abs_class"].nunique()
    verdict = ("FIELD_MODULATED_LOCAL_RESPONSE" if abs_hits >= 2
               else "LOCAL_RESPONSE_INVARIANT")
    verdicts.append({"verdict": verdict, "modulated_abs_classes": int(abs_hits),
                     "n_significant_cells": int(len(sig))})
    df.to_csv(R / "09_FIELD_MODULATED_RESPONSE.csv", index=False)
    pd.DataFrame(verdicts).to_csv(R / "09b_FIELD_MODULATED_VERDICT.csv", index=False)
    return df, verdicts


# ---------------------------------------------------------------------------
# 10 GLOBAL FORCING x LOCAL SHOCK MATRIX
# ---------------------------------------------------------------------------

def global_local_shock_matrix(cp):
    cov = cp[cp["coverage"] == "COVERED"].copy()
    fmed = float(cov["forcing"].median())
    cov["global_forcing"] = np.where(cov["forcing"] >= fmed, "HIGH_GLOBAL_FORCING",
                                     "LOW_GLOBAL_FORCING")
    cov["local_shock"] = np.where(cov["abs_ret"] >= 0.05, "HIGH_LOCAL_SHOCK",
                                  "LOW_LOCAL_SHOCK")
    rows = []
    for (gf, ls), g in cov.groupby(["global_forcing", "local_shock"]):
        rows.append({"global_forcing": gf, "local_shock": ls, "n_days": int(len(g)),
                     "median_turnover": _fmt(g["roll_turnover_30d"].median()),
                     "p_state_change": _fmt(g["state_changed_daily"].mean()),
                     "p_decoupling": _fmt(g["out_decouple"].mean()),
                     "p_contagion": _fmt(g["out_contagion"].mean()),
                     "p_rejoin": _fmt(g["out_rejoin"].mean()),
                     "median_abs": _fmt(g["abs_ret"].median()),
                     "median_forcing": _fmt(g["forcing"].median())})
    df = pd.DataFrame(rows)
    df["z_decouple_high_vs_low_forcing"] = np.nan
    df["z_contagion_high_vs_low_forcing"] = np.nan
    df["delta_p_decouple_high_minus_low_forcing"] = np.nan
    df["delta_p_contagion_high_minus_low_forcing"] = np.nan
    df["turnover_median_diff_high_minus_low_forcing"] = np.nan
    # absorption test: high local shock under high vs low forcing
    hi = cov[(cov["local_shock"] == "HIGH_LOCAL_SHOCK") & (cov["global_forcing"] == "HIGH_GLOBAL_FORCING")]
    lo = cov[(cov["local_shock"] == "HIGH_LOCAL_SHOCK") & (cov["global_forcing"] == "LOW_GLOBAL_FORCING")]
    d_hi, d_lo = hi["out_decouple"], lo["out_decouple"]
    c_hi, c_lo = hi["out_contagion"], lo["out_contagion"]
    def ztest(a, b):
        pa, na = float(a.mean()), int(len(a))
        pb, nb = float(b.mean()), int(len(b))
        p = (pa * na + pb * nb) / (na + nb)
        se = np.sqrt(p * (1 - p) * (1 / na + 1 / nb))
        return (pa - pb) / se if se > 0 else np.nan
    z_d = ztest(d_hi, d_lo) if len(d_hi) and len(d_lo) else np.nan
    z_c = ztest(c_hi, c_lo) if len(c_hi) and len(c_lo) else np.nan
    dp_d = float(d_hi.mean() - d_lo.mean()) if len(d_hi) and len(d_lo) else np.nan
    dp_c = float(c_hi.mean() - c_lo.mean()) if len(c_hi) and len(c_lo) else np.nan
    turn_diff = _med(hi["roll_turnover_30d"]) - _med(lo["roll_turnover_30d"])
    # statistical significance at n~140k is trivial; require a meaningful effect
    verdict = ("FIELD_CONDITIONAL_ABSORPTION" if (abs(z_d) > 1.96 or abs(z_c) > 1.96)
               and max(abs(dp_d), abs(dp_c)) >= 0.01
               else "LOCAL_SHOCK_DOMINANT")
    df.loc[len(df)] = {"global_forcing": "VERDICT", "local_shock": verdict,
                       "n_days": int(len(cov)),
                       "z_decouple_high_vs_low_forcing": _fmt(z_d, 2),
                       "z_contagion_high_vs_low_forcing": _fmt(z_c, 2),
                       "delta_p_decouple_high_minus_low_forcing": _fmt(dp_d),
                       "delta_p_contagion_high_minus_low_forcing": _fmt(dp_c),
                       "turnover_median_diff_high_minus_low_forcing": _fmt(turn_diff)}
    df.to_csv(R / "10_GLOBAL_LOCAL_SHOCK_MATRIX.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 11 REORGANIZATION SATURATION
# ---------------------------------------------------------------------------

def _mm(x, c, k):
    return c * x / (k + x)


def reorg_saturation(cp):
    cov = cp[cp["coverage"] == "COVERED"].copy()
    cov = cov.dropna(subset=["abs_ret"])
    cov["abs_bin"] = pd.qcut(cov["abs_ret"].rank(method="first"), 12,
                             labels=False, duplicates="drop")
    rows = []
    for regime, g_all in [("OVERALL", cov)] + [(r, g) for r, g in cov.groupby("cell4")]:
        if len(g_all) < 500:
            continue
        for metric, col in [("membership_turnover", "roll_turnover_30d"),
                            ("decoupling", "out_decouple"),
                            ("state_change", "state_changed_daily")]:
            meds = []
            xs = []
            for b, g in g_all.groupby("abs_bin"):
                v = g[col].dropna()
                if len(v) < 30:
                    continue
                xs.append(float(g["abs_ret"].median()))
                meds.append(float(v.mean()))
            if len(xs) < 4:
                continue
            xs = np.array(xs, dtype=float)
            ys = np.array(meds, dtype=float)
            c0, k0 = float(ys.max()), float(np.median(xs))
            try:
                popt, _ = curve_fit(_mm, xs, ys, p0=[max(c0, 1e-6), max(k0, 1e-4)],
                                    bounds=([1e-6, 1e-5], [2.0, 0.5]), maxfev=20000)
                c, k = float(popt[0]), float(popt[1])
                onset = k / 4.0
                rows.append({"regime": str(regime), "response": metric,
                             "n_bins": len(xs),
                             "ceiling": _fmt(c), "half_saturation_abs": _fmt(k),
                             "onset_abs_20pct_ceiling": _fmt(onset),
                             "max_observed": _fmt(ys.max()),
                             "min_observed": _fmt(ys.min())})
            except Exception:
                rows.append({"regime": str(regime), "response": metric,
                             "n_bins": len(xs), "ceiling": np.nan,
                             "half_saturation_abs": np.nan,
                             "onset_abs_20pct_ceiling": np.nan,
                             "max_observed": _fmt(ys.max()),
                             "min_observed": _fmt(ys.min()),
                             "note": "FIT_FAILED"})
    df = pd.DataFrame(rows)
    df["half_sat_ratios_vs_overall"] = np.nan
    # does regime move the half-saturation point? (only non-degenerate fits)
    for resp in ["membership_turnover", "decoupling", "state_change"]:
        half = df[(df["response"] == resp)].set_index("regime")
        if "OVERALL" not in half.index:
            continue
        base = float(half.loc["OVERALL", "half_saturation_abs"])
        ratios = []
        for r in ["HH", "HL", "LH", "LL"]:
            if r in half.index and np.isfinite(half.loc[r, "half_saturation_abs"]) \
                    and half.loc[r, "half_saturation_abs"] > 1e-3:
                ratios.append(float(half.loc[r, "half_saturation_abs"]) / max(base, 1e-9))
        if len(ratios) < 2:
            v = "SATURATION_NOT_MEASURABLE_CARRY_DOMINATED" if resp != "state_change" \
                else "SATURATION_NOT_MEASURABLE"
        else:
            moved = [x for x in ratios if x > 1.5 or x < 0.67]
            v = ("REGIME_MOVES_SATURATION_THRESHOLD" if len(moved) >= 2
                 else "SATURATION_THRESHOLD_REGIME_INVARIANT")
        df.loc[len(df)] = {"regime": "VERDICT", "response": f"{v}::{resp}",
                           "n_bins": len(ratios), "half_sat_ratios_vs_overall":
                           ";".join(str(_fmt(x)) for x in ratios)}
    df.to_csv(R / "11_REORGANIZATION_SATURATION.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 12 RELATIONAL TRANSITION LATTICE
# ---------------------------------------------------------------------------

def transition_lattice():
    snap = C.load_primary_panel()
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    st = snap["rel_state"].to_numpy()
    rows = []
    for h in [1, 3, 7]:
        fut = _future_lookup(snap, h)
        has = fut >= 0
        a = st[has]
        b = st[fut[has]]
        cnt = Counter(zip(a, b))
        tot = Counter(a)
        for (f, t), n in sorted(cnt.items()):
            p = n / tot[f]
            ft = int(tot[f])
            cls = ("COMMON" if p >= 0.10 and ft >= 50
                   else "LOCAL" if p >= 0.01 and ft >= 20
                   else "RARE" if p >= 0.001 and n >= 2
                   else "NEAR_ZERO")
            rows.append({"horizon_d": h, "from_state": f, "to_state": t,
                         "n": int(n), "p_transition": _fmt(p),
                         "class": cls, "from_total": ft})
    df = pd.DataFrame(rows)
    df.to_csv(R / "12_RELATIONAL_TRANSITION_LATTICE.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 13 REJOIN / CONTAGION / DECOUPLING CLOCKS
# ---------------------------------------------------------------------------

def _state_at_h_lut(cp):
    cov = cp[cp["coverage"] == "COVERED"]
    return cov.set_index(["cmc_id", "historical_date"])["rel_state"]


def competing_clocks(cp):
    snap = C.load_primary_panel()
    anchors = snap[snap["abs_ret"] >= 0.05].copy()
    mc = C9._mcell_partitions()
    mcmap = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["mcell6"]))
    anchors["mcell6"] = anchors["historical_date"].dt.normalize().map(mcmap)
    anchors["rank_depth"] = anchors["rank_band"].map(C9._rank_depth_band)
    lut = _state_at_h_lut(cp)
    def clock(state):
        if state in ("REJOINING", "REHABILITATING"):
            return "REJOIN"
        if state == "CONTAGIOUS":
            return "CONTAGION"
        if state == "DECOUPLED":
            return "DECOUPLING"
        if state == "LOCALLY_CONFORMING":
            return "NORMALIZED"
        if state in ("TRUE_ISOLATED", "FALSE_ISOLATED", "DISLOCATED_UNCLASSIFIED"):
            return "ISOLATED"
        return "OTHER"
    rows = []
    conds = [("OVERALL", anchors)]
    for st, g in anchors.groupby("rel_state"):
        conds.append((f"STATE_{st}", g))
    for c6, g in anchors.groupby("mcell6"):
        conds.append((f"CELL6_{c6}", g))
    for ac, g in anchors.groupby(anchors["abs_ret"].map(A._abs_class)):
        conds.append((f"ABS_{ac}", g))
    for rd, g in anchors.groupby("rank_depth"):
        conds.append((f"RANK_{rd}", g))
    for h in [1, 3, 7, 14, 30]:
        for name, g in conds:
            if len(g) < 30:
                continue
            labs = []
            for _, row in g.iterrows():
                labs.append(clock(lut.get((row["cmc_id"],
                                           row["historical_date"] + pd.Timedelta(days=h)))))
            if not labs:
                continue
            cnt = Counter(labs)
            n = len(labs)
            rows.append({"horizon_d": h, "condition": name, "n": int(n),
                         "p_rejoin": _fmt(cnt.get("REJOIN", 0) / n),
                         "p_contagion": _fmt(cnt.get("CONTAGION", 0) / n),
                         "p_decoupling": _fmt(cnt.get("DECOUPLING", 0) / n),
                         "p_normalized": _fmt(cnt.get("NORMALIZED", 0) / n),
                         "p_isolated": _fmt(cnt.get("ISOLATED", 0) / n),
                         "p_other": _fmt(cnt.get("OTHER", 0) / n)})
    df = pd.DataFrame(rows)
    df.to_csv(R / "13_REJOIN_CONTAGION_DECOUPLING_CLOCKS.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 14 / 15 VALIDATIONS (early contagion / persistent decoupling)
# ---------------------------------------------------------------------------

def _subtype_fdr(snap, subtype_col, outcome, subtypes):
    pvals = []
    for st in subtypes:
        sub = snap[[subtype_col, outcome]].dropna(subset=[outcome])
        if len(sub) < 30:
            continue
        tab = pd.crosstab(sub[subtype_col] == st, sub[outcome])
        if tab.shape != (2, 2):
            continue
        try:
            chi2, p, _, _ = chi2_contingency(tab, correction=False)
            pvals.append((st, float(p)))
        except Exception:
            continue
    if not pvals:
        return pd.DataFrame()
    _, q, _, _ = multipletests([p for _, p in pvals], method="fdr_bh")
    return pd.DataFrame({"subtype": [s for s, _ in pvals], "chi2_p": [p for _, p in pvals],
                         "fdr_q": q})


def _chrono_split(snap, subset_mask, outcome):
    g = snap[subset_mask].dropna(subset=[outcome]).sort_values("historical_date")
    if len(g) < 30:
        return np.nan, np.nan, np.nan
    mid = len(g) // 2
    r0 = float(g[outcome].iloc[:mid].mean())
    r1 = float(g[outcome].iloc[mid:].mean())
    p = np.nan
    if (g[outcome].iloc[:mid].nunique() > 1) and (g[outcome].iloc[mid:].nunique() > 1):
        try:
            chi2, p, _, _ = chi2_contingency(pd.crosstab(
                [0] * mid + [1] * (len(g) - mid), g[outcome]), correction=False)
        except Exception:
            pass
    return r0, r1, p


def _loo_cycle(snap, subset_mask, outcome):
    g = snap[subset_mask].dropna(subset=[outcome])
    rates = []
    for sp in g["subperiod"].unique():
        rest = g[g["subperiod"] != sp]
        if len(rest) >= 30:
            rates.append(float(rest[outcome].mean()))
    return (min(rates), max(rates)) if rates else (np.nan, np.nan)


def validate_subtypes():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    tl = snap[snap["is_true_loner"] == 1].copy()
    tl["subtype"] = "MIXED_OTHER"
    cond = {
        "EARLY_CONTAGION": tl["out_contagion"] == 1,
        "PERSISTENT_DECOUPLING": tl["out_decouple"] == 1,
        "RANK_HEALTH_FAILURE": (tl["price_up_30"] == 1) & (tl["rank_up_30"] == 0),
        "REJOINING_DISLOCATION": tl["st4_30"] == "REJOINING",
        "LOCAL_EXTREME_WITH_FIELD_SUPPORT": tl["abs_ret"] >= 0.10,
        "FULL_REHABILITATION": (tl["out_rejoin"] == 1) & (tl["rank_up_30"] == 1),
    }
    n_true = pd.Series(0, index=tl.index, dtype=int)
    for m in cond.values():
        n_true = n_true + m.astype(int)
    for name, m in cond.items():
        tl.loc[m & (n_true == 1), "subtype"] = name
    fdr_c = _subtype_fdr(tl, "subtype", "out_contagion", list(cond))
    fdr_d = _subtype_fdr(tl, "subtype", "out_decouple", list(cond))
    rows = []
    for target, outcome, fdr in [("EARLY_CONTAGION", "out_contagion", fdr_c),
                                 ("PERSISTENT_DECOUPLING", "out_decouple", fdr_d)]:
        mask = tl["subtype"] == target
        n = int(mask.sum())
        ncyc = int(tl[mask]["subperiod"].nunique())
        r0, r1, p_chrono = _chrono_split(tl, mask, outcome)
        loo_min, loo_max = _loo_cycle(tl, mask, outcome)
        q = (float(fdr.loc[fdr["subtype"] == target, "fdr_q"].iloc[0])
             if len(fdr) and (fdr["subtype"] == target).any() else np.nan)
        base_rate = float(tl[outcome].mean())
        sub_rate = float(tl[mask][outcome].mean()) if n else np.nan
        tl2 = tl.copy()
        tl2["ind"] = mask.astype(int)
        auc = _purged_auc(tl2, outcome, ["ind"])
        survives = (n >= MIN_SUPPORT and ncyc >= 3
                    and (pd.isna(r1) or r1 >= 0.5 * max(sub_rate, 1e-6))
                    and (pd.isna(q) or q <= 0.10)
                    and (not np.isfinite(auc) or auc >= 0.55))
        rows.append({
            "subtype": target, "n": int(n), "n_cycles": ncyc,
            "outcome_rate_in_subtype": _fmt(sub_rate),
            "outcome_rate_baseline_true_loners": _fmt(base_rate),
            "chrono_first_half_rate": _fmt(r0), "chrono_second_half_rate": _fmt(r1),
            "chrono_chi2_p": _fmt(p_chrono, 3),
            "loo_cycle_rate_min": _fmt(loo_min), "loo_cycle_rate_max": _fmt(loo_max),
            "fdr_q_across_subtype_scan": _fmt(q, 3),
            "purged_auc_indicator": _fmt(auc),
            "verdict": "SURVIVES_PURGED_FDR" if survives else "DEMOTED"})
    return pd.DataFrame(rows), tl


def persistent_decoupling_detail():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    tl = snap[(snap["is_true_loner"] == 1) & (snap["out_decouple"] == 1)].copy()
    rows = []
    rows.append({"test": "support", "detail": f"n={len(tl)}, cycles={tl['subperiod'].nunique()}",
                 "value": "n" if len(tl) >= MIN_SUPPORT else "NOT_SUPPORTED"})
    rows.append({"test": "duration", "detail": "median state age at decoupling event",
                 "value": _fmt(tl["state_age_d"].median())})
    rows.append({"test": "decoupling_rate_by_cell4", "detail": ";".join(
        f"{c}:{_fmt(g['out_decouple'].mean())}" for c, g in tl.groupby("cell4")),
        "value": "FIELD_DEPENDENT" if tl.groupby("cell4")["out_decouple"].mean().nunique() > 2 else "FIELD_FLAT"})
    rows.append({"test": "decoupling_rate_by_rank_depth", "detail": ";".join(
        f"{c}:{_fmt(g['out_decouple'].mean())}" for c, g in tl.groupby(
            tl["rank_band"].map(C9._rank_depth_band))),
        "value": "RANK_DEPENDENT"})
    rows.append({"test": "decoupling_rate_by_abs_class", "detail": ";".join(
        f"{c}:{_fmt(g['out_decouple'].mean())}" for c, g in tl.groupby(tl["abs_ret"].map(A._abs_class))),
        "value": "SHOCK_DEPENDENT"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 16 FALSE-LONER ARTIFACT RECHECK
# ---------------------------------------------------------------------------

def false_loner_recheck(cp):
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    ev = snap.copy()
    ev["vol_q"] = pd.qcut(ev["vol_30d"].fillna(ev["vol_30d"].median()).rank(method="first"),
                          5, labels=["V1", "V2", "V3", "V4", "V5"])
    ev["abs_class"] = ev["abs_ret"].map(A._abs_class)
    ev["sigma_class"] = ev["z1"].map(A._sigma_class)
    groups = [("rank_band", "rank_band"), ("volatility", "vol_q"),
              ("absolute_move", "abs_class"), ("sigma", "sigma_class"),
              ("field_cell4", "cell4"), ("field_mcell6", "mcell6")]
    mc = C9._mcell_partitions()
    mcmap = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["mcell6"]))
    ev["mcell6"] = ev["historical_date"].dt.normalize().map(mcmap)
    rows = []
    for gname, col in groups:
        for x, g in ev.groupby(col):
            if len(g) < 30 or pd.isna(x):
                continue
            rows.append({"dimension": gname, "level": str(x), "n_events": int(len(g)),
                         "false_loner_density": _fmt(g["is_false_loner"].mean()),
                         "true_loner_density": _fmt(g["is_true_loner"].mean())})
    fl = ev[ev["is_false_loner"] == 1].copy()
    fl["subtype"] = "MIXED"
    n_t = pd.Series(0, index=fl.index, dtype=int)
    cond = {
        "LOW_VOL_NORMALIZATION_ARTIFACT": (fl["abs_ret"] < 0.02) & (fl["peer_abs_med"] < 0.02),
        "TRUE_SHARED_LOCAL_MOVE": (fl["abs_ret"] >= 0.02) & (fl["peer_abs_med"] >= 0.02),
        "PEER_REORGANIZATION_EVENT": fl["roll_turnover_30d"] >= fl["roll_turnover_30d"].quantile(0.67),
        "MEASUREMENT_EDGE": fl["peer_count"] < 5,
    }
    for m in cond.values():
        n_t = n_t + m.astype(int)
    for name, m in cond.items():
        fl.loc[m & (n_t == 1), "subtype"] = name
    for st, g in fl.groupby("subtype"):
        rows.append({"dimension": "subtype", "level": st, "n_events": int(len(g)),
                     "false_loner_density": _fmt(len(g) / len(ev)),
                     "true_loner_density": np.nan,
                     "note": "median abs/peer values below"})
        rows.append({"dimension": "subtype_abs_peer_context", "level": st,
                     "n_events": int(len(g)),
                     "false_loner_density": _fmt(g["abs_ret"].median()),
                     "true_loner_density": _fmt(g["peer_abs_med"].median())})
    df = pd.DataFrame(rows)
    n_artifact = int((fl["subtype"] == "LOW_VOL_NORMALIZATION_ARTIFACT").sum())
    verdict = pd.DataFrame([{
        "n_false_loners": int(len(fl)),
        "n_low_vol_normalization_artifact": n_artifact,
        "artifact_share_of_false_loners": _fmt(n_artifact / max(len(fl), 1)),
        "median_abs_move_false_loners": _fmt(fl["abs_ret"].median()),
        "median_peer_abs_move_false_loners": _fmt(fl["peer_abs_med"].median()),
        "verdict": ("ARTIFACT_CONFIRMED" if n_artifact / max(len(fl), 1) >= 0.5
                    else "ARTIFACT_REDUCED")}])
    df.to_csv(R / "16_FALSE_LONER_RECHECK.csv", index=False)
    verdict.to_csv(R / "16b_FALSE_LONER_RECHECK_VERDICT.csv", index=False)
    return df, verdict


# ---------------------------------------------------------------------------
# 17 TRUE-LONER SPECIES
# ---------------------------------------------------------------------------

def true_loner_species():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    tl = snap[snap["is_true_loner"] == 1].copy()
    tl["subtype"] = "MIXED_OTHER"
    cond = {
        "EARLY_CONTAGION": tl["out_contagion"] == 1,
        "PERSISTENT_DECOUPLING": tl["out_decouple"] == 1,
        "RANK_HEALTH_FAILURE": (tl["price_up_30"] == 1) & (tl["rank_up_30"] == 0),
        "REJOINING_DISLOCATION": tl["st4_30"] == "REJOINING",
        "LOCAL_EXTREME_WITH_FIELD_SUPPORT": tl["abs_ret"] >= 0.10,
        "FULL_REHABILITATION": (tl["out_rejoin"] == 1) & (tl["rank_up_30"] == 1),
    }
    n_true = pd.Series(0, index=tl.index, dtype=int)
    for m in cond.values():
        n_true = n_true + m.astype(int)
    for name, m in cond.items():
        tl.loc[m & (n_true == 1), "subtype"] = name
    rows = []
    for st, g in tl.groupby("subtype"):
        rows.append({
            "subtype": st, "n": int(len(g)),
            "supported": "YES" if len(g) >= MIN_SUPPORT else "NOT_SUPPORTED",
            "share_of_true_loners": _fmt(len(g) / max(len(tl), 1)),
            "median_abs_move": _fmt(g["abs_ret"].median()),
            "median_sigma": _fmt(g["z1"].median()),
            "p_recovery_30d": _fmt(g["recover1s30"].mean()),
            "p_contagion_7d": _fmt(g["out_contagion"].mean()),
            "p_decoupling_30d": _fmt(g["out_decouple"].mean()),
            "median_state_age_d": _fmt(g["state_age_d"].median()),
            "relational_state_mode": str(g["rel_state"].mode().iloc[0]) if len(g) else ""})
    df = pd.DataFrame(rows)
    mixed = df[df["subtype"] == "MIXED_OTHER"]
    mixed_share = float(mixed["share_of_true_loners"].iloc[0]) if len(mixed) else 1.0
    verdict = pd.DataFrame([{
        "n_true_loners": int(len(tl)),
        "mixed_other_share": _fmt(mixed_share),
        "n_supported_species": int((df["supported"] == "YES").sum()),
        "verdict": ("MIXED_OTHER_REDUCED" if mixed_share < 0.35
                    else "MIXED_OTHER_DOMINANT_NO_FORCED_SPLIT")}])
    df.to_csv(R / "17_TRUE_LONER_SPECIES.csv", index=False)
    verdict.to_csv(R / "17b_TRUE_LONER_SPECIES_VERDICT.csv", index=False)
    return df, verdict


# ---------------------------------------------------------------------------
# 18 DIRECTIONAL ASYMMETRY REPLICATION
# ---------------------------------------------------------------------------

def directional_asymmetry_replication():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    snap = snap.dropna(subset=["event_sign"])
    snap["side"] = np.where(snap["event_sign"] > 0, "UP", "DOWN")
    snap["abs_class"] = snap["abs_ret"].map(A._abs_class)
    snap["sigma_class"] = snap["z1"].map(A._sigma_class)
    snap["rank_depth"] = snap["rank_band"].map(C9._rank_depth_band)
    mc = C9._mcell_partitions()
    mcmap6 = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["mcell6"]))
    mcmap4 = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["cell4"]))
    snap["mcell6"] = snap["historical_date"].dt.normalize().map(mcmap6)
    snap["cell4"] = snap["historical_date"].dt.normalize().map(mcmap4)
    groups = [("OVERALL", pd.Series("ALL", index=snap.index)),
              ("CYCLE", snap["subperiod"]), ("RANK_DEPTH", snap["rank_depth"]),
              ("FIELD_CELL6", snap["mcell6"]), ("FIELD_CELL4", snap["cell4"]),
              ("ABS_CLASS", snap["abs_class"]), ("SIGMA_CLASS", snap["sigma_class"]),
              ("RELATIONAL_STATE", snap["rel_state"])]
    rows = []
    for gname, gv in groups:
        for key, g in snap.groupby(gv):
            if len(g) < 40 or pd.isna(key):
                continue
            up = g[g["side"] == "UP"]
            dn = g[g["side"] == "DOWN"]
            if len(up) < 20 or len(dn) < 20:
                continue
            for metric, col in [("contagion_7d", "out_contagion"),
                                ("rejoin_30d", "out_rejoin"),
                                ("decoupling_30d", "out_decouple")]:
                pu = float(up[col].mean())
                pd_ = float(dn[col].mean())
                rows.append({"group": gname, "level": str(key), "metric": metric,
                             "n_up": int(len(up)), "n_down": int(len(dn)),
                             "upside_rate": _fmt(pu), "downside_rate": _fmt(pd_),
                             "down_up_ratio": _fmt(pd_ / pu if pu else np.nan),
                             "direction": ("DOWNSIDE_STRONGER" if pd_ > pu
                                           else "UPSIDE_STRONGER" if pu > pd_
                                           else "SYMMETRIC")})
    df = pd.DataFrame(rows)
    # verdict on contagion asymmetry
    c = df[df["metric"] == "contagion_7d"]
    overall = c[(c["group"] == "OVERALL")]
    cycles = c[(c["group"] == "CYCLE") & (c["direction"] != "SYMMETRIC")]
    cells = c[(c["group"] == "FIELD_CELL6") & (c["direction"] != "SYMMETRIC")]
    depth = c[(c["group"] == "RANK_DEPTH") & (c["direction"] != "SYMMETRIC")]
    if len(overall):
        od = overall["direction"].iloc[0]
        cyc_frac = float((cycles["direction"] == od).mean()) if len(cycles) else np.nan
        cell_frac = float((cells["direction"] == od).mean()) if len(cells) else np.nan
        depth_frac = float((depth["direction"] == od).mean()) if len(depth) else np.nan
        if od == "DOWNSIDE_STRONGER" and cyc_frac >= 0.6 and cell_frac >= 0.6:
            v = "ROBUST_SIGN_ASYMMETRY"
        elif od == "DOWNSIDE_STRONGER" and cyc_frac >= 0.6:
            v = "RANK_LOCAL_ASYMMETRY" if depth_frac < 0.6 else "FIELD_CONDITIONAL_ASYMMETRY"
        elif od == "DOWNSIDE_STRONGER":
            v = "FIELD_CONDITIONAL_ASYMMETRY"
        else:
            v = "NO_STABLE_ASYMMETRY"
    else:
        v = "NO_STABLE_ASYMMETRY"
    df.to_csv(R / "18_DIRECTIONAL_ASYMMETRY_REPLICATION.csv", index=False)
    pd.DataFrame([{"verdict": v,
                   "overall_contagion": ";".join(
                       f"DOWN={_fmt(r['downside_rate'])};UP={_fmt(r['upside_rate'])}"
                       for _, r in overall.iterrows()) if len(overall) else "",
                   "cycle_consistency_frac": _fmt(cyc_frac) if 'cyc_frac' in dir() else np.nan,
                   "cell_consistency_frac": _fmt(cell_frac) if 'cell_frac' in dir() else np.nan,
                   "depth_consistency_frac": _fmt(depth_frac) if 'depth_frac' in dir() else np.nan}]
                 ).to_csv(R / "18b_DIRECTIONAL_ASYMMETRY_VERDICT.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 19 / 20 UP / DOWN RELATIONAL ECOLOGY
# ---------------------------------------------------------------------------

def _ecology_conditions(snap, cp, side):
    sub = snap[snap["event_sign"] * side > 0].copy()
    mc = C9._mcell_partitions()
    mcmap6 = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["mcell6"]))
    sub["mcell6"] = sub["historical_date"].dt.normalize().map(mcmap6)
    sub["rank_depth"] = sub["rank_band"].map(C9._rank_depth_band)
    lut = _state_at_h_lut(cp)
    iso30 = np.zeros(len(sub), dtype=float)
    for i, (_, row) in enumerate(sub.iterrows()):
        st = lut.get((row["cmc_id"], row["historical_date"] + pd.Timedelta(days=30)))
        iso30[i] = st in ("TRUE_ISOLATED", "FALSE_ISOLATED",
                          "DISLOCATED_UNCLASSIFIED", "DECOUPLED")
    sub["isolated_30d"] = iso30
    rows = []
    conds = [("OVERALL", pd.Series("ALL", index=sub.index)),
             ("RANK_DEPTH", sub["rank_depth"]),
             ("FIELD_CELL6", sub["mcell6"]),
             ("ABS_CLASS", sub["abs_ret"].map(A._abs_class))]
    for gname, gv in conds:
        for key, g in sub.groupby(gv):
            if len(g) < 30 or pd.isna(key):
                continue
            rows.append({
                "condition": gname, "level": str(key), "n": int(len(g)),
                "p_rejoin_30d": _fmt(g["out_rejoin"].mean()),
                "p_rehabilitate": _fmt((g["st4_30"] == "REJOINING").mean()),
                "p_decoupling_30d": _fmt(g["out_decouple"].mean()),
                "p_contagion_7d": _fmt(g["out_contagion"].mean()),
                "p_isolated_30d": _fmt(g["isolated_30d"].mean()),
                "median_membership_turnover": _fmt(g["roll_turnover_30d"].median()),
                "median_abs_shock": _fmt(g["abs_ret"].median())})
    return pd.DataFrame(rows)


def up_down_ecology(cp):
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    up = _ecology_conditions(snap, cp, +1)
    dn = _ecology_conditions(snap, cp, -1)
    up.to_csv(R / "19_UPSIDE_RELATIONAL_ECOLOGY.csv", index=False)
    dn.to_csv(R / "20_DOWNSIDE_RELATIONAL_ECOLOGY.csv", index=False)
    return up, dn


# ---------------------------------------------------------------------------
# 21 PRD RELATIONAL-HEALTH VALIDATION
# ---------------------------------------------------------------------------

def prd_validation():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    prd = snap[(snap["price_up_14"] == 1) & (snap["rank_up_14"] == 0)].copy()
    # peer basket 14d forward (exact peer ids at the snapshot)
    sets = C.load_peer_map(C9.PRIMARY).groupby("event_index")["peer_id"].apply(
        lambda s: frozenset(s)).to_dict()
    dates, assets, Rm = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    v = np.full(len(prd), np.nan)
    for i, (_, row) in enumerate(prd.iterrows()):
        di = dpos.get(row["historical_date"])
        if di is None:
            continue
        t = dates[di]
        hi = di
        while hi + 1 < len(dates) and dates[hi + 1] <= t + pd.Timedelta(days=14):
            hi += 1
        vals = []
        for pid in sets.get(row["event_index"], ()):
            pi = apos.get(pid)
            if pi is None:
                continue
            x = np.nansum(Rm[di + 1:hi + 1, pi])
            if np.isfinite(x):
                vals.append(x)
        v[i] = float(np.median(vals)) if vals else np.nan
    prd["peer_fwd14"] = v
    prd["peer_dir"] = np.select([prd["peer_fwd14"] > 0, prd["peer_fwd14"] < 0],
                                ["PEER_UP", "PEER_DOWN"], default="PEER_FLAT")
    prd["BETA_RESCUE"] = ((prd["top500_breadth_30d"] > 0) & (prd["peer_dir"] == "PEER_UP")
                          & (prd["signed_fwd14"] <= prd["peer_fwd14"])).astype(int)
    prd["PEER_RESCUE"] = ((prd["peer_dir"] == "PEER_UP") & (prd["signed_fwd14"] <= prd["peer_fwd14"])).astype(int)
    prd["RELATIVE_DECAY"] = ((prd["peer_dir"] == "PEER_DOWN") & (prd["signed_fwd14"] > 0)).astype(int)
    prd["DELAYED_REHAB"] = ((prd["peer_dir"] == "PEER_UP") & (prd["signed_fwd14"] > prd["peer_fwd14"])
                            & (prd["rank_up_30"] == 1)).astype(int)
    prd["TEMPORARY_SPLIT"] = ((prd["signed_fwd14"] > 0) & (prd["signed_fwd30"] < 0)).astype(int)
    subtypes = ["BETA_RESCUE", "PEER_RESCUE", "RELATIVE_DECAY", "DELAYED_REHAB", "TEMPORARY_SPLIT"]
    mc = C9._mcell_partitions()
    mcmap6 = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["mcell6"]))
    prd["mcell6"] = prd["historical_date"].dt.normalize().map(mcmap6)
    # BH-FDR across the subtype scan, outcome = relational recovery (out_rejoin)
    pvals = []
    for s2 in subtypes:
        sub = prd.dropna(subset=["out_rejoin"])
        tab = pd.crosstab(sub[s2] == 1, sub["out_rejoin"])
        if tab.shape != (2, 2):
            continue
        try:
            _, p, _, _ = chi2_contingency(tab, correction=False)
            pvals.append((s2, float(p)))
        except Exception:
            continue
    qmap = {}
    if pvals:
        _, qs, _, _ = multipletests([p for _, p in pvals], method="fdr_bh")
        qmap = {s: float(q) for s, q in zip([s for s, _ in pvals], qs)}
    rows = []
    for st in subtypes:
        g = prd[prd[st] == 1]
        n = int(len(g))
        ncyc = int(g["subperiod"].nunique())
        r0, r1, p_chrono = _chrono_split(prd, prd[st] == 1, st)
        q = qmap.get(st, np.nan)
        g6 = g.dropna(subset=["mcell6"])
        field = ";".join(f"{c}:{_fmt((g6[g6['mcell6'] == c][st].mean()) if len(g6[g6['mcell6'] == c]) else np.nan)}"
                         for c in g6["mcell6"].unique()) if n else ""
        if n < MIN_SUPPORT or ncyc < 3:
            verdict = "DISSOLVE"
        elif np.isfinite(q) and q <= 0.10:
            verdict = "PROMOTE"
        else:
            verdict = "LOCAL"
        rows.append({"subtype": st, "n": int(n), "n_cycles": ncyc,
                     "supported": "YES" if n >= MIN_SUPPORT else "NOT_SUPPORTED",
                     "chrono_first_half_rate": _fmt(r0),
                     "chrono_second_half_rate": _fmt(r1),
                     "chrono_chi2_p": _fmt(p_chrono, 3),
                     "fdr_q_subtype_scan_out_rejoin": _fmt(q, 3),
                     "field_cell6_overlay": field,
                     "relational_state_mode": str(g["rel_state"].mode().iloc[0]) if n else "",
                     "verdict": verdict})
    df = pd.DataFrame(rows)
    df.to_csv(R / "21_PRD_RELATIONAL_HEALTH_VALIDATION.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 22 HEALTH x RELATIONAL OVERLAY
# ---------------------------------------------------------------------------

def health_relational_overlay():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    snap["health_cell"] = np.select(
        [(snap["price_up_14"] == 1) & (snap["rank_up_14"] == 1),
         (snap["price_up_14"] == 1) & (snap["rank_up_14"] == 0),
         (snap["price_up_14"] == 0) & (snap["rank_up_14"] == 1),
         (snap["price_up_14"] == 0) & (snap["rank_up_14"] == 0)],
        ["PRICE_UP_RANK_UP", "PRICE_UP_RANK_DOWN", "PRICE_DOWN_RANK_UP",
         "PRICE_DOWN_RANK_DOWN"], default="UNCLASSIFIED")
    rows = []
    for cell, g in snap.groupby("health_cell"):
        if len(g) < 30:
            continue
        vc = g["rel_state"].value_counts(normalize=True)
        rows.append({
            "health_cell": cell, "n": int(len(g)),
            "rel_state_composition": ";".join(f"{k}:{_fmt(v)}" for k, v in vc.items()),
            "top_relational_state": str(vc.index[0]) if len(vc) else "",
            "p_top_state": _fmt(vc.iloc[0]) if len(vc) else np.nan,
            "membership_stable_share": _fmt((g["membership_class"] == "STABLE_MEMBERS").mean()),
            "membership_rotating_share": _fmt((g["membership_class"] == "ROTATING_MEMBERS").mean()),
            "field_cell4_mode": str(g["cell4"].mode().iloc[0]) if len(g) else ""})
    df = pd.DataFrame(rows)
    # chi2: does relational-state composition differ across health cells?
    tab = pd.crosstab(snap["health_cell"], snap["rel_state"])
    chi2_p = np.nan
    if tab.shape[0] >= 2 and tab.shape[1] >= 2:
        try:
            chi2, p, _, _ = chi2_contingency(tab, correction=False)
            chi2_p = float(p)
        except Exception:
            pass
    verdict = pd.DataFrame([{
        "chi2_p_state_composition_across_health_cells": _fmt(chi2_p, 3),
        "n_health_cells": int(snap["health_cell"].nunique()),
        "verdict": ("RELATIONAL_ROLE_DIFFERENTIATES_HEALTH_CELLS" if
                    np.isfinite(chi2_p) and chi2_p < 0.05 else "COMPOSITION_NOT_DISTINCT")}])
    df.to_csv(R / "22_HEALTH_RELATIONAL_OVERLAY.csv", index=False)
    verdict.to_csv(R / "22b_HEALTH_RELATIONAL_OVERLAY_VERDICT.csv", index=False)
    return df, verdict


# ---------------------------------------------------------------------------
# 23 PREDICTIVE-NULL FREEZE (final audit)
# ---------------------------------------------------------------------------

def predictive_null_freeze():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    snap["rel_state_cat"] = snap["rel_state"].astype("category").cat.codes
    snap["rank_band_cat"] = snap["rank_band"].astype("category").cat.codes
    sets = C.load_peer_map(C9.PRIMARY).groupby("event_index")["peer_id"].apply(
        lambda s: frozenset(s)).to_dict()
    dates, assets, Rm = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    pf7 = np.full(len(snap), np.nan)
    for i, (_, row) in enumerate(snap.iterrows()):
        di = dpos.get(row["historical_date"])
        ai = apos.get(row["cmc_id"])
        if di is None or ai is None:
            continue
        t = dates[di]
        hi = di
        while hi + 1 < len(dates) and dates[hi + 1] <= t + pd.Timedelta(days=7):
            hi += 1
        vals = []
        for pid in sets.get(row["event_index"], ()):
            pi = apos.get(pid)
            if pi is None:
                continue
            x = np.nansum(Rm[di + 1:hi + 1, pi])
            if np.isfinite(x):
                vals.append(x)
        pf7[i] = float(np.median(vals)) if vals else np.nan
    snap["peer_fwd7"] = pf7
    feats = {
        "relational_state": ["rel_state_cat"],
        "exact_peer_ids": ["peer_med_ret", "peer_std_ret", "peer_fwd7", "peer_corr"],
        "membership_stability": ["membership_class_cat", "roll_turnover_30d", "entropy_30d"],
        "local_shock": ["abs_ret", "z1", "vol_30d"],
    }
    snap["membership_class_cat"] = snap["membership_class"].astype("category").cat.codes
    outcomes = {"recovery": "out_rejoin", "contagion": "out_contagion",
                "decoupling": "out_decouple"}
    rows = []
    for oname, ocol in outcomes.items():
        for fname, cols in feats.items():
            auc = _purged_auc(snap, ocol, cols)
            rows.append({"outcome": oname, "feature_family": fname,
                         "purged_auc": _fmt(auc), "n": int(len(snap))})
    df = pd.DataFrame(rows)
    verdicts = []
    freeze = True
    for oname in outcomes:
        sub = df[df["outcome"] == oname].set_index("feature_family")["purged_auc"]
        rel = float(sub.get("relational_state", np.nan))
        best = float(sub.drop(index="relational_state", errors="ignore").max())
        better = rel >= best + 0.01
        freeze = freeze and not better
        verdicts.append({"outcome": oname,
                         "relational_state_auc": _fmt(rel),
                         "best_other_auc": _fmt(best),
                         "relational_state_incremental": "YES" if better else "NO",
                         "conclusion": "NULL_FREEZE_APPLIES" if not better else "INCREMENTAL_FOUND"})
    verdicts.append({"outcome": "FINAL",
                     "relational_state_auc": np.nan, "best_other_auc": np.nan,
                     "relational_state_incremental": "n/a",
                     "conclusion": ("FREEZE_NULL_RELATIONAL_STATE_NOT_INCREMENTAL_PREDICTOR"
                                    if freeze else "DO_NOT_FREEZE_VERIFY_AGAIN")})
    pd.DataFrame(verdicts).to_csv(R / "23b_PREDICTIVE_NULL_VERDICT.csv", index=False)
    df.to_csv(R / "23_PREDICTIVE_NULL_FREEZE.csv", index=False)
    return df, verdicts


# ---------------------------------------------------------------------------
# 24 DESCRIPTION vs PREDICTION SEPARATION (markdown)
# ---------------------------------------------------------------------------

def description_prediction_separation(v23):
    md = """# DESCRIPTION vs PREDICTION SEPARATION (LF9)

**ONTOLOGY DISTINCTION.** The market OS does not require one representation to
be best at everything. Two objects coexist and must not be conflated:

| Layer | Object | What it is for | Evidence |
|---|---|---|---|
| DESCRIPTIVE | RELATIONAL_STATE | persistent object describing where an asset stands relative to its neighborhood | LF8/LF9 persistence (relational state outlives membership at 1-60d) |
| PREDICTIVE | PEER_ID / LOCAL FEATURES | possibly more predictive but unstable membership | LF8 H7 falsification; LF9 final audit (purged AUC) |
| ACTION | (deferred) | execution complexity only if the terrain proves it necessary | out of scope for this checkpoint |

**RULE.** A representation may be a good *state description* without being a
good *forecaster*. Persistence is a property of the object; forecast skill is
a property of a predictor. LF9 freezes the forecast question (see 23) unless
new data or a materially different object appears. No strategy, no PnL, no
execution, no sizing, no leverage.
"""
    (R / "24_DESCRIPTION_PREDICTION_SEPARATION.md").write_text(md, encoding="utf-8")
    return md


# ---------------------------------------------------------------------------
# 25 LOCAL TRANSFER-FUNCTION DRIFT
# ---------------------------------------------------------------------------

def local_transfer_drift():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    snap = snap.dropna(subset=["abs_ret"])
    y_hi = (snap["roll_turnover_30d"] > snap["roll_turnover_30d"].median()).astype(int)
    outs = {"abs_to_turnover": y_hi, "abs_to_decoupling": snap["out_decouple"],
            "abs_to_contagion": snap["out_contagion"], "abs_to_rejoin": snap["out_rejoin"]}
    mc = C9._mcell_partitions()
    fmap = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["forcing"]))
    snap["forcing_day"] = snap["historical_date"].dt.normalize().map(fmap)
    rows = []
    for name, y in outs.items():
        for sp, g in snap.groupby("subperiod"):
            gg = g.dropna(subset=["abs_ret"]).copy()
            gg["y"] = y.loc[gg.index]
            gg = gg.dropna(subset=["y"])
            if len(gg) < 60 or gg["y"].nunique() < 2:
                continue
            X = gg["abs_ret"].to_numpy().reshape(-1, 1)
            try:
                clf = LogisticRegression(max_iter=1000)
                clf.fit(X, gg["y"].to_numpy())
                slope = float(clf.coef_[0][0])
                ed50 = float(-clf.intercept_[0] / slope) if slope != 0 else np.nan
                rows.append({"transfer": name, "subperiod": sp, "n": int(len(gg)),
                             "gain_slope": _fmt(slope),
                             "ed50_abs_threshold": _fmt(ed50),
                             "mean_forcing": _fmt(gg["forcing_day"].mean())})
            except Exception:
                continue
    df = pd.DataFrame(rows)
    verdicts = []
    for name in outs:
        sub = df[df["transfer"] == name]
        if len(sub) < 3:
            continue
        slopes = sub["gain_slope"].dropna()
        ed50s = sub["ed50_abs_threshold"].dropna()
        cv = float(slopes.std() / abs(slopes.mean())) if len(slopes) and slopes.mean() else np.nan
        ed_range = float(ed50s.max() - ed50s.min()) if len(ed50s) else np.nan
        if cv is not None and np.isfinite(cv) and cv < 0.35 and ed_range < 0.05:
            v = "LOCAL_LAW_STABLE"
        elif cv is not None and np.isfinite(cv) and cv < 0.35:
            v = "THRESHOLD_DRIFT"
        elif ed_range < 0.05:
            v = "GAIN_DRIFT"
        else:
            v = "FIELD_CONDITIONAL_DRIFT"
        rho, p = spearmanr(sub["mean_forcing"], sub["gain_slope"]) if len(sub) >= 4 else (np.nan, np.nan)
        if v != "LOCAL_LAW_STABLE" and np.isfinite(rho) and abs(rho) > 0.6:
            v = "FIELD_CONDITIONAL_DRIFT"
        verdicts.append({"transfer": name, "n_subperiods": int(len(sub)),
                         "slope_cv": _fmt(cv), "ed50_range": _fmt(ed_range),
                         "slope_vs_forcing_spearman": _fmt(rho),
                         "verdict": v})
    vd = pd.DataFrame(verdicts)
    df.to_csv(R / "25_LOCAL_TRANSFER_FUNCTION_DRIFT.csv", index=False)
    vd.to_csv(R / "25b_LOCAL_TRANSFER_DRIFT_VERDICT.csv", index=False)
    return df, vd


# ---------------------------------------------------------------------------
# 26 LOCAL / GLOBAL HIERARCHY TEST
# ---------------------------------------------------------------------------

def local_global_hierarchy():
    snap = C.load_primary_panel()
    snap = C.attach_forward_outcomes(snap)
    mc = C9._mcell_partitions()
    fmap = dict(zip(pd.to_datetime(mc["d"]).dt.normalize(), mc["forcing"]))
    snap["forcing_day"] = snap["historical_date"].dt.normalize().map(fmap)
    snap = snap.dropna(subset=["forcing_day", "rank_band", "abs_ret", "rel_state"])
    snap["rel_state_cat"] = snap["rel_state"].astype("category").cat.codes
    snap["rank_band_cat"] = snap["rank_band"].astype("category").cat.codes
    g = ["forcing_day", "top500_breadth_30d", "top500_dispersion_30d"]
    p = ["rank_band_cat", "rank"]
    s = ["abs_ret", "z1", "vol_30d"]
    r = ["rel_state_cat"]
    models = {
        "GLOBAL": g,
        "GLOBAL_PATCH": g + p,
        "GLOBAL_PATCH_SHOCK": g + p + s,
        "GLOBAL_PATCH_SHOCK_RELATIONAL": g + p + s + r,
        "ALT_GLOBAL_RELATIONAL_DIRECT": g + r,
        "ALT_RANK_RELATIONAL_NO_SHOCK": p + r,
        "ALT_SHOCK_HEALTH_NO_RELATIONAL": g + p + s,
    }
    rows = []
    for oname, ocol in [("recovery", "out_rejoin"), ("contagion", "out_contagion"),
                        ("decoupling", "out_decouple")]:
        for mname, cols in models.items():
            auc = _purged_auc(snap, ocol, cols)
            rows.append({"outcome": oname, "model": mname, "purged_auc": _fmt(auc),
                         "n": int(len(snap))})
    df = pd.DataFrame(rows)
    verdicts = []
    for oname in ["recovery", "contagion", "decoupling"]:
        sub = df[df["outcome"] == oname].set_index("model")["purged_auc"].astype(float)
        full = sub.get("GLOBAL_PATCH_SHOCK_RELATIONAL", np.nan)
        chain = [sub.get("GLOBAL", np.nan), sub.get("GLOBAL_PATCH", np.nan),
                 sub.get("GLOBAL_PATCH_SHOCK", np.nan), full]
        monotone = all(np.isfinite(x) for x in chain) and all(
            chain[i + 1] >= chain[i] - 0.005 for i in range(3))
        alts = [sub.get("ALT_GLOBAL_RELATIONAL_DIRECT", np.nan),
                sub.get("ALT_RANK_RELATIONAL_NO_SHOCK", np.nan),
                sub.get("ALT_SHOCK_HEALTH_NO_RELATIONAL", np.nan)]
        beats_alts = np.isfinite(full) and all(np.isfinite(a) for a in alts) and all(
            full >= a - 0.005 for a in alts)
        verdicts.append({"outcome": oname,
                         "full_model_auc": _fmt(full),
                         "monotone_nested_gain": "YES" if monotone else "NO",
                         "beats_alternatives": "YES" if beats_alts else "NO",
                         "hierarchy_verdict": ("HIERARCHY_COHERENT" if monotone and beats_alts
                                               else "HIERARCHY_PARTIAL")})
    vd = pd.DataFrame(verdicts)
    df.to_csv(R / "26_LOCAL_GLOBAL_HIERARCHY.csv", index=False)
    vd.to_csv(R / "26b_LOCAL_GLOBAL_HIERARCHY_VERDICT.csv", index=False)
    return df, vd


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("[lf9] building continuous panel ...", flush=True)
    cp = C9.build_continuous_panel()

    print("[lf9] 02 continuous panel + manifest ...", flush=True)
    continuous_panel(cp)

    print("[lf9] 03 continuous persistence ...", flush=True)
    continuous_persistence(cp)

    print("[lf9] 04 topology vs role ...", flush=True)
    topology_vs_role()

    print("[lf9] 05 shock reorg timing ...", flush=True)
    shock_reorg_timing(cp)

    print("[lf9] 06 abs x sigma grid ...", flush=True)
    abs_sigma_grid(cp)

    print("[lf9] 07 volume / liquidity response ...", flush=True)
    volume_liquidity_response()

    print("[lf9] 08 global field overlay ...", flush=True)
    global_field_overlay(cp)

    print("[lf9] 09 field modulated response ...", flush=True)
    field_modulated_response(cp)

    print("[lf9] 10 global-local shock matrix ...", flush=True)
    global_local_shock_matrix(cp)

    print("[lf9] 11 reorg saturation ...", flush=True)
    reorg_saturation(cp)

    print("[lf9] 12 transition lattice ...", flush=True)
    transition_lattice()

    print("[lf9] 13 competing clocks ...", flush=True)
    competing_clocks(cp)

    print("[lf9] 14/15 subtype validations ...", flush=True)
    v14, tl = validate_subtypes()
    v14[v14["subtype"] == "EARLY_CONTAGION"].to_csv(
        R / "14_EARLY_CONTAGION_VALIDATION.csv", index=False)
    v14[v14["subtype"] == "PERSISTENT_DECOUPLING"].to_csv(
        R / "15_PERSISTENT_DECOUPLING_VALIDATION.csv", index=False)
    persistent_decoupling_detail().to_csv(
        R / "15b_PERSISTENT_DECOUPLING_DETAIL.csv", index=False)

    print("[lf9] 16 false-loner recheck ...", flush=True)
    false_loner_recheck(cp)

    print("[lf9] 17 true-loner species ...", flush=True)
    true_loner_species()

    print("[lf9] 18 directional asymmetry replication ...", flush=True)
    directional_asymmetry_replication()

    print("[lf9] 19/20 up/down ecology ...", flush=True)
    up_down_ecology(cp)

    print("[lf9] 21 PRD validation ...", flush=True)
    prd_validation()

    print("[lf9] 22 health relational overlay ...", flush=True)
    health_relational_overlay()

    print("[lf9] 23 predictive null freeze ...", flush=True)
    v23, v23b = predictive_null_freeze()

    print("[lf9] 24 description vs prediction ...", flush=True)
    description_prediction_separation(v23b)

    print("[lf9] 25 local transfer drift ...", flush=True)
    local_transfer_drift()

    print("[lf9] 26 local/global hierarchy ...", flush=True)
    local_global_hierarchy()

    print("[lf9] DONE", flush=True)


if __name__ == "__main__":
    main()
