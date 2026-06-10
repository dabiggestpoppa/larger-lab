"""
Extension Target Verification — With Tolerance
=================================================
Recomputes extension hit rates with ±2 pip tolerance on raw price data.
This matches the Holy Grail's 1-pip tolerance methodology.

For each session-start bar:
1. Calculate extension levels from Asian Range
2. Check if price reached target ± tolerance in forward window
3. Compare hit rates across all assets
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

# Extension levels as % of AR
EXTS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00, "ext_168": 1.68}
REKEY_PCT = 1.32


def get_pip_mult(symbol):
    if "JPY" in symbol: return 0.01
    if "XAU" in symbol: return 0.1
    if "XAG" in symbol: return 0.01
    if symbol in ("BTCUSD","ETHUSD","SOLUSD","LTCUSD","BCHUSD","XLMUSD","US500","DE30","FR40","HK50"): return 1.0
    return 0.0001


def verify_asset(df, symbol, tol_pips=TOLERANCE_PIPS):
    """Verify extension hit rates with tolerance for one asset."""
    pip_mult = get_pip_mult(symbol)
    tol = tol_pips * pip_mult
    
    # Need these columns
    needed = ["asian_range", "asian_high", "asian_low", "high", "close"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        return None
    
    # Filter to session starts (Monday ~03:00 EST)
    if "hour_est" in df.columns:
        mask = (df["hour_est"] >= 3) & (df["hour_est"] < 5)
        if "day_of_week" in df.columns:
            mask = mask & (df["day_of_week"] == 0)
        sessions = df[mask].copy()
    else:
        sessions = df.copy()
    
    if len(sessions) == 0:
        return None
    
    results = {}
    for ext_name, ext_pct in EXTS.items():
        hits = 0
        total = 0
        for idx, row in sessions.iterrows():
            ar = row.get("asian_range", 0)
            if ar <= 0 or pd.isna(ar):
                continue
            
            # Determine direction from Asian close vs open
            direction = "bullish" if row.get("close", 0) > row.get("open", 0) else "bearish"
            
            # Calculate target
            if direction == "bullish":
                t0 = row.get("close", row.get("asian_high", 0))
                target = t0 + (ar * ext_pct)
                # Check if forward high reached target - tolerance
                fwd_high = row.get("high", target)
                hit = fwd_high >= (target - tol)
            else:
                t0 = row.get("close", row.get("asian_low", 0))
                target = t0 - (ar * ext_pct)
                fwd_low = row.get("low", target)
                hit = fwd_low <= (target + tol)
            
            total += 1
            if hit:
                hits += 1
        
        rate = hits / total if total > 0 else 0
        results[ext_name] = {"hits": hits, "total": total, "rate": round(rate, 4)}
    
    # Rekey (132%)
    hits = 0
    total = 0
    for idx, row in sessions.iterrows():
        ar = row.get("asian_range", 0)
        if ar <= 0 or pd.isna(ar):
            continue
        direction = "bullish" if row.get("close", 0) > row.get("open", 0) else "bearish"
        if direction == "bullish":
            target = row.get("close", 0) - (ar * REKEY_PCT)
            fwd_low = row.get("low", target)
            hit = fwd_low <= (target + tol)
        else:
            target = row.get("close", 0) + (ar * REKEY_PCT)
            fwd_high = row.get("high", target)
            hit = fwd_high >= (target - tol)
        total += 1
        if hit:
            hits += 1
    
    rate = hits / total if total > 0 else 0
    results["rekey_132"] = {"hits": hits, "total": total, "rate": round(rate, 4)}
    results["symbol"] = symbol
    results["n_sessions"] = len(sessions)
    
    return results


def main():
    print("=" * 80)
    print("EXTENSION TARGET VERIFICATION — {} PIP TOLERANCE".format(TOLERANCE_PIPS))
    print("=" * 80)
    
    files = sorted(DATA_DIR.glob("*_training.parquet"))
    print("Found {} asset files\n".format(len(files)))
    
    all_results = {}
    combined = defaultdict(lambda: {"hits": 0, "total": 0})
    
    for f in files:
        symbol = f.stem.replace("_training", "")
        df = pd.read_parquet(f)
        result = verify_asset(df, symbol)
        if result:
            all_results[symbol] = result
            n = result.get("n_sessions", 0)
            for key in ["ext_25", "ext_50", "ext_100", "ext_168", "rekey_132"]:
                if key in result:
                    combined[key]["hits"] += result[key]["hits"]
                    combined[key]["total"] += result[key]["total"]
            print("{}: {} sessions | -25%={}/{}={:.1f}% | -50%={}/{}={:.1f}% | 132%={}/{}={:.1f}%".format(
                symbol, n,
                result.get("ext_25",{}).get("hits",0), result.get("ext_25",{}).get("total",0), result.get("ext_25",{}).get("rate",0)*100,
                result.get("ext_50",{}).get("hits",0), result.get("ext_50",{}).get("total",0), result.get("ext_50",{}).get("rate",0)*100,
                result.get("rekey_132",{}).get("hits",0), result.get("rekey_132",{}).get("total",0), result.get("rekey_132",{}).get("rate",0)*100,
            ))
        else:
            print("{}: SKIPPED (missing columns)".format(symbol))
    
    print("\n" + "=" * 80)
    print("COMBINED RESULTS (ALL ASSETS)")
    print("=" * 80)
    print("{:<15} {:>8} {:>8} {:>8}".format("Level", "Hits", "Total", "Rate"))
    print("-" * 45)
    
    for key in ["ext_25", "ext_50", "ext_100", "ext_168", "rekey_132"]:
        if key not in combined:
            continue
        d = combined[key]
        rate = d["hits"] / d["total"] if d["total"] > 0 else 0
        label = {"ext_25": "-25% ext", "ext_50": "-50% ext", "ext_100": "-100% ext", "ext_168": "-168% ext", "rekey_132": "132% rekey"}[key]
        print("{:<15} {:>8} {:>8} {:>7.1%}".format(label, d["hits"], d["total"], rate))
    
    with open(OUTPUT_DIR / "tolerance_{}pip_results.json".format(TOLERANCE_PIPS), "w") as f:
        json.dump({"per_asset": all_results, "combined": {k: v for k, v in combined.items()}, "tolerance_pips": TOLERANCE_PIPS}, f, indent=2, default=str)
    
    print("\nSaved to tolerance_{}pip_results.json".format(TOLERANCE_PIPS))


if __name__ == "__main__":
    main()
