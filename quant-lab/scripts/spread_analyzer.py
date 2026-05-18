#!/usr/bin/env python3
"""
Spread Analyzer — Calculate median spread per pair from CSV data.
"""
import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")

# Map filename patterns to pair names and whether they're indices
PAIR_INFO = {
    "EURUSD": {"name": "EUR/USD", "is_index": False},
    "USDCHF": {"name": "USD/CHF", "is_index": False},
    "GBPUSD": {"name": "GBP/USD", "is_index": False},
    "USDJPY": {"name": "USD/JPY", "is_index": False},
    "USDCAD": {"name": "USD/CAD", "is_index": False},
    "AUDUSD": {"name": "AUD/USD", "is_index": False},
    "NZDUSD": {"name": "NZD/USD", "is_index": False},
    "CHFJPY": {"name": "CHF/JPY", "is_index": False},
    "DE30":    {"name": "DE30", "is_index": True},
    "FR40":    {"name": "FR40", "is_index": True},
    "US500":   {"name": "US500", "is_index": True},
    "USTEC100":{"name": "USTEC100", "is_index": True},
}

def extract_pair_from_filename(filename):
    """Extract pair name from CSV filename."""
    # Remove .csv extension
    name = filename.replace(".csv", "")
    # Remove timeframe and date parts
    # Patterns: EURUSD!_M5_..., EURUSD!_M1_..., US500_M5_..., DE30_M1_...
    for key in PAIR_INFO:
        # Match pair at start of filename (possibly followed by !, _, or .)
        if name.startswith(key):
            return key
    return None

def parse_csv_spread(filepath, sample_every=100):
    """Parse CSV and extract spread column. Use sampling for large files."""
    spreads = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline()  # skip header
        for i, line in enumerate(f):
            if i % sample_every != 0:
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 9:
                try:
                    spread = float(parts[8])
                    if spread > 0:  # Skip 0 spreads (inactive hours)
                        spreads.append(spread)
                except ValueError:
                    continue
    return spreads

def main():
    csv_files = list(DOWNLOADS.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files")
    
    # Group files by pair
    pair_files = {}
    for f in csv_files:
        pair_key = extract_pair_from_filename(f.name)
        if pair_key:
            if pair_key not in pair_files:
                pair_files[pair_key] = []
            pair_files[pair_key].append(f)
    
    print(f"\nPairs found: {list(pair_files.keys())}")
    
    results = {}
    
    for pair_key, files in sorted(pair_files.items()):
        info = PAIR_INFO[pair_key]
        all_spreads = []
        
        # Prefer M5 files for speed, but use whatever is available
        m5_files = [f for f in files if "_M5_" in f.name]
        m1_files = [f for f in files if "_M1_" in f.name]
        
        # Use M5 files primarily
        target_files = m5_files if m5_files else m1_files
        
        for f in target_files:
            sample = 100 if "_M1_" in f.name else 1
            spreads = parse_csv_spread(f, sample_every=sample)
            all_spreads.extend(spreads)
        
        if not all_spreads:
            print(f"  {pair_key}: NO DATA")
            continue
        
        all_spreads = np.array(all_spreads)
        median_spread_points = float(np.median(all_spreads))
        mean_spread_points = float(np.mean(all_spreads))
        
        if info["is_index"]:
            # For indices, spread is in index points (dollars)
            median_pips = median_spread_points
            unit = "index_points"
        else:
            # For forex, convert points to pips (1 pip = 10 points)
            median_pips = median_spread_points / 10.0
            unit = "pips"
        
        results[pair_key] = {
            "name": info["name"],
            "is_index": info["is_index"],
            "median_spread_points": round(median_spread_points, 1),
            "mean_spread_points": round(mean_spread_points, 1),
            "median_spread_pips": round(median_pips, 2),
            "unit": unit,
            "sample_size": len(all_spreads),
            "files_used": [f.name for f in target_files],
        }
        
        print(f"  {pair_key:12s}: median={median_spread_points:.1f} points = {median_pips:.2f} {unit} (n={len(all_spreads):,})")
    
    # Save results
    output_file = RESULTS_DIR / "spread-analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    return results

if __name__ == "__main__":
    main()
