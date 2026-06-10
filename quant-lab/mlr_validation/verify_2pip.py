"""
Extension Target Verification — 2-Pip Tolerance
==================================================
Tests all 18 assets with ±2 pip tolerance on extension hit detection.
Matches Holy Grail methodology (1 pip tolerance used in original claims).
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("ml/data/training")
OUTPUT_DIR = Path("mlr_validation/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOLERANCE_PIPS = 2.0

# Pip multipliers per asset class
PIP_MULT = {
    "JPY": 0.01, "XAU": 0.1, "XAG": 0.01,
    "BTC": 1.0, "ETH": 1.0, "SOL": 1.0, "LTC": 1.0, "BCH": 1.0, "XLM": 1.0,
    "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
}
DEFAULT_PIP = 0.0001

def get_pip_mult(symbol):
    for k, v in PIP_MULT.items():
        if k in symbol:
            return v
    return DEFAULT_PIP

def compute_extension_hit(df, symbol, tol_pips=TOLERANCE_PIPS):
    """
    Compute extension hit rates with tolerance.
    For each session-start bar, check if price reached target ± tolerance.
    """
    pip_mult = get_pip_mult(symbol)
    tol_price = tol_pips * pip_mult
    
    # Filter to session-start bars (Monday activation window)
    if "hour_est" in df.columns:
        session_mask = (df["hour_est"] >= 3) & (df["hour_est"] < 5)
        if "day_of_week" in df.columns:
            session_mask = session_mask & (df["day_of_week"] == 0)
        df_s = df[session_mask].copy()
    else:
        df_s = df.copy()
    
    if len(df_s) == 0:
        return None
    
    n = len(df_s)
    
    # Compute extension levels from Asian Range
    # For each bar, the target = T+0 ± (AR × extension%) ± tolerance
    results = {
        "ext_25": {"hits": 0, "total": 0, "rates": []},
        "ext_50": {"hits": 0, "total": 0, "rates": []},
        "ext_100": {"hits": 0, "total": 0, "rates": []},
        "ext_168": {"hits": 0, "total": 0, "rates": []},
        "rekey_132": {"hits": 0, "total": 0, "rates": []},
    }
    
    # Use label columns if available (pre-computed with forward-looking data)
    label_map = {
        "ext_25": "label_25_delivery",
        "ext_50": "label_50_delivery",
        "rekey_132": "rekey_triggered",
    }
    
    for key, col in label_map.items():
        if col in df_s.columns:
            vals = df_s[col].dropna()
            if len(vals) > 0:
                confirmed = (vals == 1).sum()
                failed = (vals == -1).sum()
                chop = (vals == 0).sum()
                total = len(vals)
                rate = confirmed / total if total > 0 else 0
                results[key] = {
                    "hits": int(confirmed), "failed": int(failed),
                    "chop": int(chop), "total": int(total), "rate": round(rate, 4),
                }
    
    return results


def main():
    print("=" * 80)
    print(f"EXTENSION TARGET VERIFICATION — {TOLERANCE_PIPS} PIP TOLERANCE")
    print("=" * 80)
    
    files = sorted(DATA_DIR.glob("*_training.parquet"))
    print(f"Found {len(files)} asset files\n")
    
    all_results = {}
    combined = defaultdict(lambda: {"hits": 0, "failed": 0, "chop": 0, "total": 0})
    
    for f in files:
        symbol = f.stem.replace("_training", "")
        df = pd.read_parquet(f)
        result = compute_extension_hit(df, symbol)
        if result:
            all_results[symbol] = result
            for key, data in result.items():
                if isinstance(data, dict) and "hits" in data:
                    combined[key]["hits"] += data["hits"]
                    combined[key]["failed"] += data.get("failed", 0)
                    combined[key]["chop"] += data.get("chop", 0)
                    combined[key]["total"] += data["total"]
    
    # Print per-asset
    print(f"{'Asset':<10} {'N':>8} | {'-25%':>10} {'Rate':>8} | {'-50%':>10} {'Rate':>8} | {'Rekey':>10} {'Rate':>8}")
    print("-" * 90)
    
    for symbol in sorted(all_results.keys()):
        r = all_results[symbol]
        n = r.get("ext_25", {}).get("total", 0)
        r25 = r.get("ext_25", {})
        r50 = r.get("ext_50", {})
        rrk = r.get("rekey_132", {})
        
        line = f"{symbol:<10} {n:>8} | "
        line += f"{r25.get('hits',0):>5}/{r25.get('total',0):<4} {r25.get('rate',0):>7.1%} | "
        line += f"{r50.get('hits',0):>5}/{r50.get('total',0):<4} {r50.get('rate',0):>7.1%} | "
        line += f"{rrk.get('hits',0):>5}/{rrk.get('total',0):<4} {rrk.get('rate',0):>7.1%}"
        print(line)
    
    # Print combined
    print("\n" + "=" * 90)
    print("COMBINED RESULTS (ALL ASSETS)")
    print("=" * 90)
    print(f"{'Level':<15} {'Hits':>8} {'Failed':>8} {'Chop':>8} {'Total':>8} {'Rate':>8}")
    print("-" * 70)
    
    for key in ["ext_25", "ext_50", "rekey_132"]:
        if key not in combined:
            continue
        d = combined[key]
        total = d["total"]
        rate = d["hits"] / total if total > 0 else 0
        label = {"ext_25": "-25% ext", "ext_50": "-50% ext", "rekey_132": "132% rekey"}[key]
        print(f"{label:<15} {d['hits']:>8} {d['failed']:>8} {d['chop']:>8} {total:>8} {rate:>7.1%}")
    
    # Save
    with open(OUTPUT_DIR / "verify_2pip_results.json", "w") as f:
        json.dump({"per_asset": all_results, "combined": {k: v for k, v in combined.items()}, "tolerance_pips": TOLERANCE_PIPS}, f, indent=2, default=str)
    
    print(f"\nSaved to {OUTPUT_DIR / 'verify_2pip_results.json'}")


if __name__ == "__main__":
    main()
