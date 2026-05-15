#!/usr/bin/env python3
"""
Hermes Simple - Run strategies and save results
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")

def main():
    results = []
    
    # Load EURUSD data
    from nautilus.data_loader import _parse_csv
    filepath = DOWNLOADS_DIR / "EURUSD!_M5_202301020000_202605061250.csv"
    df = _parse_csv(filepath)
    df = df.tail(20000)
    
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
    
    # P90 Strategy
    position = 0
    entry_price = 0
    pnl = 0
    trades = 0
    direction = 0
    
    for i in range(100, len(df) - 1):
        row = df.iloc[i]
        hour_utc = row['hour_utc']
        date_str = str(row['date'])
        current_asian_range = asian_ranges.get(date_str, {}).get('range', 0)
        
        if 19 <= hour_utc or hour_utc < 3:
            continue
        
        if hour_utc >= 17:
            if position > 0:
                pnl += (row['close'] - entry_price) * direction * 10
                position = 0
                trades += 1
            continue
        
        if position == 0 and 7 <= hour_utc <= 15 and current_asian_range > 0:
            threshold = 4.1 if 7 <= hour_utc < 9 else (4.6 if 9 <= hour_utc < 13 else 5.9)
            body_pips = abs(row['close'] - row['open']) * 10000
            
            if body_pips >= threshold:
                direction = 1 if row['close'] > row['open'] else -1
                position = 1
                entry_price = row['close']
        
        elif position > 0 and current_asian_range > 0:
            target = entry_price + direction * current_asian_range * 0.25
            if (direction > 0 and row['high'] >= target) or (direction < 0 and row['low'] <= target):
                pnl += (row['close'] - entry_price) * direction * 10
                position = 0
                trades += 1
    
    results.append({
        "strategy": "P90_CFD_Expansion",
        "pair": "EUR/USD",
        "trades": trades,
        "pnl": round(pnl, 2),
        "return_pct": round(pnl * 100, 2)
    })
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(RESULTS_DIR / f"hermes_simple_{timestamp}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"P90: {trades} trades, {pnl * 100:.2f}% return")

if __name__ == "__main__":
    main()