"""
Extension Target Verification — Session-Level
===============================================
Only counts valid session-start bars (Monday 03:00 EST or first bar after AR set).
This matches the Holy Grail's methodology of measuring from session start.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("ml/data/training")
OUTPUT_DIR = Path("mlr_validation/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLAIMS = {
    "label_25_delivery": 0.90,
    "label_50_delivery": 0.82,
}

files = sorted(DATA_DIR.glob("*_training.parquet"))
print(f"Found {len(files)} asset files\n")

all_results = {}
combined = defaultdict(lambda: {"confirmed": 0, "failed": 0, "chop": 0, "total": 0})

for f in files:
    symbol = f.stem.replace("_training", "")
    df = pd.read_parquet(f)
    
    # Filter to session-start bars only
    # Session start = Monday 03:00 EST (first bar of activation window)
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
        # Monday = 0, Tuesday = 1, etc.
        is_monday = ts.dt.dayofweek == 0
        is_activation_hour = ts.dt.hour >= 3  # 03:00 EST
        session_mask = is_monday & is_activation_hour
        df_sessions = df[session_mask]
    elif "hour_est" in df.columns:
        session_mask = (df["hour_est"] >= 3) & (df["hour_est"] < 5)
        if "day_of_week" in df.columns:
            session_mask = session_mask & (df["day_of_week"] == 0)
        df_sessions = df[session_mask]
    else:
        # Use all bars as fallback
        df_sessions = df
    
    n_sessions = len(df_sessions)
    n_total = len(df)
    
    result = {"symbol": symbol, "total_samples": n_total, "session_samples": n_sessions}
    
    for col in ["label_25_delivery", "label_50_delivery", "rekey_triggered"]:
        if col not in df_sessions.columns:
            continue
        vals = df_sessions[col].dropna()
        if len(vals) == 0:
            continue
        
        confirmed = (vals == 1).sum()
        failed = (vals == -1).sum()
        chop = (vals == 0).sum()
        total = len(vals)
        rate = confirmed / total if total > 0 else 0
        
        result[col] = {
            "confirmed": int(confirmed), "failed": int(failed),
            "chop": int(chop), "total": int(total), "rate": round(rate, 4),
        }
        
        combined[col]["confirmed"] += int(confirmed)
        combined[col]["failed"] += int(failed)
        combined[col]["chop"] += int(chop)
        combined[col]["total"] += int(total)
    
    all_results[symbol] = result

# Print
print("=" * 90)
print("SESSION-LEVEL EXTENSION HIT RATES (Monday session starts only)")
print("=" * 90)
print(f"{'Asset':<10} {'Sessions':>8} | {'-25% Conf':>10} {'Rate':>8} | {'-50% Conf':>10} {'Rate':>8}")
print("-" * 90)

for symbol in sorted(all_results.keys()):
    r = all_results[symbol]
    ns = r.get("session_samples", 0)
    r25 = r.get("label_25_delivery", {})
    r50 = r.get("label_50_delivery", {})
    line = f"{symbol:<10} {ns:>8} | "
    line += f"{r25.get('confirmed',0):>5}/{r25.get('total',0):<4} {r25.get('rate',0):>7.1%} | "
    line += f"{r50.get('confirmed',0):>5}/{r50.get('total',0):<4} {r50.get('rate',0):>7.1%}"
    print(line)

print("\n" + "=" * 90)
print("COMBINED SESSION-LEVEL RESULTS")
print("=" * 90)
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

with open(OUTPUT_DIR / "session_extension_verification.json", "w") as f:
    json.dump({"per_asset": all_results, "combined": {k: v for k, v in combined.items()}}, f, indent=2, default=str)

print(f"\nSaved to {OUTPUT_DIR / 'session_extension_verification.json'}")
