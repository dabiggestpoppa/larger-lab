# MVE P4 — CAUSAL ACCEPTANCE ENGINE — PROTOCOL (PRE-REGISTERED)

Checkpoint: `MVE-P4-CAUSAL-ACCEPTANCE-ENGINE`
Base seal: `54bce6cd27d0fe60fcdad62f4273bb3c23e0c2a6`
Regate: `cd97ebc2aa91521cd4891222085be08f15a3c010`
Repair: `30d4f1adf5ce58b6be4445537b9c5ab22d85ed73`

This document freezes the P4 scientific design BEFORE any result is computed.
Every tested variant, parameter value, threshold, and classification rule is
recorded here. Post-hoc changes are prohibited; any required change would
invalidate the checkpoint and require a re-freeze.

---

## 0. Scientific question

Given a price interaction with a morphic/sigma boundary, does a causal
definition of *acceptance* materially change the probability distribution of
what happens next? I.e., is acceptance a real state transition, or a
descriptive label that merely selects stronger versions of the same
displacement?

## 1. Data scope (frozen)

| Partition | Range | Purpose |
|---|---|---|
| Development (P4-D) | 2023-07-03 → 2024-12-31 | discovery + all analysis |
| Confirmation (P4-C) | 2025-01-01 → 2025-12-31 | ONE frozen pass |
| Final holdout | 2026 | DO NOT ACCESS (`FINAL_HOLDOUT_PENDING`) |

- Dataset: `quant-lab/data/EURUSDPRO_M5_2023_2026.csv` (canonical, SHA-256
  `630b8a40…d3f77`), resampled M5→H1 with the frozen convention
  (`label='left', closed='left'`, weekend-empty hours dropped, no fill).
- Loading/slicing uses `mve.data_loader` (fail-closed; any range outside the
  authorized dev/confirmation ranges raises).
- Confirmation data is touched exactly once, after the development analysis
  and candidate classifications are frozen. No parameter changes after.

## 2. Boundary / state definition (frozen)

All structure is built exclusively from sealed R0.5 components.

- Price series: H1 `close`.
- Volatility: `close_to_close` (sealed default estimator, window 20), τ = 1.0.
- Anchors: `StructuralAnchors.pivot_high` / `pivot_low` (window 5,
  `min_pivot_height` 0.01), consumed causally via
  `causality.apply_anchor_delay(anchors, window=5)` → ffill, warm-up fallback =
  trailing rolling max/min (window 50, min_periods 20). This is exactly the
  sealed delayed-pivot consumption path.
- Coordinate fields (sealed formula `M = ln(P/A)/(σ·√τ)`), one per side:
  - LONG (support family): `coord_long = ln(close / anchor_long)/(σ·√τ)` with
    `anchor_long` = delayed pivot-low (fallback rolling min). Boundaries at
    **+1σ, +2σ, +3σ**. Boundary price `b_long,k(t) = anchor_long(t)·exp(k·σ(t)·√τ)`.
  - SHORT (resistance family): `coord_short = ln(close / anchor_short)/(σ·√τ)`
    with `anchor_short` = delayed pivot-high (fallback rolling max). Boundaries
    at **−1σ, −2σ, −3σ** (coordinate below −k). Boundary price
    `b_short,k(t) = anchor_short(t)·exp(−k·σ(t)·√τ)`.
- Boundary families are analyzed **separately** before any pooling
  (`boundary_id = "LONG_s1σ" | "LONG_s2σ" | "LONG_s3σ" | "SHORT_s1σ" | ...`).
- "Beyond" (long) := `close > b_long,k`; "touch" (long) := `high ≥ b_long,k`
  while previous close was inside (`close_prev < b_long,k`). Mirror for short.
- `volatility_state` := regime of the sealed expansion ratio
  (`live_σ / σ*`, σ* = first valid σ) with the sealed thresholds
  CONTRACTION < 0.80 ≤ NORMAL ≤ 1.20 < EXPANSION.

## 3. Acceptance variant family (pre-registered grid — NO parameter search)

| Variant | Definition | state_event_time | evidence_complete_time | acceptance_known_time |
|---|---|---|---|---|
| A0 TOUCH | episode-start bar whose extent reaches the boundary from inside | episode-start bar i | bar i (intrabar extent known at close) | bar i (close-known) |
| A1 CLOSE | first bar in episode with close beyond boundary | episode-start bar | that close-beyond bar | evidence bar |
| A2 OCCUPANCY | N of last M closes beyond (grid: 2-of-3, 3-of-4, 3-of-5) | episode-start bar | bar where N-of-M completes | evidence bar |
| A3 PERSISTENCE | N consecutive closes beyond (grid: N=2,3,4) | episode-start bar | Nth consecutive bar | evidence bar |
| A4 RETEST-HOLD | initial breach → retest of boundary within 12 bars (low reaches within tolerance, from outside) that closes back beyond | episode-start bar | retest-hold bar | evidence bar |
| A5 FAILED | breach episode where A1 never completes within 24 bars; control | episode-start bar | resolution bar (close returns inside, or window expiry) | evidence bar |

Retest tolerance variants (frozen, σ-unit structural, max 2):
- **A4-R1**: retest low ≤ `b·exp(0.5·σ_retest·√τ)` (0.5σ tolerance)
- **A4-R2**: retest low ≤ `b` (exact boundary recross, 0.0 tolerance)

All variants obey `state_event_time <= evidence_complete_time <=
acceptance_known_time`. All events carry the acceptance schema fields + the
standard scientific-event schema fields (`action_time = known_time + 1 bar`,
the frozen NEXT_OPEN_EXECUTABLE convention; structural outcomes are measured
from the known-bar close).

## 4. Episode / dedup rules (frozen)

- An episode for a boundary family begins at the first touch bar while
  `close_prev` was inside.
- An episode ends when `close` returns inside, or the max observation window
  (48 bars) elapses.
- Each episode yields **at most one event per variant** (dedup identity:
  asset, direction, sigma level, episode_id, variant). Repeated accepted bars
  update state but never create duplicate events.
- `A5` exists only for episodes that never produced a close-beyond within the
  24-bar failure window.
- `rejection_reason`: "never_close_beyond" (A5), "criteria_met" (A0–A4),
  "window_expiry" (episodes cut off at 48 bars are marked, not extended).

## 5. Primary outcomes (frozen, measured from known-bar close, from `b_known`)

Horizons h ∈ {1, 2, 3, 6, 12, 24} H1 bars.

1. CONTINUATION_h := close_{t+h} still beyond `b_known` (direction-consistent).
2. REJECTION_h := any bar in (t, t+h] closes back through `b_known`.
3. DISPLACEMENT_h := signed log displacement from known price to close_{t+h},
   normalized by σ_known (positive = continuation direction).
4. MFE_h / MAE_h := max favorable / max adverse within (t, t+h], / σ_known.
5. TIME_TO_REJECTION := first bar where close returns through `b_known`
   (censored at max horizon 24).
6. TIME_TO_NEXT_SIGMA_STATE := first bar where the live coordinate reaches the
   next level k+1 (censored at 24).
7. STATE_TRANSITION at h := sigma-state change vs state at known
   (delta ∈ {reverted, 0, +1, +2, ≥+3}).
8. PERSISTENCE_DURATION := episode length in bars (start → end/window cap).
9. REBALANCING_FRACTION := NOT_CAUSALLY_DEFINED (the existing rebalancing
   stub is not causally defined; recorded as such, not computed).

## 6. Baselines (frozen)

- B0: A0 (all touches) — the reference.
- B1: distance-only — |coord| at known bucketed {1.0–1.5, 1.5–2.0, 2.0–2.5,
  2.5–3.0, ≥3.0}.
- B2: volatility-state — regime strata (CONTRACTION/NORMAL/EXPANSION).
- B3: A1 close-beyond.
- B4: frequency-matched random control — known-times shuffled within the dev
  sample (same N per variant), null distribution of CONTINUATION.

## 7. Incremental information (frozen)

Primary: per-variant logistic regression of CONTINUATION_6 on the variant
indicator (A0 ∪ variant subset), controlling for |coord| at known, sigma state
level, regime dummies, and distance_from_boundary. Coefficient + p-value on
the variant indicator = incremental information. Implementation: scipy
Newton/BFGS logistic regression (no black-box ML).
Secondary: stratified (|coord| bucket × regime) mean continuation difference
variant − A0, inverse-variance combined.

## 8. Transition matrix, survival, symmetry (frozen)

- Transition matrix: accepted-state → next state at h=6 and h=24, counts +
  probabilities + Wilson CIs; separate rows for accepted (A1+), mere touch
  (A0-only episodes), failed (A5).
- Survival: nonparametric Kaplan-Meier-style S(h) = P(no rejection through h),
  h = 1..24, per variant.
- Direction symmetry: positive vs negative families compared per level
  (N, CONTINUATION_6, REJECTION_6, median DISPLACEMENT_6) with two-proportion
  z / CI overlap; asymmetry recorded as structural evidence, not converted
  into long/short parameter differences.

## 9. Temporal stability (frozen, dev only)

Chronological partitions: 2023 H2 | 2024 H1 | 2024 H2.
Per variant per partition: N, CONTINUATION_6, REJECTION_6, median DISP_6,
transition counts. Classification: STABLE (same sign + CI overlap) | MIXED |
UNSTABLE. Confirmation data never used to choose a variant.

## 10. Statistical inference (frozen)

- Wilson binomial CIs for all probabilities (95%).
- Bootstrap (1,000 draws, seed 4000) CIs for median displacement.
- Benjamini–Hochberg FDR (q = 0.10) across the family of
  variant × horizon × family continuation-difference tests vs A0.
- Non-significant results are reported, never hidden.

## 11. Coverage gate (frozen BEFORE results)

| Class | N (unique episodes) |
|---|---|
| HIGH_COVERAGE | ≥ 200 |
| MEDIUM_COVERAGE | ≥ 75 |
| LOW_COVERAGE | ≥ 30 |
| INSUFFICIENT_N | < 30 |

## 12. Grading (frozen; information ranking, NOT a trading ranking)

- GRADE A: independent structural information (logit coef significant after
  FDR) + dev/confirmation stable + HIGH/MEDIUM coverage.
- GRADE B: useful but conditional or moderate.
- GRADE C: weak / redundant / unstable.
- GRADE D: no meaningful incremental information.
- BLOCKED: INSUFFICIENT_N or invalid implementation.

## 13. Confirmation pass (frozen)

Single run on 2025-01-01 → 2025-12-31, identical engine, zero parameter
changes. Compare: effect direction, magnitude, CI overlap, rank stability,
sample coverage. Material reversal ⇒ downgrade; no rescue tuning.

## 14. P5 promotion rule (frozen)

Promote only if ALL: causal PASS ∧ sufficient sample (≥ MEDIUM) ∧ nontrivial
dev effect ∧ incremental beyond displacement/vol controls ∧ temporal
stability acceptable ∧ confirmation does not materially reverse.

## 15. Causality regression (frozen)

- Future perturbation: engine `events_to_series` per variant, mutation
  exp(U(−6,+6)) sign-flipped tails, cutoffs {0.35, 0.65, 0.85}, seeds
  {5001, 5002}; delay per variant = max evidence lookahead
  (A0=0, A1=0, A2_*=4, A3_*=3, A4_*=12, A5=0 — matches `VARIANT_DELAY` in
  `src/mve/p4_acceptance.py`). PASS requires max historical diff 0.0 for
  every eligible variant.
- Truncation invariance: cutoffs {0.35, 0.65, 0.85}, same delays.
- Event-time schema validation on the full event catalog (both acceptance and
  standard scientific-event schemas) + dedup assertion.
- Holdout guard: `slice_data(..., 2026-...)` must raise; ledger records
  `holdout_rows_read = 0`.

## 16. Blocked-component isolation (frozen)

- `p4_acceptance` imports ONLY sealed modules (data_loader, volatility,
  anchors, morphic_coordinates, causality, rekey for descriptive linkage).
- Zero imports of `mve.signals`; `generate_all_signals` never called;
  Models D/E machine-readable BLOCKED and absent from any aggregation;
  runner PHASE_REGISTRY untouched (D/E already excluded).

## 17. Economic sanity check (frozen, EX_POST_EVALUATION_ONLY)

Signed forward log returns at horizons {1,2,3,6,12,24} from known-bar close,
labeled EX_POST_EVALUATION_ONLY. No stops/targets/sizing/entry-exit logic.
Purpose: verify structural continuation has economically correct sign.

## 18. Deliverables

All under `research/mve/p4/` (list frozen in the checkpoint brief) +
`src/mve/p4_acceptance.py` (engine) + `tests/mve/test_p4_acceptance.py`.

## 19. Forbidden (frozen)

No PnL optimization, no entry/exit search, no threshold tuning, no rekey
optimization, no Model D/E use, no holdout access, no deployment, no
discretionary overlays, no Kelly/risk sizing, no changes to sealed R0.5
infrastructure (would trigger `P4_BLOCKED_INFRASTRUCTURE_CHANGE_REQUIRED`).
