# I16 — PRELIMINARY LINEAGE AND T1 IDENTITY CHECKPOINT

**Checkpoint:** `SENSOR-B5-WAVE1-I16`
**Commit:** `a07a6f4a8`
**Disposition:** PRELIMINARY IMPLEMENTATION DELIVERED. The lineage gate is **NOT CLOSED** and this
record does not close it.

---

## 1. Authorized surface

| Path | Role |
|---|---|
| `src/crypto_sensor_fabric/normalization/lineage/__init__.py` | the I16 identity and lineage package (new) |
| `tests/crypto_sensor_fabric/normalization/test_b5_i16_lineage_identity.py` | focused and adversarial I16 suite (new) |

The package lives beside `sensors/`, not inside it, because the I11 scope audit forbids `hashlib`,
`uuid4` and `datetime.now` anywhere under `sensors/`. Identity derivation needs a digest, so the
digest lives in the one package whose audit admits it. This is a placement decision made to keep an
existing guard intact, recorded here so it does not look accidental.

## 2. What the contract implements

Public surface (`lineage.__all__`): `IDENTITY_SCHEMA_VERSION`, `LINEAGE_GATE_STATE`,
`LINEAGE_GATE_CLOSED`, `REQUIRED_SENSOR_FAMILIES`, `GenerationDescriptor`,
`GenerationImmutableViolation`, `IncompleteLineageError`, `T1IdentityKey`, `assert_generation_immutable`,
`assert_lineage_complete`, `canonical_identity_bytes`, `compute_t1_record_id`,
`generation_fingerprint`, `lineage_completeness`, `missing_sensor_families`.

* **Deterministic, content-addressed identity.** `compute_t1_record_id` produces `t1:` + SHA-256 over
  `canonical_identity_bytes`, which is a canonical (key-sorted, separator-fixed) encoding of a
  `T1IdentityKey`. The id is a function of content only.
* **Independent of wall clock, execution order and machine state.** The package imports no clock, no
  randomness and no environment lookup; the identity bytes contain no timestamp field, no ordering
  index and no host path. Two runs of the same content on different machines and in different orders
  derive the same id — which the suite demonstrates by deriving ids from re-ordered and re-created
  inputs.
* **Generation immutability.** `GenerationDescriptor` + `generation_fingerprint` name a generation;
  `assert_generation_immutable` raises `GenerationImmutableViolation` when a generation's fingerprint
  changes after publication. A generation is therefore append-only in practice, not by convention.
* **Completeness assertions.** `assert_lineage_complete` raises `IncompleteLineageError` when a record
  cannot name its whole T0 chain (a record whose `raw_projection_refs` are empty, for instance);
  `lineage_completeness` wraps that as a verdict for callers that must decide rather than raise.
* **The gate state is data, not prose.** `LINEAGE_GATE_STATE = "NOT_CLOSED"` and
  `LINEAGE_GATE_CLOSED = False`, and `REQUIRED_SENSOR_FAMILIES` is the frozen eight-family tuple:
  `MECHANICAL_TRADE`, `MECHANICAL_LIQUIDATION`, `MECHANICAL_OPEN_INTEREST`, `MECHANICAL_FUNDING`,
  `MECHANICAL_BOOK_SNAPSHOT`, `MECHANICAL_BOOK_METRIC`, `MECHANICAL_POSITIONING`, `MECHANICAL_BASIS`.
  `missing_sensor_families(covered)` reports what is absent from a set of covered families, in frozen
  order, and the gate can only close when it returns empty.

## 3. Why the gate stays open, stated precisely

Wave 1 attests six of the eight family keys (open interest, funding, both book families, positioning,
basis). `missing_sensor_families` over that set still returns
`('MECHANICAL_TRADE', 'MECHANICAL_LIQUIDATION')`.

That return value is **not** a claim that trade and liquidation normalizers are missing — they exist
and are accepted in the ratified base. It is a statement about this checkpoint's own attestation: Wave
1 does not assemble the T0→T1 chain for any family, because I17–I19 own replay binding, custody and
integration, and none of them exists. The gate therefore stays `NOT_CLOSED`, `LINEAGE_GATE_CLOSED`
stays `False`, and this checkpoint does not assert completeness it has not measured.

## 4. Executed verification

`python -m pytest tests/crypto_sensor_fabric/normalization/test_b5_i16_lineage_identity.py -q`

```
19 passed
```

Adversarial coverage includes: identity stability across re-ordered inputs and re-created objects;
identity divergence when any identity-bearing field changes (and only then); canonical encoding
determinism; a mutated generation fingerprint raising `GenerationImmutableViolation`; an incomplete
lineage raising `IncompleteLineageError`; `lineage_completeness` reporting rather than raising for a
partial record; `SCHEMA_VERSION` participation in the digest; and the gate constants asserted to be
the open values, so that a future accidental closure fails a test rather than passing silently.

## 5. Limits carried forward

* Preliminary only. No T0→T1 assembly, no replay binding, no custody contract, no integration path.
* The identity key covers the fields this checkpoint can name from accepted sensor contracts; a later
  contract that adds an identity-bearing field must extend the schema version, which the digest
  already enforces.
