#!/usr/bin/env python3
"""
Analyze basis movement in pips to understand cost hurdle
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

def main():
    print("Loading data...")
    gbp_aud_bars = load_bars_csv("quant-lab/data/GBPAUD_M5.csv")
    gbp_nzd_bars = load_bars_csv("quant-lab/data/GBPNZD_M5.csv")
    aud_nzd_bars = load_bars_csv("quant-lab/data/AUDNZD_PRO_M5.csv")
    
    print("Synchronizing bars...")
    synced_bars = synchronize_bars(gbp_aud_bars, gbp_nzd_bars, aud_nzd_bars)
    print(f"  Synchronized: {len(synced_bars):,} bars")
    
    # Compute basis
    basis = []
    for bar in synced_bars:
        b = np.log(bar['gbp_aud']) - np.log(bar['gbp_nzd']) + np.log(bar['aud_nzd'])
        basis.append(b)
    
    # Convert basis to pips for each leg
    # 1 pip GBPAUD = 0.0001, 1 pip GBPNZD = 0.0001, 1 pip AUDNZD = 0.0001
    # But the basis is in log space
    
    # Basis change of 0.0001 in log space ≈ 1 pip in each leg
    # Actually: d(ln(P)) = dP/P, so 1 pip = 0.0001/P
    # For GBPAUD ~ 1.9: 1 pip = 0.0001/1.9 ≈ 5.26e-5 in log space
    # For GBPNZD ~ 2.0: 1 pip = 0.0001/2.0 = 5.0e-5 in log space
    # For AUDNZD ~ 1.1: 1 pip = 0.0001/1.1 ≈ 9.09e-5 in log space
    
    # So basis in "pip equivalents":
    # basis_pips = basis * 10000 (roughly, since all pairs ~1-2)
    
    basis_pips = np.array(basis) * 10000
    
    print("\n=== BASIS IN PIP EQUIVALENTS ===")
    print(f"Mean: {np.mean(basis_pips):.2f} pips")
    print(f"Std:  {np.std(basis_pips):.2f} pips")
    print(f"Min:  {np.min(basis_pips):.2f} pips")
    print(f"Max:  {np.max(basis_pips):.2f} pips")
    
    # Z-score at different lookbacks
    for lookback in [50, 100, 200]:
        z_scores = []
        for i in range(len(basis)):
            if i < lookback:
                z_scores.append(0.0)
            else:
                window = basis[i-lookback:i]
                mean = np.mean(window)
                std = np.std(window)
                z_scores.append((basis[i] - mean) / std if std > 0 else 0.0)
        
        z_scores = np.array(z_scores)
        print(f"\n  Lookback {lookback}:")
        print(f"    Z-score std: {np.std(z_scores):.2f}")
        print(f"    |z|>2: {np.sum(np.abs(z_scores) > 2):,} ({np.sum(np.abs(z_scores) > 2)/len(z_scores)*100:.1f}%)")
        print(f"    |z|>3: {np.sum(np.abs(z_scores) > 3):,} ({np.sum(np.abs(z_scores) > 3)/len(z_scores)*100:.1f}%)")
        
        # Expected move when |z|>2
        high_z = basis_pips[np.abs(z_scores) > 2]
        if len(high_z) > 0:
            print(f"    Basis at |z|>2: mean={np.mean(high_z):.2f}, std={np.std(high_z):.2f} pips")
    
    # Basis changes (mean reversion moves)
    print("\n=== BASIS CHANGES (1-bar, 5-bar, 12-bar) ===")
    for period in [1, 5, 12, 24]:
        changes = []
        for i in range(period, len(basis_pips)):
            changes.append(basis_pips[i] - basis_pips[i-period])
        changes = np.array(changes)
        print(f"  {period}-bar: mean={np.mean(changes):.3f}, std={np.std(changes):.2f}, max={np.max(np.abs(changes)):.2f}")
    
    # Half-life analysis
    print("\n=== MEAN REVERSION SPEED ===")
    # AR(1) on basis
    ar1 = np.corrcoef(basis[:-1], basis[1:])[0,1]
    half_life = -np.log(2) / np.log(ar1) if ar1 > 0 else np.inf
    print(f"  AR(1): {ar1:.6f}")
    print(f"  Half-life: {half_life:.1f} bars = {half_life*5/60:.1f} hours")
    
    # Expected reversion from z=2 to z=0
    # At z=2, basis is 2*std above mean
    # Reversion to mean = 2*std in basis units
    basis_std = np.std(basis)
    reversion_basis = 2 * basis_std
    reversion_pips = reversion_basis * 10000
    print(f"\n  Expected reversion from z=2 to z=0: {reversion_pips:.2f} pips (basis)")
    print(f"  Per leg (3 legs): ~{reversion_pips/3:.2f} pips each")
    
    # Cost comparison
    print("\n=== COST HURDLE ===")
    spread_total = 1.5 + 2.5 + 2.0  # 6 pips
    commission = 1.4 * 3  # 4.2 pips
    total_cost = spread_total + commission  # ~10.2 pips
    print(f"  Total round-trip cost (3 legs): ~{total_cost:.1f} pips")
    print(f"  Expected gross per trade (z=2→0): ~{reversion_pips:.1f} pips")
    print(f"  Net after costs: ~{reversion_pips - total_cost:.1f} pips")
    print(f"  Cost ratio: {total_cost/reversion_pips*100:.1f}%")
    
    # What z-score needed to overcome costs?
    needed_z = total_cost / (basis_std * 10000)
    print(f"\n  Z-score needed to break even: {needed_z:.2f}")
    print(f"  (Current entry at z=2.0 gives {reversion_pips:.1f} pips expected)")

if __name__ == "__main__":
    main()