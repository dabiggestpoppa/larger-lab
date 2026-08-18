"""Canonical raw CSV loading with OHLC validation and quarantine.

All repository candidates were empirically resolved to a UTC-naive
timestamp convention (see B2 DATA_AUDIT). This loader normalizes any
candidate into a canonical frame with a UTC (tz-aware) index.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

OHLC_COLS = ["open", "high", "low", "close"]


@dataclass(frozen=True)
class LoadResult:
    frame: pd.DataFrame
    total_rows: int
    dropped_rows: int
    ohlc_violations: int
    na_rows: int
    quarantine: pd.DataFrame


def detect_time_column(columns) -> str:
    cols = [str(c).strip().lower() for c in columns]
    if "timestamp" in cols:
        return "timestamp"
    if "time" in cols:
        return "time"
    raise ValueError(f"no time/timestamp column in {list(columns)}")


def load_canonical(path: Path) -> LoadResult:
    """Load a raw candidate CSV into a canonical frame.

    Frame columns: open, high, low, close, volume, spread(optional) and
    tz-aware UTC index. OHLC invariants (H >= max(O,C), L <= min(O,C),
    H >= L) are checked; violating rows are quarantined, not repaired.
    """
    df = pd.read_csv(path, low_memory=False)
    df.columns = [str(c).strip().lower() for c in df.columns]
    total = len(df)

    ts_col = detect_time_column(df.columns)
    parsed = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    na_rows = int(parsed.isna().sum())
    df = df.assign(_dt=parsed).dropna(subset=["_dt"])

    for col in OHLC_COLS:
        if col not in df.columns:
            raise ValueError(f"missing OHLC column {col!r} in {path}")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    valid = (
        (df["high"] >= df[["open", "close"]].max(axis=1))
        & (df["low"] <= df[["open", "close"]].min(axis=1))
        & (df["high"] >= df["low"])
    ).fillna(False)
    ohlc_violations = int((~valid).sum())
    quarantine = df.loc[~valid].copy()
    df = df.loc[valid].copy()

    keep_cols = OHLC_COLS + ["_dt"]
    for vol_col in ("tick_volume", "volume", "real_volume"):
        if vol_col in df.columns:
            keep_cols.append(vol_col)
            break
    if "spread" in df.columns:
        keep_cols.append("spread")

    df = df[keep_cols].rename(columns={"_dt": "dt"}).set_index("dt").sort_index()
    if "volume" not in df.columns and "tick_volume" in df.columns:
        df["volume"] = df["tick_volume"]
    return LoadResult(
        frame=df,
        total_rows=total,
        dropped_rows=na_rows + ohlc_violations,
        ohlc_violations=ohlc_violations,
        na_rows=na_rows,
        quarantine=quarantine,
    )
