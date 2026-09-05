# MECH-20 · 40 — RESPONSE_LAW_STATE — OS RUNTIME OBJECT PROPOSAL

**Status: PROPOSAL (not frozen).** The object is earned as a descriptive coordinate, NOT as a
trading signal. It is proposed for the Market OS architecture so that downstream modules can
condition on which response-law environment they are in.

## Why it is earned
- Gain (logistic slope, unclamped) is a **continuous, highly persistent, near-absorbing coordinate**:
  autocorr 0.99 (lag1) / 0.66 (lag30); tercile self-transition 0.98–0.99 (MECH-20 04).
- Gain + ceiling are the 2-coordinate response description (anti-coupled r = −0.85; together ~96%
  of saturation-node motion, MECH-19).
- The gain series is **bimodal and episodic**: 21 monthly regime transitions, 5 LOW-gain runs,
  7 HIGH-gain runs over 2020–2026; no single agreed changepoint (segmented regression finds
  collapses at 2021-12, 2022-12, 2024-12) (MECH-20 34–37).
- Response environment changes **delivery meaning**: HI_GAIN_LO_CEIL delivers 0.40 vs
  LO_GAIN_HI_CEIL 0.31; transfer/realization rate fell post-2022 (0.51 → 0.35) while birth-abort
  rate doubled (0.36 → 0.58) (MECH-20 06, 36).

## Proposed fields (runtime, descriptive)
```
ResponseLawState:
  gain                float   # unclamped FIELD logistic slope k (rolling 180d, step 30d)
  ceiling             float   # unclamped FIELD logistic ceiling C
  baseline_version    str     # 'PRE2022' | '2022EVENT' | 'POST2022' | 'RECURRENT' (era tag)
  deviation_from_baseline  float  # |z| of gain vs era baseline (MAD-normalized)
  recent_changepoint  bool    # segfit/cusum agreement within last 60d
  law_recovery_status str     # 'SURFACE_NORMALIZED' | 'LAW_NORMALIZED' | 'LAW_DEVIATED'
  regime              str     # 'LOW_GAIN' | 'MID_GAIN' | 'HIGH_GAIN'  (thresholds 0.35 / 0.9)
```

## Governance constraints
- NOT a trading signal. No entry/exit/sizing anywhere downstream of this object.
- NOT a permanent categorical regime: `baseline_version` is a tag, not a law.
- Surface and law recovery are SEPARATE clocks (SURFACE_END vs LAW_END), kept apart in the OS.
- The 2022 collapse is one instance of a recurring LOW_GAIN regime, not a one-off regime change
  (H3_MULTIPLE_REGIME_MODULATIONS).

## Proposal decision
RECOMMENDED for OS adoption as a **descriptive context object** (ADAPTIVE_LAW role), pending human
review. The global adaptive-law architecture freeze decision is in 46_MECH20_DECISION.md.
