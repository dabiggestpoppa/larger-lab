#!/usr/bin/env python3
"""
Step 1: Data Prep — Convert downloaded CSV files to clean parquet.
Processes files in batches to handle large files.
Outputs to nautilus/data/
"""
import os, json, sys
from pathlib import Path
from datetime import datetime
import pandas as pd

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
LOG = DATA_DIR / "prep.log"
SUMMARY = DATA_DIR / "summary.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    try:
        print(line)
    except:
        pass

def parse_file(filepath):
    """Parse a single CSV file. Returns (key, df) or None."""
    name = Path(filepath).stem
    
    # Extract symbol and timeframe
    # Pattern: EURUSD!_M5_202301020000_202605061250
    parts = name.replace('!', '').split('_')
    symbol = None
    timeframe = None
    for i, p in enumerate(parts):
        if p in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']:
            timeframe = p
            symbol = '_'.join(parts[:i])
            break
    
    if not symbol or not timeframe:
        return None
    
    key = f"{symbol}_{timeframe}"
    
    # Try different separators
    df = None
    for sep in [',', ';', '\t']:
        try:
            df = pd.read_csv(filepath, sep=sep, low_memory=False)
            if len(df.columns) >= 4:
                break
        except:
            continue
    
    if df is None or len(df.columns) < 4:
        try:
            df = pd.read_csv(filepath, low_memory=False)
        except:
            return None
    
    # Standardize columns
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ['open', 'o']: col_map[c] = 'open'
        elif cl in ['high', 'h']: col_map[c] = 'high'
        elif cl in ['low', 'l']: col_map[c] = 'low'
        elif cl in ['close', 'c']: col_map[c] = 'close'
        elif cl in ['volume', 'vol', 'v', 'tick_volume', 'tickvolume']: col_map[c] = 'volume'
        elif cl in ['time', 'date', 'datetime', 'timestamp']: col_map[c] = 'time'
    
    df = df.rename(columns=col_map)
    
    # Parse time
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time']).set_index('time')
    
    # Validate
    for col in ['open', 'high', 'low', 'close']:
        if col not in df.columns:
            return None
    
    if 'volume' not in df.columns:
        df['volume'] = 0
    
    df = df[['open', 'high', 'low', 'close', 'volume']].sort_index()
    df = df[~df.index.duplicated(keep='first')]
    
    return (key, df)

def main():
    log("="*60)
    log("STEP 1: DATA PREP")
    log("="*60)
    
    csv_files = sorted(DOWNLOADS.glob("*.csv"))
    log(f"Found {len(csv_files)} CSV files")
    
    # Group by symbol_timeframe
    groups = {}
    for f in csv_files:
        name = f.stem
        parts = name.replace('!', '').split('_')
        symbol = None
        timeframe = None
        for i, p in enumerate(parts):
            if p in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']:
                timeframe = p
                symbol = '_'.join(parts[:i])
                break
        if symbol and timeframe:
            key = f"{symbol}_{timeframe}"
            if key not in groups:
                groups[key] = []
            groups[key].append(f)
    
    log(f"Grouped into {len(groups)} symbol/timeframe combos:")
    for k in sorted(groups.keys()):
        log(f"  {k}: {len(groups[k])} file(s)")
    
    # Process each group
    summary = {}
    for key in sorted(groups.keys()):
        files = groups[key]
        log(f"\n--- {key} ({len(files)} files) ---")
        
        dfs = []
        for f in files:
            try:
                result = parse_file(f)
                if result is not None:
                    k, df = result
                    dfs.append(df)
                    log(f"  ✓ {f.name}: {len(df):,} rows")
                else:
                    log(f"  ✗ {f.name}: parse failed")
            except Exception as e:
                log(f"  ERR {f.name}: {str(e)[:100]}")
        
        if not dfs:
            log(f"  SKIP: no valid data")
            continue
        
        # Merge
        combined = pd.concat(dfs).sort_index()
        combined = combined[~combined.index.duplicated(keep='first')]
        
        # Save parquet (efficient)
        pq_path = DATA_DIR / f"{key}.parquet"
        combined.to_parquet(pq_path)
        
        summary[key] = {
            "rows": len(combined),
            "start": str(combined.index[0]),
            "end": str(combined.index[-1]),
            "files": len(files),
            "parquet": str(pq_path),
            "size_mb": round(pq_path.stat().st_size / 1e6, 1),
        }
        log(f"  → {pq_path.name}: {len(combined):,} rows, {summary[key]['size_mb']} MB")
    
    with open(SUMMARY, "w") as f:
        json.dump(summary, f, indent=2)
    
    log(f"\n{'='*60}")
    log(f"DONE: {len(summary)} datasets prepared")
    for k, v in sorted(summary.items()):
        log(f"  {k}: {v['rows']:,} rows ({v['start'][:10]} → {v['end'][:10]})")
    log(f"Summary: {SUMMARY}")

if __name__ == "__main__":
    main()
