#!/usr/bin/env python3
"""Test P90 strategy logic with synthetic data"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create synthetic EURUSD data with realistic Asian ranges
np.random.seed(42)
idx = pd.date_range('2024-01-01', periods=50000, freq='5T')

# Generate price data with daily patterns
prices = []
for i, ts in enumerate(idx):
    hour = ts.hour
    # Asian session has lower volatility
    if 19 <= hour or hour < 3:
        vol = 0.0002
    else:
        vol = 0.0005
    prices.append(1.1 + np.random.randn() * vol)

df = pd.DataFrame({
    'open': prices,
    'high': [p + abs(np.random.randn()) * 0.0003 for p in prices],
    'low': [p - abs(np.random.randn()) * 0.0003 for p in prices],
    'close': prices,
}, index=idx)
df['high'] = df[['open', 'high', 'close']].max(axis=1)
df['low'] = df[['open', 'low', 'close']].min(axis=1)

# Calculate Asian ranges
df['hour_utc'] = df.index.hour
df['date'] = df.index.date

asian_ranges = {}
for date in df['date'].unique():
    day_data = df[df['date'] == date]
    asian_mask = (day_data['hour_utc'] >= 19) | (day_data['hour_utc'] < 3)
    asian_data = day_data[asian_mask]
    if len(asian_data) > 0:
        asian_ranges[str(date)] = {
            'high': asian_data['high'].max(),
            'low': asian_data['low'].min(),
            'range': asian_data['high'].max() - asian_data['low'].min()
        }

print(f"Asian ranges calculated: {len(asian_ranges)} days")
print(f"Avg range: {np.mean([v['range'] for v in asian_ranges.values()]) * 10000:.1f} pips")

# Test P90 strategy
position = 0
entry_price = 0
pnl = 0
trades = 0
direction = 0
position_size = 0.1  # 10 micro lots

for i in range(100, len(df) - 1):
    row = df.iloc[i]
    hour_utc = row['hour_utc']
    date_str = str(row['date'])
    current_asian_range = asian_ranges.get(date_str, {}).get('range', 0)
    
    # Skip Asian session
    if 19 <= hour_utc or hour_utc < 3:
        continue
    
    # Hard exit at 17:00 UTC
    if hour_utc >= 17:
        if position > 0:
            pnl += (row['close'] - entry_price) * position_size * direction * 10000
            position = 0
            trades += 1
        continue
    
    # P90 entry (7-15 UTC)
    if position == 0 and 7 <= hour_utc <= 15 and current_asian_range > 0:
        threshold = 4.1 if 7 <= hour_utc < 9 else (4.6 if 9 <= hour_utc < 13 else 5.9)
        body_pips = abs(row['close'] - row['open']) * 10000
        
        if body_pips >= threshold:
            direction = 1 if row['close'] > row['open'] else -1
            position = 1
            entry_price = row['close']
    
    # Exit at -25% pullback (FIXED)
    elif position > 0 and current_asian_range > 0:
        target_25 = entry_price - direction * current_asian_range * 0.25
        if (direction > 0 and row['low'] <= target_25) or (direction < 0 and row['high'] >= target_25):
            pnl += (row['close'] - entry_price) * position_size * direction * 10000
            position = 0
            trades += 1

total_return = (pnl / 10000) * 100
print(f"\nP90 Strategy Results:")
print(f"  Trades: {trades}")
print(f"  PnL: {pnl:.2f}")
print(f"  Return: {total_return:.2f}%")