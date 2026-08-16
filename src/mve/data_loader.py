"""Fail-closed MVE market-data pipeline.

This module loads the canonical EURUSD M5 dataset, verifies its identity and
integrity at runtime, resamples M5 -> H1 deterministically, and exposes a
chronological slicing interface for research phases.

No synthetic/demo/alternate data is ever substituted. Every validation failure
raises and terminates the caller.

No MVE scientific logic lives here - this is infrastructure only.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class DataPipelineError(Exception):
    """Base error for data-pipeline failures (fail-closed)."""


# ---------------------------------------------------------------------------
# Canonical dataset freeze (R0.5.3 / R0.5.9)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CanonicalDataSpec:
    asset: str
    relpath: str
    sha256: str
    size_bytes: int
    rows: int
    first_timestamp: str
    last_timestamp: str
    timezone: str
    time_col: str  # epoch seconds column (authoritative when present)
    timestamp_col: str  # human-readable fallback
    open_col: str
    high_col: str
    low_col: str
    close_col: str
    volume_cols: Tuple[str, ...]  # ordered preference


# Measured directly from disk during R0 (see MVE_DATA_HASHES.json).
CANONICAL_EURUSD = CanonicalDataSpec(
    asset="EURUSD",
    relpath="quant-lab/data/EURUSDPRO_M5_2023_2026.csv",
    sha256="630b8a4052fe962bc7d87c6d49d83bc1524c7ddd83cd15e902fe504c998d3f77",
    size_bytes=15882861,
    rows=216820,
    first_timestamp="2023-07-03 00:00:00",
    last_timestamp="2026-05-29 00:25:00",
    timezone="UTC",
    time_col="time",
    timestamp_col="timestamp",
    open_col="open",
    high_col="high",
    low_col="low",
    close_col="close",
    volume_cols=("real_volume", "tick_volume"),
)

# Chronological split consumed from the R0 split lock (MVE_DATA_SPLIT_LOCK.json).
# Final holdout remains FINAL_HOLDOUT_PENDING: 2026+ is NOT an authorized range.
DEVELOPMENT_RANGE = ("2023-07-03", "2024-12-31")
CONFIRMATION_RANGE = ("2025-01-01", "2025-12-31")
AUTHORIZED_RANGES = (DEVELOPMENT_RANGE, CONFIRMATION_RANGE)
HOLDOUT_STATUS = "FINAL_HOLDOUT_PENDING"

# H1 resampling convention (frozen; matches the R0 independent audit which used
# pandas resample defaults: label='left', closed='left').
H1_LABEL = "left"
H1_CLOSED = "left"
H1_TIMEZONE = "UTC"
M5_FREQ_SECONDS = 300


def repo_root_from(module_file: str) -> str:
    """Repo root is two levels above src/mve/."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(module_file))))


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def select_volume_field(df: pd.DataFrame, candidates: Tuple[str, ...]) -> str:
    """Pick the first candidate with meaningful positive observations.

    real_volume is preferred only when it actually carries positive data;
    otherwise tick_volume is used. The choice is returned so callers can record
    it in runtime metadata.
    """
    present = [c for c in candidates if c in df.columns]
    if not present:
        raise DataPipelineError(
            f"No volume column available (candidates: {list(candidates)})"
        )
    for col in present:
        v = pd.to_numeric(df[col], errors="coerce")
        if (v > 0).any():
            return col
    # No positive volume anywhere; fall back to the first present column and
    # record it (callers may note it is zero-valued).
    return present[0]


def parse_timestamps(df: pd.DataFrame, spec: CanonicalDataSpec) -> pd.DataFrame:
    """Parse timestamps explicitly into a tz-aware UTC DatetimeIndex."""
    try:
        if spec.time_col in df.columns:
            epoch = pd.to_numeric(df[spec.time_col], errors="coerce")
            if epoch.isna().any():
                raise DataPipelineError("Invalid epoch timestamp values present")
            index = pd.to_datetime(epoch, unit="s", utc=True)
        elif spec.timestamp_col in df.columns:
            raw = df[spec.timestamp_col].astype(str)
            index = pd.to_datetime(raw, format="%Y-%m-%d %H:%M:%S", utc=True, errors="raise")
        else:
            raise DataPipelineError(
                f"Neither '{spec.time_col}' nor '{spec.timestamp_col}' column found"
            )
    except DataPipelineError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DataPipelineError(f"Invalid timestamp values: {exc}") from exc
    df = df.copy()
    df.index = index
    df.index.name = "datetime"
    return df


def validate_m5(df: pd.DataFrame, spec: CanonicalDataSpec) -> None:
    """Raise on any integrity violation. All checks are fail-closed."""
    if df.empty:
        raise DataPipelineError("Dataset is empty")

    required = {spec.open_col, spec.high_col, spec.low_col, spec.close_col}
    missing = required - set(df.columns)
    if missing:
        raise DataPipelineError(f"Missing OHLC column(s): {sorted(missing)}")

    if not df.index.is_monotonic_increasing:
        raise DataPipelineError("Timestamps are not monotonic")

    if df.index.has_duplicates:
        raise DataPipelineError("Duplicate timestamps present")

    o = pd.to_numeric(df[spec.open_col], errors="coerce")
    h = pd.to_numeric(df[spec.high_col], errors="coerce")
    l = pd.to_numeric(df[spec.low_col], errors="coerce")
    c = pd.to_numeric(df[spec.close_col], errors="coerce")

    if o.isna().any() or h.isna().any() or l.isna().any() or c.isna().any():
        raise DataPipelineError("Non-numeric OHLC values present")

    if (o <= 0).any() or (h <= 0).any() or (l <= 0).any() or (c <= 0).any():
        raise DataPipelineError("Zero/negative OHLC values present")

    bad = (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
    if bad.any():
        raise DataPipelineError(f"Invalid OHLC relationships at {int(bad.sum())} bar(s)")


def load_canonical_m5(
    spec: CanonicalDataSpec = CANONICAL_EURUSD,
    repo_root: Optional[str] = None,
) -> pd.DataFrame:
    """Load and validate the canonical M5 dataset. No fallback, no substitution."""
    root = repo_root or repo_root_from(__file__)
    path = os.path.join(root, spec.relpath)

    if not os.path.exists(path):
        raise DataPipelineError(f"Canonical data file missing: {path}")

    actual_hash = _sha256_file(path)
    if actual_hash != spec.sha256:
        raise DataPipelineError(
            f"SHA-256 mismatch for {spec.relpath}: expected {spec.sha256}, got {actual_hash}"
        )

    actual_size = os.path.getsize(path)
    if actual_size != spec.size_bytes:
        raise DataPipelineError(
            f"File size mismatch for {spec.relpath}: expected {spec.size_bytes}, got {actual_size}"
        )

    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        raise DataPipelineError(f"Failed to parse {spec.relpath}: {exc}") from exc

    df = parse_timestamps(df, spec)
    validate_m5(df, spec)

    volume_field = select_volume_field(df, spec.volume_cols)
    df = df.copy()
    df["volume"] = pd.to_numeric(df[volume_field], errors="coerce")
    df.attrs["volume_field"] = volume_field
    df.attrs["sha256"] = actual_hash
    df.attrs["source_path"] = spec.relpath

    return df


def resample_m5_to_h1(m5: pd.DataFrame) -> pd.DataFrame:
    """Resample validated M5 data to H1 (frozen convention).

    Open=first, High=max, Low=min, Close=last, Volume=sum. Empty hours with zero
    contributing M5 bars are dropped (no forward-fill, no synthetic bars). Each
    retained hour records how many source bars contributed.
    """
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(m5.columns)
    if missing:
        raise DataPipelineError(f"Missing columns for resampling: {sorted(missing)}")
    if not isinstance(m5.index, pd.DatetimeIndex):
        raise DataPipelineError("M5 input must have a DatetimeIndex")

    m5 = m5.sort_index()

    agg = m5.resample("1h", label=H1_LABEL, closed=H1_CLOSED).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )
    source_count = m5.resample("1h", label=H1_LABEL, closed=H1_CLOSED).size()

    h1 = agg.copy()
    h1["source_bar_count"] = source_count
    # Drop hours with no contributing source bar (weekend gaps). Do not fill.
    h1 = h1[h1["source_bar_count"] > 0]
    h1 = h1.dropna(subset=["open", "high", "low", "close"], how="any")
    return h1


def slice_data(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Return the chronological slice [start, end] (inclusive, UTC).

    Fails closed if the requested range extends beyond the authorized
    development/confirmation ranges (i.e. into the pending-holdout zone).
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise DataPipelineError("Data must have a DatetimeIndex to slice")

    try:
        s = pd.Timestamp(start, tz="UTC")
        e = pd.Timestamp(end, tz="UTC")
    except Exception as exc:  # noqa: BLE001
        raise DataPipelineError(f"Invalid slice bounds {start!r}/{end!r}: {exc}") from exc

    if s > e:
        raise DataPipelineError(f"Slice start {start} is after end {end}")

    for rs, re_ in AUTHORIZED_RANGES:
        lo = pd.Timestamp(rs, tz="UTC")
        hi = pd.Timestamp(re_, tz="UTC")
        if s >= lo and e <= hi:
            return df.loc[(df.index >= s) & (df.index <= e)].copy()

    raise DataPipelineError(
        f"Slice [{start}, {end}] is outside authorized ranges "
        f"{list(AUTHORIZED_RANGES)} (holdout status: {HOLDOUT_STATUS})"
    )
