# CSIA Book 3 — Native Chain / Ledger Atlas Plan v0.1

**BOOK = 3**
**MODE = PLANNING ONLY**
**STATUS = DRAFT FOR OPERATOR REVIEW**
**BOOK_1 = FROZEN_ACCEPTED**
**BOOK_2 = FROZEN_ACCEPTED**

## Authorized reconciliation directive — 2026-09-24

This v0.1 file is preserved and narrowly corrected, not regenerated, for the v0.2
ratification pass. Shared history is ancestry evidence, not by itself evidence of
same current network identity. The authorized D3-1 branch-sensitive rule and exact
Book 1 relationship classification are stated below and are carried forward into
plan v0.2; the binding decision record is the operator decision log.

## Purpose

Book 3 defines how CSIA represents the actual native architecture of blockchain and
ledger systems without forcing any family into a universal account, contract, block,
validator, or EVM model. It adds no source code and grants no implementation or live
acquisition authority.

## Core doctrine

The taxonomy adapts to the blockchain architecture. The blockchain is never forced
into the taxonomy.

### Planning principles

- **B3-P1 TOKEN != CHAIN.** An asset is not a network, ledger, execution environment,
  or security domain.
- **B3-P2 CHAIN != EXECUTION ENVIRONMENT.** A network may delegate execution,
  sequencing, settlement, or data availability to distinct components.
- **B3-P3 SHARED TOOLING != SHARED CHAIN IDENTITY.** SDKs, VMs, and libraries do not
  establish network identity or shared history.
- **B3-P4 SHARED SECURITY != SHARED EXECUTION.** Security providers and execution
  domains are separate relationships.
- **B3-P5 INTEROPERABILITY != SHARED SECURITY.** Messaging or bridging does not imply
  common validators, settlement, or governance.
- **B3-P6 EVM COMPATIBILITY != ETHEREUM SETTLEMENT.** EVM-compatible execution can
  settle elsewhere or operate on a distinct network.
- **B3-P7 NATIVE ASSET != CHAIN-LOCAL REALIZATION.** Economic asset identity and its
  representation on each ledger remain separate.
- **B3-P8 CONSENSUS != FINALITY.** Agreement mechanics and the strength/timing of
  irreversibility are distinct observations.
- **B3-P9 EXECUTION != SETTLEMENT.** Execution success does not imply settlement on
  the executing domain.
- **B3-P10 DATA AVAILABILITY != EXECUTION.** DA publication, storage, and execution
  are separate capabilities and trust relationships.
- **B3-P11 UNKNOWN != OTHER.** Unknown family-native values remain explicit unknowns,
  never a garbage-bucket classification.
- **B3-P12 FAMILY-NATIVE SEMANTICS TAKE PRECEDENCE OVER UNIVERSAL TAXONOMY.** Shared
  vocabulary may be used only where it preserves native distinctions.

## Bloc 3A — Native chain dossier envelope

Every architecture dossier has a stable `object_id`, `canonical_name`,
`architecture_family`, `network_namespace`, `network_identity_anchor`, and
`genesis_or_origin_anchor`. It also carries family-native typed references for:

- `native_asset_refs`
- `execution_model`
- `state_model`
- `consensus_model`
- `finality_model`
- `data_availability_model`
- `settlement_model`
- `validator_or_participant_model`
- `governance_model`
- `fee_model`
- `upgrade_model`
- `interoperability_model`
- `deployment_model`
- `security_model`
- `sequencing_model`
- `source_claim_refs`
- `valid_time`
- `observed_time`

The envelope is a claim-bearing dossier, not a universal object schema. A family may
add typed structures and may leave a mechanism explicitly `UNKNOWN` when the
architecture does not expose that mechanism. Examples: Bitcoin state is UTXO;
Ethereum state is account/contract state; XRPL uses ledger/account/trust-line
structures; Solana uses accounts/programs; DAG systems use events, partial order,
and convergence rather than invented block height.

Every populated field is a Book 2 claim. The dossier is promotable only when its
claims are canonical, evidenced, and temporally valid under the accepted Book 2
kernel.

## Bloc 3B — Family slot registries

Book 3 resolves the deferred Book 1 family-extension registry as a set of small,
namespaced, temporal registries:

- `EXECUTION_MODEL`
- `STATE_MODEL`
- `CONSENSUS_MODEL`
- `FINALITY_MODEL`
- `DA_MODEL`
- `SETTLEMENT_MODEL`
- `VALIDATOR_MODEL`
- `PARTICIPANT_MODEL`
- `GOVERNANCE_MODEL`
- `FEE_MODEL`
- `UPGRADE_MODEL`
- `INTEROP_MODEL`
- `DEPLOYMENT_MODEL`
- `SEQUENCING_MODEL`
- `SECURITY_MODEL`

Each registry value has a stable identifier, architecture-family owner, temporal
validity, evidence binding, and an explicit `UNKNOWN` representation when needed.
Values are never silently reclassified. Historical values remain queryable after a
fork, upgrade, migration, or shutdown. Book 3 does not create a giant universal enum.

Illustrative identifiers are `bitcoin:state:utxo`, `ethereum:execution:evm`,
`xrpl:consensus:unl-based`, `solana:execution:sealevel`,
`cosmos:consensus:cometbft`, and `polkadot:security:relay-shared-security`.

Registry admission is an operator-governed planning decision. A new family value is
not admitted merely because a vendor calls it a chain, EVM, validator, or protocol.

## Bloc 3C — Bitcoin family

Plan native representation of UTXO, Script, proof of work, mining, difficulty
adjustment, mempool, block production, probabilistic confirmation/finality, native
BTC, network rules, soft forks, hard forks, and UTXO settlement.

Keep separate: the Bitcoin network, BTC economic asset, BTC chain-local realization,
Lightning Network, Lightning channels, and wrapped BTC on other systems. Bitcoin is
not modeled as an account chain, smart-contract platform, or validator-based PoS
network.

## Bloc 3D — Ethereum / EVM family

Represent separately: Ethereum network, execution layer, consensus layer, EVM,
validator set, Beacon consensus, accounts, contracts, gas, blobs/data availability,
L1 settlement, rollups, L2 execution, sequencers, shared settlement, shared DA, OP
Stack, Arbitrum Orbit, and zk-rollup stacks.

EVM compatibility is an execution-family relation, not Ethereum identity. Base is
not Ethereum L1; Arbitrum is not a generic EVM chain; BNB Chain is not Ethereum.
Settlement relationships must be explicit and evidence-backed.

## Bloc 3E — XRPL family

Represent ledger sequence, accounts, trust lines, issued currencies, native XRP,
XRPL consensus/UNL, validators, amendments, native DEX, offer books, payment paths,
issuer/account realization, and reserve mechanics.

Do not require EVM contract semantics. XRP, XRPL, issued assets, issuers, and
trust-line realizations remain distinct.

## Bloc 3F — Solana family

Represent accounts, programs, program-derived accounts, runtime, Sealevel,
validators, epochs, leader schedule, Tower BFT, PoH-related ordering, parallel
execution, SPL assets, program deployment, upgrade authority, fee payer, and compute
units. A program is not an EVM contract; an account is not automatically an Ethereum
account.

## Bloc 3G — Cosmos family

Separate Cosmos SDK, CometBFT, IBC, Cosmos Hub, zones, appchains, modules, validator
sets, governance, IBC clients/connections/channels, relayers, and shared or
replicated security where applicable.

ATOM is not the Cosmos ecosystem; Cosmos SDK use is not Cosmos Hub membership; IBC
connectivity is not shared security; appchain identity remains independent.

## Bloc 3H — Polkadot / Substrate family

Separate Polkadot Relay Chain, parachains, historical parathreads where applicable,
Substrate, runtime, FRAME, validators, nominators, collators, shared security, XCM,
runtime upgrades, and relay settlement/security relationships.

Substrate chain does not automatically mean Polkadot parachain. Shared runtime
tooling does not establish network identity.

## Bloc 3I — Avalanche family

Represent Primary Network, P-Chain, C-Chain, X-Chain, subnets and L1 evolution
terminology, validator relationships, Snow-family consensus mechanisms, native AVAX,
chain-specific execution models, and cross-chain relations. Avalanche cannot be
reduced to C-Chain.

## Bloc 3J — Move family

Plan Sui and Aptos without assuming identical architecture. Represent the Move VM
family relationship, object-centric versus account/resource-centric differences,
execution, consensus, finality, validator sets, package/module deployment, and
asset/resource/object semantics. Shared language does not imply shared architecture.

## Bloc 3K — ICP / canister family

Represent subnets, canisters, replicas, NNS, chain-key concepts where relevant,
Wasm execution, cycles, canister deployment, subnet assignment, governance, and
upgrades. A canister is not an EVM contract. A subnet is not an ordinary shard
without evidence.

## Bloc 3L — DAG / non-linear ledger families

Represent event/order identity, partial ordering, consensus ordering, state
convergence, participant model, and finality semantics for DAG, hashgraph-like, and
block-lattice systems. Linear block height is not fabricated when it is not canonical.

## Bloc 3M — Modular / rollup / appchain systems

Represent decomposition across execution, sequencing, settlement, consensus, data
availability, and security. Reuse faithful Book 1 `SETTLES_TO`, `SECURED_BY`,
`BRIDGES_TO`, and `MESSAGES_TO` edges. Plan Book 3-local typed relations
`EXECUTES_WITH`, `USES_DA`, and `SEQUENCED_BY`; do not alias them to
`DEPENDS_ON` and do not mutate Book 1.

A rollup may execute locally, settle to Ethereum, use Celestia DA, use a centralized
sequencer, and bridge through a separate protocol. The representation must not
pretend these are one monolithic chain.

## Bloc 3N — Native asset / realization binding

Use Book 1 REALIZATION doctrine. Economic asset identity remains canonical while
chain-local realization remains explicit. Plan exact treatment for BTC, WBTC, cbBTC;
ETH, WETH, bridged ETH; native Ethereum USDC, native Base USDC, USDC.e, and other
bridged realizations; native XRP; native ATOM; and native DOT. Wrapped, bridged, and
issued variants remain explicit, with migration lineage preserved historically.

## Bloc 3O — Network identity / genesis / fork doctrine

Do not assume one universal identity anchor. Plan anchors including genesis hash,
chain ID, network ID, ledger genesis, protocol namespace, first canonical block,
validator-set origin, and deployment-specific identifier for mainnet, testnet,
devnet, forks, restarts, migrations, renamed networks, new genesis, state migration,
and consensus forks.

The planning distinction is between `SAME_NETWORK_CONTINUATION` and
`NEW_NETWORK_IDENTITY`. Shared history establishes ancestry but does not by itself
establish the same current network identity. A non-branching protocol upgrade with
one continuing canonical network, state continuity, deployment continuity, and no
persistent independent branch is `SAME_OBJECT` plus `HISTORICAL_CONTINUATION`.
Persistent independent consensus/state branches are separate `NEW_OBJECT`s, each
linked by `FORKED_FROM` to the shared ancestor with pre-fork history preserved. A
temporary or ambiguous split remains `UNKNOWN` until evidence resolves it. D3-1,
D3-2, and D3-5 supply the authorized decision basis; no identity is inferred from
a name or ticker.

## Bloc 3P — Shared security

Represent shared validator security, restaked security, relay-chain security,
replicated security, rollup settlement security, and external security providers.
`SECURED_BY` is not `RUNS_ON`, `SETTLES_TO`, `USES_DA`, or `MESSAGES_TO`.

## Bloc 3Q — Architecture change history

Plan temporal transitions for hard forks, soft forks, runtime upgrades, consensus and
VM changes, execution-model changes, DA migration, settlement migration, sequencer
decentralization, validator-model changes, governance changes, network restart,
shutdown, and L1-to-L2 migration. Architecture history remains queryable; old truth
is not rewritten.

## Evidence and Book 1 boundary

No Book 3 fact bypasses Book 2. The architecture evidence matrix defines preferred
evidence for network identity, consensus, execution, upgrades, interoperability, and
native assets. Accepted Book 1 already supports `RUNS_ON`, `USES_VM`,
`SETTLES_TO`, `SECURED_BY`, `BRIDGES_TO`, `MESSAGES_TO`, `FORKED_FROM`,
`MIGRATED_FROM`, `MIGRATED_TO`, and `REALIZES`; Book 3 reuses them only faithfully.
`EXECUTES_WITH`, `USES_DA`, and `SEQUENCED_BY` are Book 3-local relation-extension
candidates. Book 1 remains frozen and receives no mutation.

## Governance decisions authorized for v0.2

1. D3-1 — branch-sensitive fork identity: shared history is ancestry evidence,
   while current identity requires canonical, state, deployment, and branch-survival
   analysis.
2. D3-2 — conservative new-genesis restart default.
3. D3-3 — typed modular component dossiers.
4. D3-4 — typed `SECURED_BY` shared-security doctrine.
5. D3-5 — family-native network identity evidence bundle.
6. D3-6 — two-tier family registry admission.
7. D3-7 — typed migration with preserved historical objects.

These outcomes are authorized for Book 3 planning and are recorded canonically in
`CSIA_OPERATOR_DECISION_LOG.md`; plan v0.2 carries the complete consequences and
invariants. This reconciliation does not authorize implementation.
