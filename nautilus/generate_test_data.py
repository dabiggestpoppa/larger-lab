#!/usr/bin/env python3
"""Generate test EURUSD data for backtesting"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create 3 years of M5 data
idx = pd.date_range('2023-01-01', periods=300000, freq='5T')
np.random.seed(42)

# Generate realistic EURUSD price data
base_price = 1.1
prices = [base_price]
for i in range(1, len(idx)):
    change = np.random.randn() * 0.0005
    prices.append(prices[-1] + change)

df = pd.DataFrame({
    'open': prices,
    'high': [p + abs(np.random.randn()) * 0.0003 for p in prices],
    'low': [p - abs(np.random.randn()) * 0.0003 for p in prices],
    'close': prices,
}, index=idx)

# Ensure high >= open, close >= low
df['high'] = df[['open', 'high', 'close']].max(axis=1)
df['low'] = df[['open', 'low', 'close']].min(axis=1)

# Save to parquet
df.to_parquet('data/EURUSD_M5.parquet')
print(f"Created EURUSD_M5.parquet: {len(df)} rows")
print(f"Date range: {df.index[0]} to {df.index[-1]}")