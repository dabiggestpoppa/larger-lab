#!/usr/bin/env python3
"""
Quick Backtest - Fast strategy testing for Hermes autopilot
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
RESULTS_DIR.mkdir(exist_ok=True)

FX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]

def load_data(pair):
    """Load FX data"""
    filename = f"{pair}!_M5_202301020000_202605061250.csv"
    filepath = DOWNLOADS_DIR / filename
    if filepath.exists():
        df = pd.read_csv(filepath, sep='\t')
        df.columns = [c.replace('<', '').replace('>', '').lower().strip() for c in df.columns]
        return df
    return None

def test_ema_cross(df):
    """EMA Cross strategy"""
    if df is None or len(df) < 100:
        return None
    df = df.copy()
    df['ema_fast'] = df['close'].rolling(8).mean()
    df['ema_slow'] = df['close'].rolling(21).mean()
    
    position = 0
    pnl = 0
    trades = 0
    
    for i in range(21, len(df)):
        if position == 0 and df['ema_fast'].iloc[i] > df['ema_slow'].iloc[i]:
            position = 1
            entry = df['close'].iloc[i]
        elif position > 0 and df['ema_fast'].iloc[i] < df['ema_slow'].iloc[i]:
            pnl += df['close'].iloc[i] - entry
            position = 0
            trades += 1
    
    return {"return_pct": round((pnl / 100000) * 100, 2), "trades": trades}

def test_rsi(df):
    """RSI Mean Reversion"""
    if df is None or len(df) < 50:
        return None
    df = df.copy()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    position = 0
    pnl = 0
    trades = 0
    
    for i in range(14, len(df)):
        if position == 0 and df['rsi'].iloc[i] < 30:
            position = 1
            entry = df['close'].iloc[i]
        elif position > 0 and df['rsi'].iloc[i] > 70:
            pnl += df['close'].iloc[i] - entry
            position = 0
            trades += 1
    
    return {"return_pct": round((pnl / 100000) * 100, 2), "trades": trades}

def test_breakout(df):
    """Asian Breakout"""
    if df is None or len(df) < 300:
        return None
    df = df.copy()
    
    position = 0
    pnl = 0
    trades = 0
    
    for i in range(200, len(df)):
        asian_high = df['high'].iloc[i-200:i-100].max()
        asian_low = df['low'].iloc[i-200:i-100].min()
        
        if position == 0 and df['close'].iloc[i] > asian_high:
            position = 1
            entry = df['close'].iloc[i]
        elif position > 0 and df['close'].iloc[i] < asian_low:
            pnl += df['close'].iloc[i] - entry
            position = 0
            trades += 1
    
    return {"return_pct": round((pnl / 100000) * 100, 2), "trades": trades}

def main():
    print("🚀 Hermes Autopilot - Quick Backtest")
    print("="*50)
    
    results = []
    
    for pair in FX_PAIRS:
        df = load_data(pair)
        if df is None:
            print(f"❌ No data for {pair}")
            continue
        
        print(f"\n📊 Testing {pair}...")
        
        # Test each strategy
        for name, func in [("EMA_Cross", test_ema_cross), ("RSI_Reversion", test_rsi), ("Breakout", test_breakout)]:
            result = func(df)
            if result and result['return_pct'] > 0:
                result['strategy'] = name
                result['pair'] = pair
                results.append(result)
                print(f"  ✅ {name}: {result['return_pct']}% ({result['trades']} trades)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(RESULTS_DIR / f"results_{timestamp}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"📈 Found {len(results)} profitable results")
    for r in results:
        print(f"  {r['strategy']} ({r['pair']}): {r['return_pct']}%")

if __name__ == "__main__":
    main()