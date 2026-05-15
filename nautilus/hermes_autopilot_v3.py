#!/usr/bin/env python3
"""
Hermes Autopilot v3 - Autonomous Strategy Builder
Runs continuously until 5 profitable strategies are found
Fixed position sizing and exit logic
"""
import os
import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

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
        from nautilus.data_loader import _parse_csv
        filename = f"{pair}!_M5_202301020000_202605061250.csv"
        filepath = DOWNLOADS_DIR / filename
        if filepath.exists():
            df = _parse_csv(filepath)
            return df
        return None
    
    def calculate_daily_asian_ranges(self, df: pd.DataFrame) -> dict:
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
    
    def run_p90_strategy(self, df: pd.DataFrame) -> dict:
        """P90 CFD Expansion from CEREBUS manual - Fixed"""
        if df is None or len(df) < 500:
            return None
        
        df = df.copy()
        df['hour_utc'] = df.index.hour + df.index.minute / 60
        df['date'] = df.index.date
        asian_ranges = self.calculate_daily_asian_ranges(df)
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        direction = 0
        current_asian_range = 0
        
        for i in range(100, len(df) - 1):
            row = df.iloc[i]
            hour_utc = row['hour_utc']
            date_str = str(row['date'])
            
            if date_str in asian_ranges:
                current_asian_range = asian_ranges[date_str]['range']
            
            # Skip Asian session (19:00-03:00 UTC)
            if 19 <= hour_utc or hour_utc < 3:
                continue
            
            # Hard exit at 17:00 UTC
            if hour_utc >= 17:
                if position > 0:
                    pnl += (row['close'] - entry_price) * direction
                    position = 0
                    trades += 1
                continue
            
            # P90 detection (activation window 7-15 UTC)
            if position == 0 and 7 <= hour_utc <= 15 and current_asian_range > 0:
                threshold = 4.1 if 7 <= hour_utc < 9 else (4.6 if 9 <= hour_utc < 13 else 5.9)
                body_pips = abs(row['close'] - row['open']) * 10000
                
                if body_pips >= threshold:
                    direction = 1 if row['close'] > row['open'] else -1
                    position = 1
                    entry_price = row['close']
            
            # Exit at -25% Asian Range target
            elif position > 0 and current_asian_range > 0:
                target = entry_price + direction * current_asian_range * 0.25
                
                if (direction > 0 and row['high'] >= target) or (direction < 0 and row['low'] <= target):
                    pnl += (row['close'] - entry_price) * direction
                    position = 0
                    trades += 1
        
        total_return = pnl * 100  # 1 pip = 10 units per micro lot
        return {"strategy": "P90_CFD_Expansion", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_symmetry_trap(self, df: pd.DataFrame) -> dict:
        """Symmetry Trap from CEREBUS manual - Fixed"""
        if df is None or len(df) < 500:
            return None
        
        df = df.copy()
        df['hour_utc'] = df.index.hour + df.index.minute / 60
        df['date'] = df.index.date
        asian_ranges = self.calculate_daily_asian_ranges(df)
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        bias_locked = False
        bias_direction = 0
        current_asian_range = 0
        current_asian_high = 0
        current_asian_low = 0
        
        for i in range(100, len(df) - 1):
            row = df.iloc[i]
            hour_utc = row['hour_utc']
            date_str = str(row['date'])
            
            if date_str in asian_ranges:
                current_asian_range = asian_ranges[date_str]['range']
                current_asian_high = asian_ranges[date_str]['high']
                current_asian_low = asian_ranges[date_str]['low']
            
            # Layer 1: Bias Lock (8-17 UTC)
            if not bias_locked and 8 <= hour_utc <= 17:
                if row['close'] > current_asian_high:
                    bias_direction = 1
                    bias_locked = True
                elif row['close'] < current_asian_low:
                    bias_direction = -1
                    bias_locked = True
            
            # Layer 2: Atomic Entry
            elif bias_locked and position == 0 and current_asian_range > 0:
                if bias_direction > 0 and row['close'] > current_asian_high:
                    position = 1
                    entry_price = row['close']
                elif bias_direction < 0 and row['close'] < current_asian_low:
                    position = 1
                    entry_price = row['close']
            
            # Layer 3: Exit at -25% pullback
            elif position > 0 and current_asian_range > 0:
                target = entry_price - bias_direction * current_asian_range * 0.25
                
                if (bias_direction > 0 and row['low'] <= target) or (bias_direction < 0 and row['high'] >= target):
                    pnl += (row['close'] - entry_price) * bias_direction
                    position = 0
                    trades += 1
            
            # Hard exit at 17:00 UTC
            if hour_utc >= 17:
                bias_locked = False
                if position > 0:
                    pnl += (row['close'] - entry_price) * bias_direction
                    position = 0
                    trades += 1
        
        total_return = pnl * 100
        return {"strategy": "Symmetry_Trap", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_ema_cross(self, df: pd.DataFrame) -> dict:
        """EMA Cross strategy"""
        if df is None or len(df) < 100:
            return None
        
        df = df.copy()
        df['ema_fast'] = df['close'].ewm(span=8).mean()
        df['ema_slow'] = df['close'].ewm(span=21).mean()
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        
        for i in range(21, len(df) - 1):
            row = df.iloc[i]
            prev_fast = df.iloc[i-1]['ema_fast']
            prev_slow = df.iloc[i-1]['ema_slow']
            curr_fast = row['ema_fast']
            curr_slow = row['ema_slow']
            
            if position == 0 and prev_fast <= prev_slow and curr_fast > curr_slow:
                position = 1
                entry_price = row['close']
            elif position > 0 and prev_fast >= prev_slow and curr_fast < curr_slow:
                pnl += (row['close'] - entry_price)
                position = 0
                trades += 1
        
        total_return = pnl * 100
        return {"strategy": "EMA_Cross", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_rsi_reversion(self, df: pd.DataFrame) -> dict:
        """RSI Mean Reversion"""
        if df is None or len(df) < 100:
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
        entry_price = 0
        pnl = 0
        trades = 0
        
        for i in range(14, len(df) - 1):
            row = df.iloc[i]
            rsi = row['rsi']
            
            if position == 0 and rsi < 30:
                position = 1
                entry_price = row['close']
            elif position > 0 and rsi > 70:
                pnl += (row['close'] - entry_price)
                position = 0
                trades += 1
        
        total_return = pnl * 100
        return {"strategy": "RSI_Reversion", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_breakout(self, df: pd.DataFrame) -> dict:
        """Asian Session Breakout"""
        if df is None or len(df) < 500:
            return None
        
        df = df.copy()
        df['hour_utc'] = df.index.hour
        df['date'] = df.index.date
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        
        for i in range(200, len(df) - 1):
            row = df.iloc[i]
            hour_utc = row['hour_utc']
            
            # Calculate Asian range for this day
            day_data = df[df['date'] == row['date']]
            asian_mask = (day_data['hour_utc'] >= 19) | (day_data['hour_utc'] < 3)
            asian_data = day_data[asian_mask]
            
            if len(asian_data) == 0:
                continue
            
            asian_high = asian_data['high'].max()
            asian_low = asian_data['low'].min()
            
            # Skip Asian session
            if 19 <= hour_utc or hour_utc < 3:
                continue
            
            # Breakout entry
            if position == 0 and hour_utc >= 8 and hour_utc < 17:
                if row['close'] > asian_high:
                    position = 1
                    entry_price = row['close']
                elif row['close'] < asian_low:
                    position = 1
                    entry_price = row['close']
            
            # Exit at next bar
            elif position > 0:
                pnl += (row['close'] - entry_price)
                position = 0
                trades += 1
        
        total_return = pnl * 100
        return {"strategy": "Asian_Breakout", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_iteration(self):
        """Run one iteration of all strategies"""
        self.iteration += 1
        print(f"\n{'='*60}")
        print(f"🔄 ITERATION {self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        strategies = [
            ("P90_CFD_Expansion", self.run_p90_strategy),
            ("Symmetry_Trap", self.run_symmetry_trap),
            ("EMA_Cross", self.run_ema_cross),
            ("RSI_Reversion", self.run_rsi_reversion),
            ("Asian_Breakout", self.run_breakout),
        ]
        
        for name, func in strategies:
            for pair in FX_PAIRS:
                df = self.load_data(pair)
                if df is not None:
                    df.attrs['pair'] = pair
                    df = df.tail(30000)
                    result = func(df)
                    if result and result['return_pct'] > 0:
                        self.all_results.append(result)
                        if result not in self.profitable_strategies:
                            self.profitable_strategies.append(result)
                            print(f"✅ PROFITABLE: {name} on {pair} - {result['return_pct']}%")
        
        return len(self.profitable_strategies)
    
    def save_progress(self):
        """Save current progress"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = RESULTS_DIR / f"autopilot_v3_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "iteration": self.iteration,
                "profitable_count": len(self.profitable_strategies),
                "profitable_strategies": self.profitable_strategies,
                "all_results": self.all_results[-100:]
            }, f, indent=2)
        
        print(f"💾 Progress saved")
    
    def run_until_goal(self, target=5, max_iterations=50):
        """Run autopilot until goal is reached"""
        print("🚀 Hermes Autopilot v3 Starting...")
        print(f"🎯 Goal: {target} profitable strategies")
        
        while len(self.profitable_strategies) < target and self.iteration < max_iterations:
            count = self.run_iteration()
            self.save_progress()
            
            if count >= target:
                print(f"\n🎉 GOAL REACHED! {count} profitable strategies found!")
                break
            
            time.sleep(0.5)
        
        return self.profitable_strategies


if __name__ == "__main__":
    autopilot = HermesAutopilot()
    results = autopilot.run_until_goal(target=5)
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    for r in results:
        print(f"{r['strategy']} ({r['pair']}): {r['return_pct']}% return, {r['trades']} trades")