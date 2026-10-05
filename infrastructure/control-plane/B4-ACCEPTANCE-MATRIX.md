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

# B4-CXR7U9R48X2 - external-check truth at the evidence-correction head

This supersedes only the external-check ids quoted in the section above; nothing
above is rewritten. GitHub issues a new external check-run per commit, so the
ids recorded at the R48X implementation head do not describe the head that now
exists.

| Check | Run at `dce32e6666` | Run at `701da835c` | Conclusion at `701da835c` |
|---|---|---|---|
| SonarCloud Code Analysis | `110650539392` | `110912278869` | **FAILURE** |
| Kilo Code Review | `110649645875` | `110910907968` | **FAILURE** |
| b1 | `37027124632` success | `37029019652` success | success |
| b2 | `37027124708` success | `37029018864` success | success |
| b3 | `37027124647` success | `37029019889` success | success |
| b4 | `37027124548` success | `37029019135` success | success |
| B1-I1R | `37027135586` success | `37029030733` success | success |

Neither blocker changed in kind and neither was removed by suppression: no
NOSONAR, no exclusions, no severity downgrade, no profile, gate or threshold
change, no coverage manipulation, no test removal; no repository-wide LFS
migration and the LFS object is untouched. The Kilo remedy remains
operator-side - provider sandbox/LFS quota, or `GIT_LFS_SKIP_SMUDGE=1`.

**Status: internal gate green on the exact evidence head. `MERGE_AUTHORIZED =
false`** while SonarCloud `110912278869` and Kilo `110910907968` remain
FAILURE.

---

## B4-CXR7U9R48X4 - superseding correction (implementation head `f1b8e1d63`)

**Implementation head:** `f1b8e1d632e4efd0007607f0e93886f5eb4293fa` (tree
`573613b875071c0a2b387d8a043bf5a2b5fb4b4b`). **Test-only**: one file changed,
+363 / -34, **0 files under `scripts/`**; every production file, including
`pg-recovery.py`, is byte-identical to `3f5ebba2f8e7407f0a8048e4fe23a7d793eb9039`.

**Superseded claims, corrected:**

| Item | Superseded | Corrected | Authority |
|---|---|---|---|
| R48R3 nodes | 43 | **44** | b1 JUnit `37126647171`, by `classname` |
| R48R4 nodes | 39 | 39 | b1 JUnit `37126647171`, by `classname` |
| R48 total | 80 (from an impossible 43+39=82) | **83** | 44 + 39 |
| Whole suite | 679 | **682** | b1 JUnit `37126647171` |
| Duplicate full node IDs | not stated | **0** | verified |
| Kilo remedy | `GIT_LFS_SKIP_SMUDGE=1`, in-repo | **operator-side only; no in-repo lever exists** | check run `111051006409`, app `kilo-code-bot` |

The old `43` was the output of a **wrong attribution filter**: a substring match
on the full node ID counts two R48R4-owned nodes whose parametrized IDs contain
the string `r48r3`. 41 + 2 = 43. Attribution must use the owning module
(`classname`). The corrected total of 83 is 44 R48R3 + 39 R48R4, suite 682,
zero duplicates, every mandatory node selected exactly once.

**Proof-truth repairs (what the three proofs now do and do not establish):**

| Proof | Before | After |
|---|---|---|
| `test_g_an_oversized_record_denial_is_inert` | built a NORMAL valid record, acquisition SUCCEEDED, asserted only census equality; oversized never exercised | builds a record over `_RECORD_MAX_BYTES`, drives the real route, proves refusal, no truncated admission, no downstream partial-byte use, public route fails closed, all governed artifacts byte-identical |
| `test_g_an_oversized_control_becomes_reachable_without_the_bound` | *(absent)* | removes both size comparisons; asserts single anchor, transform changes source, weakened source compiles, behaviour diverges, anchor drift fails loudly |
| `test_g_a_denied_authority_mutates_nothing` | compared only the filename SET; bound `fingerprint` and never asserted it; could not separate attacker from engine | `_MutationTripwire` on the engine's `pgrec.os`; records engine mutations at helper and `os.` layer; asserts tripwire is live; coherent-pin-or-refusal; mixed generation prohibited; `trip.mutations == []`; outside artifacts compared by fingerprint pre-swap |
| `test_g_a_the_mutation_tripwire_detects_a_real_engine_mutation` | *(absent)* | fires the tripwire on a real `_write_transition_record`, asserts both layers, asserts clean disarm |
| `test_b_a_no_record_generation_fails_closed_through_the_shell_route` | dormant branch called `_classify_record_for_shell(bundle, None)` - a bundle where a record was expected; returned 4 via `isinstance(record, dict)` | branch deleted; real no-record generation via `publish_record=False`; `_classify_rollback_for_shell(str(receipt))` returns 4 **for the authority reason**, proved by `_load_transition_record` raising "no durable recovery operation record" |

**Exact implementation-head workflows (all success):** b1 `37126647171`, b2
`37126647143`, b3 `37126647113`, b4 `37126647154`, B1-I1R `37126650535`. b1
reports 682 tests / 0 failures / 0 errors / 0 skipped, `tested_commit` and
`tested_tree` matching the head and tree above, independent gate `PASS`,
`cleanup: ok`, and all five repaired/added tests executed on Linux.

**External truth at this head (not called green):** SonarCloud `111213571196`
COMPLETED/**FAILURE** (D Security + C Reliability on New Code); the annotation
feed is a 50-item sliding window (15 failure / 35 warning), the complete
new-code issue set is `INACCESSIBLE_WITHOUT_CREDENTIALS` because `SONAR_TOKEN`
is unset and Sonar is configured externally; **no** failure-level issue falls
inside the R48 gate's own files or repaired code paths. Kilo `111213177104`
in_progress; the completed run at the previous head was `111051006409`
FAILURE, produced by the `kilo-code-bot` GitHub App in its own sandbox - so
`GIT_LFS_SKIP_SMUDGE=1` **cannot be set from this repository**, and the payload
is 82 LFS objects / 3,231.9 MB with 11 objects over 50 MB, not one 626 MB
parquet. Operator-side remedy: expand the provider sandbox/LFS quota, or use
the per-repository override. No NOSONAR, exclusion, severity, profile, threshold
or coverage change, no test removal, no LFS migration, no `.lfsconfig`.

**Authorization boundary:** PR #4 OPEN, MERGEABLE, UNSTABLE, unmerged; head
`f1b8e1d63`; `main` untouched at `7c7816f382947bbc8a1f2154435fc436f2428fa8`;
`oce-program-build` is not branch-protected, so neither external failure is a
GitHub merge gate. cloud/broker/capital/execution mutations 0; recurring cost
$0; `capital.authority = none`; Book 5 and Atlas Program Block 4 untouched.

**Exit-gate truth:** `READY_FOR_OPERATOR_REVIEW` - internal implementation and
authoritative CI are complete and green at the exact implementation head;
`MERGE_AUTHORIZED = false` while SonarCloud and Kilo remain non-success.

## B4-CXR7U9R48X5 - mutation-proof completeness (supersedes the R48X4 row)

The R48X4 row above describes the tripwire accurately **for the `pgrec.os`
attribute surface only**. Two write-capable channels reachable from the tested
authority entry points were not instrumented, so "zero recorded mutations"
could not have meant "zero engine mutations".

| Channel | Reachable sites | R48X4 instrumented? | Now |
|---|---|---|---|
| `os.<MUTATORS>` (17 names) | many | yes | yes, plus `ftruncate`, `fchmod`, `lchmod`, `utime` |
| `os.open` | 5 | **no** | yes, conditional on write-capable flags |
| `os.fdopen` | 6 | **no** | yes, conditional on write-capable mode |
| builtin `open` | 2 | **no** | yes, conditional on write-capable mode, attributed by caller frame |
| `tempfile.mkstemp` / `mkdtemp` / `NamedTemporaryFile` | 5 | **no** | yes |
| `shutil.copyfileobj` | 1 | **no** | yes |
| six named durable-write helpers | - | yes | yes |

| Test | Before | After |
|---|---|---|
| `test_g_a_denied_authority_mutates_nothing` | zero over a partial surface | zero over the **audited** surface, where "audited" is computed by call-closure from the three entry points |
| `test_g_a_the_mutation_tripwire_detects_a_real_engine_mutation` | fires on a helper write | unchanged, and now sufficient because the surface behind it is complete |
| `test_h_a` .. `test_h_g` | *(absent)* | surface non-emptiness; instrumented == audited; each channel observed live; read opens silent; attribution two-sided; attacker invisible; drift fails loudly |

**Node accounting:** R48R3 44 -> **51**, R48R4 **39**, pair **90**, zero
duplicate full node IDs. Test-only commit `c237caa3` (1 file, 0 files under
`scripts/`); no production defect exposed.

**Merge policy:** PR #4 targets `main`. Authenticated reads of `main`
protection, repository rulesets, effective rulesets for both branches, and
GraphQL `rulesets` all show **none**; the owner is a `User`, so no inherited
organisation ruleset can apply. A bogus-branch control query distinguishes
"unprotected" from "not found", so this is verified rather than inferred from a
404. Neither SonarCloud nor Kilo is therefore a required merge check - but
merge authority remains withheld on OCE policy grounds.

## B4-CXR7U9R48X6 - closed-world mutation-channel proof (supersedes the X5 row)

The X5 row above is **kept and corrected, not replaced**. X5 fixed two real
omissions - `os.open` and builtin `open` - and both repairs remain. But X5
**discovered** channels from a fixed allowlist, so an unrecognised reachable
write was silently ignored instead of rejected.

**Reproduced before repair:** injecting one
`Path(target).write_text("injected")` into the reachable
`_load_transition_record`, with all function names preserved, left the X5
channel set at `[open, os.open]` and kept **H.1, H.2 and H.7 passing**.

| X5 claim | X6 status |
|---|---|
| "instrument every reachable mutation surface" | **withdrawn** - a wider list still cannot be closed |
| "instrumented set == audited set" | **restated as SUBSET** - H.2 asserts reachable ⊆ instrumented; equality is false (2 reachable vs 33 instrumented) |
| "each channel is observed live" | **restated** - each of the **2 reachable** channels is; the other 31 instrumented are capability |
| "drift fails loudly" | **withdrawn** - H.G tested name existence only; replaced by I.E (body drift) |
| per-channel "reachable sites" table | **corrected** - `os.fdopen` (6), `tempfile.*` (5), `shutil.copyfileobj` (1) and the six durable-write helpers are **whole-file** counts with **0 authority-closure sites** |
| H.7 | **deleted** - anchor-existence is not drift detection |

**Four quantities, separately measured at `ab34dada`:**

| Quantity | Value |
|---|---|
| reachable call sites (35-function closure, each classified once) | **312** |
| reachable mutation call sites | **7** |
| reachable mutation channels (distinct callees) | **2** - `open`, `os.open` |
| globally instrumented channels | **33** |

Classification of the 312 sites: 176 `PROVEN_READ_ONLY_OR_PURE`,
129 `INTERNAL_CALL`, 7 `INSTRUMENTED_MUTATION_CHANNEL`, **0**
`UNKNOWN_OR_DYNAMIC`. Call-site identity is `owner|callee|line:col` ->
**312 distinct over 312 sites, 0 ambiguous**. Unknown or dynamic calls now
**fail closed**; module receivers must match full dotted spelling, so a
bare `"open"` entry cannot admit `shutil.open` or `io.open`.

| Test | Establishes | Discriminated by mutation |
|---|---|---|
| `test_i_a_an_unknown_mutation_call_fails_the_closed_world_audit` | an unregistered write API makes the proof red and names the site | **yes** |
| `test_i_b_a_known_mutation_maps_to_its_observer_and_loses_its_observer` | observer mapping, and that losing the observer fails | **yes** |
| `test_i_c_read_only_channels_are_classified_but_stay_silent` | read-only calls are classified and silent at runtime | yes |
| `test_i_d_builtin_open_attribution_limit_is_explicit` | two-sided attribution **and its exact limit** | yes |
| `test_i_e_body_drift_fails_even_when_every_anchor_is_present` | real body drift, replacing H.7 | **yes** |
| `test_i_f_the_four_quantities_are_reported_separately` | reachable / global / instrumented are not conflated | **yes** |
| `test_i_g_the_dispatch_local_admission_is_proven_executably` | the `handler` dispatch-local admission | yes |

Two honest negative results: neutering `_assert_closed_world` leaves **H.1
passing** (it had nothing to catch), and **H.2's subset assertion does not
discriminate in isolation** (no orphan channel exists in shipped source).
The controls, not the prior tests, carry the discrimination.

**Attribution limit:** immediate engine-frame attribution covers **direct
builtin `open` calls only**; any indirect file API is rejected by the
closed-world audit unless separately instrumented.

**No production mutation defect was discovered.** The gap was in the proof,
not the engine. `pg-recovery.py` is untouched; `ab34dada` changes 1 file with
**0 files under `scripts/`**.

**Node accounting:** R48R3 51 -> **57**, R48R4 **39**, pair **96**, **0**
duplicate full node IDs. Test-only commit `ab34dada`.

**Authoritative runs:** all five workflows `success` on `ab34dada` - b1
`37144654562`, b2 `37144654601`, b3 `37144654574`, b4 `37144654554`,
B1-I1R `37144656252`. b1 artifact `b1-local-ground-evidence-eedfb77a97f9`:
**695 tests, 0 failed, 0 errors, 0 skipped** (`689 - 1 + 7` against the X5
baseline run `37138807973`), gate `"result": "PASS"`, `AUTHORITATIVE_CI`,
tested commit = `ab34dada`, source clean before and after, zero mandatory
skips, cleanup `"ok"`.

**External checks at `ab34dada` - unchanged, still red, unsuppressed:**
SonarCloud `111266350750` `completed`/`failure` (D Security and C
Reliability on new code); Kilo `111265992217` `completed`/`failure`
(provider-side `git-lfs` smudge exit 128, `annotations_count = 0`, no code
reviewed). Neither is weakened, suppressed, excluded, waived or relabelled,
and neither is claimed green.

**Merge policy (§10.5) reverified and unchanged:** no classic protection on
`main` or the head, repository rulesets `[]`, effective rulesets `[]`,
owner type `User`, `permissions.admin = true`, `reviewDecision = ""`. So
neither external check is GitHub-required - **which is not merge
authority**. PR #4 is `OPEN`, `mergedAt = null`, `MERGEABLE`,
`UNSTABLE`. **`MERGE_AUTHORIZED = false`**.

## SonarCloud new-code census - supersedes the §11.9 "sample" framing

The X6 §11.9 row is **kept and corrected**. It correctly called the
annotation feed a sample; §12 measures that sample and shows exactly
what it hid.

| §11.9 statement | Correction |
|---|---|
| "hard-capped at 50 -> a sample, not a census" | **confirmed and quantified.** Cap is SonarCloud's, not GitHub's: **132/132** non-empty slices hold exactly 50, and **page 2 is empty on all 132**, so intra-run paging reveals nothing. Unioning **across** analyses is the lever. |
| "complete new-code issue set is `INACCESSIBLE_WITHOUT_CREDENTIALS`" | **restated precisely:** the **count** is measured (**~324** current epoch); the **type** is still credential-gated. |
| "27 distinct failure-level issues across two samples" | **severe undercount.** The converged window holds **108 failure-level** and **213 warning-level**. |
| "0 are BUG-class" | **never a measurement.** The annotation object has 11 fields and **no rule key, no type**. |
| "at least one unseen bug likely exists" | **understated - it is certain**, since Reliability derives only from BUG-type. |

| Figure | Value |
|---|---|
| commits walked / analyses located | **882 / 170** |
| analyses carrying annotations | **132** |
| non-empty slices at exactly 50 | **132 / 132** |
| slices truncated by GitHub | **0** |
| distinct keys ever annotated | **1599** (1066 seen in exactly one analysis - historical) |
| **distinct keys, current epoch (converged)** | **~324** |
| keys visible in the newest single analysis | **50** |
| **keys absent from that analysis** | **271 of 321 (84%)** |

**The three figures are not interchangeable**: 1599 = ever annotated,
~324 = current epoch, 50 = one published slice. The curve plateaus at
~317-324 over the newest 40-80 analyses and then breaks open at K>80,
which is an **epoch boundary into May 2026 code**, not more data.

**Method.** Direct HTTPS to `api.github.com`; 1232 requests, 0 failures.
Two rules enforced in code: **a failed fetch is never treated as
absence**, and **page 2 is always fetched** to prove a slice is not
truncated. Dedupe is on the SonarCloud issue key in the annotation
message URL, never path+line. (An earlier `gh api` implementation
silently 404'd and reported 69 analyses / 322 keys; that round is
discarded.)

**Type attribution is still blocked, and a tempting proxy was refuted.**
`rules/show` -> 404, `rule_key` search -> `total 0`, `components/show` ->
"Project doesn't exist" (private). No `SONAR_*` in the environment, no
Sonar entry in `KEYS.md`, none among the 25 variables in `.env`, and
the operator runbook holds a literal `<paste>`. **`annotation_level`
is NOT a type proxy**: `failure` contains 17 `"[[ instead of ["` and
~45 `Cognitive Complexity` rules, all CODE_SMELLS. Trap named for
posterity: unauthenticated `issues/search` returns a clean **`total:
0`** for a private project - reporting that as *no issues* would be
false, and it was not used.

**What the gate proves without the feed:** Reliability derives only from
BUG-type and Security only from VULNERABILITY-type, and both are red -
so **at least one BUG and at least one VULNERABILITY certainly exist**
in the current new-code set, and the feed cannot say which.

**Triage residual.** Of 108 failure-level issues, 75 match known
CODE_SMELL names and 18 are shell `"[[ instead of ["` rules. The
remaining **15** are security/bug-named: path traversal at
`independent-gate-b2.py:82,135,288`, `oce_worker.py:66`,
`worker_supervisor.py:127`, **`pg-recovery.py:448,710,1118,1154,1405,
3302,3678`**, command-argument injection at **`pg-recovery.py:522`**,
ReDoS at `schema_validator.py:85`, and a `CancelledError` re-raise at
`http_api.py:137`. **Eight of the fifteen are in the recovery engine PR
#4 exists to harden.** Type unverified; these are named candidates.

Read-only. No `NOSONAR`, no exclusion, no quality-profile change, no
workflow edit. SonarCloud `111270669563` and Kilo both remain
`completed`/`failure` and neither is claimed green.
**`MERGE_AUTHORIZED = false`.**

## B4-CXR7U9R48X7 - receiver-bound authority (supersedes X6's closed-world row)

X6's row is **kept and corrected**. X6 replaced allowlist discovery with a
fail-closed classifier; what remained was closed-world in **spelling**
only.

| X6 property | X7 status |
|---|---|
| unknown spellings fail closed | **holds** - retained and proven by I.A and J.K |
| ambiguous KNOWN method names fail closed | **was false.** Admission used the bare attribute name, so `Path(src).replace(dst)` - a **filesystem rename** - was admitted as the reviewed string operation `replace`; `external.update` / `sink.append` inherited dict/list authority; `Factory().commit()` classified `INTERNAL_CALL` because class methods had been harvested into the internal namespace |

**Reproduced end-to-end before repair:** all four injected into a
reachable function with every anchor name preserved;
`_assert_closed_world` **PASSED with 0 unknowns** over 318 sites.

| Rule | Implementation |
|---|---|
| A module calls | complete dotted names only (`QUALIFIED_MODULES`, now including `os.environ`) |
| B receiver methods | 16 measured `(receiver, method)` pairs in `REVIEWED_RECEIVER_METHODS` |
| C expression receivers | 3 measured shapes only; `Path(x).replace(y)` refused |
| D INTERNAL from a bare name | module-level definitions only; 12 nested/method names dropped; **measured to break no reachable site** |
| E `_STATE_DISPATCH` | explicit dispatch seam, still proven by I.G |
| F `PURE_CONSTRUCTORS` | consulted before engine definitions; no longer dead |

**Every bare method name was removed from `READ_ONLY_REGISTRY`**, so no
receiver can inherit reviewed authority from a method name at all.

| Control | Establishes |
|---|---|
| `J.A` | `Path(src).replace(dst)` refused; cannot inherit `str.replace` authority |
| `J.B` | `external.update(...)` refused |
| `J.C` | `sink.append(...)` refused |
| `J.D` | `Factory().commit()` not an engine function; internal namespace is module-level only |
| `J.E` | reviewed dictionary `.get` calls still admitted |
| `J.F` | reviewed list `.append` calls still admitted |
| `J.G` | reviewed string methods only at reviewed receivers |
| `J.H` | `entry.stat` admitted; `other.stat` refused |
| `J.I` | reachable `os.open` maps to an observer **and fires on a live tripwire** |
| `J.J` | removing that observer makes the proof red; restoring it makes it green |
| `J.K` | the X6 `Path.write_text` control stays red |
| `J.L` | every reachable call site classified exactly once; identities distinct |
| `J.M` | the reviewed-constructor policy is reachable, not dead |

**Discrimination measured:** 9 classifier mutations, **15**
mutation/control pairs, **0 vacuous controls**. One pair is recorded
honestly as unaffected - restoring the blanket rule does not make `J.A`
fail, because the expression-receiver guard fires first; `J.A` is
discriminated by disabling that guard instead.

| Measure | X6 | X7 |
|---|---|---|
| closure functions | 35 | **35** |
| reachable call sites | 312 | **312** |
| distinct identities / ambiguous | 312 / 0 | **312 / 0** |
| READ_ONLY / INTERNAL / MUTATION / UNKNOWN | 176 / 129 / 7 / 0 | **182 / 123 / 7 / 0** |
| reachable mutation channels | 2 | **2, unchanged** |
| R48R3 / R48R4 / pair | 57 / 39 / 96 | **70 / 39 / 109** |
| duplicate full node IDs | 0 | **0** |
| b1 JUnit | 695 / 0 / 0 / 0 | **708 / 0 / 0 / 0** |

All five workflows **success** on `ac49bb7523b1e61752fb6311fe3c6114dd78f890`:
b1 `37217880283`, b2 `37217880288`, b3 `37217880287`, b4 `37217880284`,
B1-I1R `37217883110`. Gate `PASS`, 75/75 checks ok, cleanup `ok`, all 13
`J.*` controls executed on Linux.

**No production change.** `pg-recovery.py` untouched; `ac49bb75` changes 1
file with **0 files under `scripts/`**.

---

## B4-CXR7U9R48X7 - SonarCloud temporal-union correction (supersedes §12)

§12 is **kept and corrected**. Its measurements stand; its inference from
a union across analyses to a **current active** issue set is withdrawn.

| §12 claim | X7 status |
|---|---|
| "current epoch (converged) = ~324" | **withdrawn** - ~324 is *distinct issue keys observed across the selected recent analysis window*, an observational count |
| "the count is measured; only type is credential-gated" | **withdrawn** - current **membership, count, status and type** are all credential-gated |
| "current window contains 108 failure / 213 warning" | **restated** - those are annotations **observed across analyses**, not asserted currently active |
| "271 of 321 suppressed from the newest analysis" | **restated** - 271 union keys are absent from the newest published slice; absence does not distinguish *resolved* from *capped / never published* |
| "slice-across-analyses turns the sample into a census" | **withdrawn** |
| the residual 15 as confirmed current issues | **withdrawn** - named candidates, none asserted active without current-source proof |

**Preserved measurements:** 882 commits walked; 170 analyses located; 132
non-empty slices; **all 132 exactly 50**; page 2 empty on every slice;
**1,599** distinct keys ever observed; direct-HTTPS harvester refusing
failed fetches (1232 requests, 0 failures); no token present; and
`annotation_level` **is not** an issue-type proxy (refuted: the `failure`
level contains 17 `"[[ instead of ["` and ~45 `Cognitive Complexity`
rules that are code smells).

**Truthful replacements:** newest published slice = exactly **50**
annotations; recent-window observed union = ~**324** distinct keys;
**271** union keys absent from the newest published slice; absence does
not distinguish resolved from capped/not-published.

```
CURRENT_ACTIVE_SONAR_SET = INACCESSIBLE_WITHOUT_AUTHORIZED_CREDENTIALS
```

**Credential search - presence only, never values:** all seven `SONAR_*`
variables absent; operator `KEYS.md` has 0 Sonar entries; workspace `.env`
has 0 Sonar entries; the operator runbook holds a literal `<paste>`
placeholder. No token was printed, written, committed, placed in a URL or
logged. **No active count is fabricated.**

**What the red ratings prove:** Reliability = C implies **>= 1 BUG** in the
applicable current code period; Security = D implies **>= 1 VULNERABILITY**.
**Not inferred:** which annotations they are; that any security-named
annotation is a vulnerability; that the eight historical `pg-recovery.py`
candidates are currently active; that historical line numbers still
identify current sinks. **Security Hotspots do not automatically establish
Security Rating defects.**

**Current-source audit of the two live `pg-recovery.py` findings: both are
FALSE POSITIVES.** `_load_receipt` validates inline; `sha256_file`'s only
caller passes a path admitted by `_validated_open_path` (no-symlink,
approved-root containment, regular file, in that order). The same audit
found three **unguarded** `os.path.join(_transitions_dir(), ...)`
constructions (`_transition_record_path`, `_coordinate_path`, the
authority `metadata_path`) against a hardened sibling
`_derive_record_coordinate_name` - **not currently reachable** with an
unvalidated id, because every traced entry validates upstream. A
fail-open-under-refactor gap, **not a demonstrated defect**; **no
production change made**. Method limit recorded: the first automated
pass over-reported six unguarded edges and each was resolved by hand, so
the confidence is "no traced path is unguarded", not "no path exists".

**External truth at `ac49bb75`:** SonarCloud `111482427284`
`completed`/`failure`; Kilo `111482021226` (terminal state in the operator
handoff); five `validate` all `success`; PR #4 `OPEN`, unmerged,
`MERGEABLE`, `UNSTABLE`, 0 reviews; `main` unprotected; rulesets `[]`.
Neither external check is weakened, suppressed, excluded, waived or
relabelled, neither is claimed green, and neither is a GitHub-required
check - which is **not** merge authorization. **`MERGE_AUTHORIZED =
false`.**

---

## X7X - receiver-name binding provenance (`6f088e6b9`, B4-CXR7U9R48X7X1)

**Question put to the classifier:** does the receiver-bound policy handle
tuple-unpacking, walrus, comprehension and lambda receivers **without
reopening the X6 hole**?

**Answer, in two parts. The first is yes; the second was no until this
commit.**

**Q1 - a receiver that IS one of those shapes: refused, already.** No
`Tuple`, `NamedExpr`, `ListComp`, `SetComp`, `DictComp`, `GeneratorExp` or
`Lambda` receiver exists anywhere in the 35-function closure (129 method
calls with a receiver: `Name` 100, `Attribute` 23, `Call` 4, `Constant` 2).
Each normalizes to a spelling absent from every reviewed registry. K.A proves
it executably; K.B proves the shapes are absent from the real closure, so the
green suite is **not** coverage the engine exercises today.

**Q2 - one of those shapes used as the BINDING that produces a receiver
name: it FORGED the review.** At `df19763a3`, comprehension targets, walrus
targets, tuple-unpacking targets, lambda parameters, for/with targets and
augmented assignment were **all** classified `PROVEN_READ_ONLY_OR_PURE`.
X7 bound a method to a receiver NAME and never bound the NAME to a VALUE, so
the X6 failure family survived one level up. **This corrects the guarantee
X7 recorded.**

**Repair.** A reviewed pair is now admitted only when (a) the receiver name
is bound in that owner solely by **reviewed binding forms**, measured from the
source under audit against a frozen 15-entry registry, and (b) the owning
function is one of 27 measured `(owner, receiver, method)` triples. The two
rules are independently discriminated: the form rule **cannot** catch
tuple-unpacking of `record`, because `assign-unpack` is legitimate elsewhere
in the closure, so owner-scoping is what closes it.

**Discrimination: 16 mutations, 36 pairs, 17 controls, 0 vacuous, 0 invalid,
PASS.** The harness now reports a mutant that fails to *import* as INVALID
rather than as discrimination.

**Totals unchanged by the repair** - 312 sites, 182/123/7/0, 2 reachable
mutation channels - because the two new refusal conditions are never tripped
by the real engine. **40 sites** sit behind the 27 triples.

**Still open, enumerated rather than asserted away (K.M):** a reviewed
receiver rebound by a form the review *does* cover, inside a function that
*did* review that pair, remains admitted - `record = externals[0];
record.get('x')` in `_classify_record_for_shell`, and a second `for`-binding
of `entry` in `_assert_selector_authority_names`. The classifier has no value
flow. K.M fails if either ever closes, so the evidence is rewritten rather
than the control deleted.

**Also repaired:** `_classify_call`'s docstring, garbled by `ac49bb75`
absorbing its own closing delimiter. Syntactically valid, so no test caught
it - but the classifier's description of its rule order was truncated.

**Validation at `6f088e6b9`:** R48R3+R48R4 **120 passed / 3 skipped**;
R40 **34 passed / 1 skipped**; Ruff `All checks passed!` on the changed file
(13 pre-existing findings elsewhere, identical to baseline); `py_compile` OK;
`git diff --check` clean; **722 collected / 722 unique / 0 duplicate** node
IDs; CRLF preserved.

**Scope: one test module. `scripts/pg-recovery.py` is byte-identical to
`df19763a3` - no production change.** No SonarCloud or Kilo suppression,
exclusion, waiver or relabelling; no `NOSONAR`; no test deletion. No merge,
no force push, no amend/squash/rebase/reset; `main` untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`.

**External truth at `6f088e6b9`:** five `validate` all `success`; SonarCloud
and Kilo outcomes recorded in the operator handoff - neither is a
GitHub-required check, which is **not** merge authorization.
**`MERGE_AUTHORIZED = false`.** PR #4 remains **open and unmerged**.
## X8 - EXACT CALL-SITE AND BINDING AUTHORITY

Mission `B4-CXR7U9R48X8`. Supersedes the X7 and X7X authority rows; those
entries stand as valid historical evidence for what they actually proved.
Full record: `B4-EVIDENCE-RECORD.md` section 16.

**The gap, demonstrated before repair at `df19763a3`.** X7's replacement for
bare method names was a GLOBAL syntactic-pair allowlist: `_classify_call`
tested the normalized expression against `REVIEWED_RECEIVER_METHODS` and
`owner` never participated in authorization. So an approved PAIR was a global
capability. Five scenarios were admitted, each with entry-point reachability
preserved and a negative control: a known pair injected into a different
reachable owner; a duplicate inside its own owner; `roots = attacker` before
`roots.append`; `os = attacker` before `os.stat`; and a shadowed reviewed
constructor. A sixth control, a genuinely new spelling, was refused - so the
harness observed real change rather than a blanket refusal. This is the X6
failure family one level up: X6 bought authority from a method's attribute, X7
from a receiver's spelling.

**The repair.** Authority is bound to the exact reviewed source site AND to
the source context that gives the receiver its meaning, through two frozen,
independently load-bearing registries measured from the shipped engine:
`EXACT_SITE_MANIFEST` (206 `(owner, expression)` entries with exact occurrence
counts) and `REVIEWED_OWNER_DIGESTS` (35 owner digests). `_site_authority`
gates every grant, so no grant by-passes it. Both rules are needed: the digest
cannot refuse a duplicate, and the manifest cannot refuse a rebinding that adds
no call. Coordinates remain diagnostic only.

Stated boundary, NOT widened: this is exact-site and exact-owner-context
binding, **not** semantic type resolution. It proves the site is the reviewed
one in the reviewed owner and that the owner has not been edited. It does not
prove that `record` holds a dict.

**The finding that mattered most: the baseline was correct and CI was red
anyway.** Head `72d88af6c` was green locally; b1 returned **33 failed, 704
passed** on Linux, reporting 313 `UNKNOWN_OR_DYNAMIC` sites with **35 of 35**
owner digests mismatched. Measured root cause: b1 runs **CPython 3.12.14**, the
development machine **3.11.9**, and `_owner_ast_digest` used `ast.dump`, which
is not interpreter-stable - 3.12 appended `type_params` to
`FunctionDef._fields`. All 24 distinct CI-reported site coordinates existed
locally at the IDENTICAL line:col and spelling (0 absent locally), so the parse
agreed and only the serialisation differed; and the local digest equalled
precisely the value the runner reported as REVIEWED. The reviewed baseline had
a second, hidden input: the interpreter. `c90482159` replaced `ast.dump` with a
serialisation over a FROZEN VOCABULARY of field names, so a field this
interpreter does not know is never read and a field a future interpreter adds
cannot leak in. The reviewed manifest was **not** touched - verified byte for
byte, because its keys never used `ast.dump`.

**Two further defects found while proving that, both ours.** The vocabulary
omitted `id`, so every identifier in an owner was invisible to its digest and a
rename or a rebound receiver could not withdraw anything - the exact
sensitivity X8 exists to provide. M.A now ENUMERATES the real closure's fields
instead of trusting a read-through. And the discrimination harness treated a
SKIPPED mutation as a PASS: when the serializer replaced the `ast.dump` body
that `digest-includes-coordinates` anchored on, the anchor vanished, the
harness printed SKIP and still reported `PASS`, silently vacating L.I. The
harness now fails on SKIP.

**And the repair's own control asserted the wrong shape of the world.**
`c90482159` came back **1 failed, 741 passed on 3.12**: the digest repair
worked - every frozen digest, the manifest, the exact-site gate and all 26 X8
claims validated on the interpreter that had falsified them - and the single
failure was M.D, which asserted `type_params` was ABSENT from
`FunctionDef._fields`. True on 3.11, false on 3.12, so it passed on the
interpreter that had the defect and failed on the one that did not. `47db26def`
makes M.D and M.E present the field the way THIS interpreter carries it, with
an exact restore in both directions, and adds M.F: the control whose absence
allowed it, which puts the running interpreter into the 3.12 shape and re-runs
the exact comparison that failed on the runner. M.F's stated limit is that it
reproduces the one documented 3.12 AST change that caused the failure and does
not claim there are no others; the authority for that is b1 on 3.12 itself.

**Superseded X7 claims** (corrected in the record, X7 history not rewritten):
X7 bound methods to normalized receiver SPELLINGS, not exact call sites or
receiver bindings; it blocked arbitrary NEW spellings while still allowing
approved spellings to be reused or rebound without a new review decision.
"A pair that appears anywhere else is refused", the policy being safe "at this
site", receiver spelling constituting receiver binding, and J.L proving
individual call-site authorization are all superseded - J.L proves every site
is classified exactly once with a reason, which is not the same claim. The
Sonar temporal-union correction is retained unchanged: a union across analyses
remains historical observation, never a current active-issue census.

**Measurements, unchanged from the pre-X8 baseline** (so the two new refusal
conditions are never tripped by the real engine): 35 closure functions; 312
reachable call sites; 206 manifest entries; 35 owner digests; 312/312 unique
site identities; 0 missing, 0 surplus, 0 count-drift, 0 provenance mismatches;
**182 / 123 / 7 / 0** READ_ONLY / INTERNAL / MUTATION / UNKNOWN; 2 reachable
mutation channels (`open`, `os.open`), all observing; 33 globally instrumented
channels; 182/182 READ_ONLY rows carrying a reason.

**Validation at `47db26deff995034d89402964fcea28bf72562fd`.** Discrimination:
**26 mutations / 69 pairs / 34 controls / 0 vacuous / 0 skipped / 0 invalid**,
with six non-biting pairs reported individually alongside the mutation that
does discriminate each. Local R48R3+R48R4: **144 node IDs, 144 unique, 0
duplicates**; 141 passed, 3 skipped (platform-conditional). R40 **34 passed /
1 skipped**. Ruff `All checks passed!` on the changed file (13 pre-existing
findings elsewhere, identical to baseline). `py_compile` OK; `git diff
--check` clean. The whole module also runs 101 passed / 3 skipped in a
SIMULATED 3.12 world on 3.11.

**Authoritative runs at the implementation head:** b1 `37236129355`, B1-I1R
`37236132862`, b2 `37236129394`, b3 `37236129340`, b4 `37236129357` - all
`success`. Superseded head `c90482159`: b1 `37235001825` **failure**, the other
four success; recorded rather than hidden. The b1 artifact for the
implementation head was read from its own files, not inferred from workflow
colour: `tested_commit` `47db26deff995034d89402964fcea28bf72562fd`, `tested_tree`
`3ba01f5977e4e0d94c3abe8609bfcbf07a8b48b3`; JUnit **743 collected / 743
executed / 0 failed / 0 errors / 0 skipped**, 743 unique node IDs with **0
duplicates**; 15 `L.*` plus 6 `M.*` X8 nodes all present and executed;
independent gate **75 / 75 checks ok**; cleanup `{"cleanup": "ok",
"disposable_removed": true}`; the artifact's own fingerprint reports
`Python 3.12.14`.

**Scope: one test module and two Markdown files. `scripts/pg-recovery.py` is
byte-identical - no production change**, because no independently demonstrated
production defect required repair. No SonarCloud or Kilo suppression,
exclusion, waiver or relabelling; no `NOSONAR`; no test deletion. No merge, no
force push, no amend/squash/rebase/reset; `main` untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. Accounting: cloud mutations 0,
broker mutations 0, capital mutations 0, execution mutations 0, recurring cost
$0, capital authority none. SonarCloud and Kilo remain the only external checks
and neither is a GitHub-required check, which is **not** merge authorization.
**`MERGE_AUTHORIZED = false`.** PR #4 remains **open and unmerged**.

## X9 - LOSSLESS, VERSION-NORMALIZED SOURCE AUTHORITY

Mission `B4-CXR7U9R48X9`. Corrects five X8 claims (see the full record,
`B4-EVIDENCE-RECORD.md` section 17); X8's exact-site and occurrence authority
stand as valid historical evidence.

**The X8 blind spot, demonstrated before repair at `663f46b61`.** X8 kept the
owner digest stable across 3.11/3.12 by DROPPING `type_params` as "merely
interpreter metadata" and by emitting fields in the interpreter's `_fields`
order. Both halves were defects. PEP 695 type parameters create a lexical
scope visible inside the generic body, so `def f[os](): os.stat(path)` resolves
`os` to the type parameter -- and the measured probes showed the digest
unchanged (`dbb47ffe4249a39e...`), the binding walker reporting no `os`
binding, the manifest and occurrence count unchanged, and the site still
granted as `PROVEN_READ_ONLY_OR_PURE`; `hashlib`, `RecordSnapshot` and
`_transitions_dir` shadows were granted the same way. Swapping two entries of
`FunctionDef._fields` -- same values, same source -- moved the digest
`c649a4c9df70b303...` -> `4953c178717f43fe...`, and an unknown `Call` field was
silently ignored (digest identical for two different values while `ast.dump`
moved). Every reproduction had a negative control.

**The repair (R1).** The canonical serializer reads a frozen schema that
INCLUDES `type_params` (and `bound`), with the `_INTERPRETER_FIELD_ADDITIONS`
exception set removed entirely; emits fields in sorted-name order, never in
`_fields` order; normalises a MISSING `type_params` to `[]` so a non-generic
definition has one canonical value on 3.11 and 3.12 while a real non-empty
parameter is serialised like any other content; RAISES
`_UnreviewedAstFieldError` naming the node type and field when the interpreter
carries a field outside the schema; and encodes as structured JSON with tagged
scalars rather than undelimited fragments. All 35 digests were regenerated; the
206-entry manifest is byte-identical to X8 (11,292 bytes), because its keys
never used the serializer. Stated boundary: validated on CPython 3.11 and 3.12
-- no arbitrary future-version independence is claimed.

**The repair (R2).** `type-param` is part of the binding vocabulary; the walker
reports every type-parameter name on `FunctionDef`, `AsyncFunctionDef` and
`ClassDef`; and a classifier-level refusal computed from the measured binding
inventory -- deliberately INDEPENDENT of the owner digest -- refuses any call
whose callee or receiver is shadowed, naming the binding form and the shadowed
name. `def f[os](): os.stat(...)` and the `hashlib`/constructor/internal
variants are refused; with the exact-site gate neutralised the binding rule
alone still refuses; a harmless `[T]` still moves the digest and withdraws
every grant (a review decision). REAL PEP 695 syntax controls (N.G x4, N.H,
N.I) are gated to 3.12+ and executed by b1 on 3.12.14; the 3.11 suite runs the
exact synthetic shape instead and COMPARES it against the real parser on the
runner, rather than assuming equivalence.

**Measurements, unchanged from the X8 baseline** (the repair changed what the
digest and walker can see, not what is authorized): 35 closure functions; 312
reachable call sites; 206 manifest entries; 35 owner digests; 312/312 unique
site identities; 0 missing, 0 surplus, 0 count-drift; **182 / 123 / 7 / 0**
READ_ONLY / INTERNAL / MUTATION / UNKNOWN; 2 reachable mutation channels
(`open`, `os.open`), all observing; 33 globally instrumented channels; 182/182
READ_ONLY rows carrying a reason.

**Validation.** Discrimination: **34 mutations / 98 pairs / 41 controls / 0
vacuous / 0 skipped / 0 invalid**, with eight non-biting pairs reported
individually alongside the mutation that discriminates each. Local
R48R3+R48R4: **159 node IDs, 159 unique, 0 duplicates**; 150 passed, 9 skipped
(3 platform-conditional + 6 real-PEP695 gated, which b1 executes). Module also
runs 111 passed / 9 skipped in a SIMULATED 3.12 world on 3.11. R40 **34 passed
/ 1 skipped**. Ruff `All checks passed!` on the changed file (13 pre-existing
findings elsewhere, identical in count to baseline). `py_compile` OK; `git
diff --check` clean; module pure LF.

**Authoritative runs at the implementation head**
`e42b2b4e8fb0e88eaea3d165ad5bd998b7f299ef` (tree
`aadba62553d0691e5a3ab08128d9ea2912d8e1d0`): b1 `37241959812`, B1-I1R
`37241962667`, b2 `37241959938`, b3 `37241959950`, b4 `37241959726` -- all
`success`. No superseded head failed on this mission. The b1 artifact was read
from its own files, not inferred from workflow colour: `tested_commit`
`e42b2b4e8...`, `tested_tree` `aadba625...`; JUnit **758 collected / 758
executed / 0 failed / 0 errors / 0 skipped**, 758 unique node IDs with **0
duplicates**; 15 `L.*` + 6 `M.*` + 15 `N.*` all present and executed (including
the six real PEP 695 controls on the runner's own parser); independent gate
**75 / 75 checks ok** including "manifest hashes and sizes match final files";
cleanup `{"cleanup": "ok", "disposable_removed": true}`; artifact fingerprint
`Python 3.12.14`; cloud mutations 0, cost ZERO.

**Scope: one test module and two Markdown files. `scripts/pg-recovery.py` is
byte-identical across X9 (blob `6e322784beeed6c749fed0c9a0a1c67740b687ce`) --
no production change**, because no independently demonstrated production defect
required repair. No SonarCloud or Kilo suppression, exclusion, waiver or
relabelling; no `NOSONAR`; no test deletion. No merge, no force push, no
amend/squash/rebase/reset; `main` untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. Accounting: cloud mutations 0,
broker mutations 0, capital mutations 0, execution mutations 0, recurring cost
$0, capital authority none. **`MERGE_AUTHORIZED = false`.** PR #4 remains
**open and unmerged**.


## B4-FINAL-GOVERNANCE -- unauthorized external checks removed from the closure gate

Supersedes every earlier acceptance row that treated **SonarCloud Code Analysis**
or **Kilo Code Review** as a Book 4 closure gate. It does **not** withdraw the
X7/X7X temporal-union correction: those rows remain valid, and the union is
still explicitly *not* the active issue set.

| Item | Value |
|---|---|
| Operator authorization for SonarCloud | **never granted** |
| Operator authorization for Kilo | **never granted** |
| Operator account created for either | **none** |
| Operator-managed credential for either | **none** (repo Actions secrets = 0) |
| Budget / cost authority established | **none**; recurring cost stayed $0 |
| Acceptance requirement established | **none** |
| Lifecycle authority established | **none** |
| Required by branch protection | **no** -- `main` protection HTTP 404 |
| Required by repository rulesets | **no** -- rulesets `[]` |
| Attachment mechanism | **GitHub App installation only** |
| SonarQubeCloud identity | slug `sonarqubecloud`, app id `12526`, owner SonarSource |
| Kilo Code Bot identity | slug `kilo-code-bot`, app id `2193792`, owner Kilo-Org |
| Tracked repo config for either | **0** files, **0** workflow references |
| Repository webhooks | **0** |
| Removal scope | **this repository only** -- account-wide uninstall NOT used |
| Other repositories affected | **none** |
| Historical check runs deleted | **none** -- `111555287875` and `111554878664` preserved |

### Governance statements

1. Neither service was ever an operator-authorized Book 4 dependency.
2. No operator account, credentials, budget, acceptance requirement, or
   lifecycle authority was established for either.
3. Neither was required by branch protection or repository rulesets.
4. Their prior failures remain accurate historical observations.
5. Removal is **not** a pass, remediation, suppression, or false-positive
   disposition; nothing was made green and no finding was waived.
6. They are removed from the closure gate because an unapproved third-party
   service cannot acquire governance authority merely by installing a check.
7. The authoritative Book 4 gate is the **five OCE-owned workflows** plus their
   evidence artifacts, bound to the tested commit and tree.
8. Any future external scanner or reviewer requires explicit operator
   authorization, documented ownership, operator-managed credentials, cost
   authority, a declared data boundary, explicit failure semantics, and a
   documented removal procedure before it can become authoritative.

### API boundary of the removal

GitHub permits installation management only to App-scoped tokens. With repository
`admin` and a token carrying `admin:org`: `GET /user/installations` returned
**403** "You must authenticate with an access token authorized to a GitHub App in
order to list installations"; `GET /repos/.../installation` returned **401** "A
JSON web token could not be decoded"; `GET /orgs/dabiggestpoppa/installations`
returned **404** because the owner is a User, not an Organization; and the
repository-scoped `/installations`, `/integrations`, `/apps`, and
`/actions/permissions/apps` routes all returned **404**. Removal was therefore
performed by the operator through the repository-scoped GitHub UI.

### Unchanged by this correction

- `CURRENT_ACTIVE_SONAR_SET = INACCESSIBLE_WITHOUT_AUTHORIZED_CREDENTIALS` is
  still accurate; no active count is fabricated.
- Section 12's measurements stand; the union remains an observational count, not
  a current active set.
- Section 14.5's three `os.path.join` constructions remain an open
  fail-open-under-refactor gap, unrelated to these services.
- No `NOSONAR`, no exclusion, no waiver, no relabelling, no test deletion, no
  coverage manipulation, no profile/rating/threshold/gate change.
- No merge, no force push, no amend/squash/rebase/reset; `main` untouched at
  `7c7816f382947bbc8a1f2154435fc436f2428fa8`.
- Accounting: cloud mutations 0, broker mutations 0, capital mutations 0,
  execution mutations 0, recurring cost $0, `capital.authority = none`.
  **`MERGE_AUTHORIZED = false`.** PR #4 remains **open and unmerged**.

## B4-FINAL-GOVERNANCE (confirmed) -- section 18.3 removal claim falsified and superseded

Section 18 above recorded the governance correction. This row supersedes its
removal-timing claim and stands as the operative position. Nothing is deleted or
rewritten.

### Falsified claim, recorded

Section 18.3 asserted that removal "was completed by the operator through the
repository-scoped GitHub UI". Post-push verification on section 18's own
evidence head `4867c78f597ef684f042e9c0201f2e9f2c31a246` **falsified** it: `kilo-code-bot` created
check-run `111781705620` and `sonarqubecloud` created `111782766280`, both after
the removal action. An early poll appeared to show SonarCloud gone; that was
analysis latency, not removal. **Neither removal had taken effect.** Removal was
re-applied, and its verification is empirical rather than API-based because
installation enumeration remains refused (`/user/installations` **403**,
`/repos/.../installation` **401**).

| Statement | Status |
|---|---|
| SonarCloud ever passed | **NO** -- Quality Gate failed on every analysis observed |
| Kilo ever reviewed this repository | **NO** -- checkout failed (HTTP 429), never began |
| Historical failures | **remain historical and accurate**; check runs preserved, not deleted |
| Reason for removal | **never operator-authorized OCE dependency** -- not any result |
| Required by branch protection | **NO** -- `main` protection HTTP 404 |
| Required by repository rulesets | **NO** -- rulesets `[]` |
| Removal is a pass / remediation / suppression / false-positive disposition | **NO** -- it is a governance act only |
| Authoritative Book 4 gate | **the five OCE-owned workflows** plus their evidence artifacts |
| Operator account / credential / budget / lifecycle authority | **none**, for either service |
| Repo Actions secrets | **0** |

### Unaffected

- `CURRENT_ACTIVE_SONAR_SET = INACCESSIBLE_WITHOUT_AUTHORIZED_CREDENTIALS` is
  still accurate; no active count is fabricated.
- Section 12's measurements and section 14's temporal-union correction stand; the
  union remains an observational count, **not** the active issue set.
- The narrow deduction (Reliability C implies >=1 BUG; Security D implies >=1
  VULNERABILITY) is unchanged, and **no further inference is drawn** now that
  the source is gone.
- Section 14.5's three `os.path.join` constructions remain an open
  fail-open-under-refactor gap, **not** closed by this removal.
- No `NOSONAR`, exclusion, waiver, severity/profile/rating/threshold/gate
  change, coverage manipulation, or test deletion.

### Method

Verifying a GitHub App removal from this account is necessarily empirical: push
a commit after removal and observe whether either app creates a check run, and
only judge absence after the producer's asynchronous latency has elapsed.

No merge, no force push, no amend/squash/rebase/reset; `main` untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. Accounting: cloud mutations 0, broker mutations 0, capital
mutations 0, execution mutations 0, recurring cost $0, `capital.authority =
none`. **`MERGE_AUTHORIZED = false`.** PR #4 remains **open and unmerged**.
### X1 verification marker (claim-free)

Committed before any detachment verdict was reached. It records no outcome.

| Statement | Status |
|---|---|
| Operator reports access removed (app `12526`, app `2193792`) | **reported, unverified** |
| Removal proven at commit time | **NO** -- unreadable from this account (`/user/installations` **403**, `/repos/.../installation` **401**) |
| Sole purpose of this commit | **an observable post-removal push event** |
| Closure / passing-gate / verified-removal claim | **NONE** -- outcome not yet measured |
| Sections 18 and 19 | **preserved byte-for-byte**, including the falsified 18.3 removal claim |
| Marker scope | documentation only -- this file and `B4-EVIDENCE-RECORD.md` |

Predecessor `d0e4b30bd68d96edfd8b68d570a761af1d5c3aa6`. Accounting unchanged:
cloud mutations 0, broker mutations 0, capital mutations 0, execution mutations
0, recurring cost $0, `capital.authority = none`. No merge, no force push, no
amend/squash/rebase/reset; `main` untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. **`MERGE_AUTHORIZED = false`.**
PR #4 remains **open and unmerged**.

### X1 outcome - fourth falsification, and where removal must actually happen

The claim-free marker `6875ca4d6bd8a7ce538228abb67c8b2a09df8da1` was pushed at
`2026-10-05T21:10:44Z`. Both applications answered it.

| Application | App ID | Check run | Check suite | Latency after push |
|---|---|---|---|---|
| SonarQubeCloud | `12526` | `111979956611` `completed/failure` | `101236508229` | ~16 s |
| Kilo Code Bot | `2193792` | `111978689389` `in_progress` at +16m25s | `101236507928` | ~2 s |

Repository access for both applications is **active**. This is the third
marker-grade push and the third reappearance, after `4867c78f` and `d0e4b30b`.

| Statement | Status |
|---|---|
| Operator reports access removed | **reported, unverified, contradicted four times** |
| Any claimed removal in sections 18 or 19 | **falsified again** by observation on a commit that claimed nothing |
| Repository access is active | **YES** - both apps produced runs on `6875ca4d` |
| Removal claimed by this section | **NO** - only the observation is recorded |
| Closure or passing gate granted here | **NONE** |
| Removal is a pass / remediation / suppression | **NO** - a governance act only |
| Authoritative Book 4 gate | **unchanged** - the five OCE-owned workflows plus their bound artifacts |
| Sonar / Kilo classified as passing | **NO** - they are outside the OCE gate and remain failed |
| Five OCE workflow runs on `6875ca4d` | `37374252494`, `37374252505`, `37374252512`, `37374252537`, `37374260699` - all `success` |
| External result waived / suppressed / relabelled / fabricated | **NO** |
| Historical external runs | **preserved untouched** as accurate evidence of failure |

**Three further applications are attached and also answered the push**: Vercel
app `8329` (suite `101236507544`), Railway App `73253` (`101236508678`), and
Freebuff Web `1734312` (`101236509025`), all created `2026-10-05T21:10:43-44Z`.
Recorded, not adjudicated. Removing Sonar and Kilo alone would not restore an
OCE-owned check boundary.

**Root cause to act on.** A GitHub App reaches a repository only through an
*installation*, which lives on an **account**, not on a repository, and carries
its own **Repository access** selection. There is no per-repository
installation to revoke. Narrow the installation to **Only select repositories**,
deselect `larger-lab`, and **save**; also detach at SonarQube Cloud and Kilo
Code; disable SonarCloud **Automatic Analysis**; and check organization
installations, which `dabiggestpoppa` cannot see (zero org memberships, and
`/user/installations` is refused **403**, `/repos/.../installation` **401**).
Full procedure in evidence-record section 21.6.

**Verification rule.** At least five full minutes after any change (worst
observed latency 24 s), then **zero** check runs **and** check suites from app
`12526` and app `2193792`, across **three consecutive** pushes, before any
removal is accepted as verified. One clean sample is one clean sample.

No merge, no force push, no amend/squash/rebase/reset; `main` untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. Accounting: cloud mutations 0, broker
mutations 0, capital mutations 0, execution mutations 0, recurring cost $0,
`capital.authority = none`. **`MERGE_AUTHORIZED = false`.** PR #4 remains **open
and unmerged**.

### X1V2 second verification marker (claim-free)

Committed before any uninstall verdict was reached. It records no outcome.

| Statement | Status |
|---|---|
| Operator reports Sonar `12526` and Kilo `2193792` uninstalled from `dabiggestpoppa` | **reported, unverified** |
| Uninstall readable from this account | **NO** -- `/user/installations` **403**, `/repos/.../installation` **401** |
| Sole purpose of this commit | **a new observable push event** |
| Governance closure or verified-removal claim | **NONE** -- outcome not yet measured |
| Vercel `8329`, Railway `73253`, Freebuff `1734312` | **OUT OF SCOPE** -- inventory only; not altered, not characterised |
| Sections 1 through 21 | **preserved byte-for-byte** |

**Why a second marker was necessary, observed.** The prior evidence commit
`81cc3a05326218620dfa352728b507568933f65c`, which claimed nothing, was itself
answered: Kilo check-run `111985408596` at ~2 s (still `in_progress`
38 m 59 s later, at `22:08:10Z`), SonarQubeCloud check-run `111986347145`
`completed/failure` at ~14 s. A commit that asserts detachment cannot evidence
its own detachment, so the marker and the correction are separate commits.

Predecessor `81cc3a05326218620dfa352728b507568933f65c`. Marker scope: this file
and `B4-EVIDENCE-RECORD.md`, documentation only. No merge, no force push, no
amend/squash/rebase/reset; `main` untouched at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`. Accounting: cloud mutations 0, broker
mutations 0, capital mutations 0, execution mutations 0, recurring cost $0,
`capital.authority = none`. **`MERGE_AUTHORIZED = false`.** PR #4 remains **open
and unmerged**.

