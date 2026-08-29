# CRYPTO MECHANICAL SENSOR FABRIC — PLANNING INDEX v0.2

**Status:** architecture/planning only — implementation deferred until all blocs are frozen  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent research state:** `agent/crypto-quant-foundry` @ `9243201b4797b4b98cc446d1f13871668907ca79`  
**Purpose:** turn verified free derivatives/mechanical sources into a provider-independent L0/L1/L2 sensor fabric before MECH-21 and LOWER-FIELD-14 resume.  
**Doctrine:** CEREBUS / Crypto Field Modeling Bible / Market OS free-only stack.

---

## 1. Mission

Build one canonical crypto derivatives/mechanical sensor fabric that continues to function when an individual exchange has historical gaps, schema changes, endpoint outages, symbol differences, rate limits, partial field coverage, or methodology drift.

```text
PROVIDERS
  Kraken / Gate / Binance / Bybit / OKX / Deribit / Coinalyze / Bitfinex
        ↓
PROVIDER ADAPTERS
        ↓
T0 IMMUTABLE RAW EVIDENCE
        ↓
PIT + IDENTITY + SEMANTIC NORMALIZATION
        ↓
T1 CANONICAL MECHANICAL OBSERVATIONS
        ↓
QUALITY / REDUNDANCY / PROVIDER DISAGREEMENT
        ↓
T2 MECHANICAL OBSERVABLE FABRIC
        ↓
READ-ONLY SENSOR SERVICE
        ↓
HISTORICAL REPLAY / MARKET OS BRIDGE
        ↓
MECH-21 + LOWER-FIELD-14
```

Hard rules:

> No single exchange is canonical truth. The sensor is canonical; providers are evidence sources.

> Fallback providers may fill economic-sensor coverage, but provider/venue identity is never erased.

> Cross-provider disagreement is preserved as information, not averaged away silently.

---

## 2. Scientific reason

LOWER-FIELD-13 localized the strongest unresolved local question to the transition from absorption/reorganization into propagation/containment. Existing field/rank/liquidity covariates leave a downside-specific residual.

Highest-value missing mechanical families:

1. liquidations / forced deleveraging;
2. order flow / aggressor imbalance;
3. open interest / leverage state;
4. funding / positioning pressure;
5. depth / spread / liquidity withdrawal.

MECH-21 also benefits through better conditioning of:

- gain transitions;
- sterile saturation;
- transfer/realization;
- absorptive capacity;
- forcing mixtures;
- recurrent low-gain episodes;
- seasonal modulation.

This is therefore a research-substrate upgrade, not a one-off dataset.

---

## 3. Provider candidate roles

Providers remain candidates until capability probes verify actual free access, historical depth, units, semantics and reproducibility.

| Provider | Primary planned role | Secondary role |
|---|---|---|
| Kraken Futures | liquidations, OI, funding, aggressor/CVD, spread/liquidity/slippage | basis, orderbook analytics |
| Gate Futures | long/short liquidations, OI, taker flow, funding/positioning | cross-alt breadth |
| Binance USD-M | historical trades/aggTrades, OI metrics, funding, taker flow | book-depth reconstruction / backbone history |
| Bybit Linear | historical OI, funding, trades | independent leverage/flow replication |
| OKX Swap | historical trades/funding, deeper orderbooks | liquidity-withdrawal research |
| Deribit | liquidation-tagged trade anatomy, funding/trades | BTC/ETH mechanism microscope |
| Coinalyze | aggregate OI/funding/liquidation corroboration | daily history / forward intraday corroboration |
| Bitfinex community archive | historical liquidation replication | research corroboration only |

No provider becomes required until it passes free-only and usability gates.

---

## 4. Canonical sensor families

T0/T1 initial families:

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

T2 later derives:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
PositioningState
BasisState
```

Derived states are sensors/context, not trade signals.

---

## 5. Universe tiers

### U0 — Mechanism Core

BTC, ETH, highest-liquidity core perpetuals.

Richest available data: trades, liquidations, OI, funding, books/book metrics, positioning/basis.

### U1 — Broad Research Universe

Broad active perp universe.

Liquidations, OI, funding, trades/agg flow where feasible, coarse book metrics.

### U2 — Long Tail

All cheaply supported perpetuals.

Primarily OI, funding, liquidation statistics and coarse activity/positioning.

Universe membership is point-in-time and contract-lifecycle aware.

---

## 6. Storage doctrine

Actual historical data does **not** live in Git.

Git stores plans, schemas, adapters, manifests/checksums summaries, coverage reports, reproducibility commands and tests.

Data target:

```text
T0 exact raw evidence + lossless raw projections
T1 canonical PIT Parquet
T2 observables Parquet
DuckDB local analytical/discovery access
PostgreSQL operational metadata/state
```

Raw evidence is immutable and restartable.

---

## 7. Revised 12-bloc roadmap

### Why roadmap v0.2 changed

The initial planning index split provider adapters into Wave A and Wave B. During Bloc 3 planning, the common adapter protocol, QA, provider books, retry/resume and all eight provider implementations were more coherent as **one adapter architecture bloc**. Splitting the same protocol across two planning blocs would create duplicated contracts and drift.

Therefore Bloc 3 consolidated all provider adapter books. Bloc numbering from Bloc 4 onward is now authoritative under this v0.2 roadmap.

The freed planning slot is used for a dedicated read-only canonical sensor service before historical replay, which strengthens the architecture rather than reducing scope.

### BLOC 1 — CONTRACTS & SEMANTICS FOUNDATION

Freeze canonical sensors, provider/access contracts, evidence classes, equivalence, timestamps/provenance, schemas, free-only policy, missingness and quality vocabulary.

**Status:** `PASS_BLOC_01_PLAN_FROZEN`

### BLOC 2 — HISTORICAL CAPABILITY PROBE HARNESS

Executable discovery architecture for proving provider history/access/units/pagination/granularity across 2021/2022/2024/2026/recent controls.

**Status:** `PASS_BLOC_02_PLAN_FROZEN`

### BLOC 3 — PRODUCTION PROVIDER ADAPTER ARCHITECTURE

Common adapter protocol + provider books for Kraken, Gate, Binance, Bybit, OKX, Deribit, Coinalyze and Bitfinex archive; retry/rate-limit/resume/schema drift/access gates.

**Status:** `PASS_BLOC_03_PLAN_FROZEN`

### BLOC 4 — IMMUTABLE T0 RAW EVIDENCE LAKE

Exact source-byte evidence, content addressing, raw projections, partition manifests, checksums, revisions, atomic writes, durable resume coupling, storage quotas, DuckDB discovery, PostgreSQL metadata, backup/export and raw query boundary.

**Status:** in planning.

### BLOC 5 — PIT IDENTITY & SEMANTIC NORMALIZATION

Instrument identity, listing/delisting lifecycle, linear/inverse contracts, quote/settlement assets, multipliers, timestamp semantics, units, OI/liquidation/funding/aggressor normalization, source revisions, no-zero-fill and T1 lineage.

### BLOC 6 — QUALITY, REDUNDANCY & FAILOVER

SensorHealth, provider disagreement, stale/degraded modes, source-count confidence, cross-source comparison, fail-closed continuation and canonical quality scoring.

### BLOC 7 — HISTORICAL BACKFILL PROGRAM

2020-06→present backfill by sensor/provider/universe tier with resumable shards, storage estimates, coverage matrices, gap audits and review checkpoints.

### BLOC 8 — LIVE BLACK-BOX RECORDER

Continuous local-first public-feed acquisition with restart/resume, heartbeat, gap detection, connection generations and immutable raw archival.

### BLOC 9 — MECHANICAL OBSERVABLE FABRIC

LiquidationState / LeverageState / FundingState / OrderFlowState / LiquidityState / PositioningState / BasisState plus cross-venue breadth, consensus, disagreement and dispersion.

### BLOC 10 — READ-ONLY CANONICAL SENSOR SERVICE

Typed query/service boundary over T1/T2, coverage/provenance APIs, as-of-safe sensor retrieval, bulk research access and provider-independent consumer contracts. No strategy/execution endpoints.

### BLOC 11 — HISTORICAL REPLAY + MARKET OS BRIDGE

Deterministic mechanical `as_of` snapshots, event-context replay, Market OS object bridge and MECH-21/LF14 research adapters.

### BLOC 12 — FULL VALIDATION / RESEARCH RESTART PACKET

Cost gate, PIT gate, storage/integrity, historical coverage, redundancy, replay determinism, live smoke, schema compatibility, research reproducibility and final MECH-21/LF14 handoff.

---

## 8. Global acceptance principles

Every bloc inherits:

1. $0 required data-subscription cost.
2. No payment method/stake/transaction dependency for ingestion.
3. PIT-safe timestamp and contract lifecycle handling.
4. Provider identity preserved.
5. No fake cross-venue equivalence.
6. No zero-fill for missing observations.
7. No silent stale substitution.
8. Cross-source disagreement measured.
9. Exact raw evidence archived before semantic transformation.
10. Every derived value traceable to source evidence and code/methodology version.
11. Historical replay never uses data unavailable under the selected as-of semantics.
12. Research agents consume canonical sensor interfaces, not provider-native fields.
13. High-volume optional data may be paused under disk pressure, but raw evidence is not silently destroyed.
14. Geometry/research conclusions remain separate from ingestion/provider convenience.

---

## 9. Research pause / restart

MECH-21 and LOWER-FIELD-14 plans remain valid but execution waits until the fabric reaches replay/validation acceptance.

```text
Sensor Fabric plans frozen
→ implementation
→ verified history
→ T0 evidence
→ canonical PIT T1
→ mechanical T2
→ sensor service
→ historical replay
→ full quality audit
→ MECH-21
→ LOWER-FIELD-14
```

No strategy, PnL, sizing, leverage, deployment or live order placement belongs in this workstream.

---

## 10. Planning completion protocol

Every bloc plan contains:

- objective;
- assumptions;
- in/out scope;
- exact modules/files;
- schemas/contracts;
- algorithms/control flow;
- failure modes;
- acceptance tests;
- evidence outputs;
- staged commit sequence;
- stop gate;
- handoff dependencies.

After Bloc 12 planning is frozen, one master implementation prompt will instruct the execution agent to build strictly from these plans with staged commits and review gates.