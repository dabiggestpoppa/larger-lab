# BLOC 1 — ACCEPTANCE GATES, TESTS & STAGED COMMITS

**Status:** implementation-grade completion contract  
**Depends on:** Bloc 1 contracts + schema/provider registry specs.  

---

## 1. Purpose

Bloc 1 is a contract freeze, not a data-ingestion build.

It succeeds only if later blocs can implement provider probes/adapters without inventing new foundational semantics.

This document defines exactly how the implementation agent proves that.

---

## 2. Planned implementation tree

```text
quant-lab/
  src/
    crypto_sensor_fabric/
      __init__.py
      contracts/
        __init__.py
        enums.py
        base.py
        quality.py
        access.py
        identity.py
      schemas/
        __init__.py
        provider_envelope.py
        trade.py
        liquidation.py
        open_interest.py
        funding.py
        book.py
        positioning.py
        basis.py
      registry/
        __init__.py
        provider_registry.py
        semantic_equivalence.py
        methodology_registry.py
        sensor_priority.py

  config/
    crypto_sensor_fabric/
      provider_registry.yaml
      sensor_priority.yaml
      semantic_equivalence.yaml
      methodology_registry.yaml

  tests/
    crypto_sensor_fabric/
      contracts/
      schemas/
      registry/
      fixtures/

  research/
    crypto_foundry/
      sensor_fabric/
        evidence/
          bloc_01/
```

Exact package root may be adapted to the repository's established import structure after inspection, but module responsibilities must remain separated.

---

## 3. Mandatory contract enums

At minimum implementation must define validated enums for:

```text
SensorFamily
AccessClass
EvidenceClass
RetrievalMode
SemanticEquivalence
MarketType
ContractType
AggressorSide
LiquidationSide
LiquidationRole
LiquidationEventShape
NativeOIUnit
FundingType
PositioningMetric
QualityFlag
QualityState
MissingReason
```

No critical enum is represented by uncontrolled arbitrary strings in canonical schemas.

Provider IDs and methodology IDs may be controlled registry strings because they evolve independently.

---

## 4. Base-schema validation tests

### B1-T01 — required provenance

A canonical observation without:
- provider
- venue
- raw_object_uri
- raw_checksum
- schema_version
- adapter_version

must fail validation.

### B1-T02 — native symbol retention

A record may never validate without `instrument_native`.

### B1-T03 — canonical identity can fail safely

A record with unresolved canonical identity may validate only when:

```text
instrument_id_canonical = NULL
quality_flags includes INSTRUMENT_ID_UNRESOLVED
```

### B1-T04 — time fields

All canonical time fields must be timezone-aware UTC after validation/serialization.

Naive datetime input must either:
- fail, or
- be normalized only through an explicit source-timezone rule.

No silent local-time assumption.

### B1-T05 — raw traceability

Every canonical observation must trace to an immutable raw object pointer/hash.

---

## 5. Sensor-schema tests

### B1-T10 — trade side unknown allowed

Trade records without trusted taker semantics must preserve:

`aggressor_side=UNKNOWN`

rather than guess.

### B1-T11 — liquidation shape separation

Trade-level liquidation and interval aggregate liquidation must serialize with different `event_shape` values and cannot be conflated by schema coercion.

### B1-T12 — OI native preservation

A normalized OI record must retain the original `oi_native` and `native_unit`.

### B1-T13 — OI unsupported normalization

If conversion cannot be proven, normalized fields remain null with `UNIT_NORMALIZATION_UNAVAILABLE`.

### B1-T14 — funding native preservation

`funding_rate_8h_equivalent` cannot exist without `funding_rate_native`.

### B1-T15 — book source-depth semantics

A book snapshot must carry a non-empty `source_depth_definition`.

### B1-T16 — book metrics require methodology

Any reconstructed or provider-calculated metric requires `methodology_id`.

### B1-T17 — positioning population

A positioning ratio cannot validate without `population_definition`.

---

## 6. Free-only policy tests

### B1-T20 — paid source blocked

Any provider config with:

```text
access_class=PAID_EXCLUDED
```

must be rejected from `required_runtime=true`.

### B1-T21 — reference-only blocked

`FREE_REFERENCE_ONLY` cannot be marked required automated ingestion.

### B1-T22 — unverified blocked

`UNVERIFIED` cannot be promoted to a required automated dependency.

### B1-T23 — cost invariant

Required automated provider must satisfy:

```text
cost_usd_required == 0
payment_method_required == false
staking_required == false
transaction_required == false
```

### B1-T24 — auth distinction

A free API key is permitted if no payment/stake/transaction is required; `api_key_required=true` alone does not imply paid.

---

## 7. Provider-registry tests

### B1-T30 — every provider has evidence class

No registry entry without provenance class.

### B1-T31 — capabilities default unverified

Initial provider capability claims may be `claimed=true` but historical verification must remain false until Bloc 2.

### B1-T32 — critical sensor redundancy intent

Each critical sensor family must list at least two fallback candidates where the planning registry currently identifies plausible providers.

This is a planning invariant, not proof they will pass Bloc 2.

### B1-T33 — no silent provider priority override

Provider ordering is explicit config, not hard-coded application logic.

---

## 8. Semantic-equivalence tests

### B1-T40 — equivalence required

Every provider→canonical mapping requires one of:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
NOT_COMPARABLE
```

### B1-T41 — comparable mapping needs method

Any `NORMALIZABLE_COMPARABLE` mapping requires a methodology ID.

### B1-T42 — corroboration cannot be pooled by default

Registry helper must expose that `CORROBORATION_ONLY` is ineligible for automatic pooled numeric synthesis.

### B1-T43 — exact equivalence requires evidence

`EXACT_EQUIVALENT` requires an evidence/reference field. Empty evidence fails registry validation.

---

## 9. Missingness / fail-closed tests

### B1-T50 — no default zero

Missing numeric sensor fields remain null; schema defaults must not fabricate zeros.

### B1-T51 — missing reason

A structured missing observation/status object must carry a `MissingReason`.

### B1-T52 — unsupported is not zero

`NOT_SUPPORTED` cannot be interpreted as numerical zero by helpers.

### B1-T53 — stale is not fresh

`STALE_SOURCE` must not produce `QualityState.GOOD`.

---

## 10. Versioning tests

### B1-T60 — schema version present

Every serialized canonical observation has schema version.

### B1-T61 — methodology version present when normalized

Any non-native normalization carries methodology and normalization versions.

### B1-T62 — deterministic serialization

Same validated object must produce stable canonical serialization/hash under same schema version.

### B1-T63 — JSON Schema snapshot

Pydantic JSON Schema exports are committed or snapshot-tested so breaking drift is visible in Git.

---

## 11. Fixture set required

Bloc 1 fixtures should be synthetic provider-independent examples, not live API fixtures yet.

Minimum fixtures:

```text
trade_valid.json
trade_unknown_side.json
liquidation_trade_level.json
liquidation_interval_aggregate.json
oi_contracts_native.json
oi_usd_native.json
oi_unresolved_units.json
funding_8h_native.json
funding_non8h_native.json
book_snapshot_l2.json
book_metric_provider.json
book_metric_reconstructed.json
positioning_top_trader.json
basis_valid.json
identity_unresolved.json
```

No external network required to run Bloc 1 tests.

---

## 12. Evidence outputs

The execution agent must write a concise evidence package under:

`quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_01/`

Required:

### `BLOC_01_SCHEMA_INVENTORY.md`

List every canonical object, field family and owning module.

### `BLOC_01_PROVIDER_REGISTRY_SNAPSHOT.md`

Human-readable provider candidate matrix. Clearly distinguish claimed vs verified capability.

### `BLOC_01_EQUIVALENCE_MATRIX.md`

Initial known/planned mappings with equivalence status. Unprobed mappings remain provisional.

### `BLOC_01_TEST_EVIDENCE.md`

Command, test count, pass/fail, environment, commit SHA.

### `BLOC_01_DECISION.md`

One of:

```text
PASS_BLOC_01_CONTRACTS_FROZEN
PASS_BLOC_01_WITH_EXPLICIT_GAPS
FAIL_BLOC_01_CONTRACTS_INCOMPLETE
```

---

## 13. Staged implementation commit plan

When the eventual implementation agent builds Bloc 1, it must commit in this order.

### Commit B1-01 — package skeleton + governing contracts

Create:
- package tree
- enums
- base contract
- access/evidence/quality/missing enums

Message pattern:

`SENSOR-B1-01: establish sensor-fabric contract and enum foundation`

Gate:
- imports clean
- enum/unit tests pass

### Commit B1-02 — canonical sensor schemas

Create trade/liquidation/OI/funding/book/positioning/basis models.

Message:

`SENSOR-B1-02: add canonical mechanical observation schemas`

Gate:
- schema fixtures pass
- no default-zero failures
- native preservation tests pass

### Commit B1-03 — provider + priority registries

Create provider registry schema/config and sensor priority config.

Message:

`SENSOR-B1-03: add free-only provider and sensor-priority registries`

Gate:
- paid/reference/unverified required dependency tests fail closed
- all critical sensors have planned redundancy candidates

### Commit B1-04 — equivalence + methodology registries

Message:

`SENSOR-B1-04: add semantic equivalence and methodology contracts`

Gate:
- corroboration-only cannot auto-pool
- comparable mappings require methodology

### Commit B1-05 — schema export + compatibility suite

Message:

`SENSOR-B1-05: freeze JSON schemas and compatibility tests`

Gate:
- deterministic serialization
- schema snapshots
- full Bloc 1 unit suite

### Commit B1-06 — evidence + Bloc 1 decision

Message:

`SENSOR-B1-06: record contract-freeze evidence and Bloc 1 decision`

Gate:
- evidence files complete
- no unresolved foundational semantic required by Bloc 2 probe plan

---

## 14. Review checkpoints

Human/operator review should inspect after:

- B1-02: are canonical schemas conceptually correct?
- B1-04: are provider differences being over-collapsed?
- B1-06: are contracts complete enough to permit probes?

Do not wait until the whole Sensor Fabric implementation is complete to inspect schema mistakes.

---

## 15. Bloc 1 failure conditions

Bloc 1 fails if any of the following are true:

1. Provider-specific field names leak into canonical research-facing interfaces.
2. Native values are destroyed by normalization.
3. Missingness can become zero silently.
4. Provider identity can disappear during fallback.
5. Cross-venue synthesis is allowed in T1.
6. Community aggregate data is indistinguishable from first-party exchange data.
7. Paid/reference-only sources can become required dependencies.
8. Timestamps cannot distinguish effective/observed/ingested time.
9. OI/funding/liquidation units are ambiguous.
10. Semantic comparability is implicit rather than registry-controlled.
11. Schemas lack versioning.
12. Bloc 2 would need to invent a new foundational observation type merely to probe providers.

---

## 16. Stop gate before Bloc 2

Bloc 2 planning/build may rely on Bloc 1 only when the eventual implementation evidence says:

`PASS_BLOC_01_CONTRACTS_FROZEN`

Planning work may continue before code exists, but the eventual execution agent must obey this runtime gate:

```text
BLOC 1 PASS
  ↓
BLOC 2 PROBE HARNESS
```

No provider adapter implementation before the probe harness verifies actual provider behavior.

---

## 17. Bloc 2 handoff requirements

Bloc 1 hands Bloc 2:

- validated provider registry structure
- sensor family enums
- access classes
- provider capability claim fields
- canonical timestamp semantics
- missing reason vocabulary
- evidence/provenance classes
- quality flags
- sensor priority map

Bloc 2 then proves:

```text
CLAIMED CAPABILITY
→ ACTUAL REQUEST
→ VERIFIED HISTORICAL CAPABILITY
```

It must not change Bloc 1 semantics merely because one provider is inconvenient.
