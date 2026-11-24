# I10 SCOPE FINDING AND PROPOSED EXECUTABLE-TEST PLAN

**Checkpoint:** SENSOR-B5-P3-SECURITY-TEST-PACKAGE-CORRECTION-R1
**Source design:** P3 production design R0 (commit `295acb5245ecc47d6f5c0a07f8ff631aa7217c15`)
**Test file:** `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py`
**Disposition:** SECURITY_TEST_SPECIFICATION_READY — EXECUTABLE_ACCEPTANCE_PENDING

---

## 1. I10 scope finding (Phase 0, finding #3)

### The constraint

The frozen I10 scope audit
(`quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i10_scope_audit.py`,
function `test_only_the_i10_authorized_prefixes_carry_tracked_changes`)
maintains an explicit allowlist of named path prefixes that may carry tracked
changes. The allowlist includes:

- `tests/crypto_sensor_fabric/normalization/test_b5_i09p2a_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i09p2b_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i09p2c_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i09p2d_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i10_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i11_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i11r1_`
- `tests/crypto_sensor_fabric/normalization/test_b5_i11f1_`
- Plus individually named scope-audit files.

### The finding

`test_b5_p3_consumer_security.py` does **not** match any allowed prefix. The
I10 scope audit explicitly rejects it:

```
E   AssertionError: unauthorized staged path:
E   tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py
```

This was confirmed by running the I10 scope audit against the branch containing
the test file. The path is unauthorized under the frozen I10 allowlist.

### What is NOT done (per mission constraints)

- The test file is **not** renamed to an older checkpoint prefix (e.g.
  `test_b5_i11_`) merely to bypass I10. That would misrepresent the test's
  provenance and circumvent governance.
- The I10 allowlist is **not** widened. No changes to frozen plans.
- The I10 scope audit is **not** modified.

### Disposition

The unauthorized existing branch (`agent/crypto-sensor-fabric-p3-consumer-security-r1`,
HEAD `16b4a0b2e`) remains isolated. The test file is admitted only as
external research evidence under `evidence/bloc_05/p3_production_design_r0/`
(the governance-admitted prefix per `08_PROPOSED_CODE_PATHS.md` §5) until its
file path is explicitly admitted to the canonical test universe or the artifact
is explicitly classified as external research evidence.

---

## 2. Governance authorization needed for admission

To admit `test_b5_p3_consumer_security.py` to the canonical test universe, one
of the following is required:

### Option A — Add a named prefix entry (recommended)

Add `tests/crypto_sensor_fabric/normalization/test_b5_p3_` as a named entry in
the `allowed` tuple of
`test_only_the_i10_authorized_prefixes_carry_tracked_changes` in
`test_b5_i10_scope_audit.py`. This follows the existing precedent where each
distinct checkpoint suite (i09p2a–e, i11r1, i11f1) is admitted by its own
named entry rather than by widening a prefix.

This is a **governance change** requiring the same directive-level approval as
any other allowlist amendment. It does not widen an existing prefix; it adds a
distinct named entry, consistent with the existing pattern.

### Option B — Classify as external research evidence

Keep the test file outside the canonical test universe, published only under
`evidence/bloc_05/p3_production_design_r0/` (the admitted governance prefix).
The tests remain specification-ready but not part of the executed test suite
until Option A is approved.

---

## 3. Proposed executable-test plan

### Phase A: Governance (immediate, no code required)

1. **Classify the test file** as external research evidence under
   `evidence/bloc_05/p3_production_design_r0/` (done — this package).
2. **Document the I10 scope finding** (done — this document).
3. **Request Option A prefix admission** via the normal governance change
   process. Do not rename the file to bypass I10.

### Phase B: Production implementation (Agent 1, Rungs 1–4)

1. **Rung 1:** Implement `consumer/models.py` per `08_PROPOSED_CODE_PATHS.md` C1.
   - `ConsumerRequest` with no verdict-typed fields, no `rederive` parameter.
   - `ConsumerDecision` with exactly 3 members.
   - `CustodyAuthorityBasis` with exactly 3 members, no `SYNTHETIC_TEST_ONLY`.
2. **Rung 2:** Implement `consumer/policy.py` derivation ownership per C3.
3. **Rung 3:** Implement `consumer/custody_authority.py` per C2.
4. **Rung 4:** Implement evidence rebinding, replay/PIT ordering.

### Phase C: Test execution (after Rungs 1–4 merged)

1. Run `pytest quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py -v`.
2. All 51 guarded tests should execute against real production code.
3. Each test asserts its specific control (see `SECURITY_TEST_ATTACK_MATRIX.md`).
4. Any test that passes merely because all requests return `INTEGRATION_REQUIRED`
   is a false positive and must be redesigned.

### Phase D: Canonical admission (after tests pass)

1. Re-run the I10 scope audit — must pass with the test file present.
2. If Option A was approved, the allowlist now includes `test_b5_p3_`.
3. The test file becomes part of the canonical test universe.

---

## 4. Exact requirements for admission

| Requirement | Description | Status |
|-------------|-------------|--------|
| R-A | Governance approval to add `test_b5_p3_` named prefix to I10 allowlist (Option A), OR explicit classification as external research evidence (Option B) | PENDING |
| R-B | Rung 1: `consumer/models.py` implemented per design spec | NOT IMPLEMENTED |
| R-C | Rung 2: `consumer/policy.py` implemented per design spec | NOT IMPLEMENTED |
| R-D | Rung 3: `consumer/custody_authority.py` implemented per design spec | NOT IMPLEMENTED |
| R-E | Rung 4: evidence rebinding, replay/PIT ordering implemented | NOT IMPLEMENTED |
| R-F | All 51 guarded tests execute against real production code (not RED/PENDING) | BLOCKED on R-B–R-E |
| R-G | I10 scope audit passes with the test file present | BLOCKED on R-A |
| R-H | No test passes merely because all requests return `INTEGRATION_REQUIRED` | To be verified at R-F |

Until R-A and R-B through R-E are satisfied, the test package remains
SECURITY_TEST_SPECIFICATION_READY — EXECUTABLE_ACCEPTANCE_PENDING.
