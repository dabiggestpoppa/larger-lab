# QL-EXEC-R3 — Runtime State Machine

Frozen states (`runtime/state.py`):

`CREATED, STARTING, CONNECTING, WAITING_FOR_BROKER, IDENTITY_CHECK,
RECONCILING, WARMING, RUNNING, BLOCKED, STOPPING, STOPPED, FAILED`

## Key transition chains

Startup:
`CREATED -> STARTING -> CONNECTING -> IDENTITY_CHECK -> RECONCILING -> WARMING -> RUNNING`

Steady state loop:
`RUNNING -> RECONCILING -> RUNNING` and `RUNNING <-> BLOCKED`

Broker unavailable:
`CONNECTING/RUNNING/BLOCKED -> WAITING_FOR_BROKER -> CONNECTING -> ...`

Stop:
`RUNNING/BLOCKED/WAITING_FOR_BROKER -> STOPPING -> STOPPED`

Startup gates:
- `STARTING -> BLOCKED` on config/generation drift.
- `STARTING -> STOPPED` when desired state is STOPPED_BY_USER.
- `STARTING -> FAILED` on schema/identity-store corruption.

Terminal: `STOPPED`, `FAILED` (nothing proceeds without operator/human action).

## BLOCKED vs FAILED

- `BLOCKED` = alive, new-risk authority denied for an explicit condition
  (identity mismatch, reconciliation ambiguity, broker unavailable, config
  drift). Recoverable.
- `FAILED` = the runtime cannot operate coherently (store corruption, schema
  mismatch, singleton conflict). Terminal.

Every transition is validated against a frozen graph; an invalid transition
raises `InvalidStateTransition` (fail closed).
