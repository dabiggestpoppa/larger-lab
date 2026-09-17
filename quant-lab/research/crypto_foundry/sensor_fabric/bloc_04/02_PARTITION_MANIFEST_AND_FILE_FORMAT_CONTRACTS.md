# BLOC 4 — PARTITION, MANIFEST & FILE-FORMAT CONTRACTS

**Purpose:** freeze logical partitioning, physical evidence layout, raw projection formats, manifest schemas, and discovery contracts for the immutable T0 lake.

---

## 1. Separation of concerns

Bloc 4 uses three different indexing concepts. They MUST NOT be collapsed.

```text
PHYSICAL BLOB ADDRESS
  content-addressed by SHA256

LOGICAL PARTITION
  provider / venue / sensor / instrument / date / granularity

ACQUISITION RECORD
  one concrete fetch/download/stream-chunk event
```

The same physical blob may satisfy multiple acquisition records only when the exact bytes are identical.

---

## 2. Physical T0A blob format

### 2.1 Exact-byte identity

`blob_sha256` is SHA-256 of exact provider-source bytes prior to any local wrapper compression.

### 2.2 Storage compression

Allowed local wrapper encodings:

```text
NONE
ZSTD
```

Do not recompress already-compressed archives by default when negligible benefit would result.

Examples:

- `.zip`, `.gz`, `.zst`, `.parquet` source artifact → generally store exact bytes directly;
- REST JSON body → may be stored as `.blob.zst`;
- text CSV response → may be zstd wrapped;
- binary WebSocket frame chunks → zstd wrapped if beneficial.

Storage compression MUST be reversible without changing the source hash.

### 2.3 Blob path

```text
<t0_root>/blobs/sha256/<h0h1>/<h2h3>/<sha256>.blob
<t0_root>/blobs/sha256/<h0h1>/<h2h3>/<sha256>.blob.zst
```

No provider-controlled path component enters the content-addressed blob path.

---

## 3. T0B projection format

Default T0B analytical projection format:

**Apache Parquet via PyArrow-compatible schema.**

Reasons:

- typed;
- columnar;
- compressed;
- DuckDB/Polars compatible;
- easy partition discovery;
- deterministic schema versioning;
- local-first.

### Projection rules

T0B projection fields should preserve provider-native meaning.

Each projection row receives metadata columns in addition to provider-native content:

```text
_t0_projection_id
_t0_source_blob_sha256
_t0_acquisition_id
_t0_provider
_t0_venue
_t0_sensor_family
_t0_native_instrument
_t0_parser_version
_t0_schema_version
_t0_row_ordinal
```

For a projection produced from more than one source blob, use a lineage table rather than repeating an unbounded array in every row.

No canonical asset ID is required at T0B.

---

## 4. Projection schema registry

Every T0B file uses a `projection_schema_id` and semantic version.

Example:

```text
kraken_futures.market_analytics.liquidation_volume@1.0.0
binance_usdm.agg_trades@1.1.0
okx_swap.orderbook_snapshot@1.0.0
```

Version rules:

- PATCH: metadata/documentation change with identical row semantics;
- MINOR: backward-compatible additive field;
- MAJOR: field removal, type change, timestamp-semantic change, or semantic reinterpretation.

Old projections remain readable under their original schema version.

---

## 5. Logical partition key

Canonical T0 logical partition key:

```text
provider
venue
sensor_family
native_instrument
source_granularity
logical_date
```

`logical_date` should derive from provider-event/effective timestamp when that meaning is defensible. If the provider artifact has no event-level time and is published as a dated snapshot/file, use its native source date and record the date basis.

Never silently use ingestion date as event date.

Additional partition metadata:

```text
date_basis = EVENT_TIME | PROVIDER_FILE_DATE | SNAPSHOT_TIME | UNKNOWN
```

---

## 6. Projection path

Suggested path:

```text
<t0_root>/projections/
  provider=<provider>/
  venue=<venue>/
  sensor=<sensor_family>/
  instrument=<escaped_native_instrument>/
  granularity=<native_granularity>/
  year=<YYYY>/
  month=<MM>/
  day=<DD>/
  schema=<schema_id_hash>/
  part-<shard_id>-<projection_sha256_prefix>.parquet
```

Instrument path escaping must be deterministic and reversible.

Native instrument string remains inside file metadata.

---

## 7. File-size policy

Avoid both tiny-file explosion and giant monoliths.

Initial configurable targets:

```text
projection_target_size_mb = 256
projection_min_size_mb = 32
projection_max_size_mb = 1024
```

These are implementation defaults, not scientific constants.

Low-volume sensor families may violate minimum size to preserve natural daily/monthly boundaries.

High-volume book/trade projections may shard more aggressively.

Compaction may merge T0B projections LOSSLESSLY after validation; T0A blobs never compact semantically.

---

## 8. Manifest hierarchy

### 8.1 Blob manifest

One row per `EvidenceBlob`.

Suggested fields:

```text
blob_sha256 STRING PK
byte_length UINT64
stored_byte_length UINT64
source_media_type STRING
compression STRING
storage_uri STRING
integrity_state STRING
created_at TIMESTAMP_UTC
```

### 8.2 Acquisition manifest

One row per acquisition event.

```text
acquisition_id STRING PK
request_fingerprint STRING
provider STRING
venue STRING
sensor_family STRING
native_instrument STRING
native_granularity STRING
requested_start TIMESTAMP_UTC?
requested_end TIMESTAMP_UTC?
response_observed_at TIMESTAMP_UTC
ingested_at TIMESTAMP_UTC
source_locator STRING?
blob_sha256 STRING?
provider_checksum STRING?
adapter_version STRING
capability_evidence_ref STRING?
resume_token_before JSON?
resume_token_after JSON?
status STRING
quality_flags LIST<STRING>
failure_ref STRING?
```

### 8.3 Projection manifest

```text
projection_id STRING PK
provider STRING
venue STRING
sensor_family STRING
native_instrument STRING
source_granularity STRING
logical_date_start DATE
logical_date_end DATE
projection_schema_id STRING
projection_schema_version STRING
parser_version STRING
projection_uri STRING
projection_sha256 STRING
row_count UINT64
min_provider_time TIMESTAMP_UTC?
max_provider_time TIMESTAMP_UTC?
lineage_ref STRING
quality_flags LIST<STRING>
created_at TIMESTAMP_UTC
```

### 8.4 Logical partition manifest

```text
partition_manifest_id STRING PK
partition_key STRING
manifest_version UINT32
coverage_state STRING
integrity_state STRING
blob_count UINT32
projection_count UINT32
row_count UINT64?
min_time TIMESTAMP_UTC?
max_time TIMESTAMP_UTC?
gap_count UINT32?
revision_count UINT32
supersedes_manifest_id STRING?
created_at TIMESTAMP_UTC
```

---

## 9. Manifest storage strategy

Two copies with different roles:

### Durable analytical manifests

Parquet append files under:

```text
<t0_root>/catalogs/manifests/
```

These are exportable/rebuildable evidence catalog snapshots.

### Operational manifest/state database

PostgreSQL stores current operational state and searchable metadata.

PostgreSQL is NOT the raw data store.

It may store:

- blob metadata;
- acquisitions;
- current partition manifest pointer;
- storage job state;
- source revisions;
- integrity results;
- quota state;
- backup state.

A PostgreSQL loss must be recoverable from the lake manifests plus source evidence, though rebuilding may be expensive.

---

## 10. Manifest commit ordering

Correct ordering:

```text
1. acquire bytes
2. stage bytes
3. compute source SHA256
4. write blob atomically
5. verify durable blob
6. commit EvidenceBlob metadata
7. commit AcquisitionRecord
8. create/verify T0B projection [if configured]
9. commit ProjectionManifest
10. create new logical PartitionManifest version
11. advance StorageJobState / resume token
```

Never advance step 11 before all required prior durable steps complete.

---

## 11. Lineage contract

Every T0B projection must be traceable to T0A.

For simple cases:

```text
projection_id → blob_sha256
```

For multi-blob projections:

```text
projection_id
  → lineage_manifest_id
      → ordered source blobs / acquisitions
```

Lineage record fields:

```text
lineage_manifest_id
projection_id
source_blob_sha256
source_acquisition_id
source_row_start?
source_row_end?
source_order
```

Exact row-level lineage is required only when practical. At minimum, file-level lineage must be complete.

---

## 12. Revisions and source mutation

Define source revision key:

```text
provider
source_locator_or_request_fingerprint
native_instrument
sensor_family
requested/native period
```

When bytes differ under the same revision key:

```text
revision_number += 1
source_mutation = true
```

Both versions remain accessible.

The later canonical layer must choose which revision is valid for a given research mode; T0 does not delete or rewrite history.

---

## 13. Provider checksums

If provider publishes MD5/SHA256/CRC checksums:

Store:

```text
provider_checksum_algorithm
provider_checksum_value
provider_checksum_verified
```

Local SHA-256 remains mandatory even when provider checksum exists.

Provider checksum mismatch → `QUARANTINED_INTEGRITY_FAILURE`.

No projection from a failed source artifact may be marked usable.

---

## 14. Stream chunk manifest

Streaming chunks need explicit session context.

```text
stream_session_id
provider
venue
endpoint/feed
native_instrument
sensor_family
connection_generation
session_started_at
session_ended_at
chunk_sequence
first_frame_received_at
last_frame_received_at
first_provider_event_time?
last_provider_event_time?
frame_count
blob_sha256
previous_chunk_sha256?
```

Optional hash chaining may be used:

```text
chunk_chain_hash = SHA256(previous_chunk_chain_hash || blob_sha256 || metadata_hash)
```

This is an integrity aid, not a blockchain requirement.

---

## 15. Coverage states

Logical partition coverage vocabulary:

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

A partition can be `PARTIAL` while its existing blobs are individually `VERIFIED`.

Integrity and coverage are separate concepts.

---

## 16. Integrity states

```text
UNVERIFIED
LOCAL_HASH_VERIFIED
PROVIDER_HASH_VERIFIED
QUARANTINED_INTEGRITY_FAILURE
MISSING_BLOB
PROJECTION_INVALID
```

A future storage scrubber may upgrade/downgrade integrity states without altering evidence bytes.

---

## 17. DuckDB discovery views

DuckDB should expose catalog-level discovery, not force analysts to parse paths manually.

Planned views:

```text
v_t0_blobs
v_t0_acquisitions
v_t0_projections
v_t0_partitions
v_t0_gaps
v_t0_revisions
v_t0_storage_usage
```

Provider-native projection views may be added per schema family.

DuckDB must be rebuildable from Parquet manifests.

No research conclusion should depend on a manually edited DuckDB table.

---

## 18. Query contract

`RawEvidenceQuery` should support:

```text
provider?
venue?
sensor_family?
native_instrument?
source_granularity?
logical_start?
logical_end?
acquired_before?
revision_policy
integrity_minimum
include_t0a
include_t0b
```

`revision_policy` options:

```text
ALL
LATEST_ACQUIRED
FIRST_ACQUIRED
EXACT_REVISION
```

T0 query results MUST expose revision ambiguity rather than silently selecting a revision when policy is unspecified.

---

## 19. PIT warning

`ingested_at` means when OUR system stored evidence.

It does NOT necessarily equal when the market could have known the data historically.

Bloc 4 must preserve:

- provider event/effective timestamps when available;
- provider publication/file timestamps when available;
- observed/response time;
- ingestion time.

Bloc 5 defines actual PIT/canonical availability semantics.

Raw query APIs must therefore avoid using `ingested_at` as a substitute for historical effective time.

---

## 20. Acceptance outcomes

Bloc 4 file/manifest design is acceptable only if:

1. exact source bytes remain independently verifiable;
2. projections are rebuildable;
3. same bytes are deduped without losing acquisition history;
4. revisions never overwrite prior bytes;
5. manifests remain append-only/versioned;
6. logical partitions do not force physical duplication;
7. stream evidence preserves order;
8. all coverage/missingness states are explicit;
9. DuckDB views are rebuildable;
10. Bloc 5 can trace every canonical row back to source evidence.
