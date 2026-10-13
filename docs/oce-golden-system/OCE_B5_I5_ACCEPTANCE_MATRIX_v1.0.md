# OCE B5-I5 Acceptance Matrix — v1.0

**Document ID:** OCE-B5-I5-ACCEPTANCE-001
**Version:** 1.0 — FROZEN at P0 under `AUTHORIZED_STAGE=B5-I5` (before any implementation result exists)
**Scope contract:** `OCE_B5_I5_GAP_AND_SCOPE_CONTRACT_v1.0.md`
**Gate to prove:** plan §7 "Release candidate evidence complete"; charter §12 I-4 "S-2 tests pass; timeline reproducible", I-5 "G9 binding audit passes; playbook runs bounded", I-6(B5-I5) "restart-identity / engine-owned recovery reporting / duplicate-effect check / negative controls recorded"

Every row is executable: a test node (selected whole-file by the authoritative workflow with a frozen floor) or a named attestation/binding audit. All nodes live in `infrastructure/control-plane/tests/test_b5_i5_timeline.py` unless noted.

## A. Requirement-to-node map (I-4/I-5/I-6 discharges)

| Req | Charter anchor | Frozen node | Two-sided proof shape |
|---|---|---|---|
| R1 (I-4) governed submission | §12 I-4; §11 G4 | `TestGovernedSubmit::test_submit_representative_job_is_one_governed_operation` | Real loopback stack: console `submit` issues exactly one `POST /api/jobs` bound to `ControlPlaneAPI.submit_job`; the returned envelope equals the control plane's own `submit_job` response verbatim; weakened control (submit bypasses the governed op / fabricates success) turns the node red |
| R2 (I-4) catalog-bounded | §12 I-4 non-goal; §11 G5 | `TestRefusals::test_out_of_catalog_job_type_refused_before_io` | `job_type` outside `supported_job_types()` refused fail-closed before any I/O (exploding opener); weakened catalog guard admits it → red |
| R3 (I-4) dual-clock timeline | §12 I-4; §9 reconciliation | `TestDualClockTimeline::test_s2_transitions_rendered_with_both_clocks` (frozen planned node, §5.1 supersession) | Real stack drives a job `pending→leased→running→succeeded`; timeline sorted on event-time with knowledge-time annotations; both clocks present and distinct; mutated projection (drop knowledge-time / fabricate order) turns the node red |
| R4 (I-4) timeline reproducible | §12 I-4 gate | `TestDualClockTimeline::test_timeline_is_reproducible` | Two renders of identical observations are byte-identical |
| R5 (I-4) F-3 failure envelope | B5-I3 registry F-3; §9 completion/failure | `TestPartialTask::test_failure_envelope_rendered_without_false_success` (frozen planned node, §5.1 supersession) | A failed/partial task renders its `failure_envelope` verbatim and is never summarized `succeeded`; fabricated-success control turns the node red |
| R6 (I-5) evidence binding G9 | §12 I-5; §11 G9 | `TestEvidenceBinding::test_timeline_binds_to_engine_manifest_digest` | Timeline references the engine's own evidence record; binding audits the `EvidenceBuilder.outer_digest` against the operation/commit; re-hashed manifest must match, a forged digest turns the node red |
| R7 (I-5) bounded playbook G5 | §12 I-5 | `TestDrillSession::test_playbook_runs_bounded` | Versioned playbook executes within its declared step bound; unknown/over-bound step refused before side effects |
| R8 (I-6) restart-identity G6 | §12 I-6; §9 restart | `TestRestartIdentity::test_restart_rereads_identical_authoritative_state` | A fresh `ControlPlane` + re-read yields an identical authoritative view; no console state survives restart; console crash cannot alter governed state |
| R9 (I-6) engine-owned recovery G8 | §12 I-6; §9 recovery | `TestDrillSession::test_recovery_is_engine_owned_console_enacts_nothing` | Drill observes engine recovery (lease expiry → requeue); the console performs no recovery/requeue write; console-owned-recovery control turns the node red |
| R10 (I-6) duplicate-effect S-3 | §12 I-6; §9 idempotent replay | `TestDrillSession::test_duplicate_effect_check_after_worker_loss` | After worker loss + engine recovery, `verify_no_duplicate_effects()` holds and the drill report states the no-duplicate-effect result |
| R11 (I-6) denial verbatim S-4 | §12 I-6; §9 admission/refusal | `TestGovernedSubmit::test_denied_submit_rendered_verbatim_not_retried` | A tampered grant yields the governed denial envelope verbatim; the fetch happens exactly once (no silent retry); never summarized OK |
| R12 (I-6) drill report DRILL_PASS | §12 I-6 evidence | `TestDrillSession::test_drill_report_disposition_drill_pass` | After worker loss + engine recovery + duplicate-effect check, the drill report carries disposition `DRILL_PASS` |
| R13 client-only AST closure | §11 G3; §5 authority law | `TestClientOnlyReads::test_new_modules_import_no_store_and_are_stdlib_only` | AST proof: the new console modules import no `oce_control`/store/model module and only stdlib + the pack (data); behavioral: submit/timeline touch no store object |
| R14 session record schema | §8.1 session records | `TestDrillSession::test_session_record_is_append_only_and_schema_valid` | Session record `{session_id, playbook_version, actions[], drill_report_ref}` validates against its frozen schema and is append-only |

## B. Mission test-matrix rows

| Class | Node | Law |
|---|---|---|
| Authorized happy path | `TestGovernedSubmit`, `TestDualClockTimeline` | real loopback submit → timeline |
| Malformed input | `TestRefusals` | missing fields / oversize payload / malformed identity refused before I/O |
| Missing input | `TestGovernedSubmit` (401/403) | missing/invalid grant → denial or 401 detail rendered verbatim, never fabricated |
| Stale input | `TestRestartIdentity` | re-read reflects later truth; no cache |
| Conflicting authority | `TestGovernedSubmit::test_denied_submit_rendered_verbatim_not_retried` | denial envelope verbatim, no reinterpretation |
| Unauthorized/hostile | B5-I4 reuse + `TestRefusals` | non-loopback base URL refused before I/O (loopback guard reused) |
| Client creates authority | `TestClientOnlyReads`, `TestGovernedSubmit` | no mint; grant/actor verbatim; GET/POST surface contract-scoped |
| Missing canonical state | `TestPartialTask` | unparseable/absent → explicit gap, no fabricated success |
| Model/LLM unavailable | `TestClientOnlyReads` | import closure has no model runtime |
| Idempotence/determinism | `TestDualClockTimeline::test_timeline_is_reproducible` | identical inputs → byte-identical |
| Mutation-before-admission refusal | `TestRefusals` | contract-validated before the governed op is called |
| Durable state unaffected after denial | `TestGovernedSubmit` | denied submit leaves job store empty |
| Weakened-control negative controls | `TestNegativeControls` | (a) submit bypass, (b) fabricated timeline transition, (c) weakened catalog guard, (d) console-owned recovery — each executed red then green |

## C. Boundary and regression gates (attestation)

| Gate | Proof |
|---|---|
| Frozen B5-I2/I3/I4 instruments unchanged | control-plane `src/`, `contracts/`, `test_console_contracts.py`, `test_b5_i3_requirement_registry.py`, `test_b5_i4_console_kernel.py` all 0-line diff vs base; B5-I4 suite stays green (23) |
| Registry extension addendum-only | new `OCE_B5_I5_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` binds S-2/F-3 executed nodes; B5-I3 registry 0-line diff |
| No control-plane modification | `infrastructure/control-plane/src/` 0-line diff |
| No frontend change | `oce/frontend/` 0-line diff |
| CI selection | one added workflow step (B5-I4-R3 pattern), whole-file, floor 22, zero skips, orphan detection over `test_b5_i5_*.py` |
| Existing OCE validation green (G14) | shared runner + B5-I2 (24) + B5-I3 (51) + B5-I4 (23) all SUCCESS on the exact head |
| Cloud/broker/capital/execution zero (G12), cost $0 (G13), ceiling (G17) | ledger attestation + dependency/import audit |

## D. Stop-condition rows

| Trigger | Required action |
|---|---|
| `jobs.submit` cannot bind to the existing governed operation | STOP — record, no workaround |
| Timeline needs a new engine field/endpoint | STOP — record |
| Evidence cannot anchor to operation/commit | STOP — record |
| Any write/recovery enactment needed beyond the one governed submit | STOP — I-6 completion/B5-I6 territory |
| Frozen instrument drift detected | STOP — record before repair |

**FROZEN.** This matrix grants no authority; it is the pre-implementation statement of what counts as proof. B5-I6–I9 remain `LOCKED`.
