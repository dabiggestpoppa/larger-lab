# CRYPTO MECHANICAL SENSOR FABRIC — PLANNING INDEX v0.3

**Status:** `PASS_SENSOR_FABRIC_12_BLOC_ARCHITECTURE_FROZEN` — all 12 planning blocs complete; implementation not started  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent research state:** `agent/crypto-quant-foundry` @ `9243201b4797b4b98cc446d1f13871668907ca79`  
**Purpose:** build a provider-independent, free-only crypto mechanical sensor fabric before MECH-21 and LOWER-FIELD-14 resume.  
**Doctrine:** CEREBUS / Crypto Field Modeling Bible / Market OS free-only stack.

---

## 1. Mission

Build one canonical crypto derivatives/mechanical sensor fabric that continues to function when an individual exchange has historical gaps, schema changes, endpoint outages, symbol differences, rate limits, partial field coverage or methodology drift.

```text
PROVIDERS
  Kraken / Gate / Binance / Bybit / OKX / Deribit / Coinalyze / Bitfinex
        ↓
CAPABILITY PROOF
        ↓
PROVIDER ADAPTERS
        ↓
T0 IMMUTABLE RAW EVIDENCE
        ↓
PIT + IDENTITY + SEMANTIC NORMALIZATION
        ↓
T1 CANONICAL MECHANICAL OBSERVATIONS
        ↓
QUALITY / REDUNDANCY / DISAGREEMENT
        ↓
HISTORICAL BACKFILL + LIVE RECORDER
        ↓
T2 MECHANICAL OBSERVABLE FABRIC
        ↓
READ-ONLY CANONICAL SENSOR SERVICE
        ↓
HISTORICAL REPLAY / MARKET OS BRIDGE
        ↓
FULL ADVERSARIAL VALIDATION
        ↓
MECH-21 + LOWER-FIELD-14 RESTART PACKETS
```

Hard rules:

> No single exchange is canonical truth. The sensor is canonical; providers are evidence sources.

> Fallback providers may improve economic-sensor coverage, but provider/venue identity is never erased.

> Cross-provider disagreement is preserved as information, not averaged away silently.

> NULL / DATA_BLOCKED are valid scientific outputs.

---

## 2. Scientific reason

LOWER-FIELD-13 localized the strongest unresolved local question to the transition from absorption/reorganization into propagation/containment. Existing field/rank/liquidity covariates leave a downside-specific residual.

Highest-value missing mechanical families:

1. liquidations / forced deleveraging;
2. order flow / aggressor imbalance;
3. open interest / leverage state;
4. funding / positioning pressure;
5. depth / spread / liquidity withdrawal.

MECH-21 also benefits through better conditioning of gain transitions, saturation, transfer/realization, absorptive capacity, forcing mixtures, recurrent low-gain states and seasonal modulation.

This is a research-substrate upgrade, not a signal scanner.

---

## 3. Provider candidate roles

Providers remain candidates until Bloc 2 capability probes verify actual free access, historical depth, units, semantics and reproducibility.

| Provider | Primary planned role | Secondary role |
|---|---|---|
| Kraken Futures | liquidations, OI, funding, aggressor/CVD, spread/liquidity/slippage | basis, orderbook analytics |
| Gate Futures | long/short liquidations, OI, taker flow, funding/positioning | broad-alt mechanical coverage |
| Binance USD-M | historical trades/aggTrades, OI metrics, funding, taker flow | backbone history / secondary books |
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

T2 state families:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
PositioningState
BasisState
```

Cross-venue state families include:

```text
LiquidationBreadth
LeverageCompression
FundingConsensus
FlowConsensus
LiquidityWithdrawalBreadth
VenueDispersion
```

Derived states are measurement/context, not trade signals.

---

## 5. Universe tiers

### U0 — Mechanism Core

BTC, ETH and highest-liquidity core perpetuals. Richest available mechanical history/live capture.

### U1 — Broad Research Universe

Broad active perp universe with liquidations, OI, funding, selective flow/trades and coarse liquidity.

### U2 — Long Tail

Cheap broad OI/funding/liquidation/coarse positioning. Full-depth U2 disabled by default.

Universe membership is point-in-time and contract-lifecycle aware.

---

## 6. Storage doctrine

Actual historical/live data does **not** live in Git.

Git stores plans, schemas, adapters, code, compact manifests/checksums, coverage reports, reproducibility commands and tests.

Data target:

```text
T0A exact source evidence
T0B lossless provider-native projections
T1 canonical PIT observations
T2 mechanical observables
DuckDB local analytical/discovery access
PostgreSQL operational metadata/state
```

Raw evidence is immutable and restartable.

---

## 7. Authoritative 12-bloc roadmap

### BLOC 1 — CONTRACTS & SEMANTICS FOUNDATION

Canonical sensors, provider/access contracts, evidence classes, equivalence, timestamps/provenance, schemas, free-only policy, missingness and quality vocabulary.

**Status:** `PASS_BLOC_01_PLAN_FROZEN`

### BLOC 2 — HISTORICAL CAPABILITY PROBE HARNESS

Executable provider history/access/units/pagination/granularity proof across 2021/2022/2024/2026/recent controls.

**Status:** `PASS_BLOC_02_PLAN_FROZEN`

### BLOC 3 — PRODUCTION PROVIDER ADAPTER ARCHITECTURE

Common adapter protocol + provider books for Kraken, Gate, Binance, Bybit, OKX, Deribit, Coinalyze and Bitfinex archive; retry/rate-limit/resume/schema drift/access gates.

**Status:** `PASS_BLOC_03_PLAN_FROZEN`

### BLOC 4 — IMMUTABLE T0 RAW EVIDENCE LAKE

Exact source-byte evidence, content addressing, raw projections, manifests, checksums, revisions, atomic writes, durable resume, storage quotas, DuckDB discovery, PostgreSQL metadata and backup/export.

**Status:** `PASS_BLOC_04_PLAN_FROZEN`

### BLOC 5 — PIT IDENTITY & SEMANTIC NORMALIZATION

PIT instrument identity/lifecycle, linear/inverse contracts, assets/multipliers, timestamp semantics, OI/liquidation/funding/aggressor/book normalization, revisions, no-zero-fill and T1 lineage.

**Status:** `PASS_BLOC_05_PLAN_FROZEN`

### BLOC 6 — QUALITY, REDUNDANCY & FAILOVER

Provider/feed/sensor health, independence-aware source counting, semantic comparability, disagreement, failover, degraded modes and quality policy.

**Status:** `PASS_BLOC_06_PLAN_FROZEN`

### BLOC 7 — HISTORICAL BACKFILL PROGRAM

Sensor-first 2020-06→present backfill where available, deterministic shards, PIT universe, resumability, budgets, typed ragged coverage, event-window readiness and revision handling.

**Status:** `PASS_BLOC_07_PLAN_FROZEN`

### BLOC 8 — LIVE BLACK-BOX RECORDER

Always-on local-first WebSocket/REST capture, exact T0 archival, event/arrival time, heartbeats, reconnects, sequence repair, disk-pressure behavior and forward-gap registry.

**Status:** `PASS_BLOC_08_PLAN_FROZEN`

### BLOC 9 — MECHANICAL OBSERVABLE FABRIC

Venue-local mechanical states plus quality-gated cross-venue breadth/consensus/dispersion, physical + standardized magnitude, static + rolling windows and immutable T2 generations.

**Status:** `PASS_BLOC_09_PLAN_FROZEN`

### BLOC 10 — READ-ONLY CANONICAL SENSOR SERVICE

Typed local/offline query boundary over T1/T2 with `as_of`, generation, quality, coverage, lineage and failure contracts; zero provider/network calls.

**Status:** `PASS_BLOC_10_PLAN_FROZEN`

### BLOC 11 — HISTORICAL REPLAY + MARKET OS BRIDGE

Deterministic `mechanical_replay(t)`, generation locks, PIT universe, event-context compilation, shadow-live equivalence, NullBoundary and Market OS runtime-object bridge.

**Status:** `PASS_BLOC_11_PLAN_FROZEN`

### BLOC 12 — FULL VALIDATION + RESEARCH RESTART PACKET

Whole-stack free-only/PIT/lineage/adversarial certification, research-readiness matrix, MECH-21/LF14 dry-run packets and final human restart recommendation.

**Status:** `PASS_BLOC_12_PLAN_FROZEN`

---

## 8. Global acceptance principles

Every implementation bloc inherits:

1. $0 required data-subscription cost.
2. No payment method/stake/transaction dependency for ingestion.
3. PIT-safe timestamps and contract lifecycle.
4. Provider identity preserved.
5. No fake cross-venue equivalence.
6. No zero-fill for missing observations.
7. No silent stale substitution.
8. Cross-source disagreement measured.
9. Exact raw evidence archived before transformation.
10. Every derived value traceable to evidence and methodology version.
11. Historical replay never uses information unavailable under selected as-of semantics.
12. Research agents consume canonical sensor interfaces, not provider-native fields.
13. Optional high-volume data may pause under storage pressure; raw evidence is not silently destroyed.
14. Quality may be preserved or downgraded downstream, never silently upgraded.
15. Infrastructure never promotes a research mechanism.
16. No strategy, PnL, leverage, sizing, execution or deployment belongs in this program.

---

## 9. Research pause / restart

MECH-21 and LOWER-FIELD-14 plans remain valid. Execution waits until implementation reaches Bloc 12 certification and the operator authorizes restart.

```text
12-bloc architecture frozen
→ master implementation prompt
→ staged implementation B1→B12
→ final certification
→ human review
→ MECH-21 / LF14 restart
```

Primary research parents:

```text
MECH-21 ← MECH20 @ da4b9cd7302c6dcf8790ae51eed29f21dfb98df1
LF14    ← LF13   @ 9243201b4797b4b98cc446d1f13871668907ca79
```

---

## 10. Planning program complete

Program verdict:

`PASS_SENSOR_FABRIC_12_BLOC_ARCHITECTURE_FROZEN`

Next planning-layer artifact:

`MASTER_IMPLEMENTATION_AGENT_PROMPT`

That prompt must instruct the execution agent to read all 12 bloc books, execute every staged checkpoint in dependency order, preserve granular commit history, stop on blocking gates, avoid reset/force-push, protect work from concurrent agents, maintain free-only/no-trading doctrine and finish with Bloc 12 certification before any research restart.

```text
human_review_required = TRUE
next_checkpoint_authorized = FALSE
```