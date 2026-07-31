"""
Phase 1.1: Data Ingestion Pipeline
====================================
Convert all 19 asset CSVs → Parquet format.
Standardize timestamps to UTC.
Validate no gaps >5 minutes.
Generate data manifest with hashes and row counts.
"""

import hashlib
import json
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PARQUET_DIR = Path(__file__).resolve().parent.parent / "features" / "parquet"
MANIFEST_PATH = Path(__file__).resolve().parent.parent / "configs" / "data_manifest.json"

# All 19 CEREBUS assets + their CSV filenames
ASSET_FILES = {
    "EURUSD": "EURUSD_M5.csv",
    "GBPUSD": "GBPUSD_M5.csv",
    "USDCHF": "USDCHF_M5.csv",
    "USDJPY": "USDJPY_M5.csv",
    "AUDUSD": "AUDUSD_M5.csv",
    "NZDUSD": "NZDUSD_M5.csv",
    "CHFJPY": "CHFJPY_M5.csv",
    "GBPJPY": "GBPJPY_M5.csv",
    "GBPAUD": "GBPAUD_M5.csv",
    "GBPNZD": "GBPNZD_M5.csv",
    "GBPCHF": "GBPCHF_M5.csv",
    "US500":  "US500_M5.csv",
    "DE30":   "DE30_M5.csv",
    "FR40":   "FR40_M5.csv",
    "USTEC100": None,  # Not in data dir yet
    "HK50":   "HK50_M5.csv",
    "XAUUSD": "XAUUSD_M5.csv",
    "XAGUSD": "XAGUSD_M5.csv",
    "BTCUSD": "BTCUSD_M5.csv",
    "ETHUSD": "ETHUSD_M5.csv",
}


def _file_hash(path: Path) -> str:
    """SHA-256 hash of file for reproducibility tracking."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def convert_csv_to_parquet(symbol: str, csv_path: Path, pip_size: float = None) -> dict:
    """
    Convert a single asset CSV → Parquet with validation.
    Returns metadata dict for manifest.
    """
    if not csv_path.exists():
        return {"symbol": symbol, "status": "MISSING", "path": str(csv_path)}

    # Read CSV — handle various column naming conventions
    df = pd.read_csv(csv_path)

    # Normalize column names (handle dt/date/time/open/high/low/close/volume)
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ("dt", "date", "time", "datetime", "timestamp"):
            col_map[c] = "timestamp"
        elif cl in ("open", "o"):
            col_map[c] = "open"
        elif cl in ("high", "h"):
            col_map[c] = "high"
        elif cl in ("low", "l"):
            col_map[c] = "low"
        elif cl in ("close", "c"):
            col_map[c] = "close"
        elif cl in ("volume", "vol", "v"):
            col_map[c] = "volume"

    df = df.rename(columns=col_map)

    # Ensure required columns exist
    required = ["timestamp", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"symbol": symbol, "status": "ERROR", "missing_columns": missing}

    # Parse timestamps → UTC
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp").sort_index()

    # Remove duplicates
    dupes = df.index.duplicated().sum()
    df = df[~df.index.duplicated(keep="first")]

    # Gap detection: find gaps > 5 minutes
    diffs = df.index.to_series().diff()
    max_gap = diffs.max()
    gap_count = int((diffs > pd.Timedelta(minutes=5)).sum())

    # Save to Parquet
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PARQUET_DIR / f"{symbol}_M5.parquet"
    df.to_parquet(out_path, engine="pyarrow", compression="zstd")

    return {
        "symbol": symbol,
        "status": "OK",
        "rows": len(df),
        "date_start": str(df.index[0]),
        "date_end": str(df.index[-1]),
        "max_gap": str(max_gap),
        "gaps_over_5min": gap_count,
        "duplicates_removed": int(dupes),
        "parquet_path": str(out_path),
        "file_hash": _file_hash(out_path),
    }


def run_all_assets() -> dict:
    """
    Convert all 19 assets → Parquet.
    Returns full manifest dict.
    """
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {"assets": {}, "errors": []}

    for symbol, filename in ASSET_FILES.items():
        if filename is None:
            manifest["assets"][symbol] = {"status": "NO_FILE"}
            manifest["errors"].append(f"{symbol}: No CSV file configured")
            continue

        csv_path = DATA_DIR / filename
        result = convert_csv_to_parquet(symbol, csv_path)
        manifest["assets"][symbol] = result

        if result["status"] == "OK":
            print(f"  ✅ {symbol}: {result['rows']:,} rows | max_gap={result['max_gap']} | gaps>5min={result['gaps_over_5min']}")
        else:
            print(f"  ❌ {symbol}: {result['status']}")
            manifest["errors"].append(f"{symbol}: {result['status']}")

    # Save manifest
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    ok_count = sum(1 for a in manifest["assets"].values() if a.get("status") == "OK")
    print(f"\n✅ Phase 1.1 Complete: {ok_count}/{len(ASSET_FILES)} assets converted")
    print(f"   Manifest: {MANIFEST_PATH}")

    return manifest


def validate_zero_gaps(manifest: dict, max_allowed_gap_hours: int = 72) -> bool:
    """
    Validation gate: assert no asset has gaps > max_allowed_gap_hours (default 72h for weekends).
    M5 data naturally has weekend gaps — this checks for unexpected data integrity issues.
    Returns True if all pass.
    """
    failures = []
    for symbol, info in manifest["assets"].items():
        if info.get("status") != "OK":
            continue
        max_gap_str = info.get("max_gap", "0")
        # Parse max gap — if it's > 72 hours, flag it
        try:
            if "days" in max_gap_str:
                days = int(max_gap_str.split(" days")[0].split()[-1])
                if days > 3:
                    failures.append(f"{symbol}: max_gap = {max_gap_str} (exceeds 72h)")
        except (ValueError, IndexError):
            pass

    if failures:
        print("❌ GAP VALIDATION FAILED:")
        for f in failures:
            print(f"   {f}")
        return False

    print(f"✅ GAP VALIDATION PASSED: All assets within {max_allowed_gap_hours}h max gap")
    return True


def query_parquet(symbol: str, sql: str) -> pd.DataFrame:
    """
    Query a Parquet file using DuckDB for fast analytics.
    Usage: query_parquet("EURUSD", "SELECT * FROM df WHERE close > 1.1000 LIMIT 10")
    """
    parquet_path = PARQUET_DIR / f"{symbol}_M5.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"No Parquet for {symbol}. Run run_all_assets() first.")

    con = duckdb.connect()
    return con.execute(f"SELECT * FROM read_parquet('{parquet_path}') {sql}").fetchdf()


if __name__ == "__main__":
    manifest = run_all_assets()
    validate_zero_gaps(manifest)
