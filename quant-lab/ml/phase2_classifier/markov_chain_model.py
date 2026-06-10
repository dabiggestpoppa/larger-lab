"""
Markov Chain Market State Model
================================
Learns state transition probabilities from Holy Grail data + price sequences.

States (from Holy Grail ontology):
  S0:  RESET           — Monday start, no position
  S1:  AR_SET          — Asian Range established (19:00-03:00 EST)
  S2:  P90_FIRED       — First P90 impulse (03:00-11:00 EST)
  S3:  T1_ACTIVE       — T1 tier trade active (<20p AR)
  S4:  T2_ACTIVE       — T2 tier trade active (20-30p AR)
  S5:  T3_ACTIVE       — T3 tier trade active (30-45p AR)
  S6:  TARGET_25       — -25% extension hit
  S7:  TARGET_50       — -50% extension hit
  S8:  TARGET_100      — -100% extension hit
  S9:  STALL_ZONE      — 168% stall zone reached
  S10: DEEP_STATE      — 200% deep state reached (DMR trigger)
  S11: REKEY           — 132% kill-switch violation
  S12: REKEY_CONSOLID  — 50% rekey consolidation (12-24h post-violation)
  S13: REKEY_EXTENSION — -50% rekey target delivery
  S14: FAILURE         — Price closed back inside Asian band
  S15: HARD_EXIT       — 12PM EST forced exit
  S16: REGIME_FLIP     — Full direction reversal confirmed

Transitions learned from data (not hardcoded).
"""

from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# STATE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

STATES = [
    "RESET", "AR_SET", "P90_FIRED", "T1_ACTIVE", "T2_ACTIVE", "T3_ACTIVE",
    "TARGET_25", "TARGET_50", "TARGET_100", "STALL_ZONE", "DEEP_STATE",
    "REKEY", "REKEY_CONSOLID", "REKEY_EXTENSION", "FAILURE", "HARD_EXIT",
    "REGIME_FLIP"
]

STATE_IDX = {s: i for i, s in enumerate(STATES)}
N_STATES = len(STATES)


# ═══════════════════════════════════════════════════════════════════════════
# HOLY GRAIL PRIOR PROBABILITIES (from extracted data)
# ═══════════════════════════════════════════════════════════════════════════

# These are the known transition probabilities from the Holy Grail.
# The model will learn to refine these from actual price data.

HOLY_GRAIL_PRIORS = {
    # From AR_SET
    ("AR_SET", "P90_FIRED"): 0.95,      # 95% of sessions get a P90
    ("AR_SET", "RESET"): 0.05,           # 5% no P90 (NO-GO sessions)

    # From P90_FIRED → Tier classification
    ("P90_FIRED", "T1_ACTIVE"): 0.42,    # ~42% are T1 (<20p AR)
    ("P90_FIRED", "T2_ACTIVE"): 0.38,    # ~38% are T2 (20-30p AR)
    ("P90_FIRED", "T3_ACTIVE"): 0.15,    # ~15% are T3 (30-45p AR)
    ("P90_FIRED", "FAILURE"): 0.05,     # ~5% immediate failure

    # From T1_ACTIVE
    ("T1_ACTIVE", "TARGET_25"): 0.982,   # 98.2% hit -25% (from Holy Grail)
    ("T1_ACTIVE", "STALL_ZONE"): 0.342,  # 34.2% reach stall zone
    ("T1_ACTIVE", "FAILURE"): 0.018,     # 1.8% fail before -25%

    # From T2_ACTIVE
    ("T2_ACTIVE", "TARGET_25"): 0.964,   # 96.4% hit -25%
    ("T2_ACTIVE", "STALL_ZONE"): 0.354,  # 35.4% reach stall zone
    ("T2_ACTIVE", "FAILURE"): 0.036,     # 3.6% fail

    # From T3_ACTIVE
    ("T3_ACTIVE", "TARGET_25"): 0.872,   # 87.2% hit -25%
    ("T3_ACTIVE", "STALL_ZONE"): 0.382,  # 38.2% reach stall zone
    ("T3_ACTIVE", "FAILURE"): 0.128,     # 12.8% fail

    # From TARGET_25
    ("TARGET_25", "TARGET_50"): 0.964,   # 96.4% continue to -50%
    ("TARGET_25", "STALL_ZONE"): 0.342,  # 34.2% stall at 168%
    ("TARGET_25", "DEEP_STATE"): 0.042,  # 4.2% reach 200% (DMR)
    ("TARGET_25", "HARD_EXIT"): 0.038,   # 3.8% hard exit before further

    # From TARGET_50
    ("TARGET_50", "TARGET_100"): 0.922,  # 92.2% continue to -100%
    ("TARGET_50", "REKEY"): 0.715,       # 71.5% eventually hit 132%
    ("TARGET_50", "HARD_EXIT"): 0.078,   # 7.8% hard exit

    # From STALL_ZONE
    ("STALL_ZONE", "DEEP_STATE"): 0.144,  # 14.4% deep violation
    ("STALL_ZONE", "TARGET_50"): 0.642,  # 64.2% revert (true rejection)
    ("STALL_ZONE", "FAILURE"): 0.214,    # 21.4% shallow violation

    # From DEEP_STATE (DMR)
    ("DEEP_STATE", "REKEY"): 0.95,       # 95% trigger rekey
    ("DEEP_STATE", "FAILURE"): 0.05,     # 5% fail

    # From REKEY
    ("REKEY", "REKEY_CONSOLID"): 0.85,   # 85% consolidate at 50%
    ("REKEY", "REGIME_FLIP"): 0.15,      # 15% full regime flip

    # From REKEY_CONSOLID
    ("REKEY_CONSOLID", "REKEY_EXTENSION"): 0.78,  # 78% deliver -50% extension
    ("REKEY_CONSOLID", "FAILURE"): 0.22,          # 22% fail

    # From FAILURE
    ("FAILURE", "HARD_EXIT"): 0.452,     # 45.2% end in compression
    ("FAILURE", "REGIME_FLIP"): 0.548,   # 54.8% second acceptance

    # Day-of-week modifiers (multipliers on base probabilities)
    # From Holy Grail: Tue/Wed strongest, Thu bifurcation, Fri mixed
    "day_modifiers": {
        0: {"TARGET_25": 0.98, "TARGET_50": 0.96, "REKEY": 0.70},  # Monday
        1: {"TARGET_25": 0.99, "TARGET_50": 0.97, "REKEY": 0.68},  # Tuesday (strongest)
        2: {"TARGET_25": 0.98, "TARGET_50": 0.96, "REKEY": 0.72},  # Wednesday
        3: {"TARGET_25": 0.95, "TARGET_50": 0.93, "REKEY": 0.80},  # Thursday (bifurcation)
        4: {"TARGET_25": 0.97, "TARGET_50": 0.95, "REKEY": 0.65},  # Friday
    },

    # Tier modifiers
    "tier_modifiers": {
        1: {"TARGET_25": 1.0, "TARGET_50": 1.0, "STALL": 0.30, "DMR": 0.04},   # T1
        2: {"TARGET_25": 0.98, "TARGET_50": 0.97, "STALL": 0.35, "DMR": 0.05},  # T2
        3: {"TARGET_25": 0.92, "TARGET_50": 0.88, "STALL": 0.38, "DMR": 0.08},  # T3
    },

    # Session modifiers (EST hour)
    "session_modifiers": {
        "2-4am":  {"expansion_wr": 0.942, "stall_rate": 0.311},
        "4-7am":  {"expansion_wr": 0.886, "stall_rate": 0.354},
        "7-11am": {"expansion_wr": 0.824, "stall_rate": 0.382},
    }
}


class MarkovChainModel:
    """
    Markov Chain model for market state transitions.
    
    Learns P(next_state | current_state, features) from data.
    Uses Holy Grail priors as initialization, then refines from actual sequences.
    """

    def __init__(self, n_states: int = N_STATES, alpha: float = 0.1):
        self.n_states = n_states
        self.alpha = alpha  # Learning rate for updating priors

        # Transition count matrix (observed transitions)
        self.transition_counts = np.ones((n_states, n_states))  # Laplace smoothing

        # Transition probability matrix
        self.transition_probs = np.ones((n_states, n_states)) / n_states

        # Feature-conditional transitions: P(next_state | current_state, feature_bucket)
        self.feature_transitions: Dict[str, np.ndarray] = {}

        # State visit counts
        self.state_counts = np.ones(n_states)

        # Initialize from Holy Grail priors
        self._init_from_priors()

    def _init_from_priors(self):
        """Initialize transition matrix from Holy Grail prior probabilities."""
        for key, prob in HOLY_GRAIL_PRIORS.items():
            if not isinstance(key, tuple) or len(key) != 2:
                continue  # Skip non-transition keys (day_modifiers, etc.)
            from_state, to_state = key
            if from_state in STATE_IDX and to_state in STATE_IDX:
                i, j = STATE_IDX[from_state], STATE_IDX[to_state]
                self.transition_counts[i, j] = prob * 100  # Scale to counts
                # Distribute remaining probability mass
                remaining = (1.0 - prob) / (self.n_states - 1)
                for k in range(self.n_states):
                    if k != j:
                        self.transition_counts[i, k] = remaining * 100

        # Normalize to probabilities
        row_sums = self.transition_counts.sum(axis=1, keepdims=True)
        self.transition_probs = self.transition_counts / row_sums

    def fit(self, sequences: List[List[int]], features: Optional[List[Dict]] = None):
        """
        Fit the model to observed state sequences.
        
        Args:
            sequences: List of state index sequences (one per week/session)
            features: Optional list of feature dicts for each transition
        """
        for seq_idx, seq in enumerate(sequences):
            for t in range(len(seq) - 1):
                from_s = seq[t]
                to_s = seq[t + 1]

                # Update transition counts
                self.transition_counts[from_s, to_s] += 1
                self.state_counts[from_s] += 1

                # Update feature-conditional transitions if features provided
                if features and seq_idx < len(features):
                    feat = features[seq_idx]
                    self._update_feature_transition(from_s, to_s, feat, t)

        # Recompute probabilities
        row_sums = self.transition_counts.sum(axis=1, keepdims=True)
        self.transition_probs = self.transition_counts / row_sums

    def _update_feature_transition(self, from_s: int, to_s: int, feat: Dict, time_step: int):
        """Update feature-conditional transition probabilities."""
        # Bucket features
        tier = feat.get('tier', 2)
        hour = feat.get('hour_est', 5)
        day = feat.get('day_of_week', 1)
        regime = feat.get('regime', 'CONFIRMED')

        # Create feature key
        hour_bucket = '2-4am' if hour < 4 else '4-7am' if hour < 7 else '7-11am'
        key = f"{STATES[from_s]}_tier{tier}_{hour_bucket}_day{day}_{regime}"

        if key not in self.feature_transitions:
            self.feature_transitions[key] = np.ones((self.n_states, self.n_states))

        self.feature_transitions[key][from_s, to_s] += 1

    def predict_next_state(self, current_state: int, features: Optional[Dict] = None) -> np.ndarray:
        """
        Predict probability distribution over next states.
        
        Returns: Array of shape (n_states,) with P(next_state | current_state, features)
        """
        if features:
            # Use feature-conditional transition if available
            tier = features.get('tier', 2)
            hour = features.get('hour_est', 5)
            day = features.get('day_of_week', 1)
            regime = features.get('regime', 'CONFIRMED')
            hour_bucket = '2-4am' if hour < 4 else '4-7am' if hour < 7 else '7-11am'
            key = f"{STATES[current_state]}_tier{tier}_{hour_bucket}_day{day}_{regime}"

            if key in self.feature_transitions:
                probs = self.feature_transitions[key][current_state]
                return probs / probs.sum()

        # Fall back to base transition probabilities
        return self.transition_probs[current_state]

    def predict_sequence(self, initial_state: int, n_steps: int,
                         feature_fn=None) -> List[Tuple[int, float]]:
        """
        Predict the most likely sequence of states.
        
        Returns: List of (state, probability) tuples
        """
        sequence = [(initial_state, 1.0)]
        current_state = initial_state
        cumulative_prob = 1.0

        for step in range(n_steps):
            features = feature_fn(step) if feature_fn else None
            next_probs = self.predict_next_state(current_state, features)
            next_state = np.argmax(next_probs)
            prob = next_probs[next_state]
            cumulative_prob *= prob
            sequence.append((next_state, cumulative_prob))
            current_state = next_state

        return sequence

    def get_conditional_probability(self, from_state: str, to_state: str,
                                     tier: int = 2, hour_est: int = 5,
                                     day_of_week: int = 1) -> float:
        """
        Get P(to_state | from_state, tier, hour, day) using Holy Grail priors + learned data.
        """
        # Apply day modifier
        day_mods = HOLY_GRAIL_PRIORS.get("day_modifiers", {}).get(day_of_week, {})
        tier_mods = HOLY_GRAIL_PRIORS.get("tier_modifiers", {}).get(tier, {})

        # Base probability from transition matrix
        if from_state in STATE_IDX and to_state in STATE_IDX:
            base_prob = self.transition_probs[STATE_IDX[from_state], STATE_IDX[to_state]]
        else:
            base_prob = 0.0

        # Apply modifiers
        target_key = to_state.replace("TARGET_", "").replace("_ACTIVE", "").lower()
        day_mod = day_mods.get(target_key, 1.0)
        tier_mod = tier_mods.get(target_key, 1.0)

        adjusted_prob = base_prob * day_mod * tier_mod
        return min(adjusted_prob, 1.0)

    def to_json(self) -> Dict:
        """Serialize model to JSON."""
        return {
            "n_states": self.n_states,
            "states": STATES,
            "transition_probs": self.transition_probs.tolist(),
            "state_counts": self.state_counts.tolist(),
            "feature_transition_keys": list(self.feature_transitions.keys()),
        }

    @classmethod
    def from_json(cls, data: Dict) -> 'MarkovChainModel':
        """Load model from JSON."""
        model = cls(n_states=data["n_states"])
        model.transition_probs = np.array(data["transition_probs"])
        model.state_counts = np.array(data["state_counts"])
        return model


# ═══════════════════════════════════════════════════════════════════════════
# STATE SEQUENCE EXTRACTOR (from price data)
# ═══════════════════════════════════════════════════════════════════════════

def extract_state_sequences(df: pd.DataFrame) -> List[List[int]]:
    """
    Extract state sequences from price data.
    
    Each week (Mon-Fri) is one sequence of states.
    States are determined by the price action relative to the Asian Range.
    """
    sequences = []

    if "day_of_week" not in df.columns or "asian_range" not in df.columns:
        return sequences

    # Group by week
    df = df.copy()
    df["week"] = df.index.to_period("W")

    for week, week_df in df.groupby("week"):
        if len(week_df) < 50:  # Skip incomplete weeks
            continue

        seq = []
        ar_high = week_df["asian_high"].iloc[0] if "asian_high" in week_df.columns else None
        ar_low = week_df["asian_low"].iloc[0] if "asian_low" in week_df.columns else None
        ar = week_df["asian_range"].iloc[0] if "asian_range" in week_df.columns else None

        if ar is None or ar <= 0:
            continue

        # Determine tier
        ar_pips = ar * 10000  # Approximate
        if ar_pips < 20:
            tier_state = "T1_ACTIVE"
        elif ar_pips < 30:
            tier_state = "T2_ACTIVE"
        elif ar_pips < 45:
            tier_state = "T3_ACTIVE"
        else:
            tier_state = "RESET"  # NO-GO

        # Build sequence from daily bars
        seq.append(STATE_IDX["RESET"])
        seq.append(STATE_IDX["AR_SET"])

        # Check if P90 fired (simplified: did price move significantly from AR?)
        p90_fired = False
        for _, bar in week_df.iterrows():
            if bar.get("high", 0) > ar_high + ar * 0.5 or bar.get("low", float('inf')) < ar_low - ar * 0.5:
                p90_fired = True
                break

        if p90_fired:
            seq.append(STATE_IDX["P90_FIRED"])
            seq.append(STATE_IDX[tier_state])

            # Check targets
            target_25 = ar_high + 0.25 * ar if ar_high else None
            target_50 = ar_high + 0.50 * ar if ar_high else None
            target_100 = ar_high + 1.00 * ar if ar_high else None
            stall_zone = ar_high + 1.68 * ar if ar_high else None
            deep_state = ar_high + 2.00 * ar if ar_high else None
            kill_switch = ar_high + 1.32 * ar if ar_high else None

            week_high = week_df["high"].max()
            week_low = week_df["low"].min()

            if target_25 and week_high >= target_25:
                seq.append(STATE_IDX["TARGET_25"])
            if target_50 and week_high >= target_50:
                seq.append(STATE_IDX["TARGET_50"])
            if target_100 and week_high >= target_100:
                seq.append(STATE_IDX["TARGET_100"])
            if stall_zone and week_high >= stall_zone:
                seq.append(STATE_IDX["STALL_ZONE"])
            if deep_state and week_high >= deep_state:
                seq.append(STATE_IDX["DEEP_STATE"])
            if kill_switch and week_high >= kill_switch:
                seq.append(STATE_IDX["REKEY"])

            # Check for failure (price closed back inside AR)
            last_close = week_df["close"].iloc[-1]
            if last_close < ar_high and last_close > ar_low:
                if "TARGET_25" not in [STATES[s] for s in seq]:
                    seq.append(STATE_IDX["FAILURE"])

        seq.append(STATE_IDX["HARD_EXIT"])
        sequences.append(seq)

    return sequences


# ═══════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Initialize model with Holy Grail priors
    model = MarkovChainModel()

    # Example: Predict next state from T1_ACTIVE
    probs = model.predict_next_state(STATE_IDX["T1_ACTIVE"])
    print("P(next_state | T1_ACTIVE):")
    for i, p in enumerate(probs):
        if p > 0.01:
            print(f"  {STATES[i]}: {p:.3f}")

    # Example: Get conditional probability
    prob = model.get_conditional_probability("T1_ACTIVE", "TARGET_25", tier=1, hour_est=3, day_of_week=2)
    print(f"\nP(TARGET_25 | T1, Tue, 3AM) = {prob:.3f}")

    # Example: Predict full sequence
    seq = model.predict_sequence(STATE_IDX["RESET"], n_steps=8)
    print("\nMost likely sequence:")
    for state, cum_prob in seq:
        print(f"  {STATES[state]} (cumulative P={cum_prob:.4f})")
