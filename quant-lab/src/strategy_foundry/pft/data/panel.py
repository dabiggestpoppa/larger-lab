"""Canonical synchronized H1 panel construction.

Resamples M5 series to the H1 clock on UTC bucket boundaries, builds the
common synchronized panel across W/E/C/I, and tags every slot with
observed / expected-closed / unexpected-missing / stale provenance plus
its partition class. No strategy behavior is computed here.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .sessions import is_expected_closed

NY = ZoneInfo("America/New_York")

PARTITION_RULES = {
    "DEVELOPMENT": (pd.Timestamp("2023-01-01", tz="UTC"), pd.Timestamp("2024-12-31 23:00", tz="UTC")),
    "CONFIRMATION": (pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-12-31 23:00", tz="UTC")),
    "HOLDOUT": (pd.Timestamp("2026-01-01", tz="UTC"), None),
}


def partition_of(dt_utc: pd.Timestamp) -> str:
    for name, (start, end) in PARTITION_RULES.items():
        if dt_utc >= start and (end is None or dt_utc <= end):
            return name
    return "OUT_OF_RANGE"


def resample_h1(m5: pd.DataFrame) -> pd.DataFrame:
    """Aggregate M5 OHLCV into H1 buckets on UTC hour boundaries.

    open = first, high = max, low = min, close = last, volume = sum.
    Empty buckets produce NaN rows (they are not fabricated bars).
    """
    if "volume" in m5.columns:
        agg = m5.resample("1h", label="left", closed="left").agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
    else:
        agg = m5.resample("1h", label="left", closed="left").agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("close", "count"),
        )
    return agg


def _carry_price(close: pd.Series) -> pd.Series:
    """Forward-fill carried prices WITHOUT erasing the observed flag.

    Carried values are used only for RAW stale-slot state; the observed
    provenance is tracked separately.
    """
    return close.ffill()


def build_panel(
    series: dict[str, pd.DataFrame],
    expected_closed_rules: dict[str, dict],
    panel_start: pd.Timestamp,
    panel_end: pd.Timestamp,
) -> pd.DataFrame:
    """Build the synchronized H1 panel over [panel_start, panel_end).

    series: asset id -> H1 frame (already resampled, UTC index).
    expected_closed_rules: asset id -> rule from sessions.derive_expected_closed.
    """
    index = pd.date_range(panel_start, panel_end, freq="1h", tz="UTC")
    panel = pd.DataFrame(index=index)

    for asset, frame in series.items():
        frame = frame[~frame.index.duplicated(keep="last")].reindex(index)
        rule = expected_closed_rules.get(asset, {})
        obs = frame["close"].notna()

        # Expected-closed mask per slot.
        closed = np.array([is_expected_closed(ts, rule) for ts in index])

        observed = obs.to_numpy()
        carried = _carry_price(frame["close"]).to_numpy()

        stale_age = np.zeros(len(index), dtype=float)
        last_seen = None
        for i, is_obs in enumerate(observed):
            if is_obs:
                last_seen = i
                stale_age[i] = 0.0
            elif last_seen is not None:
                stale_age[i] = float(i - last_seen)  # hours since last observed bar
            else:
                stale_age[i] = np.nan  # before first observation

        missing_reason = np.where(observed, "",
                                  np.where(closed, "EXPECTED_CLOSED", "UNEXPECTED_MISSING"))

        for col in ("open", "high", "low", "close"):
            vals = frame[col].to_numpy()
            panel[f"{asset}.{col}"] = pd.Series(vals, index=index)
            # carried price for stale/missing slots (RAW stale behavior)
            carried_vals = pd.Series(vals, index=index).ffill().to_numpy()
            panel[f"{asset}.{col}_carried"] = pd.Series(carried_vals, index=index)
        panel[f"{asset}.observed"] = observed
        panel[f"{asset}.expected_closed"] = closed
        panel[f"{asset}.stale"] = ~observed
        panel[f"{asset}.stale_age_hours"] = stale_age
        panel[f"{asset}.price_origin"] = np.where(observed, "OBSERVED", "CARRIED_STALE")
        panel[f"{asset}.missing_reason"] = missing_reason
        panel[f"{asset}.bar_valid"] = True  # OHLC-violating rows were quarantined at load

    panel["canonical_ny"] = index.tz_convert(NY)
    panel["partition"] = [partition_of(ts) for ts in index]
    return panel
