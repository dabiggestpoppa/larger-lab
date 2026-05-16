#!/usr/bin/env python3
"""
P90 Backtest Runner - CEREBUS FX v4.0 Manual Strategies
Runs CFD Expansion (P90) and Symmetry Trap strategies for EUR/USD
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
RESULTS_DIR.mkdir(exist_ok=True)

class P90Backtester:
    def __init__(self):
        self.results = []
        
    def load_eurusd_data(self) -> pd.DataFrame:
        """Load EUR/USD M5 data using existing data_loader"""
        from nautilus.data_loader import _parse_csv
        filepath = DOWNLOADS_DIR / "EURUSD!_M5_202301020000_202605061250.csv"
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
        """
        Run P90 CFD Expansion strategy from CEREBUS manual
        Entry: P90 candle (M5 close with body >= threshold)
        Exit: Pullback to -25% of Asian Range (mean reversion)
        """
        if df is None or len(df) < 500:
            return {"error": "Insufficient data"}
        
        df = df.copy()
        df['hour_utc'] = df.index.hour + df.index.minute / 60
        df['date'] = df.index.date
        
        # Calculate daily Asian ranges
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
            
            # Get today's Asian range
            if date_str in asian_ranges:
                current_asian_range = asian_ranges[date_str]['range']
            
            # Skip Asian session (19:00-03:00 UTC)
            if 19 <= hour_utc or hour_utc < 3:
                continue
            
            # Hard exit at 12 PM EST (17:00 UTC)
            if hour_utc >= 17:
                if position > 0:
                    pnl += (row['close'] - entry_price) * position_size * direction * 10000
                    position = 0
                    trades += 1
                continue
            
            # P90 detection (activation window 7-15 UTC = 2-11 AM EST)
            if position == 0 and 7 <= hour_utc <= 15 and current_asian_range > 0:
                threshold = self._get_p90_threshold(hour_utc)
                body_pips = abs(row['close'] - row['open']) * 10000  # Convert to pips
                
                if body_pips >= threshold:
                    direction = 1 if row['close'] > row['open'] else -1
                    position = 1
                    entry_price = row['close']
            
            # Exit at -25% pullback target (mean reversion)
            elif position > 0 and current_asian_range > 0:
                # Target is in OPPOSITE direction (pullback to -25% of range)
                target_25 = entry_price - direction * current_asian_range * 0.25
                
                if (direction > 0 and row['low'] <= target_25) or \
                   (direction < 0 and row['high'] >= target_25):
                    pnl += (row['close'] - entry_price) * position_size * direction * 10000
                    position = 0
                    trades += 1
        
        total_return = (pnl / 10000) * 100  # 10 micro lots = 10000 units
        avg_asian_range = np.mean([v['range'] for v in asian_ranges.values()]) * 10000 if asian_ranges else 0
        return {
            "strategy": "P90_CFD_Expansion",
            "pair": "EUR/USD",
            "trades": trades,
            "pnl": round(pnl, 2),
            "return_pct": round(total_return, 2),
            "asian_range_pips": round(avg_asian_range, 1)
        }
    
    def run_symmetry_trap(self, df: pd.DataFrame) -> dict:
        """
        Run Symmetry Trap strategy from CEREBUS manual
        Three-Layer Model: Bias Lock → Atomic Entry → Distribution Targets
        """
        if df is None or len(df) < 500:
            return {"error": "Insufficient data"}
        
        df = df.copy()
        df['hour_utc'] = df.index.hour + df.index.minute / 60
        df['date'] = df.index.date
        
        # Calculate daily Asian ranges
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
        position_size = 0.1  # 10 micro lots = 0.1 standard lots
        
        for i in range(100, len(df) - 1):
            row = df.iloc[i]
            hour_utc = row['hour_utc']
            date_str = str(row['date'])
            
            # Get today's Asian range
            if date_str in asian_ranges:
                current_asian_range = asian_ranges[date_str]['range']
                current_asian_high = asian_ranges[date_str]['high']
                current_asian_low = asian_ranges[date_str]['low']
            
            # Layer 1: Bias Lock (8-17 UTC) - first M5 close outside Asian band
            if not bias_locked and 8 <= hour_utc <= 17:
                if row['close'] > current_asian_high:
                    bias_direction = 1
                    bias_locked = True
                elif row['close'] < current_asian_low:
                    bias_direction = -1
                    bias_locked = True
            
            # Layer 2: Atomic Entry (impulse + pullback)
            elif bias_locked and position == 0 and current_asian_range > 0:
                # Look for impulse in bias direction
                if bias_direction > 0 and row['close'] > current_asian_high:
                    position = 1
                    entry_price = row['close']
                elif bias_direction < 0 and row['close'] < current_asian_low:
                    position = 1
                    entry_price = row['close']
            
            # Layer 3: Exit at targets (pullback to -25% range)
            elif position > 0 and current_asian_range > 0:
                # Target is in OPPOSITE direction (pullback to -25% range)
                target_25 = entry_price - bias_direction * current_asian_range * 0.25
                
                if (bias_direction > 0 and row['low'] <= target_25) or \
                   (bias_direction < 0 and row['high'] >= target_25):
                    pnl += (row['close'] - entry_price) * position_size * bias_direction * 10000
                    position = 0
                    trades += 1
            
            # Hard exit at 17:00 UTC
            if hour_utc >= 17:
                bias_locked = False
                if position > 0:
                    pnl += (row['close'] - entry_price) * position_size * bias_direction * 10000
                    position = 0
                    trades += 1
        
        total_return = (pnl / 10000) * 100  # 10 micro lots = 10000 units
        avg_asian_range = np.mean([v['range'] for v in asian_ranges.values()]) * 10000 if asian_ranges else 0
        return {
            "strategy": "Symmetry_Trap",
            "pair": "EUR/USD",
            "trades": trades,
            "pnl": round(pnl, 2),
            "return_pct": round(total_return, 2),
            "asian_range_pips": round(avg_asian_range, 1)
        }
    
    def _get_p90_threshold(self, hour_utc: float) -> float:
        """Get P90 threshold based on time window (per CEREBUS manual)"""
        if 7 <= hour_utc < 9:
            return 4.1
        elif 9 <= hour_utc < 11:
            return 4.6
        elif 11 <= hour_utc < 13:
            return 4.6
        elif 13 <= hour_utc < 15:
            return 5.9
        return 6.2
    
    def run_all_manual_strategies(self):
        """Run all CEREBUS manual strategies"""
        print("🚀 Running CEREBUS Manual Strategies for EUR/USD")
        print("=" * 60)
        
        df = self.load_eurusd_data()
        if df is None:
            print("❌ No EUR/USD data found")
            return []
        
        # Limit to recent 50k bars for faster processing
        df = df.tail(50000)
        print(f"📊 Loaded {len(df)} bars of EUR/USD M5 data (recent 50k)")
        
        # Run P90 CFD Expansion
        print("\n📈 Running P90 CFD Expansion...")
        p90_result = self.run_p90_strategy(df)
        self.results.append(p90_result)
        print(f"   Return: {p90_result['return_pct']}% | Trades: {p90_result['trades']}")
        
        # Run Symmetry Trap
        print("\n📈 Running Symmetry Trap...")
        sym_result = self.run_symmetry_trap(df)
        self.results.append(sym_result)
        print(f"   Return: {sym_result['return_pct']}% | Trades: {sym_result['trades']}")
        
        return self.results
    
    def save_results(self):
        """Save results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = RESULTS_DIR / f"p90_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Update progress
        progress_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\PROJECT_PROGRESS.md")
        with open(progress_file, 'a') as f:
            f.write(f"\n\n## P90 Manual Strategies Results ({datetime.now()})\n")
            for r in self.results:
                f.write(f"- {r['strategy']}: {r['return_pct']}% return, {r['trades']} trades\n")
        
        print(f"\n💾 Results saved to {results_file}")


if __name__ == "__main__":
    backtester = P90Backtester()
    results = backtester.run_all_manual_strategies()
    backtester.save_results()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    for r in results:
        status = "✅ PROFITABLE" if r['return_pct'] > 0 else "❌ LOSS"
        print(f"{r['strategy']}: {r['return_pct']}% {status}")