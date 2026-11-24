# TEST DEPENDENCY MATRIX

**Checkpoint:** SENSOR-B5-P3-SECURITY-TEST-PACKAGE-CORRECTION-R1
**Source design:** P3 production design R0 (commit `295acb5245ecc47d6f5c0a07f8ff631aa7217c15`)
**Test file:** `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py`
**Disposition:** SECURITY_TEST_SPECIFICATION_READY — EXECUTABLE_ACCEPTANCE_PENDING

This matrix maps every guarded test to its production-module dependency and
Rung dependency. No test is executable until the corresponding production
modules are implemented.

---

## 1. Production module dependencies

The corrected test file imports from the following production modules at
module load. All are absent today (Rung 1–4 not merged):

| Module | Provides | Rung | Status |
|--------|----------|------|--------|
| `consumer/models.py` | `ConsumerRequest`, `ConsumerVerdict`, `ConsumerDecision`, `ConsumerRefusalReason`, `CustodyAuthorityBasis` | R1 | NOT IMPLEMENTED |
| `consumer/policy.py` | `TrustConsumerPolicy` (derive, inspect, rebind, fail-closed) | R2–R4 | NOT IMPLEMENTED |
| `consumer/custody_authority.py` | `derive_custody_authority()` (A3.1–A3.3) | R3 | NOT IMPLEMENTED |

These modules are **proposed** in `08_PROPOSED_CODE_PATHS.md` but do not exist
in `quant-lab/src/` at the current HEAD. No stub modules are committed under
`src/` (per the R0 design: "No implementation, no interface freeze, no stub
modules committed under `src/`").

---

## 2. Per-test dependency matrix

| Test ID | Test name | Production module | Rung | Runnable today | Unblocked by |
|---------|-----------|-------------------|------|----------------|--------------|
| — | test_module_collects_without_side_effects | none (collection only) | — | Yes | — |
| A01 | test_a01_forged_verdict_via_callback | models + policy | R1–R2 | No | R1, R2 merged |
| A02 | test_a02_model_construct_candidate_forgery | models + policy | R1–R2 | No | R1, R2 merged |
| A03 | test_a03_contradictory_trust_verification | policy | R2 | No | R2 merged |
| A04 | test_a04_caller_manifest_substitution | policy | R2 | No | R2 merged |
| A05 | test_a05_direct_issue_capability_minting | models + policy | R1–R3 | No | R1, R3 merged |
| A06 | test_a06_issuance_marker_copy | policy | R3 | No | R3 merged |
| A07 | test_a07_cross_record_authorization_reuse | custody_authority + policy | R2–R3 | No | R2, R3 merged |
| A08 | test_a08_cross_cutoff_authorization_reuse | custody_authority + policy | R2–R3 | No | R2, R3 merged |
| A09 | test_a09_synthetic_test_only_promotion | models | R1 | No | R1 merged |
| A10 | test_a10_forged_trust_scope | policy | R2 | No | R2 merged |
| A11 | test_a11_empty_unverified_dimensions | policy | R2 | No | R2 merged |
| A12 | test_a12_unverified_required_fields | policy | R2 | No | R2 merged |
| A13 | test_a13_evidence_substitution_after_verification | policy | R4 | No | R4 merged |
| A14 | test_a14_digest_only_custody_refused | policy | R4 | No | R4 merged |
| A15 | test_a15_forged_replay_eligibility | policy | R4 | No | R4 merged |
| A16 | test_a16_stale_cached_verdict | policy | R2 | No | R2 merged |
| A17 | test_a17_pit_inadmissible_yet_authorized | policy | R4 | No | R4 merged |
| A18 | test_a18_verifier_exception_fail_closed | policy | R2 | No | R2 merged |
| A19 | test_a19_missing_provenance | policy | R2 | No | R2 merged |
| A20 | test_a20_empty_manifest_as_authorization | custody_authority | R3 | No | R3 merged |
| — | test_exception_details_do_not_expose_payload_bytes | policy | R2 | No | R2 merged |
| — | test_exception_details_length_bounded | policy | R2 | No | R2 merged |
| — | test_keyboard_interrupt_and_system_exit_propagate | policy | R2 | No | R2 merged |
| — | test_policy_applies_replay_assessment_itself | policy | R4 | No | R4 merged |
| — | test_pit_refusal_ordering_precedes_authorization | policy | R4 | No | R4 merged |
| — | test_evidence_read_exactly_once_per_reference | policy | R4 | No | R4 merged |
| — | test_evidence_rehashed_at_consumption | policy | R4 | No | R4 merged |
| — | test_no_cached_verdict_is_authoritative | policy | R2 | No | R2 merged |
| — | test_no_wall_clock_dependent_decision | policy | R2 | No | R2 merged |
| — | test_invalid_requests_refuse_rather_than_authorize | policy | R2 | No | R2 merged |
| X01 | test_x01_t4_rewrites_manifest_pin_is_out_of_scope | models + policy | R1–R2 | No | R1, R2 merged |
| X02 | test_x02_t4_monkeypatches_verifier_is_out_of_scope | models + policy | R1–R2 | No | R1, R2 merged |
| X03 | test_x03_t4_replaces_custody_provider_is_out_of_scope | models + policy | R1–R3 | No | R1, R3 merged |
| X04 | test_x04_side_channel_dos_is_out_of_scope | — | — | No | documentation only |
| X05 | test_x05_physical_host_compromise_is_out_of_scope | — | — | No | documentation only |
| X06 | test_x06_future_operator_authority_semantics_is_out_of_scope | — | — | No | documentation only |
| CAP01 | test_cap01_direct_issue_is_threat_class_c_not_remote | models + policy | R1–R3 | No | R1, R3 merged |
| CAP02 | test_cap02_marker_copy_is_threat_class_c_not_remote | policy | R3 | No | R3 merged |
| R1 | test_harness_vs_production_rederive_callback | models | R1 | No | R1 merged |
| R2 | test_harness_vs_production_capability_object | models | R1 | No | R1 merged |
| R3 | test_harness_vs_production_marker_copy | policy | R3 | No | R3 merged |
| R4 | test_harness_vs_production_synthetic_basis | models | R1 | No | R1 merged |
| R5 | test_harness_vs_production_manifest_handling | policy | R2 | No | R2 merged |
| R6 | test_harness_vs_production_cross_cutoff | custody_authority + policy | R2–R3 | No | R2, R3 merged |
| R7 | test_harness_vs_production_replay | policy | R4 | No | R4 merged |
| A1.1 | test_consumer_request_has_no_verdict_typed_field | models | R1 | No | R1 merged |
| A1.2 | test_consumer_decision_has_exactly_three_members | models | R1 | No | R1 merged |
| A1.3 | test_custody_authority_basis_has_exactly_three_members | models | R1 | No | R1 merged |
| A2.1 | test_no_rederive_parameter_on_intake_path | models | R1 | No | R1 merged |
| A3.1 | test_empty_manifest_never_produces_authorized | custody_authority | R3 | No | R3 merged |
| A3.2 | test_no_capability_object_in_production_src | models | R1 | No | R1 merged |

---

## 3. Rung dependency summary

| Rung | Scope | Tests blocked | Status |
|------|-------|---------------|--------|
| R1 | consumer/models.py — types and laws | A01, A02, A05, A09, X01, X02, X03, CAP01, R1, R2, R4, A1.1, A1.2, A1.3, A2.1, A3.2 | NOT IMPLEMENTED |
| R2 | consumer/policy.py — derivation ownership | A01–A19 (most), X01, X02, CAP01, CAP02, R5, A2.1 | NOT IMPLEMENTED |
| R3 | consumer/custody_authority.py — custody authority derivation | A05, A06, A07, A08, A20, X03, CAP02, R3, R6, A3.1 | NOT IMPLEMENTED |
| R4 | consumer/rebinding.py — replay, PIT, evidence rebinding | A13–A15, A17, A17-variant cases, R7 | NOT IMPLEMENTED |

All 51 guarded tests are blocked on at least one unimplemented Rung. The single
executable test (`test_module_collects_without_side_effects`) has no production
dependency.

---

## 4. What unblocks execution

For all 51 guarded tests to execute against real production code:

1. **Rung 1 merged:** `consumer/models.py` exists with `ConsumerRequest`,
   `ConsumerVerdict`, `ConsumerDecision`, `ConsumerRefusalReason`,
   `CustodyAuthorityBasis` (exactly 3 members each for Decision and Basis;
   no verdict-typed fields on `ConsumerRequest`; no `rederive` parameter;
   no `SYNTHETIC_TEST_ONLY`).

2. **Rung 2 merged:** `consumer/policy.py` exists with `TrustConsumerPolicy`
   that derives verdicts itself (no callback), inspects in normative order,
   rebinds evidence, and fails closed.

3. **Rung 3 merged:** `consumer/custody_authority.py` exists with
   `derive_custody_authority()` that returns `INTEGRATION_REQUIRED` under the
   shipped empty manifest and never `AUTHORIZED`.

4. **Rung 4 merged:** replay/PIT/evidence-rebinding ordering implemented with
   PIT/replay before authority and one read per reference per consumption.

Until all four rungs are merged, every guarded test reports RED/PENDING with
the missing import error. This is the correct, honest state: the tests are
specification-ready but execution-pending.
