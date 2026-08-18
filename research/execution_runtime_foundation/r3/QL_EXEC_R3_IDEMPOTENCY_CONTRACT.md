# QL-EXEC-R3 — Idempotency Contract

Three independent idempotency layers:

1. **Strategy event** — `strategy_events` keyed by `event_id` (scoped to
   strategy + deployment_generation). Re-observing the same event is a no-op.
2. **Journal** — `runtime_events.dedup_key` UNIQUE; re-appending the same fact
   returns the existing seq.
3. **Execution intent** — deterministic `intent_id` + UNIQUE primary key.
   Re-deriving the same upstream inputs yields the same id; the second
   `create_intent` is a no-op (no second exposure).

## Rule

The runtime may trust `StrategyAdapter.event_id` only when it is non-empty and
scoped to strategy + deployment generation. The runtime never generates a
random replacement id for a duplicate event.

Result: same event after restart/retry cannot create a second exposure; a
duplicate strategy event produces no duplicate order.
