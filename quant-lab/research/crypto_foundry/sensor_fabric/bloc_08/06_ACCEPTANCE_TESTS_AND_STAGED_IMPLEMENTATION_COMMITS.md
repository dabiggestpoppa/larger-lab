# BLOC 8 — ACCEPTANCE TESTS & STAGED IMPLEMENTATION COMMITS

**Planning status:** COMPLETE FOR THIS CHAPTER  
**Implementation status:** NOT STARTED

---

## 1. Purpose

Freeze the exact implementation sequence, evidence requirements, blocking gates, and adversarial tests for the live black-box recorder.

This bloc is not complete when a WebSocket receives data.

It is complete when the recorder can survive faults while preserving exact evidence, timing truth, gap truth, restartability, and downstream compatibility.

---

## 2. Required implementation tree

```text
quant-lab/src/crypto_sensor_fabric/live/
  __init__.py
  models.py
  enums.py
  config.py
  planner.py
  recorder.py
  supervisor.py
  sessions.py
  transports/
    base.py
    websocket.py
    rest_poll.py
    snapshot.py
  heartbeat.py
  sequence.py
  clock.py
  checkpoints.py
  chunks.py
  t0_sink.py
  t1_bridge.py
  health_bridge.py
  gaps.py
  repair.py
  retention.py
  resource_policy.py
  reports.py
  providers/
    kraken.py
    gate.py
    binance.py
    bybit.py
    okx.py
    deribit.py
    coinalyze.py
```

Bitfinex community archive remains historical-only unless capability evidence later authorizes a live path.

Tests:

```text
quant-lab/tests/crypto_sensor_fabric/live/
```

Config:

```text
quant-lab/config/crypto_sensor_fabric/live/
```

---

## 3. Test layers

### L0 — pure model / config

No I/O.

### L1 — fake transport

Deterministic simulated WebSocket/REST responses.

### L2 — local filesystem integration

Real T0 chunk/manifest/checkpoint writes in temp directories.

### L3 — cross-bloc integration

Bloc 3 adapters + Bloc 4 T0 + Bloc 5 T1 + Bloc 6 quality interfaces using fixtures.

### L4 — opt-in live smoke

Tiny free/public network tests.

Normal CI may not depend on L4.

### L5 — bounded resilience pilot

24h minimum / 72h preferred operator-authorized local run.

---

## 4. Blocking acceptance gates

### G1 — No execution capability

Search/package tests prove:

- no order endpoints;
- no private position endpoints;
- no withdrawal/transfer endpoints;
- no trading credential requirement.

FAIL = BLOCK.

### G2 — Free-only access

Every live feed passes existing access policy before network connection.

FAIL = BLOCK.

### G3 — Exact evidence durability

Accepted source messages/polls are durably represented in T0 before checkpoints advance.

FAIL = BLOCK.

### G4 — Timing truth

Source event time, local receive time, and durable commit time remain distinguishable.

FAIL = BLOCK.

### G5 — Sequence integrity

Sequence-aware feeds detect skipped/reset/out-of-order messages according to provider rules.

FAIL = BLOCK for feeds claiming contiguous state.

### G6 — Restartability

Process restart resumes without silently skipping durable-boundary evidence.

FAIL = BLOCK.

### G7 — Gap honesty

Forced outages create typed gaps or explicit proof of no gap.

FAIL = BLOCK.

### G8 — T1 compatibility

Live and historical fixtures normalize to the same canonical schema family.

FAIL = BLOCK.

### G9 — Quality integration

Bloc 6 health can consume provider/feed/live observation evidence.

FAIL = BLOCK.

### G10 — Storage safety

Disk pressure suppresses P2 before P0 and never auto-deletes unique T0A.

FAIL = BLOCK.

### G11 — Historical repair handoff

Known forward gaps can generate deterministic bounded `GapRepairRequest` objects.

FAIL = BLOCK.

### G12 — Provider independence preserved

Fallback/alternate-source coverage never rewrites a missing original venue feed as complete.

FAIL = BLOCK.

---

## 5. Core deterministic unit tests

Must include:

```text
test_recorder_config_versioned
test_feed_plan_deterministic
test_universe_membership_event
test_subscription_identity
test_session_reconnect_new_id
test_source_event_vs_receive_time
test_checkpoint_only_after_durable_commit
test_valid_zero_not_missing
test_sparse_event_feed_not_false_stale
test_provider_health_vs_feed_health
test_access_gate_before_connect
test_no_execution_capabilities
```

---

## 6. Transport adversarial tests

```text
socket disconnect before subscription ack
socket disconnect immediately after ack
heartbeat continues but feed stops
feed updates while provider ping fails
rapid reconnect flapping
provider rate limit
REST timeout
REST 5xx
REST permanent 4xx
geo restriction
schema drift payload
malformed payload
oversized payload
```

Every case must produce typed state/evidence.

---

## 7. Sequence adversarial tests

For synthetic sequence-aware feeds:

```text
1,2,3,4,5                 → OK
1,2,2,3                   → DUPLICATE
1,3                       → GAP
1,3,2 within tolerance    → reorder policy
100,101 then reset 1      → expected/unexpected reset policy
checksum mismatch         → invalid book state
```

Book reconstruction test must prove it stops after a missing delta and creates a new epoch from fresh snapshot.

---

## 8. Checkpoint crash matrix

Inject crash at:

```text
A after receive before staging
B during staging
C after staging before fsync
D after fsync before T0 manifest
E after T0 manifest before checkpoint
F after checkpoint before T1
G during T1 normalization
H after T1 before quality evaluation
```

Expected bias:

- A may lose uncommitted live message and must create continuity uncertainty if detectable;
- B/C incomplete staging recovered/quarantined;
- D evidence may exist but not be cataloged—recovery reconciles;
- E may duplicate on restart but not skip;
- F/G/H T0 is authoritative and T1/quality are rebuildable.

No case may advance beyond last durable checkpoint and skip unseen source range.

---

## 9. Gap/repair test matrix

Must cover:

```text
provider exact REST repair
provider alternate archive repair
no same-provider repair but alternate venue coverage
unrepairable stream gap
machine shutdown gap
collector crash gap
rate-limited repair deferred
repair source becomes paid/access blocked
repair with overlap duplicates
repair deadline expiration
```

---

## 10. Storage-pressure tests

Simulate:

```text
NORMAL
WATCH
CONSTRAINED
CRITICAL
```

Assert:

- optional new P2 subscriptions suppressed at WATCH/CONSTRAINED according to config;
- full-depth degrades only through explicit profile change;
- P0 retained longer than P2;
- CRITICAL performs safe stop;
- unique T0A never auto-deleted;
- checkpoint/manifest metadata stays durable.

---

## 11. Clock tests

Test:

- provider timestamp normal;
- local clock offset +100ms;
- offset +5s;
- negative apparent arrival latency;
- provider server-time probe timeout;
- host clock unverified.

No automatic raw timestamp mutation.

---

## 12. Historical/live equivalence tests

Use one provider-native payload available through both historical fixture and simulated live capture.

Assert:

```text
same economic contract identity
same native unit preservation
same normalized T1 semantics
same methodology version
acquisition mode differs
lineage differs appropriately
```

This gate prevents a parallel incompatible live schema.

---

## 13. Provider conformance tests

Each enabled provider needs:

- feed capability mapping;
- subscription fixture;
- representative payload fixture;
- malformed/schema-drift fixture;
- reconnect behavior fixture;
- timestamp semantics fixture;
- T0 exact capture fixture;
- T1 normalization bridge fixture.

No provider may be marked LIVE_READY without its own conformance packet.

---

## 14. Bounded pilot acceptance

Minimum pilot scope, subject to verified capabilities:

```text
BTC
ETH
SOL

Kraken
Gate
Binance
Bybit
```

Sensors:

```text
liquidations
OI
funding
trade/aggressor input
one full-book path
```

Pilot phases:

```text
P0 startup / 2h observation
P1 24h continuous
P2 controlled restart
P3 induced feed failure
P4 gap repair
P5 optional 72h resilience extension
```

---

## 15. Pilot evidence packet

Produce:

```text
LIVE_PILOT_SUMMARY.md
live_capture_counts.parquet
live_provider_health.parquet
live_feed_health.parquet
live_gap_registry.parquet
live_repair_results.parquet
live_t0_integrity.parquet
live_t1_normalization.parquet
live_disk_profile.parquet
live_reconnect_events.parquet
live_sequence_integrity.parquet
```

No “worked fine” narrative without evidence.

---

## 16. Pilot pass conditions

At minimum:

- no unexplained T0 integrity loss;
- restart recovery passes;
- induced gaps correctly recorded;
- at least one repair flow demonstrated where provider supports it;
- book gap invalidation demonstrated;
- P0 sensor health visible;
- no execution/private credentials;
- no paid dependency;
- storage growth measured against forecast;
- live→T1 lineage complete.

Provider outages are not themselves pilot failures if the system degrades honestly.

---

## 17. Planned implementation commits

Do not squash during build/review.

```text
SENSOR-B8-I01
  live models / enums / config contracts

SENSOR-B8-I02
  recorder planner + PIT universe subscription plan

SENSOR-B8-I03
  supervisor / process lifecycle / host identity

SENSOR-B8-I04
  base transport + fake transports

SENSOR-B8-I05
  WebSocket session manager

SENSOR-B8-I06
  REST polling scheduler / rate budget bridge

SENSOR-B8-I07
  heartbeat / freshness / host clock monitor

SENSOR-B8-I08
  sequence / checksum / book epoch engine

SENSOR-B8-I09
  live chunk writer + T0 sink

SENSOR-B8-I10
  durable recorder checkpoints / restart recovery

SENSOR-B8-I11
  T1 live normalization bridge

SENSOR-B8-I12
  Bloc 6 live health bridge

SENSOR-B8-I13
  live gap registry / offline interval logic

SENSOR-B8-I14
  repair request / Bloc 7 handoff

SENSOR-B8-I15
  disk pressure / retention profile engine

SENSOR-B8-I16
  Kraken live implementation

SENSOR-B8-I17
  Gate live implementation

SENSOR-B8-I18
  Binance live implementation

SENSOR-B8-I19
  Bybit live implementation

SENSOR-B8-I20
  OKX live implementation

SENSOR-B8-I21
  Deribit live implementation

SENSOR-B8-I22
  Coinalyze live poll implementation

SENSOR-B8-I23
  provider conformance + drift fixtures

SENSOR-B8-I24
  cross-bloc historical/live equivalence tests

SENSOR-B8-I25
  adversarial reconnect/sequence/crash suite

SENSOR-B8-I26
  storage pressure / long-run chunk tests

SENSOR-B8-I27
  operator health snapshot + daily integrity report

SENSOR-B8-I28
  bounded live pilot harness

SENSOR-B8-I29
  pilot evidence packet

SENSOR-B8-I30
  final validation + Bloc 9 handoff
```

---

## 18. Review checkpoints during implementation

After I10:

> review core recorder before providers.

After each provider I16–I22:

> provider-specific review.

After I25:

> adversarial resilience review.

After I29:

> pilot evidence review before final freeze.

---

## 19. Blocking statuses

```text
PLAN_ONLY
IMPLEMENTING
CORE_READY
PROVIDER_READY
LIVE_PILOT_READY
LIVE_PILOT_RUNNING
LIVE_VALIDATED
DEGRADED_VALIDATED
ACCESS_BLOCKED
DATA_BLOCKED
VALIDATION_FAILED
```

`DEGRADED_VALIDATED` is allowed when one provider cannot operate but the architecture proves correct degraded behavior.

---

## 20. Bloc 9 handoff requirements

Bloc 9 may begin implementation only when the live recorder exposes canonical T1/quality data through provider-independent contracts.

Required handoff objects:

```text
T1 live observation stream/batches
T2Eligibility from Bloc 6
SensorHealth snapshots
Gap adjacency/provenance
Universe membership state
```

Bloc 9 must not call live provider APIs directly.

---

## 21. Final acceptance verdict options

```text
PASS_BLOC_08_LIVE_CORE
PASS_BLOC_08_LIVE_DEGRADED
PASS_BLOC_08_LIVE_VALIDATED
FAIL_BLOC_08_REQUIRES_REPAIR
```

Planning completion uses separate `PASS_BLOC_08_PLAN_FROZEN` in the freeze manifest.
