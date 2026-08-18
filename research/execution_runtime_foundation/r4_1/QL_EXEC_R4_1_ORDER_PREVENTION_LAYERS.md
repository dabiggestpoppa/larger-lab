# QL-EXEC-R4.1 — Order Prevention Layers (Defense in Depth)

Any single configuration mistake MUST NOT enable orders. Four independent
barriers are required; a broker write is possible only if ALL four fail, which
is a hard design failure.

## Layer 1 — Runtime authority gate

`GenericRuntime` authority profile pins:

- `can_submit_new_risk = false`
- `can_close_existing = false` for the shadow (no owned positions exist and
  none may be created)
- `shadow_mode = SHADOW_OBSERVE_ONLY`

The runtime refuses to enter any intent that would reach a submit call.

## Layer 2 — Read-only broker/session wrapper

`ReadOnlyBrokerSession` does not define `submit_order`, `close_position`, or
`cancel_order`. A denylist `__getattr__` raises `ShadowBrokerWriteDenied` for
those names. Even a caller holding a runtime reference cannot reach a write
call.

## Layer 3 — Deployment profile (immutable)

`TB-GENERIC-SHADOW-G1` profile carries an immutable `SHADOW_OBSERVE_ONLY`
mode. Profile hash is persisted at startup; drift blocks startup (R3
profile-drift gate). The shadow mode bit is part of the hashed profile, so
tampering to `LIVE` changes the hash and blocks.

## Layer 4 — Process/environment capability denial (optional, planned)

The shadow process runs with no broker credentials and no external-session
order authority token. In G1 (Option B) it additionally has no MT5 client at
all. This is capability denial at the environment level, not merely in code.

## Invariants to assert in tests

- `broker_write_calls == 0`
- `shadow_order_attempts == 0`
- hypothetical intents are constructed but never submitted
- blocked attempts (had the gate been absent) are counted as
  `execution_gate_denials`

## Telemetry counters (required, must equal 0)

- `broker_write_calls` — hard 0
- `shadow_order_attempts` — hard 0
- `hypothetical_intents` — informational (>= 0)
- `execution_gate_denials` — informational (>= 0)
