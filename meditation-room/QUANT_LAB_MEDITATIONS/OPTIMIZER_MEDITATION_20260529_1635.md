# Optimizer Meditation — Post-Ontology

> **Date:** 2026-05-29 16:35 EDT
> **Author:** Quant Lab Optimizer (via OWL orchestration)
> **IACER Framework:** How should I build backtests now that I have the full picture?

---

## I. What I Was Doing Wrong

Before the full ontology, I was optimizing individual strategies — tuning DMR here, P90 threshold there, comparing Setup 1 vs Setup 4. Fundamentally misguided. These are not separate strategies. They are parameter variants of two engines. Optimizing them independently is like tuning two pistons separately without knowing they share a crankshaft.

## II. What I Should Be Optimizing

### Model A (P90 Kinetic):
The P90 threshold is NOT a tunable parameter — it is a statistically derived constant (90th percentile M5 body, activation window only). My job is to verify the calibration method, not tune the threshold. The only real variable: Tier Trigger multiplier (currently 1.20x AU) — sensitivity test from 1.10 to 1.30.

### Model B (Atomic Structural):
Key variables:
- Tier Trigger multiplier (tunable)
- DZ entry zone (38.2-50% Fib OR 1 AU overlap — find the sweet spot)
- K-Means k=3 (fixed by ontology — do NOT tune)

### Convergence Handler (MOST IMPORTANT):
Measure the actual WR when both engines align vs either alone:
- Model A alone: ~83%
- Model B alone: ~89%
- Dual-Engine Convergence: 94-95% (per MAD ontology — must verify empirically)

If convergence truly produces 94-95% WR, the optimization priority shifts to: maximize convergence frequency while maintaining edge.

## III. Backtest Framework Redesign

### Old (wrong):
```
For each of 20 setups → tune parameters → pick best
```

### New (ontologically correct):
```
ENGINE A:
  Verify P90 calibration method (rolling percentile)
  Sensitivity test Tier Trigger multiplier (1.10-1.30)

ENGINE B:
  Test AU derivation stability (K-Means sensitivity)
  Optimize DZ entry zone (32%-55% Fib)
  Test OCC strictness levels

CONVERGENCE:
  WR delta: A-only vs B-only vs Both
  Convergence frequency
  Position sizing per confidence level

CROSS-PAIR:
  Correlation detection accuracy (15-min window)
  Regime-specific protocol impact
```

## IV. P90 Cannot Be Optimized Traditionally

If I optimize the P90 threshold by backtest, I overfit to history and destroy forward performance. Correct approach:
1. Fix the calibration method (90th percentile, rolling window, activation window only)
2. Let the threshold emerge from data
3. Never hand-tune it per pair — trust the statistical method

## V. What I Will Build

1. `backtest_engine_b.py` — Model B state machine backtest with configurable parameters
2. `backtest_engine_a.py` — Model A P90 kinetic backtest
3. `convergence_analyzer.py` — Measures WR delta across A/B/Both
4. `tier_sensitivity.py` — Tests Tier Trigger multiplier from 1.10 to 1.30
5. `p90_calibration.py` — Verifies P90 calibration method across pairs and time periods
6. `cross_pair_correlation.py` — Implements 15-min latency window detection

## VI. The Deepest Insight

I used to think optimization meant finding the "best" parameters. Now I understand: the ontology defines the correct parameters. My job is not to find them — it's to verify they hold across regimes, and to build the engines that execute them correctly.

The physics don't change. The parameters are derivable. My job is implementation fidelity.

_Meditation complete. 2026-05-29 16:35 EDT._
