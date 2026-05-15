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

FX_PAIRS = ["EURUSD"]  # Focus on EUR/USD per user request

class HermesAutopilot:
    def __init__(self):
        self.profitable_strategies = []
        self.all_results = []
        self.iteration = 0
        
    def load_data(self, pair: str) -> pd.DataFrame:
        """Load FX data from Downloads or generate test data"""
        from nautilus.data_loader import _parse_csv
        filename = f"{pair}!_M5_202301020000_202605061250.csv"
        filepath = DOWNLOADS_DIR / filename
        if filepath.exists():
            df = _parse_csv(filepath)
            return df
        
        # Generate test data if file not found
        print(f"Generating test data for {pair}...")
        idx = pd.date_range('2023-01-01', periods=50000, freq='5T')
        np.random.seed(42)
        
        base_price = 1.1
        prices = [base_price]
        opens = [base_price]
        
        for i in range(1, len(idx)):
            # Create occasional larger moves to simulate P90 triggers (4.1+ pips = 0.00041)
            if i % 200 == 0:
                change = np.random.randn() * 0.0015  # Larger move for P90
            else:
                change = np.random.randn() * 0.0003
            prices.append(prices[-1] + change)
            opens.append(prices[-2])  # Previous close as open
        
        df = pd.DataFrame({
            'open': opens,
            'high': [p + abs(np.random.randn()) * 0.0005 for p in prices],
            'low': [p - abs(np.random.randn()) * 0.0005 for p in prices],
            'close': prices,
        }, index=idx)
        
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
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
        position_size = 0.1  # 10 micro lots = 0.1 standard lots
        
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
                    pnl += (row['close'] - entry_price) * position_size * direction * 10000
                    position = 0
                    trades += 1
                continue
            
            # P90 detection (activation window 7-15 UTC = 2-11 AM EST)
            if position == 0 and 7 <= hour_utc <= 15 and current_asian_range > 0:
                # P90 thresholds by time window (per CEREBUS manual)
                if 7 <= hour_utc < 9:
                    threshold = 4.1
                elif 9 <= hour_utc < 11:
                    threshold = 4.6
                elif 11 <= hour_utc < 13:
                    threshold = 4.6
                elif 13 <= hour_utc < 15:
                    threshold = 5.9
                elif 15 <= hour_utc < 17:
                    threshold = 6.2
                else:
                    threshold = 0
                    
                body_pips = abs(row['close'] - row['open']) * 10000
                
                if body_pips >= threshold:
                    direction = 1 if row['close'] > row['open'] else -1
                    position = 1
                    entry_price = row['close']
            
            # Exit at -25% pullback (mean reversion)
            elif position > 0 and current_asian_range > 0:
                target_25 = entry_price - direction * current_asian_range * 0.25
                
                if (direction > 0 and row['low'] <= target_25) or \
                   (direction < 0 and row['high'] >= target_25):
                    pnl += (row['close'] - entry_price) * position_size * direction * 10000
                    position = 0
                    trades += 1
        
        total_return = (pnl / 10000) * 100
        return {"strategy": "P90_Base_Strategy", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_symmetry_trap(self, df: pd.DataFrame) -> dict:
        """Symmetry Trap from CEREBUS manual - Enhanced"""
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
        position_size = 0.1  # 10 micro lots
        highest = 0
        lowest = 0
        
        for i in range(100, len(df) - 1):
            row = df.iloc[i]
            hour_utc = row['hour_utc']
            date_str = str(row['date'])
            
            if date_str in asian_ranges:
                current_asian_range = asian_ranges[date_str]['range']
                current_asian_high = asian_ranges[date_str]['high']
                current_asian_low = asian_ranges[date_str]['low']
            
            # Skip Asian session
            if 19 <= hour_utc or hour_utc < 3:
                continue
            
            # Layer 1: Bias Lock (8-17 UTC) - breakout of Asian range
            if not bias_locked and 8 <= hour_utc <= 17 and current_asian_range > 0:
                if row['close'] > current_asian_high:
                    bias_direction = 1
                    bias_locked = True
                elif row['close'] < current_asian_low:
                    bias_direction = -1
                    bias_locked = True
            
            # Layer 2: Atomic Entry - retest of Asian range
            elif bias_locked and position == 0 and current_asian_range > 0:
                if bias_direction > 0 and row['close'] > current_asian_high:
                    position = 1
                    entry_price = row['close']
                    highest = entry_price
                    lowest = entry_price
                elif bias_direction < 0 and row['close'] < current_asian_low:
                    position = 1
                    entry_price = row['close']
                    highest = entry_price
                    lowest = entry_price
            
            # Layer 3: Exit with trailing stop
            elif position > 0 and current_asian_range > 0:
                highest = max(highest, row['high'])
                lowest = min(lowest, row['low'])
                
                # Trailing stop: 20 pips
                if bias_direction > 0 and row['low'] <= highest - 0.0020:
                    pnl += (row['close'] - entry_price) * position_size * 10000
                    position = 0
                    trades += 1
                elif bias_direction < 0 and row['high'] >= lowest + 0.0020:
                    pnl += (entry_price - row['close']) * position_size * 10000
                    position = 0
                    trades += 1
            
            # Hard exit at 17:00 UTC
            if hour_utc >= 17:
                bias_locked = False
                if position > 0:
                    pnl += (row['close'] - entry_price) * position_size * bias_direction * 10000
                    position = 0
                    trades += 1
        
        total_return = (pnl / 10000) * 100
        return {"strategy": "Symmetry_Trap", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_ema_cross(self, df: pd.DataFrame) -> dict:
        """EMA Cross strategy - Enhanced with trailing stop"""
        if df is None or len(df) < 100:
            return None
        
        df = df.copy()
        df['ema_fast'] = df['close'].ewm(span=8).mean()
        df['ema_slow'] = df['close'].ewm(span=21).mean()
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        position_size = 0.1  # 10 micro lots
        direction = 0
        highest = 0
        lowest = 0
        
        for i in range(21, len(df) - 1):
            row = df.iloc[i]
            prev_fast = df.iloc[i-1]['ema_fast']
            prev_slow = df.iloc[i-1]['ema_slow']
            curr_fast = row['ema_fast']
            curr_slow = row['ema_slow']
            
            # Golden cross entry
            if position == 0 and prev_fast <= prev_slow and curr_fast > curr_slow:
                position = 1
                entry_price = row['close']
                direction = 1
                highest = entry_price
                lowest = entry_price
            # Death cross entry (short)
            elif position == 0 and prev_fast >= prev_slow and curr_fast < curr_slow:
                position = 1
                entry_price = row['close']
                direction = -1
                highest = entry_price
                lowest = entry_price
            
            # Manage open position with trailing stop
            elif position > 0:
                highest = max(highest, row['high'])
                lowest = min(lowest, row['low'])
                
                # Trailing stop: 15 pips for long, 15 pips for short
                if direction > 0 and row['low'] <= highest - 0.0015:
                    pnl += (row['close'] - entry_price) * position_size * 10000
                    position = 0
                    trades += 1
                elif direction < 0 and row['high'] >= lowest + 0.0015:
                    pnl += (entry_price - row['close']) * position_size * 10000
                    position = 0
                    trades += 1
                
                # Exit on opposite signal
                elif direction > 0 and prev_fast >= prev_slow and curr_fast < curr_slow:
                    pnl += (row['close'] - entry_price) * position_size * 10000
                    position = 0
                    trades += 1
                elif direction < 0 and prev_fast <= prev_slow and curr_fast > curr_slow:
                    pnl += (entry_price - row['close']) * position_size * 10000
                    position = 0
                    trades += 1
        
        total_return = (pnl / 10000) * 100
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
        position_size = 0.1  # 10 micro lots
        
        for i in range(14, len(df) - 1):
            row = df.iloc[i]
            rsi = row['rsi']
            
            if position == 0 and rsi < 30:
                position = 1
                entry_price = row['close']
            elif position > 0 and rsi > 70:
                pnl += (row['close'] - entry_price) * position_size * 10000
                position = 0
                trades += 1
        
        total_return = (pnl / 10000) * 100
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
        position_size = 0.1  # 10 micro lots
        direction = 0
        
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
            
            # Breakout entry with direction
            if position == 0 and hour_utc >= 8 and hour_utc < 17:
                if row['close'] > asian_high:
                    position = 1
                    entry_price = row['close']
                    direction = 1
                elif row['close'] < asian_low:
                    position = 1
                    entry_price = row['close']
                    direction = -1
            
            # Exit at next bar with direction
            elif position > 0:
                if direction > 0:
                    pnl += (row['close'] - entry_price) * position_size * 10000
                else:
                    pnl += (entry_price - row['close']) * position_size * 10000
                position = 0
                trades += 1
        
        total_return = (pnl / 10000) * 100
        return {"strategy": "Asian_Breakout", "pair": df.attrs.get('pair', 'UNKNOWN'), "trades": trades, "pnl": round(pnl, 2), "return_pct": round(total_return, 2)}
    
    def run_iteration(self):
        """Run one iteration of all strategies"""
        self.iteration += 1
        print(f"\n{'='*60}")
        print(f"🔄 ITERATION {self.iteration} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        strategies = [
            ("P90_Base_Strategy", self.run_p90_strategy),
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
                    if result:
                        self.all_results.append(result)
                        if result['return_pct'] > 0:
                            if result not in self.profitable_strategies:
                                self.profitable_strategies.append(result)
                                print(f"✅ PROFITABLE: {name} on {pair} - {result['return_pct']}%")
                        else:
                            print(f"   {name}: {result['return_pct']}% (trades: {result['trades']}, pnl: {result['pnl']})")
        
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