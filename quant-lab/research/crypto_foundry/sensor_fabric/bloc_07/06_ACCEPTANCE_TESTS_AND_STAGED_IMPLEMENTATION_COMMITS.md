# BLOC 7 — ACCEPTANCE TESTS AND STAGED IMPLEMENTATION COMMITS

**Purpose:** freeze the execution sequence and pass/fail evidence for the historical backfill program.

---

## 1. Implementation tree

Suggested structure:

```text
quant-lab/src/crypto_sensor_fabric/backfill/
  models.py
  planner.py
  universe.py
  shards.py
  scheduler.py
  budgets.py
  storage_forecast.py
  gap_registry.py
  revision_registry.py
  coverage.py
  readiness.py
  checkpoints.py
  orchestrator.py
  providers/
    kraken.py
    gate.py
    binance.py
    bybit.py
    okx.py
    deribit.py
    coinalyze.py
    bitfinex_archive.py
```

Provider files here are orchestration policies only; actual acquisition remains in Bloc 3 adapters.

---

## 2. Core test groups

### B7-T01 — Deterministic shard generation

Same plan/config/universe snapshot produces identical shard keys/order.

### B7-T02 — PIT universe clipping

No shard requests data before active_from or after active_to unless explicit lifecycle probe.

### B7-T03 — NOT_EXPECTED semantics

Pre-launch periods are not counted as gaps.

### B7-T04 — Resume safety

Crash after T0 commit but before checkpoint resumes without skipping evidence.

### B7-T05 — At-least-once acquisition

Repeated shard fetch does not corrupt T0 or create false T1 duplicates.

### B7-T06 — Provider fallback truth

Missing provider A + available provider B improves canonical coverage while A remains marked unavailable.

### B7-T07 — Rate budget

Scheduler cannot exceed configured provider quota under concurrency.

### B7-T08 — Retry-After compliance

429 response pauses correctly and resumes later.

### B7-T09 — Disk pressure

CONSTRAINED/CRITICAL states pause correct sensor classes without deleting T0.

### B7-T10 — Storage forecast

Pilot actuals update forecast error and future estimate.

### B7-T11 — Large archive streaming

Monthly trade archive can process without full-file memory load.

### B7-T12 — Partial download safety

Interrupted archive never becomes committed exact evidence.

### B7-T13 — Provider checksum

Known checksum mismatch quarantines file.

### B7-T14 — Source mutation

Same logical source boundary with new bytes creates revision ticket, retains old blob.

### B7-T15 — Fixed-cadence gap detection

Missing OI/funding interval is detected relative to expected lifecycle/cadence.

### B7-T16 — Event-stream no-event vs no-feed

Valid zero/event absence is not automatically classified as gap.

### B7-T17 — Archive/API overlap

Hard-ID duplicates are not doubled in T1.

### B7-T18 — Semantic conflict

Archive/API disagreement creates conflict/revision evidence rather than silent preference.

### B7-T19 — Independence-aware coverage

Aggregator does not increase strict source quorum when dependency is unresolved.

### B7-T20 — T0→T1→quality chain

Shard cannot become COMPLETE until all required downstream validation stages pass.

### B7-T21 — Event-window coverage

Research event overlap correctly marks missing pre/post mechanical windows.

### B7-T22 — Sentinel-era schema drift

Historical fixture with changed schema is parsed/versioned or fails closed.

### B7-T23 — Free-only gate

Requester-pays/premium/payment-required source cannot enter automated backfill.

### B7-T24 — Deep-book gate

Full-depth backfill cannot begin without forecast + storage + semantics approvals.

### B7-T25 — Ragged coverage

Output matrix preserves partial/known-gap/history-unavailable states without coercing rectangle.

---

## 3. Adversarial scenarios

Must simulate:

1. provider says 2021 supported but returns empty;
2. symbol launched 2023 while planner targets 2020;
3. monthly archive missing one day;
4. REST endpoint repeats final page forever;
5. provider changes units mid-history;
6. provider returns same interval twice with revised value;
7. local disk hits 86% during book backfill;
8. 429 occurs across one endpoint but not another;
9. Coinalyze overlaps Binance/Bybit and would fake R3 if naive;
10. book delta sequence has one missing update;
11. archive checksum passes but T1 normalization fails;
12. backfill process killed between manifest commit and checkpoint update;
13. free endpoint becomes premium halfway through program;
14. current partial month is mistaken for closed history;
15. community archive disagrees with first-party venue evidence.

All must have deterministic expected states.

---

## 4. Evidence fixtures

Offline tests require synthetic/checked-in small fixtures only.

Fixture set should include:
- REST windowed response;
- cursor pagination;
- daily archive;
- monthly archive;
- checksum manifest;
- provider-empty response;
- source revision pair;
- schema-drift pair;
- lifecycle metadata;
- rate-limit response;
- book sequence gap;
- aggregator dependency graph.

No normal CI test may depend on live internet.

---

## 5. Live smoke tests

Opt-in only.

Tiny checks:
- one recent instrument/sensor per provider;
- one old historical checkpoint if cheap;
- one archive HEAD/download sample where permitted.

No broad historical backfill in CI.

---

## 6. Staged implementation commits

The execution agent must use granular commits and **must not squash** during review.

```text
SENSOR-B7-I01
  backfill models / enums / plan versioning

SENSOR-B7-I02
  PIT universe snapshot + lifecycle clipping

SENSOR-B7-I03
  deterministic shard planner / splitter

SENSOR-B7-I04
  resource budgets / rate scheduler

SENSOR-B7-I05
  storage forecast / pilot estimator

SENSOR-B7-I06
  shard state machine / checkpoint persistence

SENSOR-B7-I07
  Kraken backfill policy

SENSOR-B7-I08
  Gate backfill policy

SENSOR-B7-I09
  Binance archive/API policy

SENSOR-B7-I10
  Bybit backfill policy

SENSOR-B7-I11
  OKX historical/book policy

SENSOR-B7-I12
  Deribit sequence/history policy

SENSOR-B7-I13
  Coinalyze corroboration policy

SENSOR-B7-I14
  Bitfinex community archive policy

SENSOR-B7-I15
  gap detection / gap ticket registry

SENSOR-B7-I16
  source revisions / archive-API reconciliation

SENSOR-B7-I17
  coverage matrix / typed ragged states

SENSOR-B7-I18
  historical redundancy / independence report

SENSOR-B7-I19
  incremental T0→T1→Bloc6 validation pipeline

SENSOR-B7-I20
  event-window coverage / research readiness

SENSOR-B7-I21
  sensor-phase checkpoint reports

SENSOR-B7-I22
  disk-pressure / deep-book controls

SENSOR-B7-I23
  adversarial + crash/restart suite

SENSOR-B7-I24
  pilot backfill evidence packet

SENSOR-B7-I25
  final Bloc 7 validation / Bloc 8 handoff
```

---

## 7. Required pilot before full history

Implementation must run a bounded pilot after adapters/T0/T1/quality components exist.

Pilot minimum:

```text
BTC + ETH + one alt
3 providers where available
liquidation + OI + funding
one trade/archive path
one book path if authorized
```

Dates:

```text
one 2022 stress window
one 2024 ordinary window
one recent 2026 window
```

Pilot proves:
- storage estimates;
- resume;
- lineage;
- normalization;
- coverage states;
- provider disagreement;
- quality/readiness outputs.

The pilot is evidence, not a research conclusion.

---

## 8. Bloc 7 acceptance gates

### Gate A — deterministic planning
PASS if identical plan inputs produce identical shards.

### Gate B — PIT lifecycle
PASS if no false pre-listing gaps/requests.

### Gate C — durable/resumable
PASS if crash injection cannot skip committed work.

### Gate D — resource safety
PASS if rate/disk/memory controls work under adversarial tests.

### Gate E — raw integrity
PASS if archives/responses are T0-committed and checksum/revision rules pass.

### Gate F — normalization chain
PASS if pilot flows through Bloc 5 with complete lineage.

### Gate G — quality/redundancy
PASS if Bloc 6 produces independence-aware quality states.

### Gate H — ragged coverage truth
PASS if unavailable/partial/not-expected are explicit.

### Gate I — research-readiness
PASS if scope-aware readiness can be queried.

### Gate J — free-only
PASS if no prohibited paid/requester-pays dependency is required.

---

## 9. Blocking failures

Block Bloc 8 planning handoff if implementation design cannot preserve:
- PIT universe;
- exact T0 evidence;
- resumability;
- typed gaps;
- provider identity;
- source independence;
- no-zero-fill;
- free-only policy;
- research scope-aware readiness.

---

## 10. Bloc 8 handoff requirements

Bloc 8 — Live Black-Box Recorder must inherit:
- provider adapters;
- T0 commit path;
- T1 normalization path;
- Bloc 6 health/quality;
- storage pressure policy;
- universe tiers;
- typed gaps;
- lineage;
- free-only access gate.

Live collection must complement historical backfill, not invent a second incompatible data stack.

---

## 11. Planning verdict

`PASS_BLOC_07F_ACCEPTANCE_AND_COMMITS`
