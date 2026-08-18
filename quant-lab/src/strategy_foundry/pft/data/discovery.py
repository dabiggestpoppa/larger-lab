"""Raw data discovery and file-structure inspection.

Scans the repository for candidate price files for the PFT universe and
characterizes their structure (rows, date span, bars-per-day pattern,
weekend structure) to resolve timestamp conventions empirically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Instrument families required by the A1 v2.2 universe.
UNIVERSE_PATTERNS = {
    "W": [r"LCO", r"OILUSD", r"BRENT"],
    "E": [r"EURUSD"],
    "C": [r"USDCAD"],
    "EC": [r"EURCAD"],
    "I": [r"DE30", r"DAX", r"GDAXI"],
}

TIMEFRAME_PATTERNS = {
    "M5": r"_M5|_5m",
    "H1": r"_H1|_1h",
    "D1": r"_D1|_1d",
}


@dataclass(frozen=True)
class Candidate:
    path: str
    family: str
    timeframe: str
    size_bytes: int


def discover_candidates(data_dir: Path) -> list:
    """Find candidate price files for the PFT universe in a data directory."""
    candidates = []
    if not data_dir.exists():
        return candidates
    for path in sorted(data_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in (".csv", ".parquet"):
            continue
        name = path.name.upper()
        family = None
        for fam, patterns in UNIVERSE_PATTERNS.items():
            if any(re.search(p, name) for p in patterns):
                family = fam
                break
        timeframe = None
        for tf, patterns in TIMEFRAME_PATTERNS.items():
            if any(re.search(p, name) for p in patterns):
                timeframe = tf
                break
        if family and timeframe:
            candidates.append(Candidate(
                path=str(path), family=family, timeframe=timeframe,
                size_bytes=path.stat().st_size,
            ))
    return candidates


def _read_head(path: Path, n: int = 5) -> pd.DataFrame:
    return pd.read_csv(path, nrows=n)


def detect_format(path: Path) -> dict:
    """Detect the CSV column conventions of a file."""
    head = _read_head(path)
    cols = [str(c).strip().lower() for c in head.columns]
    fmt = {
        "columns": cols,
        "has_time": "time" in cols,
        "has_timestamp": "timestamp" in cols,
        "has_spread": "spread" in cols,
        "has_tick_volume": "tick_volume" in cols,
        "has_real_volume": "real_volume" in cols,
        "has_volume": "volume" in cols,
        "has_unix_time": False,
    }
    if fmt["has_timestamp"] and not fmt["has_time"]:
        ts = head.iloc[0]["timestamp"]
        fmt["has_unix_time"] = isinstance(ts, (int, float)) and ts > 1_000_000_000
    return fmt


def inspect_file_structure(path: Path) -> dict:
    """Characterize bars/day, weekend structure, and date span."""
    df = pd.read_csv(path, low_memory=False)
    fmt = detect_format(path)
    ts_col = "timestamp" if "timestamp" in fmt["columns"] else "time"
    raw = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    df = df.assign(_dt=raw)
    df = df.dropna(subset=["_dt"])
    total_rows = len(df)
    start = df["_dt"].min()
    end = df["_dt"].max()
    day = df["_dt"].dt.date
    bars_per_day = day.value_counts()
    median_bpd = float(bars_per_day.median()) if len(bars_per_day) else 0.0
    p90_bpd = float(bars_per_day.quantile(0.90)) if len(bars_per_day) else 0.0
    # weekend structure
    dow = df["_dt"].dt.dayofweek
    weekend_bars = int((dow >= 5).sum())
    weekday_bars = int((dow < 5).sum())
    return {
        "path": str(path),
        "rows": total_rows,
        "start": start.isoformat() if start is not pd.NaT else None,
        "end": end.isoformat() if end is not pd.NaT else None,
        "span_days": float((end - start).total_seconds() / 86400) if end is not pd.NaT and start is not pd.NaT else None,
        "median_bars_per_day": median_bpd,
        "p90_bars_per_day": p90_bpd,
        "weekend_bars": weekend_bars,
        "weekday_bars": weekday_bars,
        "weekend_fraction": round(weekend_bars / max(total_rows, 1), 4),
        "format": fmt,
    }


def summarize_candidates(data_dir: Path) -> list:
    return [inspect_file_structure(Path(c.path)) for c in discover_candidates(data_dir)]
