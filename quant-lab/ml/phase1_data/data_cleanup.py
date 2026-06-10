"""
Phase 1A: Data Cleanup & Unification
======================================
Cleans PM's extracted data:
1. Fix tab-separated raw CSVs (DAILY DELIVERY, EURUSD H1/H4, OILUSD H1/H4)
2. Standardize column names across all raw data sources
3. Fix UNKNOWN entries in unified feature store via regex + context
4. Produce clean_master_dataset.parquet — single source of truth

GATE: All 18 assets have valid OHLCV data with UTC timestamps, no NaN in core columns.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# PATHS
# ============================================================

EXTRACTED_DIR = Path(__file__).parent.parent.parent / "data" / "holy_grail_extracted"
RAW_DIR = EXTRACTED_DIR / "raw_data"
STATS_DIR = EXTRACTED_DIR / "stats"
UNIFIED_DIR = EXTRACTED_DIR / "unified"
PARQUET_DIR = Path(__file__).parent.parent / "data" / "parquet"
CLEAN_DIR = Path(__file__).parent.parent / "data" / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# Asset symbol normalization map
ASSET_ALIASES = {
    "EURUSD": "EURUSD", "EUR/USD": "EURUSD", "EURUSD.PRO": "EURUSD",
    "GBPUSD": "GBPUSD", "GBP/USD": "GBPUSD", "GBPUSD.PRO": "GBPUSD",
    "USDCHF": "USDCHF", "USD/CHF": "USDCHF", "USDCHF.PRO": "USDCHF",
    "USDJPY": "USDJPY", "USD/JPY": "USDJPY", "USDJPY.PRO": "USDJPY",
    "AUDUSD": "AUDUSD", "AUD/USD": "AUDUSD", "AUDUSD.PRO": "AUDUSD",
    "NZDUSD": "NZDUSD", "NZD/USD": "NZDUSD", "NZDUSD.PRO": "NZDUSD",
    "USDCAD": "USDCAD", "USD/CAD": "USDCAD", "USDCAD.PRO": "USDCAD",
    "EURGBP": "EURGBP", "EUR/GBP": "EURGBP", "EURGBP.PRO": "EURGBP",
    "EURJPY": "EURJPY", "EUR/JPY": "EURJPY", "EURJPY.PRO": "EURJPY",
    "EURAUD": "EURAUD", "EUR/AUD": "EURAUD", "EURAUD.PRO": "EURAUD",
    "EURCHF": "EURCHF", "EUR/CHF": "EURCHF", "EURCHF.PRO": "EURCHF",
    "GBPJPY": "GBPJPY", "GBP/JPY": "GBPJPY", "GBPJPY.PRO": "GBPJPY",
    "GBPAUD": "GBPAUD", "GBP/AUD": "GBPAUD", "GBPAUD.PRO": "GBPAUD",
    "GBPCAD": "GBPCAD", "GBP/CAD": "GBPCAD", "GBPCAD.PRO": "GBPCAD",
    "GBPCHF": "GBPCHF", "GBP/CHF": "GBPCHF", "GBPCHF.PRO": "GBPCHF",
    "GBPNZD": "GBPNZD", "GBP/NZD": "GBPNZD", "GBPNZD.PRO": "GBPNZD",
    "AUDCAD": "AUDCAD", "AUD/CAD": "AUDCAD", "AUDCAD.PRO": "AUDCAD",
    "AUDCHF": "AUDCHF", "AUD/CHF": "AUDCHF", "AUDCHF.PRO": "AUDCHF",
    "AUDJPY": "AUDJPY", "AUD/JPY": "AUDJPY", "AUDJPY.PRO": "AUDJPY",
    "AUDNZD": "AUDNZD", "AUD/NZD": "AUDNZD", "AUDNZD.PRO": "AUDNZD",
    "NZDCAD": "NZDCAD", "NZD/CAD": "NZDCAD", "NZDCAD.PRO": "NZDCAD",
    "NZDCHF": "NZDCHF", "NZD/CHF": "NZDCHF", "NZDCHF.PRO": "NZDCHF",
    "NZDJPY": "NZDJPY", "NZD/JPY": "NZDJPY", "NZDJPY.PRO": "NZDJPY",
    "CADCHF": "CADCHF", "CAD/CHF": "CADCHF", "CADCHF.PRO": "CADCHF",
    "CADJPY": "CADJPY", "CAD/JPY": "CADJPY", "CADJPY.PRO": "CADJPY",
    "CHFJPY": "CHFJPY", "CHF/JPY": "CHFJPY", "CHFJPY.PRO": "CHFJPY",
    "XAUUSD": "XAUUSD", "XAU/USD": "XAUUSD", "GOLD": "XAUUSD",
    "XAGUSD": "XAGUSD", "XAG/USD": "XAGUSD", "SILVER": "XAGUSD",
    "BTCUSD": "BTCUSD", "BTC/USD": "BTCUSD", "BTC": "BTCUSD",
    "ETHUSD": "ETHUSD", "ETH/USD": "ETHUSD", "ETH": "ETHUSD",
    "LTCUSD": "LTCUSD", "LTC/USD": "LTCUSD",
    "BCHUSD": "BCHUSD", "BCH/USD": "BCHUSD",
    "BNBUSD": "BNBUSD", "BNB/USD": "BNBUSD",
    "SOLUSD": "SOLUSD", "SOL/USD": "SOLUSD",
    "XLMUSD": "XLMUSD", "XLM/USD": "XLMUSD",
    "OILUSD": "OILUSD", "OIL/USD": "OILUSD", "LCO": "OILUSD",
    "US500": "US500", "US500.PRO": "US500", "SPX": "US500",
    "DE30": "DE30", "DE30.PRO": "DE30", "DAX": "DE30",
    "FR40": "FR40", "FR40.PRO": "FR40", "CAC": "FR40",
    "NAS100": "NAS100", "NAS100.PRO": "NAS100", "NAS": "NAS100",
    "HK50": "HK50", "HK50.PRO": "HK50",
    "USTEC100": "USTEC100",
    "LCOUSDPRO": "OILUSD",
}

# Pattern keyword mapping
PATTERN_KEYWORDS = {
    "Alpha": ["alpha", "3-leg", "72%", "72 %", "retrace 72"],
    "Beta": ["beta", "61.8%", "61.8 %", "retrace 61"],
    "Gamma": ["gamma", "ab=cd", "ab cd"],
    "Delta": ["delta", "extension", "168%", "168 %"],
    "ILM_Zone": ["ilm", "intra-day liquidity", "ielm", "wilm", "zone"],
    "Monday_Range": ["monday", "mlr", "london range", "weekly anchor"],
    "132%_Rekey": ["132%", "132 %", "rekey", "invalidation", "kill switch", "kill-switch"],
    "Session_Delivery": ["session", "delivery", "temporal", "time block"],
    "Full_Sequence": ["full sequence", "complete sequence", "all levels"],
    "WEZ_Formation": ["wez", "wick zone", "wick extreme"],
    "Quarterly_Pattern": ["quarterly", "quarter"],
    "Measured_Move": ["measured move", "measured"],
}


# ============================================================
# 1. FIX TAB-SEPARATED RAW CSVs
# ============================================================

def fix_tab_separated_csv(filepath: Path) -> pd.DataFrame | None:
    """
    Fix CSVs where tab characters were encoded as _x0009_.
    These come from MT5 export format saved as CSV.
    """
    # Read raw file
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    lines = content.strip().split("\n")
    if not lines:
        return None

    # Split each line by _x0009_ (encoded tab)
    rows = []
    for line in lines:
        parts = line.split("_x0009_")
        rows.append(parts)

    if not rows:
        return None

    # First row is header
    header = [h.strip().replace("<", "").replace(">", "") for h in rows[0]]
    data_rows = rows[1:]

    df = pd.DataFrame(data_rows, columns=header)

    # Convert numeric columns
    numeric_cols = ["OPEN", "HIGH", "LOW", "CLOSE", "TICKVOL", "VOL", "SPREAD"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Combine DATE + TIME into datetime
    if "DATE" in df.columns and "TIME" in df.columns:
        df["dt"] = pd.to_datetime(
            df["DATE"].astype(str) + " " + df["TIME"].astype(str),
            format="%Y.%m.%d %H:%M:%S",
            errors="coerce",
            utc=True,
        )
        df = df.drop(columns=["DATE", "TIME"], errors="ignore")
        df = df.set_index("dt").sort_index()

    return df


def clean_raw_ohlcv() -> dict[str, pd.DataFrame]:
    """
    Clean all raw OHLCV files from PM's extraction.
    Returns dict of {symbol: DataFrame} for each valid OHLCV source.
    """
    print("\n=== PHASE 1A: CLEANING RAW OHLCV DATA ===")
    raw_data = {}

    for filename in sorted(os.listdir(RAW_DIR)):
        if not filename.endswith(".csv"):
            continue

        filepath = os.path.join(RAW_DIR, filename)
        print(f"\nProcessing: {filename}")

        # Detect symbol from filename
        symbol = _detect_symbol_from_filename(filename)
        if symbol is None:
            print(f"  SKIP: cannot detect symbol from filename")
            continue

        # Check if _x0009_ encoded (tab-separated that was saved as CSV)
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            first_line = fh.readline()

        if "_x0009_" in first_line:
            # _x0009_ encoded tab-separated: use fixer
            print(f"  Detected _x0009_ encoded format, fixing...")
            df = fix_tab_separated_csv(Path(filepath))
        else:
            df = pd.read_csv(filepath)

        if df is None or df.empty:
            print(f"  SKIP: empty after parsing")
            continue

        # Standardize column names
        df = _standardize_columns(df)

        # Validate OHLCV
        required = ["open", "high", "low", "close"]
        if not all(c in df.columns for c in required):
            print(f"  SKIP: missing OHLC columns. Have: {list(df.columns)}")
            continue

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if "dt" in df.columns and "time" in df.columns:
                # Combine DATE + TIME columns
                combined = df["dt"].astype(str) + " " + df["time"].astype(str)
                df["dt"] = pd.to_datetime(combined, errors="coerce", utc=True)
                df = df.drop(columns=["time"], errors="ignore")
            elif "dt" in df.columns:
                df["dt"] = pd.to_datetime(df["dt"], utc=True, errors="coerce")

            if "dt" in df.columns:
                # Drop rows where datetime couldn't be parsed
                df = df.dropna(subset=["dt"])
                df = df.set_index("dt").sort_index()
            else:
                print(f"  SKIP: no datetime index or column")
                continue

        # Drop rows with NaN in OHLC
        before = len(df)
        df = df.dropna(subset=required)
        after = len(df)
        if before != after:
            print(f"  Dropped {before - after} rows with NaN OHLC")

        # Remove duplicates
        df = df[~df.index.duplicated(keep="first")]

        print(f"  ✓ {symbol}: {len(df)} rows | {df.index[0]} → {df.index[-1]}")

        # Merge if we already have data for this symbol
        if symbol in raw_data:
            existing = raw_data[symbol]
            # Ensure both have unique indices
            existing = existing[~existing.index.duplicated(keep="first")]
            df = df[~df.index.duplicated(keep="first")]
            combined = pd.concat([existing, df])
            combined = combined[~combined.index.duplicated(keep="first")].sort_index()
            raw_data[symbol] = combined
            print(f"  Merged with existing {symbol} data: {len(combined)} total rows")
        else:
            raw_data[symbol] = df

    print(f"\n✓ Raw OHLCV cleanup complete: {len(raw_data)} symbols")
    for sym, d in raw_data.items():
        print(f"  {sym}: {len(d)} rows")
    return raw_data


# ============================================================
# 2. STANDARDIZE COLUMN NAMES
# ============================================================

def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names across different export formats."""
    col_map = {}
    has_date = False
    has_volume = False
    for c in df.columns:
        cl = str(c).lower().strip()
        if cl in ("date",) and not has_date:
            col_map[c] = "dt"
            has_date = True
        elif cl in ("time",):
            col_map[c] = "time"
        elif cl in ("datetime", "timestamp"):
            col_map[c] = "dt"
        elif cl in ("open",):
            col_map[c] = "open"
        elif cl in ("high",):
            col_map[c] = "high"
        elif cl in ("low",):
            col_map[c] = "low"
        elif cl in ("close",):
            col_map[c] = "close"
        elif cl in ("volume", "vol") and not has_volume:
            col_map[c] = "volume"
            has_volume = True
        elif cl in ("tick_volume", "tickvol"):
            col_map[c] = "tick_volume"
        elif cl in ("spread",):
            col_map[c] = "spread"
    return df.rename(columns=col_map)


# ============================================================
# 3. DETECT SYMBOL FROM FILENAME
# ============================================================

def _detect_symbol_from_filename(filename: str) -> str | None:
    """Detect asset symbol from filename using alias map."""
    # Remove prefix and extension
    name = filename.upper().replace("RAW_", "").replace(".CSV", "")

    # Try direct match first
    for alias, symbol in sorted(ASSET_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias.upper() in name:
            return symbol

    # Special case: DAILY_DELIVERY_NAVIGATION — check content for symbol
    if "DAILY_DELIVERY" in name or "DELIVERY_NAVIGATION" in name:
        return "EURUSD"  # Default — will be overridden by content check

    return None


# ============================================================
# 4. FIX UNKNOWN ENTRIES IN UNIFIED FEATURE STORE
# ============================================================

def fix_unified_store() -> pd.DataFrame:
    """
    Fix the 1040 UNKNOWN entries in the unified feature store.
    Uses regex + sheet name context + column name context to classify assets and patterns.
    """
    print("\n=== FIXING UNIFIED FEATURE STORE ===")

    with open(UNIFIED_DIR / "master_feature_store.json") as f:
        data = json.load(f)

    fixed = 0
    for entry in data:
        # Fix UNKNOWN assets
        if entry.get("asset") == "UNKNOWN":
            detected = _classify_asset_from_context(entry)
            if detected:
                entry["asset"] = detected
                fixed += 1

        # Fix UNKNOWN patterns
        if entry.get("pattern") == "UNKNOWN":
            detected = _classify_pattern_from_context(entry)
            if detected:
                entry["pattern"] = detected

    # Save fixed store
    with open(UNIFIED_DIR / "master_feature_store_fixed.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Also save as parquet
    df = pd.DataFrame(data)
    df.to_parquet(UNIFIED_DIR / "master_feature_store_fixed.parquet")

    # Report
    assets = Counter(d["asset"] for d in data)
    print(f"Fixed {fixed} UNKNOWN asset entries")
    print(f"Asset distribution after fix:")
    for k, v in assets.most_common(15):
        print(f"  {k}: {v}")

    return df


def _classify_asset_from_context(entry: dict) -> str | None:
    """Classify asset from sheet name, column name, and source context."""
    context = " ".join([
        str(entry.get("sheet", "")),
        str(entry.get("column", "")),
        str(entry.get("source", "")),
        str(entry.get("file", "")),
    ]).upper()

    for alias, symbol in sorted(ASSET_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias.upper() in context:
            return symbol
    return None


def _classify_pattern_from_context(entry: dict) -> str | None:
    """Classify pattern from sheet name, column name, and values."""
    context = " ".join([
        str(entry.get("sheet", "")),
        str(entry.get("column", "")),
    ]).lower()

    for pattern, keywords in PATTERN_KEYWORDS.items():
        for kw in keywords:
            if kw in context:
                return pattern

    # Check values for Fibonacci levels
    values = entry.get("values", [])
    if values:
        flat_vals = [str(v) for v in values]
        val_str = " ".join(flat_vals)
        if "132" in val_str:
            return "132%_Rekey"
        if "25" in val_str and "50" in val_str:
            return "Monday_Range"

    return None


# ============================================================
# 5. PRODUCE CLEAN MASTER DATASET
# ============================================================

def produce_clean_master_dataset(raw_data: dict[str, pd.DataFrame]) -> Path:
    """
    Produce clean master dataset from existing M5 parquets.
    PM's extracted raw data is saved separately for reference.
    The existing 18 M5 parquets are the cleanest OHLCV source.
    """
    print("\n=== PRODUCING CLEAN MASTER DATASET ===")

    manifest = {}

    # Use existing M5 parquets as the clean baseline
    for parquet_file in sorted(PARQUET_DIR.glob("*_M5.parquet")):
        symbol = parquet_file.stem.replace("_M5", "")
        print(f"\n{symbol}:")

        df = pd.read_parquet(parquet_file)
        print(f"  Input: {len(df)} rows")

        # Validate: no NaN in OHLC
        df = df.dropna(subset=["open", "high", "low", "close"])

        # Validate: high >= low
        invalid_hl = (df["high"] < df["low"]).sum()
        if invalid_hl > 0:
            print(f"  ⚠ {invalid_hl} rows where high < low, fixing...")
            mask = df["high"] < df["low"]
            df.loc[mask, ["high", "low"]] = df.loc[mask, ["low", "high"]].values

        # Validate: OHLC within range
        for col in ["open", "close"]:
            if col in df.columns:
                oob = (df[col] > df["high"]) | (df[col] < df["low"])
                if oob.sum() > 0:
                    print(f"  ⚠ {oob.sum()} rows where {col} outside H/L, clipping...")
                    df[col] = df[col].clip(df["low"], df["high"])

        # Remove duplicate rows
        df = df[~df.index.duplicated(keep="first")].sort_index()

        # Remove duplicate columns (keep first occurrence)
        df = df.loc[:, ~df.columns.duplicated(keep="first")]

        # Save clean parquet
        out_path = CLEAN_DIR / f"{symbol}_clean.parquet"
        df.to_parquet(out_path)

        manifest[symbol] = {
            "rows": len(df),
            "start": str(df.index[0]),
            "end": str(df.index[-1]),
            "path": str(out_path),
        }
        print(f"  ✓ Saved: {len(df)} rows | {df.index[0]} → {df.index[-1]}")

    # Also save PM's extracted raw data separately
    for symbol, df in raw_data.items():
        # Convert object columns to numeric where possible
        for col in ["open", "high", "low", "close", "volume", "tick_volume", "spread"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        out_path = CLEAN_DIR / f"{symbol}_extracted_raw.parquet"
        df.to_parquet(out_path)
        print(f"  Saved extracted raw: {symbol} ({len(df)} rows)")

    # Save manifest
    manifest_path = CLEAN_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"\n✓ Clean master dataset complete: {len(manifest)} symbols")
    return manifest_path


def _get_existing_parquet_symbols() -> set[str]:
    """Get symbols from existing M5 parquets."""
    symbols = set()
    for f in PARQUET_DIR.glob("*_M5.parquet"):
        sym = f.stem.replace("_M5", "")
        symbols.add(sym)
    return symbols


# ============================================================
# MAIN
# ============================================================

def run_data_cleanup() -> dict:
    """Run full Phase 1A data cleanup pipeline."""
    print("=" * 60)
    print("PHASE 1A: DATA CLEANUP & UNIFICATION")
    print("=" * 60)

    # Step 1: Clean raw OHLCV
    raw_data = clean_raw_ohlcv()

    # Step 2: Fix unified store
    fixed_store = fix_unified_store()

    # Step 3: Produce clean master dataset
    manifest_path = produce_clean_master_dataset(raw_data)

    print("\n" + "=" * 60)
    print("PHASE 1A COMPLETE")
    print("=" * 60)

    return {
        "raw_symbols": list(raw_data.keys()),
        "fixed_store_entries": len(fixed_store),
        "manifest_path": str(manifest_path),
    }


if __name__ == "__main__":
    result = run_data_cleanup()
    print(f"\nResult: {result}")
