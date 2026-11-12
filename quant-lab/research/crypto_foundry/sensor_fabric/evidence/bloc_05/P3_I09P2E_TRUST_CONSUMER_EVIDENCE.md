# P3 / I09 P2e — Trust-Consumer Conformance Engine: Implementation Evidence

**Workstream:** Parallel Build Lane — Agent 1 (Implementation Lead)
**Branch:** `agent/crypto-sensor-fabric-trust-consumer-r1`
**Immutable reference:** `agent/crypto-sensor-fabric-integration-r1 @ 3e53a65897283b32d42dfe6d879e7acf389fd873`
**Authoritative specification:** `BLOC_05_I09P2E_TRUST_CONSUMER_CONTRACT.md` (P2e)
**Final disposition:** `P3_R1_IMPLEMENTATION_READY_FOR_INDEPENDENT_AUDIT`

---

## 1. Starting HEAD and final HEAD

| Item | Value |
|---|---|
| Starting HEAD (pinned Integration R1) | `3e53a65897283b32d42dfe6d879e7acf389fd873` |
| Commit on branch since R1 | `03da8e4c9b1ab81ebb35960212e9fa7fd4581139` |
| Final local HEAD | `03da8e4c9b1ab81ebb35960212e9fa7fd4581139` |
| Final remote HEAD (origin) | `03da8e4c9b1ab81ebb35960212e9fa7fd4581139` |
| Local == remote | Yes |

The branch descends directly from the pinned R1 HEAD; `3e53a6589` is an ancestor of `03da8e4c9`. History was not rewritten — no rebase, no squash, no force-push.

## 2. Completed versus remaining work

### Completed (Phases 1–6)

- **Consumer boundary:** three typed outcomes — `ACCEPT_FIELD_BINDING`, `REFUSE`, `INTEGRATION_REQUIRED`.
- **Four mandatory inspections (§3)** on every path: trust scope, nonempty unverified dimensions, custody-source authorization distinct from custody verification, verified-field allowlist.
- **Copied/deserialized verdict revalidation (§4):** re-derivation against the policy's own trusted context; comparison of `approval_id`, `registry_digest`, `artifact_id`, `trust_scope`, `fields_verified`, `custody_source_authorized`; refusal on any divergence.
- **Evidence-byte rebinding (§7):** re-reads actual store bytes at consumption, re-hashes with `evidence_digest`, refuses missing/mismatched/digest-only custody.
- **PIT/replay separation (§6):** reuses `verify_trade_record`, `pit_availability_refusal`, `ReplayEligibility`, `assess_replay_eligibility` without duplicating their rules; all four PIT/replay combinations tested.
- **Adversarial test suite:** 24 attack families (plus expanded offset-aware-equality and DST-boundary cases) covering forged scope, empty unverified dimensions, unauthorized custody source, missing/substituted evidence bytes, approval/registry/artifact/field-allowlist forgery, cached verdict after revocation, same-day date-only PIT ambiguity, naive cutoff, offset-aware equality, DST folds, PIT/replay disagreement, sibling-field substitution, false liquidation transformation claim, mixed batch, retry bypass, unauthenticated acquisition lineage, forged instrument identity, no-cutoff-auth-as-PIT-approval.
- **Multipath conformance:** identical policy across single-record, cached, deserialized, evidence-reread, and refusal-handling paths.
- **Governance scope:** `INTEGRATION_STATE` unchanged (`INTEGRATION_REQUIRED`), no custody authority created, no whole-record trust assertion, approval manifest remains empty.

### Remaining (not done by this workstream; deliberately deferred)

- **Focused regression on existing P2a–P2e / I05 / I06 / I09 / I10 / I11 suites:** could not be executed in this sparse checkout because those test files are tracked but not materialized on disk (5051 `D` entries in worktree status). Agent 2 owns the full canonical regression slot; this workstream's isolated suite (70 tests) passes.
- **Canonical full-HEAD regression:** deferred to Agent 2's audit gate; not inherited as this workstream's result.
- **Production integration:** explicitly out of scope — no ingestion application, no custody service, no provider approval, no application initializer. Documented as a deferred dependency (§6 of the contract).

### What was NOT touched

- No source modules modified (`verification.py`, `authority/__init__.py`, `time/enums.py` reused unchanged).
- Agent 2's audit branch `agent/crypto-sensor-fabric-audit-p2er2` untouched (still `985e1aa373a0324e749c559d6fdb534702748196`).
- `main` untouched (still `a794a9af80ae8deddacf2991de17b7d71e445756`).
- Frozen Bloc 5 contract preserved unchanged.
- Approval manifest remains empty (`artifacts == {}`).

## 3. Full module architecture

```
quant-lab/tests/crypto_sensor_fabric/normalization/
└── test_b5_i09p2e_trust_consumer.py   (implementation + 70 tests)

quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/
└── P3_I09P2E_TRUST_CONSUMER_EVIDENCE.md  (this document, in the allowlisted evidence prefix)
```

The implementation lives entirely in one test-only module:

| Component | Kind | Responsibility |
|---|---|---|
| `ConsumerDecision` (Enum) | typed outcome | `ACCEPT_FIELD_BINDING` / `REFUSE` / `INTEGRATION_REQUIRED` |
| `ConsumerRefusalReason` (Enum) | typed refusal | 14 typed reasons (forged scope, empty unverified dims, unauthorized custody, digest-only custody, missing/mismatch bytes, cached divergence, field-not-in-allowlist, verification failed, PIT inadmissible, replay blocked, naive cutoff, no PIT availability, intraday ambiguity) |
| `ConsumerVerdict` (frozen dataclass) | output | decision, field allowlist, unverified dims, trust scope, PIT/replay/custody statuses, custody-source-authorized flag, typed refusal reason + detail |
| `DeterministicEvidenceStore` | fixture | in-memory byte store; NOT production custody |
| `ConsumerPolicy` | central engine | `_apply` runs all four inspections + evidence rebinding on every path; `evaluate`/`evaluate_cached` re-derive before inspecting (§4) |
| `_base_verdict` / `_forged_verdict` | fixtures | valid verdict via `model_validate`; forged verdict via `model_construct` (violates model laws, simulates non-verifier objects) |
| `_replay_evaluation` | fixture | synthetic replay-eligibility object |

Reused primitives (imported, not duplicated, not modified):

- `RecordVerification`, `verify_trade_record`, `TrustedAuthorityContext`, `TrustedCustodyProvider`, `INTEGRATION_STATE`, `TRUST_SCOPE_ECONOMIC_FIELD_BINDING`, `RecordVerificationError`, `RecordVerificationRefusal` from `normalization.sensors.verification`
- `evidence_digest` from `normalization.authority`
- `ReplayEligibility` from `normalization.time.enums`
- `pit_availability_refusal` referenced in docstring (PIT availability rule)

## 4. Four mandatory inspections (§3) — enforced on every path

All four run inside `ConsumerPolicy._apply`, so single, batch, cached, deserialized, and evidence-reread paths cannot skip them:

| # | Inspection | Enforcement | Refusal reason |
|---|---|---|---|
| 1 | Trust scope must equal `ECONOMIC_FIELD_BINDING` | `derived.trust_scope != TRUST_SCOPE_ECONOMIC_FIELD_BINDING` → refuse | `FORGED_TRUST_SCOPE` |
| 2 | `unverified_dimensions` must be nonempty | empty set → refuse; preserved through serialization/caching | `EMPTY_UNVERIFIED_DIMENSIONS` |
| 3 | `custody_source_authorized` read as its own fact | `custody_verified=True` with `custody_source_authorized=False` → `INTEGRATION_REQUIRED`, never auto-True | `UNAUTHORIZED_CUSTODY_SOURCE` (integration required, not refuse) |
| 4 | `fields_verified` is the allowlist | any required field not in `fields_verified` → refuse; sibling canonical fields rejected | `FIELD_NOT_IN_ALLOWLIST` |

No whole-record trust assertion is ever returned; trust is always field-scoped.

## 5. Cached-verdict revalidation (§4)

`ConsumerPolicy.evaluate` / `evaluate_cached`:

- Accepts a `candidate` (stored/copied/deserialized verdict, may be `None` for fresh evaluation) and a `rederive` callable.
- `rederive` produces a fresh `RecordVerification` from the policy's **own** `TrustedAuthorityContext` — never a context supplied by the record's producer.
- Re-derivation errors (`RecordVerificationError`, e.g. `APPROVAL_REVOKED`, `PIT_CUTOFF_REQUIRED`) → `REFUSE` with `VERIFICATION_FAILED`.
- If `candidate is not None`, compares `approval_id`, `registry_digest`, `artifact_id`, `trust_scope`, `fields_verified`, `custody_source_authorized` between candidate and derived; any divergence → `REFUSE` with `CACHED_VERDICT_DIVERGENCE`.
- Only after revalidation passes does `_apply` run the four inspections.
- A stored verdict with no re-derivation path cannot be accepted by construction — it is a claim, not a capability.

## 6. Evidence-byte rebinding (§7)

`ConsumerPolicy._rebind_evidence`:

- Takes `evidence_references: dict[reference, expected_digest]`.
- For each reference, reads actual bytes from the store at consumption time.
- Missing bytes → `REFUSE` `EVIDENCE_BYTES_MISSING`.
- Re-hashed digest != expected → `REFUSE` `EVIDENCE_BYTES_MISMATCH`.
- No `None` mapping → nothing to rebind (verdict carries no evidence references).
- Digest-only custody (verified at verification time but no rebindable bytes at consumption) → refused when bytes are expected.
- The store is explicitly a test fixture, not production custody infrastructure.

## 7. PIT/replay separation (§6)

- PIT admissibility comes from `verify_trade_record` / `pit_availability_refusal` via `derived.pit_admissible`.
- Replay eligibility comes from the I05 gate via `ReplayEligibility` / `assess_replay_eligibility` passed as `replay_evaluation`.
- Neither overrides the other; both independently applicable refusal reasons preserved.
- No acquisition timestamps synthesized; no inference from event time / mtime / cutoff.
- `EVALUATION_TIME_REQUIRED` / `PIT_CUTOFF_REQUIRED` treated as caller errors, not data verdicts.

All four combinations tested:
| PIT | Replay | Result |
|-----|--------|--------|
| Admissible | Eligible | `ACCEPT_FIELD_BINDING` |
| Admissible | Blocked | `REFUSE` `REPLAY_BLOCKED`, `pit_status=ADMISSIBLE` |
| Inadmissible | Eligible | `REFUSE` `PIT_INADMISSIBLE` |
| Inadmissible | Blocked | `REFUSE`; both `pit_status=INADMISSIBLE` and `replay_status=BLOCKED_TIMESTAMP` surfaced |

## 8. Attack matrix and results

70 tests, **70 passed**. Adversarial families (24), including explicit offset-aware-equality and DST-boundary cases that drive the reused `pit_availability_refusal` rule:

| # | Attack | Result |
|---|---|---|
| 1 | Forged trust scope (`FULL_RECORD_AUTHENTICITY`) | REFUSE `FORGED_TRUST_SCOPE` |
| 2 | Empty unverified dimension set | REFUSE `EMPTY_UNVERIFIED_DIMENSIONS` |
| 3 | unverified_dimensions dropped during JSON serialization/deserialization | preserved; propagated into verdict |
| 4 | Unauthorized custody source (`custody_source_authorized=False`) | INTEGRATION_REQUIRED |
| 5 | Digest-only custody proof (verified but no rebindable bytes) | REFUSE `EVIDENCE_BYTES_MISSING` |
| 6 | Evidence byte substitution at consumption | REFUSE `EVIDENCE_BYTES_MISMATCH` |
| 7 | Evidence missing at consumption | REFUSE `EVIDENCE_BYTES_MISSING` |
| 8 | Copied verdict with forged approval ID | REFUSE `CACHED_VERDICT_DIVERGENCE` |
| 9 | Copied verdict with forged registry digest | REFUSE `CACHED_VERDICT_DIVERGENCE` |
| 10 | Cached verdict after approval revocation (re-derivation raises) | REFUSE `VERIFICATION_FAILED` |
| 11 | Same-day date-only PIT ambiguity | REFUSE `PIT_INADMISSIBLE` |
| 12 | Missing approval availability | REFUSE `PIT_INADMISSIBLE` |
| 13 | Naive evaluation cutoff | REFUSE `VERIFICATION_FAILED` (`PIT_CUTOFF_REQUIRED`) |
| 14 | Offset-aware equality (same instant, different offset) | admissible (`None`); one-minute-before refused `APPROVAL_NOT_YET_AVAILABLE`; naive basis text `ValueError` |
| 15 | DST edge cases (fall-back fold, spring-forward naive local, DST same-day date-only) | fold resolves by true instant (fold=0 refused, fold=1 admissible); naive local refused `EVALUATION_TIME_REQUIRED`; same-day date-only `INTRADAY_PIT_AMBIGUOUS` |
| 16 | PIT admissible but replay blocked | REFUSE `REPLAY_BLOCKED`, `pit_status=ADMISSIBLE` |
| 17 | Replay eligible but PIT inadmissible | REFUSE `PIT_INADMISSIBLE` |
| 18 | Unlisted canonical field required | REFUSE `FIELD_NOT_IN_ALLOWLIST` |
| 19 | Sibling canonical field substitution (`trade_volume` for `trade_price`) | REFUSE `FIELD_NOT_IN_ALLOWLIST` |
| 20 | Liquidation record claiming verified economic transformation | `record_transformation_verified=False`, `downstream_trusted=False`, INTEGRATION_REQUIRED |
| 21 | Mixed-acceptance batch (one good, one forged) | per-record independent outcomes; forged refused |
| 22 | Refusal incorrectly retried as transient | same digest-mismatch refusal on retry — not transient |
| 23 | Unauthenticated source lineage promotion | model construction raises (contradictory state) |
| 24 | Forged instrument identity | `instrument_authenticated=False`, `instrument_authentication_ref=None` |
| 25 | Missing acquisition lineage | `SOURCE_LINEAGE` / `ACQUISITION_LINEAGE` in unverified_dimensions; not synthesized |
| 26 | No-cutoff authentication presented as PIT approval | REFUSE `PIT_INADMISSIBLE` |

Plus multipath conformance tests (single, cached, deserialized, evidence reread, typed refusal handling) and governance scope tests (integration state unchanged, trust scope constant, no custody authority created, no whole-record trust assertion).

## 9. Focused regression

| Suite | Result |
|---|---|
| New P3 conformance suite (`test_b5_i09p2e_trust_consumer.py`) | **70 passed** |
| P2a–P2e, I05/I06 replay, I09 semantic determinism, I10 scope, I11 nonregression | **436 passed, 1 failed** in the R3 run (see §15). The one failure is the I10 audit's *unstaged* worktree-deletion assertion, caused solely by the partial checkout (missing data files appear as deletions); its staged-path assertion passes. |
| Relevant governance predicates | `INTEGRATION_STATE == INTEGRATION_REQUIRED` verified in-test; approval manifest `artifacts == {}` verified from the shipped file |

No source modules were modified by this workstream, so there is no source-level regression to detect from this change. Dependent primitives were reused unchanged.

## 10. Canonical regression status

**Not run by this workstream.** The full canonical regression of the integration candidate is Agent 2's responsibility and requires a full (non-sparse) checkout. This workstream's result is limited to its own isolated suite (70 passed). Reported explicitly as incomplete rather than adjudicated.

## 11. Governance and source scope

- **Frozen Bloc 5 contract:** preserved unchanged; implementation follows its §3–§7 mandatory behaviors.
- **No production modules modified:** `normalization/sensors/verification.py`, `normalization/authority/__init__.py`, `normalization/time/enums.py` all reused unchanged.
- **No ingestion wiring:** engine is experimental/test-only; not connected to real ingestion.
- **No allowlist broadening:** `fields_verified` remains the strict allowlist; no sibling-field expansion.
- **Approval manifest:** remains empty (`artifacts == {}`), admitting nothing.
- **Custody authority:** none created; `custody_source_authorized` always `False` unless an operator decision records it externally.
- **Governance inventory:** no mechanical updates made; no governance hashes hand-edited; no historical audit evidence rewritten.

## 12. Remaining unverified dimensions

Per the contract §2 and §8, the following dimensions stay `unverified` on every verdict and must not be upgraded:

- `SOURCE_LINEAGE` / `ACQUISITION_LINEAGE` — no authenticated acquisition instant exists in the repository; not synthesized from event time, mtime, or cutoff.
- `CUSTODY_SOURCE_AUTHORITY` — `custody_source_authorized` is `False`; requires an operator decision recorded in the governance ledger.
- `instrument_authenticated` / `source_revision_authenticated` — `False` unless an approval names those identities.
- `record_transformation_verified` — `False` for every liquidation record; liquidation canonical side not treated as transformation-proven.

These remain the consumer's explicit, propagated limitations — not formatting choices.

## 13. Production-authority limitations

This prototype does **not** establish production consumer authority:

- `custody_source_authorized` is always `False`; economic use requires an operator-controlled custody decision recorded outside the verdict.
- `source_lineage_verified`, `instrument_authenticated`, `source_revision_authenticated` remain `False`.
- `record_transformation_verified` stays `False` for liquidation records.
- `ACQUISITION_LINEAGE` stays unverified.
- `INTEGRATION_REQUIRED` is returned whenever the custody source is unauthorized — the consumer cannot self-ratify.
- No ingestion application, initializer, custody service, provider approval, liquidation transformation, or program gate is present.
- Hard stops honored: no production merge, no live ingestion, no real custody authorization, no provider certification, no verified liquidation economics, no I11/I12/I17 or Bloc 6 advancement, no program-gate promotion.

## 14. Independent audit requirements

Before any consumer built on this engine is promoted:

1. Run the full canonical regression (P2a–P2e, I05–I11) in a full non-sparse checkout under Agent 2's gate.
2. Operator records a custody-source authorization decision in the governance ledger so the consumer can transition from `INTEGRATION_REQUIRED` to field binding.
3. Add an authenticated acquisition lineage record so `ACQUISITION_LINEAGE` can leave `unverified_dimensions`.
4. Verify the consumer holds its own reviewed root and never accepts one from the record's producer.
5. Verify the four mandatory inspections execute on every path including batch and cached paths.
6. Verify stored verdicts are re-derived (§4) rather than trusted.
7. Verify PIT admission and replay eligibility are computed by different code paths with different vocabularies.
8. Verify the serialization/UI surface carries `unverified_dimensions` verbatim.
9. Verify `custody_source_authorized` is resolved by an operator decision, not inferred from a passing test.

---

## 15. R3 closure addendum (full-checkout governance / conformance validation)

**Starting SHA:** `c0e3440bf4b0ed09156be360be0bdeeeb00d3460`
**Final SHA:** recorded by the R3 commit that follows this document (see branch HEAD).
**Ancestry:** P3 descends from Integration R1 `3e53a6589` (verified).

### 15.1 Full-checkout status — BLOCKED by host disk exhaustion

A full, non-sparse worktree at the exact P3 HEAD could not be materialized. The tracked tree is 196.0 MB (6,773 files), but the host volume was at 98–100% capacity and a concurrent process consumed gigabytes during each attempt. Three attempts (`git worktree add`, `checkout-index -a -f`, `git archive | tar -x`) each aborted with `No space left on device` after writing several thousand files; each partial tree was removed and the disk returned to its prior free space. To avoid filling the user's system disk, no further full materialization was attempted.

What was done instead, at the exact P3 HEAD:
* inventory verified from Git objects (authoritative, checkout-free);
* the complete `quant-lab/tests/crypto_sensor_fabric/` (341 files), `quant-lab/config/crypto_sensor_fabric/` (26), `evidence/bloc_05/` (95), `scripts/` (11) and the frozen `research/.../bloc_05` plan were materialized into the isolated worktree;
* focused regression executed against those.

This is a partial-tree verification, not the full-checkout proof Phase 0 requires. It is reported as blocked, not satisfied.

### 15.2 Python inventory (checkout-free, exact)

| Commit | Tracked `.py` |
|---|---|
| Integration R1 `3e53a6589` | 1,096 |
| P3 HEAD `c0e3440bf` | **1,097** |

Exactly one `.py` was added between them: `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py`. No other `.py` was added, deleted or renamed. The 1,097 figure is confirmed; no publisher/allowlist widening was performed.

### 15.3 Governance publisher

No committed artifact encodes a Python-file-count inventory for the sensor-fabric checkpoint (the I11R2 governance-binding audit governs dashboard/ledger readers, not file counts), so there was nothing to re-publish. No hashes were hand-edited and no allowlist was widened.

### 15.4 I10 scope outcome

Running the frozen I10 scope audit surfaced one genuine governance finding: the evidence document previously lived under `tests/crypto_sensor_fabric/normalization/`, which the frozen `allowed` prefix list does **not** admit. Rather than widen the allowlist, the document was relocated into the already-admitted `research/crypto_foundry/sensor_fabric/evidence/bloc_05/` prefix. After relocation the audit's **staged-path** assertion passes. The audit's **unstaged** assertion still reports the partial checkout's missing data files as deletions; that is an environment artifact, not an unauthorized change (no data file was modified).

### 15.5 Focused regression (actual counts)

* P2a–P2e + P3: **233 passed**.
* I05 availability/replay, I06 replay-safety, I09 semantics, I10 scope, I11 liquidation/scope: **203 passed, 1 failed** (the I10 unstaged-deletion artifact above).
* Combined focused run: **436 passed, 1 failed**, 0 errors, 0 skips.
* P3 suite after the R3 tightenings: **70 passed**.

### 15.6 Reattack results (Phase 3)

* Shipped `approval_manifest.json` has `artifacts == {}`; `INTEGRATION_STATE == INTEGRATION_REQUIRED`.
* The P3 module never loads the shipped manifest or a real trusted authority: every `ACCEPT_FIELD_BINDING` outcome is gated on an explicitly synthetic `custody_source_authorized=True` fixture blown on a synthetic policy context. No fixture represents a real approved provider.
* Two loose assertions that merely *permitted* ACCEPT were tightened to deterministic expectations (the 2x2 PIT/replay matrix now expects ACCEPT only when both are satisfied, and the cached-path test now requires ACCEPT exactly), so a boundary regression can no longer pass silently.

### 15.7 Full canonical regression

Not run by this workstream. Agent 2 owns the memory-intensive final-HEAD slot, and the partial tree cannot host evidence-determinism tests. Status: **incomplete / delegated**.

### 15.8 Remaining acceptance requirements

1. Materialize a full non-sparse checkout on a host with sufficient free space and run the canonical suite there.
2. Confirm the canonical node-id universe (previous 4,640 tests plus the 70 P3 tests) with no missing or duplicated IDs.
3. Confirm the I10 audit's unstaged assertion is green in that full checkout.
4. Operator records custody-source authorization before any economic use.
5. Authenticated acquisition lineage before `ACQUISITION_LINEAGE` leaves `unverified_dimensions`.

---

## 16. R5 addendum (governance recovery, custody-authority repair, controlled publication)

**Starting SHA:** `5ce62c26da8a63dd84160f21694e5eceef406018`
**Final SHA:** recorded by the R5 commit that follows this document (see branch HEAD).
**Ancestry:** P3 descends from Integration R1 `3e53a6589`; the R5 commits sit directly on the R4 starting SHA above.

### 16.1 Environment and storage state

The R4 disk exhaustion did not recur: the volume was at **55 GB free (78 % of 238 GB)** when R5 began. Worktree registrations had been reclaimed between runs, and the R4 worktree no longer existed, so nothing from R4 survived. All R4 results below were therefore **re-produced from scratch**, not inherited.

`.worktrees/trust-consumer-r1` was created at the starting SHA and `git worktree add` materialized **all 6,773 tracked files (100 %)**, leaving zero missing tracked files and zero worktree deletions. This is the first full, non-sparse checkout this workstream has achieved; R3's §15.1 blocker is closed as an environment condition, without weakening any assertion that depended on it.

No bulk `checkout-index` was used while storage was unstable, and no shared `.git`, cache, worktree or process data was deleted or altered.

### 16.2 Governance publisher (Phase 1)

```
UPDATE_I11R2_EVIDENCE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=quant-lab/src \
  python3 -m pytest -p no:cacheprovider -q \
  quant-lab/tests/crypto_sensor_fabric/storage/test_i11r2_binding_audit.py::test_governance_binding_audit_is_measured_and_committed
```

Result: `1 passed`. The publisher recomputes the whole payload (scan → allowlist → hit sets → row verdicts → frozen provenance pin) from the tree; no JSON was hand-edited.

Measured diff — the entire change:

```
@@ -78 +78 @@
-  "python_files_scanned": 1096,
+  "python_files_scanned": 1097,
```

1 insertion, 1 deletion. Because the diff is a single JSON count value, every allowlist, hit set, row verdict and the frozen I07R1I provenance pin are byte-identical by construction. `1097` equals `git ls-files '*.py' | wc -l` at this HEAD.

The new P3 module trips **zero** of the three governance predicates (`## Current state`, `SENSOR_FABRIC_IMPLEMENTATION_PROGRESS`, `Current checkpoint`), so **no allowlist was widened** to accommodate it; the module is admitted by the existing `test_b5_i09` named prefix. This artifact was staged and committed **first**, as `8360c9dd1`, before any further work.

### 16.3 Confirmed RED counterexamples (Phase 2/3)

Nine negative tests were written first and run against the unmodified policy: **9 failed**. Four failed with the unsafe behaviour actually **observed**, on the one code path the traceback proved:

| Attack | Controlled input | Observed before repair | Required |
|---|---|---|---|
| AT53 | caller `rederive` returns `custody_source_authorized=True` | `ACCEPT_FIELD_BINDING` (asserted `INTEGRATION_REQUIRED`, got accept) | `INTEGRATION_REQUIRED` |
| AT43 | synthetic fixture flag promoted | `ACCEPT_FIELD_BINDING` | never `AUTHORIZED` |
| AT55 | forged cached and forged re-derived verdicts agree True | `ACCEPT_FIELD_BINDING` | `INTEGRATION_REQUIRED` |
| AT39 | evidence bytes verified, digest matches | `ACCEPT_FIELD_BINDING` | bytes ≠ source authority |

The remaining five failed because the mechanism they test did not exist yet, which is itself the finding: there was no policy-owned authority object, no record binding and no cutoff binding to attack.

| Attack | Reason for RED | Required |
|---|---|---|
| AT54 | no capability existed to refuse a forged context | reject |
| AT56 | no record binding existed (red-team AT56 independently reproduced `ACCEPT`) | `INTEGRATION_REQUIRED` |
| cross-cutoff | no cutoff binding existed | re-evaluate PIT/replay |
| empty manifest | no approved-authority mechanism existed | never establishes approval |
| synthetic-not-attested | no authority category existed | distinguishable status |

### 16.4 Security repair behaviour

Custody-source authority is now a **policy-owned capability** (`CustodyAuthorityCapability`), never a value the record or a callback supplies:

* mintable only through `from_reviewed_context`, which re-validates the manifest through `TrustedAuthorityContext.from_reviewed_root` (a `model_construct`-forged context dies there) and requires a **loader-issued `SemanticAuthority`** carrying the authority module's private issuance seal;
* bound to record identity (artifact / approval / registry digest and record kind) and to the knowledge cutoff;
* `ConsumerPolicy._custody_grant` **never consults** `derived.custody_source_authorized`.

Consequences, all enforced by tests: a caller `rederive` cannot accept; agreement between two forged verdicts cannot accept; cross-record and cross-cutoff reuse cannot accept; verified evidence bytes do not authorize a source.

**Empty manifest ⇒ no operator authority.** The shipped `approval_manifest.json` has `"artifacts": {}`, so `ATTESTED_OPERATOR` cannot be minted: the authorization gate returns `INTEGRATION_REQUIRED`. `SYNTHETIC_TEST_ONLY` capability exists solely so downstream field-scope logic stays testable, reports `custody_source_authorization_status="SYNTHETIC_TEST_ONLY"`, and can never report `AUTHORIZED` or `custody_source_authorized=True`.

**Frozen model untouched.** No `authority_origin` field was added to `RecordVerification`; the authority lives externally, as the frozen plan requires.

**Ordering.** PIT and replay are adjudicated before the authority gate, so an inadmissible record is still `REFUSE`d regardless of what any custody source claims, while authorization itself can only yield `INTEGRATION_REQUIRED` or an attested `ACCEPT`.

### 16.5 Test results (Phase 4)

| Suite | Result |
|---|---|
| P3 conformance module | **79 passed** — the original 70 preserved unmodified in behaviour, plus 9 new authority-boundary tests |
| `tests/crypto_sensor_fabric/normalization` (P2a–P2e, I05, I09, I10 scope, P3) | **1310 passed**, 0 failed, 0 errors |
| `tests/crypto_sensor_fabric/storage` targeted set — I05 evidence/adversarial/retry, I06, I09 evidence/admission/quota, I10 evidence/schema/relations, I11R2 governance + evidence | **265 passed**, 0 failed |

The whole `storage` directory was attempted first and abandoned: it ran at roughly 4 %/min and stalled in slow database-backed modules, so the required I05/I06/I09/I10/I11 set was run explicitly instead. That is a deliberate scope decision, not a substitute claim: modules outside that set (`test_i11_postgres_*`, `test_i11r1_postgres_integration`, `test_i11r1_defect_reproduction`) were **not** executed here and are reported as unrun rather than passed.

I05 and I10 scope audits are green in this full checkout, including their previously blocking **unstaged** assertions — the R3/R4 failures were the partial-checkout deletions, confirmed by their disappearance rather than by relaxing the tests.

Historical positive-path fixtures were updated only to the new bounded model: they now construct the policy with an explicitly non-authoritative synthetic capability, and the cached-path test asserts `SYNTHETIC_TEST_ONLY` rather than `AUTHORIZED`.

### 16.6 Changed paths

* `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py` — capability repair + 9 boundary tests
* `quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` — publisher output, one count line
* this evidence document

No source module under `quant-lab/src/` was modified.

### 16.7 Remaining unverified authority dimensions

1. **No approved operator-authority mechanism exists.** `ATTESTED_OPERATOR` is unreachable while the shipped manifest approves nothing; wiring one requires a reviewed manifest plus operator review, which is out of scope here.
2. **In-process data boundary only.** The capability is not a signature scheme and does not resist code running with the application's privileges (`model_construct` skips validators) — the `authority` loader's own bounded claim.
3. **`custody_status` remains report-only** and still reflects the record's own claim; it is not authority.
4. No production consumer, provider certification, custody authorization or program-gate promotion exists; `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED`.
5. The red-team branch's own adversarial file is not part of this implementation branch, so those cases are not counted here.

---

## 17. R2 directive recovery addendum (parallel trust-consumer build)

**Starting HEAD:** `ea1fdeb7714b57f07085eb6dfadefafccd7658bb`
**Final HEAD:** recorded by the commit that follows this section.
**Reference base:** Integration R1 `3e53a6589` (ancestor of every commit below).

### 17.1 What recovery found

The SENSOR-B5-I09P3-R2 directive arrived after this branch had already completed
R3 and R5. Phase 0 recovery therefore found **no unbuilt requirement and no
unfinished work**: the R2 phases are a subset of what is already committed.
Recovery also found three dirty tracked artifacts in the worktree
(`BLOC_04_I15*`), which were non-hermetic side effects of an earlier suite run —
restored, verified clean, and **not** committed.

| Commit | Scope |
|---|---|
| `03da8e4c9` | conformance engine + adversarial suite |
| `aa784c114` | implementation evidence document |
| `c0e3440bf` | offset-aware equality and DST boundaries |
| `5ce62c26d` | R3 governance conformance closure |
| `8360c9dd1` | R5 governance count republish (1,097) |
| `ea1fdeb77` | R5 custody-authority repair |

### 17.2 Four mandatory inspections (Phase 1)

All four run in one central `_apply`, so every path — single, batch, cached,
deserialized, evidence-reread — is subject to the same policy.

| Inspection | Enforcement |
|---|---|
| 1. Trust scope | `derived.trust_scope` must be `ECONOMIC_FIELD_BINDING`, else `REFUSE / FORGED_TRUST_SCOPE` |
| 2. Unverified dimensions | non-empty required on every verdict, else `REFUSE / EMPTY_UNVERIFIED_DIMENSIONS`; preserved on all exit paths |
| 3. Custody-source authorization | decided by a policy-owned capability (R5) — `custody_verified` and the record's own `custody_source_authorized` flag confer nothing; no capability ⇒ `INTEGRATION_REQUIRED` |
| 4. Field allowlist | every required field must appear in `fields_verified`, else `REFUSE / FIELD_NOT_IN_ALLOWLIST`; sibling fields are not substitutes |

`custody_verified=True` never implies `custody_source_authorized=True`, and the
in-memory `DeterministicEvidenceStore` cannot create authorization: it is a
fixture for byte rebinding only.

### 17.3 Copied verdicts and bytes (Phase 2)

`evaluate` re-derives through the consumer's own `rederive` and compares
`approval_id`, `registry_digest`, `artifact_id`, `trust_scope`,
`fields_verified` and `custody_source_authorized`; any divergence is
`REFUSE / CACHED_VERDICT_DIVERGENCE`. At consumption the bytes are re-read from
the store and re-hashed: missing bytes are `EVIDENCE_BYTES_MISSING`, substituted
bytes are `EVIDENCE_BYTES_MISMATCH`. A digest alone, with no bytes, is refused.

R5 sharpened this further: matching cached and re-derived verdicts are *not*
authority either, because the authority lives outside the verdict entirely.

### 17.4 PIT and replay independence (Phase 3)

The engine reuses `pit_availability_refusal` and the I05
`ReplayEligibility`/`assess_replay_eligibility` gate; it duplicates neither rule.
Both are adjudicated **before** the custody gate, so an inadmissible record is
`REFUSE`d regardless of what any custody source claims. The 2x2 matrix
(PIT × replay) is asserted directly, and refusal reasons stay independently
applicable and separately reported.

### 17.5 Attack matrix (Phase 4) — 24 of 24 present

| # | Attack | Test |
|---|---|---|
| 1 | Forged verdict scope | `test_01_forged_trust_scope` |
| 2 | Missing unverified dimensions | `test_02_empty_unverified_dimension_set` |
| 3 | Unauthorized custody source | `test_04_unauthorized_custody_source` |
| 4 | Missing evidence bytes | `test_07_evidence_missing_at_consumption` |
| 5 | Digest mismatch | `test_06_evidence_byte_substitution` |
| 6 | Approval ID substitution | `test_08_copied_verdict_forged_approval_id` |
| 7 | Registry digest substitution | `test_09_copied_verdict_forged_registry_digest` |
| 8 | Artifact ID substitution | `test_forged_artifact_id` |
| 9 | Forged verified-field list | `test_forged_field_allowlist` |
| 10 | Cached verdict after revocation | `test_10_cached_verdict_after_approval_revocation` |
| 11 | Same-day date-only PIT ambiguity | `test_11_same_day_date_only_pit_ambiguity` |
| 12 | Missing PIT availability | `test_12_missing_approval_availability` |
| 13 | Naive cutoff | `test_13_naive_evaluation_cutoff_refused` |
| 14 | Offset-aware equality | `test_14_*` (5 cases) |
| 15 | DST edge cases | `test_15_*` (4 cases) |
| 16 | PIT/replay disagreement | `test_14_pit_admissible_but_replay_blocked`, `test_15_replay_eligible_but_pit_inadmissible`, 2x2 matrix |
| 17 | Unverified sibling field | `test_17_sibling_canonical_field_substitution` |
| 18 | False liquidation transformation | `test_18_liquidation_record_claiming_verified_economic_transformation` |
| 19 | Mixed-acceptance batch | `test_19_batch_mixed_trusted_and_refused` |
| 20 | Serialization dropping limitations | `test_03_unverified_dimensions_omitted_during_serialization` |
| 21 | Unauthenticated acquisition lineage | `test_21_unauthenticated_source_lineage_promotion`, `test_23_missing_acquisition_lineage` |
| 22 | Forged instrument/revision identity | `test_22_forged_instrument_identity` |
| 23 | Refusal retry bypass | `test_20_refusal_incorrectly_retried_as_transient` |
| 24 | Cutoff auth mistaken for PIT | `test_24_no_cutoff_authentication_presented_as_pit_admission` |

Beyond the 24, R5 added 9 authority-boundary tests (AT43, AT53–AT56, cross-cutoff,
synthetic-not-attested, empty-manifest, evidence-bytes-≠-authority).

### 17.6 Multipath consistency (Phase 5)

One `ConsumerPolicy` with typed `ConsumerDecision` outcomes serves single,
cached, deserialized and evidence-reread paths; `TestMultiPathConformance`
asserts the same verdicts on each. There is no second, drifting policy.

### 17.7 Focused regression (Phase 7)

| Suite | Result |
|---|---|
| P3 conformance module | **79 passed** |
| `tests/crypto_sensor_fabric/normalization` (P2a–P2e, I05, I09, I10 scope, P3) | **1310 passed** |
| Storage governed set (I05/I06, I09, I10, I11R2) | **265 passed**, 0 failed, 0 errors |

### 17.8 Canonical regression status

A **COMPLETE** canonical run of the full 4,719-node universe exists
(`canonical-p3-r1`, disposition `COMPLETE`, outcome GREEN, 4,708 passed / 0
failed / 11 platform skips, collected digest = executed digest), produced by the
hermetic runner on the dedicated canonical branch at commit `725fa4d15`.

**Scope caveat, stated plainly:** that run executed on
the canonical branch, whose *test tree* is identical to this HEAD's (the
differences are the runner scripts, the governance count and documentation). It
is therefore strong evidence for this code and P3's 79 nodes were green inside
it, but it is not a run of this branch's HEAD and is not presented as one.

### 17.9 Governance and scope (Phase 6)

* Approval manifest remains empty: `"artifacts": {}`.
* Tracked `.py` = **1,097**, matching the published governance count exactly.
* No allowlist widened; no production module modified; `quant-lab/src/` untouched by this directive.
* The engine stays in the experimental test-only namespace — no ingestion wiring.
* Agent 2 branches untouched: `p3-redteam-r1` `532e11e2b`, `p3-redteam-r2` `982492766`, `p3-redteam-r3` `d829e0e69`, `p3-r5-reattack` `49e081c5d`.

### 17.10 Remaining unverified dimensions

1. No approved operator-authority mechanism exists, so `ATTESTED_OPERATOR` cannot be minted; the gate returns `INTEGRATION_REQUIRED` by design.
2. The capability is an in-process data boundary, not a signature scheme.
3. `custody_status` remains report-only.
4. Production integration remains deferred and out of scope.

### 17.11 Disposition

`P3_R1_IMPLEMENTATION_READY_FOR_INDEPENDENT_AUDIT` — the implementation and its
attack matrix are complete and green on this branch; nothing is self-ratified
and no production authority is claimed.

---

## 18. R6 addendum (six independent findings executed to repair)

**Starting HEAD:** `e3cf47ff5b9f089ff02ff64db70f6d25922ebbd2`
**Branch:** `agent/crypto-sensor-fabric-trust-consumer-r6`
**Independent findings:** reattack branch `49e081c5da5affba9f421e2e5c61d3bfe3acb780`

### 18.1 The six findings are real

Reproduced against unmodified R5 with the adversary's own test file, executed as a
transient overlay (never committed, deleted before any governance run):

```
6 failed, 23 passed in 2.33s
FAILED ...::TestR3Replay::test_rg08_forged_replay_eligibility_cannot_authorize
FAILED ...::TestCapabilityForgery::test_cap01_direct_construction_with_attested_operator
FAILED ...::TestCapabilityForgery::test_cap02_manifest_digest_is_never_validated
FAILED ...::TestCapabilityForgery::test_cap03_basis_is_plain_replaceable_data
FAILED ...::TestCapabilityForgery::test_cap08b_provider_substitution
FAILED ...::TestCapabilityForgery::test_cap12_record_kind_substitution
```

CAP12's failure text is the clearest statement of the defect:

```
decision=ACCEPT_FIELD_BINDING (authorized=True, status='AUTHORIZED')
```

R5's "policy-owned capability" was a public dataclass. Constructing it, or
`dataclasses.replace`-ing it, was enough to mint operator authority — AT53's
attacker was relocated, not removed.

### 18.2 Repairs

| Finding | Repair |
|---|---|
| CAP01 direct construction | Issuance is marked by a module-private object stored **outside** the dataclass fields (``object.__setattr__`` in ``_issue``); ``_custody_grant`` requires that marker. Ordinary construction carries none. |
| CAP03 ``replace`` promotion | Because the marker is not a field, ``dataclasses.replace`` cannot carry it onto a promoted copy, so the copy authorizes nothing. |
| CAP02 unvalidated digest | An attested capability must carry ``manifest_sha256 == TRUSTED_MANIFEST_SHA256``. |
| CAP08b provider substitution | ``provider`` is bound into the grant and compared with the record's provider; ``None`` never matches. |
| CAP12 kind wildcard | ``record_kind`` is required for an attested grant and compared exactly; the ``None`` wildcard is gone. |
| RG08 forged replay | Replay is adjudicated by the policy from frozen ``ReplayEvidence`` via I05's ``assess_replay_eligibility``. A caller-supplied object is flattened to ``NOT_POLICY_DERIVED`` and **refused**; it can never unlock acceptance. |

The capability is still a dataclass (so ``replace`` remains usable), but issuance — not
shape — is what grants authority. With the shipped manifest empty, no path can mint
``ATTESTED_OPERATOR``, so genuine operator authority remains **unavailable by construction**.

### 18.3 Post-repair results

| Suite | Result |
|---|---|
| Adversary overlay — the six + 23 R3 gates | **28 passed, 1 failed** (see 18.4) |
| P3 conformance module | **93 passed** (79 preserved + 14 new R6 tests) |
| `tests/crypto_sensor_fabric/normalization` | **1324 passed** |
| Storage governed set (I05/I06, I09, I10, I11R2) | **265 passed**, 0 failed, 0 errors |

Each of the six now fails closed with ``INTEGRATION_REQUIRED`` (or ``REFUSE`` for RG08),
never ``AUTHORIZED``.

### 18.4 One disclosed conflict: RG05

``test_rg05_cutoff_binding_exists_and_is_enforced`` asserts that a **directly
constructed ATTESTED_OPERATOR capability must be honoured at its own cutoff**
(``ACCEPT_FIELD_BINDING``). That positive leg *is* the CAP01 bypass: satisfying it and
satisfying CAP01 are mutually exclusive. The security finding wins. The cutoff-binding
property is preserved and re-asserted under synthetic semantics in
``test_r6_14_same_cutoff_is_honoured_under_synthetic_semantics`` (same cutoff →
``SYNTHETIC_TEST_ONLY`` acceptance; later cutoff → ``INTEGRATION_REQUIRED``).
RG05's refusal leg (cross-cutoff reuse) still passes.

The adversary's test file was **not** modified and **not** committed; the conflict is
reported rather than silenced by editing their assertion.

### 18.5 New negative tests (14)

Forged capability with correct identity · replaced basis · wrong manifest digest ·
provider substitution · record-kind mismatch · cross-record reuse · cross-cutoff reuse ·
forged replay object · cached forged verdicts · synthetic-never-attested ·
correct digest with unauthorized custody · empty manifest mints nothing ·
policy-derived replay from real evidence · same-cutoff binding under synthetic semantics.

### 18.6 Governance

* Frozen Bloc 5 plans unchanged; manifest ``artifacts == {}``.
* Tracked ``.py`` = **1,097**, matching the published I11R2 count exactly (no publisher run needed: no file added or removed).
* I05/I10 scope audits green inside the 1324-test run.
* No production module modified; no live consumer; historical evidence untouched.
* The red-team overlay was transient and is absent from the tree.

### 18.7 Remaining limitations

1. The issuance marker is an in-process data boundary. Code that reaches ``object.__setattr__`` with module internals is outside the model — the same bound the ``authority`` loader documents.
2. ``custody_status`` remains report-only.
3. ``ATTESTED_OPERATOR`` is unreachable while the manifest is empty; that is intended, not pending work.
4. Replay-eligible acceptance is no longer asserted from a caller object anywhere; ELIGIBLE classification is proven by the I05 gate's own suite, which the policy now calls directly.

### 18.8 Disposition

`R6_READY_FOR_INDEPENDENT_REATTACK` — the six reported grants are closed and verified by
the adversary's own tests, with one mutually-exclusive test documented rather than edited.

---

**Signed off:** Agent 1 — Implementation Lead
**Status:** `P3_R1_IMPLEMENTATION_READY_FOR_INDEPENDENT_AUDIT` (full-checkout regression still outstanding, reported as blocked) — experimental, fail-closed, test-only; no production authority claimed.