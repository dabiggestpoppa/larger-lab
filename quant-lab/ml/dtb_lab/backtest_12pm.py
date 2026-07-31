"""
Directional Bias Backtest — 12PM Cutoff
Uses 12PM EST (17:00 UTC) as the measurement point instead of daily close.
This is the DTB engine shutdown time — the manual's hard exit.
"""
import sys, os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import numpy as np
from pathlib import Path
from dtb_lab.directional_bias import DirectionalBias

RAW_DATA_DIR = Path("../data")

def backtest_12pm(symbol: str = "EURUSD") -> pd.DataFrame:
    """Run 3-Lens Ternary Bias backtest using 12PM cutoff."""
    p = RAW_DATA_DIR / f"{symbol}_M5.csv"
    if not p.exists():
        print(f"ERROR: {p} not found!")
        return pd.DataFrame()

    df = pd.read_csv(p)
    df['dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['dt']).set_index('dt').sort_index()
    df['est_hour'] = (df.index.hour - 5) % 24
    df['trade_date'] = df.index.date

    bias = DirectionalBias()
    results = []

    for date, day_bars in df.groupby("trade_date"):
        if len(day_bars) < 50:
            continue

        # ── 12PM cutoff: use bars up to 17:00 UTC ──
        bars_12pm = day_bars[day_bars.index.hour < 17]
        if len(bars_12pm) < 20:
            continue

        # Evaluate bias at 12PM
        result = bias.evaluate(bars_12pm, symbol)

        # ── Measure outcome at 12PM (not daily close) ──
        if len(bars_12pm) > 0:
            # Price at 3AM (8UTC) — the session open
            session_open = bars_12pm.iloc[0]["open"]

            # Price at 12PM (17UTC) — the hard exit
            price_12pm = bars_12pm.iloc[-1]["close"]

            # High/Low between 3AM and 12PM
            high_12pm = bars_12pm["high"].max()
            low_12pm = bars_12pm["low"].min()

            # Actual direction at 12PM
            actual_dir = "LONG" if price_12pm > session_open else "SHORT"

            # Did bias direction match?
            dir_correct = (
                result.direction.value == actual_dir
                if result.direction.value != "NONE"
                else None
            )

            # Did -25% target hit in bias direction by 12PM?
            asian_range = result.asian_range_pips
            if asian_range > 0 and result.direction.value == "LONG":
                target_25 = session_open + 0.25 * asian_range / 10000
                target_hit = high_12pm >= target_25
            elif asian_range > 0 and result.direction.value == "SHORT":
                target_25 = session_open - 0.25 * asian_range / 10000
                target_hit = low_12pm <= target_25
            else:
                target_hit = None

            # MFE in bias direction by 12PM
            if result.direction.value == "LONG":
                mfe = (high_12pm - session_open) * 10000
            elif result.direction.value == "SHORT":
                mfe = (session_open - low_12pm) * 10000
            else:
                mfe = 0

            results.append({
                "date": str(date),
                "state": result.state.value,
                "bias_direction": result.direction.value,
                "confidence": result.confidence,
                "regime_ratio": result.regime_ratio,
                "asian_range_pips": result.asian_range_pips,
                "actual_direction_12pm": actual_dir,
                "direction_correct_12pm": dir_correct,
                "target_25_hit_12pm": target_hit,
                "mfe_pips_12pm": round(mfe, 2),
                "lens_a": result.lens_a.value,
                "lens_b": result.lens_b.value,
                "lens_c": result.lens_c.value,
                "lens_a_time": result.lens_a_time,
                "lens_b_time": result.lens_b_time,
            })

    return pd.DataFrame(results)


def report(results: pd.DataFrame, symbol: str):
    """Generate accuracy report."""
    if len(results) == 0:
        print("No results!")
        return

    print("=" * 60)
    print(f"DIRECTIONAL BIAS BACKTEST — 12PM CUTOFF ({symbol})")
    print("=" * 60)
    print(f"\nTotal days: {len(results)}")

    # Days with a signal
    signaled = results[results["bias_direction"] != "NONE"]
    print(f"Days with bias signal: {len(signaled)}")

    if len(signaled) > 0:
        correct = signaled[signaled["direction_correct_12pm"] == True]
        acc = len(correct) / len(signaled) * 100
        print(f"Direction accuracy (12PM): {acc:.1f}%")

    # Target hit rate
    target_data = signaled[signaled["target_25_hit_12pm"].notna()]
    if len(target_data) > 0:
        hits = target_data[target_data["target_25_hit_12pm"] == True]
        hit_rate = len(hits) / len(target_data) * 100
        print(f"Target -25% hit rate (by 12PM): {hit_rate:.1f}% ({len(hits)}/{len(target_data)})")

    # MFE stats
    mfe_data = signaled[signaled["mfe_pips_12pm"] > 0]
    if len(mfe_data) > 0:
        print(f"\nMFE stats (when bias fires):")
        print(f"  Mean: {mfe_data['mfe_pips_12pm'].mean():.1f} pips")
        print(f"  Median: {mfe_data['mfe_pips_12pm'].median():.1f} pips")
        print(f"  25th: {mfe_data['mfe_pips_12pm'].quantile(0.25):.1f} pips")
        print(f"  75th: {mfe_data['mfe_pips_12pm'].quantile(0.75):.1f} pips")

    # By state
    print(f"\n── BY STATE ──")
    for state in results["state"].unique():
        sd = results[results["state"] == state]
        ss = sd[sd["bias_direction"] != "NONE"]
        if len(ss) > 0:
            sc = ss[ss["direction_correct_12pm"] == True]
            sa = len(sc) / len(ss) * 100
            sh = ss[ss["target_25_hit_12pm"] == True]
            hr = len(sh) / len(ss) * 100
            print(f"  {state}: {len(sd)} days, {len(ss)} signaled, "
                  f"dir_acc={sa:.1f}%, target_hit={hr:.1f}%")
        else:
            print(f"  {state}: {len(sd)} days, no signals")

    # By regime
    print(f"\n── BY REGIME ──")
    for regime in results["lens_c"].unique():
        rd = results[results["lens_c"] == regime]
        rs = rd[rd["bias_direction"] != "NONE"]
        if len(rs) > 0:
            rc = rs[rs["direction_correct_12pm"] == True]
            ra = len(rc) / len(rs) * 100
            print(f"  {regime}: {len(rd)} days, acc={ra:.1f}%")

    # Conflict analysis
    conflict = results[
        (results["lens_a"] != "NONE")
        & (results["lens_b"] != "NONE")
        & (results["lens_a"] != results["lens_b"])
    ]
    aligned = results[
        (results["lens_a"] != "NONE")
        & (results["lens_a"] == results["lens_b"])
    ]
    print(f"\n── LENS ANALYSIS ──")
    print(f"  A != B (conflict): {len(conflict)} days")
    print(f"  A == B (aligned): {len(aligned)} days")
    if len(aligned) > 0:
        ac = aligned[aligned["direction_correct_12pm"] == True]
        print(f"  A == B accuracy: {len(ac)/len(aligned)*100:.1f}%")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    for sym in ["EURUSD", "USDCHF"]:
        results = backtest_12pm(sym)
        if len(results) > 0:
            report(results, sym)
            results.to_csv(f"dtb_lab/bias_12pm_{sym}.csv", index=False)
