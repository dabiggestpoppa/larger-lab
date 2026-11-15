# PROPOSED CODE PATHS, COMPONENT PLAN AND INTERFACE SKETCHES

**Nothing in this document exists yet.** No file under `quant-lab/src/` is created or modified by this checkpoint. Paths are proposals for a later implementation directive.

## 1. New files (three modules, deliberately)

```
quant-lab/src/crypto_sensor_fabric/normalization/consumer/__init__.py
quant-lab/src/crypto_sensor_fabric/normalization/consumer/models.py
quant-lab/src/crypto_sensor_fabric/normalization/consumer/custody_authority.py
quant-lab/src/crypto_sensor_fabric/normalization/consumer/policy.py
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py
```

Why three modules and not six: `models` (data), `custody_authority` (one derivation), `policy` (orchestration + rebinding + fail-closed). Rebinding stays a private function in `policy.py` (≈30 lines) rather than its own module; a separate module earns its keep only when a second consumer exists.

## 2. Component plan

### C1 — `consumer/models.py`

| Aspect | Detail |
|---|---|
| Responsibility | Typed request and verdict; the refusal vocabulary |
| Inputs | — (pure types) |
| Outputs | `ConsumerRequest`, `ConsumerVerdict`, `ConsumerDecision`, `ConsumerRefusalReason`, `CustodyAuthorityBasis` |
| Trust boundary | Accepts untrusted data *shapes*; mints no authority |
| Dependencies | `normalization.models.NormalizationModelBase` only |
| Failure | Validation error on construction (frozen, `extra="forbid"`, naive-datetime refused) |
| Invariants | No field typed as a verdict/authority object; `ConsumerDecision` has exactly 3 members; basis has exactly 3 members and no synthetic one |
| Tests | A1.1–A1.5 |
| Reuse | `NormalizationModelBase`, `OpaqueIdentifier`, `canonical_json_bytes` |

```
ConsumerRequest(
    record: T1TradeRecord | T1LiquidationRecord,
    artifact_bytes: bytes,
    required_fields: tuple[str, ...] = (),
    evidence_references: Mapping[str, str] | None = None,  # reference -> approved digest
    knowledge_cutoff: datetime | None = None,
    replay_evidence: ReplayEvidence | None = None,
    claimed_manifest_bytes: bytes | None = None,           # compared, never adopted
)

ConsumerVerdict(
    decision, verified_field_allowlist, unverified_dimensions, trust_scope,
    pit_status, replay_status, custody_status,
    custody_source_authorized: bool, custody_source_authorization_status,
    refusal_reason, refusal_detail,
)
```

### C2 — `consumer/custody_authority.py`

| Aspect | Detail |
|---|---|
| Responsibility | Derive `AUTHORIZED / INTEGRATION_REQUIRED / UNAUTHORIZED` from pinned manifest bytes for one bound identity tuple |
| Inputs | `manifest_bytes` (policy-pinned), `artifact_id`, `approval_id`, `registry_digest`, `record_kind`, `provider`, `knowledge_cutoff` |
| Outputs | `(CustodyAuthorityBasis, status_detail)` |
| Trust boundary | Reads only policy-held bytes; never accepts a caller authorization object |
| Dependencies | `authority.parse_approval_manifest`, `authority.manifest_digest`, `authority.TRUSTED_MANIFEST_SHA256` |
| Failure | Malformed manifest ⇒ `UNAUTHORIZED`; empty manifest ⇒ `INTEGRATION_REQUIRED`; any binding mismatch ⇒ `INTEGRATION_REQUIRED` |
| Invariants | Under `"artifacts": {}` this function cannot return `AUTHORIZED`; no global mutable state; pure w.r.t. its arguments |
| Tests | A3.1–A3.3 |
| Reuse | `ApprovalManifest`, `ApprovedArtifact`, the pin, `record_kind` semantics already used by the harness (`CAP12`) |

```
def derive_custody_authority(
    *, manifest_bytes: bytes, artifact_id: str, approval_id: str,
    registry_digest: str, record_kind: str | None, provider: str | None,
    knowledge_cutoff: datetime | None,
) -> tuple[CustodyAuthorityBasis, str]
```

**Note on the empty-manifest law.** The returned basis is computed, so `INTEGRATION_REQUIRED` is a *result*, not a default. There is no parameter that can change it — which is the property the shipped state depends on.

### C3 — `consumer/policy.py`

| Aspect | Detail |
|---|---|
| Responsibility | Own the root, registry and custody provider; derive the verdict; inspect in normative order; re-bind evidence; fail closed |
| Inputs | A `ConsumerRequest`; policy-held `TrustedAuthorityContext` source (pinned bytes), `NormalizationMethodologyRegistry`, `TrustedCustodyProvider` |
| Outputs | `ConsumerVerdict` — every path returns one, including failures |
| Trust boundary | The only place where untrusted data meets trusted derivation |
| Dependencies | `sensors/verification.py` (`verify_trade_record`, `verify_liquidation_record`, `TrustedAuthorityContext`, `RecordVerificationError`), `time/replay_gate.assess_replay_eligibility`, `authority.evidence_digest`, C1, C2 |
| Failure | Typed refusal ⇒ mapped REFUSE; unexpected ⇒ REFUSE `VERIFIER_CRASH` with bounded detail; `KeyboardInterrupt`/`SystemExit` propagate |
| Invariants | One derivation per consumption; PIT and replay before authority; no cached verdict ever accepted; identical inputs ⇒ identical verdict (no wall clock, no RNG) |
| Tests | A2.1–A2.5, A4.1–A4.5 |
| Reuse | All of the verifier; replay gate; `evidence_digest`; `TrustedCustodyProvider` |

```
class TrustConsumerPolicy:
    def __init__(self, *, root_loader, methodology_registry, custody: TrustedCustodyProvider | None = None) -> None
    def evaluate(self, request: ConsumerRequest) -> ConsumerVerdict
    def check_against(self, request: ConsumerRequest, candidate: RecordVerification) -> ConsumerVerdict  # divergence only
    # private
    def _derive(self, request) -> RecordVerification          # calls the verifier
    def _inspect(self, derived, request) -> ConsumerVerdict   # normative order
    def _rebind(self, references, custody) -> None | raise    # private, ~30 lines
    def _fail_closed(self, exc) -> ConsumerVerdict
```

`rederive: Callable[[], RecordVerification]` is **absent by design** — see `03_TRUST_BOUNDARY_SPEC.md` §C.

## 3. Existing code touched

| File | Change |
|---|---|
| `sensors/verification.py` | **none** |
| `normalization/authority/__init__.py` | **none** |
| `normalization/time/replay_gate.py` | **none** |
| `normalization/models.py` | **none** |
| `config/.../approval_manifest.json` | **none** (stays empty) |
| `quant-lab/src/**` overall | **zero changes in this checkpoint** |

## 4. Reuse ledger (explicit non-duplication)

| Need | Reused symbol | New code written |
|---|---|---|
| record verification | `verify_trade_record`, `verify_liquidation_record` | none |
| trusted root | `TrustedAuthorityContext.from_reviewed_root` + `TRUSTED_MANIFEST_SHA256` | none |
| approval parsing | `parse_approval_manifest`, `ApprovalManifest` | none |
| digest | `manifest_digest`, `evidence_digest` | none |
| custody bytes | `TrustedCustodyProvider`, `_custody_verified` | rebinding call only |
| replay | `assess_replay_eligibility`, `ReplayEvidence` | flattening of foreign objects |
| PIT | `_require_cutoff`, `_assert_intraday_pit`, `pit_availability_refusal` | none |
| result laws | `RecordVerification._trust_laws`, `assert_trustworthy` | inspection, not re-validation |

## 5. Governance placement of this design

Published under `quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/p3_production_design_r0/` because the frozen I10 scope audit admits that prefix and **rejects** new top-level trees (it already rejected `.github/` during the I09 CI checkpoint). Documentation must not widen a sealed path allowlist.

## 6. Estimated effort and remaining rungs

| Rung | Scope | Estimate | Can start |
|---|---|---|---|
| 1 | models + laws | small (≈1 day) | now, independent |
| 2 | derivation ownership | medium (≈2–3 days) | after R1 |
| 3 | custody authority derivation | medium (≈2 days) | after R2 |
| 4 | replay/PIT/rebinding ordering | medium (≈2 days) | after R3 (rebind part independent) |
| 5 | A01–A20 negative suite | medium (≈2–3 days) | **now**, from the threat model |
| 6 | canonical regression + independent audit | large (≈1 day per run + audit latency) | after R5 |
| 7 | governance reconciliation | small (≈1 day) | after R6 |

**Remaining rungs after this design: 7.** None of them is authorized by this document.
