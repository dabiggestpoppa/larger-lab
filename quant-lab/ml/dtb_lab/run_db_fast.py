"""Fast directional bias test — sample every N bars instead of every bar."""
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
    "AUDJPY": "AUDJPY_PRO_M5.csv",
    "NZDJPY": "NZDJPY_PRO_M5.csv",
    "CHFJPY": "CHFJPY_M5.csv",
    "AUDNZD": "AUDNZD_PRO_M5.csv",
    "GBPAUD": "GBPAUD_M5.csv",
    "GBPCAD": "GBPCAD_PRO_M5.csv",
    "AUDCAD": "AUDCAD_PRO_M5.csv",
    "EURAUD": "EURAUD_PRO_M5.csv",
    "EURNZD": "EURNZD_PRO_M5.csv",
    "EURCAD": "EURCAD_PRO_M5.csv",
    "NZDCAD": "NZDCAD_PRO_M5.csv",
    "NZDCHF": "NZDCHF_PRO_M5.csv",
    "CADJPY": "CADJPY_PRO_M5.csv",
    "CADCHF": "CADCHF_PRO_M5.csv",
    "XAUUSD": "XAUUSD_M5.csv",
    "XAGUSD": "XAGUSD_M5.csv",
    "US500": "US500_M5.csv",
    "DE30": "DE30_M5.csv",
    "FR40": "FR40_M5.csv",
    "HK50": "HK50_M5.csv",
    "BTCUSD": "BTCUSD_M5.csv",
    "BCHUSD": "BCHUSD_M5.csv",
    "LTCUSD": "LTCUSD_M5.csv",
    "BNBUSD": "BNBUSD_M5.csv",
    "XLMUSD": "XLMUSD_M5.csv",
}

engine = DirectionalBias()
all_results = []
SAMPLE_EVERY = 20  # Sample every 20th bar (~1 per day)

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
        
        if len(df) < 200:
            continue
        
        # Sample every N bars
        sample_indices = list(range(0, len(df), SAMPLE_EVERY))
        
        signal_days = 0
        correct = 0
        state_counts = {}
        
        for i in sample_indices:
            try:
                result = engine.evaluate(df.iloc[:i+1], symbol)
                s = result.state.value
                state_counts[s] = state_counts.get(s, 0) + 1
                
                if s in ["9/9_LOCK", "EXHAUSTION"]:
                    signal_days += 1
                    if i < len(df) - 1:
                        actual = "LONG" if df.iloc[i+1]['close'] > df.iloc[i]['close'] else "SHORT"
                        if result.direction.value == actual:
                            correct += 1
            except:
                continue
        
        accuracy = (correct / signal_days * 100) if signal_days > 0 else 0
        
        print("%-8s: %5d bars, %4d samples, %3d signals, acc=%5.1f%%, states=%s" % (
            symbol, len(df), len(sample_indices), signal_days, accuracy, state_counts))
        
        all_results.append({
            "symbol": symbol,
            "bars": len(df),
            "samples": len(sample_indices),
            "signal_days": signal_days,
            "correct": correct,
            "accuracy": round(accuracy, 1),
        })
        
    except Exception as e:
        print("ERROR %s: %s" % (symbol, e))

print("\n" + "="*70)
print("DIRECTIONAL BIAS — ALL ASSETS (sorted by accuracy)")
print("="*70)
results_df = pd.DataFrame(all_results)
if len(results_df) > 0:
    results_df = results_df.sort_values("accuracy", ascending=False)
    for _, row in results_df.iterrows():
        print("%-8s: acc=%5.1f%%  signals=%3d  bars=%5d" % (
            row['symbol'], row['accuracy'], row['signal_days'], row['bars']))
    results_df.to_csv(RESULTS_DIR / "directional_bias_all_assets.csv", index=False)
    print("\nSaved to quant-lab/ml/dtb_lab/directional_bias_all_assets.csv")
