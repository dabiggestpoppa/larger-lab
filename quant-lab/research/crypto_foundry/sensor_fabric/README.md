# CRYPTO MECHANICAL SENSOR FABRIC — PLANNING INDEX

**Status:** architecture/planning only — no provider adapter implementation yet  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent research state:** `agent/crypto-quant-foundry` @ `9243201b4797b4b98cc446d1f13871668907ca79`  
**Purpose:** turn the newly verified free derivatives/mechanical data sources into a provider-independent L0/L1/L2 sensor fabric before MECH-21 and LOWER-FIELD-14 resume.  
**Doctrine:** CEREBUS / Crypto Field Modeling Bible / Market OS free-only stack.  

---

## 1. Mission

Build one canonical crypto derivatives/mechanical sensor fabric that continues to function when any individual exchange has historical gaps, schema changes, endpoint outages, symbol differences, rate limits, or partial field coverage.

The system is organized around **canonical sensors**, not vendors.

```text
PROVIDERS
  Kraken / Gate / Binance / Bybit / OKX / Deribit / Coinalyze / Bitfinex
        ↓
PROVIDER ADAPTERS
        ↓
T0 IMMUTABLE RAW
        ↓
PIT + IDENTITY + SEMANTIC NORMALIZATION
        ↓
T1 CANONICAL MECHANICAL OBSERVATIONS
        ↓
VENUE SENSOR STATES + CROSS-VENUE SYNTHESIS
        ↓
T2 MECHANICAL OBSERVABLE FABRIC
        ↓
HISTORICAL REPLAY / SHADOW LIVE
        ↓
MECH-21 + LOWER-FIELD-14
```

Hard rule:

> No single exchange is canonical truth. The sensor is canonical; providers are evidence sources.

Second hard rule:

> Fallback providers may fill coverage, but provider identity is never erased. Cross-provider disagreement is preserved as information rather than silently averaged away.

---

## 2. Scientific reason for the build

LOWER-FIELD-13 localized the strongest unresolved local question to the transition from absorption/reorganization into propagation/containment. Existing field/rank/liquidity covariates leave a material downside-specific residual. Highest-value missing mechanical families are:

1. liquidations / forced deleveraging
2. order flow / aggressor imbalance
3. open interest / leverage state
4. funding / positioning pressure
5. depth / spread / liquidity withdrawal

MECH-20/21 also benefit because these sensors can condition:

- gain transitions
- sterile saturation
- transfer/realization
- absorptive capacity
- forcing mixtures
- recurrent low-gain episodes
- calendar/seasonal modulation

This infrastructure therefore upgrades the research substrate itself rather than creating a one-off sign-asymmetry dataset.

---

## 3. Planned provider roles

Providers remain candidates until capability probes verify real historical access, units, semantics, and zero-cost status.

| Provider | Planned primary role | Planned secondary role |
|---|---|---|
| Kraken Futures | liquidations, OI, funding, aggressor/CVD, spread/liquidity/slippage | basis, orderbook analytics |
| Gate.io Futures | long/short liquidations, OI, taker flow, funding/positioning | cross-alt breadth |
| Binance public data | historical trades/aggTrades, OI metrics, funding, taker flow | book-depth reconstruction / backbone history |
| Bybit | historical OI, funding, trades | independent leverage/flow replication |
| OKX | historical trades/funding and deeper orderbook modules | historical liquidity-withdrawal research |
| Deribit | liquidation-tagged trade anatomy, funding/trades | BTC/ETH mechanism microscope |
| Coinalyze | free aggregate OI/funding/liquidation corroboration | daily long-history / forward intraday corroboration |
| Bitfinex liquidation archive | independent historical liquidation replication | research validation only |

No provider becomes a required dependency until it passes the free-only and usability gates.

---

## 4. Canonical high-value sensor families

### 4.1 LiquidationState

Preserve long/short separation, notional, counts, intensity vs OI, acceleration, breadth, and cross-venue dispersion.

### 4.2 LeverageState

Preserve OI in native/base/USD units where available, velocity, acceleration, OI×price state, and cross-venue breadth.

### 4.3 FundingState

Preserve native funding interval/rate as truth plus explicitly derived normalized equivalents.

### 4.4 OrderFlowState

Aggressor buy/sell notional, signed flow, taker imbalance, CVD, persistence, breadth, and venue consensus.

### 4.5 LiquidityState

Spread, depth at economically normalized bps bands, book imbalance, slippage, withdrawal, and recovery.

### 4.6 PositioningState / BasisState

Contextual positioning ratios and basis. These never overwrite OI/funding/order-flow primitives.

---

## 5. Universe tiers

### U0 — Mechanism Core

BTC, ETH, and the most liquid core perpetuals.

Store the richest available data:
- trades
- liquidations
- OI
- funding
- books / book metrics
- positioning / basis where available

### U1 — Broad Research Universe

Broad actively traded perpetual universe.

Store:
- trades/agg flow where economically reasonable
- liquidations
- OI
- funding
- coarse book metrics

### U2 — Long Tail

All cheaply supported perpetual instruments.

Store primarily:
- OI
- funding
- liquidation statistics
- coarse activity/positioning

Universe membership must be point-in-time and instrument-lifecycle aware.

---

## 6. Storage doctrine

Actual historical data does **not** live in Git.

Git stores:
- plans
- schemas
- adapters
- manifests
- checksums
- source registries
- coverage reports
- reproducibility commands
- tests

Data storage target:

```text
T0 raw parquet lake
T1 canonical parquet lake
T2 observables parquet lake
DuckDB analytical access
PostgreSQL operational metadata / manifests / state
```

Raw partitions are immutable and restartable.

---

## 7. Full bloc roadmap

The planning sequence is deliberately built one bloc at a time. All blocs are completed as implementation-grade plans before the execution agent receives one master build prompt.

### BLOC 1 — CONTRACTS & SEMANTICS FOUNDATION

Freeze:
- canonical sensor vocabulary
- provider/access registry contract
- equivalence classes
- observation timestamps/provenance
- canonical schemas
- free-only policy
- fail-closed rules
- quality-flag vocabulary
- implementation acceptance gates

**Status:** being completed now.

### BLOC 2 — HISTORICAL CAPABILITY PROBE HARNESS

Plan the executable discovery system that verifies actual provider historical depth against 2021/2022/2024/2026 dates, field availability, pagination, rate limits, symbols, units, auth and gaps.

### BLOC 3 — PROVIDER ADAPTER WAVE A

Kraken + Gate + Binance + Bybit.

### BLOC 4 — PROVIDER ADAPTER WAVE B

OKX + Deribit + Coinalyze + Bitfinex archive.

### BLOC 5 — IMMUTABLE T0 RAW LAKE

Partitioning, manifests, checksums, retry/resume/idempotency and immutable source capture.

### BLOC 6 — PIT IDENTITY & SEMANTIC NORMALIZATION

Instrument identity, listings/delistings, linear/inverse, quote/settlement assets, contract multipliers, time semantics, unit normalization and no-zero-fill rules.

### BLOC 7 — QUALITY, REDUNDANCY & FAILOVER

SensorHealth, provider disagreement, stale/degraded modes, cross-source comparison, source-count confidence and fail-closed continuation.

### BLOC 8 — HISTORICAL BACKFILL PROGRAM

2020-06→present backfill by sensor family with resumable shards and coverage matrices.

### BLOC 9 — LIVE BLACK-BOX RECORDER

Continuous local-first public-feed collector with restart/resume, heartbeat, gap detection and raw archival.

### BLOC 10 — MECHANICAL OBSERVABLE FABRIC

LiquidationState / LeverageState / FundingState / OrderFlowState / LiquidityState / PositioningState / BasisState plus cross-venue breadth/consensus/dispersion.

### BLOC 11 — HISTORICAL REPLAY + MARKET OS BRIDGE

Deterministic `as_of` mechanical snapshot, research event-context bridge, runtime schemas and MECH-21/LF14 handoff.

### BLOC 12 — FULL VALIDATION / RESEARCH RESTART PACKET

Cost gate, PIT gate, historical coverage, provider redundancy, replay determinism, live smoke, schema compatibility and final research handoff.

---

## 8. Global acceptance principles

Every future bloc inherits these:

1. **$0 required subscription cost.**
2. **No payment method/stake/transaction dependency for ingestion.**
3. **PIT-safe timestamps and symbol lifecycle.**
4. **Provider identity preserved.**
5. **No fake cross-venue equivalence.**
6. **No zero-fill for missing observations.**
7. **No silent stale substitution.**
8. **Cross-source disagreement is measured.**
9. **Raw responses archived before transformation.**
10. **Every derived value is traceable to source observations and code version.**
11. **Historical replay must never use data learned after `as_of`.**
12. **Research agents consume canonical sensors, never provider-specific fields.**

---

## 9. Research pause / restart rule

MECH-21 and LOWER-FIELD-14 plans remain valid, but execution should wait until the fabric reaches the replay bridge acceptance gate.

Restart sequence:

```text
Sensor Fabric v1
→ verified history
→ canonical PIT panel
→ mechanical replay
→ quality audit
→ MECH-21
→ LOWER-FIELD-14
```

No strategy, PnL, execution, sizing, leverage or live order placement belongs in this workstream.

---

## 10. Planning completion protocol

Each bloc plan must contain:

- objective
- assumptions
- in-scope / out-of-scope
- exact files/modules to build
- schemas/contracts
- algorithms/control flow
- failure modes
- acceptance tests
- evidence outputs
- staged commit sequence
- stop gate
- handoff dependencies to the next bloc

After BLOC 12 planning is complete, issue one master implementation prompt instructing the execution agent to build strictly from these plans and commit at every planned checkpoint.
