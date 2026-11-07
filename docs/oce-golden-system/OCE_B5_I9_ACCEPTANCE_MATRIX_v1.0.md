# OCE Golden System — B5-I9 Acceptance Matrix — v1.0

**Document ID:** OCE-B5-I9-ACCEPTANCE-001
**Version:** 1.0
**Status:** `B5-I9 P0 = DRAFT FOR OPERATOR REVIEW`
**Registry:** `OCE_B5_I9_REQUIREMENT_TEST_REGISTRY_v1.0.json` (canonical; this matrix is derived and must not drift from it)
**Base:** `833f7d1b9f2dfec2986fb9516d0abde06bf23dae`

---

## 1. How to read this matrix

Every row is one requirement. `Binding` is exactly one of `test`, `attestation`,
`static`, `deferred`. A `test` row names exactly one planned node; a non-test row names
none and records its owner instead. No row claims `PASS`: P0 proves nothing about
behaviour, and the starting state vocabulary is `PLANNED`, `MAPPED`,
`DEFERRED_WITH_OWNER`, `BLOCKED`.

## 2. Arithmetic (recomputed by the validator)

| Measure | Value |
|---|---|
| Requirements | 51 |
| By category | book6_handoff 8, boundary 5, extraction 10, g16 4, no_platform_law 9, packaging 9, stage_identity 6 |
| By binding | attestation 4, deferred 2, static 4, test 41 |
| By state | DEFERRED_WITH_OWNER 2, MAPPED 41, PLANNED 8 |
| PASS claims | 0 |
| Planned nodes | 41 across 5 planned test files |
| Failure classes bound | 25 of 25 declared (floor 22) |
| Mutations planned | 10 (floor 10) |

## 3. Rows

| Requirement | Category | Acceptance observable | Binding | Planned node | State |
|---|---|---|---|---|---|
| `B5I9-SI-01` | stage_identity | the contract's identity section names all four clauses and all three non-identities | test | `TestStageIdentity::test_stage_identity_matches_governing_clauses` | MAPPED |
| `B5I9-SI-02` | stage_identity | packet artifacts carry base_sha == merged main | test | `TestStageIdentity::test_base_sha_is_the_merged_main` | MAPPED |
| `B5I9-SI-03` | stage_identity | every declared deliverable exists; no undeclared document is required | test | `TestStageIdentity::test_deliverable_set_is_complete` | MAPPED |
| `B5I9-SI-04` | stage_identity | every citation names an existing file and a clause that exists | test | `TestStageIdentity::test_claims_resolve_in_their_sources` | MAPPED |
| `B5I9-SI-05` | stage_identity | no test_b5_i9_*.py, no b5_i9 symbol in workflows | test | `TestStageIdentity::test_no_implementation_artifact_at_p0` | MAPPED |
| `B5I9-SI-06` | stage_identity | sha256(prefix[0:191950]) equals 83a40ac7... | test | `TestLedgerAppend::test_ledger_prefix_unchanged_and_appended` | MAPPED |
| `B5I9-EX-01` | extraction | 26 rows, nine-class vocabulary, no unclassified candidate | test | `TestClassification::test_every_candidate_classified_once` | MAPPED |
| `B5I9-EX-02` | extraction | no row combining AUTHORITY_BEARING source with EXTRACTABLE_* class | test | `TestClassification::test_authority_bearing_items_are_never_extractable` | MAPPED |
| `B5I9-EX-03` | extraction | no PRIVATE_API or PLATFORM_INTERNAL path appears in a public surface list | test | `TestClassification::test_private_interfaces_never_promoted` | MAPPED |
| `B5I9-EX-04` | extraction | each EXTRACTABLE_* row has a refusal statement | test | `TestClassification::test_extractable_items_declare_refusal_behaviour` | MAPPED |
| `B5I9-EX-05` | extraction | each EXTRACTABLE_* row has a recovery statement | test | `TestClassification::test_extractable_items_declare_recovery_behaviour` | MAPPED |
| `B5I9-EX-06` | extraction | each EXTRACTABLE_* row carries source path, provenance and limitation | test | `TestClassification::test_extractable_items_declare_provenance_and_limits` | MAPPED |
| `B5I9-EX-07` | extraction | kernel.py rejected as stable API; job_store.py rejected as prohibited | test | `TestClassification::test_negative_control_rejects_reusable_looking_component` | MAPPED |
| `B5I9-EX-08` | extraction | rule R1 stated and applied to every row | static | — | PLANNED |
| `B5I9-EX-09` | extraction | each of the 26 rows has a source path or an absent marker | static | — | PLANNED |
| `B5I9-EX-10` | extraction | no extraction performed; deferred owner named | deferred | — | DEFERRED_WITH_OWNER |
| `B5I9-NP-01` | no_platform_law | zero control-plane files re-exported | test | `TestNoPlatform::test_no_reexport_of_control_plane_internals` | MAPPED |
| `B5I9-NP-02` | no_platform_law | public surface contains only EXTRACTABLE_* paths | test | `TestNoPlatform::test_no_private_module_in_public_surface` | MAPPED |
| `B5I9-NP-03` | no_platform_law | no consumer-side canonical store | test | `TestNoPlatform::test_no_second_canonical_state` | MAPPED |
| `B5I9-NP-04` | no_platform_law | no extracted admission/refusal/recovery decision | test | `TestNoPlatform::test_no_duplicated_authority_decision` | MAPPED |
| `B5I9-NP-05` | no_platform_law | ownership table has one claimant per function | test | `TestNoPlatform::test_single_owner_per_authority_function` | MAPPED |
| `B5I9-NP-06` | no_platform_law | schema declares one source; no duplicate key with a different default | test | `TestNoPlatform::test_single_configuration_truth` | MAPPED |
| `B5I9-NP-07` | no_platform_law | no absolute path, hostname or provider name | test | `TestNoPlatform::test_no_environment_or_host_embedded` | MAPPED |
| `B5I9-NP-08` | no_platform_law | network and broker symbol scans empty | test | `TestNoPlatform::test_no_cloud_or_execution_surface` | MAPPED |
| `B5I9-NP-09` | no_platform_law | provider and hosting name scan empty | test | `TestNoPlatform::test_no_cloud_or_provider_surface` | MAPPED |
| `B5I9-PK-01` | packaging | each artifact has Document ID, Version, Status, Stage | test | `TestProvenance::test_every_artifact_records_identity` | MAPPED |
| `B5I9-PK-02` | packaging | recorded sha256/size equal recomputation over LF-normalized bytes | test | `TestProvenance::test_manifest_rows_recomputed_from_bytes` | MAPPED |
| `B5I9-PK-03` | packaging | byte-identical output across two generations | test | `TestProvenance::test_generation_is_byte_identical` | MAPPED |
| `B5I9-PK-04` | packaging | digest pair equal | test | `TestProvenance::test_second_run_matches_first` | MAPPED |
| `B5I9-PK-05` | packaging | secret-pattern scan clean; no value echoed | test | `TestProvenance::test_no_secret_material` | MAPPED |
| `B5I9-PK-06` | packaging | oversized artifact fails with its size | test | `TestProvenance::test_artifact_size_rule_enforced` | MAPPED |
| `B5I9-PK-07` | packaging | import set and network-symbol scan | test | `TestProvenance::test_validator_stdlib_only_and_offline` | MAPPED |
| `B5I9-PK-08` | packaging | no runtime package produced; B5-I6/B6 ownership stated | static | — | PLANNED |
| `B5I9-PK-09` | packaging | network symbol and URL scan empty; absent network is not a failure | test | `TestProvenance::test_validator_performs_no_network_access` | MAPPED |
| `B5I9-HO-01` | book6_handoff | seven named states with independent values | test | `TestHandoff::test_seven_states_are_distinct` | MAPPED |
| `B5I9-HO-02` | book6_handoff | state triple reads false | test | `TestHandoff::test_book6_states_remain_false` | MAPPED |
| `B5I9-HO-03` | book6_handoff | no book6/b6 folder, branch, test, source or evidence file | test | `TestHandoff::test_no_book6_artifact_exists` | MAPPED |
| `B5I9-HO-04` | book6_handoff | list covers charter, lifecycle, kernel, evidence, laws, limitations, G16, hashes, main identity | test | `TestHandoff::test_consumable_evidence_list_is_complete` | MAPPED |
| `B5I9-HO-05` | book6_handoff | start conditions require the authorization token | test | `TestHandoff::test_start_requires_fresh_authorization` | MAPPED |
| `B5I9-HO-06` | book6_handoff | no agent self-ratifies the scope | attestation | — | PLANNED |
| `B5I9-HO-07` | book6_handoff | governance-complete state reads false | attestation | — | PLANNED |
| `B5I9-HO-08` | book6_handoff | no B6 implementation artifact | deferred | — | DEFERRED_WITH_OWNER |
| `B5I9-GA-01` | g16 | G16 status reads OPEN with the blocker id | test | `TestG16::test_g16_remains_open_with_owner` | MAPPED |
| `B5I9-GA-02` | g16 | missing condition quoted verbatim | test | `TestG16::test_missing_condition_carried_forward` | MAPPED |
| `B5I9-GA-03` | g16 | owner: independent auditor distinct from the implementer | static | — | PLANNED |
| `B5I9-GA-04` | g16 | blocking table states both facts | attestation | — | PLANNED |
| `B5I9-BD-01` | boundary | locks block reads false | test | `TestLocks::test_merge_authorized_false` | MAPPED |
| `B5I9-BD-02` | boundary | capital_authority none; no broker symbol | test | `TestLocks::test_no_capital_or_execution_authority` | MAPPED |
| `B5I9-BD-03` | boundary | cost 0; cloud mutations 0 | attestation | — | PLANNED |
| `B5I9-BD-04` | boundary | changed paths subset of declared set | test | `TestLocks::test_changed_file_boundary` | MAPPED |
| `B5I9-BD-05` | boundary | scratch paths absent; tracked tree clean | test | `TestLocks::test_no_scratch_residue` | MAPPED |

## 4. Closure rules

Requirement-to-node closure: every `test` row's node appears exactly once in the planned
surface and every inventory node belongs to exactly one requirement. Deferred closure:
every `deferred` row names a future stage and an owner. Failure closure: every declared
class is bound by at least one requirement, and every requirement's class is declared.

## 5. What acceptance will require (implementation stage, not P0)

Acceptance is not "the documents exist". It requires the 37 planned nodes to execute,
the 10 mutations to be discriminated with byte-exact restoration, a pristine rerun to
match, and the operator to ratify the extraction scope. Until then the stage is
`DRAFT FOR OPERATOR REVIEW`.
