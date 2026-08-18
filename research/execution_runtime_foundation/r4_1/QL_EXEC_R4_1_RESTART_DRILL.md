# QL-EXEC-R4.1 — Restart Drill

One controlled generic-shadow restart is performed while legacy TB stays
running.

## Steps

1. Confirm legacy TB running and unaffected.
2. Record shadow normalized state (rolling window, latest common bar, basis,
   z, basket state, processed event cursor, desired state).
3. `shadowctl stop` (intentional) or kill the shadow process (crash drill).
4. Confirm active TB heartbeat continues normally throughout.
5. `shadowctl start`; runtime performs cold-start reconstruction from
   `shadow_state/tb-generic-shadow-g1/runtime.sqlite`.
6. Confirm: same rolling-state output after warmup, no duplicate shadow event,
   no duplicate hypothetical intent, broker_write_calls == 0.

## Pass criteria

- state reconstruction matches pre-restart state (STATE_RECONSTRUCTION parity)
- no duplicate event / intent
- desired state respected (RUNNING persists across crash; STOPPED_BY_USER
  stays stopped)
- active TB unaffected (heartbeat age stays green, no log errors)

## Crash drill (desired-state invariant)

Unexpected process death must NOT change shadow desired state. Emulate a new
runtime object reading the same store: desired state stays RUNNING; supervisor
(when it exists) is responsible for respawn.
