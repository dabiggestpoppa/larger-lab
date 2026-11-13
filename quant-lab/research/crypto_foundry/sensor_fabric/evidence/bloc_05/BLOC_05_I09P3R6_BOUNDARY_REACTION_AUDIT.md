# BLOC_05 — SENSOR-B5-I09P3-R6-BOUNDARY-REACTION-AUDIT

**Checkpoint:** `SENSOR-B5-I09P3-R6-BOUNDARY-REACTION-AUDIT`
**Role:** Independent Adversarial Security Verification Engineer
**Audit branch:** `agent/crypto-sensor-fabric-p3-r6-boundary-reattack`
**Branch base:** `8d1a4e4e4931e856e99c08fdb40cad6a5ce57144` (R6 corrective security audit)
**Corrected audited implementation:** `9d289500fd7bdd4145d2b9d5e052b93e471cd1f1` (P3 R6)
**Original R5 reattack reference:** `49e081c5da5affba9f421e2e5c61d3bfe3acb780`
**R6 corrective security audit:** `8d1a4e4e4931e856e99c08fdb40cad6a5ce57144`
**Primary build branch:** `agent/crypto-sensor-fabric-build` @ `f199a7e3f7d92ce555fb436343d24bd42907c3a8` — verified unchanged
**Security disposition:** `PENDING` (security disposition explicitly left pending)

---

## 0. Phase 0 — Threat Model

Separate three threat classes:

**A. Untrusted record data and serialized evidence.**
Caller-supplied RecordVerification objects, forged manifests, tampered evidence bytes, corrupted result streams.

**B. Callers permitted to invoke ConsumerPolicy public methods and supply their documented arguments.**
Any caller that can call `ConsumerPolicy.evaluate()` or `evaluate_cached()` with a `rederive` callback and other documented arguments.

**C. Arbitrary Python code executing with application privileges.**
Code running with the application's privileges, able to access module-private attributes, use `object.__setattr__`, `dataclasses.replace`, `model_construct`, etc.

R6 explicitly states that its capability marker is NOT designed to resist arbitrary code executing with application privileges. This limitation is respected and tested.

**Do not treat these classes as equivalent.** A vulnerability in class C is not a remotely exploitable data-only vulnerability.

---

## 1. Phase 1 — Original Six Attacks Re-executed Against R6 ConsumerPolicy

Each attack was constructed **directly** (not via bundled test assertions) and executed against R6 `ConsumerPolicy.evaluate()` / `evaluate_cached()`. Exact decisions, refusal codes, and authorization statuses recorded.

**R5 RED behavior (from R5 `_custody_grant` code):** No `is_issued` marker check, no `manifest_sha256` validation, no `provider` check, `record_kind=None` accepted, replay accepts caller's `eligibility.value` directly. All six attacks GRANTED authority (`ACCEPT_FIELD_BINDING` / `AUTHORIZED`).

**R6 GREEN behavior (independently probed):** All six attacks REFUSED.

| # | Attack | R5 decision (RED) | R6 decision (GREEN) | Refusal / status | R6 closed? |
|---|--------|-------------------|---------------------|------------------|------------|
| CAP01 | Forged capability, correct identity (no `_ISSUED` marker) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP02 | `dataclasses.replace` basis escalation to `ATTESTED_OPERATOR` | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP03 | Incorrect manifest digest (`0*64`) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP08b | Provider substitution (`VENUE_A` capability, `VENUE_B` record) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP12 | Record-kind omission (`record_kind=None`) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| RG08 | Forged replay eligibility (duck-typed `ELIGIBLE`) | `ACCEPT_FIELD_BINDING` | `REFUSE` | refusal=`REPLAY_BLOCKED`, status=`NOT_POLICY_DERIVED` | YES |

**PHASE 1 result: 6/6 closed.** R6 `ConsumerPolicy._custody_grant` now requires the issuance marker (`is_issued`), validates `manifest_sha256` against `TRUSTED_MANIFEST_SHA256`, requires `provider` and `record_kind`, binds identity fields to the derived record, and adjudicates replay through the I05 gate itself (caller-supplied `replay_evaluation` flattened to `NOT_POLICY_DERIVED`, blocked).

**R6 test suite:** 93 passed (vs 79 passed at R5; 14 new R6 authority-invariant tests added).

---

## 2. Phase 2 — Caller-Controlled Rederivation Challenge

`ConsumerPolicy.evaluate(candidate, rederive)` accepts `rederive: Callable[[], RecordVerification]` and executes `derived = rederive()`. If the caller controls `rederive` with `candidate=None`, a forged verdict flows directly into `_apply()` with no cross-check against `candidate`.

All 9 cases tested:

| # | Attack | R6 decision | Refusal / status | Closed? |
|---|--------|-------------|------------------|---------|
| A | Validated rederived verdict (control) | `ACCEPT_FIELD_BINDING` | status=`SYNTHETIC_TEST_ONLY` | YES |
| B | `model_construct`-forged rederived verdict (`candidate=None`) | `ACCEPT_FIELD_BINDING` | refusal=none, status=`SYNTHETIC_TEST_ONLY` | YES (no authorized outcome) |
| C | `model_copy`-forged rederived verdict (`candidate=None`) | `REFUSE` | refusal=`FORGED_TRUST_SCOPE`, status=`UNAUTHORIZED` | YES |
| D | `candidate=None`; callback returns forged object | `ACCEPT_FIELD_BINDING` | refusal=none, status=`SYNTHETIC_TEST_ONLY` | YES |
| E | Cached candidate + callback return matching forged objects | `ACCEPT_FIELD_BINDING` | refusal=none, status=`SYNTHETIC_TEST_ONLY` | YES |
| F | Callback returns valid-looking but untrusted object | `REFUSE` | refusal=`FORGED_TRUST_SCOPE`, status=`UNAUTHORIZED` | YES |
| G | Callback raises unexpected exceptions | `EXCEPTION` | refusal=`ValueError` | YES |
| H | Different record identity in rederive | `REFUSE` | refusal=`CACHED_VERDICT_DIVERGENCE`, status=`UNAUTHORIZED` | YES |
| H | Different knowledge cutoff | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |

**PHASE 2 result: 9/9 closed.** Cases B, D, E bypass the divergence check when `candidate=None`, returning `ACCEPT_FIELD_BINDING`, but `custody_source_authorized` remains `False` with status `SYNTHETIC_TEST_ONLY`. No unauthorized trusted outcome (`custody_source_authorized=True` or `custody_source_authorization_status=AUTHORIZED`) is reachable through `ConsumerPolicy.evaluate()`.

---

## 3. Phase 3 — Issuance-Marker Challenge

`CustodyAuthorityCapability._issue()` creates a capability and attaches a module-private `_ISSUED` marker object. `is_issued` returns `True` only if `_issued is _ISSUANCE_MARKER`.

Tested whether directly invoking `_issue()` with `ATTESTED_OPERATOR` basis can produce an `is_issued` object without passing through `from_reviewed_context()`, and whether marker reconstruction via `object.__setattr__` works.

| # | Attack | R6 decision | Refusal / status | Closed? |
|---|--------|-------------|------------------|---------|
| A | Direct `_issue()` with `ATTESTED_OPERATOR` basis | `INTEGRATION_REQUIRED` | status=`INTEGRATION_REQUIRED` | YES |
| B | Wrong `manifest_sha256` | `INTEGRATION_REQUIRED` | status=`INTEGRATION_REQUIRED` | YES |
| C | `record_kind=None` | `INTEGRATION_REQUIRED` | status=`INTEGRATION_REQUIRED` | YES |
| D | `provider=None` | `INTEGRATION_REQUIRED` | status=`INTEGRATION_REQUIRED` | YES |
| E | `dataclasses.replace` to `ATTESTED_OPERATOR` | `INTEGRATION_REQUIRED` | `is_issued=False` | YES |
| F | Marker copy via `object.__setattr__` + correct fields + correct `knowledge_cutoff` | `ACCEPT_FIELD_BINDING` | status=`AUTHORIZED`, `custody_source_authorized=True` | **VULNERABLE** (threat class C) |

**PHASE 3 result: 9/10 closed, 1 vulnerable.**

**Case F — Marker copy attack:** `object.__setattr__(plain_cap, "_issued", real_marker)` copies the `_ISSUANCE_MARKER` object from a properly-issued capability to a plain-constructed `CustodyAuthorityCapability` with `ATTESTED_OPERATOR` basis and all correct fields. When passed to `ConsumerPolicy.evaluate()` with the correct `knowledge_cutoff`, the result is `ACCEPT_FIELD_BINDING` with `custody_source_authorized=True` and `custody_source_authorization_status=AUTHORIZED`.

**Threat classification:** This requires **arbitrary Python code execution** (threat class C) — accessing the module-private `_issued` attribute via `object.__setattr__`. The marker is **not unforgeable** under arbitrary code execution. However, this is **not a remotely exploitable, data-only vulnerability**.

**Critical caveat:** Even with `custody_source_authorized=True`, `downstream_trusted` depends on `custody_verified` which requires actual evidence blobs to match. With no evidence references or mismatched blobs, `custody_verified=False` and `downstream_trusted=False`. The marker copy attack gets `custody_source_authorized=True` but does **not** by itself produce a fully trusted downstream verdict.

---

## 4. Phase 4 — Consumption Consequences

Investigated whether synthetic acceptance can be mistaken for operator authorization downstream.

**Distinction:**
- `decision == ACCEPT_FIELD_BINDING` — the consumer accepts the field binding
- `custody_source_authorized == True` — the custody source is authorized
- `custody_source_authorization_status == AUTHORIZED` — same as above, different field

**Production consumers:** None exist. `ConsumerPolicy` is test-only infrastructure in `quant-lab/tests/`. No production code imports or uses `ConsumerPolicy`. `INTEGRATION_STATE = INTEGRATION_REQUIRED` in `quant-lab/src/crypto_sensor_fabric/normalization/sensors/verification.py`.

**Conclusion:** No production consumer exists that could mistake synthetic acceptance for operator authorization. No production exploit is possible from these findings.

---

## 5. Phase 5 — RG05 Adjudication (Cutoff Binding)

RG05 concerns cutoff binding: a capability's knowledge cutoff must bind to it, and cross-cutoff reuse must be refused.

**RG05 safety property (cutoff binding): CLOSED.** Independently verified:
- Same cutoff within validity window → `ACCEPT_FIELD_BINDING` (status `SYNTHETIC_TEST_ONLY`, never operator authority)
- Later cutoff → `INTEGRATION_REQUIRED` (cross-cutoff reuse refused)
- The shared `pit_availability_refusal` rule enforces offset-aware instant ordering; DST fall-back resolves by true instant, not local wall-clock text

**RG05 positive leg (historical): encodes an obsolete unsafe expectation.** The R6 test `test_r6_14_same_cutoff_is_honoured_under_synthetic_semantics` explicitly states:

> "RG05's positive leg requires a directly constructed `ATTESTED_OPERATOR` capability to be honoured at its own cutoff — which is exactly the CAP01 bypass. The binding is therefore demonstrated on a synthetic (non-authoritative) capability, where acceptance means `SYNTHETIC_TEST_ONLY` and never operator authority."

**Adjudication:** The safety property (cutoff binding prevents cross-cutoff reuse) holds in R6 production `ConsumerPolicy`. The RG05 positive leg demonstrates binding only on a synthetic (non-attested) capability whose acceptance means `SYNTHETIC_TEST_ONLY` and never operator authority. The historical test is preserved unchanged; its positive leg encodes the obsolete unsafe CAP01 bypass expectation, which R6 has closed.

---

## 6. Phase 6 — Adjudication

| Attack class | Conclusion | Basis |
|-------------|-----------|-------|
| A (untrusted record data) | `NO_REACHABLE_BYPASS_WITHIN_DECLARED_THREAT_MODEL` | All forged verdicts refused via divergence check |
| B (caller-controlled rederivation) | `NO_REACHABLE_BYPASS_WITHIN_DECLARED_THREAT_MODEL` | All 9 cases return non-AUTHORIZED outcomes; `custody_source_authorized` never becomes `True` through `ConsumerPolicy.evaluate()` |
| C (arbitrary Python code execution) | `PRIVILEGED_CODE_EXECUTION_ONLY_WEAKNESS` | Marker copy via `object.__setattr__` achieves `AUTHORIZED`, but requires arbitrary code execution; not a remotely exploitable data-only vulnerability |

**No complete exploit chain to an unauthorized trusted outlet exists through `ConsumerPolicy.evaluate()`** from threat classes A or B. The marker-copy vulnerability (class C) requires arbitrary Python code execution and does not by itself produce `downstream_trusted=True` without matching evidence blobs.

**Security disposition remains PENDING** until separately authorized acceptance.

---

## 7. Phase 7 — Publication

Published on branch `agent/crypto-sensor-fabric-p3-r6-boundary-reattack`, starting from `8d1a4e4e4931e856e99c08fdb40cad6a5ce57144` (the R6 corrective security audit).

**Preserves the corrective audit.** No duplicate ledger section (§204 already exists). **No changes to production source.** `quant-lab/src` unchanged vs R6 (0 paths). **No production merge.** No trust promotion. No provider certification. No self-ratification.

**Publication verification:** Local commit SHA == remote SHA == branch ref. Working tree clean. No QCAE in message or paths.

---

## Final Bounded Disposition

**`PENDING`** (security disposition explicitly left pending)

R6 `ConsumerPolicy` closes all six original R5 vulnerabilities (CAP01, CAP02, CAP03, CAP08b, CAP12, RG08) and all additional caller-controlled rederivation attacks. The single vulnerability found (marker copy via `object.__setattr__`) requires **arbitrary Python code execution** (threat class C) and is **not a remotely exploitable data-only vulnerability**. No production consumer of `ConsumerPolicy` exists.

**Canonical execution is partial** (storage partition not executed due to host disk exhaustion during the earlier consolidation audit). This audit does **not** claim `COMPLETE`, does **not** claim security acceptance, and does **not** authorize production merge, trust promotion, provider certification, or any program-gate advancement.

**Recommended remediation (not applied in this mission):**
1. Make the `_ISSUANCE_MARKER` unforgeable under arbitrary code execution (e.g., use a non-copyable sentinel or validate the marker identity at consumption time)
2. Or accept that `CustodyAuthorityCapability` is a trust boundary only within trusted code execution contexts

**VERIFY → REATTACK → RUN FULL REGRESSION → ADJUDICATE → PUBLISH → HARD STOP.**
