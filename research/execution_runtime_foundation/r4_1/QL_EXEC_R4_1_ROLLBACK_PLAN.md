# QL-EXEC-R4.1 — Rollback Plan

Rollback is trivial and does not touch the active TB stack.

## Steps

1. `shadowctl stop` — terminate the generic shadow process.
2. Delete or retain the isolated state directory
   `shadow_state/tb-generic-shadow-g1/` (retention is safe; deletion is safe).
3. Leave legacy TB completely untouched.

## Why no broker cleanup is needed

The generic shadow never owns broker positions. It has no write API, so there
is nothing broker-side to unwind.

## Non-goals

- No active TB state rollback.
- No Task Scheduler change.
- No credential revocation (none were created).

## Rollback trigger conditions

- any MISMATCH in a safety-relevant parity surface (signal/entry/exit/
  direction/quantity/session/ownership)
- broker_write_calls != 0 (immediate hard stop + investigation)
- shadow resource bound exceeded and throttling insufficient
- operator decision

Shadow remains orderless in every trigger path.
