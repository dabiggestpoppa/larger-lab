# QL_EXEC_R4_MULTI_LEG_ORCHESTRATION

`MultiLegExecutionPlan` + `BasketOrchestrator`
(`execution_runtime/tb/basket.py`) is the strategy-agnostic multi-leg primitive
introduced to express basket/pair/hedge strategies above `BrokerSession`. It is
NOT a change to `BrokerSession` and carries NO TB symbols.

## Contract

- parent `plan_id` + ordered legs;
- per-leg deterministic `leg_intent_id` (plan + leg + symbol + side + quantity);
- dependency/order policy (sequential submit);
- fill verification (ownership tag + magic against broker truth);
- rollback/flatten policy (broken hedge -> close owned -> verify flat);
- completion condition (all legs filled -> OPEN; all owned flat -> CLOSED).

## Lifecycle

`CREATED -> PRECHECKED -> SUBMITTING -> OPEN`
`-> BROKEN_HEDGE -> FLATTENING -> ABORTED_FLAT`
`-> CLOSING -> CLOSED`
`-> RECONCILIATION_REQUIRED` (ambiguous).

## Write-ahead / idempotency

- Commit parent plan + every leg intent BEFORE the first broker call.
- Broker calls happen outside any SQLite write transaction.
- A replayed `plan_id` is an idempotent no-op (never a second exposure).
- On restart, `recover()` reconstructs OPEN / flattens partial / aborts,
  never blindly resubmits.

## Generalization rule

It is generalized only because basket/pair/hedge semantics are reusable for
other multi-leg strategies; it is not a TB-only class. TB symbols live only in
the adapter/harness fixtures, never in the orchestrator.
