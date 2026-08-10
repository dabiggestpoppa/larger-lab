"""
Phase 5 - Routing Event Engine detection machinery.
CR-P5-ROUTING-EVENT-ENGINE-01

Deterministic statistical detectors: origin events, residual shocks, network
dislocations, bridge/parking/destination candidates, episode de-duplication
with hysteresis. Every statistic uses only trailing (<= T) data.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_5_events import (
    CURRENCIES,
    PAIRS,
    CURRENCY_PAIRS,
    RoutingEvent,
    build_threshold_manifest,
)

RUN_LENGTH = 120  # trailing H1 window for statistical references


# ----------------------------------------------------------------------
# Trailing statistical helpers (fully backward-looking)
# ----------------------------------------------------------------------


def _rolling_pct(series: pd.Series, window: int = RUN_LENGTH) -> pd.Series:
    """Percentile rank of the current value within trailing window."""
    def _pct_latest(x):
        return float(np.mean(x <= x[-1]))
    return series.rolling(window, min_periods=window).apply(_pct_latest, raw=True)


def _rolling_mad(series: pd.Series, window: int = RUN_LENGTH) -> pd.Series:
    """Median-absolute-deviation based trailing score."""
    def _score(x):
        med = np.median(x)
        mad = np.median(np.abs(x - med))
        if mad <= 0:
            return 0.0
        return float((x[-1] - med) / (1.4826 * mad))
    return series.rolling(window, min_periods=window).apply(_score, raw=True)


def _rolling_z(series: pd.Series, window: int = RUN_LENGTH) -> pd.Series:
    return (series - series.rolling(window, min_periods=window).mean()) / \
        series.rolling(window, min_periods=window).std().replace(0, np.nan)


# ----------------------------------------------------------------------
# Detector state (component frames at every timestamp)
# ----------------------------------------------------------------------


def compute_event_components(
    factor_df: pd.DataFrame,
    residual_df: pd.DataFrame,
    feature_df: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """
    Build the per-timestamp component surface used by all detectors.

    Returns dict of DataFrames indexed by timestamp (the H1 panel):
      - factors: currency factors (already present)
      - shocks: residual shok state per pair
      - candidates: bridge/parking/destination candidate scores per currency
      - network: network-level stress components
    """
    idx = factor_df.index

    # ---- residual shock state ----
    shock_cols = {}
    for pair in PAIRS:
        res = residual_df[f"{pair}_residual"]
        shock_cols[f"{pair}_shock_z"] = _rolling_z(res)
        shock_cols[f"{pair}_shock_mad"] = _rolling_mad(res)
        shock_cols[f"{pair}_shock_pct"] = _rolling_pct(res.abs())
        # residual volatility adjustment (trailing)
        rv = res.abs().rolling(RUN_LENGTH, min_periods=RUN_LENGTH).mean()
        shock_cols[f"{pair}_shock_vol_adj"] = res.abs() / rv.replace(0, np.nan)
    shocks = pd.DataFrame(shock_cols, index=idx)

    # ---- candidate components (bridge/parking/destination) ----
    cand = {}
    for c in CURRENCIES:
        factor = f"{c}_factor"
        vel = f"{c}_velocity_4h"
        acc = f"{c}_acceleration_4h"
        br = f"{c}_breadth_fraction"
        vol = f"{c}_factor_volatility_4h"
        rank = f"{c}_rank"
        cand[f"{c}_factor"] = factor_df[factor]
        cand[f"{c}_velocity"] = feature_df[vel] if vel in feature_df else np.nan
        cand[f"{c}_acceleration"] = feature_df[acc] if acc in feature_df else np.nan
        cand[f"{c}_breadth"] = feature_df[br] if br in feature_df else np.nan
        cand[f"{c}_volatility"] = feature_df[vol] if vol in feature_df else np.nan
        cand[f"{c}_rank"] = feature_df[rank] if rank in feature_df else np.nan
        cand[f"{c}_rank_change"] = feature_df[rank].diff() if rank in feature_df else np.nan
    # residuals specifically for bridge/parking/destination
    for pair in ["EURGBP", "GBPJPY", "GBPCHF", "EURCHF", "CHFJPY", "EURJPY"]:
        cand[f"{pair}_residual"] = residual_df[f"{pair}_residual"]
    candidates = pd.DataFrame(cand, index=idx)

    # ---- network-level components ----
    net = {
        "network_dispersion": feature_df.get("fx_dispersion_4h", np.nan),
        "network_rmse": factor_df.get("network_fit_rmse", np.nan),
        "max_pair_residual": residual_df.abs().max(axis=1),
        "residual_breadth": (residual_df.abs()
                             .gt(residual_df.abs().rolling(RUN_LENGTH, min_periods=RUN_LENGTH)
                                 .quantile(0.95))
                             ).sum(axis=1),
    }
    network = pd.DataFrame(
        {k: (v if isinstance(v, pd.Series) else pd.Series(v, index=idx))
         for k, v in net.items()}, index=idx)

    return {"factors": factor_df, "shocks": shocks,
            "candidates": candidates, "network": network}


# ----------------------------------------------------------------------
# Origin detector
# ----------------------------------------------------------------------


def _origin_signal_for_currency(c: str, comp: Dict[str, pd.DataFrame],
                                feature_df: pd.DataFrame) -> pd.DataFrame:
    """Raw origin-predisposition components for one currency (symmetric)."""
    factors = comp["factors"]
    cand = comp["candidates"]
    f = f"{c}_factor"
    s = pd.DataFrame(index=factors.index)
    s["factor"] = factors[f]
    for h in ["4h", "8h", "12h"]:
        s[f"cum_{h}"] = feature_df.get(f"{c}_{h}", np.nan)
    s["velocity"] = cand[f"{c}_velocity"]
    s["acceleration"] = cand[f"{c}_acceleration"]
    s["breadth"] = cand[f"{c}_breadth"]
    s["rank"] = cand[f"{c}_rank"]
    s["volatility"] = cand[f"{c}_volatility"]
    # volatility-adjusted magnitude
    s["vol_adj"] = s["factor"] / s["volatility"].replace(0, np.nan)
    s["factor_abs"] = s["factor"].abs()
    s["abs_pct"] = _rolling_pct(s["factor_abs"])       # trailing percentile of magnitude
    s["abs_mad"] = _rolling_mad(s["factor_abs"])       # MAD score of magnitude
    s["abs_z"] = _rolling_z(s["factor_abs"])           # trailing z
    return s


def _dest_rank(cur_origin: str, factors: pd.DataFrame, candidates: pd.DataFrame,
               feature_df: pd.DataFrame) -> Tuple[str, str, str]:
    """
    Contemporaneous destination ranking: which OTHER currencies receive flow.
    Signs oriented so that positive factor = strengthening.
    """
    others = [c for c in CURRENCIES if c != cur_origin]
    def score(c: str) -> float:
        posf = factors[f"{c}_factor"].iloc[-1] if len(factors) else 0.0
        posa = candidates[f"{c}_acceleration"].iloc[-1] if len(candidates) else 0.0
        br = candidates[f"{c}_breadth"].iloc[-1] if len(candidates) else 0.0
        rk = candidates[f"{c}_rank"].iloc[-1] if len(candidates) else 0.0
        rk_imp = candidates[f"{c}_rank_change"].iloc[-1] if len(candidates) else 0.0
        return float(posf + 0.5 * (posa if pd.notna(posa) else 0)
                     + br * (1.0 if pd.notna(br) else 0)
                     + 0.25 * (rk_imp if pd.notna(rk_imp) else 0))
    scored = sorted(others, key=lambda c: score(c), reverse=True)
    ranked = [c for c in scored]
    return (ranked[0] if len(ranked) > 0 else None,
            ranked[1] if len(ranked) > 1 else None,
            ranked[2] if len(ranked) > 2 else None)


def detect_origin_episodes(
    factor_df: pd.DataFrame,
    residual_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    comp: Dict[str, pd.DataFrame],
    manifest: Dict,
) -> pd.DataFrame:
    """
    Detect currency origin episodes for all 5 currencies symmetrically.

    Returns DataFrame of episode records (one row per episode).
    """
    entry_pc = manifest["hysteresis"]["entry_percentile"]
    reset_pc = manifest["hysteresis"]["reset_percentile"]
    episodes = []

    for c in CURRENCIES:
        sig = _origin_signal_for_currency(c, comp, feature_df)
        # composite pressure score = sum of evidence z/pct components
        press = sig["factor"].abs()
        press = press.rolling(RUN_LENGTH, min_periods=RUN_LENGTH).apply(
            lambda x: float(np.mean(np.abs(x) <= np.abs(x[-1]))), raw=True)
        dirn = np.sign(sig["factor"])

        in_episode = False
        episode_start = None
        peak_ts = None
        peak_sev = 0.0
        peak_press = 0.0
        for t in range(len(press)):
            ts = press.index[t]
            p = press.iloc[t]
            d = dirn.iloc[t]
            sev = max(0.0, (p - reset_pc) / (1.0 - reset_pc)) if p > reset_pc else 0.0
            if not in_episode:
                # entry: pressure above entry percentile
                if p >= entry_pc:
                    in_episode = True
                    episode_start = ts
                    peak_ts = ts
                    peak_press = p
                    peak_sev = sev
                    episode_dir = "ACCUMULATION" if d >= 0 else "LIQUIDATION"
            else:
                # continuation while above reset; end if below reset or dir flips
                if p < reset_pc or (d != 0 and (d >= 0) != (episode_dir == "ACCUMULATION")):
                    events = _emit_episode(c, sig, episode_start, peak_ts, peak_sev,
                                           peak_press, episode_dir, factor_df, residual_df,
                                           feature_df, comp, manifest)
                    episodes.extend(events)
                    in_episode = False
                    episode_start = None
                    peak_ts = None
                else:
                    if p > peak_press:
                        peak_press = p
                        peak_ts = ts
                        peak_sev = sev
        # close any open episode at end
        if in_episode and episode_start is not None:
            events = _emit_episode(c, sig, episode_start, peak_ts, peak_sev,
                                   peak_press, episode_dir, factor_df, residual_df,
                                   feature_df, comp, manifest)
            episodes.extend(events)

    return pd.DataFrame(episodes) if episodes else pd.DataFrame()


def _emit_episode(c, sig, start, peak, peak_sev, peak_press, direction,
                  factor_df, residual_df, feature_df, comp, manifest) -> List[Dict]:
    """Materialise one episode's RoutingEvent(s)."""
    end = peak  # the episode length measured as duration
    if start is None or peak is None:
        return []
    duration_h = max(1.0, float((pd.Timestamp(peak) - pd.Timestamp(start)).total_seconds() / 3600.0))
    severity = _severity_from_score(peak_sev, manifest)
    # contemporaneous origin feature snapshot at peak
    row_ts = pd.Timestamp(peak)
    if row_ts in factor_df.index:
        fac = factor_df.loc[row_ts]
    else:
        fac = pd.Series(dtype=float)
    c_factor = float(fac.get(f"{c}_factor", np.nan))
    c_vel = float(comp["candidates"].loc[row_ts, f"{c}_velocity"]) if row_ts in comp["candidates"].index else np.nan
    c_acc = float(comp["candidates"].loc[row_ts, f"{c}_acceleration"]) if row_ts in comp["candidates"].index else np.nan
    c_br = float(comp["candidates"].loc[row_ts, f"{c}_breadth"]) if row_ts in comp["candidates"].index else np.nan
    c_rk = float(comp["candidates"].loc[row_ts, f"{c}_rank"]) if row_ts in comp["candidates"].index else np.nan
    c_vol = float(comp["candidates"].loc[row_ts, f"{c}_volatility"]) if row_ts in comp["candidates"].index else np.nan

    d1, d2, d3 = _dest_rank(c, comp["factors"].loc[:row_ts], comp["candidates"].loc[:row_ts],
                            feature_df.loc[:row_ts])

    gbp = _bridge_components(c, comp, row_ts)
    chf = _parking_components(c, comp, row_ts)
    jpy = _destination_components(c, comp, row_ts)

    ev = RoutingEvent(
        event_id=f"{c}_ORIGIN_{start:%Y%m%d%H%M}",
        event_start=str(start), peak_timestamp=str(peak), event_end=str(end),
        duration_hours=duration_h, event_family="BROAD_CURRENCY_EVENT",
        origin_currency=c, direction=direction, severity=severity,
        severity_score=round(peak_sev, 4),
        origin_strength=round(c_factor, 8) if pd.notna(c_factor) else None,
        origin_velocity=round(c_vel, 8) if pd.notna(c_vel) else None,
        origin_acceleration=round(c_acc, 8) if pd.notna(c_acc) else None,
        origin_breadth=round(c_br, 6) if pd.notna(c_br) else None,
        origin_rank=round(c_rk, 4) if pd.notna(c_rk) else None,
        origin_volatility=round(c_vol, 8) if pd.notna(c_vol) else None,
        destination_rank_1=d1, destination_rank_2=d2, destination_rank_3=d3,
        gbp_bridge_score_components=gbp,
        chf_parking_score_components=chf,
        jpy_destination_score_components=jpy,
        network_dispersion=float(comp["network"]["network_dispersion"].loc[row_ts]) if row_ts in comp["network"].index else None,
        network_rmse=float(comp["network"]["network_rmse"].loc[row_ts]) if row_ts in comp["network"].index else None,
        max_pair_residual=float(comp["network"]["max_pair_residual"].loc[row_ts]) if row_ts in comp["network"].index else None,
        broad_vs_localized="BROAD_CURRENCY_EVENT",
    )
    return [asdict(ev)]


def _severity_from_score(score: float, manifest: Dict) -> str:
    if pd.isna(score):
        return "LOW"
    for name, (lo, hi) in manifest["severity_buckets"].items():
        if lo <= score < hi:
            return name
    return "EXTREME"


# ----------------------------------------------------------------------
# Bridge / parking / destination candidate components
# ----------------------------------------------------------------------


def _bridge_components(origin: str, comp: Dict[str, pd.DataFrame], ts) -> Dict:
    cand = comp["candidates"]
    if ts not in cand.index:
        return {}
    row = cand.loc[ts]
    return {
        "GBP_factor": float(row["GBP_factor"]) if pd.notna(row["GBP_factor"]) else None,
        "GBP_velocity": float(row["GBP_velocity"]) if pd.notna(row["GBP_velocity"]) else None,
        "GBP_acceleration": float(row["GBP_acceleration"]) if pd.notna(row["GBP_acceleration"]) else None,
        "GBP_breadth": float(row["GBP_breadth"]) if pd.notna(row["GBP_breadth"]) else None,
        "GBP_rank_change": float(row["GBP_rank_change"]) if pd.notna(row["GBP_rank_change"]) else None,
        "EURGBP_residual": float(row["EURGBP_residual"]) if pd.notna(row["EURGBP_residual"]) else None,
        "GBPJPY_residual": float(row["GBPJPY_residual"]) if pd.notna(row["GBPJPY_residual"]) else None,
        "GBPCHF_residual": float(row["GBPCHF_residual"]) if pd.notna(row["GBPCHF_residual"]) else None,
    }


def _parking_components(origin: str, comp: Dict[str, pd.DataFrame], ts) -> Dict:
    cand = comp["candidates"]
    if ts not in cand.index:
        return {}
    row = cand.loc[ts]
    return {
        "CHF_factor": float(row["CHF_factor"]) if pd.notna(row["CHF_factor"]) else None,
        "CHF_breadth": float(row["CHF_breadth"]) if pd.notna(row["CHF_breadth"]) else None,
        "CHF_acceleration": float(row["CHF_acceleration"]) if pd.notna(row["CHF_acceleration"]) else None,
        "CHF_rank_change": float(row["CHF_rank_change"]) if pd.notna(row["CHF_rank_change"]) else None,
        "EURCHF_residual": float(row["EURCHF_residual"]) if pd.notna(row["EURCHF_residual"]) else None,
        "GBPCHF_residual": float(row["GBPCHF_residual"]) if pd.notna(row["GBPCHF_residual"]) else None,
        "CHFJPY_residual": float(row["CHFJPY_residual"]) if pd.notna(row["CHFJPY_residual"]) else None,
    }


def _destination_components(origin: str, comp: Dict[str, pd.DataFrame], ts) -> Dict:
    cand = comp["candidates"]
    if ts not in cand.index:
        return {}
    row = cand.loc[ts]
    return {
        "JPY_factor": float(row["JPY_factor"]) if pd.notna(row["JPY_factor"]) else None,
        "JPY_positive": float(row["JPY_factor"]) if pd.notna(row["JPY_factor"]) else None,
        "JPY_acceleration": float(row["JPY_acceleration"]) if pd.notna(row["JPY_acceleration"]) else None,
        "JPY_breadth": float(row["JPY_breadth"]) if pd.notna(row["JPY_breadth"]) else None,
        "JPY_rank_change": float(row["JPY_rank_change"]) if pd.notna(row["JPY_rank_change"]) else None,
        "EURJPY_residual": float(row["EURJPY_residual"]) if pd.notna(row["EURJPY_residual"]) else None,
        "GBPJPY_residual": float(row["GBPJPY_residual"]) if pd.notna(row["GBPJPY_residual"]) else None,
        "CHFJPY_residual": float(row["CHFJPY_residual"]) if pd.notna(row["CHFJPY_residual"]) else None,
    }


# ----------------------------------------------------------------------
# Residual shock detector
# ----------------------------------------------------------------------


def detect_residual_shocks(
    residual_df: pd.DataFrame,
    comp: Dict[str, pd.DataFrame],
    manifest: Dict,
) -> pd.DataFrame:
    """Detect pair residual shock episodes (trailing-normalised)."""
    shocks = comp["shocks"]
    shock_thresh = manifest.get("residual_p95_threshold", 0.0)
    episodes = []
    start_ts = None
    peak_ts = None
    peak_sev = 0.0
    current_pair = None
    entry_pc = manifest["hysteresis"]["entry_percentile"]
    reset_pc = manifest["hysteresis"]["reset_percentile"]

    for t in range(len(residual_df)):
        ts = residual_df.index[t]
        pct_row = shocks.iloc[t]
        # find max percentile pair
        pcts = [pct_row[f"{p}_shock_pct"] for p in PAIRS if pd.notna(pct_row[f"{p}_shock_pct"])]
        if not pcts:
            continue
        mx = max(pcts)
        mx_pair = PAIRS[int(np.argmax([pct_row[f"{p}_shock_pct"] if pd.notna(pct_row[f"{p}_shock_pct"]) else -1 for p in PAIRS]))]
        if start_ts is None:
            if mx >= entry_pc:
                start_ts = ts; peak_ts = ts; current_pair = mx_pair; peak_sev = mx
        else:
            if mx < reset_pc or mx_pair != current_pair:
                episodes.append({
                    "event_id": f"RESIDUAL_{current_pair}_{start_ts:%Y%m%d%H%M}",
                    "event_start": str(start_ts), "peak_timestamp": str(peak_ts),
                    "event_end": str(peak_ts),
                    "duration_hours": max(1.0, float((peak_ts - start_ts).total_seconds() / 3600.0)),
                    "event_family": "RESIDUAL_SHOCK", "origin_currency": current_pair,
                    "direction": None, "severity": _severity_from_score(peak_sev, manifest),
                    "severity_score": round(float(peak_sev), 4),
                    "broad_vs_localized": "PAIR_SPECIFIC_DISLOCATION",
                })
                start_ts = None; peak_ts = None; current_pair = None; peak_sev = 0.0
            elif mx > peak_sev:
                peak_sev = mx; peak_ts = ts
    if start_ts is not None:
        episodes.append({
            "event_id": f"RESIDUAL_{current_pair}_{start_ts:%Y%m%d%H%M}",
            "event_start": str(start_ts), "peak_timestamp": str(peak_ts),
            "event_end": str(peak_ts),
            "duration_hours": max(1.0, float((peak_ts - start_ts).total_seconds() / 3600.0)),
            "event_family": "RESIDUAL_SHOCK", "origin_currency": current_pair,
            "direction": None, "severity": _severity_from_score(peak_sev, manifest),
            "severity_score": round(float(peak_sev), 4),
            "broad_vs_localized": "PAIR_SPECIFIC_DISLOCATION",
        })
    return pd.DataFrame(episodes) if episodes else pd.DataFrame()


# ----------------------------------------------------------------------
# Network dislocation detector
# ----------------------------------------------------------------------


def detect_network_dislocations(
    factor_df: pd.DataFrame,
    residual_df: pd.DataFrame,
    comp: Dict[str, pd.DataFrame],
    manifest: Dict,
) -> pd.DataFrame:
    """Detect NETWORK_DISLOCATION episodes from network stress combinations."""
    network = comp["network"]
    dispersion = network["network_dispersion"]
    disp_z = _rolling_z(dispersion)
    disp_thr = manifest.get("network_dispersion_z_threshold", 2.0)
    rmse_thr = manifest.get("network_rmse_p95", 0.0)

    episodes = []
    in_ep = False
    start_ts = None; peak_ts = None; peak_sev = 0.0
    for t in range(len(network)):
        ts = network.index[t]
        z = disp_z.iloc[t]
        rm = network["network_rmse"].iloc[t]
        stress = 0.0
        if pd.notna(z) and z > disp_thr:
            stress += 1.0
        if pd.notna(rm) and rm > rmse_thr:
            stress += 1.0
        sev = stress / 2.0  # 0..1
        if not in_ep:
            if stress >= 1:
                in_ep = True; start_ts = ts; peak_ts = ts; peak_sev = sev
        else:
            if stress == 0:
                episodes.append({
                    "event_id": f"NETWORK_DISLOCATION_{start_ts:%Y%m%d%H%M}",
                    "event_start": str(start_ts), "peak_timestamp": str(peak_ts),
                    "event_end": str(peak_ts),
                    "duration_hours": max(1.0, float((peak_ts - start_ts).total_seconds() / 3600.0)),
                    "event_family": "NETWORK_DISLOCATION", "origin_currency": None,
                    "direction": None, "severity": _severity_from_score(peak_sev * 2, manifest),
                    "severity_score": round(float(peak_sev), 4),
                    "network_dispersion": float(dispersion.iloc[t]) if pd.notna(dispersion.iloc[t]) else None,
                    "network_rmse": float(rm) if pd.notna(rm) else None,
                    "max_pair_residual": float(network["max_pair_residual"].iloc[t]) if pd.notna(network["max_pair_residual"].iloc[t]) else None,
                    "broad_vs_localized": "NETWORK_DISLOCATION",
                })
                in_ep = False; start_ts = None; peak_ts = None; peak_sev = 0.0
            elif sev > peak_sev:
                peak_sev = sev; peak_ts = ts
    if in_ep and start_ts is not None:
        episodes.append({
            "event_id": f"NETWORK_DISLOCATION_{start_ts:%Y%m%d%H%M}",
            "event_start": str(start_ts), "peak_timestamp": str(peak_ts),
            "event_end": str(peak_ts),
            "duration_hours": max(1.0, float((peak_ts - start_ts).total_seconds() / 3600.0)),
            "event_family": "NETWORK_DISLOCATION", "origin_currency": None,
            "direction": None, "severity": _severity_from_score(peak_sev * 2, manifest),
            "severity_score": round(float(peak_sev), 4),
            "network_dispersion": None, "network_rmse": None,
            "max_pair_residual": None,
            "broad_vs_localized": "NETWORK_DISLOCATION",
        })
    return pd.DataFrame(episodes) if episodes else pd.DataFrame()