# BLOC 4 — STORAGE FOOTPRINT, RETENTION, DUCKDB, POSTGRES & BACKUP

**Purpose:** keep the T0 evidence lake durable and useful on a local workstation without allowing high-volume book/trade data to crowd out core mechanical evidence.

---

## 1. Local-first storage policy

Initial deployment assumes a single-user local machine.

No cloud storage is required.

The storage layer must nevertheless separate:

```text
EVIDENCE BYTES
ANALYTICAL PROJECTIONS
OPERATIONAL METADATA
DISCOVERY CATALOG
BACKUP/EXPORT STATE
```

so later migration to external disk/object storage does not change data semantics.

---

## 2. Storage priority classes

Not every sensor has equal scientific value per byte.

### P0 — CRITICAL PERMANENT

Small/medium volume and high research value:

- liquidations;
- open interest;
- funding;
- positioning ratios;
- basis;
- provider capability/coverage evidence;
- manifests/checksums.

Default: retain T0A permanently.

### P1 — HIGH-VALUE PERMANENT / COMPRESS

- trades/aggTrades used to reconstruct aggressor flow;
- provider historical archives;
- liquidation-tagged trades;
- raw book metrics where source does not expose full book.

Default: permanent under lossless compression/compaction.

### P2 — HIGH-VOLUME SELECTIVE

- full/deep order-book snapshots;
- high-frequency live book streams;
- redundant trade feeds across large long-tail universe.

Default: strongest retention for U0, selective/coarser retention for U1, generally metrics-only or no full raw book for U2 unless research explicitly promotes it.

### P3 — REBUILDABLE PROJECTION/CACHE

- T0B compacted projections;
- DuckDB materializations;
- local indexes.

May be rebuilt from T0A. Can be evicted before authoritative evidence if disk pressure demands.

---

## 3. Universe-aware retention

### U0 Mechanism Core

BTC, ETH, plus selected highest-liquidity perps.

Retain richest evidence:

- trades;
- liquidations;
- OI;
- funding;
- deep books where feasible;
- spread/depth/slippage source evidence;
- positioning/basis.

### U1 Broad Research Universe

Retain:

- liquidations;
- OI;
- funding;
- trades/agg flow where cost-effective;
- coarse book snapshots/metrics.

### U2 Long Tail

Retain primarily:

- OI;
- funding;
- liquidation stats;
- low-cost activity/positioning.

Full high-frequency orderbook collection is OFF by default for U2.

This is a storage policy, not a claim that long-tail liquidity is unimportant.

---

## 4. No automatic destructive retention in v1

Default policy:

> The fabric may pause optional ingestion under disk pressure, compact losslessly, or evict rebuildable caches, but it may not silently delete irreplaceable T0A evidence merely because it is old.

Destructive raw-evidence expiration requires explicit future operator policy and evidence-class reasoning.

Provider-reproducible archives may someday support local cache eviction, but v1 should not assume future provider availability.

---

## 5. Lossless compaction

Allowed:

- merge many small T0B Parquet files into larger Parquet projections;
- zstd-wrap uncompressed T0A REST/stream artifacts;
- consolidate stream frames into larger immutable chunks while preserving exact frame payload/order metadata;
- rebuild indexes/catalog files.

Not allowed:

- downsample T0A and delete originals;
- average book snapshots and call result raw;
- drop duplicate-looking provider rows from T0;
- alter numeric precision;
- replace multiple revisions with one revision.

Compaction itself must create lineage and validation evidence.

---

## 6. Disk watermark policy

Configurable defaults:

```text
NORMAL     < 70% data-volume utilization
WATCH      >=70%
CONSTRAINED >=85%
CRITICAL   >=95%
```

Implementation should support absolute free-space floors in addition to percentage thresholds.

### NORMAL

All authorized ingestion allowed.

### WATCH

- estimate projected storage growth;
- emit warnings;
- prioritize compaction of P3/T0B tiny files.

### CONSTRAINED

Pause/defer optional high-volume P2 collection/backfill first:

- long-tail orderbooks;
- redundant full-depth books;
- low-priority duplicate trade feeds.

Continue P0 critical mechanical sensors where safe.

### CRITICAL

Pause all non-essential writes before filesystem exhaustion.

Never delete raw automatically to make room.

Emit:

`STORAGE_CAPACITY_BLOCKED`.

---

## 7. Storage estimator

Before large backfills, provide a dry-run estimator using Bloc 2 capability evidence and small samples.

Estimate by:

```text
provider
sensor_family
universe_tier
instrument
expected_days
bytes_per_day_raw
bytes_per_day_projection
estimated_total
confidence_band
```

Particularly estimate:

- Binance/Bybit/OKX trade history;
- OKX/Kraken book history;
- live U0 L2 collection.

A backfill that exceeds configured disk budget must not begin silently.

---

## 8. Retention config

Proposed configuration:

```yaml
sensor_families:
  MECHANICAL_LIQUIDATION:
    priority: P0
    t0a_retention: permanent
  MECHANICAL_OPEN_INTEREST:
    priority: P0
    t0a_retention: permanent
  MECHANICAL_FUNDING:
    priority: P0
    t0a_retention: permanent
  MECHANICAL_TRADE:
    priority: P1
    u0: permanent
    u1: permanent_if_budget
    u2: selective
  MECHANICAL_BOOK_SNAPSHOT:
    priority: P2
    u0: richest_feasible
    u1: coarse_or_metrics
    u2: disabled_default
```

Actual values remain operator-configurable.

---

## 9. DuckDB role

DuckDB is the local analytical/discovery engine.

It is NOT durable truth.

Use it for:

- scanning T0B projections;
- querying manifest Parquet;
- coverage inspection;
- file-size/storage analytics;
- provider-native exploratory joins;
- later T1/T2 analytical access.

Do not insert hand-edited truth into DuckDB.

The database file can be deleted/rebuilt from manifests/projections.

---

## 10. DuckDB catalog bootstrap

Provide deterministic bootstrap command, e.g. conceptually:

```text
sensor-fabric catalog rebuild --root <data_root>
```

It should register/read:

```text
blobs manifest
acquisition manifest
projection manifest
partition manifests
coverage tables
```

Then produce views:

```text
v_t0_blobs
v_t0_acquisitions
v_t0_projections
v_t0_partitions
v_t0_gaps
v_t0_revisions
v_t0_quarantine
v_t0_storage_usage
```

Rebuilding catalog must not mutate evidence.

---

## 11. PostgreSQL role

PostgreSQL is the operational state store, not analytical bulk storage.

Tables/concepts:

```text
provider_registry
adapter_readiness
storage_jobs
storage_job_transitions
blobs_current_metadata
acquisitions
partition_manifest_current
source_revisions
integrity_checks
quota_state
backup_state
recovery_runs
```

Large raw payloads, trade rows, or full books do NOT belong in Postgres.

---

## 12. PostgreSQL rebuildability

Where possible, current metadata must be reconstructible from:

- versioned Parquet manifests;
- configuration in Git;
- T0 evidence/projection tree.

Operational-only transient fields such as locks/current job leases need not be recoverable historically.

A Postgres restore must never be the only route to recovering raw evidence inventory.

---

## 13. Backup classes

### B0 — UNBACKED

Only local primary copy exists.

### B1 — MANIFEST_BACKED

Git/config + catalog export exists, but evidence bytes have one copy.

### B2 — SECOND_COPY_VERIFIED

Evidence has a second verified filesystem copy, such as external drive/NAS.

### B3 — OFFSITE_VERIFIED

Future optional offsite copy. Not required now.

No UI/report may say “backed up” when state is B0/B1 for actual evidence bytes.

---

## 14. Local backup/export design

Provide deterministic export pack process:

```text
sensor-fabric export create \
  --provider ... \
  --sensor ... \
  --start ... \
  --end ... \
  --destination /external/path
```

Export contains:

- selected T0A blobs;
- selected T0B projections if requested;
- acquisition manifests;
- partition manifests;
- lineage manifests;
- checksums;
- export manifest.

Then verify destination hashes.

Do not rely on filesystem copy success alone.

---

## 15. Export manifest

```text
export_id
created_at
source_data_root
selection_query
blob_count
projection_count
total_bytes
manifest_sha256
objects[]
verification_state
```

Destination verification produces signed-by-system/hash evidence, not cryptographic identity claims beyond checksum integrity.

---

## 16. Restore test

A backup is not trusted until a sample restore works.

Required test:

1. export fixture-size evidence pack;
2. remove/repoint primary test catalog;
3. restore export into empty test root;
4. rebuild catalog;
5. verify blob hashes;
6. re-open T0B projections;
7. compare manifests/query output.

At least one automated fixture restore test belongs in CI.

---

## 17. Git policy

NEVER commit real historical raw datasets to Git.

Git may contain:

- tiny synthetic fixtures;
- tiny legally/publicly safe provider fixtures after review;
- schemas;
- checksums/manifests with no secrets;
- coverage summary reports;
- code/config.

`.gitignore` must cover configurable local data roots and common accidental raw paths.

CI should include a size/secret guard against accidental dataset commits.

---

## 18. High-volume L2/book strategy

Book data is likely the dominant footprint.

Policy:

1. prioritize U0;
2. preserve provider-native historical archive artifacts when available rather than exploding them permanently into redundant row stores;
3. make T0B book projections rebuildable;
4. compute size estimate before extraction/backfill;
5. favor economically normalized book metrics later at T2 for U1/U2;
6. preserve enough U0 raw depth to answer LF14 liquidity-withdrawal mechanics;
7. do not collect full long-tail L2 merely because an endpoint exists.

---

## 19. Trade footprint strategy

Raw trades/aggTrades are important because aggressor flow may need reconstruction.

Preference order:

```text
provider bulk compressed archive
> page-by-page exact response artifacts
> reconstructed minute aggregates only as T2 derivative
```

Never replace raw trades with OHLCV if trade-level flow is the sensor goal.

For U1/U2, storage estimator can determine which venues/instruments remain feasible.

---

## 20. Query performance strategy

T0 is optimized for integrity first, but discovery should remain usable.

Use:

- manifests to prune blob search;
- T0B Parquet for row queries;
- DuckDB statistics/partition pruning;
- projection compaction;
- no millions of tiny files;
- optional metadata cache.

Do not mutate raw layout merely for one research query.

---

## 21. Filesystem portability

Paths stored in manifests should distinguish:

```text
storage_object_key
backend_id
resolved_local_path
```

Avoid persisting machine-specific absolute paths as canonical identity.

A data root should be movable to another disk while blob IDs/manifests remain valid.

---

## 22. Backup / cloud doctrine

Cloud is optional later.

If a future object store is added:

- exact same SHA256 IDs;
- no required paid dependency for core local operation;
- no cloud-only truth;
- explicit replication state;
- encryption/access control where appropriate;
- cost reviewed separately.

Bloc 4 v1 must work with local filesystem alone.

---

## 23. Storage health outputs

Produce:

```text
storage_usage_by_priority
storage_usage_by_provider
storage_usage_by_sensor
storage_usage_by_universe_tier
projection_overhead
orphan_bytes
quarantine_bytes
estimated_days_to_threshold
backup_coverage
```

These are infrastructure metrics, not market signals.

---

## 24. Acceptance gate

Storage/retention plan passes only when:

- critical small mechanical sensors cannot be crowded out by optional full-depth data;
- no destructive raw retention occurs automatically;
- disk pressure fails safely;
- DuckDB is rebuildable;
- Postgres is metadata-only;
- backups are checksum-verified;
- high-volume backfills require size estimates;
- local operation has zero mandatory cloud/storage subscription cost.
