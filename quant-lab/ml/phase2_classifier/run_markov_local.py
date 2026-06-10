import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from markov_chain_model import MarkovChainModel, STATES, STATE_IDX
import json, pandas as pd, numpy as np

DATA_DIR = Path('ml/data/training')
OUTPUT_DIR = Path('ml/data/markov_results')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(DATA_DIR.glob('*_training.parquet'))
print(f'Found {len(files)} asset files')

all_data = {}
for f in files:
    symbol = f.stem.replace('_training', '')
    all_data[symbol] = pd.read_parquet(f)

model = MarkovChainModel(n_states=len(STATES), alpha=0.3)
print(f'Model initialized with {len(STATES)} states')

sequences = []
for symbol, df in all_data.items():
    seq = []
    for _, row in df.iterrows():
        state = STATE_IDX.get('RESET', 0)
        if 'label_25_delivery' in row.index:
            val = row.get('label_25_delivery')
            if pd.notna(val):
                state = STATE_IDX.get('TARGET_25', 6) if val == 1 else STATE_IDX.get('FAILURE', 14)
        if 'rekey_triggered' in row.index:
            val = row.get('rekey_triggered')
            if pd.notna(val) and val == 1:
                state = STATE_IDX.get('REKEY', 11)
        seq.append(state)
    if len(seq) > 10:
        sequences.append(seq)

print(f'Total sequences: {len(sequences)}')
model.fit(sequences)

probs = []
for i in range(len(STATES)):
    for j in range(len(STATES)):
        p = model.transition_probs[i, j]
        if p > 0.01:
            probs.append((STATES[i], STATES[j], p))

print()
print('=' * 70)
print('TRANSITION PROBABILITIES (Top 30)')
print('=' * 70)
for s1, s2, p in sorted(probs, key=lambda x: -x[2])[:30]:
    print(f'  {s1:<20s} -> {s2:<20s}: {p:>6.1%}')

print()
print('Simulating 10,000 weekly sequences...')
outcomes = model.simulate_weeks(n_simulations=10000)
total = sum(outcomes.values())
print()
print('WEEKLY OUTCOMES:')
for outcome, count in sorted(outcomes.items(), key=lambda x: -x[1]):
    print(f'  {outcome:<20s}: {count:>5,} ({count/total:>5.1%})')

results = {
    'transition_probs': {f'{s1}->{s2}': p for s1, s2, p in probs},
    'simulation_outcomes': dict(outcomes),
    'n_assets': len(all_data),
    'n_sequences': len(sequences),
}
with open(OUTPUT_DIR / 'markov_local_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)
out_path = OUTPUT_DIR / "markov_local_results.json"
print(f"Saved to {out_path}")