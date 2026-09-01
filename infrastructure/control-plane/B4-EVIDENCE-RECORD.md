# OCE Book 4 — Configuration & Security Control Spine Evidence Record

**Status:** `COMPLETE / B4-CXR5-CLOSURE / GATED_COMPLETE`
**Branch:** `oce-program-build`
**B4-CXR5 repair start SHA:** `047b5eb6afd7e46a48024726fbbb1e83b2d876cd`
**Book 4 start SHA:** `acddeb696e6b5df1828fc7baf8c7bfbd2eb43e90`
**B4-R3R repair start SHA:** `a58671b45e812049b72669466020bb88b7019489`
**B4-CXR3 repair start SHA:** `27a21c9ae2a089dbc324b356407237751082c9d5`
**B4-CXR4 repair start SHA:** `adeeadaafbb4388e37a97a587f9fd2a1349ce9c4`
**Book 2:** `RATIFIED / GATED_COMPLETE` · **Book 3:** `COMPLETE / GATED_COMPLETE`
**main:** `7e7ef7222c4ecdea568b34583fd81406165cc9b6` (untouched)

## Core invariant (this repair)

> **THE CONFIGURATION OCE VALIDATES IS THE CONFIGURATION EVERY RUNTIME
> PROCESS ACTUALLY USES**, and **NO UNTRUSTED RUNTIME INPUT CAN MODIFY,
> REPLACE, OR BYPASS THE AUTHORITY THAT VALIDATES IT.**

Independent review found the previous green suite still allowed a runtime
input to modify the authority that validates it. The B4-CXR3 sequence
repairs every enumerated escape path. Each is closed with a real proof.

## Ordered repair commits (all pushed, `oce-program-build`)

| Commit | Message | Defect |
|---|---|---|
| `0e44617c` | B4-CXR3R1: separate secret initialization from runtime authority | CXR3-01 |
| `c17b7142` | B4-CXR3R2: remove arbitrary runtime DSN injection paths | CXR3-02 |
| `1cb9a8d7` | B4-CXR3R3: canonicalize outbound worker target and DB host boundary | CXR3-03 / CXR3-04 |
| `c508212c` | B4-CXR3R4: enforce setting ownership in the real resolver | CXR3-05 |
| `8ff074cd` | B4-CXR3R5: lock capital authority to none | CXR3-06 |
| `888a6adc` | B4-CXR3R6: repair override-audit durability truth label | CXR3-07 |
| `07314b43` | B4-CXR3R7: unify startup-truth semantics and doctor readiness | CXR3-08 |
| `780f7ceb` | B4-CXR3R8: refresh config-input inventory and close adversarial gaps | CXR3-09 / CXR3-10 |

No repair commit was amended, squashed, or rewritten. Intermediate CI runs
that failed the exact-count gate before the registry was regenerated at
B4-CXR3R8 are preserved as truthful historical evidence (e.g. `33460848791`
.. `33504839138`), never deleted.

## Final authoritative Book 4 run

Authoritative closure proof is the dedicated `b4-config-spine-validation`
run below. Its conclusion was verified from the actual junit XML +
independent gate + final package verifier + cleaned artifact, not inferred
from the run conclusion alone.

- **Branch:** `oce-program-build`
- **Implementation commit:** `780f7ceb40d328b6bde7d9909d45a5f276e2883c`
- **Implementation tree:** `ef965e944b2132c2888ff957431c7c3dd99392da`
- **CI workflow:** `b4-config-spine-validation`
- **CI run:** `33505225957`
- **CI conclusion:** `success`
- **CI URL:** `https://github.com/dabiggestpoppa/larger-lab/actions/runs/33505225957`
- **OCE_RUN_ID:** `c4ca8bfc70cb`
- **Artifact ID:** `9799398331`
- **Artifact name:** `b4-config-spine-evidence-c4ca8bfc70cb`
- **Outer ZIP SHA-256:** `dcf290aab6485e34aad3a30b4f4b93f5d54fe5ab330b80602f3ab25e394a9daa`
- **Totals (from junit.xml, independent):** 510 collected / 510 executed /
  510 passed / 0 failed / 0 errors / 0 skipped; 0 duplicate full node-ids.
- **config-spine category:** 216 / 216 executed / 216 passed / 0 skipped / 0 missing.
- **Independent gate:** `PASS` (137 checks — identity, exact totals, no
  duplicates, every mandatory id, category totals, migrations, source clean
  before/after, cleanup verified, durable PG volume preserved, manifest
  hashes/sizes match, cloud mutations 0, cost `ZERO`).
- **Final package verifier:** `PASS` (read-only).
- **Evidence manifest:** `33` entries, all hashes and sizes independently
  re-verified.
- **Regression on the same head:** `b1-local-ground-validation` success,
  `b2-control-plane-validation` success, `b3-worker-fabric-validation`
  success.

## Repair proof summary (each has tests)

- **CXR3-01 secret self-legitimation closed:** ambient `POSTGRES_PASSWORD`
  cannot rewrite an existing store, cannot materialize a missing store, and
  a matching password + DSN cannot self-legitimate; denial has zero
  authority-side effects (store hash invariant). Runtime reads are read-only
  (`read_runtime_secret` / `derive_runtime_dsn`); init is explicit
  (`initialize_runtime_secret`).
- **CXR3-02 DSN escapes removed:** `worker_loop --dsn` rejected at CLI;
  `build_durable_app` has no DSN override; lifecycle `migrate()` takes no DSN;
  `migrate.py --db` is required and loopback-only.
- **CXR3-03 worker target canonicalized:** `outbound_cp_url()` runs the gate
  first and treats `OCE_CP_URL` as a verified compatibility assertion —
  external hosts, noncanonical ports, credentials, and forbidden configs
  block before any socket activity.
- **CXR3-04 DB host boundary:** `postgres.host` is a loopback-only enum
  (`127.0.0.1`); external / RFC1918 / IPv6 / credential values rejected via
  env, file, and cli.
- **CXR3-05 ownership enforced:** policy-owned and operator(po)-owned
  settings reject every non-default source in the real resolver; the full
  weakening matrix (redact toggles, sandbox, sessions, egress, redis, live,
  cloud, capital) fails closed.
- **CXR3-06 capital locked:** `capital.authority` is `none`; `approved` is
  blocked through env/file/cli/default/override for every actor including PO.
- **CXR3-07 audit truth label:** the in-process override audit is explicitly
  NON-AUTHORITATIVE; durability requires an attached append-only sink; no
  canonical path claims durability it does not have.
- **CXR3-08 startup truth:** `validate_startup` is the config gate,
  `validate_runtime_readiness` is the complete contract (ready implies
  secret_ok implies ok), `require_runtime_startable` fails closed on all;
  doctor fails when the reference is absent, custom-unresolved, or revoked.
- **CXR3-09 inventory:** `B4-CONFIG-INPUT-INVENTORY.md` v2 records every
  authority-bearing input with an explicit disposition.
- **CXR3-10 adversarial closure:** unresolved/revoked doctor proofs and the
  aggregate "denial has zero authority-side effects" store-hash proof.

## Durable archive

- **Location:** `~/Desktop/oce-b4-archive/run-33505225957/`
- Original ZIP preserved byte-exact at `original-evidence.zip`
  (SHA-256 `dcf290aa…`, 50046 bytes).
- Expanded machine-readable copy under `expanded/` (33 files).
- Full provenance in `provenance.json`.

## Previously superseded evidence (preserved, not closure proof)

- Run `33461183563` / `27a21c9a` (B4-CXR2 head) — prior green run,
  superseded by the CXR3 sequence; preserved byte-exact.
- Runs `33460848791` .. `33504839138` — intermediate CXR3 commits that
  failed the exact-count gate until the registry was regenerated at
  B4-CXR3R8; preserved as truthful failure evidence.

---

## B4-CXR4 — POST-CLOSURE AUTHORITY-ESCAPE REPAIR (supersedes the CXR3 closure)

Independent POST-CLOSURE review of the CXR3 closure found remaining runtime
paths the registered suite did not exercise. The CXR4 sequence below closes
each path. The CXR3 closure (run `33505225957` / `780f7ceb`) remains valid
historical evidence for what its suite tested — it is SUPERSEDED by CXR4,
never rewritten. The CXR3 evidence record above is preserved intact.

### Exit-gate statements (B4-CXR4)

1. ORDINARY START / RESTART / RECOVER CAN NEVER MODIFY AN EXISTING SECRET
   AUTHORITY.
2. ONE PINNED EFFECTIVE CONFIGURATION GOVERNS THE ENTIRE ACTIVATION.
3. NO DATABASE MUTATION OCCURS BEFORE THE BOOK 4 AUTHORITY GATE.
4. THE CONFIGURED SECRET REFERENCE IS THE SECRET AUTHORITY EVERY DATABASE
   CONSUMER ACTUALLY USES.
5. "DURABLE" MEANS DEMONSTRABLY PERSISTENT — NEVER JUST NON-NULL.
6. A CONFIGURATION-VALID RESULT IS NEVER MISREPRESENTED AS RUNTIME-READY.

All six are implemented and test-proven in the ordered repair commits.

### Ordered repair commits (all pushed, `oce-program-build`)

| Commit | Message | CXR4 defect |
|---|---|---|
| `1cc2b3fa` | B4-CXR4R1: make secret initialization one-time and startup read-only | CXR4-01 |
| `27a3e7a4` | B4-CXR4R2: lock the secret reference to one canonical authority | CXR4-02 |
| `1b7cc82f` | B4-CXR4R3: pin every runtime activation to one immutable context | CXR4-03 |
| `053ec4e3` | B4-CXR4R4: gate recover/migrate first and bind migration identity exactly | CXR4-04 / CXR4-05 |
| `3c03f5f3` | B4-CXR4R5: make audit durability a proven property | CXR4-06 |
| `53961288` | B4-CXR4R6: truthful config-vs-readiness terminology and lifecycle matrix | CXR4-07 / CXR4-08 |
| `fde3fbd6` | B4-CXR4R7: close adversarial matrix and regenerate mandatory registry | CXR4-10 |

No repair commit was amended, squashed, or rewritten. The intermediate run
`33510911587` (B4-CXR4R6 head `53961288`) failed the exact-count gate before
the registry was regenerated at B4-CXR4R7 and is preserved as truthful
historical failure evidence.

### Authoritative Book 4 run (CXR4)

Verified from the actual junit XML + independent gate + final package
verifier + cleaned artifact, not from the run conclusion.

- **Branch:** `oce-program-build`
- **Implementation commit:** `fde3fbd681112fabbcc4703459f5c626f8f85e16`
- **Implementation tree:** (see source-identity.json in the artifact)
- **CI workflow:** `b4-config-spine-validation`
- **CI run:** `33511157386`
- **CI conclusion:** `success`
- **CI URL:** `https://github.com/dabiggestpoppa/larger-lab/actions/runs/33511157386`
- **OCE_RUN_ID:** `a31d0d0a6a1b`
- **Artifact ID:** `9801747176`
- **Artifact name:** `b4-config-spine-evidence-a31d0d0a6a1b`
- **Outer ZIP SHA-256:** `c4d1d1045c265778cb1c92dbb14f601a285bc2b014783d1a9f423d459070985b` (51,807 bytes, byte-exact original)
- **Totals (from junit.xml, independent):** 541 collected / 541 executed /
  541 passed / 0 failed / 0 errors / 0 skipped; 0 duplicate full node-ids.
- **config-spine category:** 240 / 240 executed / 240 passed / 0 skipped / 0 missing.
- **Independent gate:** `PASS` (137 checks); **final package verifier:** `PASS`.
- **Stage status:** `B4-CONFIG-SPINE-CLOSURE` `PASS`, exit 0.
- **Manifest:** 33/33 entries hash+size verified.
- **Source cleanliness:** clean before AND after; **cleanup:** removed=True
  (containers+networks removed, durable PostgreSQL volume preserved).
- **Cloud mutations:** 0; **cost:** ZERO; broker/capital/execution mutations 0.
- **Regressions on the same head:** b1 `33511157324`, b2 `33511157330`,
  b3 `33511157354` — all `success`.
- **Archive:** `~/Desktop/oce-b4-archive/run-33511157386/`
  (`original-evidence.zip` + `expanded/` + `provenance.json`).

## Confirmation

- `main` untouched: `7e7ef7222c4ecdea568b34583fd81406165cc9b6`.
- Book 5 NOT started; Program Block 4 NOT started.
- No cloud resources purchased/provisioned/deployed; cloud dormant;
  recurring cost `$0`; cloud mutations `0`; no GPU spend.
- Broker / paper / live trading disabled; no capital authority
  (`capital.authority=none`, locked); no execution mutations.
- No trading-strategy or CEREBUS rule changes.
- No OpenClaw activation; a second Hermes agent was not created.
- Book 2 and Book 3 evidence records unchanged; both remain GATED_COMPLETE.
- The source tree was clean before and after the authoritative run; cleanup
  removed containers and networks while preserving the durable PostgreSQL
  volume.

---

## B4-CXR5 — POST-CLOSURE SOURCE-TRUTH REPAIR (supersedes the CXR4 closure)

Independent POST-CLOSURE source review found runtime paths the CXR4-registered
suite did not exercise. The CXR5 sequence below closes each path. The CXR4
closure (run `33511157386` / `fde3fbd6`) remains VALID HISTORICAL EVIDENCE
FOR THE CXR4 REGISTERED SUITE (541 tests) — it is SUPERSEDED BY POST-CLOSURE
CXR5 SOURCE REVIEW, never rewritten. The CXR4 evidence record above is
preserved intact.

### Exit-gate statements (B4-CXR5)

1. NO PASSWORD, TOKEN, OR PASSWORD-BEARING DSN APPEARS IN PROCESS ARGV.
2. ONLY THE REPOSITORY-OWNED CANONICAL MIGRATION PROGRAM CAN MUTATE THE
   GOVERNED DATABASE.
3. EVERY PROCESS IN ONE ACTIVATION PROVES THE SAME PINNED ACTIVATION LINEAGE.
4. NO AMBIENT INPUT CAN REPLACE THE GOVERNED JOB, WORKSPACE, ARTIFACT,
   CREDENTIAL, OR DURABLE-STATE AUTHORITY.
5. NO NON-DURABLE OVERRIDE CAN RETURN AN AUTHORITATIVE/APPLICABLE VALUE.
6. THE CONFIGURATION AUDIT IS TRANSACTIONALLY ISOLATED, SECRET-FREE,
   RELOADABLE, AND APPEND-ONLY.
7. PRODUCTION SECRET ROTATION IS FULLY COHERENT OR EXPLICITLY FUTURE-LOCKED —
   NEVER A STORE-ONLY PRETENSE.
8. CONFIGURATION-VALID, DEPENDENCY-HEALTHY, STARTED, AND RUNTIME-READY ARE
   NEVER CONFUSED.
9. EVERY DENIED PATH HAS ZERO AUTHORITY-SIDE EFFECTS.

All nine are implemented and test-proven in the ordered repair commits.

### Ordered repair commits (all pushed, `oce-program-build`)

| Commit | Message | CXR5 defect |
|---|---|---|
| `294b1cb9` | B4-CXR5R1: eliminate secret-bearing process and CLI surfaces | CXR5-01 |
| `d44ce91c` | B4-CXR5R2: bind database mutation to the canonical migration program | CXR5-02 |
| `3818abd4` | B4-CXR5R3: carry one proven activation lineage across every runtime process | CXR5-03 |
| `6c67389c` | B4-CXR5R4: make secret lifecycle and credential representation truthful | CXR5-04 |
| `dd6e7fb9` | B4-CXR5R5: make durable audit unavoidable and transactionally isolated | CXR5-05 |
| `e515a8a5` | B4-CXR5R6: govern every credential, execution and storage input | CXR5-06 |
| `16afdff0` | B4-CXR5R7: make activation and readiness terminology literal | CXR5-07 |
| `5816e38f` | B4-CXR5R8: regenerate mandatory registry and lifecycle authority matrix | CXR5-08 |
| `f046eb41` | B4-CXR5X1: fix CI-only test isolation exposed by the authoritative run | CI-only |

No repair commit was amended, squashed, or rewritten. Intermediate CI runs
that failed the exact-count gate are preserved as truthful historical failure
evidence: `33521127480`/`33521127595` (B4-CXR5R4 head `6c67389c`, 1 CI-only
failure) and `33537120847`/`33537120850`/`33537120851` (B4-CXR5R8 head
`5816e38f`, 3 CI-only test-isolation failures later fixed at `f046eb41`).

### Authoritative Book 4 run (CXR5)

Verified from the actual junit.xml + independent gate + final package
verifier + cleaned artifact, not from the run conclusion. The artifact was
independently downloaded and re-verified.

- **Branch:** `oce-program-build`
- **Implementation commit:** `f046eb4144c52df4aa1688d6cca8005b1119fb33`
- **Implementation tree:** `83fb51693672687ba18adc9abe7fd451b6ca0fb9`
- **CI workflow:** `b4-config-spine-validation`
- **CI run:** `33537592969`
- **CI conclusion:** `success`
- **CI URL:** `https://github.com/dabiggestpoppa/larger-lab/actions/runs/33537592969`
- **OCE_RUN_ID:** `def3114c2163`
- **Artifact ID:** `9812328456`
- **Artifact name:** `b4-config-spine-evidence-def3114c2163`
- **Outer ZIP SHA-256:** `b9e692bc3c956a4a60e2566093cc8311905f055075d2bff379c611f58418a00e`
  (54,595 bytes, byte-exact original)
- **Totals (from junit.xml, independent):** 596 collected / 596 executed /
  596 passed / 0 failed / 0 errors / 0 skipped; 0 duplicate full node-ids;
  zero hidden skips (skipped=0, reasons=[]).
- **Category totals (all executed, all passed, 0 skipped):** unit 85,
  adversarial 30, end-to-end-job 6, outbound-session 7, representative-job 2,
  cli-lifecycle 7, fabric-pg 12, config-spine 277, sandbox-resource 27,
  po-hermes-boundary 11, api 6, local-lifecycle 47, postgres 13,
  scheduler 7, worker 13, redis 2, validation-regression 16,
  worker-fabric-core 20, worker-supervisor 8 (= 596).
- **Independent gate:** `PASS` (137 checks — identity, exact totals, zero
  skips, no duplicates, every mandatory id, every category, migrations
  `0001`..`0007` applied, source clean before/after, cleanup verified,
  durable PG volume preserved, all artifacts present); **final package
  verifier:** `PASS` (read-only).
- **Evidence manifest:** 33/33 entries, all hashes and sizes independently
  re-verified from the downloaded artifact.
- **Source cleanliness:** clean before AND after (`dirty=[]`).
- **Cleanup:** removed=True (containers removed, networks removed, durable
  PostgreSQL volume preserved=True).
- **Cloud mutations:** 0; **cost:** ZERO; **cloud deployment:** NOT_DEPLOYED;
  broker/capital/execution mutations 0; **capital authority:** none.
- **Regressions on the same head `f046eb41`:** b1 `33537593059`, b2
  `33537592958`, b3 `33537592963` — all `success`.
- **Archive:** `~/Desktop/oce-b4-archive/run-33537592969/`
  (`original-evidence.zip` + `expanded/` + `provenance.json`).

### Proof summary (each has registered tests in the 596)

- **Secret-free argv (CXR5-01):** canary passwords and worker tokens proven
  absent from argv, captured subprocess command lists, stdout/stderr, and
  logs; `/proc/<pid>/cmdline` proofs run in CI (1 truthful POSIX-only skip
  locally); production `migrate.py` has no `--db` and the worker no
  `--token`; ambient `POSTGRES_DSN`/`POSTGRES_PASSWORD` stripped from child
  environments.
- **Canonical migration program (CXR5-02):** `--dir` rejected; migration
  discovery bound to the repository-owned canonical directory; symlink
  escape, duplicate versions, non-regular files, and alternate-directory
  injection all blocked; canary SQL never executes; `down` is
  TEST-ONLY/FUTURE-LOCKED in the production CLI with a tested rollback path;
  migration-set identity (ordered filenames, versions, hashes) bound to the
  activation, no SQL contents in evidence.
- **One activation lineage (CXR5-03):** a single authoritative parent
  ActivationContext per activation; children (API, worker, migration,
  outbound worker) consume the parent's safe ActivationEnvelope and prove
  context ID, secret generation, and revocation state or fail closed before
  any socket/DB/process activity; sanitized child environments built from the
  pinned activation; later `os.environ` mutation cannot move children;
  legacy optional re-resolution entrypoints fail closed in production mode.
- **Secret lifecycle truth (CXR5-04):** initialization passwords validated
  (empty/undersized/CR-LF/NUL/control chars rejected) before persistence;
  structured connection parameters — no raw DSN string concatenation;
  `compose.env` written atomically with restrictive permissions at creation;
  failed projection never mutates the approved secret store; file locking /
  compare-and-swap prevents concurrent metadata loss; complete secrets.json
  schema validation (object, string secrets, valid metadata, valid
  generation); production rotation is explicitly FUTURE-LOCKED — no store-only
  write is labeled a rotation.
- **Durable audit (CXR5-05):** no public/runtime method returns an
  authoritative/applicable override without proven durable audit;
  non-durable evaluator renamed `evaluate_override_preview` and returns a
  decision object only, unreachable by runtime callers; one audit transaction
  per operation (no TOCTOU); dedicated audit connection; commit failure
  rolls back and applies no override; idempotent request/correlation ID;
  full durable record (audit ID, request ID, actor, setting, safe requested
  change, previous/new safe values, reason, decision, timestamp, config
  fingerprints, backend identity, authorized state); secret canaries rejected
  (zero secret bytes written); append-only enforced in real PostgreSQL
  (UPDATE/DELETE refused, fresh-connection read-back proves persistence);
  `proven()` proves expected schema/backend; fake sinks cannot self-report
  authority.
- **Governed inputs (CXR5-06):** every credential/execution/storage input
  reclassified (CANONICAL / VERIFIED_COMPATIBILITY_ASSERTION /
  INTERNAL_DERIVED / INIT_ONLY / TEST_ONLY / DEPRECATED_AND_REJECTED);
  `OCE_JOB_FILE` is TEST_ONLY and rejected in production before any
  job/workspace activity; production workers fetch authoritative job detail
  from the control plane; external workspace/artifact/runtime paths rejected;
  symlink escape and secret-store overlap blocked; worker identity must
  reconcile with admitted identity; ambient worker credentials cannot
  self-authorize.
- **Literal terminology (CXR5-07):** config-only in-memory assembly reports
  `configured`/`initialized`/`config_valid` — never `started`;
  `ControlPlane.startup()` truthfully relabeled; `wait_ready` →
  `wait_dependencies` (dependency health only); `smoke` pinned to the
  activation destination; `gate_start` → `config_gate`; compatibility
  wrappers never preserve false semantic names in production paths.
- **Adversarial closure (CXR5-08):** adversarial matrix regenerated from
  source; mandatory registry regenerated from actual pytest collection (596
  ids, zero duplicates, 541 → +55 from R1–R7+X1); input inventory and
  lifecycle authority matrix regenerated; leak scan over argv/process-command
  surfaces; every denied path proves store hash, compose-env hash, migration
  ledger, and audit ledger unchanged with no container start, process
  launch, workspace creation, artifact publication, or socket activity.

## CXR5 Final record

- **CXR5 start SHA:** `047b5eb6afd7e46a48024726fbbb1e83b2d876cd`
- **Ordered CXR5 repair SHAs:** `294b1cb9`, `d44ce91c`, `3818abd4`,
  `6c67389c`, `dd6e7fb9`, `e515a8a5`, `16afdff0`, `5816e38f`, `f046eb41`
- **Final implementation SHA/tree:** `f046eb4144c52df4aa1688d6cca8005b1119fb33`
  / `83fb51693672687ba18adc9abe7fd451b6ca0fb9`
- **Authoritative workflow run:** `33537592969` (`b4-config-spine-validation`)
- **OCE_RUN_ID:** `def3114c2163`
- **Artifact:** `9812328456` / `b4-config-spine-evidence-def3114c2163`
- **Artifact digest:** `b9e692bc3c956a4a60e2566093cc8311905f055075d2bff379c611f58418a00e`
- **Totals:** 596 collected / 596 executed / 596 passed / 0 failed / 0 errors /
  0 skipped; 0 duplicates; zero hidden skips.
- **Category counts:** unit 85, adversarial 30, end-to-end-job 6,
  outbound-session 7, representative-job 2, cli-lifecycle 7, fabric-pg 12,
  config-spine 277, sandbox-resource 27, po-hermes-boundary 11, api 6,
  local-lifecycle 47, postgres 13, scheduler 7, worker 13, redis 2,
  validation-regression 16, worker-fabric-core 20, worker-supervisor 8.
- **Manifest:** 33/33 hash+size verified independently.
- **Source cleanliness:** clean before and after.
- **Cleanup:** removed=True; durable PostgreSQL volume preserved.
- **Regressions:** b1 `33537593059`, b2 `33537592958`, b3 `33537592963` —
  all success on the same head.
- **Capital authority:** none. **Cloud mutations:** 0. **Broker mutations:** 0.
  **Execution mutations:** 0. **Recurring cost:** $0.
- **main:** `7e7ef7222c4ecdea568b34583fd81406165cc9b6` (unchanged, verified).
- **Branch-protection/signing limitations:** commits are not GPG-signed
  (verified `%G?` = N for the whole CXR5 chain); no branch-protection
  force-push guard is evidenced on `oce-program-build`.
- **Unresolved limitations:** `/proc/<pid>/cmdline` proofs require POSIX and
  execute in CI (1 truthful local skip on Windows); a coherent multi-resource
  rotation program (DB credential + store + compose + connection
  invalidation + generation transition + audit) remains future work,
  deliberately future-locked in Book 4.

## Confirmation (CXR5)

- `main` untouched: `7e7ef7222c4ecdea568b34583fd81406165cc9b6`.
- Book 5 NOT started; Program Block 4 NOT started.
- No cloud resources purchased/provisioned/deployed; cloud dormant;
  recurring cost `$0`; cloud mutations `0`; no GPU spend.
- Broker / paper / live trading disabled; no capital authority
  (`capital.authority=none`, locked); no execution mutations.
- No trading-strategy or CEREBUS rule changes.
- No OpenClaw activation; no additional Hermes deployment.
- Book 2 and Book 3 evidence records unchanged; both remain GATED_COMPLETE.
- The source tree was clean before and after the authoritative run; cleanup
  removed containers and networks while preserving the durable PostgreSQL
  volume.

---

## B4-CXR6 — POST-CLOSURE AUTHORITY REPAIR (supersedes the CXR5 closure)

Independent POST-CLOSURE source review found authority paths the CXR5-registered
suite did not attack: the activation envelope was forgeable (plain JSON in an
ambient env var with a recomputable plain-SHA identity), OCE_CI_MODE was an
environment-unlocked test seam, audit request-id reuse could authorize an
unaudited change, and ordinary start still re-entered initialization.

```
B4-CXR5:
    VALID HISTORICAL EVIDENCE FOR THE 596-TEST REGISTERED SUITE
    SUPERSEDED BY POST-CLOSURE CXR6 SOURCE REVIEW
```

The CXR5 CI run (33537592969) and artifact (9812328456) were REAL; their
adversarial model did not cover recomputable-envelope forgery,
environment-created test authority, or divergent audit-ID reuse. The CXR5
evidence record above is preserved intact and is never rewritten.

### Ordered repair commits (all pushed, `oce-program-build`)

| Commit | Message | CXR6 defect |
|---|---|---|
| `e114c496` | B4-CXR6R1: authenticate and re-derive child activation authority | CXR6-01 |
| `0462f1e5` | B4-CXR6R2: remove environment-unlocked test authority | CXR6-02 |
| `066a7879` | B4-CXR6R3: make audit idempotency exact and collision-safe | CXR6-03 |
| `cf8ca8d7` | B4-CXR6R4: make ordinary activation read-only over secret authority | CXR6-04 |
| `f6f11144` | B4-CXR6R5: correct authority inventory and closure truth labels | CXR6-05 |
| `a96c05e1` | B4-CXR6R6: adversarial closure and registry regeneration | CXR6-06 |
| `fd5b3274` | B4-CXR6X1: fix CI-only failures exposed by the authoritative CXR6 run | CI |

### CXR6-01 — activation envelope is no longer forgeable

The ambient `OCE_ACTIVATION_ENVELOPE` carrier is now an AUTHENTICATED,
role-bound activation capability: HMAC-SHA-256 over the complete typed
payload (schema version, context identity, config + security-state
fingerprints, secret reference/backend/generation/revocation, control-plane
host/port, scheduler interval, PostgreSQL host/port/database/user, canonical
control-plane URL, migration-set identity, parent activation ID, child role,
capability nonce, issuance/expiry) with a DEDICATED 256-bit
activation-handoff key stored 0600 under `.runtime` — never in environment,
argv, process title, logs, evidence, diagnostics, or the repository, and
domain-separated from the PostgreSQL password and worker token.

Verification is constant-time (`hmac.compare_digest`); unknown fields,
duplicate/ambiguous JSON keys, bool-as-int confusion, malformed types,
out-of-range ports, and oversized carriers are rejected; after
authentication the child RE-DERIVES canonical identities (effective-config
fingerprint, security-state fingerprint, canonical control-plane URL from
host+port, PostgreSQL port/database/user from canonical authority, secret
backend identity, migration-set identity) and compares them against the
authenticated payload. Capabilities are role-bound (api/worker/migration/
outbound_worker — an API capability can never launch a worker, etc.),
single-use (consumed-nonce ledger), time-boxed, and fail closed on
rotation/revocation staleness, expiry, or replay.

### CXR6-02 — OCE_CI_MODE carries zero authority

`OCE_CI_MODE` is now OPERATIONAL_IDENTITY_ONLY: changing it has zero effect
on credentials, job source, execution content, workspace, artifact
destination, database, network, process launch, or secret authority. The
production worker entrypoint rejects `OCE_JOB_FILE` and ambient
`OCE_WORKER_SECRET` unconditionally, before any job/workspace/process/socket
activity. Test injection exists ONLY through the private dependency seam
(`ProductionWorkerDependencies` vs `TestWorkerDependencies` in
`oce_b3_worker_test_deps.py`) supplied directly by test code — never
selected by an environment string, pytest/CI detection, username, path, or
process name.

### CXR6-03 — audit idempotency is exact and collision-safe

A request/correlation ID may reconcile ONLY the exact same durable decision.
`PostgresAuditSink.append` inserts and commits; on conflict it reads back
the committed record and compares the FULL canonical decision (actor,
setting, requested_change, reason, previous, new, decision, authorized,
before/after fingerprints, backend identity). An exact retry reconciles as
the same committed operation; any divergent semantic field fails closed
with zero applicable value and the durable row unchanged. Rowcount zero is
never treated as success without reconciliation; uncertain-commit recovery
reads back and verifies the exact record.

### CXR6-04 — ordinary activation is read-only over secret authority

`start`/`restart`/`recover` never call `configure()` and never materialize
missing material (postgres password, worker token, activation handoff key
must already exist or activation fails closed with a `configure` hint
before any mutation). `configure` is the explicit initialization command
and preflights configuration posture, the static loopback compose
boundary, and store readability/schema BEFORE any write, with atomic store
mutation. `start_process` requires an explicit verified child environment;
the `compose_environment()` compatibility default for API/worker launch is
removed (compose.env remains a Docker-Compose-only carrier). A failed
start/restart/recover alters no secret, config, capability, database,
workspace, or artifact state.

### CXR6-05 — truthful input inventory

`B4-CONFIG-INPUT-INVENTORY.md` regenerated from source: `migrate --db` and
`migrate --dir` are DEPRECATED_AND_REJECTED; `OCE_ACTIVATION_ENVELOPE` is
VERIFIED_INTERNAL_CAPABILITY (never OPERATIONAL); `OCE_CI_MODE` is
OPERATIONAL_IDENTITY_ONLY with zero runtime authority; `OCE_JOB_FILE` and
`OCE_WORKER_SECRET` are production-rejected with test injection available
only through the private dependency seam.

### CXR6-06 — adversarial closure and registry regeneration

The mandatory registry was regenerated from actual pytest collection: **644
ids** (596 + 48 CXR6 proofs), zero duplicate node ids, per-category totals
(unit 120, config-spine 286, local-lifecycle 51). Zero-side-effect matrix
proves forged/role-confused/replayed/malformed capabilities leave
secrets.json, the handoff key, and the consumed-nonce ledger byte-identical
with no container start, process launch, workspace, artifact, or socket
activity.

### B4-CXR6X1 — CI-exposed repair (run 33551112500, OCE_RUN_ID 6617cd2f8128)

The first authoritative CXR6 run collected 644 and executed 644 with exactly
2 failures, both test-side defects where the new authority model changed the
subprocess contract: (1) the CXR6R2 production worker fetches job detail
from the control plane, so the service-test fixture had to wire the real
`PgJobStore` into `WorkerProtocolServer` (`job_store=jstore`, matching the
proven end-to-end fixture); (2) a lifecycle test relied on Docker being
ABSENT locally to fail at the docker preflight, so it now mocks docker
unavailable — the store-invariance assertion is deterministic in every
environment. No production source changed.

## CXR6 Final record

- **CXR6 start SHA:** `fed04ff15929544de55b74da8956b08022cf8eb1`
  (B4-CXR5-EVIDENCE — preserved, never amended; CXR5 chain intact)
- **Ordered CXR6 repair SHAs:** `e114c496`, `0462f1e5`, `066a7879`,
  `cf8ca8d7`, `f6f11144`, `a96c05e1`, `fd5b3274`
- **Final implementation SHA/tree:** `fd5b32747dba1c93223093966c1edcee3b6680a6`
  / `e8d9f30b1a679047011d1ac63fbd1b4395dcbfd4`
- **Authoritative workflow run:** `33555566041` (`b4-config-spine-validation`)
- **OCE_RUN_ID:** `c048f12cca64`
- **Artifact:** `9819232513` / `b4-config-spine-evidence-c048f12cca64`
- **Artifact digest:** `ad41faac6a62462a125d60803bfaf5bc64e97f7106bce0516b801f900122e34a`
  (57727 bytes)
- **Totals:** 644 collected / 644 executed / 644 passed / 0 failed / 0 errors /
  0 skipped; 0 duplicates; zero hidden skips.
- **Category counts:** unit 120, adversarial 30, end-to-end-job 6,
  outbound-session 7, representative-job 2, cli-lifecycle 7, fabric-pg 12,
  config-spine 286, sandbox-resource 27, po-hermes-boundary 11, api 6,
  local-lifecycle 51, postgres 13, scheduler 7, worker 13, redis 2,
  validation-regression 16, worker-fabric-core 20, worker-supervisor 8.
- **Manifest:** 33/33 hash+size verified independently (from the raw GitHub
  Actions artifact download).
- **Source cleanliness:** clean before and after.
- **Cleanup:** removed=True; containers/network removed; durable PostgreSQL
  volume preserved.
- **Regressions:** b1 `33555565900`, b2 `33555565878`, b3 `33555566072` —
  all success on the same head `fd5b3274`.
- **Authenticated-capability forgery matrix (all rejected before any
  activity):** forged field + recomputed context_id; forged postgres
  port/database/user (alternate database identity); forged canonical
  control-plane URL to an external host while keeping control_plane_host
  loopback; forged config fingerprint; forged security-state fingerprint /
  backend identity; forged migration-set identity; single-byte tamper;
  missing/invalid MAC; duplicate JSON keys; oversized carrier; role
  confusion (api↔worker↔migration↔outbound_worker); replay after
  consumption/expiry; stale capability after secret rotation/revocation.
- **Capability-key leak scan:** zero 64-hex handoff-key lookalikes in the
  evidence set; key never present in env/argv/logs/diagnostics/evidence.
- **OCE_CI_MODE authority result:** zero config authority — CI mode never
  unlocks job file or ambient worker secret.
- **Job/credential test-seam result:** production entrypoint rejects
  `OCE_JOB_FILE` and `OCE_WORKER_SECRET` before file read / value
  consumption; test injection works only through the private dependency
  seam.
- **Audit exact-retry result:** one truthful durable row, exact
  reconciliation.
- **Audit divergent-request-ID result:** zero applicable value; existing
  durable row unchanged (actor/setting/reason/new-value/fingerprint all
  tested).
- **Ordinary-start secret-invariance result:** store byte-identical through
  start/restart/recover; missing material blocks with `configure` hint.
- **Failed-start zero-side-effect result:** no secret/config/capability/
  ledger/workspace/artifact/process mutation on any denied path.
- **Capital authority:** none. **Cloud mutations:** 0. **Broker mutations:** 0.
  **Execution mutations:** 0. **Recurring cost:** $0.
- **main:** `7e7ef7222c4ecdea568b34583fd81406165cc9b6` (unchanged, verified).
- **Archive:** `~/Desktop/oce-b4-archive/run-33555566041/`
  (`original-evidence.zip` + `expanded/` + `provenance.json`); the CXR5
  archive `run-33537592969/` and the provisional runs are preserved intact.
- **Branch-protection/signing limitations:** commits are not GPG-signed; no
  branch-protection force-push guard is evidenced on `oce-program-build`.
- **Unresolved limitations:** `/proc/<pid>/cmdline` proofs require POSIX and
  execute in CI (1 truthful local skip on Windows); a coherent multi-resource
  rotation program (DB credential + store + compose + connection
  invalidation + generation transition + audit) remains future work,
  deliberately future-locked in Book 4; the consumed-nonce ledger and
  activation TTL are local-runtime primitives (no distributed authority).
