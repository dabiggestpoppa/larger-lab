"""
Markov Chain Local Run
======================
Uses Holy Grail priors as transition matrix.
Simulates weekly sequences to estimate outcome probabilities.
"""
import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from markov_chain_model import MarkovChainModel, STATES, STATE_IDX, N_STATES

OUTPUT_DIR = Path('ml/data/markov_results')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Build model from priors
model = MarkovChainModel(n_states=N_STATES, alpha=0.3)
print(f'Model initialized with {N_STATES} states')
print(f'Transition matrix shape: {model.transition_probs.shape}')

# Show top prior-based transitions
probs = []
for i in range(N_STATES):
    for j in range(N_STATES):
        p = model.transition_probs[i, j]
        if p > 0.01:
            probs.append((STATES[i], STATES[j], p))

print()
print('=' * 70)
print('HOLY GRAIL PRIOR TRANSITIONS (Top 30)')
print('=' * 70)
for s1, s2, p in sorted(probs, key=lambda x: -x[2])[:30]:
    print(f'  {s1:<20s} -> {s2:<20s}: {p:>6.1%}')

# Simulate weekly sequences
print()
print('Simulating 10,000 weekly sequences from priors...')

np.random.seed(42)
n_sims = 10000
max_steps = 25
outcomes = {}

for sim in range(n_sims):
    state = STATE_IDX["RESET"]
    for step in range(max_steps):
        probs_vec = model.transition_probs[state]
        probs_vec = np.maximum(probs_vec, 0)
        total_p = probs_vec.sum()
        if total_p <= 0:
            outcomes["DEAD_END"] = outcomes.get("DEAD_END", 0) + 1
            break
        probs_vec = probs_vec / total_p
        next_state = np.random.choice(N_STATES, p=probs_vec)
        s_name = STATES[next_state]
        if s_name in ("HARD_EXIT", "REKEY_EXTENSION", "REGIME_FLIP"):
            outcomes[s_name] = outcomes.get(s_name, 0) + 1
            break
        if s_name == "FAILURE" and step > 3:
            outcomes["FAILURE"] = outcomes.get("FAILURE", 0) + 1
            break
        state = next_state
    else:
        outcomes["INCOMPLETE"] = outcomes.get("INCOMPLETE", 0) + 1

total_sim = sum(outcomes.values())
print()
print('WEEKLY OUTCOMES (from Holy Grail priors):')
print('-' * 45)
for outcome, count in sorted(outcomes.items(), key=lambda x: -x[1]):
    print(f'  {outcome:<20s}: {count:>5,} ({count/total_sim:>5.1%})')

# Delivery analysis
print()
print('=' * 70)
print('EXTENSION DELIVERY ANALYSIS')
print('=' * 70)

p_t1 = 0.42
p_t2 = 0.38
p_t3 = 0.15

p_25 = p_t1 * 0.982 + p_t2 * 0.964 + p_t3 * 0.872
p_50 = p_25 * 0.964
p_100 = p_50 * 0.922
rekey_rate = p_50 * 0.715
dmr_rate = p_25 * 0.042

print(f'  P(hit -25% extension):  {p_25:>6.1%}')
print(f'  P(hit -50% extension):  {p_50:>6.1%}')
print(f'  P(hit -100% extension): {p_100:>6.1%}')
print(f'  P(rekey triggered):     {rekey_rate:>6.1%}')
print(f'  P(DMR deep state):      {dmr_rate:>6.1%}')
print(f'  P(failure before -25%): {1-p_25:>6.1%}')

# Save results
results = {
    'transition_probs': {f'{s1}->{s2}': round(p, 4) for s1, s2, p in probs},
    'simulation_outcomes': dict(outcomes),
    'delivery_analysis': {
        'p_hit_25': round(p_25, 4),
        'p_hit_50': round(p_50, 4),
        'p_hit_100': round(p_100, 4),
        'p_rekey': round(rekey_rate, 4),
        'p_dmr': round(dmr_rate, 4),
        'p_failure': round(1 - p_25, 4),
    },
    'n_simulations': n_sims,
}
out_file = OUTPUT_DIR / 'markov_local_results.json'
with open(out_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f'\nSaved to {out_file}')
