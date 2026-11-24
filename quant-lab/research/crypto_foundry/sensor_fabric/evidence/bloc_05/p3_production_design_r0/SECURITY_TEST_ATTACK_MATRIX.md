# SECURITY TEST ATTACK-TO-ASSERTION MATRIX

**Checkpoint:** SENSOR-B5-P3-SECURITY-TEST-PACKAGE-CORRECTION-R1
**Source design:** P3 production design R0 (commit `295acb5245ecc47d6f5c0a07f8ff631aa7217c15`)
**Reference branch:** `agent/crypto-sensor-fabric-p3-consumer-security-r1` (HEAD `16b4a0b2e`)
**Test file:** `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py`
**Disposition:** SECURITY_TEST_SPECIFICATION_READY — EXECUTABLE_ACCEPTANCE_PENDING

This document maps every prevented attack (A01–A20), out-of-scope condition
(X01–X06), threat-model correctness check (CAP01/CAP02), R5/R6 comparison
check (R1–R7), and production interface contract check (A1.1–A3.1) to its
concrete assertions in the corrected test package.

All 51 guarded tests currently report RED/PENDING because the production
consumer modules (`consumer/models.py`, `consumer/policy.py`,
`consumer/custody_authority.py`) do not yet exist (Rung 1–4 not merged).
No test is claimed as passing security evidence.

---

## 1. Attack matrix — A01–A20 (prevented attacks from 04_THREAT_MODEL.md)

| ID | Attack | Concrete input construction | API entry point | Expected safe decision | Forbidden outcome | Assertions | Rung dep | Runnable today |
|----|--------|----------------------------|-----------------|------------------------|-------------------|------------|----------|----------------|
| A01 | Forged verdict via factory callback | ConsumerRequest with no callback field; policy derives verdict itself | `TrustConsumerPolicy.evaluate(request)` | Not `ACCEPT_FIELD_BINDING` | Caller-supplied forged verdict accepted | `verdict.decision != ACCEPT_FIELD_BINDING`; no `rederive` field on `ConsumerRequest` | R1–R2 | No (RED/PENDING) |
| A02 | model_construct/model_copy verdict forgery as candidate | Forged RecordVerification with `trust_scope=FULL_RECORD_TRUST` passed as candidate | `evaluate()` (no candidate parameter) | Divergence refusal, not acceptance | Forged candidate accepted in place of derivation | `verdict.decision != ACCEPT_FIELD_BINDING or status != AUTHORIZED` | R1–R2 | No (RED/PENDING) |
| A03 | Contradictory trust verification | model_copy(forgery) bypassing trust laws | `evaluate()` calls `assert_trustworthy()` on derived verdict | `CONTRADICTORY_VERIFICATION` refusal | Contradictory verdict accepted | `assert_trustworthy()` called before inspection; refusal on contradiction | R2 | No (RED/PENDING) |
| A04 | Caller-controlled manifest substitution | `claimed_manifest_bytes` set to forged bytes | `evaluate(request)` | Derives from pinned root only; claimed bytes compared, never adopted | Claimed bytes adopted as derivation root | `verdict.decision != ACCEPT_FIELD_BINDING` | R2 | No (RED/PENDING) |
| A05 | Direct issuance-capability minting | No capability object presented (none exists in production) | `evaluate(request)` | No capability-typed field on `ConsumerRequest` | Capability object accepted for authorization | No `capability`/`authority_object` field; `status != AUTHORIZED` | R1–R3 | No (RED/PENDING) |
| A06 | Issuance-marker copy | No `_issued` marker exists in production | `evaluate(request)` | Nothing to copy; recomputation from pinned bytes | Copied marker grants authorization | `custody_source_authorization_status != AUTHORIZED` | R3 | No (RED/PENDING) |
| A07 | Cross-record authorization reuse | `record_kind="LIQUIDATION"`, `provider="VENUE_B"` with VENUE_A/TRADE evidence | `evaluate(request)` | Identity tuple bound into derivation; reuse blocked | Evidence from one record authorizes another | `status != AUTHORIZED` | R2–R3 | No (RED/PENDING) |
| A08 | Cross-cutoff authorization reuse | `knowledge_cutoff` changed to a different instant | `evaluate(request)` | Cutoff is derivation input; change → `INTEGRATION_REQUIRED` | Cutoff mismatch inherits authorization | `status != AUTHORIZED` | R2–R3 | No (RED/PENDING) |
| A09 | SYNTHETIC_TEST_ONLY promotion | No `SYNTHETIC_TEST_ONLY` member exists | `evaluate(request)` | Basis has exactly 3 members; no synthetic | Synthetic basis accepted as authorized | `"SYNTHETIC_TEST_ONLY" not in basis names`; `status != AUTHORIZED` | R1 | No (RED/PENDING) |
| A10 | Forged trust scope | Verdict with `trust_scope != ECONOMIC_FIELD_BINDING` | Inspection 1 | `FORGED_TRUST_SCOPE` refusal | Non-ECONOMIC_FIELD_BINDING scope accepted | `decision == REFUSE or refusal_reason == FORGED_TRUST_SCOPE` | R2 | No (RED/PENDING) |
| A11 | Empty unverified dimensions | Verdict with `unverified_dimensions=()` | Inspection 2 | `EMPTY_UNVERIFIED_DIMENSIONS` refusal | Empty dimensions read as whole-record auth | `decision == REFUSE or refusal_reason == EMPTY_UNVERIFIED_DIMENSIONS` | R2 | No (RED/PENDING) |
| A12 | Unverified required fields | Required field not in `fields_verified` | `evaluate(request)` | `FIELD_NOT_IN_ALLOWLIST` refusal | Caller-demanded unverified field accepted | `decision == REFUSE or refusal_reason == FIELD_NOT_IN_ALLOWLIST` | R2 | No (RED/PENDING) |
| A13 | Evidence substitution after verification | Evidence bytes swapped between derive and inspect | Rebinding at consumption | Bytes replaced → `EVIDENCE_BYTES_MISMATCH`; removed → `EVIDENCE_BYTES_MISSING` | Cached digest trusted without re-read | `decision != ACCEPT_FIELD_BINDING or status != AUTHORIZED` | R4 | No (RED/PENDING) |
| A14 | Digest-only custody | Custody object echoes digest without holding bytes | Rebinding requires readable bytes | Missing bytes → refuse; digest-only report not evidence | Digest-only custody accepted | `status != AUTHORIZED` | R4 | No (RED/PENDING) |
| A15 | Forged replay eligibility | Caller-supplied replay evaluation object | Policy applies `assess_replay_eligibility` to `ReplayEvidence` | Flattened to `NOT_POLICY_DERIVED`, blocked | Caller eligibility flag honored | `decision != ACCEPT_FIELD_BINDING or status != AUTHORIZED` | R4 | No (RED/PENDING) |
| A16 | Stale cached verdict | Cached verdict after revocation/cutoff move | Re-derivation every call | Cache never authoritative; divergence refuses | Cached verdict accepted over fresh derivation | `decision != ACCEPT_FIELD_BINDING or status != AUTHORIZED` | R2 | No (RED/PENDING) |
| A17 | PIT-inadmissible yet authorized | `pit_admissible=False` record | PIT/replay adjudicated before authority | Refused before authority check | Custody overrides PIT refusal | `decision == REFUSE or refusal_reason == PIT_INADMISSIBLE` | R4 | No (RED/PENDING) |
| A18 | Verifier exception / fail-open | Verifier raises unexpected exception | `_fail_closed` maps to `REFUSE VERIFIER_CRASH` | Refuses, never degrades open | Error converted to acceptance | `decision != ACCEPT_FIELD_BINDING` | R2 | No (RED/PENDING) |
| A19 | Missing provenance | `authority_provenance is None` | Verifier refuses `PROVENANCE_MISSING` | Refused; no synthetic admission | Missing provenance treated as admissible | `decision == REFUSE or refusal_reason == PROVENANCE_MISSING` | R2 | No (RED/PENDING) |
| A20 | Empty manifest as authorization | Shipped manifest `{"artifacts": {}}` | Derivation from pinned manifest bytes | `INTEGRATION_REQUIRED`, never `AUTHORIZED` | Empty manifest treated as "no restrictions" | `status != AUTHORIZED` | R3 | No (RED/PENDING) |

### Additional security cases (06_ACCEPTANCE_MATRIX.md §3)

| ID | Case | Assertion | Rung dep | Runnable today |
|----|------|-----------|----------|----------------|
| — | Exception details do not expose payload bytes | `refusal_detail` excludes artifact bytes, manifest, evidence digest | R2 | No (RED/PENDING) |
| — | Exception details length-bounded | `len(refusal_detail) <= 200` for crashes | R2 | No (RED/PENDING) |
| — | KeyboardInterrupt/SystemExit propagate | Not swallowed by consumer | R2 | No (RED/PENDING) |
| — | Policy applies replay assessment itself | Policy owns replay (R3) | R4 | No (RED/PENDING) |
| — | PIT/refusal ordering precedes authorization | PIT/replay before authority | R4 | No (RED/PENDING) |
| — | Evidence read exactly once per reference | One read per reference per consumption (R-08) | R4 | No (RED/PENDING) |
| — | Evidence re-hashed at consumption | Re-hashing at consumption time | R4 | No (RED/PENDING) |
| — | No cached verdict is authoritative | Identical inputs → identical verdicts | R2 | No (RED/PENDING) |
| — | No wall-clock-dependent decision | Deterministic derivation | R2 | No (RED/PENDING) |
| — | Invalid requests refuse rather than authorize | Invalid → REFUSE, never AUTHORIZED | R2 | No (RED/PENDING) |

---

## 2. Out-of-scope matrix — X01–X06 (documented, not defended)

| ID | Condition | Why out of scope | Assertion | Runnable today |
|----|-----------|-----------------|-----------|----------------|
| X01 | T4 rewrites manifest pin | Pin is compile-time constant; T4 can rewrite constants | Pin exists; policy does not adopt caller manifest | No (RED/PENDING) |
| X02 | T4 monkeypatches verifier | Mitigation is process isolation/code review, not a Python sentinel | Policy does not adopt monkeypatched verifier | No (RED/PENDING) |
| X03 | T4 replaces custody provider | Store is T3-supplied wiring; hostile wiring = compromised process | Policy does not adopt hostile custody provider | No (RED/PENDING) |
| X04 | Side-channel/DoS | Availability, not integrity; bound at API edge | Documented, not defended | No (RED/PENDING) |
| X05 | Physical/host compromise | Outside application boundary | Documented, not defended | No (RED/PENDING) |
| X06 | Future operator authority semantics | Governance, not code; empty manifest ships | Documented, not defended | No (RED/PENDING) |

---

## 3. Threat-model correctness — CAP01/CAP02

| ID | Observation | Threat class | Production defense | Assertion | Runnable today |
|----|-------------|--------------|-------------------|-----------|----------------|
| CAP01 | Direct `CustodyAuthorityCapability._issue()` | C (arbitrary code execution) | No capability object in production | `status != AUTHORIZED` | No (RED/PENDING) |
| CAP02 | Marker copy via `object.__setattr__` | C (arbitrary code execution) | Nothing to copy; no marker object | `status != AUTHORIZED` | No (RED/PENDING) |

**Classification note:** Both are threat-class C observations from the R6 audit
(package head `5be77af4b`). They require application-level Python execution.
They are NOT relabeled as remotely exploitable.

---

## 4. R5/R6-to-production comparison matrix

| ID | Harness behavior | Production behavior | Semantic difference | Runnable today |
|----|-----------------|-------------------|-------------------|----------------|
| R1 | `rederive: Callable` trusted after the fact | No callback; policy derives | Derivation replaces assertion | No (RED/PENDING) |
| R2 | `CustodyAuthorityCapability` with `_issue()` | No capability object | Recomputation replaces presentation | No (RED/PENDING) |
| R3 | Marker copy → AUTHORIZED (threat class C) | Nothing to copy | Marker model removed entirely | No (RED/PENDING) |
| R4 | `SYNTHETIC_TEST_ONLY` basis | Exactly 3 basis members, no synthetic | Synthetic state removed | No (RED/PENDING) |
| R5 | Context pins reviewed root | Same + claimed bytes never adopted | Claimed bytes are input only | No (RED/PENDING) |
| R6 | `capability.knowledge_cutoff` compared | Cutoff is derivation input | Cutoff as input, not comparable field | No (RED/PENDING) |
| R7 | Caller replay object flattened | Policy applies `assess_replay_eligibility` | Same direction, production owns replay fully | No (RED/PENDING) |

Expected design divergence is explicitly **not** treated as a security regression.

---

## 5. Production interface contract (A1.1–A3.1)

| ID | Requirement | Assertion | Runnable today |
|----|-------------|-----------|----------------|
| A1.1 | `ConsumerRequest` has no verdict-typed field | No field typed `RecordVerification`/`ConsumerVerdict`/etc. | No (RED/PENDING) |
| A1.2 | `ConsumerDecision` has exactly 3 members | `ACCEPT_FIELD_BINDING`, `REFUSE`, `INTEGRATION_REQUIRED` | No (RED/PENDING) |
| A1.3 | `CustodyAuthorityBasis` has exactly 3 members | `AUTHORIZED`, `INTEGRATION_REQUIRED`, `UNAUTHORIZED` | No (RED/PENDING) |
| A2.1 | No `rederive` parameter on intake path | No `Callable[[], RecordVerification]` parameter | No (RED/PENDING) |
| A3.1 | Empty manifest never produces `AUTHORIZED` | `status != AUTHORIZED` under `{"artifacts": {}}` | No (RED/PENDING) |
| A3.2 | No capability object in `src/` | No `_issue`/`capability`-typed field | No (RED/PENDING) |

---

## 6. Runnable status summary

| Category | Count | Runnable today | Status |
|----------|-------|----------------|--------|
| Collection safety | 1 | Yes | PASSES |
| A01–A20 attacks | 20 | No | RED/PENDING |
| Additional security cases | 10 | No | RED/PENDING |
| X01–X06 out-of-scope | 6 | No | RED/PENDING |
| CAP01/CAP02 classification | 2 | No | RED/PENDING |
| R5/R6 comparison | 7 | No | RED/PENDING |
| Interface contract | 6 | No | RED/PENDING |
| **Total guarded** | **51** | **No** | **RED/PENDING** |
| **Grand total** | **52** | **1** | **51 RED/PENDING + 1 pass** |

**Do not claim 51 executable or passing security tests.** The 51 guarded tests
are written and structurally complete but cannot execute until the production
consumer modules (Rung 1–4) are implemented.
