#!/usr/bin/env python3
"""
Data prep: Read downloaded CSV files and convert to Nautilus-compatible format.
Scans C:\Users\wifik\Downloads for M1/M5 CSV files.
Outputs parquet files to nautilus/data/
"""
import os
import sys
import glob
import pandas as pd
from pathlib import Path

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

LOG_FILE = DATA_DIR / "prep_log.txt"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def detect_format(df):
    """Detect CSV column format."""
    cols = [c.lower() for c in df.columns]
    if 'open' in cols and 'high' in cols and 'low' in cols and 'close' in cols:
        return 'ohlc'
    if 'bidopen' in cols or 'bid' in cols[0] if cols else False:
        return 'bidask'
    return 'unknown'

def parse_csv(filepath):
    """Parse a single CSV file into a clean DataFrame."""
    # Try different separators and formats
    for sep in [',', ';', '\t', '|']:
        try:
            df = pd.read_csv(filepath, sep=sep, nrows=5)
            if len(df.columns) >= 4:
                df = pd.read_csv(filepath, sep=sep)
                break
        except:
            continue
    else:
        df = pd.read_csv(filepath)
    
    # Detect and standardize columns
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
        df = df.dropna(subset=['time'])
        df = df.set_index('time')
    
    # Ensure required columns
    for col in ['open', 'high', 'low', 'close']:
        if col not in df.columns:
            return None
    
    # Add volume if missing
    if 'volume' not in df.columns:
        df['volume'] = 0
    
    # Sort and deduplicate
    df = df.sort_index()
    df = df[~df.index.duplicated(keep='first')]
    
    return df[['open', 'high', 'low', 'close', 'volume']]

def extract_symbol(filename):
    """Extract symbol from filename like EURUSD!_M5_202301020000_202605061250.csv"""
    name = Path(filename).stem
    # Remove timeframe and date parts
    parts = name.replace('!', '').split('_')
    for i, p in enumerate(parts):
        if p in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']:
            return '_'.join(parts[:i])
    return parts[0]

def extract_timeframe(filename):
    """Extract timeframe from filename."""
    name = Path(filename).stem.upper()
    for tf in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1']:
        if f'_{tf}_' in name or name.endswith(f'_{tf}'):
            return tf
    return 'UNKNOWN'

def main():
    log(f"{'='*60}")
    log(f"DATA PREP — {pd.Timestamp.now()}")
    log(f"{'='*60}")
    
    # Find all CSV files
    csv_files = list(DOWNLOADS.glob("*.csv"))
    log(f"Found {len(csv_files)} CSV files in Downloads")
    
    # Group by symbol
    symbols = {}
    for f in csv_files:
        symbol = extract_symbol(f.name)
        tf = extract_timeframe(f.name)
        key = f"{symbol}_{tf}"
        if key not in symbols:
            symbols[key] = []
        symbols[key].append(f)
    
    log(f"Grouped into {len(symbols)} symbol/timeframe combinations:")
    for key in sorted(symbols.keys()):
        files = symbols[key]
        log(f"  {key}: {len(files)} file(s)")
    
    # Process each symbol
    results = {}
    for key in sorted(symbols.keys()):
        files = symbols[key]
        log(f"\n--- Processing {key} ({len(files)} files) ---")
        
        dfs = []
        for f in files:
            try:
                df = parse_csv(f)
                if df is not None and len(df) > 0:
                    dfs.append(df)
                    log(f"  ✓ {f.name}: {len(df)} rows, {df.index[0]} → {df.index[-1]}")
                else:
                    log(f"  ✗ {f.name}: no valid data")
            except Exception as e:
                log(f"  ✗ {f.name}: {e}")
        
        if dfs:
            combined = pd.concat(dfs)
            combined = combined.sort_index()
            combined = combined[~combined.index.duplicated(keep='first')]
            
            # Save as parquet
            out_path = DATA_DIR / f"{key}.parquet"
            combined.to_parquet(out_path)
            
            # Also save as CSV for easy inspection
            csv_path = DATA_DIR / f"{key}.csv"
            combined.to_csv(csv_path)
            
            results[key] = {
                "rows": len(combined),
                "start": str(combined.index[0]),
                "end": str(combined.index[-1]),
                "files": len(files),
                "parquet": str(out_path),
            }
            log(f"  → Saved {len(combined)} rows to {out_path.name}")
    
    # Summary
    log(f"\n{'='*60}")
    log(f"SUMMARY — {len(results)} datasets prepared:")
    for key, info in sorted(results.items()):
        log(f"  {key}: {info['rows']:,} rows ({info['start'][:10]} → {info['end'][:10]})")
    
    # Save summary JSON
    import json
    with open(DATA_DIR / "data_summary.json", "w") as f:
        json.dump(results, f, indent=2)
    log(f"\nSummary saved to {DATA_DIR / 'data_summary.json'}")
    return results

if __name__ == "__main__":
    main()
