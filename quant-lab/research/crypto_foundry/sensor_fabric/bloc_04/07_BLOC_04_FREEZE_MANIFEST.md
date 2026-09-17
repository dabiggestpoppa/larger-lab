# BLOC 4 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze the immutable T0 raw-evidence lake before the execution agent builds storage or Bloc 5 defines PIT normalization.

---

## 1. Frozen decisions

### F1 — T0 is evidence, not analytics

T0 exists to preserve source truth and lineage.

### F2 — Two raw evidence forms

```text
T0A = exact source artifact bytes
T0B = lossless/rebuildable provider-native projection
```

T0A is authoritative.

### F3 — Content-addressed exact bytes

T0A uses SHA-256 over exact source bytes before local wrapper compression.

### F4 — Acquisitions are separate from blobs

Multiple retrievals can reference one identical blob while preserving repeated acquisition history.

### F5 — Physical blob address is separate from logical partition

Provider/sensor/date organization lives in manifests/projections, not duplicated blob trees.

### F6 — Raw projections default to Parquet

T0B is provider-native, schema-versioned, lineage-complete and rebuildable from T0A.

### F7 — Atomic commit ordering is mandatory

Blob durability precedes acquisition/manifest durability; manifest durability precedes resume advancement.

### F8 — At-least-once acquisition + idempotent storage

Duplicate acquisition is safer than skipped evidence.

### F9 — Raw artifacts are immutable

Corrections/revisions append new evidence; no in-place rewrite.

### F10 — Source mutation is first-class

Same request/source boundary returning different bytes becomes explicit `SOURCE_MUTATION` / revision history.

### F11 — Coverage and integrity are separate

A partial partition may contain verified blobs; a complete-looking partition may still have integrity failure.

### F12 — Missingness remains explicit

No acquisition, failed acquisition, provider empty, confirmed no data, history unavailable, access blocked and detected gaps remain distinct.

### F13 — No event-level economic dedupe in T0

Byte dedupe is allowed. Provider/event semantic dedupe belongs downstream.

### F14 — Disk pressure pauses before deleting

No automatic destructive T0A retention in v1.

Optional high-volume P2 data pauses before critical P0 mechanical sensors.

### F15 — Full-depth/book storage is universe-aware

Richest U0; selective/coarse U1; full U2 book collection disabled by default.

### F16 — DuckDB is rebuildable discovery

DuckDB is not truth.

### F17 — PostgreSQL is operational metadata only

No large raw market payloads/books/trades in Postgres.

### F18 — Backup claims are explicit

`UNBACKED`, `MANIFEST_BACKED`, `SECOND_COPY_VERIFIED`, `OFFSITE_VERIFIED` are distinct.

### F19 — Raw query boundary is provider-independent

Bloc 5 consumes `RawEvidenceQuery` / `RawNormalizationBatch`, not filesystem globs or adapter-native fetch methods.

### F20 — Historical market reconstruction differs from system acquisition replay

`ingested_at` is not silently used as historical market availability time.

### F21 — Bloc 5 may reinterpret semantics, never source evidence

Every T1 row must retain lineage back to T0.

---

## 2. Frozen core storage objects

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

---

## 3. Frozen storage priority classes

```text
P0 CRITICAL PERMANENT
  liquidations / OI / funding / positioning / basis / manifests

P1 HIGH-VALUE PERMANENT-COMPRESS
  trades/aggTrades / historical archives / liquidation-tagged trades

P2 HIGH-VOLUME SELECTIVE
  full/deep books / high-frequency live books / redundant long-tail trades

P3 REBUILDABLE
  T0B projections / DuckDB materializations / caches/indexes
```

No scientific conclusion is implied by storage priority.

---

## 4. Frozen disk-pressure states

Configurable initial defaults:

```text
NORMAL       <70%
WATCH        >=70%
CONSTRAINED  >=85%
CRITICAL     >=95%
```

Absolute free-space floors are also required.

At CONSTRAINED/CRITICAL, ingestion pauses according to priority; raw evidence is not silently deleted.

---

## 5. Frozen integrity vocabulary

```text
UNVERIFIED
LOCAL_HASH_VERIFIED
PROVIDER_HASH_VERIFIED
QUARANTINED_INTEGRITY_FAILURE
MISSING_BLOB
PROJECTION_INVALID
```

Frozen coverage vocabulary:

```text
COMPLETE_SOURCE_BOUNDARY
PARTIAL
KNOWN_GAP
EMPTY_CONFIRMED
NOT_ATTEMPTED
FAILED
ACCESS_BLOCKED
HISTORY_UNAVAILABLE
QUARANTINED
REVISION_CONFLICT
```

---

## 6. Frozen raw revision policies

Raw query revision modes:

```text
ERROR_ON_AMBIGUITY
ALL
FIRST_SEEN
LATEST_SEEN
EXACT_REVISION
PROVIDER_DECLARED_CANONICAL
```

Default research-safe behavior should fail on ambiguity rather than silently pick latest.

---

## 7. Frozen local storage components

```text
local filesystem = initial T0 backend
Parquet = default T0B projection format
DuckDB = rebuildable discovery/analysis
PostgreSQL = operational metadata/state
zstd = allowed wrapper compression
SHA256 = mandatory exact-source identity
```

No cloud dependency required.

---

## 8. Frozen planning history

```text
SENSOR-PLAN-B4A
  immutable T0 evidence architecture

SENSOR-PLAN-B4B
  partition / manifest / file-format contracts

SENSOR-PLAN-B4C
  integrity / atomicity / revision / recovery

SENSOR-PLAN-B4D
  storage footprint / retention / DuckDB / Postgres / backup

SENSOR-PLAN-B4E
  raw query / replay boundary / Bloc 5 handoff

SENSOR-PLAN-B4F
  acceptance tests / staged implementation commits

SENSOR-PLAN-ROADMAP-R1
  reconciled 12-bloc roadmap after adapter consolidation

SENSOR-PLAN-B4G
  freeze manifest
```

---

## 9. Frozen future implementation sequence

```text
SENSOR-B4-I01  models/enums
SENSOR-B4-I02  content addressing/paths/checksums
SENSOR-B4-I03  atomic filesystem backend
SENSOR-B4-I04  acquisition + manifest repository
SENSOR-B4-I05  raw projections + lineage
SENSOR-B4-I06  revisions/source mutation
SENSOR-B4-I07  durable job state/resume coupling
SENSOR-B4-I08  recovery/quarantine
SENSOR-B4-I09  quota/storage estimator
SENSOR-B4-I10  DuckDB discovery
SENSOR-B4-I11  PostgreSQL operational metadata
SENSOR-B4-I12  raw query/replay API
SENSOR-B4-I13  export/backup/restore
SENSOR-B4-I14  Bloc 3 integration
SENSOR-B4-I15  security/hardening
SENSOR-B4-I16  acceptance/evidence
SENSOR-B4-I17  Bloc 5 handoff
```

No squashing during staged implementation review.

---

## 10. Bloc 4 acceptance gates frozen

Implementation must later pass:

- exact-byte evidence;
- atomic durability;
- immutability;
- revision preservation;
- manifest referential integrity;
- T0B→T0A lineage;
- explicit missingness;
- safe storage-pressure behavior;
- DuckDB rebuild;
- metadata-only Postgres role;
- checksum-verified export/restore;
- Bloc 3 resume coupling;
- Bloc 5 normalization readiness.

Any failure in exact evidence, atomicity or lineage is blocking.

---

## 11. Roadmap reconciliation

The original planning README split adapters across Bloc 3 and Bloc 4.

Bloc 3 planning demonstrated that one common adapter architecture with all eight provider implementation books is more coherent and prevents duplicate contracts.

The authoritative roadmap is now `README.md` v0.2:

```text
1 Contracts/Semantics
2 Capability Probes
3 Provider Adapters
4 T0 Raw Evidence Lake
5 PIT Identity/Semantic Normalization
6 Quality/Redundancy/Failover
7 Historical Backfill
8 Live Black-Box Recorder
9 Mechanical Observable Fabric
10 Read-Only Canonical Sensor Service
11 Historical Replay/Market OS Bridge
12 Full Validation/Research Restart
```

This preserves a 12-bloc program while increasing architectural separation.

---

## 12. Bloc 5 handoff

Bloc 5 must design **PIT identity and semantic normalization** using the T0 evidence/query contracts frozen here.

Required topics:

1. canonical instrument identity;
2. listing/delisting lifecycle;
3. linear/inverse contracts;
4. base/quote/settlement assets;
5. contract multipliers;
6. provider timestamp meanings;
7. effective/observed/publication/ingestion semantics;
8. historical revision PIT policy;
9. OI native/base/USD normalization;
10. liquidation side/unit/notional normalization;
11. funding interval normalization;
12. aggressor-side semantics;
13. book/depth normalization;
14. row/event duplicate policy;
15. no-zero-fill;
16. quality flags;
17. native-value preservation;
18. complete T1→T0 lineage.

Bloc 5 cannot alter T0 source artifacts.

---

## 13. Completion checklist

- [x] exact T0A evidence object defined
- [x] T0B raw projection defined
- [x] content addressing defined
- [x] acquisitions separated from blobs
- [x] logical partition model defined
- [x] file-format policy defined
- [x] manifests/catalogs defined
- [x] checksums defined
- [x] revision/source mutation defined
- [x] atomic-write ordering defined
- [x] crash/recovery matrix defined
- [x] resume coupling defined
- [x] quarantine defined
- [x] storage priorities defined
- [x] disk watermarks defined
- [x] U0/U1/U2 book/trade retention defined
- [x] DuckDB role defined
- [x] PostgreSQL role defined
- [x] backup/export/restore defined
- [x] raw query/replay distinction defined
- [x] Bloc 5 interface defined
- [x] staged implementation commits defined
- [x] acceptance gates defined
- [x] master roadmap reconciled

---

## 14. Final planning verdict

`PASS_BLOC_04_PLAN_FROZEN`

Rationale:

The fabric now has an implementation-grade immutable evidence architecture: exact source bytes, content-addressed dedupe, acquisition provenance, lossless raw projections, logical manifests, revision preservation, crash-safe atomicity, durable resume coupling, local storage controls, high-volume retention rules, rebuildable DuckDB discovery, operational Postgres metadata, checksum-verified backup/export and a strict downstream query/lineage contract for PIT normalization.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 5`
