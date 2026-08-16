# MVE P7 — SIGNAL MODEL FALSIFICATION PROTOCOL (Pre-Registration)

> **Checkpoint:** MVE-P7-SIGNAL-MODEL-FALSIFICATION
> **Base:** 96c4a90a77cb2b19fedca9093ca47e6f2a171dc0 (P6.5 seal)
> **Written before any P7 measurement.** Falsification phase — the default
> hypothesis is **REDUNDANT UNTIL PROVEN OTHERWISE**.

---

## 1. Nature of this checkpoint

P4 (acceptance) and P6 (rekey) were rejected as independent information
layers; P6.5 pruned them and sealed the minimal surviving core
(price → anchors → volatility → morphic coordinates → sigma states →
model logic). P7 now falsifies the three surviving signal models against
their closest simple equivalents.

P7 is a FALSIFICATION phase:

- it does NOT prove Models A/B/C work;
- it does NOT optimize entries/stops/sizing/Kelly;
- it does NOT run trade PnL;
- it does NOT read 2026;
- it does NOT call Models D/E or `generate_all_signals`;
- it does NOT re-introduce acceptance/rekey alpha.

A full null result (ALL MODELS REDUNDANT) is a valid, expected outcome and
permits `status = PASS`.

## 2. Frozen inputs

- Canonical data: `quant-lab/data/EURUSDPRO_M5_2023_2026.csv`,
  SHA256 `630b8a40…d3f77`, H1 frozen resampling (no forward-fill).
- Development: 2023-07-03 .. 2024-12-31. Confirmation: 2025-01-01 ..
  2025-12-31 (single pass). Holdout: 2026 — **FINAL_HOLDOUT_PENDING, 0 rows**.
- Sealed field construction (identical to P4/P6): trailing prior-50-bar
  close extremes (`.max()/.min().shift(1)`, min_periods 20), close-to-close
  rolling volatility, signed coordinate
  `x = ln(price/anchor)/vol` (upper family, direction +1; models are
  |x|-symmetric so the upper-family reference is representative and matches
  the executed P4/P6 field).
- Sealed generators: `src/mve/signals.py` `SignalGenerator` (Models A/B/C
  only). Sealed matrix classifications:
  A = CAUSAL_DELAYED_CONFIRMATION, B = CAUSAL_REALTIME,
  C = CAUSAL_DELAYED_CONFIRMATION.
- P6.5 baseline crosswalk: `research/mve/p65/MVE_P65_BASELINE_CROSSWALK.csv`.

## 3. Frozen model & baseline definitions (boundary B = 1.0, step 1.0)

| ID | Definition | Known at |
|---|---|---|
| **MODEL_A** | |x| crosses +1σ boundary AND |x| still beyond at the next bar (1-bar no-close-back confirmation) | confirmation bar i+1 |
| **MODEL_B** | |x| > boundary AND 3-bar occupancy ≥ 0.8 (occupancy = fraction of last 3 bars with \|x\| > boundary, recomputed from coordinates) | realtime bar i |
| **MODEL_C** | |x| crosses +1σ at i−1, then reaches \|x\| > 2σ at i (escalation entry) | confirmation bar i |
| **B3_PLAIN_BREAKOUT** | first bar where \|x\| crosses B (close basis) — the shared plain threshold baseline | crossing bar i |
| **A_BASE** | 1σ crossing + 1-bar persistence (structurally identical to MODEL_A) | i+1 |
| **B_BASE** | threshold + 3-bar occupancy ≥ 0.8 (structurally identical to MODEL_B) | i |
| **C_BASE** | 1σ→2σ escalation (structurally identical to MODEL_C) | i |
| **C_DIRECT_2SIGMA** | \|x\| > 2σ entry without the 1σ-escalation precondition (plain higher-threshold crossing) | i |

**Frozen falsification contrasts** (the scientific content):

- **MODEL_A** vs **B3_PLAIN_BREAKOUT**: does the 1-bar confirmation filter
  improve event quality (timing/selection value)? Does the A flag add
  incremental info beyond coordinate magnitude once the crossing is known?
- **MODEL_B** vs **B3_PLAIN_BREAKOUT**: does the 3-bar occupancy construction
  filter events better than the raw threshold?
- **MODEL_C** vs **C_DIRECT_2SIGMA**: does the 1σ→2σ escalation path add
  information beyond simply being at 2σ?

Because A/B/C are structurally near-identical to their own A/B/C_BASE, the
pairwise contrast is the honest falsification: **the model is credited only
for what its extra construction layer changes** relative to the plain event.

## 4. Event / episode construction

Each model/baseline signal series is converted to episodes:

- **Discrete-entry models (A, C, C_DIRECT_2SIGMA, B3):** each +1/−1 signal
  bar starts an episode; consecutive same-direction signals within 2 bars
  are merged into one episode (dedup).
- **State models (B):** contiguous runs of the active state form one
  episode; event time = first bar of the run (known at that bar).

Every episode records:

```
event_id, model, direction, event_time (structural bar),
evidence_complete_time, known_time, action_time (= known_time),
coordinate_at_known, sigma_state, vol_tercile, anchor_age,
distance_from_boundary, hour, session, prior_state_duration
```

Event-time contract (frozen): `event_time <= evidence_complete_time <=
known_time <= action_time`. Validators fail closed on missing/NaT/ordering
violations. No backdating.

## 5. Primary outcomes (from known_time, fixed horizons 1, 2, 3, 6, 12, 24)

For each episode:

- signed forward displacement (σ-normalized coordinate delta, signed by direction)
- absolute displacement
- directional hit rate (P(sign of displacement == direction))
- continuation probability (P(|x| still beyond B at h))
- rejection probability (P(|x| back inside B at h))
- MFE-like structural excursion (max favorable |x| − boundary over (k, k+h])
- MAE-like structural excursion (max adverse drawdown below entry |x|)
- time to rejection (first bar back inside B, capped at horizon)
- time to next sigma state (first bar with a different sigma state)
- next sigma-state distribution at h
- state persistence duration (contiguous beyond-state length)
- transition entropy of the next-state distribution

No PnL, no stops, no targets, no sizing.

## 6. Incremental information test

For each model, on the union episode set (dev only), fit logistic regression
on the h=6 continuation outcome:

- **Null:** controls only — |x| at known (coordinate magnitude), sigma state,
  vol tercile, direction, distance-from-boundary, hour, session, anchor age,
  prior state duration, **plus the plain baseline signal flag** (B3 for A/B,
  C_DIRECT_2SIGMA flag for C).
- **Full:** null + the complex-model flag.

Report: model coefficient, LR p-value, likelihood-ratio test, BH-FDR across
the three model families, bootstrap CI on the incremental lift (paired where
events match). A model is REDUNDANT if its flag is non-significant after the
baseline flag and coordinate/sigma controls.

Also: paired bootstrap on matched event pairs (MODEL_AND_BASELINE class) for
the h=6 continuation difference.

## 7. Timing value (Models A/C, delayed confirmation)

For every matched pair (baseline at i, model at i+d):

- delay d (bars)
- move already consumed before model action: |x[i+d]| − |x[i]| (structural)
- false-positive reduction: P(rejection by h=6) baseline vs model
- displacement quality: signed displacement at h=6 baseline vs model
- MAE reduction
- answer: is the confirmation worth the lost move?

## 8. Selection value

Event matching classes (frozen):

```
MODEL_AND_BASELINE   both fire (matched within ±2 bars, same direction)
MODEL_ONLY           model fires, baseline does not
BASELINE_ONLY        baseline fires, model does not
NEITHER              (control; not an event)
```

Compare MODEL_ONLY vs BASELINE_ONLY outcomes (hit rate, displacement, MFE,
MAE, rejection) to determine whether the model's filter selects genuinely
better events or merely discards/suppresses baseline events.

## 9. Direction symmetry

Separate positive/negative-coordinate episodes for every model/baseline.
Compare N, hit rate, signed displacement, MFE, MAE, rejection, transition
outcomes. Report asymmetry explicitly; never average it away.

## 10. Temporal stability & confirmation discipline

- Dev blocks: 2023H2, 2024H1, 2024H2 (same-sign requirement).
- **Freeze** model/baseline definitions, outcomes, controls, promotion
  criteria BEFORE opening 2025 (registry hash enforced).
- One 2025 confirmation pass. No post-confirmation tuning. No rescue.
- Stability labels: STABLE / MIXED / UNSTABLE.

## 11. N coverage gates (frozen)

- N ≥ 200: HIGH; N ≥ 75: MEDIUM; N ≥ 30: LOW; N < 30: INSUFFICIENT_N.
- Report N and effect size; do not promote tiny-N variants.

## 12. Promotion criteria (all ten required)

1. causality PASS (perturbation 0.0, truncation PASS, schema clean)
2. N ≥ 200 (dev, HIGH coverage)
3. raw structural effect meaningful
4. incremental effect survives baseline+controls (LR flag significant after
   BH-FDR, and bootstrap CI on incremental lift excludes 0)
5. timing/filtering value positive (delay justified, or realtime value)
6. temporal stability STABLE or MIXED (not UNSTABLE)
7. 2025 confirmation does not materially reverse
8. no dependence on acceptance/rekey alpha
9. no dependence on Models D/E or the aggregate
10. holdout untouched

Promotion means **ELIGIBLE_FOR_ECONOMIC_TRANSLATION** only — never
"deployable" or "profitable".

## 13. Evidence labels

VALIDATED / CONFIRMED / INCREMENTAL / REDUNDANT / CONDITIONAL / MIXED /
UNSTABLE / INSUFFICIENT_N / REJECTED / BLOCKED.

## 14. Null outcome

ALL MODELS REDUNDANT is a valid P7 outcome. If so, recommend
MVE-P7.5-CORE-STATE-SEAL. If one or more survive, recommend
MVE-P8-STRUCTURAL-GENERALIZATION. No automatic progression.

## 15. Multiple-test control

BH-FDR over exploratory families; effect sizes + bootstrap CIs are primary;
no p-value fishing; no post-hoc threshold search.

## 16. Artifacts

All MVE_P7_* artifacts under `research/mve/p7/` per the checkpoint spec,
including event ledgers, matching, structural outcomes, incremental
information, timing/selection value, direction symmetry, temporal stability,
confirmation results, per-model results, transition matrix, state survival,
statistical inference, causality audit, evidence status matrix, promotion
matrix, report, decision.
