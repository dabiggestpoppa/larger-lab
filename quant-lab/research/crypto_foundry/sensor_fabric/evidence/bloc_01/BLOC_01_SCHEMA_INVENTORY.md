# BLOC 1 — SCHEMA INVENTORY

Evidence package: `quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_01/`
Code SHA at inventory time: `daf9257ac44cbf99e6e88d74e83752f4e1865c48`
JSON-schema snapshots: `quant-lab/config/crypto_sensor_fabric/schema_snapshots/` (14 committed, drift-tested).

---

## 1. Contract layer — `quant-lab/src/crypto_sensor_fabric/contracts/`

| Module | Object | Field families | Notes |
|---|---|---|---|
| `enums.py` | `SensorFamily` | 8 frozen families | MECHANICAL_TRADE / _LIQUIDATION / _OPEN_INTEREST / _FUNDING / _BOOK_SNAPSHOT / _BOOK_METRIC / _POSITIONING / _BASIS |
| `enums.py` | `AccessClass` | free-only taxonomy | FREE_AUTOMATED, FREE_LIMITED_AUTOMATED, FREE_REFERENCE_ONLY, PAID_EXCLUDED, UNVERIFIED |
| `enums.py` | `EvidenceClass` | provenance class | FIRST_PARTY_EXCHANGE, FIRST_PARTY_AGGREGATOR, THIRD_PARTY_AGGREGATOR, COMMUNITY_ARCHIVE, RECONSTRUCTED_INTERNAL |
| `enums.py` | `RetrievalMode` | REST / WS / BULK_FILE / COMMUNITY_ARCHIVE | |
| `enums.py` | `SemanticEquivalence` | EXACT_EQUIVALENT, NORMALIZABLE_COMPARABLE, CORROBORATION_ONLY, NOT_COMPARABLE | |
| `enums.py` | `MarketType`, `ContractType`, `AggressorSide`, `AggregationType` | market / contract / side vocabularies | |
| `enums.py` | `LiquidationSide`, `LiquidationRole`, `LiquidationEventShape` | liquidation vocabulary | TRADE_LEVEL / INTERVAL_AGGREGATE / TOTAL_AGGREGATE |
| `enums.py` | `NativeOIUnit`, `FundingType`, `PositioningMetric` | OI / funding / positioning vocabularies | |
| `enums.py` | `QualityFlag` | 21 canonical additive flags | frozen set; registry changes require Bloc governance |
| `enums.py` | `QualityState` | GOOD / DEGRADED / STALE / PARTIAL / UNVERIFIED / BLOCKED | |
| `enums.py` | `MissingReason` | 11 member vocabulary | no member is a numeric zero |
| `enums.py` | `BookSide`, `ReferenceType`, `BookMetricName`, `ProviderStatus`, `VenueID` | supporting controlled vocabularies | |
| `base.py` | `CanonicalObservationBase` | identity + PIT time + raw traceability + versions + quality | effective/observed/ingested UTC; raw_object_uri + raw_checksum mandatory; unresolved identity requires INSTRUMENT_ID_UNRESOLVED |
| `base.py` | `MissingObservation` | structured missingness object | mandatory MissingReason |
| `base.py` | canonical serialization helpers | canonical_dump / canonical_bytes / canonical_hash | deterministic under same schema version |
| `access.py` | `FreeOnlyPolicy` + F9 gate | cost/access contract | cost==0, no payment/stake/transaction, class in {FREE_AUTOMATED, FREE_LIMITED_AUTOMATED} |
| `quality.py` | `derive_quality_state` / `has_blocking_flag` | conservative flag→state aggregation | STALE_SOURCE never → GOOD; blocking flags dominate → BLOCKED (R03) |
| `identity.py` | `InstrumentIdentity` | economic contract identity | asset ≠ contract; lifecycle fields |

## 2. Schema layer — `quant-lab/src/crypto_sensor_fabric/schemas/`

| Module | Model | Distinct fields beyond base | Key invariant |
|---|---|---|---|
| `provider_envelope.py` | `ProviderEnvelope` | envelope_id, retrieval metadata, raw pointer, access_class | provenance only; never a canonical observation |
| `trade.py` | `MechanicalTrade` | price/quantity native, quote notional, aggressor/maker side, aggregation_type | untrusted side ⇒ UNKNOWN (B1-T10) |
| `liquidation.py` | `MechanicalLiquidation` | event_shape, side, role, native price/qty, USD notionals, long/short aggregates | shapes never merged at T1 (B1-T11) |
| `open_interest.py` | `MechanicalOpenInterest` | oi_native + native_unit, oi_base/quote/usd, prices, normalization_method | native preserved; normalization requires method + versions (B1-T12/13, T61) |
| `funding.py` | `MechanicalFunding` | funding_rate_native, interval, 8h equivalent, annualized, predicted/realized | derived never replaces native (B1-T14) |
| `book.py` | `MechanicalBookSnapshot`, `PriceLevel` | best bid/ask, level arrays, provider_level_count, source_depth_definition, is_full_depth, sequence_id | depth definition mandatory (B1-T15) |
| `book.py` | `MechanicalBookMetric` | metric_name, value, unit, side, distance_bps, methodology_id | methodology mandatory (B1-T16) |
| `positioning.py` | `MechanicalPositioning` | positioning_metric, long/short/ratio, population_definition | population mandatory (B1-T17) |
| `basis.py` | `MechanicalBasis` | basis_native, basis_bps, reference_price/type, tenor | reference type controlled |
| `export.py` | JSON-schema export | snapshot manager | deterministic, drift-tested (B1-T63) |

## 3. Registry layer — `quant-lab/src/crypto_sensor_fabric/registry/` + `quant-lab/config/crypto_sensor_fabric/`

| Module / config | Object | Contents |
|---|---|---|
| `provider_registry.py` + `provider_registry.yaml` | `ProviderRegistry` | 8 candidate providers, evidence class, status, FreeOnlyPolicy access, capability claims (all verified=false), fallback candidates; controlled capability vocabulary covers all 8 sensor families incl. positioning + basis (R02) |
| `sensor_priority.py` + `sensor_priority.yaml` | `SensorPriorityRegistry` | 5 critical sensor states with min_preferred_sources=2 and ordered source lists |
| `semantic_equivalence.py` + `semantic_equivalence.yaml` | `SemanticEquivalenceRegistry` | 6 provisional mappings, all with evidence_reference, versioned |
| `methodology_registry.py` + `methodology_registry.yaml` | `MethodologyRegistry` | 9 versioned methodologies (normalization/reconstruction/classification), all PROVISIONAL |

## 4. Storage partitioning note

Bloc 1 defines contracts only.  Storage partitioning (`sensor_family`,
`provider`, `venue`, `instrument_id_canonical`, `effective_date`) is deferred
to later blocs (02 §20); no T0/T1/T2 data is written in Bloc 1.
