# BLOC 7 — PROVIDER BACKFILL PLAYBOOKS AND SHARDING

**Purpose:** freeze provider-specific acquisition paths and deterministic shard rules for historical reconstruction.

---

## 1. General principle

Bloc 7 uses **one backfill orchestrator** over provider-native acquisition methods.

The orchestrator owns:
- what to backfill;
- deterministic shard boundaries;
- resource budgets;
- sequencing;
- retries/deferments;
- coverage/evidence accounting.

Bloc 3 adapters own:
- provider-native request syntax;
- pagination;
- archive download mechanics;
- rate-limit semantics;
- parsing and raw response envelopes.

The orchestrator must not duplicate provider logic.

---

## 2. Acquisition mode classes

```text
REST_WINDOWED
REST_CURSOR
REST_TIME_CURSOR
BULK_DAILY_ARCHIVE
BULK_MONTHLY_ARCHIVE
BULK_PROVIDER_FILE
HISTORICAL_DOWNLOAD_JOB
COMMUNITY_ARCHIVE
```

Each provider/sensor capability declares the allowed modes in the capability registry.

---

## 3. Deterministic shard key

Canonical shard identity:

```text
sha256(
  backfill_plan_version |
  provider_id |
  venue_id |
  sensor_family |
  instrument_instance_id |
  granularity |
  acquisition_mode |
  start_at |
  end_at
)
```

Same plan inputs must generate the same shard keys.

Changing semantic meaning or acquisition boundaries requires a new plan version rather than mutating old shard identity.

---

## 4. Default shard sizing by sensor

Initial planning defaults; Bloc 2 verified capabilities may override.

### Liquidations / OI / funding / positioning / basis

Prefer:

```text
DAILY or WEEKLY API SHARDS
MONTHLY if provider endpoint can reliably return complete month
```

### Raw trades / aggTrades

Prefer provider archives:

```text
MONTHLY archive when supplied
DAILY archive if monthly unavailable
REST only for gap repair / providers without archive
```

### Full/deep books

Prefer provider-native historical files/jobs.

Use much smaller logical shards because of size:

```text
DAY
or
HOUR for extremely dense event books
```

### Aggregated book metrics

May use larger daily/weekly windows if provider directly serves interval analytics.

---

## 5. Kraken Futures playbook

Target roles:
- liquidation volume
- open interest
- funding
- aggressor differential / CVD
- spread / liquidity / slippage
- orderbook analytics
- basis

Backfill preference:
1. verified historical analytics endpoints;
2. provider-native time windows;
3. smallest request count that preserves deterministic completeness.

Special checks:
- interval endpoint limit behavior;
- earliest verified history by metric;
- whether all analytics types share identical history;
- whether a metric's timestamp is interval start/end;
- contract lifecycle changes;
- XBT/BTC identity handling;
- API response revisions/source mutations.

Kraken metric absence for a historical period is typed per metric; do not infer all Kraken mechanics unavailable because one analytic family is unavailable.

---

## 6. Gate Futures playbook

Target roles:
- long/short liquidation size and USD values
- OI
- taker flow
- funding
- positioning/user ratios
- broad alt universe

Backfill preference:
1. contract statistics history;
2. funding history;
3. trades only where scientifically valuable / supported.

Special checks:
- max historical lookback per interval;
- long/short liquidation semantics;
- base quantity versus USD fields;
- interval aggregation boundaries;
- contracts introduced/delisted;
- pagination/window overlap;
- position-side interpretation.

Gate is expected to be especially valuable for U1 broad-alt mechanical coverage.

---

## 7. Binance USD-M playbook

Target roles:
- historical trades / aggTrades
- funding
- OI/metrics where archives/endpoints support them
- taker flow reconstruction
- secondary depth/book snapshots

Preference:

```text
FIRST-PARTY BULK ARCHIVES
> REST pagination
```

when both are equivalent and archives are hashable.

Archive order:
1. monthly files for completed historical months;
2. daily files for recent/incomplete months and gap repair;
3. REST only for evidence repair or missing archive capability.

Special checks:
- provider checksums;
- archive holes;
- historical header/schema changes;
- `isBuyerMaker` fixture semantics;
- duplicates between daily and monthly archives;
- archive publication latency;
- known historical liquidation absence is not zero.

Never mix monthly+daily duplicates into T1 without hard-ID dedupe through Bloc 5.

---

## 8. Bybit Linear playbook

Target roles:
- OI
- funding
- trades
- independent leverage/flow corroboration

Backfill preference:
1. public historical endpoints with cursor;
2. public trade archives if capability probe verifies reproducibility.

Special checks:
- OI starts at symbol launch;
- cursor termination;
- time-ordering direction;
- maximum rows/window;
- funding cadence by instrument;
- historical symbol renames or category migrations.

Shard planner must clamp requested start to verified symbol launch where known.

---

## 9. OKX Swap playbook

Target roles:
- historical trades
- funding
- deep historical orderbook modules
- liquidity research

Backfill preference:
1. official historical market-data files/jobs;
2. public history APIs.

Book history must be separately budgeted from other sensors.

Special checks:
- depth module level (50/400/5000);
- whether output is snapshot or event/delta form;
- snapshot cadence;
- reconstruction requirements;
- download-job expiration;
- file checksum/integrity;
- storage estimate before download;
- quote/collateral changes.

Only U0 gets richest depth by default.

---

## 10. Deribit playbook

Target roles:
- liquidation-tagged trades
- BTC/ETH mechanism microscope
- funding/trades

Backfill preference:
- timestamp or sequence based public historical trades.

Special checks:
- trade sequence continuity;
- liquidation marker `M`, `T`, `MT` preservation;
- instrument naming/lifecycle;
- inverse contract denomination;
- option trades must not silently enter perpetual sensor family;
- maker/taker role remains distinct from position side.

Deribit liquidation-tagged trades are often `CORROBORATION_ONLY` against interval liquidation-volume sensors, but are primary evidence for trade-level liquidation anatomy.

---

## 11. Coinalyze playbook

Target roles:
- OI/funding/liquidation corroboration
- daily long-history context
- forward intraday corroboration

Constraints:
- free key;
- free call limits;
- finite intraday history.

Rules:
- never expect long intraday history when provider retention does not support it;
- daily history and intraday history have separate coverage states;
- aggregator dependency graph must be populated where source composition is known/unknown;
- Coinalyze cannot inflate independent-source quorum when dependency is unresolved.

---

## 12. Bitfinex community liquidation archive playbook

Target role:
- independent research replication of liquidation mechanics.

Evidence class:

```text
COMMUNITY_RECONSTRUCTED
```

not first-party exchange truth.

Rules:
- archive provenance and release/version must be pinned;
- checksum local copy;
- preserve original archive/files in T0A;
- capture extractor/tool version;
- record claimed and actually observed historical range;
- do not allow it to become sole critical runtime dependency.

---

## 13. Shard boundary rules

### Calendar boundaries

Prefer UTC-aligned boundaries unless provider semantics require otherwise.

```text
hour: [HH:00, next HH:00)
day:  [00:00Z, next 00:00Z)
month:[first 00:00Z, next month first 00:00Z)
```

Provider-inclusive endpoint boundaries must be normalized in acquisition logic to avoid omission/duplication.

### Launch/delist boundaries

Shard boundary is clipped to:

```text
max(requested_start, instrument_active_from)
min(requested_end, instrument_active_to)
```

### Current partial period

Never treat incomplete current day/month as equivalent to closed historical period.

Use explicit:

```text
OPEN_PERIOD
```

state.

---

## 14. Shard splitting

A shard may be split deterministically if:
- provider limit exceeded;
- payload too large;
- repeated timeout;
- memory pressure;
- size forecast exceeds target;
- source uses smaller archive granularity.

Split rule should be deterministic:

```text
parent → equal temporal halves
```

or provider-native calendar partition.

Child lineage to parent must be retained.

---

## 15. Shard merging

Acquisition shards are **not physically merged destructively** at T0A.

T0B/T1 may compact for query efficiency only when lineage preserves every original acquisition/evidence blob.

---

## 16. Provider fallback during historical backfill

Fallback means:

> continue acquiring the economic sensor from other providers.

It does **not** mean:

> fabricate the missing provider's venue history.

Example:

```text
Kraken liquidation history unavailable 2021
Gate available 2021

Result:
Kraken/2021 = HISTORY_UNAVAILABLE
Gate/2021   = AVAILABLE
cross-venue liquidation coverage = reduced venue set
```

---

## 17. Planning verdict

`PASS_BLOC_07B_PROVIDER_PLAYBOOKS_AND_SHARDING`
