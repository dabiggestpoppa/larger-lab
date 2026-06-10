"""
Extension Target Verification — All Assets
============================================
Verifies extension hit rates against Holy Grail claims.
Uses CC's training data labels: -1=FAILED, 0=CHOP, 1=CONFIRMED
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("ml/data/training")
OUTPUT_DIR = Path("mlr_validation/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Holy Grail claims (from 281 weeks, EURUSD)
CLAIMS = {
    "label_25_delivery": 0.90,   # Claimed 90%
    "label_50_delivery": 0.82,   # Claimed 82%
}

files = sorted(DATA_DIR.glob("*_training.parquet"))
print(f"Found {len(files)} asset files\n")

all_results = {}
combined = defaultdict(lambda: {"confirmed": 0, "failed": 0, "chop": 0, "total": 0})

for f in files:
    symbol = f.stem.replace("_training", "")
    df = pd.read_parquet(f)
    n = len(df)
    
    result = {"symbol": symbol, "total_samples": n}
    
    for col in ["label_25_delivery", "label_50_delivery", "rekey_triggered"]:
        if col not in df.columns:
            continue
        vals = df[col].dropna()
        if len(vals) == 0:
            continue
        
        confirmed = (vals == 1).sum()
        failed = (vals == -1).sum()
        chop = (vals == 0).sum()
        total = len(vals)
        rate = confirmed / total if total > 0 else 0
        
        result[col] = {
            "confirmed": int(confirmed),
            "failed": int(failed),
            "chop": int(chop),
            "total": int(total),
            "rate": round(rate, 4),
        }
        
        combined[col]["confirmed"] += int(confirmed)
        combined[col]["failed"] += int(failed)
        combined[col]["chop"] += int(chop)
        combined[col]["total"] += int(total)
    
    all_results[symbol] = result

# Print per-asset
print("=" * 80)
print("PER-ASSET EXTENSION HIT RATES")
print("=" * 80)
print(f"{'Asset':<10} {'N':>8} | {'-25% Conf':>10} {'-25% Fail':>10} {'-25% Chop':>10} | {'-50% Conf':>10} {'-50% Fail':>10}")
print("-" * 80)

for symbol in sorted(all_results.keys()):
    r = all_results[symbol]
    n = r.get("total_samples", 0)
    r25 = r.get("label_25_delivery", {})
    r50 = r.get("label_50_delivery", {})
    line = f"{symbol:<10} {n:>8} | "
    line += f"{r25.get('confirmed',0):>10} {r25.get('failed',0):>10} {r25.get('chop',0):>10} | "
    line += f"{r50.get('confirmed',0):>10} {r50.get('failed',0):>10}"
    print(line)

# Print combined
print("\n" + "=" * 80)
print("COMBINED RESULTS (ALL ASSETS)")
print("=" * 80)
print(f"{'Level':<25} {'Confirmed':>10} {'Failed':>10} {'Chop':>10} {'Total':>10} {'Rate':>8} {'Claim':>8} {'Status':>10}")
print("-" * 95)

for col in ["label_25_delivery", "label_50_delivery", "rekey_triggered"]:
    if col not in combined:
        continue
    d = combined[col]
    total = d["total"]
    rate = d["confirmed"] / total if total > 0 else 0
    label = col.replace("label_", "").replace("_delivery", "").replace("_triggered", "")
    
    claim = CLAIMS.get(col)
    if claim is not None:
        diff = rate - claim
        status = "PASS" if diff >= 0 else f"LOW {diff:+.1%}"
        claim_str = f"{claim:.1%}"
    else:
        status = "MEASURED"
        claim_str = "N/A"
    
    print(f"{label:<25} {d['confirmed']:>10} {d['failed']:>10} {d['chop']:>10} {total:>10} {rate:>7.1%} {claim_str:>8} {status:>10}")

# Save
with open(OUTPUT_DIR / "extension_verification.json", "w") as f:
    json.dump({"per_asset": all_results, "combined": {k: v for k, v in combined.items()}}, f, indent=2, default=str)

print(f"\nSaved to {OUTPUT_DIR / 'extension_verification.json'}")
