# 04 — What was built, what it proved, and the withdrawal

Rung 1 was implemented and executed. This document is the record of that work; the code was
removed from the branch afterwards (proof in §7) because it cannot pass the frozen I01 audit
until the third amendment is granted.

## 1. The two authorized files, as written

| File | Git blob sha | Lines | Python inventory |
|---|---|---|---|
| `src/crypto_sensor_fabric/normalization/consumer/models.py` | `f7f2ab98f0e6f3b275dd7beb3020e3e3b6df9c1f` | 350 | +1 |
| `tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py` | `837a7943d1b2e8f3cf93a2927d2f1ce44f6f0659` | 714 | +1 |

No `consumer/__init__.py`, no `policy.py`, no `custody_authority.py`, no `rebinding.py`, no
security suite. Import without `__init__.py` was exercised by the test run itself, not assumed.

## 2. Public surface

```python
__all__ = [
    "CustodyAuthorityBasis", "ConsumerDecision", "ConsumerEvidenceReference",
    "ConsumerRefusalReason", "ConsumerRequest", "ConsumerVerdict",
    "TRUST_SCOPE_ECONOMIC_FIELD_BINDING",
]
```

`ConsumerEvidenceReference` is the supporting type the directive's "immutable evidence-reference
representations" requires: a frozen `(reference, approved_digest)` value. A bare `tuple[str, str]`
cannot reject a malformed digest, and a `dict` field is a mutable caller-owned container whose
order a consumer cannot rely on.

| Model | Fields |
|---|---|
| `ConsumerRequest` | `record: T1TradeRecord \| T1LiquidationRecord`, `artifact_bytes: bytes` (`repr=False`), `required_fields: tuple[...]`, `evidence_references: tuple[ConsumerEvidenceReference, ...]`, `knowledge_cutoff: KnowledgeCutoff \| None`, `replay_evidence: ReplayEvidence \| None`, `claimed_manifest_bytes: bytes \| None` (`repr=False`) |
| `ConsumerVerdict` | `decision`, `trust_scope: Literal["ECONOMIC_FIELD_BINDING"]`, `verified_field_allowlist`, `unverified_dimensions`, `pit_status`, `replay_status`, `custody_status`, `custody_source_authorization_status`, `custody_source_authorized`, `refusal_reason`, `refusal_detail` |

`ConsumerDecision` = {ACCEPT_FIELD_BINDING, REFUSE, INTEGRATION_REQUIRED} — exactly three.
`CustodyAuthorityBasis` = {AUTHORIZED, INTEGRATION_REQUIRED, UNAUTHORIZED} — exactly three,
`SYNTHETIC_TEST_ONLY` absent. `ConsumerRefusalReason` = the 12 design codes, including the ones
only Rungs 2–3 can emit, so a later rung adds behavior without changing the vocabulary.

## 3. Decisions that needed a ruling, and the ruling

| Decision | Ruling | Reason |
|---|---|---|
| Base immutability | `frozen=True` set locally on consumer models | `NormalizationModelBase` is deliberately **not** frozen (storage-style mutable rows). The R0 spec's "frozen" claim was wrong about the base; the models are the stricter case and say so. |
| `trust_scope` type | `Literal["ECONOMIC_FIELD_BINDING"]` | A free string with a default can be forged at construction; a wider scope is now unrepresentable rather than merely refused at inspection. |
| Evidence order | canonical ascending by `(reference, approved_digest)`; **refused**, not sorted | Same precedent as the T1 quality-flag order law: silently sorting rewrites caller data. Duplicates refused. |
| Cutoff rejection | explicit `BeforeValidator` refusing `date`, then `coerce_utc` | Measured: pydantic alone accepts both a bare date and a naive datetime. |
| Verdict consistency | `REFUSE` requires a reason; other decisions forbid refusal metadata; `custody_source_authorized` must equal `basis is AUTHORIZED` | Shape laws, not new authorization semantics. |
| Binary serialization | `ser_json_bytes`/`val_json_bytes` = `base64` | Default UTF-8 byte codec **raises** on non-UTF-8 evidence and does not round-trip; base64 both ways does. |
| `ACCEPT` with empty allowlist; meaning of `EMPTY_UNVERIFIED_DIMENSIONS` | **not** enforced | The design does not settle these; Rung 2 policy owns them. Recorded, not invented. |

## 4. A1.1–A1.5, as executed

All five are asserted by executed tests, not by inspection alone. `32 passed in 4.66s`.

| Req | Test | Result |
|---|---|---|
| A1.1 | recursive walk of resolved annotation types from `ConsumerRequest` (unions and nested consumer models included) — no `RecordVerification`, `TrustedAuthorityContext`, `SemanticAuthority`, `CustodyAuthorityCapability`, verdict/decision/authority type, no `authority`-module type, no `Callable`, no `Any`; no field name in `{authority, authorized, custody_authority, trusted, verdict, decision, callback, …}`; `record` resolves to exactly the two T1 types | PASS |
| A1.2 | `set(ConsumerDecision)` is exactly the three members; `ACCEPT` / `AUTHORIZED` absent | PASS |
| A1.3 | `set(CustodyAuthorityBasis)` is exactly three; `SYNTHETIC_TEST_ONLY` absent | PASS |
| A1.4 | frozen assignment refused; unknown field refused; naive cutoff refused; bare date refused; offset normalized to UTC; base64 round-trip over non-UTF-8 bytes; canonical bytes stable; bytes hidden from `repr` | PASS |
| A1.5 | clean subprocess: `sensors.verification` **not** loaded after importing the model module | PASS |

### Recursion boundary (stated, not hidden)

A1.1's walk stops at `normalization.sensors`. The T1 record is the *authorized payload* and it
legitimately carries its own upstream `authority_provenance` claim; recursing into it would
refuse the record the directive requires. The slot is separately pinned to exactly
`{T1TradeRecord, T1LiquidationRecord}`, so it cannot be widened to an authority or a mapping.

## 5. Negative cases executed

unknown field · naive cutoff · bare date · invalid decision · authority basis smuggled as a
decision · digest format · tuple-typed immutable evidence · duplicate evidence · duplicate
required fields · non-canonical order refused rather than sorted · REFUSE without reason ·
refusal metadata on a non-refusal decision · custody boolean/basis disagreement · widened
trust scope · request carrying a verdict, a decision or an authorization status · a verdict
offering no callable and no `issue`/`authorize`.

## 6. Measured pydantic behaviour (the part the directive warned about)

pydantic **2.13.4**, CPython **3.11**.

| Observation | Measured |
|---|---|
| `date` for a `datetime` field | **accepted**, coerced to midnight — so the module refuses it by name |
| naive `datetime` | accepted by the field type — refused by `coerce_utc` |
| `model_construct(...)` | skips every validator: an object of type `ConsumerVerdict` holding raw strings (`"ACCEPT_FIELD_BINDING"`, `"AUTHORIZED"`) that no law would admit |
| `model_copy(update={"trust_scope": "FULL_RECORD_TRUST"})` | skips validation; the copy holds a value the schema forbids |
| `frozen=True` | prevents attribute assignment on the ordinary path; **does not** prevent either bypass |

Consequence, and the reason a test asserts it: a verdict is a **data representation, not an
authorization capability**. No consumer may infer provenance from the class or from a field
value; the future policy must re-derive the answer from evidence.

### Enclosed-record mutability (limitation, recorded)

`ConsumerRequest` freezes its own bindings but does not deep-copy `record`. The T1 layer is a
repository-convention mutable model, so a caller who mutates the record after construction
changes what the request encloses. Deep-freezing the T1 layer is not D-1's business; this is
recorded as a limitation rather than papered over.

## 7. Import graph

Clean-subprocess measurement after `import …consumer.models`:

| Module | Loaded | Reading |
|---|---|---|
| `…normalization.sensors.verification` | **False** | the required isolation holds |
| `…normalization.authority` | **True** | transitive from the authorized payload: `sensors/trade.py` imports `MappingProvenance` from `..authority`. That module's body executes only regex compilations and string constants — no manifest read, no file, no clock. Type import, not forbidden runtime behaviour. |

The test asserts both facts rather than asserting the convenient one. AST checks additionally
prove the module contains no `os`/`io`/`socket`/`pathlib`/`subprocess`/`hashlib`/`json`/`yaml`
import, and calls none of `verify_trade_record`, `verify_liquidation_record`,
`load_trusted_authority`, `parse_approval_manifest`, `verify_evidence_custody`,
`verify_mapping_provenance`, `assess_replay_eligibility`, `now`, `utcnow`, `sha256`, `open`.

## 8. Collection, re-measured rather than inherited

| Tree | Nodes | Digest (SHA-256 over sorted unique node IDs) |
|---|---|---|
| With the implementation present | **4,765** | `5239abe5c029cf27ac262e9fd5157bf4f1698f437fbe87f1833634d6e575bc1d` |
| Published branch (implementation withdrawn) | **4,733** | `1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` |

The delta is exactly the 32 contract nodes; the published digest equals the canonical anchor
**byte for byte**, which is the proof that withdrawal was clean. The 4,733-node universe was
**not executed** — Rung 6 owns the full regression.

## 9. Withdrawal, and what remains

Removed: the `consumer/` directory and the contract file. Verified afterwards: worktree clean,
tracked Python **1,102**, six audits **122 passed**, universe **4,733** / anchor digest, empty
manifest and `INTEGRATION_REQUIRED` untouched.

Remaining limitation: the implementation exists as a record (hashes, surface, results) rather
than as a commit. Given I01's single named entry plus the prepared I05/I10 predicate, the same
content commits as A2 and the same 32 tests pass; no design work is outstanding.
