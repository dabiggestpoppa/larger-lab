# OCE Golden System
## B5-I8 — Acceptance Matrix (P0) — v1.0

**Document ID:** OCE-B5-I8-ACCEPTANCE-001
**Version:** 1.0
**Status:** `P0_DRAFT_FOR_OPERATOR_REVIEW` — **planning only; zero PASS claims.**
**Stage:** `AUTHORIZED_STAGE=B5-I8-P0` · **Base SHA (observed):** `7393228dd4b21be9440785204ea9e640800d5d95`
**Registry:** `OCE_B5_I8_REQUIREMENT_TEST_REGISTRY_v1.0.json` (`OCE-B5-I8-REGISTRY-001`, 55 entries)
**Contract:** `OCE_B5_I8_IMPLEMENTATION_CONTRACT_v1.0.md` (clause column = its section)
**`MERGE_AUTHORIZED=false`** · `B5-I9 = LOCKED` · Book 6 `UNAUTHORIZED` · cost `$0` · `capital.authority = none`

## 0. Frozen counts (arithmetic, recomputable from the registry JSON)

| Dimension | Distribution | Total |
|---|---|---|
| Requirements by kind | identity 3 · boundary 4 · e2e 4 · adversarial 10 · usability 7 · evidence_audit 6 · measurement 4 · gate 4 · evidence_law 8 · deferred 5 | **55** |
| Bindings | test 40 · static 3 · runner 0 · attestation 7 · deferred 5 | **55** |
| States | PLANNED 40 · MAPPED 10 · DEFERRED_WITH_OWNER 5 · BLOCKED 0 | **55** |
| Planned test nodes | 40 across 5 files | **40** |
| Deferred owners | Operator · B5-I9 · Book 6 · post-Book-6 phase · Operator (independent audit) | **5** |

`55 = 3+4+4+10+7+6+4+4+8+5 = 40+7+3+5 = 40+10+5+0`. No requirement is unbound;
no planned node is unclaimed; the count follows the four audit axes plus `G16`, the inherited
laws, eight audit evidence laws and five deferred obligations — it is not sized to resemble B5-I7.

## 1. Acceptance matrix (55 rows)

| ID | Kind | Authority | Planned proof / surface | Refusal condition (observable) | P0 disposition |
|---|---|---|---|---|---|
| `B5I8-DF01` | deferred | charter section 12 row I-7; B5-I7 contract 20 | `infrastructure/control-plane/tests/test_b5_i7_web_view.py (frozen planned node string)` | The obligation being executed inside B5-I8 is a scope violation visible in the diff. | `DEFERRED_WITH_OWNER` |
| `B5I8-DF02` | deferred | Block 5 plan section 7 | `correction ADRs + B6 contract (B5-I9 evidence)` | The obligation being executed inside B5-I8 is a scope violation visible in the diff. | `DEFERRED_WITH_OWNER` |
| `B5I8-DF03` | deferred | Block 5 plan section 7 | `Block 6 plan artifacts` | The obligation being executed inside B5-I8 is a scope violation visible in the diff. | `DEFERRED_WITH_OWNER` |
| `B5I8-DF04` | deferred | Block 5 plan section 7 | `evaluation service + blind instrument evidence` | The obligation being executed inside B5-I8 is a scope violation visible in the diff. | `DEFERRED_WITH_OWNER` |
| `B5I8-DF05` | deferred | Block 5 plan section 7 | `independent audit report (external to this agent)` | The obligation being executed inside B5-I8 is a scope violation visible in the diff. | `DEFERRED_WITH_OWNER` |
| `B5I8-EL01` | evidence_law | B5-I7 EL01; B5-I7 contract section 22 evidence laws | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL01::test_no_unverified_sha_recorded_as_fact` | An unresolvable SHA turns the law red. | `PLANNED` |
| `B5I8-EL02` | evidence_law | B5-I7 EL02 | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL02::test_no_run_or_artifact_id_recorded_before_existence` | A pre-recorded id turns the law red. | `PLANNED` |
| `B5I8-EL03` | evidence_law | B5-I7 EL04 | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL03::test_planned_totals_labeled_expected` | A planned total labelled OBSERVED turns the law red. | `PLANNED` |
| `B5I8-EL04` | evidence_law | B5-I7 EL05 | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL04::test_observed_totals_bound_to_parsed_raw_artifact` | An observed value with no parsed source turns the law red. | `PLANNED` |
| `B5I8-EL05` | evidence_law | B5-I7 EL13; contract section 11 | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL05::test_human_evidence_labeled_non_blind_not_independent` | An independence or blindness claim turns the law red. | `PLANNED` |
| `B5I8-EL06` | evidence_law | B5-I7 EL15 | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL06::test_no_all_gates_passed_language_while_gate_pending` | The phrase appearing with a pending gate turns the law red. | `PLANNED` |
| `B5I8-EL07` | evidence_law | Block 5 plan section 7 row B5-I8; B5-I7 EL07 | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL07::test_audit_verdict_recomputable_not_free_text` | A prose-only verdict turns the law red. | `PLANNED` |
| `B5I8-EL08` | evidence_law | B5-I7 EL03/EL05 | `infrastructure/control-plane/tests/test_b5_i8_evidence_laws.py::TestEL08::test_no_evidence_value_untraceable_to_raw_source` | An orphan value turns the law red. | `PLANNED` |
| `B5I8-R01` | identity | Block 5 plan section 7 row B5-I8; charter section 12 rows I-7/I-8 | `contract section 1 and 1.1 (stage identity table and cross-numbering table)` | Any scope statement that names B5-I8 a build or web-view increment contradicts plan section 7 and is visible in the packet diff. | `MAPPED` |
| `B5I8-R02` | identity | Block 5 plan section 7 row B5-I8 gate; charter section 5 authority law; B5-I7 contract section 4.3 | `contract section 3 allowed/prohibited surface table` | A production or existing-test file in the changed-file boundary fails the boundary check. | `MAPPED` |
| `B5I8-R03` | identity | B5-I7 contract section 4.1 and 20 (B5I7-DF01); B5-I3 construction plan section 8 | `static path probe over infrastructure/control-plane/tests/test_b5_i7_web_view.py` | The file existing at audit time is a boundary violation detected by the probe. | `MAPPED` |
| `B5I8-R04` | boundary | charter section 5 rules 1-9; section 8.3 | `contract section 6 inherited laws (verified, not re-implemented)` | Any audit artifact that becomes authoritative state, or any client-side mint, fails the authority law. | `MAPPED` |
| `B5I8-R05` | boundary | charter section 6; architecture amendment A003; Block 5 plan section 9 | `contract section 3 transport/local-only rows plus dependency audit` | Any provider import, analytics call, listening socket or non-loopback endpoint fails the audit. | `MAPPED` |
| `B5I8-R06` | boundary | charter section 8.3; Block 5 plan section 8; charter gate G12 | `contract section 17 locks and accounting` | Any capital/broker/execution surface or dependency fails the audit. | `MAPPED` |
| `B5I8-R07` | boundary | Block 5 plan section 6 C5.S5 and section 7 row B5-I9; Block 6 plan section 1 | `contract section 5 boundary table` | An extraction decision, correction ADR or Book 6 draft inside this stage is a scope violation. | `MAPPED` |
| `B5I8-R08` | e2e | Block 5 plan section 7 row B5-I8 ('E2E audit'); charter section 11 G7 | `infrastructure/control-plane/tests/test_b5_i8_e2e.py::TestEndToEndPath::test_full_governed_path_reexecuted_from_frozen_message` | A stack-unreachable or failed path must render explicit refusal, never a green terminal state. | `PLANNED` |
| `B5I8-R09` | e2e | charter section 11 G6 and section 9 restart row | `infrastructure/control-plane/tests/test_b5_i8_e2e.py::TestEndToEndPath::test_restart_preserves_governed_state_identity` | Any identity drift across restart fails the node. | `PLANNED` |
| `B5I8-R10` | e2e | charter section 11 G8; Block 5 plan section 5 C4.S4; B5-I6 drill record | `infrastructure/control-plane/tests/test_b5_i8_e2e.py::TestEndToEndPath::test_drill_path_reproduces_recorded_disposition` | A disposition that cannot be reproduced is reported as a finding, never silently re-adopted. | `PLANNED` |
| `B5I8-R11` | e2e | charter section 11 G5 and section 9 admission row; packet S-4 | `infrastructure/control-plane/tests/test_b5_i8_e2e.py::TestEndToEndPath::test_denial_path_rendered_verbatim_end_to_end` | A suppressed or paraphrased denial fails the node. | `PLANNED` |
| `B5I8-R12` | adversarial | charter section 5 rules 1-3; section 11 G3 | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestAuthorityMinting::test_client_cannot_mint_identity_or_grant` | Any minted authority object fails the node; a demonstrated bypass is STOP-6. | `PLANNED` |
| `B5I8-R13` | adversarial | charter section 5 rule 7; section 11 G5; packet section 12 | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestForgedState::test_forged_client_state_refused_before_effect` | A side effect before refusal fails the node. | `PLANNED` |
| `B5I8-R14` | adversarial | charter section 9 progress-observation row; inherited law 'unknown is not zero' | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestTruthCollapse::test_unknown_never_renders_zero` | Coercion to 0 or to empty fails the node. | `PLANNED` |
| `B5I8-R15` | adversarial | inherited law 'partial is not success'; Block 5 plan section 3 C2.S4 | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestTruthCollapse::test_partial_never_renders_success` | A complete-looking success from partial data fails the node. | `PLANNED` |
| `B5I8-R16` | adversarial | charter section 6 fail-closed clause; section 11 G7 | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestTruthCollapse::test_stale_state_never_renders_green` | Stale data rendered as live fails the node. | `PLANNED` |
| `B5I8-R17` | adversarial | charter section 6 and section 11 G1/G2 | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestTransport::test_non_loopback_request_fail_closed` | Acceptance of a non-loopback peer fails the node. | `PLANNED` |
| `B5I8-R18` | adversarial | charter section 11 G5; section 10 last bullet | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestTransport::test_unsupported_route_refused_before_side_effect` | A generic 500, a silent no-op or a hidden success fails the node. | `PLANNED` |
| `B5I8-R19` | adversarial | charter section 10; B5-I7 defect history D2/D3 | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestRedaction::test_secret_material_absent_from_audit_output` | A surviving secret value fails the node and is STOP-6. | `PLANNED` |
| `B5I8-R20` | adversarial | Block 5 plan section 3 C2.S4; charter section 10 bounded inputs | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestBounds::test_oversized_input_refused_within_bounds` | Unbounded reading or silent truncation presented as complete fails the node. | `PLANNED` |
| `B5I8-R21` | adversarial | charter section 7 kernel determinism; Block 5 plan section 3 C2.S2 | `infrastructure/control-plane/tests/test_b5_i8_adversarial.py::TestDeterminism::test_adversarial_case_ordering_deterministic` | Order-dependent output fails the node. | `PLANNED` |
| `B5I8-R22` | usability | Block 5 plan section 6 C5.S3; section 4 C2.S5 human evidence | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestUsabilityProtocolExecution::test_protocol_tasks_defined_and_executed` | An unexecuted or self-declared protocol fails the node. | `PLANNED` |
| `B5I8-R23` | usability | Block 5 plan section 6 C5.S3; charter section 11 G16 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestComprehension::test_state_comprehension_recorded` | A missing comprehension record fails the node. | `PLANNED` |
| `B5I8-R24` | usability | Block 5 plan section 6 C5.S3; charter section 11 G16 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestComprehension::test_refusal_comprehension_recorded` | A refusal the operator cannot identify fails the node. | `PLANNED` |
| `B5I8-R25` | usability | Block 5 plan section 6 C5.S3; charter section 11 G16 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestComprehension::test_recovery_comprehension_recorded` | A recovery outcome the operator cannot distinguish fails the node. | `PLANNED` |
| `B5I8-R26` | usability | inherited laws unknown-is-not-zero and partial-is-not-success; G16 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestComprehension::test_unknown_and_partial_recognized` | Conflation of unknown/partial with success fails the node. | `PLANNED` |
| `B5I8-R27` | usability | charter section 11 G16; Block 5 plan section 6 C5.S3 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestAccessibility::test_accessibility_semantics_verified` | A missing or unlabelled state/refusal surface fails the node. | `PLANNED` |
| `B5I8-R28` | usability | B5-I7 evidence law EL13; B5-I7 ratification section 6 | `contract section 11 evidence-class table` | An independence or blindness claim fails the audit; EL05 detects it. | `MAPPED` |
| `B5I8-R29` | evidence_audit | Block 5 plan section 7 row B5-I8 ('evidence audit'); B5-I7 EL01 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestEvidenceAudit::test_prior_stage_citations_resolve_to_commits` | An unresolvable cited SHA fails the node. | `PLANNED` |
| `B5I8-R30` | evidence_audit | Block 5 plan section 7 row B5-I8; B5-I7 EL02/EL05 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestEvidenceAudit::test_run_and_artifact_ids_resolve_to_raw_evidence` | An id with no raw source fails the node. | `PLANNED` |
| `B5I8-R31` | evidence_audit | B5-I7 EL15; charter section 11 final sentence | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestEvidenceAudit::test_no_all_green_claim_while_gate_pending` | An all-green claim over a pending gate fails the node. | `PLANNED` |
| `B5I8-R32` | evidence_audit | Block 5 ledger append-only law; B5-I7 section 18 ledger proof | `static prefix comparison of git blob bytes at base and audit head` | Any edited historical byte fails the prefix comparison. | `MAPPED` |
| `B5I8-R33` | evidence_audit | B5-I7 EL09; B5-I7 contract section 22 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestEvidenceAudit::test_manifest_rows_recompute_over_committed_bytes` | A stale row fails the node. | `PLANNED` |
| `B5I8-R34` | evidence_audit | Block 5 plan section 7 row B5-I8 gate; B5-I7 EL07 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestAuditVerdict::test_verdict_recomputable_from_committed_evidence` | A narrative verdict with no recomputation path fails the node. | `PLANNED` |
| `B5I8-R35` | measurement | Block 5 plan section 6 C5.S1 measurement discipline; section 11 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestMeasurements::test_time_to_first_useful_state_measured` | An unlabelled or estimated value presented as observed fails the node. | `PLANNED` |
| `B5I8-R36` | measurement | Block 5 plan section 6 C5.S3; charter section 11 G16 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestMeasurements::test_navigation_steps_measured` | A missing navigation count fails the node. | `PLANNED` |
| `B5I8-R37` | measurement | Block 5 plan section 6 C5.S3; section 4 C2.S5 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestMeasurements::test_task_completion_and_error_measured` | An unreported error count fails the node. | `PLANNED` |
| `B5I8-R38` | measurement | charter section 7 determinism; Block 5 plan section 3 C2.S2 | `infrastructure/control-plane/tests/test_b5_i8_usability_measurements.py::TestMeasurements::test_audit_replay_is_deterministic` | A differing replay fails the node. | `PLANNED` |
| `B5I8-R39` | gate | B5-I3 construction plan section 5/8; B5-I3 registry G16; B5-I7 contract section 20 B5I7-DF02 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestUsabilityProtocol::test_accessibility_and_usability_verified` | A renamed or relocated G16 node fails the inheritance check. | `PLANNED` |
| `B5I8-R40` | gate | charter section 11 G14; B5-I7 contract section 22 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestGateClosure::test_g14_adjacent_population_stays_green` | A red adjacent node fails the node and the stage. | `PLANNED` |
| `B5I8-R41` | gate | charter section 11 G15; failure plan section 4 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestGateClosure::test_g15_mutation_controls_discriminate` | A non-discriminating mutation fails the node. | `PLANNED` |
| `B5I8-R42` | gate | charter section 11 G17 and section 12 ceiling accounting | `static scope audit over the packet (no new increment, no Book 6 artifact)` | Any new increment, B5-I9 artifact or Book 6 document fails the audit. | `MAPPED` |

## 2. Disposition law

Every row above is a planning disposition: `PLANNED` (a future node is bound, nothing executes yet),
`MAPPED` (the binding target exists today as a document or a static check), or
`DEFERRED_WITH_OWNER` (an owner, a reason and a future stage are recorded).
**No row is `PASS`, no gate is claimed met, and `G16` remains open.**

## 3. Cross-reference validity

Every ID in this matrix is a registry ID, and every registry ID appears here exactly once
(55/55). Every `test` row names a node in the frozen inventory; the inherited `G16` node
`TestUsabilityProtocol::test_accessibility_and_usability_verified` appears verbatim at `B5I8-R39`.
