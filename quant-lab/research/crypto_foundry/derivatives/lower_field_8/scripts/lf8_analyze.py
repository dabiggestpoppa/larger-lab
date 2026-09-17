"""LOWER-FIELD-8 analysis — dynamic relational state, peer membership entropy,
neighborhood lifecycle, temporal delivery of peer reorganization, up/down peer
ecology, false-loner decomposition, local contagion/rejoin lattice, PRD
relational health.

Built on the LF5 PIT substrate (event-anchored peer snapshots) + LF6 consensus
loner labels + LF7 reclassification. Research only: no strategy, no PnL, no
execution. Outputs 02-24 written to lower_field_8/.
"""
from __future__ import annotations

import json
import warnings
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from scipy.stats import spearmanr, ranksums, chi2_contingency
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import lf8_common as C

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = C.ROOT
H = C.H
MIN_SUPPORT = C.MIN_SUPPORT
STATE_ORDER = C.STATE_ORDER_EXT

FAMILY_ORDER = C.DEEP_FAMILIES

ABS_CLASSES = [("<2%", 0.0, 0.02), ("2-5%", 0.02, 0.05), ("5-10%", 0.05, 0.10),
               ("10-20%", 0.10, 0.20), (">20%", 0.20, np.inf)]
SIGMA_CLASSES = [("2-3σ", 2.0, 3.0), ("3-4σ", 3.0, 4.0), ("4σ+", 4.0, np.inf)]


def _fmt(v, nd=4):
    try:
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return np.nan
        return round(float(v), nd)
    except (TypeError, ValueError):
        return v


def _abs_class(x):
    for name, lo, hi in ABS_CLASSES:
        if lo <= x < hi:
            return name
    return ">20%"


def _sigma_class(x):
    for name, lo, hi in SIGMA_CLASSES:
        if lo <= x < hi:
            return name
    return "4σ+"


def _med(series):
    s = pd.Series(series).dropna()
    return float(s.median()) if len(s) else np.nan


def _mean(series):
    s = pd.Series(series).dropna()
    return float(s.mean()) if len(s) else np.nan


# ---------------------------------------------------------------------------
# Loaders / shared artifacts
# ---------------------------------------------------------------------------

def load_all():
    panels = {}
    for fam in FAMILY_ORDER:
        p = C.build_family_panel(fam)
        p = C.attach_forward_outcomes(p)
        panels[fam] = p
    sets_by_fam = {}
    for fam in FAMILY_ORDER:
        pm = C.load_peer_map(fam)
        sets_by_fam[fam] = pm.groupby("event_index")["peer_id"].apply(
            lambda s: frozenset(s)).to_dict()
    return panels, sets_by_fam


def _future_lookup(snap, h):
    """Per-row: index of the asset's nearest snapshot in [t+h-3, t+h+3]
    (or -1 if none). Row order is preserved from the sorted frame."""
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    n = len(snap)
    fut = np.full(n, -1)
    for cid, g in snap.groupby("cmc_id", sort=False):
        dates = g["historical_date"].to_numpy()
        pos = g.index.to_numpy()
        m = len(g)
        lo_d = dates + pd.Timedelta(days=max(1, h - 3))
        hi_d = dates + pd.Timedelta(days=h + 3)
        j = 0
        for i in range(m):
            if j <= i:
                j = i + 1
            while j < m and dates[j] < lo_d[i]:
                j += 1
            if j < m and dates[j] <= hi_d[i]:
                fut[pos[i]] = pos[j]
    return fut


# =========================================================================
# 02 PEER-LIFETIME PARADOX RESOLUTION
# =========================================================================

def _alive_in_panel(snap, h):
    """Fraction of snapshots whose asset still has a substrate row at t+h
    (wide return matrix presence)."""
    dates, assets, R = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    out = np.full(len(snap), np.nan)
    for i in range(len(snap)):
        di = dpos.get(snap["historical_date"].iloc[i])
        ai = apos.get(snap["cmc_id"].iloc[i])
        if di is None or ai is None:
            continue
        t = dates[di]
        lo = di + 1
        hi = di
        while hi + 1 < len(dates) and dates[hi + 1] <= t + pd.Timedelta(days=h):
            hi += 1
        out[i] = float(np.isfinite(R[lo:hi + 1, ai]).any()) if hi >= lo else 0.0
    return out


def paradox_resolution(panels, sets_by_fam):
    """Separate SAME_MEMBER_SURVIVAL / ANY_NEIGHBORHOOD_SURVIVAL /
    RELATIONAL_STATE_SURVIVAL / PEER_FAMILY_SURVIVAL. Also reproduces LF7's
    'fraction alive' figure to test whether it is a data-availability floor."""
    ev_all = C.load_events()
    ev_all["event_index"] = ev_all.index
    rows = []
    for fam in FAMILY_ORDER:
        snap = panels[fam].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
        sets = sets_by_fam[fam]
        pm = C.load_peer_map(fam)
        peer_events = ev_all[ev_all["event_index"].isin(pm["event_index"])]
        alive7 = float(peer_events["fwd7_cum"].notna().mean())
        alive30 = float(peer_events["fwd30_cum"].notna().mean())
        alive60 = float(pm["peer_return"].notna().mean())
        alive_map = {1: np.nan, 7: alive7, 30: alive30, 60: alive60}
        for h in [1, 3, 7, 14, 30, 60]:
            fut = _future_lookup(snap, h)
            n = len(snap)
            has_fut = fut >= 0
            jac = np.full(n, np.nan)
            for i in range(n):
                if fut[i] >= 0:
                    a = sets.get(snap["event_index"].iloc[i], frozenset())
                    b = sets.get(snap["event_index"].iloc[fut[i]], frozenset())
                    jac[i] = len(a & b) / max(len(a | b), 1)
            same_member_uncond = np.nanmean(np.where(has_fut, jac, 0.0))
            same_member_cond = np.nanmean(jac[has_fut]) if has_fut.any() else np.nan
            st0 = snap["rel_state"].to_numpy()
            st_f = st0[fut.clip(0)]
            st_f[~has_fut] = np.nan
            rel_cond = float(np.nanmean(st_f[has_fut] == st0[has_fut])) if has_fut.any() else np.nan
            rel_uncond = float(np.nanmean((st_f == st0) & has_fut))
            alive = _alive_in_panel(snap, h)
            rows.append({
                "peer_family": fam, "horizon_d": h,
                "n_snapshots": int(n),
                "any_neighborhood_survival": float(has_fut.mean()),
                "alive_in_panel_at_h": _fmt(float(np.nanmean(alive))),
                "same_member_jaccard_cond": _fmt(same_member_cond),
                "same_member_jaccard_uncond": _fmt(same_member_uncond),
                "relational_state_survival_cond": _fmt(rel_cond),
                "relational_state_survival_uncond": _fmt(rel_uncond),
                "peer_family_survival": float(has_fut.mean()),  # family map still emits snapshots
                "lf7_fraction_alive_signal": _fmt(alive_map.get(h, np.nan)),
                "lf7_alive_note": ("DATA_FLOOR_peer_return_notna_approx" if h == 60
                                    else "fwd_cum_availability"),
            })
    df = pd.DataFrame(rows)
    # verdict per family
    verdicts = []
    for fam in FAMILY_ORDER:
        sub = df[df["peer_family"] == fam]
        same60 = sub[sub["horizon_d"] == 60]["same_member_jaccard_cond"].iloc[0]
        any60 = sub[sub["horizon_d"] == 60]["any_neighborhood_survival"].iloc[0]
        rel60 = sub[sub["horizon_d"] == 60]["relational_state_survival_cond"].iloc[0]
        alive = sub[sub["horizon_d"] == 60]["lf7_fraction_alive_signal"].iloc[0]
        v = []
        if same60 < 0.30:
            v.append("A_REJECTED_same_peers_do_not_persist")
        if any60 >= 0.30 and rel60 > same60:
            v.append("B_SUPPORTED_neighborhood_survives_members_rotate")
        if alive >= 0.80 and same60 < 0.30:
            v.append("C_PARTIAL_lf7_60d_alive_figure_is_data_floor_not_membership")
        v.append("D_MIXTURE")
        verdicts.append({"peer_family": fam,
                         "same_member_60d": _fmt(same60),
                         "any_neighborhood_60d": _fmt(any60),
                         "relational_state_60d": _fmt(rel60),
                         "lf7_alive_60d": _fmt(alive),
                         "paradox_resolution": " | ".join(v)})
    return df, pd.DataFrame(verdicts)


# =========================================================================
# 03 RELATIONAL-STATE DEFINITIONS (support)
# =========================================================================

def state_definitions(panels):
    rows = []
    rules = {
        "LOCALLY_CONFORMING": "default: |res_z|<=1.5 and none of the stress conditions",
        "TRUE_ISOLATED": "|res_z|>1.5 AND peer dispersion <= p67 AND abs move >= 2% (real idiosyncratic move)",
        "FALSE_ISOLATED": "|res_z|>1.5 AND peer dispersion <= p67 AND abs move < 2% (sigma-inflated small move)",
        "REORGANIZING": "consecutive-snapshot membership turnover >= p67 (membership churning)",
        "REJOINING": "previous snapshot dislocated (|prev_res_z|>1.5) and residual back <= 1.5 sigma",
        "REHABILITATING": "previous snapshot dislocated and residual back <= 1.0 sigma with low turnover",
        "CONTAGIOUS": "|res_z|>1.0 AND peer dispersion > p67 AND peer abs move > 1% (shared local move)",
        "DECOUPLED": "|res_z|>1.5 persistently (previous snapshot also dislocated or full turnover)",
        "PEER_STRESSED": "peer dispersion >= p67 AND peer abs move >= p67 while asset within 1.5 sigma",
        "DISLOCATED_UNCLASSIFIED": "|res_z|>1.5 not claimed by any named state (honest leftover)",
    }
    for fam in FAMILY_ORDER:
        snap = panels[fam]
        vc = snap["rel_state"].value_counts()
        for st in STATE_ORDER:
            n = int(vc.get(st, 0))
            rows.append({
                "peer_family": fam, "relational_state": st,
                "n_snapshots": n,
                "fraction": _fmt(n / max(len(snap), 1)),
                "supported": "YES" if n >= MIN_SUPPORT else "NOT_SUPPORTED",
                "purpose": rules.get(st, ""),
                "pit_safe": "YES",  # assigned from t0 + asset-past only
            })
    return pd.DataFrame(rows)


# =========================================================================
# 04 RELATIONAL-STATE PERSISTENCE
# =========================================================================

def state_persistence(panels, sets_by_fam):
    rows = []
    for fam in FAMILY_ORDER:
        snap = panels[fam].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
        sets = sets_by_fam[fam]
        for h in [1, 3, 7, 14, 30, 60]:
            fut = _future_lookup(snap, h)
            has = fut >= 0
            st0 = snap["rel_state"].to_numpy()
            st_f = st0[fut.clip(0)]
            jac = np.full(len(snap), np.nan)
            for i in range(len(snap)):
                if has[i]:
                    a = sets.get(snap["event_index"].iloc[i], frozenset())
                    b = sets.get(snap["event_index"].iloc[fut[i]], frozenset())
                    jac[i] = len(a & b) / max(len(a | b), 1)
            for st in STATE_ORDER:
                m = st0 == st
                if not m.any():
                    continue
                mf = m & has
                rel_cond = float(np.nanmean(st_f[mf] == st)) if mf.any() else np.nan
                jac_cond = float(np.nanmean(jac[mf])) if mf.any() else np.nan
                rows.append({
                    "peer_family": fam, "relational_state": st, "horizon_d": h,
                    "n": int(m.sum()),
                    "n_with_future": int(mf.sum()),
                    "relational_state_persistence_cond": _fmt(rel_cond),
                    "exact_membership_jaccard_cond": _fmt(jac_cond),
                    "rel_vs_member_ratio": _fmt(rel_cond / jac_cond if jac_cond and rel_cond else np.nan),
                    "relational_state_persistence_uncond": _fmt(
                        float(np.nanmean((st_f == st) & has)) if m.any() else np.nan),
                })
    return pd.DataFrame(rows)


# =========================================================================
# 05 PEER MEMBERSHIP ENTROPY
# =========================================================================

def _window_top_peer(snap, sets, w):
    """Modal peer within each snapshot's trailing w-day window (per asset)."""
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    top = np.full(len(snap), np.nan, dtype=object)
    for cid, g in snap.groupby("cmc_id", sort=False):
        dates = g["historical_date"].to_numpy()
        pos = g.index.to_numpy()
        eis = g["event_index"].to_numpy()
        for i in range(len(g)):
            lo = dates[i] - pd.Timedelta(days=w)
            cnt = Counter()
            for j in range(i, -1, -1):
                if dates[j] < lo:
                    break
                cnt.update(sets.get(eis[j], ()))
            if cnt:
                top[pos[i]] = cnt.most_common(1)[0][0]
    return top


def membership_entropy(panels, sets_by_fam):
    rows = []
    for fam in FAMILY_ORDER:
        snap = panels[fam].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
        sets = sets_by_fam[fam]
        for w in [7, 14, 30, 60]:
            top = _window_top_peer(snap, sets, w)
            first_of_asset = snap.groupby("cmc_id").cumcount() == 0
            prev_top = np.array([None] + list(top[:-1]), dtype=object)
            dom_persist = float(np.nanmean([
                (t == p) for t, p in zip(top[~first_of_asset.to_numpy()],
                                         prev_top[~first_of_asset.to_numpy()])
                if t is not None and p is not None and not (isinstance(t, float) and np.isnan(t))]))
            col_u, col_e, col_c, col_ent, col_t = (f"unique_peers_{w}d", f"eff_peers_{w}d",
                                                   f"conc_{w}d", f"entropy_{w}d",
                                                   "turnover_prev")
            rows.append({
                "peer_family": fam, "window_d": w,
                "median_unique_peers": _fmt(snap[col_u].median()),
                "median_effective_peers": _fmt(snap[col_e].median()),
                "median_concentration": _fmt(snap[col_c].median()),
                "median_entropy_bits": _fmt(snap[col_ent].median()),
                "mean_membership_turnover": _fmt(snap[col_t].mean()),
                "dominant_member_persistence": _fmt(dom_persist),
                "n_snapshots": int(len(snap)),
            })
    # concentration-vs-diffusion: early vs late entropy per asset (30d window)
    conc_rows = []
    for fam in FAMILY_ORDER:
        snap = panels[fam].sort_values(["cmc_id", "historical_date"])
        for cid, g in snap.groupby("cmc_id", sort=False):
            if len(g) < 4:
                continue
            mid = len(g) // 2
            e_early = g["entropy_30d"].iloc[:mid].median()
            e_late = g["entropy_30d"].iloc[mid:].median()
            conc_rows.append({"peer_family": fam, "asset_id": cid,
                              "entropy_early_bits": e_early, "entropy_late_bits": e_late,
                              "diff_late_minus_early": (e_late - e_early) if pd.notna(e_late) and pd.notna(e_early) else np.nan})
    cd = pd.DataFrame(conc_rows)
    trend = []
    for fam in FAMILY_ORDER:
        sub = cd[cd["peer_family"] == fam]["diff_late_minus_early"].dropna()
        if len(sub) < 30:
            trend.append({"peer_family": fam, "verdict": "NOT_SUPPORTED",
                          "median_entropy_drift_bits": np.nan, "n_assets": int(len(sub))})
            continue
        w, p = ranksums(sub[sub < 0], sub[sub > 0]) if (sub < 0).any() and (sub > 0).any() else (np.nan, np.nan)
        drift = float(sub.median())
        verdict = "CONCENTRATING" if drift < -0.05 else ("DIFFUSING" if drift > 0.05 else "STABLE")
        trend.append({"peer_family": fam, "verdict": verdict,
                      "median_entropy_drift_bits": _fmt(drift),
                      "frac_assets_concentrating": _fmt((sub < 0).mean()),
                      "n_assets": int(len(sub))})
    return pd.DataFrame(rows), pd.DataFrame(trend)


# =========================================================================
# 06 PEER-STATE LATTICE
# =========================================================================

def peer_state_lattice(panels):
    snap = panels[C.PRIMARY_FAMILY]
    rows = []
    for (mc, st), g in snap.groupby(["membership_class", "rel_state"]):
        if len(g) < MIN_SUPPORT:
            continue
        rows.append({
            "membership_stability": mc, "relational_state": st,
            "n": int(len(g)),
            "median_abs_shock": _fmt(g["abs_ret"].median()),
            "median_sigma_shock": _fmt(g["z1"].median()),
            "median_rank": _fmt(g["rank"].median(), 0),
            "median_state_age_d": _fmt(g["state_age_d"].median()),
            "p_recovery_30d": _fmt(g["recover1s30"].mean()),
            "p_contagion_7d": _fmt(g["out_contagion"].mean()),
            "p_decoupling_30d": _fmt(g["out_decouple"].mean()),
            "p_rejoin_30d": _fmt(g["out_rejoin"].mean()),
        })
    return pd.DataFrame(rows)


# =========================================================================
# 07 NEIGHBORHOOD LIFECYCLE
# =========================================================================

def _lifecycle_stage(row):
    gap = row["days_since_prev"]
    if pd.isna(gap) or gap >= 60:
        return "FORMATION"
    mc = row["membership_class"]
    if mc == "ROTATING_MEMBERS":
        return "MEMBERSHIP_ROTATION"
    if row["peer_stress"] == 1 or row["abs_ret"] >= 0.10:
        return "STRESS"
    st = row["rel_state"]
    if st == "DECOUPLED":
        return "DECOUPLING"
    if st in ("REJOINING", "REHABILITATING"):
        return "REJOIN"
    if mc == "STABLE_MEMBERS" and st in ("LOCALLY_CONFORMING", "TRUE_ISOLATED"):
        return "STABLE_LOCAL_ROLE"
    return "TRANSITION"


def neighborhood_lifecycle(panels):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    snap["stage"] = snap.apply(_lifecycle_stage, axis=1)
    # clock: days until next snapshot (episode duration); dissolution = gaps >= 60d
    nxt = snap.groupby("cmc_id")["historical_date"].shift(-1)
    snap["stage_duration_d"] = (nxt - snap["historical_date"]).dt.days
    snap["reconstitution"] = ((snap["stage"] == "FORMATION")
                              & (snap["days_since_prev"] >= 60)).astype(int)
    clocks = []
    for st, g in snap.groupby("stage"):
        dur = g["stage_duration_d"].dropna()
        clocks.append({
            "stage": st, "n_episodes": int(len(g)),
            "n_terminated": int(dur.notna().sum()),
            "median_duration_d": _fmt(dur.median()), "mean_duration_d": _fmt(dur.mean()),
            "p25_duration_d": _fmt(dur.quantile(0.25)), "p75_duration_d": _fmt(dur.quantile(0.75)),
        })
    # transition probabilities between consecutive snapshots (empirical)
    prev_stage = snap.groupby("cmc_id")["stage"].shift()
    trans = []
    for (a, b), g in snap[prev_stage.notna()].groupby([prev_stage, snap["stage"]]):
        trans.append({"from_stage": a, "to_stage": b, "n": int(len(g))})
    tdf = pd.DataFrame(trans)
    if len(tdf):
        tot = tdf.groupby("from_stage")["n"].transform("sum")
        tdf["p_transition"] = (tdf["n"] / tot).round(4)
    return pd.DataFrame(clocks), tdf, snap


# =========================================================================
# 08 PEER FORMATION / DISSOLUTION CLOCKS (temporal lenses)
# =========================================================================

LENS = [-7, -3, -1, 0, 1, 3, 7, 14, 30]


def formation_dissolution_clocks(panels):
    snap = panels[C.PRIMARY_FAMILY]
    sub = pd.read_parquet(C.SUBSTRATE, columns=["cmc_id", "historical_date", "ret_1d",
                                                "vol_30d", "rank_vel_7d", "sigma_t0",
                                                "top500_breadth_30d", "top500_dispersion_30d"])
    sub["historical_date"] = pd.to_datetime(sub["historical_date"])
    sub = sub.rename(columns={"ret_1d": "abs_ret_sub"})
    sub["abs_ret_sub"] = sub["abs_ret_sub"].abs()
    event_types = {
        "HIGH_TURNOVER": snap["roll_turnover_30d"] >= snap["roll_turnover_30d"].quantile(0.67),
        "LOW_TURNOVER": snap["roll_turnover_30d"] <= snap["roll_turnover_30d"].quantile(0.33),
        "LONER": snap["is_true_loner"] == 1,
        "CONTAGION": snap["out_contagion"] == 1,
        "REJOIN": snap["out_rejoin"] == 1,
        "DECOUPLING": snap["out_decouple"] == 1,
    }
    rows = []
    for etype, mask in event_types.items():
        idx = snap[mask.to_numpy() if hasattr(mask, "to_numpy") else mask]
        if len(idx) < 30:
            continue
        base = idx[["event_index", "cmc_id", "historical_date"]].copy()
        for lag in LENS:
            tgt = base.copy()
            tgt["t_lag"] = tgt["historical_date"] + pd.Timedelta(days=lag)
            m = tgt.merge(sub, left_on=["cmc_id", "t_lag"], right_on=["cmc_id", "historical_date"],
                          how="left")
            snap_lag = _nearest_snapshot(idx, lag)
            rows.append({
                "event_type": etype, "lag_d": lag, "n": int(len(idx)),
                "median_vol_30d": _fmt(m["vol_30d"].median()),
                "median_rank_vel_7d": _fmt(m["rank_vel_7d"].median()),
                "median_abs_move": _fmt(m["abs_ret_sub"].median()),
                "median_breadth": _fmt(m["top500_breadth_30d"].median()),
                "median_dispersion": _fmt(m["top500_dispersion_30d"].median()),
                "median_sigma_t0": _fmt(m["sigma_t0"].median()),
                "median_member_entropy": _fmt(snap_lag["entropy_30d"].median()),
                "median_peer_dispersion": _fmt(snap_lag["peer_std_ret"].median()),
                "median_member_turnover": _fmt(snap_lag["roll_turnover_30d"].median()),
                "p_state_conforming": _fmt((snap_lag["rel_state"] == "LOCALLY_CONFORMING").mean()),
                "p_state_reorganizing": _fmt((snap_lag["rel_state"] == "REORGANIZING").mean()),
            })
    return pd.DataFrame(rows)


def _nearest_snapshot(snap, lag, tol=3):
    """Nearest snapshot per row within [t+lag-tol, t+lag+tol]; NaN row otherwise.
    Returns a frame with the same index as the input, filled from the snapshot
    series of the input itself (which must be a subset of the full panel)."""
    snap = snap.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    n = len(snap)
    fut = np.full(n, -1)
    for cid, g in snap.groupby("cmc_id", sort=False):
        dates = g["historical_date"].to_numpy()
        pos = g.index.to_numpy()
        m = len(g)
        lo_d = dates + pd.Timedelta(days=lag - tol)
        hi_d = dates + pd.Timedelta(days=lag + tol)
        j = 0
        for i in range(m):
            if j <= i:
                j = i + 1
            while j < m and dates[j] < lo_d[i]:
                j += 1
            if j < m and dates[j] <= hi_d[i]:
                fut[pos[i]] = pos[j]
    keep = ["entropy_30d", "peer_std_ret", "roll_turnover_30d", "rel_state"]
    res = snap.iloc[fut.clip(0)][keep].copy()
    res.index = snap.index
    res.loc[fut < 0] = np.nan
    return res


# =========================================================================
# 09 STATIC vs ROLLING PEERS
# =========================================================================

def _peer_cum_fwd(ei, t, members, h, dpos, apos, dates, R):
    di = dpos.get(t)
    if di is None or not members:
        return np.nan
    t_ = dates[di]
    hi = di
    while hi + 1 < len(dates) and dates[hi + 1] <= t_ + pd.Timedelta(days=h):
        hi += 1
    vals = []
    for pid in members:
        ai = apos.get(pid)
        if ai is None:
            continue
        v = np.nansum(R[di + 1:hi + 1, ai])
        if np.isfinite(v):
            vals.append(v)
    return float(np.median(vals)) if vals else np.nan


def static_vs_rolling(panels, sets_by_fam):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    sets = sets_by_fam[C.PRIMARY_FAMILY]
    dates, assets, R = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    rows = []
    for h in [1, 3, 7, 14, 30]:
        fut = _future_lookup(snap, h)
        static = np.full(len(snap), np.nan)
        rolling = np.full(len(snap), np.nan)
        asset_cum = snap[f"signed_fwd{h}"].to_numpy() if f"signed_fwd{h}" in snap else np.full(len(snap), np.nan)
        for i in range(len(snap)):
            t = snap["historical_date"].iloc[i]
            ei = snap["event_index"].iloc[i]
            static[i] = _peer_cum_fwd(ei, t, sets.get(ei, ()), h, dpos, apos, dates, R)
            if fut[i] >= 0:
                fei = snap["event_index"].iloc[fut[i]]
                rolling[i] = _peer_cum_fwd(fei, t, sets.get(fei, ()), h, dpos, apos, dates, R)
        # hybrid: static for h<=7, rolling for h>7 (frozen then rolling)
        hybrid = static.copy()
        if h > 7:
            hybrid = np.where(np.isfinite(rolling), rolling, static)
        for view, vec in [("STATIC_T0_PEERS", static), ("ROLLING_PEERS", rolling),
                          ("HYBRID_FROZEN_THEN_ROLLING", hybrid)]:
            ok = np.isfinite(vec) & np.isfinite(asset_cum)
            corr = float(np.corrcoef(vec[ok], asset_cum[ok])[0, 1]) if ok.sum() >= 30 else np.nan
            resid = (asset_cum - vec)[ok]
            sign_agree = float((np.sign(vec[ok]) == np.sign(asset_cum[ok])).mean()) if ok.any() else np.nan
            rows.append({
                "view": view, "horizon_d": h, "n": int(ok.sum()),
                "corr_with_asset_fwd": _fmt(corr),
                "residual_std": _fmt(resid.std()),
                "sign_agreement": _fmt(sign_agree),
                "median_basket_fwd": _fmt(np.nanmedian(vec)),
            })
    return pd.DataFrame(rows)


# =========================================================================
# 10 PEER REORGANIZATION RESPONSE CURVES
# =========================================================================

def response_curves(panels):
    snap = panels[C.PRIMARY_FAMILY].copy()
    snap["abs_class"] = snap["abs_ret"].map(_abs_class)
    snap["sigma_class"] = snap["z1"].map(_sigma_class)
    snap["vol_decile"] = pd.qcut(snap["vol_30d"].rank(method="first"), 5,
                                 labels=["V1", "V2", "V3", "V4", "V5"])
    snap["rankvel_bin"] = pd.qcut(snap["rank_vel_30d"].rank(method="first"), 5,
                                   labels=["RV1", "RV2", "RV3", "RV4", "RV5"])
    drivers = [
        ("VOL_AMPLITUDE", "vol_decile"),
        ("ABS_SHOCK", "abs_class"),
        ("SIGMA_SHOCK", "sigma_class"),
        ("RANK_MIGRATION", "rankvel_bin"),
        ("FIELD_STATE", "cell4"),
    ]
    rows = []
    for dname, col in drivers:
        for x, g in snap.groupby(col):
            if len(g) < 30:
                continue
            y = g["roll_turnover_30d"].dropna()
            if len(y) < 30:
                continue
            rows.append({
                "driver": dname, "driver_level": str(x),
                "n": int(len(g)),
                "p10_turnover": _fmt(y.quantile(0.10)), "p25_turnover": _fmt(y.quantile(0.25)),
                "median_turnover": _fmt(y.median()), "p75_turnover": _fmt(y.quantile(0.75)),
                "p90_turnover": _fmt(y.quantile(0.90)),
            })
    df = pd.DataFrame(rows)
    # verdicts per driver: shape classification from ordered level medians +
    # raw spearman for monotone drivers
    verdicts = []
    order_map = {"ABS_SHOCK": [a for a, _, _ in ABS_CLASSES],
                 "SIGMA_SHOCK": [s for s, _, _ in SIGMA_CLASSES],
                 "FIELD_STATE": ["LL", "LH", "HL", "HH"]}
    for dname, col in drivers:
        sub = df[df["driver"] == dname]
        ok = np.isfinite(snap["roll_turnover_30d"].to_numpy())
        yv = snap["roll_turnover_30d"].to_numpy()[ok]
        if dname in ("VOL_AMPLITUDE", "RANK_MIGRATION"):
            xv = snap[col].cat.codes.to_numpy()[ok]
        else:
            xv = snap[col].map({v: i for i, v in enumerate(order_map[dname])}).to_numpy()[ok]
        rho, p = spearmanr(xv, yv)
        rho = float(rho) if np.isfinite(rho) else np.nan
        p = float(p) if np.isfinite(p) else np.nan
        if dname in order_map:
            sub = sub.set_index("driver_level").reindex(order_map[dname]).dropna(subset=["median_turnover"])
        else:
            sub = sub.sort_values("driver_level")
        if len(sub) < 3:
            sh = "NO_STABLE_RELATION"
        else:
            meds = sub["median_turnover"].to_numpy(dtype=float)
            d = np.diff(meds)
            d = d[np.isfinite(d)]
            if len(d) < 2:
                sh = "NO_STABLE_RELATION"
            elif d[0] * d[-1] < 0 or (d[0] * d[1] < 0):
                sh = "NON_MONOTONIC"
            elif abs(rho) < 0.15 or not np.isfinite(p) or p > 0.05:
                sh = "NO_STABLE_RELATION"
            elif abs(d[1]) > 2.5 * max(abs(d[0]), 1e-9) and d[0] * d[1] > 0:
                sh = "THRESHOLD"
            elif abs(d[0]) > abs(d[1]) > 0 and d[0] * d[1] > 0:
                sh = "SATURATING"
            else:
                sh = "LINEAR"
        verdicts.append({"driver": dname, "shape": sh,
                         "spearman_rho": _fmt(rho), "spearman_p": _fmt(p, 3),
                         "n_levels": int(len(sub))})
    return df, pd.DataFrame(verdicts)


# =========================================================================
# 11 REORGANIZATION TIMING (pairwise ordering)
# =========================================================================

def reorg_timing(panels):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    sub = pd.read_parquet(C.SUBSTRATE, columns=["cmc_id", "historical_date", "ret_1d",
                                                "vol_30d", "rank_vel_7d", "sigma_t0"])
    sub["historical_date"] = pd.to_datetime(sub["historical_date"])
    sub = sub.rename(columns={"ret_1d": "abs_ret_sub"})
    sub["abs_ret_sub"] = sub["abs_ret_sub"].abs()
    hi_turn = snap["roll_turnover_30d"] >= snap["roll_turnover_30d"].quantile(0.67)
    anchors = snap[hi_turn].copy().reset_index(drop=True)
    flags = ["VOL_EXPANSION", "ABS_SHOCK", "SIGMA_SHOCK", "RANK_MIGRATION",
             "MEMBERSHIP_TURNOVER", "RELATIONAL_STATE_CHANGE", "CONTAGION",
             "REJOIN", "DECOUPLING"]
    first_lag = {f: np.full(len(anchors), np.nan) for f in flags}
    snap["_prev_state"] = snap.groupby("cmc_id")["rel_state"].shift()
    vol_ref = np.nanmedian(snap["vol_30d"])
    p90_rv = np.nanquantile(snap["rank_vel_7d"].abs(), 0.90)
    p67_turn = np.nanquantile(snap["roll_turnover_30d"], 0.67)
    p67_pstd = np.nanquantile(snap["peer_std_ret"], 0.67)
    for i, row in anchors.iterrows():
        cid, t = row["cmc_id"], row["historical_date"]
        for lag in [-3, -2, -1, 0, 1, 2, 3]:
            tl = t + pd.Timedelta(days=lag)
            srow = sub[(sub["cmc_id"] == cid) & (sub["historical_date"] == tl)]
            sn = snap[(snap["cmc_id"] == cid) & (snap["historical_date"] == tl)]
            if len(srow):
                r = srow.iloc[0]
                if r["vol_30d"] >= 1.5 * vol_ref and not np.isfinite(first_lag["VOL_EXPANSION"][i]):
                    first_lag["VOL_EXPANSION"][i] = lag
                if r["abs_ret_sub"] >= 0.02 and not np.isfinite(first_lag["ABS_SHOCK"][i]):
                    first_lag["ABS_SHOCK"][i] = lag
                if r["sigma_t0"] >= 2 and not np.isfinite(first_lag["SIGMA_SHOCK"][i]):
                    first_lag["SIGMA_SHOCK"][i] = lag
                if abs(r["rank_vel_7d"]) >= p90_rv and not np.isfinite(first_lag["RANK_MIGRATION"][i]):
                    first_lag["RANK_MIGRATION"][i] = lag
            if len(sn):
                r = sn.iloc[0]
                if r["roll_turnover_30d"] >= p67_turn and not np.isfinite(first_lag["MEMBERSHIP_TURNOVER"][i]):
                    first_lag["MEMBERSHIP_TURNOVER"][i] = lag
                ps = r.get("_prev_state")
                if ps is not None and pd.notna(ps) and ps != r["rel_state"] and not np.isfinite(first_lag["RELATIONAL_STATE_CHANGE"][i]):
                    first_lag["RELATIONAL_STATE_CHANGE"][i] = lag
                if r["rel_state"] in ("CONTAGIOUS", "PEER_STRESSED") and not np.isfinite(first_lag["CONTAGION"][i]):
                    first_lag["CONTAGION"][i] = lag
                if r["rel_state"] in ("REJOINING", "REHABILITATING") and not np.isfinite(first_lag["REJOIN"][i]):
                    first_lag["REJOIN"][i] = lag
                if r["rel_state"] == "DECOUPLED" and not np.isfinite(first_lag["DECOUPLING"][i]):
                    first_lag["DECOUPLING"][i] = lag
    fl = pd.DataFrame(first_lag, index=anchors.index)
    counts = fl.notna().sum()
    rows = []
    for f in flags:
        rows.append({"flag": f, "n_detected": int(counts[f]),
                     "median_first_lag": _fmt(fl[f].median()),
                     "mean_first_lag": _fmt(fl[f].mean())})
    # pairwise precedence: fraction of anchors where X first precedes Y
    pw = []
    for x in flags:
        for y in flags:
            if x == y:
                continue
            both = fl[[x, y]].dropna()
            if len(both) < 30:
                continue
            prec = float((both[x] < both[y]).mean())
            pw.append({"flag_x": x, "flag_y": y, "n_both": int(len(both)),
                       "p_x_before_y": _fmt(prec)})
    return pd.DataFrame(rows), pd.DataFrame(pw)


# =========================================================================
# 12 PEER REORGANIZATION ENTROPY
# =========================================================================

def reorg_entropy(panels, sets_by_fam):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    hi = snap["roll_turnover_30d"] >= snap["roll_turnover_30d"].quantile(0.67)
    anchors = snap[hi].reset_index(drop=True)
    pre = _nearest_snapshot(anchors, -7, tol=4)
    post = _nearest_snapshot(anchors, 7, tol=4)
    post14 = _nearest_snapshot(anchors, 14, tol=4)
    # label entropy of asset's own state distribution inside window
    def label_entropy(anchor_df, lag, tol=4):
        out = []
        for _, row in anchor_df.iterrows():
            t = row["historical_date"] + pd.Timedelta(days=lag)
            g = snap[(snap["cmc_id"] == row["cmc_id"])
                     & (snap["historical_date"] >= t - pd.Timedelta(days=tol))
                     & (snap["historical_date"] <= t + pd.Timedelta(days=tol))]
            if len(g) == 0:
                out.append(np.nan)
            else:
                out.append(C._entropy_series(g["rel_state"].value_counts().to_numpy()))
        return np.array(out)
    le_during = label_entropy(anchors, 0)
    le_pre = label_entropy(anchors, -7)
    le_post = label_entropy(anchors, 14)
    # peer-family disagreement at anchor event (mean 1-Jaccard across family pairs)
    fam_sets = {f: sets_by_fam[f] for f in FAMILY_ORDER}
    disagreement = []
    for ei in anchors["event_index"]:
        vals = []
        fams = [f for f in FAMILY_ORDER if ei in fam_sets[f]]
        for a in range(len(fams)):
            for b in range(a + 1, len(fams)):
                sa, sb = fam_sets[fams[a]][ei], fam_sets[fams[b]][ei]
                vals.append(1 - len(sa & sb) / max(len(sa | sb), 1))
        disagreement.append(float(np.mean(vals)) if vals else np.nan)
    disagreement = np.array(disagreement)
    # reconstitution: entropy at first snapshot after turnover back below p50
    recon_entropy = []
    for _, row in anchors.iterrows():
        g = snap[(snap["cmc_id"] == row["cmc_id"])
                 & (snap["historical_date"] > row["historical_date"])].sort_values("historical_date")
        g = g[g["roll_turnover_30d"] <= snap["roll_turnover_30d"].quantile(0.5)]
        if len(g):
            recon_entropy.append(g.iloc[0]["entropy_30d"])
        else:
            recon_entropy.append(np.nan)
    recon_entropy = np.array(recon_entropy)
    during_ent = anchors["entropy_30d"].to_numpy()
    rows = [{
        "metric": "membership_entropy_30d", "n": int(len(anchors)),
        "pre_median": _fmt(pre["entropy_30d"].median()),
        "during_median": _fmt(np.nanmedian(during_ent)),
        "post_median": _fmt(post["entropy_30d"].median()),
    }]
    rows.append({
        "metric": "relational_label_entropy",
        "n": int(len(anchors)),
        "pre_median": _fmt(np.nanmedian(le_pre)), "during_median": _fmt(np.nanmedian(le_during)),
        "post_median": _fmt(np.nanmedian(le_post)),
    })
    rows.append({
        "metric": "peer_family_disagreement", "n": int(len(anchors)),
        "pre_median": np.nan, "during_median": _fmt(np.nanmedian(disagreement)), "post_median": np.nan,
    })
    rows.append({
        "metric": "peer_residual_dispersion", "n": int(len(anchors)),
        "pre_median": _fmt(pre["peer_std_ret"].median()),
        "during_median": _fmt(anchors["peer_std_ret"].median()),
        "post_median": _fmt(post["peer_std_ret"].median()),
    })
    rows.append({
        "metric": "entropy_after_reconstitution", "n": int(len(anchors)),
        "pre_median": np.nan, "during_median": np.nan,
        "post_median": _fmt(np.nanmedian(recon_entropy)),
    })
    d = pd.DataFrame(rows)
    # does reconstitution lower entropy below the during-reorg level?
    frac_lower = float(np.nanmean(recon_entropy < during_ent))
    verdict = "RECONSTITUTION_LOWERS_ENTROPY" if frac_lower >= 0.55 else "NO_CLEAR_RECONSTITUTION_DROP"
    return d, verdict, anchors, pre, post, post14, le_pre, le_during, le_post, disagreement, recon_entropy


# =========================================================================
# 13 RELATIONAL vs FIELD ENTROPY
# =========================================================================

def relational_vs_field_entropy(panels):
    snap = panels[C.PRIMARY_FAMILY].copy()
    age = C7_age_in_cell()
    snap = snap.merge(age, on=["cmc_id", "historical_date"], how="left")
    snap["age_band"] = snap["age_in_cell"].map(lambda a: "AGE_1" if a == 1 else
                                               ("AGE_2_3" if a <= 3 else ("AGE_4_7" if a <= 7 else
                                                ("AGE_8_14" if a <= 14 else "AGE_15_PLUS"))))
    rel_ent = []
    for (c4, ab), g in snap.groupby(["cell4", "age_band"]):
        if len(g) < 30:
            continue
        rel_ent.append({"cell4": c4, "age_band": ab, "n_snapshots": int(len(g)),
                        "relational_state_entropy": C._entropy_series(g["rel_state"].value_counts().to_numpy()),
                        "membership_entropy_median": float(g["entropy_30d"].median())})
    rel = pd.DataFrame(rel_ent)
    try:
        field = pd.read_csv(M12 / "08_CONSTRAINT_RESOLUTION_ENTROPY.csv")
        field = field[field["scope"] == "cell_age"][["cell", "age_band", "branch_entropy"]]
    except Exception:
        return pd.DataFrame(), pd.DataFrame([{"join": "DATA_BLOCKED", "detail": "mech_12 constraint entropy unavailable"}])
    cellmap = {"HH": "HIGH_BREADTH_HIGH_DISP", "HL": "HIGH_BREADTH_LOW_DISP",
               "LH": "LOW_BREADTH_HIGH_DISP", "LL": "LOW_BREADTH_LOW_DISP"}
    rel["cell"] = rel["cell4"].map(cellmap)
    joined = rel.merge(field, on=["cell", "age_band"], how="inner")
    joined["field_entropy"] = joined["branch_entropy"]
    rows = []
    for _, g in joined.groupby(["cell4", "age_band"]):
        rows.append(g.iloc[0].to_dict())
    out = pd.DataFrame(rows)
    if len(out) >= 10:
        rho, p = spearmanr(out["field_entropy"], out["relational_state_entropy"])
        fmed, rmed = out["field_entropy"].median(), out["relational_state_entropy"].median()
        tighten = ((out["field_entropy"] < fmed) & (out["relational_state_entropy"] > rmed)).sum()
        verdict = pd.DataFrame([{
            "join_grain": "CELL_x_AGE_BAND", "date_grain_join": "DATA_BLOCKED",
            "n_cells": int(len(out)), "spearman_field_vs_relational": _fmt(rho),
            "spearman_p": _fmt(p, 3),
            "n_field_constraint_tightening_relational_rising": int(tighten),
            "interpretation": "GLOBAL_CONSTRAINT_TIGHTENING_with_LOCAL_IDENTITY_REORGANIZATION" if tighten > 0 else "NO_DIVERGENT_CELLS",
        }])
    else:
        verdict = pd.DataFrame([{"join_grain": "CELL_x_AGE_BAND", "date_grain_join": "DATA_BLOCKED",
                                 "n_cells": int(len(out)), "detail": "insufficient joined cells"}])
    return out, verdict


def C7_age_in_cell():
    import lf7_common as C7
    return C7.load_age_in_cell()


# =========================================================================
# 14 FALSE-LONER DECOMPOSITION
# =========================================================================

def false_loner_decomposition(panels):
    snap = panels[C.PRIMARY_FAMILY]
    fl = snap[snap["is_false_loner"] == 1].copy()
    if len(fl) == 0:
        return pd.DataFrame([{"verdict": "DATA_BLOCKED", "n": 0}])
    p67_turn = fl["roll_turnover_30d"].quantile(0.67)
    fl["subtype"] = "MIXED"
    cond = {
        "MEASUREMENT_EDGE": (fl["peer_count"] < 5) | (fl.get("flag_any_quality", pd.Series(False, index=fl.index)).fillna(False)),
        "LOW_VOL_NORMALIZATION_ARTIFACT": (fl["abs_ret"] < 0.02) & (fl["peer_abs_med"] < 0.02),
        "TRUE_SHARED_LOCAL_MOVE": (fl["abs_ret"] >= 0.02) & (fl["peer_abs_med"] >= 0.02),
        "PEER_REORGANIZATION_EVENT": fl["roll_turnover_30d"] >= p67_turn,
    }
    n_true = pd.Series(0, index=fl.index, dtype=int)
    for name, m in cond.items():
        n_true = n_true + m.astype(int)
    for name in ["MEASUREMENT_EDGE", "LOW_VOL_NORMALIZATION_ARTIFACT",
                 "TRUE_SHARED_LOCAL_MOVE", "PEER_REORGANIZATION_EVENT"]:
        fl.loc[cond[name] & (n_true == 1), "subtype"] = name
    rows = []
    for st, g in fl.groupby("subtype"):
        rows.append({
            "subtype": st, "n": int(len(g)),
            "supported": "YES" if len(g) >= MIN_SUPPORT else "NOT_SUPPORTED",
            "median_abs_move": _fmt(g["abs_ret"].median()),
            "median_sigma": _fmt(g["z1"].median()),
            "median_peer_abs_move": _fmt(g["peer_abs_med"].median()),
            "median_membership_entropy": _fmt(g["entropy_30d"].median()),
            "median_peer_turnover": _fmt(g["roll_turnover_30d"].median()),
            "field_state_mode": str(g["cell4"].mode().iloc[0]) if len(g) else "",
            "relational_state_mode": str(g["rel_state"].mode().iloc[0]) if len(g) else "",
        })
    return pd.DataFrame(rows)


# =========================================================================
# 15 TRUE-LONER SUBTYPES
# =========================================================================

def true_loner_subtypes(panels):
    snap = panels[C.PRIMARY_FAMILY]
    tl = snap[snap["is_true_loner"] == 1].copy()
    tl["subtype"] = "MIXED_OTHER"
    cond = {
        "FULL_REHABILITATION": (tl["out_rejoin"] == 1) & (tl["rank_up_30"] == 1),
        "RANK_HEALTH_FAILURE": (tl["price_up_30"] == 1) & (tl["rank_up_30"] == 0),
        "EARLY_CONTAGION": tl["out_contagion"] == 1,
        "PERSISTENT_DECOUPLING": tl["out_decouple"] == 1,
        "REJOINING_DISLOCATION": tl["st4_30"] == "REJOINING",
        "LOCAL_EXTREME_WITH_FIELD_SUPPORT": tl["abs_ret"] >= 0.10,
    }
    n_true = pd.Series(0, index=tl.index, dtype=int)
    for name, m in cond.items():
        n_true = n_true + m.astype(int)
    for name in cond:
        tl.loc[cond[name] & (n_true == 1), "subtype"] = name
    rows = []
    for st, g in tl.groupby("subtype"):
        rows.append({
            "subtype": st, "n": int(len(g)),
            "supported": "YES" if len(g) >= MIN_SUPPORT else "NOT_SUPPORTED",
            "median_abs_move": _fmt(g["abs_ret"].median()),
            "median_sigma": _fmt(g["z1"].median()),
            "p_recovery_30d": _fmt(g["recover1s30"].mean()),
            "p_rank_repair_30d": _fmt(g["out_rank_repair"].mean()),
            "median_state_age_d": _fmt(g["state_age_d"].median()),
            "median_membership_turnover": _fmt(g["roll_turnover_30d"].median()),
            "relational_state_mode": str(g["rel_state"].mode().iloc[0]) if len(g) else "",
        })
    return pd.DataFrame(rows)


# =========================================================================
# 16 REJOIN / CONTAGION / DECOUPLING LATTICE
# =========================================================================

def rejoin_contagion_lattice(panels):
    snap = panels[C.PRIMARY_FAMILY].copy()
    snap["abs_class"] = snap["abs_ret"].map(_abs_class)
    snap["sigma_class"] = snap["z1"].map(_sigma_class)
    snap["loner"] = np.select([snap["is_true_loner"] == 1, snap["is_false_loner"] == 1],
                              ["TRUE_LONER", "FALSE_LONER"], default="NOT_LONER")
    rows = []
    dropped = 0
    for (lon, st, ac, sc), g in snap.groupby(["loner", "rel_state", "abs_class", "sigma_class"]):
        if len(g) < MIN_SUPPORT:
            dropped += len(g)
            continue
        rows.append({
            "loner": lon, "relational_state": st, "abs_class": ac, "sigma_class": sc,
            "n": int(len(g)),
            "p_rejoin": _fmt(g["out_rejoin"].mean()),
            "p_contagion": _fmt(g["out_contagion"].mean()),
            "p_decoupling": _fmt(g["out_decouple"].mean()),
            "p_relapse": _fmt(g["out_relapse"].mean()),
            "p_rank_repair": _fmt(g["out_rank_repair"].mean()),
            "p_price_repair": _fmt(g["out_price_repair"].mean()),
        })
    # hierarchical collapse: coarsen abs x sigma to regain support
    snap["shock_coarse"] = np.select(
        [(snap["z1"] < 3) & (snap["abs_ret"] < 0.05), (snap["z1"] < 3) & (snap["abs_ret"] >= 0.05),
         (snap["z1"] >= 3) & (snap["abs_ret"] < 0.10), (snap["z1"] >= 3) & (snap["abs_ret"] >= 0.10)],
        ["LOW_SIG_LOW_ABS", "LOW_SIG_HIGH_ABS", "HIGH_SIG_LOW_ABS", "HIGH_SIG_HIGH_ABS"],
        default="UNCLASSIFIED")
    collapsed = []
    for (lon, st, sc), g in snap.groupby(["loner", "rel_state", "shock_coarse"]):
        if len(g) < MIN_SUPPORT:
            dropped += len(g)
            continue
        collapsed.append({
            "loner": lon, "relational_state": st, "shock_coarse": sc,
            "n": int(len(g)),
            "p_rejoin": _fmt(g["out_rejoin"].mean()),
            "p_contagion": _fmt(g["out_contagion"].mean()),
            "p_decoupling": _fmt(g["out_decouple"].mean()),
            "p_relapse": _fmt(g["out_relapse"].mean()),
            "p_rank_repair": _fmt(g["out_rank_repair"].mean()),
            "p_price_repair": _fmt(g["out_price_repair"].mean()),
        })
    return (pd.DataFrame(rows), pd.DataFrame(collapsed),
            {"granular_dropped_rows": int(dropped)})


# =========================================================================
# 17 DIRECTIONAL RELATIONAL ASYMMETRY
# =========================================================================

def directional_asymmetry(panels, sets_by_fam):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    sets = sets_by_fam[C.PRIMARY_FAMILY]
    dates, assets, R = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    peer_fwd7 = np.full(len(snap), np.nan)
    for i in range(len(snap)):
        peer_fwd7[i] = _peer_cum_fwd(snap["event_index"].iloc[i], snap["historical_date"].iloc[i],
                                     sets.get(snap["event_index"].iloc[i], ()), 7, dpos, apos, dates, R)
    snap["peer_fwd7"] = peer_fwd7
    snap["peer_fwd30"] = np.nan
    for i in range(len(snap)):
        snap.iloc[i, snap.columns.get_loc("peer_fwd30")] = _peer_cum_fwd(
            snap["event_index"].iloc[i], snap["historical_date"].iloc[i],
            sets.get(snap["event_index"].iloc[i], ()), 30, dpos, apos, dates, R)
    up = snap[snap["event_sign"] > 0]
    dn = snap[snap["event_sign"] < 0]
    rows = []
    for name, fn in [
        ("median_membership_turnover", lambda g: g["roll_turnover_30d"].median()),
        ("median_membership_entropy", lambda g: g["entropy_30d"].median()),
        ("p_rejoin_30d", lambda g: g["out_rejoin"].mean()),
        ("p_contagion_7d", lambda g: g["out_contagion"].mean()),
        ("p_decoupling_30d", lambda g: g["out_decouple"].mean()),
        ("p_peer_catchup", lambda g: (g["peer_fwd7"] > 0).mean()),
        ("p_peer_catchdown", lambda g: (g["peer_fwd7"] < 0).mean()),
        ("p_persistent_outperformance_30d", lambda g: (g["signed_fwd30"] > g["peer_fwd30"]).mean()),
        ("p_persistent_underperformance_30d", lambda g: (g["signed_fwd30"] < g["peer_fwd30"]).mean()),
        ("median_state_age_d", lambda g: g["state_age_d"].median()),
    ]:
        vu = fn(up) if len(up) else np.nan
        vd = fn(dn) if len(dn) else np.nan
        rows.append({"metric": name, "upside": _fmt(vu), "downside": _fmt(vd),
                     "upside_n": int(len(up)), "downside_n": int(len(dn)),
                     "asymmetry_direction": "UPSIDE_STRONGER" if vu > vd else ("DOWNSIDE_STRONGER" if vd > vu else "SYMMETRIC")})
    # direct test on turnover
    stat, p = ranksums(up["roll_turnover_30d"].dropna(), dn["roll_turnover_30d"].dropna()) if len(up) > 20 and len(dn) > 20 else (np.nan, np.nan)
    rows.append({"metric": "ranksum_turnover_asymmetry_p", "upside": np.nan, "downside": np.nan,
                 "upside_n": int(len(up)), "downside_n": int(len(dn)),
                 "asymmetry_direction": f"p={_fmt(p, 3)}" if np.isfinite(p) else "NOT_TESTED"})
    return pd.DataFrame(rows)


# =========================================================================
# 18 / 19 UPSIDE / DOWNSIDE LOCAL ECOLOGY
# =========================================================================

def _ecology(snap, sign):
    """Ecology classes for one sign (snap must carry peer_fwd columns)."""
    sub = snap[snap["event_sign"] * sign > 0].copy()
    catch_name = "PEER_CATCHUP" if sign > 0 else "PEER_CATCHDOWN"
    cond = {
        "TRUE_LONER": sub["is_true_loner"] == 1,
        "FALSE_LONER": sub["is_false_loner"] == 1,
        catch_name: (sub["peer_fwd7"] * sign) > 0.01,
        "LOCAL_CONTAGION": sub["out_contagion"] == 1,
        "PERSISTENT_DECOUPLING": sub["out_decouple"] == 1,
    }
    sub["ecology"] = "OTHER"
    n_true = pd.Series(0, index=sub.index, dtype=int)
    for m in cond.values():
        n_true = n_true + m.fillna(False).astype(int)
    for name, m in cond.items():
        sub.loc[m.fillna(False) & (n_true == 1), "ecology"] = name
    rows = []
    for ec, g in sub.groupby("ecology"):
        rows.append({
            "ecology": ec, "n": int(len(g)),
            "p_membership_stable": _fmt((g["membership_class"] == "STABLE_MEMBERS").mean()),
            "median_membership_entropy": _fmt(g["entropy_30d"].median()),
            "median_member_turnover": _fmt(g["roll_turnover_30d"].median()),
            "field_state_mode": str(g["cell4"].mode().iloc[0]) if len(g) else "",
            "rank_patch_mode": str(g["rank_band"].mode().iloc[0]) if len(g) else "",
            "median_abs_shock": _fmt(g["abs_ret"].median()),
            "median_sigma_shock": _fmt(g["z1"].median()),
            "median_state_age_d": _fmt(g["state_age_d"].median()),
            "p_rejoin_30d": _fmt(g["out_rejoin"].mean()),
            "p_price_repair": _fmt(g["recover1s30"].mean()),
        })
    return pd.DataFrame(rows)


def up_down_ecology(panels, sets_by_fam):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    sets = sets_by_fam[C.PRIMARY_FAMILY]
    dates, assets, R = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    for h in [7, 30]:
        col = f"peer_fwd{h}"
        v = np.full(len(snap), np.nan)
        for i in range(len(snap)):
            v[i] = _peer_cum_fwd(snap["event_index"].iloc[i], snap["historical_date"].iloc[i],
                                 sets.get(snap["event_index"].iloc[i], ()), h, dpos, apos, dates, R)
        snap[col] = v
    return _ecology(snap, +1), _ecology(snap, -1)


# =========================================================================
# 20 / 21 CONTAGION / REJOIN PRIMITIVE AUDITS
# =========================================================================

COORDS = ["roll_turnover_30d", "entropy_30d", "vol_30d", "abs_ret", "z1",
          "rank_vel_7d", "top500_breadth_30d", "state_age_d", "is_true_loner",
          "peer_stress"]


def _purged_auc(snap, outcome, features):
    """3-fold subperiod-purged logistic AUC."""
    sp = snap["subperiod"].dropna().unique()
    if len(sp) < 3:
        sp = snap.index.to_numpy() % 3
        sp = pd.Series(sp, index=snap.index)
    else:
        sp = snap["subperiod"]
    folds = pd.Series(pd.factorize(sp)[0], index=snap.index)
    aucs = []
    for k in range(3):
        tr = folds != k
        te = folds == k
        if tr.sum() < 50 or te.sum() < 20:
            continue
        Xtr = snap.loc[tr, features].fillna(snap[features].median())
        ytr = snap.loc[tr, outcome]
        Xte = snap.loc[te, features].fillna(snap[features].median())
        yte = snap.loc[te, outcome]
        if ytr.nunique() < 2 or yte.nunique() < 2:
            continue
        clf = LogisticRegression(max_iter=1000, C=1.0)
        clf.fit(Xtr, ytr)
        try:
            aucs.append(roc_auc_score(yte, clf.predict_proba(Xte)[:, 1]))
        except ValueError:
            continue
    return float(np.mean(aucs)) if aucs else np.nan


def primitive_audit(panels, outcome, name):
    snap = panels[C.PRIMARY_FAMILY].copy()
    snap = snap.dropna(subset=[outcome])
    rows = []
    singles = {}
    for c in COORDS:
        if snap[c].nunique() < 2 or snap[c].isna().all():
            continue
        auc = _purged_auc(snap, outcome, [c])
        singles[c] = auc
        rows.append({"coordinate": c, "purged_auc_single": _fmt(auc), "n": int(len(snap))})
    best = sorted(singles.items(), key=lambda kv: -kv[1])
    # greedy forward selection (purged AUC; stop when no >= 0.005 gain)
    chosen = []
    remaining = list(singles.keys())
    cur_auc = 0.5
    while remaining and len(chosen) < 4:
        cands = []
        for c in remaining:
            auc = _purged_auc(snap, outcome, chosen + [c])
            cands.append((c, auc))
        c, auc = max(cands, key=lambda kv: kv[1])
        if auc < cur_auc + 0.005:
            break
        chosen.append(c)
        remaining.remove(c)
        cur_auc = auc
    best_auc = singles[best[0][0]] if best else np.nan
    pair_auc = _purged_auc(snap, outcome, [best[0][0], best[1][0]]) if len(best) >= 2 else np.nan
    if best_auc >= 0.65:
        verdict = f"{name}_PRIMITIVE"
    elif pair_auc >= 0.65:
        verdict = "CONDITIONAL_PRIMITIVE"
    elif best_auc >= 0.58:
        verdict = "LOCAL_RULE"
    else:
        verdict = "NO_COMPACT_STRUCTURE"
    rows.append({"coordinate": "BEST_SINGLE", "purged_auc_single": _fmt(best_auc), "n": int(len(snap)),
                 "best_coordinate": best[0][0] if best else ""})
    rows.append({"coordinate": "BEST_PAIR", "purged_auc_single": _fmt(pair_auc), "n": int(len(snap)),
                 "best_pair": " + ".join([b[0] for b in best[:2]]) if len(best) >= 2 else ""})
    rows.append({"coordinate": "GREEDY_SET", "purged_auc_single": _fmt(cur_auc),
                 "n": int(len(snap)), "best_pair": " + ".join(chosen)})
    return pd.DataFrame(rows), verdict


# =========================================================================
# 22 DECOUPLING / DECAY BRIDGE
# =========================================================================

def decoupling_bridge(panels):
    snap = panels[C.PRIMARY_FAMILY]
    dc = snap[snap["out_decouple"] == 1].copy()
    # restrict to events with 90d forward availability
    dc = dc[dc["historical_date"] <= pd.Timestamp("2026-05-23")]
    fwd = C.substrate_forward(dc, horizons=(30, 60, 90))
    # substrate_forward re-emits cmc_id/historical_date; dropping them
    # avoids suffixed duplicate columns (cmc_id_x/_y) after the merge.
    fwd = fwd.drop(columns=["cmc_id", "historical_date"], errors="ignore")
    dc = dc.merge(fwd, on="event_index", how="left")
    rows = []
    for h in [30, 60, 90]:
        price = dc[f"cum_ret_{h}d"]
        rank = dc[f"rank_{h}d"]
        rows.append({
            "horizon_d": h, "n": int(len(dc)),
            "p_price_health": _fmt((price > 0).mean()),
            "p_rank_health": _fmt((rank < dc["rank"]).mean()),
            "median_price_health_cum_ret": _fmt(price.median()),
            "median_rank_at_h": _fmt(rank.median(), 0),
            "median_vol_30d": _fmt(dc["vol_30d"].median()),
            "median_liq_proxy": _fmt(dc["liq_proxy"].median()),
            "median_activity_turnover": _fmt(dc["turnover"].median()),
            "p_activity_positive": _fmt((dc["volume_24h_usd"] > 0).mean()),
        })
    # peer normalization + relational persistence at nearest snapshot >= +30/+60
    dcs = dc.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    for h in [30, 60]:
        fut = _future_lookup(dcs, h)
        has = fut >= 0
        sub = dcs[has]
        futsub = dcs.iloc[fut[has]]
        rows.append({
            "horizon_d": h, "n": int(has.sum()),
            "peer_normalization_median_resz": _fmt(futsub["res_z"].abs().median()),
            "relational_state_persistence": _fmt((futsub["rel_state"].to_numpy() == sub["rel_state"].to_numpy()).mean()),
            "median_membership_entropy_at_h": _fmt(futsub["entropy_30d"].median()),
            "p_rel_state_still_decoupled": _fmt((futsub["rel_state"] == "DECOUPLED").mean()),
        })
    return pd.DataFrame(rows)


# =========================================================================
# 23 PRD AS RELATIONAL HEALTH
# =========================================================================

def prd_relational_health(panels, sets_by_fam):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    sets = sets_by_fam[C.PRIMARY_FAMILY]
    dates, assets, R = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    for h in [7, 14, 30]:
        v = np.full(len(snap), np.nan)
        for i in range(len(snap)):
            v[i] = _peer_cum_fwd(snap["event_index"].iloc[i], snap["historical_date"].iloc[i],
                                 sets.get(snap["event_index"].iloc[i], ()), h, dpos, apos, dates, R)
        snap[f"peer_fwd{h}"] = v
    prd = snap[(snap["price_up_14"] == 1) & (snap["rank_up_14"] == 0)].copy()
    prd["abs_class"] = prd["abs_ret"].map(_abs_class)
    prd["sigma_class"] = prd["z1"].map(_sigma_class)
    prd["peer_dir"] = np.select([prd["peer_fwd14"] > 0, prd["peer_fwd14"] < 0],
                                ["PEER_UP", "PEER_DOWN"], default="PEER_FLAT")
    prd["subtype"] = ""
    prd["BETA_RESCUE"] = ((prd["top500_breadth_30d"] > 0) & (prd["peer_dir"] == "PEER_UP")
                          & (prd["signed_fwd14"] <= prd["peer_fwd14"])).astype(int)
    prd["PEER_RESCUE"] = ((prd["peer_dir"] == "PEER_UP") & (prd["signed_fwd14"] <= prd["peer_fwd14"])).astype(int)
    prd["RELATIVE_DECAY"] = ((prd["peer_dir"] == "PEER_DOWN") & (prd["signed_fwd14"] > 0)).astype(int)
    prd["DELAYED_REHAB"] = ((prd["peer_dir"] == "PEER_UP") & (prd["signed_fwd14"] > prd["peer_fwd14"])
                            & (prd["rank_up_30"] == 1)).astype(int)
    prd["TEMPORARY_SPLIT"] = ((prd["signed_fwd14"] > 0) & (prd["signed_fwd30"] < 0)).astype(int)
    rows = []
    for col in ["BETA_RESCUE", "PEER_RESCUE", "RELATIVE_DECAY", "DELAYED_REHAB", "TEMPORARY_SPLIT"]:
        g = prd[prd[col] == 1]
        rows.append({
            "subtype": col, "n": int(len(g)),
            "supported": "YES" if len(g) >= MIN_SUPPORT else "NOT_SUPPORTED",
            "median_abs_shock": _fmt(g["abs_ret"].median()),
            "median_sigma": _fmt(g["z1"].median()),
            "relational_state_mode": str(g["rel_state"].mode().iloc[0]) if len(g) else "",
            "membership_stability_mode": str(g["membership_class"].mode().iloc[0]) if len(g) else "",
            "field_state_mode": str(g["cell4"].mode().iloc[0]) if len(g) else "",
            "p_true_loner": _fmt(g["is_true_loner"].mean()),
            "p_false_loner": _fmt(g["is_false_loner"].mean()),
            "p_peer_up": _fmt((g["peer_dir"] == "PEER_UP").mean()),
            "p_rejoin_30d": _fmt(g["out_rejoin"].mean()),
            "p_decoupling_30d": _fmt(g["out_decouple"].mean()),
        })
    # overall cross-tab
    xtab = prd.groupby(["peer_dir", "rel_state"]).size().reset_index(name="n")
    return pd.DataFrame(rows), xtab, prd


# =========================================================================
# 24 RELATIONAL-STATE INFORMATION GAIN
# =========================================================================

def info_gain(panels, sets_by_fam):
    snap = panels[C.PRIMARY_FAMILY].sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    sets = sets_by_fam[C.PRIMARY_FAMILY]
    dates, assets, R = C._wide_returns()
    dpos = {d: i for i, d in enumerate(dates)}
    apos = {a: i for i, a in enumerate(assets)}
    pf7 = np.full(len(snap), np.nan)
    for i in range(len(snap)):
        pf7[i] = _peer_cum_fwd(snap["event_index"].iloc[i], snap["historical_date"].iloc[i],
                               sets.get(snap["event_index"].iloc[i], ()), 7, dpos, apos, dates, R)
    snap["peer_fwd7"] = pf7
    snap["rank_band_cat"] = snap["rank_band"].astype("category").cat.codes
    snap["rel_state_cat"] = snap["rel_state"].astype("category").cat.codes
    snap["membership_class_cat"] = snap["membership_class"].astype("category").cat.codes
    sets_feats = {
        "exact_peer_ids": ["peer_med_ret", "peer_std_ret", "peer_fwd7", "peer_corr"],
        "peer_family_label": ["n_families_voted", "n_families_true"],
        "rank_band": ["rank_band_cat"],
        "simple_correlation": ["peer_corr"],
        "relational_state": ["rel_state_cat"],
        "membership_stability": ["membership_class_cat", "roll_turnover_30d", "entropy_30d"],
    }
    outcomes = {"recovery": "out_rejoin", "contagion": "out_contagion", "decoupling": "out_decouple"}
    rows = []
    for oname, ocol in outcomes.items():
        for fname, feats in sets_feats.items():
            auc = _purged_auc(snap, ocol, feats)
            rows.append({"outcome": oname, "feature_family": fname, "purged_auc": _fmt(auc),
                         "n": int(len(snap))})
    df = pd.DataFrame(rows)
    verdicts = []
    for oname in outcomes:
        sub = df[df["outcome"] == oname].set_index("feature_family")["purged_auc"]
        rel = sub.get("relational_state", np.nan)
        best_other = sub.drop(index=["relational_state"], errors="ignore").max()
        verdicts.append({
            "outcome": oname,
            "relational_state_auc": _fmt(rel),
            "best_other_auc": _fmt(best_other),
            "rel_state_beats_exact_peer_ids": str(rel > sub.get("exact_peer_ids", np.nan)),
            "rel_state_beats_best_other": str(rel > best_other),
            "dynamic_relational_state_more_robust": "YES" if rel >= best_other + 0.01 else "NO",
        })
    return df, pd.DataFrame(verdicts)


# =========================================================================
# MAIN
# =========================================================================

def main():
    print("[lf8] loading panels (5 families) ...", flush=True)
    panels, sets_by_fam = load_all()

    print("[lf8] 02 paradox resolution ...", flush=True)
    p02, p02v = paradox_resolution(panels, sets_by_fam)
    p02.to_csv(R / "02_PEER_LIFETIME_PARADOX_RESOLUTION.csv", index=False)
    p02v.to_csv(R / "02b_PARADOX_VERDICTS.csv", index=False)

    print("[lf8] 03 state definitions ...", flush=True)
    p03 = state_definitions(panels)
    p03.to_csv(R / "03_RELATIONAL_STATE_DEFINITIONS.csv", index=False)

    print("[lf8] 04 state persistence ...", flush=True)
    p04 = state_persistence(panels, sets_by_fam)
    p04.to_csv(R / "04_RELATIONAL_STATE_PERSISTENCE.csv", index=False)

    print("[lf8] 05 membership entropy ...", flush=True)
    p05, p05t = membership_entropy(panels, sets_by_fam)
    p05.to_csv(R / "05_PEER_MEMBERSHIP_ENTROPY.csv", index=False)
    p05t.to_csv(R / "05b_ENTROPY_TREND.csv", index=False)

    print("[lf8] 06 peer-state lattice ...", flush=True)
    p06 = peer_state_lattice(panels)
    p06.to_csv(R / "06_PEER_STATE_LATTICE.csv", index=False)

    print("[lf8] 07 neighborhood lifecycle ...", flush=True)
    p07, p07t, _ = neighborhood_lifecycle(panels)
    p07.to_csv(R / "07_NEIGHBORHOOD_LIFECYCLE.csv", index=False)
    p07t.to_csv(R / "07b_LIFECYCLE_TRANSITIONS.csv", index=False)

    print("[lf8] 08 formation/dissolution clocks ...", flush=True)
    p08 = formation_dissolution_clocks(panels)
    p08.to_csv(R / "08_PEER_FORMATION_DISSOLUTION_CLOCKS.csv", index=False)

    print("[lf8] 09 static vs rolling ...", flush=True)
    p09 = static_vs_rolling(panels, sets_by_fam)
    p09.to_csv(R / "09_STATIC_VS_ROLLING_PEERS.csv", index=False)

    print("[lf8] 10 response curves ...", flush=True)
    p10, p10v = response_curves(panels)
    p10.to_csv(R / "10_PEER_REORGANIZATION_RESPONSE_CURVES.csv", index=False)
    p10v.to_csv(R / "10b_RESPONSE_CURVE_VERDICTS.csv", index=False)

    print("[lf8] 11 reorganization timing ...", flush=True)
    p11, p11p = reorg_timing(panels)
    p11.to_csv(R / "11_REORGANIZATION_TIMING.csv", index=False)
    p11p.to_csv(R / "11b_TIMING_PRECEDENCE.csv", index=False)

    print("[lf8] 12 reorganization entropy ...", flush=True)
    p12, v12, *_ = reorg_entropy(panels, sets_by_fam)
    p12.to_csv(R / "12_PEER_REORGANIZATION_ENTROPY.csv", index=False)
    with open(R / "_12_verdict.json", "w") as fh:
        json.dump({"reconstitution_verdict": v12}, fh)

    print("[lf8] 13 relational vs field entropy ...", flush=True)
    p13, v13 = relational_vs_field_entropy(panels)
    p13.to_csv(R / "13_RELATIONAL_VS_FIELD_ENTROPY.csv", index=False)
    v13.to_csv(R / "13b_FIELD_JOIN_VERDICT.csv", index=False)

    print("[lf8] 14 false-loner decomposition ...", flush=True)
    p14 = false_loner_decomposition(panels)
    p14.to_csv(R / "14_FALSE_LONER_DECOMPOSITION.csv", index=False)

    print("[lf8] 15 true-loner subtypes ...", flush=True)
    p15 = true_loner_subtypes(panels)
    p15.to_csv(R / "15_TRUE_LONER_SUBTYPES.csv", index=False)

    print("[lf8] 16 rejoin/contagion/decoupling lattice ...", flush=True)
    p16, p16c, p16d = rejoin_contagion_lattice(panels)
    p16.to_csv(R / "16_REJOIN_CONTAGION_DECOUPLING_LATTICE.csv", index=False)
    p16c.to_csv(R / "16b_LATTICE_COLLAPSED.csv", index=False)
    with open(R / "_16_dropped.json", "w") as fh:
        json.dump(p16d, fh)

    print("[lf8] 17 directional asymmetry ...", flush=True)
    p17 = directional_asymmetry(panels, sets_by_fam)
    p17.to_csv(R / "17_DIRECTIONAL_RELATIONAL_ASYMMETRY.csv", index=False)

    print("[lf8] 18/19 up/down ecology ...", flush=True)
    up, dn = up_down_ecology(panels, sets_by_fam)
    up.to_csv(R / "18_UPSIDE_LOCAL_ECOLOGY.csv", index=False)
    dn.to_csv(R / "19_DOWNSIDE_LOCAL_ECOLOGY.csv", index=False)

    print("[lf8] 20/21 primitive audits ...", flush=True)
    p20, v20 = primitive_audit(panels, "out_contagion", "CONTAGION")
    p20.to_csv(R / "20_CONTAGION_PRIMITIVE_AUDIT.csv", index=False)
    with open(R / "_20_verdict.json", "w") as fh:
        json.dump({"verdict": v20}, fh)
    p21, v21 = primitive_audit(panels, "out_rejoin", "REJOIN")
    p21.to_csv(R / "21_REJOIN_PRIMITIVE_AUDIT.csv", index=False)
    with open(R / "_21_verdict.json", "w") as fh:
        json.dump({"verdict": v21}, fh)

    print("[lf8] 22 decoupling bridge ...", flush=True)
    p22 = decoupling_bridge(panels)
    p22.to_csv(R / "22_DECOUPLING_DECAY_BRIDGE.csv", index=False)

    print("[lf8] 23 PRD relational health ...", flush=True)
    p23, p23x, _ = prd_relational_health(panels, sets_by_fam)
    p23.to_csv(R / "23_PRD_RELATIONAL_HEALTH.csv", index=False)
    p23x.to_csv(R / "23b_PRD_CROSSTAB.csv", index=False)

    print("[lf8] 24 relational-state information gain ...", flush=True)
    p24, v24 = info_gain(panels, sets_by_fam)
    p24.to_csv(R / "24_RELATIONAL_STATE_INFORMATION_GAIN.csv", index=False)
    v24.to_csv(R / "24b_INFO_GAIN_VERDICTS.csv", index=False)

    print("[lf8] DONE", flush=True)


if __name__ == "__main__":
    main()
