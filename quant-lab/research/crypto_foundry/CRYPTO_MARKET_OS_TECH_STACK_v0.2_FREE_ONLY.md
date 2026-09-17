# CRYPTO MARKET OS — TECH STACK v0.2 FREE-ONLY

**Status:** architecture / data-source plan update only  
**Branch:** `agent/crypto-quant-foundry`  
**Parent architecture:** `CRYPTO_MARKET_OS_BUILD_BLUEPRINT_v0.1.md`  
**Cost doctrine:** **NO PAID DATA DEPENDENCIES.** A source may enter the automated stack only when the required information is available at $0 under the current public terms. Paid-only endpoints remain reference-only / excluded.  
**Verification date:** 2026-08-28

---

## 1. Cost Gate

Before integrating any external source, classify it:

- `FREE_AUTOMATED` — documented $0 API / SDK / public endpoint suitable for programmatic ingestion.
- `FREE_LIMITED_AUTOMATED` — $0 programmatic access with rate / call / feature limits. Cache and respect limits.
- `FREE_REFERENCE_ONLY` — useful information is visible at $0, but no verified free programmatic interface exists.
- `PAID_EXCLUDED` — the required programmatic data requires subscription, stake, per-call payment, or enterprise access.
- `UNVERIFIED` — pricing / access terms are not explicit enough to build against. Treat as excluded until verified.

Hard rule: **FREE_REFERENCE_ONLY, PAID_EXCLUDED, and UNVERIFIED sources cannot become required runtime dependencies.**

Every provider adapter must carry:

`provider, access_class, verified_at, rate_limit, auth_mode, terms_url, fallback, provenance`.

If a previously free source becomes paid, the adapter must fail closed and the OS must continue from alternate free sources or mark the sensor `DATA_BLOCKED`.

---

## 2. External Source Decisions

### 2.1 SoSoValue — INCLUDE

**Access:** `FREE_LIMITED_AUTOMATED`.

Current public developer page states:
- Demo API plan is $0.
- API key can be obtained for free.
- current published rate limit is 20 calls/minute.
- ETF data and crypto news feeds are available / being developed under the developer platform.

Use initially for:
- BTC spot ETF flow state
- ETH spot ETF flow state
- ETF AUM / traded-value context where exposed
- crypto news feed where available under the free plan
- later free coin / sector data only after endpoint availability is verified

Market OS role:

`EXTERNAL_INSTITUTIONAL_FLOW_SENSOR`

Do not convert ETF flows directly into direction. Research whether they explain common forcing, activation depth, persistence, branch entropy, or state transitions.

Implementation notes:
- REST adapter
- local cache
- 20 RPM ceiling
- immutable raw response archive before transformation
- PIT timestamps preserved

---

### 2.2 Spectre AI — INCLUDE AS OPTIONAL EXTERNAL SENSOR ONLY

**Access:** `FREE_LIMITED_AUTOMATED`.

Current public site advertises:
- Explorer = Free
- read-only API endpoints
- 1,000 calls/day free
- paid Developer / Institutional tiers and paid/staked tiers exist, but they are explicitly excluded from this plan

Use only the documented free read-only endpoints.

Potential sensors:
- external market-intelligence verdicts
- public whale / onchain / social / market summaries where exposed free
- external corroboration / disagreement against native Market OS state

Market OS role:

`EXTERNAL_INTELLIGENCE_CROSSCHECK`

Spectre is **not canonical truth** and must not define the ontology. Treat its synthesized outputs as third-party observations.

Hard blocks:
- no $99 Developer plan
- no institutional plan
- no x402 / USDC pay-per-call
- no token staking to unlock data
- no paid WebSocket requirement

If a required endpoint is outside Explorer/free allowance -> `DATA_BLOCKED` or use another source.

---

### 2.3 LI.FI / Jumper — INCLUDE LATER FOR FREE ROUTING / SIMULATION DATA

**Access:** `FREE_LIMITED_AUTOMATED` for API / SDK integration.

Current LI.FI public plan states Standard integration is free and public support documentation states free API keys are available. Published limits include public / authenticated rate limits; Standard advertises up to roughly 200 requests/minute depending on endpoint / plan context.

Market OS role later:

`CROSS_CHAIN_ROUTE_SENSOR`

and eventually

`DEFI_EXECUTION_ROUTER`

Free research / simulation uses:
- available cross-chain routes
- bridge / DEX path availability
- quoted amounts
- route composition
- estimated gas / fees / slippage when returned
- route redundancy

Important cost distinction:

**API integration can be free, but actual onchain transactions are not free.** LI.FI may charge transaction fees and underlying chains / bridges / DEXs charge their own costs. Therefore during research and Market OS build:

`QUOTE / ROUTE / SIMULATE = ALLOWED`
`EXECUTE TRANSACTION = NOT AUTHORIZED`

No route should be executed merely because the information API is free.

---

### 2.4 Token Terminal — REFERENCE ONLY, NO REQUIRED AUTOMATED INTEGRATION

**Access:** `FREE_REFERENCE_ONLY` for limited web features; `PAID_EXCLUDED` for the programmatic data product required by the OS.

Current public pricing indicates:
- Pro is paid (~$325/month at verification time).
- REST API is a separate subscription / custom-priced product.
- API key is provided after subscribing.
- Token Terminal has historically exposed limited free web / Studio functionality, including a small number of charts / dashboards for free users.

Decision:

Do **not** make Token Terminal API part of the stack.

Allowed:
- manual research reference
- methodology reference
- validation ideas
- use public/free visible information only when terms permit

Not allowed:
- paid API
- paid Pro
- Data Room
- any workflow that silently assumes Token Terminal programmatic access

For protocol fundamentals, prefer free primary/onchain sources and protocol-native APIs / subgraphs / RPC reads where possible.

---

### 2.5 Polymarket Analytics / Falcon — FREE WEB REFERENCE; API UNVERIFIED FOR $0

**Access:**
- `FREE_REFERENCE_ONLY` for the Polymarket Analytics web product: current legacy pricing advertises a $0/forever tier with market analytics and trader leaderboards.
- Falcon developer API: `UNVERIFIED` for zero-cost programmatic use. The public API page offers API keys and MCP access but does not publish a clear $0 API allowance / rate limit sufficient to classify it as free automated infrastructure.

Decision:

Do **not** make Falcon / Polymarket Analytics API a required dependency until explicit $0 API terms are documented.

Allowed:
- manual reference to free dashboard analytics
- research of prediction-market concepts

For an eventual automated `EXPECTATION_FIELD`, prefer verified free public prediction-market sources / official public endpoints rather than introducing a paid dependency. Any substitute must separately pass the free-only gate before integration.

---

### 2.6 Yieldz — FREE REFERENCE / DEFI DISCOVERY SURFACE, NOT A CANONICAL API DEPENDENCY

**Access:** `FREE_REFERENCE_ONLY` / `UNVERIFIED` for programmatic ingestion.

Yieldz publicly exposes a usable web interface and documentation showing markets / vaults across protocols such as Morpho, Aave, Lista, Fluid and others. Public pages expose APY, liquidity, utilization, LLTV and related opportunity context. However, no sufficiently clear public $0 developer API contract was verified for a canonical automated dependency.

Decision:

Use Yieldz as:
- DeFi discovery UI
- reference implementation
- source of ideas for which lending / vault observables matter

Do not make it a required runtime feed.

Instead, when DeFi sensors are built, ingest from the underlying protocols / chains using free public contracts, RPC calls, protocol APIs, subgraphs, or other verified-free interfaces.

Potential eventual observables inspired by Yieldz:
- deposit APY
- borrow APY
- utilization
- available liquidity
- LLTV / LTV
- oracle state
- IRM state
- APY history
- vault composition

---

## 3. Updated Free-Only External Sensor Stack

```text
CORE NATIVE MARKET / PIT DATA
        |
        +--> PRICE / VOLUME / RANK / SUPPLY
        +--> FUNDING / OI / LIQUIDATIONS (free providers only)
        +--> STABLECOIN / TVL / DEX / CHAIN DATA (free providers only)
        |
        v
MARKET OS TERRAIN
        |
        +--> SoSoValue free API
        |      -> ETF / institutional-flow context
        |
        +--> Spectre Explorer free API [optional corroborator]
        |      -> external intelligence crosscheck
        |
        +--> protocol-native / onchain free reads
        |      -> protocol economics / lending / utilization / liquidity
        |
        +--> prediction-market official/public free endpoints [future]
        |      -> expectation field
        |
        +--> LI.FI free API [later quote/simulation only]
               -> route / bridge / DEX path context

REFERENCE ONLY:
Token Terminal free web / methodologies
Polymarket Analytics free web dashboard
Yieldz free web / docs

EXCLUDED AS REQUIRED DEPENDENCIES:
Token Terminal paid API / Pro / Data Room
Falcon API until $0 programmatic terms verified
Spectre paid / x402 / staked tiers
LI.FI enterprise paid tiers
any paid Yieldz / third-party data product if introduced
```

---

## 4. Provider Independence

The OS should never be architected around one third-party vendor.

Canonical flow:

```text
PROVIDER RAW RESPONSE
-> provider adapter
-> source-normalized observation
-> PIT canonical layer
-> observable layer
-> state layer
```

No provider-specific field names above the adapter layer.

Every high-value sensor should eventually support:
- primary provider
- free fallback or direct-chain reconstruction
- provenance comparison
- stale-data detection
- rate-limit handling

If no free fallback exists, label that sensor non-critical until one is built.

---

## 5. Current Research Objects That Now Affect Runtime Architecture

### 5.1 Market Field Surface

MECH-15 tested the raw 16-cell state x constraint surface and selected a **6-cell reduced candidate surface** rather than retaining all 16 cells.

Current status:
- raw 16-cell matrix survived permutation falsification
- 8 ROBUST / 7 LOCAL / 1 SPARSE cells
- held-out stability is PARTIAL, not fully stable
- 6-cell cut preserves approximately 0.915 mean structural information under the checkpoint definition
- age remains a partial overlay

Runtime implication:

Do not hard-code the original 16 labels as the production ontology.

Design `FieldSnapshot` so the representation is versioned:

```text
raw_global_state: HH | HL | LH | LL
spatial_activation: HIGH | LOW
temporal_constraint: HIGH | LOW
raw_matrix_cell: optional 16-cell label
reduced_surface_cell: versioned candidate label
state_age: integer
age_band: categorical
surface_version: string
surface_confidence: ...
```

The six-cell surface remains `CONDITIONAL` until stronger chronological validation.

### 5.2 Dynamic Relational State

LOWER-FIELD-8 resolves peer topology into three separate objects:

```text
MEMBERSHIP = who the peers are
NEIGHBORHOOD = whether a usable peer set exists
RELATIONAL_STATE = the asset's role relative to its current neighborhood
```

Current result:
- exact same-member persistence decays strongly
- relational-state persistence is materially higher
- membership entropy is broadly stationary
- relational state does **not** add predictive information beyond stronger peer representations in LF8 purged AUC tests

Runtime implication:

`RelationalSnapshot` is justified as a **descriptive local-state object**, not an alpha score.

It should preserve:
- relational state
- peer family
- current peer IDs
- peer membership entropy
- turnover
- neighborhood availability
- state persistence / age
- confidence / quality

Do not collapse dynamic peer IDs into a permanent graph.

---

## 6. Revised Runtime Objects

Minimum object set remains:

```text
FieldSnapshot
PatchSnapshot
RelationalSnapshot
LifecycleSnapshot
ConstraintSnapshot
ShockSnapshot
DirectionalSnapshot
ExternalFlowSnapshot
ProtocolSnapshot
ExpectationSnapshot        # future, free source required
RouteQuoteSnapshot         # future LI.FI quote/simulation only
OpportunityCandidate
RiskState
ExecutionCandidate
ResearchEvidence
NullBoundary
```

New external objects are sensors / context. They do not override core terrain.

---

## 7. Revised Build Priority

### NOW — research / ontology

1. continue Field Model v1 validation
2. deepen reduced Market Field Surface stability
3. continue dynamic relational-state validation
4. freeze nulls and conditional regions
5. define external sensor semantics before ingestion

### NEXT — OS substrate

1. OS-00 canonical schemas
2. OS-01 evidence / node registry
3. OS-02 PIT historical state compiler
4. OS-03 replay engine
5. OS-04 state query API
6. free-source ingestion adapters
   - SoSoValue first external adapter
   - free native/onchain protocol adapters
   - Spectre Explorer optional crosscheck adapter
7. OS-05 shadow-live scanner

### LATER — DeFi intelligence

1. protocol-native free lending / vault sensors
2. free DEX / liquidity / oracle state
3. DeFi opportunity ontology
4. LI.FI route quote/simulation adapter
5. no execution until separately authorized

---

## 8. Free-Only CI / Monitoring Rules

Add tests that fail when:
- an adapter requires a paid subscription
- an endpoint returns payment-required semantics
- a free quota is exhausted and code silently substitutes stale data
- access class changes from FREE to PAID without review
- provenance is missing
- rate limits are ignored

Add provider registry fields:

```text
cost_usd_required = 0
free_tier_required = true
payment_method_required = false
staking_required = false
transaction_required = false   # data ingestion only
```

For LI.FI specifically, `transaction_required=false` must remain true until execution phase authorization.

---

## 9. Governing Free-Data Statement

> The Market OS may learn from any public source, but its required operating data stack must be reproducible at **$0 in data-subscription cost**. Paid vendor convenience may never become a hidden dependency. Where a vendor charges for programmatic access, prefer direct onchain reconstruction, protocol-native endpoints, or another verified-free source.

`human_review_required = TRUE`
`next_checkpoint_authorized = FALSE`
