# MISSING IMPLEMENTATION REPORT

**Checkpoint:** SENSOR-B5-P3-SECURITY-TEST-PACKAGE-CORRECTION-R1
**Source design:** P3 production design R0 (commit `295acb5245ecc47d6f5c0a07f8ff631aa7217c15`)
**Test file:** `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py`
**Disposition:** SECURITY_TEST_SPECIFICATION_READY — EXECUTABLE_ACCEPTANCE_PENDING

This report documents the production modules that must exist before the 51
guarded security tests can execute. None of these modules exist in
`quant-lab/src/` at the current HEAD. No stub modules are committed under
`src/` (per the R0 design).

---

## 1. Missing production modules

| Module | Required symbols | Required by | Rung | Status |
|--------|-----------------|-------------|------|--------|
| `consumer/models.py` | `ConsumerRequest`, `ConsumerVerdict`, `ConsumerDecision`, `ConsumerRefusalReason`, `CustodyAuthorityBasis` | All guarded tests | R1 | NOT IMPLEMENTED |
| `consumer/policy.py` | `TrustConsumerPolicy` (with `evaluate(request) -> ConsumerVerdict`) | Most guarded tests | R2–R4 | NOT IMPLEMENTED |
| `consumer/custody_authority.py` | `derive_custody_authority()` | A20, A3.1, R6, X03 | R3 | NOT IMPLEMENTED |

### `consumer/models.py` (Rung 1)

Must define:
- `ConsumerRequest` — **no** field typed `RecordVerification`, `ConsumerVerdict`,
  `SemanticAuthority`, `TrustedAuthorityContext`, or any callable returning a
  verdict (A1.1). No `rederive` parameter (A2.1).
- `ConsumerDecision` — exactly `ACCEPT_FIELD_BINDING`, `REFUSE`,
  `INTEGRATION_REQUIRED` — no `ACCEPT`, no `AUTHORIZED` (A1.2).
- `ConsumerVerdict` — typed verdict with refusal vocabulary.
- `CustodyAuthorityBasis` — exactly `AUTHORIZED`, `INTEGRATION_REQUIRED`,
  `UNAUTHORIZED` — **no** `SYNTHETIC_TEST_ONLY` (A1.3).
- Frozen, `extra="forbid"`, naive-datetime-refusing model laws mirroring
  `NormalizationModelBase` (A1.4).

### `consumer/policy.py` (Rungs 2–4)

Must define `TrustConsumerPolicy` with:
- `evaluate(request: ConsumerRequest) -> ConsumerVerdict` — derives the verdict
  itself; **no** `rederive: Callable[[], RecordVerification]` parameter
  (R1, A2.1).
- Policy-owned root: `TrustedAuthorityContext` built from pinned manifest bytes
  (R2, spec A).
- `assert_trustworthy()` called on every derived verdict before inspection
  (A03, R2).
- Inspection in normative order: trust scope → unverified dimensions →
  evidence rebinding → fields → PIT → replay → authority (A10–A12, A13–A15,
  A17, R4).
- Evidence rebinding at consumption: one read per reference, re-hashed
  (A13, A14, R4).
- Fail-closed: typed refusal → mapped REFUSE; unexpected exception →
  `REFUSE VERIFIER_CRASH` with bounded detail (≤200 chars, no payload repr,
  no traceback); `KeyboardInterrupt`/`SystemExit` propagate (A18, R2).
- No cached verdict accepted; re-derivation every call (A16, R2).

### `consumer/custody_authority.py` (Rung 3)

Must define `derive_custody_authority()`:
- Inputs: pinned `manifest_bytes`, `artifact_id`, `approval_id`,
  `registry_digest`, `record_kind`, `provider`, `knowledge_cutoff`.
- Output: `(CustodyAuthorityBasis, status_detail)`.
- Under shipped manifest `{"artifacts": {}}` → `INTEGRATION_REQUIRED`, never
  `AUTHORIZED` (A20, A3.1).
- Pure function of its arguments; no global mutable state (R3).
- Any binding mismatch → `INTEGRATION_REQUIRED` (A07, A08, R6).

---

## 2. Why these modules are absent

The R0 design checkpoint (commit `295acb5245`) is **documentation only**:
"No implementation, no interface freeze, no stub modules committed under
`src/`." The three modules are **proposed** in `08_PROPOSED_CODE_PATHS.md`
(C1–C3) but implementation awaits a later directive (Rungs 1–4).

Agent 1 is building Rung 1 simultaneously (`agent/crypto-sensor-fabric-p3-consumer-rung1-r1`).
This security test package does **not** depend on Agent 1's unmerged code and
is kept isolated. The tests will execute against whatever production
implementation satisfies the interface contract in `08_PROPOSED_CODE_PATHS.md`.

---

## 3. Impact on test execution

| Metric | Value |
|--------|-------|
| Total guarded tests | 51 |
| Executable today | 0 |
| Tests that pass today | 1 (collection safety only) |
| Tests that fail today | 51 (all RED/PENDING with named import error) |
| Tests that would pass when production exists | 51 (if implementation satisfies the contract) |
| Tests that would fail when production exists | 0 (if implementation satisfies the contract) |

**No test is claimed as passing security evidence.** The 51 guarded tests
report RED/PENDING with the concrete import error until the production modules
exist.

---

## 4. No production source changes

This correction package:
- Does not modify any file under `quant-lab/src/`.
- Does not edit Agent 1's contract tests.
- Does not widen the frozen I10 allowlist.
- Does not create stub modules under `src/`.
- Does not activate authority, promote trust, certify providers, or self-ratify.
