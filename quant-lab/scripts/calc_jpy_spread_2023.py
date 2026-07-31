#!/usr/bin/env python3
"""
Calculate historical average spread for JPY pairs from 2023 onward.
Uses PRO CSV files which have a 'spread' column.
"""
import csv
from pathlib import Path

DATA_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")

JPY_PAIRS = ["EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY", "USDJPY"]

def calc_spread_from_2023(pair):
    """Calculate average spread from 2023-01-01 onward."""
    # Try PRO file first (has spread column)
    for pattern in [f"{pair}_PRO_M5.csv", f"{pair}_PRO.csv"]:
        filepath = DATA_DIR / pattern
        if not filepath.exists():
            continue
        
        spreads = []
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            spread_col = None
            time_col = 0
            if header:
                for i, h in enumerate(header):
                    if h.lower().strip() == 'spread':
                        spread_col = i
                    if h.lower().strip() in ('time', 'timestamp', 'date'):
                        time_col = i
            for row in reader:
                if not row:
                    continue
                try:
                    year = int(row[time_col][:4])
                    if year < 2023:
                        continue
                except:
                    continue
                if spread_col is not None and len(row) > spread_col:
                    try:
                        s = float(row[spread_col])
                        if s > 0:
                            spreads.append(s)
                    except:
                        continue
        if spreads:
            return sum(spreads) / len(spreads), len(spreads), pattern
    
    # Fallback: use regular CSV, high-low range as proxy
    for pattern in [f"{pair}_M5.csv", f"{pair}.csv"]:
        filepath = DATA_DIR / pattern
        if not filepath.exists():
            continue
        
        spreads = []
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            time_col = 0
            if header:
                for i, h in enumerate(header):
                    if h.lower().strip() in ('time', 'timestamp', 'date'):
                        time_col = i
            for row in reader:
                if not row or len(row) < 4:
                    continue
                try:
                    year = int(row[time_col][:4])
                    if year < 2023:
                        continue
                    high = float(row[2])
                    low = float(row[3])
                    spread = high - low
                    if spread > 0:
                        spreads.append(spread)
                except:
                    continue
        if spreads:
            return sum(spreads) / len(spreads), len(spreads), pattern + " (H-L)"
    
    return None, 0, "NOT FOUND"

print("JPY Pair Historical Spread (2023 onward)")
print("=" * 70)
print(f"{'Pair':12s} {'File':30s} {'AvgSpread':>12s} {'Samples':>10s}")
print("-" * 70)

for pair in JPY_PAIRS:
    avg, n, fname = calc_spread_from_2023(pair)
    if avg is not None:
        print(f"{pair:12s} {fname:30s} {avg:12.2f} {n:>10d}")
    else:
        print(f"{pair:12s} {'NO DATA':30s}")
