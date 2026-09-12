# OCE Local Ground — Operator Runbook (B1-LOCAL, A-003)

This runbook is the one documented walkthrough for operating OCE **without any
cloud account**. Default behaviour is always `local`. Cloud is deferred.

## 0. Prerequisites

- Git, Python 3.10+ (required for scripts and tests).
- Docker + Docker Compose v2 (required only for the container runtime; scripts
  and tests degrade honestly without it — telemetry renders `UNKNOWN`, never
  healthy).
- No cloud account, public domain, certificate, IP, or inbound port is
  required.

## 1. Bootstrap (idempotent)

```bash
bash infrastructure/local-ground/scripts/bootstrap-local.sh
```

Creates `infrastructure/local-ground/var/` and `compose/.env` from the example
only if absent; **never overwrites** an existing `.env`. Secrets are read from
the environment first, then `.env`. Startup validation **fails closed** when a
required secret is missing or still a placeholder.

## 2. Start, inspect, stop, restart

```bash
OCE_RUNTIME_TARGET=local bash infrastructure/local-ground/scripts/oce-ctl local up
OCE_RUNTIME_TARGET=local bash infrastructure/local-ground/scripts/oce-ctl local health
OCE_RUNTIME_TARGET=local bash infrastructure/local-ground/scripts/oce-ctl local status
OCE_RUNTIME_TARGET=local bash infrastructure/local-ground/scripts/oce-ctl local logs postgresql
OCE_RUNTIME_TARGET=local bash infrastructure/local-ground/scripts/oce-ctl local down
```

`local status` prints the independent ledger model:

```
local_ground_state:      BUILDING / VERIFYING / LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW
cloud_plan_state:        NOT_VALIDATED / VALIDATED_NO_APPLY
cloud_activation_state:  DEFERRED_BY_OPERATOR
cloud_deployment_state:  NOT_DEPLOYED
cloud_cost_state:        ZERO
next_local_book:         B2
operator_hold_reason:    CLOUD_PURCHASE_DEFERRED
```

Restarting the Compose stack does not lose authoritative state (PostgreSQL).

## 3. Backup and restore

```bash
bash infrastructure/local-ground/scripts/oce-ctl backup --out var/backups/manual-1
bash infrastructure/local-ground/scripts/oce-ctl restore --from var/backups/manual-1
```

Every backup carries `BACKUP_MANIFEST.sha256`; restore verifies size and hash
for every file and **rejects corrupt backups** without touching the target.

When the running stack is available, a backup also packages **authoritative
data**, not just `var/`:

- `postgres/dump.sql` — logical backup via `pg_dump` from the pinned image;
- `artifacts/artifacts.tar.gz` — the artifact volume (MinIO `/data`);
- `backup-info.json` — format, schema version, includes, created_at, RUN_ID,
  source commit, and tool versions (no secrets).

Restore applies the PostgreSQL dump and artifact contents into the running
container; it **fails closed** if the backup contains data but the required
runtime is unavailable. Redis is deliberately **not** restored — it is
disposable transport state, never authoritative truth. Clean-room recovery
destroys only Book 1 test volumes, recreates clean volumes, starts the stack,
and restores into them.

## 4. Local workers

```bash
bash infrastructure/local-ground/scripts/oce-ctl worker admit <envelope.json>
bash infrastructure/local-ground/scripts/oce-ctl worker reject <envelope.json>
```

Workers are bounded by `contracts/worker-task-envelope.schema.json`: allowed
paths/tools, authority, budget, time limit, expected outputs, forbidden
actions. Unauthorized envelopes are rejected.

## 5. Cloud plan / apply boundary (deferred)

```bash
OCE_RUNTIME_TARGET=cloud-plan bash infrastructure/local-ground/scripts/oce-ctl deploy validate --target cloud
OCE_RUNTIME_TARGET=cloud-plan bash infrastructure/local-ground/scripts/oce-ctl deploy plan --target cloud
OCE_RUNTIME_TARGET=cloud bash infrastructure/local-ground/scripts/oce-ctl deploy apply --target cloud   # DENIED
```

`validate` and `plan` are read-only and deterministic. `apply` **fails closed**
without an authorization envelope; no provider is ever contacted while
`cloud_activation_state=DEFERRED_BY_OPERATOR`.

## 6. Validation and evidence

```bash
bash infrastructure/local-ground/scripts/validate-local --evidence-dir <outside-repo-dir>
```

The shared runner produces identity, environment fingerprint, acceptance
output, cloud-plan, cloud-apply-denial, adversarial output, stage log/status,
`independent-gate.json`, and an `evidence-manifest.json` (SHA-256). On
failure it preserves diagnostics (compose ps, container inspect, bounded
logs, networks, volumes) and records a truthful cleanup outcome without
masking the original exit code. CI runs the same runner with a single
`OCE_RUN_ID`.

## 7. Recovery

The `local-recovery` profile exercises clean-room restore and clean rebuild.
No operator action loses canonical state: PostgreSQL is authoritative; Redis
is disposable transport; artifact content is checksummed and backed up.
