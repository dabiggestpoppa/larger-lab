# BLOC 4 — IMMUTABLE T0 RAW EVIDENCE LAKE ARCHITECTURE

**Planning status:** implementation-grade architecture  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Parent:** BLOC 3 `PASS_BLOC_03_PLAN_FROZEN`  
**Purpose:** define the durable local-first storage boundary that receives provider-adapter evidence before any PIT normalization, cross-venue synthesis, or research feature construction.

---

## 1. Governing principle

T0 is evidence, not an analytics table.

```text
PROVIDER / ARCHIVE / STREAM
        ↓
BLOC 3 ADAPTER
        ↓
RAW PAYLOAD ENVELOPE
        ↓
T0 IMMUTABLE EVIDENCE LAKE
        ↓
LOSSLESS RAW PROJECTION [optional/rebuildable]
        ↓
BLOC 5 PIT IDENTITY + SEMANTIC NORMALIZATION
```

Hard rule:

> If the source evidence cannot be reconstructed byte-for-byte or traced to an immutable source artifact plus acquisition metadata, it is not durable T0 evidence.

T0 must preserve enough source-native truth to re-parse the provider years later under a new parser without relying on the current parser implementation.

---

## 2. Scope

### In scope

- exact provider payload preservation;
- content-addressed immutable blobs;
- acquisition records;
- request fingerprints from Bloc 3;
- partition manifests;
- source checksums;
- archive/file integrity;
- stream chunking;
- raw provider-native projections;
- atomic writes;
- append/revision semantics;
- crash recovery;
- deterministic discovery;
- storage footprint controls;
- local-first backup/export;
- evidence query contract;
- durable resume/job state linkage;
- provenance into Bloc 5.

### Out of scope

- canonical instrument identity;
- OI/funding/notional normalization;
- cross-provider dedupe by economic event;
- provider failover synthesis;
- LiquidationState / LeverageState / OrderFlowState formulas;
- historical backfill execution at scale;
- live collector orchestration;
- strategy, PnL, execution or trading logic.

Those belong to later blocs.

---

## 3. T0 has two evidence forms

A single representation is insufficient because exact source bytes and convenient row-wise access solve different problems.

### T0A — SOURCE ARTIFACT EVIDENCE

The exact response/file/frame payload received from the provider.

Examples:

- HTTP response body bytes;
- provider `.zip`, `.gz`, `.csv`, `.json`, `.parquet` bulk file;
- WebSocket frame payload;
- streamed NDJSON/CSV chunk constructed from exact received frames;
- source manifest/checksum file when supplied by provider.

T0A is authoritative evidence.

### T0B — RAW RECORD PROJECTION

A lossless provider-native row projection generated from T0A for efficient local inspection.

Examples:

- Binance aggTrade rows with provider-native columns;
- Gate contract-stat rows;
- Kraken analytics rows;
- raw order-book snapshot rows.

T0B rules:

1. it MUST reference one or more T0A blob hashes;
2. it MUST preserve provider-native values and names or a reversible field map;
3. it is rebuildable and therefore not more authoritative than T0A;
4. it MUST NOT introduce canonical asset semantics;
5. it MUST NOT perform cross-venue aggregation;
6. if projection and source artifact disagree, T0A wins and projection is invalidated.

---

## 4. Core storage objects

### 4.1 `EvidenceBlob`

Immutable content-addressed source bytes.

Required metadata:

```text
blob_sha256
byte_length
stored_byte_length
source_media_type
storage_encoding
compression
created_at
storage_uri
integrity_state
```

`blob_sha256` is computed over the exact unmodified source bytes before optional local storage compression/wrapping.

A single blob may be referenced by multiple acquisitions when the same content is retrieved repeatedly.

### 4.2 `AcquisitionRecord`

Represents the act of acquiring evidence.

```text
acquisition_id
provider
venue
sensor_family
request_fingerprint
adapter_version
adapter_capability_version
requested_start
requested_end
native_instrument
native_granularity
request_started_at
response_observed_at
ingested_at
http_status_or_source_status
source_locator
blob_sha256
provider_checksum
resume_token_before
resume_token_after
quality_flags
failure_ref
```

Multiple `AcquisitionRecord`s may point to the same `EvidenceBlob`.

This preserves repeated acquisition evidence without duplicating bytes.

### 4.3 `RawProjectionArtifact`

Optional T0B provider-native projection.

```text
projection_id
source_blob_sha256[]
projection_schema_id
projection_schema_version
parser_version
row_count
min_provider_time
max_provider_time
partition_key
projection_uri
projection_sha256
quality_flags
```

### 4.4 `PartitionManifest`

Logical coverage/index object.

```text
manifest_id
manifest_version
provider
venue
sensor_family
native_instrument
logical_date_start
logical_date_end
blob_refs[]
projection_refs[]
row_count_if_known
min_time
max_time
coverage_state
integrity_state
revision_count
created_at
supersedes_manifest_id
```

A manifest is versioned and append-only. New manifests supersede prior manifests; old manifests are never mutated out of existence.

### 4.5 `StorageJobState`

Durable job-state pointer linking Bloc 3 resume semantics to storage durability.

```text
job_id
provider
sensor_family
request_fingerprint
resume_token
last_committed_acquisition_id
last_committed_blob_sha256
last_manifest_id
status
updated_at
```

The resume token may advance only after its corresponding evidence blob and acquisition record are durable.

---

## 5. Content-addressed storage doctrine

T0A bytes use SHA-256 content addressing.

Conceptual path:

```text
<t0_root>/blobs/sha256/ab/cd/<full_sha256>.blob[.zst]
```

The path is independent of provider naming.

Provider/sensor/date discovery is performed through manifests/index metadata rather than duplicating the same blob into many directory trees.

Benefits:

- exact duplicate downloads occupy one blob;
- provider retries remain auditable as separate acquisition records;
- source mutation is detectable;
- checksums are first-class;
- manifests can be rebuilt from metadata;
- future object-storage migration does not change evidence identity.

Content-addressing MUST NOT be used to claim two economically distinct provider events are the same. It deduplicates bytes only.

---

## 6. Logical partition model

Logical partitions are defined independently from physical blob paths.

Minimum partition coordinates:

```text
provider
venue
sensor_family
native_instrument
logical_date
source_granularity
```

Recommended logical partition hierarchy:

```text
provider=<provider>/
venue=<venue>/
sensor=<sensor>/
instrument=<native_instrument>/
year=<YYYY>/month=<MM>/day=<DD>/
```

This hierarchy is used for T0B projections and manifest discovery, NOT for duplicating T0A content blobs.

### Partition-size rule

Do not blindly use one file per minute, request, or event.

Target T0B projection files should generally land in a useful analytical file-size range (implementation should start around 128–512 MiB target uncompressed/logical payload and tune empirically).

For low-volume data such as funding/OI/liquidation summaries, daily or monthly files may be appropriate.

For high-volume trades/books, shard within a day:

```text
part-00000.parquet
part-00001.parquet
...
```

No tiny-file explosion.

---

## 7. Source-boundary preservation

Provider archives and APIs have meaningful native boundaries that must not be erased at T0A.

Examples:

- Binance monthly archive remains one exact source blob even if projected into daily T0B partitions;
- an OKX downloadable order-book artifact remains one source blob;
- a Kraken REST page remains traceable to its exact response bytes;
- a WebSocket stream chunk must preserve frame ordering and receive metadata.

A T0B partition may contain rows from multiple T0A blobs, but lineage must remain complete.

---

## 8. REST/API payload handling

For JSON/CSV REST responses:

1. capture exact body bytes;
2. capture relevant response headers separately;
3. hash original body bytes;
4. optionally store body using local zstd compression;
5. store compression metadata in `EvidenceBlob`;
6. create `AcquisitionRecord` only after blob durability;
7. optionally parse into T0B;
8. create/update append-only logical manifest.

Never pretty-print/re-serialize JSON and call it raw evidence.

---

## 9. Bulk archive handling

If provider supplies an archive/file:

1. preserve downloaded bytes exactly;
2. compute local SHA-256;
3. preserve provider checksum when offered;
4. verify provider checksum before `integrity_state=VERIFIED`;
5. retain source URL/object key and retrieval time;
6. extraction happens into a temporary workspace;
7. T0B projection is generated from extracted contents;
8. extracted temporary files may be removed after projection if the original archive is preserved and re-extraction is deterministic.

Corrupt archives are retained only in quarantine, never promoted to usable evidence.

---

## 10. Streaming/WebSocket evidence

Streaming payload volume requires chunked immutable evidence.

Proposed model:

```text
StreamSession
  ↓
StreamChunk 0001
StreamChunk 0002
...
```

Each chunk contains exact received payloads plus enough framing metadata to reconstruct order.

Minimum frame metadata:

```text
session_id
frame_sequence
received_at
provider_event_time_if_present
payload_length
payload_bytes
connection_generation
```

Chunks are closed by one or more of:

- target byte size;
- maximum wall-clock duration;
- graceful connection restart;
- day boundary.

Recommended initial targets are implementation-tunable, e.g. 256–1024 MiB compressed or 15–60 minute chunks for high-volume streams.

Chunk closure must be atomic and checksummed.

Partial open chunks after crash are recovered/quarantined according to the atomic-write protocol.

---

## 11. Response headers and acquisition context

Do not store only bodies.

Evidence metadata should preserve useful non-secret headers such as:

- content type;
- content length;
- ETag;
- Last-Modified;
- provider request ID;
- rate-limit headers;
- checksum headers;
- content encoding.

Secrets/auth tokens MUST be redacted before persistence.

No API key, cookie, bearer token, signed credential, or private account identifier may enter T0 manifests.

---

## 12. Immutability model

The following are immutable once committed:

- T0A blob bytes;
- blob SHA;
- acquisition facts as originally observed;
- provider checksum evidence;
- raw projection artifact contents;
- historical manifest versions.

Corrections happen by appending new objects.

Never edit an old raw artifact in place.

---

## 13. Append/revision semantics

### Same request, same bytes

```text
request_fingerprint same
blob_sha256 same
```

Create a new acquisition record if the request was genuinely repeated, but reuse the existing blob.

### Same request, different bytes

```text
request_fingerprint same
blob_sha256 differs
```

Store BOTH blobs and flag:

`SOURCE_MUTATION`

Then establish a revision relationship.

Do not silently replace the earlier source.

### Provider republishes an archive

Store the new artifact as a separate revision even if its URL/file name is identical.

### Parser improves

T0A does not change.

Create a new T0B projection version tied to the same source blob(s).

---

## 14. Missing data

T0 storage distinguishes:

```text
NO_ACQUISITION_ATTEMPT
ACQUISITION_FAILED
SOURCE_RETURNED_EMPTY
SOURCE_CONFIRMED_NO_DATA
HISTORICAL_RANGE_UNAVAILABLE
CAPABILITY_UNAVAILABLE
ACCESS_BLOCKED
GAP_DETECTED
```

None of these equal numeric zero.

Failure evidence belongs in operational metadata; no fake raw row should be emitted merely to fill a partition.

---

## 15. Local-first backend abstraction

The initial backend is local filesystem.

Required storage interface should nevertheless be narrow:

```text
put_blob_atomic()
blob_exists()
open_blob()
verify_blob()
put_projection_atomic()
open_projection()
list_manifest_refs()
storage_usage()
```

No cloud dependency in v1.

A future object-storage backend must preserve identical blob IDs, manifests and semantics.

---

## 16. Directory proposal

Implementation target:

```text
quant-lab-data/
  crypto_sensor_fabric/
    t0/
      blobs/
        sha256/
      projections/
        provider=.../
        venue=.../
        sensor=.../
        instrument=.../
        year=.../
        month=.../
        day=.../
      quarantine/
      staging/
      exports/

    catalogs/
      manifests/
      coverage/

    duckdb/
      sensor_fabric.duckdb
```

The actual data root MUST be configurable and MUST NOT be committed to Git.

Git contains code, schema, fixture-size evidence and manifests/coverage summaries only.

---

## 17. Repository implementation proposal

Later execution agent should build roughly:

```text
quant-lab/src/crypto_sensor_fabric/storage/
  __init__.py
  models.py
  blob_store.py
  filesystem_backend.py
  atomic.py
  checksums.py
  projections.py
  manifests.py
  catalog.py
  jobs.py
  retention.py
  quota.py
  recovery.py
  query.py
  export.py

quant-lab/config/crypto_sensor_fabric/
  storage.yaml
  retention.yaml

quant-lab/tests/crypto_sensor_fabric/storage/
  test_blob_store.py
  test_atomic.py
  test_checksums.py
  test_manifests.py
  test_revisions.py
  test_jobs.py
  test_recovery.py
  test_quota.py
  test_query.py
```

---

## 18. Non-negotiable invariants

1. `SHA256(read(blob)) == blob_sha256` after decoding local storage compression.
2. A resume token may never point past evidence not yet durably committed.
3. No manifest may reference a nonexistent blob/projection.
4. T0A is immutable.
5. T0B is versioned and rebuildable.
6. Repeated acquisition never destroys prior evidence.
7. Source mutation is surfaced.
8. No secrets are persisted.
9. Provider identity is preserved.
10. No cross-provider economic synthesis occurs in T0.
11. Missingness is explicit.
12. High-volume storage pressure may pause ingestion but may not silently delete evidence.
13. Research code does not query T0 directly once canonical layers exist; T0 is evidence/reconstruction infrastructure.

---

## 19. Bloc 4 completion target

Planning is complete only when later implementation can answer:

- where exact source bytes live;
- how duplicate bytes are deduplicated without losing acquisition history;
- how revisions are preserved;
- how stream evidence is chunked;
- how projection files remain lossless/rebuildable;
- how atomicity is guaranteed;
- how disk pressure is handled;
- how manifests/indexes are maintained;
- how evidence is queried and exported;
- how Bloc 3 resume tokens become durable only after committed evidence;
- how Bloc 5 receives complete provenance.
