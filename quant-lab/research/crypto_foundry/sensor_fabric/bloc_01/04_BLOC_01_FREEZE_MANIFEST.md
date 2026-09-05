# BLOC 1 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Purpose:** make the Bloc 1 planning decisions explicit so later blocs and the eventual execution agent cannot silently reinterpret them.

---

## 1. Frozen architectural decisions

### F1 — Sensor-first architecture

Canonical system objects are sensor families, not provider APIs.

Providers are evidence sources beneath canonical contracts.

### F2 — Three data tiers are mandatory

```text
T0 RAW PROVIDER EVIDENCE
T1 CANONICAL PIT OBSERVATIONS
T2 DERIVED MECHANICAL OBSERVABLES
```

Provider adapters may not jump directly to T2.

### F3 — Provider identity is permanent provenance

Fallback does not erase provider/venue identity.

### F4 — Cross-venue synthesis begins only at T2

No composite cross-venue liquidation/OI/order-flow values in T1.

### F5 — Native values survive normalization

Normalized OI/funding/notional fields are additional fields, never destructive replacements.

### F6 — Missingness is explicit

No implicit zero-fill.
No silent forward-fill.
No unsupported=0 semantics.

### F7 — Point-in-time timestamps are separate

Every canonical observation distinguishes, where semantically applicable:

```text
effective_at
observed_at
ingested_at
```

### F8 — Economic contract identity survives asset normalization

A canonical BTC identity does not erase venue/contract/inverse-vs-linear distinctions.

### F9 — Free-only runtime dependency gate

Required automated sources must satisfy:

```text
cost_usd_required = 0
payment_method_required = false
staking_required = false
transaction_required = false
access_class ∈ {FREE_AUTOMATED, FREE_LIMITED_AUTOMATED}
```

### F10 — Evidence class is separate from access class

A free community archive is not first-party exchange truth.

### F11 — Semantic equivalence is explicit

All provider→canonical mappings carry:

```text
EXACT_EQUIVALENT
NORMALIZABLE_COMPARABLE
CORROBORATION_ONLY
NOT_COMPARABLE
```

### F12 — Methodology is versioned

Any non-trivial conversion/reconstruction has a methodology ID/version.

### F13 — Research consumes canonical interfaces

MECH/LF research code may not couple directly to Gate/Binance/Kraken native field names.

---

## 2. Frozen initial canonical sensor families

```text
MECHANICAL_TRADE
MECHANICAL_LIQUIDATION
MECHANICAL_OPEN_INTEREST
MECHANICAL_FUNDING
MECHANICAL_BOOK_SNAPSHOT
MECHANICAL_BOOK_METRIC
MECHANICAL_POSITIONING
MECHANICAL_BASIS
```

A later sensor family requires explicit architecture amendment if it cannot be represented by these contracts.

---

## 3. Frozen initial critical research sensor states

T2 later derives, at minimum:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
PositioningState
BasisState
```

These names do not dictate feature formulas yet. Bloc 10 handles derived semantics.

---

## 4. Frozen provider candidate set for first fabric build

```text
KRAKEN_FUTURES
GATE_FUTURES
BINANCE_USDM
BYBIT_LINEAR
OKX_SWAP
DERIBIT
COINALYZE
BITFINEX_COMMUNITY_ARCHIVE
```

This is a candidate set, not a guarantee of successful ingestion.

Bloc 2 must verify actual behavior.

A provider that fails free-only/history/usability gates may be demoted or excluded without redesigning the sensor fabric.

---

## 5. Frozen source-role principle

No provider is expected to cover everything.

The target redundancy is complementary:

```text
LIQUIDATIONS
  Kraken / Gate
  + Deribit microscope
  + Coinalyze/Bitfinex corroboration

OPEN INTEREST
  Bybit / Gate / Kraken
  + Binance / Coinalyze

FUNDING
  Bybit / Kraken / Gate
  + Binance / OKX / Deribit / Coinalyze

ORDER FLOW
  Binance / Kraken
  + Gate / Bybit / OKX

DEPTH / LIQUIDITY
  OKX / Kraken
  + Binance secondary reconstruction
```

If one source lacks a sensor or historical interval, another source may cover the economic sensor **without pretending it observed the missing venue**.

---

## 6. Frozen implementation constraints

Bloc 1 implementation later must be:

- Python 3.12+
- typed
- Pydantic v2 compatible
- Arrow/Parquet friendly
- offline-testable
- no network dependency in unit tests
- deterministic serialization where required
- provider registry config-driven
- strict fail-closed free-only validation

---

## 7. Frozen planning staged commits

Planning history for this bloc:

```text
SENSOR-PLAN-00
  saved master sensor-fabric roadmap

SENSOR-PLAN-B1A
  contracts + semantics

SENSOR-PLAN-B1B
  schemas + provider/equivalence registries

SENSOR-PLAN-B1C
  acceptance tests + implementation commits

SENSOR-PLAN-B1D
  freeze manifest
```

Future execution commits are separately defined in `03_ACCEPTANCE_GATES_TESTS_AND_COMMITS.md`.

---

## 8. Bloc 1 completion checklist

Planning questions answered:

- [x] What is a provider observation?
- [x] What is canonical vs derived?
- [x] Which sensor families exist initially?
- [x] How are provider and venue identity preserved?
- [x] How are instruments represented?
- [x] How are effective/observed/ingested timestamps distinguished?
- [x] How are access/free-only conditions represented?
- [x] How are evidence classes represented?
- [x] How is semantic equivalence controlled?
- [x] How are native values preserved?
- [x] How is missingness represented?
- [x] How are quality states represented?
- [x] How is versioning represented?
- [x] What schemas must exist?
- [x] What tests must pass?
- [x] What staged implementation commits are required?
- [x] What is the stop gate before Bloc 2 implementation?

Bloc 1 planning is therefore frozen unless a later bloc exposes a genuine contradiction.

---

## 9. Inputs to Bloc 2 planning

Bloc 2 must design the historical capability probe around these questions for every provider/sensor pair:

1. Does the endpoint/feed/file actually work at $0?
2. Is auth required?
3. What historical date range is actually returned?
4. Can it query/contain 2021?
5. 2022?
6. 2024?
7. 2026?
8. What granularity exists?
9. What symbols/instrument families exist?
10. What quantity/price units are returned?
11. What is the timestamp meaning?
12. What pagination/limit behavior exists?
13. What gaps appear?
14. What rate limit applies?
15. What raw payload shape maps to Bloc 1 contracts?
16. What semantic-equivalence class is defensible?
17. What missing reason is emitted when unavailable?
18. What evidence should be stored to prove the result?

Bloc 2 is verification only. It must not yet build the complete production provider adapters.

---

## 10. Final planning decision

`PASS_BLOC_01_PLAN_FROZEN`

Rationale:

The sensor fabric now has a complete provider-independent observation contract, schema plan, provider/evidence registry structure, semantic-equivalence rules, free-only gate, quality/missingness rules, staged implementation test plan and explicit handoff to capability probing.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 2`
