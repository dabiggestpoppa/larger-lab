# BLOC 8 — LIVE BLACK-BOX RECORDER ARCHITECTURE

**Planning status:** COMPLETE FOR THIS CHAPTER  
**Implementation status:** NOT STARTED  
**Parent:** Bloc 7 historical backfill program  
**Purpose:** define one always-on, local-first, provider-independent forward recorder that uses the same Bloc 3 adapters, Bloc 4 T0 evidence store, Bloc 5 T1 normalizers, and Bloc 6 quality system as historical research.

---

## 1. Mission

The recorder exists so future research never again depends on whether a third party preserved a historical feed.

It must continuously preserve public mechanical evidence for the supported universe while the local machine is online.

It is not a trading engine.
It is not an execution daemon.
It is not an alerting product.
It is not a separate live-data architecture.

It is the forward-time counterpart of Bloc 7:

```text
PUBLIC LIVE PROVIDER FEEDS
        ↓
Bloc 3 provider adapters / feed clients
        ↓
LIVE ACQUISITION ENVELOPES
        ↓
Bloc 4 T0A exact evidence + T0B raw projections
        ↓
Bloc 5 T1 PIT normalization
        ↓
Bloc 6 quality / redundancy / failover
        ↓
Bloc 9 mechanical observables
```

Hard rule:

> Historical and live acquisition may use different transport mechanics, but they must converge into the same evidence, lineage, normalization, and quality contracts.

---

## 2. Core architectural principles

### P1 — Local-first

Default operation is on the user's machine.

No cloud service is required for correctness.

Cloud deployment may be added later without changing recorder semantics.

### P2 — Public data only

The recorder uses only free/public or free-limited automated sources admitted by the existing free-only policy.

No trading API keys are required.
No private account state is collected.
No payment/staking/transaction dependency may be introduced.

### P3 — Exact source evidence before analytics

Every accepted live message, poll response, archive fragment, or repair response enters T0 before downstream aggregation.

### P4 — Event time and arrival time are distinct

Live systems must retain:

```text
source_event_at
source_publish_at        # when available
collector_received_at
collector_committed_at
normalized_at
```

The recorder must never replace source event time with local receive time.

### P5 — At-least-once capture is safer than silent omission

Duplicates can be deduped downstream with lineage.
Missing source evidence cannot be reconstructed reliably later.

### P6 — Reconnect is not equivalent to continuity

After any disconnect, the system must explicitly determine whether a gap occurred.

### P7 — Sequence integrity is provider-specific

Providers with update IDs, sequence numbers, checksums, or snapshot+delta books keep those semantics intact.

### P8 — Machine-off periods are honest gaps

If the local machine is shut down:

```text
LOCAL_RECORDER_OFFLINE
```

is recorded.

Later historical/public endpoints may repair some gaps, but the system may not pretend uninterrupted live capture existed.

### P9 — Continuous recording must respect disk pressure

Critical P0 mechanics survive before optional high-volume L2 streams.

### P10 — Live health and market state are different

A feed can be unhealthy during a calm market.
A feed can be healthy during extreme volatility.

Collector health metadata must never be interpreted as market mechanics.

---

## 3. Recorder layers

```text
L8.0 SUPERVISION
  process lifecycle / start / stop / restart / heartbeat

L8.1 TRANSPORT
  WebSocket / REST poll / SSE if later supported / provider files

L8.2 SESSION
  authentication-free session state / subscriptions / rate budgets

L8.3 CAPTURE
  receive exact provider payload + local timing metadata

L8.4 INTEGRITY
  sequence checks / checksum checks / expected interval checks

L8.5 T0 COMMIT
  exact evidence durable write

L8.6 NORMALIZE
  T1 canonical observations

L8.7 QUALITY
  provider/feed/observation/sensor health

L8.8 GAP REGISTRY
  disconnect / sequence / polling / local-offline gaps

L8.9 REPAIR HANDOFF
  bounded historical repair through Bloc 7 infrastructure
```

No layer may jump over T0.

---

## 4. Live acquisition modes

Initial transport modes:

```text
WEBSOCKET_STREAM
REST_FIXED_INTERVAL_POLL
REST_EVENT_DRIVEN_POLL
REST_SNAPSHOT_REPAIR
HISTORICAL_GAP_REPAIR
PROVIDER_BULK_FORWARD_DROP   # only if provider exposes rolling public files
```

Each provider/sensor capability chooses a mode explicitly.

Examples:

```text
TRADES
  usually WEBSOCKET_STREAM

LIQUIDATIONS
  WebSocket when public and complete enough
  REST analytics poll when provider exposes interval aggregates

OPEN INTEREST
  REST_FIXED_INTERVAL_POLL or provider analytics feed

FUNDING
  REST_FIXED_INTERVAL_POLL plus funding-event capture where supported

BOOKS
  WEBSOCKET_STREAM snapshot+delta or snapshot polling depending provider
```

---

## 5. Core runtime objects

### `RecorderInstance`

Represents one running recorder process.

Required fields:

```text
recorder_instance_id
host_id
started_at
stopped_at
software_version
config_version
status
shutdown_reason
last_heartbeat_at
```

### `FeedSubscription`

```text
subscription_id
provider_id
venue_id
sensor_family
instrument_native
canonical_contract_ref
transport_mode
subscription_params
started_at
ended_at
status
```

### `LiveSession`

```text
session_id
provider_id
transport_mode
opened_at
closed_at
close_reason
reconnect_parent_session_id
remote_endpoint_id
```

### `LiveCaptureEnvelope`

```text
capture_id
provider_id
venue_id
subscription_id
session_id
sensor_family
source_event_at
collector_received_at
collector_committed_at
raw_payload_ref
transport_metadata
sequence_metadata
quality_flags
```

### `HeartbeatObservation`

```text
heartbeat_id
provider_id
feed_id
expected_interval
last_message_at
observed_at
lag_ms
status
```

### `LiveGap`

```text
gap_id
provider_id
venue_id
sensor_family
instrument
start_at
end_at
reason
sequence_start
sequence_end
repair_status
repair_evidence_refs
```

### `RecorderCheckpoint`

```text
checkpoint_id
feed_id
session_id
last_durable_source_position
last_t0_commit_ref
last_t1_generation_ref
written_at
```

---

## 6. Sensor recording priority

Forward capture priority follows research value and storage economics.

### P0 — always attempt while machine is online

```text
LIQUIDATIONS
OPEN INTEREST
FUNDING
POSITIONING/BASIS where cheap
RECORDER HEALTH / GAP METADATA
```

### P1 — high-value event flow

```text
TRADES / AGGTRADES
AGGRESSOR FLOW INPUTS
LIQUIDATION-TAGGED TRADES
```

### P2 — expensive microstructure

```text
FULL L2 / DEEP BOOK DELTAS
HIGH-FREQUENCY SNAPSHOTS
```

P2 is U0-first and disk-governed.

---

## 7. Universe policy

The same U0/U1/U2 doctrine remains.

### U0 Mechanism Core

Richest forward capture:

- trades
- liquidations
- OI
- funding
- deep books where feasible
- positioning/basis

### U1 Broad Research

- liquidations
- OI
- funding
- trades or aggregated flow
- coarse book metrics

### U2 Long Tail

- OI
- funding
- liquidation statistics
- cheap activity/positioning

Full-depth U2 remains disabled by default.

Universe changes are point-in-time events, not silent config edits.

---

## 8. Forward universe transitions

When an instrument enters or leaves a universe tier:

```text
UniverseMembershipEvent
```

must record:

```text
instrument
old_tier
new_tier
effective_at
observed_at
reason
policy_version
```

Collection changes apply after the membership event becomes effective.

Historical data is not backfilled merely because an asset moves to U0 unless Bloc 7 later authorizes it.

---

## 9. Provider session states

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

Transitions are explicit and auditable.

No hidden infinite reconnect loop.

---

## 10. Feed states

A provider can remain healthy while one feed fails.

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

This maps directly into Bloc 6 feed-health objects.

---

## 11. Startup sequence

Recorder startup must be ordered:

```text
1 load config + policy versions
2 verify free-only provider eligibility
3 inspect disk/quota state
4 open T0 / metadata repositories
5 recover incomplete local checkpoints
6 materialize point-in-time universe
7 construct feed plan
8 start low-volume P0 feeds
9 verify health
10 start P1 feeds
11 start authorized P2 feeds
12 emit READY or DEGRADED_READY
```

If T0 storage is unavailable, the recorder must not continue as an in-memory-only data consumer.

---

## 12. Shutdown sequence

Graceful shutdown:

```text
stop new subscriptions
→ stop polling schedules
→ drain in-flight messages
→ commit T0
→ commit T1 where configured
→ write feed checkpoints
→ write final heartbeats
→ close sessions
→ mark recorder stopped
```

Forced shutdown is later reconciled from durable state.

---

## 13. Crash philosophy

A crash may produce:

- duplicate messages after reconnect;
- an unclosed session record;
- an interval whose final expected poll never occurred;
- a book whose delta sequence cannot resume safely.

It may not silently produce:

- fabricated continuity;
- advanced checkpoints without durable evidence;
- fake zero intervals;
- untraceable loss.

Recovery favors conservative gaps and duplicate capture over invented completeness.

---

## 14. Local machine identity

Each recorder host gets a persistent non-secret `host_id`.

This is useful because later operation may include:

```text
DESKTOP
LAPTOP
CLOUD_REPLICA
```

but v1 assumes one local authoritative recorder.

Multiple hosts may not simultaneously claim one exclusive feed lease unless multi-recorder coordination is explicitly implemented later.

---

## 15. No execution boundary

The recorder may contain:

- public market endpoints;
- public WebSocket URLs;
- optional read-only/free API keys where allowed.

It may not contain:

- order placement;
- withdrawal;
- transfer;
- account-position state;
- private balances;
- trading credentials.

This must be enforceable by package boundaries and tests.

---

## 16. Configuration architecture

Proposed config:

```text
config/crypto_sensor_fabric/live/
  recorder.yaml
  providers.yaml
  universe_policy.yaml
  sensor_policy.yaml
  polling_intervals.yaml
  disk_policy.yaml
  reconnect_policy.yaml
  repair_policy.yaml
```

Config is versioned and included in recorder evidence.

---

## 17. Implementation module plan

```text
quant-lab/src/crypto_sensor_fabric/live/
  models.py
  recorder.py
  supervisor.py
  planner.py
  websocket.py
  polling.py
  session.py
  heartbeat.py
  sequence.py
  checkpoints.py
  gaps.py
  repair.py
  retention.py
  health_bridge.py
  t0_sink.py
  t1_bridge.py
  providers/
```

Provider modules remain thin wrappers around Bloc 3/provider-specific live mechanics.

---

## 18. Key non-goals

Bloc 8 does not define:

- T2 mechanical state formulas;
- cross-venue aggregate mechanics;
- signal generation;
- strategy logic;
- order routing;
- automated trading;
- production cloud orchestration;
- mobile notifications.

---

## 19. Acceptance intent

Bloc 8 implementation must later prove:

1. capture persists exact evidence;
2. event-time and receive-time remain distinct;
3. disconnect produces explicit continuity review;
4. sequence gaps are detected;
5. restart resumes from durable checkpoints;
6. local shutdown gaps are honest;
7. P0 sensors survive disk pressure longer than P2;
8. historical and live evidence normalize into the same T1 contracts;
9. Bloc 6 health consumes live evidence cleanly;
10. no execution/private-account capability exists.

---

## 20. Planning decision

The live recorder is one acquisition mode of the same sensor fabric, not a parallel market-data product.

`human_review_required = TRUE`
