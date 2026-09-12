# BLOC 8 — FREEZE MANIFEST

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Branch:** `agent/crypto-sensor-fabric-plan`  
**Purpose:** freeze the live black-box recorder architecture before any execution agent runs always-on collection.

---

## 1. Frozen decisions

### F1 — Live is not a separate stack

Live capture must use the same:

```text
Bloc 3 provider adapters
Bloc 4 T0 evidence store
Bloc 5 T1 normalization
Bloc 6 quality/redundancy/failover
Bloc 7 repair infrastructure
```

as historical research.

### F2 — Local-first default

The recorder runs correctly on the local machine without cloud infrastructure.

### F3 — Public/free-only market data

No trading/private API key is required.
No payment/staking/transaction-gated source may become a required live dependency.

### F4 — Exact source evidence before analytics

Every accepted live payload/poll response enters T0 before checkpoints may advance.

### F5 — Event time and receive time remain distinct

Minimum timing truth:

```text
source_event_at
source_publish_at when known
collector_received_at
collector_committed_at
normalized_at
```

### F6 — Reconnect does not imply continuity

Every disconnect/reconnect triggers continuity determination.

### F7 — Sequence integrity is provider-specific and mandatory when available

Gap/checksum failure invalidates any state requiring contiguous updates.

### F8 — Sparse event feeds need special health logic

No liquidation messages is not automatically a stale feed.

### F9 — Machine-off intervals are honest gaps

`LOCAL_MACHINE_OFFLINE` / `LOCAL_RECORDER_CRASH` remain explicit until repaired or declared unrecoverable.

### F10 — Forward gaps feed Bloc 7 repair

Live recorder requests bounded repair; it does not launch uncontrolled historical sweeps.

### F11 — Same-provider repair has precedence

Alternate venues may restore canonical sensor coverage but cannot erase original venue gaps.

### F12 — At-least-once capture bias

Duplicates are safer than skipped evidence.

### F13 — Live streams are chunked immutably

Bounded chunks close on time/size/session/sequence/schema/shutdown boundaries.

### F14 — Disk pressure pauses/degrades before deletion

P2 books lose priority before P0 mechanical sensors.

Unique T0A is never silently auto-deleted in v1.

### F15 — Fidelity downgrade is explicit

Changing from full depth to coarse snapshots/metrics creates an explicit acquisition profile change.

### F16 — Universe is point-in-time

U0/U1/U2 membership changes are versioned events.

### F17 — New listings require valid identity before normalization

No ambiguous contract identity is allowed to silently enter T1.

### F18 — Delisting ends expected collection

Post-delisting absence becomes NOT_EXPECTED rather than feed gap.

### F19 — Live provider roles are complementary

No single provider is canonical truth.

### F20 — Historical and live provider payloads must normalize compatibly

Acquisition mode may differ; economic T1 semantics may not silently diverge.

### F21 — Provider/Feed/Sensor health remain separate

A provider can be up while one feed is stale, and one provider can be down while a sensor remains redundant.

### F22 — Disagreement remains evidence

Cross-provider divergence is not automatically quarantined or averaged away.

### F23 — Book gaps create new valid epochs

A missing delta invalidates contiguous reconstruction until fresh snapshot/sequence restart.

### F24 — Host clock quality is observable

Local receive-latency calculations cannot silently trust a drifting host clock.

### F25 — Live operation never includes execution

No orders, withdrawals, balances, private positions, or trading credentials.

---

## 2. Frozen live acquisition modes

```text
WEBSOCKET_STREAM
REST_FIXED_INTERVAL_POLL
REST_EVENT_DRIVEN_POLL
REST_SNAPSHOT_REPAIR
HISTORICAL_GAP_REPAIR
PROVIDER_BULK_FORWARD_DROP
```

Only verified capabilities may be enabled.

---

## 3. Frozen runtime objects

```text
RecorderInstance
FeedSubscription
LiveSession
LiveCaptureEnvelope
HeartbeatObservation
LiveGap
RecorderCheckpoint
RecorderOfflineInterval
GapRepairRequest
LiveEvidenceChunk
UniverseMembershipEvent
LiveDisagreementEvent
```

---

## 4. Frozen recorder startup order

```text
config/policy verification
→ free-only gate
→ disk/quota gate
→ T0/metadata repositories
→ checkpoint recovery
→ PIT universe
→ P0 feed plan
→ P0 health verification
→ P1 feeds
→ authorized P2 feeds
→ READY / DEGRADED_READY
```

If durable T0 is unavailable, live capture does not continue in memory-only mode.

---

## 5. Frozen recorder shutdown order

```text
stop new subscriptions
→ stop polls
→ drain in-flight data
→ durable T0 commit
→ T1 bridge where configured
→ checkpoints
→ final health/session records
→ STOPPED
```

---

## 6. Frozen session/feed states

Provider session states:

```text
DISABLED
STARTING
CONNECTING
SUBSCRIBING
HEALTHY
DEGRADED
STALE
DISCONNECTED
BACKING_OFF
RECOVERING
ACCESS_BLOCKED
STOPPED
FAILED
```

Feed states:

```text
NOT_STARTED
STARTING
ACTIVE
IDLE_EXPECTED
STALE
SEQUENCE_GAP
CHECKSUM_FAILURE
RATE_DEGRADED
PARTIAL
RECOVERING
STOPPED
FAILED
```

---

## 7. Frozen sequence integrity states

```text
SEQUENCE_OK
SEQUENCE_DUPLICATE
SEQUENCE_REORDERED_WITHIN_TOLERANCE
SEQUENCE_GAP
SEQUENCE_RESET_EXPECTED
SEQUENCE_RESET_UNEXPECTED
CHECKSUM_OK
CHECKSUM_FAILURE
UNVERIFIABLE
```

---

## 8. Frozen live gap taxonomy

```text
PROVIDER_TRANSPORT_OUTAGE
PROVIDER_FEED_STALE
SUBSCRIPTION_FAILURE
SEQUENCE_GAP
CHECKSUM_FAILURE
REST_POLL_MISSED
RATE_LIMIT_DEFERRED
ACCESS_BLOCKED
LOCAL_RECORDER_CRASH
LOCAL_MACHINE_OFFLINE
LOCAL_NETWORK_OUTAGE
LOCAL_DISK_PRESSURE_PAUSE
LOCAL_CLOCK_INVALID
CONFIG_DISABLED
UNIVERSE_NOT_SELECTED
UNKNOWN_CONTINUITY
```

`CONFIG_DISABLED` and `UNIVERSE_NOT_SELECTED` are expected absence.

---

## 9. Frozen gap lifecycle

```text
OPEN
BOUNDED
REPAIR_QUEUED
REPAIRING
REPAIRED_EXACT_PROVIDER
COVERED_ALTERNATE_PROVIDER
PARTIALLY_REPAIRED
UNREPAIRABLE
DISMISSED_NOT_A_GAP
```

Original venue repair and canonical sensor coverage remain separate statuses.

---

## 10. Frozen repair priority

```text
same provider exact semantics
→ same provider compatible historical endpoint
→ same provider bulk/archive evidence
→ alternate-provider canonical coverage
→ unrepaired / DATA_BLOCKED
```

No paid rescue.

---

## 11. Frozen recording priority

```text
P0
  liquidations / OI / funding / positioning / basis / health-gap metadata

P1
  trades / aggTrades / aggressor-flow inputs / liquidation-tagged trades

P2
  deep books / high-frequency snapshots
```

---

## 12. Frozen retention profiles

```text
RICH_U0
STANDARD_U1
LEAN_U2
EMERGENCY_P0_ONLY
```

Any profile change is explicit and versioned.

---

## 13. Frozen disk behavior

Bloc 4 thresholds remain:

```text
NORMAL
WATCH
CONSTRAINED
CRITICAL
```

At high pressure:

```text
optional P2 suppressed first
→ selective fidelity downgrade only if explicitly configured
→ P0 protected
→ CRITICAL safe stop
```

No silent T0A deletion.

---

## 14. Frozen book modes

```text
FULL_DELTA
TOP_N_DELTA
PERIODIC_FULL_SNAPSHOT
NORMALIZED_BPS_METRICS_ONLY
DISABLED
```

Metric-only history may not be presented as reconstructable full-book history.

---

## 15. Frozen provider live roles

```text
KRAKEN
  rich analytics / liquidation / OI / funding / CVD / liquidity / basis

GATE
  broad-alt liquidation / OI / taker / funding / positioning

BINANCE
  trades/aggTrades / aggressor inputs / OI-funding / depth / possible live liq if verified

BYBIT
  independent OI/funding/trades / selected books / liquidation if verified

OKX
  trades/funding / independent depth-liquidity / OI if verified

DERIBIT
  BTC-ETH liquidation-tagged trade microscope / funding / books

COINALYZE
  limited free corroboration polling

BITFINEX COMMUNITY ARCHIVE
  historical-only by default
```

Actual feed enablement requires capability proof.

---

## 16. Frozen live redundancy principle

Independent source count uses Bloc 6 dependency graph.

Aggregators cannot increase strict quorum when their upstream dependencies overlap native sources.

---

## 17. Frozen pilot scope

Minimum planned live pilot, where verified:

```text
BTC + ETH + SOL
Kraken + Gate + Binance + Bybit
liquidations + OI + funding + trade/aggressor input
+ one full-book path
```

Functional minimum:

```text
24h
```

Preferred resilience extension:

```text
72h
```

Pilot must include controlled failures/restart/gap repair, not just passive uptime.

---

## 18. Frozen planning history

```text
SENSOR-PLAN-B8A
  live recorder architecture

SENSOR-PLAN-B8B
  transport / heartbeat / sequence / reconnect

SENSOR-PLAN-B8C
  storage / retention / disk pressure / rotation

SENSOR-PLAN-B8D
  live health / gap registry / repair handoff

SENSOR-PLAN-B8E
  provider live playbooks / universe policy

SENSOR-PLAN-B8F
  acceptance tests / staged implementation commits

SENSOR-PLAN-B8G
  freeze manifest / Bloc 9 handoff
```

---

## 19. Frozen future implementation sequence

```text
SENSOR-B8-I01  models/enums/config
SENSOR-B8-I02  PIT live feed planner
SENSOR-B8-I03  supervisor/host lifecycle
SENSOR-B8-I04  base + fake transports
SENSOR-B8-I05  WebSocket session manager
SENSOR-B8-I06  REST polling scheduler
SENSOR-B8-I07  heartbeat/freshness/clock
SENSOR-B8-I08  sequence/checksum/book epochs
SENSOR-B8-I09  live chunks/T0 sink
SENSOR-B8-I10  durable checkpoints/recovery
SENSOR-B8-I11  T1 live bridge
SENSOR-B8-I12  Bloc 6 health bridge
SENSOR-B8-I13  gap/offline registry
SENSOR-B8-I14  repair/Bloc 7 handoff
SENSOR-B8-I15  retention/disk-pressure engine
SENSOR-B8-I16  Kraken live
SENSOR-B8-I17  Gate live
SENSOR-B8-I18  Binance live
SENSOR-B8-I19  Bybit live
SENSOR-B8-I20  OKX live
SENSOR-B8-I21  Deribit live
SENSOR-B8-I22  Coinalyze live polling
SENSOR-B8-I23  conformance/drift fixtures
SENSOR-B8-I24  historical-live equivalence
SENSOR-B8-I25  adversarial reconnect/sequence/crash
SENSOR-B8-I26  storage-pressure/long-run chunks
SENSOR-B8-I27  health snapshot/daily report
SENSOR-B8-I28  bounded pilot harness
SENSOR-B8-I29  pilot evidence packet
SENSOR-B8-I30  final validation / Bloc 9 handoff
```

No squashing during staged review.

---

## 20. Frozen blocking acceptance gates

Implementation must prove:

- no execution/private capability;
- free-only feed access;
- exact T0 durability before checkpoint;
- event/arrival/commit timing separation;
- sequence-gap detection;
- restartability;
- gap honesty;
- T1 compatibility with historical ingestion;
- Bloc 6 live health integration;
- safe disk-pressure behavior;
- bounded repair handoff;
- provider identity/venue gaps preserved.

Any failure in these is blocking.

---

## 21. Bloc 8 completion checklist

- [x] common live-recorder architecture
- [x] local-first doctrine
- [x] WebSocket/REST modes
- [x] event-time vs arrival-time model
- [x] heartbeat semantics
- [x] sparse-feed health semantics
- [x] sequence/checksum model
- [x] reconnect/resubscribe rules
- [x] book snapshot+delta recovery
- [x] durable live chunks
- [x] disk pressure/retention
- [x] machine shutdown/crash recovery
- [x] live gap registry
- [x] historical repair handoff
- [x] independence-aware live redundancy
- [x] provider live playbooks
- [x] PIT universe transitions
- [x] provider capability activation gates
- [x] historical/live equivalence gate
- [x] adversarial test suite
- [x] bounded pilot plan
- [x] staged implementation commits
- [x] Bloc 9 handoff

---

## 22. Bloc 9 handoff

Bloc 9 must design the **Mechanical Observable Fabric** on top of canonical T1 observations plus Bloc 6 eligibility/quality.

It must define descriptive T2 objects such as:

```text
LiquidationState
LeverageState
FundingState
OrderFlowState
LiquidityState
PositioningState
BasisState
```

and cross-venue mechanical coordinates such as:

```text
LiquidationBreadth
LeverageCompression
FlowConsensus
LiquidityWithdrawalBreadth
FundingConsensus
VenueDispersion
```

Bloc 9 must preserve:

- venue-local values;
- independent-source counts;
- quality mode;
- source disagreement;
- coverage;
- methodology versions;
- T2→T1→T0 lineage.

It may not create trading signals or execution logic.

---

## 23. Final planning verdict

`PASS_BLOC_08_PLAN_FROZEN`

Rationale:

The sensor fabric now has a complete forward recorder plan using the same evidence and quality substrate as historical research: public/free-only live transports, exact T0 capture, event/arrival timing truth, sequence-aware continuity, reconnect/resubscribe rules, machine-offline gap truth, bounded historical repair, priority-aware local storage, explicit fidelity profiles, provider-specific live playbooks, independence-aware redundancy, historical/live normalization equivalence, adversarial resilience tests, a bounded multi-provider pilot, and 30 staged implementation checkpoints.

`human_review_required = TRUE`
`next_bloc_planning_authorized = FALSE until operator asks for Bloc 9`
