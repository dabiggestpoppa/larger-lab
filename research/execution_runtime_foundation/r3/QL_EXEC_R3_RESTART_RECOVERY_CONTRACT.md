# QL-EXEC-R3 — Restart Recovery Contract

On restart the runtime NEVER submits blindly. It reads the durable intent,
reads broker truth, reconciles, and determines whether the order/position
already exists, then continues.

## Crash window handling

- **Crash after intent, before submit** (`AFTER_INTENT_COMMIT`):
  local `INTENT_CREATED`, broker flat -> `LOCAL_INTENT_BROKER_MISSING` ->
  safe retry of the SAME deterministic intent (no duplicate possible).
- **Crash after broker accept, before local result** (`AFTER_BROKER_SUBMIT`):
  local `INTENT_CREATED`, broker has the position ->
  `BROKER_OWNED_LOCAL_MISSING` -> reconstruct `OPEN_VERIFIED` WITHOUT resubmit.
- **Crash during close** (`AFTER_CLOSE_SUBMIT`):
  local `CLOSE_PENDING`, broker flat -> `CLOSED_MATCH` -> mark closed; broker
  still holds -> `CLOSE_RETRY`.

## Desired state on restart

- `RUNNING` -> full cold-start reconstruction.
- `STOPPED_BY_USER` -> remain stopped; do not connect/execute.
- Unexpected crash -> desired state stays `RUNNING`.

## Generation change

A deployment-generation change is detected (`GENERATION_DRIFT`) and blocked.
Existing unresolved owned exposure from an old generation is never silently
assumed by the new generation.
