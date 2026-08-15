"""
Phase 8 - CEREBUS primitive extraction (brief sections 2-4).

Computes the canonical CEREBUS primitive stream for every frozen routing event
inside the standardized research window t0 -> t0 + 120 minutes:

  - daily tier        (canonical Pine get_tier(): T1 <20 / T2 20-30 / T3 30-45 /
                       NO-GO >=45 pips of the Asian range; NA before 03:00 EST)
  - P90 print         (M5 candle body >= hour-bucket threshold in 2-11 AM EST)
  - tier impulse      (P90 print that ALSO breaches the Asian band)
  - midpoint events   (side, touch, cross, close-through, reclaim, rejection)
  - rekey             (132% Asian-range violation, canonical violation_long/short)

No threshold is invented: all primitives use the canonical CEREBUS definitions
from the repository's Pine script, cascade implementation, Asian-range extractor
and label generators. USDJPY pip = 0.01.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Canonical constants (frozen from CEREBUS V5 Pine + cascade config)
# ---------------------------------------------------------------------------

USDJPY_PIP = 0.01
ASIAN_START_EST = 19
ASIAN_END_EST = 3          # 03:00 EST -> Asian range complete
ENTRY_START_EST = 2
ENTRY_END_EST = 11
VIOLATION_MULT = 1.32

# P90 candle-body thresholds (pips) by EST hour bucket (cascade config).
P90_THRESHOLDS: List[Tuple[int, int, float]] = [
    (2, 4, 4.1), (4, 6, 4.6), (6, 8, 4.6), (8, 10, 5.9), (10, 11, 6.2),
]

# Daily tier boundaries in pips (Pine get_tier / cascade tier_config).
TIER_BOUNDS: List[Tuple[str, float]] = [
    ("T1", 20.0), ("T2", 30.0), ("T3", 45.0), ("NO-GO", np.inf),
]

# Research window: 120 minutes in fixed causal buckets.
WINDOW_MIN = 120
BUCKETS: List[Tuple[int, int, str]] = [
    (0, 15, "0_15"), (15, 30, "15_30"), (30, 45, "30_45"),
    (45, 60, "45_60"), (60, 90, "60_90"), (90, 120, "90_120"),
]
CUMULATIVE_BUCKETS: List[Tuple[int, str]] = [
    (15, "15m"), (30, "30m"), (60, "60m"), (90, "90m"), (120, "120m"),
]

M5_SHA256 = "719353ad7475aa7f877683f3bc7ff82cf15c1345f0aea2339acd114b0d6c3f3c"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_m5(path: Path) -> pd.DataFrame:
    """Load the canonical USDJPY M5 parquet, verifying its frozen hash."""
    actual = _sha256(path)
    if actual != M5_SHA256:
        raise ValueError(
            f"M5 data hash mismatch: expected {M5_SHA256}, got {actual}. "
            "Refusing to consume an un-frozen data source."
        )
    df = pd.read_parquet(path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    # Drop rows with no price information (weekends/holidays store NaN OHLC).
    df = df.dropna(subset=["open", "high", "low", "close"])
    return df


# ---------------------------------------------------------------------------
# Session-day Asian ranges (canonical extract_asian_ranges semantics)
# ---------------------------------------------------------------------------

def est_series(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """New York local time (DST-aware, per canonical asian_range.py)."""
    return idx.tz_convert("America/New_York")


def session_of(est: pd.DatetimeIndex) -> np.ndarray:
    """Session day label (tz-naive): date if hour >= 19 else date - 1 day."""
    naive = est.tz_localize(None)
    dates = naive.normalize()
    out = np.where(naive.hour >= ASIAN_START_EST,
                   dates, dates - pd.Timedelta(days=1))
    return np.asarray(out, dtype="datetime64[ns]")


def session_of_series(ts: pd.Series) -> pd.Series:
    """Session day labels for a tz-aware Series of timestamps (tz-naive out)."""
    est = ts.dt.tz_convert("America/New_York")
    naive = est.dt.tz_localize(None)
    dates = naive.dt.normalize()
    shift = (est.dt.hour < ASIAN_START_EST).astype(int)
    return (dates - shift * pd.Timedelta(days=1)).astype("datetime64[ns]")


def build_session_ar_table(m5: pd.DataFrame) -> pd.DataFrame:
    """
    Per-session-day Asian range table (canonical 19:00-03:00 EST window).
    Columns: session, ar_pips, ar_high, ar_low, midpoint, tier.
    """
    est = est_series(m5.index)
    sess = session_of(est)
    df = m5.copy()
    df["session"] = sess

    # Asian window: 19:00 - 03:00 EST
    asian_mask = (est.hour >= ASIAN_START_EST) | (est.hour < ASIAN_END_EST)
    ar = df[asian_mask].groupby("session").agg(
        ar_high=("high", "max"), ar_low=("low", "min"),
    )
    ar = ar.reset_index()
    ar["ar_pips"] = (ar["ar_high"] - ar["ar_low"]) / USDJPY_PIP
    ar["midpoint"] = (ar["ar_high"] + ar["ar_low"]) / 2.0

    # tier classification (canonical boundaries)
    tiers = []
    for v in ar["ar_pips"]:
        for name, bound in TIER_BOUNDS:
            if v < bound:
                tiers.append(name)
                break
    ar["tier"] = tiers
    ar = ar.sort_values("session").reset_index(drop=True)
    return ar


# ---------------------------------------------------------------------------
# Per-bar primitive flags on the full M5 frame
# ---------------------------------------------------------------------------

def _p90_threshold_for_hour(h: int) -> float:
    for lo, hi, thr in P90_THRESHOLDS:
        if lo <= h < hi:
            return thr
    return 0.0


def build_primitive_frame(m5: pd.DataFrame, ar: pd.DataFrame) -> pd.DataFrame:
    """
    Annotate every M5 bar with its session context and primitive flags.
    Returns a frame indexed like m5 with columns:
      session, ar_high, ar_low, ar_pips, midpoint, tier, ar_complete,
      est_hour, body_pips, in_p90_window, p90_print, p90_dir, band_breach,
      breach_dir, tier_impulse, impulse_dir, rekey_bull, rekey_bear,
      mid_touch_up, mid_touch_down, mid_cross, mid_side (close vs midpoint).
    """
    est = est_series(m5.index)
    sess = session_of(est)
    df = m5.copy()
    df["session"] = sess
    df["est_hour"] = est.hour
    df["est_date"] = est.normalize()

    # merge session context
    ar_map = ar.set_index("session")
    df = df.join(ar_map, on="session", how="left")

    # Asian range complete at 03:00 EST of the day after session start
    df["ar_complete"] = df["est_hour"] >= ASIAN_END_EST

    body = (df["close"] - df["open"]).abs()
    df["body_pips"] = body / USDJPY_PIP
    df["in_p90_window"] = (df["est_hour"] >= ENTRY_START_EST) & (
        df["est_hour"] < ENTRY_END_EST)

    thr = np.array([_p90_threshold_for_hour(int(h)) for h in df["est_hour"]])
    df["p90_threshold"] = thr
    df["p90_print"] = df["in_p90_window"] & df["ar_complete"] & (
        df["body_pips"] >= thr)
    df["p90_dir"] = np.where(
        df["p90_print"], np.where(df["close"] > df["open"], "bull", "bear"),
        "")

    # Asian band breach (only meaningful when AR complete)
    df["band_breach"] = False
    df["breach_dir"] = ""
    comp = df["ar_complete"]
    bull_breach = comp & (df["high"] >= df["ar_high"])
    bear_breach = comp & (df["low"] <= df["ar_low"])
    df.loc[bull_breach, "band_breach"] = True
    df.loc[bull_breach, "breach_dir"] = "bull"
    df.loc[bear_breach, "band_breach"] = True
    df.loc[bear_breach, "breach_dir"] = "bear"

    # tier impulse = P90 print + band breach in the same direction
    df["tier_impulse"] = df["p90_print"] & df["band_breach"] & (
        df["p90_dir"] == df["breach_dir"])
    df["impulse_dir"] = np.where(df["tier_impulse"], df["p90_dir"], "")

    # rekey = 132% violation
    viol_bull = comp & (df["high"] >= df["ar_high"] + VIOLATION_MULT
                        * df["ar_pips"] * USDJPY_PIP)
    viol_bear = comp & (df["low"] <= df["ar_low"] - VIOLATION_MULT
                        * df["ar_pips"] * USDJPY_PIP)
    df["rekey_bull"] = viol_bull
    df["rekey_bear"] = viol_bear

    # midpoint primitives
    m = df["midpoint"]
    df["mid_touch_up"] = df["high"] >= m
    df["mid_touch_down"] = df["low"] <= m
    df["mid_cross"] = (df["open"] - m) * (df["close"] - m) < 0
    df["mid_close_above"] = df["close"] > m
    df["mid_close_below"] = df["close"] < m
    df["mid_side"] = np.where(df["mid_close_above"], "above",
                              np.where(df["mid_close_below"], "below", "on"))

    return df


# ---------------------------------------------------------------------------
# Windowed primitive extraction for routing events
# ---------------------------------------------------------------------------

def extract_event_primitives(
    ev_ts: pd.Timestamp,
    prim: pd.DataFrame,
) -> pd.DataFrame:
    """
    All primitive events inside [t0, t0 + WINDOW_MIN] as a long frame.
    Columns: prim_type (p90|tier_impulse|rekey|mid_cross|mid_close_through),
             direction (bull|bear), ts, minutes_from_t0, bucket, aligned
             (filled by caller per family).
    """
    t0 = pd.Timestamp(ev_ts)
    if t0.tz is None:
        t0 = t0.tz_localize("UTC")
    t_end = t0 + pd.Timedelta(minutes=WINDOW_MIN)
    win = prim.loc[(prim.index >= t0) & (prim.index <= t_end)]

    if len(win) == 0:
        return pd.DataFrame(columns=[
            "prim_type", "direction", "ts", "minutes_from_t0", "bucket"])

    mins = (win.index - t0).total_seconds() / 60.0
    bucket = pd.cut(mins, bins=[b[0] for b in BUCKETS] + [120.0],
                    labels=[b[2] for b in BUCKETS], right=False)

    rows = []
    # P90 prints
    for ts, r in win[win["p90_print"]].iterrows():
        rows.append({"prim_type": "p90", "direction": r["p90_dir"],
                     "ts": ts, "minutes_from_t0": float((ts - t0).total_seconds() / 60.0)})
    # tier impulses
    for ts, r in win[win["tier_impulse"]].iterrows():
        rows.append({"prim_type": "tier_impulse", "direction": r["impulse_dir"],
                     "ts": ts, "minutes_from_t0": float((ts - t0).total_seconds() / 60.0)})
    # rekeys
    for ts, r in win[win["rekey_bull"] | win["rekey_bear"]].iterrows():
        d = "bull" if r["rekey_bull"] else "bear"
        rows.append({"prim_type": "rekey", "direction": d,
                     "ts": ts, "minutes_from_t0": float((ts - t0).total_seconds() / 60.0)})
    # midpoint crosses
    for ts, r in win[win["mid_cross"]].iterrows():
        d = "bull" if r["mid_close_above"] else "bear"
        rows.append({"prim_type": "mid_cross", "direction": d,
                     "ts": ts, "minutes_from_t0": float((ts - t0).total_seconds() / 60.0)})

    out = pd.DataFrame(rows)
    if len(out):
        out["bucket"] = pd.cut(
            out["minutes_from_t0"], bins=[b[0] for b in BUCKETS] + [120.0],
            labels=[b[2] for b in BUCKETS], right=False).astype(str)
    return out


def bucket_counts(stream: pd.DataFrame, prim_type: str) -> Dict[str, int]:
    """Counts per bucket for a primitive type (0-filled)."""
    out = {}
    if len(stream):
        sub = stream[stream["prim_type"] == prim_type]
        counts = sub["bucket"].value_counts()
        for _, _, name in BUCKETS:
            out[name] = int(counts.get(name, 0))
    else:
        for _, _, name in BUCKETS:
            out[name] = 0
    return out


def cumulative_counts(bucket_counts: Dict[str, int]) -> Dict[str, int]:
    """Cumulative counts at 15/30/60/90/120m from per-bucket counts."""
    cum = {}
    total = 0
    for lo, hi, name in BUCKETS:
        total += bucket_counts.get(name, 0)
        if hi in (15, 30, 60, 90, 120):
            cum[f"{hi}m"] = total
    return cum
