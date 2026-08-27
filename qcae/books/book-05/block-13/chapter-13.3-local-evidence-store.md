# Chapter 13.3 — Local Evidence Store

## Mission

Persist QCAE's evidence, receipts, provenance, registry state, negative knowledge, run artifacts, and relationship records locally in a form that remains auditable and migratable to future OCE-governed infrastructure.

## Storage Layers

A practical initial design may use:

```text
structured metadata: SQLite/DuckDB or equivalent
analytical snapshots: Parquet
human-readable reports: Markdown
raw artifacts: content-addressed filesystem/object-style store
```

Exact technology is implementation policy. The invariant is machine-readable canonical state plus immutable/hashable artifact references.

## Canonical Objects

Store at least:

```text
contracts
atoms
relationships
candidates
source snapshots
evaluations
worker runs
evidence artifacts
reproducibility packages
acquisition decisions
capability receipts
negative knowledge
monitoring state
authority decisions
```

## Content Addressing

Where practical, raw evidence is addressed by cryptographic digest. Metadata references the digest rather than trusting mutable paths.

## Append vs Mutate

Historical evidence/decisions should be append-oriented. New evaluations supersede or invalidate prior state through explicit relationships rather than rewriting history.

## Schema Migration

Schema versions are explicit. Migrations preserve old evidence semantics or record transformation provenance.

## Backup/Recovery

The local store must support backup and deterministic restoration because QCAE memory is expensive engineering capital.

## Invariants

1. Canonical memory is structured, not chat history.
2. Raw evidence is immutable/hashable where practical.
3. Historical decisions are not silently overwritten.
4. Schemas are versioned/migratable.
5. Human-readable reports are views, not the sole source of truth.
6. Local evidence can later be federated/submitted to OCE.

## Exit Criteria

Standalone QCAE has durable memory sufficient for resumability, negative knowledge, auditing, and later governance migration.
