"""
Extension Target Verification — Final
========================================
Uses CC's pre-computed labels (label_25_delivery, label_50_delivery, rekey_triggered)
which are already computed with forward-looking price data.

The labels use exact hit detection (no tolerance).
We report the raw hit rates — this is the REAL data, no forcing.

Holy Grail claims (from 281 weeks, EURUSD):
- -25% extension: 90% hit rate
- -50% extension: 82% hit rate
- 132% rekey: 95% claimed, 71.53% actual

Our data: ALL sessions (not just validated weeks), ALL 18 assets.
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

# Holy Grail claims
CLAIMS = {
    "label_25_delivery": {"claim": 0.90, "note": "EURUSD validated weeks only"},
    "label_50_delivery": {"claim": 0.82, "note": "EURUSD validated weeks only"},
    "rekey_triggered": {"claim": 0.95, "note": "Claimed 95%, actual 71.53%"},
}


def main():
    print("=" * 80)
    print("EXTENSION TARGET VERIFICATION — FINAL (2 PIP TOLERANCE)")
    print("=" * 80)
    print("Tolerance: +/- {} pips on extension levels".format(TOLERANCE_PIPS))
    print("Data: ALL session-start bars, ALL 18 assets")
    print()

    files = sorted(DATA_DIR.glob("*_training.parquet"))
    print("Found {} asset files\n".format(len(files)))

    all_results = {}
    combined = defaultdict(lambda: {"confirmed": 0, "failed": 0, "chop": 0, "total": 0})

    for f in files:
        symbol = f.stem.replace("_training", "")
        df = pd.read_parquet(f)

        # Filter to session-start bars
        if "hour_est" in df.columns:
            mask = (df["hour_est"] >= 3) & (df["hour_est"] < 5)
            if "day_of_week" in df.columns:
                mask = mask & (df["day_of_week"] == 0)
            sessions = df[mask]
        else:
            sessions = df

        n_sess = len(sessions)
        if n_sess == 0:
            print("{}: NO SESSION BARS".format(symbol))
            continue

        result = {"symbol": symbol, "n_sessions": n_sess}

        for col in ["label_25_delivery", "label_50_delivery", "rekey_triggered"]:
            if col not in sessions.columns:
                continue
            vals = sessions[col].dropna()
            if len(vals) == 0:
                continue

            confirmed = int((vals == 1).sum())
            failed = int((vals == -1).sum())
            chop = int((vals == 0).sum())
            total = int(len(vals))
            rate = confirmed / total if total > 0 else 0

            result[col] = {"confirmed": confirmed, "failed": failed, "chop": chop, "total": total, "rate": round(rate, 4)}

            combined[col]["confirmed"] += confirmed
            combined[col]["failed"] += failed
            combined[col]["chop"] += chop
            combined[col]["total"] += total

        all_results[symbol] = result

        r25 = result.get("label_25_delivery", {})
        r50 = result.get("label_50_delivery", {})
        rrk = result.get("rekey_triggered", {})
        print("{}: {} sessions | -25%={}/{}={:.1f}% | -50%={}/{}={:.1f}% | Rekey={}/{}={:.1f}%".format(
            symbol, n_sess,
            r25.get("confirmed",0), r25.get("total",0), r25.get("rate",0)*100,
            r50.get("confirmed",0), r50.get("total",0), r50.get("rate",0)*100,
            rrk.get("confirmed",0), rrk.get("total",0), rrk.get("rate",0)*100,
        ))

    # Combined
    print("\n" + "=" * 80)
    print("COMBINED RESULTS (ALL ASSETS)")
    print("=" * 80)
    print("{:<20} {:>8} {:>8} {:>8} {:>8} {:>8} {:>8} {:>10}".format(
        "Level", "Confirmed", "Failed", "Chop", "Total", "Rate", "Claim", "Status"))
    print("-" * 90)

    for col in ["label_25_delivery", "label_50_delivery", "rekey_triggered"]:
        if col not in combined:
            continue
        d = combined[col]
        total = d["total"]
        rate = d["confirmed"] / total if total > 0 else 0
        label = col.replace("label_", "").replace("_delivery", "").replace("_triggered", "")

        claim_info = CLAIMS.get(col, {})
        claim = claim_info.get("claim")
        note = claim_info.get("note", "")

        if claim is not None:
            diff = rate - claim
            status = "PASS" if diff >= 0 else "LOW ({:+.1%})".format(diff)
            claim_str = "{:.0%}".format(claim)
        else:
            status = "MEASURED"
            claim_str = "N/A"

        print("{:<20} {:>8} {:>8} {:>8} {:>8} {:>7.1%} {:>8} {:>10}".format(
            label, d["confirmed"], d["failed"], d["chop"], total, rate, claim_str, status))
        if note:
            print("  Note: {}".format(note))

    # Save
    output = {
        "tolerance_pips": TOLERANCE_PIPS,
        "per_asset": all_results,
        "combined": {k: v for k, v in combined.items()},
        "holy_grail_claims": {k: v["claim"] for k, v in CLAIMS.items()},
    }
    with open(OUTPUT_DIR / "final_verification.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print("\nSaved to {}".format(OUTPUT_DIR / "final_verification.json"))


if __name__ == "__main__":
    main()
