"""
Phase 6 - Forward routing analyses.
CR-P6-FORWARD-ROUTING-STUDY-01

Thematic studies over the frozen Phase 5 event set: destination leadership and
transition matrices, GBP bridge / CHF parking / JPY destination tests, residual
shock lead-lag and decay, network dislocation outcomes, sleeper candidates,
session/severity/regime/direction conditioning, development->candidate->
holdout validation, and multiple-testing control.

Nothing here chooses thresholds by future PnL. All statistics are deterministic.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_events import (
    CURRENCIES,
    DEV_SUBPERIODS,
    HORIZONS,
    PAIRS,
    assign_split,
    assign_subperiod,
)
from .phase_6_stats import (
    bh_fdr,
    bootstrap_ci,
    bootstrap_destination_probability,
    describe,
    one_sample_t,
    rank_corr,
)

NS_PER_HOUR = 3600 * 10**9

# Candidate freeze criteria (development-only, effect-size first).
MIN_CANDIDATE_N = 50
MIN_CANDIDATE_EFFECT = 0.15
CANDIDATE_Q = 0.10
MIN_SUBPERIOD_SIGN = 3  # of 4 development subperiods

HORIZON_FAMILIES = {
    1: "SHORT", 2: "SHORT", 4: "SHORT",
    6: "MEDIUM", 8: "MEDIUM", 12: "MEDIUM",
    24: "LONG", 48: "LONG",
}

HIGH_RESIDUAL_PAIRS = ["EURGBP", "EURJPY", "EURCHF"]


# ---------------------------------------------------------------------------
# Long-form factor outcomes
# ---------------------------------------------------------------------------


def build_long_factor_outcomes(ev: pd.DataFrame,
                               horizons: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Long frame: one row per (origin event, horizon, currency) with the forward
    factor, destination flag, and conditioning fields.
    """
    horizons = horizons or HORIZONS
    rows = []
    for h in horizons:
        dest_col = f"destination_{h}"
        for c in CURRENCIES:
            sub = ev[["event_id", "event_ts", "origin_currency", "direction",
                      "severity", "session", "regime_dispersion", "regime_vol",
                      "network_state", "factor_vol_mean"]].copy()
            sub["horizon_h"] = h
            sub["currency"] = c
            sub["forward"] = ev[f"{c}_forward_{h}"]
            sub["is_destination"] = (ev[dest_col] == c).astype(int)
            rows.append(sub)
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------------------
# Destination probability matrix (section 5 + conditioning 20-23)
# ---------------------------------------------------------------------------


def destination_probability_matrix(long_out: pd.DataFrame,
                                   group_cols: Optional[List[str]] = None,
                                   horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    group_cols = group_cols or ["origin_currency", "direction", "severity",
                                "session", "regime_dispersion"]
    out_rows = []
    for h in horizons:
        sub = long_out[long_out["horizon_h"] == h]
        for gvals, grp in sub.groupby(group_cols, dropna=False):
            gdict = dict(zip(group_cols, gvals))
            n_events = grp["event_id"].nunique()
            for c in CURRENCIES:
                m = (grp["currency"] == c)
                cnt = int(m.sum())
                if cnt == 0:
                    continue
                is_dest = grp.loc[m, "is_destination"].to_numpy(dtype=float)
                boot = bootstrap_destination_probability(is_dest)
                out_rows.append({
                    **gdict, "horizon_h": h, "destination": c,
                    "n_events": n_events, "count": cnt,
                    "prob": boot["estimate"], "ci_low": boot["ci_low"],
                    "ci_high": boot["ci_high"], "se": boot["se"],
                })
    return pd.DataFrame(out_rows)


# ---------------------------------------------------------------------------
# Destination transition matrix (section 4)
# ---------------------------------------------------------------------------


def destination_transition_matrix(ev: pd.DataFrame,
                                  horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    pairs_h = list(zip(horizons[:-1], horizons[1:]))
    rows = []
    for from_h, to_h in pairs_h:
        fcol, tcol = f"destination_{from_h}", f"destination_{to_h}"
        for (orig, direc), grp in ev.groupby(["origin_currency", "direction"], dropna=False):
            valid = grp[[fcol, tcol]].dropna()
            if valid.empty:
                continue
            n = len(valid)
            for (d_from, d_to), cnt in valid.value_counts().items():
                rows.append({
                    "origin_currency": orig, "direction": direc,
                    "from_h": from_h, "to_h": to_h,
                    "dest_from": d_from, "dest_to": d_to,
                    "count": int(cnt), "n": int(n),
                    "prob": float(cnt / n),
                })
    return pd.DataFrame(rows)


def destination_sequence_summary(ev: pd.DataFrame,
                                 horizons: Optional[List[int]] = None) -> pd.DataFrame:
    """Modal destination leader per (origin, direction) at each horizon."""
    horizons = horizons or HORIZONS
    rows = []
    for h in horizons:
        col = f"destination_{h}"
        for (orig, direc), grp in ev.groupby(["origin_currency", "direction"], dropna=False):
            vc = grp[col].dropna().value_counts()
            if vc.empty:
                continue
            top = vc.index[0]
            rows.append({
                "origin_currency": orig, "direction": direc, "horizon_h": h,
                "dominant_destination": top, "count": int(vc.iloc[0]),
                "n": int(vc.sum()),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# GBP bridge test (section 9) + lead-lag sequence (section 10)
# ---------------------------------------------------------------------------


def _nonnull_mask(ev: pd.DataFrame, col: str) -> np.ndarray:
    vals = ev[col]
    return np.array([v is not None and not (isinstance(v, float) and np.isnan(v))
                     for v in vals])


def gbp_bridge_analysis(ev: pd.DataFrame,
                        horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    cand = ev[_nonnull_mask(ev, "gbp_bridge_score_components")].copy()
    rows = []
    if cand.empty:
        return pd.DataFrame()
    for (orig, direc), grp in cand.groupby(["origin_currency", "direction"], dropna=False):
        n = len(grp)
        lead = {h: float((grp[f"destination_{h}"] == "GBP").mean()) for h in horizons}
        # transfer: given GBP led at +1h, who leads later?
        gbp1 = grp[grp["destination_1"] == "GBP"]
        trans = {}
        for h in [4, 8, 12, 24]:
            if len(gbp1):
                trans[f"after_GBP_dest_{h}"] = gbp1[f"destination_{h}"].mode().iloc[0] \
                    if len(gbp1[f"destination_{h}"].dropna()) else None
            else:
                trans[f"after_GBP_dest_{h}"] = None
        rows.append({
            "origin_currency": orig, "direction": direc, "n": n,
            "initial_GBP_lead_rate": lead[1],
            "GBP_lead_rate_2h": lead[2], "GBP_lead_rate_4h": lead[4],
            "GBP_lead_rate_8h": lead[8], "GBP_lead_rate_24h": lead[24],
            "GBP_lead_decay": lead[1] - lead[24],
            **trans,
        })
    return pd.DataFrame(rows)


def bridge_lead_lag_sequence(ev: pd.DataFrame,
                             horizons: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Time to peak rank (best rank within 24h) for GBP/CHF/JPY/USD per origin
    event, plus first-to-peak ordering counts per origin.
    """
    horizons = [h for h in (horizons or HORIZONS) if h <= 24]
    currs = ["GBP", "CHF", "JPY", "USD"]
    rows = []
    for _, r in ev.iterrows():
        base = {"event_id": r["event_id"], "origin_currency": r["origin_currency"]}
        for c in currs:
            ranks = [r.get(f"{c}_rank_{h}") for h in horizons]
            finite = [(h, v) for h, v in zip(horizons, ranks) if v is not None and np.isfinite(v)]
            if finite:
                best = min(finite, key=lambda x: x[1])
                base[f"time_to_{c}_peak_rank"] = best[0]
                base[f"{c}_peak_rank"] = best[1]
            else:
                base[f"time_to_{c}_peak_rank"] = np.nan
                base[f"{c}_peak_rank"] = np.nan
        rows.append(base)
    out = pd.DataFrame(rows)
    summary = []
    for orig, grp in out.groupby("origin_currency"):
        order = []
        for _, r in grp.iterrows():
            times = {c: r[f"time_to_{c}_peak_rank"] for c in currs}
            finite = {c: t for c, t in times.items() if np.isfinite(t)}
            if finite:
                order.append(min(finite, key=finite.get))
        first = pd.Series(order).value_counts()
        summary.append({
            "origin_currency": orig, "n": len(grp),
            "first_to_peak_GBP": int(first.get("GBP", 0)),
            "first_to_peak_CHF": int(first.get("CHF", 0)),
            "first_to_peak_JPY": int(first.get("JPY", 0)),
            "first_to_peak_USD": int(first.get("USD", 0)),
            "mean_time_to_GBP": float(grp["time_to_GBP_peak_rank"].mean()),
            "mean_time_to_CHF": float(grp["time_to_CHF_peak_rank"].mean()),
            "mean_time_to_JPY": float(grp["time_to_JPY_peak_rank"].mean()),
            "mean_time_to_USD": float(grp["time_to_USD_peak_rank"].mean()),
        })
    return pd.DataFrame(summary)


# ---------------------------------------------------------------------------
# CHF parking test (section 11)
# ---------------------------------------------------------------------------


def chf_parking_analysis(ev: pd.DataFrame,
                         horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    cand = ev[_nonnull_mask(ev, "chf_parking_score_components")].copy()
    rows = []
    if cand.empty:
        return pd.DataFrame()
    for (orig, direc), grp in cand.groupby(["origin_currency", "direction"], dropna=False):
        n = len(grp)
        lead = {h: float((grp[f"destination_{h}"] == "CHF").mean()) for h in horizons}
        # time to leadership loss: first horizon where CHF not leader (approx)
        loss_times = []
        for _, r in grp.iterrows():
            loss = None
            for h in horizons:
                if r.get(f"destination_{h}") != "CHF":
                    loss = h
                    break
            if loss is not None:
                loss_times.append(loss)
        rows.append({
            "origin_currency": orig, "direction": direc, "n": n,
            "CHF_lead_rate_1h": lead[1], "CHF_lead_rate_2h": lead[2],
            "CHF_lead_rate_4h": lead[4], "CHF_lead_rate_8h": lead[8],
            "CHF_lead_rate_12h": lead[12], "CHF_lead_rate_24h": lead[24],
            "median_time_to_leadership_loss_h": float(np.median(loss_times)) if loss_times else np.nan,
            "p_loss_within_24h": float(np.mean([t <= 24 for t in loss_times])) if loss_times else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# JPY destination test (section 12)
# ---------------------------------------------------------------------------


def jpy_destination_analysis(ev: pd.DataFrame,
                             horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    cand = ev[_nonnull_mask(ev, "jpy_destination_score_components")].copy()
    rows = []
    if cand.empty:
        return pd.DataFrame()
    for (orig, direc), grp in cand.groupby(["origin_currency", "direction"], dropna=False):
        n = len(grp)
        lead = {h: float((grp[f"destination_{h}"] == "JPY").mean()) for h in horizons}
        fwd = {h: float(grp[f"JPY_forward_{h}"].mean()) for h in horizons}
        rank_imp = {h: float(grp[f"JPY_rank_change_{h}"].mean()) for h in horizons}
        # time to JPY leadership: first horizon where JPY is destination
        ttl = []
        for _, r in grp.iterrows():
            first = None
            for h in horizons:
                if r.get(f"destination_{h}") == "JPY":
                    first = h
                    break
            if first is not None:
                ttl.append(first)
        rows.append({
            "origin_currency": orig, "direction": direc, "n": n,
            **{f"JPY_lead_rate_{h}h": lead[h] for h in horizons},
            **{f"JPY_forward_mean_{h}h": fwd[h] for h in horizons},
            **{f"JPY_rank_improvement_{h}h": rank_imp[h] for h in horizons},
            "median_time_to_JPY_leadership_h": float(np.median(ttl)) if ttl else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Residual shock lead-lag (sections 13-14) and decay (section 15)
# ---------------------------------------------------------------------------


def _comp_lookup(comp: pd.DataFrame, ts: pd.Timestamp, col: str) -> float:
    """Value of comp[col] at the bar at or before ts."""
    idx = comp.index
    pos = int(np.searchsorted(idx.values.astype("int64"), int(ts.value), side="right")) - 1
    if pos < 0 or pos >= len(idx):
        return np.nan
    return float(comp.iloc[pos][col])


def residual_leadlag_analysis(res_ev: pd.DataFrame, ev_all: pd.DataFrame,
                              comp: pd.DataFrame,
                              horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    net_ts = pd.to_datetime(ev_all[ev_all["event_family"] == "NETWORK_DISLOCATION"]["event_start"], utc=True).to_numpy()
    net_ns = np.array([t.value for t in net_ts])

    rows = []
    for _, r in res_ev.iterrows():
        pair = r["origin_currency"]
        base, quote = pair[:3], pair[3:]
        T = r["event_ts"]
        shock_z = _comp_lookup(comp, T, f"{pair}_shock_z")
        for h in horizons:
            base_move = r.get(f"{base}_forward_{h}")
            quote_move = r.get(f"{quote}_forward_{h}")
            net_pre = int(np.sum((net_ns > int(T.value)) & (net_ns <= int(T.value) + h * NS_PER_HOUR)))
            d1 = r.get("destination_1")
            dh = r.get(f"destination_{h}")
            dest_change = int((d1 is not None and dh is not None and d1 != dh)) if h > 1 else 0
            rows.append({
                "pair": pair, "base_currency": base, "quote_currency": quote,
                "horizon_h": h, "shock_z": shock_z,
                "base_forward": base_move, "quote_forward": quote_move,
                "network_events_in_window": net_pre, "destination_change": dest_change,
            })
    long = pd.DataFrame(rows)

    out_rows = []
    for (pair, h), grp in long.groupby(["pair", "horizon_h"]):
        n = int(grp["base_forward"].notna().sum())
        rho_b = rank_corr(grp["shock_z"].to_numpy(), grp["base_forward"].to_numpy())
        rho_q = rank_corr(grp["shock_z"].to_numpy(), grp["quote_forward"].to_numpy())
        out_rows.append({
            "pair": pair, "horizon_h": h, "n": n,
            "mean_base_forward": float(grp["base_forward"].mean()),
            "mean_quote_forward": float(grp["quote_forward"].mean()),
            "p_network_in_window": float(grp["network_events_in_window"].mean()),
            "destination_change_rate": float(grp["destination_change"].mean()),
            "rho_shock_base": rho_b, "rho_shock_quote": rho_q,
        })
    return pd.DataFrame(out_rows)


def classify_high_residual_pairs(leadlag: pd.DataFrame) -> List[Dict]:
    """Section 14: classify EURGBP/EURJPY/EURCHF residual behaviour at +4h."""
    out = []
    for pair in HIGH_RESIDUAL_PAIRS:
        row = leadlag[(leadlag["pair"] == pair) & (leadlag["horizon_h"] == 4)]
        if row.empty:
            out.append({"pair": pair, "classification": "INCONCLUSIVE", "rho": np.nan, "n": 0})
            continue
        r = row.iloc[0]
        rho = r["rho_shock_base"]
        if rho >= 0.15 and r["n"] >= 50:
            cls = "LEADING_INFORMATION"
        elif rho <= -0.15 and r["n"] >= 50:
            cls = "MEAN_REVERTING_LOCAL_DISLOCATION"
        else:
            cls = "CONTEMPORANEOUS_NOISE"
        out.append({"pair": pair, "classification": cls, "rho": float(rho),
                    "n": int(r["n"]), "mean_base_forward_4h": float(r["mean_base_forward"])})
    return out


def residual_decay_analysis(res_ev: pd.DataFrame, comp: pd.DataFrame,
                            decay_h: Optional[List[int]] = None) -> pd.DataFrame:
    decay_h = decay_h or [1, 2, 4, 8, 12, 24]
    rows = []
    for _, r in res_ev.iterrows():
        pair = r["origin_currency"]
        T = r["event_ts"]
        res0 = _comp_lookup(comp, T, f"{pair}_residual")
        row = {"pair": pair, "event_id": r["event_id"], "residual_T": res0}
        for h in decay_h:
            row[f"residual_{h}h"] = _comp_lookup(comp, T + pd.Timedelta(hours=h), f"{pair}_residual")
        # empirical half-life
        hl = np.nan
        if res0 is not None and np.isfinite(res0) and abs(res0) > 1e-18:
            for h in decay_h:
                v = row[f"residual_{h}h"]
                if v is not None and np.isfinite(v) and abs(v) <= 0.5 * abs(res0):
                    hl = float(h)
                    break
        row["half_life_h"] = hl
        rows.append(row)
    long = pd.DataFrame(rows)

    out_rows = []
    for pair, grp in long.groupby("pair"):
        n = int(grp["residual_T"].notna().sum())
        out_rows.append({
            "pair": pair, "n": n,
            "mean_residual_T": float(grp["residual_T"].mean()),
            **{f"mean_residual_{h}h": float(grp[f"residual_{h}h"].mean()) for h in decay_h},
            "median_half_life_h": float(grp["half_life_h"].median()),
            "p_decayed_12h": float((grp["half_life_h"] <= 12).mean()),
            "p_decayed_24h": float((grp["half_life_h"] <= 24).mean()),
        })
    return pd.DataFrame(out_rows)


# ---------------------------------------------------------------------------
# Network dislocation outcomes (section 16)
# ---------------------------------------------------------------------------


def network_dislocation_outcomes(net_ev: pd.DataFrame, comp: pd.DataFrame,
                                 horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    rows = []
    for _, r in net_ev.iterrows():
        T = r["event_ts"]
        base = {
            "event_id": r["event_id"],
            "disp_T": r.get("network_dispersion"),
            "rmse_T": r.get("network_rmse"),
            "max_res_T": r.get("max_pair_residual"),
        }
        for h in horizons:
            base[f"disp_{h}h"] = _comp_lookup(comp, T + pd.Timedelta(hours=h), "network_dispersion")
            base[f"rmse_{h}h"] = _comp_lookup(comp, T + pd.Timedelta(hours=h), "network_rmse")
            base[f"destination_{h}"] = r.get(f"destination_{h}")
            fwd = {c: r.get(f"{c}_forward_{h}") for c in CURRENCIES}
            finite = {c: v for c, v in fwd.items() if v is not None and np.isfinite(v)}
            base[f"weakest_{h}"] = min(finite, key=finite.get) if finite else None
            vol = [_comp_lookup(comp, T + pd.Timedelta(hours=h), f"{c}_volatility") for c in CURRENCIES]
            base[f"factor_vol_{h}h"] = float(np.nanmean(vol)) if any(np.isfinite(vol)) else np.nan
        rows.append(base)
    long = pd.DataFrame(rows)

    out_rows = []
    for h in horizons:
        n = int(long[f"disp_{h}h"].notna().sum())
        disp_change = long[f"disp_{h}h"] - long["disp_T"]
        rmse_change = long[f"rmse_{h}h"] - long["rmse_T"]
        norm = float((disp_change < 0).mean()) if n else np.nan
        out_rows.append({
            "horizon_h": h, "n": n,
            "mean_dispersion_change": float(disp_change.mean()),
            "mean_rmse_change": float(rmse_change.mean()),
            "p_normalize": norm,
            "p_expand": float((disp_change > 0).mean()) if n else np.nan,
            "leader_EUR": float((long[f"destination_{h}"] == "EUR").mean()) if n else np.nan,
            "leader_GBP": float((long[f"destination_{h}"] == "GBP").mean()) if n else np.nan,
            "leader_USD": float((long[f"destination_{h}"] == "USD").mean()) if n else np.nan,
            "leader_CHF": float((long[f"destination_{h}"] == "CHF").mean()) if n else np.nan,
            "leader_JPY": float((long[f"destination_{h}"] == "JPY").mean()) if n else np.nan,
            "mean_factor_vol": float(long[f"factor_vol_{h}h"].mean()),
        })
    return pd.DataFrame(out_rows)


# ---------------------------------------------------------------------------
# MFE / MAE summaries (sections 17-18)
# ---------------------------------------------------------------------------


def factor_mfe_mae(ev: pd.DataFrame, horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    rows = []
    for (orig, direc), grp in ev.groupby(["origin_currency", "direction"], dropna=False):
        for h in horizons:
            for c in CURRENCIES:
                mfe = grp[f"{c}_mfe_{h}"].dropna()
                mae = grp[f"{c}_mae_{h}"].dropna()
                if mfe.empty:
                    continue
                rows.append({
                    "origin_currency": orig, "direction": direc, "horizon_h": h,
                    "currency": c, "n": int(len(mfe)),
                    "mean_mfe": float(mfe.mean()), "median_mfe": float(mfe.median()),
                    "mean_mae": float(mae.mean()), "median_mae": float(mae.median()),
                })
    return pd.DataFrame(rows)


def pair_mfe_mae(ev: pd.DataFrame, horizons: Optional[List[int]] = None) -> pd.DataFrame:
    horizons = horizons or HORIZONS
    rows = []
    for h in horizons:
        for p in PAIRS:
            ret = ev[f"{p}_return_{h}"].dropna()
            mfe = ev[f"{p}_mfe_{h}"].dropna()
            mae = ev[f"{p}_mae_{h}"].dropna()
            rv = ev[f"{p}_rv_{h}"].dropna()
            if ret.empty:
                continue
            rows.append({
                "pair": p, "horizon_h": h, "n": int(len(ret)),
                "mean_return": float(ret.mean()), "median_return": float(ret.median()),
                "mean_mfe": float(mfe.mean()), "median_mfe": float(mfe.median()),
                "mean_mae": float(mae.mean()), "median_mae": float(mae.median()),
                "mean_rv": float(rv.mean()),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sleeper score (section 19)
# ---------------------------------------------------------------------------


def sleeper_score_analysis(ev: pd.DataFrame, comp: pd.DataFrame,
                           panel: pd.DataFrame,
                           horizons: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Vectorised sleeper candidate score (value-identical to a per-event loop).
    For every (event, pair) compute: factor divergence, pair residual, low
    relative realised move, destination acceleration, residual normalisation.
    """
    horizons = horizons or HORIZONS
    ev = ev.reset_index(drop=True)
    ts_arr = pd.to_datetime(ev["event_ts"], utc=True)
    ts_ns = np.array([t.value for t in ts_arr])

    # component frame as a numpy matrix with column index
    comp_np = comp.to_numpy(dtype=float)
    comp_col = {c: i for i, c in enumerate(comp.columns)}
    # event row in comp (searchsorted left; events lie on the grid)
    cgrid_ns = comp.index.values.astype("int64")
    crow = np.minimum(np.searchsorted(cgrid_ns, ts_ns, side="left"), len(comp_np) - 1)

    closes = panel[[f"{p}_close" for p in PAIRS]]
    closes_arr = closes.to_numpy(dtype=float)
    pgrid_ns = panel.index.values.astype("int64")
    prow = np.minimum(np.searchsorted(pgrid_ns, ts_ns, side="left"), len(closes_arr) - 1)

    acc_cols = [comp_col[f"{c}_acceleration"] for c in CURRENCIES]
    dest_acc = np.abs(comp_np[crow][:, acc_cols])
    # finite-only, like the original loop (0.0 when nothing finite)
    dest_acc = np.where(np.isfinite(dest_acc), dest_acc, 0.0).max(axis=1)

    rows = []
    for pi, p in enumerate(PAIRS):
        base, quote = p[:3], p[3:]
        f_b = comp_np[crow, comp_col[f"{base}_factor"]]
        f_q = comp_np[crow, comp_col[f"{quote}_factor"]]
        res = comp_np[crow, comp_col[f"{p}_residual"]]
        vol_adj = comp_np[crow, comp_col[f"{p}_shock_vol_adj"]]

        div = np.where(np.isfinite(f_b) & np.isfinite(f_q), np.abs(f_b - f_q), 0.0)
        res_abs = np.where(np.isfinite(res), np.abs(res), 0.0)
        norm_state = np.where(np.isfinite(vol_adj), vol_adj, 0.0)

        # trailing 4h absolute move from panel closes
        tr = np.full(len(ev), np.nan)
        ok = (prow >= 4)
        c_now = closes_arr[prow, pi]
        c_prev = np.empty_like(c_now)
        c_prev[ok] = closes_arr[np.maximum(prow[ok] - 4, 0), pi]
        valid = ok & np.isfinite(c_now) & np.isfinite(c_prev) & (c_prev > 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            tr[valid] = np.abs(np.log(c_now[valid] / c_prev[valid]))

        rel_move = np.where(np.isfinite(tr), np.minimum(tr / 1e-4, 5.0), 2.5)
        score = (div / 1e-4) + (res_abs / 1e-4) + 0.5 * (1.0 - rel_move / 5.0) \
            + (dest_acc / 1e-4) + (norm_state / 5.0)

        d = pd.DataFrame({
            "event_id": ev["event_id"], "pair": p,
            "sleeper_candidate_score": score,
            "factor_divergence": div, "pair_residual": res_abs,
            "relative_realized_move": tr,
            "destination_acceleration": dest_acc,
            "residual_normalization_state": norm_state,
        })
        for h in horizons:
            col = f"{p}_return_{h}"
            v = ev[col].to_numpy(dtype=float)
            d[f"future_abs_return_{h}h"] = np.where(np.isfinite(v), np.abs(v), np.nan)
        rows.append(d)
    long = pd.concat(rows, ignore_index=True)

    summary_rows = []
    for h in horizons:
        y = long[f"future_abs_return_{h}h"]
        rho = rank_corr(long["sleeper_candidate_score"].to_numpy(), y.to_numpy())
        # quintile bucket means
        q = long["sleeper_candidate_score"].rank(pct=True)
        qb = pd.qcut(q, 5, labels=[1, 2, 3, 4, 5])
        bucket = long.groupby(qb, observed=True)[y.name].mean()
        summary_rows.append({
            "horizon_h": h, "n": int(y.notna().sum()),
            "rank_corr_score_future_move": rho,
            "bucket1_lowest_mean": float(bucket.iloc[0]) if len(bucket) == 5 else np.nan,
            "bucket5_highest_mean": float(bucket.iloc[4]) if len(bucket) == 5 else np.nan,
            "monotonic_gain": float(bucket.iloc[4] - bucket.iloc[0]) if len(bucket) == 5 else np.nan,
        })
    summary = pd.DataFrame(summary_rows)
    return long, summary


# ---------------------------------------------------------------------------
# Development results, candidate freeze, holdout validation, subperiods
# ---------------------------------------------------------------------------


def development_results_table(long_out: pd.DataFrame,
                              split_assign: str = "development") -> pd.DataFrame:
    """Per (origin, direction, destination, horizon) stats on the chosen split."""
    sub = long_out[long_out["split"] == split_assign]
    rows = []
    keys = ["origin_currency", "direction", "currency", "horizon_h"]
    for gvals, grp in sub.groupby(keys, dropna=False):
        gd = dict(zip(keys, gvals))
        fwd = grp["forward"].to_numpy(dtype=float)
        fwd = fwd[np.isfinite(fwd)]
        if len(fwd) == 0:
            continue
        desc = describe(fwd)
        tstat = one_sample_t(fwd)
        is_dest = grp.loc[grp["forward"].notna(), "is_destination"].to_numpy(dtype=float)
        dp = bootstrap_destination_probability(is_dest) if len(is_dest) else {}
        rows.append({
            **gd, "split": split_assign,
            "n": desc["n"], "dest_prob": dp.get("estimate", np.nan),
            "dest_prob_ci_low": dp.get("ci_low", np.nan),
            "dest_prob_ci_high": dp.get("ci_high", np.nan),
            "mean_forward": desc["mean"], "median_forward": desc["median"],
            "std_forward": desc["std"], "effect": desc["effect"],
            "ci_low": desc["ci_low"], "ci_high": desc["ci_high"],
            "t": tstat["t"], "p": tstat["p"],
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        # FDR within logical family (origin x direction)
        fam = out.groupby(["origin_currency", "direction"], dropna=False)
        q = np.full(len(out), np.nan)
        for _, g in fam:
            q[g.index] = bh_fdr(g["p"].to_numpy())
        out["q"] = q
    return out


def _subperiod_signs(ev_long: pd.DataFrame, origin: str, direction: str,
                     currency: str, h: int) -> List[Optional[int]]:
    sub = ev_long[
        (ev_long["origin_currency"] == origin)
        & (ev_long["direction"] == direction)
        & (ev_long["currency"] == currency)
        & (ev_long["horizon_h"] == h)
        & (ev_long["subperiod"] != "HOLDOUT")
    ]
    signs = []
    for name, _, _ in DEV_SUBPERIODS:
        vals = sub.loc[sub["subperiod"] == name, "forward"].dropna()
        signs.append(int(np.sign(vals.mean())) if len(vals) >= 10 else 0)
    return signs


def freeze_candidates(dev_results: pd.DataFrame,
                      ev_long: pd.DataFrame) -> List[Dict]:
    """Freeze candidate relationships from DEVELOPMENT results only."""
    cand = []
    df = dev_results[dev_results["split"] == "development"].copy()
    df = df[df["n"] >= MIN_CANDIDATE_N].copy()
    df = df[df["currency"] != df["origin_currency"]].copy()
    df = df[df["direction"].notna()].copy()
    for _, r in df.iterrows():
        if not np.isfinite(r["effect"]) or abs(r["effect"]) < MIN_CANDIDATE_EFFECT:
            continue
        if not np.isfinite(r["q"]) or r["q"] > CANDIDATE_Q:
            continue
        signs = _subperiod_signs(ev_long, r["origin_currency"], r["direction"],
                                 r["currency"], int(r["horizon_h"]))
        n_same = sum(1 for s in signs if s != 0 and s == int(np.sign(r["effect"])))
        if n_same < MIN_SUBPERIOD_SIGN:
            continue
        sign_word = "strength" if r["effect"] > 0 else "weakness"
        cand.append({
            "relationship_id": f"{r['origin_currency']}_{r['direction']}_TO_{r['currency']}_H{int(r['horizon_h'])}",
            "event_family": "BROAD_CURRENCY_EVENT",
            "origin": r["origin_currency"], "direction": r["direction"],
            "destination": r["currency"], "horizon_h": int(r["horizon_h"]),
            "horizon_family": HORIZON_FAMILIES[int(r["horizon_h"])],
            "dev_n": int(r["n"]), "dev_effect": float(r["effect"]),
            "dev_dest_prob": float(r["dest_prob"]),
            "dev_ci_low": float(r["ci_low"]), "dev_ci_high": float(r["ci_high"]),
            "dev_q": float(r["q"]), "subperiod_signs": signs,
            "subperiod_same_sign_count": int(n_same),
            "description": (f"{r['origin_currency']} {r['direction']} -> "
                            f"{r['currency']} relative {sign_word}, horizon {int(r['horizon_h'])}h "
                            f"(family {HORIZON_FAMILIES[int(r['horizon_h'])]})"),
        })
    # deterministic order
    cand.sort(key=lambda c: (c["origin"], c["direction"], c["destination"], c["horizon_h"]))
    return cand


def holdout_validation(candidates: List[Dict], ev_long: pd.DataFrame) -> pd.DataFrame:
    """Evaluate each frozen candidate on the holdout; label VALIDATED/WEAKENED/FAILED."""
    rows = []
    for c in candidates:
        sub = ev_long[
            (ev_long["split"] == "holdout")
            & (ev_long["origin_currency"] == c["origin"])
            & (ev_long["direction"] == c["direction"])
            & (ev_long["currency"] == c["destination"])
            & (ev_long["horizon_h"] == c["horizon_h"])
        ]
        fwd = sub["forward"].to_numpy(dtype=float)
        fwd = fwd[np.isfinite(fwd)]
        desc = describe(fwd) if len(fwd) else {"n": 0, "mean": np.nan, "effect": np.nan,
                                               "ci_low": np.nan, "ci_high": np.nan}
        ho_effect = desc["effect"]
        dev_effect = c["dev_effect"]
        if desc["n"] == 0 or not np.isfinite(ho_effect) or not np.isfinite(dev_effect):
            label = "INCONCLUSIVE"
        elif np.sign(ho_effect) != np.sign(dev_effect):
            label = "FAILED"
        elif abs(ho_effect) >= 0.5 * abs(dev_effect):
            label = "VALIDATED"
        else:
            label = "WEAKENED"
        rows.append({
            **c, "holdout_n": desc["n"], "holdout_effect": ho_effect,
            "holdout_mean": desc["mean"], "holdout_ci_low": desc["ci_low"],
            "holdout_ci_high": desc["ci_high"], "holdout_label": label,
        })
    return pd.DataFrame(rows)


def subperiod_stability(candidates: List[Dict], ev_long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in candidates:
        row = {"relationship_id": c["relationship_id"],
               "origin": c["origin"], "direction": c["direction"],
               "destination": c["destination"], "horizon_h": c["horizon_h"]}
        for name, _, _ in DEV_SUBPERIODS:
            sub = ev_long[
                (ev_long["subperiod"] == name)
                & (ev_long["origin_currency"] == c["origin"])
                & (ev_long["direction"] == c["direction"])
                & (ev_long["currency"] == c["destination"])
                & (ev_long["horizon_h"] == c["horizon_h"])
            ]
            vals = sub["forward"].dropna()
            row[f"{name}_effect"] = float(vals.mean() / vals.std(ddof=1)) if len(vals) >= 10 else np.nan
            row[f"{name}_n"] = int(len(vals))
        sub = ev_long[
            (ev_long["subperiod"] == "HOLDOUT")
            & (ev_long["origin_currency"] == c["origin"])
            & (ev_long["direction"] == c["direction"])
            & (ev_long["currency"] == c["destination"])
            & (ev_long["horizon_h"] == c["horizon_h"])
        ]
        vals = sub["forward"].dropna()
        row["HOLDOUT_effect"] = float(vals.mean() / vals.std(ddof=1)) if len(vals) >= 10 else np.nan
        row["HOLDOUT_n"] = int(len(vals))
        rows.append(row)
    return pd.DataFrame(rows)


def multiple_testing_table(dev_results: pd.DataFrame) -> pd.DataFrame:
    """All development hypothesis tests with BH q-values within families."""
    df = dev_results[dev_results["split"] == "development"].copy()
    rows = []
    fam = df.groupby(["origin_currency", "direction"], dropna=False)
    for (orig, direc), g in fam:
        q = bh_fdr(g["p"].to_numpy())
        for i, r in g.iterrows():
            rows.append({
                "family": f"{orig}_{direc}", "origin_currency": orig,
                "direction": direc, "destination": r["currency"],
                "horizon_h": r["horizon_h"], "n": r["n"],
                "mean_forward": r["mean_forward"], "effect": r["effect"],
                "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                "p": r["p"], "q": q[g.index.get_loc(i)] if i in g.index else np.nan,
                "dest_prob": r["dest_prob"],
            })
    return pd.DataFrame(rows)
