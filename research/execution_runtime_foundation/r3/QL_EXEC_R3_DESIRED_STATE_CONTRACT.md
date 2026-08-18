# QL-EXEC-R3 — Desired State Contract

Desired states (`DesiredState`): `RUNNING`, `STOPPED_BY_USER`.

- Desired state is persisted in the `desired_state` table (durable).
- On startup, the runtime reads desired state BEFORE connecting/executing.
- `STOPPED_BY_USER` on restart => remain `STOPPED`; do NOT connect/execute.
- `stop()` persists `STOPPED_BY_USER`, then disconnects cleanly and releases
  the singleton lock.
- Unexpected process death does NOT alter desired state: desired state stays
  `RUNNING`; a future supervisor (R5-ish) restarts the worker.

## Open-risk policy on stop

R3 does NOT automatically abandon owned positions. Stop:
- stops new event production (no new risk),
- preserves the ability to reconcile/close owned risk if an exit is already
  pending (the close path is separately evaluable via authority),
- disconnects only once the close/reconcile path is consistent or no exit is
  pending.
