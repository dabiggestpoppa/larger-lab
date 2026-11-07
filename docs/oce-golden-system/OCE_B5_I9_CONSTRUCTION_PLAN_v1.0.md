# OCE Golden System — B5-I9 Construction Plan — v1.0

**Document ID:** OCE-B5-I9-CONSTRUCTION-001
**Version:** 1.0
**Status:** `B5-I9 P0 = DRAFT FOR OPERATOR REVIEW` — implementation NOT STARTED
**Base:** `833f7d1b9f2dfec2986fb9516d0abde06bf23dae`

---

## 1. Position

B5-I9 is the factory gate and the B6 reusable-extraction contract, completed by the
operator. Its construction is therefore **evidence construction**, not software
construction: documents, a registry, a failure matrix, a mutation plan and one read-only
validator. The phase list below is the plan the operator would authorize; none of it is
executed here.

P0 (this packet) is phase 0 and is already complete as a draft.

## 2. Phases after operator authorization

| Phase | Scope | Exit gate | Artifacts |
|---|---|---|---|
| `P1` | Ratify the extraction classification and its limitations | Operator ratifies scope (`B5.C5.S5`) | Signed classification; no code moves |
| `P2` | Build the 37 planned proof nodes | All nodes execute against the packet itself | Five test files under `infrastructure/control-plane/tests/` |
| `P3` | Execute the 10-mutation battery | 10/10 discriminated, byte-exact restore, pristine rerun | Mutation results JSON |
| `P4` | Produce the factory gate packet | Arithmetic reconciles; hashes recomputed from bytes | Gate packet + evidence record |
| `P5` | Close the learning ledger and correction decisions | No meaningful observation silently discarded | Learning ledger section |
| `P6` | Hand off to Book 6 under a fresh authorization | `BOOK_6_AUTHORIZED` turns true only by operator act | Handoff record |

## 3. Planned node inventory (41 nodes, 5 files)

No file is created at P0. Node ids are fully qualified as `Class::test_name` inside their
planned file.

### `tests/test_b5_i9_book6_handoff.py`

| Node | Requirement |
|---|---|
| `TestG16::test_g16_remains_open_with_owner` | `B5I9-GA-01` |
| `TestG16::test_missing_condition_carried_forward` | `B5I9-GA-02` |
| `TestHandoff::test_book6_states_remain_false` | `B5I9-HO-02` |
| `TestHandoff::test_consumable_evidence_list_is_complete` | `B5I9-HO-04` |
| `TestHandoff::test_no_book6_artifact_exists` | `B5I9-HO-03` |
| `TestHandoff::test_seven_states_are_distinct` | `B5I9-HO-01` |
| `TestHandoff::test_start_requires_fresh_authorization` | `B5I9-HO-05` |

### `tests/test_b5_i9_extraction_classification.py`

| Node | Requirement |
|---|---|
| `TestClassification::test_authority_bearing_items_are_never_extractable` | `B5I9-EX-02` |
| `TestClassification::test_every_candidate_classified_once` | `B5I9-EX-01` |
| `TestClassification::test_extractable_items_declare_provenance_and_limits` | `B5I9-EX-06` |
| `TestClassification::test_extractable_items_declare_recovery_behaviour` | `B5I9-EX-05` |
| `TestClassification::test_extractable_items_declare_refusal_behaviour` | `B5I9-EX-04` |
| `TestClassification::test_negative_control_rejects_reusable_looking_component` | `B5I9-EX-07` |
| `TestClassification::test_private_interfaces_never_promoted` | `B5I9-EX-03` |

### `tests/test_b5_i9_no_platform_extraction.py`

| Node | Requirement |
|---|---|
| `TestNoPlatform::test_no_cloud_or_execution_surface` | `B5I9-NP-08` |
| `TestNoPlatform::test_no_cloud_or_provider_surface` | `B5I9-NP-09` |
| `TestNoPlatform::test_no_duplicated_authority_decision` | `B5I9-NP-04` |
| `TestNoPlatform::test_no_environment_or_host_embedded` | `B5I9-NP-07` |
| `TestNoPlatform::test_no_private_module_in_public_surface` | `B5I9-NP-02` |
| `TestNoPlatform::test_no_reexport_of_control_plane_internals` | `B5I9-NP-01` |
| `TestNoPlatform::test_no_second_canonical_state` | `B5I9-NP-03` |
| `TestNoPlatform::test_single_configuration_truth` | `B5I9-NP-06` |
| `TestNoPlatform::test_single_owner_per_authority_function` | `B5I9-NP-05` |

### `tests/test_b5_i9_packet_packaging_and_provenance.py`

| Node | Requirement |
|---|---|
| `TestProvenance::test_artifact_size_rule_enforced` | `B5I9-PK-06` |
| `TestProvenance::test_every_artifact_records_identity` | `B5I9-PK-01` |
| `TestProvenance::test_generation_is_byte_identical` | `B5I9-PK-03` |
| `TestProvenance::test_manifest_rows_recomputed_from_bytes` | `B5I9-PK-02` |
| `TestProvenance::test_no_secret_material` | `B5I9-PK-05` |
| `TestProvenance::test_second_run_matches_first` | `B5I9-PK-04` |
| `TestProvenance::test_validator_performs_no_network_access` | `B5I9-PK-09` |
| `TestProvenance::test_validator_stdlib_only_and_offline` | `B5I9-PK-07` |

### `tests/test_b5_i9_stage_identity_and_scope.py`

| Node | Requirement |
|---|---|
| `TestLedgerAppend::test_ledger_prefix_unchanged_and_appended` | `B5I9-SI-06` |
| `TestLocks::test_changed_file_boundary` | `B5I9-BD-04` |
| `TestLocks::test_merge_authorized_false` | `B5I9-BD-01` |
| `TestLocks::test_no_capital_or_execution_authority` | `B5I9-BD-02` |
| `TestLocks::test_no_scratch_residue` | `B5I9-BD-05` |
| `TestStageIdentity::test_base_sha_is_the_merged_main` | `B5I9-SI-02` |
| `TestStageIdentity::test_claims_resolve_in_their_sources` | `B5I9-SI-04` |
| `TestStageIdentity::test_deliverable_set_is_complete` | `B5I9-SI-03` |
| `TestStageIdentity::test_no_implementation_artifact_at_p0` | `B5I9-SI-05` |
| `TestStageIdentity::test_stage_identity_matches_governing_clauses` | `B5I9-SI-01` |

## 4. Ordering and dependencies

`P1` precedes `P2` because a proof cannot assert a classification the operator has not
ratified. `P2` precedes `P3` because a mutation must have a discriminator to fail. `P4`
depends on `P3` for its mutation evidence. `P5` depends on `P4`. `P6` depends on the
operator, not on the agent.

## 5. Planned validator

`infrastructure/control-plane/scripts/b5_i9_p0_validate.py` is committed with this packet.
It is read-only, stdlib-only, offline, and it is the only executable artifact B5-I9 P0
creates. It validates the packet against itself: identity, classification, arithmetic,
closure, boundary and ledger prefix. It is not a test file and does not execute any B5-I9
implementation behaviour.

## 6. Verification at P0

| Check | Method |
|---|---|
| JSON parse and canonicalization | `json.load` then sorted-key re-dump |
| Unique ids / one binding / zero PASS | registry assertions |
| Arithmetic recomputation | counts derived from rows, compared to declared totals |
| Requirement-to-node closure | set equality between requirement nodes and inventory nodes |
| Failure and mutation closure | declared sets versus referenced sets |
| Citations resolve | each citation's file exists and its clause token is present |
| Boundary | no test/workflow/B6 artifact; no production file changed |
| Ledger prefix | `sha256(LF[0:191950]) == 83a40ac7...` |
| Style | CRLF consistent with neighbouring documents; `git diff --check`; secret scan |

## 7. Estimated effort

Documentation and one validator: no compute, no provider, no cloud. Cost `$0`. The binding
constraint is operator attention, not machine time.
