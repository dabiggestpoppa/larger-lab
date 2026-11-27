# I12 — OPEN INTEREST NORMALIZER CHECKPOINT

**Checkpoint:** `SENSOR-B5-WAVE1-I12`
**Commit:** `a07a6f4a8`
**Disposition:** IMPLEMENTED — bounded; the USD-derived fields stay blocked by an unadmitted
methodology, exactly as the frozen contract requires.

---

## 1. Authorized surface

| Path | Role |
|---|---|
| `src/crypto_sensor_fabric/normalization/sensors/oi.py` | the I12 normalizer (new) |
| `src/crypto_sensor_fabric/normalization/sensors/admission.py` | shared semantic-admission ladder (new, wave-wide) |
| `tests/crypto_sensor_fabric/normalization/test_b5_i12_oi_semantics.py` | focused and adversarial I12 suite (new) |

No file outside that set carries I12 logic. The shared helper is wave-wide and is described in
`README.md` §4.

## 2. What the contract implements

Public surface (`oi.__all__`): `OI_CONTRACTS_METHODOLOGY_ID`,
`OI_USD_PASSTHROUGH_METHODOLOGY_ID`, `OpenInterestAggregationScope`, `OpenInterestNativeUnit`,
`OpenInterestObservationInput`, `OpenInterestSnapshotScope`, `T1OpenInterestRecord`,
`normalize_open_interest`.

* **Unit distinctions are structural, not advisory.** `OpenInterestNativeUnit` is
  `CONTRACTS | BASE_ASSET | QUOTE_ASSET | USD | PROVIDER_SPECIFIC | UNKNOWN`; the record carries the
  native unit it was admitted under, so a consumer cannot read a contract count as a coin count.
* **Snapshot scope is declared.** `OpenInterestSnapshotScope` is
  `POINT_SNAPSHOT | INTERVAL_LAST | INTERVAL_AVERAGE | PROVIDER_AGGREGATE | UNKNOWN`. An interval
  aggregate is never relabelled a point snapshot.
* **A measured zero is not a defaulted zero.** A zero keeps its native value only with verified
  coverage; a zero whose coverage is not verified admits no derived amount (04 §4, mirroring the
  opposite rule at 04 §3.5).
* **Aggregation scope is explicit.** `OpenInterestAggregationScope` is
  `SINGLE_VENUE | MULTI_VENUE_AGGREGATE`, and a multi-venue aggregate can never be attributed to one
  venue: the record's venue field is refused for aggregate scope rather than copied from a
  constituent.
* **Admission is registry-derived.** The unit claim resolves through the shared ladder
  (`admit_sensor_field`) against the semantic-authority registry; a caller can assert a unit in the
  payload, and that assertion is exactly what gets refused when the registry does not corroborate it.
* **Contract-denominated quantities need PIT contract terms.** Without a PIT-valid
  `ContractTermsSnapshot` the contracts→base and contracts→quote conversions are typed refusals
  (`blocked_amount`) citing `OI_CONTRACTS_TO_USD_V1`; there is no multiplier constant, no default
  contract size and no implied fallback anywhere in the module.
* **`oi_usd` is always blocked.** `B5_I08_UNITS_V1` is not admitted, so the USD field is emitted as a
  `blocked_amount` carrying that methodology id and the record sets
  `usd_native_passthrough_pending`. A record-level validator makes an *unblocked* `oi_usd` a
  construction error, so the dependency cannot be bypassed by hand-constructing a record.
* **Native-unit observations still work.** The I08 dependency blocks the derived USD field only; a
  valid `CONTRACTS`, `BASE_ASSET` or `QUOTE_ASSET` observation normalizes completely, which is why
  this checkpoint is a delivery rather than a wait.

## 3. Executed verification

`python -m pytest tests/crypto_sensor_fabric/normalization/test_b5_i12_oi_semantics.py -q`

```
25 passed
```

Adversarial coverage in that suite includes: contract-denominated observation with no terms
(refused, not guessed); terms present but not PIT-valid at the observation's availability;
caller-asserted unit contradicting the registry (refused with `CONTRADICTION` /
`NOT_COMPARABLE_MAPPING`); corroboration-only mapping refused with `CORROBORATION_ONLY_MAPPING`
rather than promoted; measured zero with and without verified coverage; multi-venue aggregate
attempting a single-venue attribution; `PROVIDER_SPECIFIC`/`UNKNOWN` units; and an attempt to
hand-build a record with a live `oi_usd` (construction error).

The suite runs against a **synthetic trust root** labelled
`SYNTHETIC_TEST_AUTHORITY_NOT_PROVIDER_DOCUMENTATION`, because the shipping approval manifest is
empty. It therefore proves the admission *mechanism*, not any provider's semantics: with the real
manifest empty every production admission refuses with `UNTRUSTED_AUTHORITY`, which the suite also
asserts.

## 4. Limits carried forward

* `B5_I08_UNITS_V1` remains unadmitted. Nothing in this checkpoint admits it, and no USD open
  interest value can be produced until a separate methodology authorization exists.
* No provider row was admitted and no provider evidence was fabricated to make a test pass.
* `LINEAGE_GATE` is untouched here (see the I16 checkpoint).
