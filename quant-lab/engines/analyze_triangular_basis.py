#!/usr/bin/env python3
"""
Analyze triangular basis statistics for GBPAUD/GBPNZD/AUDNZD
"""

import numpy as np
import csv
from datetime import datetime
from pathlib import Path

_TIMESTAMP_FORMATS = [
    "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
    "%Y%m%d %H:%M:%S",
]

def parse_timestamp(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp '{raw}'")

def load_bars_csv(csv_path: str):
    bars = []
    path = Path(csv_path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = "\t" if "\t" in first_line else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            clean_row = {k.strip().strip("<").strip(">"): v for k, v in row.items()}
            ts_raw = (clean_row.get("timestamp") or clean_row.get("Timestamp")
                      or clean_row.get("TIMESTAMP") or clean_row.get("datetime")
                      or clean_row.get("Datetime") or clean_row.get("DATETIME")
                      or clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
            if ts_raw is None:
                date_val = (clean_row.get("date") or clean_row.get("Date") or clean_row.get("DATE"))
                time_val = (clean_row.get("time") or clean_row.get("Time") or clean_row.get("TIME"))
                if date_val and time_val:
                    ts_raw = f"{date_val.strip()} {time_val.strip()}"
            if ts_raw is None or not ts_raw.strip():
                continue
            o = clean_row.get("OPEN") or clean_row.get("open")
            h = clean_row.get("HIGH") or clean_row.get("high")
            l = clean_row.get("LOW") or clean_row.get("low")
            c = clean_row.get("CLOSE") or clean_row.get("close")
            if any(v is None for v in (o, h, l, c)):
                continue
            bars.append({
                'timestamp': parse_timestamp(ts_raw),
                'open': float(o), 'high': float(h), 'low': float(l), 'close': float(c)
            })
    bars.sort(key=lambda b: b['timestamp'])
    return bars

def synchronize_bars(gbp_aud_bars, gbp_nzd_bars, aud_nzd_bars):
    gbp_aud_map = {b['timestamp']: b for b in gbp_aud_bars}
    gbp_nzd_map = {b['timestamp']: b for b in gbp_nzd_bars}
    aud_nzd_map = {b['timestamp']: b for b in aud_nzd_bars}
    
    all_timestamps = set(gbp_aud_map.keys()) | set(gbp_nzd_map.keys()) | set(aud_nzd_map.keys())
    all_timestamps = sorted(all_timestamps)
    
    synced = []
    for ts in all_timestamps:
        gbp_aud_bar = gbp_aud_map.get(ts)
        gbp_nzd_bar = gbp_nzd_map.get(ts)
        aud_nzd_bar = aud_nzd_map.get(ts)
        
        if gbp_aud_bar and gbp_nzd_bar and aud_nzd_bar:
            synced.append({
                'timestamp': ts,
                'gbp_aud': gbp_aud_bar['close'],
                'gbp_nzd': gbp_nzd_bar['close'],
                'aud_nzd': aud_nzd_bar['close'],
            })
    return synced

def compute_basis(bars):
    basis = []
    for bar in bars:
        b = np.log(bar['gbp_aud']) - np.log(bar['gbp_nzd']) + np.log(bar['aud_nzd'])
        basis.append(b)
    return basis

def main():
    print("Loading data...")
    gbp_aud_bars = load_bars_csv("quant-lab/data/GBPAUD_M5.csv")
    gbp_nzd_bars = load_bars_csv("quant-lab/data/GBPNZD_M5.csv")
    aud_nzd_bars = load_bars_csv("quant-lab/data/AUDNZD_PRO_M5.csv")
    
    print(f"  GBPAUD: {len(gbp_aud_bars):,} bars")
    print(f"  GBPNZD: {len(gbp_nzd_bars):,} bars")
    print(f"  AUDNZD: {len(aud_nzd_bars):,} bars")
    
    print("Synchronizing bars...")
    synced_bars = synchronize_bars(gbp_aud_bars, gbp_nzd_bars, aud_nzd_bars)
    print(f"  Synchronized: {len(synced_bars):,} bars")
    
    print("Computing basis...")
    basis = compute_basis(synced_bars)
    
    print("\n=== BASIS STATISTICS ===")
    print(f"Count: {len(basis):,}")
    print(f"Mean: {np.mean(basis):.8f}")
    print(f"Std:  {np.std(basis):.8f}")
    print(f"Min:  {np.min(basis):.8f}")
    print(f"Max:  {np.max(basis):.8f}")
    print(f"Range: {np.max(basis) - np.min(basis):.8f}")
    
    # Percentiles
    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
        print(f"  P{p}: {np.percentile(basis, p):.8f}")
    
    # Rolling z-score analysis
    lookback = 100
    z_scores = []
    for i in range(len(basis)):
        if i < lookback:
            z_scores.append(0.0)
        else:
            window = basis[i-lookback:i]
            mean = np.mean(window)
            std = np.std(window)
            if std > 0:
                z = (basis[i] - mean) / std
            else:
                z = 0.0
            z_scores.append(z)
    
    print("\n=== Z-SCORE STATISTICS ===")
    print(f"Mean: {np.mean(z_scores):.4f}")
    print(f"Std:  {np.std(z_scores):.4f}")
    print(f"Min:  {np.min(z_scores):.4f}")
    print(f"Max:  {np.max(z_scores):.4f}")
    
    # Count exceedances
    for threshold in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
        above = sum(1 for z in z_scores if z > threshold)
        below = sum(1 for z in z_scores if z < -threshold)
        total = above + below
        print(f"  |z| > {threshold}: {total:,} ({total/len(z_scores)*100:.2f}%)  [above: {above:,}, below: {below:,}]")
    
    # Autocorrelation
    print("\n=== AUTOCORRELATION ===")
    for lag in [1, 5, 10, 20, 50, 100]:
        if lag < len(basis):
            corr = np.corrcoef(basis[:-lag], basis[lag:])[0,1]
            print(f"  Lag {lag}: {corr:.4f}")
    
    # Half-life estimation (OU process)
    # Using AR(1) coefficient
    if len(basis) > 1:
        ar1 = np.corrcoef(basis[:-1], basis[1:])[0,1]
        if ar1 > 0 and ar1 < 1:
            half_life = -np.log(2) / np.log(ar1)
            print(f"\n=== MEAN REVERSION ===")
            print(f"  AR(1) coefficient: {ar1:.6f}")
            print(f"  Half-life (bars): {half_life:.1f}")
            print(f"  Half-life (hours): {half_life * 5 / 60:.1f}")  # 5-min bars
    
    # Session analysis
    print("\n=== SESSION ANALYSIS (EST) ===")
    asian_basis = []
    london_basis = []
    ny_basis = []
    
    for i, bar in enumerate(synced_bars):
        est_hour = (bar['timestamp'].hour - 5) % 24
        if est_hour >= 19 or est_hour < 3:
            asian_basis.append(basis[i])
        elif 3 <= est_hour < 12:
            london_basis.append(basis[i])
        elif 12 <= est_hour < 17:
            ny_basis.append(basis[i])
    
    for name, data in [("Asian (7PM-3AM)", asian_basis), ("London (3AM-12PM)", london_basis), ("NY (12PM-5PM)", ny_basis)]:
        if data:
            print(f"  {name}: mean={np.mean(data):.8f}, std={np.std(data):.8f}, count={len(data):,}")

if __name__ == "__main__":
    main()