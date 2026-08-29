# BLOC 7 — RESOURCE BUDGETS, STORAGE FORECASTS, AND RATE LIMITS

**Purpose:** ensure historical acquisition remains local-first, free-only, restartable and resource-aware before multi-year downloads begin.

---

## 1. Resource doctrine

Backfill is constrained by four independent budgets:

```text
NETWORK / PROVIDER RATE
LOCAL DISK
LOCAL CPU / MEMORY
WALL-CLOCK / OPERATOR WINDOW
```

The orchestrator may slow, split or defer work. It may not violate provider limits or silently delete evidence to continue.

---

## 2. BackfillBudget

Each run receives a budget object:

```text
BackfillBudget
  max_wall_clock_seconds
  max_network_requests
  max_download_bytes
  min_free_disk_bytes
  max_disk_utilization_ratio
  max_parallel_providers
  max_parallel_shards_per_provider
  max_memory_bytes_per_worker
  sensor_priority_policy
  universe_priority_policy
  provider_rate_policy_version
```

A run may stop cleanly at budget exhaustion and resume later.

---

## 3. Provider rate budget

Each provider has explicit config:

```text
ProviderRateBudget
  provider_id
  requests_per_second
  requests_per_minute
  requests_per_window
  weight_units_per_window
  burst_limit
  cool_down_seconds
  retry_after_respected
  max_concurrency
  archive_download_concurrency
```

Where providers use weighted endpoints, request count alone is insufficient.

Use token-bucket/leaky-bucket style control or provider-specific equivalent.

---

## 4. Fairness and pacing

Do not let one provider starve others.

Suggested scheduler classes:

```text
CRITICAL_SENSOR
NORMAL_SENSOR
HIGH_VOLUME_SENSOR
GAP_REPAIR
```

Round-robin or weighted fair scheduling should preserve progress across providers while prioritizing P1/P2/P3 sensors.

---

## 5. Rate-limit behavior

### Soft approach

At 70–80% of documented/verified quota:
- begin conservative pacing;
- reduce speculative probe calls;
- prefer archive downloads.

### Hard limit / 429

On `Retry-After`:
- respect exact header where valid;
- checkpoint shard state;
- suspend only affected provider/endpoint family where possible.

Repeated 429 despite compliant pacing becomes:

```text
RATE_POLICY_REVIEW_REQUIRED
```

not aggressive retries.

---

## 6. Storage forecasting before execution

Every sensor/provider/universe combination should have a forecast:

```text
StorageForecast
  provider
  sensor
  universe_tier
  instruments
  date_range
  source_bytes_estimate
  t0a_bytes_estimate
  t0b_bytes_estimate
  t1_bytes_estimate
  index_manifest_bytes_estimate
  confidence
  basis
```

Forecast basis may be:
- capability probe sample;
- known archive sizes;
- recent-day extrapolation;
- provider metadata;
- empirical prior backfill shards.

Unknown estimate must be labelled `LOW_CONFIDENCE` rather than guessed silently.

---

## 7. Pilot before full backfill

For large sensor families, mandatory pilot:

```text
BTC 1 day
ETH 1 day
representative alt 1 day
```

and where density is time-varying:

```text
quiet historical day
high-volatility historical day
recent day
```

Use samples to estimate compressed/raw size and record distribution.

Do not extrapolate book footprint solely from one quiet day.

---

## 8. Storage priority from Bloc 4

Inherited:

```text
P0 critical permanent
  liquidation / OI / funding / positioning / basis

P1 high-value permanent-compress
  trades / aggTrades / liquidation-tagged trades

P2 high-volume selective
  deep books / high-frequency books / redundant long-tail trades

P3 rebuildable
  projections / indexes / caches
```

Backfill scheduling must honor this hierarchy.

---

## 9. Deep-book storage gate

Before any full-depth historical book program, require:

1. verified history exists;
2. PIT semantics understood;
3. reconstruction method understood;
4. pilot storage estimate complete;
5. local free-space gate passed;
6. U0/U1 policy permits it;
7. expected research value documented;
8. pause/resume tested;
9. gap handling tested;
10. source files can be preserved without destructive compaction.

If any fails:

```text
DEEP_BOOK_BACKFILL_DEFERRED
```

and continue other sensor families.

---

## 10. Initial book depth policy

### U0

Allowed:
- richest verified book source compatible with local budget;
- prioritize BTC/ETH and limited core alts.

### U1

Prefer:
- snapshots/coarse depth metrics;
- selected event windows;
- reduced level count where provider offers native options.

### U2

No full-depth historical book backfill by default.

---

## 11. Trade archive policy

Bulk first-party archives are preferred when:
- free;
- public;
- checksum-able or locally hashable;
- immutable/revision-trackable;
- date/instrument boundaries are explicit.

Archive downloads still count against local storage and network budgets.

---

## 12. Disk pressure integration

Use Bloc 4 states:

```text
NORMAL
WATCH
CONSTRAINED
CRITICAL
```

Backfill policy:

### NORMAL
All authorized work.

### WATCH
- no new speculative P2 expansions;
- update storage forecast;
- prefer P0/P1 completion.

### CONSTRAINED
- pause deep-book/high-volume U1/U2;
- allow P0 and high-value P1 if free-space floor safe.

### CRITICAL
- pause new acquisitions;
- commit current atomic work;
- produce disk-pressure evidence;
- require operator action.

No automatic deletion of T0A.

---

## 13. CPU/memory budget

Large decompression/projection jobs must stream/chunk.

Rules:
- avoid loading complete monthly trade archives into memory;
- bound Parquet row-group creation;
- normalize incrementally;
- one pathological instrument may not OOM entire backfill daemon;
- failed memory-heavy shard is split deterministically and retried.

---

## 14. Network interruption

Large archives support:
- provider HTTP range resume if verified safe;
- otherwise clean full-file retry;
- partial files never promoted as T0 evidence;
- staged partial download has separate `.partial` state.

Provider checksum, if supplied, is verified before final commit.

---

## 15. Budget evidence

Each run outputs:

```text
budget_start.json
budget_end.json
provider_rate_usage.parquet
storage_forecast.parquet
storage_actuals.parquet
forecast_error.parquet
resource_deferments.parquet
```

Forecast error should improve later planning rather than be discarded.

---

## 16. Zero-cost gate

Backfill may consume:
- local disk;
- local network bandwidth;
- local CPU.

It may not automatically activate:
- paid API plans;
- requester-pays object storage;
- cloud egress;
- premium archives;
- payment-card-required trials;
- transaction/staking gated access.

If provider free history is insufficient:

```text
HISTORY_UNAVAILABLE_FREE_ONLY
```

or use another verified zero-cost source.

---

## 17. Planning verdict

`PASS_BLOC_07C_RESOURCE_BUDGETS`
