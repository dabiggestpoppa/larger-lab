"""
ATTEMPT 2: Temporal Squeeze / Schedule Deficit Engine
======================================================
Tracks real-time pace vs expected pace to detect when market is behind schedule
and must compress remaining distribution into shrinking time window.
"""
import sys, os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import numpy as np
from pathlib import Path
from dtb_lab.directional_bias import DirectionalBias

RAW_DATA_DIR = Path("../data")


def evaluate_temporal_squeeze(df: pd.DataFrame, symbol: str = "EURUSD") -> pd.DataFrame:
    """
    For each trading day, track the pace at multiple checkpoints and detect
    schedule deficits that predict forced compression (gear shifts).
    """
    bias = DirectionalBias()
    df = df.copy()
    df['est_hour'] = (df.index.hour - 5) % 24
    df['trade_date'] = df.index.date

    # Expected pace curves by tier (cumulative % of total range delivered by each hour)
    # These are the "schedule" the market should follow
    PACE_CURVES = {
        "T1": {8: 0.15, 9: 0.30, 10: 0.50, 11: 0.70, 12: 0.85, 13: 0.95, 14: 1.00},
        "T2": {8: 0.12, 9: 0.25, 10: 0.42, 11: 0.60, 12: 0.78, 13: 0.90, 14: 1.00},
        "T3": {8: 0.10, 9: 0.20, 10: 0.35, 11: 0.52, 12: 0.70, 13: 0.85, 14: 1.00},
    }

    results = []
    for date, day_bars in df.groupby("trade_date"):
        if len(day_bars) < 50:
            continue

        bars_12pm = day_bars[day_bars.index.hour < 17]
        if len(bars_12pm) < 20:
            continue

        result = bias.evaluate(bars_12pm, symbol)
        if result.direction.value == "NONE":
            continue

        session_open = bars_12pm.iloc[0]["open"]
        high_12pm = bars_12pm["high"].max()
        low_12pm = bars_12pm["low"].min()
        price_12pm = bars_12pm.iloc[-1]["close"]

        # Total range delivered by 12PM
        total_range = (high_12pm - low_12pm) * 10000

        # MFE in bias direction
        if result.direction.value == "LONG":
            mfe = (high_12pm - session_open) * 10000
        else:
            mfe = (session_open - low_12pm) * 10000

        # Determine tier for pace curve
        ar = result.asian_range_pips
        if ar < 20:
            tier = "T1"
        elif ar < 30:
            tier = "T2"
        else:
            tier = "T3"

        pace_curve = PACE_CURVES[tier]

        # Track pace at each checkpoint
        pace_checks = {}
        for check_hour in [9, 10, 11, 12, 13]:
            check_bars = bars_12pm[bars_12pm.index.hour < check_hour + 1]
            if len(check_bars) < 5:
                continue

            if result.direction.value == "LONG":
                delivered = (check_bars["high"].max() - session_open) * 10000
            else:
                delivered = (session_open - check_bars["low"].min()) * 10000

            expected_fraction = pace_curve.get(check_hour, 0.5)
            expected_mfe = ar * expected_fraction * 2.5  # Approximate total expected

            if expected_mfe > 0:
                actual_fraction = delivered / expected_mfe
            else:
                actual_fraction = 0

            pace_checks[f"pace_{check_hour}h"] = round(actual_fraction, 3)

        # Schedule deficit at 9AM
        pace_9h = pace_checks.get("pace_9h", 0)
        deficit_9am = max(0, 0.30 - pace_9h)  # Should be at 30% by 9AM

        # Required velocity to finish by 12PM
        remaining = max(0, ar * 2.5 - mfe)  # Remaining expected distribution
        hours_remaining = max(0.5, (17 - 12))  # Hours until 12PM from last checkpoint
        required_velocity = remaining / hours_remaining if hours_remaining > 0 else 0

        # Temporal squeeze flag
        squeeze = 1 if (deficit_9am > 0.15 and pace_9h < 0.20) else 0

        # Direction correct at 12PM
        dir_correct = 1 if (
            (result.direction.value == "LONG" and price_12pm > session_open)
            or (result.direction.value == "SHORT" and price_12pm < session_open)
        ) else 0

        results.append({
            "date": str(date),
            "state": result.state.value,
            "bias_direction": result.direction.value,
            "regime": result.lens_c.value,
            "asian_range_pips": ar,
            "tier": tier,
            "actual_mfe": round(mfe, 2),
            "direction_correct": dir_correct,
            "deficit_9am": round(deficit_9am, 3),
            "squeeze_flag": squeeze,
            "required_velocity": round(required_velocity, 2),
            **pace_checks,
        })

    return pd.DataFrame(results)


def report(results: pd.DataFrame, symbol: str):
    """Generate temporal squeeze report."""
    if len(results) == 0:
        print("No results!")
        return

    print("=" * 60)
    print(f"ATTEMPT 2: TEMPORAL SQUEEZE / SCHEDULE DEFICIT ({symbol})")
    print("=" * 60)
    print(f"\nTotal days: {len(results)}")

    # Squeeze vs non-squeeze
    squeeze = results[results["squeeze_flag"] == 1]
    no_squeeze = results[results["squeeze_flag"] == 0]

    print(f"\n── SQUEEZE ANALYSIS ──")
    if len(squeeze) > 0:
        correct = squeeze[squeeze["direction_correct"] == 1]
        print(f"  SQUEEZE days: {len(squeeze)}, acc={len(correct)/len(squeeze)*100:.1f}%")
    if len(no_squeeze) > 0:
        correct = no_squeeze[no_squeeze["direction_correct"] == 1]
        print(f"  NO SQUEEZE days: {len(no_squeeze)}, acc={len(correct)/len(no_squeeze)*100:.1f}%")

    # Pace analysis
    print(f"\n── PACE AT CHECKPOINTS ──")
    for hour in [9, 10, 11, 12, 13]:
        col = f"pace_{hour}h"
        if col in results.columns:
            pace_vals = results[col].dropna()
            if len(pace_vals) > 0:
                print(f"  {hour:2d}: mean={pace_vals.mean():.3f}, "
                      f"std={pace_vals.std():.3f}, "
                      f"<0.5={(pace_vals < 0.5).sum()}/{len(pace_vals)}")

    # Deficit analysis
    print(f"\n── SCHEDULE DEFICIT AT 9AM ──")
    deficit = results["deficit_9am"].dropna()
    if len(deficit) > 0:
        high_deficit = results[results["deficit_9am"] > 0.15]
        low_deficit = results[results["deficit_9am"] <= 0.15]
        if len(high_deficit) > 0:
            correct = high_deficit[high_deficit["direction_correct"] == 1]
            print(f"  High deficit (>0.15): {len(high_deficit)} days, "
                  f"acc={len(correct)/len(high_deficit)*100:.1f}%")
        if len(low_deficit) > 0:
            correct = low_deficit[low_deficit["direction_correct"] == 1]
            print(f"  Low deficit (<=0.15): {len(low_deficit)} days, "
                  f"acc={len(correct)/len(low_deficit)*100:.1f}%")

    # Overall
    correct = results[results["direction_correct"] == 1]
    print(f"\n  OVERALL: {len(correct)}/{len(results)} = {len(correct)/len(results)*100:.1f}%")
    print(f"{'='*60}")


if __name__ == "__main__":
    for sym in ["EURUSD", "USDCHF"]:
        p = RAW_DATA_DIR / f"{sym}_M5.csv"
        if not p.exists():
            print(f"SKIP {sym}: no data")
            continue
        df = pd.read_csv(p)
        df['dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
        df = df.dropna(subset=['dt']).set_index('dt').sort_index()
        results = evaluate_temporal_squeeze(df, sym)
        if len(results) > 0:
            report(results, sym)
            results.to_csv(f"dtb_lab/attempt2_{sym}.csv", index=False)
