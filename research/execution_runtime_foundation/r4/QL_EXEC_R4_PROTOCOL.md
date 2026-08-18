# QL_EXEC_R4_PROTOCOL — TB Full Nonregression Migration Harness

Checkpoint: `QL-EXEC-R4-TB-FULL-NONREGRESSION-MIGRATION-HARNESS`
Base: `b94fbbae897cd8b81e21408ee91bdbb7b0925553` (R3, 309/309 PASS)

## Question

Can the proven TB Forward strategy and runtime semantics be represented
faithfully through the generic R3 runtime substrate, **without** changing
strategy science, market-data semantics, signal timing, capital semantics,
broker semantics, ownership, recovery behavior, or runtime state semantics?

## Answer (this checkpoint)

Yes — for offline/replay parity. Two execution paths (reference PATH A and
generic PATH B) are fed identical frozen bars and compared surface-by-surface:

- Strategy science: **EXACT** (both reuse the canonical `TriangularBasisLiveEngine`).
- Market data: **EXACT** (raw bar-open-time key, common closed bar, fail-closed).
- Execution: **EXACT** (model-weight -> notional -> lots, basket open/close).
- Failure recovery: **EXACT** final broker state (broken hedge flattens owned).
- Restart/crash: **EXACT** (no duplicate resubmission, reconstruct from broker).
- Ownership/foreign: **EXACT** (foreign positions never touched).
- Causality: **EXACT** (future perturbation + truncation invariance).
- Purity: no Capital Routing science, no MetaTrader5 in the generic runtime,
  no real broker, no active TB writes.

## Boundaries (NOT done)

- No active TB replacement, no Task Scheduler change, no live/real orders.
- No multi-account/fleet, no portfolio master, no TradeLocker, no copier.
- No Capital Routing A/B / 70-30 / H1 / pos_t / 1R.
- R3 GenericRuntime stays single-leg; the multi-leg basket is a NEW orchestration
  layer (`BasketOrchestrator`) above `BrokerSession` (documented R4 extension).

## Pass gates

All 20 R3 gates plus R4-specific: strategy parity, market-data parity,
execution parity, runtime parity, primary-shadow zero-order, foreign-position
protection, restart duplicate prevention, causality, and purity. Result: PASS.

## Next

Recommend `QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN`. R4 PASS is
offline/replay parity only — it does NOT authorize active migration.
