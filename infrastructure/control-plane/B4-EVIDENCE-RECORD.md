# OCE Book 4 — Configuration & Security Control Spine Evidence Record

**Status:** `IMPLEMENTATION CONVERGED — CLOSURE BLOCKED` (only the SonarQube gate remains; see the CXR7U9R28–R30 superseding section at the end of this record)
**Final implementation commit:** `8ce72fb86c88a2d7768dc1c9a2bd9568f60d6aa1`, tree `4e14b63fb69fcae9ecf18941ff40731143626344` — six workflows green on it
**CXR7U9 quality gate:** SonarQube Security D / Reliability C on new code on the current head (required A/A) — credential- and disposition-blocked; see the CXR7U9R28–R30 section at the end of this record
**Branch:** `oce-program-build`
**B4-CXR5 repair start SHA:** `047b5eb6afd7e46a48024726fbbb1e83b2d876cd`
**Book 4 start SHA:** `acddeb696e6b5df1828fc7baf8c7bfbd2eb43e90`
**B4-R3R repair start SHA:** `a58671b45e812049b72669466020bb88b7019489`
**B4-CXR3 repair start SHA:** `27a21c9ae2a089dbc324b356407237751082c9d5`
**B4-CXR4 repair start SHA:** `adeeadaafbb4388e37a97a587f9fd2a1349ce9c4`
**Book 2:** `RATIFIED / GATED_COMPLETE` · **Book 3:** `COMPLETE / GATED_COMPLETE`
**main:** `d09941e75f3da6040254e0e6193dcf670207273b` (untouched; the CXR7U9 start SHA `583614ff…` was reconciled into this branch)

## Core invariant (this repair)

> **THE CONFIGURATION OCE VALIDATES IS THE CONFIGURATION EVERY RUNTIME
> PROCESS ACTUALLY USES**, and **NO UNTRUSTED RUNTIME INPUT CAN MODIFY,
> REPLACE, OR BYPASS THE AUTHORITY THAT VALIDATES IT.**

Independent review found the previous green suite still allowed a runtime
input to modify the authority that validates it. The B4-CXR3 sequence
repairs every enumerated escape path. Each is closed with a real proof.

## Ordered repair commits (all pushed, `oce-program-build`)

| Commit | Message | Defect |
---|---|---|
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

---

## B4-CXR7 — POST-CLOSURE AUTHORITY REPAIR — BLOCKED AT GATE (NOT CLOSED)

CXR7 opens from `f46e1beb` (B4-CXR6-EVIDENCE). The reality lock passed: HEAD
== origin == `f46e1beb`, clean tree, 0 ahead / 0 behind, CXR6 chain intact
(`e114c496`..`fd5b3274`), `main` == `7e7ef7222c4ecdea568b34583fd81406165cc9b6`.

Per the mission's own directive, before any implementation the exact Book 4
threat boundary must be documented — and if the current same-user local
architecture cannot establish an enforceable parent/child issuance boundary
without an unauthorized scope expansion, the limitation is recorded and the
gate returns `BLOCKED_B4_CXR7`. **That is what happened. CXR7 is BLOCKED;
no implementation was attempted and no closure is claimed.**

### The threat-boundary question, answered

* **Is a child process trusted to possess all parent authority?** Under the
  current architecture, structurally YES: API / worker / migration /
  outbound-worker children are launched by `local_lifecycle.start_process`
  as ordinary subprocesses under the SAME OS principal (same account, same
  token) on both the Windows dev host and the single-user Ubuntu CI runner.
  There is no OS/process trust boundary between parent and child: a child
  can read everything its account can read, including the 0600
  activation-handoff key (0600 excludes OTHER accounts, not same-account
  children) and every other file the operator can read.
* **Is role separation intended to constrain a compromised/misbehaving
  child?** The CXR6 claim set implies YES (`build_envelope`/`child_role`
  role-binding, "a verified child cannot reissue"), but the implementation
  does not enforce it: children receive the SAME `ActivationContext` type
  the parent uses (`_context_from_envelope` reconstructs the full parent
  object, including `build_envelope()` and `child_environment()`), and that
  type MACs with a key the child can read.

**CXR7 deliberately does not claim the second while implementing the first**
(mission CXR7-01): the honest statement is that the current single-principal
architecture trusts every child with all parent authority.

### Confirmed audit findings (source-verified, this session)

* **Amplification is real, not hypothetical.** `ActivationContext`
  (config_startup.py:741) exposes `build_envelope(child_role=...)` (line
  826) and `child_environment(child_role=...)` (line 868), both of which
  MAC a NEW role-bound capability with the dedicated handoff key read from
  disk (`ActivationEnvelope.to_json` -> `ls.read_activation_handoff_key()`).
  A verified worker child that reconstructs its context via
  `_context_from_envelope` can mint VALID `api`, `migration`, and
  `outbound_worker` capabilities for the same activation: every re-derived
  canonical value (postgres port/db/user, backend identity, derived CP URL,
  security fingerprint, effective-config fingerprint, context_id) matches
  because they are properties of the activation, not of the role. This was
  demonstrated by executing the real code path (scratch audit proof, since
  removed; working tree clean).
* **The registered non-reissuance proof is vacuous.**
  `tests/test_b4_cxr6_activation_capability.py:270`:
  `assert not hasattr(child, "build_envelope") or True` — `or True`
  guarantees PASS, and `child` DOES have the method.
* **Verification material IS issuance material.** HMAC-SHA-256 with a
  shared symmetric key authenticates "someone possessing the key"; it
  cannot distinguish issuer from verifier when every verifier (same-account
  child) can read the key (mission CXR7-01).
* **Children receive the parent issuer type** (mission CXR7-01 requirement
  I/J): `_context_from_envelope` returns `ActivationContext`, the same class
  `create_activation_context` returns to the parent. Child-safe type does
  not exist.

### Why each acceptable pattern fails within scope

* **Asymmetric signatures (e.g. Ed25519):** an on-disk private key is
  readable by same-account children — a child can self-sign any role. A
  private key held only in parent memory leaves no OS boundary preventing
  same-account access, and the child still needs a TRUST ANCHOR for the
  public key. A public key transported via environment/disk is attacker-
  replaceable by the same principal (mission: "a public key supplied only
  through attacker-controlled environment data is not a trust anchor; an
  asymmetric private key stored in the same child-readable runtime
  directory is also not a repair"). Embedding a static keypair in the
  repository would spread one issuance key across every deployment with no
  per-install secrecy. None of these establishes issuer/verifier
  separation.
* **Supervisor/broker behind a REAL OS/process trust boundary (protected
  IPC, distinct OS identity):** requires a separate OS principal — a
  service account, elevated broker, or per-UID container isolation. That is
  an explicit scope expansion (Hard Boundary 11: no expansion into
  distributed/cloud capability infrastructure; the Book 4 local-first
  runtime is single-principal, and the mandatory adversarial suite runs
  in-process under one CI user).
* **Distinct OS identities/sandboxes per role:** same scope expansion; the
  lifecycle child path (`subprocess.Popen`, same user) cannot express it,
  and CXR7's required proofs A–J must execute in the registered pytest
  suite on a single-user runner.

### Required to unblock (exact, for the operator)

An enforceable parent/child issuance boundary requires at least one of:

1. a broker/supervisor process running under a DIFFERENT OS principal
   (service account, or per-role containers with distinct UIDs) that owns
   the issuance key and issues role-bound capabilities over protected IPC
   that same-principal children cannot influence; or
2. child processes launched with restricted tokens/capabilities that
   genuinely cannot read issuer material; or
3. an explicit, documented relaxation of the authority model back to
   "children are trusted with parent authority" with the role-binding
   claims and tests rewritten to match, or
4. an authorized scope expansion decision (new infrastructure) from the
   operator.

Options 1/2/4 are scope expansions outside Book 4 authority; option 3
would falsify CXR7's own exit-gate statements (1–2). Per the mission, the
honest disposition is to record this exact limitation and return.

### Disposition

* **Status: `BLOCKED_B4_CXR7: no enforceable parent/child issuance boundary
  exists`.** No repair commits were created (R1–R6 intentionally NOT
  implemented; R2–R6 alone cannot satisfy exit-gate statements 1–2, and
  partial repairs without the core boundary would misrepresent progress).
* **CXR6 remains the current closure** (`fd5b3274` / run `33555566041` /
  artifact `9819232513`) — VALID HISTORICAL EVIDENCE FOR ITS REGISTERED
  644-TEST SUITE, superseded by nothing; CXR7 did not close and claims no
  repair. The CXR6 run was real; its model did not cover
  same-principal-child amplification (a shared symmetric key readable by
  every verified child).
* **Immutability preserved:** branch tip unchanged at `f46e1beb`; no
  pushes made this session; CXR3–CXR6 history, archives
  (`oce-b4-archive/run-33505225957/`, `run-33511157386/`,
  `run-33537592969/`, `run-33555566041/`), and `main` are untouched.
* **Hard boundaries respected:** no Book 5; no Program Block 4; no cloud /
  broker / capital / execution mutations; recurring cost `$0`; capital
  authority `none`; no false security claims substituted for the explicit
  blocker.
* **Suspects deliberately NOT claimed as closures:** child non-
  reissuance, non-amplification, verification-material-not-issuance,
  issuer/verifier separation, direct-launch trust-root proof. These are
  the exact unresolved blockers.

## B4-CXR7U — SINGLE-PRINCIPAL TRUST MODEL + CLOSURE-PROOF REPAIR (supersedes the CXR7 BLOCKED state as directed by the operator disposition)

### Operator disposition (recorded, not rewritten)

The CXR7 blocker (`35b940cf`) was ACCEPTED as technically correct: mutually
hostile same-principal isolation is unavailable without an unauthorized scope
expansion. The operator did NOT authorize an OS-isolation expansion. Instead:

> The OCE supervisor, API, worker, migration, and outbound-worker processes
> running as the same approved local OS principal form ONE trusted computing
> base. `OCE_ACTIVATION_ENVELOPE` is an AUTHENTICATED PARENT-LAUNCH HANDOFF
> with role/audience consistency checking — not a security boundary against
> arbitrary code already executing as the approved OCE OS account.
> SAME-PRINCIPAL ARBITRARY CODE EXECUTION IS FULL LOCAL OCE COMPROMISE.

The disposition supersedes the impossible hostile-child portion of the original
CXR7 exit gate WITHOUT erasing the blocker finding. `B4-THREAT-MODEL.md`
(CXR7U1) is the canonical boundary statement referenced by the inventory,
lifecycle matrix, tests, and this record.

### Ordered commit history (all pushed, `oce-program-build`; no squash, no amend)

CXR7U start SHA: `f46e1beb21c6ec5f25c94278949dea946449a503` (CXR6 evidence head).

| Commit | Gate step |
|---|---|
| `35b940cf` | CXR7-BLOCKED (137-line non-amplification assessment; evidence-record only) |
| `0476cf0d` | CXR7U1 canonical single-principal trust boundary |
| `50902d2b` | CXR7U2 parent/child context separation |
| `d3d3cb6f` | CXR7U3 trusted-program lock + isolation truth |
| `7124c0aa` | CXR7U4 atomic fail-closed handoff consumption |
| `6db19c11` | CXR7U5 real PostgreSQL audit reconciliation |
| `0781b93d` | CXR7U6 complete-or-nothing initialization |
| `080c82da` | CXR7U7 test integrity, inventory, matrices, registry |
| `471e3e2c` | CXR7U8R1 mutation controls isolated + attributable failures |
| `d36efb86` | CXR7U8R2 vacuous paths removed, real production entrypoints |
| `5cbe0d88` | CXR7U8R3 configure serialized + crash/restart recoverable |
| `20f8404e` | CXR7U8R4 exact PostgreSQL reconciliation + schema proof |
| `b56bc75f` | CXR7U8R5 corrupt secret authority fails closed |
| `890e2eee` | CXR7U8X1 CI-exposed repairs (run `33979406177`) |
| `b1f7a078` | CXR7U8X2 CI-exposed repairs (run `33986527406`) |

Final implementation SHA/tree: `b1f7a07881df1173ca7bb20183f99e04acc3cf6f` /
`0b51afccd362a7b15d028464dde047f2a763396e`.

### CXR7U Final authoritative run

- **CI workflow:** `b4-config-spine-validation`
- **CI run:** `34118435301` — **success**
- **CI URL:** `https://github.com/dabiggestpoppa/larger-lab/actions/runs/34118435301`
- **OCE_RUN_ID:** `c4394d247914`
- **Artifact ID / name:** `10017304559` / `b4-config-spine-evidence-c4394d247914`
- **Outer ZIP SHA-256 (from run log):** `5955f45aca019f499edd35706855bf38d00d449aeedf8e11e55bc7e7e902dced`
- **Totals (junit.xml, independently re-parsed):** 835 collected / 835 executed /
  835 passed / 0 failed / 0 errors / **0 skipped** (zero hidden skips in CI);
  registry `duplicate_ids: []`; expected=collected=executed=passed=835.
- **Category counts (validation-summary.md):** unit 122/122, adversarial 30/30,
  end-to-end-job 6/6, outbound-session 7/7, representative-job 2/2,
  cli-lifecycle 7/7, fabric-pg 12/12, config-spine 475/475,
  sandbox-resource 27/27, po-hermes-boundary 11/11, api 6/6,
  local-lifecycle 51/51, postgres 13/13, scheduler 7/7, worker 13/13,
  redis 2/2, validation-regression 16/16, worker-fabric-core 20/20,
  worker-supervisor 8/8.
- **Independent gate:** `PASS` (identity repo/branch/commit/tree, exact totals,
  zero duplicates, every mandatory id, migrations, source clean before/after,
  cleanup verified, durable PG volume preserved, manifest hashes/sizes,
  cloud mutations 0, cost ZERO).
- **Evidence manifest:** 33 entries — all hashes AND sizes independently
  re-verified after download (33/33 verified, 0 bad).
- **Regression on the same head:** `b1-local-ground-validation` `34118435295`
  success; `b2-control-plane-validation` `34118435261` success;
  `b3-worker-fabric-validation` `34118435201` success.
- **Real PostgreSQL reconciliation executed in CI:** the container-backed
  `test_b4_cxr7_audit_reconciliation` module and the postgres/fabric-pg
  categories ran against real PostgreSQL in CI (Docker 28.0.4; 0 skips).
- **Leak scan:** 11 canary/leak-defense testcases executed in the same
  authoritative run (committed-file canary scan, error-path canary redaction,
  fingerprint no-leak), all passing.
- **Source cleanliness:** `source-cleanliness.json` — before CLEAN / after
  CLEAN at commit `b1f7a078`.
- **Cleanup:** `containers_removed=True networks_removed=True
  postgres_volume_preserved=True`.
- **Archive:** `~/Desktop/oce-b4-archive/run-34118435301/` (35 files, full
  independent verification above).

### CXR7U proof summary (each backed by registered tests)

- **Single-principal TCB model documented honestly** (CXR7U1): in-scope =
  adversarial inputs, forged/malformed/stale/expired/replayed/wrong-audience
  handoffs, unauthorized init/rotation/migration/override, corrupt state,
  partial writes/concurrency/replay races, untrusted job parameters, direct
  child entrypoint invocation. Out of scope = same-principal arbitrary code
  execution, compromised trusted component, `.runtime` read/modify,
  admin/root/SYSTEM, kernel/host, repo/runtime replacement, same-user
  debugger, mutually hostile same-principal isolation.
- **Verified children expose no parent issuance API** (CXR7U2):
  `VerifiedChildContext` has no `build_envelope`/`issue_child_handoff`/
  `child_environment`; behavioral tests prove ordinary issuance through a
  child context fails, parent issues every required audience, wrong audience
  fails before runtime activity, tampered/malformed handoffs fail, and
  ambient-only input without store access cannot create a valid MAC.
  Truth label: TYPE SEPARATION IS API-LEVEL LEAST PRIVILEGE AND DEFENSE IN
  DEPTH — not OS isolation.
- **Only repository-owned allowlisted programs execute** (CXR7U3): unknown
  job types fail closed before subprocess; parameters are data only (never
  source/argv/shell/imports/script paths/env or fs authority); shell
  disabled; workspace traversal/symlink escape/repo overlap blocked;
  production cannot select the test dependency seam;
  generated/downloaded/third-party/plugin/strategy/user-supplied/
  model-produced code MAY NOT EXECUTE until a real OS-isolation increment is
  separately authorized and proven.
- **Isolation reporting is literal** (CXR7U3): `BoundedProcessRunner` +
  `resource_limits_available`/`resource_enforcement_report`; POSIX reports
  resource bounding only; Windows reports watchdog/tree termination
  literally; network authorization denied by policy with OS network
  enforcement NOT IMPLEMENTED; no evidence calls this an adversarial
  sandbox.
- **Mutation tests never modify the canonical checkout** (CXR7U8R1): every
  control materializes a minimum runnable tree under `tmp_path`, pins cwd
  and PYTHONPATH to the copy, and hashes the canonical checkout
  before/after; byte-identity proven across normal mutant failure,
  mutation-function exception, subprocess timeout, subprocess termination,
  invalid mutant, and collection failure.
- **A mutation proof passes only when the expected assertion detects the
  mutant** (CXR7U8R1/R2): baseline collected-exactly-once/
  passed-exactly-once/rc=0 first; mutant digest verified changed; detection
  accepted only on normal completion with the expected node failed;
  JUnit-parsed; negative controls prove missing node ID, collection error,
  syntax-error mutant, timeout, unrelated failing test, and absent
  replacement pattern do NOT count as detection.
- **Configure is serialized and recoverable after actual process
  interruption** (CXR7U6/U8R3): whole-operation exclusive lock;
  authoritative bundle committed atomically; compose.env is a derived
  projection with an authority generation/fingerprint; interrupted
  projection rolls forward deterministically; real subprocess kills after
  every staging stage and during projection all recover on restart
  configure; two concurrent configure processes — exactly one succeeds, the
  loser fails without erasing the winner's commit; unrelated metadata
  survives; no stale rollback over a successful commit.
- **Audit retries reconcile without an aborted transaction** (CXR7U8R4):
  `INSERT ... ON CONFLICT DO NOTHING RETURNING audit_id` handles BOTH
  governed uniqueness constraints without aborting; no-row result
  reconciles against the durable row; exact semantic match is idempotent;
  divergence fails closed; every returned audit ID resolves to the durable
  row that exists (identity model B); the transaction remains usable after
  reconciliation; proven through the PRODUCTION sink on real PostgreSQL.
- **Audit durability proof is bound to the exact governed structure**
  (CXR7U8R4/U8-06): pinned database/role identity, public-schema table,
  exact column types AND nullability, PK specifically on audit_id,
  request_id uniqueness index bound to this exact table/schema/column
  (unique/valid/ready), append-only trigger calling the governed function,
  enabled; schema-mutation proofs (PK moved, same-named index in another
  schema/on another table/wrong column, wrong trigger function, cloned
  table in another schema) all fail the proof.
- **Corrupt secret authority never behaves like empty state** (CXR7U8R5):
  missing = uninitialized; unreadable/invalid-JSON/non-object/wrong-schema/
  wrong-typed = corruption (`SecretStoreCorrupt`/`SecretStoreUnreadable`);
  every read and mutation path (initialize/resolve/generation/revoke/
  rotate/configure/start/restart/recover) fails closed with store-bytes
  BEFORE == AFTER, no compose, no DB mutation, no process launch, no new
  authority file, no projection rewrite.
- **No mandatory security test can pass vacuously** (CXR7U7/U8R2): AST
  anti-vacuity gate (no `assert ... or True`, no `assert True`, no
  constant-false ternaries, no unconditional early returns before the
  security decision) + 8 mutation negative controls over parent/child
  separation, role/audience validation, atomic nonce consumption,
  corrupt-ledger refusal, audit canonicalization, configure
  rollback/recovery, trusted-program allowlisting, truthful isolation
  reporting.

### Historical evidence preserved

- **CXR6 closure:** implementation `fd5b32747dba1c93223093966c1edcee3b6680a6`,
  evidence head `f46e1beb21c6ec5f25c94278949dea946449a503`, workflow run
  `33555566041`, OCE_RUN_ID `c048f12cca64`, artifact `9819232513`
  (`b4-config-spine-evidence-c048f12cca64`), digest
  `ad41faac6a62462a125d60803bfaf5bc64e97f7106bce0516b801f900122e34a`,
  644/644 PASS — valid historical evidence for its registered suite.
- **CXR7 blocker:** `35b940cf` preserved verbatim (section above); not
  rewritten as a false alarm.
- **Intermediate failed runs preserved:** `33979406177` (4 failed + 34 errors
  -> U8X1) and `33986527406` (5 failed -> U8X2), with their failure artifacts
  downloaded and root-caused; both are truthful history, not closure proof.

### Boundaries and cost (this sequence)

- `main` unchanged: `7e7ef7222c4ecdea568b34583fd81406165cc9b6`.
- Capital authority: **none**. Cloud mutations: **0**. Broker mutations:
  **0**. Capital mutations: **0**. Execution-authority mutations: **0**.
- Recurring cost: **$0**. No Book 5, no Program Block 4, no OS-principal
  separation, no restricted tokens, no VM/container isolation expansion, no
  network firewall, no generated/model/plugin code execution, no cloud
  provisioning, no remote PostgreSQL, no GPU spend, no broker connection, no
  paper/live trading, no CEREBUS changes, no OpenClaw activation, no
  production deployment.

### Unresolved limitations (truthfully recorded, not blockers to this gate)

- OS network enforcement remains NOT IMPLEMENTED (policy denial only).
- Resource bounding is not hostile-code containment; the single-principal
  TCB model applies (same-principal arbitrary code execution is full local
  OCE compromise).
- Process-crash recovery is proven for process kill; power-loss durability
  of the atomic bundle replacement is bounded by the OS/filesystem semantics
  of atomic rename and is NOT separately proven.
- The AST anti-vacuity gate is static and cannot prove arbitrary test
  correctness; behavioral proofs remain authoritative.


## B4-CXR7U9 — PRE-MERGE PROOF AND QUALITY REPAIR (SUPERSEDED by the CXR7U9R23+ section below)


Start SHA: `caa1791e0f35f8975150577975867a96eafa7fc4` (CXR7U evidence head; not amended).
PR: #4 (base main, head oce-program-build, OPEN, not merged).

### Implemented repairs (CI-green on final head `3fef6615`)

- `b5b53de5` R1+R2: audit-proof transaction cleanup unconditional (every negative branch leaves TX_IDLE) + governed-identity binding (`proven_authoritative()`; structure-only `inspect_structure()` can never authorize an override).
- `c3e226a3` R3: production configure no longer consumes `CXR7U8_CONFIGURE_*` ambient variables; interruption instrumentation is a private in-process seam only.
- `9e3bf98f` R4: first Sonar repair round (28 findings).
- `15e116fd` R5: mandatory registry regenerated (875 unique full node IDs, zero duplicates).
- `bce3283e` X3: missing `PostgresAuditSink` import in shared `_pinned` helper (run 34590833387: 21 container failures, all one NameError).
- `db14871e` X4: MinIO artifact-store image repointed to `quay.io/minio/minio` with the identical pinned release tag after Docker Hub removed it (b1-local-ground runs 34698877725 + rerun failed on pull-access-denied; quay.io registry API verified the tag exists).
- `1a81dd7d` X5: all 25 visible Sonar failure-level findings — realpath fail-closed taint guards (pg-recovery, pg-verify, independent-gate), 4 cognitive-complexity extractions (oce_worker.main, validate_engine check_scaffold_scan/check_meta_test_evidence, recovery-ops.cmd_add), duplicate-literal constants, 15 shell `[[` conversions, restore.sh case default.
- `3fef6615` X6: S5734 — lifecycle CLI dispatcher no longer swallows `SystemExit`; it propagates to the `sys.exit(main())` boundary (behavior unchanged end-to-end; 771 local tests green).

### Authoritative CI on `3fef6615`

- b1-local-ground-validation: run 34703724053 — success.
- b2-control-plane-validation: run 34703724028 — success.
- b3-worker-fabric-validation: run 34703724068 — success.
- b4-config-spine-validation: run 34703724055 — success.
- B1-I1R Validation: pre-existing failure on every branch commit (stale Book-1 cloud-ground workflow requiring absent evidence); b1-local-ground is the in-force Book 1 regression and is green.

### Unresolved gate: SonarQube Security E / Reliability C (exit-gate statements 6 and 7)

The SonarCloud quality gate on new code remains Security E / Reliability C after two full repair rounds (X5, X6) covering every visible failure-level finding. The remaining gap is credential-blocked:

1. No Sonar token exists anywhere reachable: repository and organization secrets are empty, no scanner configuration exists, and SonarCloud analyzes the repository through its GitHub App.
2. The SonarCloud issues API returns an empty 200 response for this private project when unauthenticated — verified by sending the same request to a bogus project key and receiving an identical empty response — so the exact issue inventory cannot be enumerated.
3. The GitHub check-run annotation channel is capped at 50 issues and the visible set rotates as the head moves; findings visible across rounds were repaired, but ratings did not move, proving gate-driving findings exist beyond the visible cap.
4. Dispositions (true-positive fix vs false-positive marking) for the unseen findings — including the four AI-taint Path Traversal findings whose canonical disposition under the single-principal threat model is false-positive — require SonarCloud API write access.
5. Quality-gate weakening (NOSONAR suppression, exclusion patterns, severity downgrades, project policy changes) is prohibited by the CXR7U9 mission and was not performed.

Operator action required: provide SonarCloud API credentials for exact inventory and FP disposition, or explicitly accept the gate state. PR #4 remains OPEN and unmerged.

## B4-CXR7U9R23+ — FINAL CONVERGENCE (current status)

Authorized start SHA: `583614ff221eb4a020418547df4db6e23faf2a26`.
Current `main`: `d09941e75f3da6040254e0e6193dcf670207273b` (untouched by this
work; verified against the live ref).
PR: #4 — base `main`, head `oce-program-build`, **OPEN**, now **MERGEABLE**
(the Book 4 / main conflict was reconciled, not rewritten).

### Main reconciliation without history rewrite

`86fe3bef` **B4-CXR7U9R23** is a normal merge commit whose parents are
`583614ff` (first parent, the CXR7U9 start SHA) and `d09941e7` (current
main). No rebase, squash, amend, force push, or cherry-pick: every CXR7 /
CXR7U / CXR7U9 commit is still reachable and unmodified, `origin/main` is an
ancestor of the head, and `main` itself was never written to. The only
textual conflicts were the expected `.gitattributes` / `.gitignore`, resolved
by union, and `30d407d4` **X1** narrowed the reconciled LF normalization to
`.github/**` and `infrastructure/**` so main's CRLF-stored Python files are no
longer reported modified on a Linux checkout (which is what failed
b1-local-ground run `35173531507` with `source dirty (2)`).

### Ordered repair chain on this head

| Commit | Message | Why |
|---|---|---|
| `86fe3bef` | B4-CXR7U9R23 | reconcile current main without rewriting Book 4 history |
| `87bdc1b1` | B4-CXR7U9R24 | verified Gitleaks installer; evidence dir created before fallible installs |
| `44c3212e` | B4-CXR7U9R25 | prove the locked CI toolchain contract; Galaxy ranges labelled truthfully |
| `30d407d4` | B4-CXR7U9X1 | stop the reconciled LF rules from dirtying main's CRLF files |
| `da70f596` | B4-CXR7U9X2 | read the expected branch from the contract again |
| `1ed502fa` | B4-CXR7U9X3 | let the contract-scoped B1 workflow run on a dispatch head |
| `67f8547e` | B4-CXR7U9R26 | copy the restore archive into a private container directory |
| `b6054cf2` | B4-CXR7U9R27 | regenerate mandatory registry after final repairs |

Final implementation commit: `b6054cf2e812af976d36347adf2ed2464d66b76c`,
tree `b171cd3fa433ac50fa06d1a148366c6e9c642c56`.

### Correction of the previous R22 record

The R22 consumer workflows are **no longer unverified**, and the earlier
claim that they were is superseded. `b1-i1r3-validation` run `35169053088`
executed on `583614ff` and showed, truthfully: locked Python dependency
install PASS, locked Ansible toolchain install PASS, Gitleaks install FAIL
(`wget --max-redirect=0` cannot follow a GitHub release redirect, exit 8),
validation runner NOT EXECUTED, evidence upload FAIL (uninitialized path).
R24 repaired the download and reordered evidence initialization; R25
strengthened the lock proof; X2 and X3 repaired the two further defects that
only became reachable once the runner could start.

### Defects found and repaired in this convergence

- **X2 — `EXPECTED_BRANCH: unbound variable`.** The R8 override replaced the
  contract read instead of guarding it, so every run without an override died
  one line later under `set -u` (run `35222992244`). That is the whole
  push/dispatch path of b1-i1r3-validation, which is why it never surfaced
  before. The contract default is restored, with the contract path passed as
  argv so no caller-controlled string is parsed as Python code, and three
  proofs execute the shipped shell block under `set -u`.
- **X3 — contract-scoped workflow could not run on a dispatch head.** With X2
  fixed, the runner compared the observed branch against the checkpoint
  contract's `authorized_branch` (`oce`) while the engine it invokes is handed
  `--target-branch "$OBSERVED_BRANCH"`; on any other head the two disagree.
  b1-i1r3-validation now passes the same explicit, logged override the PR
  workflow passes (`OCE_EXPECTED_BRANCH=github.ref_name`), which resolves
  identically to the contract on its own push trigger.
- **R26 — genuine security defect.** `pg-recovery.py` copied the restore
  archive to a name this script chose inside a shared, world-writable
  container directory, so anything already in the container could pre-create
  that path; the archive now lands in a directory the container creates
  exclusively (`mktemp -d`, mode 0700), and a failed creation fails closed.
  The proof drives the real helper with stubbed docker calls and fails if the
  fixed shared-directory name returns.

### Authoritative CI on `b6054cf2` (all six success)

| Workflow | Run | OCE_RUN_ID | Result | Artifact |
|---|---|---|---|---|
| b1-i1r3-validation (dispatch) | 35226292176 | `d1db85eab1a5` | READY_FOR_OPERATOR_REVIEW | 10500055545 `b1-i1r3h-evidence-d1db85eab1a5` sha256:620c978c… |
| B1-I1R Validation (pull_request) | 35226291144 | `3181dd55c19d` | READY_FOR_OPERATOR_REVIEW | 10499172233 `b1-i1r-evidence-3181dd55c19d` sha256:4721e75a… |
| b1-local-ground-validation | 35226284783 | `456b98465eb5` | LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW | 10499446687 `b1-local-ground-evidence-456b98465eb5` sha256:285d56ce… |
| b2-control-plane-validation | 35226284789 | `3f0d4be95d73` | GATE PASS | 10499681151 `b2-control-plane-evidence-3f0d4be95d73` sha256:5df0890e… |
| b3-worker-fabric-validation | 35226284957 | `12fc1d8928d6` | GATE PASS | 10499086623 `b3-worker-fabric-evidence-12fc1d8928d6` sha256:5772ece3… |
| b4-config-spine-validation | 35226284955 | `fca2584a5c2f` | GATE PASS | 10499421520 `b4-config-spine-evidence-fca2584a5c2f` sha256:4cb451e3… |

Job-step detail for both B1 workflows: locked Python dependencies installed,
locked Ansible toolchain installed from `requirements-ansible.lock.txt`,
Gitleaks installed with `Checksum verified: 3e157a26081e296d4cb94ef0d87441c9afc5f392cb02957656dd5cfeb7aaf6c9`,
regression suite 67/67 with zero skips, INITIAL phase 31 executed / 0 skipped,
adversarial suite 49/49 in a disposable worktree, final phase 35 executed /
0 skipped, independent final gate `READY_FOR_OPERATOR_REVIEW` with
`{'PASS': 35, 'FAIL': 0, 'BLOCKED': 0, 'SKIPPED': 0}`, `CLEAN` both before and
after, and the evidence artifact uploaded. B1-I1R Validation evaluates the PR
merge ref (`bf10df5065a5`); b1-i1r3-validation evaluates `b6054cf2` directly.

B2/B3/B4 report `{"collected": 905, "executed": 905, "passed": 905,
"failed": 0, "errors": 0, "skipped": 0}` — the regenerated registry (905
mandatory ids, 19 categories, zero duplicates) matched actual collection in
CI. b1-local-ground reports 166 passed with no hidden skips.

### Independent artifact verification (performed, not asserted)

All six artifacts were downloaded and re-verified outside CI: each zip's
sha256 equals the digest GitHub reports for it, and every entry in each
`evidence-manifest.json` (7 + 7 + 37 + 33 + 33 + 33 = **150 entries**) matches
the extracted file's sha256 and size with **0 problems**. The verification
prefers exact paths because the artifacts hold same-named receipts in several
directories.

### Toolchain and checksum proof (R22/R24/R25)

- `requirements-ansible.lock.txt`: 38 resolved entries, every one exactly
  pinned with at least one sha256; installs via
  `pip install --require-hashes --only-binary ':all:'` in both B1 workflows;
  no loose `pip install ansible-core==…` remains; a tampered hash fails the
  install (proven locally and by the installer tests).
- Ansible Galaxy collections remain **range-constrained, not pinned**, and
  the file and workflows say so.
- Gitleaks `v8.18.1` is fetched over HTTPS via a redirect-capable client,
  authenticated by an embedded reviewed digest verified **before** extraction;
  a substituted archive aborts before tar runs. The runner log shows the
  digest it verified.

### SonarQube quality gate — still open, credential-blocked

Fresh window on this head (check-run `105213531803`): **D Security Rating on
New Code / C Reliability Rating on New Code** (required ≥ A),
50 annotations visible.

- Visible security-class findings: `pg-recovery.py` and
  `worker_supervisor.py` "Path Traversal via faulty LLM-supplied CLI
  arguments", and a ReDoS finding in `schema_validator._validate_string`.
  Both traversal sinks **already** canonicalize and contain their input
  (`_validated_open_path` against approved roots; realpath +
  `commonpath` inside the fenced runtime dir) — the analyzer does not follow
  containment implemented inside a helper, which is why earlier inline
  realpath repairs cleared two equivalent findings. Both are now backed by
  executable proofs (R27) rather than by assertion.
- The ReDoS sink already refuses over-bound input before the regex; R27
  proves the regex is never reached for over-bound input.
- The two `python:S5332` loopback-HTTP findings seen in the previous window
  match the deliberate Book 4 loopback architecture (no TLS terminator,
  127.0.0.1 bind, single-principal TCB) and need an **operator accepted-risk
  disposition**; they were not silenced.
- Exact inventory and rating remain unobtainable from this workstation: no
  Sonar token exists in the environment or the repository, and the
  unauthenticated issues API returns an empty 200 for every query (verified:
  `total: 0` for all types while the check window lists 50 issues), so it is
  not an authoritative inventory. The annotation channel is capped at 50 and
  rotates as the head moves.
- No quality-gate weakening was performed: no NOSONAR, no exclusions, no
  severity changes, no project-policy edits.

**Operator action required:** provide SonarCloud credentials for exact
inventory and false-positive/accepted-risk disposition, or explicitly accept
the gate state.

### Kilo Code Review — external service failure, not a code failure

`Kilo Code Review` failed on `30d407d4` with
`Workspace setup failed: sandbox storage full: termination nonzero exit, exit
code 128` inside `github.com/git-lfs/git-lfs/errors` — a storage failure in
the review sandbox while fetching LFS objects, not a finding about this
branch. Later heads show the review cancelled as superseded. main's
`*.parquet filter=lfs` rule was retained and no LFS history was rewritten to
satisfy it.

### Invariants for this convergence

- cloud mutations = 0 · broker mutations = 0 · capital mutations = 0 ·
  execution-authority mutations = 0 · recurring cost = $0.
- `main` unchanged (`d09941e7`); no PR merge performed; Book 5 not begun.
- No destructive stash/worktree cleanup, and no unrelated branch was pushed.

### Unresolved limitations

- The Sonar gate above (exit-gate statements 6 and 7) remains the only open
  exit condition.
- One R27 proof skips truthfully where the platform cannot create symlinks
  (Windows without the privilege); Linux CI exercises it.

## Confirmation (CXR7U)

CXR7U exit-gate statements 1-11 verified: single-principal TCB explicit (1);
handoff authenticates parent activation with role/audience consistency
without hostile-child claims (2); verified children expose no parent
issuance API (3); arbitrary/generated/third-party/plugin/model-produced code
execution blocked (4); resource/network/OS enforcement reported literally
(5); exactly one concurrent nonce consumer (6); corrupt security state fails
closed (7); audit retry proven through the real PostgreSQL sink (8); explicit
initialization complete-or-nothing (9); no mandatory security test passes
vacuously (10); final evidence claims only what the implementation proves
(11). Book 4 was closed at the CXR7U sequence; that closure is superseded by the
later B4-CXR7 / CXR7U9 repair sequence, so it is no longer the current status.
The current status is `IMPLEMENTATION CONVERGED — CLOSURE BLOCKED` (see the
CXR7U9R28–R30 section below).

## B4-CXR7U9R28–R30 — SUPERSEDING EXACT-HEAD EVIDENCE — `IMPLEMENTATION CONVERGED — CLOSURE BLOCKED`

**Gate:** B4-CXR7U9R30 · **Branch:** `oce-program-build` · **R30 start SHA:** `8ce72fb86c88a2d7768dc1c9a2bd9568f60d6aa1`
**PR #4:** OPEN, **not merged**, `MERGEABLE` (previously CONFLICTING), base `main` (`d09941e7`), head
`8ce72fb8`; the title remains *IN PROGRESS — NOT MERGE AUTHORIZED*.

### Why this section exists — it supersedes the finality claim above

`13d19acc3` (B4-CXR7U9-EVIDENCE) was valid evidence for implementation `b6054cf2`
(tree `b171cd3f`), and it stays historically valid for exactly what it tested.
Two implementation commits followed it, so it is **historical, not final**:

| Commit | Message |
|---|---|
| `25c7cef64` | B4-CXR7U9R28: make path-authority prose match enforcement |
| `8ce72fb86` | B4-CXR7U9R29: one containment owner, and its proof runs in CI |

**Final implementation commit:** `8ce72fb86c88a2d7768dc1c9a2bd9568f60d6aa1`,
tree `4e14b63fb69fcae9ecf18941ff40731143626344`.

R30 changed no implementation, test or workflow file — it is proof and evidence
only. No amend, squash, rebase, force push or history rewrite was performed;
`main` is untouched and is an ancestor of this head.

### What R28 and R29 changed

- **R28 (prose must match enforcement).** `_validated_open_path` in
  `pg-recovery.py` enforced `realpath == abspath` (symlink rejection),
  approved-root containment and a regular-file check while its own docstring
  said *"there is NO fixed approved root, so NO containment check is claimed"*
  and called its inputs `OPERATOR_TRUSTED_INPUT`. The byte-identical paragraph
  had been copied into `pg-verify.py`, and the path-authority suite repeated the
  claim — a third site the request had not named. All three now state the
  enforcement order the code implements (paths are data, never authority; the
  content SHA check still fails closed). The duplicated symlink probe in
  `test_worker_supervisor.py` was replaced with the inline `try/except OSError`
  idiom its two sibling tests already use, leaving one named probe project-wide
  (`needs_symlink` in the path-authority suite).
- **R29 (one owner, and the proof runs in CI).** `pg-verify.py` carried
  byte-identical copies of `pg-recovery.py`'s `_approved_roots`,
  `_validated_open_path` and `_validated_read_text` (63 lines) in a file that
  already loads `pg-recovery` as `_PG`, and re-implemented its inventory tamper
  check; it now binds those three from `_PG` and calls
  `_PG._load_protected_inventory` (−66 lines). That duplication is *why* the
  false docstring existed twice. `pg-recovery.py`'s documented step 2 no longer
  re-enumerates the roots `_approved_roots` owns, and the suite asserts the
  single-owner invariant (`test_containment_has_exactly_one_owner`) instead of
  looping every case over both modules. R29 also selected
  `test_b4_cxr7u9r7_path_authority.py` in the local-ground runner
  (`PATH_AUTHORITY_TEST`, beside the seven existing paths), so the containment
  proofs execute in CI rather than only on a workstation.

### Authoritative CI on the final implementation `8ce72fb8` — six workflows, all success

| Workflow | Run | Event | Tested identity | OCE_RUN_ID | Result | Artifact / digest | Manifest |
|---|---|---|---|---|---|---|---|
| b1-local-ground-validation | `35235034640` | push | commit = tested_commit = `8ce72fb8`, tree `4e14b63f`, branch `oce-program-build` | `d404adfb2910` | 185 collected / 185 executed / 185 passed / 0 failed / 0 errors / 0 skipped; independent gate PASS (60 checks, 0 failing) | `10502387873` `b1-local-ground-evidence-d404adfb2910` sha256:636784c162cfa5dead2a58864de08b7e6d3b14d7cc6666a4d98d1f863f475af9 | 37/37 |
| b1-i1r3-validation | `35261014346` | workflow_dispatch | commit = tested_commit = `8ce72fb8`, tree `4e14b63f`, attached checkout | `5f923dbc54e2` | final gate `{PASS: 35, FAIL: 0, BLOCKED: 0, SKIPPED: 0}`; regressions 67/67; adversarial 49/49 | `10514967859` `b1-i1r3h-evidence-5f923dbc54e2` sha256:bb0731167eba574c194ff9f561b10ae714d3d63a224ae0175f90d8b7d55e1dd3 | 7/7 |
| B1-I1R Validation | `35235039845` | pull_request | tests the PR merge ref `f18d17d6` (parents `d09941e7` + `8ce72fb8`), implementation_tree `4e14b63f` | `268190abb498` | final gate `{PASS: 35, FAIL: 0, BLOCKED: 0, SKIPPED: 0}`; regressions 67/67; adversarial 49/49 | `10503093307` `b1-i1r-evidence-268190abb498` sha256:b9dc05edc105caee842c9705fde737cc30dd27656d805c2492b4030b2f4ae304 | 7/7 |
| b2-control-plane-validation | `35235034603` | push | `8ce72fb8` / `4e14b63f`, ci_ref `oce-program-build` | `46414348160f` | 905/905/905/0/0/0; independent gate PASS (137 checks, 0 failing) + final verifier PASS (144 checks, 0 failing) | `10502327671` `b2-control-plane-evidence-46414348160f` sha256:fb0ef33cbd97de08908878d1616c9236628e29a20154c6d5c702b93efcfdc4aa | 33/33 |
| b3-worker-fabric-validation | `35235034573` | push | `8ce72fb8` / `4e14b63f`, ci_ref `oce-program-build` | `a9c677c71226` | 905/905/905/0/0/0; both gates PASS | `10502883096` `b3-worker-fabric-evidence-a9c677c71226` sha256:7a3be7e0fe139c97ba4b2a9bb9dee2da39029c7f88a6097af1c42b9c5688efb3 | 33/33 |
| b4-config-spine-validation | `35235034620` | push | `8ce72fb8` / `4e14b63f`, ci_ref `oce-program-build` | `56fb88c3281e` | 905/905/905/0/0/0; both gates PASS | `10502967772` `b4-config-spine-evidence-56fb88c3281e` sha256:002705a70299639f5eacda39be5c4322c6ba2320c3a372710206b09e6839b69d | 33/33 |

Every job step of every one of the six runs concluded `success` (12/12 in the four
push workflows, 15/15 in both B1 workflows), including *Install pinned Python
dependencies*, *Install Ansible and ansible-lint*, *Install Gitleaks (verified
checksum, outside the workspace)*, *Run shared validation runner* and *Upload
evidence artifact*. b2/b3/b4 report `source-cleanliness` clean **before and
after**; b1-local-ground writes `source-clean.json`; B1-I1R logs `STEP d: source
clean` and `STEP j: source still clean` with `worktree-cleanup {removed: true,
pruned: true}`. Cleanup: `compose_down_rc 0`, `containers_remaining []`,
`networks_removed true`, durable Postgres volume preserved.

Manifest verification was performed by downloading each artifact, not copied:
every zip's sha256 equals the digest GitHub reports, and every manifest entry
(37 + 7 + 7 + 33 + 33 + 33 = **150**) matches the extracted file's sha256 and
size — **0 problems**. Entries are matched on exact paths because these
artifacts legitimately hold same-named receipts in nested `operations/`
directories; a basename-only matcher reports three false mismatches.

### Path-authority proof now executes in CI (R29)

Run `35235034640` executed the suite at **19 collected / 19 executed / 19 passed
/ 0 skipped**, including `test_symlink_file_rejected`,
`test_symlink_parent_directory_rejected`,
`test_cli_argument_cannot_approve_its_own_root`,
`test_denial_has_zero_durable_side_effects` and
`test_containment_has_exactly_one_owner`. The local-ground runner's selection is
185 collected/executed/passed, up from 166 before the wiring; the earlier
statement in this record that the traversal sinks were "backed by executable
proofs (R27)" is only now literally true for the `pg-recovery.py` sink.

### Mandatory registry

`infrastructure/control-plane/scripts/b2_registry.py` holds **905 unique full
node ids with zero duplicates** (two further quoted strings containing `::` are
category prefixes, not node ids) and the runner fails closed on duplicates.
b2/b3/b4 collected exactly 905 and passed 905/905 on this head — independent
proof that the committed registry matches actual collection. R28/R29/R30 changed
no collected node id, so no regeneration was required.

### SonarQube quality gate — unresolved; requires operator credentials and a disposition decision

Check-run `105249956178` on `8ce72fb8`: **D Security Rating on New Code / C
Reliability Rating on New Code** (required ≥ A) — gate failed. Classification of
what is obtainable:

- **EXTERNAL_OR_UNAVAILABLE_EVIDENCE (the inventory itself).** The GitHub
  annotation channel returns exactly 50 entries — GitHub's cap — and rotates as
  the head moves, so it is a window, not an inventory. No Sonar token exists in
  this environment; the repository exposes no secret and carries no scanner
  configuration (SonarCloud analyzes through its GitHub App); and the
  unauthenticated issues API returns `total: 0` for this project **and** for
  unrelated public projects, so it cannot enumerate anything.
- **OPERATOR_ACCEPTED_RISK_REQUIRED.** Two `python:S5332` "Using HTTP protocol
  is insecure" findings at `config_startup.py:1130` and `:1435` match Book 4's
  deliberate loopback-HTTP architecture (127.0.0.1 bind, no TLS terminator,
  operator-accepted single-principal TCB). They were not silenced and cannot be
  cleared from this workstation.
- **Containment proof the analyzer cannot follow.** One "Path Traversal via
  faulty LLM-supplied CLI arguments" at `pg-recovery.py:584`. Trace performed on
  the source: taint enters as the `--archive` CLI argument and reaches
  `open(os.path.realpath(_validated_open_path(archive)), "rb")`;
  `_validated_open_path` enforces, in order, `realpath(path) == abspath(path)`
  (symlink indirection rejected), containment in `_approved_roots()` (program
  identity from `realpath(__file__)` plus the operator-declared
  `OCE_BACKUP_ROOTS`), and existing-regular-file. The artifact path cannot
  supply its own containment root and denial has no durable side effect — all
  four properties are executed by the 19 CI tests above. The remaining
  discrepancy is the analyzer's inability to follow containment implemented
  inside a helper (the earlier inline `realpath`/`commonpath` repairs are what
  cleared two equivalent findings). Clearing it in Sonar therefore needs either
  a false-positive disposition or an inline repair; an inline repair is a source
  change that would invalidate all six proofs above while leaving the `S5332`
  items — and hence the failing Security rating — in place.
- The 13 failure-level entries in the window are duplicate-literal,
  cognitive-complexity, shell-idiom and composite-assertion items; the
  operator's standing direction is that they are code smells and are not to be
  chased for this gate.

No NOSONAR, exclusion, severity change, quality-profile or gate-policy edit was
made. **Operator action required:** SonarCloud credentials for the exact
inventory plus an accepted-risk decision on the loopback-HTTP findings.

### Kilo Code Review — external sandbox failure, not a finding about this branch

`Kilo Code Review` check-run `105248679429` failed on `8ce72fb8` with `Review
failed: Workspace setup failed: sandbox storage full: termination nonzero exit,
exit code 128`, raised inside `git-lfs` while smudging main's LFS object
(`.../ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet: smudge filter lfs
failed`; `Clone succeeded, but checkout failed`). It published **zero
annotations**: the reviewer never reached the branch, so this is a
review-*service* capacity failure, re-verified on this head rather than assumed
from the earlier one. One retry was requested with `POST
/repos/dabiggestpoppa/larger-lab/check-runs/105248679429/rerequest` (accepted by
the API; no new Kilo check-run was created), so the failing check-run remains the
only Kilo result. main's `*.parquet filter=lfs` rule was retained and no LFS
history was rewritten to satisfy it.

### Invariants

cloud mutations = 0 · broker mutations = 0 · capital mutations = 0 ·
execution-authority mutations = 0 · recurring cost = $0 · `main` unchanged at
`d09941e75f3da6040254e0e6193dcf670207273b` · PR #4 OPEN and unmerged · Book 5 not
begun · no unrelated branch pushed · no stash or worktree destroyed.

### Unresolved limitations

1. The Sonar gate (exit-gate statements 6 and 7) is unsatisfied: it needs
   credentials for the exact inventory and an operator accepted-risk decision
   for the deliberate loopback-HTTP findings.
2. Kilo Code Review cannot complete inside its own sandbox while the
   repository's LFS objects exceed that sandbox's storage; external, and the one
   permitted retry did not change it.
3. `b1-i1r3-validation` runs the contract-scoped B1 increment on a non-`oce` ref
   through the explicit `OCE_EXPECTED_BRANCH` override (X3). Its artifact
   records `expected_branch=oce`, `observed_git_branch=oce-program-build`,
   `branch_provenance=git-symbolic-ref`, and the gate accepted it. Disclosed for
   operator ratification; it is a contract question, not a code change.
4. Windows hosts without the symlink privilege skip the platform-dependent
   symlink cases locally; Linux CI executes them (19/19 above).
5. The annotation channel's 50-entry cap means the visible Sonar list is a
   window; no claim is made about findings outside it.

### Final commit discipline

This section is documentation/evidence only. Its parent is the final
implementation commit `8ce72fb86c88a2d7768dc1c9a2bd9568f60d6aa1`; it changes no
Python, shell, workflow, registry, migration or executable file.

## ERRATUM — correction of remote-state claims, current-head check state, and R28 scope

**Observation basis:** every live-state fact in this erratum was read in one pass
from the GitHub REST API, the GitHub CLI and `git ls-remote` at
**2026-09-17T19:31:25Z**, and each is anchored to the commit it was read for.
Nothing below is inferred from an earlier reading.

**Why an erratum and not an edit:** the claims corrected here were committed in
`a932e8e5`. They were not fabrications — they were *unanchored* observations
whose refs moved (this campaign has now seen `main` advance and PR mergeability
flip twice) — so they are corrected in place without deleting or rewriting any
text of this record, including the sentences quoted below.

### E1 — PR #4 is `CONFLICTING`, not `MERGEABLE` (supersedes line 1201)

Quoted, as committed (line 1201): "**PR #4:** OPEN, **not merged**, `MERGEABLE`
(previously CONFLICTING), base `main` (`d09941e7`), head `8ce72fb8`".

Corrected, read at 2026-09-17T19:31:25Z for head
`a932e8e56d3d88acc728fb06727edc36bec33b60`:

| Field | Value at 2026-09-17T19:31:25Z |
|---|---|
| `state` | `OPEN` |
| `merged` / `merged_at` | `false` / `null` |
| `mergeable` | `CONFLICTING` (REST `mergeable=false`, `mergeable_state=dirty`) |
| `mergeStateStatus` | `DIRTY` |
| `baseRefOid` | `d09941e75f3da6040254e0e6193dcf670207273b` |
| `headRefOid` | `a932e8e56d3d88acc728fb06727edc36bec33b60` |
| `title` | unchanged, `IN PROGRESS — NOT MERGE AUTHORIZED` |
| `url` | `https://github.com/dabiggestpoppa/larger-lab/pull/4` |

So `base main (d09941e7)` was correct **as GitHub's `baseRefOid`** and stays
correct at that field; `MERGEABLE` is the wrong value. It was true when read
before this branch's own evidence push and became false when `main` moved, which
is precisely the failure mode this erratum exists to stop.

### E2 — `main` is `7c7816f3`, not `d09941e7` (supersedes line 1360 and line 13)

Quoted, as committed (line 1360): "execution-authority mutations = 0 · recurring
cost = $0 · `main` unchanged at `d09941e75f3da6040254e0e6193dcf670207273b`".
Quoted, as committed (line 13): "**main:**
`d09941e75f3da6040254e0e6193dcf670207273b` (untouched; the CXR7U9 start SHA
`583614ff…` was reconciled into this branch)".

Corrected, read at 2026-09-17T19:31:25Z: `refs/heads/main` =
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. The advance is two commits,
`813f8da8` ("docs(oce): record unified OCE convergence end state") and
`7c7816f3` ("docs(oce): point main at convergence end state"), touching only
`docs/oce-golden-system/OCE_CONVERGENCE_END_STATE_AND_BRANCH_ROLES_v1.0.md` and
`docs/oce-golden-system/README.md`.

Facts that remain true and are **not** corrected: this branch never wrote to
`main` (every CXR7U9 push targeted `refs/heads/oce-program-build`, at
2026-09-17T19:31:25Z = `a932e8e56d3d88acc728fb06727edc36bec33b60`); `d09941e7` is
a strict ancestor of `7c7816f3`; `7c7816f3` is not an ancestor of this head; no
PR merge was performed.

### E3 — the evidence head `a932e8e5` has its own check state, recorded here for the first time

Read at 2026-09-17T19:31:25Z for
`a932e8e56d3d88acc728fb06727edc36bec33b60`; the commit carries **five
check-runs and no SonarCloud check-run**:

| Check | Conclusion | Check-run id | Run / URL |
|---|---|---|---|
| `validate` (b1-local-ground-validation) | success | 105341155715 | run 35262414558 |
| `validate` (b2-control-plane-validation) | success | 105341155605 | run 35262414545 |
| `validate` (b3-worker-fabric-validation) | success | 105341155728 | run 35262414735 |
| `validate` (b4-config-spine-validation) | success | 105341156122 | run 35262414638 |
| `Kilo Code Review` | **failure** | 105341155513 | https://github.com/dabiggestpoppa/larger-lab/runs/105341155513 |
| `SonarCloud Code Analysis` | **absent** | — | — |

- Kilo, exact reason as published for this head: title `Kilo Code Review failed`,
  summary `Review failed: Workspace setup failed`, **0 annotations**, started
  `2026-09-17T19:01:51Z`, completed `2026-09-17T19:21:08Z`, review detail
  `https://app.kilo.ai/code-reviews/209e56d1-366c-483a-ace9-a6c13df74c1c`. This is
  the same failure class as `8ce72fb8` (check-run `105248679429`: `Review failed:
  Workspace setup failed: sandbox storage full`, exit 128 in `git-lfs` while
  smudging main's Parquet object, review detail
  `https://app.kilo.ai/code-reviews/1bddc74d-c6a6-4798-9a16-e988aecbd291`), but
  *this* output carries less detail, so the shared class is inferred from the
  identical title and the workspace-setup stage, not asserted from this text.
- **No SonarCloud check-run exists on `a932e8e5`**, so the evidence commit has no
  Sonar verdict at all — neither pass nor fail. The only Sonar verdict in this
  campaign remains check-run `105249956178` on `8ce72fb8` (`Quality Gate failed`,
  `D Security Rating on New Code` / `C Reliability Rating on New Code`,
  completed `2026-09-17T14:42:51Z`, detail
  `https://sonarcloud.io/dashboard?id=dabiggestpoppa_larger-lab&pullRequest=4`).
- Consequence: "all six required workflows pass on the final implementation"
  holds for `8ce72fb8` and does **not** transfer to the evidence commit. B1-I1R
  Validation cannot run on `a932e8e5` while the PR is conflicting, because a
  `pull_request` workflow needs a merge ref that GitHub does not build for a
  conflicting PR.

### E4 — R28's real scope (corrects its description in the R28–R30 section above)

The section above describes R28 as the path-authority prose commit plus the
symlink-probe collapse. Its actual diff is **8 files, +80 / −112**, tree
`5da5593f5e1b3350c2da78a455735391222b77d8`:

| File | + | − |
|---|---|---|
| `.github/workflows/b1-i1r3-validation.yml` | 4 | 12 |
| `infrastructure/cloud-ground/scripts/install-gitleaks.sh` | 10 | 20 |
| `infrastructure/cloud-ground/scripts/run-validation.sh` | 6 | 15 |
| `infrastructure/control-plane/tests/test_worker_supervisor.py` | 4 | 16 |
| `infrastructure/local-ground/scripts/pg-recovery.py` | 23 | 21 |
| `infrastructure/local-ground/scripts/pg-verify.py` | 16 | 13 |
| `infrastructure/local-ground/tests/test_b4_cxr7u9r7_path_authority.py` | 11 | 8 |
| `infrastructure/local-ground/tests/test_gate_regressions.py` | 6 | 7 |

The unrecorded content is the clarity pass carried in the same commit: comment
trims in `b1-i1r3-validation.yml`, `install-gitleaks.sh` and `run-validation.sh`,
and the consolidation of the installer-contract assertions in
`test_gate_regressions.py` into the test that owns them. Recorded here because
the CI evidence on `8ce72fb8` depends on these files, and a reader auditing what
R28 changed could not see this from the previous description. For completeness,
R29's diff is 4 files, +40 / −102 (`pg-verify.py` −65 net, the rest the suite and
the runner's selection line).

### E5 — rule for citing remote state in this record

Remote state is an **observation with an as-of time**, never an invariant. Every
citable remote fact is written as `value, read at <UTC timestamp>, for <SHA>`.
Before citing `mergeable`, `mergeStateStatus`, `baseRefOid`, `headRefOid`,
`refs/heads/main`, or which check-runs exist on a head, re-read them and state
the new timestamp. The three claims corrected above were all true when first
read; they became false because refs moved, and nothing in this record said when
they had been read.

### E6 — scope of this erratum

Documentation only. It changes no implementation, test, workflow, registry,
migration or expected-branch file, and it merges nothing. No text of this record
is deleted or rewritten, including the claims quoted in E1–E4. Parent commit:
`a932e8e56d3d88acc728fb06727edc36bec33b60`; `refs/heads/main` at write time:
`7c7816f382947bbc8a1f2154435fc436f2428fa8`, untouched by this branch.

## B4-CXR7U9R32–R33 — ADJUDICATION OF THE SONAR TRAVERSAL FINDING AND SINK-BINDING PROOF — `IMPLEMENTATION CONVERGED — CLOSURE BLOCKED`

Appended after the erratum above, under the same rule: every remote-state
statement below is written as *value, read at UTC timestamp, for SHA* — re-read
before citing. No earlier section of this record is modified; where an earlier
section is superseded, that is stated here rather than edited there. Docs-only:
no source, test, workflow, registry, migration or expected-branch file.

### R34.1 — adjudication: DEMONSTRATED_FALSE_POSITIVE (no TRUE_DEFECT repaired)

The failure-level Sonar annotation "Path Traversal via faulty LLM-supplied CLI
arguments" on `infrastructure/local-ground/scripts/pg-recovery.py` is ONE taint
finding whose anchor moves between analysis windows:

* `:584` — the `open(os.path.realpath(_validated_open_path(archive)), "rb")`
  sink in `phase_promote` (annotation window read 2026-09-17T19:40Z for
  `a932e8e5`);
* `:294` — `sha256_file`'s unconstrained `path` parameter, reached by the same
  flow's `sha256_file(_validated_open_path(archive))` call at :570 (window read
  2026-09-17T20:15Z for `a856c1a6`, check-run `105362413305`);
* `:397` — `_load_receipt`'s `open(_validated_open_path(path))`, the same
  flow's receipt-input branch (window read 2026-09-17T21:01:47Z for
  `54f5193b`, check-run `105374693997`).

All three anchors sit on one source-to-sink flow: the `--archive`/`--receipt-in`
CLI arguments (LLM-supplied) reach the container-bridge and `open()` sinks only
through `_validated_open_path` — single owner, shared with `pg-verify.py` via
the R29 import binding — whose enforcement order is (1) `realpath == abspath`
(symlink indirection refused), (2) containment in `_approved_roots()` (program
identity: engine dir + `var/recovery`, plus the operator-declared
`OCE_BACKUP_ROOTS`; a CLI/artifact argument can never approve its own root),
(3) existing regular file. Adjudication: **DEMONSTRATED_FALSE_POSITIVE** —
containment proof Sonar's taint engine cannot follow. No TRUE_DEFECT exists in
this flow, so no source repair was made; the anchors moved because the engine
re-anchors within the guarded flow, not because three defects were found and
left open. The window's other traversal-class item,
`independent-gate-b2.py:275` (read for `54f5193b`, see 21:01:47Z above), is the
same class in a different file, covered by `TestGateOpsRootContainment` in the
same CI-executed suite; the loopback-HTTP `python:S5332` findings remain an
operator-disposition item, unchanged.

### R34.2 — the four adjudication conditions, each proven at the shipped surface

Suite `infrastructure/local-ground/tests/test_b4_cxr7u9r7_path_authority.py`,
selected by the real local-ground runner since R29:

1. **Approved-root authority cannot be supplied by the artifact path** —
   `_approved_roots()` consults only `__file__`-derived identity and the
   `OCE_BACKUP_ROOTS` env channel; proven by `test_cli_argument_cannot_approve_its_own_root`
   and the CLI `self-declared-root` refusal case.
2. **Canonical containment** — probe matrix (out-of-band, Windows host,
   2026-09-17 ~19:50Z): dot-slash, double-slash, in-root `..` all resolve to
   the same contained file; escape `..`, absolute-outside, and the
   prefix-sibling root (`roots-evil` beside `roots`, which a `startswith`
   containment check would admit) are refused. Pinned in CI by
   `test_every_admitted_spelling_resolves_inside_an_approved_root` (R33) and
   `test_prefix_sibling_outside_the_root_is_refused` (R33).
3. **Symlink rejection** — `test_symlink_file_rejected` plus the CLI
   `symlink-into-root` case whose target IS inside an approved root and is
   still refused; executed on Linux CI with zero skips (see R34.4).
4. **Denial with zero durable side effects** — the four hostile-archive CLI
   refusals (R32: outside-root, dot-dot, self-declared root, symlink-into-root)
   each assert exit 1, `phases == ["inventory_validated"]`, `promoted is False`,
   `quarantine_dropped is False`, and that the caller's receipt is the only
   file created anywhere (`set(after) - set(before) == {receipt}`);
   instrumented-`phase_promote` cases prove the guard precedes every docker
   call, with a vacuity control showing the instrumentation DOES observe calls
   for an approved archive.

### R34.3 — the two proof commits

* `a856c1a6c58c43cfa4d0c5f34e4e5ef7b0c08cb8` — `B4-CXR7U9R32: prove the
  promote sink refuses hostile archives` (+6 tests driving the real CLI and
  `phase_promote`; red-green verified out-of-band in a scratch tree: with the
  guard removed, 9 tests fail including hostile archives reaching the container
  bridge with 3 recorded `mktemp -d` calls).
* `54f5193b336bc34d4313fc8231cd4c767a0ad376` — `B4-CXR7U9R33: prove every
  promote sink receives the validator's contained path` (+4 tests binding the
  VALUES the sinks receive: `sha256_file`'s parameter and the `docker cp`
  source observed during a real promote equal the validator's canonical
  contained path; every admitted spelling resolves to that file; prefix-sibling
  refused; the engine's only `sha256_file` call site AST-bound to the validator,
  red-green verified out-of-band — a scratch copy with the wrapper removed or a
  second raw call added fails the invariant; shipped source passes).

Tree at `54f5193b`: `84fe43b3cc85f8522c55ce9aa1de7089fae71d88`.

### R34.4 — re-run evidence on `54f5193b` (all five runs verified from artifacts)

| Workflow | Run | Event | Result |
|---|---|---|---|
| b1-local-ground-validation | 35272160396 | push | junit **195/195/0/0/0** (was 185: +4 R33, +6 R32, +4 net from R29/R30-era drift), manifest **37/37** exact-matched (hash+size; the 3 basename-collision receipts resolved by exact-name matching, the R30 lesson), path-authority **29/29, 0 failed, 0 skipped** XML-parsed, all 4 R33 tests executed by name |
| b2-control-plane-validation | 35272160470 | push | 905/905/0/0/0 |
| b3-worker-fabric-validation | 35272160448 | push | 905/905/0/0/0 |
| b4-config-spine-validation | 35272160318 | push | 905/905/0/0/0 |
| b1-i1r3-validation | 35272231471 | workflow_dispatch | regressions 67/67, adversarial 49/49, OCE_RUN_ID `e14c8008b740`, `tested_commit == 54f5193b`, tree `84fe43b3` in `initial-validation-results.json` |

All five: conclusion success, zero non-success and zero skipped steps (per-step
API read 2026-09-17T20:55–20:58Z for `54f5193b`); identity records prove
`commit == tested_commit == 54f5193b…` and `tested_tree == 84fe43b3…`.
Registry regeneration is a verified no-op: `collected 905 mandatory ids,
registry OK: total=905 categories=19`, zero duplicate node IDs, zero
local-ground node ids (local-ground is collected by the runner, not the
control-plane registry), file unchanged — no separate registry commit required.
Local fresh suites (Windows host, 2026-09-17 ~20:30Z): path-authority 25
passed / 4 truthful Windows symlink skips, gate regressions 58 passed,
backup-hardening 42 passed; `py_compile` + `ruff` clean; no docker stack left.

The sixth authoritative workflow, `b1-i1r-validation`, has NO sanctioned
execution path on this head: its triggers are `push:
oce/block-1-i1r-truth-repair` and `pull_request: branches: [main]` with no
`workflow_dispatch` (source read at `54f5193b`), and PR #4 is CONFLICTING, so
no merge ref exists for a pull_request run to build. Its latest green run
(`35235039845`, PR merge-ref `f18d17d6`, tree `4e14b63f`, R30-era) predates
R32/R33 and is **historical**.

### R34.5 — historical relabel (mission section 6)

All run evidence recorded for earlier heads — the 8ce72fb8 five-run set and
`35261014346`, the a856c1a6 five-run set (`35268241881` b1-i1r3,
`35268236276` b4, `35268236273` b3, `35268236275` b1, `35268236324` b2), and
every run cited in sections above — is **historical**: it proves the trees it
tested and no longer the current head. The runs in R34.4 on `54f5193b` are the
current authoritative set. R32/R33 changed tests and proof only (no production
source, workflow, or registry file), so the control-plane/worker-fabric/config-
spine binaries they exercised are unchanged; the b2/b3/b4 re-runs on
`54f5193b` confirm 905/905 on the new tree regardless.

### R34.6 — current check-run state on `54f5193b` (fresh read 2026-09-17T21:01:47Z for `54f5193b`)

* `SonarCloud Code Analysis` — **failure**, check-run `105374693997`,
  completed 2026-09-17T20:42:12Z; Quality Gate D Security / C Reliability on
  new code; 30 annotations in the exposed window; the only traversal-class
  items are `pg-recovery.py:397` (adjudicated R34.1) and
  `independent-gate-b2.py:275` (same class, same suite coverage).
* `Kilo Code Review` — **queued** at read time ("Waiting for a review slot…",
  check-run `105373959340`). Prior exact-head observations: on `a932e8e5` it
  failed `Review failed: Workspace setup failed` with 0 annotations (check-run
  `105341155513`), and on `8ce72fb8` it failed in its own sandbox with storage
  full during LFS smudge, 0 annotations — external review-service capacity,
  not source findings.
* `validate` × 5 — success (ids `105373921246`, `105373921529`,
  `105373921715`, `105373922122`, `105374153614`), one per R34.4 run.

### R34.7 — status

**IMPLEMENTATION CONVERGED — CLOSURE BLOCKED.** Book 4 is not closed. The
remaining blockers, unchanged by R32/R33: (1) the Sonar quality gate reports
D/C against required A/A — the pg-recovery traversal finding is adjudicated
false-positive with executable CI proof, but the loopback-HTTP `python:S5332`
findings need an attributable operator accepted-risk disposition or an
authorized TLS architecture change, and no Sonar credentials exist on this
machine for an authoritative full inventory; (2) `b1-i1r-validation` cannot
fire on this branch while PR #4 is CONFLICTING (main advanced externally to
`7c7816f3…`, read 2026-09-17T21:01:47Z; `main` remains untouched by this
branch) and has no workflow_dispatch trigger; (3) PR #4 remains OPEN,
unmerged, title `IN PROGRESS — NOT MERGE AUTHORIZED`. PR #4 state: open,
merged=false, mergeable=CONFLICTING, mergeStateStatus=DIRTY, base
`d09941e7…`, head `54f5193b…` (GraphQL read 2026-09-17T21:01:47Z for
`54f5193b`). Cloud mutations 0; broker mutations 0; capital mutations 0;
execution-authority mutations 0; recurring cost $0. Book 5 not begun.

---

## B4-CXR7U9R39 — SUPERSEDING SECTION (2026-09-23)

This section supersedes everything above it as CURRENT TRUTH. The R34 and
earlier sections remain valid HISTORICAL evidence for their own exact heads;
they do not describe the current implementation.

### R39 scope

Independent review found four closure gaps after R35–R38: (A) a cross-store
partial restore (the artifact volume was replaced before PostgreSQL
recovery, so a PG failure left the two durable stores from different
snapshots); (B) ambient receipt-write authority (`OCE_RECOVERY_STATE_DIR`
could grant the write root); (C) receipts were structurally valid but
replayable (no durable one-time transition authority); (D) main and build
were not converged (two reviewed strategic-documentation commits absent).

### R39 commits (all pushed, `oce-program-build`, none amended or squashed)

| Commit | Message |
|---|---|
| `87792340` | B4-CXR7U9R39M1: reconcile current main doctrine into build branch (merge of origin/main `7c7816f3`; README.md resolved semantically — main's convergence doctrine preserved, stale `oce`-branch and Block-1 claims historical-labeled) |
| `a7287175` | B4-CXR7U9R39R1: make full replacement rollback-coherent across durable stores (staged two-resource protocol: artifact staged + live snapshot, PG promoted with quarantine held, both verified, then commit; any pre-commit failure restores both stores and writes a truthful transaction-rollback receipt) |
| `56c99c10` | B4-CXR7U9R39R2: make receipt persistence governed and collision safe (write authority is program identity `var/recovery`; no environment override; symlink rejection in target and parents; receipt-in == receipt-out refused; exclusive O_CREAT, no overwrite of an existing receipt; collision-resistant same-directory temporaries; flush + directory fsync; residue cleaned on failure) |
| `e36a4878` | B4-CXR7U9R39R3: make recovery transition authority durable and single use (per-promotion high-entropy operation id; durable record under `var/recovery/transitions`; CREATED→STAGED→PROMOTED→FINALIZED/ROLLED_BACK/FAILED; content-digest binding receipt↔record; replay/substitution/cross-operation/cross-run denied before any docker or catalog call; exclusive claim files make the one-time consumption atomic) |
| `d9399c9b` | B4-CXR7U9R39R4: prove the recovery transaction and transition invariants (container-backed cross-store cases, gate-selection wiring, registry regeneration from real collection) |
| `7f7a852b` | B4-CXR7U9R39X: repair the CI-exposed recovery-transaction defects (see below) |
| `f69f8aa7` | B4-CXR7U9R39X: create the evidence directory restore.sh writes receipts into |
| `351fe6a6` | B4-CXR7U9R39X: name the failure site in the rollback receipt and align the stopped-state identity check |
| `4f362b7d` | **CURRENT R39 IMPLEMENTATION HEAD** — B4-CXR7U9R39X: prove restored user-data truth, not MinIO's runtime bookkeeping; tree `e3e24484bea90fe251e55566b6549ce277948c60` |

### CI-exposed repairs (R39X) — what CI proved beyond the local suite

CI run `35770877299` (head `d9399c9b`, 14 failures, artifact-reproduced)
proved two production defects and two harness defects:

1. **Artifact identity was hashed after `docker start`**: MinIO reformats
   its pool on startup (writes format metadata into /data), so the restored
   volume could never verify against the staged snapshot — the SUCCESS path
   itself blocked. Every identity restore.sh compares is now captured while
   the artifact service is stopped; the service starts only after
   verification passes.
2. **Rollback verified the restored original against the backup's
   inventory**, but a full replace exists precisely because the original can
   differ from the backup (PG logs: `relation "public.backup_probe" does not
   exist` after a correct restore). Promotions now capture a pre-promotion
   ROLLBACK FLOOR before any durable mutation, persist it in the durable
   operation record, and every rollback verifies the restored original
   against the floor, never the backup. This also fixed the finalize
   rollback path (the quarantine was being dropped by the failing finalize
   before `phase_rollback` could use it — the earlier "quarantine database
   missing" failures).
3. restore.sh never created `OCE_EVIDENCE_DIR` — best-effort evidence copies
   silently discarded receipts (run `35869637929`); the run now creates it.
4. Each BLOCKED exit inside the transaction names its failure site in the
   rollback receipt reason (run `35871528334`: the physical rollback already
   passed; only the receipt's generic reason failed the binding check).

### Final CI truth (exact head `4f362b7d`, all five workflows)

```
35874437326  b1-local-ground-validation  success
35874437336  b2-control-plane-validation success
35874437355  b3-worker-fabric-validation success
35874437497  b4-config-spine-validation success
35874446142  B1-I1R Validation           success (after one transient
             runner-DNS failure against galaxy.ansible.com on the first
             attempt of this run; the identical step succeeded on the two
             previous heads; failed-job rerun per GitHub policy; cloud-ground
             untouched by R39)
```

Local-ground suite at this head: 276 collected / 276 executed / 262+ passed,
0 failed (per CI artifact test-summary.json; the container-backed recovery
transaction cases all pass, including interrupted full-replace and finalize
replay). Gate-regression synthetic-package failures from the earlier R4 gate
wiring are fixed (the fixture now carries the R39 must-pass selection).

### R39 exit-gate truth

- main doctrine converged: origin/main `7c7816f3` merged as `87792340`; main itself untouched
- PR #4: OPEN, MERGEABLE, head `4f362b7d` (NOT merge-authorized; no merge performed)
- cross-store coherence: proven container-backed (failure cases restore both stores; success commits both stores from one backup)
- ambient receipt-write authority: removed (program identity only; hostile `OCE_RECOVERY_STATE_DIR` proof passes)
- receipt writes: no symlink following, no overwrite, exclusive creation, residue-free failure
- transition authority: durable, one-time, digest-bound; replay/substitution/cross-operation denied before mutation
- SonarCloud: unchanged blocker (credentials/operator disposition still required; not weakened, no NOSONAR added)
- cloud mutations 0; broker mutations 0; capital mutations 0; execution-authority mutations 0; recurring cost $0
- Book 5 not begun; Atlas Program Block 4 not begun

---

## R40 SUPERSEDING SECTION — ATOMIC TRANSITION SELECTION + CRASH-SAFE CROSS-STORE COMMIT (B4-CXR7U9R40)

**Status:** PENDING_OPERATOR_REVIEW (append-only supersession; all R39 and earlier sections above remain historical truth, not rewritten).

**Start SHA (authorized):** `c6844d4ca1b2d5f78501c81caf29b251275df42e` (R39 evidence head).
**Implementation head:** `bc6f2e84d1d7426ffd9368b04a8d7081bf72ec0a` (B4-CXR7U9R40R4).
**origin/main:** `7c7816f382947bbc8a1f2154435fc436f2428fa8` (untouched).
**PR #4:** OPEN, unmerged, base `main` ← head `oce-program-build`; mergeable=true, mergeStateStatus=UNSTABLE (SonarCloud failure + Kilo external failure keep it unstable; mergeable is NOT reported as "all required checks passed").

### Commit chain (append-only, no amend/squash/rebase/force-push)

```
febafe4f  B4-CXR7U9R40R1  make recovery transition selection operation-wide and atomic
80959860  B4-CXR7U9R40R2  make the cross-store commit boundary crash coherent
bc6f2e84  B4-CXR7U9R40R4  prove transition, commit-boundary and evidence invariants adversarially
```

R40-03 (immutable transaction-rollback-receipt registration) landed inside
`B4-CXR7U9R40R2`'s restore.sh changes: `register_op` now indexes
`transaction-rollback-receipt.json` with hash and size exactly like every
other registered receipt, so the visible chain has three R40 commits. This is
stated here rather than rewritten into history.

### R40-01 — operation-wide atomic transition claim

Before: finalize and rollback claimed DIFFERENT files
(`<op>.finalize.claim` vs `<op>.rollback.claim`); two processes could both win
O_EXCL and concurrently mutate one recovery operation (reproduced against the
published R39 code). After: ONE operation-wide claim file; the durable state
check and the exclusive claim acquisition are one inseparable CAS boundary;
the selected transition is durably recorded in the claim; the state ladder
rejects any regression from FINALIZING/ROLLING_BACK to PROMOTED; a losing
transition fails before any Docker/PostgreSQL/catalog/receipt mutation.

Proofs (`test_b4_cxr7u9r40r1_operation_wide_claim.py`,
`test_b4_cxr7u9r40r1_claim_race_inprocess.py`): real OS-level O_EXCL races
from separately loaded engine modules contending through real threads —
finalize-vs-rollback, finalize-vs-finalize, rollback-vs-rollback: exactly one
winner each; the loser performs zero docker calls, zero catalog calls, zero
receipt writes, zero durable-state rewrites; interruption after claim leaves
the opposite transition without fresh authority; restart shows the durable
selected transition and cannot replace it.

### R40-02 — durable cross-store commit boundary

PostgreSQL's irreversible point (quarantine drop) is now durably recorded in
the transition record (`commit_point`), written by load-bearing code in the
engine, not by a volatile shell flag. restore.sh's EXIT trap consults the
durable record (`durable_precommit`) before deciding whether artifact
rollback is legal; `PG_FINALIZED`/`COMMITTED` are no longer commit authority.
Post-commit failures are never reported as `FAILED` (which would mislabel
committed data); ambiguous restarts go through the new fail-closed
`pg-recovery.py reconcile` phase, which inspects the durable transition state,
quarantine presence and canonical truth and records the committed result
without guessing. `_record_transition` was fixed to MERGE into the durable
record instead of rebuilding it (it previously wiped durable keys such as
`commit_point` and `rollback_floor`).

Proofs (`test_b4_cxr7u9r40r2_commit_boundary.py`): pre-commit failure → both
stores restored; post-commit-point failure → artifact rollback refused with
both stores left on the promoted snapshot; reconcile refuse/guess states.

### R40-03 — immutable transaction rollback evidence

`register_op` indexes `transaction-rollback-receipt.json` into
`operations/<operation-id>/` with its hash and size, bound to the same
operation/run/commit/tree; registration is idempotent and append-only, so a
later recovery cannot replace it; index-vs-receipt mismatch is detected by
`recovery-ops verify`.

### R40-04 — negative controls

`test_b4_cxr7u9r40r4_negative_controls.py` proves the tests FAIL when the
protections are removed: different claim filenames re-admit the both-win race;
state-check-before-claim re-admits the separable race; EXIT-trap rollback
ignoring the durable commit state restores artifacts post-commit;
PG_FINALIZED-only authority restores artifacts after the irreversible point;
removing the transaction receipt from registration loses the evidence.

### Fresh CI truth (exact implementation head `bc6f2e84`, all five validation workflows)

```
35911572906  b1-local-ground-validation  success
35911572914  b2-control-plane-validation success
35911572985  b3-worker-fabric-validation success
35911572944  b4-config-spine-validation success
35911578831  B1-I1R Validation           success (pull_request; ran against the real merge ref)
```

Earlier R40 runs on intermediate heads (e.g. 35911567455 b3 cancelled on
push-supersede) are historical; the runs above are the exact-head authority.
SonarCloud Code Analysis: **failure** (unchanged gate; D Security / C
Reliability findings not suppressed, not excluded, no NOSONAR added, no
thresholds modified). Kilo Code Review: **external failure** (workspace-setup;
not called green). PR #4 mergeable=true but mergeStateStatus=UNSTABLE.

### R40 exit-gate truth

1. finalize and rollback cannot both claim one operation (operation-wide atomic claim, real-process proof)
2. transition winner chosen by one durable, operation-wide, atomic authority change
3. failure/int interruption cannot produce cross-store old/new divergence (durable commit boundary, container-backed suite green)
4. PostgreSQL's irreversible commit point durably observable and controls artifact rollback legality
5. post-commit evidence failure does not roll back only one store
6. crash/restart reconciliation does not guess (fail-closed `reconcile` phase)
7. transaction-level rollback evidence immutably indexed
8. documentation distinguishes implementation-head (`bc6f2e84`), evidence-head (this commit), and external-check truth (Sonar fail, Kilo fail)

cloud mutations 0; broker mutations 0; capital mutations 0; execution-authority
mutations 0; recurring cost $0. Book 5 not begun; Atlas Program Block 4 not
begun; PR #4 not merged; main untouched.

---

## R41 TRUTH-CORRECTION SECTION — AUTHORITATIVE R40 EXECUTION + CI REPAIR (B4-CXR7U9R41)

**Status:** `IN_PROGRESS / EXTERNAL-CI-BLOCKED` (append-only; R40 and all earlier sections remain historical truth and are not rewritten).

**Authorized start SHA:** `23ba4baa6b2f32df6d4dc4d2d1b69d49ac0920cc` (R40 evidence head).
**R41 implementation head:** `057d25dd78dbafdde462dbcee681b6d62a474791` (`B4-CXR7U9R41X`).
**origin/main:** `7c7816f382947bbc8a1f2154435fc436f2428fa8` (untouched).
**PR #4:** OPEN, unmerged, base `main` ← head `oce-program-build`; `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`. Mergeable is not reported as all required checks passing.

### R41 append-only commit chain

```
1e22ed01  B4-CXR7U9R41R1  execute the repaired R40 proofs in authoritative CI
18db4c66  B4-CXR7U9R41X  name the winning transition in the claim refusal truthfully
fabb135c  B4-CXR7U9R41X  count only engine-minted receipts in the loser-mutation proof
057d25dd  B4-CXR7U9R41X  make the non-atomic claim negative control deterministic
```

The R41 repair is intentionally narrow. It wires the five repaired R40/R41
proof files into the single existing local-ground pytest invocation, keeps the
real process races on the governed filesystem and O_EXCL, repairs the
multi-process test harness, and makes the non-atomic negative control prove its
double-win deterministically. The weakened control forces both callers past
the existence check, neutralizes only the subsequent record rewrite, and then
observes two successful claims. It no longer skips when scheduling happens to
serialize the race.

### R41 local proof results

At the R41 implementation head, the focused selection produced:

```
37 passed, 1 skipped in 7.77s
Ruff: clean on all changed Python files
```

The one skip is the truthful container-gated loser-mutation test in the local
Windows environment; the three real-process race tests execute without Docker
and are included in the authoritative runner selection. The complete
local-ground runner selection is now explicitly named in
`infrastructure/local-ground/scripts/run-validation.sh`; no second pytest
invocation or new workflow was introduced.

### R41 exact-head CI truth

The implementation head `057d25dd` produced these exact-head validation runs:

```
36008618657  b3-worker-fabric-validation  success
36008618689  b2-control-plane-validation  success
36008618870  b4-config-spine-validation  success
36008626072  B1-I1R Validation            success
36008618864  b1-local-ground-validation  failure (Docker registry unauthorized)
```

The `b1-local-ground-validation` failure is an external runner/container
startup failure before the acceptance proofs: Docker reported
`Error response from daemon: unauthorized: access to the requested resource is
not authorized` while pulling the existing compose services. The run reported
`3 failed, 283 passed, 28 errors`; the errors are the container-backed tests
whose shared `local up` could not authenticate to the registry. This is not
reported as a source failure and was not hidden by changing the selection.

The failed workflow was rerun through GitHub's sanctioned
`gh run rerun --failed` path (run `36008618864`, attempt 2). It reproduced the
same Docker registry `unauthorized` startup failure. No source change was made
to appease the unavailable registry.

### R41 external-check truth

- SonarCloud Code Analysis: **failure**, unchanged and unsuppressed; no NOSONAR,
  exclusions, severity changes, or threshold weakening.
- Kilo Code Review: **pending** in the current live PR check view; it is not
  called green.
- PR #4 remains OPEN, unmerged, and `UNSTABLE`; it was not merged.
- `main` remains at `7c7816f3`; main was not modified or pushed.
- cloud mutations = 0; broker mutations = 0; capital mutations = 0;
  execution-authority mutations = 0; recurring cost = $0.
- Book 5 and Atlas Program Block 4 were not begun.

### R41 exit-gate status

The R41 source and proof-repair requirements are implemented and locally
validated. R41 cannot be marked closed until the authoritative local-ground
workflow completes with the container stack available, and the external
Sonar/Kilo dispositions are resolved. No self-ratification is claimed.
