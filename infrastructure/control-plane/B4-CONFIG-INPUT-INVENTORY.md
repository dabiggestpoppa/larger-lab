# OCE Book 4 — Configuration Input Inventory (B4-R3R, Defect R-02)

Every runtime-significant configuration input consumed by the local
control-plane runtime is enumerated here with its disposition under the Book 4
configuration spine. **No meaningful runtime setting may remain INVISIBLE to
the spine.**

Disposition classes:

- `CANONICAL` — controlled by the spine registry; validated fail-closed.
- `COMPATIBILITY_ADAPTER` — legacy input mapped into a canonical setting through
  a documented adapter with deterministic precedence and deprecation status.
- `INTERNAL_RUNTIME_DERIVED` — produced by OCE itself from canonical settings
  (never an operator input).
- `DEPRECATED_AND_REJECTED` — no longer accepted; setting it fails closed.
- `OPERATIONAL` — non-config variable (CI/worker plumbing); classified by the
  governed-namespace policy, not a spine setting.
- `VERIFIED_COMPATIBILITY_ASSERTION` — accepted ONLY when it equals the
  canonical value derived from the validated effective config; anything else
  fails closed before any socket/DB activity (B4-CXR3R3).
- `INIT_ONLY` — consumed exclusively by the explicit initialization path
  (`configure` / first governed start / CI runner / test stack); runtime read
  paths never materialize from it (B4-CXR3R1).

## Inventory

| Input | Consumer | Security significance | Canonical setting | Status | Accepted source | Disposition |
|---|---|---|---|---|---|---|
| `OCE_CONTROL_PLANE_HOST` | http_api, local_lifecycle | bind host | `control_plane.host` | canonical | env (loopback enum only) | CANONICAL |
| `OCE_CONTROL_PLANE_PORT` | http_api, local_lifecycle | bind port | `control_plane.port` | canonical | env | CANONICAL |
| `OCE_SCHEDULER_INTERVAL` | http_api scheduler | pacing | `control_plane.scheduler_interval` | canonical | env | CANONICAL (validated 1..3600) |
| `OCE_CONTROL_PLANE_PUBLIC_LISTEN` | spine | network expansion | `control_plane.public_listen` | canonical | env | CANONICAL (True => rejected) |
| `OCE_API_PORT` | http_api, local_lifecycle (legacy) | bind port | `control_plane.port` | legacy alias | env, only when canonical absent | COMPATIBILITY_ADAPTER (reserved 8080 rejected) |
| `OCE_POSTGRES_HOST` | governed_runtime_dsn, spine | DB host | `postgres.host` | canonical | env | CANONICAL (loopback enum `127.0.0.1` only — external/RFC1918/IPv6/credential values rejected, CXR3-04) |
| `OCE_POSTGRES_PASSWORD_REF` | spine secret ref | DB credential | `postgres.password_ref` | canonical | env (reference only) | CANONICAL |
| `POSTGRES_PASSWORD` | local_secrets (init only) | DB credential | — (feeds approved runtime store) | legacy init | env at `configure` time only, never at runtime | INIT_ONLY (B4-CXR3R1: runtime reads never materialize/overwrite from it) |
| `POSTGRES_DSN` | require_runtime_dsn (runtime) | DB connection | — (derived from secret ref) | legacy | accepted ONLY when equal to the governed derivation (internal propagation) | DEPRECATED_AND_REJECTED as a bypass (divergent DSN fails; ambient password cannot self-legitimate, B4-CXR3R1) |
| `worker_loop --dsn` | worker_loop | DB connection | — (governed derivation) | removed | none | DEPRECATED_AND_REJECTED (CLI argument removed, B4-CXR3R2 — unrecognized args fail at argparse) |
| `build_durable_app(dsn=...)` | http_api durable wiring | DB connection | — (governed derivation) | removed | none | DEPRECATED_AND_REJECTED (parameter removed, B4-CXR3R2 — TypeError) |
| `migrate --db` | scripts/migrate.py | DB migration target | — (governed derivation) | required CLI | loopback hosts only | CANONICAL-GUARDED (B4-CXR3R2: --db required, non-loopback host rejected before any connection) |
| `OCE_REDIS_MODE` | spine | transport truth | `redis.mode` | canonical | env | CANONICAL (transport only) |
| `OCE_WORKERS_EGRESS` | execution_runtime | network policy | `workers.egress` | canonical | env | CANONICAL (deny/loopback only) |
| `OCE_SANDBOX_STRICT` | execution_runtime | isolation | `sandbox.strict` | canonical | env | CANONICAL (False = rejected) |
| `OCE_SANDBOX_PROCESS_TREE_TERMINATION` | execution_runtime | isolation | `sandbox.process_tree_termination` | canonical | env | CANONICAL |
| `OCE_SESSIONS_AUTH_REQUIRED` | worker protocol | outbound auth | `sessions.auth_required` | canonical | env | CANONICAL (False = rejected) |
| `OCE_EXECUTION_BROKER_ENABLED` | spine | live execution | `execution.broker_enabled` | canonical | env | CANONICAL (True = rejected) |
| `OCE_EXECUTION_PAPER_TRADING_ENABLED` | spine | paper execution | `execution.paper_trading_enabled` | canonical | env | CANONICAL (True = rejected) |
| `OCE_EXECUTION_LIVE_ORDER_MODE` | spine | live orders | `execution.live_order_mode` | canonical | env | CANONICAL (disabled only) |
| `OCE_CAPITAL_AUTHORITY` | spine | capital | `capital.authority` | canonical | env | CANONICAL (LOCKED to `none` in Book 4 — any `approved` value rejected at every source and every actor incl. PO, B4-CXR3R5) |
| `OCE_CLOUD_PROVISIONING` | spine | billable cloud | `cloud.provisioning` | canonical | env | CANONICAL (True = rejected) |
| `OCE_CLOUD_GPU_BURST` | spine | billable cloud | `cloud.gpu_burst` | canonical | env | CANONICAL (True = rejected) |
| `OCE_CLOUD_ACCOUNTS` | spine | billable cloud | `cloud.accounts` | canonical | env | CANONICAL (non-empty = rejected) |
| `OCE_CLOUD_COST_CEILING_USD` | spine | billable cloud | `cloud.cost_ceiling_usd_per_month` | canonical | env | CANONICAL (>0 = rejected) |
| `OCE_LOG_REDACT_SECRETS` | logging | leakage | `logging.redact_secrets` | canonical | env | CANONICAL |
| `OCE_LOG_REDACT_CLI` | CLI | leakage | `logging.redact_cli` | canonical | env | CANONICAL |
| `.runtime/secrets.json` | local_secrets, spine backend | secret store | — (approved local secret backend) | durable | runtime dir 0600 | INTERNAL_RUNTIME_DERIVED (untracked) |
| `.runtime/compose.env` | docker compose | secret carrier | — | derived | runtime dir 0600 | INTERNAL_RUNTIME_DERIVED (untracked) |
| `OCE_WORKER_ID` | worker_loop, oce_b3_worker | worker identity | — | operational | env | OPERATIONAL |
| `OCE_WORKER_TOKEN` | worker_loop | worker auth | — | operational | env | OPERATIONAL |
| `OCE_WORKER_SECRET` | oce_b3_worker | worker auth | — | operational | env | OPERATIONAL |
| `OCE_CP_URL` | oce_b3_worker | outbound worker target | — (canonical loopback endpoint) | compatibility assertion | env | VERIFIED_COMPATIBILITY_ASSERTION (B4-CXR3R3: gate always runs first; URL must equal canonical `control_plane.host:port` — external hosts, noncanonical ports, credentials, and redirects fail closed before any socket) |
| `OCE_JOB_FILE` | oce_b3_worker | job input | — | operational | env | OPERATIONAL |
| `OCE_RUN_ID` | CI runner/evidence | run identity | — | operational | env | OPERATIONAL |
| `OCE_STAGE_LABEL` / `OCE_BLOCK_LABEL` / `OCE_BOOK_LABEL` | CI runner/gate | evidence identity | — | operational | env | OPERATIONAL |
| `OCE_EVIDENCE_DIR` / `OCE_ARTIFACT_BASE` / `OCE_RUNTIME_DIR` | CI runner | evidence paths | — | operational | env | OPERATIONAL |
| `OCE_EXPECTED_REPO/BRANCH/COMMIT/TREE` | CI runner/gate | identity verification | — | operational | env | OPERATIONAL |
| `OCE_WS_BASE` / `OCE_ATTEMPT_WS` | B3 execution | workspace paths | — | operational | env | OPERATIONAL |
| `OCE_CI_MODE` | CI runner | test-mode toggle | — | operational | env | OPERATIONAL |

## Governed-namespace rule (B4-R3R1)

Every `OCE_*` variable in the process environment must be a known canonical env
var (`ENV_MAP`), a compatibility alias, or a documented operational variable.
Unknown `OCE_*` variables fail closed with an operator-legible message naming
the variable — a typoed execution override (`OCE_EXECUTION_BROKER_ENABLD`) can
no longer be silently ignored.

Plain `POSTGRES_PASSWORD` / `POSTGRES_DSN` are consumed ONLY by the initial
`configure` secret materialization path (INIT_ONLY, B4-CXR3R1). The durable
runtime constructs its DSN from the governed `postgres.password_ref` -> secret
store -> ephemeral DSN boundary (B4-R3R3/R4); runtime reads never materialize
or overwrite the store.

## Authority rules (B4-CXR3R4/R5)

- Policy-owned and operator(po)-owned settings reject every non-default source:
  safe canonical policy is immutable at this stage; changes require the
  authorized override path (which is separately gated). Precedence
  (cli > env > file) never overrides authority.
- `capital.authority` is LOCKED to `none` in Book 4 — no source, actor, or
  override path can produce live-capital authority.

## Split-brain convergence (B4-R3R2+ / B4-CXR3R2/R3)

- HTTP host/port: `http_api` binds `control_plane.host` : `control_plane.port`
  from the validated effective config. `OCE_API_PORT` only maps through the
  documented alias and 8080 (the legacy default) is rejected as reserved.
- Scheduler tick: `control_plane.scheduler_interval`.
- Postgres DSN: single derivation path — secret reference -> approved local
  store -> in-memory DSN. `POSTGRES_DSN` at runtime entry is rejected unless it
  equals the governed derivation; `worker_loop --dsn`, `build_durable_app(dsn)`,
  and divergent `migrate --db` are all removed/rejected.
- Outbound workers: the control-plane target derives from the validated
  effective config; `OCE_CP_URL` is a verified compatibility assertion only.
- Durable DB host: `postgres.host` is loopback-only (127.0.0.1) while the
  local-first Book 4 contract is in force.