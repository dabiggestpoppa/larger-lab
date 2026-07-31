"""
ATTEMPT 1: Reverse-Constraint Variable Isolation
===================================================
Tags the 4 deterministic miss pathways and adds reverse-constraint features.
Tests whether structural signatures can explain the 20-30% "variance".
"""
import sys, os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import numpy as np
from pathlib import Path
from dtb_lab.directional_bias import DirectionalBias

RAW_DATA_DIR = Path("../data")


def tag_miss_pathways(df: pd.DataFrame, symbol: str = "EURUSD") -> pd.DataFrame:
    """
    For every trading day, tag which of the 4 structural pathways applies.
    Uses the existing DTB + Bias systems to identify misses and categorize them.
    """
    bias = DirectionalBias()
    df = df.copy()
    df['est_hour'] = (df.index.hour - 5) % 24
    df['trade_date'] = df.index.date

    results = []
    for date, day_bars in df.groupby("trade_date"):
        if len(day_bars) < 50:
            continue

        bars_12pm = day_bars[day_bars.index.hour < 17]
        if len(bars_12pm) < 20:
            continue

        # Get bias evaluation
        result = bias.evaluate(bars_12pm, symbol)

        if result.direction.value == "NONE":
            continue

        # Measure actual outcome
        session_open = bars_12pm.iloc[0]["open"]
        price_12pm = bars_12pm.iloc[-1]["close"]
        high_12pm = bars_12pm["high"].max()
        low_12pm = bars_12pm["low"].min()

        # MFE in bias direction
        if result.direction.value == "LONG":
            mfe = (high_12pm - session_open) * 10000
            target_25 = session_open + 0.25 * result.asian_range_pips / 10000
            target_hit = high_12pm >= target_25
            target_hit_time = None
            if target_hit:
                # Find when target was first hit
                for idx, bar in bars_12pm.iterrows():
                    if bar["high"] >= target_25:
                        target_hit_time = idx.strftime("%H:%M")
                        break
        else:
            mfe = (session_open - low_12pm) * 10000
            target_25 = session_open - 0.25 * result.asian_range_pips / 10000
            target_hit = low_12pm <= target_25
            target_hit_time = None
            if target_hit:
                for idx, bar in bars_12pm.iterrows():
                    if bar["low"] <= target_25:
                        target_hit_time = idx.strftime("%H:%M")
                        break

        # DTB predicted MFE (from tier multiplier)
        predicted_mfe = result.asian_range_pips * result.regime_ratio * 0.5
        if result.lens_c.value == "CONFIRMED":
            predicted_mfe *= 1.5
        elif result.lens_c.value == "FAILED":
            predicted_mfe *= 0.7

        # Deviation
        deviation = abs(mfe - predicted_mfe) if predicted_mfe > 0 else 0

        # ── Tag the 4 pathways ──
        pathway = "BASELINE"
        if deviation > 3:
            # Pathway A: Delayed Resolution
            if (result.lens_c.value in ["FAILED", "CAUTION"]
                    and target_hit
                    and target_hit_time
                    and target_hit_time >= "11:30"):
                pathway = "DELAYED_RESOLVER"

            # Pathway B: Gear Shift Over-Delivery
            elif mfe > predicted_mfe * 1.20:
                pathway = "GEAR_SHIFT"

            # Pathway C: Midpoint Stall
            elif (target_hit and target_hit_time
                  and target_hit_time < "11:00"
                  and price_12pm < (session_open + 0.5 * (high_12pm - session_open))):
                pathway = "MIDPOINT_STALL"

            # Pathway D: Post-12PM Fade
            elif target_hit and target_hit_time and target_hit_time < "11:50":
                # Check if price faded after 12PM
                post_12pm = day_bars[day_bars.index.hour >= 17]
                if len(post_12pm) > 0:
                    post_close = post_12pm.iloc[-1]["close"]
                    fade = abs(post_close - price_12pm) * 10000
                    if fade > 3:
                        pathway = "POST_12PM_FADE"

        # Reverse-constraint features
        pips_distributed = (bars_12pm["high"].max() - bars_12pm["low"].min()) * 10000
        au_size = result.asian_range_pips * 0.5  # Approximate AU from tier
        remaining_deficit = max(0, predicted_mfe - pips_distributed)
        required_loops = remaining_deficit / au_size if au_size > 0 else 0
        mins_remaining = max(1, (17 - bars_12pm.index[-1].hour) * 60)
        time_pressure = mins_remaining / max(1, required_loops * 52)  # 52 min per loop

        results.append({
            "date": str(date),
            "state": result.state.value,
            "bias_direction": result.direction.value,
            "regime": result.lens_c.value,
            "regime_ratio": result.regime_ratio,
            "asian_range_pips": result.asian_range_pips,
            "predicted_mfe": round(predicted_mfe, 2),
            "actual_mfe": round(mfe, 2),
            "deviation": round(deviation, 2),
            "pathway": pathway,
            "target_hit": target_hit,
            "target_hit_time": target_hit_time,
            "required_loops": round(required_loops, 1),
            "time_pressure_ratio": round(time_pressure, 3),
            "direction_correct": 1 if (
                (result.direction.value == "LONG" and price_12pm > session_open)
                or (result.direction.value == "SHORT" and price_12pm < session_open)
            ) else 0,
        })

    return pd.DataFrame(results)


def report(results: pd.DataFrame, symbol: str):
    """Generate pathway analysis report."""
    if len(results) == 0:
        print("No results!")
        return

    print("=" * 60)
    print(f"ATTEMPT 1: REVERSE-CONSTRAINT PATHWAY ANALYSIS ({symbol})")
    print("=" * 60)
    print(f"\nTotal days analyzed: {len(results)}")

    # Pathway distribution
    print(f"\n── PATHWAY DISTRIBUTION ──")
    for pathway in results["pathway"].unique():
        pw = results[results["pathway"] == pathway]
        if len(pw) > 0:
            correct = pw[pw["direction_correct"] == 1]
            acc = len(correct) / len(pw) * 100
            mean_dev = pw["deviation"].mean()
            print(f"  {pathway:25s}: {len(pw):4d} days, "
                  f"acc={acc:5.1f}%, mean_dev={mean_dev:.1f}p")

    # Accuracy by pathway
    print(f"\n── ACCURACY BY PATHWAY ──")
    for pathway in ["BASELINE", "DELAYED_RESOLVER", "GEAR_SHIFT", "MIDPOINT_STALL", "POST_12PM_FADE"]:
        pw = results[results["pathway"] == pathway]
        if len(pw) > 0:
            correct = pw[pw["direction_correct"] == 1]
            acc = len(correct) / len(pw) * 100
            target_hits = pw[pw["target_hit"] == True]
            hit_rate = len(target_hits) / len(pw) * 100
            print(f"  {pathway:25s}: acc={acc:5.1f}%, target_hit={hit_rate:.1f}%")

    # Time pressure analysis
    print(f"\n── TIME PRESSURE ANALYSIS ──")
    tp = results[results["time_pressure_ratio"] > 0]
    if len(tp) > 0:
        high_tp = tp[tp["time_pressure_ratio"] > 1.0]
        low_tp = tp[tp["time_pressure_ratio"] <= 1.0]
        if len(high_tp) > 0:
            print(f"  High pressure (>1.0): {len(high_tp)} days, "
                  f"acc={high_tp['direction_correct'].mean()*100:.1f}%")
        if len(low_tp) > 0:
            print(f"  Low pressure (<=1.0): {len(low_tp)} days, "
                  f"acc={low_tp['direction_correct'].mean()*100:.1f}%")

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
        results = tag_miss_pathways(df, sym)
        if len(results) > 0:
            report(results, sym)
            results.to_csv(f"dtb_lab/attempt1_{sym}.csv", index=False)
