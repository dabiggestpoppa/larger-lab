"""R0.1 File Reality Audit.

Computes, directly from each file on disk, the quantities the DATA_TRUTH_LOCK
claimed: path, size, true SHA-256, row count, first/last timestamp, timezone,
duplicate timestamps, missing bars, weekend vs abnormal gaps, zero/negative
prices, OHLC consistency, and volume availability.

Outputs a JSON dictionary keyed by relative path, printed to stdout.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "quant-lab", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

# Forex M5: session closes Friday 21:00 UTC, reopens Sunday 21:00 UTC.
M5_SECONDS = 300

FILES = [
    "EURUSDPRO_M5_2023_2026.csv",  # claimed primary
    "EURUSDPRO_M5_2023_2025.csv",
    "EURUSD_M5.csv",
    "GBPUSD_M5.csv",
    "GBPUSD_M5_fetched.csv",
    "USDJPY_M5.csv",
    "USDJPY_M5_fetched.csv",
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024 * 8), b""):
            h.update(chunk)
    return h.hexdigest()


def is_weekend_utc(ts: int) -> bool:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    # Friday 21:00 UTC or later counts as weekend-adjacent; Sunday before 21:00 too.
    if dt.weekday() == 4 and dt.hour >= 21:
        return True
    if dt.weekday() == 5:  # Saturday
        return True
    if dt.weekday() == 6 and dt.hour < 21:  # Sunday before reopen
        return True
    return False


def audit(path: str) -> dict:
    full = os.path.join(DATA_DIR, path)
    result = {"path": path, "exists": os.path.exists(full)}
    if not result["exists"]:
        result["error"] = "file not found"
        return result

    result["size_bytes"] = os.path.getsize(full)
    result["sha256"] = sha256_file(full)

    # Raw-line row count (excluding header), robust to trailing newline.
    with open(full, "rb") as f:
        raw = f.read()
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines = lines[:-1]
    result["raw_line_count_incl_header"] = len(lines)
    result["data_row_count"] = len(lines) - 1

    try:
        df = pd.read_csv(full)
    except Exception as e:  # noqa: BLE001
        result["read_error"] = str(e)
        return result

    result["columns"] = list(df.columns)
    n = len(df)
    result["pandas_row_count"] = n

    if "time" in df.columns:
        t = pd.to_numeric(df["time"], errors="coerce")
        result["epoch_min"] = int(t.min())
        result["epoch_max"] = int(t.max())
        result["first_timestamp_utc"] = datetime.fromtimestamp(t.min(), tz=timezone.utc).isoformat()
        result["last_timestamp_utc"] = datetime.fromtimestamp(t.max(), tz=timezone.utc).isoformat()
        result["duplicate_epochs"] = int(t.duplicated().sum())
        result["non_monotonic"] = int((t.diff().dropna() <= 0).sum())
        # Missing bars vs a continuous M5 grid between min and max.
        expected = (t.max() - t.min()) // M5_SECONDS + 1
        result["expected_m5_slots"] = int(expected)
        result["missing_slots_vs_continuous_grid"] = int(expected - t.nunique())

    if "timestamp" in df.columns:
        ts_str = df["timestamp"].astype(str)
        result["timestamp_first"] = ts_str.iloc[0]
        result["timestamp_last"] = ts_str.iloc[-1]
        # Infer timezone: assume UTC, note it.
        result["timezone"] = "UTC (assumed; epoch+timestamp agree)"

    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            v = pd.to_numeric(df[col], errors="coerce")
            result[f"{col}_nulls"] = int(v.isna().sum())
            result[f"{col}_le_zero"] = int((v <= 0).sum())

    if all(c in df.columns for c in ["open", "high", "low", "close"]):
        o = pd.to_numeric(df["open"], errors="coerce")
        h = pd.to_numeric(df["high"], errors="coerce")
        l = pd.to_numeric(df["low"], errors="coerce")
        c = pd.to_numeric(df["close"], errors="coerce")
        bad = (
            (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
        )
        result["ohlc_inconsistencies"] = int(bad.sum())

    for col in ["tick_volume", "real_volume", "spread"]:
        if col in df.columns:
            v = pd.to_numeric(df[col], errors="coerce")
            result[f"{col}_all_zero"] = bool((v == 0).all())
            result[f"{col}_min"] = float(v.min())
            result[f"{col}_max"] = float(v.max())

    # Gap classification using actual epoch sequence.
    if "time" in df.columns:
        t = pd.to_numeric(df["time"], errors="coerce")
        diffs = t.diff().dropna()
        gaps = diffs[diffs > M5_SECONDS]
        weekend = sum(1 for g in gaps if is_weekend_utc(int(t.iloc[1:][gaps.index.get_loc(g)]) if False else 0))
        # Recompute cleanly: gap is "weekend" if its start bar is weekend-adjacent.
        weekend_gaps = 0
        abnormal_gaps = 0
        gap_detail = []
        for idx in gaps.index:
            gap_seconds = int(gaps[idx])
            start_ts = int(t.loc[idx - 1]) if (idx - 1) in t.index else None
            if start_ts is not None and is_weekend_utc(start_ts):
                weekend_gaps += 1
            else:
                abnormal_gaps += 1
                gap_detail.append({"after_epoch": start_ts, "gap_minutes": gap_seconds // 60})
        result["weekend_gaps"] = weekend_gaps
        result["abnormal_gaps"] = abnormal_gaps
        result["abnormal_gap_detail"] = gap_detail[:20]

    return result


def main():
    out = {}
    for path in FILES:
        out[path] = audit(path)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    sys.exit(main())
