"""
Phase 8 - event fingerprint table (brief section 16).

One row per routing event with baseline outcomes (frozen Phase 7 baseline for
the family) plus every CEREBUS primitive summary inside the 120-minute window.
Also emits the linked long-form primitive stream (P8_PRIMITIVE_STREAM_LONG.csv).
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_8_primitives import (
    BUCKETS, CUMULATIVE_BUCKETS, WINDOW_MIN,
    build_primitive_frame, bucket_counts, cumulative_counts,
    extract_event_primitives,
)

# Baseline configs frozen from Phase 7.5 (CR-P8 brief section 1).
BASELINE = {
    "A": {"origin": "EUR", "direction": "ACCUMULATION", "trade": "long",
          "delay_h": 2, "hold_h": 6, "aligned_dir": "bull"},
    "B": {"origin": "EUR", "direction": "LIQUIDATION", "trade": "short",
          "delay_h": 1, "hold_h": 6, "aligned_dir": "bear"},
}

PRIM_TYPES = ["p90", "tier_impulse", "rekey", "mid_cross"]


def _aligned(direction: str, aligned_dir: str) -> int:
    """1 aligned, -1 opposed, 0 neutral (no direction)."""
    if direction == aligned_dir:
        return 1
    if direction in ("bull", "bear"):
        return -1
    return 0


def build_fingerprints(
    events: pd.DataFrame,
    prim: pd.DataFrame,
    execution: pd.DataFrame,
) -> pd.DataFrame:
    """
    events: routing events (event_id, event_start, origin_currency, direction,
            severity, session).
    prim:   full annotated M5 primitive frame.
    execution: Phase 7 execution grid rows for USDJPY at the frozen
            (delay, hold) with directional returns already applied (dir_net_bps,
            dir_mfe_bps, dir_mae_bps, time_to_mfe_h, time_to_mae_h, split).
    Returns the P8_EVENT_FINGERPRINT frame.
    """
    fam_cols = []
    for fid, cfg in BASELINE.items():
        sub = events[
            (events["origin_currency"] == cfg["origin"])
            & (events["direction"] == cfg["direction"])
        ].copy()
        sub["family"] = fid

        ex = execution[
            (execution["event_id"].isin(sub["event_id"]))
            & (execution["delay_h"] == cfg["delay_h"])
            & (execution["hold_h"] == cfg["hold_h"])
        ][["event_id", "dir_return_bps", "dir_net_bps", "dir_mfe_bps",
           "dir_mae_bps", "time_to_mfe_h", "time_to_mae_h", "rv_bps_per_h",
           "split"]].copy()
        ex = ex.rename(columns={
            "dir_return_bps": "baseline_return_bps",
            "dir_net_bps": "baseline_net_bps",
            "dir_mfe_bps": "baseline_mfe_bps",
            "dir_mae_bps": "baseline_mae_bps",
            "time_to_mfe_h": "baseline_time_to_mfe_h",
            "time_to_mae_h": "baseline_time_to_mae_h",
            "rv_bps_per_h": "baseline_rv_bps_per_h",
        })
        sub = sub.merge(ex, on="event_id", how="left")
        # The SEALED Phase 7/7.5 baseline uses volatility-normalized PnL
        # (position = target_vol / realized vol, target 10 bps/h). Keep the raw
        # bps as secondary; the primary outcome mirrors the frozen baseline.
        pos = np.where(sub["baseline_rv_bps_per_h"].fillna(0) > 0,
                       10.0 / sub["baseline_rv_bps_per_h"], 1.0)
        sub["baseline_position"] = pos
        sub["baseline_vol_bps"] = sub["baseline_net_bps"] * pos
        sub["baseline_vol_mfe_bps"] = sub["baseline_mfe_bps"] * pos
        sub["baseline_vol_mae_bps"] = sub["baseline_mae_bps"] * pos
        sub["baseline_win"] = np.where(sub["baseline_vol_bps"] > 0, 1,
                                       np.where(sub["baseline_vol_bps"] < 0, 0, np.nan))
        sub["baseline_entry_time"] = pd.to_datetime(
            sub["event_start"], utc=True) + pd.to_timedelta(cfg["delay_h"], unit="h")
        sub["baseline_exit_time"] = pd.to_datetime(
            sub["event_start"], utc=True) + pd.to_timedelta(
            cfg["delay_h"] + cfg["hold_h"], unit="h")
        sub["trade"] = cfg["trade"]
        sub["aligned_dir"] = cfg["aligned_dir"]

        # ---- primitive summaries ----
        feats = []
        long_rows = []
        for _, ev in sub.iterrows():
            t0 = pd.Timestamp(ev["event_start"])
            stream = extract_event_primitives(t0, prim)
            if len(stream):
                stream = stream.copy()
                stream["event_id"] = ev["event_id"]
                stream["family"] = fid
                stream["aligned"] = [_aligned(d, cfg["aligned_dir"])
                                     for d in stream["direction"]]
                long_rows.append(stream)

            f = {"event_id": ev["event_id"]}
            # per-primitive-type counts and timings
            for pt in PRIM_TYPES:
                bc = bucket_counts(stream, pt)
                cc = cumulative_counts(bc)
                sub_pt = stream[stream["prim_type"] == pt] if len(stream) else \
                    pd.DataFrame()
                n = len(sub_pt)
                f[f"{pt}_total"] = n
                f[f"{pt}_aligned"] = int((sub_pt["direction"] == cfg["aligned_dir"]).sum()) if n else 0
                f[f"{pt}_opposed"] = int(
                    ((sub_pt["direction"] != cfg["aligned_dir"]) & (sub_pt["direction"] != "")).sum()) if n else 0
                f[f"{pt}_first_min"] = float(sub_pt["minutes_from_t0"].min()) if n else np.nan
                f[f"{pt}_last_min"] = float(sub_pt["minutes_from_t0"].max()) if n else np.nan
                for k, v in bc.items():
                    f[f"{pt}_{k}"] = v
                for k, v in cc.items():
                    f[f"{pt}_cum{k}"] = v

            # density (per elapsed hour up to last primitive)
            all_pt = stream if len(stream) else pd.DataFrame()
            if len(all_pt):
                last = float(all_pt["minutes_from_t0"].max())
                elapsed_h = max(last, 1.0) / 60.0
                f["primitive_density"] = len(all_pt) / elapsed_h
            else:
                f["primitive_density"] = 0.0

            # tier / p90 ratios (brief section 7)
            t_total = f.get("tier_impulse_total", 0)
            p_total = f.get("p90_total", 0)
            t_alg = f.get("tier_impulse_aligned", 0)
            p_alg = f.get("p90_aligned", 0)
            t_opp = f.get("tier_impulse_opposed", 0)
            p_opp = f.get("p90_opposed", 0)
            f["tier_to_p90_ratio"] = t_total / (p_total + 1)
            f["p90_to_tier_ratio"] = p_total / (t_total + 1)
            f["aligned_commitment_ratio"] = (t_alg + p_alg) / (t_total + p_total + 1)
            f["opposition_ratio"] = (t_opp + p_opp) / (t_total + p_total + 1)

            # midpoint state at t0 (from the bar containing t0 or first after)
            f["midpoint_start_state"] = _midpoint_state_at(t0, prim)

            # rekey success/failure (canonical: return inside band within 60m)
            if f.get("rekey_total", 0) > 0:
                rk = stream[stream["prim_type"] == "rekey"]
                f["rekey_success"] = int(any(
                    _rekey_returned(ts, d, prim, cfg) for _, ts, d in
                    [(r, r["ts"], r["direction"]) for _, r in rk.iterrows()]))
                f["rekey_failure"] = int(f["rekey_total"] - f["rekey_success"])
            else:
                f["rekey_success"] = 0
                f["rekey_failure"] = 0
            feats.append(f)

        feat = pd.DataFrame(feats)
        sub = sub.merge(feat, on="event_id", how="left")
        fam_cols.append(sub)

    out = pd.concat(fam_cols, ignore_index=True, sort=False)

    # Events without a valid baseline window (NaN outcome) carry no evaluable
    # outcome and are excluded from the fingerprint universe.
    out = out.dropna(subset=["baseline_vol_bps"]).reset_index(drop=True)

    # sequence code: primitives in time order as T/P/R/M codes
    out["first_sequence"] = out["event_id"].map(
        lambda eid: _sequence_code(eid, prim, out))
    out["sequence_code"] = out["first_sequence"]

    # event-level latency of first primitive of any type (minutes)
    first_cols = [f"{pt}_first_min" for pt in PRIM_TYPES]
    out["time_to_first_primitive"] = out[first_cols].min(axis=1, skipna=True)

    return out


def build_long_stream(fingerprints: pd.DataFrame, prim: pd.DataFrame,
                      events: pd.DataFrame) -> pd.DataFrame:
    """Long-form primitive stream with full timestamps (linked to fingerprints)."""
    rows = []
    for _, ev in events.iterrows():
        t0 = pd.Timestamp(ev["event_start"])
        stream = extract_event_primitives(t0, prim)
        if not len(stream):
            continue
        fid = _family_of(ev)
        if fid is None:
            continue
        cfg = BASELINE[fid]
        s = stream.copy()
        s["event_id"] = ev["event_id"]
        s["family"] = fid
        s["aligned"] = [_aligned(d, cfg["aligned_dir"]) for d in s["direction"]]
        s["event_time"] = t0
        rows.append(s)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    return out.sort_values(["event_id", "ts"]).reset_index(drop=True)


def _family_of(ev: pd.Series) -> Optional[str]:
    for fid, cfg in BASELINE.items():
        if (ev["origin_currency"] == cfg["origin"]
                and ev["direction"] == cfg["direction"]):
            return fid
    return None


def _midpoint_state_at(t0: pd.Timestamp, prim: pd.DataFrame) -> str:
    """Side of midpoint (above/below/na) at the first bar >= t0."""
    win = prim.loc[prim.index >= t0]
    if not len(win):
        return "na"
    r = win.iloc[0]
    if not r["ar_complete"]:
        return "na"
    return "above" if r["mid_close_above"] else ("below" if r["mid_close_below"] else "on")


def _rekey_returned(ts: pd.Timestamp, direction: str, prim: pd.DataFrame,
                    cfg: Dict) -> bool:
    """True if price closes back inside the band within 60m of the rekey."""
    t_end = ts + pd.Timedelta(minutes=60)
    win = prim.loc[(prim.index > ts) & (prim.index <= t_end)]
    if not len(win):
        return False
    r0 = prim.loc[ts]
    viol_bull = r0["rekey_bull"]
    viol_bear = r0["rekey_bear"]
    level = r0["ar_high"] + 1.32 * r0["ar_pips"] * 0.01 if viol_bull else \
        r0["ar_low"] - 1.32 * r0["ar_pips"] * 0.01
    if viol_bull:
        return bool((win["close"] < level).any())
    return bool((win["close"] > level).any())


def _sequence_code(event_id, prim: pd.DataFrame, fp: pd.DataFrame) -> str:
    """Primitive sequence as T/P/R/M codes with aligned/opposed suffix.

    Ordering: tier_impulse (T), p90 (P), rekey (R), mid_cross (M).
    Depth capped at 4 primitives (brief section 11).
    """
    ev = fp[fp["event_id"] == event_id]
    if not len(ev):
        return ""
    t0 = pd.to_datetime(ev.iloc[0]["event_start"], utc=True)
    cfg = BASELINE[ev.iloc[0]["family"]]
    stream = extract_event_primitives(t0, prim)
    if not len(stream):
        return ""
    code_map = {"tier_impulse": "T", "p90": "P", "rekey": "R", "mid_cross": "M"}
    seq = []
    for _, r in stream.sort_values("minutes_from_t0").iterrows():
        c = code_map.get(r["prim_type"], "?")
        a = _aligned(r["direction"], cfg["aligned_dir"])
        suff = "A" if a == 1 else ("O" if a == -1 else "")
        seq.append(c + suff)
        if len(seq) >= 4:
            break
    return "-".join(seq) if seq else ""



