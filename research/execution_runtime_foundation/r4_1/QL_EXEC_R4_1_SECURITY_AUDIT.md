# QL-EXEC-R4.1 — Security Audit

## Secrets

- No plaintext broker credentials are duplicated or stored.
- No credentials appear in logs, telemetry, heartbeats, or artifacts.
- Preferred session mode is EXTERNAL_SESSION if concurrent-read behaviour is
  ever proven safe; G1 (Option B) does not even require a session, since it
  consumes exported snapshots.

## Order-authority denial

- ReadOnlyBrokerSession has no write API.
- Runtime `can_submit_new_risk = false` (pinned).
- Immutable `SHADOW_OBSERVE_ONLY` profile, hashed at startup.
- (Optional) process-level capability denial: no broker credentials / no MT5
  client in the shadow process.

## Isolation

- Separate runtime_id, state dir, SQLite, PID lock, logs, heartbeat, telemetry,
  desired state, deployment generation.
- No shared mutable state between shadow and active TB.
- No signal/registry/scheduler interference with active TB PIDs.

## Residual risks (documented, not hidden)

1. MT5 concurrent-read safety is UNRESOLVED — mitigated by choosing Option B
   (no concurrent access) for G1.
2. A hypothetical legacy export channel adds a read-only surface to the active
   stack — mitigated by making it additive and implementing it only under
   R4.2 review.

## Conclusion

The shadow cannot execute, cannot write active TB state, and stores no secrets.
