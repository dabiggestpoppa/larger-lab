"""
Directional bias backtest v2 — efficient single-pass per asset.
Instead of calling evaluate() for each day, we walk through the data once
and track the bias state at each bar.
"""
import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "quant-lab/ml")

from pathlib import Path
import pandas as pd
from directional_bias import DirectionalBias

DATA_DIR = Path("quant-lab/data")
RESULTS_DIR = Path("quant-lab/ml/dtb_lab")

ASSET_FILES = {
    "EURUSD": "EURUSD_M5.csv",
    "GBPUSD": "GBPUSD_M5_fetched.csv",
    "USDCHF": "USDCHF_M5.csv",
    "USDJPY": "USDJPY_M5.csv",
    "AUDUSD": "AUDUSD_M5.csv",
    "NZDUSD": "NZDUSD_M5.csv",
    "USDCAD": "USDCAD_PRO_M5.csv",
    "EURGBP": "EURGBP_PRO_M5.csv",
    "EURCHF": "EURCHF_PRO_M5.csv",
    "EURJPY": "EURJPY_PRO_M5.csv",
    "GBPCHF": "GBPCHF_M5.csv",
    "GBPJPY": "GBPJPY_M5.csv",
    "XAUUSD": "XAUUSD_M5.csv",
    "XAGUSD": "XAGUSD_M5.csv",
    "US500": "US500_M5.csv",
    "DE30": "DE30_M5.csv",
    "FR40": "FR40_M5.csv",
    "BTCUSD": "BTCUSD_M5.csv",
}

engine = DirectionalBias()
all_results = []

for symbol, filename in ASSET_FILES.items():
    filepath = DATA_DIR / filename
    if not filepath.exists():
        continue
    
    try:
        df = pd.read_csv(filepath)
        
        if 'timestamp' in df.columns:
            df['dt'] = pd.to_datetime(df['timestamp'])
        elif 'time' in df.columns:
            df['dt'] = pd.to_datetime(df['time'])
        else:
            continue
        
        df = df.set_index('dt').sort_index()
        
        if len(df) < 100:
            continue
        
        # Add est_hour for daily grouping
        df['est_hour'] = (df.index.hour - 5) % 24
        df['date'] = df.index.date
        
        # Group by date, evaluate once per day using the last bar of each day
        daily_groups = df.groupby('date')
        dates = sorted(daily_groups.groups.keys())
        
        signal_days = 0
        correct = 0
        lock_correct = 0
        lock_total = 0
        state_counts = {}
        
        prev_result = None
        
        for date in dates:
            day_bars = daily_groups.get_group(date)
            if len(day_bars) < 5:
                continue
            
            # Get all bars up to end of this day
            end_of_day = day_bars.index[-1]
            subset = df.loc[:end_of_day]
            
            if len(subset) < 50:
                continue
            
            # Only re-evaluate if we have new bars since last evaluation
            if prev_result is None or len(subset) != prev_result[1]:
                result = engine.evaluate(subset, symbol)
                prev_result = (result, len(subset))
            else:
                result = prev_result[0]
            
            s = result.state.value
            state_counts[s] = state_counts.get(s, 0) + 1
            
            if s in ["9/9_LOCK", "EXHAUSTION"]:
                signal_days += 1
                # Check next bar direction
                next_idx = df.index.get_loc(end_of_day) + 1
                if next_idx < len(df):
                    next_close = df.iloc[next_idx]['close']
                    curr_close = day_bars.iloc[-1]['close']
                    actual = "LONG" if next_close > curr_close else "SHORT"
                    if result.direction.value == actual:
                        correct += 1
                    
                    if s == "9/9_LOCK":
                        lock_total += 1
                        if result.direction.value == actual:
                            lock_correct += 1
        
        accuracy = (correct / signal_days * 100) if signal_days > 0 else 0
        lock_acc = (lock_correct / lock_total * 100) if lock_total > 0 else 0
        
        print("%-8s: %4d days, %3d signals, acc=%5.1f%%, lock=%5.1f%% (%d), states=%s" % (
            symbol, len(dates), signal_days, accuracy, lock_acc, lock_total, state_counts))
        
        all_results.append({
            "symbol": symbol,
            "days": len(dates),
            "signal_days": signal_days,
            "accuracy": round(accuracy, 1),
            "lock_accuracy": round(lock_acc, 1),
            "lock_total": lock_total,
            "states": str(state_counts),
        })
        
    except Exception as e:
        print("ERROR %s: %s" % (symbol, e))

print("\n" + "="*80)
print("DIRECTIONAL BIAS BACKTEST — ALL ASSETS (sorted by 9/9_LOCK accuracy)")
print("="*80)
results_df = pd.DataFrame(all_results)
if len(results_df) > 0:
    results_df = results_df.sort_values("lock_accuracy", ascending=False)
    for _, row in results_df.iterrows():
        print("%-8s: overall=%5.1f%%  lock=%5.1f%% (%d/%d)  days=%d  %s" % (
            row['symbol'], row['accuracy'], row['lock_accuracy'],
            row['lock_total'], row['signal_days'], row['days'], row.get('states', '')))
    results_df.to_csv(RESULTS_DIR / "directional_bias_backtest_v2.csv", index=False)
    print("\nSaved to quant-lab/ml/dtb_lab/directional_bias_backtest_v2.csv")
