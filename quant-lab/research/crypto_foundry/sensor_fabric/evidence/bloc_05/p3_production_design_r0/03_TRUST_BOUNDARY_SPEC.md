# PRODUCTION TRUST-BOUNDARY SPECIFICATION

Each boundary below states the rule, the mechanism that enforces it, the attack it stops, and how a reviewer can observe that it holds.

---

## A. Record producers may provide data

**Rule.** A producer supplies record content and artifact bytes. Nothing it supplies is authority.

**Mechanism.** `ConsumerRequest` carries `record`, `artifact_bytes`, and optional `claimed_manifest_bytes`. The policy **ignores** `claimed_manifest_bytes` for derivation and only compares it against the pinned root, refusing on mismatch (`TRUSTED_CONTEXT_MISMATCH`).

**Stops.** An actor that supplies both the record and its approval.

**Observable.** Remove the field entirely from a request: the verdict is unchanged. Change the claimed bytes: the policy refuses rather than adopts.

**Existing enforcement.** `TrustedAuthorityContext.from_reviewed_root` already refuses non-pinned bytes; today's callers simply have no way to hand bytes in at all.

---

## B. Callers may request verification

**Rule.** A caller may name *what* it wants inspected and *which fields* it needs. It may not name the verdict.

**Mechanism.** `ConsumerRequest(record, artifact_bytes, required_fields, evidence_references, knowledge_cutoff, replay_evidence)`. `required_fields` is a narrowing filter, not a grant: unknown names refuse with `FIELD_NOT_IN_ALLOWLIST`.

**Stops.** A caller asserting `decision="ACCEPT"` — there is no such parameter.

**Observable.** The request type has no field of type `RecordVerification`, `ConsumerVerdict`, `SemanticAuthority`, or `TrustedAuthorityContext`.

---

## C. Trusted policy code owns verification derivation — the `rederive` question

**The harness accepts `rederive: Callable[[], RecordVerification]`.** A callback name is not provenance: the policy cannot distinguish a lambda that calls `verify_trade_record` from a lambda that returns `RecordVerification.model_construct(...)` or a stale cached object. The harness partly compensates (`assert_trustworthy`, divergence checks) but only *rejects forgeries it happens to notice*; it never gains proof that the value came from the verifier.

**Production rule.** The consumer **never accepts a verification object or a factory for one**. It accepts a request and returns a verdict, calling the verifier itself:

```python
# production shape (design, not implementation)
verdict = verify_trade_record(
    request.record,
    trusted_context=self._root(),                 # policy-owned, pinned
    artifact_bytes=request.artifact_bytes,
    methodology_registry=self._registry,          # policy-owned
    knowledge_cutoff=request.knowledge_cutoff,
    custody=self._custody,                        # policy-owned TrustedCustodyProvider
)
```

**Stops.** Forged, copied, fixture, replayed, and deserialized verdicts — they cannot enter the pipeline, because there is no parameter for them.

**Observable.** `TrustConsumerPolicy` has no parameter, attribute, or method argument typed `Callable[[], RecordVerification]`, and none typed `RecordVerification` on the intake path.

**Migration note.** Where a caller today holds a stored verdict, production offers *divergence detection only*: `check_against(candidate)` re-derives and refuses with `CACHED_VERDICT_DIVERGENCE` on any difference in scope, fields, identity, or custody claim. A matching candidate is **not** promoted to evidence; the freshly derived verdict is what the verdict is built from.

---

## D. Trusted policy code owns authority issuance

**Rule.** Authorization is produced by policy-owned derivation over pinned bytes, and by nothing else.

**Mechanism.** `SemanticAuthority` remains loader-issued (`_LOADER_SEAL`). Custody authorization is **recomputed** per evaluation (§5 below) rather than issued as an object.

**Stops.** Any caller-side attempt to present authority.

**Observable.** No public constructor for "authorized"; the only path to `custody_source_authorized=True` reads the pinned manifest.

---

## E. Callers cannot promote `SYNTHETIC_TEST_ONLY` into `ATTESTED_OPERATOR`

**Rule.** Production ships **no synthetic basis at all**.

The harness needs `SYNTHETIC_TEST_ONLY` so field-scope logic stays testable under an empty manifest. That value must not exist in `src/`: a production enum containing a "not really authorized but let it through" state is a permanent invitation to wire it to a config flag.

**Mechanism.** Production basis is derived, not enum-supplied:

| Derived basis | When |
|---|---|
| `AUTHORIZED` | the pinned manifest carries an approved operator-authority artifact naming this custody provider, this artifact, this record kind, this provider, and this cutoff |
| `INTEGRATION_REQUIRED` | the manifest is empty, or any binding above fails |
| `UNAUTHORIZED` | a manifest that is malformed or names a non-operator custody mechanism |

There is no synonym for `AUTHORIZED` a caller can type.

**Stops.** Promotion by construction (no field exists), promotion by copy (nothing to copy), promotion by config (`INTEGRATION_REQUIRED` is computed from bytes, not settings).

**Testability preserved.** Downstream field-scope tests inject a *test double at the policy seam* (a `TrustedCustodyProvider` + a synthetic manifest fixture passed to an internal seam), and assert that production-path code yields `INTEGRATION_REQUIRED`. The double lives in `tests/`, exactly as the harness's `DeterministicEvidenceStore` does today.

---

## F. Cached verification objects do not establish trust

**Rule.** A store may return a previously computed verdict. That verdict is evidence of *what a previous call derived*, never of *what is true now*.

**Mechanism.** On every consumption the policy re-derives; a cached object is only compared, and comparison failure is a refusal. Custody and PIT can both have changed since the cache was written (revocation, cutoff move, blob replacement).

**Stops.** Cache poisoning, stale authority after revocation, replay of an old verdict across cutoffs.

**Observable.** Deleting the cache changes only latency; every verdict field is recomputed.

---

## G. Evidence bytes are rebound before consumption

**Rule.** Verification hashed bytes at derivation time; consumption re-reads them and re-hashes them.

**Mechanism.** `rebind_evidence(references, custody)` reads each referenced blob through the policy's `TrustedCustodyProvider` and compares `evidence_digest(blob)` to the approved digest. Missing bytes → `EVIDENCE_BYTES_MISSING`; differing bytes → `EVIDENCE_BYTES_MISMATCH`. A digest that travels alone (no bytes held) is **not** custody: that is the P2B-11 / F-R1-01 defect, and it refuses.

**Stops.** Post-verification substitution of evidence; digest-only "proof".

**Observable.** Replace the blob between derive and inspect (test seam) → refusal.

---

## H. Replay eligibility is derived by the policy

**Rule.** The policy applies `assess_replay_eligibility` to `ReplayEvidence` it received as *data*. An object that merely looks like an evaluation is not an evaluation.

**Mechanism.** `ReplayEvidence` → `assess_replay_eligibility` → `ReplayEvaluation`. Any caller-supplied evaluation is flattened to `NOT_POLICY_DERIVED` with `blocked=True`.

**Stops.** RG08's "any object with `.eligibility` is eligible".

**Observable.** A forged object with `eligibility="ELIGIBLE"` yields `REPLAY_BLOCKED`, not acceptance.

---

## I. Knowledge cutoffs and provider identities are bound

**Rule.** A verdict is valid for one cutoff instant and one provider/record identity.

**Mechanism.** The verifier refuses naive/bare-date cutoffs (`_require_cutoff`) and intraday ambiguity (`_assert_intraday_pit`). The consumer binds `(artifact_id, approval_id, registry_digest, record_kind, provider, knowledge_cutoff)` into the custody-authority derivation, so authority computed at cutoff *T* cannot be reused at *T'*.

**Stops.** Cross-cutoff inheritance; cross-record reuse ("the capability I held for BTCUSDT/TRADE authorizes ETHUSDT/TRADE"); venue polarity transfer.

**Observable.** Change any bound element → `INTEGRATION_REQUIRED` (authority) or `PROVENANCE_MISMATCH` (verification).

---

## J. Empty approval manifests imply `INTEGRATION_REQUIRED`

**Rule.** The shipped manifest approves nothing (`"artifacts": {}`, schema `b5-i09p2a-1`, authority `B5_I09P2A_EMPTY_TRUST_ROOT_V1`). Therefore **no** custody source can be authorized, and `INTEGRATION_STATE` stays `INTEGRATION_REQUIRED`.

**Mechanism.** `derive_custody_authority` reads the pinned bytes; with no artifacts it returns `INTEGRATION_REQUIRED` unconditionally — not "authorized with warnings", not "authorized for tests".

**Stops.** A consumer pipeline that assumes authorization exists because code compiled.

**Observable.** Under the shipped manifest, every consumption returns `INTEGRATION_REQUIRED` regardless of input, and no code path can return `AUTHORIZED`.

---

## 5. Why authority is derived instead of issued (the capability replacement)

The harness's `CustodyAuthorityCapability` is defended by an in-process sentinel: `_ISSUANCE_MARKER`, a non-field attribute set only by `_issue()`, with the stated bounded claim that it "does not resist code running with the application's privileges".

Two demonstrated attack classes remain against any such object:

- **CAP01 — direct minting.** `CustodyAuthorityCapability._issue(...)` is reachable by name; a module-level marker is one `object()` away from reproduction.
- **CAP02 — marker copying.** `object.__setattr__(copy, "_issued", _ISSUANCE_MARKER)` (or `dataclasses.replace` plus one line) produces a "genuine" capability from a stolen identity marker.

Production cannot make an in-process sentinel uncopyable, and should not pretend otherwise. It can make copies **worthless**: if the consumer never reads an authorization object, a perfect forgery of one authorizes nothing.

**Therefore:** authorization is a function `(pinned_manifest_bytes, artifact_id, approval_id, registry_digest, record_kind, provider, cutoff) → AUTHORIZED | INTEGRATION_REQUIRED | UNAUTHORIZED`, evaluated inside the policy at consumption time from bytes the policy loaded. A caller can compute the same function — and will get `INTEGRATION_REQUIRED`, because the manifest is empty. There is no value to steal, no marker to copy, and no constructor to abuse.

This is strictly stronger than the harness for D15, and it is enforceable rather than aspirational.
