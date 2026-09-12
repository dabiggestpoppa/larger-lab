# BLOC 7 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze the historical backfill program before any execution agent launches multi-year downloads.

---

## 1. Frozen decisions

### F1 — Backfill is sensor-first

Priority is:

```text
LIQUIDATIONS
→ OPEN INTEREST
→ FUNDING
→ AGGRESSOR FLOW / TRADES
→ BOOK / DEPTH / SPREAD
→ POSITIONING / BASIS
```

Provider order is secondary to economic sensor coverage.

### F2 — Initial historical target

Configurable, with initial target:

```text
2020-06-01 → present
```

Actual provider/instrument history may begin later.

### F3 — Ragged history is valid

No forced rectangular panel.

Typed states preserve:

```text
NOT_EXPECTED
AVAILABLE_COMPLETE
AVAILABLE_PARTIAL
KNOWN_GAP
PROVIDER_EMPTY_CONFIRMED
HISTORY_UNAVAILABLE
UNSUPPORTED
ACCESS_BLOCKED
RATE_DEFERRED
DISK_DEFERRED
QUARANTINED
REVISION_CONFLICT
UNKNOWN
```

### F4 — PIT universe controls requests

No current-universe back-projection.

Instrument lifecycle clips shard boundaries.

### F5 — Deterministic shards

Shard identity includes provider, venue, sensor, contract, granularity, mode and temporal boundary under a plan version.

### F6 — Provider-native acquisition survives

REST/archive/download-job/community archive mechanics remain provider-specific through Bloc 3 adapters.

### F7 — Bulk archives preferred where first-party and reproducible

Especially for dense historical trades.

### F8 — Deep books are storage-gated

Rich U0 first; selective U1; U2 full-depth disabled by default.

### F9 — Every shard flows through T0→T1→quality

HTTP success alone cannot produce COMPLETE.

### F10 — Resume after durability

At-least-once acquisition + idempotent evidence storage.

### F11 — Provider fallback does not repair missing venue history

Other providers may improve canonical economic-sensor coverage while the original venue gap remains explicit.

### F12 — Valid zero differs from missing

No-event, provider-empty, suspicious-empty and missing-feed are distinct.

### F13 — Source revisions append

Old source bytes remain; changed history creates revision tickets and possibly new T1 generation.

### F14 — Aggregators cannot fake redundancy

Strict source count is independence-aware through Bloc 6 dependency graph.

### F15 — Free-only remains hard gate

No requester-pays, premium, payment-method-required, staking or transaction-gated rescue.

### F16 — Storage/rate budgets are first-class

Backfill may pause/defer; it may not silently violate rate limits or delete T0A.

### F17 — Validation is incremental

Do not wait for six years of history before testing semantics.

### F18 — Research readiness is scope-aware

No global `data_ready` boolean.

### F19 — Research event overlap matters

A year can have high coverage while a specific LF14 event lacks required pre/post mechanics.

### F20 — Historical truth report is mandatory

Each sensor phase must say what was requested, what existed, what was acquired, what normalized safely, where redundancy exists, and where gaps remain.

---

## 2. Frozen backfill eras

Reporting eras:

```text
E0 2020-06 → 2020-12
E1 2021
E2 2022
E3 2023
E4 2024
E5 2025
E6 2026 → present
```

These are reporting partitions, not forced acquisition boundaries.

---

## 3. Frozen universe policy

### U0 Mechanism Core

Richest available mechanical history:
- liquidations
- OI
- funding
- trades/flow
- books/liquidity
- positioning/basis

### U1 Broad Research

Broad perpetual universe:
- liquidations
- OI
- funding
- selective trades/flow
- coarse liquidity

### U2 Long Tail

Cheap broad history:
- OI
- funding
- liquidation statistics
- coarse positioning/activity

No full-depth U2 by default.

---

## 4. Frozen provider role map

```text
KRAKEN
  analytics: liquidation / OI / funding / CVD / liquidity / basis

GATE
  broad-alt liquidation / OI / taker / funding / positioning

BINANCE
  first-party trade archives / aggTrades / funding / metrics / secondary books

BYBIT
  historical OI / funding / trades

OKX
  historical trades / funding / deep book modules

DERIBIT
  liquidation-tagged trade anatomy / BTC-ETH microscope

COINALYZE
  corroboration / daily long history / forward intraday

BITFINEX COMMUNITY ARCHIVE
  liquidation replication only; community evidence
```

Final implementation use depends on Bloc 2 verified capability evidence.

---

## 5. Frozen acquisition modes

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

---

## 6. Frozen shard states

```text
PLANNED
ELIGIBILITY_CHECKED
READY
ACQUIRING
T0_COMMITTED
T1_NORMALIZED
QUALITY_EVALUATED
COMPLETE

NOT_EXPECTED
UNSUPPORTED
HISTORY_UNAVAILABLE
ACCESS_BLOCKED
RATE_DEFERRED
DISK_DEFERRED
PARTIAL
GAP_DETECTED
REVISION_REVIEW_REQUIRED
QUARANTINED
FAILED_RETRYABLE
FAILED_FINAL
```

---

## 7. Frozen resource controls

Budgets cover:
- provider rates/weights;
- network bytes;
- local disk;
- local CPU/memory;
- wall clock;
- parallelism.

Bloc 4 disk states apply:

```text
NORMAL
WATCH
CONSTRAINED
CRITICAL
```

At CRITICAL, new acquisition stops safely.

---

## 8. Frozen gap/repair rules

Repair same-provider evidence first:

```text
retry original
→ alternate verified provider-native acquisition mode
→ archive/API counterpart
→ confirm history unavailable
→ stop venue-specific repair
```

Another venue can improve canonical coverage but does not erase provider gap.

---

## 9. Frozen revision rules

Same source boundary with changed bytes:

```text
old blob retained
new blob appended
revision ticket
semantic diff
new T1 generation if required
```

No destructive rewriting.

---

## 10. Frozen research-readiness states

```text
NOT_STARTED
ACQUIRING
RAW_READY
T1_PARTIAL
QUALITY_PARTIAL
RESEARCH_LOCAL_ONLY
RESEARCH_REDUNDANT
RESEARCH_CROSS_VENUE
RESEARCH_MULTI_ERA
DATA_BLOCKED
VALIDATION_FAILED
```

Readiness is queried by sensor + asset/universe + dates + granularity + evidence requirements.

---

## 11. Frozen sensor-phase checkpoints

Mandatory checkpoints after:

```text
L = liquidation history
O = open-interest history
F = funding history
T = trade/aggressor inputs
B = book/liquidity history
```

Each must produce coverage, redundancy, gaps, revisions and sentinel-era validation.

---

## 12. Frozen sentinel periods

Every major sensor must be validated across:

```text
2021 high-activity sample
2022 stress sample
2024 ordinary/regime sample
2026 recent sample
+ at least one quiet period
```

This prevents recent-only parser validation.

---

## 13. Frozen planning history

```text
SENSOR-PLAN-B7A
  historical backfill architecture

SENSOR-PLAN-B7B
  provider playbooks + deterministic sharding

SENSOR-PLAN-B7C
  rate/storage/resource budgets

SENSOR-PLAN-B7D
  gap repair / revisions / coverage truth

SENSOR-PLAN-B7E
  incremental validation / research readiness

SENSOR-PLAN-B7F
  acceptance tests + staged implementation commits

SENSOR-PLAN-B7G
  freeze manifest + Bloc 8 handoff
```

---

## 14. Frozen future implementation sequence

```text
SENSOR-B7-I01  models/enums/plan versions
SENSOR-B7-I02  PIT universe snapshot
SENSOR-B7-I03  deterministic shard planner
SENSOR-B7-I04  resource/rate scheduler
SENSOR-B7-I05  storage forecasting
SENSOR-B7-I06  shard state/checkpoint durability
SENSOR-B7-I07  Kraken policy
SENSOR-B7-I08  Gate policy
SENSOR-B7-I09  Binance policy
SENSOR-B7-I10  Bybit policy
SENSOR-B7-I11  OKX policy
SENSOR-B7-I12  Deribit policy
SENSOR-B7-I13  Coinalyze policy
SENSOR-B7-I14  Bitfinex archive policy
SENSOR-B7-I15  gap registry
SENSOR-B7-I16  source revisions / reconciliation
SENSOR-B7-I17  typed coverage matrix
SENSOR-B7-I18  historical redundancy matrix
SENSOR-B7-I19  incremental T0→T1→quality chain
SENSOR-B7-I20  event-window coverage / readiness
SENSOR-B7-I21  sensor-phase checkpoints
SENSOR-B7-I22  disk/deep-book controls
SENSOR-B7-I23  adversarial/crash suite
SENSOR-B7-I24  bounded pilot packet
SENSOR-B7-I25  final validation / Bloc 8 handoff
```

No squashing during staged review.

---

## 15. Pilot gate before full backfill

Pilot must cover, where available:

```text
BTC + ETH + one alt
3 providers
liquidation + OI + funding
one trade/archive path
one book path if authorized
```

Across:

```text
2022 stress
2024 ordinary
2026 recent
```

Pilot must prove:
- deterministic shards;
- safe resume;
- T0 integrity;
- T1 normalization;
- source independence;
- ragged coverage;
- quality/readiness;
- storage forecast accuracy.

No full historical sweep before pilot acceptance.

---

## 16. Bloc 7 completion checklist

- [x] historical target defined
- [x] sensor priority defined
- [x] provider playbooks defined
- [x] PIT universe policy defined
- [x] deterministic sharding defined
- [x] archive vs API policy defined
- [x] rate budgets defined
- [x] storage forecasts defined
- [x] deep-book gate defined
- [x] crash/resume defined
- [x] gap taxonomy defined
- [x] gap repair defined
- [x] source revision handling defined
- [x] typed coverage defined
- [x] independence-aware redundancy defined
- [x] incremental validation defined
- [x] sensor checkpoints defined
- [x] event-overlap coverage defined
- [x] research-readiness defined
- [x] pilot gate defined
- [x] staged commits defined
- [x] Bloc 8 handoff defined

---

## 17. Bloc 8 handoff

Bloc 8 must design the **Live Black-Box Recorder** using the exact same provider adapters, T0 store, T1 normalizers and Bloc 6 quality system.

It must cover:
1. WebSocket/public-feed collectors;
2. REST polling for OI/funding/analytics where needed;
3. event-time vs arrival-time capture;
4. heartbeat/staleness/gap detection;
5. reconnect/resubscribe semantics;
6. sequence-gap repair;
7. continuous T0 archival;
8. disk-pressure behavior;
9. rotating partitions/chunks;
10. forward data retention by universe tier;
11. daemon/process supervision;
12. restart after machine shutdown;
13. local-only default operation;
14. live health evidence;
15. historical backfill gap-fill integration.

Live collection may later help repair future gaps but must not create a separate incompatible evidence format.

---

## 18. Final planning verdict

`PASS_BLOC_07_PLAN_FROZEN`

Rationale:

The historical program is now implementation-grade: sensor-first acquisition, PIT universe control, deterministic shards, provider-specific backfill playbooks, resource/rate/storage gates, deep-book controls, crash-safe resume, typed gaps, non-destructive source revisions, independence-aware redundancy, incremental T0→T1→quality validation, event-window coverage, scope-aware research readiness, bounded pilot requirements and 25 staged implementation checkpoints.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 8`
