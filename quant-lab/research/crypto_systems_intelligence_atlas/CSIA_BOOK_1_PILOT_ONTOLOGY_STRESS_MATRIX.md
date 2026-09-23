# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 1 — PILOT ONTOLOGY STRESS MATRIX

**Document ID:** CSIA-B1-PILOT-001
**Version:** 0.1
**Status:** PLANNING ARTIFACT — VALIDATION INSTRUMENT FOR BOOK 1
**Depends on:** `CSIA_BOOK_1_IDENTITY_ONTOLOGY_TEMPORAL_GRAPH_PLAN_v0.1.md` (Blocs 1A–1D)
**Purpose:** Prove the Book 1 ontology cannot cheat, by exercising it against seven intentionally unlike systems. No implementation. No code.
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`

---

# 0. Method

For each pilot system we enumerate:

1. **Required Book 1 objects** — which Bloc 1B primary classes + role tags the system needs.
2. **Required edge types** — which Bloc 1C dictionary entries and hyperedges the system's real structure demands.
3. **What breaks under an EVM-biased ontology** — the concrete modeling failure if the graph assumed accounts/contracts/gas.
4. **Ontology extension needed** — any gap found in Book 1 v0.1 (this drives amendments, not silent patching).

Pilot set (chosen for maximal architectural distance):

```text
P1  Bitcoin        UTXO, script-less smart contracts, mining economy
P2  Ethereum       EVM, account model, rollup-centric settlement root
P3  XRP Ledger     account model, no smart contracts (core), trustlines,
                   native DEX, UNL validators, no mining
P4  Solana         SVM, account model w/ programs, stake economy,
                   high-throughput fee market
P5  Cosmos         SDK/CometBFT, sovereign appchains, IBC, shared security
P6  ICP            canister compute, subnets, reverse gas, neuron governance
P7  DAG network    (representative, e.g., Fantom/Tangle-family semantics)
                   blockDAG, probabilistic/declarative finality device
```

Cross-cutting anchor case: **USDC** (multi-chain token with native + bridged deployments) is traced through all seven to stress identity and temporal doctrine.

---

# P1 — BITCOIN

## Required Book 1 objects
- `BLOCKCHAIN` (primary) + role tags: `UTXO`, `MONOLITHIC`
- `TOKEN` — BTC as `NATIVE_TO` asset (no deployment, native marker)
- `VALIDATOR_SYSTEM` — miners/mining pools as economy objects (`ENTITY` for pools; `MARKET`-adjacent hash-rate economy is Book 3/6, not 1)
- `PROTOCOL` — Lightning Network (layer-2 state channels; role tag `PAYMENT_RAIL`)
- `STANDARD` — BIPs (BIP-32/39/84/141…) as first-class STANDARD objects
- `PROTOCOL` — Bitcoin Script semantics captured as family attribute (no VM object — deliberately no `USES_VM` edge)
- `BRIDGE` — federation/multisig bridges (e.g., wBTC custody) anchored to Bitcoin assets

## Required edge types
- `NATIVE_TO` (BTC→Bitcoin)
- `SECURED_BY` (Bitcoin→mining economy via `VALIDATOR_SYSTEM`)
- `STANDARD` conformance: `USES_STANDARD` ( Lightning→BIP specs; wallets→BIP-32/39)
- `BUILT_WITH` (client implementations)
- `LAYERED_ON`-shaped relationship: Lightning `RUNS_ON` Bitcoin (with `PAYMENT_RAIL` role)
- `BRIDGES_TO` / `HE-BRIDGE-ROUTE` (wBTC-style bridges)
- Hyperedge `HE-SECURITY-SHARE` not needed; simple SECURED_BY suffices

## What breaks under EVM bias
- No contract addresses exist: deployment identity must survive with `NATIVE_MARKER` and protocol-level issuance — an EVM-biased model would invent a fake "native contract" or drop BTC-as-asset entirely.
- UTXO model has no account balances: "address" semantics differ; any EVM account-model field would be fabricated.
- Lightning has no contracts in the EVM sense; an ontology requiring `USES_VM` would either misclassify or block Lightning entirely.
- Mining-pool security is not validator staking: `STAKED_IN` is invalid; SECURED_BY must carry mechanism diversity (PoW vs PoS) or be forced into wrong semantics.
- BIP standards are not ERCs but are equally load-bearing; an EVM-only STANDARD family would omit them.

## Ontology extension needed
- E-1: `SECURED_BY` requires a `mechanism` attribute (POW | POS | DPOS | BFT | HYBRID | FEDERATED) — Book 1 v0.1 edge dictionary implies but does not state; **amend edge dictionary**.
- E-2: Lightning-style state-channel L2 needs a role tag `STATE_CHANNEL` (currently only rollup/sidechain tags exist). **Amend role-tag registry.**
- E-3: No amendment needed for native-marker deployment (1A already covers).

---

# P2 — ETHEREUM

## Required Book 1 objects
- `BLOCKCHAIN` + `ACCOUNT`, `EVM`, `MONOLITHIC`→`MODULAR` (post-4844 rollup-centric; **valid-time role-tag change** — a Book 1D showcase)
- `VM` object (EVM) — `USES_VM` edge target
- `STANDARD` objects — ERC-20/721/1155/4337
- `TOKEN` — ETH (`NATIVE_TO`), plus ERC-20s via deployments
- `ROLLUP` chains as BLOCKCHAIN + `ROLLUP_OPTIMISTIC`/`ROLLUP_ZK` tags, each with `SEQUENCER_INFRASTRUCTURE` objects
- `DATA_AVAILABILITY_NETWORK` (external DA where applicable; post-4844 blob space as Ethereum-native DA)
- `BRIDGE` — canonical rollup bridges vs third-party
- `ORACLE_NETWORK` — consumer relationships
- `ENTITY` — Ethereum Foundation, client teams

## Required edge types
- `USES_VM` (Ethereum, rollups→EVM)
- `ISSUED_ON` (every ERC-20 deployment)
- `SETTLES_TO` (rollups→Ethereum) — the canonical settlement-DAG case
- `RUNS_ON` (protocols→Ethereum; rollups→Ethereum for execution anchoring)
- `VALIDATED_BY` (Ethereum→PoS validator system; distinct from rollup sequencers)
- `MESSAGES_TO` / `BRIDGES_TO` (L1↔L2 messaging)
- `DATA_FROM` (rollups→DA layer where external)
- `HE-ISSUANCE` (USDC: Circle/Base/settlement Ethereum)
- `GOVERNED_BY` (protocol parameter governance via onchain systems)

## What breaks under EVM bias (inverse stress — here bias *fits*, which is itself a test)
- The bias risk at Ethereum is the opposite: over-generalization. The stress is that Ethereum must NOT become the template — validated by the other six rows, not this one.
- Real Ethereum-specific check: sequencer as separate infrastructure class (a centralized sequencer is a dependency edge from every rollup — an EVM-biased "it's just a chain" model misses systemic risk).
- Settlement vs bridge distinction: an optimistic rollup SETTLES_TO; a sidechain with its own consensus (e.g., historic examples) only BRIDGES_TO — the 1C rule must survive Ethereum's own family diversity.

## Ontology extension needed
- E-4: none — Ethereum validates existing classes; sequencer class already present `[→SG-B]`.

---

# P3 — XRP LEDGER

## Required Book 1 objects
- `LEDGER` (XRPL is a ledger, not a general chain) + role tags: `ACCOUNT`, `CONSENSUS_BFT`-family (UNL-based), `MONOLITHIC`
- `TOKEN` — XRP (`NATIVE_TO`), plus issued assets (IOUs) via trustline semantics
- `PROTOCOL` — XRPL native DEX (orderbook, not AMM — role tag `DEX` as *role*, primary class PROTOCOL or a native-DEX application object)
- `STANDARD` — issued-asset/trustline semantics as family attribute
- `VALIDATOR_SYSTEM` — UNL (Unique Node List) validators
- `STABLECOIN` — RLUSD and similar, native-issued on XRPL
- `BRIDGE` — XLS-38 / cross-chain bridges (EVM sidechains: an *associated EVM chain* must be a separate BLOCKCHAIN object)

## Required edge types
- `NATIVE_TO` (XRP→XRPL)
- `ISSUED_ON` (issued assets; trustline representation is family attribute)
- `VALIDATED_BY` (XRPL→UNL validator system)
- `SECURED_BY` with mechanism `CONSENSUS_BFT`-family (no mining, no staking — E-1 mechanism attribute is exercised hard)
- `RUNS_ON` (native DEX→XRPL — no contracts involved)
- `BRIDGES_TO` (XRPL↔EVM sidechain; XRPL↔external chains)
- `HE-ISSUANCE` (stablecoin issuer + XRPL + settlement pattern differs from EVM: no contract address; issuer *account* is the anchor — deployment identity must admit **issuer-account markers**, not only contracts)

## What breaks under EVM bias
- No smart contracts on core XRPL: an EVM-shaped dossier (Constitution §16 v0.1 flaw `[→MA-08]`) would force empty/meaningless "smart-contract model" slots while having no slots for trustlines, orderbooks, or UNLs.
- Issued assets are anchored to issuer accounts, not contracts — deployment identity needs `ISSUER_ACCOUNT` as a native marker variant; a contract-address-only identity model would misrepresent every issued asset.
- Native DEX: an ontology where DEX implies AMM/contract-pool would miss XRPL orderbooks entirely.
- No gas market: fee model is burn-based; EVM fee fields would be fabricated.
- The XRPL↔EVM sidechain: without strict object separation, an EVM-biased model would merge "XRPL" and "XRPL EVM sidechain" into one object.

## Ontology extension needed
- E-5: DeploymentIdentity.address must admit marker variants: `CONTRACT | NATIVE | ISSUER_ACCOUNT | PROGRAM | CANISTER | PACKAGE` (Solana/ICP need this too). **Amend 1A.6 schema — marker enum.**
- E-6: Trustline/issued-asset semantics need a family extension slot (already provided by §16.2/Bloc 1B family slots — confirm in matrix, no amendment if slots exist).

---

# P4 — SOLANA

## Required Book 1 objects
- `BLOCKCHAIN` + `ACCOUNT`, `SVM`, `MONOLITHIC`
- `VM` — SVM
- `TOKEN` — SOL (`NATIVE_TO`); SPL tokens via deployments (marker `PROGRAM`/mint)
- `PROTOCOL` — DEXs (AMM/CLMM), lending; all deployed via programs (marker variant per E-5)
- `VALIDATOR_SYSTEM` — stake economy, validators, delegation
- `STAKING_PROTOCOL` — LSTs (liquid staking tokens as TOKEN objects with `REDEEMS_FOR`)
- `APPLICATION`/`MARKET` — priority-fee/MEV marketplace objects (`SEQUENCER_INFRASTRUCTURE` analog: block-engine/JITO-style infra as MEV role tag)
- `RPC_INFRASTRUCTURE`, `INDEXING_INFRASTRUCTURE` — as objects for dependency edges

## Required edge types
- `NATIVE_TO` (SOL)
- `ISSUED_ON` (SPL mints)
- `VALIDATED_BY` (→ stake economy)
- `SECURED_BY` mechanism `POS`-with-delegation
- `STAKED_IN` (SOL→staking; LST receipts→)
- `RESTAKED_IN` — not natively (no EigenLayer analog at core) — a *negative* test: ontology must not force a restaking edge where none exists
- `DEPENDS_ON` (protocols→RPC/indexing infrastructure)
- `RUNS_ON` (programs→SVM)
- `ORACLE_FOR` / `DATA_FROM` (Pyth/Switchboard-native patterns)
- `WRAPS`/`REDEEMS_FOR` (LSTs, bridged assets)

## What breaks under EVM bias
- Programs are not contracts in the EVM sense (state lives in accounts, program logic is stateless) — a contract-address-only identity would misrepresent SPL mints vs program IDs; E-5 marker enum resolves.
- SPL token standard differs from ERC-20 (mint authority, freeze authority) — STANDARD objects must be family-specific.
- No native multi-chain deployment pattern via bridges-only: Solana-native issuance (e.g., wrapped BTC via specific programs) has program-level trust assumptions, not generic bridge assumptions.
- Priority fees/MEV marketplace: EVM-centric MEV classes (builders/relays) don't map 1:1; role tags must absorb family variation.

## Ontology extension needed
- E-7: `MEV_INFRASTRUCTURE` role tag must be family-parameterized (Ethereum builder/relay vs Solana block-engine). **Confirm role-tag registry wording — amend if ambiguous.**

---

# P5 — COSMOS

## Required Book 1 objects
- `BLOCKCHAIN` × N — each appchain (Cosmos Hub, Osmosis, …) is its own BLOCKCHAIN + `IBC_SOVEREIGN`, `ACCOUNT`, `COMETBFT`-family tags
- `STANDARD` — IBC protocol, ERC-20-equivalents (Cosmos SDK modules as family attribute)
- `INTEROP_PROTOCOL` — IBC itself (distinct object from any chain!)
- `TOKEN` — ATOM ≠ Cosmos Hub ≠ IBC ≠ Cosmos SDK (the IACER's own foundational example)
- `VALIDATOR_SYSTEM` — per-chain validator sets; provider/consumer for ICS
- `STAKING_PROTOCOL` — native staking per chain
- `BRIDGE`/`INTEROP_PROTOCOL` — non-IBC bridges (to Ethereum etc.) as separate objects
- `GOVERNANCE_SYSTEM` — per-chain onchain governance

## Required edge types
- `NATIVE_TO` (ATOM→Cosmos Hub; OSMO→Osmosis)
- `MESSAGES_TO` / `HE-BRIDGE-ROUTE` (IBC channels: chain↔chain via IBC — the canonical hyperedge case; pairwise flattening loses channel state/versions)
- `SECURED_BY` + `HE-SECURITY-SHARE` (ICS consumers→provider chain)
- `VALIDATED_BY` (per-chain)
- `STAKED_IN` (per-chain)
- `BRIDGES_TO` (non-IBC external bridges)
- `USES_STANDARD` (appchains→IBC, SDK modules)
- `COMPETES_WITH` (appchains competing for same liquidity — E2+ bar test)
- `GOVERNED_BY` (per-chain governance systems)

## What breaks under EVM bias
- "Cosmos" is a *family*, not a chain: an EVM-biased model where one chain = one ecosystem entry collapses hundreds of sovereign chains into one object. ATOM ≠ Cosmos Hub ≠ IBC ≠ SDK must survive (IACER A2).
- IBC is not a bridge in the lock-and-mint sense: a BRIDGE-only model loses light-client trust semantics; IBC must be INTEROP_PROTOCOL with MESSAGES_TO + hyperedge channels.
- Shared security (ICS) has no EVM analog at all — without SECURED_BY/HE-SECURITY-SHARE, consumer chains look like independent L1s.
- Each appchain has its own governance/fee token: an EVM "L1+gas token" template breaks for chains with fee abstraction/multiple fee tokens.

## Ontology extension needed
- E-8: `HE-BRIDGE-ROUTE` hyperedge must carry channel attributes (channel id, state, version) as family-parameterized attributes. **Amend hyperedge registry.**
- E-9: ICS shared-security needs `HE-SECURITY-SHARE` with `PROVIDER/CONSUMER/MECHANISM` roles — present in 1C.6 registry; **confirm, no amendment**.

---

# P6 — ICP (INTERNET COMPUTER)

## Required Book 1 objects
- `BLOCKCHAIN` (ICP) + role tags: `CANISTER_COMPUTE`, `ACTOR_MODEL`, `MONOLITHIC`-with-subnets (subnet composition is family attribute)
- `TOKEN` — ICP (`NATIVE_TO`, reverse-gas model)
- `GOVERNANCE_SYSTEM` — Network Nervous System (neurons, proposals) as first-class object
- `APPLICATION` — canisters as deployable computation objects (identity: canister IDs — marker variant `CANISTER` per E-5)
- `VALIDATOR_SYSTEM` — subnet node providers (per-subnet!)
- `STANDARD` — service-worker/HTTPS-outcalls/chain-key (threshold signatures) standards
- `STABLECOIN` — native-issued on ICP
- `RPC_INFRASTRUCTURE` analog — boundary nodes (family-specific infra object)

## Required edge types
- `NATIVE_TO` (ICP token)
- `VALIDATED_BY` (subnet→node-provider systems; *subnet-level*, not chain-level — a chain whose security is internally partitioned)
- `SECURED_BY` (mechanism `CHAIN_KEY`-threshold-BFT family)
- `GOVERNED_BY` (→NNS; onchain governance executing upgrades — governance evidence at E0)
- `ISSUED_ON` (canister-issued tokens; ck-variants: `WRAPS` chain-key tokens→BTC/ETH assets)
- `RUNS_ON` (applications→subnets — a RUNS_ON whose range is *sub-object* of a chain)
- `BRIDGES_TO` (chain-key integration to Bitcoin/Ethereum — trust-model hyperedge: `HE-BRIDGE-ROUTE` with threshold-crypto mechanism attribute)
- `DEPENDS_ON` (canisters→boundary nodes)

## What breaks under EVM bias
- Canisters are not contracts: they hold state+wasm, communicate via async messages, and pay for *compute* (reverse gas) — a contract-address model misrepresents canister identity and economics entirely.
- Subnets: ICP is internally many replicated blockchains; a single-chain model loses the actual security topology (application availability depends on subnet health).
- Governance executes upgrades on-chain via NNS: an ontology without executable GOVERNED_BY (governance as runtime authority) misses ICP's core mechanic.
- Chain-key bridging is threshold-signature-native, not lock-and-mint: BRIDGE model needs mechanism attribute (ties to E-1/E-8).
- No gas in the EVM sense: fee model family slot required.

## Ontology extension needed
- E-10: `RUNS_ON` range must admit family-scoped sub-objects (subnet, shard, partition) via a `chain_scope` attribute. **Amend edge dictionary RUNS_ON entry.**
- E-11: `HE-BRIDGE-ROUTE` mechanism attribute (covers chain-key; same amendment as E-8 generalized).

---

# P7 — DAG-FAMILY NETWORK (representative: blockDAG with probabilistic finality)

## Required Book 1 objects
- `BLOCKCHAIN` + role tags: `DAG`, `MONOLITHIC`
- `TOKEN` — native (`NATIVE_TO`)
- `VALIDATOR_SYSTEM` — per DAG-family validator economics
- `STANDARD` — DAG-native finality/confirmation standards
- `APPLICATION` — EVM-compatible DAG networks additionally carry `EVM` tag + `USES_VM` (a DAG chain can be EVM-executing — the tag model must compose)

## Required edge types
- `NATIVE_TO`
- `VALIDATED_BY` / `SECURED_BY` (mechanism family)
- `RUNS_ON` / `USES_VM` (for EVM-executing DAG chains — composition test)
- `BRIDGES_TO` / `MESSAGES_TO` (external interop)
- `ISSUED_ON` (assets)

## What breaks under EVM bias
- Ordering/consensus: DAG ordering is not linear-block; finality semantics are family-specific (probabilistic or declarative devices). An EVM model assumes linear finality language — temporal doctrine's finality-anchoring (ADV-1D-J) must admit family finality devices.
- An EVM-executing DAG would be collapsed into "just an EVM chain" — losing the consensus topology that is its distinguishing structural fact; conversely a DAG-only model would lose its EVM execution reality. The tag-composition model (BLOCKCHAIN + `DAG` + `EVM` + `USES_VM`) is precisely what must survive.
- Tip-selection/confirmation-depth metrics have no EVM analog — family slots required (§16.2).

## Ontology extension needed
- E-12: Finality-device family attribute registry (LINEAR_DETERMINISTIC | PROBABILISTIC | DECLARATIVE_DAG | BFT_INSTANT | OPTIMISTIC_ZK_ROLLUP etc.) — Book 3B populates; Book 1 must reserve the slot. **Amend Bloc 1B family-slot registry.**

---

# CROSS-CUTTING ANCHOR — USDC THROUGH ALL SEVEN

| System | Identity objects (1A) | Edges (1C) | Temporal case (1D) |
|---|---|---|---|
| Bitcoin | n/a (no native USDC) — absence is representable | none | absence ≠ unknown (Axiom 6) |
| Ethereum | canonical deployment (contract marker) | ISSUED_ON; HE-ISSUANCE | issuance valid_from exact |
| XRPL | ISSUER_ACCOUNT marker deployment | ISSUED_ON (trustline family slot) | trustline enablement precedes asset use |
| Solana | PROGRAM/mint marker deployment | ISSUED_ON; COLLATERAL_IN | native-issuance migration window |
| Cosmos | IBC-routed representation (via channels) | WRAPS→? (IBC vouchers: non-custodial channel semantics differ from WRAPS — **see E-13**) | channel open/close bounds edge validity |
| ICP | CANISTER marker (ckUSDC analog) | WRAPS / REDEEMS_FOR via chain-key | threshold-facility existence window |
| DAG/EVM | contract marker per EVM-DAG | ISSUED_ON | standard |

**E-13 (new finding):** IBC vouchers are neither `WRAPS` (custodial) nor plain `ISSUED_ON` canonical deployments — they are channel-bound representations. Either (a) a new deployment status `CHANNEL_REPRESENTATIVE`, or (b) `WRAPS` with mechanism attribute. **Requires operator decision R-1A-5; recorded as amendment candidate.**

---

# SUMMARY MATRIX

| Pilot | New objects needed? | New edges needed? | EVM-bias breakage | Amendments |
|---|---|---|---|---|
| Bitcoin | No | No | Native-marker identity, no-VM modeling, PoW mechanism | E-1, E-2 |
| Ethereum | No | No | Over-generalization guarded by other pilots | — |
| XRPL | No | No | Issuer-account identity, no-contract DEX, trustlines | E-5 |
| Solana | No | No | Program identity, family MEV | E-5, E-7 |
| Cosmos | No | No | Sovereign-chain multiplicity, IBC ≠ bridge, ICS | E-8 |
| ICP | No | No | Canister identity, subnets, executable governance | E-5, E-10, E-11 |
| DAG | No | No | Finality semantics, tag composition | E-12 |

**Verdict:** The Book 1 v0.1 ontology structure (primary class + role tags + family slots + marker-variant deployments + hyperedges + bitemporal fields) survives all seven pilots with **zero structural failures**. Twelve amendment candidates (E-1..E-13, minus confirmed-none) are required — all are extensions within the constitutional extension mechanism, none are architectural rework. E-13 requires an operator decision (R-1A-5).

---

# BLOCK 1 VALIDATION ROLE

This matrix is the evidence artifact that validates Book 1's exit gate: an ontology that cannot represent these seven systems without distortion is not the ontology the constitution demands.

End of pilot ontology stress matrix.
