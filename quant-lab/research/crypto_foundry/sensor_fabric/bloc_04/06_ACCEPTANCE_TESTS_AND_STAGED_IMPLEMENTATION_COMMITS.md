# BLOC 4 — ACCEPTANCE TESTS & STAGED IMPLEMENTATION COMMITS

**Purpose:** define exactly how the immutable T0 lake is built, reviewed, and accepted later by the execution agent.

---

## 1. Build principle

Bloc 4 implementation must be reviewable as infrastructure, not delivered as one giant storage commit.

The execution agent must stop after every planned commit, run the relevant tests, record evidence, then continue.

No provider-specific adapter logic should be rewritten in this bloc except integration hooks required to persist Bloc 3 outputs.

---

## 2. Required implementation modules

Target tree:

```text
quant-lab/src/crypto_sensor_fabric/storage/
  __init__.py
  models.py
  paths.py
  checksums.py
  compression.py
  atomic.py
  blob_store.py
  projections.py
  lineage.py
  manifests.py
  catalog.py
  jobs.py
  revisions.py
  recovery.py
  quota.py
  retention.py
  query.py
  replay.py
  export.py
  duckdb_catalog.py
  postgres_repository.py

quant-lab/config/crypto_sensor_fabric/
  storage.yaml
  retention.yaml
  quota.yaml

quant-lab/tests/crypto_sensor_fabric/storage/
  fixtures/
  test_models.py
  test_paths.py
  test_blob_store.py
  test_atomic.py
  test_checksums.py
  test_compression.py
  test_projection.py
  test_lineage.py
  test_manifests.py
  test_revisions.py
  test_jobs.py
  test_recovery.py
  test_quota.py
  test_retention.py
  test_query.py
  test_replay.py
  test_export_restore.py
  test_duckdb_rebuild.py
  test_postgres_metadata.py
```

Exact filenames may shift only if responsibilities remain one-to-one and reviewable.

---

## 3. Required typed models

At minimum:

```text
EvidenceBlob
AcquisitionRecord
RawProjectionArtifact
ProjectionLineage
PartitionManifest
StorageJobState
StorageJobTransition
SourceRevision
IntegrityCheck
StorageQuotaState
BackupState
RawEvidenceQuery
RawEvidenceResult
RawNormalizationBatch
RecoveryAction
ExportManifest
```

All models must serialize deterministically where used in hashing/evidence IDs.

---

## 4. Test layers

### S0 — schema/unit tests

- typed validation;
- enum values;
- UTC timestamp enforcement;
- path escaping;
- hash formats;
- required provenance.

### S1 — local filesystem storage tests

- put/read exact bytes;
- dedupe same hash;
- zstd wrapper round-trip;
- content hash verification;
- no provider path traversal.

### S2 — atomicity/crash tests

Simulate failure at each commit step.

Expected:

- no partial final objects;
- no resume skip;
- recoverable orphan states;
- explicit quarantine.

### S3 — manifest/revision tests

- same request/same bytes;
- same request/new bytes;
- append-only manifest versions;
- current pointer transactions;
- revision ambiguity query.

### S4 — projection/lineage tests

- exact source refs;
- parser version changes;
- projection invalidation;
- rebuild from T0A;
- multi-blob lineage.

### S5 — quota/retention tests

- NORMAL/WATCH/CONSTRAINED/CRITICAL;
- optional P2 pause before P0;
- no automatic T0A deletion;
- size estimator blocks oversized planned job.

### S6 — catalog/replay/query tests

- query by provider/sensor/date;
- integrity filters;
- revision modes;
- deterministic source order;
- acquisition-vs-market reconstruction distinction exposed.

### S7 — backup/restore tests

- export manifest;
- copy verification;
- restore to empty root;
- DuckDB rebuild;
- hash equivalence.

### S8 — Bloc 3 integration fixture tests

Given a synthetic `RawPayloadEnvelope` / `FetchBatch`:

- persist T0A;
- write AcquisitionRecord;
- optional T0B projection;
- manifest update;
- advance resume only after commit.

No live network is needed.

---

## 5. Mandatory property tests / invariants

Where practical use property-based tests for:

- arbitrary payload bytes round-trip;
- random path-safe instrument strings;
- repeated identical acquisitions;
- revision sequences;
- crash step ordering;
- manifest version monotonicity;
- query range boundaries.

Core assertions:

```text
stored(source_bytes) -> read() == source_bytes
SHA256(read()) == EvidenceBlob.blob_sha256
resume_position <= durable_manifest_position
manifest_ref -> object exists OR manifest integrity fails loudly
```

---

## 6. Security tests

Must test:

- query/header secret redaction;
- path traversal rejection (`../` etc.);
- no shell interpolation from provider instrument strings;
- no symlink escape from data root;
- export destination boundary checks;
- fixtures contain no live credentials.

A failing secret scan is BLOCKING.

---

## 7. Performance tests

Not micro-optimization, but protect against unusable design.

Fixture/synthetic benchmarks:

- write 1 GiB-equivalent stream in chunks without unbounded memory;
- scan 10k+ manifest rows;
- query many projections through DuckDB;
- content dedupe does not require loading entire huge files into memory;
- hash streaming works incrementally.

Large files should be streamed, not `read()` fully by default.

Performance evidence is informational unless it violates configured hard resource ceilings.

---

## 8. Storage resource ceilings

Implementation should be configurable for workstation constraints.

Tests ensure:

- memory use is bounded by chunk size;
- hash/checksum operations stream;
- archive extraction checks free-space before expanding;
- projections write row groups incrementally where needed;
- critical disk watermark pauses safely.

No fixed RAM/disk assumption is baked into science logic.

---

## 9. Acceptance gates

### G4-01 — Exact evidence gate

PASS when arbitrary source bytes can be stored/retrieved exactly with verified source SHA256.

### G4-02 — Atomic durability gate

PASS when crash matrix produces no cursor skip or half-valid final object.

### G4-03 — Immutability gate

PASS when committed T0A cannot be overwritten through public storage APIs.

### G4-04 — Revision gate

PASS when same source key/different bytes creates explicit revision and preserves both versions.

### G4-05 — Manifest gate

PASS when all current manifests reference existing valid objects and historical versions remain available.

### G4-06 — Lineage gate

PASS when every T0B projection resolves completely to T0A blob/acquisition evidence.

### G4-07 — Missingness gate

PASS when no acquisition/no data/failure/history unavailable are distinguishable and none become numeric zero.

### G4-08 — Storage-pressure gate

PASS when optional high-volume writes pause before critical P0 sensor evidence and no raw auto-deletion occurs.

### G4-09 — Catalog rebuild gate

PASS when DuckDB discovery is reconstructed from manifest/projection files on an empty catalog.

### G4-10 — Operational metadata gate

PASS when Postgres contains metadata/state only and raw payload tables are absent.

### G4-11 — Export/restore gate

PASS when fixture evidence pack restores into empty root and hashes/query results match.

### G4-12 — Bloc 3 handoff gate

PASS when adapter output persists and resume checkpoint advances only after durable manifest commit.

### G4-13 — Bloc 5 readiness gate

PASS when `RawNormalizationBatch` exposes sufficient source/timestamp/unit/lineage evidence for PIT normalization without filesystem/path assumptions.

---

## 10. Evidence outputs

Implementation must generate review artifacts under something like:

```text
quant-lab/evidence/crypto_sensor_fabric/bloc_04/
  test_report.json
  invariants.json
  crash_matrix.json
  revision_matrix.json
  storage_layout.json
  quota_simulation.json
  duckdb_rebuild.json
  restore_test.json
  bloc4_readiness.json
```

Large raw fixture output stays outside Git unless deliberately tiny.

Evidence summaries/checksums may be committed.

---

## 11. Staged implementation commits

### `SENSOR-B4-I01 — storage models and enums`

Build typed models/enums only.

Tests:

- model validation;
- enum/failure vocabulary;
- deterministic serialization.

### `SENSOR-B4-I02 — content addressing, paths, checksums`

Build:

- SHA256 streaming;
- path derivation;
- storage object IDs;
- zstd metadata.

Tests:

- byte identity;
- path safety;
- large streaming hash.

### `SENSOR-B4-I03 — atomic filesystem backend`

Build:

- staging;
- fsync/rename;
- blob put/open/verify;
- immutable write guard.

Tests:

- atomic crash boundaries;
- duplicate blob write.

### `SENSOR-B4-I04 — acquisition and manifest repository`

Build:

- acquisitions;
- blob metadata;
- partition manifest append versions;
- current pointer semantics.

Tests:

- referential integrity;
- concurrent manifest versioning.

### `SENSOR-B4-I05 — raw projection and lineage layer`

Build T0B Parquet projection contracts and lineage.

Tests:

- source refs;
- schema versions;
- multi-blob projection.

### `SENSOR-B4-I06 — revision/source mutation handling`

Build explicit revision registry.

Tests:

- identical refetch;
- mutated source;
- ambiguity resolution.

### `SENSOR-B4-I07 — durable job state and resume coupling`

Build storage job transitions and Bloc 3 resume integration.

Tests:

- cursor never advances before manifest durability;
- restart after each state.

### `SENSOR-B4-I08 — recovery/quarantine scanner`

Build orphan/staging/corruption recovery.

Tests:

- full crash matrix;
- quarantine paths.

### `SENSOR-B4-I09 — quota and storage estimator`

Build:

- watermarks;
- priority classes;
- size estimation;
- safe pause decisions.

Tests:

- P2 pauses before P0;
- no destructive auto-delete.

### `SENSOR-B4-I10 — DuckDB discovery catalog`

Build manifest-backed DuckDB bootstrap/views.

Tests:

- destroy/rebuild catalog;
- compare query results.

### `SENSOR-B4-I11 — PostgreSQL operational metadata repository`

Build metadata/state persistence only.

Tests:

- no raw payload storage;
- reconstruction/import interfaces.

### `SENSOR-B4-I12 — raw evidence query/replay API`

Build:

- RawEvidenceQuery;
- readers;
- revision modes;
- raw replay cursor.

Tests:

- range/revision/integrity behavior.

### `SENSOR-B4-I13 — export/backup/restore pack`

Build checksum-verified local export/restore.

Tests:

- fresh-root restore;
- catalog rebuild;
- hash parity.

### `SENSOR-B4-I14 — Bloc 3 integration`

Wire production adapter `FetchBatch` / `RawPayloadEnvelope` to storage writer.

Use fixtures, not live network.

### `SENSOR-B4-I15 — hardening and security`

Run:

- secret scan;
- path traversal;
- symlink escape;
- corruption handling;
- resource bounds.

### `SENSOR-B4-I16 — final acceptance + evidence packet`

Run all G4 gates and produce evidence.

### `SENSOR-B4-I17 — Bloc 5 handoff`

Document stable public interfaces, schema versions, known limitations, and normalization-ready evidence contract.

---

## 12. Commit discipline

Each commit must:

1. start from latest branch head;
2. touch only its planned responsibility unless dependency fix is unavoidable;
3. include tests for new behavior;
4. run relevant subset plus regression suite;
5. record evidence summary;
6. avoid drive-by refactors;
7. never squash previous staged commits during build review.

Amendments may follow review, but history should show what changed and why.

---

## 13. Blocking conditions

Bloc 4 implementation is BLOCKED from completion if any of these remain:

- raw bytes can be overwritten;
- checksum identity is ambiguous;
- resume token can advance ahead of durable evidence;
- same request/different bytes silently replaces history;
- manifest points to missing object without loud integrity failure;
- T0B lineage is incomplete;
- disk pressure auto-deletes T0A;
- Postgres becomes bulk raw store;
- DuckDB becomes unique source of truth;
- secret credentials appear in persisted evidence metadata;
- Bloc 5 needs provider-specific filesystem knowledge.

---

## 14. Final implementation verdicts

Allowed:

```text
PASS_BLOC_04_IMPLEMENTED
PASS_BLOC_04_IMPLEMENTED_WITH_DATA_VOLUME_LIMITS
BLOCKED_BLOC_04_INTEGRITY
BLOCKED_BLOC_04_STORAGE_CAPACITY
FAIL_BLOC_04_ATOMICITY
FAIL_BLOC_04_LINEAGE
FAIL_BLOC_04_RESTORE
```

No “mostly works” verdict for raw evidence integrity.
