"""
Fixed data prep: Read downloaded CSV files (tab-separated, MT5 format) and convert to parquet.
"""
import os, sys, glob, json, io
import pandas as pd
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "prep_log.txt"
SUMMARY_FILE = DATA_DIR / "summary.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_mt5_csv(filepath):
    """Parse MT5 tab-separated CSV format."""
    try:
        df = pd.read_csv(filepath, sep='\t', skipinitialspace=True, engine='python')
        
        if len(df.columns) < 5:
            df = pd.read_csv(filepath, sep='\t', encoding='utf-8-sig', skipinitialspace=True, engine='python')
        
        if len(df.columns) < 5:
            return None
        
        # Normalize column names - strip < > and whitespace
        col_map = {}
        for c in df.columns:
            cl = str(c).strip().lower().replace('<', '').replace('>', '')
            if cl == 'date': col_map[c] = 'date'
            elif cl == 'time': col_map[c] = 'time'
            elif cl == 'open': col_map[c] = 'open'
            elif cl == 'high': col_map[c] = 'high'
            elif cl == 'low': col_map[c] = 'low'
            elif cl == 'close': col_map[c] = 'close'
            elif cl in ('tickvol', 'vol', 'volume', 'tick_volume'): col_map[c] = 'volume'
            elif cl == 'spread': col_map[c] = 'spread'
        
        df = df.rename(columns=col_map)
        
        # Combine date and time into datetime index
        if 'date' in df.columns and 'time' in df.columns:
            dt_str = df['date'].astype(str).str.strip() + ' ' + df['time'].astype(str).str.strip
            df['datetime'] = pd.to_datetime(dt_str, errors='coerce')
        elif 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'].astype(str), errors='coerce')
        else:
            return None
        
        df = df.dropna(subset=['datetime'])
        df = df.set_index('datetime')
        
        # Ensure numeric OHLC
        for col in ['open', 'high', 'low', 'close']:
            if col not in df.columns:
                return None
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        
        if 'volume' not in df.columns:
            df['volume'] = 0
        else:
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
        
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='first')]
        
        return df[['open', 'high', 'low', 'close', 'volume']]
        
    except Exception as e:
        log(f"  Parse error: {e}")
        return None

def main():
    log("=" * 60)
    log("FIXED DATA PREP - MT5 Tab-Separated Format")
    log("=" * 60)
    
    csv_files = sorted(glob.glob(str(DOWNLOADS / "*.csv")))
    log(f"Found {len(csv_files)} CSV files")
    
    # Group by symbol/timeframe
    groups = {}
    for f in csv_files:
        fname = os.path.basename(f)
        parts = fname.replace('.csv', '').split('_')
        if len(parts) >= 2:
            symbol = parts[0].replace('!', '')
            tf = parts[1]
            key = f"{symbol}_{tf}"
            if key not in groups:
                groups[key] = []
            groups[key].append(f)
    
    log(f"Grouped into {len(groups)} symbol/timeframe combos")
    
    summary = {}
    success_count = 0
    
    for key, files in sorted(groups.items()):
        log(f"\n--- {key} ({len(files)} files) ---")
        
        dfs = []
        for f in files:
            fname = os.path.basename(f)
            log(f"  Parsing {fname}...")
            df = parse_mt5_csv(f)
            if df is not None and len(df) > 0:
                log(f"  OK {len(df)} bars, {df.index[0]} to {df.index[-1]}")
                dfs.append(df)
            else:
                log(f"  FAIL {fname}: parse failed")
        
        if dfs:
            combined = pd.concat(dfs)
            combined = combined.sort_index()
            combined = combined[~combined.index.duplicated(keep='first')]
            
            out_path = DATA_DIR / f"{key}.parquet"
            combined.to_parquet(out_path)
            
            summary[key] = {
                "bars": len(combined),
                "start": str(combined.index[0]),
                "end": str(combined.index[-1]),
                "files": len(files),
                "path": str(out_path),
            }
            log(f"  SAVED {len(combined)} bars to {out_path.name}")
            success_count += 1
        else:
            log(f"  SKIP: no valid data")
            summary[key] = {"bars": 0, "error": "no valid data"}
    
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    log(f"\n{'=' * 60}")
    log(f"DONE: {success_count}/{len(groups)} datasets prepared")
    
    return success_count

if __name__ == "__main__":
    main()
