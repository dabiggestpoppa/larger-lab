# CSIA Book 4 Substitutability Stress Matrix

- **Version:** v0.1
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Purpose:** test whether a candidate can replace an incumbent for a specific function, under stated technical and governance conditions

## Rule set

Substitutability is:

- directional: candidate can substitute for incumbent, not vice versa by default;
- contextual: scoped to a function, chain, route, environment, or state condition;
- time-valid: valid only during an evidenced interval;
- evidence-backed: compatibility and migration claims bind to Book 2;
- non-economic in this matrix: no investment score or capital ranking.

Candidate change classes are `DROP_IN`, `CONFIG_CHANGE`, `CONTRACT_CHANGE`,
`PROTOCOL_UPGRADE`, `MIGRATION_REQUIRED`, `ECONOMICALLY_INFEASIBLE`,
`NO_KNOWN_SUBSTITUTE`, and `UNKNOWN`. These are stress outcomes, not facts about
any named provider.

## Stress matrix

| Function | Candidate substitute | Technical change | Governance required | Migration / state impact | Security impact | Downtime risk | Evidence required | Classification posture |
|---|---|---|---|---|---|---|---|---|
| Oracle feed swap | another feed or oracle delivery path | Contract/interface, heartbeat, freshness, decimals, and caller changes may be required | Consumer, data source, or protocol governance may be required | Existing positions, fallback state, and update continuity | Manipulation, freshness, and delivery trust may change | Stale reads, pause, or emergency fallback | Consumer contract/config, feed specification, update/fallback mechanism, source and delivery evidence | `CONFIG_CHANGE`, `CONTRACT_CHANGE`, or `MIGRATION_REQUIRED`; never assumed `DROP_IN` |
| RPC provider swap | another RPC endpoint/provider | API, chain support, rate limits, archive, tracing, or transaction semantics may differ | Application/operator change control | Endpoint state and in-flight requests | Key, node, transport, and censorship exposure may change | Submission/reads may fail during cutover | Application config, deployment manifest, provider docs, failover evidence | `CONFIG_CHANGE`, `CONTRACT_CHANGE`, or `MIGRATION_REQUIRED`; runtime scope must be stated |
| Indexer swap | another indexer/data API | Query schema, freshness, entity mapping, pagination, and lag may differ | Product/operator change approval | Historical index state and backfill | Data completeness and source integrity may change | UI/API degradation or stale reads | Query contract, consumer config, indexer source, backfill and fallback evidence | `CONFIG_CHANGE`, `CONTRACT_CHANGE`, or `MIGRATION_REQUIRED`; often soft runtime |
| DA migration | another DA provider or native DA | Blob format, namespace, proof, retrieval, and settlement-layer changes may be required | Rollup governance and upgrade process | Historical data availability, recovery, and fallback | Data availability and censorship assumptions may change | Publication/retrieval pause or recovery gap | Rollup config, publication/retrieval evidence, proof/availability mechanism, governance record | `PROTOCOL_UPGRADE` or `MIGRATION_REQUIRED`; not drop-in by default |
| Bridge replacement | canonical or third-party bridge | Asset contract, message format, verifier, finality, and liquidity route may differ | Asset/bridge governance and emergency controls | Locked/minted/burned state and migration path | Verifier, threshold, liquidity, and message ordering may change | Asset route interruption and user/operator action | Contracts, route config, verifier state, asset migration documentation | `CONTRACT_CHANGE` or `MIGRATION_REQUIRED`; never universal replacement |
| Messaging layer replacement | another message transport or chain-native route | Endpoint, encoding, acknowledgement, retry, and finality semantics may differ | Consumer and route governance | In-flight messages and replay state | Auth, ordering, and liveness assumptions may change | Message loss/duplication or delayed finality | Protocol specification, deployed config, route/endpoint state, operator evidence | `PROTOCOL_UPGRADE` or `MIGRATION_REQUIRED` |
| Sequencer replacement | another sequencer or decentralized set | Batch format, sequencing policy, derivation, and soft-confirmation semantics may differ | Rollup governance and upgrade process | Sequencing continuity, reorgs, and operator keys | Centralization/censorship and liveness assumptions may change | Liveness or user-experience disruption | Sequencer config, batch/derivation evidence, governance and operator records | `PROTOCOL_UPGRADE` or `MIGRATION_REQUIRED`; not inferred from operator count |
| SDK replacement | another SDK/framework | API, ABI, generated clients, serialization, test/build behavior may differ | Usually no protocol governance for pure build tooling | Rebuild/deployment artifacts; no chain state if build-time only | Dependency vulnerabilities and signing/client behavior may change | Deployment/build outage only | Repository manifest, lockfile, build config, versioned API evidence | `DROP_IN` only for proven build compatibility; otherwise `CONFIG_CHANGE` or `MIGRATION_REQUIRED` |
| Validator/security-provider replacement | another validator/guardian/security service | Key set, verification contract, threshold, attestation, and finality may differ | Validator/governance and often consumer governance | Key rotation, pending messages, and state synchronization | Security threshold and compromise domain may change | Verification halt or unsafe migration | Validator/guardian config, contract state, key/governance evidence | `PROTOCOL_UPGRADE` or `MIGRATION_REQUIRED`; rarely drop-in |
| Canonical bridge replacement | third-party bridge or another canonical route | Asset representation, finality, canonical registry, and liquidity/migration path may differ | Canonical registry and asset governance | Asset state, backing, and bridge records | Canonical trust and finality assumptions may change | Asset access and liquidity interruption | Canonical registry, contracts, asset migration, finality and governance evidence | `MIGRATION_REQUIRED` or `NO_KNOWN_SUBSTITUTE` until proven |
| Relayer replacement | another relayer or relayer set | Message format, proof construction, fee policy, and delivery timing may differ | Operator or route governance may be minimal or material | Replay, fee, and delivery state | Key/operator compromise and censorship may change | Message delay or temporary route unavailability | Relayer implementation/config, route/endpoint state, operator evidence, activation evidence | `CONFIG_CHANGE`, `PROTOCOL_UPGRADE`, or `MIGRATION_REQUIRED`; never assume permissionless substitutes are independent |

## Function-specific rules

1. A substitute for a price feed is not automatically a substitute for an
   attestation, reserve proof, automation trigger, or data-delivery service.
2. A substitute for RPC reads is not automatically a substitute for transaction
   submission, archive access, tracing, or consensus execution.
3. An indexer is often a soft runtime or product dependency; classify it separately
   from protocol safety and settlement.
4. DA substitution must preserve publication, retrieval, availability proof, and
   settlement assumptions as applicable.
5. A canonical bridge and a third-party bridge may have different finality,
   canonicality, liquidity, and migration constraints.
6. A relayer replacement is not automatically a verifier replacement.
7. An SDK replacement is build-time unless runtime behavior is independently
   evidenced.
8. `ECONOMICALLY_INFEASIBLE` is not an investment score; it describes a documented
   feasibility constraint for the scoped function and time.
9. `UNKNOWN` remains the result when evidence cannot distinguish `DROP_IN` from a
   contract or protocol change.

## Planning verdict

**PASS_FOR_PLANNING.** The requested substitutions fit a directional, contextual,
time-valid assessment record with explicit technical, governance, migration, state,
security, downtime, and evidence dimensions. No provider substitution is asserted
by this matrix.
