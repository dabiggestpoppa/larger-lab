# BLOC 10 — LOCAL BACKEND, CACHING & RUNTIME POLICY

## 1. Purpose

Freeze local runtime behavior so the canonical sensor service remains deterministic, cheap, offline-capable and fast enough for research batches.

## 2. Backend responsibilities

### Parquet

Authoritative local T1/T2 analytical storage artifacts.

### DuckDB

Read-only query execution, joins, window scans and local materialization discovery.

### PostgreSQL

Operational metadata only:

```text
generation catalog
manifest pointers
readiness state
quality policy refs
lineage indexes
job/runtime metadata
```

No raw high-volume market data should be copied into Postgres simply to serve queries.

## 3. Offline-first startup

Service startup must succeed with all network access disabled.

Startup sequence:

```text
load config
→ verify catalog versions
→ verify local generation manifests
→ verify backend integrity
→ open read-only query connections
→ expose health/readiness
```

Any provider/network client import in the service dependency graph is an architectural violation.

## 4. Cache classes

Allowed caches:

```text
C0 metadata cache
C1 manifest/generation cache
C2 schema cache
C3 query-result cache
C4 bounded materialized window cache
```

Caches are rebuildable and never authoritative.

## 5. Cache keys

Query-result cache keys MUST include:

```text
request fingerprint
T1/T2 generation IDs
quality policy version
dependency graph version
revision policy
as_of policy
response schema version
```

A generation change automatically prevents stale-cache equivalence.

## 6. Cache invalidation

No time-based cache invalidation alone is sufficient for canonical correctness.

Invalidate/bypass on:

- generation change;
- policy version change;
- revision change;
- schema change;
- catalog integrity issue;
- explicit strict-reproducibility request.

## 7. Current/live local reads

`LIVE_CURRENT` reads only data already durably committed by Bloc 8 into canonical stores.

It never waits on or triggers a provider refresh.

Freshness is reported from upstream state.

## 8. Concurrency

Multiple research readers are allowed.

Service should default to:

- read-only file handles/connections;
- bounded query workers;
- bounded memory;
- no mutation locks against ingestion beyond normal atomic generation publication;
- generation snapshot pinning for long requests.

A request begins against a resolved generation set and finishes against the same set even if a newer generation is published mid-query.

## 9. Publication model

New generations become query-visible only after atomic catalog publication.

```text
build generation
→ validate
→ publish manifest atomically
→ update accepted generation pointer
→ new queries may resolve it
```

In-flight queries remain pinned to old accepted generation.

## 10. Performance targets

Planning targets, to be benchmarked rather than assumed:

```text
single state lookup: interactive/local
30D window lookup: interactive/local
multi-state event context: seconds-scale target
1k-event research batch: bounded batch job, not per-event network-style calls
```

Exact thresholds should be set during implementation benchmark evidence based on local hardware.

## 11. Resource controls

The service must support:

```text
max_query_rows
max_scan_bytes
max_concurrent_queries
max_batch_events
max_memory_per_query
query_timeout
```

Exceeding limits returns explicit `QueryResourceLimit` rather than crashing the machine.

## 12. Observability

Local runtime metrics:

```text
query count
latency
rows scanned
bytes scanned
cache hit rate
backend errors
generation resolution failures
quality/coverage failures
resource-limit rejections
```

These are service-health metrics, not market observables.

## 13. Determinism gate

The same strict query over the same pinned generation/policy set must return the same normalized data ordering and response hash.

Nondeterministic ordering or unpinned latest-state behavior is blocking.