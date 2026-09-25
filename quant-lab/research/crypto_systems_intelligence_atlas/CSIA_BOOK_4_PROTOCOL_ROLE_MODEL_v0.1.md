# CSIA Book 4 Protocol Role Model

- **Version:** v0.1
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Purpose:** model what infrastructure service a system provides without reducing it to one category

## 1. Role doctrine

A system may hold multiple simultaneous roles. Roles are:

- multi-valued;
- non-exclusive;
- temporal;
- evidence-backed;
- scoped to a function, chain, service, or environment;
- distinct from token identity, ownership, and economic importance.

Role assignment is not a claim that the system is universally responsible for
every action associated with the role. A role record must say what service is
provided, to whom, under which mechanism, and during which valid interval.

## 2. Candidate role model

```text
RoleAssignment
  role_assignment_id
  system_ref
  role_type
  function
  scope                    # chain, ecosystem, protocol, route, service, environment
  mechanism
  consumes[]               # optional service/dependency context
  provides[]               # optional output/service context
  valid_from
  valid_to
  book2_claim_refs[]
  source_snapshot_refs[]
  state = ACTIVE | HISTORICAL | DECLARED | UNKNOWN
```

A role assignment is not a dependency record. It may support one or more
Book 4 dependency records, but the direction, function, evidence, and failure
consequence must be explicit.

## 3. Role families

### 3.1 Oracle and data roles

- `ORACLE_NETWORK`: coordinates publishers, data delivery, or oracle services.
- `DATA_PUBLISHER`: signs, submits, or otherwise publishes data under a mechanism.
- `DATA_SOURCE`: originates the underlying datum or event.
- `FEED`: named data product consumed by a consumer.
- `PRICE_FEED`: price-specific feed role, not every datum.
- `ATTESTATION_SERVICE`: proof, reserve, or external-state attestation role.
- `DELIVERY_LAYER`: transports oracle data to a chain or consumer.
- `AUTOMATION_SERVICE`: triggers or executes data-dependent automation.
- `MESSAGING_SERVICE`: transports messages, distinct from asset bridging.
- `FALLBACK_SOURCE`: alternate source used under stated conditions.

The same system may be an oracle network, delivery layer, automation service, and
messaging service. Token issuance or token utility does not define these roles.

### 3.2 Interoperability roles

- `MESSAGE_TRANSPORT`
- `ASSET_BRIDGE`
- `CANONICAL_BRIDGE`
- `LIGHT_CLIENT_VERIFIER`
- `VALIDATOR_VERIFIER`
- `GUARDIAN_VERIFIER`
- `ORACLE_ASSISTED_VERIFIER`
- `LOCK_MINT`
- `BURN_MINT`
- `LIQUIDITY_BRIDGE`
- `INTENT_BASED_TRANSFER`
- `CHAIN_NATIVE_INTEROPERABILITY`
- `RELAYER_LAYER`
- `ENDPOINT`
- `CHANNEL`
- `ROUTE`

These roles are not interchangeable. A message transport role does not establish
asset bridging, and a bridge role does not establish settlement.

### 3.3 Modular infrastructure roles

- `DA_NETWORK`
- `DA_PROVIDER`
- `BLOB_DATA_PUBLICATION`
- `SAMPLING_AVAILABILITY_MECHANISM`
- `RETRIEVAL_SERVICE`
- `SEQUENCER`
- `SETTLEMENT_LAYER`
- `SECURITY_PROVIDER`
- `FALLBACK_DA`

`USES_DA`, `SETTLES_TO`, `SECURED_BY`, and `RUNS_ON` remain separate accepted or
Book 3-local semantics.

### 3.4 Developer and operational infrastructure roles

- `RPC_PROVIDER`
- `NODE_INFRASTRUCTURE`
- `INDEXER`
- `DATA_API`
- `SDK`
- `FRAMEWORK`
- `DEVELOPER_TOOL`
- `WALLET_INFRASTRUCTURE`
- `EXPLORER`
- `OPERATIONAL_PROVIDER`
- `HOSTED_SERVICE`

Runtime, soft-runtime, build-time, developer-tooling, optional-tool, and
hosted-service scope must be attached to the role or relation. A system may be a
hosted service to one product and an optional tool to another.

## 4. Role examples

| System | Candidate role set | What must remain distinct |
|---|---|---|
| Chainlink | oracle network; feed delivery; automation; messaging; proof/reserve infrastructure | Oracle service identity is not token identity; feed, delivery, automation, and proof functions need separate assignments. |
| Pyth | oracle/data network; publisher ecosystem; price feed; delivery layer | Publisher, feed, chain delivery, and consumer dependency are not one undifferentiated role. |
| RedStone | oracle/data network; feed and delivery infrastructure | Do not infer independent failure domains or current deployments from the role alone. |
| API3 | oracle/data and attestation service candidate | Attestation is not automatically a price feed or generic data integration. |
| IBC | messaging framework; interoperability protocol; route fabric | Client/connection/channel/relayer structure and chain-native interoperability remain explicit. |
| CCIP | messaging and interoperability service candidate | Message transport does not automatically become a canonical asset bridge. |
| LayerZero | messaging/endpoint/verification infrastructure candidate | Endpoint and verifier semantics are not generic bridge dependency. |
| Wormhole | messaging, gateway, guardian/verification, and asset-transfer infrastructure candidate | Verifier and asset-transfer roles need separate evidence. |
| Axelar | gateway, messaging, verification, and asset-transfer infrastructure candidate | Gateway/validator/bridge roles must not be flattened. |
| Celestia | DA network; modular infrastructure; settlement-adjacent dependency for some consumers | DA use is not settlement or security equivalence. |
| Alchemy | RPC provider; developer API; hosted node infrastructure | RPC availability is not protocol consensus; hosted service scope is temporal. |
| The Graph | indexing and data API infrastructure candidate | Indexer use may be soft runtime, product-only, or optional. |
| An SDK | build-time component; possible developer tooling | A build-time component is not a runtime provider by default. |

Examples are role stress cases only. They are not current deployment assertions.

## 5. Multi-role invariants

1. A system may have zero, one, or many active role assignments.
2. A role may apply to one chain or route and not another.
3. Role validity must be time-bounded; historical roles remain historical.
4. A role does not imply ownership, governance control, token utility, or economic value.
5. A role does not imply that every consumer depends on the system directly.
6. A role may be provided by a system whose backend is operated by another entity;
   provider identity and operator identity are separate evidence fields.
7. If role semantics cannot be stated without a new edge type, use a local typed
   record and seek operator review before any Book 1 amendment.
8. A fallback role is conditional and must state activation conditions.
9. A route role is not a capital-flow or liquidity claim.
10. Unknown role assignment remains `UNKNOWN`; absence of evidence is not evidence of
    absence of a role.

## 6. Role-to-relationship projection

| Role evidence | Possible accepted relation | Required local qualifier |
|---|---|---|
| Provides data to consumer | `ORACLE_FOR` | feed, source, publisher, chain deployment, update/delivery mechanism |
| Messages to chain | `MESSAGES_TO` | message type, endpoint/channel, transport scope |
| Bridges to chain | `BRIDGES_TO` | bridge product, route, asset/function scope, verification mechanism |
| Routes through system | `ROUTED_THROUGH` | technical route only; Book 5 owns capital flow |
| Uses DA | `USES_DA` | provider, publication, retrieval, fallback, valid time |
| Runs on infrastructure | `RUNS_ON` | host/service scope; not settlement or security |
| Built with SDK | `BUILT_WITH` | build-time scope and runtime consequence, if any |
| Operated by entity | `OPERATED_BY` | operator evidence; not failure-domain equality |
| Hosted by provider | `HOSTS` | hosted service and outage scope |

No projection is made solely from a role name, token symbol, partnership, or
marketing statement.

## 7. Identity and lifecycle rules

System identity, role identity, token identity, operator identity, provider
identity, and failure-domain identity are separate. A token may have a role in a
protocol’s governance or economics without being the infrastructure provider. An
operator may operate multiple systems without creating a single shared failure
domain. A provider may serve multiple roles without every role sharing the same
failure mechanism.

Lifecycle transitions such as migration, deprecation, replacement, or fallback
must preserve prior and next role assignments with valid times. Migration is not
proof of substitutability, and a declared replacement is not proof of active
failover.

## 8. Planning verdict

**PASS_FOR_PLANNING.** A multi-valued, temporal, evidence-backed role model can
represent oracle, bridge, DA, RPC, indexing, SDK, and developer-infrastructure
cases without forcing every system into one category. The role model is a
candidate Book 4 local typed layer; it does not amend Book 1 or Book 3.
