# OCE Golden System
## B5-I8 — Independent Audit Implementation Evidence — v1.0

**Document ID:** OCE-B5-I8-EVIDENCE-002  
**Implementation head:** `e999a4a342f8a2ebb8f99045206d67d04d6fcbbf` (tree `82fa85a020c2ae61afd54fdf5066fa08249e86af`) · **Base:** `e999a4a342f8a2ebb8f99045206d67d04d6fcbbf`  
**Bundles:** `OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json`, `OCE_B5_I8_MUTATION_RESULTS_v1.0.json`  
**Stage:** `AUTHORIZED_STAGE=B5-I8-IMPLEMENTATION` · `MERGE_AUTHORIZED=false` · `B5-I9 = LOCKED` · Book 6 `UNAUTHORIZED` · cost `$0` · `capital.authority = none`

---

## 1. What was built

| Path | Kind | Purpose |
|---|---|---|
| `infrastructure/control-plane/tests/test_b5_i8_e2e.py` | test | 4 frozen E2E nodes |
| `infrastructure/control-plane/tests/test_b5_i8_adversarial.py` | test | 10 frozen adversarial nodes |
| `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py` | test | 8 frozen audit/gate nodes, incl. the verbatim `G16` node |
| `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py` | test | 10 frozen usability/measurement nodes |
| `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py` | test | `EL01`–`EL08`, two-sided |
| `infrastructure/control-plane/tests/b5_i8_audit_support.py` | test-only helper | deterministic fixtures, protocol execution, verdict recomputation |
| `infrastructure/control-plane/scripts/b5_i8_build_evidence.py` | tooling | executes the protocol, writes the bundle |
| `infrastructure/control-plane/scripts/b5_i8_mutation_battery.py` | tooling | 12 mutations, byte-exact restore |
| `.github/workflows/b5-i8-audit-validation.yml` | CI | fail-closed selection of the whole 40-node surface |
| `docs/.../OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json` | evidence | machine-readable audit bundle |
| `docs/.../OCE_B5_I8_MUTATION_RESULTS_v1.0.json` | evidence | mutation battery record |

## 2. Arithmetic and closure

| Dimension | Frozen | Observed |
|---|---|---|
| Requirements | 55 unique | 55 / 55 |
| Bindings | 40 test / 7 attestation / 3 static / 5 deferred | unchanged (`requirement_set`) |
| Planned nodes | 40 in 5 files | 40 collected / 40 executed / 40 passed |
| Failure classes | 18 | 18 provoked and asserted |
| Mutations | floor 12 | 12 executed, 12 discriminated |
| Adjacent population | floor 189 | 189+ over the ten pre-existing B5 files |
| Ledger prefix | `83a40ac7…` / 191950 B | recomputed identically |

## 3. E2E results

The governed path is re-executed over the real `oce_console.panel` / `kernel` / `drill` surfaces:
one read per declared surface in the frozen order, canonical state nowhere in the client,
`non_authoritative: true`, a render equal to its own digest, restart identity reproduced in a
fresh interpreter, drill disposition reproduced under the frozen three-field mask, and a
governed denial rendered verbatim with no green summary.

## 4. Adversarial results and the 18 classes

`F01` unreachable · `F02` denial · `F03` malformed · `F04` partial · `F05` inconsistent ·
`F06` stale · `F07` unknown · `F08` oversized payload · `F09` collection width ·
`F10` nondeterminism · `F11` secret leakage · `F12` non-loopback · `F13` write authority ·
`F14` unsupported route · `F15` client divergence · `F16` accessibility/comprehension ·
`F17` false claim/self-reference · `F18` external dependency.

Each class is provoked against the real surface and requires its named refusal or containment;
the laws are two-sided, so a law that stopped firing is red.

## 5. Usability and G16

Protocol executed: 4/4 tasks, zero errors. `G16` remains **OPEN** — no organizationally independent operator: the protocol was executed by the B5-I8 implementer (single operator, non-blind; B5I8-DF05 unresolved).

## 6. Measurements

| Measure | Value | Unit |
|---|---|---|
| `tasks_defined` | 4 | tasks |
| `tasks_completed` | 4 | tasks |
| `task_errors` | 0 | errors |
| `navigation_steps_total` | 10 | governed reads |
| `time_to_first_useful_state_ms` | 122.751 | ms |

Every value carries its command, tested SHA, environment and artifact. No estimate is promoted.

## 7. Evidence laws and EL09

`EL01`–`EL08` run on the committed bundle and on a falsified copy (each law must go red). The
historical ledger row still begins with its 191950-byte prefix `83a40ac7…`; the twelve immutable
non-ledger rows of the superseding manifest still match their committed bytes exactly, including
the whole-file workflow row B5-I8 deliberately did not touch.

## 8. Mutation battery

| ID | Law weakened | Target | Discriminating node | Verdict |
|---|---|---|---|---|
| `M01` | client is not an authority | `infrastructure/console/src/oce_console/panel.py` | `TestAuthorityMinting::test_client_cannot_mint_identity_or_grant` | DISCRIMINATED |
| `M02` | unknown is not zero | `infrastructure/console/src/oce_console/panel.py` | `TestTruthCollapse::test_unknown_never_renders_zero` | DISCRIMINATED |
| `M03` | partial is not success | `infrastructure/console/src/oce_console/panel.py` | `TestTruthCollapse::test_partial_never_renders_success` | DISCRIMINATED |
| `M04` | denied is observable | `infrastructure/console/src/oce_console/panel.py` | `TestEndToEndPath::test_denial_path_rendered_verbatim_end_to_end` | DISCRIMINATED |
| `M05` | loopback-only transport | `infrastructure/console/src/oce_console/transport.py` | `TestTransport::test_non_loopback_request_fail_closed` | DISCRIMINATED |
| `M06` | the client has no write path in the read surfaces | `infrastructure/console/src/oce_console/transport.py` | `TestAuthorityMinting::test_client_cannot_mint_identity_or_grant` | DISCRIMINATED |
| `M07` | unsupported refused before side effect | `infrastructure/console/src/oce_console/transport.py` | `TestTransport::test_unsupported_route_refused_before_side_effect` | DISCRIMINATED |
| `M08` | recursive redaction | `infrastructure/console/src/oce_console/panel.py` | `TestRedaction::test_secret_material_absent_from_audit_output` | DISCRIMINATED |
| `M09` | bounded collection width | `infrastructure/console/src/oce_console/panel.py` | `TestBounds::test_oversized_input_refused_within_bounds` | DISCRIMINATED |
| `M10` | deterministic ordering | `infrastructure/console/src/oce_console/panel.py` | `TestDeterminism::test_adversarial_case_ordering_deterministic` | DISCRIMINATED |
| `M11` | the verdict is recomputed, not asserted | `docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json` | `TestAuditVerdict::test_verdict_recomputable_from_committed_evidence` | DISCRIMINATED |
| `M12` | accessibility semantics are checked | `docs/oce-golden-system/OCE_B5_I8_AUDIT_EVIDENCE_v1.0.json` | `TestAccessibility::test_accessibility_semantics_verified` | DISCRIMINATED |

Restoration byte-exact for every row; tracked worktree clean after the battery; confirming
rerun `40 passed in 8.66s` (exit 0).

## 9. Defects found and repaired

| ID | Defect | Class | Repair |
|---|---|---|---|
| `D-CI-1` | The P0 packet places the selection step in `.github/workflows/b1-i1r-validation.yml`, but B5-I7's frozen `EL09` pins that file as a whole-file immutable row: any added step turns `TestEL09` red (demonstrated, 26/27). | governance conflict | The step lives in a dedicated additive workflow `b5-i8-audit-validation.yml`; the pinned file stays byte-identical. The letter of the P0 clause is not met; the conflict is disclosed rather than repaired by weakening `EL09`. |
| `D1` | The first battery harness crashed on a node-id split and left `panel.py` mutated. | tooling | Restored from git, added a guaranteed `try/finally` restore, re-verified the law suite. |
| `D2` | `G15` asserted the totals of the run that produced its own document (self-reference). | test | The totals assertion was removed; the authoritative 40/40 witness is the CI selection proof. Disclosed. |
| `D3` | The forbidden-phrase detector flagged a quotation of the prohibition inside `F17`. | test | The detector is negation-aware and still flags an asserted claim (two-sided). |

## 10. Limitations

- `SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`; `B5I8-DF05` remains open.
- `G16` remains `OPEN`: no independent operator executed the protocol.
- The usability sample is one operator, non-blind, on one machine; timings are observations.
- `refs/pull/21/merge` (`7dc1248e…`) was pruned after PR #21 merged; the exemption is recorded.
- The E2E proof drives the real client surfaces in-process rather than a live stack, so `F01` is
  proved through the transport refusal path, not a real outage.
- The mutation battery mutates production client files in the working tree and restores them
  byte-exactly; it does not run in CI, so its reproducibility is the committed harness.

## 11. Same-agent audit score

`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT` — SPEC 8.5 · DESIGN 8.5 · CORRECTNESS 8.0 · QUALITY 8.0 → **8.25/10**.

Deductions: `D-CI-1` (the named CI file could not be used); `G15` self-reference removed (`D2`);
the battery is not exercised in CI; the E2E proof is in-process rather than a live stack; a shared
support module couples the five files.

## 12. Accounting

`B5-I8 = IMPLEMENTED — AWAITING OPERATOR REVIEW` · `MERGE_AUTHORIZED = false` · `B5-I9 = LOCKED` ·
Book 6 `UNAUTHORIZED` · post-Book-6 evaluation `UNSTARTED` · web view `ABSENT` · cost `$0` ·
`capital.authority = none` · Freebuff untouched.

## 13. Exact-head CI identity — head `b3e761e33948a4a7e763ac2bcfef5a8d1dadf910`

Downloaded and parsed from the raw artifacts, not read from the badge.

| Field | Value |
|---|---|
| `head_sha` | `b3e761e33948a4a7e763ac2bcfef5a8d1dadf910` |
| `head_tree` | `12fcec2edcff22337de1de33dfbebdb6dda9a472` |
| `pr_head_sha` | `b3e761e33948a4a7e763ac2bcfef5a8d1dadf910` |
| `tested_tree` | `12fcec2edcff22337de1de33dfbebdb6dda9a472` |
| `merge_ref_sha` | `c2990c8cdbd9a221566dec6de8de6e7bc016d047` |
| `merge_ref_first_parent` | `e999a4a342f8a2ebb8f99045206d67d04d6fcbbf` |
| `merge_ref_second_parent` | `b3e761e33948a4a7e763ac2bcfef5a8d1dadf910` |
| `merge_ref_tree` | `12fcec2edcff22337de1de33dfbebdb6dda9a472` |
| `merge_ref_tree_equals_tested_tree` | `true` |
| `b5_i8_run_id` | `42061931200` |
| `b5_i8_check_suite_id` | `113977456198` |
| `b5_i8_job_id` | `127365645961` |
| `b5_i8_conclusion` | `success` |
| `b5_i8_event` | `pull_request` |
| `b1_i1r_run_id` | `42061931573` |
| `b1_i1r_check_suite_id` | `113977457536` |
| `b1_i1r_job_id` | `127365646581` |
| `b1_i1r_conclusion` | `success` |
| `artifact_id` | `13432118604` |
| `artifact_name` | `b5-i8-evidence-c3ae4aedc154` |
| `artifact_size_bytes` | `5071` |
| `artifact_expires_at` | `2026-12-05T16:12:36Z` |
| `collected` | `40` |
| `executed` | `40` |
| `passed` | `40` |
| `failures` | `0` |
| `errors` | `0` |
| `skipped` | `0` |
| `unique_nodes` | `40` |
| `orphan_files` | `none` |
| `node_closure` | `true` |
| `adjacent_population` | `{'returncode': 0, 'counts': {'test_b5_i2_mutation_harness.py': 16, 'test_b5_i3_requirement_registry.py': 51, 'test_b5_i4_console_kernel.py': 23, 'test_b5_i5_timeline.py': 45, 'test_b5_i6_console_restart.py': 5, 'test_b5_i6_deploy_pkg.py': 9, 'test_b5_i6_fail_closed.py': 4, 'test_b5_i6_recovery_drill.py': 9, 'test_b5_i7_governed_change.py': 12, 'test_b5_i7_evidence_laws.py': 15}, 'total': 189}` |
| `manifest_result` | `immutable rows exact; ledger prefix 191950 B = 83a40ac7…` |
| `mutation_result` | `12/12 DISCRIMINATED; byte-exact restore; tracked tree clean` |
| `cleanup_result` | `workspace cleaned in the workflow; no residue asserted` |
| `local_pre_existing_failures` | `32` |
| `local_pre_existing_scope` | `test_b4_startup_gate/​test_b4_cxr7/​test_b4_cxr6/​test_local_lifecycle (Windows host; 33 on base)` |

The selection proof records `collected=executed=passed=40`, `failures=errors=skipped=0`,
`unique_nodes=40`, `node_closure=true`, no orphan files, the five planned files, `pr_head_sha`,
the tested tree and both merge-ref parents.

## 14. Shared-support audit (appended 2026-11-06)

`b5_i8_audit_support.py` is shared by all five frozen files. Closure audit of every
helper used by two or more files:

| Helper | Class | Why it cannot create false agreement |
|---|---|---|
| `frozen_message`, `panel_document`, `protocol_tasks`, `accessibility_checks` | input fixture only | fixed inputs; they carry no expectation and cannot pass a node |
| `recompute_verdict`, `verdict_digest`, `gates`, `digest_obj` | independent oracle | recompute from the registry and mutation document; the bundle's own verdict text is compared against them, never used as input |
| `git`, `collect_adjacent`, `collected_nodes` | production adapter | shell out to real `git`/`pytest`; a defect shows up as a collection mismatch, and the CI selection step recomputes the same closure independently in `b5-i8-registry-proof.json` |
| `evidence`, `registry`, `mutations`, `ci_identity`, `load` | evidence parser | pure readers of committed bytes; they never synthesize an expected value |
| `forbidden_hits`, `workflow_text`, `workflow_b5_i8_step` | assertion helper | static text assertions with two-sided controls; they cannot make a runtime proof pass |

Controls against circular agreement:

- `M01`–`M12` mutate **production** panel/transport files, not the support module, so a
  shared helper cannot satisfy them: the battery's red nodes come from the audited
  surface.
- The G15 totals owner was moved off the bundle onto the committed CI identity record
  and the registry (§7 of this record, defect `D2`), so a defective bundle generator
  cannot make its own totals pass.
- The 40-node non-vacuity audit names each node's target, oracle and negative control
  (`OCE_B5_I8_NODE_NONVACUITY_AUDIT_v1.0.json`); a node with no reachable target or no
  discriminating control cannot be recorded as `NON_VACUOUS`.
- No authority decision lives in the support module: it computes, it does not decide a
  gate. Gate language and `G16` status are recomputed by `gates()` from the recorded
  attestation class.

Residual coupling (disclosed): the five files share one module, so a defect in a parser
helper would surface as several red nodes at once. That is a blast-radius disclosure,
not a circular-agreement path, because no helper both produces and checks the same
value. The same-agent score in §11 carries this as a QUALITY deduction.
