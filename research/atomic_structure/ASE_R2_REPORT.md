# ASE-2 — Empirical Transitions / Distribution Baselines

## Trader review

This checkpoint is descriptive only. No strategy PnL, optimization, execution-policy comparison, confirmation data, or holdout data was used.

1. **Current state prediction:** empirical transition tables are generated from observed development counts. They are reproducible descriptive relationships, not trading signals.
2. **Failure information:** failure-type transition tables are generated; sparse/unavailable next-event fields remain explicitly marked rather than filled with priors.
3. **Tier + time + state:** remaining-range baseline tables compare unconditional, tier, tier/state, loop-count, and balance groupings. In-sample summaries are diagnostic, not out-of-sample validation.
4. **Remaining range:** the canonical terrain provides 03/06/09/12 checkpoint ranges and final-range retrospective denominators; baseline quantiles are recorded separately.
5. **Noon extreme lock:** the existing ASE-1 terrain artifact ends at 17:00 only as a daily range summary and does not preserve post-noon OHLC path details. Noon touch/close-beyond probabilities are therefore `NOT_IDENTIFIABLE_FROM_TERRAIN_CENSUS`, not invented.
6. **Noon failure predictors:** no valid estimate can be made without retained post-noon bars and a causal ATR/variance source; this is marked unavailable.
7. **-25 lock:** the existing loop ledger does not contain the exact frozen CEREBUS -25 band-edge event geometry and retained post-hit path. Post-25 matrices are explicitly unavailable.
8. **Morning range / ATR:** no ATR series was present in the terrain artifact, so ATR-tail and lock-ratio calculations remain unavailable rather than fabricated.
9. **ML readiness:** ASE-2 produces usable empirical baseline infrastructure, but the unavailable noon/post-25 and lack of held-out scoring mean this checkpoint should be treated as **PARTIAL_TRANSITION_STRUCTURE**, not as authorization for ASE-3.

## Technical record

- Branch: `agent/atomic-structure-foundry`
- Source: ASE-1.1 development terrain, EURUSD M5
- Development: 2023-01-03 through 2024-12-31
- Sessions: 442
- Loop records: 11,252
- Bootstrap seed: 20260821; dependency unit: session/day; 2,000 resamples where estimable
- Event calendar: `EVENT_DATA_UNAVAILABLE`
- Causality inheritance: ASE-1.1 audit PASS; no future-derived labels were introduced as live features

Generated artifacts include state transition counts/probabilities, next-loop direction, failure transitions, remaining-range baselines and quantiles, timing/survival schemas, uncertainty layering, variance-clock availability status, noon/post-25 ledgers, ATR-related availability status, and bootstrap metadata.

## Decision

`PARTIAL_TRANSITION_STRUCTURE`: transition and remaining-range descriptive infrastructure is complete, but the current terrain schema cannot identify the required post-noon or post-25 path outcomes without additional source-path reconstruction. ASE-3 remains unauthorized.

Guardrails:

- `strategy_pnl_computed = false`
- `optimization_performed = false`
- `confirmation_consumed = false`
- `holdout_consumed = false`
- `ASE3_authorized = false`
