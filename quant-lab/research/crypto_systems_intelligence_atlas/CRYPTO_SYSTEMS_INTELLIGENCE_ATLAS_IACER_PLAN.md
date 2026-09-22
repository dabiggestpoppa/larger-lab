# CRYPTO SYSTEMS INTELLIGENCE ATLAS (CSIA)
## IACER PLAN — RIGHT HEMISPHERE OF CRYPTO SENSOR

**Working title:** Crypto Systems Intelligence Atlas (CSIA)  
**Role:** Right hemisphere / investor-fundamental intelligence layer  
**Companion system:** Crypto Sensor Fabric = left hemisphere / trader-mechanical intelligence layer  
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`  
**Status:** INTENT + ARCHITECTURE PLAN ONLY  
**Implementation authority:** NONE until constitution + bloc authorization  
**Date:** 2026-09-22

---

# I — INTENT

Build a living, evidence-backed world model of the crypto ecosystem.

The system should explain:

- what each important blockchain, ledger, network, protocol, bridge, oracle, stablecoin, application layer, infrastructure layer, and market primitive actually does;
- how each system is architected;
- what it depends on;
- what depends on it;
- where liquidity and capital move;
- which protocols act as bridges, routers, settlement layers, execution layers, data layers, liquidity hubs, credit rails, payment rails, or application infrastructure;
- what each token is economically and operationally tied to;
- what ecosystem or technological direction a project is structurally committed to;
- how architecture, integrations, adoption, capital flows, upgrades, regulation, and narrative changes connect to price and market behavior.

This is the **fundamental / investor-facing half** of Crypto Sensor.

The existing Crypto Sensor answers:

> What is the market doing?

CSIA answers:

> What is the system, what changed inside it, why does that change matter, and what relationships should we watch?

The Context Bridge between both systems should eventually answer:

> What changed structurally, did users/capital/network activity confirm it, and did the market price it?

---

# A — ABSTRACTIONS

## A1. Right hemisphere vs left hemisphere

```text
LEFT HEMISPHERE                         RIGHT HEMISPHERE
CRYPTO SENSOR                           CSIA
TRADER / MECHANICAL                     INVESTOR / STRUCTURAL

price                                    architecture
open interest                            ecosystem topology
funding                                  protocol roles
liquidations                             dependencies
basis / premium                          integrations
order books                              adoption
volatility                               capital plumbing
cross-venue state                        token utility
mechanical regimes                       developer / usage state
                                         governance / upgrades
                                         narrative + catalysts

                  \                    /
                   \                  /
                    CONTEXT BRIDGE
                          |
                          v
                 MARKET UNDERSTANDING
```

Neither side replaces the other.

The right hemisphere must not become a price-signal generator by default.

The left hemisphere must not pretend price mechanics alone explain system structure.

---

## A2. The object is the system, not just the token

Primary object types:

```text
BLOCKCHAIN
LEDGER
ROLLUP
L2
L3
APPCHAIN
SIDECHAIN
DAG_NETWORK
MODULAR_CHAIN
DATA_AVAILABILITY_NETWORK
ORACLE_NETWORK
INTEROPERABILITY_PROTOCOL
BRIDGE
MESSAGING_LAYER
STABLECOIN
DEX
PERP_DEX
LENDING_PROTOCOL
MONEY_MARKET
STAKING_PROTOCOL
RESTAKING_PROTOCOL
LIQUID_STAKING_PROTOCOL
RWA_PROTOCOL
PAYMENT_NETWORK
STORAGE_NETWORK
COMPUTE_NETWORK
DEPIN_NETWORK
IDENTITY_NETWORK
PRIVACY_NETWORK
WALLET_INFRASTRUCTURE
RPC_INFRASTRUCTURE
INDEXER
DEVELOPER_TOOLING
GOVERNANCE_SYSTEM
TOKEN
APPLICATION
MARKET_INFRASTRUCTURE
OTHER
```

A token is not automatically the same thing as its network or protocol.

Examples:

- XRP != XRP Ledger.
- ATOM != Cosmos SDK != IBC != Cosmos Hub.
- ETH != Ethereum execution != EVM != the Ethereum rollup ecosystem.
- LINK != Chainlink oracle feeds alone.
- DOT != Polkadot relay/shared-security architecture.
- BTC != the full Bitcoin ecosystem.

These distinctions are foundational.

---

## A3. Native architecture first

Every chain is modeled according to its own architecture.

Do not force everything into an EVM-shaped model.

Examples of architecture families that need distinct treatment:

- Bitcoin / UTXO systems;
- Ethereum / EVM systems;
- Solana / SVM systems;
- XRP Ledger;
- Cosmos SDK / CometBFT / IBC systems;
- Polkadot / Substrate / XCM systems;
- Avalanche multi-chain / custom-L1 architecture;
- Move ecosystems such as Sui and Aptos;
- ICP / canister-compute architecture;
- DAG-based systems;
- modular / rollup-centric systems;
- appchain architectures;
- permissioned / enterprise-linked ledger systems where materially relevant.

Normalization happens only at the comparison layer.

---

## A4. Three map resolutions

### Global map

Shows the whole crypto system:

- major architecture families;
- settlement / execution layers;
- interoperability;
- capital rails;
- oracle/data rails;
- stablecoin rails;
- liquidity hubs;
- cross-ecosystem dependencies.

### Chain map

Each meaningful blockchain / ledger receives its own anatomy.

Example categories:

- consensus;
- execution;
- validator/security model;
- native asset;
- fee model;
- VM / programming model;
- smart-contract support;
- scaling;
- wallets;
- stablecoins;
- bridges;
- interoperability;
- oracles;
- DEXs;
- lending;
- derivatives;
- staking;
- RWAs;
- payments;
- DePIN;
- applications;
- developer tooling;
- RPC/indexing;
- governance;
- major integrations;
- capital routes.

### Protocol map

Each systemically important protocol gets its own dependency graph:

```text
WHAT IT DOES
WHAT IT RUNS ON
WHAT IT DEPENDS ON
WHAT DEPENDS ON IT
WHAT ASSETS IT ROUTES
WHAT RISKS IT INTRODUCES
WHAT VALUE ITS TOKEN CAPTURES
WHAT ECOSYSTEMS IT CONNECTS
```

---

## A5. Role is multi-dimensional

A project may have multiple roles simultaneously.

Example:

```text
CHAINLINK
- oracle network
- data delivery
- cross-chain messaging
- proof-of-reserve infrastructure
- automation
- dependency for lending / derivatives / RWA systems
```

Therefore the atlas must use a graph / multi-tag model, not a one-category spreadsheet.

---

## A6. Structural commitment

"Commitment" means the architecture, economic model, ecosystem dependencies, and strategic direction a system is structurally tied to.

Examples:

```text
BASE
- Ethereum settlement
- EVM
- OP Stack
- Ethereum rollup ecosystem

OSMOSIS
- Cosmos SDK
- IBC
- sovereign appchain model
- Cosmos liquidity ecosystem

CELESTIA
- modular architecture
- data availability
- rollup-centric design

CHAINLINK
- chain-agnostic middleware
- oracle/data delivery
- cross-chain connectivity
```

Commitment is evidence-based, versioned, and can change.

---

## A7. Capital plumbing

The atlas must map how value moves through the system.

Examples:

```text
FIAT
 -> stablecoin issuer
 -> native chain issuance
 -> bridge
 -> DEX
 -> lending
 -> collateral
 -> perp venue
 -> staking / yield
 -> exit route
```

Research objects include:

- stablecoin issuance;
- native vs bridged assets;
- bridge topology;
- liquidity pools;
- lending markets;
- collateral pathways;
- staking/restaking;
- yield markets;
- treasury / reserve assets;
- perp collateral;
- RWA settlement;
- cross-chain routing.

---

## A8. Narrative -> action -> confirmation

Narrative alone is not treated as fundamental evidence.

The system should distinguish:

```text
NARRATIVE
   |
   v
STRUCTURAL ACTION
upgrade / integration / launch / bridge / institutional use / tokenization
   |
   v
NETWORK RESPONSE
usage / developers / transactions / addresses / contracts
   |
   v
CAPITAL RESPONSE
TVL / stablecoins / liquidity / bridge flow / lending / volume
   |
   v
MARKET RESPONSE
price / OI / funding / basis / relative strength
```

This becomes the core Context Bridge between CSIA and Crypto Sensor.

---

## A9. Ecosystem evolution

The atlas is versioned over time.

It should detect and preserve:

- new chains;
- new protocols;
- migrations;
- new bridges;
- bridge shutdowns;
- native asset issuance;
- stablecoin expansion;
- new L2s / appchains;
- changes in DA;
- oracle adoption;
- validator/security changes;
- major governance upgrades;
- token-model changes;
- protocol rebrands;
- acquisitions;
- dependencies appearing/disappearing;
- chain/protocol deprecations.

The goal is not only:

> What is the architecture?

but also:

> How is the architecture changing?

---

# C — CONTEXT

## C1. Existing Quant Lab / Crypto Sensor

Crypto Sensor Fabric is already the mechanical evidence spine.

Its active responsibilities include:

- exchange / venue mechanics;
- market data;
- funding;
- OI;
- basis / premium;
- liquidation state;
- order-book observations;
- provenance;
- immutable evidence;
- provider-specific semantics;
- historical/live mechanical research.

CSIA must sit beside it, not inside it initially.

---

## C2. Existing queued Capital Field work

The existing queued Capital Field/source-atlas concept already contains pieces such as:

- DEX/CEX mechanics;
- onchain flow;
- bridges;
- lending;
- yield;
- RWA;
- protocol economics;
- capital routing.

CSIA is broader.

Capital Field should eventually become one major subsystem / lens inside CSIA rather than the entire right hemisphere.

---

## C3. Coverage philosophy

The atlas is not limited to the most fashionable chains.

Candidate inclusion can come from any architecture family if it has meaningful:

- market capitalization;
- trading volume;
- onchain activity;
- stablecoin/liquidity activity;
- developer ecosystem;
- protocol dependency;
- institutional relevance;
- infrastructure importance;
- architectural uniqueness;
- historical/systemic relevance.

Expected coverage includes, but is not limited to:

- Bitcoin;
- Ethereum;
- XRP Ledger;
- Solana;
- BNB Chain;
- Avalanche;
- Cosmos / major appchains;
- Polkadot / Substrate ecosystem;
- Cardano;
- TON;
- Sui;
- Aptos;
- ICP;
- NEAR;
- Hedera;
- Algorand;
- Tron;
- major EVM chains;
- major L2s;
- modular stacks;
- DAG systems;
- interoperability networks;
- oracle networks;
- stablecoin systems;
- major DeFi infrastructure.

No fixed list is frozen at planning time.

Coverage expands through evidence-backed discovery.

---

## C4. Sources

Future source hierarchy should prefer:

1. protocol / chain official documentation;
2. repositories and technical specs;
3. explorer / RPC / indexer data;
4. first-party dashboards;
5. foundation / governance publications;
6. audited smart-contract / deployment data;
7. high-quality research / analytics sources;
8. aggregators as corroboration;
9. social/news only as discovery or narrative evidence.

A claim about architecture or dependency must be source-backed.

A social narrative is never canonical architecture truth.

---

## C5. Data model direction

The correct foundation is a temporal knowledge graph / hypergraph, not a flat taxonomy.

Core node types:

```text
CHAIN
PROTOCOL
TOKEN
BRIDGE
ORACLE
STABLECOIN
APPLICATION
ENTITY
ASSET
VALIDATOR_SET
VM
STANDARD
GOVERNANCE_SYSTEM
MARKET
INTEGRATION
EVENT
NARRATIVE
```

Core edge types:

```text
RUNS_ON
SETTLES_TO
SECURED_BY
USES_VM
BRIDGES_TO
MESSAGES_TO
ORACLE_FOR
ISSUED_ON
COLLATERAL_IN
LIQUIDITY_ON
DEPENDS_ON
INTEGRATES_WITH
FORKED_FROM
BUILT_WITH
GOVERNED_BY
STAKED_IN
RESTAKED_IN
ROUTED_THROUGH
MIGRATED_FROM
MIGRATED_TO
COMPETES_WITH
COMPLEMENTS
```

Every important edge should eventually support:

- source;
- observed date;
- valid-from;
- valid-to;
- confidence;
- evidence type;
- status.

---

# E — EXPECTATIONS

## E1. System behavior

CSIA should eventually be able to answer questions like:

- What is XRP Ledger's actual architecture and ecosystem?
- Which protocols depend directly on Chainlink?
- Which major systems ultimately settle to Ethereum?
- Which chains are EVM-compatible but not Ethereum-settled?
- What is native to Cosmos/IBC versus merely connected to it?
- Where does USDC move across chains?
- What protocols rely on a specific bridge?
- What happens structurally if a major oracle or bridge fails?
- Which chains gained meaningful stablecoin/liquidity activity over the last quarter?
- Which narratives were followed by actual integrations and capital?
- Which ecosystems are growing fundamentally while market price remains weak?
- Which assets are trading strongly with little structural confirmation?
- How does a chain's ecosystem change after a major upgrade?

---

## E2. Research surfaces

The system should expose at least:

### Architecture
- consensus;
- VM;
- settlement;
- execution;
- DA;
- interoperability;
- security model.

### Ecosystem
- applications;
- DeFi;
- stablecoins;
- wallets;
- developer tooling;
- infrastructure;
- institutional integrations.

### Capital
- TVL;
- stablecoin supply;
- bridge flows;
- lending;
- DEX liquidity;
- derivatives;
- staking;
- yield;
- RWA.

### Activity
- transactions;
- active users/addresses where meaningful;
- fees;
- contract deployment;
- developer activity;
- validator/node health where relevant.

### Token economics
- supply;
- issuance;
- burns;
- staking;
- collateral use;
- governance role;
- fee role;
- value-capture pathways.

### Narrative / events
- upgrades;
- launches;
- integrations;
- regulation;
- institutional adoption;
- partnerships;
- migrations;
- outages;
- exploits.

### Relationships
- dependencies;
- integrations;
- bridges;
- shared security;
- shared liquidity;
- common middleware;
- competitor/complement topology.

---

## E3. Fundamental states

Eventually, evidence may be summarized into descriptive state vectors such as:

```text
ARCHITECTURE_STATE
ECOSYSTEM_GROWTH_STATE
CAPITAL_STATE
USAGE_STATE
DEVELOPER_STATE
LIQUIDITY_STATE
TOKEN_UTILITY_STATE
VALUE_CAPTURE_STATE
DEPENDENCY_CENTRALITY
INTEROPERABILITY_STATE
STABLECOIN_STATE
GOVERNANCE_UPGRADE_STATE
NARRATIVE_STATE
NARRATIVE_CONFIRMATION_STATE
```

These are research summaries, not investment ratings.

No hidden "good coin / bad coin" score.

---

## E4. Context Bridge expectations

The interface with Crypto Sensor should allow combinations like:

```text
RIGHT:
ecosystem growth + stablecoin inflow + new integrations

LEFT:
spot strength + OI expansion + healthy funding

BRIDGE:
STRUCTURAL + CAPITAL + MARKET CONFIRMATION
```

or:

```text
RIGHT:
social narrative spike, no measurable adoption

LEFT:
OI spike + extreme funding + liquidation concentration

BRIDGE:
SPECULATIVE MOVE / FUNDAMENTAL CONFIRMATION ABSENT
```

The exact labels will be defined later in evidence-backed research.

---

## E5. Ongoing-development expectations

CSIA is not a one-time report.

It should support:

- scheduled source discovery;
- change detection;
- graph revisions;
- stale-edge detection;
- source-health checks;
- new-chain/protocol candidate queues;
- operator review;
- reproducible snapshots;
- historical topology replay.

---

# R — RESULTS

## R1. End product

A living, navigable, machine-readable **crypto world model** consisting of:

### 1. Global Blockchain Systems Map

Zoomed-out architecture of the crypto market.

### 2. Chain Atlases

A dedicated map for every materially relevant blockchain / ledger.

### 3. Protocol Atlases

Deep maps for systemically relevant middleware and applications.

### 4. Dependency Graph

What depends on what.

### 5. Interoperability Graph

How chains and protocols communicate.

### 6. Capital Plumbing Graph

How assets and liquidity move.

### 7. Token Role Map

What tokens actually do inside their systems.

### 8. Ecosystem Evolution Timeline

How architecture and relationships change.

### 9. Fundamental Research Panel

Investor-facing current-state view.

### 10. Context Bridge

Fundamental / narrative / capital state joined to Crypto Sensor mechanical market state.

---

## R2. Example operator flow

```text
SEARCH: XRP
   |
   v
XRP TOKEN
   |
   +--> XRP LEDGER
           |
           +--> consensus
           +--> validators
           +--> DEX / AMM
           +--> issued assets
           +--> stablecoins
           +--> payments
           +--> RWA/tokenization
           +--> bridges
           +--> EVM-related systems
           +--> apps/integrations
           +--> governance/upgrades
           +--> activity/capital data
   |
   v
RECENT STRUCTURAL CHANGES
   |
   v
CAPITAL / USAGE CONFIRMATION
   |
   v
CRYPTO SENSOR MARKET STATE
```

---

## R3. Relationship to other programs

```text
CRYPTO SENSOR FABRIC
= market mechanics / trader hemisphere

CSIA
= architecture + fundamentals + ecosystem + narrative / investor hemisphere

CAPITAL FIELD
= capital-plumbing subsystem within broader CSIA

QCAE / RESEARCH MESH
= future discovery / evidence acquisition support

OCE
= future orchestration / scheduling / operational execution

CONTEXT BRIDGE
= joins CSIA state to Crypto Sensor state
```

No component silently gains authority over another.

---

## R4. Explicit non-goals

CSIA is not initially:

- a token recommender;
- an automated investment ranking;
- a trading execution system;
- a sentiment bot;
- a news summarizer;
- a static infographic;
- a generic crypto encyclopedia;
- an everything-is-EVM taxonomy;
- a single composite score.

It is a **structural intelligence substrate**.

---

## R5. Success condition

The project succeeds when an operator can ask:

> "Show me this asset / chain / protocol and explain its actual place in crypto."

and receive:

1. native architecture;
2. token/system distinction;
3. ecosystem;
4. dependencies;
5. integrations;
6. capital routes;
7. current fundamental state;
8. major recent structural changes;
9. narrative vs evidence;
10. corresponding market state from Crypto Sensor.

That is the complete brain bridge.

---

# NEXT PLANNING STAGE

This IACER document defines the mission.

The next artifact is the **CSIA Constitution**.

The constitution should freeze:

1. mission and authority;
2. epistemic rules;
3. source hierarchy;
4. native-architecture doctrine;
5. graph ontology;
6. temporal / provenance rules;
7. inclusion / exclusion rules;
8. narrative-evidence rules;
9. fundamental-state boundaries;
10. Context Bridge boundaries;
11. relationship to Crypto Sensor / Capital Field / QCAE / OCE;
12. operator gates;
13. test and evidence doctrine;
14. amendment procedure;
15. bloc authorization rules.

Only after constitution ratification should we write the implementation books, blocs, and chapters.

---

# CURRENT DECISION

```text
PROJECT = CRYPTO_SYSTEMS_INTELLIGENCE_ATLAS
ROLE = RIGHT_HEMISPHERE
PRIMARY_USER_LENS = INVESTOR_FUNDAMENTAL
PAIR_SYSTEM = CRYPTO_SENSOR
PRIMARY_MODEL = TEMPORAL_KNOWLEDGE_GRAPH
NATIVE_ARCHITECTURE_FIRST = TRUE
CHAIN_SPECIFIC_ATLASES = TRUE
GLOBAL_ATLAS = TRUE
CAPITAL_PLUMBING = INCLUDED
NARRATIVE_TO_ACTION_BRIDGE = INCLUDED
ONGOING_DISCOVERY = REQUIRED
TRADING_AUTHORITY = FALSE
EXECUTION_AUTHORITY = FALSE
IMPLEMENTATION_AUTHORITY = FALSE
NEXT = CONSTITUTION
```
