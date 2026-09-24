# CSIA Book 3 — Native Architecture Pilot Matrix v0.1

**MODE = PLANNING ONLY**
**STATUS = DRAFT FOR OPERATOR REVIEW**
**EVIDENCE RULE = every populated fact requires a Book 2 claim family**

This matrix is a planning coverage test, not an implementation or live-data claim.
`UNKNOWN` means the pilot has not established the value; it is not `OTHER`.

## Bitcoin

1. Architecture family: Bitcoin / UTXO proof-of-work ledger.
2. State model: family-native UTXO set and transaction graph.
3. Execution model: Script validation and transaction processing.
4. Consensus model: proof of work and mining.
5. Finality model: probabilistic confirmation/confirmation depth.
6. DA model: full-node block and mempool propagation; precise availability claim requires evidence.
7. Settlement model: Bitcoin L1 UTXO settlement.
8. Participant/validator model: miners and validating full nodes; no validator-set abstraction imposed.
9. Governance model: network rules, node/software consensus, and social coordination; exact governance split requires evidence.
10. Upgrade model: soft fork and hard fork histories.
11. Interoperability model: native network plus Lightning and external bridge relations; distinct dossiers.
12. Sequencing model: block producer and transaction/block ordering; mempool policy is distinct from consensus.
13. Security model: proof-of-work hash power and consensus rules.
14. Native asset relationship: BTC economic asset versus UTXO realization; WBTC/cbBTC separate.
15. Network identity anchor: genesis hash and network namespace; chain ID is not assumed.
16. Book 1 nodes: ledger, transaction, block, UTXO, asset, network, fork/realization.
17. Book 1 edges: PRODUCES, CONSENSUS_ON, SETTLES, REALIZES, FORKS_TO, MESSAGES_TO.
18. Required extensions: UTXO state, Script execution, PoW/mining, mempool, probabilistic finality.
19. Book 2 evidence families: network identity, consensus, execution model, native asset, upgrade/fork.
20. Unresolved gaps: exact DA guarantee, Lightning dossier boundary, governance decomposition.

## Ethereum

1. Architecture family: Ethereum execution, consensus, settlement, and EVM layers.
2. State model: account and contract state.
3. Execution model: EVM execution.
4. Consensus model: Beacon consensus and PoS validator duties.
5. Finality model: protocol finality/justification and confirmation semantics; exact claim must be evidence-bound.
6. DA model: Ethereum data availability and blob availability; provider relationships explicit.
7. Settlement model: Ethereum L1 settlement.
8. Participant/validator model: Ethereum validators and execution clients.
9. Governance model: protocol governance and client/software coordination; exact entities require evidence.
10. Upgrade model: protocol upgrades, hard forks, and client releases.
11. Interoperability model: L2s, bridges, messaging, and external DA; not identity equivalence.
12. Sequencing model: L1 ordering and L2 sequencer relationships explicit.
13. Security model: validator consensus and L1 settlement security.
14. Native asset relationship: ETH economic asset, WETH, bridged ETH, L2 representations.
15. Network identity anchor: genesis/network namespace plus chain ID and deployment-specific anchors.
16. Book 1 nodes: network, execution layer, consensus layer, account, contract, transaction, asset, L2.
17. Book 1 edges: EXECUTES_WITH, SECURED_BY, SETTLES_TO, USES_DA, MESSAGES_TO, REALIZES.
18. Required extensions: layered component dossier, beacon consensus, blobs, rollup relations.
19. Book 2 evidence families: network identity, consensus, execution, upgrade, settlement, native asset, interoperability.
20. Unresolved gaps: finality wording, blob/DA provider boundaries, L2-specific identities.

## Base

1. Architecture family: OP Stack rollup ecosystem; not Ethereum L1 identity.
2. State model: rollup account/contract state.
3. Execution model: EVM-compatible rollup execution.
4. Consensus model: separate sequencer and Ethereum settlement/consensus relationship.
5. Finality model: settlement/finality inherited through the rollup stack, not assumed equal to L1 local confirmation.
6. DA model: OP Stack DA mode; Ethereum or external DA relation must be evidenced.
7. Settlement model: Ethereum settlement relationship explicit.
8. Participant/validator model: sequencer, rollup operators, and Ethereum validators/security providers.
9. Governance model: OP Stack/Base governance and upgrade authority; exact entities require evidence.
10. Upgrade model: software releases and network upgrades.
11. Interoperability model: bridges, canonical bridges, and L2 messaging.
12. Sequencing model: centralized or distributed sequencer relation explicit.
13. Security model: Ethereum settlement/security plus sequencer trust assumptions.
14. Native asset relationship: ETH/WETH and token representations; native versus bridged status explicit.
15. Network identity anchor: chain ID plus OP Stack deployment/genesis configuration; not Ethereum L1 solely.
16. Book 1 nodes: rollup, sequencer, settlement domain, DA domain, account, contract, bridge.
17. Book 1 edges: EXECUTES_WITH, SETTLES_TO, USES_DA, SECURED_BY, SEQUENCED_BY, BRIDGES_TO.
18. Required extensions: modular component dossier and sequencer/security distinction.
19. Book 2 evidence families: network identity, execution, settlement, DA, security, native asset, interoperability.
20. Unresolved gaps: operator governance and exact DA/finality claims.

## Arbitrum

1. Architecture family: Arbitrum Orbit rollup family.
2. State model: EVM-compatible account/contract state.
3. Execution model: Arbitrum execution stack.
4. Consensus model: separate sequencer and settlement domain.
5. Finality model: settlement/finality relationship explicit; no generic L2 finality assumption.
6. DA model: DA provider relation explicit, including Ethereum or external DA choices.
7. Settlement model: Arbitrum Orbit settlement target.
8. Participant/validator model: sequencer, batcher, proposer/validator roles, and settlement security.
9. Governance model: DAO/operator/upgrade authority requires evidence.
10. Upgrade model: contract, chain, and system upgrades distinct.
11. Interoperability model: bridge and L1/L2 messaging relationships.
12. Sequencing model: batch sequencing distinct from settlement.
13. Security model: settlement domain plus fraud-proof or validity-proof model explicit.
14. Native asset relationship: ETH/WETH and chain-specific token realizations.
15. Network identity anchor: chain ID and Orbit genesis/deployment configuration, not generic Arbitrum identity.
16. Book 1 nodes: rollup, batcher, prover/validator, settlement, DA, account, contract.
17. Book 1 edges: EXECUTES_WITH, SETTLES_TO, USES_DA, SECURED_BY, SEQUENCED_BY, BRIDGES_TO.
18. Required extensions: proof-system, batcher, and settlement-specific typed fields.
19. Book 2 evidence families: network identity, execution, settlement, security, DA, native asset.
20. Unresolved gaps: proof-system version and governance decomposition.

## XRPL

1. Architecture family: XRP Ledger family.
2. State model: ledger/account/trust-line model.
3. Execution model: XRPL transaction and offer-book semantics; no EVM requirement.
4. Consensus model: XRP Ledger consensus/UNL.
5. Finality model: ledger finality semantics; exact thresholds require evidence.
6. DA model: replicated ledger and historical full-node data retention; no DA-layer conflation.
7. Settlement model: XRPL ledger settlement.
8. Participant/validator model: UNL validators and network participants.
9. Governance model: amendments and validator governance.
10. Upgrade model: amendments and protocol amendments.
11. Interoperability model: payment paths, native DEX, gateways/bridges as explicit relations.
12. Sequencing model: ledger sequence and transaction ordering.
13. Security model: UNL consensus and amendment governance.
14. Native asset relationship: XRP native asset; issued assets and trust lines separate.
15. Network identity anchor: ledger genesis plus network namespace; chain ID not assumed.
16. Book 1 nodes: ledger, account, trust line, issued currency, offer, path, validator, amendment.
17. Book 1 edges: ISSUES, REALIZES, SETTLES, VOTES_ON, AMENDS, MESSAGES_TO.
18. Required extensions: trust-line, issuer, offer-book, ledger-sequence, and amendment types.
19. Book 2 evidence families: network identity, consensus, execution, native asset, upgrade, interoperability.
20. Unresolved gaps: exact operational governance and bridge realization boundaries.

## Solana

1. Architecture family: Solana account/program execution family.
2. State model: accounts and program-derived state.
3. Execution model: Solana runtime and parallel execution.
4. Consensus model: Tower BFT plus PoH-related ordering mechanism.
5. Finality model: Solana commitment/finality semantics; exact claim requires evidence.
6. DA model: validator replication and ledger retention; not automatically Ethereum blob DA.
7. Settlement model: Solana settlement domain.
8. Participant/validator model: validators and leader schedule.
9. Governance model: validator/authority and on-chain governance relations.
10. Upgrade model: cluster upgrades, feature gates, program deployment, upgrade authority.
11. Interoperability model: SPL assets and external messaging/bridges explicit.
12. Sequencing model: leader schedule and PoH ordering distinct from execution parallelism.
13. Security model: Tower BFT/PoH and validator security.
14. Native asset relationship: SOL and SPL assets distinct.
15. Network identity anchor: genesis plus cluster/network namespace and deployment configuration.
16. Book 1 nodes: account, program, derived account, validator, epoch, ledger, asset.
17. Book 1 edges: RUNS_ON, SECURED_BY, PRODUCES, REALIZES, UPGRADES, MESSAGES_TO.
18. Required extensions: account/program, parallel execution, leader schedule, compute-unit, and upgrade-authority types.
19. Book 2 evidence families: network identity, consensus, execution, upgrade, native asset, interoperability.
20. Unresolved gaps: exact DA and cross-chain relation classifications.

## Cosmos Hub

1. Architecture family: Cosmos Hub / Cosmos SDK application.
2. State model: application-specific store and modules.
3. Execution model: Cosmos SDK application execution.
4. Consensus model: CometBFT consensus.
5. Finality model: CometBFT finality semantics; exact evidence required.
6. DA model: validator-replicated state and data availability; not assumed identical to a DA layer.
7. Settlement model: Cosmos Hub settlement domain.
8. Participant/validator model: validator set and staking participants.
9. Governance model: Cosmos Hub governance and staking governance.
10. Upgrade model: coordinated chain upgrades and application upgrades.
11. Interoperability model: IBC clients, connections, channels, and relayers.
12. Sequencing model: CometBFT block ordering and application execution relation.
13. Security model: validator consensus and staking security.
14. Native asset relationship: ATOM native to the hub; IBC assets and representations distinct.
15. Network identity anchor: chain ID, genesis, and Cosmos namespace; SDK use alone is insufficient.
16. Book 1 nodes: chain, module, validator, IBC client/connection/channel, asset, governance proposal.
17. Book 1 edges: RUNS_ON, SECURED_BY, MESSAGES_TO, SETTLES, ISSUES, VOTES_ON.
18. Required extensions: module, IBC, staking, governance, and chain-upgrade types.
19. Book 2 evidence families: network identity, consensus, execution, governance, interoperability, native asset.
20. Unresolved gaps: relation between application state and validator data availability.

## Osmosis

1. Architecture family: Cosmos SDK/IBC application chain; not Cosmos Hub by default.
2. State model: application modules and IBC-aware state.
3. Execution model: Cosmos SDK application execution.
4. Consensus model: CometBFT or evidence-bound chain-specific consensus.
5. Finality model: chain-specific CometBFT/finality evidence.
6. DA model: validator replication; distinct from Celestia DA unless explicitly used.
7. Settlement model: Osmosis settlement domain.
8. Participant/validator model: independent validator set and staking roles.
9. Governance model: chain-specific governance and parameter changes.
10. Upgrade model: coordinated chain upgrades.
11. Interoperability model: IBC channels and Osmosis-specific modules.
12. Sequencing model: CometBFT ordering and application execution.
13. Security model: independent validator security unless shared security is evidenced.
14. Native asset relationship: OSMO native asset; IBC assets distinct.
15. Network identity anchor: chain ID and genesis; Cosmos SDK membership is not identity.
16. Book 1 nodes: chain, module, validator, IBC route, asset, governance.
17. Book 1 edges: RUNS_ON, SECURED_BY, MESSAGES_TO, SETTLES, ISSUES.
18. Required extensions: independent appchain and IBC-native fields.
19. Book 2 evidence families: network identity, consensus, execution, interoperability, native asset.
20. Unresolved gaps: exact module and governance decomposition.

## Celestia

1. Architecture family: modular data-availability network.
2. State model: DA-specific namespace/blob state; not account-chain substitution.
3. Execution model: DA sampling/availability execution distinct from rollup execution.
4. Consensus model: Celestia-specific consensus family.
5. Finality model: DA finality/availability semantics.
6. DA model: primary DA role.
7. Settlement model: no universal settlement role; dependent rollups may settle elsewhere.
8. Participant/validator model: DA validators and light nodes.
9. Governance model: Celestia governance/upgrade process.
10. Upgrade model: protocol/software upgrades.
11. Interoperability model: rollup namespace/DA relations, not generic bridge identity.
12. Sequencing model: DA-specific ordering and sampling relation.
13. Security model: DA security provider relation to dependent systems.
14. Native asset relationship: TIA native asset and DA-service realization distinct.
15. Network identity anchor: chain ID/genesis/deployment configuration and namespace.
16. Book 1 nodes: DA network, namespace, blob/data sample, validator, light node, dependent rollup.
17. Book 1 edges: USES_DA, SECURED_BY, MESSAGES_TO, SETTLES_TO where applicable.
18. Required extensions: DA-specific, namespace, sampling, and non-settlement semantics.
19. Book 2 evidence families: network identity, consensus, DA model, security, native asset.
20. Unresolved gaps: exact DA/settlement separation per deployment.

## Polkadot

1. Architecture family: Polkadot Relay Chain and parachain architecture.
2. State model: relay-chain state plus parachain-specific state.
3. Execution model: Substrate/Wasm runtime and relay execution.
4. Consensus model: relay-chain consensus family; parachain consensus is scoped separately.
5. Finality model: relay and parachain finality relation explicit.
6. DA model: relay/parachain availability relation; not assumed one universal DA layer.
7. Settlement model: Relay Chain settlement/security relationship.
8. Participant/validator model: relay validators, nominators, collators.
9. Governance model: relay governance and runtime governance relations.
10. Upgrade model: runtime upgrades and coordinated network upgrades.
11. Interoperability model: XCM channels/messages and bridges.
12. Sequencing model: relay block sequencing and parachain relation.
13. Security model: shared security versus independent security must be explicit.
14. Native asset relationship: DOT native relay asset; parachain assets distinct.
15. Network identity anchor: genesis/spec identity plus parachain genesis/chain identity.
16. Book 1 nodes: relay, parachain, runtime, validator, nominator, collator, XCM message, asset.
17. Book 1 edges: SECURED_BY, SETTLES_TO, MESSAGES_TO, RUNS_ON, UPGRADES.
18. Required extensions: shared security, XCM, collator, runtime, and parachain types.
19. Book 2 evidence families: network identity, consensus, security, interoperability, upgrade, native asset.
20. Unresolved gaps: parachain-specific security and settlement evidence.

## Standalone Substrate chain

1. Architecture family: standalone Substrate chain, not automatically a Polkadot parachain.
2. State model: Substrate runtime storage.
3. Execution model: Substrate/Wasm runtime.
4. Consensus model: chain-specific babe/grandpa or other evidence-bound configuration.
5. Finality model: chain-specific finality configuration.
6. DA model: chain-specific node replication.
7. Settlement model: standalone settlement domain.
8. Participant/validator model: validator/nominator set.
9. Governance model: runtime/governance configuration.
10. Upgrade model: runtime upgrades.
11. Interoperability model: XCM only if enabled/evidenced.
12. Sequencing model: chain-specific block/transaction ordering.
13. Security model: independent security unless explicitly shared.
14. Native asset relationship: native asset is chain-specific.
15. Network identity anchor: chain spec/genesis and network namespace.
16. Book 1 nodes: standalone chain, runtime, validator, block, asset.
17. Book 1 edges: RUNS_ON, SECURED_BY, UPGRADES, MESSAGES_TO.
18. Required extensions: explicit standalone vs parachain security distinction.
19. Book 2 evidence families: network identity, consensus, execution, upgrade, native asset.
20. Unresolved gaps: exact runtime and consensus configuration.

## Avalanche

1. Architecture family: Avalanche Primary Network with P-Chain, C-Chain, and X-Chain.
2. State model: chain-specific state ledgers.
3. Execution model: P-Chain/C-Chain/X-Chain execution differences.
4. Consensus model: Snow-family consensus mechanisms.
5. Finality model: chain/subnet-specific finality.
6. DA model: validator replication and subnet-specific data availability.
7. Settlement model: Primary Network/subnet relations; C-Chain is not whole Avalanche.
8. Participant/validator model: Primary Network validators and subnet validator relations.
9. Governance model: Avalanche governance and subnet governance.
10. Upgrade model: Avalanche upgrades and subnet upgrades.
11. Interoperability model: cross-chain/subnet messaging.
12. Sequencing model: Snowman/P-Chain/C-Chain/X-Chain ordering relations.
13. Security model: validator/subnet security model.
14. Native asset relationship: AVAX native asset and chain/subnet realizations.
15. Network identity anchor: Primary Network/subnet identity and genesis/config.
16. Book 1 nodes: Primary Network, P-Chain, C-Chain, X-Chain, subnet, validator, asset.
17. Book 1 edges: SECURED_BY, MESSAGES_TO, SETTLES_TO, REALIZES, PRODUCES.
18. Required extensions: multi-chain/subnet and Snow consensus types.
19. Book 2 evidence families: network identity, consensus, execution, security, native asset, interoperability.
20. Unresolved gaps: current subnet terminology and chain-specific finality evidence.

## ICP

1. Architecture family: Internet Computer canister/subnet family.
2. State model: canister state and subnet replica state.
3. Execution model: Wasm/canister execution.
4. Consensus model: ICP consensus family; exact subnet mechanics require evidence.
5. Finality model: subnet finality semantics.
6. DA model: replicated subnet state and replica availability; not assumed generic shard DA.
7. Settlement model: subnet/network settlement relation.
8. Participant/validator model: replicas and subnet nodes.
9. Governance model: NNS and subnet governance.
10. Upgrade model: canister and subnet governance upgrades.
11. Interoperability model: canister/message and cross-subnet relations.
12. Sequencing model: subnet ingress and consensus ordering.
13. Security model: threshold/replica security model.
14. Native asset relationship: ICP native asset and cycles distinct.
15. Network identity anchor: network/subnet identity plus deployment configuration.
16. Book 1 nodes: network, subnet, canister, replica, message, cycle, NNS proposal.
17. Book 1 edges: RUNS_ON, SECURED_BY, MESSAGES_TO, UPGRADES, FUNDS.
18. Required extensions: canister, replica, subnet, cycles, and Wasm types.
19. Book 2 evidence families: network identity, execution, consensus, governance, upgrade, native asset.
20. Unresolved gaps: exact finality and cross-subnet evidence.

## Hedera

1. Architecture family: Hedera hashgraph family.
2. State model: account/token/contract or native service state as applicable.
3. Execution model: Hedera services and EVM-compatible execution where enabled.
4. Consensus model: hashgraph-style consensus family.
5. Finality model: Hedera consensus finality semantics.
6. DA model: consensus-node replication and service-specific storage.
7. Settlement model: Hedera network settlement.
8. Participant/validator model: consensus nodes and permissioned network roles.
9. Governance model: Hedera council/governance relations.
10. Upgrade model: network/service upgrades.
11. Interoperability model: mirrors, tokens, and external bridges/messages.
12. Ordering model: hashgraph ordering/consensus, distinct from linear blocks.
13. Security model: Hedera consensus-node security model.
14. Native asset relationship: HBAR and service-specific assets distinct.
15. Network identity anchor: network/mainnet/testnet identity and configuration; chain ID not universal.
16. Book 1 nodes: network, consensus node, account, token, service, asset.
17. Book 1 edges: SECURED_BY, PRODUCES, REALIZES, MESSAGES_TO, ISSUES.
18. Required extensions: hashgraph, service, permissioned node, and EVM-optional fields.
19. Book 2 evidence families: network identity, consensus, execution, governance, native asset.
20. Unresolved gaps: exact service and network identity boundaries.

## Sui

1. Architecture family: Move/object-centric Sui family.
2. State model: object-centric owned/shared/immutable objects and resources.
3. Execution model: Move VM and object execution.
4. Consensus model: Sui family consensus.
5. Finality model: Sui finality/commit semantics.
6. DA model: validator replication; exact DA characterization requires evidence.
7. Settlement model: Sui network settlement.
8. Participant/validator model: validators and committee.
9. Governance model: Sui governance and upgrade authority.
10. Upgrade model: protocol/package upgrades.
11. Interoperability model: Move packages and cross-chain messaging distinct.
12. Sequencing model: consensus ordering and object execution relation.
13. Security model: validator consensus and Move execution safety.
14. Native asset relationship: SUI native asset and Move coin/object representations.
15. Network identity anchor: genesis/network namespace and chain configuration.
16. Book 1 nodes: object, owner, Move package, module, transaction, validator, asset.
17. Book 1 edges: RUNS_ON, SECURED_BY, REALIZES, UPGRADES, MESSAGES_TO.
18. Required extensions: object/resource, Move package/module, and object-centric state types.
19. Book 2 evidence families: network identity, execution, consensus, upgrade, native asset.
20. Unresolved gaps: exact finality and DA semantics.

## Aptos

1. Architecture family: Move/account/resource-centric Aptos family.
2. State model: accounts, resources, and object-store state.
3. Execution model: Aptos VM/Move execution.
4. Consensus model: Aptos family consensus.
5. Finality model: Aptos finality/commit semantics.
6. DA model: validator replication; exact characterization requires evidence.
7. Settlement model: Aptos network settlement.
8. Participant/validator model: validator set and committee.
9. Governance model: Aptos governance and upgrade authority.
10. Upgrade model: protocol/module upgrades.
11. Interoperability model: Move packages and cross-chain messaging distinct.
12. Sequencing model: consensus ordering and transaction execution.
13. Security model: validator consensus and Move execution safety.
14. Native asset relationship: APT native asset and Move resource/token representations.
15. Network identity anchor: genesis/network namespace and chain configuration.
16. Book 1 nodes: account, resource, Move package, module, transaction, validator, asset.
17. Book 1 edges: RUNS_ON, SECURED_BY, REALIZES, UPGRADES, MESSAGES_TO.
18. Required extensions: account/resource, Move package/module, and Aptos-specific state types.
19. Book 2 evidence families: network identity, execution, consensus, upgrade, native asset.
20. Unresolved gaps: exact finality and DA semantics.

## NEAR

1. Architecture family: NEAR sharded account/runtime family.
2. State model: accounts, contracts, and shard state.
3. Execution model: NEAR runtime/WASM execution.
4. Model consensus/finality: NEAR consensus and finality semantics require family-native evidence.
5. DA model: shard/replica replication; not assumed identical to a modular DA layer.
6. Settlement model: NEAR network settlement.
7. Participant/validator model: validators and shard assignment.
8. Governance model: NEAR governance and protocol upgrade relations.
9. Upgrade model: runtime/protocol upgrades.
10. Interoperability model: native messaging and external bridges distinct.
11. Sequencing/model: shard sequencing and consensus ordering.
12. Security model: validator and threshold security relations.
13. Native asset relationship: NEAR native asset and token/NFT realizations.
14. Network identity anchor: network namespace, genesis, and deployment configuration.
15. Book 1 nodes: network, shard, account, contract, validator, asset.
16. Book 1 edges: RUNS_ON, SECURED_BY, MESSAGES_TO, SETTLES, UPGRADES.
17. Book 1 nodes/edges: duplicate-safe; no EVM account/contract assumption.
18. Required extensions: shard, WASM contract, and threshold/finality fields.
19. Book 2 evidence families: network identity, execution, consensus, upgrade, native asset, interoperability.
20. Unresolved gaps: exact shard/security and finality semantics.

## Pilot conclusion

The pilot set is representable without an EVM-centered universal model. Bitcoin,
XRPL, Solana, Cosmos, Substrate, Avalanche, ICP, Move, Hedera, DAG-capable systems,
and modular stacks retain native mechanisms while sharing only deliberately scoped
Book 1 nodes, Book 1 edges, and Book 2 evidence claims.
