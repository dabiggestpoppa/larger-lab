# I15 — POSITIONING AND BASIS NORMALIZER CHECKPOINT

**Checkpoint:** `SENSOR-B5-WAVE1-I15`
**Commit:** `a07a6f4a8`
**Disposition:** IMPLEMENTED — both families, bounded; unrelated populations are structurally
non-interchangeable and every unusable basis reference is a typed refusal.

---

## 1. Authorized surface

| Path | Role |
|---|---|
| `src/crypto_sensor_fabric/normalization/sensors/positioning.py` | the I15a normalizer (new) |
| `src/crypto_sensor_fabric/normalization/sensors/basis.py` | the I15b normalizer (new) |
| `src/crypto_sensor_fabric/normalization/sensors/admission.py` | shared admission ladder (new, wave-wide) |
| `tests/crypto_sensor_fabric/normalization/test_b5_i15_positioning_basis_semantics.py` | focused and adversarial I15 suite (new) |

## 2. Positioning

Public surface (`positioning.__all__`): `PositioningMetricType`, `PositioningObservationInput`,
`T1PositioningRecord`, `normalize_positioning`.

* **Population semantics are required, not inferred.** `population_scope` is required and non-blank.
  Two positioning records are comparable only when they declare the same population, which is what
  makes "unrelated long/short populations" structurally non-interchangeable: a record that does not
  declare its population cannot produce a comparable record at all.
* **Five metric types are five measurements, not one.** `PositioningMetricType` is
  `ACCOUNT_LONG_SHORT_RATIO | TOP_TRADER_ACCOUNT_RATIO | TOP_TRADER_POSITION_RATIO |
  TAKER_BUY_SELL_RATIO | PROVIDER_DEFINED_RATIO`. An account ratio is not a position ratio: they count
  different populations in different units, and the module never converts one into the other.
* `PROVIDER_DEFINED_RATIO` is representable but carries no implied semantics; it is a declared
  provider-specific measurement, usable only by a consumer that knows the provider.

## 3. Basis

Public surface (`basis.__all__`): `BasisReferenceRefusal`, `BasisUnit`, `BasisObservationInput`,
`T1BasisRecord`, `normalize_basis`.

The frozen contract requires reference instrument identity, an approved reference-price type,
compatible units, a PIT-valid reference price and complete lineage. Each is enforced, and each
failure has its own code — a generic refusal would not tell an operator which dependency to repair:

| `BasisReferenceRefusal` | Meaning |
|---|---|
| `NOT_SUPPLIED` | no reference price accompanied the observation |
| `TYPE_NOT_APPROVED` | supplied, but its type is not an approved reference type |
| `NO_REFERENCE_AVAILABILITY` | supplied with no availability instant, so PIT validity is unprovable |
| `LATE_REFERENCE` | the reference became available after the observation's knowledge cutoff |
| `UNIT_MISMATCH` | the reference's unit is incompatible with the observation's |

* **Approved reference types are exactly `PROVIDER_INDEX` and `PROVIDER_MARK`.** A trade print, a
  settlement value or a provider-defined number is `TYPE_NOT_APPROVED`; substituting one for an index
  is the exact failure this checkpoint exists to prevent.
* **Late or substituted references are refused, never fallback-filled.** There is no "use the next
  available price" path in the module.
* **No cross-venue synthesis at T1.** The record names one reference instrument; combining venues is
  a downstream analytical act with its own methodology.
* **No derived basis bps.** No registry methodology exists for a computed basis, so the record carries
  `basis_comparable` — a comparability verdict, not a number — and the two instrument identities plus
  the reference identity. Emitting basis points here would be an invented methodology wearing a
  field name.

## 4. Executed verification

`python -m pytest tests/crypto_sensor_fabric/normalization/test_b5_i15_positioning_basis_semantics.py -q`

```
20 passed
```

Adversarial coverage includes: a positioning record with a blank or missing population (refused);
two records with different populations compared (non-comparable, not merged); an account ratio read
as a position ratio (refused); each of the five `BasisReferenceRefusal` members produced by its own
case; a reference available exactly at the cutoff versus one instant after it; a unit-mismatched
reference; a `TYPE_NOT_APPROVED` substitution attempt; and an attempt to obtain basis points rather
than a comparability verdict.

## 5. Limits carried forward

* `basis_comparable` is a verdict, not an arithmetic result. No basis bps, no annualized basis and no
  implied carry is produced anywhere in Wave 1.
* As in the other checkpoints, the suites run against a synthetic trust root
  (`SYNTHETIC_TEST_AUTHORITY_NOT_PROVIDER_DOCUMENTATION`) and separately assert that the shipping
  empty manifest refuses with `UNTRUSTED_AUTHORITY`.
