# MECH-6 PREREGISTRATION

**Checkpoint:** CRYPTO-ALT-MECH-6 — MICRO-STATE SEQUENCE ATLAS, BREADTH TRANSMISSION,
LOCAL MOTIFS & RESEARCH-TO-ALPHA ROLE MAPPING
**Date:** 2026-08-26
**Empirical parent:** MECH-5 `244ca246` (PASS_MECH5_FAILURE_ANATOMY) ·
MECH-4 `487131da` (PASS_ALT_MECH4_WITH_LIMITATIONS) ·
MECH-3 `23ff4c12` (PASS_ALT_MECH3_WITH_LIMITATIONS)
**Role:** AGENT 1 — CANONICAL FIELD CARTOGRAPHER. Terrain/mechanism research ONLY.
**Governance:** NO strategy, NO PnL, NO entries/exits, NO sizing, NO live signals.
`human_review_required = TRUE`, `next_checkpoint_authorized = FALSE`.

This document is written BEFORE outcome analysis. It fixes variables, state
definitions, event windows, lags, inclusion rules, subperiods, minimum samples,
test families, and promotion rules.

---

## 1. Data & PIT truth

- Canonical MECH-4 daily frame `daily`: 2,196 days, 2020-06-01 → 2026-08-23,
  74 columns, built from PIT inputs via `M4.build_daily`. Used exactly as cached
  (no new interpolation, no future-filled values).
- Canonical release ledger: **125 concentration-release events** (`EXIT_000` …)
  with `first_destination`, `days_to_destination_d`, `state_age_d`, regime flags,
  `subperiod`. Preserved verbatim from MECH-4/5 — no relabeling.
- Rank-band frame `bm`: 7 bands × 2,196 days (`median_rank_velocity_7d`,
  `breadth_7d`, `median_return_1d`, `market_cap_share`).
- MECH-5 artifacts reused: `15_FAILURE_SEQUENCE_MAP.csv` (motifs), MECH-4
  `33_FIRST_MOVE_TRUE_DELIVERY.csv` (first-move classes), MECH-5
  `12_TERMINATION_MATCHED_CONTROLS.csv` (termination windows).
- No wallet/order-flow data. Relative repricing is NEVER called capital flow.

## 2. Event cohort & outcome families

Hierarchical, precedence-documented families (unchanged from MECH-5):

| Family | Members | n |
|---|---|---|
| SUCCESS / sustained propagation | BROAD_RISK_EXPANSION, LARGE_ALT_ROTATION, MID_CAP_ROTATION, ETH_BROADENING | 27 |
| REENTRY / snapback | BTC_CONCENTRATION | 52 |
| MIXED / no clear route | MIXED_NO_CLEAR_ROUTE | 44 |
| OTHER (excluded from binary success/failure; censored in WS5) | STABLECOIN_PARKING, CAPITAL_EXIT | 2 |

Success/failure binary used only where preregistered: `SUCCESS_LABELS` vs
`FAILURE_LABELS = REENTRY ∪ MIXED` (n=123 primary). Transient-touch vs
sustained-dwell distinctions from MECH-4 are preserved.

## 3. Subperiods & cycles

- Subperiods (from `daily.subperiod`): 2020-2021 (554d), 2022 (338d), 2023
  (344d), 2024 (357d), 2025-2026 (600d).
- Condition axes (existing canonical flags): BTC_UP/DOWN, VOL_HIGH/LOW,
  BREADTH_EXPANDING/CONTRACTING, ETH_STRONG/WEAK, RISK_ON/OFF, CONC_RISING/FALLING.

## 4. State atoms (see 02_STATE_ATOM_DICTIONARY.md)

Atoms are computed from daily-frame columns with fixed, documented thresholds —
no threshold is fit to outcomes. Three families:

1. **Canonical state axis:** `daily.state` (10 states).
2. **Coordinate axes** (mutually exclusive within axis):
   BREADTH_EXPANDING/FADING/STABLE; RANK_RECRUITING/STALL/DETERIORATING;
   CONC_RISING/FALLING; ETH_STRONG/WEAK.
3. **Composite micro-state** (single daily label, documented priority):
   RANK_RECRUITMENT → BREADTH_FADE → BREADTH_EXPANSION → CONCENTRATION_REBUILD →
   CONCENTRATION_RELEASE → ETH_IMPROVING → ETH_WEAKENING → BTC_SUPPORT →
   BTC_WEAKNESS → NEUTRAL. Priority reflects the MECH-5-established ordering
   (depth/breadth are route-gate coordinates; BTC is background).

## 5. Workstream preregistrations

### WS1 — Micro-state event atlas
125 events × horizons {0,1,2,3,5,7,10,14,21,30}: canonical state, composite
micro-state, per-axis atoms, breadth/rank/concentration/ETH/BTC coordinates,
volatility, leadership width, dispersion, chain TVL. Output
`03_MICROSTATE_EVENT_PANEL.parquet` + dictionary. No inference in WS1 — it is
the raw material.

### WS2 — Local sequence discovery
- **Event-anchored:** for each event, sequence = atom tuple over horizon
  lattices {t0,t1,t3}, {t0,t3,t7}, {t0,t7,t14}, on canonical-state, composite,
  breadth-axis, rank-axis atoms. Effective independent count = n (each event is
  one observation; 125 max).
- **Panel scan:** composite micro-state daily series; state-change paths
  (consecutive runs collapsed) of length 3. Effective count = number of
  bounded paths (each bounded by state changes).
- For every candidate: raw count, effective count, cycle counts, median
  duration, outcome distribution (success/reentry/mixed by +7D / +30D), lift vs
  marginal-product baseline, percentile bootstrap CI (B=500), BH-FDR across all
  scanned tuples.
- **Promotion rules (named LOCAL_SEQUENCE):** effective ≥ 50 AND present in
  ≥ 3 subperiods AND lift ≥ 1.25 AND FDR q < 0.10 AND not a trivial restatement
  of the outcome label.
- Otherwise: GLOBAL_SEQUENCE / CONDITIONAL_SEQUENCE / LOCAL_SEQUENCE /
  DESCRIPTIVE_SEQUENCE / LOW_SAMPLE_CURIOSITY / NULL / DISSOLVE.

### WS3 — Breadth transmission anatomy
Breadth coordinates: level (top500_breadth_30d), velocity (5D change),
acceleration (5D change of velocity), persistence (share of next-7D days above
release level), depth (deeper-band recruitment, med_ret30_201_500 relative to
11-50), divergence (breadth vs market-return sign disagreement), exhaustion
(breadth falling while level high), recovery (post-retrace rebound). Questions
Q1-Q7 (which changes first; best discriminator; sufficiency of expansion;
stall-before-failure; acceleration beyond level; late decay = failure vs
maturation; per-class breadth signatures). Tests: rank-sum, univariate AUC,
nested logistic (+Δlogloss/Brier/AUC, purged CV), all with BH-FDR.

### WS4 — Failure motif refinement (EARLY_SNAPBACK n=28, BREADTH_FADE n=23)
Profile geometry: breadth at release, rank recruitment, BTC context, dispersion,
concentration-rebuild speed, time-to-reentry / time-to-peak, decay speed, price
during fade, fade-vs-route-failure timing. Subfamily splits (BTC_UP/DOWN,
breadth high/low, cycle) with FDR. **n < 50 ⇒ subfamilies stay
DESCRIPTIVE/LOW_SAMPLE — never named promotion.**

### WS5 — Two-clock prospective competing-risk
At-risk = 125 releases; competing events REENTRY (52), MIXED (44),
PROPAGATION (27), OTHER (2, censored). Daily cause-specific hazard
h_k(h) = resolves-to-k at h / at-risk(h); cumulative incidence; state-conditioned
hazards by release-day regime flags and by rank-recruitment tercile.
Censoring: unresolved within 30D. This is PROSPECTIVE — no conditioning on
eventual outcomes.

### WS6 — Local termination microsequences
Success events (n=27): first-decline ordering of breadth/vol/top3-share/ETH-rel/
BTC-ret/deeper-rank/dispersion within 14D before termination; termination
signature classes (BREADTH_FIRST, VOL_FIRST, CONC_REBUILD_FIRST, ETH_FIRST,
ABRUPT). **n < 50 ⇒ DESCRIPTIVE_ONLY.**

### WS7 — Conditional local-rule audit
Each promoted/near-promoted sequence's outcome rate conditioned on the 6
condition axes + state-age terciles + cycle. Fisher exact + BH-FDR.
Classification: GLOBAL / CONDITION_DEPENDENT / CYCLE_LOCAL / NULL.

### WS8 — Alpha-role registry (research preparation ONLY)
Every earned statistic tagged with roles (STRUCTURAL_STATE, REGIME_FILTER,
TRANSITION_GATE, DIRECTION, DISTRIBUTION, VOLATILITY_POTENTIAL,
TEMPORAL_DELIVERY, PROPAGATION_DEPTH, FAILURE_FILTER, DECAY_TERMINATION,
REROUTING, LOCAL_CLUSTER, RISK_CONTEXT, EXECUTION_CONTEXT, UNKNOWN) + evidence
level, n, conditionality, known nulls, data limits, causal level, redundancies.
NO trades, NO thresholds for execution, NO weights, NO PnL.

### WS9 — Node graph update
Nodes/edges across MECH-1..6 with node_id, type, local/global, condition,
parent/child state, median latency, n_effective, effect, confidence, causal
level, alpha_role, status. Edge types: PRECEDES, CONDITIONS, GATES, CO_OCCURS,
FOLLOWS, TERMINATES, REENTERS, RECRUITS_DEPTH, DISSOLVES_TO, UNKNOWN.

## 6. Statistical discipline

- BH-FDR for every multi-test family; retain all failed cells.
- Bootstrap B=500 (percentile CI); permutation B=500 with finite-sample
  corrected p = (k+1)/(B+1); minimum reportable p ≈ 0.002.
- Purged/chronological
  splits for nested models (embargo ≥ outcome window).
- No future data used to define states at t. No causal claim above L2
  (conditional lead-lag) without mechanism support.
- MINIMUM OBSERVATION RULE: ≥ 50 effective independent observations + ≥ 3
  subperiods for named LOCAL_NODE/LOCAL_SEQUENCE; else LOW_SAMPLE_CURIOSITY.

## 7. Decision rubric

- `PASS_MECH6_MICROSTATE_SEQUENCE_ATLAS` — ≥1 promoted LOCAL_SEQUENCE (≥50
  effective, ≥3 subperiods, FDR-corrected lift) AND breadth transmission stage
  structure earned.
- `PASS_MECH6_WITH_LIMITATIONS` — breadth transmission + prospective two-clock
  survive, but no sequence reaches the naming bar.
- `FAIL_MECH6_NO_RECURRING_STRUCTURE` — no stable addition; breadth claims
  collapse under perturbation.
- `DATA_BLOCKED_MECH6` — observation layer insufficient for the questions.

PASS does NOT mean profitable. Files existing is NOT completion — each artifact
must answer its scientific question.
