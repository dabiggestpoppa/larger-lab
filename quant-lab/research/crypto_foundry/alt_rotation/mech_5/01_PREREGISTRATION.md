# MECH-5 PREREGISTRATION

## CHECKPOINT: CRYPTO-ALT-MECH-5
FAILURE ANATOMY, ROTATION SURVIVAL, TEMPORAL DIVERGENCE & TERMINATION PRECURSORS

## DATE: 2026-08-27

## ROLE: AGENT 1 — CANONICAL FIELD CARTOGRAPHER

## RESEARCH QUESTION

When initially similar release/rotation attempts diverge, what is the FIRST
observable difference between sustained propagation, immediate delivery,
RETEST_RELOAD, failed ignition, snapback/reentry, and mixed/no-route failure?

## CANONICAL EVENT COHORT

125 concentration-release events from MECH-4 canonical ledger.

Outcome families:
- A: SNAPBACK / REENTRY (52)
- B: MIXED / NO CLEAR ROUTE (44)
- C: FAILED_IGNITION (52, from first-move classification)
- D: IMMEDIATE_DELIVERY (14)
- E: RETEST_RELOAD (14)
- F: SUSTAINED_PROPAGATION (BROAD_RISK + ALT = 27)
- G: BROAD_RISK_SUSTAINED (18)
- H: ALT_FAMILY_SUSTAINED (9)

## WORKSTREAMS

### WS1: First-Divergence Analysis
- Align events at t0 = release date
- Compare cohorts at +0D, +1D, +2D, +3D, +5D, +7D, +10D, +14D, +21D, +30D
- Variables: breadth30, breadth change, top3 concentration, BTC return, ETH relative,
  volatility, rank dispersion, rank-band velocity, leadership width
- For each variable: earliest separation day, effect size, CI, robustness
- Tests: rank-sum at each horizon, FDR-corrected

### WS2: Success vs Failure Weight Map
- Incremental logistic models M0-M6
- M0: current state only (10 features)
- M1: + breadth family
- M2: + volatility family
- M3: + rank participation / migration
- M4: + concentration / BTC / ETH relative
- M5: + state age / timing
- M6: + sector / chain local
- Report: delta log loss, delta Brier, AUC, permutation p

### WS3: RETEST_RELOAD Internal Anatomy
- Compare RETEST_RELOAD vs FAILED_IGNITION during retracement
- Variables during retrace: breadth retention, concentration rebuild, rank velocity,
  volatility, ETH relative
- Earliest internal-state difference
- Bootstrap validation (n=14 small, report LOCAL_MOTIF if unstable)

### WS4: Two-Clock Temporal Mechanism
- Escape hazard: P(escape within h | current state, age)
- Propagation hazard: P(sustained within h | escape, evolving state)
- Failure hazard: P(reentry within h | escape, evolving state)
- Horizons: 1D, 2D, 3D, 5D, 7D, 10D, 14D, 21D, 30D
- Test whether narrower windows improve info beyond existing lattice

### WS5: Early Decay / Termination Reconstruction
- Align sustained propagation episodes at termination
- Compare against matched alive propagation episodes
- Variables: breadth, rank velocity, leadership width, concentration, volatility
- First deterioration time, signal→end latency
- Verdict: EARLY_DECAY_SEQUENCE / COINCIDENT / ABRUPT / NULL

### WS6: Failure-Sequence Clustering
- Reconstruct state sequences from release through resolution
- Cluster by interpretable transitions
- Identify recurring failure motifs: EARLY_SNAPBACK, BREADTH_FADE,
  VOLATILITY_FADE, LEADERSHIP_NARROWING, CONCENTRATION_REBUILD

### WS7: Conditional Rescue Test
- Recheck null patterns under earned states (BTC_UP/DOWN, VOL_HIGH/LOW, etc.)
- FDR correction applied

### WS8: Causality Ladder
- Classify every result L0-L6

## STATISTICAL DISCIPLINE

- FDR (BH) correction across all tests within each workstream
- Bootstrap (B=500) for effect-size CIs
- Leave-one-cycle-out for stability
- Minimum sample: n >= 10 for any comparison (warn if < 20)
- All nulls preserved
- Permutation p = (k+1)/(B+1) finite-sample corrected

## DECISION VOCABULARY

- PASS_MECH5_FAILURE_ANATOMY
- PASS_MECH5_WITH_LIMITATIONS
- FAIL_MECH5_NO_DIVERGENCE_STRUCTURE
- BLOCKED_MECH5_DATA

## NO STRATEGY. NO PNL. NO DEPLOYMENT.
