# RUNG 1 — IMPLEMENTATION-READY SPECIFICATION

Ready to execute the moment D-1 is authorized. Assumes exactly two new files (`consumer/models.py`, `test_b5_p3_consumer_contracts.py`) and no `__init__.py` unless import safety proves otherwise.

## 1. `consumer/models.py` — surface

All models inherit `NormalizationModelBase` (frozen, `extra="forbid"`, canonical JSON) as the normalization package already does. No I/O, no imports from `sensors/verification.py` at runtime.

```python
class ConsumerDecision(str, Enum):
    ACCEPT_FIELD_BINDING = "ACCEPT_FIELD_BINDING"
    REFUSE = "REFUSE"
    INTEGRATION_REQUIRED = "INTEGRATION_REQUIRED"
    # exactly three; no ACCEPT, no AUTHORIZED

class ConsumerRefusalReason(str, Enum):
    FORGED_TRUST_SCOPE
    EMPTY_UNVERIFIED_DIMENSIONS
    EVIDENCE_BYTES_MISSING
    EVIDENCE_BYTES_MISMATCH
    FIELD_NOT_IN_ALLOWLIST
    PIT_INADMISSIBLE
    REPLAY_BLOCKED
    NAIVE_CUTOFF
    CACHED_VERDICT_DIVERGENCE
    VERIFICATION_FAILED
    VERIFIER_CRASH
    UNAUTHORIZED_CUSTODY_SOURCE

class CustodyAuthorityBasis(str, Enum):
    AUTHORIZED
    INTEGRATION_REQUIRED
    UNAUTHORIZED
    # exactly three; SYNTHETIC_TEST_ONLY forbidden

class ConsumerRequest(NormalizationModelBase):
    record: T1TradeRecord | T1LiquidationRecord      # T1 only; no verdict, no authority
    artifact_bytes: bytes                             # Field(repr=False)
    required_fields: tuple[OpaqueIdentifier, ...] = ()
    evidence_references: tuple[tuple[str, str], ...] = ()   # (reference, approved_digest)
    knowledge_cutoff: datetime | None = None
    replay_evidence: ReplayEvidence | None = None
    claimed_manifest_bytes: bytes | None = None       # compared, never adopted

class ConsumerVerdict(NormalizationModelBase):
    decision: ConsumerDecision
    verified_field_allowlist: tuple[...] = ()
    unverified_dimensions: tuple[...] = ()
    trust_scope: str = "ECONOMIC_FIELD_BINDING"
    pit_status: str
    replay_status: str
    custody_status: str
    custody_source_authorized: bool = False
    custody_source_authorization_status: CustodyAuthorityBasis
    refusal_reason: ConsumerRefusalReason | None = None
    refusal_detail: str | None = None
```

### Design choices worth flagging

- **`evidence_references` as a tuple of pairs, not a `dict`.** A `dict` field is mutable-by-reference and pydantic would accept a caller-owned mapping; a tuple of pairs makes the request hashable-in-practice, order-free to compare, and impossible to mutate after construction.
- **`record` typed as the two concrete T1 records** rather than `Any`: a caller cannot smuggle a verdict or authority object through it, and pydantic validates the shape at the boundary.
- **No `custody_authority` field of any kind.** Authorization is not a request input.
- **`trust_scope` defaults to the one admissible constant** but remains a field so inspection can refuse a forged value.
- **Naive datetime rejection** comes from `NormalizationModelBase`; Rung 1 must prove it with a test rather than assume it.

## 2. A1.1–A1.5 conformance plan

| Req | Test that proves it | Failure mode if absent |
|---|---|---|
| A1.1 | reflect over `ConsumerRequest.model_fields`: no annotation resolves to `RecordVerification`, `ConsumerVerdict`, `SemanticAuthority`, `TrustedAuthorityContext`, `CustodyAuthorityCapability`, `Callable`, or any callable-returning-verdict type; and no field name in `{authority, authorized, custody_authority, trusted}` | a callback could re-enter the intake path |
| A1.2 | `set(ConsumerDecision) == {3 members}` and `len == 3` | a fourth decision (e.g. `ACCEPT`) drifts in |
| A1.3 | `set(CustodyAuthorityBasis) == {AUTHORIZED, INTEGRATION_REQUIRED, UNAUTHORIZED}` and `"SYNTHETIC_TEST_ONLY" not in members` | test-only authority ships |
| A1.4 | construct → mutate raises; extra field raises; naive cutoff raises; bare `date` raises; `model_dump()` → `model_validate()` round-trips to an equal object; `json` serialisation stable across two dumps | silent coercion / mutability |
| A1.5 | `sys.modules` inspection after importing `consumer.models` in a **clean** subprocess: `crypto_sensor_fabric.normalization.sensors.verification` not in `sys.modules` | model module drags the verifier in |

## 3. Additional negative tests (from the mission)

| Test | Assertion |
|---|---|
| unknown field | `ConsumerRequest(..., decision="ACCEPT")` raises |
| naive cutoff | `datetime(2026,6,1,12,0)` raises |
| bare date | `date(2026,6,1)` raises |
| invalid decision | `ConsumerVerdict(decision="ACCEPT", ...)` raises |
| authority injection | no field accepts an authorization value; `CustodyAuthorityBasis.AUTHORIZED` supplied anywhere in a request is rejected as an unknown field |
| mutable defaults | two instances built with defaults do not share container identity |
| copy is not authorization | `verdict.model_copy(update={...})` produces a value whose `custody_source_authorized` is unchanged by copying, and a copied request confers nothing (asserted structurally: copying cannot add a field, since `extra="forbid"`) |

## 4. What Rung 1 must NOT contain

- No import of `sensors/verification.py` (runtime), `authority`, `time/replay_gate`.
- No manifest reading, no custody access, no digest computation.
- No `rederive`, no factory, no callback parameter.
- No `SYNTHETIC_TEST_ONLY`, no `_issue`, no marker object.
- No policy method, no `evaluate()`.

If the implementation finds it "needs" any of these to make a test pass, the scope has been exceeded — stop.

## 5. Expected governance inventory impact

| Item | Value |
|---|---|
| Tracked `.py` before | 1,102 |
| Files added | 2 (models + contract test) |
| Tracked `.py` after | **1,104** |
| I11R2 republish | `UPDATE_I11R2_EVIDENCE=1`, single line 1,102 → 1,104 |
| New collection nodes | equal to the number of contract tests written (count re-measured, **never** inherited; old digest invalid) |
| Full 4,733-node regression | **not run** in Rung 1 (Rung 6) |

## 6. Definition of done (Rung 1)

- [ ] two authorized files exist, nothing else added to `src/`
- [ ] A1.1–A1.5 proven by executed tests
- [ ] all seven negative tests pass
- [ ] governance suite green (I05, I09, I10, I11R2) at 1,104
- [ ] `INTEGRATION_STATE` and manifest byte-identical to base
- [ ] no authority pathway exists: a grep for `AUTHORIZED`-setting code in `src/` returns only the enum definition
