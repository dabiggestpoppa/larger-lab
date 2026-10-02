# OCE Book 4 — Configuration & Security Control Spine
## Acceptance Matrix

Status: `IN_PROGRESS` · Branch `oce-program-build` · Start SHA `acddeb696e6b5df1828fc7baf8c7bfbd2eb43e90`

### Planning interpretation (recorded, no material conflict)
There is no literal "Book 4" file in the planning history. The governing/ratified
planning material is the **OCE Constitution (Block 00)** and the **Block 03
Constitutional Spine dossier**, with this mission's prompt as the concrete Book 4
spec. Book 4 is the next **implementation book** after the closed Book 3 Worker
Fabric on `oce-program-build` — it is **not** Program Block 4 (PO Governed
Builder). Field names and precedence below are derived from the mission inventory
(A–J) and the frozen Book 2/3 contracts; no competing standard is invented.

### Acceptance surfaces

| # | Requirement (mission) | Implementation surface | Test | Evidence |
|---|----------------------|------------------------|------|----------|
| A | Canonical settings ownership | `config_spine.py` registry/schema | `test_b4_config_spine` (registry/validation) | `b4-config-registry-results.json` |
| B | Deterministic resolution / precedence | `resolve()` layered precedence | `test_b4_config_spine` (precedence) | `b4-precedence-results.json` |
| C | Startup validation — fail closed | `validate_effective()` | `test_b4_config_spine` (startup rejection) | `b4-startup-failclosed-results.json` |
| D | Secret reference model | `secret ref + resolve/rotate/revoke` | `test_b4_config_spine` (secret lifecycle) | `b4-secret-reference-results.json` |
| E | Redaction / leakage defense | `redact()` over logs/exceptions/evidence | `test_b4_config_spine` + leak scan | `b4-redaction-results.json`, `b4-secret-leak-scan-results.json` |
| F | Authorization boundaries / overrides | operator override audit | `test_b4_config_spine` (override audit) | `b4-authorization-results.json` |
| G | Network / firewall posture | public-listen / egress deny | `test_b4_config_spine` (network denial) | `b4-network-posture-results.json` |
| H | Live-order / execution denial | mode/market gates, deny path | `test_b4_config_spine` (live-order denial) | `b4-live-order-denial-results.json` |
| I | Billable cloud gates | cloud/burst/provision deny | `test_b4_config_spine` (cloud denial) | `b4-cloud-gate-results.json` |
| J | Config drift / effective state | deterministic fingerprint | `test_b4_config_spine` (fingerprint) | `b4-drift-fingerprint-results.json` |
| M | Adversarial matrix | see test module cases | `test_b4_config_spine` (adversarial) | `b4-adversarial-results.json` |
| R | Book 2/3 regression | shared runner full suite | container CI + local | `unit/pg/...` category artifacts |

### Milestones (ordered commits)
- B4-R1: settings registry + ownership + fail-closed startup validation
- B4-R2: deterministic precedence/resolution + drift fingerprint
- B4-R3: secret reference model + redaction + leak scan + rotation/revocation
- B4-R4: authorization boundaries + operator-override audit
- B4-R5: network posture + live-order denial + billable cloud gates
- B4-R6: adversarial matrix + regression wiring + dedicated CI
- B4-R7: authoritative execution, evidence archive, evidence-only commit

---

## ACTUAL IMPLEMENTATION LEDGER / SUPERSEDING MILESTONE STATUS (B4-R3R7)

*The section above preserves the original planning sequence as historical
intent. It does NOT describe what shipped. The ledger below is the truth;
never infer completed scope from commit labels alone.*

### Superseding implementation history

| Planned milestone | Actual commit | Actual scope | Remaining scope | Reason for deviation | Evidence status |
|---|---|---|---|---|---|
| R1 registry/startup | `d793f36b` B4-R1 | canonical settings registry + ownership + fail-closed resolution | — | planning intent | superseded by R3R repairs |
| R2 precedence/fingerprint | `14da06f8` B4-R2 | surfaces A-J spine tests (95) | — | planning intent | superseded by R3R repairs |
| R3 secret lifecycle | `a58671b4` B4-R3 | startup gate hooked into ControlPlane/lifecycle/doctor | — | startup gate took priority | superseded (fabricated-ref defect) |
| (unplanned) B4-R4 | `4624ec38` B4-R4 | config-spine CI category + dedicated workflow | — | completed before B4-R3R mission arrived | active (provisional) |
| R3R1 provenance + namespace | `488f1699` B4-R3R1 | env!=file provenance; governed OCE_* namespace; input inventory | — | independent review of B4-R3 | active |
| R3R2 runtime convergence | `fdcbf34b` B4-R3R2 | host/port + scheduler interval from effective config; every entrypoint gated | — | split-brain repair | active |
| R3R3 secret storage | `f9b85f5d` B4-R3R3 | RuntimeSecretBackend; config-vs-runtime start split; unbacked refs fail closed | — | fabricated-ref removal | active |
| R3R4 DB binding | `518c4e01` B4-R3R4 | governed DSN derivation; POSTGRES_DSN bypass denied | — | secret-boundary convergence | active |
| R3R5 fingerprints | `dde36795` B4-R3R5 | config-identity + security-state fingerprints | — | blind-fingerprint defect | active |
| R3R6 redaction | `9eb926eb` B4-R3R6 | cand-error no-echo validation; canonical redaction primitive | — | error-path leakage defect | active |
| R3R7 ledger | (this commit) B4-R3R7 | acceptance matrix / implementation ledger | — | Defect R-10 | active |
| R4 authorization/override audit | covered in code + suite since B4-R2 | `ConfigAuthorization` boundary; operator_override audit tests exist in `test_b4_config_spine` (surface F) | not yet isolated as a dedicated closure milestone / evidence artifact | original milestone ordering folded into B4-R2 spine suite | partially (tests green; milestone-level evidence artifact pending) |
| R5 network/live/cloud gates | not started as isolated milestone | — | deny surfaces implemented inside spine `validate_effective` + R3R2 runtime gate; dedicated gate milestone outstanding | folded into earlier milestones | open |
| R6 adversarial/regression + CI | partially | — | dedicated B4 workflow pushed; full adversarial matrix + authoritative CI run pending | workflow landed in B4-R4 | open |
| R7 authoritative evidence | not started | — | authoritative run, artifact archive, evidence-only commit | — | open |

### Superseding milestone status

- **Book 4 status:** `IN_PROGRESS / CLOSURE_REPAIR` (post-B4-R3R sequence)
- **B4-R1..R4 commits:** preserved exactly as historical evidence; scope claims
  above reflect what they actually contain, not what the old milestone names
  suggested.
- **Known open items before book close:**
  1. R6-op: full adversarial matrix execution under the dedicated B4 workflow
     (currently only provisional workflow + registry wiring exist; the R3R
     adversarial proofs live in the local B4 suite classes TestR3R*).
  2. R7-op: authoritative CI evidence, artifact download + hashing, provenance
     record, evidence-only commit.
  3. Secret-leak scan over src/tests/scripts for the B4 canary + any committed
     fixture material.
  4. Registry regeneration from actual collection (new B4 test classes added
     across the R3R sequence) before the authoritative CI run.
  5. Final acceptance re-check: source cleanliness, cleanup evidence, cloud
     mutations=0, cost=$0, main=7e7ef722 untouched.

---

## SUPERSEDING LEDGER — B4-CXR3 / B4-R3R8 (authority-escape repair closure)

*Independent review of the B4-R3R closure found the suite green but still
untrue to the core invariants: a runtime input could modify the authority
that validates it (secret self-legitimation), and passing the gate did not
prove the process used that same authorized configuration. The CXR3 repair
sequence below closes those escape paths. Book 4 is closed after this
sequence; see `B4-EVIDENCE-RECORD.md`.*

| Repair | Commit | Scope | CXR3 defect | Evidence |
|---|---|---|---|---|
| B4-CXR3R1 | `0e44617c` | secret init vs runtime read authority (`initialize_runtime_secret` / `read_runtime_secret` / `derive_runtime_dsn`; no ambient self-legitimation; compose env read-only) | CXR3-01 | lifecycle + spine tests, store-snapshot invariance |
| B4-CXR3R2 | `c17b7142` | remove runtime DSN injection (worker `--dsn` removed; `build_durable_app` no DSN override; `migrate()` no DSN param; `migrate.py --db` required + loopback-guarded) | CXR3-02 | startup-gate subprocess proofs |
| B4-CXR3R3 | `1cb9a8d7` | outbound worker CP target canonicalized (`outbound_cp_url` gate-first + verified assertion); `postgres.host` loopback-only enum | CXR3-03 / CXR3-04 | worker-target + DB-host adversarial proofs |
| B4-CXR3R4 | `c508212c` | ownership enforced in the real resolver: policy/operator(po) settings reject non-default sources | CXR3-05 | full weakening matrix (env/file/cli) |
| B4-CXR3R5 | `8ff074cd` | capital authority locked to `none` (validate_effective + override guard) | CXR3-06 | capital lock proofs incl. PO |
| B4-CXR3R6 | `888a6adc` | override-audit truth label (in-process audit NON-AUTHORITATIVE; append-only durable sink seam) | CXR3-07 | audit-truth proofs |
| B4-CXR3R7 | `07314b43` | unified startup truth (`validate_configuration` vs `validate_runtime_readiness` vs `require_runtime_startable`; doctor readiness) | CXR3-08 | no start=True+secret_ok=False; doctor proofs |
| B4-CXR3R8 | `780f7ceb` | config-input inventory refresh (VERIFIED_COMPATIBILITY_ASSERTION / INIT_ONLY / DEPRECATED_AND_REJECTED dispositions); doctor custom/revoked ref; aggregate denial side-effect invariance; registry regenerated to 510 | CXR3-09 / CXR3-10 | inventory doc + adversarial closure |

### Authoritative closure (B4-CXR3, verified from junit + gate + artifact)

- **Run:** `33505225957` on `780f7ceb` — `b4-config-spine-validation` **success**
- **OCE_RUN_ID:** `c4ca8bfc70cb`; **artifact:** `b4-config-spine-evidence-c4ca8bfc70cb` (id `9799398331`)
- **JUnit:** 510 collected / 510 executed / 510 passed / 0 failed / 0 errors / 0 skipped
- **Independent gate:** PASS (137 checks); **final package verifier:** PASS
- **Manifest:** 33/33 entries hash+size verified; **outer ZIP SHA-256:** `dcf290aab6485e34aad3a30b4f4b93f5d54fe5ab330b80602f3ab25e394a9daa`
- **Source clean before + after; cleanup removed=True (PG volume preserved); cloud mutations 0; cost $0**
- **Archive:** `~/Desktop/oce-b4-archive/run-33505225957/`

### Previously superseded (preserved, not closure proof)

- Run `33461183563` / `27a21c9a` (B4-CXR2 head) — prior green run, superseded
  by the CXR3 sequence.
- Runs `33460848791`..`33504839138` — intermediate CXR3 commits failed the
  exact-count gate until the registry was regenerated at B4-CXR3R8; each
  preserved as truthful historical evidence.

---

## SUPERSEDING LEDGER — B4-CXR4 (post-closure authority-escape repair)

*Independent POST-CLOSURE review of the CXR3 closure found remaining runtime
paths the registered suite did not exercise: an existing secret store could
still be overwritten by an ambient password, custom secret references could
split compose/migration/API truth, the runtime re-read the environment
instead of consuming one pinned activation, recover/migrate could mutate
before the gate, migration targets were not bound to the exact governed
identity, override durability was duck-typed, and config-valid wording
overstated runtime readiness. The CXR4 sequence below closes each path.
The CXR3 closure (`33505225957` / `780f7ceb`) remains valid historical
evidence for what its suite tested — it is SUPERSEDED by CXR4, never
rewritten.*

| Repair | Commit | Scope | CXR4 defect | Evidence |
|---|---|---|---|---|
| B4-CXR4R1 | `1cc2b3fa` | one-time secret initialization; startup/restart/configure READ-ONLY over an existing store; atomic writes; explicit rotation path | CXR4-01 | store byte-invariance A/B/C/D/E, init F, rotation G, partial-write H |
| B4-CXR4R2 | `27a3e7a4` | secret reference future-locked to `secret:runtime-local` at config validation — one secret authority, resolvable custom refs blocked | CXR4-02 | future-lock proofs incl. resolvable ref; fingerprint identity observability |
| B4-CXR4R3 | `1b7cc82f` | immutable `ActivationContext` — snapshot env once, pin config + secret metadata, every durable consumer (bind/scheduler/DSN/worker URL/migrations/lifecycle) consumes it; stale context on rotation/revocation | CXR4-03 | env-mutation invariance, rotation/revocation stale proofs, deterministic context id |
| B4-CXR4R4 | `053ec4e3` | recover/migrate gate FIRST (no compose/migrate/launch before the gate); migration target = EXACT governed identity (host+port+db+user+credential, never echoed); stop stays usable under invalid config | CXR4-04 / CXR4-05 | gate-first zero-mutation proofs, alternate-identity rejection, localhost alias determinism |
| B4-CXR4R5 | `3c03f5f3` | audit durability is a PROVEN property: list/duck-typed sinks never durable; canonical `operator_override_durable` requires PostgresAuditSink (migration 0006 ledger); failed commit fails the override closed | CXR4-06 | truth-label proofs, commit-failure fail-closed, read-back proof |
| B4-CXR4R6 | `53961288` | `validate_configuration` (config_ok) never reports start/ready/startable; messages say "configuration valid"; lifecycle authority matrix doc | CXR4-07 / CXR4-08 | terminology proofs, `B4-LIFECYCLE-AUTHORITY-MATRIX.md` |
| B4-CXR4R7 | `fde3fbd6` | adversarial closure of the CXR4-10 matrix (incl. migrate-denial store invariance) + registry regenerated to 541 | CXR4-10 | store-invariance M, full matrix |

### Authoritative closure (B4-CXR4) — see `B4-EVIDENCE-RECORD.md`

### Previously superseded (preserved, not closure proof)

- The CXR3 closure (run `33505225957` / `780f7ceb`) remains valid historical
evidence of the CXR3 suite and is superseded by the CXR4 sequence above.

---

## SUPERSEDING LEDGER — B4-CXR7U / CXR7U8 (single-principal trust model + closure-proof repair)

*CXR7 was BLOCKED at its gate: the original hostile-child isolation requirement
was impossible under the local-first single-principal architecture. The operator
ACCEPTED that blocker as technically correct and issued the CXR7U disposition:
Book 4 is ONE trusted computing base; `OCE_ACTIVATION_ENVELOPE` is an
authenticated parent-launch handoff with role/audience consistency checking —
NOT an OS isolation boundary. CXR7U1–U7 implemented that model; CXR7U8 (R1–R5,
X1, X2) repaired the proofs so they are literal. Book 4 is closed after this
sequence; see `B4-EVIDENCE-RECORD.md`.*

| Repair | Commit | Scope | Evidence |
|---|---|---|---|
| CXR7-BLOCKED | `35b940cf` | exact non-amplification blocker assessment (137 lines, evidence-record only) | preserved verbatim in `B4-EVIDENCE-RECORD.md` |
| CXR7U1 | `0476cf0d` | canonical single-principal threat model (`B4-THREAT-MODEL.md`) + 12 boundary tests | threat model referenced by inventory/matrices/tests |
| CXR7U2 | `50902d2b` | `ParentActivationContext` vs `VerifiedChildContext` separation; `issue_child_handoff`; vacuous `or True` test replaced | child-type behavioral proofs |
| CXR7U3 | `d3d3cb6f` | trusted-program execution lock (`program_for` allowlist); `BoundedProcessRunner` truthful isolation reporting | trusted-program + truthful-report tests |
| CXR7U4 | `7124c0aa` | atomic fail-closed `consume_handoff_once` ledger | 20 concurrent/replay/corruption tests |
| CXR7U5 | `6db19c11` | canonical audit representation + strengthened `proven()` + container-backed production-sink tests | real PostgreSQL reconciliation |
| CXR7U6 | `0781b93d` | journal-based complete-or-nothing `configure`; truthful `recover()` PID cleanup | failure-injection matrix |
| CXR7U7 | `080c82da` | anti-vacuity AST gate + 8 mutation negative controls | security-test integrity |
| CXR7U8R1 | `471e3e2c` | mutation controls isolated under `tmp_path` (canonical checkout byte-identical) + attributable-failure protocol (JUnit-parsed, 6 negative controls) | `test_b4_cxr7_test_integrity` (43 tests) |
| CXR7U8R2 | `d36efb86` | vacuous paths removed; behavioral proofs on real `start()` / real worker dispatch gate / real seam | production-entrypoint tests |
| CXR7U8R3 | `5cbe0d88` | configure serialized (whole-operation lock) + crash/restart recoverable (durable journal snapshot, roll-forward, real subprocess interruption) | crash/concurrency test module (11) |
| CXR7U8R4 | `20f8404e` | exact PostgreSQL reconciliation (`ON CONFLICT DO NOTHING RETURNING`; durable-ID returns; transaction stays usable) + exact-schema `proven()` (PK column, schema-pinned index/trigger identity) | container-backed U8-05/06 tests |
| CXR7U8R5 | `b56bc75f` | corrupt secret authority fails closed (`SecretStoreCorrupt`/`SecretStoreUnreadable`); byte-invariance across every mutation/read path | corrupt-store byte-invariance matrix |
| CXR7U8X1 | `890e2eee` | CI-exposed repairs from run `33979406177` (4 failed + 34 errors): broken test-helper SQL, unreadable-store configure path, Linux-truthful isolation assertions | failure artifact preserved |
| CXR7U8X2 | `b1f7a078` | CI-exposed repairs from run `33986527406` (5 failed): decoy-index `finally` ordering (DuplicateTable cascade), `authorized` DEFAULT TRUE auto-cast, `_clean_db` residue hardening | failure artifact preserved |

### Authoritative closure (B4-CXR7U, verified from junit + gate + artifact)

- **Run:** `34118435301` on `b1f7a078` — `b4-config-spine-validation` **success**
- **OCE_RUN_ID:** `c4394d247914`; **artifact:** `b4-config-spine-evidence-c4394d247914` (id `10017304559`)
- **JUnit:** 835 collected / 835 executed / 835 passed / 0 failed / 0 errors / 0 skipped; duplicate_ids `[]`
- **Regression on the same head:** `b1-local-ground-validation` success (`34118435295`),
  `b2-control-plane-validation` success (`34118435261`), `b3-worker-fabric-validation` success (`34118435201`)
- **Archive:** `~/Desktop/oce-b4-archive/run-34118435301/` (33 manifest entries, all hashes re-verified)

### Previously superseded (preserved, not closure proof)

- The CXR6 closure (run `33555566041` / `fd5b3274`) remains valid historical
  evidence of its 644-test suite; its model did not cover same-principal-child
  amplification. Superseded by the CXR7U sequence, never rewritten.
- The CXR7 blocker record (`35b940cf`) is preserved verbatim; the operator
  disposition supersedes the impossible hostile-child requirement without
  erasing the finding.
- Intermediate failed runs `33979406177` (U8X1 repairs) and `33986527406`
  (U8X2 repairs) are preserved as truthful historical evidence.

### R39/R40 superseding status (append-only, do not rewrite the sections above)

- **Book 4 status:** `IN_PROGRESS / CLOSURE_REPAIR` — recovery-transaction
  closure through R40; the book is NOT closed and no self-ratification is
  claimed.
- **R39 (B4-CXR7U9R39):** main doctrine reconciled (`87792340`), cross-store
  rollback-coherent full replacement, governed collision-safe receipt
  persistence, durable single-use transition authority, adversarial/container
  proofs, four R39X CI-exposure repairs. Implementation head `4f362b7d` and
  evidence head `c6844d4c` both carried five green validation workflows (exact
  IDs in B4-EVIDENCE-RECORD.md's R39 section).
- **R40 (B4-CXR7U9R40):** atomic operation-wide transition selection
  (`febafe4f`), crash-coherent irreversible commit boundary + immutable
  transaction-rollback-receipt registration (`80959860`), adversarial
  transition/commit-boundary/evidence invariants and negative controls
  (`bc6f2e84`). Concurrency proofs use real OS-level O_EXCL races from
  separately loaded engine modules; commit-boundary proofs inject failure
  before/after the durable commit point; negative controls prove the suites
  fail when each protection is removed.
- **CI truth (exact R40 implementation head `bc6f2e84`):** all five validation
  workflows success — b1-local-ground 35911572906, b2-control-plane
  35911572914, b3-worker-fabric 35911572985, b4-config-spine 35911572944,
  B1-I1R 35911578831 (pull_request against the real merge ref). SonarCloud =
  failure (gate unchanged, not suppressed); Kilo = external workspace-setup
  failure (not called green). PR #4: mergeable=true, mergeStateStatus=UNSTABLE
  — mergeable is NOT "all required checks passed".
- **R7-op status:** satisfied in substance — authoritative exact-head runs,
  artifact verification, and the superseding evidence record now exist through
  R40; the final R40-EVIDENCE documentation commit carries this section.
- **Still open before book close:** operator acceptance of R39/R40; SonarCloud
  credential/operator disposition; Kilo external service recovery.

### R41 truth correction (append-only)

- **R41 (B4-CXR7U9R41):** the R40 proof files are now selected by the single
  authoritative local-ground pytest invocation. The real-process claim races
  execute without Docker; the container-backed loser proof remains truthfully
  container-marked. The non-atomic negative control now uses a deterministic
  barrier and proves a double-win rather than skipping.
- **R41 implementation head:** `057d25dd`; focused local result `37 passed,
  1 skipped`; Ruff clean. The skip is the local Windows container gate, not a
  hidden CI skip.
- **Exact-head validation runs:** `36008618657` b3 success,
  `36008618689` b2 success, `36008618870` b4 success, `36008626072`
  B1-I1R success. `36008618864` b1-local-ground is blocked before the
  container proofs by Docker registry `unauthorized`; its sanctioned rerun
  reproduced the same external startup failure. It is not called green.
- **External checks:** SonarCloud remains failure/unsuppressed; Kilo is pending
  in the live PR view and is not called green. PR #4 remains OPEN,
  `MERGEABLE`, `UNSTABLE`, and NOT MERGE AUTHORIZED.
- **R41 status:** `IN_PROGRESS / EXTERNAL-CI-BLOCKED`. No cloud, broker,
  capital, or execution authority was introduced; recurring cost is $0. Book 5
  and Atlas Program Block 4 remain untouched.

### R41R2 crash-coherence repair (append-only)

| Repair | Commit | Scope | Evidence |
|---|---|---|---|
| B4-CXR7U9R41R2 | `6afb849a` | fsynced forward-commit intent before quarantine drop; explicit ladder; receipt/record/claim/identity/intent-bound `resume-finalize`; engine-owned fail-closed rollback law | focused engine + shell proofs |
| B4-CXR7U9R41R3 | `9f47e541` | eight real-process crash/restart cases, five resume-binding refusals, three executable negative controls; wired into the existing single pytest invocation | 16-test crash-coherence module; 335 collected; 8 exact crash IDs; 0 duplicate crash IDs |
| B4-CXR7U9R41R3X | `af69345d` | Linux CI repair: exec the sleeping crash-boundary process so kill does not wait on a descendant-held pipe | exact-head rerun; all R41R2 proofs passed |

**Implementation head:** `af69345daaf37b52bbf6fa1a4c60b28b9140ed02`.

**Exact-head validation runs:**

- `36034493154` b2-control-plane-validation — success
- `36034493249` b3-worker-fabric-validation — success
- `36034493173` b4-config-spine-validation — success
- `36034499330` B1-I1R Validation — success
- `36034493288` b1-local-ground-validation — failure on attempt 1 and
  sanctioned failed-job rerun attempt 2; both report Docker registry
  `unauthorized` for the existing `artifact-store` image, with
  `3 failed, 304 passed, 28 errors`. The R41R2 module itself passed.

**Exit-gate truth:** implementation and executable proofs are complete, but
status remains `IN_PROGRESS / EXTERNAL-CI-BLOCKED`. SonarCloud is failure and
unsuppressed; Kilo is queued; PR #4 is OPEN, unmerged, MERGEABLE, and UNSTABLE.
No cloud, broker, capital, or execution-authority mutation occurred; recurring
cost is $0. Book 5 and Atlas Program Block 4 remain untouched.

### R41R4 completion repair (append-only)

| Repair | Commit | Scope | Evidence |
|---|---|---|---|
| B4-CXR7U9R41R4 | `bb098bec` | governed operation-scoped `preintent-rollback`, exact admission/identity/digest binding, old/old convergence, truthful terminal receipt, and finalize/abort serialization | 13 R41R4 node IDs in the single authoritative local-ground invocation |
| B4-CXR7U9R41R4-S | `76d88c4a` | replace the inaccessible registry image with an exact local build from official pinned MinIO source | release `RELEASE.2024-05-28T17-19-04Z`, peeled `f79a4ef4d0dc3e6562cad0d1d1db674bc8c75531`, source SHA-256 `558275de8aaf5fa04cca55cfd712ea76886e34b47458a591e2754b3caeaab2c3` |
| B4-CXR7U9R41R4-X1..X9 | `6698f825`..`bba377a8` | immutable source/base authority, executable build evidence, canonical S3 signing, native curl SigV4, and container stdin preservation | source-built image health, bucket/object PUT, exact-body GET, and restart persistence passed |

**R41 implementation head:** `bba377a857c5747f320e56fec5d41ac60f597f4a`.
**Implementation tree:** `28fb0952c76cd001cba16169046a661b61e26ec4`.
**OCE_RUN_ID:** `4b9980d9c97d`.

**Exact implementation-head validation:** all five workflows succeeded: b1
`36059471143`, b2 `36059471084`, b3 `36059471054`, b4 `36059471058`, and B1-I1R
`36059477563`. B1 reports 348 collected / 348 executed / 348 passed, 0 failures,
0 errors, 0 skips, 27/27 container-backed tests passed, and independent gate
75 PASS / 0 FAIL over 37 manifested artifacts. Source was clean before/after and
container cleanup removed all disposable containers, networks, and volumes.

**Truth correction:** R41R2 crash cases 01/02 established classification and
reconciliation only, not executable old/old rollback after a spent finalize
claim. The prior Quay `unauthorized` diagnosis as a merely external runner issue
is superseded: the registry reference itself was not viable. R41R4 builds the
exact official source locally and removes that dependency without publication or
new credentials.

**Exit-gate truth:** `READY_FOR_OPERATOR_REVIEW`; no self-ratification or merge.
SonarCloud is failure/unsuppressed; Kilo was in progress and is not called green.
PR #4 is OPEN, unmerged, and UNSTABLE. `main` remains `7c7816f3`. Cloud, broker,
capital, and execution-authority mutations are 0; recurring cost is $0; Book 5
and Atlas Program Block 4 remain untouched.

### B4-CXR7U9R42 superseding repair (append-only)

`R41R4: SUPERSEDED BY B4-CXR7U9R42 POST-REVIEW REPAIR`. The prior exact-head
R41R4 green workflows remain real and valid for the tests they executed; the
coverage boundary was incomplete, not fabricated.

| Repair | Commit | Acceptance proof | Exact-head evidence |
|---|---|---|---|
| B4-CXR7U9R42R1 | `78b68ae6` | no finalize/resume/rollback mutation-capable body is reachable from an unlocked exception path; full authorization and branch consumption occur inside OS execution authority; denied binding restores zero durable metadata | focused R39/R40/R41 recovery suites pass |
| B4-CXR7U9R42R2 | `d86b3e82` | deterministic real-process invalid-to-valid proof; fresh/resume/ordinary/pre-intent contention; malformed/digest/unregistered receipt zero-effect snapshots; executable weakened-engine control observes unlocked mutation | 8/8 R42 node IDs selected in authoritative runner |
| B4-CXR7U9R42R3 | `4720a27e` | authenticated exact-byte S3 GET after service restart plus unchanged image release/revision/ID and `/data` volume identity; disappearance/body/volume/image negative controls | container-backed source-built MinIO proof passes |
| B4-CXR7U9R42X1 | `698462ac` | malformed receipt is truthfully classified at minimal execution binding while preserving the historical no-call/no-mutation assertion | exact implementation head green |

**Implementation head:** `698462ac6588cdbfb11f0e9c67b03b6e67db01f3`.
**Implementation tree:** `07073a8f28b34dd6a2618d4d93c436266349a762`.
**Exact-head workflows:** b1 `36075925792`, b2 `36075925798`, b3 `36075925728`,
b4 `36075925780`, and B1-I1R `36075929965` — all success.

**Artifact truth:** `b1-local-ground-evidence-9bb6ee8e858e`, OCE_RUN_ID
`9bb6ee8e858e`, reports 360/360 executed and passed, zero failures/errors/skips,
27/27 container-backed tests, all eight R42 race IDs, the executable negative
control, authenticated post-restart S3 GET, independent gate 75 PASS / 0 FAIL,
37 manifest entries with hashes/sizes reverified, source clean before/after,
verified cleanup, and read-only final-package verifier PASS.

**Superseded boundaries closed:** unlocked invalid-to-valid recovery re-entry
and the absence of a post-restart authenticated S3 object retrieval proof.
Prior R41/R41R2/R41R4 sections remain preserved verbatim above.

**Current authorization boundary:** SonarCloud remains failure/unsuppressed;
Kilo is recorded by fresh external result after the evidence head. PR #4 stays
OPEN, unmerged, MERGEABLE, and UNSTABLE. `main` remains `7c7816f3`. No cloud,
broker, capital, or execution-authority mutation occurred; recurring cost is $0.
Book 5 and Atlas Program Block 4 remain untouched.

### B4-CXR7U9R44 superseding repair (append-only)

`R43: SUPERSEDED BY B4-CXR7U9R44 POST-REVIEW REPAIR` (and R42 likewise). The
prior exact-head R42/R43 green workflows remain real and valid for the tests
they executed; the coverage boundary was incomplete, not fabricated.
Correction of the prior boundary statement: **R43 CLOSED THE KNOWN LOCK-ABA
AND ROLLBACK-RESUME DEFECTS, BUT DID NOT TEST CRASHES INSIDE CLAIM
PUBLICATION OR DENIAL-SIDE-EFFECT-FREE COORDINATE PROVISIONING.**

Three post-R43 review findings closed by this repair: (1) the canonical
branch selector became VISIBLE before its payload was durable, so death in
that window left a zero-byte claim that spent the one-time authority and
stranded PROMOTED; (2) entering execution authority created the permanent
lock coordinate BEFORE authorization, so a denial — including an arbitrary
unregistered operation id — left durable growth; (3) a denied fresh retry
could ERASE an earlier committed owner's execution metadata.

| Repair | Commit | Acceptance proof | Exact-head evidence |
|---|---|---|---|
| B4-CXR7U9R44R1 | `74321f5c` | crash-atomic claim publication: durable temporary + atomic NO-REPLACE publication; malformed selector fails closed in reconcile and classifier; negative control retargeted to the pre-R44 primitive | R44 boundary sweep passes on Linux CI |
| B4-CXR7U9R44R2 | `ff6912d4` | lock coordinates provisioned ONLY through governed authority: governed-operation proof (record+format+digest) precedes any coordinate open/create; promotion provisions exactly one; every denial provisions nothing | R44 provisioning + hostile-id growth proofs pass |
| B4-CXR7U9R44R3 | `0aefe40e` | attempt-owned execution metadata v3: selector read under the OS lock; cross-branch and prior-committed-evidence overwrite refused; compare-and-delete with byte-for-byte restore | R44 metadata preservation proofs pass |
| B4-CXR7U9R44R4 | `d3d5ba37` | real-process proofs of all seven publication crash boundaries; executable poison control reproduces the zero-byte claim at runtime | R44 proof module green |
| B4-CXR7U9R44R5 | `a8c6e0b1` | R44 proof module selected in the authoritative runner with unique node IDs | runner selection proof passes |
| B4-CXR7U9R44X1 | `bccc9cc5` | R35 aligned: pre-authority conflict reported as truthful refusal; denial proves byte-identical tree plus exactly the promotion-provisioned coordinate | R35 suite 39 passed / 1 skipped |
| B4-CXR7U9R44X2 | `30370dc5` | liveness-safe discard: OS-lock-proven death (never names/timestamps); live writer's temporary untouchable; bounded retreat from creation and Windows release windows; new real-process proof module selected in the runner | R44X2 module 5/5 on Linux CI; R40R1 race repaired |

Mid-gate truth record: exact-head CI on `bccc9cc5` FAILED (b1 run
`36243225760`, the two-thread claim race produced no winner). Root cause was
a REAL DEFECT introduced by R44R1 — the discard step deleted a LIVE
publisher's in-flight temporary — repaired in R44X2 and recorded as
observed; not dismissed as a flake.

**Implementation head:** `30370dc5116789414eeede41fff7acef90bdff25`.
**Implementation tree:** `43d2c78a5ca0b90b3749779f62fd1fe08f2c1633`.
**Exact-head workflows:** b1 `36248776201`, b2 `36248776161`,
b3 `36248776197`, b4 `36248776169`, and B1-I1R `36248779729` — all success.

**Artifact truth:** `b1-local-ground-evidence-b16c3e20112f`, OCE_RUN_ID
`b16c3e20112f`, reports 417/417 executed and passed on Linux, zero
failures/errors/skips (both platform-gated R44 proofs RAN), 62
container-backed tests passed, all R44 and R44X2 proofs, independent gate
75 PASS / 0 FAIL (AUTHORITATIVE_CI), adversarial 8 PASS / 0 FAIL, 37
manifest entries with sha256 reverified (0 mismatches), source clean
before/after, main `7c7816f3` untouched, cloud_mutations 0,
cloud_cost_state ZERO, cloud_activation_state DEFERRED_BY_OPERATOR.

**Superseded boundaries closed:** crash windows inside claim publication;
denial-side persistent coordinate growth; committed metadata loss on denied
retry; and (found by CI mid-gate, fixed in R44X2) discard interference with
a live publisher's in-flight temporary. Prior sections remain preserved
verbatim above.

**Current authorization boundary:** SonarCloud is FAILURE/unsuppressed on
this head; Kilo has NO CONCLUSION (pending) and is not called green. PR #4
stays OPEN, unmerged, MERGEABLE, and UNSTABLE. `main` remains `7c7816f3`.
No cloud, broker, capital, or execution-authority mutation occurred;
recurring cost is $0. Book 5 and Atlas Program Block 4 remain untouched.

**Exit-gate truth:** `READY_FOR_OPERATOR_REVIEW`.

---

## B4-CXR7U9R45 — SUPERSEDING SECTION (selector binding and final quality-gate truth)

**Gate missions:**
1. One selector classification law: `_selector_agrees_with_finalizing` is the single predicate consumed by the shell FINALIZING branch and phase_reconcile (R45R3: 15-row matrix driving a real CLI child and real reconciliation, cross-surface agreement map, zero-mutation census per row).
2. Receipt binding: classification keys on the exact promote receipt digest via the four-state `_claim_state` law; a digest without expectation is `unbound_or_mismatched` (R45R1).
3. Claim path/type admission: realpath containment in the governed transitions directory, symlink refusal, regular-file-only, POSIX group/other-bit refusal, double-lstat TOCTOU (R45R2; refusal tests executable on Linux).
4. Denied classification has zero durable side effects.
5. The mandatory runner selects every R45 proof module; collected node ids are unique; every skip is a declared platform gate (R45R5 proofs).
6. All mandatory proofs executed in authoritative CI with zero skips: b1 467/467, b2 905/905 (read from its `independent-gate.json`; b3/b4 run the same control-plane suite and their gates PASS), I1R 67/67 + 35/35 + 31/31 plus the adversarial battery green (run IDs below).
7. Sonar findings repaired or individually proven and truthfully blocked on operator disposition — no suppression, exclusion, or severity change (R45R4 inventory in its commit; R45X1 repairs R45R4's own CI-demonstrated defects).
8. Kilo's completed workspace-setup failure is recorded truthfully; Kilo remains FAILURE on the final head.
9. Evidence record and acceptance matrix agree on closure status (both BLOCKED, below).

**Implementation head:** `1a66231234363587cc3d6471bce0c6cbc5718bb8`.
**Exact-head workflows:** b1 `36326811618`, b2 `36326811625`,
b3 `36326811620`, b4 `36326811621`, and B1-I1R `36326813971` — all success.

**Repair chain:** R45X1 (four R45R4 defects: artifact-image heredoc import,
worktree-cleanup printf corruption, `_parse_json` Path/str comparison,
audit exception pins), R45X2 (worktree-create stderr diagnostics),
R45X3 (LFS-smudge skip; GitHub LFS budget exhaustion captured verbatim in
run 36326018898 and preserved — account-level, operator-side).

**Artifact truth:** b1 evidence `b1-local-ground-evidence-2e756cada5d9`,
OCE_RUN_ID `2e756cada5d9`: 467/467 passed on Linux, zero
failures/errors/skips, independent gate PASS, 37 manifest artifacts with
sha256 recorded, source clean before and after, main `7c7816f3` untouched,
cloud_mutations 0, cloud_cost_state ZERO, cloud_activation_state
DEFERRED_BY_OPERATOR. Failed intermediate heads (`dfbfa699` 5/5 failed;
`c2829789` and `2d4e1ff3` I1R worktree failures) are recorded in the
evidence record, not erased. Prior sections remain preserved verbatim
above.

**Current authorization boundary:** SonarCloud FAILURE (D Security /
C Reliability on New Code) unsuppressed on this head; Kilo FAILURE; PR #4
OPEN, MERGEABLE, UNSTABLE, unmerged; `main` at `7c7816f3`; no cloud,
broker, capital, or execution-authority mutation; recurring cost is $0;
Book 5 and Atlas Program Block 4 untouched.

**Exit-gate truth:** `BLOCKED_B4_CXR7U9R45: SonarCloud quality gate FAILURE (D Security / C Reliability on New Code) and Kilo Code Review FAILURE on head 1a662312 — operator-side adjudication required`.
---

## B4-CXR7U9R46 — SUPERSEDING SECTION (FD-bound selector snapshot and final gate truth)

**Gate missions, and how each is discharged:**

1. **No claim is read by validating a pathname and reopening it.** R46R1
   replaced that reader with ONE FD-bound snapshot: no-follow directory and
   coordinate, descriptor admission (regular, private, no foreign durable
   name, no mutation across admission), raw `os.read` from that same
   descriptor, then a device/inode identity proof of the canonical name.
2. **One decision reads the claim once.** R46R2 removed the
   classify-then-re-read shape; classification and branch selection consume the
   same immutable snapshot.
3. **A replacement at any boundary fails closed with zero authority-side
   effects.** R46R5 places replacements at the pre-open stat, after admission,
   after parse, after the identity proof, between classification and branch
   extraction, and between shell classification and phase admission — all
   deterministic (hooks, never sleeps), all denying, none mutating the claim,
   the residue, the record or the catalog.
4. **The refusals are proven non-vacuous.** Two executable weakened controls
   restore the pre-R46 reader and the pre-R46 two-read decision in child
   processes and show them ACCEPTING the deterministic replacement
   (`MIXED` / `ACCEPTED`) while the shipped engine prints `REFUSED` with
   `reads=1`.
5. **The receiptless law binds a receipt, not a branch name.** R46R3 binds it
   to the durable transition record's own `receipt_sha256`; foreign,
   malformed or missing digests fail closed.
6. **The state/selector matrix is corrected.** R46R4: CREATED/STAGED with any
   claim → 4; ROLLED_BACK requires a receipt and the exact rollback selector
   (6, else 4); FAILED is always 4; **FINALIZING without an exact claim → 4**,
   not governed abort.
7. **A crash in the publication window stays resumable.** R46X1 corrected the
   law that Linux CI proved wrong: POSIX `os.link`-then-`os.unlink` leaves a
   durably published claim with two names, and a bare `st_nlink == 1` check
   refused it. The durable-name law now admits the engine's own publisher
   residue, censuses the governed directory descriptor-relative, and refuses
   any other durable name — including one placed outside that directory,
   which cannot hide because the census must account for every `st_nlink`
   name. Six R44 crash-recovery proofs that this had broken pass again.
8. **Denial has zero authority-side effects.** R46X1 proof x6 asserts the
   governed tree, the claim bytes, the publisher residue and any foreign name
   are byte-identical after both an admitted read and a refused one.
9. **Every mandatory proof runs in authoritative Linux CI with zero skips.**
   b1 507 collected / 507 executed / 507 passed / **0 skipped**
   (`mandatory_skipped: 0`), including the POSIX-only crash-residue proofs;
   b2 905/905 with 0 skipped; b3/b4 gates PASS; I1R SUCCESS.
10. **Evidence no longer claims double-lstat is TOCTOU-safe.** The R45 claim is
    corrected in the evidence record, and the R46R5 weakened control makes the
    old reader's acceptance executable rather than merely disputed.
11. **SonarCloud exact-head truth is reported from the live check, with every
    remaining issue in the reported window identified precisely** — 14
    failure-level and 36 warning-level annotations, each named by path:line,
    issue key and rule, together with the explicit caveat that GitHub caps the
    annotation surface at 50 per check run and the window is not a total. The
    gate is FAILURE (C Reliability and D Security on New Code) and is not
    called green anywhere.
12. **Kilo's LFS checkout failure is an exact operator blocker.** The clone
    succeeds; the checkout exits 128 smudging a 626 MB parquet because the
    account LFS budget is exhausted. No repository-controlled non-destructive
    configuration can change a provider-side clone, and de-LFS-ing the object
    is forbidden; the two operator actions are named in the record.

**Implementation head:** `35ad028d0248398a6f2e5934134a041f5a89b018`
(tree `37bc6aa6067a39236bf3db427b7d439ecbc135b0`).
**Exact-head workflows:** b1 `36768503334`, b2 `36768503165`, b3
`36768503180`, b4 `36768503174`, B1-I1R `36768510004` — all success.

**Artifact truth:** b1 evidence `b1-local-ground-evidence-545408ffd8c7`,
OCE_RUN_ID `545408ffd8c7`: 507/507 passed on Linux, zero
failures/errors/skips, 27/27 container-backed, independent gate 75 PASS /
0 FAIL (AUTHORITATIVE_CI), adversarial 8 PASS / 0 FAIL, 37 manifest artifacts
with sha256 recorded, source clean before and after, `cloud_mutations 0`,
`cloud_cost_state ZERO`, `cloud_activation_state DEFERRED_BY_OPERATOR`. b2 gate
PASS (run_id `83626fb4bd5f`): 905/905 passed, 0 skipped, registry expected
total 905. Failed intermediate heads (`0a9157ffa` b1 `36759645882`, and
`8da2ab532` b1 `36763822266`) are recorded in the evidence record, not erased.
Prior sections remain preserved verbatim above.

**Current authorization boundary:** SonarCloud quality gate FAILURE on New
Code, unsuppressed, at this head; Kilo Code Review FAILURE on an exhausted
Git LFS budget; PR #4 OPEN, MERGEABLE, UNSTABLE, unmerged, head `35ad028d`;
`main` at `7c7816f3`; no cloud, broker, capital, or execution-authority
mutation; recurring cost is $0; Book 5 and Atlas Program Block 4 untouched.

**Exit-gate truth:** `READY_FOR_OPERATOR_REVIEW` — internal authoritative CI
is fully green at the evidence head and every review criterion above is
discharged by the implementation, its proofs, or an exactly named external
operator action (SonarCloud adjudication of the New Code ratings and of the
three path-traversal hot spots; restoring or skipping the LFS smudge for
Kilo's checkout; and merge authorization). PR #4 is NOT merged and no merge
authority is claimed or exercised.
**Evidence head:** `b9cc9cc5692a7a707decf3e7d044283f6c1224ac` (documentation
only: no code, test, gate or artifact change). All five workflows SUCCESS at
that exact head — b1 `36770063990`, b2 `36770064008`, b3 `36770064055`, b4
`36770064134`, B1-I1R `36770071461` — with b1 again reporting 507/507 passed,
0 skipped, `mandatory_skipped 0`, independent gate 75 PASS / 0 FAIL, 37
manifest artifacts, `cloud_mutations 0`, `cloud_cost_state ZERO`. SonarCloud at
that head is check run `110074790755`, COMPLETED / FAILURE, same two failed
New Code ratings, and a THIRD distinct 50-annotation window (17 failure-level,
33 warning-level) — which is the clearest available proof that the annotation
surface is a sliding window and never an inventory; the gate is not called
green at any head. Kilo at that head is check run `110073886281`, COMPLETED /
FAILURE, the identical provider-side LFS-budget smudge failure, still an exact
operator blocker. PR #4 is OPEN, MERGEABLE, UNSTABLE, unmerged at that head;
`main` untouched at `7c7816f3`. The exit-gate truth above is unchanged.

## B4-CXR7U9R47 — superseding acceptance truth (one complete authority snapshot; no caller-declared authority root)

**Requirement set (mission §2–§5) → implementation → proof, all at implementation head `6a8ec1158` (tree `f05e057741ad6bf9a0fdb173d6bbe20362ad6fb8`):**

| # | Requirement | Implementation surface | Proof (executed in authoritative Linux CI, 0 skips) |
|---|-------------|------------------------|-----------------------------------------------------|
| 1 | ONE immutable `RecoveryAuthoritySnapshot` per complete decision | `_acquire_recovery_authority` + `RecoveryAuthoritySnapshot` (pg-recovery.py) | `test_b4_cxr7u9r47r1_authority_snapshot.py`: record/selector read counters ≤1/≤1 on every ladder row; mixed-generation replay never performs read 2; weakened two-read control accepts the swapped generation (non-vacuous) |
| 2 | No hidden rereads in any participating helper | `_claim_state`, `_valid_transition_claim`, `_selector_agrees_with_finalizing`, `_receiptless_selector_agrees` consume `authority=` | R1 suite read-counters + the pure-classifier proof (every reader raises; classification still succeeds) |
| 3 | No public caller-declared authority root | `--classify-state`/`--transition-dir` unparsed (exit 2); `_test_classify_state_for_shell` private seam; engine-derived root in `_classify_rollback_for_shell`/`_bound_operation`; restore.sh updated | `test_b4_cxr7u9r47r2_no_caller_authority.py`: attacker record+selector+directory ⇒ 4, world byte-identical; AST surface proof: no classification function takes a directory parameter; zero container/db/receipt mutations on denial |
| 4 | Original coordinate admitted before any resolution | `_derive_claim_coordinate` returns UNRESOLVED; `_open_governed_directory` opens with O_NOFOLLOW (Windows: reparse refusal + no-follow stat) | `test_b4_cxr7u9r47r3_directory_coordinate.py`: collection proof (no realpath/isdir in derive); red-green control — realpath-first R46 form ACCEPTS the symlinked directory, shipped form REFUSES it (executed on Linux CI) |
| 5 | Record/selector generations never mixed | admitted record pinned into the same snapshot as the selector | R1 pin proof: replacement landing mid-decision leaves the verdict from the ADMITTED record; a later decision sees the replacement (4, not 6) |
| 6 | Singular selector implementation | `_classify_claim_content` defined exactly once; shadowed duplicate deleted | `test_b4_cxr7u9r47r4_singular_bounded_selector.py` AST proofs: 1 definition; zero top-level collisions module-wide |
| 7 | Bounded selector input | `_CLAIM_MAX_BYTES = 4096`; pre-read `st_size` check + during-read cumulative check in `_read_admitted_claim` | R4 proofs: oversized refused before any `os.read`; growing refused mid-read (`grew past`); truncated/empty/malformed refused whole; padding-smuggling refused; governed tree byte-identical after every denial; valid selector still accepted |
| 8 | Dedicated R47 tests in the real authoritative runner | `run-validation.sh` defines+selects all four R47 variables | 45 R47 nodes collected, 0 duplicate node IDs, **45 executed in b1 CI JUnit with 0 skips** |
| 9 | Mandatory registry | `b2_registry.py` validates unchanged (905 ids, control-plane only) | b2 run `36918303770` success |
| 10 | Weakened controls genuinely fail | R1 two-read control, R3 realpath-first control | both executed in CI (0 skips), both visibly accept the attack the shipped engine refuses |

**Implementation-head CI (all SUCCESS):** b1 `36918303772` (552/552 passed, 0 failed, 0 errors, **0 skipped**, `mandatory_skipped 0`, 27/27 container-backed, independent gate PASS, adversarial 8/0, 37 manifest artifacts, source clean pre/post, cleanup ok, OCE_RUN_ID `0a517418956f`), b2 `36918303770`, b3 `36918303802`, b4 `36918303763`, B1-I1R `36918308876`. The failed intermediate head `f696132c5` (b1 `36916007080`: two POSIX-gated proof defects invisible on Windows) was repaired by append-only `B4-CXR7U9R47X1` (`6a8ec1158`) and the full workflow set re-ran green — recorded, not erased.

**External truth (fresh, exact-head, not called green):** SonarCloud `110558634247` COMPLETED/**FAILURE** (C Reliability + D Security on New Code; 50-annotation sliding window: 14 failure-level / 36 warning-level; no NOSONAR, exclusions, severity or profile changes). Kilo `110557745711` COMPLETED/**FAILURE** — provider-side clone cannot smudge the 626 MB LFS parquet ("sandbox storage full", exit 128); operator action: restore/increase the LFS quota or set `GIT_LFS_SKIP_SMUDGE=1` in Kilo's checkout. LFS object untouched.

**Local totals (Windows host, disclosed):** focused R39–R47 293 passed / 24 skipped (all Windows-gated; all executed in Linux CI); full split 386c/357p/29s + 135c/118p/16s; the one local failure (`test_backup_hardening::test_incomplete_full_backup_rejected`) is a 60 s subprocess timeout around `backup.sh` (74–80 s on this host), reproduced at start head `53c51741e` in a detached worktree and passing in Linux CI at `6a8ec1158` — pre-existing environment timing, not an R47 regression. `test_local_ground.py` not run locally (Docker stack absent on this host); it runs in b1 CI.

**Authorization boundary:** PR #4 OPEN, MERGEABLE, UNSTABLE, unmerged, head `6a8ec1158`; `main` untouched at `7c7816f382947bbc8a1f2154435fc436f2428fa8`; cloud/broker/capital/execution mutations 0; recurring cost $0; no LFS migration; Book 5 and Atlas Program Block 4 untouched. `MERGE_AUTHORIZED = false` while SonarCloud or Kilo remains non-success.

**Exit-gate truth:** `READY_FOR_OPERATOR_REVIEW` — internal implementation and authoritative CI are complete and green at the implementation head; every internal R47 requirement is discharged by executable proof with zero CI skips; the two external failures are exactly named with their operator actions, and merge authorization is explicitly withheld.
---

# B4-CXR7U9R48 — AUTHORITY COHERENCE REPAIR AND DEEP IMMUTABILITY

**This section supersedes nothing in R47. It records what R47 and R47S
achieved, the two defects R47 left open, and every R48 repair.** R47's
evidence remains valid for the tests R47 actually ran.

## 1. What R47 and R47S legitimately achieved

R47 proved one record read and one selector read per decision, removed
caller-declared authority roots, anchored the coordinate before path
resolution, and made selector parsing singular and bounded. R47S1 closed a
real command-argument-injection channel at the `docker exec` / `docker cp`
operands. R47S2 cleared reliability findings that were real defects. R47S3
repaired the R43 negative control that had silently stopped weakening the
engine, after Linux CI exposed it as a barrier timeout.

R47S implementation-head authoritative workflow runs:
`36946471672` b1, `36946471666` b2, `36946471606` b3, `36946471626` b4,
`36946476467` B1-I1R — all SUCCESS at `cb2f0ed8a0db82568222a894624ea4bc369724b8`.

## 2. The two defects R47 left open

### 2.1 Post-R47 authority-coherence defect (directory generation mixing)

R47 proved a *count* of reads, not their *provenance*. The record was read
through a PATHNAME while the selector was read through the admitted directory
descriptor, so a whole-directory replacement landing between them produced an
ACCEPTED decision combining a PROMOTED record from generation A with a
`finalize` selector from generation B.

Reproduced deterministically before the repair: the weakened R47-shaped
control returns `record_state='PROMOTED'` with `selector='finalize'` and the
mixed verdict is accepted. The shipped engine at `5cc57a02` refuses the same
attack. This discrimination is an executable proof, not an assertion.

### 2.2 Shallow immutability defect

`@dataclass(frozen=True)` stopped attribute rebinding and nothing else. The
nested mappings remained ordinary dicts, so `snapshot.record["state"] =
"FINALIZED"` and `snapshot.selector.claim["transition"] = "finalize"` both
succeeded, and a caller holding the dict it supplied could rewrite decision
material underneath a decision already in progress.

### 2.3 Generalised anchor-scan limitation (R47S3's own proof)

The S3 integrity scan accepted an anchor if it occurred in ANY approved target
text. That is a weaker claim than it appears: an anchor that drifted out of
its intended target but happened to occur somewhere else would have passed.
This was found by simulating the S2 reformat — the first version of the check
had no teeth at all, because hoisting the R43 anchor into a module constant
made it invisible to a scan that only read inline `.replace()` literals.

## 3. Every R48 repair

| SHA | Tree | Subject |
|---|---|---|
| `f9d1ae7f937ddb52b409e2af9ecf5e6ee1d99847` | `d97236fe906a4c839310760d8f289ebb7685b6f1` | R48R1 bind recovery record and selector to one directory fd |
| `bbb58b2ae3007d0fafe0f4c7a8f6d99334b3c422` | `b4f16b76a4147d8c24049f909bd30050771b4056` | R48R2 make recovery authority deeply immutable |
| `116c42bf61b4809ae6c6cfd6fd2a8a127ee0613d` | `d3422f9570bcd362770cc0275bd684695fbc8aa4` | R48R3 prove coherent authority generation and immutability |
| `5cc57a02188c525b865273782fc58dd2515c6f5c` | `38ebdbe1c09cc129e42550d3a0102db8f9c065bc` | R48R4 simplify classification and bind negative controls to targets |

R48R1: one admitted transitions-directory descriptor owns BOTH reads. The
record is opened descriptor-relative with `os.open(name, flags, dir_fd=...)`,
bounded before and during the read, admitted for type, privacy, durable-name
census, inode stability and pathname identity. The directory identity is
rechecked after both reads — descriptor-relative on POSIX, re-identified
without following a redirection on Windows — and any change fails closed.
`_load_transition_record` no longer participates in any authority decision; a
caller-supplied record is a cross-check only.

R48R2: authority material is deeply immutable. Mappings are rebuilt as an
immutable dict refusing `setitem`/`delitem`/`pop`/`popitem`/`update`/
`setdefault`/`clear`/`ior`; sequences become tuples; sets become frozensets.
A dict SUBCLASS is used rather than `MappingProxyType` because the engine's own
decision law is expressed in `isinstance(x, dict)` checks and canonical digests
must stay JSON-serialisable.

R48R3: 33 deterministic proofs, every attack paired with a weakened control.

R48R4: the classifier is one dispatch table over pure per-state handlers.
Writing the proofs found a real defect: an unhashable `state` raised
`TypeError` out of the table lookup instead of failing closed. Six negative
controls were retargeted with their weakened behaviour unchanged.

## 4. Test truth

Full local collection on this Windows host: **591 passed, 48 skipped, 1
failed**. The single failure is `test_backup_hardening.py::
test_incomplete_full_backup_rejected`, a pre-existing host-timing failure
(60 s `subprocess.TimeoutExpired` around `backup.sh --scope state-only`);
it reproduces identically at the authorised start head and passes in Linux CI.

All R4x recovery/recovery-authority suites: **377 passed, 18 skipped**. The 18
skips are declared platform gates; the R48R3 directory-replacement and
deep-immutability proofs execute on every platform, and the three POSIX-only
record attacks execute in Linux CI.

R48 added 72 mandatory nodes (33 in R48R3, 39 in R48R4), all selected by
`run-validation.sh` and all present in the registry with zero duplicate node
IDs.

## 5. External checks — unchanged, and disclosed

- **SonarCloud** check run `110650539392` — **FAILURE** at the R47S
  implementation head. GitHub's annotation feed is a 50-item SAMPLE of the
  open new-code issues; absence from it is not proof an issue is resolved, so
  no repository-wide finding count is claimed here. No NOSONAR, no
  exclusions, no profile or threshold changes were made in R48.
- **Kilo Code Review** check run `110649645875` — **FAILURE**, provider-side,
  during workspace setup and before code review: `sandbox storage full`,
  exit 128, in `git-lfs smudge` on
  `quant-lab/research/crypto_foundry/alt_rotation/data_1/ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet`
  (`Clone succeeded, but checkout failed`). Remedy is operator-side: raise the
  provider's LFS/sandbox storage quota, or set `GIT_LFS_SKIP_SMUDGE=1` in the
  checkout environment. The LFS object is untouched. Kilo is NOT claimed to
  have succeeded on the basis of any local test.

## 6. Accounting

cloud mutations = 0 · broker mutations = 0 · capital mutations = 0 ·
execution mutations = 0 · recurring cost = $0 · capital.authority = none.
origin/main remains `7c7816f382947bbc8a1f2154435fc436f2428fa8`, untouched.

**Status: INTERNAL R48 IMPLEMENTATION COMPLETE. `MERGE_AUTHORIZED = false`
while SonarCloud and Kilo remain non-success.**


# B4-CXR7U9R48X - acceptance correction

This supersedes the R48 acceptance row only; nothing above is rewritten.

The R48 row recorded internal closure on a Windows host whose local totals
(640) did not reconcile with the 671 collected, and whose exact evidence head
was red on Linux. That is corrected here.

| Item | R48 evidence head | R48X implementation head |
|---|---|---|
| head | `a659584ea488e1e2b2d3cfdd8a8ee3896400a00c` | `dce32e66662d2a88f2e47e1ed9016a86febf87f1` |
| b1 run | `36954352454` FAILURE | `37027124632` success |
| JUnit | 671 collected / 10 failed | 679 collected / 679 passed / 0 failed |
| errors | 0 | 0 |
| skipped | 0 | 0 |
| duplicate node IDs | 0 | 0 |
| independent gate | not green | 75 checks, 0 failing |
| b2 / b3 / b4 / B1-I1R | success | success |

Ten Linux failures are accounted for by full node ID: seven legacy
`test_durable_state_controls_rollback_legality` parameterizations (fixture
permission drift, production rule unchanged) and three R48R3 proof defects
(mixed-generation control ordering, descriptor-lifetime observation,
over-strict side-effect expectation). All ten now pass on Linux.

**Status: internal R48X gate satisfied. `MERGE_AUTHORIZED = false`** while
SonarCloud `110650539392` and Kilo `110649645875` remain FAILURE.
