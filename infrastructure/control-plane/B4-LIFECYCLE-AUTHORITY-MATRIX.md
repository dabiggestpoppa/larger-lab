# Book 4 — Lifecycle Authority Matrix (B4-CXR4R6 / CXR4-08)

One principle governs every lifecycle command:

> **No lifecycle command may acquire more authority merely by being called.**

Each command's authority is enumerated below. Two separate layers must both
hold for any mutation:

1. **Source precedence** (`default < file < environment < cli`) — which input
   wins when sources disagree.
2. **Actor authority** (policy / operator / operator:po) — whether the actor
   is authorized to change policy at all.

And the activation invariant (B4-CXR4R3/R4):

> **NO DATABASE OR INFRASTRUCTURE MUTATION OCCURS BEFORE THE BOOK 4
> AUTHORITY GATE** (validated effective config + resolved governed secret,
> frozen into an `ActivationContext`).

## Commands

| Command     | Config gate | Runtime readiness | May initialize | May mutate secret store | May mutate PostgreSQL | May start containers | May start worker/API | Destructive authority needed | Usable under broken config (emergency) |
|-------------|-------------|-------------------|----------------|-------------------------|-----------------------|----------------------|----------------------|------------------------------|----------------------------------------|
| configure   | no          | no                | **YES**        | YES (one-time init only) | no                    | no                   | no                   | no                           | yes (initialization path)              |
| doctor      | yes (read)  | yes (read)        | no             | no                      | no                    | no                   | no                   | no                           | yes (observes, never mutates)          |
| start       | yes         | yes                | yes (first run only) | no (existing store is READ-ONLY) | yes (migrations after gate) | yes (after gate) | yes (after gate)     | no                           | no                                    |
| restart     | yes (activation half) | yes     | no             | no (existing store is READ-ONLY) | yes (migrations after gate) | yes (after gate) | yes (after gate)     | no                           | shutdown half yes; activation half no  |
| recover     | yes         | yes                | no             | no (existing store is READ-ONLY) | yes (migrations after gate) | yes (after gate) | yes (after gate)     | no                           | no                                    |
| migrate     | yes         | yes                | no             | no                      | yes (exact governed DB only) | no                | no                   | no                           | no                                    |
| wait-ready  | no          | no                 | no             | no                      | no                    | no                   | no                   | no                           | yes                                   |
| smoke       | yes (read)  | no                 | no             | no                      | no                    | no                   | no                   | no                           | no (needs a live API)                  |
| stop        | **no**      | **no**             | no             | no                      | no                    | no (down)            | no (terminate)       | no                           | **yes — safe shutdown is always allowed** |
| destroy     | no          | no                 | no             | no                      | no (volume removal)   | no (down -v)         | no (terminate)       | **YES — explicit `--yes`**     | yes (explicit authorization)           |

## Authority classes

- **INITIALIZATION**: `configure` only — the one-time materialization of the
  local runtime secret (B4-CXR4R1). Once the store exists, ordinary
  start/restart/recover/configure are READ-ONLY over it; an ambient
  `POSTGRES_PASSWORD` can never rewrite, rotate, or erase it.
- **ACTIVATION**: `start` / restart's activation half / `recover` — the full
  pinned readiness gate (`create_activation_context`) runs FIRST; compose up,
  migrations, and process launch happen only after it passes (B4-CXR4R4).
- **DATABASE MUTATION**: `migrate` — full pinned authority first, and the
  target must be the EXACT governed PostgreSQL identity (host + port + db +
  user + governed credential authority; B4-CXR4R4).
- **OBSERVATION**: `doctor`, `smoke`, `wait-ready` — read-only.
- **SAFE SHUTDOWN**: `stop` — must remain available even under an invalid
  config; terminating known PID-file-owned processes and `compose down` never
  requires a healthy configuration.
- **DESTRUCTION**: `destroy` — removes the durable PostgreSQL volume and
  requires the explicit `--yes` confirmation; never triggered implicitly.

## Override authority

- Policy-owned settings (`sandbox.strict`, `workers.egress`, `redis.mode`,
  `execution.*`, `cloud.*`, `logging.redact_*`, `sessions.auth_required`,
  `capital.authority`, `control_plane.public_listen`) cannot be weakened by
  file/env/CLI/operator input (B4-CXR3R4).
- A configuration override becomes authoritative ONLY through a PROVEN
  append-only durable audit sink (B4-CXR4R5); without one, overrides are
  blocked — durability is never duck-typed.
