# MVE CAUSALITY CONTRACT

> **Checkpoint:** MVE-R0.5-CAUSALITY-GATE (2026-08-15)
> **Rule:** `output at time t = f(information available at or before t)`.
> Future bars must never modify historical values, timestamps, anchors,
> volatility states, acceptance timestamps, rekey timestamps, or events.

## Classifications

| Class | Meaning | Consumable by a live signal? |
|---|---|---|
| `CAUSAL_REALTIME` | knowable at bar t using only data <= t | yes |
| `CAUSAL_DELAYED_CONFIRMATION` | event occurs at t, knowable only after N confirmation bars; event time != knowledge time | yes, only at knowledge time |
| `EX_POST_ONLY` | event-study labeling / descriptive statistics over the whole sample | no, never |
| `CAUSAL_VIOLATION` | backdates: places a value at t using bars after t | no — blocker |
| `BLOCKED_SCIENTIFIC_IMPLEMENTATION` | stub / crashes / placeholder; scientific logic not yet authorized | no |

## Component classification (every public method)

### `volatility.py` — VolatilityEstimators
| Method | Class |
|---|---|
| `calculate_all_estimators` | CAUSAL_REALTIME |
| `_close_to_close_volatility` | CAUSAL_REALTIME (trailing rolling std) |
| `_ewma_volatility` | CAUSAL_REALTIME (trailing ewm) |
| `_parkinson_volatility` | CAUSAL_REALTIME (trailing rolling) |
| `_garman_klass_volatility` | CAUSAL_REALTIME (trailing rolling; uses `highs.shift(1)` = past) |
| `_atr_normalized_volatility` | CAUSAL_REALTIME (trailing rolling) |
| `_mad_volatility` | CAUSAL_REALTIME (trailing rolling apply) |
| `_garch_volatility` | CAUSAL_REALTIME — **note:** simplified rolling-std stand-in, not a real GARCH fit; scientific fidelity unverified (not a causality issue) |
| `analyze_estimator_quality` / `evaluate_estimator_quality` / `_calculate_estimator_quality` | EX_POST_ONLY (full-sample stats, correlation vs realized vol) |
| `get_best_estimators` | EX_POST_ONLY (consumes quality metrics) |
| `compare_volatility_fields` | CAUSAL_REALTIME given causal anchors; frozen sigma = first valid vol (series-prefix constant — causal, but a fragile convention; see Anchor Causality) |
| `analyze_volatility_regimes` | labels CAUSAL_REALTIME; transition probabilities EX_POST_ONLY (whole-sample histogram) |

### `anchors.py` — StructuralAnchors
| Method | Class |
|---|---|
| `_calculate_pivot_high` / `_calculate_pivot_low` | **CAUSAL_DELAYED_CONFIRMATION** — event at bar i, known at bar i+window (right-side comparison) |
| `_calculate_support_levels` / `_calculate_resistance_levels` | CAUSAL_REALTIME (trailing window incl. current) |
| `_calculate_trend_line` | CAUSAL_REALTIME (fit on window ending at i) |
| `_calculate_volume_profile` | CAUSAL_REALTIME (trailing) |
| `_calculate_time_based_anchors` | CAUSAL_REALTIME (trailing percentiles) |
| `_calculate_volatility_based_anchors` | CAUSAL_REALTIME (trailing) |
| `calculate_all_anchors` | mixed — composition of the above |
| `evaluate_anchor_quality` / `_calculate_anchor_quality` / `get_best_anchors` | EX_POST_ONLY |
| `get_weighted_anchors` | CAUSAL_REALTIME given causal inputs (weights are config) |

### `morphic_coordinates.py` — MorphicCoordinates
| Method | Class |
|---|---|
| `calculate_morphic_coordinates` | CAUSAL_REALTIME given causal anchors + volatility (elementwise at t) |
| `calculate_live_frozen_coordinates` | CAUSAL_REALTIME (frozen = first valid vol prefix constant) |
| `calculate_volatility_expansion_ratio` | CAUSAL_REALTIME (elementwise) |
| `classify_volatility_regimes` | CAUSAL_REALTIME (elementwise thresholds) |
| `calculate_sigma_states` | CAUSAL_REALTIME (elementwise) |
| `analyze_coordinate_statistics` / `calculate_coordinate_persistence` / `analyze_coordinate_regimes` / `calculate_coordinate_transitions` | EX_POST_ONLY (whole-sample descriptive) |
| `analyze_coordinate_trends` | EX_POST_ONLY (**uses `prices.shift(-1)` forward returns**) |

### `regime.py` — VolatilityRegimeModel
| Method | Class |
|---|---|
| `classify_displacement_regime` / `classify_expansion_regime` / `create_two_dimensional_state_map` | CAUSAL_REALTIME |
| `analyze_regime_transitions` / `create_regime_heatmap` | EX_POST_ONLY |
| `analyze_regime_persistence` | EX_POST_ONLY (**note:** computes "same-state" rate within each state's own rows — descriptive only) |
| `analyze_regime_specific_behavior` / `analyze_high_displacement_high_expansion` | EX_POST_ONLY (**uses `prices.iloc[idx+1]` forward returns**) |
| `analyze_regime_stability` | EX_POST_ONLY (**note:** contains placeholder values) |

### `sigma_states.py` — SigmaStates
| Method | Class |
|---|---|
| `classify_sigma_states` | CAUSAL_REALTIME (elementwise) |
| `detect_sigma_events` (+ `_detect_occupation/acceptance/continuation`) | CAUSAL_REALTIME (continuation uses trailing rolling window ending at i) |
| `analyze_event_statistics` / `analyze_event_regimes` / `calculate_event_transitions` / `evaluate_state_quality` / `get_best_states` / `analyze_event_time_metrics` / `analyze_event_regime_effects` | EX_POST_ONLY |
| `analyze_event_trends` | EX_POST_ONLY (**uses `prices.shift(-1)`**) |
| `analyze_event_state_transitions` | EX_POST_ONLY (**uses `states.iloc[idx+1]`**) |

### `acceptance.py` — AcceptanceCriteria
| Method | Class |
|---|---|
| `calculate_occupancy` / `calculate_all_occupancy` | CAUSAL_REALTIME (trailing window ending at i) |
| `classify_acceptance` | CAUSAL_REALTIME (elementwise on occupancy) |
| `calculate_rebalancing_fraction` | CAUSAL_REALTIME (uses `prices.iloc[i]` and `iloc[i-1]`) |
| `analyze_acceptance_statistics` / `analyze_acceptance_buckets` / `analyze_acceptance_quality` / `get_best_acceptance_levels` | EX_POST_ONLY |
| `analyze_acceptance_forward_returns` / `analyze_acceptance_regime_effects` / `analyze_rebalancing_effects` | EX_POST_ONLY (**use `prices.iloc[idx+horizon]` / `iloc[idx+1]`**) |

### `rekey.py` — MorphicRekey
| Method | Class |
|---|---|
| `_rekey_variant_a` (RKEY-A) | CAUSAL_REALTIME (re-anchor at the crossing bar using bars <= i) — CAUSAL_IMPLEMENTABLE |
| `_rekey_variant_b` (RKEY-B) | CAUSAL_DELAYED_CONFIRMATION — **repaired (R0.5.1):** anchor value formula unchanged, but activation moved from scan-origin i to the retest bar j (`rekey_event_time = i`, `known/active = j`); verified future-mutation and truncation invariant (max diff 0.0, was 1.033 pre-repair) |
| `_rekey_variant_c` (RKEY-C) | CAUSAL_REALTIME (trailing window only) — **repaired (R0.5.1):** NaN ready-guard, no `int(NaN)` crash, no synthetic rekeys |
| `calculate_rekey_variants` | composition of the repaired variants |
| `detect_rekey_events` | CAUSAL — emits schema-valid rekey events (R0.5.1) |
| `analyze_rekey_variants` / `analyze_rekey_effectiveness` / `analyze_rekey_continuation` / `analyze_rekey_trends` | EX_POST_ONLY (**use `prices.iloc[i+1]` forward returns**) |

### `signals.py` — SignalGenerator
| Method | Class |
|---|---|
| `generate_sigma_escape_signals` (Model A) | CAUSAL_DELAYED_CONFIRMATION — **repaired (R0.5.1):** signal known at the confirmation bar i+1; documented SHORT = mirror implemented (prior elif was dead code) |
| `generate_accepted_sigma_breakout_signals` (Model B) | CAUSAL_REALTIME — **repaired (R0.5.1):** cosmetic next-bar read removed (output never depended on bar i+1); realtime accepted-state signal; docstring retest-entry = BLOCKED_LOGIC_SPEC (never implemented) |
| `generate_recursive_morphic_trend_signals` (Model C) | CAUSAL_DELAYED_CONFIRMATION — **repaired (R0.5.1):** entry known at the +2-sigma confirmation bar; exit realtime trailing window |
| `generate_multi_timeframe_morphic_alignment_signals` (Model D) | BLOCKED_LOGIC_SPEC (contradictory conditions, ambiguous mapping — `MVE_R05_1_MODEL_D_AUDIT.md`); realtime elementwise; NaN guard added |
| `generate_morphic_trend_score_signals` (Model E) | BLOCKED_LOGIC_SPEC — **record corrected:** no NameError (prior "undefined n" was a misreading); Q component is a whole-sample scalar (measured repaint); excluded from execution |
| `generate_all_signals` / `combine_signals` | compositional |

### `backtest.py` — evaluation harness, not a signal source
`run_backtest` / `run_multi_asset_backtest` / `run_walk_forward_backtest` /
`run_sensitivity_analysis` / `run_monte_carlo_simulation` /
`run_cost_sensitivity_analysis` — EVALUATION. Post-hoc evaluation of signals;
not causal research components. Monte Carlo is simulation (test fixtures only).

## Enforcement

- `src/mve/causality.py` provides `future_perturbation_check`, `truncation_check`,
  `apply_anchor_delay`, `validate_acceptance_events`, `validate_rekey_events`,
  `assert_unique_events`.
- `tests/mve/test_causality.py` (35 tests) proves: volatility/coordinates/sigma/
  occupancy/acceptance/RKEY-A/RKEY-C/MTF future-mutation + truncation invariance;
  frozen-sigma invariance; pivot knowledge delay; H1 knowledge timing; schema
  validation; event dedup; holdout guard; fixture isolation; and records the
  RKEY-B and escape/breakout/recursive violations as findings.
