# CRYPTO MARKET OS — BUILD BLUEPRINT v0.1

**Status:** Architecture planning only — research-first, local-first, no production deployment yet  
**Branch:** `agent/crypto-quant-foundry`  
**Purpose:** Preserve the intended build path from research terrain into a market-reading operating system.  
**Governing doctrine:** CEREBUS / Crypto Field Research Constitution / Crypto Field Modeling Bible.

---

## 1. Mission

The target is **not** a signal scanner. It is a market operating system that continuously reconstructs market state, local structure, constraints, lifecycle, perturbations, health, opportunity classes, risk, and later execution options.

The OS must answer, before any strategy logic:

1. What field are we in?
2. How mature is the current state?
3. Which constraints are tightening or opening?
4. Which rank/sector/chain/local patches are active?
5. What kind of perturbation occurred, and how material was it?
6. Is the move isolated, peer-carried, reorganizing, contagious, decoupled, or rehabilitating?
7. Which branches remain plausible and which have been invalidated?
8. How much of the field can activate spatially?
9. How constrained is future resolution temporally?
10. Which opportunity families are compatible with the current terrain?
11. Which strategy/execution modules are explicitly blocked?
12. What should the operator or agent watch next?

**Core rule:** understand the field first; downstream action is a routing problem.

---

## 2. Canonical System Layers

```text
L0  DATA / SENSOR FABRIC
    ↓
L1  NORMALIZATION + PIT TRUTH
    ↓
L2  FEATURE / OBSERVABLE FABRIC
    ↓
L3  GLOBAL FIELD MODEL
    ↓
L4  LOCAL PATCH + RELATIONAL MODEL
    ↓
L5  LIFECYCLE / CLOCK / ENTROPY MODEL
    ↓
L6  SHOCK + MATERIALITY MODEL
    ↓
L7  DIRECTIONAL GEOMETRY
    ↓
L8  OPPORTUNITY / ALPHA ROUTER
    ↓
L9  STRATEGY MODULES
    ↓
L10 PORTFOLIO + RISK ROUTER
    ↓
L11 EXECUTION / VENUE / DEFI ROUTER
    ↓
L12 AGENT OPERATOR + JOURNAL + LEARNING
```

No lower layer may silently override a higher-layer terrain constraint.

---

## 3. Layer Responsibilities

### L0 — Data / Sensor Fabric

Market data:
- OHLCV / trades / order book where available
- market cap / rank / supply
- BTC / ETH / market aggregates
- volatility
- funding / OI / liquidations
- stablecoin supply / flows
- TVL / DEX activity / bridge activity
- chain and protocol state
- protocol yields / borrow rates / utilization
- gas / fees / congestion
- venue liquidity / spreads / depth
- macro / cross-asset inputs later

DeFi extension, later:
- lending markets
- AMM pools
- LP yields
- staking / restaking
- incentives / emissions
- oracle state
- liquidation thresholds
- flash-loan liquidity / fees
- bridge conditions
- protocol solvency / utilization
- smart-contract / protocol risk metadata

Every source needs:
`source_id, observed_at, effective_at, ingested_at, revision_id, quality_flags`.

### L1 — Normalization + PIT Truth

Responsibilities:
- canonical timestamps
- asset / chain / protocol identity resolution
- corporate/token actions where relevant
- missingness
- no zero-fill across absence
- causal rolling windows
- survivorship / delisting handling
- rank-band reconstruction
- provenance
- data quality scoring

This is fail-closed infrastructure.

### L2 — Observable Fabric

Reusable observable families:
- breadth
- dispersion
- concentration
- rank velocity / depth
- absolute and sigma-normalized movement
- volatility / volatility state
- tail density
- peer residuals
- peer turnover / relational entropy
- stablecoin / TVL / chain sensors
- liquidity / activity / venue state
- protocol-level DeFi observables later

Features are sensors, not conclusions.

### L3 — Global Field Model

Initial crypto objects:
- HH / HL / LH / LL breadth×dispersion state
- state age
- global forcing intensity
- field entropy / branch entropy
- broad-up / broad-down / mixed directional geometry
- concentration / deconcentration context
- global participation depth

This layer emits a `FieldSnapshot`.

### L4 — Local Patch + Relational Model

Objects:
- rank patches
- sector / chain / age / liquidity patches where earned
- dynamic peer neighborhoods
- relational state rather than permanent peer identity
- true/false loner
- rejoin / contagion / decoupling / rehabilitation
- peer turnover / membership entropy
- local field health

This layer emits `PatchSnapshot` and `RelationalSnapshot` objects.

### L5 — Lifecycle / Clock / Entropy Model

Objects:
- state birth / initiation geometry
- lifecycle stage
- stay / exit / reentry / propagation clocks
- failure clocks
- rank recruitment clocks
- entropy collapse
- metastable / transit-corridor descriptors where earned
- spatial activation vs temporal resolution constraint matrix

Outputs describe **available branches**, not a trade.

### L6 — Shock + Materiality Model

Always preserve separate coordinates:
- sigma-normalized surprise
- absolute displacement
- peer-relative displacement
- rank / liquidity / volatility context

Candidate labels:
- statistical-only shock
- physical shock
- compound shock
- trivial high-sigma move
- local contagion event
- genuine dislocation

No `2σ = important` shortcut.

### L7 — Directional Geometry

Direction enters only after terrain context.

Objects:
- isolated up/down
- coordinated up/down
- broad vs narrow upside
- broad vs narrow downside
- sign asymmetry
- directional information gain given state / age / entropy / patch / materiality / peers

This layer answers:
`Which directional resolutions remain compatible with current constraints?`

It does not directly issue orders.

### L8 — Opportunity / Alpha Router

First true translation layer.

Input: complete field context.

Output:
- eligible opportunity families
- blocked opportunity families
- horizon
- confidence / evidence strength
- required confirmation
- risk flags
- source research nodes

Opportunity families eventually include:
- directional continuation / reversal
- relative value
- dispersion / convergence
- regime transition
- volatility
- carry
- cross-chain / cross-venue dislocation
- DeFi yield / lending / LP opportunities
- liquidation / collateral stress
- flash-loan / atomic-arbitrage opportunities
- hedging / capital parking

An opportunity is not automatically executable.

### L9 — Strategy Modules

Thin modules operating only when authorized by L8.

Contain:
- entry logic
- invalidation
- exit / target logic
- horizon
- transaction-cost model
- capacity
- backtest evidence

Strategies must not reimplement the market ontology.

### L10 — Portfolio + Risk Router

Cross-opportunity responsibilities:
- exposure aggregation
- correlation / common-field concentration
- factor and patch concentration
- drawdown controls
- liquidity / capacity
- leverage
- scenario / stress
- capital allocation
- hedge selection

### L11 — Execution / Venue / DeFi Router

Traditional / exchange execution:
- NautilusTrader adapter path
- broker / exchange adapters
- MT5 bridge where needed
- paper / simulation / live modes

DeFi path later:
- protocol adapters
- RPC / node providers
- transaction simulation
- allowance / approval policy
- smart-contract interaction policy
- gas / slippage / MEV awareness
- flash-loan simulation and atomic-route validation
- wallet / key isolation

All DeFi execution should be sandbox/simulation-first and separate from the research core.

### L12 — Agent Operator

Agent responsibilities eventually:
- read current Market OS state
- explain state in plain language
- identify changed constraints
- surface opportunities
- route research questions
- run approved backtests
- compare opportunity families
- manage paper/live modules if explicitly authorized
- monitor failures / invalidations
- journal decisions and outcomes
- maintain provenance links back to research nodes

The agent must be ontology-adjacent, not free-form signal hunting.

---

## 4. Canonical Runtime Objects

Design the whole OS around stable schemas rather than notebook outputs.

Minimum objects:

```text
FieldSnapshot
PatchSnapshot
RelationalSnapshot
LifecycleSnapshot
ConstraintSnapshot
ShockSnapshot
DirectionalSnapshot
OpportunityCandidate
RiskState
ExecutionCandidate
ResearchEvidence
NullBoundary
```

Every object should contain:
- `as_of`
- `universe`
- `inputs`
- `state`
- `confidence`
- `quality_flags`
- `evidence_refs`
- `valid_region`
- `invalid_region`
- `status` = PROMOTED / LOCAL / DESCRIPTIVE / PARKED / NULL / DATA_BLOCKED

The scanner UI and agent should consume these objects, not raw research CSVs directly.

---

## 5. Proposed Technology Stack

### Primary language

**Python 3.12+**

Use Python for research, data services, feature computation, model services, orchestration interfaces, and adapters unless a performance bottleneck is demonstrated.

### Research / numerical

- Polars — primary columnar feature work / large PIT panels
- NumPy / SciPy — numerical/statistical primitives
- pandas — interoperability only where needed
- statsmodels / scikit-learn — classical models / validation
- PyArrow / Parquet — canonical analytical storage interchange
- optional PyTorch later for earned learned models

Do not start with deep learning.

### Analytical storage

**Parquet + object/file storage** for raw/research datasets.

**DuckDB** for local analytical queries, research joins, rapid reproducibility.

DuckDB is not the live system of record.

### Operational state database

**PostgreSQL** as canonical operational metadata/state/provenance store.

Store:
- current and historical snapshots
- evidence registry
- research-node registry
- opportunities
- agent decisions
- strategy registrations
- portfolio/risk state
- protocol/venue metadata

Use TimescaleDB only if time-series operational workloads prove the need; do not require it at v0.

### Cache / coordination

**Redis** for:
- hot current snapshots
- distributed locks
- rate limits
- short-lived queues/caches
- event fan-out where simple

Do not use Redis as durable truth.

### Event / message architecture

Start simple:
- typed internal events
- PostgreSQL outbox + Redis streams / lightweight queue if needed

Only introduce Kafka/Redpanda when throughput, replay, and service independence objectively require it.

### API / service layer

**FastAPI + Pydantic v2**

Expose typed internal APIs:
- `/field`
- `/patches`
- `/relational`
- `/lifecycle`
- `/shocks`
- `/directional`
- `/opportunities`
- `/risk`
- `/evidence`

Pydantic schemas should mirror canonical runtime objects.

### Orchestration

Near term:
- existing OCE / Forge orchestration remains top-level agent/workflow control
- simple Python jobs / cron for deterministic refresh jobs

Later, if workflow complexity warrants:
- Prefect or Dagster for data/model pipelines

Do not add both.

### Backtesting / execution

Reuse repository investment in **NautilusTrader** for event-driven backtests, simulation, and execution adapters. Existing Quant Lab already targets Nautilus strategy and backtest paths, so the Market OS should feed context into Nautilus rather than replace it. The repository currently identifies `projects/trading/nautilus/` as the strategy/backtest path. 

### External research / fundamentals

Use existing OpenBB integration path as an external data/research surface, not as the ontology itself.

### DeFi / on-chain later

Python:
- web3.py
- eth-abi / eth-account
- protocol-specific SDKs only behind adapters

Infrastructure:
- read-only RPC providers first
- archival node / indexed provider where needed
- local fork simulation (Anvil or equivalent)
- transaction simulation before signing

Possible indexing layer later:
- self-hosted lightweight indexers or provider APIs initially
- dedicated chain warehouse only when sensor coverage requires it

### UI / command center

Phase 1:
- API + CLI + generated state reports

Phase 2:
- lightweight web dashboard
- React / Next.js if a full UI is warranted

UI should visualize the ontology:
- current field
- lifecycle
- entropy
- patch activation map
- peer/relational state
- shock map
- directional geometry
- opportunity routing
- evidence / confidence

Avoid building a candlestick dashboard clone.

### Observability

Start:
- structured JSON logs
- OpenTelemetry-compatible tracing IDs
- Prometheus metrics if services become persistent
- Grafana only once useful

Every state output should carry provenance and computation version.

### Packaging / environment

- `uv` for Python dependency/environment management
- Docker Compose for local multi-service environment
- local-first development
- cloud only for deployment / continuous services / heavy workloads

### CI / quality

- pytest
- Ruff
- mypy or pyright
- schema compatibility tests
- PIT/leakage tests
- deterministic fixture tests
- research claim/evidence checks
- Docker smoke tests

---

## 6. Data Tiers

```text
T0 RAW
    immutable source observations

T1 CANONICAL
    cleaned PIT-safe normalized observations

T2 OBSERVABLES
    breadth, dispersion, rank, peers, vol, chain sensors...

T3 STATE
    field / patch / relational / lifecycle / shock snapshots

T4 OPPORTUNITY
    contextual opportunity candidates

T5 EXECUTION
    strategy / portfolio / venue decisions

T6 JOURNAL
    what was known, chosen, executed, invalidated, learned
```

Never let T4/T5 feed back into T0-T3 definitions during research without explicit versioned research review.

---

## 7. Research-to-Production Promotion Pipeline

A research finding should move through:

```text
RESEARCH ARTIFACT
→ SEMANTIC DEFINITION
→ CANONICAL NODE REGISTRY
→ REPRODUCIBLE FEATURE
→ OFFLINE SNAPSHOT COMPUTATION
→ HISTORICAL REPLAY
→ SHADOW LIVE COMPUTATION
→ STABILITY / DATA QUALITY AUDIT
→ OS RUNTIME NODE
→ OPPORTUNITY ROUTER ELIGIBILITY
```

A strategy cannot be the promotion mechanism for a research node.

---

## 8. Build Phases

### PHASE A — Finish Field Model v1

Before heavy OS code:
- lifecycle / entropy
- initiation/failure geometry
- rank threshold hierarchy
- perturbation response curves
- directional asymmetry
- dynamic relational state
- absolute×sigma materiality
- health / decay bridge
- canonical node map

Deliverable:
`CRYPTO_FIELD_MODEL_v1.md` + machine-readable node registry.

### PHASE B — Freeze Canonical Schemas

Define Pydantic/JSON schemas for all runtime objects.

No UI yet.
No strategy yet.

### PHASE C — Historical State Compiler

Build deterministic pipeline that converts historical PIT data into dated OS snapshots.

Goal:
`date/time -> complete Market OS state`.

This becomes the substrate for alpha translation.

### PHASE D — Market OS Replay Engine

Replay historical time and expose exactly what the OS would have known then.

Agent can ask:
- what was state at t?
- what branches were valid?
- what changed over next checkpoint?

This is more important than a dashboard.

### PHASE E — Live Shadow Scanner

Run the same compiler live without generating trades.

Compare:
- data quality
- state stability
- research distribution drift
- missing sensors
- latency

### PHASE F — Opportunity Ontology

Create non-execution opportunity families and router.

Example:
`MATURE_HH_PROPAGATION_CONTEXT`
`TRUE_LONER_REJOIN_CONTEXT`
`BROAD_UPSIDE_ACTIVATION`
`DEEP_THRESHOLD_ACTIVATION`

Still no order placement.

### PHASE G — Alpha Translation Lab

For each opportunity family:
- candidate action families
- horizon
- expectancy
- costs
- capacity
- falsification

Strategies become plugins consuming OpportunityCandidate objects.

### PHASE H — Portfolio / Risk OS

Capital routing, common-factor risk, correlation, drawdown, capacity, exposure, hedging.

### PHASE I — DeFi Opportunity Intelligence

Research and map:
- lending / borrowing
- yield farming
- LP / concentrated liquidity
- staking / restaking
- stablecoin basis / carry
- liquidation / collateral states
- cross-venue / cross-chain dislocations
- flash-loan route feasibility
- protocol / smart-contract risk

Output is `DeFiOpportunityCandidate`, not immediate execution.

### PHASE J — Execution Fabric

Paper / simulation first.

Then venue-specific execution adapters with strict human authorization.

### PHASE K — Agent Operator

Agent reads OS objects and can:
- explain
- query evidence
- compare states
- research anomalies
- route opportunities
- run backtests
- maintain journal
- monitor approved execution modules

### PHASE L — Adaptive Research Loop

Live anomalies feed back as research questions, never silent model mutation.

```text
ANOMALY
→ RESEARCH QUEUE
→ FALSIFICATION
→ HUMAN REVIEW
→ VERSIONED ONTOLOGY UPDATE
```

---

## 9. Repository Shape — Proposed

```text
quant-lab/market_os/
├── constitution/
├── schemas/
├── registry/
│   ├── nodes/
│   ├── evidence/
│   └── nulls/
├── data/
│   ├── ingestion/
│   ├── canonical/
│   └── quality/
├── observables/
├── field/
├── patches/
├── relational/
├── lifecycle/
├── shocks/
├── directional/
├── opportunities/
├── risk/
├── replay/
├── live/
├── api/
├── agent/
└── tests/

quant-lab/defi_os/
├── protocols/
├── sensors/
├── opportunities/
├── simulation/
├── risk/
└── adapters/
```

Do not move current research folders into this runtime tree. Research remains evidence; promoted nodes are reimplemented cleanly in `market_os/`.

---

## 10. Versioning

Version independently:
- data schema
- observable definitions
- field ontology
- opportunity ontology
- strategy module
- risk policy
- execution adapter

Every snapshot records these versions.

Never allow an agent to answer “why did the OS classify this?” without a reproducible version/evidence path.

---

## 11. Local-First Deployment

Development default:

```text
Windows/Linux workstation
+ Python
+ DuckDB
+ Parquet
+ PostgreSQL
+ Redis
+ Docker Compose
```

Cloud later only for:
- continuous ingestion
- live scanner uptime
- heavier history/chain indexing
- remote agent access
- observability / backups

Do not build cloud lock-in into the ontology.

---

## 12. DeFi Placement in the OS

DeFi is not a separate philosophy. It is another opportunity domain downstream of the same market-reading core.

Example future flow:

```text
GLOBAL FIELD
→ CHAIN / PROTOCOL PATCH
→ LIQUIDITY / COLLATERAL STATE
→ YIELD / UTILIZATION / FLOW STATE
→ PROTOCOL RISK
→ OPPORTUNITY CLASS
→ SIMULATION
→ RISK ROUTER
→ EXECUTION ADAPTER
```

Possible opportunity classes later:
- yield carry
- LP deployment
- lending / borrow-rate spread
- stablecoin carry
- liquidation-support / auction opportunity
- cross-DEX arbitrage
- cross-chain dislocation
- flash-loan atomic arbitrage
- hedge / collateral rebalancing

No DeFi execution should bypass protocol-risk and simulation layers.

---

## 13. Agent Contract

The future agent should never default to:
> “What can I buy?”

It should default to:
> “What is the market structure, what changed, what constraints are active, what is locally abnormal, and what opportunity families are permitted by the current state?”

Required agent sequence:

```text
READ STATE
→ READ EVIDENCE
→ IDENTIFY CHANGE
→ IDENTIFY VALID BRANCHES
→ IDENTIFY LOCAL CONTEXT
→ ROUTE OPPORTUNITIES
→ APPLY RISK
→ REQUEST / CHECK AUTHORIZATION
→ ACT OR OBSERVE
→ JOURNAL
```

Research nulls and invalid regions are first-class constraints.

---

## 14. What NOT to Build Early

Do not prematurely build:
- giant React dashboard
- Kafka cluster
- vector DB as a substitute for canonical state
- deep neural state model
- autonomous trading loop
- smart-contract executor
- strategy marketplace
- real-time microservice zoo
- fixed static peer graph
- one monolithic alpha model

Build the ontology compiler and replay engine first.

---

## 15. Nearest Future Engineering Checkpoints

After Field Model v1 is frozen:

1. `OS-00` — canonical runtime schemas
2. `OS-01` — evidence + node registry
3. `OS-02` — PIT historical state compiler
4. `OS-03` — replay engine
5. `OS-04` — state query API
6. `OS-05` — shadow-live scanner
7. `OS-06` — opportunity ontology/router
8. `OS-07` — strategy-plugin interface
9. `OS-08` — portfolio/risk router
10. `OS-09` — agent/operator interface
11. `DEFI-00` — protocol sensor architecture
12. `DEFI-01` — DeFi opportunity ontology

---

## Governing Statement

> The Market OS is a **reader and decoder of constrained market state**. Alpha, strategy, investment, hedging, yield deployment, flash-loan routing, and execution are downstream applications of that understanding — not the organizing principle of the system.
