"""
Run Markov Chain Model Locally
================================
Learns state transition probabilities from training data.
Uses Holy Grail priors + actual data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from markov_chain_model import MarkovChainModel, HOLY_GRAIL_PRIORS, STATES
import json
import pandas as pd

DATA_DIR = Path("ml/data/training")
OUTPUT_DIR = Path("ml/data/markov_results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load all data
files = sorted(DATA_DIR.glob("*_training.parquet"))
print(f"Found {len(files)} asset files")

all_data = {}
for f in files:
    symbol = f.stem.replace("_training", "")
    df = pd.read_parquet(f)
    all_data[symbol] = df
    print(f"  {symbol}: {len(df):,} rows")

# Initialize model with Holy Grail priors
model = MarkovChainModel(
    states=STATES,
    prior_probs=HOLY_GRAIL_PRIORS,
    learning_rate=0.3,  # 70% learned, 30% prior
)

# Learn from data
print("\nLearning transition probabilities from data...")
for symbol, df in all_data.items():
    model.learn_from_dataframe(df, symbol)

# Print results
print("\n" + "=" * 70)
print("MARKOV CHAIN TRANSITION PROBABILITIES")
print("=" * 70)

probs = model.get_transition_probs()
for (s1, s2), prob in sorted(probs.items(), key=lambda x: -x[1]):
    if prob > 0.01:
        print(f"  {s1:<20s} → {s2:<20s}: {prob:>6.1%}")

# Simulate
print("\nSimulating 10,000 weekly sequences...")
outcomes = model.simulate_weeks(n_simulations=10000)
total = sum(outcomes.values())
print("\nWEEKLY DELIVERY OUTCOMES:")
for outcome, count in sorted(outcomes.items(), key=lambda x: -x[1]):
    print(f"  {outcome:<20s}: {count:>5,} ({count/total:>5.1%})")

# Save
results = {
    "transition_probs": {f"{s1}→{s2}": p for (s1, s2), p in probs.items()},
    "simulation_outcomes": dict(outcomes),
    "n_assets": len(all_data),
}
with open(OUTPUT_DIR / "markov_local_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nSaved to {OUTPUT_DIR / 'markov_local_results.json'}")
