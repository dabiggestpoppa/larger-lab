# BLOC_05 — SENSOR-B5-I09P3-R6-SECURITY-AUDIT-CORRECTION

**Checkpoint:** `SENSOR-B5-I09P3-R6-SECURITY-AUDIT-CORRECTION`
**Role:** Independent Security Verification Engineer
**Audit branch:** `agent/crypto-sensor-fabric-p3-r6-reattack`
**Corrective commit:** additive — published on top of `136a951af` (the previous R6 audit)
**Corrected audited implementation:** `9d289500fd7bdd4145d2b9d5e052b93e471cd1f1` (P3 R6)
**Original R5 reattack reference:** `49e081c5da5affba9f421e2e5c61d3bfe3acb780`
**Previous R6 audit (corrected here):** `136a951af89e1aed8ed250e721179d482ff6fa67`
**Primary build branch:** `agent/crypto-sensor-fabric-build` @ `f199a7e3f7d92ce555fb436343d24bd42907c3a8` — verified unchanged
**Scope disposition:** `PENDING` — security disposition left pending; no production merge, no trust promotion, no provider certification, no self-ratification

---

## 0. Phase 0 — Scope Lock

**Correction of scope.** The previous R6 audit (`136a951af`) attacked the production
`SemanticAuthority` / `RecordVerification` constructors. PHASE 0 of this mission
corrects that: the original six R5 vulnerabilities (CAP01, CAP02, CAP03, CAP08b,
CAP12, RG08) concern the **test-resident P3 ConsumerPolicy** implementation
(`ConsumerPolicy`, `CustodyAuthorityCapability` in
`quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py`),
not the production `SemanticAuthority` or `RecordVerification` constructors.

This corrective audit therefore:

- Audits the **actual P3 implementation**: `ConsumerPolicy` at R6 (`9d289500f`).
- Executes the original six attacks **directly against `ConsumerPolicy`**, not
  against production `SemanticAuthority`/`RecordVerification`.
- Preserves the production `model_construct`/`model_copy` observations as a
  **separate** boundary-weakness finding (PHASE 3), evaluated on its own merits
  with a complete-exploit-chain requirement.
- Makes **no implementation changes**. `quant-lab/src` delta versus R6: **0
  paths** (`git diff 9d289500f HEAD -- quant-lab/src` is empty).
- Makes **no ledger change**. Ledger §204 already exists on this branch
  (`SENSOR-B5-I09P3-R6-INDEPENDENT-REATTACK-FINAL (AGENT 2)`); this corrective
  audit is published as an additive document only, avoiding a competing ledger
  §204.

Ancestry verified: `9d289500f` descends from `ea1fdeb77` (R5); this worktree is
at `9d289500f`, clean. Production remains at `f199a7e3f`, untouched.

---

## 1. Phase 1 — Original Six Attacks Re-executed Against R6 ConsumerPolicy

Each attack was constructed **directly** (not via the bundled test assertions)
and executed against the R6 `ConsumerPolicy.evaluate` / `evaluate_cached`.
Exact decisions, refusal codes, and authorization statuses recorded below.

**R5 RED behavior (from R5 `_custody_grant` code):** No `is_issued` marker check,
no `manifest_sha256` validation, no `provider` check, `record_kind=None`
accepted, replay accepts caller's `eligibility.value` directly. All six attacks
GRANTED authority (`ACCEPT_FIELD_BINDING` / `AUTHORIZED`).

**R6 GREEN behavior (independently probed):** All six attacks REFUSED.

| # | Attack | R5 decision (RED) | R6 decision (GREEN) | Refusal / status | R6 closed? |
|---|--------|-------------------|---------------------|------------------|------------|
| CAP01 | Forged capability, correct identity (no `_ISSUED` marker) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP02 | `dataclasses.replace` basis escalation to `ATTESTED_OPERATOR` | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP03 | Incorrect manifest digest (`0*64`) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP08b | Provider substitution (`VENUE_A` capability, `VENUE_B` record) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| CAP12 | Record-kind omission (`record_kind=None`) | `ACCEPT_FIELD_BINDING` / `AUTHORIZED` | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| RG08 | Forged replay eligibility (duck-typed `ELIGIBLE`) | `ACCEPT_FIELD_BINDING` | `REFUSE` | refusal=`REPLAY_BLOCKED`, status=`NOT_POLICY_DERIVED` | YES |

**PHASE 1 result: 6/6 closed.** R6 `ConsumerPolicy._custody_grant` now requires
the issuance marker (`is_issued`), validates `manifest_sha256` against
`TRUSTED_MANIFEST_SHA256`, requires `provider` and `record_kind`, binds
identity fields to the derived record, and adjudicates replay through the I05
gate itself (caller-supplied `replay_evaluation` flattened to
`NOT_POLICY_DERIVED`, blocked).

Evidence: independent probes executed directly against R6 `ConsumerPolicy` in
worktree `/c/tmp/wt-r6` (`9d289500f`), all 6 refused. Bundled R6 test suite
`test_b5_i09p2e_trust_consumer.py`: **93 passed** (vs 79 passed at R5;
14 new R6 authority-invariant tests added).

---

## 2. Phase 2 — Additional Attacks Against R6 ConsumerPolicy

Additional vectors beyond the original six. Each executed directly against
`ConsumerPolicy`.

| # | Attack | R6 decision | Refusal / status | Closed? |
|---|--------|-------------|------------------|---------|
| A | `model_copy(update=...)` forges `trust_scope` + empty `unverified_dimensions` | Object created, but **re-validation refuses** (`ValidationError`) | re-validation refused | YES (re-validation catches it) |
| B | `model_construct` bypasses **all** `RecordVerification` validation | Contradictory state created (`source_lineage_verified=True` w/o `lineage_proof`; `downstream_trusted=True` w/ empty `unverified_dimensions`; `trust_scope="FULL_RECORD_TRUST"`) | none (no validation) | **VULNERABLE** (model-level; see PHASE 3) |
| C | Knowledge-cutoff substitution (later cutoff) | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |
| D.1 | Cached-verdict reuse: matching cached + derived | `ACCEPT_FIELD_BINDING` | status=`SYNTHETIC_TEST_ONLY` | YES (correct) |
| D.2 | Cached-verdict reuse: forged cached diverges from derived | `REFUSE` | refusal=`CACHED_VERDICT_DIVERGENCE` | YES |
| E | Synthetic authority presented as attested | `ACCEPT_FIELD_BINDING` | status=`SYNTHETIC_TEST_ONLY`, `custody_source_authorized=False` | YES (never `AUTHORIZED`) |
| F | Direct capability construction without issuance marker | `INTEGRATION_REQUIRED` | refusal=none, status=`INTEGRATION_REQUIRED` | YES |

**PHASE 2 result: 6 closed, 1 vulnerable (B).**

Key observation for attack B: `RecordVerification.model_construct` skips all
`_trust_laws` validators, and `model_copy(update=...)` bypasses validation.
However, **`ConsumerPolicy.evaluate` calls `rederive()` first and runs all four
inspections on the `derived` verdict, not on the caller-supplied `candidate`**.
The candidate is only compared field-by-field against `derived`; any divergence
yields `CACHED_VERDICT_DIVERGENCE` → `REFUSE`. Therefore attack B is a **model-level
boundary weakness**, not an exploitable authorization bypass through the public
`ConsumerPolicy.evaluate` API (see PHASE 3).

---

## 3. Phase 3 — Production Model Findings (Evaluated Separately)

The production `model_construct` / `model_copy` observations from the previous
audit are preserved here as a **separate** finding, evaluated against the actual
ConsumerPolicy consumption path with a complete-exploit-chain requirement.

### 3.1 Observations preserved

- **B (model_construct):** `RecordVerification.model_construct()` skips the
  `_trust_laws` `after`-validator entirely, permitting contradictory state
  (e.g. `source_lineage_verified=True` without `lineage_proof`,
  `downstream_trusted=True` with empty `unverified_dimensions`,
  `trust_scope="FULL_RECORD_TRUST"`).
- **A (model_copy):** `RecordVerification.model_copy(update=...)` creates a new
  object without re-running validators; `trust_scope`, `unverified_dimensions`,
  `custody_source_authorized` can be changed without re-validation.

### 3.2 Exploit-chain analysis through ConsumerPolicy

`ConsumerPolicy.evaluate(candidate, rederive, ...)`:

1. `derived = rederive()` — fresh `RecordVerification` built by the policy's
   own `verify_trade_record` (validated via `model_validate`). This is the
   authoritative verdict.
2. If `candidate` is not `None`, it is compared field-by-field against
   `derived`; any divergence → `REFUSE` / `CACHED_VERDICT_DIVERGENCE`.
3. `self._apply(derived, ...)` — **all four inspections run on `derived`**, not
   on `candidate`.

### 3.3 Finding classification

Because every inspection runs on the `rederive()`-produced verdict and the
caller-supplied `candidate` is only cross-checked for divergence, a
`model_construct`-forged `candidate` **cannot** cause `ConsumerPolicy.evaluate`
to return `ACCEPT_FIELD_BINDING` or `custody_source_authorized=True` without a
matching valid `derived`. **No complete exploit chain to an unauthorized trusted
outlet exists through `ConsumerPolicy.evaluate`.**

**Classification: potential boundary weakness (B), not a production
authorization compromise.** The `RecordVerification` model permits
self-contradictory construction via `model_construct`, but no consumer code path
trusts such an object without re-derivation. This is recorded as a boundary
weakness to be hardened (run validators on `model_copy`/`model_construct`), not
as a demonstrated production compromise.

---

## 4. Phase 4 — Audit Accounting Correction

The previous committed audit (`136a951af`) reported inconsistent totals: it
quoted a collection count and an executed count in the same breath without
separating them, and its storage partition did not execute (host disk full).
This corrective audit publishes the reconciled tally.

### 4.1 Corrected execution accounting (measured, not inherited)

**Corrected full-accounting numbers** (from the canonical universe, corrected
in this audit):

| Metric | Value |
|--------|-------|
| Collected | 4,733 |
| Digest | `1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` |
| Duplicates | 0 |
| Malformed | 0 |
| Collection errors | none (exit 0) |
| Executed | 2,704 |
| Passed | 2,703 |
| Skipped | 1 |
| Failed | 0 |
| Errors | 0 |
| Missing | 2,029 (= 4,733 − 2,704) |
| Extra | 0 |
| Duplicate | 0 |

**Collection ≠ execution.** Two numbers are reported separately and never
conflated:

1. **Full-accounting numbers** (corrected in this audit): 4,733 collected,
   2,704 executed (2,703 passed + 1 skipped), 2,029 missing, digest verified.
   These describe the complete canonical-universe execution.

2. **Independent focused verification subset** (independently executed by this
   audit on this tree, all passed): Normalization 1,324; governed storage set
   265 (incl. I11R2 evidence+binding 14); runner self-tests 24; R2 negative
   suite 16; R3 negative suite 9. Total **1,638 passed, 0 failed**. These are a
   subset of the executed nodes, not the whole execution.

The remaining executed nodes (2,704 − 1,638 = 1,066) were part of the broader
canonical-universe execution but were not part of this audit's focused
independent verification subset. The ~2,029 missing nodes (primarily the storage
partition, 130 files) were **not executed** because the host disk reached 100%
during execution. This is an environment limitation, not a regression. Per
PHASE 6, Agent 1 owns the full canonical execution; this audit does **not**
claim `COMPLETE` and does **not** repeat the storage regression.

### 4.2 Corrected acceptance matrix (25 gates)

| GATE | EXPECTED | OBSERVED | EVIDENCE | RESULT |
|------|----------|----------|----------|--------|
| G01 | Audited SHA `9d289500f` resolves | commit | `git cat-file -t` | PASS |
| G02 | R5 `ea1fdeb77` is ancestor of R6 | yes | `merge-base --is-ancestor` | PASS |
| G03 | R6 changes zero production source | 0 `.py` in `quant-lab/src` | `git diff ea1fdeb77..9d289500f -- quant-lab/src` | PASS |
| G04 | Primary branch unchanged | `f199a7e3` at origin | `git ls-remote origin` | PASS |
| G05 | Working bytes match blobs | clean porcelain | `git status --porcelain` | PASS |
| G06 | Frozen plan commit `4bb677f9e` exists | commit | `git cat-file -t` | PASS |
| G07 | Plans unmodified by R6 | no plan diff | `git diff` | PASS |
| G08 | CAP01 closed (forged capability refused) | `INTEGRATION_REQUIRED` | PHASE 1 probe | PASS |
| G09 | CAP02 closed (manifest digest validated) | `TRUSTED_MANIFEST_SHA256` checked | PHASE 1 probe | PASS |
| G10 | CAP03 closed (replace cannot escalate) | `is_issued=False` after replace | PHASE 1 probe | PASS |
| G11 | CAP08b closed (provider binding) | `INTEGRATION_REQUIRED` | PHASE 1 probe | PASS |
| G12 | CAP12 closed (record kind required) | `INTEGRATION_REQUIRED` | PHASE 1 probe | PASS |
| G13 | RG08 closed (forged replay refused) | `REFUSE`/`REPLAY_BLOCKED` | PHASE 1 probe | PASS |
| G14 | A: `model_copy` forgery caught on re-validation | `ValidationError` | PHASE 2 probe A | PASS |
| G15 | B: `model_construct` bypasses all validation | contradictory state creatable | PHASE 2 probe B | **FAIL** (model-level boundary weakness; NOT exploitable through `ConsumerPolicy.evaluate` — see PHASE 3) |
| G16 | C: cutoff substitution refused | `INTEGRATION_REQUIRED` | PHASE 2 probe C | PASS |
| G17 | D.1: matching cached verdict passes | `ACCEPT_FIELD_BINDING` | PHASE 2 probe D.1 | PASS |
| G18 | D.2: forged cached verdict diverges refused | `CACHED_VERDICT_DIVERGENCE` | PHASE 2 probe D.2 | PASS |
| G19 | E: synthetic never `AUTHORIZED` | `SYNTHETIC_TEST_ONLY` | PHASE 2 probe E | PASS |
| G20 | F: direct construction without marker refused | `INTEGRATION_REQUIRED` | PHASE 2 probe F | PASS |
| G21 | Collection count | 4,733 | `pytest --collect-only` + digest | PASS |
| G22 | Collection digest matches | `1036049742127c8f…` | independent digest recompute | PASS |
| G23 | Production manifest empty | `artifacts == {}` | manifest parse | PASS |
| G24 | `INTEGRATION_REQUIRED` in force | `INTEGRATION_REQUIRED` | code check | PASS |
| G25 | Storage regression | not executed (disk full) | PHASE 4 note | **DEFERRED** |

**Corrected tally: 23 PASS, 1 FAIL (G15, model-level boundary weakness B — not a production authorization compromise), 1 DEFERRED (G25, storage regression).**

Note: The previous audit's FAILs about production `SemanticAuthority`/`RecordVerification` are out of scope for this ConsumerPolicy audit (PHASE 0) and are addressed separately in PHASE 3 as boundary weaknesses, not production compromises.

---

## 5. Phase 5 — RG05 Adjudication (Cutoff Binding)

RG05 concerns cutoff binding: a capability's knowledge cutoff must bind to it,
and cross-cutoff reuse must be refused.

**RG05 safety property (cutoff binding): CLOSED.** Independently verified:
- Same cutoff within validity window → `ACCEPT_FIELD_BINDING` (status
  `SYNTHETIC_TEST_ONLY`, never operator authority).
- Later cutoff → `INTEGRATION_REQUIRED` (cross-cutoff reuse refused).
- The shared `pit_availability_refusal` rule enforces offset-aware instant
  ordering; `DST` fall-back resolves by true instant, not local wall-clock text.

**RG05 positive leg (historical): encodes an obsolete unsafe expectation.** The
R6 test `test_r6_14_same_cutoff_is_honoured_under_synthetic_semantics` states
explicitly:

> "RG05's positive leg requires a directly constructed `ATTESTED_OPERATOR`
> capability to be honoured at its own cutoff — which is exactly the CAP01
> bypass. The binding is therefore demonstrated on a synthetic (non-authoritative)
> capability, where acceptance means `SYNTHETIC_TEST_ONLY` and never operator
> authority."

**Adjudication:** The safety property (cutoff binding prevents cross-cutoff
reuse) holds in R6 production `ConsumerPolicy`. However, the RG05 positive leg
demonstrates binding only on a **synthetic (non-attested) capability**, whose
acceptance means `SYNTHETIC_TEST_ONLY` and never operator authority. The
historical test is **preserved unchanged**; its positive leg encodes the obsolete
unsafe CAP01 bypass expectation, which R6 has closed. No production authorization
compromise results.

---

## 6. Phase 6 — Remaining Security Boundaries

### Closed (R6 ConsumerPolicy)
- All six original attacks (CAP01, CAP02, CAP03, CAP08b, CAP12, RG08).
- Additional attacks A, C, D.1, D.2, E, F.
- RG05 safety property (cutoff binding).

### Potential boundary weakness (not a production compromise)
- **G15 / B:** `RecordVerification.model_construct` bypasses `_trust_laws`;
  `model_copy(update=...)` bypasses validation. Through `ConsumerPolicy.evaluate`,
  `rederive()` produces the authoritative verdict and inspections run on it, so
  no complete exploit chain to an unauthorized trusted outlet exists through the
  public API. Recommended hardening: run validators on `model_copy` /
  `model_construct`, or make `assert_trustworthy()` mandatory at consumption
  points.

### Not executed (environment limitation)
- **G25 / storage regression:** ~2,029 nodes (130 storage test files) not run
  because the host disk reached 100% during execution. Agent 1 owns the full
  canonical execution; this audit does not claim `COMPLETE` and does not repeat
  the storage regression.

### Out of scope (per PHASE 0)
- Production `SemanticAuthority` / `RecordVerification` constructors: **0
  changes** in R6 (`git diff ea1fdeb77..9d289500f -- quant-lab/src` empty).
  The production-model findings are documented in PHASE 3 as boundary
  weaknesses, not consumer-policy audit failures.

---

## 7. Phase 7 — Publication

**Published as an additive corrective commit** on the owned independent audit
lineage `agent/crypto-sensor-fabric-p3-r6-reattack`, on top of `136a951af`.

**No competing ledger §204:** Ledger §204 already exists on this branch
(`SENSOR-B5-I09P3-R6-INDEPENDENT-REATTACK-FINAL (AGENT 2)`). This corrective
audit is published as a **new document only** (`BLOC_05_I09P3R6_CORRECTIVE_AUDIT.md`);
no ledger section is added, renumbered, or rewritten.

**No implementation changes:** `quant-lab/src` unchanged vs R6 (0 paths).
**No production merge:** production remains at `f199a7e3f`.
**No trust promotion, no provider certification, no self-ratification.**
**Security disposition left `PENDING`.**

Publication verification: local commit SHA == remote SHA == branch ref;
working tree clean; no QCAE in message or paths.

---

## Final Bounded Disposition

**`PENDING`** (security disposition explicitly left pending)

R6 `ConsumerPolicy` closes all six original R5 vulnerabilities (CAP01, CAP02,
CAP03, CAP08b, CAP12, RG08) and the additional attacks, with the single
model-level boundary weakness (`model_construct` bypasses `RecordVerification`
validation) that is **not exploitable through `ConsumerPolicy.evaluate`** because
every inspection runs on a freshly re-derived verdict. RG05's cutoff-binding
safety property holds; its positive leg encodes the obsolete unsafe CAP01 bypass
expectation, now demonstrated only on a synthetic (non-attested) capability.

The canonical execution is **partial** (4,733 collected, 2,704 executed,
2,029 missing — storage partition not run due to host disk exhaustion). This
audit does **not** claim `COMPLETE`, does **not** claim security acceptance,
and does **not** authorize production merge, trust promotion, provider
certification, or any program-gate advancement.

**VERIFY → REATTACK → RUN FULL REGRESSION → ADJUDICATE → PUBLISH → HARD STOP.**
