# OCE B5-I6 Acceptance Matrix — v1.0

**Document ID:** OCE-B5-I6-ACCEPTANCE-001
**Version:** 1.0 — FROZEN at P0 under `AUTHORIZED_STAGE=B5-I6` (before any implementation result exists)
**Scope contract:** `OCE_B5_I6_GAP_AND_SCOPE_CONTRACT_v1.0.md`
**Gate to prove:** plan §7 "Clean local install/restart/restore pass"; charter §12 I-6 completion "recovery-drill end-to-end passes; negative controls recorded"; plan §5 C4.S1 "local install works; remote mutation remains hold-gated", C4.S2 "operator detects failure and traces request locally", C4.S4 "RTO/RPO and consistency objectives demonstrated"

Every row is executable: a test node (selected whole-file by the authoritative workflow with a frozen floor) or a named attestation/binding audit. Nodes live in the four B5-I6 files under `infrastructure/control-plane/tests/`.

## A. Requirement-to-node map (I-6 completion + C4.S1–S4 discharges)

| Req | Anchor | Frozen node | Two-sided proof shape |
|---|---|---|---|
| R1 (I-6/G5) unsupported drill operation refused | §5 plan row I-6; charter §11 G5 | `test_b5_i6_recovery_drill.py::TestFailClosed::test_unsupported_drill_operation_refused` | Unknown drill step / over-bound playbook / unknown session resume refused fail-closed **before any action** (exploding recorder proves zero actions); weakened guard admits → red |
| R2 (I-6/G8) console reports, never enacts | charter §11 G8; §9 Recovery | `test_b5_i6_recovery_drill.py::TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting` | Real loopback stack drill: console issues exactly ONE write (the governed submit); engine performs lease expiry + requeue; structural closure over drill **and session_store** modules (no engine verbs); console-owned-recovery weakening → red |
| R3 (I-6/G15) negative controls detect bypass | charter §11 G15 | `test_b5_i6_recovery_drill.py::TestAdversarialControls::test_bypassed_authority_detected` | Executed weakened controls: (a) console-enacted recovery, (b) `DRILL_PASS` minted without engine duplicate-effect sequence, (c) consent-less replay admitted, (d) denial-as-success — each turns its intended node red, then restores green byte-identically |
| R4 (I-6/S-3) worker-loss drill, no duplicate effect | charter §12 I-6; §9 idempotent replay | `test_b5_i6_recovery_drill.py::TestDrillReport::test_s3_lease_requeue_completion_no_duplicate_effect` | Engine drives pending→leased→running, heartbeat stale, engine `recover_abandoned_leases()` requeues, second worker completes; `verify_no_duplicate_effects()` true; exactly one job in store; report bound to engine identity with `DRILL_PASS` |
| R5 (I-6/F-6) consent-governed replay | construction plan stage I-6 (F-6 consent half); charter §9 idempotent replay | `test_b5_i6_recovery_drill.py::TestConsentReplay::test_replay_without_consent_refused_before_actions` + `::test_consented_replay_is_idempotent_and_no_duplicate_effect` | Replay of a partial session without explicit operator consent → `DrillRefusal` before any action; with consent → only remaining steps append (prior actions byte-identical), replay is idempotent, report states the duplicate-effect result; consent-bypass control → red |
| R6 (I-6/G6) restart preserves session record | registry planned node; charter §9 Restart; §11 G6 | `test_b5_i6_console_restart.py::TestRestartIdentity::test_restart_preserves_session_record` | Durable record written by `SessionStore`; a fresh store (console restart) loads a byte-identical, schema-valid, append-only record; engine/job state unaltered by console restart |
| R7 (F-4 console half) crash leaves partial record | registry F-4 console half (§5.1 supersession); charter §9 Interruption | `test_b5_i6_console_restart.py::TestConsoleCrash::test_session_record_marked_partial_on_crash` | Real console subprocess killed mid-drill (SIGTERM after first action): durable record exists with `status: partial`, all pre-crash actions present (RPO 0), control-plane state untouched; a completed record can never be left partial by crash |
| R8 engine restart cannot resurrect console state | charter §9; B5-I5 E2E invariant | `test_b5_i6_console_restart.py::TestRestartIdentity::test_engine_restart_leaves_console_state_untouched_and_reads_fail_closed` | Fresh `ControlPlane` (in-memory store): console session file untouched; `read_job` of the old id raises `JobReadRefusal` fail-closed — never a fabricated or cached success |
| R9 (I-6/S-4) denial verbatim, no silent retry | registry planned node; charter §11 G5/S-4 | `test_b5_i6_fail_closed.py::TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry` | Tampered grant on the drill path → governed denial envelope rendered verbatim, exactly ONE fetch (counting opener), never summarized OK, never retried |
| R10 missing identity renders gap, never green | charter §9 Progress observation | `test_b5_i6_fail_closed.py::TestDenialRendering::test_missing_identity_renders_unverifiable_never_ok` | HTTP-layer 401 `detail` body → `UNVERIFIABLE` with raw preserved (or refusal before I/O where identity is absent pre-construction); never `OK` |
| R11 denied authority can never complete a drill | charter §9 Admission; §11 G4/G5 | `test_b5_i6_fail_closed.py::TestDenialRendering::test_denied_authority_never_completes_a_drill` | Drill with denied submit → no `DRILL_PASS`, no completion, no session flip to `complete`, store empty; weakening → red |
| R12 (C4.S1) manifest deterministic | plan §5 C4.S1; constitution §12.2 | `test_b5_i6_deploy_pkg.py::TestReleaseManifest::test_manifest_is_deterministic_byte_identical` | Two generations over the same tree → byte-identical manifest (no wall-clock, sorted inventory/keys) |
| R13 (C4.S1) manifest complete + rollback metadata | plan §5 C4.S1 (*package, dry run, rollback*); constitution §498 DeploymentManifest | `test_b5_i6_deploy_pkg.py::TestReleaseManifest::test_manifest_covers_declared_install_set_and_rollback` | Every console module, contract pack, compose file, dependency lock and representative-catalog source hashed; rollback pointer field present and validated; missing declared file → generation fails closed |
| R14 (C4.S1) tamper detection | G15 (d) scope contract §7 | `test_b5_i6_deploy_pkg.py::TestReleaseManifest::test_tampered_install_file_fails_verification` | Materialized install with one byte flipped → verification FAIL naming the file; weakened verification admits → red |
| R15 (C4.S1) clean install dry run | plan §7 gate (*clean local install*) | `test_b5_i6_deploy_pkg.py::TestReleaseManifest::test_clean_install_dry_run_verifies_and_imports` | Fresh temp dir materialized from the manifest only; every sha256 verified; console package import-checks and renders a status document **from the installed copy**; remote deployment never attempted |
| R16 (C4.S2) operator detects failure | plan §5 C4.S2 | `test_b5_i6_deploy_pkg.py::TestObservability::test_stack_failure_detected_fail_closed` | Unbound loopback port → whole-view `STACK_UNREACHABLE` (exit-2 semantics), no stale green; degraded governed response → `DEGRADED` with denial verbatim |
| R17 (C4.S2) trace a request locally | plan §5 C4.S2 (*traces request locally*) | `test_b5_i6_deploy_pkg.py::TestObservability::test_operator_traces_governed_operation_in_audit_surface` | Submit → `request_id`/operation traceable in the engine's own `audit.read` surface and bound in the timeline/evidence record — correlation proven from console reads only |
| R18 (C4.S3) chaos matrix rows executable | plan §5 C4.S3 | `test_b5_i6_deploy_pkg.py::TestChaosMatrix::test_process_and_dependency_injections_fail_closed` + `…::test_partial_write_and_timeout_injections_fail_closed` | Process kill (console subprocess against killed/absent stack) → fail-closed; dependency outage (closed port) → fail-closed; partial write (session store interruption) → record stays partial/valid; timeout (injected transport timeout) → `StackUnreachable`, never fabricated success |
| R19 (C4.S4) restore drill + RTO/RPO | plan §5 C4.S4; constitution Art. XV (*untested restore is unverified*) | `test_b5_i6_deploy_pkg.py::TestRestoreObjectives::test_restore_drill_meets_rpo_and_rto_objectives` | RPO: zero persisted drill actions lost across console crash/restart; zero duplicate effects; evidence manifest re-derived byte-identically after engine restart (identity RPO 0). RTO: measured on the engine clock from worker-loss injection to `DRILL_PASS` within the frozen objective bound (lease TTL + fixed drill steps) — no wall-clock claim |
| R20 (C4.S2) runbook exists and binds to executable nodes | plan §5 C4.S2 deliverable *runbook* | attestation + `TestObservability` nodes above | `OCE_B5_I6_DEPLOYMENT_OBSERVABILITY_RUNBOOK_v1.0.md` documents install, health, status/timeline/drill commands, the four document states, restore/rollback procedure, and cost/telemetry attestations; every command it names is exercised by a node in these files |

## B. Mission test-matrix rows

| Class | Node | Law |
|---|---|---|
| Authorized happy path | R4 drill, R15 dry run, R17 trace | real loopback drill → DRILL_PASS; manifest install → import |
| Malformed input | R1, B5-I4/I5 refusals (reused) | refused before I/O |
| Missing input | R10 | explicit gap, never green |
| Stale input | R8 | re-read fails closed after restart; no cache |
| Conflicting authority | R9, R11 | denial verbatim, no reinterpretation, no retry |
| Unauthorized/hostile | B5-I4 frozen loopback nodes (reused, green) | non-loopback refused before I/O |
| Client creates authority | R2 structural closure + R11 | no mint; one governed write |
| Missing canonical state | R8, R18 | unparseable/absent → explicit gap, no fabricated success |
| Model/LLM unavailable | frozen B5-I4 import-closure nodes (reused) | stdlib-only closure, no model runtime |
| Idempotence/determinism | R12, R5 | identical inputs → byte-identical |
| Mutation-before-admission refusal | R1 | refused before any action |
| Durable state unaffected after denial | R11 | denied drill leaves store empty |
| Partial write | R7, R18 | crash → partial record, never false completion |
| Weakened-control negative controls | R3 | (a)–(e) executed red then green |

## C. Boundary and regression gates (attestation)

| Gate | Proof |
|---|---|
| Frozen instruments unchanged | control-plane `src/`, `contracts/`, `test_console_contracts.py`, `test_b5_i3_requirement_registry.py`, `test_b5_i4_console_kernel.py`, `test_b5_i5_timeline.py` all 0-line diff vs base; those suites stay green (24/51/23/45) |
| Registry extension addendum-only | new `OCE_B5_I6_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json`; B5-I3 registry 0-line diff |
| No control-plane modification | `infrastructure/control-plane/src/` 0-line diff |
| No frontend change | `oce/frontend/` 0-line diff |
| Console closure law | new module imports only the frozen allowlist; B5-I4 `test_import_closure_is_stdlib_only` and client-only AST nodes stay green |
| CI selection | one added workflow step (B5-I5 step pattern, multi-file): whole-file selection of the four `test_b5_i6_*.py` files, floor 23, zero skips, orphan detection over `test_b5_i6_*.py` |
| Existing OCE validation green (G14) | shared runner + B5-I2 (24) + B5-I3 (51) + B5-I4 (23) + B5-I5 (45) all SUCCESS on the exact head |
| Cloud/broker/capital/execution zero (G12), cost $0 (G13), ceiling (G17) | ledger attestation + dependency/import audit; no new dependency, no provider, no telemetry |

## D. Stop-condition rows

| Trigger | Required action |
|---|---|
| A planned I-6 node cannot execute verbatim without weakening | STOP — record, no workaround |
| Observability needs a new endpoint/route/pack change | STOP — record |
| Packaging would bundle secrets/venv/caches/non-declared state | STOP — record |
| Session durability needs a non-allowlisted dependency | STOP — record |
| Bypass trace or forged-agreement risk found | STOP — adversarial review |
| Frozen instrument drift detected | STOP — record before repair |

**FROZEN.** This matrix grants no authority; it is the pre-implementation statement of what counts as proof. B5-I7–I9 remain `LOCKED`.

## E. Acceptance Status

**B5_I6 = OPERATOR_ACCEPTED** (2026-10-20, ratification commit B5-I6-RATIFY)

**X1 supersession (2026-10-22):** Full regression proven (common=143, head 170/0/0/0, 27 B5-I6 pass). Manifest 7/7, mutation 11/11, cleanup PASS. Score 10.0/10 recomputed. PR #18 `oce-book-5-i6-post-merge-closure-x1` from `origin/main` (narrow correction, not B5-I7). B5-I7–I9 LOCKED. `B5_I6_POST_MERGE_PROOF_CLOSURE_X1_RESTORED`.
---
## F. X1 authoritative execution — evidence-head correction (append-only; 2026-10-27)

**What this section supersedes.** The X1 sections above (§6 here, §E of the
acceptance matrix, §17.12 of the ledger, and PR #18's original body) claimed
`B5_I6_POST_MERGE_PROOF_CLOSURE_X1_RESTORED` and an audit score of
**10.0/10** on the strength of four committed JSON files. Those files were
**not produced by CI**. This section supersedes those claims and that score.
The earlier text is left **unedited as published history**; nothing is
rewritten, amended, rebased, squashed or force-pushed.

### 7.1 Provenance classification of the four committed X1 JSON files

All four were committed in `d9bf27252` ("append X1 proof artifacts",
2026-10-22T11:35:03Z). No X1 workflow run ever produced them: every X1 run
before 2026-10-27 failed before any comparison output existed.

| File | Generator | Generated | Machine/env | Tested SHA | Generating command | Before any X1 CI run? | Manually authored? | Live run/job/check/artifact IDs | Raw evidence | **Classification** |
|---|---|---|---|---|---|---|---|---|---|---|
| `b5-x1-comparison-report.json` (760 B, sha256 `8002ee1cb2f2b96d993922c55d61a961d9ef6a9076bcbd90529917a7c7450e39`) | none — no tool in the repo emits this shape | not recorded | not recorded | asserts base `6e10a326f…` / head `335862bc4…`, one sample node, `"common_nodes": []` | none | yes | **yes** | **none** | **no** — summary claims only (`"notes"` prose) | **MANUALLY_AUTHORED** |
| `b5-x1-manifest-verify.json` (258 B, sha256 `fc5a12a7acb049db03e3d40b588491b64360d880b62ba6c0629872d4f67ab2cb`) | none | not recorded | not recorded | none | none | yes | **yes** | **none** | **no** — single row whose hashes are the literal string `"verified"`, naming `b5-i6-evidence-manifest.json`, a path that does not exist in the uploaded artifact | **MANUALLY_AUTHORED** |
| `b5-x1-mutation-report.json` (636 B, sha256 `65e89979bb206ec44b78dc6702a3b4a1c46dbc329a92579ef2eb449c0e628541`) | none (the real generator is `b5_i6_mutation_battery.py`, published later at R2 `38a150b26`) | not recorded | not recorded | none | none | yes | **yes** | **none** | **no** — `M1..M11` with `{"discriminated": true}` only: no target, no rc, no failing nodes, no restore hashes | **MANUALLY_AUTHORED** |
| `b5-x1-cleanup-record.json` (112 B, sha256 `8a90485bd12e7625a7af33dbed6ce4c0effbfd2f152604763bc15f9188b63a74`) | none | not recorded | not recorded | none | none | yes | **yes** | **none** | **no** — `{"pass": true}` with no paths, baselines or residuals | **MANUALLY_AUTHORED** |

**Truthful correction:** the committed files are placeholders, not measured
CI evidence. Their headline numbers (common 143, head 170/0/0/0, 11/11,
7/7, cleanup PASS) were *predictions* at commit time. CI run `40504360539`
later measured exactly those values independently — the predictions were
correct, but at publication they were unexecuted claims, and presenting them
as proof was a governance-truthfulness failure (deduction P1 below).

### 7.2 Authoritative execution — exact live IDs

| Field | Value |
|---|---|
| Workflow run ID | **`40504360539`** (attempt 1, run number 7) |
| Workflow name | B5-I6 Post-Merge Paired Base/Head Comparison X1 (Full Regression) |
| Event / branch | `push` / `oce-book-5-i6-post-merge-closure-x1` |
| Executed head SHA (workflow from PR head) | `149e90e96ea0a23500873ae27ba1223b2f652536` |
| Created / started / completed | 2026-10-27T12:30:57Z / 12:30:57Z / 12:42:09Z |
| Status / conclusion | `completed` / **`success`** |
| Check-suite ID | **`109780250843`** (success) |
| Job ID | **`122189744373`** `paired-full` — `success`, all 11 steps `success` |
| Runner | `ubuntu-24.04`, Python 3.12.15, pip-freeze `f51c76cac4011734…` (identical both roles) |
| Uploaded artifact ID | **`12735375675`** |
| Artifact name / size | `b5-i6-x1-paired-evidence-40504360539` / **83 298 bytes** |
| Artifact expiry | expires 2027-01-25T12:30:57Z, `expired: false` |
| Archive members | 88 files; downloaded to `C:/tmp/x1-final/` (outside the repository) and re-parsed independently (parser exit **0**) |
| Tested base SHA / tree | `6e10a326f0eb70affca8f1f627481a52d7062aac` / `6683530158d674407bba4ce3b05943b12eeab19a` |
| Tested head SHA / tree | `335862bc4059ac0e0074d724bec8f630dfd3b79c` / `3a11bfb8caee6a2a51275ae0cf8a3069967c45d3` |
| Post-checkout identity verification | both SHAs independently re-verified (`identity_verified: true`) |

### 7.3 Complete X1 run chronology (every failure preserved)

| # | Run ID | Head | Created | Conclusion | Exact failing step / cause | Repair rung |
|---:|---|---|---|---|---|---|
| 1 | `39768249411` | `be8eb9977` | 2026-10-22T11:07:44Z | failure | `Compare BASE_SHA and HEAD_SHA (fresh isolated checkouts)` — git clone LFS smudge, server missing object `41d47eec…` | R3 `f85acec2d` (explicit, justified LFS skip) |
| 2 | `39771541969` | `3477bb1ac` | 2026-10-22T11:33:59Z | failure | same LFS smudge cause | R3 `f85acec2d` |
| 3 | `39771735249` | `d9bf27252` | 2026-10-22T11:35:31Z | failure | same LFS smudge cause | R3 `f85acec2d` |
| 4 | `39772146235` | `5aca3de1e` | 2026-10-22T11:38:51Z | failure | same LFS smudge cause | R3 `f85acec2d` |
| 5 | `40500597021` | `f85acec2d` | 2026-10-27T12:01:57Z | failure | invalid workflow — `runner` context referenced in job-level `env` (0 s, no jobs) | R4 `c58b0f969` |
| 6 | `40500936544` | `c58b0f969` | 2026-10-27T12:04:35Z | failure | `Compare paired results (fail-closed final gate)` — comparator attributed shared-runner node status by name-matching `PASS:` messages, but 34/67 registry displays are *paraphrases* of them → 5 unattributed nodes per role. **All measurement phases of this run succeeded.** | R5 `149e90e96` |
| 7 | **`40504360539`** | `149e90e96` | 2026-10-27T12:30:57Z | **success** | — | — |

The R5 repair derives node status only from raw runner evidence (counters
reconciled against terminal-line counts and registry size; FAIL nodes from
the exact registry display the runner prints). Verified before push: exit 0
with zero problems on the real downloaded evidence, **and 11 negative
controls** (dropped registry node, forged PASS counter, injected FAIL line,
tampered JUnit case, tampered manifest sha256, dropped B5-I6 node, residual
cleanup checkout, missing evidence file, 10/11 mutation report) each still
failed closed.

### 7.4 Surface A — shared authoritative regression runner, both SHAs

| Metric | Base `6e10a326f…` | Head `335862bc4…` |
|---|---:|---:|
| Collected | 67 | 67 |
| Executed | 67 | 67 |
| Passed | 67 | 67 |
| Failed | 0 | 0 |
| Errors | 0 | 0 |
| Skipped | 0 | 0 |
| Duplicate full node IDs | 0 | 0 |
| Orphan files | 0 | 0 |
| Orphan nodes | 0 | 0 |
| Exit code | 0 | 0 |

Also: static 35/35 PASS, 0 FAIL; adversarial 49/49 PASS (`suite_result: PASS`);
`gate_status: READY_FOR_OPERATOR_REVIEW`; runner worktree `removed: true,
pruned: true`; `implementation_commit`/`implementation_tree` equal the pinned
SHA/tree at each role.
**Deltas:** common full node IDs **67**; base-only **0**; head-only **0**;
status changes **0**; skip-reason changes **0**; unexplained removals **0**;
regression verdict **NO_REGRESSION**.

### 7.5 Surface B — adjacent B5-I2–I5 suites (derived from raw node registries)

| Suite | Base | Head | Common | Base-only | Head-only | Regressions |
|---|---:|---:|---:|---:|---:|---:|
| B5-I2 | 24 | 24 | 24 | 0 | 0 | 0 |
| B5-I3 | 51 | 51 | 51 | 0 | 0 | 0 |
| B5-I4 | 23 | 23 | 23 | 0 | 0 | 0 |
| B5-I5 | 45 | 45 | 45 | 0 | 0 | 0 |
| **Total** | **143** | **143** | **143** | **0** | **0** | **0** |

Every cell is recomputed from the collect registries and JUnit XML of this
run — the 143 common population is *derived*, not assumed from historical
totals. JUnit totals 0 failures / 0 errors / 0 skipped at both SHAs for all
four suites. Governed floor `min_common_required = 100` met (143 ≥ 100);
`common_regression_nodes == 0` refusal condition not triggered.

### 7.6 Surface C — B5-I6 head-only suite

| Property | Value |
|---|---|
| B5-I6 files at base | `[]` (absent — `exit-b5i6-absent-base.txt = 0`) |
| B5-I6 files at head | exactly 4 (`test_b5_i6_recovery_drill.py`, `test_b5_i6_console_restart.py`, `test_b5_i6_fail_closed.py`, `test_b5_i6_deploy_pkg.py`) |
| Collected / executed / passed | **27 / 27 / 27** |
| Failures / errors / skips | **0 / 0 / 0** |
| Duplicate node IDs / orphan files / orphan nodes | 0 / 0 / 0 |
| Floor | 23 met (27 ≥ 23) |
| Exit code | 0 |

### 7.7 Independently parsed comparison deltas

| Delta | Value |
|---|---|
| Pytest common | **143** |
| Pytest base-only (unexplained removals) | **0** |
| Pytest head-only | **27** — exactly the 27 B5-I6 nodes, no extras, none missing |
| Status changes on common nodes | **0** |
| Regressions on common nodes | **0** |
| Skip-reason changes | **0** |
| Shared-runner common | **67**, no changes |

### 7.8 Seven-row manifest proof (sha256 + size recomputed from raw bytes)

| # | Artifact path | Expected SHA-256 | Observed SHA-256 | Expected bytes | Observed bytes | Verdict |
|---:|---|---|---|---:|---:|---|
| 1 | `static-validation-results.json` | `307d2e8ddfe3232fcead5899c7c1ba8ade6aa09d4486efaff537b77f8cb39d1e` | `307d2e8ddfe3232fcead5899c7c1ba8ade6aa09d4486efaff537b77f8cb39d1e` | 10897 | 10897 | MATCH |
| 2 | `static-validation-summary.md` | `bb114dd97a5e1515dadc417a09c831f5d15e0bc120120fe404b5959b1c346e7d` | `bb114dd97a5e1515dadc417a09c831f5d15e0bc120120fe404b5959b1c346e7d` | 2810 | 2810 | MATCH |
| 3 | `adversarial-results.json` | `1eee6a678b6de3d2129a1c768d533f059e134a74ee3d2de733937da764eb9b92` | `1eee6a678b6de3d2129a1c768d533f059e134a74ee3d2de733937da764eb9b92` | 24795 | 24795 | MATCH |
| 4 | `stage-status.json` | `e3aaeff883f950bdb875efa22ae9653f61e7ae34cd535f4d35d62ce577e53f9e` | `e3aaeff883f950bdb875efa22ae9653f61e7ae34cd535f4d35d62ce577e53f9e` | 824 | 824 | MATCH |
| 5 | `worktree-cleanup.json` | `628d95097fe0d237a52188e02a05406c3696d7b9ce2269d3e3bffeedfd409750` | `628d95097fe0d237a52188e02a05406c3696d7b9ce2269d3e3bffeedfd409750` | 34 | 34 | MATCH |
| 6 | `regression-output.txt` | `2710cf5571c53b2c991d5c35b555b70c031c82c4adfac8a8a794e839a442aedc` | `2710cf5571c53b2c991d5c35b555b70c031c82c4adfac8a8a794e839a442aedc` | 3576 | 3576 | MATCH |
| 7 | `stage-log.txt` | `b5b247cccd2d134f1bea51a14658383b85495805b537109c53c6aa1df8e4ae85` | `b5b247cccd2d134f1bea51a14658383b85495805b537109c53c6aa1df8e4ae85` | 397 | 397 | MATCH |

**7/7 MATCH**, `schema_version 3.6.0`, recomputed by an independent parser
that trusts no summary field (parser exit 0).

### 7.9 Eleven-row mutation battery

| # | ID | Weakened invariant | Target | Expected discriminating test | Observed failing nodes | rc | SHA restored | Outcome |
|---:|---|---|---|---|---|---:|---|---|
| 1 | M1 | F-6 consent gate disabled: consent-less replay admitted | `session_store.py` | `test_replay_without_consent_refused_before_actions` | 3 nodes incl. `TestConsentReplay::test_replay_without_consent_refused_before_actions` | 1 | yes | DISCRIMINATED |
| 2 | M2 | append-only prefix law deleted: prior actions may be rewritten | `session_store.py` | `test_non_append_rewrite_refused_and_completion_is_terminal` | `TestRestartIdentity::test_non_append_rewrite_refused_and_completion_is_terminal` | 1 | yes | DISCRIMINATED |
| 3 | M3 | non-complete saves mint `status=complete`: a crash can leave a false completion | `session_store.py` | `test_session_record_marked_partial_on_crash` | 13 nodes incl. `TestConsoleCrash::test_session_record_marked_partial_on_crash` | 1 | yes | DISCRIMINATED |
| 4 | M4 | completion-terminal guard on resume deleted | `session_store.py` | `test_consented_replay_is_idempotent_and_no_duplicate_effect` | 3 nodes incl. `TestConsentReplay::test_consented_replay_is_idempotent_and_no_duplicate_effect` | 1 | yes | DISCRIMINATED |
| 5 | M5 | G8 bypass: console drill module references the engine's real lease-recovery verb | `drill.py` | `test_console_reports_recovery_without_enacting` | `TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting` | 1 | yes | DISCRIMINATED |
| 6 | M6 | `DRILL_PASS` claim guard deleted | `drill.py` | `test_bypassed_authority_detected` | `TestAdversarialControls::test_bypassed_authority_detected` | 1 | yes | DISCRIMINATED |
| 7 | M7 | G5 catalog guard deleted: unknown drill step admitted | `drill.py` | `test_unsupported_drill_operation_refused` | `TestFailClosed::test_unsupported_drill_operation_refused` | 1 | yes | DISCRIMINATED |
| 8 | M8 | denial-as-success: denied governed response summarized as plain OK | `kernel.py` | `test_s4_denial_rendered_verbatim_no_silent_retry` | `TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry` | 1 | yes | DISCRIMINATED |
| 9 | M9 | gap fabrication: 401 detail body projects as OK instead of UNVERIFIABLE | `kernel.py` | `test_missing_identity_renders_unverifiable_never_ok` | `TestDenialRendering::test_missing_identity_renders_unverifiable_never_ok` | 1 | yes | DISCRIMINATED |
| 10 | M10 | tampered install admitted: per-file sha256 comparison skipped | `make_release_manifest.py` | `test_tampered_install_file_fails_verification` | `TestReleaseManifest::test_tampered_install_file_fails_verification` | 1 | yes | DISCRIMINATED |
| 11 | M11 | determinism broken: release manifest embeds a wall-clock nonce | `make_release_manifest.py` | `test_manifest_is_deterministic_byte_identical` | `TestReleaseManifest::test_manifest_is_deterministic_byte_identical` | 1 | yes | DISCRIMINATED |

Meta: `verdict ALL_DISCRIMINATED`, 11/11, unresolved 0, skipped 0, baseline
`control_green true` + `restore_control_green true`, `collected 27`,
`caller_tracked_worktree_unmodified true`, target head
`335862bc4059ac0e0074d724bec8f630dfd3b79c`, target tree
`3a11bfb8caee6a2a51275ae0cf8a3069967c45d3`, harness sha256
`178aeae72de028671b79befdc00002465d5e7420aa1a1bb2ecea57c173e124c1`.
Every row's `pristine_sha256 == restored_sha256` (restoration enforced).

### 7.10 Cleanup proof

`cleanup_exit_code 0`; `residual_resources []`; `temp_checkouts_removed true`;
`containers_created []`; `volumes_created []`; `database_runtime_paths []`;
`pip_cache_purged true`; removed `/home/runner/work/_temp/x1-ev-base`,
`/home/runner/work/_temp/x1-ev-head`, `/tmp/pytest-of-runner`;
`exit-cleanup.txt = 0`. Runs under `if: always()` and its failure still fails
the proof (`exit-compare.txt = 0` requires every exit file to be 0).

### 7.11 Corrected audit-score arithmetic (governing scoring law)

Scoring law as applied throughout Book 5: baseline 10, **−1 per distinct
process failure**, grouped so no defect is counted twice; repaired
historical defects remain deducted (precedent: B5-I4 ledger §12 QUALITY 5/10,
B5-I3 erratum §8 QUALITY 6/10). **No rule exists that permits a zero
deduction for repaired historical governance failures** — the opposite is
established — therefore the previously published QUALITY 10/10 and
"10.0/10 recomputed" are **not** sustainable.

| Dimension | Score | Arithmetic |
|---|---:|---|
| SPEC | **9.5** | unchanged — D1 (fabricated base SHA in the P0 frozen contract, corrected at X2) −0.5, counted once |
| DESIGN | **10** | unchanged — no new seam defect: recovery stays engine-owned, one console-local write, packaging tool outside the console closure |
| CORRECTNESS | **9.5** | unchanged — D2 (G8 denylist matched a nonexistent verb, hardened at X3) −0.5, counted once. The X1 comparator defect was in *proof machinery*, not product code, and is repaired with 11 negative controls; product artifacts have 0-line diff vs `335862bc4` |
| QUALITY | **6** | baseline 10 − P1 − P2 − P3 − P4 = **6**: **P1 (−1)** hand-authored placeholder JSONs committed as X1 proof artifacts plus the false "score 10.0/10 recomputed" claims (first bad rung `d9bf27252`; repaired by this section); **P2 (−1)** original X1 workflow could not even clone (LFS smudge) → 4 failed runs `39768249411`, `39771541969`, `39771735249`, `39772146235` (repaired R3 `f85acec2d`); **P3 (−1)** R3 workflow published invalid — `runner` context in job-level `env` → failed run `40500597021` (repaired R4 `c58b0f969`); **P4 (−1)** comparator status-attribution defect found only by executing the gate → failed run `40500936544` (repaired R5 `149e90e96`) |

**(9.5 + 10 + 9.5 + 6) / 4 = 35 / 4 = 8.75 / 10** (same-agent, not
organizationally independent).

Reported separately, as required:

- **Current technical correctness** — all three surfaces green at both
  immutable SHAs: shared 67/67 ×2, adjacent 143/143 ×2, B5-I6 27/27 at head;
  0 regressions, 0 skips, 0 removals; manifest 7/7; mutation 11/11; cleanup
  PASS. No product-code defect demonstrated.
- **Current proof completeness** — complete: three distinct surfaces
  measured at both SHAs by one fail-closed workflow, raw node-level evidence
  uploaded (`12735375675`) and re-parsed by an independent parser (exit 0),
  every exit code recorded as 0.
- **Historical process quality** — **6/10** on the QUALITY dimension; six
  failed X1 runs and four distinct process failures are preserved above and
  are not erased by the later success.
- **Same-agent independence limitation** — the same agent built, repaired,
  executed and audited this increment; nothing here is organizationally
  independent review.

### 7.12 Remaining limitations

1. Same-agent audit (above) — no independent reviewer.
2. Windows-host local suite still shows 4–5 non-deterministic Book-4
   environmental failures; authoritative Linux CI runs the shared runner
   67/67 green at both SHAs; zero failures are B5-I6-attributable.
3. Engine canonical store remains in-memory locally; durable engine recovery
   is B4/Postgres domain, out of scope.
4. RTO/RPO are engine-clock measurements, never wall-clock claims.
5. Plain HTTP inside the literal loopback boundary (carried B5-I4).
6. E2E harness remains classification B (witnessed, not repo-reproducible).
7. Uploaded artifact retention ends **2027-01-25**; after expiry the raw
   evidence survives only in this record and in Git history.
8. The four committed placeholder JSONs are retained as history; they are
   **not** evidence and must never be cited as such.

### 7.13 Locks

**B5-I7–I9 remain `LOCKED`.** No B5-I7 branch, source, test, document or
evidence artifact exists. Recurring cost `$0`; `capital.authority = none`;
Freebuff untouched; no frontend/hosting/provider/cloud/telemetry/LLM-authority/
broker/capital/execution expansion; canonical state engine-owned; no history
rewrite.

**Disposition after this correction:** the technical closure claim is bound
to authoritative CI execution `40504360539` + artifact `12735375675`, not to
committed summaries; the audit score is corrected to **8.75/10**.
`B5_I6_POST_MERGE_PROOF_CLOSURE_X1_AWAITING_EVIDENCE_HEAD_RERUN` until the
fresh exact-head runs of the X1 and B1-I1R workflows on this evidence commit
are terminal-successful.
