# QL-EXEC-R3 — Execution Intent Contract

`ExecutionIntent` (runtime/intent.py) is the write-ahead record persisted before
any broker submission.

## Deterministic identity

`execution_intent_id(...)` hashes canonical JSON over immutable
execution-semantic inputs:

```
runtime_id, account_id, strategy_id, deployment_generation, event_id,
economic_target_id, instrument, side, broker_quantity
```

- Prefix `EI1_` + sha256 truncated to 24 hex chars.
- NO random UUID. NO wall-clock time (execution identities never depend on
  wall time).

## Intent states

`INTENT_CREATED, INTENT_SUBMITTED, INTENT_FILLED, INTENT_PARTIALLY_FILLED,
INTENT_REJECTED, INTENT_TRANSPORT_ERROR, INTENT_CLOSED, INTENT_ABORTED`.

## Position states (owned)

`REQUESTED, FILLED, PARTIALLY_FILLED, CLOSE_PENDING, CLOSED, ABORTED`.

`CLOSE_PENDING` is the durable exit intent written before a close submission,
which is what makes crash-during-close recoverable.
