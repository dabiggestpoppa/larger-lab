# QL_EXEC_R4_REPORT — TB Full Nonregression Migration Harness

Status: **PASS**
Base: `b94fbbae897cd8b81e21408ee91bdbb7b0925553`
Tests: **355/355 PASS** (309 prior R1-R3 + 46 new R4)

## What was built

A side-by-side comparison harness proving the TB Forward strategy/runtime can be
expressed through the generic R3 substrate, without changing science or touching
the active deployment.

- `execution_runtime/tb/adapters.py` — TBStrategyAdapter (canonical engine),
  TBTranslationAdapter (sealed lot translation), transparent capital policy.
- `execution_runtime/tb/basket.py` — strategy-agnostic multi-leg
  `BasketOrchestrator` (write-ahead, broken hedge, close, recover, dedup).
- `execution_runtime/tb/parity.py` — 6-tier parity classification + trace
  normalization (semantics-preserving).
- `execution_runtime/tb/reference.py` — pure reference broker/executor (the
  canonical execution path ported without the MetaTrader5 import).
- `execution_runtime/tb/harness.py` — LegacyTBHarness (PATH A), GenericTBHarness
  (PATH B), ParityRunner.

## Key results

| surface | result |
|---|---|
| strategy (basis/z/thresholds/session/direction/weights) | EXACT |
| market data (raw open-time, common closed bar, fail-closed) | EXACT |
| translation (model weight -> notional -> lots) | EXACT (0.07/0.07/0.13) |
| normal open/close lifecycle trace + state | EXACT |
| primary shadow zero-order | EXACT (0 orders both paths) |
| broken hedge / leg rejects / partial | EXACT final state (ABORTED_FLAT) |
| restart flat/open/partial/close + crash windows | EXACT (no duplicate) |
| ownership / foreign protection | EXACT (foreign untouched) |
| causality (future perturbation, truncation) | EXACT |
| purity (no CR science, no MT5 in runtime, no active TB writes) | PASS |

## Safety-strengthening (nonregressive)

- Generic path emits explicit per-leg fill confirmation before broken-hedge
  flatten (more explicit journal).
- Generic path refuses to mark CLOSED while owned exposure remains.
- Duplicate owned leg is flagged rather than tolerated.
- These do not change normal-path behavior, economic quantity, or strategy
  decisions.

## Latent R3 fix

A wall-clock-derived `reconciliation_runs.run_id` could collide when start() and
step() reconcile within the same millisecond (surfaced under full-suite load).
Fixed in `RuntimeStore.record_reconciliation_run` with a monotonic suffix; the
deterministic prefix is preserved. No R1-R3 behavior change.

## NOT done / deferred

Active TB migration, Task Scheduler change, real MT5/broker, multi-account,
fleet supervisor, Capital Routing science, performance acceptance gates.

## Conclusion

The generic path has proven OFFLINE/REPLAY parity. This is NOT active
deployment authorization. Next checkpoint: R4.1 shadow-deployment PLAN.
