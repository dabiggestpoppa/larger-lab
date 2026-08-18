# QL-EXEC-R3 — Heartbeat Contract

Durable, lightweight heartbeat (no sensitive secrets).

Fields: `runtime_id, state, desired_state, observed_at, broker_connected,
last_reconciliation_state, last_strategy_event_id, blocking_reason`.

- Persisted to the `heartbeats` table.
- Frequency is configurable via the injected clock; tests use deterministic
  ticks (one heartbeat per `step()`).
- No production frequency is hardcoded from TB.

## Telemetry

`TelemetrySnapshot` is read-only: `runtime_id, account_id, strategy_id,
runtime_state, desired_state, broker_connected, identity_match,
reconciliation_state, reconciliation_clean, new_risk_authorized,
owned_positions_count, foreign_positions_count, unresolved_intents,
last_heartbeat, last_error, blocking_reason, blockers`.

No dashboard control surface (no execution buttons); future dashboard is
read-only by default.
