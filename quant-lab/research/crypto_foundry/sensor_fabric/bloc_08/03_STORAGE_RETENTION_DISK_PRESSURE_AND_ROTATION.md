# BLOC 8 — STORAGE, RETENTION, DISK PRESSURE & ROTATION

**Planning status:** COMPLETE FOR THIS CHAPTER  
**Implementation status:** NOT STARTED

---

## 1. Objective

Define how continuously arriving live evidence is durably chunked, rotated, retained, compacted, and throttled without violating Bloc 4 immutability or letting high-volume feeds crowd out critical mechanical sensors.

---

## 2. Storage invariants inherited from Bloc 4

Live recording inherits:

```text
T0A exact bytes are authoritative
T0B projections are rebuildable
raw evidence is immutable
source revisions append
disk pressure pauses before deletion
DuckDB is discovery, not truth
Postgres is metadata/state, not raw payload storage
```

Bloc 8 adds only forward-stream lifecycle rules.

---

## 3. Stream chunking model

Live feeds arrive as unbounded streams, so T0A cannot rely on one file per process lifetime.

Each stream is written into bounded `LiveEvidenceChunk` objects.

Required metadata:

```text
chunk_id
provider_id
venue_id
feed_id
session_id
sensor_family
instrument_scope
chunk_opened_at
chunk_closed_at
first_source_event_at
last_source_event_at
first_receive_at
last_receive_at
message_count
uncompressed_bytes
stored_bytes
sha256
compression
integrity_status
```

---

## 4. Chunk boundary triggers

A chunk closes when any configured trigger fires:

```text
TIME_LIMIT
SIZE_LIMIT
MESSAGE_COUNT_LIMIT
SESSION_END
SEQUENCE_RESET
SCHEMA_VERSION_CHANGE
SOURCE_MUTATION_BOUNDARY
GRACEFUL_SHUTDOWN
```

Example defaults may differ by feed.

High-volume trades/books likely use shorter/smaller chunks than OI polling.

---

## 5. Exact-byte semantics for WebSocket streams

For WebSocket feeds, exact source evidence should preserve each provider payload as received plus framing metadata sufficient to reconstruct message boundaries.

Allowed storage form:

```text
length-prefixed binary records
or
newline-delimited exact text payloads when provider frames are textual and delimiter-safe
```

The implementation must not parse JSON and reserialize it as the only T0A representation because key ordering/whitespace can change exact bytes.

---

## 6. REST poll evidence

Each REST poll remains an independent Bloc 4 acquisition/evidence object.

Live orchestration may group metadata operationally, but it may not concatenate and erase request boundaries.

---

## 7. T0B live projection layout

Recommended logical partition:

```text
T0B/
  provider=<provider>/
  venue=<venue>/
  sensor=<sensor>/
  instrument=<native_or_scope>/
  date=YYYY-MM-DD/
  hour=HH/
```

Fine partitioning is logical, not physical T0A blob duplication.

Hourly is a default discovery boundary for high-frequency live evidence, configurable by sensor.

---

## 8. Rotation frequency by sensor class

Initial planning guidance:

```text
P0 low-volume mechanics
  hour/day logical projection

P1 trades/events
  5m-60m chunks depending volume

P2 deep books
  1m-15m chunks depending venue/message rate
```

No final byte thresholds are frozen before pilot measurement.

---

## 9. Retention doctrine

### P0 critical mechanical evidence

```text
LIQUIDATIONS
OI
FUNDING
POSITIONING
BASIS
GAP/HEALTH METADATA
```

Target: permanent local retention where storage permits.

### P1 trades/aggressor inputs

Target: permanent compressed retention for U0/U1 where economically reasonable.

### P2 deep books

Target: selective permanent retention with stricter universe and disk controls.

### P3 rebuildable projections/caches

May be evicted and rebuilt.

---

## 10. Live disk states

Use Bloc 4 states:

```text
NORMAL       <70%
WATCH        >=70%
CONSTRAINED  >=85%
CRITICAL     >=95%
```

Plus absolute free-space floors.

The implementation must evaluate both percentage and absolute headroom because a 4TB disk at 90% free remaining differs operationally from a 256GB disk at 90% used.

---

## 11. Disk-pressure response matrix

### NORMAL

- all authorized feeds operate;
- normal chunk/compaction cadence.

### WATCH

- forecast storage growth;
- suppress optional new P2 subscriptions;
- compact rebuildable projections more aggressively;
- emit operator warning.

### CONSTRAINED

- stop new deep-book/U2 optional feeds;
- reduce authorized book depth/sampling only through explicit configured fallback profile;
- retain P0/P1;
- pause nonessential background compactions requiring large temp space.

### CRITICAL

- stop new acquisition safely before filesystem exhaustion;
- commit/close current chunks if possible;
- preserve manifests/checkpoints;
- never silently delete T0A;
- mark `STORAGE_CRITICAL_STOP`.

---

## 12. No silent fidelity downgrade

If the recorder changes from:

```text
FULL_L2
```

to:

```text
TOP20_SNAPSHOT_1S
```

under resource pressure, that is a new acquisition profile and must be explicit in metadata.

It cannot masquerade as the same feed quality.

---

## 13. Retention profiles

Proposed named profiles:

```text
RICH_U0
STANDARD_U1
LEAN_U2
EMERGENCY_P0_ONLY
```

Profile configuration is versioned.

Research queries can later exclude lower-fidelity periods if needed.

---

## 14. Book storage profiles

Possible book modes:

```text
FULL_DELTA
TOP_N_DELTA
PERIODIC_FULL_SNAPSHOT
NORMALIZED_BPS_METRICS_ONLY
DISABLED
```

Only `FULL_DELTA`/provider-native snapshots qualify for later full-book reconstruction.

Metric-only storage cannot be promoted to full book history.

---

## 15. Full-book reconstruction evidence

If full books are reconstructed from snapshot+deltas, store:

```text
snapshot_ref
first_delta_ref
last_delta_ref
sequence_range
checksum_results
reconstruction_version
```

Reconstructed books are T0B/T1 derived artifacts, not T0A exact provider evidence unless the provider itself sent complete snapshots.

---

## 16. Compaction policy

Compaction is allowed only for rebuildable layers.

Examples:

```text
small T0B Parquet files
DuckDB catalog fragments
cache tables
```

Compaction must preserve:

- row lineage;
- source references;
- schema versions;
- exact T0A references.

No compaction may discard unique T0A evidence.

---

## 17. Compression policy

Allowed default:

```text
zstd
```

Compression occurs after SHA-256 identity is computed over exact source bytes when the source bytes are the canonical content-addressed object.

Compression level may differ by feed and CPU budget.

---

## 18. Write amplification control

High-frequency feeds must avoid pathological tiny sync writes.

Allowed strategy:

```text
append to bounded staging segment
→ periodic fsync
→ finalize chunk
→ hash
→ atomic commit
```

But checkpoints may advance only after durable committed evidence.

A crash may re-fetch/replay recent messages; it may not skip them because an in-memory buffer claimed progress.

---

## 19. T1 live write cadence

T1 normalization need not occur message-by-message for every feed.

Allowed modes:

```text
STREAMING_NORMALIZE
MICROBATCH_NORMALIZE
CHUNK_CLOSE_NORMALIZE
```

Choice depends on sensor and downstream latency needs.

For v1 research infrastructure, microbatch/chunk normalization is preferred where it reduces complexity without losing PIT timing.

---

## 20. Storage accounting

Track by:

```text
provider
sensor
universe tier
instrument
T0A
T0B
T1
cache
```

Metrics:

```text
bytes_per_hour
bytes_per_day
compression_ratio
forecast_7d
forecast_30d
forecast_180d
```

Forecasts inform policy but do not auto-delete evidence.

---

## 21. Hot / warm / cold local tiers

Optional local storage abstraction:

```text
HOT
  recent active chunks / fast SSD

WARM
  closed historical local partitions

COLD_LOCAL
  external local drive / second local volume
```

This is physical placement only.

Semantic evidence identity remains unchanged.

---

## 22. Backup interaction

Live evidence inherits Bloc 4 backup states:

```text
UNBACKED
MANIFEST_BACKED
SECOND_COPY_VERIFIED
OFFSITE_VERIFIED
```

A live feed may operate while recent chunks remain UNBACKED, but the status must be visible.

No false backup claim.

---

## 23. Machine shutdown planning

On planned shutdown:

- rotate open chunks;
- fsync metadata;
- persist checkpoints;
- emit recorder offline interval start.

On restart:

- close unresolved prior session logically;
- classify shutdown gap;
- start repair planning if provider history supports it.

---

## 24. Unexpected power loss

Recovery procedure:

```text
scan staging area
→ verify finalized chunks
→ identify incomplete chunks
→ quarantine/truncate only with explicit recovery rules
→ restore last durable checkpoint
→ mark uncertain interval
→ reconnect
→ repair if possible
```

Never assume the tail of an incomplete chunk was fully written.

---

## 25. Forward gap registry storage

`LiveGap` records must be durable even if the raw market gap is unrepaired.

This registry becomes the bridge into Bloc 7 repair jobs.

---

## 26. Storage evidence outputs

Implementation should produce:

```text
live_storage_report.md
live_storage_by_sensor.parquet
chunk_integrity_report.parquet
disk_pressure_events.parquet
retention_profile_history.parquet
```

---

## 27. Acceptance tests

Test:

- chunk rotation by time/size/session;
- exact-frame preservation;
- crash during staging;
- crash after fsync before manifest;
- disk WATCH/CONSTRAINED/CRITICAL transitions;
- P2 suppression before P0;
- no automatic T0A deletion;
- explicit fidelity downgrade;
- compaction lineage;
- restart with incomplete chunk;
- storage forecast calculation.

---

## 28. Planning decision

The recorder must fail by pausing collection before it fails by destroying evidence or silently changing data fidelity.
