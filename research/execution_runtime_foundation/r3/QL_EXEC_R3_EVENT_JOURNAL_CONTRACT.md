# QL-EXEC-R3 — Append-Only Event Journal Contract

- `runtime_events` is append-only: historical events are never rewritten or
  deleted. Current state is materialized separately.
- Every journal row carries `seq` (monotonic), `event_id`, `event_type`, `ts`,
  `dedup_key` (UNIQUE), `payload`, `payload_hash`.
- `dedup_key` makes journaling idempotent: re-appending the same fact returns
  the existing seq instead of a second row.
- `payload_hash` = sha256 of canonical JSON (sorted keys) for integrity checks.

Journaled lifecycle facts include:
`EVENT_OBSERVED, CAPITAL_DECISION, TARGET_CREATED, INTENT_CREATED,
ORDER_SUBMITTED, ORDER_REJECTED, ORDER_TRANSPORT_ERROR, POSITION_OPEN_VERIFIED,
PARTIAL_FILL_OBSERVED, EXIT_REQUESTED, POSITION_CLOSED_VERIFIED, CLOSE_REJECTED,
RECONCILED`.

Event identity (`event_id`) from the strategy is trusted only when non-empty and
scoped to strategy + deployment generation (the `strategy_events` table stores
both). The runtime never fabricates replacement IDs for duplicates.
