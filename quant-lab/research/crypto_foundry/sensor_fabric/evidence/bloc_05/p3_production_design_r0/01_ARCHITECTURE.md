# P3 PRODUCTION TRUST CONSUMER — ARCHITECTURE (R0)

**Checkpoint:** SENSOR-B5-P3-PRODUCTION-TRUST-CONSUMER-DESIGN-R0
**Base:** consolidated candidate `6de26be9130eb99e0a9b53b340fc5bfaafa4a684`
**Status:** design only. No production source is changed by this checkpoint.

---

## 1. What exists today

Production already owns the *derivation* half of the trust contract, and owns it well:

| Production module | What it already guarantees |
|---|---|
| `normalization/authority/__init__.py` | loader-issued `SemanticAuthority` behind a private `_LOADER_SEAL`; `ApprovalManifest`/`ApprovedArtifact`; duplicate-key-rejecting `parse_approval_manifest`; `manifest_digest`/`evidence_digest`; `load_semantic_authority`, `load_trusted_authority`, `verify_evidence_custody`, `verify_mapping_provenance`; the pinned `TRUSTED_MANIFEST_SHA256 = 3d707c59…2654` |
| `normalization/sensors/verification.py` | `RecordVerification` with self-enforcing trust laws and `assert_trustworthy()`; `TrustedAuthorityContext.from_reviewed_root` (refuses any manifest that is not the pinned root); `TrustedCustodyProvider` protocol + `BlobStoreCustody`; `_custody_verified` (re-hashes bytes, refuses a caller-supplied digest map); `verify_trade_record`, `verify_liquidation_record`; `INTEGRATION_STATE = "INTEGRATION_REQUIRED"`; `TRUST_SCOPE_ECONOMIC_FIELD_BINDING` |
| `normalization/time/replay_gate.py` | `ReplayEvidence`, `ReplayEvaluation`, `assess_replay_eligibility`, `UnassessableReplayEvidence` |
| `normalization/identity/*` | provider/record identity and lifecycle/cutoff resolution |
| `normalization/models.py` | `NormalizationModelBase`, canonical JSON bytes, frozen/extra-forbid conventions |

A grep confirms the gap precisely: **no module under `quant-lab/src/` outside `sensors/verification.py` mentions `RecordVerification`, `downstream_trusted`, or `verify_trade_record`.** The verdict type exists; nothing consumes it.

The *consumption* half — `ConsumerPolicy`, `ConsumerDecision`, `ConsumerVerdict`, `CustodyAuthorityCapability`, `AuthorityBasis` — exists **only** in `quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py`.

## 2. The architectural defect to fix

That harness contract accepts:

```python
evaluate(candidate, rederive: Callable[[], RecordVerification], ...)
```

A callable's *name* proves nothing. `rederive` is invoked and its return value trusted; any caller who can pass a lambda can pass one that returns a `model_copy(update=...)` forgery, a fixture, or a replayed object. The harness mitigates this with `assert_trustworthy()` and cached-verdict divergence checks, but that is *detection after the fact* of a value the policy never derived. Production must not inherit this shape.

**Production principle: derivation, not assertion.** The consumer never receives a verification object. It receives a *request* that names the record and the fields wanted, and it calls the verifier itself, with a context and custody provider that the policy holds.

## 3. Target architecture

```
                     untrusted                      trust boundary                      trusted
   ┌────────────────────────┐        ┌──────────────────────────────────────────────────────────┐
   │ record producer / venue│        │  TrustConsumerPolicy (new, production)                    │
   │ raw record + bytes     │───────▶│  1. validate ConsumerRequest (shape, not authority)       │
   └────────────────────────┘        │  2. construct TrustedAuthorityContext.from_reviewed_root  │
                                     │     over PINNED manifest bytes held by the policy         │
                                     │  3. call verify_trade_record / verify_liquidation_record  │
                                     │     (policy-held custody provider)                        │
                                     │  4. assert_trustworthy() on the derived verdict           │
                                     │  5. inspect: scope, dimensions, fields, PIT, replay       │
                                     │  6. re-bind evidence bytes at consumption                 │
                                     │  7. derive custody authority from pinned manifest bytes   │
                                     │  8. return ConsumerVerdict (typed, bounded, fail-closed)  │
                                     └──────────────────────────────────────────────────────────┘
                                                        │
                                            ┌───────────┴───────────┐
                                            ▼                       ▼
                                    SemanticAuthority       ReplayEvaluation
                                    (loader-issued)         (policy-applied)
```

Four rules carry the boundary:

- **R1 — The policy derives the verdict.** No caller-supplied `RecordVerification` is ever inspected as evidence; a `candidate` may only be used for *divergence detection* against a freshly derived verdict, never in its place.
- **R2 — The policy owns the root.** `TrustedAuthorityContext` is built by the policy from pinned bytes it loads itself. Manifest bytes arriving with the record are compared, never used.
- **R3 — The policy owns replay.** `assess_replay_eligibility` is applied by the policy to `ReplayEvidence`; a caller-supplied eligibility object is flattened to `NOT_POLICY_DERIVED` and blocks.
- **R4 — The policy owns custody authority.** Authorization is *recomputed from the pinned manifest at every evaluation*, not carried as an object.

R4 is the significant departure from the harness and is argued in `03_TRUST_BOUNDARY_SPEC.md` §5.

## 4. Why not port the harness

The harness is a conformance oracle, not an implementation: it contains a `DeterministicEvidenceStore` fixture, a `synthetic_for_field_scope_tests` capability constructor, an `ATTESTED_OPERATOR` basis that cannot be minted under an empty manifest, and AT-numbered attack fixtures. Copying it into `src/` would move test scaffolding into the trusted path and, worse, ship a `SYNTHETIC_TEST_ONLY` basis in production code where a future caller could mistake it for a weakened authorization state.

Production takes: the *decision taxonomy*, the *inspection order*, the *refusal vocabulary*, and the *fail-closed result shape*. Production does not take: the store fixture, the capability object, the synthetic basis, or the callback.

## 5. Non-goals for R0

- No implementation, no interface freeze, no stub modules committed under `src/`.
- No change to `INTEGRATION_STATE`, the approval manifest, provider boundaries, or the ledger.
- No claim that the empty-manifest `INTEGRATION_REQUIRED` state can be resolved by any code in this repository: it is a custody fact, not a bug.

## 6. Reading order

`02_RESPONSIBILITY_MATRIX.md` (who owns what) → `03_TRUST_BOUNDARY_SPEC.md` (the enforceable boundaries) → `04_THREAT_MODEL.md` (what is in and out of scope) → `05_IMPLEMENTATION_RUNGS.md` (sequence and stops) → `06_ACCEPTANCE_MATRIX.md` (how each rung is judged) → `07_RISK_REGISTER.md` → `08_PROPOSED_CODE_PATHS.md`.
