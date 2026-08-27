# Chapter 15.9 — Evidence & Registry Services

## Mission

Implement durable QCAE memory as services that create, validate, store, retrieve, hash, and relate capability/evidence objects without coupling domain logic to one database engine.

## Services

```text
EvidenceArtifactService
ProvenanceService
HashingService
CapabilityReceiptService
CapabilityRegistryService
RepositoryRegistryService
RelationshipService
NegativeKnowledgeService
Search/RetrievalService
```

## Persistence Ports

Domain/application services use repository interfaces such as:

```text
ContractRepository
CapabilityRepository
EvidenceRepository
JobRepository
ReceiptRepository
RelationshipRepository
MonitoringRepository
```

SQLite/DuckDB/Parquet/filesystem implementations live under infrastructure.

## Transaction Boundaries

Canonical state updates that must remain consistent—such as lifecycle state plus newly accepted evidence refs—use explicit transactions/unit-of-work semantics.

## Search

Retrieval combines structured filters with semantic/text search where useful. Semantic retrieval cannot override canonical IDs/status fields.

## Negative Knowledge

Rejected candidates and failed experiments share the same first-class storage/retrieval path as successes.

## Invariants

1. Storage engine is abstracted behind repositories.
2. Canonical structured fields outrank semantic-search guesses.
3. Evidence hashing/provenance is centralized.
4. Negative knowledge is first-class.
5. Related state updates have explicit consistency boundaries.
6. Receipts are generated from canonical objects/evidence, not free-form memory.

## Exit Criteria

The implementation agent can build durable QCAE memory now and swap/federate storage later without rewriting domain semantics.
