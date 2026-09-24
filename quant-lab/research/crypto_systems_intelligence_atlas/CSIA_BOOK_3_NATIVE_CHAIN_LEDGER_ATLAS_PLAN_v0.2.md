# CSIA Book 3 — Native Chain / Ledger Atlas Plan v0.2

**BOOK = 3**
**PLAN_VERSION = v0.2**
**MODE = PLANNING ONLY**
**STATUS = OPERATOR DECISIONS CLOSED / READY FOR RATIFICATION**
**BOOK_1 = FROZEN_ACCEPTED**
**BOOK_2 = FROZEN_ACCEPTED**
**BOOK_3_IMPLEMENTATION_AUTHORITY = FALSE**
**LIVE_ACQUISITION_AUTHORITY = FALSE**

## 1. Purpose and authority boundary

Book 3 defines how CSIA represents native blockchain and ledger architecture
without forcing any family into an account, contract, block, validator, EVM, or
monolithic trust-domain model. It is a planning contract for later offline design.

This version reconciles only the two blocking seams identified after v0.1:

1. branch-sensitive fork and network identity;
2. exact support classification for Book 3 relationship semantics.

It does not implement Book 3, acquire live data, call RPC endpoints, create
collectors or databases, mutate Book 1, or mutate Book 2.

## 2. Governing planning principles

- **B3-P1 TOKEN != CHAIN.** Economic assets, network identities, ledgers,
  execution environments, and security domains remain distinct.
- **B3-P2 CHAIN != EXECUTION ENVIRONMENT.** Execution, sequencing, settlement,
  consensus, data availability, and security may be distinct components.
- **B3-P3 SHARED TOOLING != SHARED IDENTITY.** SDK, VM, library, or standards use
  does not establish network identity.
- **B3-P4 SHARED SECURITY != SHARED EXECUTION.** Security-provider relations
  remain separate from execution and settlement.
- **B3-P5 INTEROPERABILITY != SHARED SECURITY.** Messaging and bridging do not
  imply common validators, settlement, governance, or identity.
- **B3-P6 EVM COMPATIBILITY != ETHEREUM SETTLEMENT.** EVM compatibility is an
  execution-family fact, not network identity or settlement identity.
- **B3-P7 NATIVE ASSET != REALIZATION.** Economic asset identity and chain-local
  realization remain separate and retain `REALIZES` lineage.
- **B3-P8 CONSENSUS != FINALITY.** Agreement and irreversibility are separate,
  evidence-backed claims.
- **B3-P9 EXECUTION != SETTLEMENT.** Successful execution does not imply
  settlement on the executing domain.
- **B3-P10 DATA AVAILABILITY != EXECUTION.** Publication, storage, sampling,
  retention, and execution are separate capabilities.
- **B3-P11 UNKNOWN != OTHER.** Unresolved identity and architecture facts remain
  explicit `UNKNOWN` or `CONTESTED` claims.
- **B3-P12 FAMILY-NATIVE SEMANTICS TAKE PRECEDENCE.** Shared vocabulary is used
  only where it preserves native distinctions.

## 3. Corrected fork and network identity doctrine

**Shared history establishes ancestry. Shared history does not by itself establish
the same current network identity.**

### 3.1 Non-branching protocol upgrade

If one canonical network continues, state continuity remains, deployment/network
continuity remains, and no persistent independent branch survives, classify the
network as:

- `SAME_OBJECT`; and
- `HISTORICAL_CONTINUATION`.

The upgrade is a temporal architecture-history event. Shared history supports
ancestry, while canonical, state, deployment, and branch-survival evidence support
current identity.

### 3.2 Persistent divergent fork

If separate canonical branches persist with separate consensus histories, state
histories, and miner/validator/participant authority, classify each divergent
current network identity as `NEW_OBJECT` as appropriate. Preserve:

- `FORKED_FROM` to the shared ancestor or origin;
- shared ancestry; and
- pre-fork history.

A persistent branch must never collapse into the other branch merely because they
share history.

### 3.3 Temporary or ambiguous split

If persistent identity cannot yet be determined from the Book 2 evidence bundle,
classification remains `UNKNOWN`. Conflicting supported claims remain
`UNKNOWN / CONTESTED`. CSIA must not fabricate continuity or new-object status.

### 3.4 New-genesis restart

New genesis is `NEW_OBJECT` by default. Reused name, ticker, operator, branding,
namespace, or chain ID does not by itself defeat the conservative default. A claimed
family-native continuation exception must be surfaced for operator review with an
evidence-backed identity bundle; it cannot be silently admitted.

## 4. Network identity evidence bundle

No universal single identity anchor exists. D3-5 adopts a family-native evidence
bundle that may include:

- genesis or origin;
- chain/network ID;
- namespace;
- deployment ID or deployment manifest;
- state-history continuity;
- consensus continuity; and
- other family-native stable identifiers.

Binding rules:

- ticker is never sufficient;
- name is never sufficient;
- chain ID is never universal;
- genesis is strong evidence but not universally sufficient;
- every identity claim remains bound to accepted Book 2 canonical evidence;
- unresolved evidence conflict remains `UNKNOWN / CONTESTED`.

## 5. Exact Book 1 relationship support

The accepted Book 1 `EdgeType` contract already supports the following semantics.
Book 3 reuses them faithfully and does not report them as missing:

- `RUNS_ON`
- `USES_VM`
- `SETTLES_TO`
- `SECURED_BY`
- `BRIDGES_TO`
- `MESSAGES_TO`
- `FORKED_FROM`
- `MIGRATED_FROM`
- `MIGRATED_TO`
- `REALIZES`

The following Book 3 architecture semantics have no exact accepted Book 1 edge:

- `EXECUTES_WITH`
- `USES_DA`
- `SEQUENCED_BY`

They are `BOOK3_RELATION_EXTENSION_CANDIDATE` semantics. Book 3 may own typed local
architecture relations for them. They must not be added to Book 1 by this plan,
aliased to `DEPENDS_ON`, or weakened until a separately authorized future
amendment process.

`BOOK_1_MUTATION = NONE`.

## 6. Architecture dossier and temporal model

Each architecture dossier carries a stable object identity, canonical label,
architecture family, network namespace, family-native identity evidence refs,
native asset refs, and typed references for execution, state, consensus, finality,
DA, settlement, validator/participant, governance, fee, upgrade, interoperability,
deployment, security, and sequencing.

Every populated field is a Book 2 claim with evidence, authority resolution, valid
time, and observed time. Historical values remain queryable after upgrades,
forks, migrations, relationship changes, or shutdown. A missing mechanism is
explicitly `UNKNOWN`; it is not forced into a universal model.

## 7. Family registries and two-tier admission

Book 3 planning reserves namespaced, temporal registries for execution, state,
consensus, finality, DA, settlement, validator, participant, governance, fee,
upgrade, interoperability, deployment, sequencing, and security values.

D3-6 adopts two-tier admission:

1. **New registry family or semantic namespace:** explicit operator approval.
2. **New value in an already-ratified registry:** evidence-based admission is
   permitted only when canonical Book 2 evidence exists, a namespaced stable ID
   exists, temporal validity is recorded, provenance is retained, and no semantic
   collision exists.

Escalation to the operator is mandatory for semantic collision, family ambiguity,
taxonomy drift, a mechanism outside the ratified namespace, or any attempted
universal fallback. Vendor naming alone is insufficient.

## 8. Modular component identity

Execution, sequencing, settlement, DA, security, consensus, and bridge/messaging
roles may be represented by distinct typed component dossiers. A modular stack is
not forced into one monolithic object or trust domain.

`SETTLES_TO`, `SECURED_BY`, `BRIDGES_TO`, and `MESSAGES_TO` remain faithful Book 1
projections where applicable. `EXECUTES_WITH`, `USES_DA`, and `SEQUENCED_BY` remain
typed Book 3-local relations. Shared security is represented by `SECURED_BY` and
remains distinct from `RUNS_ON`, `SETTLES_TO`, `USES_DA`, and `MESSAGES_TO`.

## 9. Migration and historical continuity

State or deployment migration preserves both source and destination identity,
`MIGRATED_FROM` / `MIGRATED_TO` lineage, valid-time history, migration evidence,
and asset `REALIZES` lineage. `SUPERSESSION` and historical status are temporal
claims. The source object is never overwritten into the destination.

## 10. Bloc scope

### Bloc 3A — Native chain dossier envelope

Define the claim-bearing, family-native dossier and explicit unknown handling.
Bind every field to Book 2.

### Bloc 3B — Family slot registries

Use namespaced temporal registries and D3-6 two-tier admission. Vendor naming is
not authority.

### Bloc 3C — Bitcoin family

Represent UTXO, Script, proof of work, mining, mempool, probabilistic finality,
soft/hard fork history, native BTC, Lightning, and chain-local asset realizations
without an account/EVM model.

### Bloc 3D — Ethereum / EVM family

Separate Ethereum execution, consensus, EVM, validator, blob/DA, settlement,
rollup execution, sequencer, bridge, and asset realization concerns. EVM
compatibility never implies Ethereum L1 identity.

### Bloc 3E — XRPL family

Represent ledger sequence, accounts, trust lines, issued currencies, XRP, UNL,
amendments, DEX/order-book semantics, payment paths, and issuer/account
realizations without mandatory EVM semantics.

### Bloc 3F — Solana family

Represent accounts, programs, runtime, Sealevel, validators, epochs, leader
schedule, Tower BFT, PoH-related ordering, parallel execution, upgrades, fees,
and SPL assets with native distinctions.

### Bloc 3G — Cosmos family

Separate Cosmos SDK, CometBFT, IBC, Cosmos Hub, zones, appchains, validators,
governance, and shared or replicated security. SDK use is not Hub identity.

### Bloc 3H — Polkadot / Substrate family

Separate relay chain, parachains, Substrate, runtime, FRAME, validators,
nominators, collators, shared security, XCM, upgrades, and settlement. Shared
tooling does not establish parachain identity or membership.

### Bloc 3I — Avalanche family

Represent Primary Network, P-Chain, C-Chain, X-Chain, subnets, validators,
Snow-family mechanisms, AVAX, chain-specific execution, and cross-chain relations.

### Bloc 3J — Move family

Represent Sui and Aptos without collapsing object-centric and account/resource-
centric differences. Shared Move tooling does not erase native architecture.

### Bloc 3K — ICP / canister family

Represent subnets, canisters, replicas, NNS, chain-key concepts where evidenced,
Wasm execution, cycles, deployment, assignment, governance, and upgrades without
ordinary-contract or generic-shard assumptions.

### Bloc 3L — DAG / non-linear ledger families

Represent event/order identity, partial ordering, consensus ordering, convergence,
participants, and finality without fabricated linear block height.

### Bloc 3M — Modular / rollup / appchain systems

Decompose execution, sequencing, settlement, consensus, DA, security, and
interoperability into typed components and faithful Book 1 or Book 3-local
relations.

### Bloc 3N — Native asset / realization binding

Preserve canonical economic asset identity and explicit chain-local realization.
Migration and representation history remain queryable through Book 1 semantics.

### Bloc 3O — Network identity / genesis / fork doctrine

Apply Sections 3 and 4: ancestry is not identity by itself; branch survival,
canonical continuity, state, deployment, and family-native evidence determine the
classification.

### Bloc 3P — Shared security

Use `SECURED_BY` with its accepted mechanism semantics. Keep security distinct from
execution, settlement, DA, and messaging.

### Bloc 3Q — Architecture change history

Record temporal transitions for forks, upgrades, VM/consensus/DA/settlement/
sequencer/security changes, restarts, shutdown, and migration. Historical truth is
never rewritten.

## 11. Closed operator decisions D3-1 through D3-7

| Decision | Ratified planning outcome | Status |
|---|---|---|
| D3-1 | Branch-sensitive fork identity: ancestry is not current identity; non-branching upgrade preserves identity; persistent divergence creates new objects with `FORKED_FROM`; unresolved split remains `UNKNOWN`. | CLOSED / RATIFIED |
| D3-2 | New-genesis restart is `NEW_OBJECT` by default; reuse of name, ticker, operator, or branding is insufficient; a family-native continuation exception requires operator review. | CLOSED / RATIFIED |
| D3-3 | Modular roles use typed independent component dossiers rather than one monolithic trust domain. | CLOSED / RATIFIED |
| D3-4 | Shared security uses faithful Book 1 `SECURED_BY`, distinct from `RUNS_ON`, `SETTLES_TO`, `USES_DA`, and `MESSAGES_TO`. | CLOSED / RATIFIED |
| D3-5 | Network identity uses a family-native evidence bundle; no universal single anchor exists; conflict remains `UNKNOWN / CONTESTED`. | CLOSED / RATIFIED |
| D3-6 | Registry admission is two-tier: new family/namespace requires operator; evidence-qualified new values may be admitted inside a ratified namespace. | CLOSED / RATIFIED |
| D3-7 | Migration preserves typed lineage and historical objects; source identity is never overwritten into the destination. | CLOSED / RATIFIED |

The canonical decision records are appended to `CSIA_OPERATOR_DECISION_LOG.md`.

## 12. Evidence, anti-EVM, and authority gates

- `BOOK_2_EVIDENCE_BOUNDARY = PASS`
- `ANTI_EVM = PASS`
- `BOOK_3_FACTS_BYPASSING_BOOK_2 = 0`
- `BOOK_1_FROZEN = TRUE`
- `BOOK_1_CONTRACT_AMENDMENT_COUNT = 0`
- `LIVE_ACQUISITION_AUTHORITY = FALSE`
- `BOOK_3_IMPLEMENTATION_AUTHORITY = FALSE`

Ratification of this plan does not authorize source code, live data, RPC,
collectors, database or graph-database work, or any downstream acquisition.

## 13. v0.1 to v0.2 changelog

- Corrected fork doctrine so shared history establishes ancestry but not current
  network identity by itself.
- Added explicit non-branching, persistent-divergence, and unresolved-split
  outcomes.
- Audited accepted Book 1 `EdgeType` values directly and reclassified ten already-
  supported relations.
- Classified `EXECUTES_WITH`, `USES_DA`, and `SEQUENCED_BY` as Book 3-local
  extension candidates without aliasing or Book 1 mutation.
- Recorded authorized D3-1 through D3-7 outcomes and their consequences.
- Preserved the v0.1 artifacts and narrowed the reconciliation to the two blocking
  seams; no unrelated Book 3 scope was added.
