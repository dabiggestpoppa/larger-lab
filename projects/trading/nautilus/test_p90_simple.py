#!/usr/bin/env python3
"""
Simple P90 test with synthetic data to verify logic
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_test_data(days=30):
    """Generate synthetic EUR/USD M5 data"""
    data = []
    base_price = 1.1000
    start = datetime(2024, 1, 1, 0, 0)
    
    for i in range(days * 24 * 12):  # 5-min bars
        ts = start + timedelta(minutes=5*i)
        # Random walk with drift
        base_price += np.random.normal(0, 0.0002)
        high = base_price + abs(np.random.normal(0, 0.0001))
        low = base_price - abs(np.random.normal(0, 0.0001))
        open_price = base_price + np.random.normal(0, 0.00005)
        close = base_price + np.random.normal(0, 0.00005)
        
        data.append({
            'timestamp': ts,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def calculate_daily_asian_ranges(df):
    """Calculate Asian Range (19:00-03:00 UTC) for each day"""
    df = df.copy()
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
    return asian_ranges

def run_p90_strategy(df):
    """P90 CFD Expansion - Fixed logic"""
    df = df.copy()
    df['hour_utc'] = df.index.hour + df.index.minute / 60
    df['date'] = df.index.date
    asian_ranges = calculate_daily_asian_ranges(df)
    
    position = 0
    entry_price = 0
    pnl = 0
    trades = 0
    direction = 0
    current_asian_range = 0
    position_size = 0.1  # 10 micro lots
    
    for i in range(100, len(df) - 1):
        row = df.iloc[i]
        hour_utc = row['hour_utc']
        date_str = str(row['date'])
        
        if date_str in asian_ranges:
            current_asian_range = asian_ranges[date_str]['range']
        
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
        
        # P90 detection (7-15 UTC)
        if position == 0 and 7 <= hour_utc <= 15 and current_asian_range > 0:
            threshold = 4.1 if 7 <= hour_utc < 9 else (4.6 if 9 <= hour_utc < 13 else 5.9)
            body_pips = abs(row['close'] - row['open']) * 10000
            
            if body_pips >= threshold:
                direction = 1 if row['close'] > row['open'] else -1
                position = 1
                entry_price = row['close']
        
        # Exit at -25% pullback (mean reversion)
        elif position > 0 and current_asian_range > 0:
            target = entry_price - direction * current_asian_range * 0.25
            
            if (direction > 0 and row['low'] <= target) or (direction < 0 and row['high'] >= target):
                pnl += (row['close'] - entry_price) * position_size * direction * 10000
                position = 0
                trades += 1
    
    total_return = (pnl / 10000) * 100
    return {"trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}

if __name__ == "__main__":
    import sys
    
    # Write output to file
    with open("test_output.txt", "w") as f:
        f.write("Testing P90 strategy with synthetic data...\n")
        df = generate_test_data(days=60)
        f.write(f"Generated {len(df)} bars\n")
        
        result = run_p90_strategy(df)
        f.write(f"Result: {result}\n")
        
        # Test with real data if available
        try:
            from nautilus.data_loader import _parse_csv
            from pathlib import Path
            filepath = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
            if filepath.exists():
                df_real = _parse_csv(filepath)
                if df_real is not None:
                    f.write(f"\nReal data: {len(df_real)} bars\n")
                    result_real = run_p90_strategy(df_real.tail(50000))
                    f.write(f"Real result: {result_real}\n")
        except Exception as e:
            f.write(f"Could not load real data: {e}\n")