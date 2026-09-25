# CSIA Book 4 Failure-Domain Stress Matrix

- **Version:** v0.1
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Purpose:** test whether shared infrastructure is represented as a technical mechanism rather than a category guess

## Classification

- `SHARED_FAILURE_DOMAIN`: evidence shows a failure mechanism can affect the
  listed systems or functions.
- `PARTIAL_SHARED_DOMAIN`: correlation exists for a bounded function, region,
  component, or time interval, but not the whole system.
- `INDEPENDENT`: evidence supports independence for the stated scope; this is not
  a default assumption.
- `UNKNOWN`: evidence is insufficient or conflicting.

The same-provider rule is not a rule. A provider brand can be an input to identity,
but the mechanism must be evidenced. The same category likewise does not prove
correlation. A `FailureDomain` must carry mechanism, scope, affected systems,
valid time, and Book 2 provenance.

## Stress matrix

| Scenario | Planning classification before evidence | Mechanism to test | Evidence required | Guardrail |
|---|---|---|---|---|
| Two protocols use the same oracle network | `UNKNOWN` or `PARTIAL_SHARED_DOMAIN` | Shared feed, publisher, updater, delivery, aggregation, or operator failure | Consumer configs, feed/deployment identity, publisher/update/delivery mechanism, operator evidence, valid time | Same network does not prove same feed or same failure consequence. |
| Same oracle network but different feeds | `UNKNOWN` or `PARTIAL_SHARED_DOMAIN` | Shared publisher, updater, data source, delivery layer, or operator despite different feed IDs | Feed IDs, source/publisher mapping, delivery and operator evidence | Different feeds are not automatically independent. |
| Same feed but different chains | `PARTIAL_SHARED_DOMAIN` or `UNKNOWN` | Shared source, publisher, aggregation, delivery, or operator across deployments | Per-chain deployment and consumer config, update mechanism, operator and delivery evidence | Chain-specific contracts do not eliminate a common upstream. |
| Same bridge verifier set | `SHARED_FAILURE_DOMAIN` candidate | Common validator/guardian set or verification contract failure | Verifier configuration, contract/state evidence, operator/governance mechanism, valid time | Do not infer from bridge name alone. |
| Different bridge products sharing a verifier | `SHARED_FAILURE_DOMAIN` candidate | Shared verifier set, key set, governance, or backend | Product-to-verifier mapping and technical mechanism | Product diversity is not verifier independence. |
| Two RPC brands sharing backend/operator | `SHARED_FAILURE_DOMAIN` candidate | Common backend, node cluster, cloud account, operator, region, or upstream | Deployment manifests, operator/backend docs, infrastructure configuration | Brand diversity is not failure independence. |
| Multiple providers on the same cloud | `PARTIAL_SHARED_DOMAIN` or `SHARED_FAILURE_DOMAIN` candidate | Cloud account, region, control plane, identity, or outage domain | Provider deployment evidence, cloud/account/region scope, operator configuration | Shared category or vendor does not prove shared security. |
| Same sequencer operator | `SHARED_FAILURE_DOMAIN` candidate | Shared sequencer process, operator control, or signing infrastructure | Sequencer configuration, operator identity, process/deployment evidence | Operator identity is evidence, not definition. |
| Shared DA | `SHARED_FAILURE_DOMAIN` candidate | Shared DA publication, retrieval, namespace, provider, or availability mechanism | `USES_DA` config, publication/retrieval evidence, provider mechanism | DA is not automatically settlement or security. |
| Shared validator set | `SHARED_FAILURE_DOMAIN` candidate | Common validator keys, stake, software, operator, or governance | Validator-set and operator/governance evidence | Category overlap alone is insufficient. |
| Shared code library | `PARTIAL_SHARED_DOMAIN` or `UNKNOWN` | Shared implementation, release artifact, build pipeline, or vulnerability path | Source manifest, lockfile, build/release evidence, deployed version | A library can be shared without shared runtime operation. |
| Shared governance multisig | `PARTIAL_SHARED_DOMAIN` or `UNKNOWN` | Control over upgrades, verifier changes, pause, migration, or treasury | Governance membership, control scope, execution evidence, valid time | Governance is not ownership and does not prove technical failure propagation. |
| Shared custodian | `SHARED_FAILURE_DOMAIN` candidate | Shared custody account, key, operator, policy engine, or withdrawal mechanism | Custody arrangement, key/operator/policy evidence | Technical route and capital control remain distinct. |
| Shared relayer | `PARTIAL_SHARED_DOMAIN` or `SHARED_FAILURE_DOMAIN` candidate | Shared relayer operator, keys, backend, queue, or route path | Relayer deployment/operator evidence, activation path, route config | Permissionless relayers may be independent only when mechanism is evidenced. |
| Shared indexer | `PARTIAL_SHARED_DOMAIN` or `UNKNOWN` | Shared indexer backend, database, source API, or freshness mechanism | Indexer deployment, source and consumer config, fallback behavior | Indexer dependence may be soft, product-only, or optional. |
| Common external API | `SHARED_FAILURE_DOMAIN` candidate | Shared API endpoint, provider backend, authentication, or rate limit | Application configuration, provider evidence, timeout/fallback behavior | Consumer diversity does not prove endpoint diversity. |
| Fallback provider sharing same upstream source | `CORRELATED` planning stress; classify `PARTIAL_SHARED_DOMAIN` or `SHARED_FAILURE_DOMAIN` only when scope/mechanism support it | Primary and fallback converge on same source, publisher, backend, or operator | Primary/fallback config, upstream mapping, activation and operator evidence | Two providers do not create two independent sources. |

## Mechanism requirements

A future Book 4 implementation should require, at minimum:

1. the affected function and bounded scope;
2. the technical object or process that can fail;
3. the relation between affected systems and that object/process;
4. whether the relation is active, conditional, historical, or unknown;
5. valid time and Book 2 claim references;
6. evidence that distinguishes shared control from shared security or ownership;
7. a reason that the mechanism can propagate to the affected systems.

A shared brand, ecosystem, category, token, or partnership is not sufficient.

## Independence and correlation review

`INDEPENDENT` is permitted only with a stated scope, such as “independent operator
control for this RPC function during this interval,” and with evidence for the
relevant dimensions. A system may be independent at one layer and correlated at
another: two RPC endpoints may use different providers but one cloud region, or two
bridges may use different products but one verifier set.

## Planning verdict

**PASS_FOR_PLANNING.** The requested scenarios expose the need for a typed
mechanism-based `FailureDomain`, not a provider/category heuristic. All current
classifications remain provisional and require Book 2 evidence before any canonical
claim.
