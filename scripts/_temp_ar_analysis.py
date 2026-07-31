import pandas as pd
from pathlib import Path

DATA_DIR = Path("quant-lab/data")
tier_files = list(DATA_DIR.glob("ml/data/tiers/*_asian_ranges.csv"))

print("=== ACTUAL ASIAN RANGE PERCENTILES ===")
print()

results = {}
for f in sorted(tier_files):
    symbol = f.stem.replace("_asian_ranges", "")
    df = pd.read_csv(f)
    ar = df["ar_pips"]
    
    p50 = ar.quantile(0.50)
    p90 = ar.quantile(0.90)
    max_ar = ar.max()
    
    # Tier breakpoints at 33rd and 67th percentile
    t1_max = ar.quantile(0.33)
    t2_max = ar.quantile(0.67)
    
    # Round to nice numbers
    t1_max = round(t1_max / 5) * 5
    t2_max = round(t2_max / 5) * 5
    t3_max = t2_max * 2
    
    results[symbol] = {"T1": t1_max, "T2": t2_max, "T3": t3_max}
    
    print("%-8s: T1<=%4.0fp  T2<=%4.0fp  T3<=%4.0fp  (p50=%.0f, p90=%.0f, max=%.0f, n=%d)" % (
        symbol, t1_max, t2_max, t3_max, p50, p90, max_ar, len(df)))

print()
print("=== SUGGESTED TIER CONFIGS ===")
for sym, tiers in sorted(results.items()):
    print('    "%s": {"T1": {"ar_max": %.0f}, "T2": {"ar_max": %.0f}, "T3": {"ar_max": %.0f}},' % (
        sym, tiers["T1"], tiers["T2"], tiers["T3"]))
