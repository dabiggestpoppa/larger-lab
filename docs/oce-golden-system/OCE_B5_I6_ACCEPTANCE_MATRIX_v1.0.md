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

**X1 supersession (2026-10-22):** `B5_I6_POST_MERGE_PROOF_CLOSURE_RESTORED` superseded by `B5_I6_POST_MERGE_PROOF_CLOSURE_INCOMPLETE`. PR #17 closure tested only 4 B5-I6 files (common=[]); full regression, manifest 7/7, mutation 11/11, cleanup, and score recalculation not proven. Corrective X1 branch from `origin/main` required (not B5-I7). B5-I7–I9 LOCKED.
