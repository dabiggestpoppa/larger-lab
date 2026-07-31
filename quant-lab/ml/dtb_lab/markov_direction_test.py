"""
Markov Chain Direction Prediction Test
=======================================
Uses the existing MarkovChainModel to predict directional bias.
Tests whether Markov state probabilities can improve direction accuracy
beyond the current 69-78% from the 3-Lens Ternary system.

The Markov model predicts P(next_state | current_state, features).
We use it to predict P(TARGET_25 | AR_SET, tier, regime, time) as a
direction confidence score.
"""
import sys, os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from dtb_lab.directional_bias import DirectionalBias, BiasDirection

# Add phase2_classifier to path for Markov model
sys.path.insert(0, str(Path(__file__).parent.parent / "phase2_classifier"))
from markov_chain_model import MarkovChainModel, STATES, STATE_IDX, extract_state_sequences

RAW_DATA_DIR = Path("../data")


def test_markov_direction(symbol: str = "EURUSD") -> pd.DataFrame:
    """
    Test Markov chain direction prediction.

    For each trading day:
    1. Extract the state sequence from price data
    2. At each checkpoint (3AM, 6AM, 9AM), get P(TARGET_25 | current_state)
    3. Use this as a direction confidence score
    4. Compare against actual outcome
    """
    p = RAW_DATA_DIR / f"{symbol}_M5.csv"
    if not p.exists():
        print(f"SKIP {symbol}: no data")
        return pd.DataFrame()

    df = pd.read_csv(p)
    df['dt'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
    df = df.dropna(subset=['dt']).set_index('dt').sort_index()
    df['est_hour'] = (df.index.hour - 5) % 24
    df['trade_date'] = df.index.date

    # Initialize Markov model (uses Holy Grail priors)
    markov = MarkovChainModel()

    # Also initialize the 3-Lens Bias system for comparison
    bias = DirectionalBias()

    results = []
    for date, day_bars in df.groupby("trade_date"):
        if len(day_bars) < 50:
            continue

        bars_12pm = day_bars[day_bars.index.hour < 17]
        if len(bars_12pm) < 20:
            continue

        # ── 3-Lens Bias evaluation ──
        bias_result = bias.evaluate(bars_12pm, symbol)
        if bias_result.direction == BiasDirection.NONE:
            continue

        # ── Markov direction prediction ──
        # Get the current state at each checkpoint
        # Map the bias system's tier to Markov tier
        tier = 1
        if bias_result.asian_range_pips >= 30:
            tier = 3
        elif bias_result.asian_range_pips >= 20:
            tier = 2

        # Markov prediction at 9AM (hour_est = 14 UTC = 9AM EST)
        # From AR_SET state, what's P(TARGET_25)?
        ar_set_idx = STATE_IDX["AR_SET"]
        target_25_idx = STATE_IDX["TARGET_25"]

        # Get P(next_state | AR_SET) at 9AM
        markov_probs_9am = markov.predict_next_state(
            ar_set_idx,
            features={"tier": tier, "hour_est": 9, "day_of_week": 0, "regime": "CONFIRMED"}
        )
        p_target_25_9am = markov_probs_9am[target_25_idx]

        # Also get P(next_state | P90_FIRED) at 9AM
        p90_idx = STATE_IDX["P90_FIRED"]
        markov_probs_p90 = markov.predict_next_state(
            p90_idx,
            features={"tier": tier, "hour_est": 9, "day_of_week": 0, "regime": "CONFIRMED"}
        )
        p_target_25_from_p90 = markov_probs_p90[target_25_idx]

        # ── Actual outcome ──
        session_open = bars_12pm.iloc[0]["open"]
        price_12pm = bars_12pm.iloc[-1]["close"]
        high_12pm = bars_12pm["high"].max()
        low_12pm = bars_12pm["low"].min()

        if bias_result.direction == BiasDirection.LONG:
            mfe = (high_12pm - session_open) * 10000
            target_hit = high_12pm >= session_open + 0.25 * bias_result.asian_range_pips / 10000
        else:
            mfe = (session_open - low_12pm) * 10000
            target_hit = low_12pm <= session_open - 0.25 * bias_result.asian_range_pips / 10000

        dir_correct = (
            (bias_result.direction == BiasDirection.LONG and price_12pm > session_open)
            or (bias_result.direction == BiasDirection.SHORT and price_12pm < session_open)
        )

        results.append({
            "date": str(date),
            "bias_state": bias_result.state.value,
            "bias_direction": bias_result.direction.value,
            "bias_confidence": bias_result.confidence,
            "markov_p_target25_from_ar": round(p_target_25_9am, 4),
            "markov_p_target25_from_p90": round(p_target_25_from_p90, 4),
            "regime_ratio": bias_result.regime_ratio,
            "asian_range_pips": bias_result.asian_range_pips,
            "actual_mfe": round(mfe, 2),
            "target_hit": target_hit,
            "direction_correct": 1 if dir_correct else 0,
        })

    return pd.DataFrame(results)


def report(results: pd.DataFrame, symbol: str):
    """Generate Markov direction report."""
    if len(results) == 0:
        print("No results!")
        return

    print("=" * 60)
    print(f"MARKOV DIRECTION PREDICTION TEST ({symbol})")
    print("=" * 60)
    print(f"\nTotal days: {len(results)}")

    # Baseline (3-Lens Bias only)
    correct = results[results["direction_correct"] == 1]
    baseline_acc = len(correct) / len(results) * 100
    print(f"\n3-Lens Bias accuracy: {baseline_acc:.1f}%")

    # Markov confidence analysis
    print(f"\n── MARKOV P(TARGET_25) DISTRIBUTION ──")
    p_ar = results["markov_p_target25_from_ar"]
    p_p90 = results["markov_p_target25_from_p90"]
    print(f"  From AR_SET:  mean={p_ar.mean():.4f}, std={p_ar.std():.4f}")
    print(f"  From P90:     mean={p_p90.mean():.4f}, std={p_p90.std():.4f}")

    # Accuracy by Markov confidence buckets
    print(f"\n── ACCURACY BY MARKOV CONFIDENCE (from P90) ──")
    for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        above = results[results["markov_p_target25_from_p90"] >= threshold]
        if len(above) > 0:
            correct_above = above[above["direction_correct"] == 1]
            acc = len(correct_above) / len(above) * 100
            print(f"  P >= {threshold:.1f}: {len(above):4d} days, acc={acc:.1f}%")

    # Combined: 3-Lens + Markov
    print(f"\n── COMBINED (3-Lens + Markov) ──")
    for threshold in [0.0, 0.1, 0.2, 0.3]:
        mask = results["markov_p_target25_from_p90"] >= threshold
        filtered = results[mask]
        if len(filtered) > 0:
            correct_f = filtered[filtered["direction_correct"] == 1]
            acc = len(correct_f) / len(filtered) * 100
            target_hits = filtered[filtered["target_hit"] == True]
            hit_rate = len(target_hits) / len(filtered) * 100
            print(f"  Markov P >= {threshold:.1f}: {len(filtered):4d} days, "
                  f"dir_acc={acc:.1f}%, target_hit={hit_rate:.1f}%")

    # By bias state
    print(f"\n── BY BIAS STATE ──")
    for state in results["bias_state"].unique():
        sd = results[results["bias_state"] == state]
        sc = sd[sd["direction_correct"] == 1]
        acc = len(sc) / len(sd) * 100 if len(sd) > 0 else 0
        mean_p = sd["markov_p_target25_from_p90"].mean()
        print(f"  {state}: {len(sd)} days, acc={acc:.1f}%, "
              f"mean_markov_p={mean_p:.4f}")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    for sym in ["EURUSD", "USDCHF"]:
        results = test_markov_direction(sym)
        if len(results) > 0:
            report(results, sym)
            results.to_csv(f"dtb_lab/markov_direction_{sym}.csv", index=False)
