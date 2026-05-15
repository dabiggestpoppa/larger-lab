#!/usr/bin/env python3
"""
Hermes Autopilot - Run until 5 profitable strategies found
"""
import os
import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
RESULTS_DIR.mkdir(exist_ok=True)

FX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]

def load_data(pair: str) -> pd.DataFrame:
    """Load FX data from Downloads"""
    filename = f"{pair}!_M5_202301020000_202605061250.csv"
    filepath = DOWNLOADS_DIR / filename
    if filepath.exists():
        df = pd.read_csv(filepath, sep='\t')
        df.columns = [c.replace('<', '').replace('>', '').lower().strip() for c in df.columns]
        return df
    return None

def run_strategy(name: str, strategy_type: str, df: pd.DataFrame, pair: str = "UNKNOWN") -> dict:
    """Run a single strategy backtest"""
    if df is None or len(df) < 200:
        return None
    
    df = df.copy()
    df['returns'] = df['close'].pct_change()
    
    position = 0
    entry_price = 0
    pnl = 0
    trades = 0
    
    for i in range(50, len(df) - 1):
        row = df.iloc[i]
        
        if strategy_type == "ema_cross":
            ema_fast = df['close'].iloc[max(0,i-8):i].mean()
            ema_slow = df['close'].iloc[max(0,i-21):i].mean()
            
            if position == 0 and ema_fast > ema_slow:
                position = 1
                entry_price = row['close']
            elif position > 0 and ema_fast < ema_slow:
                pnl += (row['close'] - entry_price) * position
                position = 0
                trades += 1
                
        elif strategy_type == "rsi_reversion":
            prices = df['close'].iloc[max(0,i-14):i+1]
            if len(prices) >= 15:
                deltas = prices.diff().dropna()
                gains = deltas.where(deltas > 0, 0)
                losses = -deltas.where(deltas < 0, 0)
                avg_gain = gains.tail(14).mean()
                avg_loss = losses.tail(14).mean()
                rsi = 100 - (100 / (1 + avg_gain / max(avg_loss, 0.0001)))
                
                if position == 0 and rsi < 30:
                    position = 1
                    entry_price = row['close']
                elif position > 0 and rsi > 70:
                    pnl += (row['close'] - entry_price) * position
                    position = 0
                    trades += 1
                    
        elif strategy_type == "breakout":
            if i < 200:
                continue
            asian_high = df['high'].iloc[i-200:i-100].max()
            asian_low = df['low'].iloc[i-200:i-100].min()
            
            if position == 0 and row['close'] > asian_high:
                position = 1
                entry_price = row['close']
            elif position > 0 and row['close'] < asian_low:
                pnl += (row['close'] - entry_price) * position
                position = 0
                trades += 1
                
        elif strategy_type == "macd_momentum":
            if i < 30:
                continue
            prices = df['close'].iloc[max(0,i-26):i+1]
            ema_fast = prices.ewm(span=12).mean().iloc[-1]
            ema_slow = prices.ewm(span=26).mean().iloc[-1]
            macd = ema_fast - ema_slow
            
            prev_prices = df['close'].iloc[max(0,i-27):i].iloc[-26:]
            prev_ema_fast = prev_prices.ewm(span=12).mean().iloc[-1]
            prev_ema_slow = prev_prices.ewm(span=26).mean().iloc[-1]
            prev_macd = prev_ema_fast - prev_ema_slow
            
            if position == 0 and macd > 0 and prev_macd <= 0:
                position = 1
                entry_price = row['close']
            elif position > 0 and macd < 0:
                pnl += (row['close'] - entry_price) * position
                position = 0
                trades += 1
                
        elif strategy_type == "volatility":
            if i < 30:
                continue
            prices = df['close'].iloc[max(0,i-20):i+1]
            sma = prices.mean()
            std = prices.std()
            bb_width = (sma + 2*std) - (sma - 2*std)
            
            # Calculate average width
            widths = []
            for j in range(20, len(df)):
                p = df['close'].iloc[max(0,j-20):j+1]
                if len(p) >= 20:
                    w = (p.mean() + 2*p.std()) - (p.mean() - 2*p.std())
                    widths.append(w)
            avg_width = sum(widths) / len(widths) if widths else 1
            
            if position == 0 and bb_width < avg_width * 0.8:
                position = 1
                entry_price = row['close']
            elif position > 0 and bb_width > avg_width * 1.2:
                pnl += (row['close'] - entry_price) * position
                position = 0
                trades += 1
    
    total_return = (pnl / 100000) * 100
    return {
        "strategy": name,
        "pair": pair,
        "trades": trades,
        "pnl": round(pnl, 2),
        "return_pct": round(total_return, 2),
    }

def main():
    # Log to file instead of stdout
    log_file = open(r'C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results\autopilot_run.log', 'w')
    
    def log(msg):
        log_file.write(msg + '\n')
        log_file.flush()
    
    log("🚀 Hermes Autopilot Starting...")
    log(f"🎯 Goal: 5 profitable strategies")
    
    profitable = []
    all_results = []
    iteration = 0
    
    strategies = [
        ("EMA_Cross_Optimized", "ema_cross"),
        ("RSI_Mean_Reversion", "rsi_reversion"),
        ("Asian_Breakout", "breakout"),
        ("MACD_Momentum", "macd_momentum"),
        ("Volatility_Compression", "volatility"),
    ]
    
    while len(profitable) < 5 and iteration < 20:
        iteration += 1
        log(f"\n{'='*60}")
        log(f"🔄 ITERATION {iteration}")
        log(f"{'='*60}")
        
        for name, stype in strategies:
            for pair in FX_PAIRS[:5]:
                df = load_data(pair)
                if df is not None:
                    result = run_strategy(name, stype, df, pair)
                    if result and result['return_pct'] > 0:
                        all_results.append(result)
                        if result not in profitable:
                            profitable.append(result)
                            log(f"✅ {name} on {pair}: {result['return_pct']}%")
        
        # Save progress
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = RESULTS_DIR / f"autopilot_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({"profitable": profitable, "all": all_results}, f, indent=2)
        
        if len(profitable) >= 5:
            log(f"\n🎉 GOAL REACHED! {len(profitable)} profitable strategies!")
            break
    
    log("\n" + "="*60)
    log("📊 FINAL RESULTS")
    log("="*60)
    for r in profitable:
        log(f"{r['strategy']} ({r['pair']}): {r['return_pct']}% return, {r['trades']} trades")
    
    log_file.close()

if __name__ == "__main__":
    main()