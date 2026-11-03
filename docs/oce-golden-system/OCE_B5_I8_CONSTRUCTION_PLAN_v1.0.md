# OCE Golden System
## B5-I8 — Construction Plan (P0) — v1.0

**Document ID:** OCE-B5-I8-PLAN-001
**Version:** 1.0
**Status:** `P0_DRAFT_FOR_OPERATOR_REVIEW` — no rung beyond P0 is authorized.
**Stage:** `AUTHORIZED_STAGE=B5-I8-P0` · Base `7393228dd4b21be9440785204ea9e640800d5d95`
**Contract:** `OCE_B5_I8_IMPLEMENTATION_CONTRACT_v1.0.md` · **Registry:** `OCE-B5-I8-REGISTRY-001` (55) · **Failure plan:** `OCE_B5_I8_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md` (18 classes, 12 mutations)

---

## 1. Ladder

Each rung is a separate authorization decision by the operator. Nothing below P0 exists yet.

| Rung | Purpose | Allowed files | Forbidden files | Tests required before commit | Exit gate | Evidence output | Stop |
|---|---|---|---|---|---|---|---|
| **P0** (this) | Freeze stage identity, scope, registry, failure taxonomy, construction ladder, acceptance matrix | the five `docs/oce-golden-system/OCE_B5_I8_*` files + ledger append | everything else | none (planning) | deterministic P0 validator clean; zero `PASS` claims | this packet + draft PR | `STOP-9` if scope exceeds authority |
| **R1** | Create the audit skeleton: five planned test files, collection wired, `G16` node id verbatim, no assertions weakened | `infrastructure/control-plane/tests/test_b5_i8_*.py` | production, console, contracts, frontend, workflows | focused collection == 40; every node present by exact id | 40 nodes collected, 0 skipped, 0 xfail | launch record (no artifact schema yet) | `STOP-5` if the frozen node id cannot be created verbatim |
| **R2** | E2E + authority/state-boundary proofs | same five files | production | `test_b5_i8_e2e.py` green; authority-minting node green and able to go red | 4 E2E + 10 adversarial nodes green | JUnit + collect | `STOP-6` on any bypass |
| **R3** | Evidence audit + `G16` usability protocol execution | same five files + `docs/.../OCE_B5_I8_USABILITY_PROTOCOL_AND_RESULTS_v1.0.md` | production; any prior-stage document | evidence audit green incl. citation resolution; usability tasks executed and recorded | `G16` evidence bundle complete with human attestation and explicit limitation labels | usability protocol + results + accessibility findings | `STOP-2` if `G16` needs the web view; `STOP-7` on untraceable value |
| **R4** | Measurements + evidence laws `EL01`–`EL08` two-sided | same five files | production | 8 laws green on real evidence and red on a falsified copy | 40/40 focused nodes, zero skip/fail/error, unique ids | JUnit + collect + law output | `STOP-7` |
| **R5** | Mutation battery (floor 12) | `infrastructure/control-plane/scripts/b5_i8_mutation_battery.py` + results JSON | production | 12/12 mutations RED, 12 distinct hashes, byte-exact restoration | every mutation discriminates its named node | `OCE_B5_I8_MUTATION_RESULTS_v1.0.json` | non-discriminating mutation ⇒ FAIL |
| **R6** | One additive CI selection step + manifest + cleanup | `.github/workflows/b1-i1r-validation.yml` (additive only) + evidence docs | any non-additive workflow change | exact-head run with whole-file selection and floor 40 | parsed artifact: 40 nodes, zeros in fail/error/skip, manifest rows recompute, cleanup clean | artifact `b1-i1r-evidence-<run_id>` | `STOP-1` if a workflow change beyond additive is needed |
| **EVIDENCE** | Measured evidence, boundaries, ledger append | docs + ledger | production | full adjacent population green at both ends; common population > 0 | ledger section with observed SHAs/run ids only | evidence record | `STOP-7` |
| **RATIFY** | Operator ratification (operator only) | ratification record | production | every mandatory gate earned | operator decision | ratification record | any unearned gate ⇒ HOLD |

The ladder is **audit-shaped**: no rung adds product behavior. If a rung appears to need production code, the stage has discovered a defect that belongs to a separate, freshly authorized repair stage — not to B5-I8.

## 2. Authority and non-goals

- May not create the web view, its tests, a stub, or a "preview" (`B5I8-R03`, `B5I8-DF01`).
- May not modify `infrastructure/console/**`, `infrastructure/control-plane/src/**`, `contracts/**`, `oce/frontend`, or any existing test file.
- May not decide reusable extraction, author correction ADRs, or draft the Book 6 contract (`B5-I9`).
- May not introduce an endpoint, a provider, telemetry, hosting, or any billable dependency.
- May not declare `G16` met without recorded protocol results.

## 3. Planned node inventory (40, exact)

| # | File | Node | Requirement |
|---|---|---|---|
| 1 | `test_b5_i8_e2e.py` | `TestEndToEndPath::test_full_governed_path_reexecuted_from_frozen_message` | `B5I8-R08` |
| 2 | `test_b5_i8_e2e.py` | `TestEndToEndPath::test_restart_preserves_governed_state_identity` | `B5I8-R09` |
| 3 | `test_b5_i8_e2e.py` | `TestEndToEndPath::test_drill_path_reproduces_recorded_disposition` | `B5I8-R10` |
| 4 | `test_b5_i8_e2e.py` | `TestEndToEndPath::test_denial_path_rendered_verbatim_end_to_end` | `B5I8-R11` |
| 5 | `test_b5_i8_adversarial.py` | `TestAuthorityMinting::test_client_cannot_mint_identity_or_grant` | `B5I8-R12` |
| 6 | `test_b5_i8_adversarial.py` | `TestForgedState::test_forged_client_state_refused_before_effect` | `B5I8-R13` |
| 7 | `test_b5_i8_adversarial.py` | `TestTruthCollapse::test_unknown_never_renders_zero` | `B5I8-R14` |
| 8 | `test_b5_i8_adversarial.py` | `TestTruthCollapse::test_partial_never_renders_success` | `B5I8-R15` |
| 9 | `test_b5_i8_adversarial.py` | `TestTruthCollapse::test_stale_state_never_renders_green` | `B5I8-R16` |
| 10 | `test_b5_i8_adversarial.py` | `TestTransport::test_non_loopback_request_fail_closed` | `B5I8-R17` |
| 11 | `test_b5_i8_adversarial.py` | `TestTransport::test_unsupported_route_refused_before_side_effect` | `B5I8-R18` |
| 12 | `test_b5_i8_adversarial.py` | `TestRedaction::test_secret_material_absent_from_audit_output` | `B5I8-R19` |
| 13 | `test_b5_i8_adversarial.py` | `TestBounds::test_oversized_input_refused_within_bounds` | `B5I8-R20` |
| 14 | `test_b5_i8_adversarial.py` | `TestDeterminism::test_adversarial_case_ordering_deterministic` | `B5I8-R21` |
| 15 | `test_b5_i8_independent_audit.py` | `TestUsabilityProtocol::test_accessibility_and_usability_verified` **(frozen `G16` id — verbatim)** | `B5I8-R39` |
| 16 | `test_b5_i8_independent_audit.py` | `TestEvidenceAudit::test_prior_stage_citations_resolve_to_commits` | `B5I8-R29` |
| 17 | `test_b5_i8_independent_audit.py` | `TestEvidenceAudit::test_run_and_artifact_ids_resolve_to_raw_evidence` | `B5I8-R30` |
| 18 | `test_b5_i8_independent_audit.py` | `TestEvidenceAudit::test_no_all_green_claim_while_gate_pending` | `B5I8-R31` |
| 19 | `test_b5_i8_independent_audit.py` | `TestEvidenceAudit::test_manifest_rows_recompute_over_committed_bytes` | `B5I8-R33` |
| 20 | `test_b5_i8_independent_audit.py` | `TestAuditVerdict::test_verdict_recomputable_from_committed_evidence` | `B5I8-R34` |
| 21 | `test_b5_i8_independent_audit.py` | `TestGateClosure::test_g14_adjacent_population_stays_green` | `B5I8-R40` |
| 22 | `test_b5_i8_independent_audit.py` | `TestGateClosure::test_g15_mutation_controls_discriminate` | `B5I8-R41` |
| 23 | `test_b5_i8_usability_measurements.py` | `TestUsabilityProtocolExecution::test_protocol_tasks_defined_and_executed` | `B5I8-R22` |
| 24 | `test_b5_i8_usability_measurements.py` | `TestComprehension::test_state_comprehension_recorded` | `B5I8-R23` |
| 25 | `test_b5_i8_usability_measurements.py` | `TestComprehension::test_refusal_comprehension_recorded` | `B5I8-R24` |
| 26 | `test_b5_i8_usability_measurements.py` | `TestComprehension::test_recovery_comprehension_recorded` | `B5I8-R25` |
| 27 | `test_b5_i8_usability_measurements.py` | `TestComprehension::test_unknown_and_partial_recognized` | `B5I8-R26` |
| 28 | `test_b5_i8_usability_measurements.py` | `TestAccessibility::test_accessibility_semantics_verified` | `B5I8-R27` |
| 29 | `test_b5_i8_usability_measurements.py` | `TestMeasurements::test_time_to_first_useful_state_measured` | `B5I8-R35` |
| 30 | `test_b5_i8_usability_measurements.py` | `TestMeasurements::test_navigation_steps_measured` | `B5I8-R36` |
| 31 | `test_b5_i8_usability_measurements.py` | `TestMeasurements::test_task_completion_and_error_measured` | `B5I8-R37` |
| 32 | `test_b5_i8_usability_measurements.py` | `TestMeasurements::test_audit_replay_is_deterministic` | `B5I8-R38` |
| 33 | `test_b5_i8_evidence_laws.py` | `TestEL01::test_no_unverified_sha_recorded_as_fact` | `B5I8-EL01` |
| 34 | `test_b5_i8_evidence_laws.py` | `TestEL02::test_no_run_or_artifact_id_recorded_before_existence` | `B5I8-EL02` |
| 35 | `test_b5_i8_evidence_laws.py` | `TestEL03::test_planned_totals_labeled_expected` | `B5I8-EL03` |
| 36 | `test_b5_i8_evidence_laws.py` | `TestEL04::test_observed_totals_bound_to_parsed_raw_artifact` | `B5I8-EL04` |
| 37 | `test_b5_i8_evidence_laws.py` | `TestEL05::test_human_evidence_labeled_non_blind_not_independent` | `B5I8-EL05` |
| 38 | `test_b5_i8_evidence_laws.py` | `TestEL06::test_no_all_gates_passed_language_while_gate_pending` | `B5I8-EL06` |
| 39 | `test_b5_i8_evidence_laws.py` | `TestEL07::test_audit_verdict_recomputable_not_free_text` | `B5I8-EL07` |
| 40 | `test_b5_i8_evidence_laws.py` | `TestEL08::test_no_evidence_value_untraceable_to_raw_source` | `B5I8-EL08` |

Arithmetic: 4 + 10 + 8 + 10 + 8 = **40**. Focused floor **40**. Collections must equal execution; ids unique; no orphan file; no orphan registry node; zero skip/xfail.

## 4. Adjacent regression population (recomputed, not inherited)

`OBSERVED` during this P0 on base `7393228d`:

```
python -m pytest infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py \
  test_b5_i3_requirement_registry.py test_b5_i4_console_kernel.py test_b5_i5_timeline.py \
  test_b5_i6_console_restart.py test_b5_i6_deploy_pkg.py test_b5_i6_fail_closed.py \
  test_b5_i6_recovery_drill.py test_b5_i7_governed_change.py test_b5_i7_evidence_laws.py \
  --collect-only -q
=> 189 tests collected
```

Ten pre-existing B5 files, **189** nodes. The inherited 186 came from a different, nine-file selection at the B5-I7 stage; it is **not** used here. Adjacent floor **189** (`FLOOR`), base/head common population required > 0, `common_nodes == 0 => FAIL`.

## 5. Evidence architecture

| Element | Frozen definition |
|---|---|
| Implementation head | the commit carrying the last implementation change (R6), named after observation |
| Evidence head | the commit carrying the evidence documents and ledger append, distinct from the implementation head |
| Merge-ref identity | GitHub `pull_request` merge ref; verified by its tree and by the second parent equalling the evidence head |
| Post-merge truth | recorded only after the merge exists; never predicted |
| Exact-head CI binding | run id, check-run, job id and artifact id recorded **after** the artifact is parsed |
| Artifact schema | `b1-i1r-evidence-<run_id>` containing `b5-i8-collect.txt`, `b5-i8-junit.xml`, `b5-i8-pytest-output.txt` |
| JUnit schema | one suite; `tests=40`, `failures=0`, `errors=0`, `skipped=0`; unique `(classname, name)` pairs |
| Registry proof schema | recomputed counts must equal the registry's `requirement_set` block exactly |
| Manifest schema | `{path, sha256, size_bytes}` per artifact, hashed over LF-normalized bytes |
| Cleanup schema | machine-readable residual state must be empty (`[]`) |
| Mutation schema | `{mutation_id, target, expected_node, observed_node, red, pristine_sha256, restored_sha256, worktree_clean_after}` |
| Usability schema | `{task_id, surface, completion, error, time_to_first_useful_state_ms, navigation_steps, comprehension_result, recorded_by}` |
| Accessibility schema | `{check_id, surface, assertion, result, finding}` |

## 6. Frozen floors and laws

- focused floor **40** (`FLOOR`) · adjacent floor **189** (`OBSERVED`)
- zero skip / zero failure / zero error
- collection == execution
- duplicate node ids ⇒ FAIL
- orphan test file ⇒ FAIL · orphan registry node ⇒ FAIL
- manifest hash+size recompute required
- cleanup proof required
- common-node base/head comparison required; `common_nodes == 0 => FAIL`
- reserved web-view file present ⇒ FAIL
- any `PASS` claim at P0 ⇒ FAIL

## 7. B5-I7 carry-forward limitations

| Limitation (B5-I7 record) | Classification for B5-I8 | Treatment |
|---|---|---|
| no CI run existed for rung R4 alone | inherited, still relevant | B5-I8 records a run per rung it actually pushes; it cannot retroactively create B5-I7's |
| local shared runner environmentally blocked (absent docker/gitleaks) | inherited, still relevant | CI remains authoritative; local runs labelled `PARTIAL_ENVIRONMENT` |
| `localhost` prose vs literal `127.0.0.1`/`[::1]` transport | inherited, still relevant | audited as stricter-than-prose; **not** silently reconciled in B5-I8 |
| mutation artifact hashes raw working-tree bytes | inherited, still relevant | B5-I8's battery must hash the LF-normalized blob and say so |
| `EL09` working-tree trust boundary | not relevant to B5-I8 (different stage's law set) | unchanged, unedited |
| `EL10`/`EL11` battery trust boundary | inherited in spirit | B5-I8 reruns its own battery rather than trusting an artifact |
| same-agent audit (8.38/10) | inherited, permanent | every B5-I8 score carries the same label; `DF05` carries the independent-auditor obligation |
| reserved `test_b5_i7_web_view.py` prefix debt | inherited, permanent | asserted absent; disclosed as unrepairable under append-only law |
| D1–D9 defect history | inherited, closed or recorded | not reopened; no frozen B5-I7 artifact edited |
| local `main` stale (909 behind at this lock) | inherited, stage-scoped | branch derived from live `origin/main`; staleness recorded, not repaired |

Nothing in this table authorizes editing a frozen B5-I7 artifact. Where a limitation is "must be closed", it is closed by B5-I8's own evidence, never by rewriting B5-I7's.
