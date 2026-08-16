# TB-R3 — Persistence / Reconciliation Report

**Status: PASS** — durable, append-only, restart-safe truth layer built and
verified without touching strategy science.

## What was built

### New code (`quant-lab/tb_live/`)

| file | role |
|------|------|
| `state_machine.py` | Frozen R3 durable basket lifecycle (15 states, 25 valid transitions, terminal `BLOCKED_UNKNOWN_STATE`). Distinct from the adopted atomic-execution layer's internal BasketState. |
| `persistence.py` | `BasketLedger` — SQLite+WAL append-only event ledger, schema v1, monotonic seq, idempotency via UNIQUE `dedup_key`, write-ahead (intent persisted before execution), startup integrity check, reconstruction solely from durable records. |
| `reconciliation.py` | `Reconciler` + `BrokerStateView` — broker-vs-local comparison, frozen classification set, explicit broker ownership rules, manual-intervention detection, never flattens anything. |

### Modified (`quant-lab/mt5/triangular_basis_executor.py`)

* `ExecutionLayerBrokerView` adapter exposing execution-layer positions to the
  reconciler.
* `open_ledger()` + `reconcile_on_startup()` — startup gate: integrity check →
  reconstruct → reconcile → only then the SHADOW loop (any block → fail
  closed).
* Loop wiring: `SIGNAL_REJECTED` / `SIGNAL_OBSERVED` per bar,
  `BASKET_INTENT_CREATED` **before** any execution (write-ahead),
  `EXIT_SIGNAL_OBSERVED` on close, `ENGINE_STARTED`/`ENGINE_SHUTDOWN`/`ENGINE_BLOCKED`.
* Fixed latent `NameError`: `TRIANGLE_SYMBOLS` was referenced in `run_loop`
  but never defined.

### Test suite (`quant-lab/engines/tb_r3_tests.py`) — 40 tests

State machine (4), ledger basics (5), idempotency/write-ahead/control
isolation (5), crash/restart reconstruction (10), reconciliation cases A–N
(11), integrity failure modes (7), executor shadow-loop wiring (1), zero-order
guarantee (1).

## Verification

| suite | collected | passed | failed | skipped |
|-------|-----------|--------|--------|---------|
| TB-R3 | 40 | 40 | 0 | 0 |
| TB-R1.1 | 36 | 36 | 0 | 0 |
| TB-R2 | 26 | 26 | 0 | 0 |
| TB-P6 | 411 | 411 | 0 | 0 |
| TB-P7 | 160 | 160 | 0 | 0 |
| R2 historical parity | 265,809 bars | PRIMARY 194/194, CONTROL 405/405, 0 mismatches, max z diff ~9.25e-13, no forming-bar leakage | — | — |

## Key verified facts

1. **Append-only durable ledger** — SQLite+WAL, no update/delete API.
2. **Explicit basket state machine** — invalid transitions fail closed at
   append time AND at startup integrity check.
3. **Write-ahead** — `BASKET_INTENT_CREATED` persisted before execution;
   crash between intent and fills reconstructs to LOCAL_ONLY → FLAT_VERIFIED.
4. **Restart reconstruction** — a fresh ledger on the same file reconstructs
   state/direction/legs from durable records alone.
5. **Broker reconciliation** — cases A–N enforced by tests (MATCHED /
   BROKER_ONLY / LOCAL_ONLY / PARTIAL_MATCH / ORPHAN_POSITION /
   UNKNOWN_POSITION).
6. **Partial basket** → BROKEN_HEDGE classification, BLOCKED (never silently
   flattened; R3 invents no live recovery).
7. **Orphan TB basket** detected; **foreign-magic positions** never altered
   and never block the TB engine; **TB-magic without linkage** → ORPHAN,
   blocked.
8. **Manual intervention** detected via recorded-ticket-vs-broker diff.
9. **Idempotency** — duplicate intent/fill/close/reconcile events are no-ops.
10. **Corruption** — schema mismatch, sequence gap, payload-hash mismatch,
    invalid transition, missing states, DB lock/corruption all fail closed.
11. **Control isolation** — CONTROL events never touch executable basket
    state.
12. **order_send unreachable** — persistence/reconciliation modules contain
    no call sites and no MetaTrader5 import; the executor's own source calls
    `order_send(` nowhere (verified by test).

## Open risks / notes

* `max_signal_bar_age_s`, quote-age and skew tolerances remain
  `PROVISIONAL_EXECUTION_SAFETY_LIMITS` (not PnL-validated) — unchanged from
  R2.
* Reconciliation classifies and blocks; the actual flatten/close actions when
  execution is eventually authorized remain the atomic execution layer's
  domain (R5 / later gates).
* The R1 audit harness's 5 stale-API failures are pre-existing since R1.1
  (signed-exit repair replaced the old boolean/naive-exit API); they are not
  an R3 regression and the R1.1 suite (36/36) tests the new semantics.

## Scientific changes

**NONE.** basis, z (lookback 200, ddof=0, previous-bars-only), entry
(strict >3.0 / >2.5), signed exits (±0.25 / 0), z=6 stop, session
(fixed UTC-5 London 3–12 EST), weights (TB-B), re-entry, and cost semantics
are untouched. Parity reproduced exactly.

## Execution authorization

NOT_AUTHORIZED · demo=false · live=false · control execution=false ·
order_send unreachable in default mode.

## Next recommended checkpoint

**TB-R4-FULL-ENGINE-REPLAY-AND-FAILURE-SEAL** — combine R2 market data + R1.1
strategy + TB-B weights + execution contract + atomic mock layer + R3 durable
state into one end-to-end replay (normal lifecycle, restart lifecycle,
latency, duplicate signals, partial fills, disconnects, crashes, stale data,
manual changes). Demo authorization comes only after that seal.
