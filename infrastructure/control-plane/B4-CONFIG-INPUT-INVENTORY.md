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
- `TEST_ONLY` — reachable ONLY through the explicit private dependency
  object/function seam supplied by test code; an environment string (incl.
  `OCE_CI_MODE=true`) can NEVER unlock it, and the production CLI and
  environment construction cannot instantiate it (B4-CXR6R2).
- `VERIFIED_INTERNAL_CAPABILITY` — carries runtime authority ONLY after
  cryptographic verification (HMAC-SHA-256 with the dedicated 0600
  activation-handoff key, role binding, single use, freshness, expiry, and
  canonical re-derivation). Plain JSON in an ambient environment variable is
  NEVER authoritative (B4-CXR6R1).
- `OPERATIONAL_IDENTITY_ONLY` — evidence/run identity only; changing it has
  ZERO effect on credentials, job source, execution content, workspace,
  artifact destination, database, network, process launch, or secret
  authority (B4-CXR6R2).
- `DEPRECATED_AND_REJECTED` — known to the governed namespace but refused
  outright; the authority it used to carry lives in the approved secret store
  (B4-CXR5R6).

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
| `migrate --db` | scripts/migrate.py | DB migration target | — (governed derivation) | removed | none | DEPRECATED_AND_REJECTED (B4-CXR5R1: the production `--db` interface is REMOVED — a password-bearing DSN can never appear in process argv, /proc/<pid>/cmdline, command capture, or diagnostics; the governed connection is resolved internally from the pinned activation authority) |
| `migrate --dir` | scripts/migrate.py | SQL source selection | — (repository-owned canonical `migrations/`) | removed | none | DEPRECATED_AND_REJECTED (B4-CXR5R2/CXR6R5: an operator-controlled directory can never select the SQL executed against the governed database — symlink escape, alternate directories, non-regular files, duplicate versions, and unrecognized forms are rejected; only the canonical migration program mutates the governed DB) |
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
| `.runtime/activation_handoff_key` | activation capability MAC | activation-handoff key | — (dedicated authority) | derived | runtime dir 0600 | INTERNAL_RUNTIME_DERIVED (B4-CXR6R1: high-entropy 256-bit key initialized ONCE by `configure`, read-only at runtime; domain-separated from the PostgreSQL password and worker token; never in env/argv/logs/evidence/repository) |
| `OCE_WORKER_ID` | worker_loop, oce_b3_worker | worker identity | — | verified | env | VERIFIED_COMPATIBILITY_ASSERTION (reconciled against the admitted identity at the challenge/response handshake — a mismatch fails closed before any job activity, B4-CXR5R6) |
| `OCE_WORKER_TOKEN` | — (none; authority moved to the approved store) | worker auth | — | removed | none | DEPRECATED_AND_REJECTED (B4-CXR5R6: the worker token lives ONLY in `.runtime/secrets.json` via `initialize_worker_token`/`read_worker_token`; ambient presence refused by the governed-namespace check) |
| `OCE_WORKER_SECRET` | oce_b3_worker | worker auth | — | rejected | none | DEPRECATED_AND_REJECTED at the production entrypoint (B4-CXR6R2: the ambient value is NEVER consumed — the approved store `worker_token` is the only worker-credential authority; test injection exists only through the private `TestWorkerDependencies` object seam, never an environment string) |
| `OCE_CP_URL` | oce_b3_worker | outbound worker target | — (canonical loopback endpoint) | compatibility assertion | env | VERIFIED_COMPATIBILITY_ASSERTION (B4-CXR3R3: gate always runs first; URL must equal canonical `control_plane.host:port` — external hosts, noncanonical ports, credentials, and redirects fail closed before any socket) |
| `OCE_JOB_FILE` | oce_b3_worker | job source | — | rejected | none | DEPRECATED_AND_REJECTED at the production entrypoint (B4-CXR6R2: production workers must fetch authoritative job detail from the control plane; a local file is rejected before any job/workspace/process/socket activity and can never replace job type/params/resource envelope/trust zone/required capabilities; test injection exists only through the private `TestWorkerDependencies` object seam) |
| `OCE_RUN_ID` | CI runner/evidence | run identity | — | operational | env | OPERATIONAL |
| `OCE_STAGE_LABEL` / `OCE_BLOCK_LABEL` / `OCE_BOOK_LABEL` | CI runner/gate | evidence identity | — | operational | env | OPERATIONAL |
| `OCE_EVIDENCE_DIR` | CI runner/gate | evidence identity (CI output dir) | — | operational | env | OPERATIONAL (identity only — CI-runner-owned evidence path, no execution/storage authority) |
| `OCE_ARTIFACT_BASE` | oce_b3_worker | artifact destination | — | constrained | env | INTERNAL_DERIVED + containment (B4-CXR5R6: path must stay beneath the working root; traversal/symlink-escape/absolute-external/repo-overwrite/secret-store-overlap rejected) |
| `OCE_RUNTIME_DIR` | oce_worker CLI | persistent worker state | — | constrained | env/CLI | INTERNAL_DERIVED + containment (B4-CXR5R6: canonical default or relative-under-root only; cannot redirect durable authority) |
| `OCE_EXPECTED_REPO/BRANCH/COMMIT/TREE` | CI runner/gate | identity verification | — | operational | env | OPERATIONAL |
| `OCE_WS_BASE` / `OCE_ATTEMPT_WS` | oce_b3_worker | workspace/execution destination | — | constrained | env | INTERNAL_DERIVED + containment (B4-CXR5R6: must stay beneath the working root; traversal/symlink-escape/absolute-external/repo-overwrite/secret-store-overlap rejected) |
| `OCE_CI_MODE` | CI runner | evidence labeling | — | operational identity | env | OPERATIONAL_IDENTITY_ONLY (B4-CXR6R2: carries ZERO credential/job/execution/storage/database/network/process/secret authority — production code never unlocks anything because `OCE_CI_MODE=true` exists) |
| `OCE_ACTIVATION_ENVELOPE` | child processes (API/worker/migration/outbound worker) | activation lineage | — (verified internal capability) | internal | env (MAC-authenticated carrier) | VERIFIED_INTERNAL_CAPABILITY (B4-CXR6R1: NEVER OPERATIONAL — plain JSON is never authoritative; authority exists only after HMAC-SHA-256 verification with the dedicated 0600 handoff key, role binding, single use, freshness, expiry, and canonical re-derivation; direct ambient injection without a valid protected proof fails before any socket/database/migration/workspace/process activity) |

## CXR6 corrections (supersede the rows above)

- `migrate --db` was previously listed as a required loopback-guarded CLI input;
  CXR5 removed it and this inventory now records it DEPRECATED_AND_REJECTED.
- `migrate --dir` is added and DEPRECATED_AND_REJECTED.
- `OCE_ACTIVATION_ENVELOPE` was previously unlisted while carrying runtime
  authority; it is now VERIFIED_INTERNAL_CAPABILITY (never OPERATIONAL).
- `OCE_CI_MODE` was described as operational while it unlocked job/credential
  behavior; it is now OPERATIONAL_IDENTITY_ONLY with zero runtime authority.
- `OCE_JOB_FILE` / `OCE_WORKER_SECRET` were described as "test seam under
  OCE_CI_MODE=true"; they are now DEPRECATED_AND_REJECTED at the production
  entrypoint, with test injection available ONLY through the private
  `TestWorkerDependencies` object seam.
- Claims like "authenticated test seam" and "forged envelope refused" that
  were stronger than the implementation supported are corrected to the
  VERIFIED_INTERNAL_CAPABILITY and OPERATIONAL_IDENTITY_ONLY truths above.

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