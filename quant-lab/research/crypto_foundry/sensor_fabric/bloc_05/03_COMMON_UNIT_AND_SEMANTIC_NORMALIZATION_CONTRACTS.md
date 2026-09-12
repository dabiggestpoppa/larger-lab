# BLOC 5 — COMMON UNIT & SEMANTIC NORMALIZATION CONTRACTS

**Planning status:** COMPLETE DRAFT FOR FREEZE  
**Implementation status:** NOT STARTED  
**Purpose:** freeze how provider-native values become canonical T1 values while preserving native quantities, units, conversion inputs, methodology versions, and semantic uncertainty.

---

## 1. Central rule

Normalization may add comparability.

It may not destroy source meaning.

For every value that is normalized, T1 must preserve:

```text
native_value
native_unit
normalized_value optional
normalized_unit optional
normalization_methodology_id
normalization_methodology_version
conversion_inputs
quality_flags
```

Hard rule:

> A normalized value without enough lineage to reconstruct how it was produced is invalid T1 evidence.

---

## 2. T1 observation envelope

All canonical sensor records inherit a common envelope.

```text
T1ObservationEnvelope
  t1_record_id
  sensor_family
  provider
  venue
  contract_instance_id
  economic_contract_id
  canonical_asset_id
  source_event_at optional
  interval_start_at optional
  interval_end_at optional
  effective_at optional
  market_available_at optional
  observed_at
  ingested_at
  normalized_at
  source_revision_id
  identity_registry_version
  contract_terms_version
  semantic_registry_version
  normalization_methodology_id
  normalization_methodology_version
  raw_lineage_refs[]
  quality_flags[]
  replay_eligibility
```

Sensor-specific records extend this envelope.

---

## 3. Numeric policy

### 3.1 Preserve provider precision

Do not round provider-native values during ingestion merely for convenience.

### 3.2 Canonical numeric types

Implementation should prefer:

- Arrow/Parquet decimal types for money/notional/contract amounts where feasible;
- integer counts for counts;
- explicit floating-point only where source or derived mathematics requires it;
- nullable values rather than sentinel values.

### 3.3 No fake precision

A value reported to 2 decimals does not become more precise because conversion code outputs 12 decimals.

Track optional:

```text
source_precision
conversion_precision
```

---

## 4. Canonical quantity vocabulary

Minimum units/types:

```text
CONTRACTS
BASE_ASSET
QUOTE_ASSET
SETTLEMENT_ASSET
USD
USDT
USDC
OTHER_QUOTE
PERCENT
RATE_PER_INTERVAL
BPS
PRICE
COUNT
```

Unit identity must include asset where relevant.

`1000 BASE_ASSET` without `BTC`/`ETH` identity is incomplete.

---

## 5. Native vs derived quantity fields

Never force one universal number where providers expose different native quantities.

Example OI record may contain:

```text
oi_native_value
oi_native_unit
oi_contracts optional
oi_base optional
oi_quote optional
oi_usd optional
```

Derived fields can be null when conversion is not defensible.

This is preferable to invented completeness.

---

## 6. Contract multiplier normalization

All derivative quantity conversions must reference the PIT-valid `ContractInstance`.

The terms registry supplies:

```text
contract_multiplier
multiplier_unit
payoff_type
quote_asset
settlement_asset
```

No provider-specific multiplier may be hard-coded inside research notebooks.

Conversion code belongs in the normalization layer and is versioned.

---

## 7. Linear contract framework

For a verified linear contract, base/quote conversions can use the documented contract quantity convention.

Generic conceptual relation:

```text
base_exposure = contracts × base_per_contract
quote_notional = base_exposure × reference_price
```

Exact formulas are provider/contract-term driven.

The implementation may not assume `1 contract = 1 base asset` unless verified.

---

## 8. Inverse contract framework

Inverse contracts require special handling because contract notional and base exposure depend on contract specification and price.

The normalization object must record:

```text
reference_price
reference_price_type
reference_price_time
reference_price_source
```

when a price-dependent conversion is performed.

Allowed reference-price semantics are explicit, e.g.:

```text
PROVIDER_MARK
PROVIDER_INDEX
TRADE_PRICE
MID_PRICE
INTERVAL_CLOSE
```

No silent substitution between them.

If the required price is unavailable PIT-safely:

```text
normalized_value = NULL
quality_flag = UNIT_CONVERSION_BLOCKED
```

---

## 9. Stablecoin/fiat conversion

USDT, USDC, USD, and other stable/fiat quotes are distinct.

Canonical policy:

```text
native quote notional = preserved truth
USD equivalent = optional derived value
```

USD equivalent requires a PIT-safe `ConversionRateObservation`:

```text
from_asset
into_asset
rate
effective_at
market_available_at
source
methodology
quality
```

No permanent `1 USDT = 1 USD` assumption.

This preserves depeg mechanics and prevents normalization from erasing the very liquidity/stress phenomena the research may later study.

---

## 10. Cross-currency conversion hierarchy

Preferred conversion evidence:

1. direct venue/reference market with verified PIT price;
2. high-quality independent market/reference feed already inside canonical data;
3. documented derived cross through USD if both legs are PIT-valid;
4. no conversion.

Do not fetch a future/current exchange rate while normalizing old records.

---

## 11. Semantic equivalence classes

Bloc 1 defined:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
NOT_COMPARABLE
```

Bloc 5 operationalizes them.

Every provider-field mapping contains:

```text
provider_field
canonical_field
semantic_equivalence_class
native_definition
transformation
methodology_id
blocking_assumptions
known_limitations
```

A field marked `CORROBORATION_ONLY` may be stored at T1 but cannot enter a cross-provider canonical metric as if exact.

---

## 12. Provider semantic registry

Planned config:

```text
provider_semantics/
  kraken.yaml
  gate.yaml
  binance.yaml
  bybit.yaml
  okx.yaml
  deribit.yaml
  coinalyze.yaml
  bitfinex_archive.yaml
```

Each mapping records:

- source endpoint/archive;
- provider field name;
- data type;
- native unit;
- economic definition;
- timestamp meaning;
- whether cumulative or interval-local;
- direction/side convention;
- exact normalization formula;
- evidence reference;
- semantic confidence;
- last verified date.

---

## 13. Semantic confidence

Initial values:

```text
VERIFIED_FIRST_PARTY
VERIFIED_SECONDARY
RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS
COMMUNITY_DOCUMENTED
AMBIGUOUS
```

`AMBIGUOUS` blocks use in critical T1 normalized fields.

Community evidence can support corroboration but cannot silently masquerade as first-party semantics.

---

## 14. Null and zero policy

These states are different:

```text
0 = verified economic zero
NULL = value not available / not applicable / cannot be normalized
```

Missing reason remains explicit:

```text
NOT_REPORTED
NOT_SUPPORTED
NOT_YET_LISTED
DELISTED
HISTORY_UNAVAILABLE
PROVIDER_EMPTY
CONVERSION_BLOCKED
SEMANTICS_UNVERIFIED
ACCESS_BLOCKED
SOURCE_GAP
```

A zero liquidation interval can only be emitted if the source semantics support that the provider reported the completed interval and it contained zero liquidations.

No missing payload becomes zero.

---

## 15. Canonical observation status

Each record carries:

```text
normalization_status =
  NORMALIZED
  PARTIALLY_NORMALIZED
  NATIVE_ONLY
  BLOCKED_IDENTITY
  BLOCKED_TIME
  BLOCKED_SEMANTICS
  BLOCKED_CONVERSION
  QUARANTINED
```

A `NATIVE_ONLY` record can remain valuable evidence while being excluded from cross-provider analysis.

---

## 16. Methodology registry

Any non-trivial transform must be registered.

`NormalizationMethodology`:

```text
methodology_id
version
sensor_family
description
formula_or_algorithm
required_inputs
output_units
PIT_requirements
known_limitations
introduced_at
deprecated_at optional
```

Examples:

```text
OI_LINEAR_BASE_V1
OI_INVERSE_USD_V1
FUNDING_8H_SIMPLE_EQUIV_V1
BINANCE_AGGRESSOR_SIDE_V1
LIQ_LONG_SHORT_SEMANTICS_V1
BOOK_LEVEL_BASE_CONVERSION_V1
STABLECOIN_USD_PIT_V1
```

---

## 17. Conversion lineage

Each derived normalized field should expose machine-readable input lineage, e.g.:

```text
conversion_inputs = [
  contract_multiplier_ref,
  price_observation_ref,
  fx_conversion_ref
]
```

This makes it possible to answer:

> Why was Gate OI converted to this USD value on this timestamp?

without reproducing the entire pipeline manually.

---

## 18. Cross-provider comparability gate

Before two normalized fields can be compared, validate:

1. sensor family same;
2. economic definition compatible;
3. interval semantics compatible;
4. units compatible after explicit conversion;
5. venue scope known;
6. identity resolved;
7. no blocking quality flags;
8. equivalence class permits comparison.

This gate belongs in the canonical library so research cannot bypass it casually.

---

## 19. Provider-native aggregate fields

Some providers expose already-derived analytics such as CVD, slippage, liquidity scores, or aggregate liquidation volume.

Policy:

- store them as provider-native T1 observations;
- preserve native methodology if documented;
- classify semantic equivalence;
- do not assume they match our later cross-venue T2 definition;
- reconstruct from lower-level evidence separately when possible.

Example:

```text
KRAKEN_NATIVE_CVD
```

is evidence, not automatically identical to:

```text
FABRIC_CVD_V1
```

which Bloc 9 may later derive.

---

## 20. Scope boundaries

T1 normalization may compute unit conversions required to make a provider observation economically interpretable.

T1 should not compute broad research features such as:

- liquidation acceleration;
- OI velocity;
- CVD slope;
- cross-venue consensus;
- liquidity withdrawal state;
- mechanical breadth;
- capacity state.

Those are T2 / Bloc 9.

---

## 21. Required modules

```text
normalization/
  common/
    envelope.py
    numeric.py
    units.py
    conversion.py
    methodologies.py
    semantic_registry.py
    comparability.py
    missingness.py
```

---

## 22. Invariants

1. native values survive;
2. conversion assumptions are explicit;
3. stablecoin != USD by default;
4. inverse conversion requires PIT-valid contract terms and reference price;
5. null != zero;
6. provider-native derived analytics are not promoted to cross-provider truth automatically;
7. every derived canonical value references a methodology version;
8. semantics can fail closed without discarding raw evidence.

---

## 23. Handoff

The next document freezes the **sensor-family-specific normalization rules** for trades, liquidations, OI, funding, books, positioning, and basis.
