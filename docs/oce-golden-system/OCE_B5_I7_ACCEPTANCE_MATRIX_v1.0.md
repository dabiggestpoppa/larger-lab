# OCE Golden System
## B5-I7 — Acceptance Matrix (P0) — v1.0

**Document ID:** OCE-B5-I7-ACCEPTANCE-001
**Version:** 1.0
**Status:** **P0 FROZEN — MAPPING ONLY. NO IMPLEMENTATION GATE IS `PASS`.**
**Stage:** `AUTHORIZED_STAGE=B5-I7-P0`
**Base SHA (observed):** `c6a6479da427ddfe6af06622fc80b2221a4cdc5c`
**Registry:** `OCE_B5_I7_REQUIREMENT_TEST_REGISTRY_v1.0.json` (`OCE-B5-I7-REGISTRY-001`, 44 entries)
**Contract:** `OCE_B5_I7_IMPLEMENTATION_CONTRACT_v1.0.md` (clause column = its section)
**`MERGE_AUTHORIZED = false`** · recurring cost `$0` · `capital.authority = none`

## 0. Frozen counts (arithmetic, recomputable from the registry JSON)

| Dimension | Distribution | Total |
|---|---|---|
| Requirements by class | identity 1 · change_cycle 6 · boundary 3 · gate 3 · panel 9 · measurement 3 · learning 1 · evidence_law 15 · deferred 3 | **44** |
| Bindings | test 27 · attestation 10 · static 2 · runner 2 · deferred 3 | **44** |
| States | PLANNED 35 · MAPPED 6 · DEFERRED_WITH_OWNER 3 · BLOCKED 0 | **44** |
| Planned test nodes | 27 (12 in `test_b5_i7_governed_change.py`, 15 in `test_b5_i7_evidence_laws.py`) | **27** |
| Deferred owners | Operator (I-7 web view) · B5-I8 (G16 usability) · B5-I9 (C5.S5 extraction) | **3** |

`44 = 1+6+3+3+9+3+1+15+3 = 27+10+2+2+3 = 35+6+3+0`.
No requirement is unbound; no binding target is unclaimed by a requirement.

## 1. Acceptance matrix (44 rows)

| ID | Authority | Planned implementation surface | Proof type | Negative control (observable failure) | Evidence artifact | Exit condition |
|---|---|---|---|---|---|---|
| `B5I7-DF01` | charter §12 row I-7; B5-I6 gap contract §5; contract §4.1, §20 | none in B5-I7 (owner: Operator (charter §12 row I-7)) | `deferred` | Creation of test_b5_i7_web_view.py or any web surface during B5-I7 is a boundary violation visible in the diff. | registry row `B5I7-DF01` + contract §20 (no B5-I7 artifact) | no B5-I7 artifact produced; owner + future stage recorded |
| `B5I7-DF02` | plan §7 row B5-I8; charter §11 G16; contract §4.2 | none in B5-I7 (owner: B5-I8 (plan §7 row B5-I8)) | `deferred` | B5-I7 executing or claiming usability evidence pulls a B5-I8 obligation into scope. | registry row `B5I7-DF02` + contract §20 (no B5-I7 artifact) | no B5-I7 artifact produced; owner + future stage recorded |
| `B5I7-DF03` | plan §6 C5.S5; plan §7 row B5-I9; contract §4.2 | none in B5-I7 (owner: B5-I9 (plan §7 row B5-I9, operator-only completion)) | `deferred` | Any extraction or SDK artifact authored in B5-I7 pulls a B5-I9 obligation into scope. | registry row `B5I7-DF03` + contract §20 (no B5-I7 artifact) | no B5-I7 artifact produced; owner + future stage recorded |
| `B5I7-EL01` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL01::test_no_unverified_sha_recorded_as_fact`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A cited 40-hex SHA that git cannot resolve fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL02` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL02::test_no_run_or_artifact_id_recorded_before_existence`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | An id absent from the raw artifact set fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL03` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL03::test_manually_authored_json_not_presented_as_execution_evidence`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | An evidence JSON without parser provenance from raw output fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL04` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL04::test_planned_totals_labeled_expected_not_observed`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A planned total labelled OBSERVED fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL05` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL05::test_observed_totals_bound_to_parsed_raw_artifacts`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | An observed total with no parsed raw source fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL06` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL06::test_green_claims_carry_sha_and_tree_binding`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A success claim lacking head SHA and tree identity fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL07` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL07::test_regression_absence_never_proven_by_new_tests_only`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A regression-absence claim based only on new nodes fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL08` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL08::test_common_regression_population_nonzero_and_at_floor`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A zero or below-floor common population fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL09` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL09::test_manifest_rows_recomputed_hash_and_size`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A manifest row whose recomputed sha256/size differs fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL10` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL10::test_mutation_claims_require_discrimination_and_restoration`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A mutation never observed red, or a tree not restored byte-identically, fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL11` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL11::test_cleanup_claims_require_machine_readable_residual_state`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A cleanup claim without a machine-readable residual listing fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL12` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL12::test_historical_process_defects_remain_visible`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A record that erases the B5-I6 X1 process defects fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL13` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL13::test_same_agent_audit_not_labeled_independent`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | The phrase asserting independent review of a same-agent audit fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL14` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL14::test_no_ratification_before_all_mandatory_gates`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A ratification statement while any gate is unexecuted fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-EL15` | contract §22; B5-I6 X1 lessons (ledger §17.12-§17.13, corrected audit 8.75/10) | `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` -> `TestEL15::test_no_all_gates_passed_language_while_any_gate_pending`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | An all-green claim alongside a skipped or pending gate fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R01` | plan §7 row B5-I7; charter §12 row I-8 | `docs/oce-golden-system/OCE_B5_I7_IMPLEMENTATION_CONTRACT_v1.0.md` -> `§1 Stage identity` | `attestation` | Any scope statement claiming charter increment I-7, B5-I8 or B5-I9 work as B5-I7 contradicts §1 and is visible in the contract diff. | `docs/oce-golden-system/OCE_B5_I7_IMPLEMENTATION_CONTRACT_v1.0.md` (§1 Stage identity) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R02` | charter §12 row I-8; packet §11 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestSingleChange::test_exactly_one_governed_change_recorded`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A change record naming two or more changes fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R03` | charter §12 I-8 stop column; packet §11; contract §4.3 | `git diff --name-only --diff-filter=M c6a6479da427ddfe6af06622fc80b2221a4cdc5c -- infrastructure/control-plane/src infrastructure/control-plane/contracts infrastructure/control-plane/tests (output must be empty)` | `static` | Any modified control-plane source, contract or existing test file makes the diff non-empty. | captured command output in the rung evidence note (stdout + exit code) | `git diff --name-only --diff-filter=M <base> -- <paths>` returns empty at every rung and at the evidence head |
| `B5I7-R04` | charter §12 I-8 non-goals; plan §9; contract §6 | `docs/oce-golden-system/OCE_B5_I7_IMPLEMENTATION_CONTRACT_v1.0.md` -> `§6 Prohibited scope` | `attestation` | An added route, job type, schema or extraction artifact is a named boundary violation recorded against §6. | `docs/oce-golden-system/OCE_B5_I7_IMPLEMENTATION_CONTRACT_v1.0.md` (§6 Prohibited scope) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R05` | plan §5 C4.S5 | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` -> `§1 Intent` | `attestation` | A change record whose intent section is absent, or written after the change, fails the attestation review. | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` (§1 Intent) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R06` | plan §5 C4.S5 | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` -> `§2 Plan and affected surfaces` | `attestation` | A plan listing a surface outside the allowed-surface table of contract §5 is rejected. | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` (§2 Plan and affected surfaces) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R07` | plan §5 C4.S5; contract §21 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestChangeCycle::test_change_has_positive_and_negative_proofs`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A change with only a positive proof, or with a negative control never executed red, fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R08` | plan §5 C4.S5 (release and rollback) | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` -> `§4 Release and rollback` | `attestation` | A manifest that is non-deterministic, or rollback metadata missing base_commit/procedure, is refused. | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` (§4 Release and rollback) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R09` | constitution append-only evidence law; contract §5 | `git diff --name-only c6a6479da427ddfe6af06622fc80b2221a4cdc5c -- 'docs/oce-golden-system/OCE_B5_I[0-6]*' (output must be empty)` | `static` | Any frozen prior-stage document differing from the base blob fails the diff check. | captured command output in the rung evidence note (stdout + exit code) | `git diff --name-only <base> -- 'docs/oce-golden-system/OCE_B5_I[0-6]*'` returns empty at every rung |
| `B5I7-R10` | charter §12 I-8 'control-plane suite passing unchanged'; charter §11 G14 | `.github/workflows/b1-i1r-validation.yml step 'Execute B5-I7 governed-change proofs'` | `runner` | Any node-count delta, skip, error or collection difference versus the base run makes the runner assertion fail. | shared runner log + `stage-status.json` inside `b1-i1r-evidence-<run_id>` | CI step parses junit at exact head: collected == base collected, skipped == 0, failed == 0, errored == 0; floor 27 met |
| `B5I7-R11` | charter §11 G14; contract §2 | `infrastructure/cloud-ground/scripts/run-validation.sh` | `runner` | A non-terminal or non-success shared-runner exit makes the gate not executed, never passed. | shared runner log + `stage-status.json` inside `b1-i1r-evidence-<run_id>` | shared runner exits 0 and `stage-status.json.gate_status == READY_FOR_OPERATOR_REVIEW`, parsed from the raw artifact of the exact-head run |
| `B5I7-R12` | charter §12 I-8 gate column; plan §5 C4.S4 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestRegressionDrill::test_unchanged_stack_drill_report_byte_identical`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | Any byte difference between the reference and rerun drill report fails the identity comparison. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | sha256(reference report) == sha256(rerun report) recorded from raw bytes at R1/R3 |
| `B5I7-R13` | charter §12 I-8 evidence column; contract §22 | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` -> `§5 Evidence binding` | `attestation` | A SHA, run id or artifact id that does not resolve to an existing object/run invalidates the record. | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` (§5 Evidence binding) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R14` | plan §6 C5.S4; charter §12 I-8 evidence column | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` -> `§6 Learning ledger entries` | `attestation` | An observation without disposition/owner, or a dropped observation, fails the attestation review. | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` (§6 Learning ledger entries) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R15` | contract pack frozen reads (A12); contract §7 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelContract::test_undeclared_surface_refused_before_io`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | An undeclared surface that reaches the transport raises ConsoleRefusal with reason unsupported_surface and zero socket attempts. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R16` | charter §5 authority law; packet §11 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelReadOnly::test_panel_issues_only_get_requests`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | Any POST/PUT/PATCH/DELETE attempt or invoke-surface access fails the request-log assertion. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R17` | charter §10 fail-closed law; matrix X4/X7 precedent; contract §13 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelFailClosed::test_unreachable_stack_never_renders_healthy`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | An unreachable stack that yields state OK or any numeric queue value fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R18` | charter §5 rule 9 (verbatim denial); contract §12, §14 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelFailClosed::test_unknown_queue_depth_rendered_unknown_not_zero`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A missing field rendered as 0 or as green, or a second automatic request after a denial, fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R19` | charter §7 deterministic kernel; contract §9 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelDeterminism::test_identical_inputs_render_byte_identically`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | Two renders of the same inputs differing in bytes, key order or newline fail the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R20` | charter §6 local-only topology; contract §10 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelLoopback::test_non_loopback_base_url_refused`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | A non-loopback target that opens a socket fails the blocked-off-loopback control. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R21` | charter §10 security/privacy; contract §17 | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelSecurity::test_panel_output_contains_no_secret_material`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | Any credential-shaped value in rendered output fails the secret-pattern scan of the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R22` | contract §11 input bounds | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestPanelBounds::test_oversized_and_malformed_input_refused`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | An oversized (>64 KiB document / >512-byte argument) or malformed payload accepted without refusal fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R23` | charter §8.1 required surface; contract §18 (X3 compatibility) | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` -> `TestCompatibility::test_documented_status_command_and_exit_codes_unchanged`
(selection step `Execute B5-I7 governed-change proofs`, planned at rung R4) | `test` | Any changed exit code or failing documented status invocation fails the node. | CI artifact `b1-i1r-evidence-<run_id>`: `b5-i7-junit.xml`, `b5-i7-pytest-output.txt`, `b5-i7-collect.txt` (PLANNED) | node green at exact head with zero skip, floor 27 met |
| `B5I7-R24` | plan §6 C5.S1 | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` -> `§7 Cost and time` | `attestation` | An unlabelled figure, or an OBSERVED label with no measurement provenance, fails the attestation review. | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md` (§7 Cost and time) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R25` | charter §13/§15 accounting; plan §7 | `docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` -> `§18.6 Locks and accounting` | `attestation` | Any nonzero recurring cost or authority value contradicts the frozen accounting row. | `docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` (§18.6 Locks and accounting) | section exists, self-consistent, and is cited by the ledger entry |
| `B5I7-R26` | plan §6 C5.S2; packet §12 | `docs/oce-golden-system/OCE_B5_I7_REUSE_INVENTORY_v1.0.md` -> `§2 Verified reuse (import/runtime paths)` | `attestation` | A claimed reuse item with no import path or executed path is struck from the inventory. | `docs/oce-golden-system/OCE_B5_I7_REUSE_INVENTORY_v1.0.md` (§2 Verified reuse (import/runtime paths)) | section exists, self-consistent, and is cited by the ledger entry |


## 1. Reading rules

- **Status vocabulary (P0):** `PLANNED` (binding target does not exist yet),
  `MAPPED` (binding target exists in this tree today), `DEFERRED_WITH_OWNER`,
  `BLOCKED`. **No row is `PASS` during P0** — P0 freezes the map, it does not execute it.
- Every registry ID appears exactly once in this matrix; the row count equals
  `requirement_set.total` (44). Negative controls are executable expectations, not prose:
  each names the observable result when the implementation is weakened or the claim fails.
- Proof types: `test` (executable node), `static` (command over the tree/history),
  `runner` (authoritative CI selection parsed from raw artifacts), `attestation`
  (documentary section with a named consumer), `deferred` (obligation owned elsewhere).

## 2. Two-sided test plan (per behavioral claim)

| Dimension | Rule for every `test` row |
|---|---|
| Positive proof | the real implementation passes the node |
| Refusal/negative proof | a hostile or out-of-scope input reaches an explicit refusal with the frozen reason vocabulary |
| Weakened-implementation control | a deliberately weakened implementation is EXECUTED and must fail the node (never source-string theater) |
| Mutation expectation | each mutation in the battery is expected to make a named node red, then is restored byte-identically |
| Adjacent regression | the node is executed together with the B5-I2..B5-I6 suites and the shared runner (common population, floor below) |
| Cleanup assertion | after every red execution: `git status --porcelain` empty, no residual file/port/process, recorded machine-readably |

Hostile cases mandatory in R3: malformed input; oversized input; unknown fields;
duplicate identifiers; stale identity; unauthorized transition; client-side forged state;
non-loopback access where prohibited; missing dependency; interrupted operation; replay;
partial evidence; recovery disagreement; unverifiable output. Each maps to a failure class
in `OCE_B5_I7_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md` §2 and to at least one node above.

## 3. Floors and zero-skip

- **Frozen node floor: 27** (all 27 planned `test` bindings) — `EXPECTED` at P0,
  re-derived at R4 from `pytest --collect-only` and recorded as `OBSERVED` only then.
- **Zero skip / zero xfail / zero deselect / zero collection error** in the B5-I7 step.
- Common regression population must be **nonzero and ≥ floor** (`B5I7-EL08`), executed at
  **both** the base SHA and the implementation head (`B5I7-EL07`).

## 4. Evidence artifacts and retention

| Artifact | Produced at | Retention |
|---|---|---|
| `b5-i7-collect.txt`, `b5-i7-junit.xml`, `b5-i7-pytest-output.txt` | R4 CI step | inside `b1-i1r-evidence-<run_id>` artifact, standard retention |
| shared runner log + `stage-status.json` | R4 | same artifact |
| mutation battery raw output + restoration hashes | R3 | same artifact + change record §8 |
| reference vs rerun drill reports (sha256 + bytes) | R1/R3 | change record §4/§5 |
| `OCE_B5_I7_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` | EVIDENCE rung | repo, append-only |

No placeholder JSON may be cited as execution evidence (`B5I7-EL03`); every JSON cited in
the ledger must be produced by a parser over raw output and carry its source run id.
