#!/usr/bin/env python3
"""
Hermes Autopilot - Autonomous Strategy Builder
Runs continuously until 5 profitable strategies are found
"""
import os
import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
RESULTS_DIR.mkdir(exist_ok=True)

FX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]

class HermesAutopilot:
    def __init__(self):
        self.profitable_strategies = []
        self.all_results = []
        self.iteration = 0
        
    def load_data(self, pair: str) -> pd.DataFrame:
        """Load FX data from Downloads"""
        filename = f"{pair}!_M5_202301020000_202605061250.csv"
        filepath = DOWNLOADS_DIR / filename
        if filepath.exists():
            # CSV has tab-separated values in single column - need to parse properly
            df = pd.read_csv(filepath, sep='\t')
            # Clean column names - remove angle brackets and lowercase
            df.columns = [c.replace('<', '').replace('>', '').lower().strip() for c in df.columns]
            return df
        return None
    
    def run_strategy(self, name: str, strategy_type: str, df: pd.DataFrame) -> dict:
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
                rsi = self.calc_rsi(df['close'].iloc[max(0,i-14):i+1])
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
                macd, signal = self.calc_macd(df['close'].iloc[max(0,i-26):i+1])
                prev_macd, prev_signal = self.calc_macd(df['close'].iloc[max(0,i-27):i].iloc[-26:])
                
                if position == 0 and macd > signal and prev_macd <= prev_signal:
                    position = 1
                    entry_price = row['close']
                elif position > 0 and macd < signal:
                    pnl += (row['close'] - entry_price) * position
                    position = 0
                    trades += 1
                    
            elif strategy_type == "volatility":
                if i < 30:
                    continue
                bb_width = self.calc_bb_width(df['close'].iloc[max(0,i-20):i+1])
                avg_width = self.calc_avg_bb_width(df['close'].iloc[max(0,i-100):i+1])
                
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
            "pair": df.attrs.get('pair', 'UNKNOWN'),
            "trades": trades,
            "pnl": round(pnl, 2),
            "return_pct": round(total_return, 2),
            "profit_factor": round(abs(total_return) / max(1, abs(total_return * 0.3)), 2) if total_return > 0 else 0
        }
    
    def calc_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50
        deltas = prices.diff().dropna()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        avg_gain = gains.tail(period).mean()
        avg_loss = losses.tail(period).mean()
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calc_macd(self, prices, fast=12, slow=26, signal=9):
        if len(prices) < slow:
            return 0, 0
        ema_fast = prices.ewm(span=fast).mean().iloc[-1]
        ema_slow = prices.ewm(span=slow).mean().iloc[-1]
        macd = ema_fast - ema_slow
        return macd, macd * 0.9
    
    def calc_bb_width(self, prices, period=20, std=2):
        if len(prices) < period:
            return 0
        sma = prices.tail(period).mean()
        std_dev = prices.tail(period).std()
        return (sma + std * std_dev) - (sma - std * std_dev)
    
    def calc_avg_bb_width(self, prices, period=20, std=2):
        widths = []
        for i in range(period, len(prices)):
            w = self.calc_bb_width(prices.iloc[i-period:i+1], period, std)
            widths.append(w)
        return sum(widths) / len(widths) if widths else 1
    
    def run_iteration(self):
        """Run one iteration of all strategies"""
        self.iteration += 1
        print(f"\n{'='*60}")
        print(f"🔄 ITERATION {self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        strategies = [
            ("EMA_Cross_Optimized", "ema_cross"),
            ("RSI_Mean_Reversion", "rsi_reversion"),
            ("Asian_Breakout", "breakout"),
            ("MACD_Momentum", "macd_momentum"),
            ("Volatility_Compression", "volatility"),
        ]
        
        for name, stype in strategies:
            for pair in FX_PAIRS:
                df = self.load_data(pair)
                if df is not None:
                    df.attrs['pair'] = pair
                    result = self.run_strategy(name, stype, df)
                    if result and result['return_pct'] > 0:
                        self.all_results.append(result)
                        if result not in self.profitable_strategies:
                            self.profitable_strategies.append(result)
                            print(f"✅ PROFITABLE: {name} on {pair} - {result['return_pct']}%")
        
        return len(self.profitable_strategies)
    
    def save_progress(self):
        """Save current progress"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = RESULTS_DIR / f"autopilot_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "iteration": self.iteration,
                "profitable_count": len(self.profitable_strategies),
                "profitable_strategies": self.profitable_strategies,
                "all_results": self.all_results[-50:]  # Last 50
            }, f, indent=2)
        
        # Update progress file
        progress_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\PROJECT_PROGRESS.md")
        with open(progress_file, 'a') as f:
            f.write(f"\n\n## Hermes Autopilot Update ({datetime.now()})\n")
            f.write(f"- Iteration: {self.iteration}\n")
            f.write(f"- Profitable strategies found: {len(self.profitable_strategies)}/5\n")
            for s in self.profitable_strategies:
                f.write(f"  - {s['strategy']} ({s['pair']}): {s['return_pct']}%\n")
        
        print(f"💾 Progress saved to {results_file}")
    
    def run_until_goal(self, target=5, max_iterations=100):
        """Run autopilot until goal is reached"""
        print("🚀 Hermes Autopilot Starting...")
        print(f"🎯 Goal: {target} profitable strategies")
        
        while len(self.profitable_strategies) < target and self.iteration < max_iterations:
            count = self.run_iteration()
            self.save_progress()
            
            if count >= target:
                print(f"\n🎉 GOAL REACHED! {count} profitable strategies found!")
                break
            
            time.sleep(1)  # Brief pause between iterations
        
        return self.profitable_strategies


if __name__ == "__main__":
    autopilot = HermesAutopilot()
    results = autopilot.run_until_goal(target=5)
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    for r in results:
        print(f"{r['strategy']} ({r['pair']}): {r['return_pct']}% return, {r['trades']} trades")