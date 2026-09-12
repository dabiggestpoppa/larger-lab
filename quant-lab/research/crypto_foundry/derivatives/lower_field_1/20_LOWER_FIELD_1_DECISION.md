# LOWER-FIELD-1 — DECISION

**Checkpoint:** CRYPTO-ALT-LOWER-FIELD-1
**Parent:** `9c2b7d7f8bf1e1ee6bdefaf69528d47f3cf935ee`
**Node:** Agent 2 — Derivative / Side-lane Falsifier

No strategy. No PnL. No hedge construction. No production authority.

---

## 1. Core-question adjudication

> When lower-ranked crypto moves, what is the distributional anatomy?

- **HOW MUCH:** median ~2.7% (flat); raw tail p99 fattens ~2.5× with depth, but
  this is a volatility effect — sigma-normalized tail frequency is flat (04).
- **HOW FAST:** 1σ ≈ 2d, 2σ ≈ 5d, 3σ ≈ 7–8d, peak ≈ 9–10d — rank-independent
  (05).
- **HOW LONG / HOW IT ENDS:** single-day spikes (median time-above-2σ = 0),
  fast reversion inside 1σ in 1d (05/06); deep-DOWN extremes give back ~43%
  within 7d vs 3% for deep-UP (13).
- **WITH WHOM:** aggregate rides BTC/ETH (corr 0.81→0.87 by depth); extremes
  progressively decouple (BTC co-move 62%→53%); participation mostly
  ISOLATED/LOCAL_CLUSTER, GLOBAL_SYNC rare (10, 11).
- **UNDER WHAT STATE:** SHORT_HOT_MEDIUM_COLD + high top-500 breadth + younger
  age raise delivery probability (07, 09).
- **HOW IT ENDS:** asymmetric, depth-dependent reversal (13).

**Dominant description:** FRAGMENTATION with a central common-factor core.
Not directional propagation, not global-sync coherent tails, not sustained
amplification. Delivery is breadth-gated from above and issued as isolated local
tail events that reverse fast.

## 2. Node adjudication (per prereg classes)

| Node | Classification |
|------|----------------|
| AMPLITUDE_GRADIENT_IS_VOLATILITY_DRIVEN | DESCRIPTIVE_ONLY |
| UNIFORM_FAST_DELIVERY_TIMESCALE | DESCRIPTIVE_ONLY |
| TAIL_ACTIVATION_GRADIENT_REVALIDATED | LOCAL_NODE (magnitude; not direction) |
| BREADTH_PROPAGATION_NOT_EXIT_TRIGGERED | PROMOTION_CANDIDATE |
| TAIL_IDIOSYNCRATIC_DECOUPLING | PROMOTION_CANDIDATE |
| ASYMMETRIC_DEPTH_DEPENDENT_REVERSAL | LOCAL_NODE |
| FRAGMENTED_TAIL_PARTICIPATION | LOCAL_NODE |
| DEFENSIVE_SECTOR_RISK_OFF_POCKET | LOCAL_RULE |
| RISK_ON_STREAK_REVERSION / DISPERSION_STREAK_TAIL_FOLLOW | LOCAL_RULE |
| EXIT_NO_HANDOFF | NULL |
| BROAD_SECTOR_CHAIN_ORGANIZATION | NULL / DISSOLVE |
| AMPLIFIER (raw gradient) | DISSOLVE |

PROMOTION_CANDIDATES are proposed to Agent 1; none become canonical
automatically.

## 3. Causality ceiling

Highest level reached: **L2 (conditional lead-lag)** only for the
breadth→delivery association (09). Contemporaneous co-movement (11, 12) is L0/L1.
Time-to-delivery and reversal are L1. **No L5/L6 mechanistic or causal claims.**

## 4. Data / observation limits

- Single-venue price risk for the deepest tails; stale/zero-volume flags
  present (~2% stale, ~7.9% zero-volume in 501-2000).
- Effect sizes are small-to-moderate (Cohen's d ≤ ~0.14; residual pockets ≤ ~2pp).
- Forward-window analyses right-censored at 30d; overlapping-event independence
  for reversal not fully purged (recount recommended).
- Cross-field anchored on MECH-4 EXIT event dates (burned-in coordinates), not
  on Agent-1 outcome labels.

## 5. Effective independent counts / coverage

- Panel: 3.29M rows, 7,330 assets, ranks 501-2000, 2,195 dates.
- Sigma-normalized events: 329,488 (10% of rows are ≥3σ events — fat tails).
- SHORT_HOT_MEDIUM_COLD rows: 638,130 (08).
- MECH-4 exit anchors: 125 (14/15).
- Subperiod split and BH-FDR applied where broad grids were scanned.

## 6. Decision

```
PASS_LOWER_FIELD_1_DISTINCT_TAIL_ANATOMY_WITH_LIMITATIONS
```

Rationale: the checkpoint establishes a **structurally distinct, reproducible
distributional anatomy** for the lower field — volatility-scaled tail activation,
central-common/tail-idiosyncratic coupling, breadth-gated delivery, and
asymmetric rank-dependent reversal — none of which reduce to ordinary beta or
pure noise. It remains a negative on direction and a negative on exit-handoff.

**human_review_required = TRUE**
**next_checkpoint_authorized = FALSE**

STOP after LOWER-FIELD-1. WAIT FOR HUMAN REVIEW.

## 7. Output inventory

- 01_PREREGISTRATION.md, 02_EVENT_DEFINITION_AUDIT.md
- 03_AMPLITUDE_DISTRIBUTIONS.csv, 04_SIGMA_NORMALIZED_MOVE_DISTRIBUTIONS.csv
- 05_TIME_TO_DELIVERY.csv, 06_EVENT_DURATION_DECAY.csv
- 07_TAIL_ACTIVATION_REVALIDATION.csv
- 08_POTENTIAL_REALIZATION_PANEL.parquet, 09_POTENTIAL_REALIZATION_DIVERGENCE.csv
- 10_GROUP_BEHAVIOR_CLASSIFICATION.csv, 11_LOCAL_COUPLING_MATRIX.csv
- 12_CONDITIONAL_CHAIN_SECTOR.csv
- 13_REVERSAL_DECAY_GEOMETRY.csv
- 14_CROSS_FIELD_ALIGNMENT.csv, 15_CROSS_FIELD_HANDOFF_TESTS.csv,
  16_FORM_CHANGE_BY_RANK.csv
- 17_LOCAL_SEQUENCE_MAP.csv (+ raw)
- 18_LOWER_FIELD_1_SYNTHESIS.md, 19_LOWER_FIELD_1_PROMOTION_CANDIDATES.md,
  20_LOWER_FIELD_1_DECISION.md
- Scripts: lf1_common, lf1_amplitude, lf1_delivery, lf1_tail_reversal,
  lf1_potential_realization, lf1_group_coupling, lf1_conditional_lenses,
  lf1_cross_field, lf1_local_sequences.