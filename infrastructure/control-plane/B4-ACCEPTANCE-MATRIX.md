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
