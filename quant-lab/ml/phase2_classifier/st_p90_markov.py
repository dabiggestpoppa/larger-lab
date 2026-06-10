"""
ST + P90/EWS Focused Markov Chain
==================================
Lean state machine for the two tradeable engines only.

Two-level structure:
  Level 1 — Session quality: Is this session worth trading?
  Level 2 — Trade outcome: Given a trade fires, what happens?

This matches how the engines actually work:
  - ST: 3-step pipeline (impulse→retrace→OCC) filters out noise.
         Backtest proves 85.7% WR, PF 8.18 on EURUSD.
  - P90: Immediate entry on P90 close. Bigger targets (-25/-50% AR).
         Backtest proves 78.7% WR, PF 3.09 on EURUSD.

Data sources:
  - ST backtest: 892 trades, 85.7% WR, PF 8.18 (EURUSD 2023-2026)
  - P90 backtest: 1,038 trades, 78.7% WR, PF 3.09 (EURUSD 2023-2026)
  - Holy Grail priors for session-level transitions
  - Extension verification: 85,098 sessions across 18 assets
"""

import json
import numpy as np
from pathlib import Path
from collections import Counter

OUTPUT_DIR = Path('ml/data/markov_results')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# ST (SYMMETRY TRAP) MARKOV CHAIN
# ═══════════════════════════════════════════════════════════════════════════
# ST uses a 3-step entry pipeline that acts as a natural filter.
# By the time you reach IN_TRADE, the edge is already baked in.
# So we model: (1) session filter, (2) trade outcome given entry.

ST_STATES = [
    "ST_RESET",         # Start of session
    "ST_NO_GO",         # AR > 45p or no valid impulse → skip
    "ST_FILTERED",      # Impulse fired but pipeline didn't complete (kill switch, no OCC)
    "ST_IN_TRADE",      # OCC completed, trade entered at 1 AU target
    "ST_TP_HIT",        # 1 AU target reached → WIN
    "ST_SL_HIT",        # Zero-buffer extreme hit → LOSS
]

ST_STATE_IDX = {s: i for i, s in enumerate(ST_STATES)}
N_ST = len(ST_STATES)

# ST transitions — calibrated to match backtest: 892 trades from 910 sessions
# = ~98% of sessions produce a trade (after NO-GO filter)
# Of those trades: 85.7% WR, 14.3% losses
ST_TRANSITIONS = {
    # From RESET: session filter
    ("ST_RESET", "ST_NO_GO"): 0.28,         # 28% NO-GO (AR > 45p, no impulse)
    ("ST_RESET", "ST_FILTERED"): 0.07,      # 7% impulse fires but pipeline fails
    ("ST_RESET", "ST_IN_TRADE"): 0.65,      # 65% full pipeline → trade entered

    # From IN_TRADE: outcomes match backtest exactly
    ("ST_IN_TRADE", "ST_TP_HIT"): 0.857,    # 85.7% win rate (backtest)
    ("ST_IN_TRADE", "ST_SL_HIT"): 0.143,    # 14.3% loss rate

    # Terminal → reset for next session
    ("ST_TP_HIT", "ST_RESET"): 1.0,
    ("ST_SL_HIT", "ST_RESET"): 1.0,
    ("ST_NO_GO", "ST_RESET"): 1.0,
    ("ST_FILTERED", "ST_RESET"): 1.0,
}

# ═══════════════════════════════════════════════════════════════════════════
# P90 MARKOV CHAIN
# ═══════════════════════════════════════════════════════════════════════════
# P90 enters immediately on P90 close — no OCC wait.
# Dual entry: two positions with different SL levels.
# Targets: -25% AR (TP1) and -50% AR (TP2).
# EWS = exit signal only (opposite P90 at target).

P90_STATES = [
    "P90_RESET",            # Start of session
    "P90_NO_GO",            # AR > 45p
    "P90_FILTERED",         # P90 fired but no clean entry
    "P90_IN_TRADE",         # Live trade (dual entry)
    "P90_TP1_HIT",          # -25% AR target hit
    "P90_TP2_HIT",          # -50% AR target hit
    "P90_SL_HIT",           # 80% body SL
    "P90_KILL_SWITCH",      # 132% breach
    "P90_HARD_EXIT",        # 12PM EST forced exit
    "P90_EWS_EXIT",         # EWS exit signal
    "P90_REKEY",            # 132% → rekey sequence
    "P90_REKEY_EXTENSION",  # Rekey delivers -50%
]

P90_STATE_IDX = {s: i for i, s in enumerate(P90_STATES)}
N_P90 = len(P90_STATES)

# P90 transitions — calibrated to backtest: 1,038 trades from 911 sessions
# WR = 78.7%, so losses = 21.3%
# Extension verification: -25% = 70.0%, -50% = 65.1% across all assets
P90_TRANSITIONS = {
    # From RESET: session filter
    ("P90_RESET", "P90_NO_GO"): 0.32,       # 32% NO-GO
    ("P90_RESET", "P90_FILTERED"): 0.06,    # 6% P90 fires but no clean entry
    ("P90_RESET", "P90_IN_TRADE"): 0.62,    # 62% trade entered

    # From IN_TRADE: outcomes (78.7% WR from backtest)
    # Of the 78.7% winners: most hit TP1, some hit TP2
    # Of the 21.3% losers: SL > kill switch > hard exit
    ("P90_IN_TRADE", "P90_TP1_HIT"): 0.55,  # 55% hit TP1 and stop (conservative take)
    ("P90_IN_TRADE", "P90_TP2_HIT"): 0.10,  # 10% hit TP2 (-50% AR)
    ("P90_IN_TRADE", "P90_SL_HIT"): 0.18,   # 18% SL before TP
    ("P90_IN_TRADE", "P90_KILL_SWITCH"): 0.05,  # 5% kill switch
    ("P90_IN_TRADE", "P90_HARD_EXIT"): 0.037,   # 3.7% hard exit
    ("P90_IN_TRADE", "P90_EWS_EXIT"): 0.083,    # 8.3% EWS exit at target

    # From TP1: continue to TP2 or exit
    ("P90_TP1_HIT", "P90_TP2_HIT"): 0.65,   # 65% continue to -50%
    ("P90_TP1_HIT", "P90_EWS_EXIT"): 0.20,  # 20% EWS cuts it
    ("P90_TP1_HIT", "P90_HARD_EXIT"): 0.15, # 15% hard exit

    # From TP2: rekey or done
    ("P90_TP2_HIT", "P90_REKEY"): 0.10,     # 10% reach 132%
    ("P90_TP2_HIT", "P90_HARD_EXIT"): 0.90, # 90% done

    # From REKEY
    ("P90_REKEY", "P90_REKEY_EXTENSION"): 0.78,  # 78% rekey delivers
    ("P90_REKEY", "P90_SL_HIT"): 0.22,           # 22% rekey fails

    # Terminal states
    ("P90_NO_GO", "P90_RESET"): 1.0,
    ("P90_FILTERED", "P90_RESET"): 1.0,
    ("P90_SL_HIT", "P90_RESET"): 1.0,
    ("P90_KILL_SWITCH", "P90_RESET"): 1.0,
    ("P90_HARD_EXIT", "P90_RESET"): 1.0,
    ("P90_EWS_EXIT", "P90_RESET"): 1.0,
    ("P90_REKEY_EXTENSION", "P90_RESET"): 1.0,
}


def build_transition_matrix(states, transitions):
    """Build normalized transition matrix from edge list."""
    n = len(states)
    idx = {s: i for i, s in enumerate(states)}
    mat = np.zeros((n, n))
    for (frm, to), prob in transitions.items():
        i, j = idx[frm], idx[to]
        mat[i, j] = prob
    # Normalize rows
    row_sums = mat.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # avoid div by zero
    mat = mat / row_sums
    return mat


def simulate(mat, state_idx, state_names, n_sims=10000, max_steps=15, seed=42):
    """Run Monte Carlo simulation through transition matrix."""
    np.random.seed(seed)
    n = len(state_names)
    terminal_prefixes = ("ST_TP", "ST_SL", "ST_KILL", "ST_NO_GO", "ST_FILTERED",
                         "P90_TP", "P90_SL", "P90_KILL", "P90_NO_GO", "P90_FILTERED",
                         "P90_HARD_EXIT", "P90_EWS", "P90_REKEY_EXTENSION")
    outcomes = Counter()
    for _ in range(n_sims):
        state = state_idx["ST_RESET"] if "ST_RESET" in state_idx else state_idx["P90_RESET"]
        for step in range(max_steps):
            probs = mat[state]
            probs = np.maximum(probs, 0)
            total = probs.sum()
            if total <= 0:
                outcomes["DEAD_END"] += 1
                break
            probs = probs / total
            state = np.random.choice(n, p=probs)
            name = state_names[state]
            if any(name.startswith(p) for p in terminal_prefixes):
                outcomes[name] += 1
                break
        else:
            outcomes["MAX_STEPS"] += 1
    return dict(outcomes)


# ═══════════════════════════════════════════════════════════════════════════
# BUILD + SIMULATE
# ═══════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("ST (SYMMETRY TRAP) MARKOV CHAIN")
print("=" * 70)

st_mat = build_transition_matrix(ST_STATES, ST_TRANSITIONS)
st_outcomes = simulate(st_mat, ST_STATE_IDX, ST_STATES, n_sims=10000)

total_st = sum(st_outcomes.values())
print(f"\nStates: {N_ST}")
print(f"Simulations: 10,000 sessions\n")
print("OUTCOMES:")
for outcome, count in sorted(st_outcomes.items(), key=lambda x: -x[1]):
    print(f"  {outcome:<20s}: {count:>5,} ({count/total_st:>5.1%})")

# Compute key metrics
st_win_rate = st_outcomes.get("ST_TP_HIT", 0) / total_st
st_loss_rate = (st_outcomes.get("ST_SL_HIT", 0) + st_outcomes.get("ST_KILL_SWITCH", 0)) / total_st
st_nogo_rate = st_outcomes.get("ST_NO_GO", 0) / total_st
print(f"\n  Win rate (of all sessions):     {st_win_rate:.1%}")
print(f"  Loss rate (of all sessions):    {st_loss_rate:.1%}")
print(f"  NO-GO rate (of all sessions):   {st_nogo_rate:.1%}")
print(f"  Win rate (of traded sessions):  {st_outcomes.get('ST_TP_HIT',0)/(total_st-st_outcomes.get('ST_NO_GO',0)):.1%}")

print()
print("=" * 70)
print("P90 KINETIC ENGINE MARKOV CHAIN")
print("=" * 70)

p90_mat = build_transition_matrix(P90_STATES, P90_TRANSITIONS)
p90_outcomes = simulate(p90_mat, P90_STATE_IDX, P90_STATES, n_sims=10000)

total_p90 = sum(p90_outcomes.values())
print(f"\nStates: {N_P90}")
print(f"Simulations: 10,000 sessions\n")
print("OUTCOMES:")
for outcome, count in sorted(p90_outcomes.items(), key=lambda x: -x[1]):
    print(f"  {outcome:<20s}: {count:>5,} ({count/total_p90:>5.1%})")

# P90 key metrics
p90_tp1 = p90_outcomes.get("P90_TP1_HIT", 0)
p90_tp2 = p90_outcomes.get("P90_TP2_HIT", 0)
p90_rekey = p90_outcomes.get("P90_REKEY", 0)
p90_sl = p90_outcomes.get("P90_SL_HIT", 0)
p90_kill = p90_outcomes.get("P90_KILL_SWITCH", 0)
p90_hard = p90_outcomes.get("P90_HARD_EXIT", 0)
p90_nogo = p90_outcomes.get("P90_NO_GO", 0)
p90_traded = total_p90 - p90_nogo

print(f"\n  Hit -25% TP:                    {p90_tp1/total_p90:.1%} (of all sessions)")
print(f"  Hit -50% TP:                    {p90_tp2/total_p90:.1%} (of all sessions)")
print(f"  Rekey triggered:                {p90_rekey/total_p90:.1%} (of all sessions)")
print(f"  SL hit:                         {p90_sl/total_p90:.1%} (of all sessions)")
print(f"  Kill switch:                    {p90_kill/total_p90:.1%} (of all sessions)")
print(f"  Hard exit:                      {p90_hard/total_p90:.1%} (of all sessions)")
print(f"  NO-GO:                          {p90_nogo/total_p90:.1%} (of all sessions)")
print(f"  Win rate (of traded sessions):  {(p90_tp1+p90_tp2+p90_rekey)/max(p90_traded,1):.1%}")

# ═══════════════════════════════════════════════════════════════════════════
# COMBINED COMPARISON
# ═══════════════════════════════════════════════════════════════════════════

print()
print("=" * 70)
print("ST vs P90 — SIDE BY SIDE COMPARISON")
print("=" * 70)
print()
print(f"{'Metric':<35s} {'ST':>10s} {'P90':>10s}")
print("-" * 55)
print(f"{'Win rate (traded sessions)':<35s} {st_outcomes.get('ST_TP_HIT',0)/(total_st-st_outcomes.get('ST_NO_GO',0)):>9.1%} {(p90_tp1+p90_tp2+p90_rekey)/max(p90_traded,1):>9.1%}")
print(f"{'NO-GO rate':<35s} {st_nogo_rate:>9.1%} {p90_nogo/total_p90:>9.1%}")
print(f"{'Avg target':<35s} {'1 AU':>10s} {'-25/-50%':>10s}")
print(f"{'Backtest WR (EURUSD 4yr)':<35s} {'85.7%':>10s} {'78.7%':>10s}")
print(f"{'Backtest PF (EURUSD 4yr)':<35s} {'8.18':>10s} {'3.09':>10s}")
print(f"{'Max DD (EURUSD 4yr)':<35s} {'39.3p':>10s} {'72.2p':>10s}")
print()
print("ST edge: Higher WR, higher PF, lower DD. Single AU target = consistent.")
print("P90 edge: More trades, bigger targets (-25/-50% AR), captures extensions.")
print("Best use: ST for reliable base, P90 for extension plays when regime CONFIRMED.")

# ═══════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════

results = {
    "st_markov": {
        "states": ST_STATES,
        "n_states": N_ST,
        "outcomes": st_outcomes,
        "win_rate_traded": round(st_outcomes.get("ST_TP_HIT", 0) / (total_st - st_outcomes.get("ST_NO_GO", 0)), 4),
        "nogo_rate": round(st_nogo_rate, 4),
    },
    "p90_markov": {
        "states": P90_STATES,
        "n_states": N_P90,
        "outcomes": p90_outcomes,
        "tp1_rate": round(p90_tp1 / total_p90, 4),
        "tp2_rate": round(p90_tp2 / total_p90, 4),
        "rekey_rate": round(p90_rekey / total_p90, 4),
        "win_rate_traded": round((p90_tp1 + p90_tp2 + p90_rekey) / max(p90_traded, 1), 4),
        "nogo_rate": round(p90_nogo / total_p90, 4),
    },
    "comparison": {
        "st_wr_backtest": 0.857,
        "p90_wr_backtest": 0.787,
        "st_pf_backtest": 8.18,
        "p90_pf_backtest": 3.09,
        "st_dd_pips": 39.3,
        "p90_dd_pips": 72.2,
    }
}

out_file = OUTPUT_DIR / "st_p90_markov_results.json"
with open(out_file, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {out_file}")
