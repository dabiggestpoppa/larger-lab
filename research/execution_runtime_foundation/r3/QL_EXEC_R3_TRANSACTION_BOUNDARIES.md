# QL-EXEC-R3 — Transaction Boundaries

## Write-ahead discipline

```
TX1:  create_intent(ExecutionIntent)  -> commit        (durable intent)
----  broker boundary (NO SQLite write transaction held) ----
      broker.submit_order(order_intent)
TX2:  update_intent(...) + record_broker_order(...)    -> commit
      + upsert_owned_position(...)                      -> commit
```

- No broker call ever occurs inside a SQLite write transaction.
- The crash window between TX1 and TX2 is handled by reconciliation on restart,
  never by blind resubmission.

## Other transaction boundaries

- Event acceptance/idempotency (`record_strategy_event`) commits atomically.
- Capital decision + economic target + intent write-ahead each commit before
  the next stage.
- Position-state transitions (FILLED -> CLOSE_PENDING -> CLOSED) commit
  separately so no impossible partially-committed local state exists.

## Truthful exactly-once language

R3 does NOT claim distributed exactly-once execution. It guarantees:
- idempotent intent (deterministic id),
- at-most-one intended exposure (journal + intent UNIQUE),
- reconciliation-driven duplicate prevention.
Broker/network uncertainty prevents magical exactly-once semantics.
