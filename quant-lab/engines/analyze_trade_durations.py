#!/usr/bin/env python3
"""
Analyze trade durations and exit patterns
"""

import json
import numpy as np
from datetime import datetime

# Load trades from backtest
with open('quant-lab/reports/triangular_trades.json', 'r') as f:
    trades = json.load(f)

print(f"Total trades: {len(trades)}")

# Analyze by exit reason
exit_counts = {}
exit_pnl = {}
for t in trades:
    reason = t['result']
    exit_counts[reason] = exit_counts.get(reason, 0) + 1
    if reason not in exit_pnl:
        exit_pnl[reason] = []
    exit_pnl[reason].append(t['pnl_net_pips'])

print("\n=== EXIT REASONS ===")
for reason, count in sorted(exit_counts.items(), key=lambda x: -x[1]):
    pnls = exit_pnl[reason]
    print(f"  {reason}: {count} ({count/len(trades)*100:.1f}%) | Avg PnL: {np.mean(pnls):.2f} | Median: {np.median(pnls):.2f}")

# Analyze trade duration
print("\n=== TRADE DURATIONS ===")
durations = []
for t in trades:
    entry = datetime.fromisoformat(t['entry_time'])
    exit = datetime.fromisoformat(t['exit_time'])
    duration_min = (exit - entry).total_seconds() / 60
    durations.append(duration_min)

print(f"  Mean: {np.mean(durations):.1f} min")
print(f"  Median: {np.median(durations):.1f} min")
print(f"  Min: {np.min(durations):.1f} min")
print(f"  Max: {np.max(durations):.1f} min")

# Duration by exit reason
for reason in ['TP_HIT', 'SL_HIT', 'TIMEOUT']:
    reason_durations = []
    for t in trades:
        if t['result'] == reason:
            entry = datetime.fromisoformat(t['entry_time'])
            exit = datetime.fromisoformat(t['exit_time'])
            duration_min = (exit - entry).total_seconds() / 60
            reason_durations.append(duration_min)
    if reason_durations:
        print(f"  {reason}: mean={np.mean(reason_durations):.1f}, median={np.median(reason_durations):.1f} min")

# Entry time distribution
print("\n=== ENTRY TIME DISTRIBUTION (EST) ===")
entry_hours = []
for t in trades:
    entry = datetime.fromisoformat(t['entry_time'])
    est_hour = (entry.hour - 5) % 24
    entry_hours.append(est_hour)

for h in range(0, 24):
    count = sum(1 for eh in entry_hours if eh == h)
    if count > 0:
        print(f"  {h:2d}:00 EST: {count} trades")

# PnL by entry hour
print("\n=== PNL BY ENTRY HOUR (EST) ===")
hour_pnl = {}
for t in trades:
    entry = datetime.fromisoformat(t['entry_time'])
    est_hour = (entry.hour - 5) % 24
    if est_hour not in hour_pnl:
        hour_pnl[est_hour] = []
    hour_pnl[est_hour].append(t['pnl_net_pips'])

for h in sorted(hour_pnl.keys()):
    pnls = hour_pnl[h]
    print(f"  {h:2d}:00 EST: {len(pnls)} trades, avg={np.mean(pnls):.2f}, median={np.median(pnls):.2f}")

# Time to mean reversion (half-life = 21.7 bars = 108 min)
print("\n=== TIME TO REVERSION ANALYSIS ===")
half_life_min = 21.7 * 5  # 108.5 minutes
print(f"  Theoretical half-life: {half_life_min:.0f} minutes")

# What % of trades have duration > half-life?
long_enough = sum(1 for d in durations if d > half_life_min)
print(f"  Trades lasting > half-life: {long_enough}/{len(trades)} ({long_enough/len(trades)*100:.1f}%)")

# PnL for trades lasting > half-life
long_pnls = [t['pnl_net_pips'] for t in trades 
             if (datetime.fromisoformat(t['exit_time']) - datetime.fromisoformat(t['entry_time'])).total_seconds()/60 > half_life_min]
short_pnls = [t['pnl_net_pips'] for t in trades 
              if (datetime.fromisoformat(t['exit_time']) - datetime.fromisoformat(t['entry_time'])).total_seconds()/60 <= half_life_min]

print(f"  > Half-life: {len(long_pnls)} trades, avg PnL: {np.mean(long_pnls):.2f}")
print(f"  <= Half-life: {len(short_pnls)} trades, avg PnL: {np.mean(short_pnls):.2f}")

# Session analysis
print("\n=== SESSION ANALYSIS ===")
session_pnl = {'Asian': [], 'London': [], 'NY': []}
for t in trades:
    entry = datetime.fromisoformat(t['entry_time'])
    est_hour = (entry.hour - 5) % 24
    if est_hour >= 19 or est_hour < 3:
        session_pnl['Asian'].append(t['pnl_net_pips'])
    elif 3 <= est_hour < 12:
        session_pnl['London'].append(t['pnl_net_pips'])
    else:
        session_pnl['NY'].append(t['pnl_net_pips'])

for session, pnls in session_pnl.items():
    if pnls:
        print(f"  {session}: {len(pnls)} trades, avg={np.mean(pnls):.2f}, median={np.median(pnls):.2f}, WR={sum(1 for p in pnls if p>0)/len(pnls)*100:.1f}%")

# Z-score at entry
print("\n=== ENTRY Z-SCORE DISTRIBUTION ===")
entry_zs = [abs(t['entry_zscore']) for t in trades]
print(f"  Mean |z| at entry: {np.mean(entry_zs):.2f}")
print(f"  Median |z| at entry: {np.median(entry_zs):.2f}")

# PnL by entry z-score bins
print("\n=== PNL BY ENTRY |Z| BIN ===")
for z_min, z_max in [(2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 10.0)]:
    bin_pnls = [t['pnl_net_pips'] for t in trades if z_min <= abs(t['entry_zscore']) < z_max]
    if bin_pnls:
        print(f"  |z| in [{z_min}, {z_max}): {len(bin_pnls)} trades, avg={np.mean(bin_pnls):.2f}, WR={sum(1 for p in bin_pnls if p>0)/len(bin_pnls)*100:.1f}%")