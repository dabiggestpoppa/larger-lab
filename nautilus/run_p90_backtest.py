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

# P90 Thresholds per CEREBUS FX v4.0 manual (pips)
P90_THRESHOLDS = {
    "early": {"time": "2-4 AM EST", "threshold": 4.1},
    "mid": {"time": "4-6 AM EST", "threshold": 4.6},
    "late": {"time": "6-8 AM EST", "threshold": 4.6},
    "cutoff": {"time": "8-10 AM EST", "threshold": 5.9},
}

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
    
    def run_p90_strategy(self, df: pd.DataFrame) -> dict:
        """
        Run P90 CFD Expansion strategy from CEREBUS manual
        Entry: P90 candle (M5 close with body >= threshold)
        Exit: -25% / -50% Asian Range targets
        """
        if df is None or len(df) < 500:
            return {"error": "Insufficient data"}
        
        df = df.copy()
        df['returns'] = df['close'].pct_change()
        df['body'] = abs(df['close'] - df['open'])
        # Timestamp is in the index
        df['hour_utc'] = df.index.hour + df.index.minute / 60
        df['date'] = df.index.date
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        direction = 0
        daily_asian_range = {}  # Cache for daily Asian ranges
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        direction = 0
        
        for i in range(100, len(df) - 1):
            row = df.iloc[i]
            hour_utc = row['hour_utc']
            
            # Skip Asian session
            if 19 <= hour_utc or hour_utc < 3:
                continue
            
            # Skip after 12 PM EST (17:00 UTC)
            if hour_utc >= 17:
                if position > 0:
                    pnl += (row['close'] - entry_price) * position
                    position = 0
                    trades += 1
                continue
            
            # P90 detection (activation window 7-15 UTC = 2-11 AM EST)
            if position == 0 and 7 <= hour_utc <= 15:
                threshold = self._get_p90_threshold(hour_utc)
                body_pips = row['body'] * 10000  # Convert to pips for EUR/USD
                
                if body_pips >= threshold:
                    direction = 1 if row['close'] > row['open'] else -1
                    position = 1
                    entry_price = row['close']
            
            # Exit at targets
            elif position > 0:
                target_25 = entry_price + direction * asian_range * 0.25
                target_50 = entry_price + direction * asian_range * 0.50
                
                if (direction > 0 and row['high'] >= target_25) or \
                   (direction < 0 and row['low'] <= target_25):
                    pnl += (row['close'] - entry_price) * position * direction
                    position = 0
                    trades += 1
        
        total_return = (pnl / 100000) * 100
        return {
            "strategy": "P90_CFD_Expansion",
            "pair": "EUR/USD",
            "trades": trades,
            "pnl": round(pnl, 2),
            "return_pct": round(total_return, 2),
            "asian_range_pips": round(asian_range * 10000, 1)
        }
    
    def run_symmetry_trap(self, df: pd.DataFrame) -> dict:
        """
        Run Symmetry Trap strategy from CEREBUS manual
        Three-Layer Model: Bias Lock → Atomic Entry → Distribution Targets
        """
        if df is None or len(df) < 500:
            return {"error": "Insufficient data"}
        
        df = df.copy()
        # Timestamp is in the index
        df['hour_utc'] = df.index.hour + df.index.minute / 60
        
        # Calculate Asian Range
        asian_mask = (df['hour_utc'] >= 19) | (df['hour_utc'] < 3)
        asian_high = df[asian_mask]['high'].max()
        asian_low = df[asian_mask]['low'].min()
        asian_range = asian_high - asian_low
        
        position = 0
        entry_price = 0
        pnl = 0
        trades = 0
        bias_locked = False
        bias_direction = 0
        
        for i in range(100, len(df) - 1):
            row = df.iloc[i]
            hour_utc = row['hour_utc']
            
            # Layer 1: Bias Lock (8-17 UTC)
            if not bias_locked and 8 <= hour_utc <= 17:
                if row['close'] > asian_high:
                    bias_direction = 1
                    bias_locked = True
                elif row['close'] < asian_low:
                    bias_direction = -1
                    bias_locked = True
            
            # Layer 2: Atomic Entry
            elif bias_locked and position == 0:
                # Look for impulse + pullback
                if bias_direction > 0 and row['close'] > asian_high:
                    position = 1
                    entry_price = row['close']
                elif bias_direction < 0 and row['close'] < asian_low:
                    position = 1
                    entry_price = row['close']
            
            # Layer 3: Exit at targets
            elif position > 0:
                target = entry_price - bias_direction * asian_range * 0.25
                if (bias_direction > 0 and row['low'] <= target) or \
                   (bias_direction < 0 and row['high'] >= target):
                    pnl += (row['close'] - entry_price) * position * bias_direction
                    position = 0
                    trades += 1
            
            # Hard exit at 17:00 UTC
            if hour_utc >= 17 and position > 0:
                pnl += (row['close'] - entry_price) * position * bias_direction
                position = 0
                trades += 1
        
        total_return = (pnl / 100000) * 100
        return {
            "strategy": "Symmetry_Trap",
            "pair": "EUR/USD",
            "trades": trades,
            "pnl": round(pnl, 2),
            "return_pct": round(total_return, 2),
            "asian_range_pips": round(asian_range * 10000, 1)
        }
    
    def _get_p90_threshold(self, hour_utc: float) -> float:
        """Get P90 threshold based on time window"""
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