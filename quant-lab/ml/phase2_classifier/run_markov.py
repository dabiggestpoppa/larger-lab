"""
Run Markov Chain Model on Holy Grail data.
Learns state transition probabilities from actual price sequences.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter

# Import the model
import sys
sys.path.insert(0, str(Path(__file__).parent))
from markov_chain_model import MarkovChainModel, STATES, STATE_IDX, HOLY_GRAIL_PRIORS

DATA_DIR = Path("ml/data/training")
OUTPUT_DIR = Path("mlr_validation/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_state_sequences(df, symbol):
    """
    Extract state sequences from training data.
    Each week (Mon-Fri) is one sequence.
    """
    sequences = []
    current_seq = []

    # Group by week
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
        df = df.copy()
        df["week"] = ts.dt.isocalendar().week.values
        df["year"] = ts.dt.isocalendar().year.values
        df["dayofweek"] = ts.dt.dayofweek.values
    elif "date" in df.columns:
        ts = pd.to_datetime(df["date"])
        df = df.copy()
        df["week"] = ts.dt.isocalendar().week.values
        df["year"] = ts.dt.isocalendar().year.values
        df["dayofweek"] = ts.dt.dayofweek.values
    else:
        # Use row index as proxy
        df = df.copy()
        df["week"] = np.arange(len(df)) // 288  # ~288 M5 bars per day
        df["year"] = 0
        df["dayofweek"] = np.arange(len(df)) % 5

    for (year, week), week_df in df.groupby(["year", "week"]):
        seq = []
        for _, row in week_df.iterrows():
            state = classify_state(row, symbol)
            if state is not None:
                seq.append(STATE_IDX[state])

        if len(seq) >= 3:  # Need at least 3 states for a meaningful sequence
            sequences.append(seq)

    return sequences


def classify_state(row, symbol):
    """Classify a bar into a market state based on features."""
    # Determine direction
    direction = "bullish" if row.get("close", 0) > row.get("open", 0) else "bearish"

    # Check labels
    l25 = row.get("label_25_delivery", None)
    l50 = row.get("label_50_delivery", None)
    rekey = row.get("rekey_triggered", None)
    regime = row.get("regime_at_time", None)

    # Classify based on what's happened
    if rekey is not None and rekey == 1:
        return "REKEY"
    elif l25 is not None and l25 == -1:
        return "FAILURE"
    elif l50 is not None and l50 == 1:
        return "TARGET_50"
    elif l25 is not None and l25 == 1:
        return "TARGET_25"
    elif regime == "CONFIRMED":
        return "T1_ACTIVE"  # Simplified
    elif regime == "FAILED":
        return "FAILURE"
    else:
        return "AR_SET"  # Default


def main():
    print("=" * 70)
    print("MARKOV CHAIN MODEL — Training on Holy Grail Data")
    print("=" * 70)

    # Initialize model with Holy Grail priors
    model = MarkovChainModel()
    print("\nInitialized with {} states".format(len(STATES)))
    print("Holy Grail priors loaded: {} transitions".format(len([k for k in HOLY_GRAIL_PRIORS.keys() if isinstance(k, tuple)])))

    # Load all asset data
    files = sorted(DATA_DIR.glob("*_training.parquet"))
    print("Found {} asset files".format(len(files)))

    all_sequences = []
    asset_stats = {}

    for f in files:
        symbol = f.stem.replace("_training", "")
        df = pd.read_parquet(f)
        sequences = extract_state_sequences(df, symbol)
        all_sequences.extend(sequences)

        # Count state frequencies
        state_counts = Counter()
        for seq in sequences:
            for s in seq:
                state_counts[STATES[s]] += 1

        asset_stats[symbol] = {
            "n_sequences": len(sequences),
            "state_counts": dict(state_counts),
            "avg_seq_length": np.mean([len(s) for s in sequences]) if sequences else 0,
        }

        print("  {}: {} sequences, avg length {:.1f}".format(
            symbol, len(sequences), asset_stats[symbol]["avg_seq_length"]))

    print("\nTotal sequences: {}".format(len(all_sequences)))

    # Fit model
    print("\nFitting Markov Chain to observed sequences...")
    model.fit(all_sequences)

    # Print learned transition probabilities
    print("\n" + "=" * 70)
    print("LEARNED TRANSITION PROBABILITIES (Top transitions)")
    print("=" * 70)

    for i, from_state in enumerate(STATES):
        probs = model.transition_probs[i]
        top_idx = np.argsort(probs)[-3:][::-1]
        for j in top_idx:
            if probs[j] > 0.01:
                print("  {} -> {}: {:.1%}".format(from_state, STATES[j], probs[j]))

    # Compare to Holy Grail priors
    print("\n" + "=" * 70)
    print("COMPARISON: Learned vs Holy Grail Priors")
    print("=" * 70)

    comparisons = [
        (("AR_SET", "P90_FIRED"), "AR_SET -> P90_FIRED"),
        (("T1_ACTIVE", "TARGET_25"), "T1 -> -25%"),
        (("T2_ACTIVE", "TARGET_25"), "T2 -> -25%"),
        (("TARGET_25", "TARGET_50"), "-25% -> -50%"),
        (("TARGET_50", "REKEY"), "-50% -> 132% rekey"),
        (("REKEY", "REKEY_CONSOLID"), "REKEY -> CONSOLID"),
        (("FAILURE", "HARD_EXIT"), "FAILURE -> HARD_EXIT"),
    ]

    for (from_s, to_s), label in comparisons:
        if from_s in STATE_IDX and to_s in STATE_IDX:
            i, j = STATE_IDX[from_s], STATE_IDX[to_s]
            learned = model.transition_probs[i, j]
            prior_key = (from_s, to_s)
            prior = HOLY_GRAIL_PRIORS.get(prior_key, "N/A")
            if isinstance(prior, float):
                print("  {}: Prior={:.1%} | Learned={:.1%} | Diff={:+.1%}".format(
                    label, prior, learned, learned - prior))
            else:
                print("  {}: Prior={} | Learned={:.1%}".format(label, prior, learned))

    # Save model
    model_data = {
        "transition_probs": model.transition_probs.tolist(),
        "transition_counts": model.transition_counts.tolist(),
        "state_counts": model.state_counts.tolist(),
        "states": STATES,
        "n_sequences_trained": len(all_sequences),
        "asset_stats": asset_stats,
    }

    with open(OUTPUT_DIR / "markov_chain_model.json", "w") as f:
        json.dump(model_data, f, indent=2, default=str)

    print("\nModel saved to {}".format(OUTPUT_DIR / "markov_chain_model.json"))

    # Generate predictions for each asset
    print("\n" + "=" * 70)
    print("STATE DISTRIBUTION BY ASSET")
    print("=" * 70)

    for symbol in sorted(asset_stats.keys()):
        stats = asset_stats[symbol]
        counts = stats["state_counts"]
        total = sum(counts.values()) if counts else 0
        if total == 0:
            continue

        top_states = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        line = "{}: ".format(symbol)
        line += " | ".join(["{}={:.0%}".format(s, c/total) for s, c in top_states])
        print(line)


if __name__ == "__main__":
    main()
