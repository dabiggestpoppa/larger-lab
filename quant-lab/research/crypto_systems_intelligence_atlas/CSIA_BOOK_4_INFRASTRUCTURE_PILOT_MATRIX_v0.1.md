# CSIA Book 4 Infrastructure Pilot Matrix

- **Version:** v0.1
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Acquisition:** none
- **Purpose:** stress the proposed dependency model with known architectural categories without claiming current deployment coverage

## Reading rules

Each row is a pilot question, not a populated fact record. “Candidate” means the
schema must be able to represent the semantic after Book 2 evidence is obtained.
Blank or `UNKNOWN` fields are intentional. No pilot asserts a current integration,
provider relationship, redundancy level, failure domain, or substitute.

The matrix fields are:

- canonical object type and roles;
- chains/ecosystems served, as a scope placeholder;
- direct dependencies and dependents, with function and direction;
- accepted Book 1 and Book 3 relations;
- Book 4 extension candidates;
- failure-domain questions;
- redundancy questions;
- substitutability questions;
- temporal state and Book 2 evidence families;
- unresolved gaps.

## Oracle and data pilots

| Pilot | Canonical object / candidate roles | Chains/ecosystems served | Direct dependency / dependent questions | Book 1 / Book 3 relation surface | Book 4 extension candidate | Failure, redundancy, substitution questions | Evidence families and unresolved gaps |
|---|---|---|---|---|---|---|---|
| Chainlink | Oracle network; feed; delivery; automation; attestation | Per-feed and per-chain scope unknown | Which feed/function is consumed? Does consumer fail or degrade without it? | `ORACLE_FOR`, `PRICES`, `DATA_FROM` only when semantically appropriate | `OracleServiceContext`, feed-specific dependency record | Are multiple feeds independent by publisher/upstream/delivery? Can a feed be swapped without redesign? | Deployed consuming contract/config, official integration docs tied to version, chain state; feed, publisher, delivery, fallback, and current deployment gaps |
| Pyth | Oracle network; publisher ecosystem; price feed; delivery | Per-feed and chain scope unknown | Consumer dependency on specific feed, publisher, or delivery path? | `ORACLE_FOR`; `PRICES` for price function | Feed/update/delivery context and path record | Are multiple publishers and delivery paths independent? Is fallback active? | Publisher/update mechanism, deployment config, official docs, onchain consumer; source concentration and chain-specific behavior gaps |
| RedStone | Oracle/data network; feed; delivery | Per-feed and chain scope unknown | Is it a primary, fallback, optional, or integrated service? | `ORACLE_FOR`; `DATA_FROM` only for non-oracle data | Feed family and delivery mechanism attributes | Are multiple feeds independent? Can a consumer change feed without contract redesign? | Consumer configuration, feed/deployment evidence, official docs; current feed coverage and operational dependency gaps |
| API3 | Oracle/data and attestation service candidate | Per-service and chain scope unknown | Does attestation serve a security, pricing, or data function? | `ORACLE_FOR` or `DATA_FROM` by function; no generic flattening | Attestation role and mechanism record | Is attestation substitutable by a price feed? No; assess function separately. | Service/consumer configuration, attestation mechanism, deployment evidence; service identity and dependency gaps |

## Interoperability and bridge pilots

| Pilot | Canonical object / candidate roles | Chains/ecosystems served | Direct dependency / dependent questions | Book 1 / Book 3 relation surface | Book 4 extension candidate | Failure, redundancy, substitution questions | Evidence families and unresolved gaps |
|---|---|---|---|---|---|---|---|
| IBC | Messaging framework; interoperability protocol; route fabric; endpoint/channel/relayer roles | Per client/connection/channel scope unknown | Does a protocol use a specific channel, client, connection, or relayer path? | `MESSAGES_TO`; `ROUTED_THROUGH`; `BRIDGES_TO` only for asset-bridge function | Route/endpoint/channel/relayer typed context; hyperedge likely for full route | Are multiple relayers independent? Can a channel be replaced without a new trust or governance model? | Deployed channel/client/connection state, route config, relayer/operator evidence, official architecture; current route and verifier gaps |
| CCIP | Messaging and interoperability service; chain/endpoint role | Per chain/endpoint scope unknown | Message transport versus asset transfer; is the consumer dependent on service or optional? | `MESSAGES_TO`; `BRIDGES_TO` only for asset route | Endpoint, message, relayer, and route context | Are multiple lanes/providers independent? Is replacement an upgrade or migration? | Deployed configuration, endpoint/message evidence, official docs; version and current deployment gaps |
| LayerZero | Messaging/endpoint/verification infrastructure candidate | Per endpoint and chain scope unknown | Does a consumer require a specific endpoint, verifier set, or message path? | `MESSAGES_TO`; `VALIDATED_BY`/`SECURED_BY` only with mechanism | Endpoint/verifier/message typed context; hyperedge for route | Are endpoint and verifier failure domains shared? Can an endpoint be replaced without security-model change? | Endpoint/verifier config, deployed contracts, official architecture; trust and redundancy evidence gaps |
| Wormhole | Messaging; gateway; guardian/verification; asset-transfer candidate | Per gateway and route scope unknown | Is the role message transport, verification, or asset transfer? | `MESSAGES_TO`; `BRIDGES_TO`; `VALIDATED_BY` or `SECURED_BY` by mechanism | Gateway/guardian/route context | Are guardian and message paths independent? Can one role substitute for another? | Gateway/guardian config, contracts, official docs, route state; current deployment and operator gaps |
| Axelar | Gateway; messaging; validation/verification; asset-transfer candidate | Per gateway and route scope unknown | Is consumer dependent on gateway, validator set, message layer, or route? | `MESSAGES_TO`; `BRIDGES_TO`; validation/security only when explicit | Gateway/validator/route context; possible hyperedge | Are validators and gateways correlated? Is a different gateway drop-in or migration? | Gateway/validator config, contracts, route evidence, official docs; current deployment and governance gaps |
| Canonical rollup bridge | Canonical bridge; asset bridge; route; verifier | Per rollup and settlement scope unknown | Does it serve settlement, only connectivity, or asset movement? | `BRIDGES_TO`; `SETTLES_TO` only with separate evidence; `ROUTED_THROUGH` for route | Route/canonicality/verification context | Can a third-party bridge replace it for a given function? What state and trust changes result? | Rollup/bridge config, contracts, route state, settlement documentation; current route and security gaps |
| Third-party liquidity/asset bridge | Asset bridge; liquidity bridge; route; verifier | Per source/destination and asset scope unknown | Is dependency technical, optional, or route-specific? | `BRIDGES_TO`; `ROUTED_THROUGH`; `INTEGRATES_WITH` when optional | Asset/route/verifier/liquidity-bridge context | Can route be replaced without liquidity or asset migration? Which economic effects belong to Book 5? | Deployed contracts, route/liquidity configuration, operator docs; capital flow and current liquidity gaps |

## DA and modular infrastructure pilots

| Pilot | Canonical object / candidate roles | Chains/ecosystems served | Direct dependency / dependent questions | Book 1 / Book 3 relation surface | Book 4 extension candidate | Failure, redundancy, substitution questions | Evidence families and unresolved gaps |
|---|---|---|---|---|---|---|---|
| Celestia | DA network; provider; publication/retrieval infrastructure | Per rollup and namespace scope unknown | Does consumer require DA for safety, liveness, recovery, or optional publication? | `USES_DA`; no automatic `SETTLES_TO`/`SECURED_BY` | DA provider/publication/retrieval/fallback context | Are fallback providers active and independent? Is migration a protocol upgrade? | Rollup config, blob publication, official architecture, operator docs; current deployment and security assumptions gaps |
| EigenDA | DA provider; publication/retrieval/security infrastructure candidate | Per rollup and service scope unknown | Is it primary, fallback, or optional DA? What retrieval path is required? | `USES_DA` | DA service/function/operator/fallback record | Is a provider migration contract-compatible? Are constraints shared? | Deployed config, publication/retrieval evidence, official docs; current coverage and security gaps |
| Avail | DA network/provider; modular infrastructure candidate | Per rollup and namespace scope unknown | Does use establish DA, security, or settlement? | `USES_DA` | DA publication/retrieval/migration context | Can another DA be activated without governance or state migration? | Rollup config, publication evidence, official docs; current deployment and fallback gaps |
| Ethereum DA | Native chain DA; data publication infrastructure | Per rollup and chain scope unknown | Is Ethereum DA native settlement-adjacent infrastructure or a generic provider? | `USES_DA`; `SETTLES_TO` remains separate | Native DA publication/retrieval context | Is a fallback DA available? What assumptions differ from external DA? | Rollup config, blob publication, chain/rollup docs; version and consumer-specific evidence gaps |

## RPC, indexing, and developer infrastructure pilots

| Pilot | Canonical object / candidate roles | Chains/ecosystems served | Direct dependency / dependent questions | Book 1 / Book 3 relation surface | Book 4 extension candidate | Failure, redundancy, substitution questions | Evidence families and unresolved gaps |
|---|---|---|---|---|---|---|---|
| Alchemy | RPC provider; hosted node infrastructure; developer API | Per chain and product scope unknown | Required for transaction submission, reads, indexing, or optional product? | `RUNS_ON`/`HOSTS` or local dependency; not consensus | RPC service/runtime-scope record | Do multiple products share backend/cloud/operator? Can provider swap preserve behavior? | App/operator config, deployment manifest, provider docs, failover behavior; current dependency and backend gaps |
| Infura | RPC provider; hosted node infrastructure; developer API | Per chain and product scope unknown | Hard runtime, soft runtime, build-time, or optional integration? | `RUNS_ON`/`HOSTS` or local dependency | RPC service/runtime-scope record | Is failover active or manual? Is another provider technically compatible? | App config, manifests, operator docs; current coverage and correlated infrastructure gaps |
| QuickNode | RPC provider; hosted service | Per chain and product scope unknown | Which protocol function fails or degrades? | `RUNS_ON`/`HOSTS` or local dependency | RPC service/runtime-scope record | Are endpoints independent by operator/cloud/upstream? | Config, manifests, provider docs; operational dependency and independence gaps |
| The Graph | Indexer; data API; hosted service candidate | Per chain/index scope unknown | Does consumer require fresh indexed data for execution, or only UI/analytics? | `INTEGRATES_WITH` or soft dependency | Indexing/runtime-scope record | Can indexer swap preserve query semantics and freshness? | Consumer config, API contract, indexer docs, fallback evidence; current index and dependency gaps |
| Subsquid | Indexer; data API; developer infrastructure candidate | Per chain/index scope unknown | Is indexing a soft runtime or developer-only dependency? | `INTEGRATES_WITH`/`BUILT_WITH` by scope | Indexing/service-scope record | What happens if the indexer is stale or unavailable? | Query/config evidence, source repository, provider docs; current deployment gaps |
| Helius | RPC/indexing/API infrastructure candidate | Per chain and service scope unknown | Which service function is consumed and by which consumer? | `RUNS_ON`/`HOSTS`/`INTEGRATES_WITH` | RPC/index/API service record | Are API and RPC failure paths correlated? | Config, API contract, operator docs; current service scope gaps |
| SDK/framework pilot | SDK; build-time component; developer tooling; possible runtime contract | Per implementation and version scope unknown | Does use end at build time or create a runtime contract dependency? | `BUILT_WITH` with build/runtime scope | Runtime-scope attribute or local build record | Does a different SDK require contract, protocol, or governance changes? | Source manifest, lockfile, import, build config, versioned docs; runtime consequence gaps |
| Hosted RPC provider pilot | RPC provider; hosted service; operational provider | Per chain and environment scope unknown | Is it production-critical, soft, fallback, or developer-only? | `HOSTS`, `RUNS_ON`, local dependency | Runtime-scope and failover record | Is a second provider deployed and independently activated? | Deployment manifest, app config, operator docs, failover test/evidence; current dependency gaps |
| Decentralized infrastructure provider pilot | Provider; node/operator network; hosted or self-operated service | Per chain and service scope unknown | Are nodes independently operated, or do they share verifier/operator/cloud? | `OPERATED_BY`, `RUNS_ON`, local dependency | Provider/operator/failure-domain context | Does decentralization establish failure independence? No; mechanism evidence required. | Node/operator records, deployment config, architecture docs; operator and independence gaps |

## Cross-pilot unresolved questions

1. Which service is directly consumed, and which relations are only transitive?
2. Is the service required for safety, liveness, state recovery, user operation, or
   only product functionality?
3. Does multiple-provider use mean active failover, manual failover, or merely a
   declared option?
4. Which upstream source, verifier, operator, cloud, codebase, or governance
   creates correlation?
5. What is the valid time of each relationship and fallback?
6. Can a substitute preserve the exact function, trust assumptions, state, and
   governance constraints?
7. Which Book 2 claim families are required before any current fact can be loaded?
8. Which role or route requires a hyperedge rather than a flattened pairwise edge?

## Planning verdict

**PASS_FOR_PLANNING.** The requested oracle, messaging, bridge, DA, RPC, indexing,
SDK, hosted-service, and decentralized-provider cases fit a typed multi-role model
with explicit evidence gaps. The matrix is not a current infrastructure atlas and
does not authorize acquisition.
