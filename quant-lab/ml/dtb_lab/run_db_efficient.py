"""
Efficient directional bias test — run once per asset using all available data.
Uses the last N bars as a single evaluation point (not cumulative).
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
        
        # Run evaluation on the full dataset once
        result = engine.evaluate(df, symbol)
        
        # Get state counts by evaluating at the last bar
        state_val = result.state.value
        direction_val = result.direction.value
        confidence = result.confidence
        regime_ratio = result.regime_ratio
        lens_a = result.lens_a.value if hasattr(result.lens_a, 'value') else str(result.lens_a)
        lens_b = result.lens_b.value if hasattr(result.lens_b, 'value') else str(result.lens_b)
        lens_c = result.lens_c.value if hasattr(result.lens_c, 'value') else str(result.lens_c)
        
        # Check next-bar direction accuracy
        if len(df) > 1:
            actual = "LONG" if df.iloc[-1]['close'] > df.iloc[-2]['close'] else "SHORT"
            correct = 1 if direction_val == actual else 0
        else:
            correct = 0
            actual = "N/A"
        
        print("%-8s: %5d bars, state=%-15s dir=%-5s conf=%.2f ratio=%.2f A=%-5s B=%-5s C=%-10s actual=%s correct=%d" % (
            symbol, len(df), state_val, direction_val, confidence, regime_ratio, lens_a, lens_b, lens_c, actual, correct))
        
        all_results.append({
            "symbol": symbol,
            "bars": len(df),
            "state": state_val,
            "direction": direction_val,
            "confidence": confidence,
            "regime_ratio": regime_ratio,
            "lens_a": lens_a,
            "lens_b": lens_b,
            "lens_c": lens_c,
        })
        
    except Exception as e:
        print("ERROR %s: %s" % (symbol, e))

print("\n" + "="*70)
print("DIRECTIONAL BIAS — CURRENT STATE (most recent bar)")
print("="*70)
results_df = pd.DataFrame(all_results)
if len(results_df) > 0:
    print(results_df.to_string(index=False))
    results_df.to_csv(RESULTS_DIR / "directional_bias_current.csv", index=False)
