#!/usr/bin/env python3
"""
Run P90 backtest with generated test data
Creates synthetic EUR/USD data if real data is not available
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Generate realistic EUR/USD test data
np.random.seed(42)

# Create 3 years of M5 data (about 315,000 bars)
idx = pd.date_range('2023-01-01', periods=315000, freq='5T')

# Generate price data with daily patterns
prices = [1.0800]  # Starting price
for i in range(1, len(idx)):
    ts = idx[i]
    hour = ts.hour
    
    # Asian session has lower volatility
    if 19 <= hour or hour < 3:
        vol = 0.0001
    else:
        vol = 0.0003
    
    # Add some trend
    trend = 0.000001 * np.sin(i / 10000)
    change = np.random.randn() * vol + trend
    prices.append(prices[-1] + change)

df = pd.DataFrame({
    'open': prices,
    'high': [p + abs(np.random.randn()) * 0.0002 for p in prices],
    'low': [p - abs(np.random.randn()) * 0.0002 for p in prices],
    'close': prices,
}, index=idx)

# Ensure high >= open, close >= low
df['high'] = df[['open', 'high', 'close']].max(axis=1)
df['low'] = df[['open', 'low', 'close']].min(axis=1)

# Save to parquet for faster loading
df.to_parquet('data/EURUSD_M5_test.parquet')
print(f"Created test data: {len(df)} rows")
print(f"Date range: {df.index[0]} to {df.index[-1]}")

# Now run the P90 strategy
df['hour_utc'] = df.index.hour + df.index.minute / 60
df['date'] = df.index.date

# Calculate Asian ranges
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

print(f"Asian ranges: {len(asian_ranges)} days")
print(f"Avg range: {np.mean([v['range'] for v in asian_ranges.values()]) * 10000:.1f} pips")

# Run P90 strategy
position = 0
entry_price = 0
pnl = 0
trades = 0
direction = 0
position_size = 0.1

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