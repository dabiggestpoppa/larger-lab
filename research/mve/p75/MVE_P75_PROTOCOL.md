# MVE-P7.5 — CORE STATE SEAL (Pre-Registration)

> **Checkpoint:** MVE-P7.5-CORE-STATE-SEAL
> **Base commit:** bda32020d439a780e9aa4b7c2c45dd4254e533f0 (P7)
> **Status:** SEAL CHECKPOINT — no new alpha science
> **Date:** 2026-08-16

---

## 1. Purpose

Formally define, freeze, and verify the minimal scientifically surviving MVE
architecture after:

- P4 acceptance — REDUNDANT / PRUNED
- P6 rekey — REDUNDANT / PRUNED
- P7 Model A / Model B — REJECTED_REDUNDANT
- P7 Model C — ARCHIVED_CONDITIONAL_NOT_INCREMENTAL

The surviving scientific object is the **causal morphic field state**:

```
price
→ causal structural anchors (trailing extremes)
→ causal volatility normalization (close_to_close)
→ morphic coordinates (signed, vol-normalized)
→ sigma state (frozen quantization)
→ state transition / survival description
```

**The core state is a CAUSAL REPRESENTATION OF MARKET STRUCTURE.**
It is **NOT** a validated trading strategy, a positive-EV signal, a deployable
engine, or profitable alpha. P7.5 preserves this distinction everywhere.

## 2. NO NEW SCIENCE (frozen prohibitions)

P7.5 may NOT:

- invent signal models or thresholds
- optimize parameters
- run PnL / stops / targets / Kelly / sizing
- repair Model D or Model E
- promote Model C
- re-test acceptance or rekey
- read 2026 (FINAL_HOLDOUT_PENDING, holdout_rows_read = 0)
- use any blocked component (MODEL_D, MODEL_E, generate_all_signals)

P7.5 MAY:

- inspect existing sealed code
- run mechanical causality/dependency/parity checks
- create a deterministic core-state wrapper over sealed primitives

## 3. Core-State Contract

The wrapper `src/mve/core_state.py` must:

1. Input causal H1 bars (open/high/low/close/volume).
2. Produce per-bar core-state records using **only** sealed causal primitives:
   - trailing-extreme anchors (`P4_TRAILING_WINDOW=50`, `shift(1)` causal delay)
   - `close_to_close` volatility estimator
   - `coordinate_fields` / `per_boundary_signals` morphic coordinates
   - frozen sigma quantization
3. Reproduce exactly the canonical series from the sealed P7 pipeline:
   - anchor series (trail_hi / trail_lo)
   - volatility series (close_to_close)
   - coordinate series (signed x, upper family)
   - sigma-state series (signed floor quantization, P7 `control_fields` convention)
4. NOT import or call: `mve.signals` (Models A–E), `mve.p6_rekey`
   (predictive rekey), acceptance event machinery, `generate_all_signals`.
5. NOT contain strategy/PnL logic (no entries, stops, targets, sizing).

Schema fields (all causal; descriptive state variables only):

| field | definition |
|-------|-----------|
| timestamp | bar time (index) |
| anchor_type | "trailing_extreme_50" |
| anchor_up / anchor_lo | causal trailing extremes (shift(1)) |
| volatility_estimate | close_to_close vol |
| volatility_quality | causal coverage of vol (min_periods check) |
| coordinate | signed x (close basis, upper family) |
| abs_coordinate | \|coordinate\| |
| sigma_band | unsigned band floor(\|x\|) — P4/P6 convention |
| sigma_state | signed floor(x/STEP) — P7 convention |
| previous_sigma_state | shift(1) of sigma_state |
| state_age | consecutive bars in same sigma_state |
| transition_type | UP / DOWN / STAY vs previous sigma_state |
| distance_to_nearest_sigma_boundary | fractional part of \|x\| |
| coordinate_velocity | x - x.shift(1) |
| coordinate_acceleration | velocity - velocity.shift(1) |
| anchor_age | bars since trailing extreme last changed |
| data_quality | valid primitive coverage flag |
| causal_known_time | = timestamp (all inputs bar t use data <= t) |

No new predictive features. Only exposure of already-causal state variables.

## 4. Component Status (frozen)

| component | status |
|-----------|--------|
| anchors | CAUSAL_STATE_PRIMITIVE |
| volatility | CAUSAL_STATE_PRIMITIVE |
| morphic coordinates | CAUSAL_STATE_PRIMITIVE |
| sigma state | CAUSAL_STATE_PRIMITIVE |
| state transition | CAUSAL_DESCRIPTIVE_PRIMITIVE |
| acceptance | PRUNED_PREDICTIVE |
| RKEY-A | PRUNED_PREDICTIVE |
| RKEY-B | PRUNED_PREDICTIVE |
| RKEY-C | ARCHIVED_INSUFFICIENT_N |
| Model A | REJECTED_REDUNDANT |
| Model B | REJECTED_REDUNDANT |
| Model C | ARCHIVED_CONDITIONAL_NOT_INCREMENTAL |
| Model D | BLOCKED_LOGIC_SPEC |
| Model E | BLOCKED_LOGIC_SPEC |
| generate_all_signals | BLOCKED_AGGREGATE |

## 5. Parity Gate

The core-state wrapper output must match the sealed P7 pipeline series with
numeric tolerance 1e-9 (deterministic identity expected):

- anchor_up / anchor_lo vs P7 trailing extremes
- volatility vs P7 close_to_close
- coordinate vs P7 signed x
- sigma_state vs P7 control_fields sigma

Any mismatch = FAIL. No scientific changes permitted.

## 6. Causality Gates (bounded, mechanical)

Reuse the sealed causality harness on the core-state wrapper:

- future perturbation: max diff MUST be 0.0 (coordinate + sigma series)
- truncation invariance: MUST be 0.0
- static leakage scan: 0 blocked, 0 unknowns in `core_state.py`
- causal→ex-post dependency audit: 0
- blocked-component isolation: PASS (no signals / p6_rekey imports)

## 7. Holdout Lock

2026 is never read. Field truncated at 2025-12-31 before any computation.

- holdout_status = FINAL_HOLDOUT_PENDING
- holdout_rows_read = 0
- holdout_guard_pass = true

## 8. Artifacts (all under research/mve/p75/)

MVE_P75_PROTOCOL.md (this file)
MVE_P75_INPUT_HASH_MANIFEST.json
MVE_P75_CORE_STATE_DEFINITION.md
MVE_P75_CORE_STATE_SCHEMA.json
MVE_P75_COMPONENT_STATUS.csv
MVE_P75_FALSIFICATION_REGISTRY.csv
MVE_P75_LEGACY_ARCHITECTURE_MAP.md
MVE_P75_CORE_PARITY.json
MVE_P75_CAUSALITY_AUDIT.json
MVE_P75_MODEL_C_ARCHIVE.md
MVE_P75_HOLDOUT_GUARD.json
MVE_P75_REPORT.md
MVE_P75_DECISION.json

## 9. Tests (new tests/mve/test_p75_seal.py)

- core-state schema completeness
- anchor / volatility / coordinate / sigma parity vs sealed pipeline
- future perturbation = 0.0
- truncation = 0.0
- acceptance excluded, rekey predictive logic excluded
- Model A/B/C/D/E excluded, generate_all_signals excluded
- holdout guard (2026 never read)
- falsification registry integrity
- no strategy / PnL logic in core_state.py
- no promotion flags

Run: sealed 82 + P4 46 + P6 38 + P6.5 23 + P7 36 + P7.5 new tests.

## 10. Decision Values (frozen)

core_state_defined = true
predictive_alpha_validated = false
standalone_strategy_validated = false
economic_translation_ready = false
new_science_performed = false
best_trading_rule_selected = false
p8_authorized = false
holdout_status = FINAL_HOLDOUT_PENDING
holdout_rows_read = 0

## 11. Pass Gate

mve_p75_core_state_seal_pass = true ONLY IF all of: P7 conclusions frozen
correctly, no model rescue, minimal core defined, schema complete, wrapper
deterministic, parity passes, perturbation 0.0, truncation passes,
falsification registry complete, Model C disposition explicit, D/E blocked,
holdout untouched, no new science, no trading rule, P8 not auto-authorized,
tests pass.
