"""
Run 3-Lens Ternary Directional Bias test on all available assets.
"""
import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "quant-lab/ml")

from pathlib import Path
import pandas as pd
from directional_bias import DirectionalBias

DATA_DIR = Path("quant-lab/data")
RESULTS_DIR = Path("quant-lab/ml/dtb_lab")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

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

for symbol, filename in ASSET_FILES.items():
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"SKIP {symbol}: file not found")
        continue
    
    try:
        df = pd.read_csv(filepath)
        
        if 'timestamp' in df.columns:
            df['dt'] = pd.to_datetime(df['timestamp'])
        elif 'time' in df.columns:
            df['dt'] = pd.to_datetime(df['time'])
        else:
            print(f"SKIP {symbol}: no time column")
            continue
        
        df = df.set_index('dt').sort_index()
        
        if len(df) < 100:
            print(f"SKIP {symbol}: only {len(df)} bars")
            continue
        
        signal_days = 0
        correct = 0
        state_counts = {}
        
        for i in range(len(df)):
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
        
        print(f"{symbol}: {len(df)} bars, {signal_days} signals, acc={accuracy:.1f}%, states={state_counts}")
        
        all_results.append({
            "symbol": symbol,
            "bars": len(df),
            "signal_days": signal_days,
            "correct": correct,
            "accuracy": round(accuracy, 1),
            "states": str(state_counts),
        })
        
    except Exception as e:
        print(f"ERROR {symbol}: {e}")

print("\n" + "="*70)
print("DIRECTIONAL BIAS SUMMARY — ALL ASSETS (sorted by accuracy)")
print("="*70)
results_df = pd.DataFrame(all_results)
if len(results_df) > 0:
    results_df = results_df.sort_values("accuracy", ascending=False)
    print(results_df.to_string(index=False))
    results_df.to_csv(RESULTS_DIR / "directional_bias_all_assets.csv", index=False)
    print(f"\nSaved to {RESULTS_DIR / 'directional_bias_all_assets.csv'}")
