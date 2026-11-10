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
- **Adversarial test suite:** 24 attack families covering forged scope, empty unverified dimensions, unauthorized custody source, missing/substituted evidence bytes, approval/registry/artifact/field-allowlist forgery, cached verdict after revocation, same-day date-only PIT ambiguity, naive cutoff, PIT/replay disagreement, sibling-field substitution, false liquidation transformation claim, mixed batch, retry bypass, unauthenticated acquisition lineage, forged instrument identity, no-cutoff-auth-as-PIT-approval.
- **Multipath conformance:** identical policy across single-record, cached, deserialized, evidence-reread, and refusal-handling paths.
- **Governance scope:** `INTEGRATION_STATE` unchanged (`INTEGRATION_REQUIRED`), no custody authority created, no whole-record trust assertion, approval manifest remains empty.

### Remaining (not done by this workstream; deliberately deferred)

- **Focused regression on existing P2a–P2e / I05 / I06 / I09 / I10 / I11 suites:** could not be executed in this sparse checkout because those test files are tracked but not materialized on disk (5051 `D` entries in worktree status). Agent 2 owns the full canonical regression slot; this workstream's isolated suite (61 tests) passes.
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
├── test_b5_i09p2e_trust_consumer.py   (implementation + 61 tests)
└── P3_I09P2E_TRUST_CONSUMER_EVIDENCE.md  (this document)
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

61 tests, **61 passed**. Adversarial families (24):

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
| 14 | PIT admissible but replay blocked | REFUSE `REPLAY_BLOCKED`, `pit_status=ADMISSIBLE` |
| 15 | Replay eligible but PIT inadmissible | REFUSE `PIT_INADMISSIBLE` |
| 16 | Unlisted canonical field required | REFUSE `FIELD_NOT_IN_ALLOWLIST` |
| 17 | Sibling canonical field substitution (`trade_volume` for `trade_price`) | REFUSE `FIELD_NOT_IN_ALLOWLIST` |
| 18 | Liquidation record claiming verified economic transformation | `record_transformation_verified=False`, `downstream_trusted=False`, INTEGRATION_REQUIRED |
| 19 | Mixed-acceptance batch (one good, one forged) | per-record independent outcomes; forged refused |
| 20 | Refusal incorrectly retried as transient | same digest-mismatch refusal on retry — not transient |
| 21 | Unauthenticated source lineage promotion | model construction raises (contradictory state) |
| 22 | Forged instrument identity | `instrument_authenticated=False`, `instrument_authentication_ref=None` |
| 23 | Missing acquisition lineage | `SOURCE_LINEAGE` / `ACQUISITION_LINEAGE` in unverified_dimensions; not synthesized |
| 24 | No-cutoff authentication presented as PIT approval | REFUSE `PIT_INADMISSIBLE` |

Plus multipath conformance tests (single, cached, deserialized, evidence reread, typed refusal handling) and governance scope tests (integration state unchanged, trust scope constant, no custody authority created, no whole-record trust assertion).

## 9. Focused regression

| Suite | Result |
|---|---|
| New P3 conformance suite (`test_b5_i09p2e_trust_consumer.py`) | **61 passed** |
| P2a–P2e, I05/I06 replay, I09 semantic determinism, I10 scope, I11 nonregression | Not executed — sparse checkout; those test files are tracked but not materialized (5051 `D` entries). Agent 2 owns the full canonical regression slot. |
| Relevant governance predicates | `INTEGRATION_STATE == INTEGRATION_REQUIRED` verified in-test; approval manifest empty verified in-worktree |

No source modules were modified by this workstream, so there is no source-level regression to detect from this change. Dependent primitives were reused unchanged.

## 10. Canonical regression status

**Not run by this workstream.** The full canonical regression of the integration candidate is Agent 2's responsibility and requires a full (non-sparse) checkout. This workstream's result is limited to its own isolated suite (61 passed). Reported explicitly as incomplete rather than adjudicated.

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

**Signed off:** Agent 1 — Implementation Lead
**Status:** `P3_R1_IMPLEMENTATION_READY_FOR_INDEPENDENT_AUDIT` — experimental, fail-closed, test-only; no production authority claimed.