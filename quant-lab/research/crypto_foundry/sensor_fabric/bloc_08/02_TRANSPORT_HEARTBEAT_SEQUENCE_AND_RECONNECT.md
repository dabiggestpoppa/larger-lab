# BLOC 8 — TRANSPORT, HEARTBEAT, SEQUENCE & RECONNECT

**Planning status:** COMPLETE FOR THIS CHAPTER  
**Implementation status:** NOT STARTED

---

## 1. Objective

Define the live transport mechanics so WebSocket and REST feeds can fail, reconnect, resume, and repair without silently fabricating continuity.

The recorder must answer four questions for every feed:

1. Did the transport stay connected?
2. Did expected source messages continue arriving?
3. Did source ordering remain valid?
4. If continuity broke, can the gap be proven and repaired?

---

## 2. Transport abstraction

Common transport interface:

```text
open()
close()
subscribe()
unsubscribe()
receive()
poll()
health()
checkpoint()
```

Transport implementations:

```text
WebSocketTransport
RestPollingTransport
RestSnapshotTransport
HistoricalRepairTransport
```

Provider-specific adapters own endpoint syntax and provider-native subscription messages.

Bloc 8 owns lifecycle/orchestration.

---

## 3. WebSocket session contract

Each connection becomes a `LiveSession` with:

```text
session_id
provider_id
endpoint_id
opened_at
connected_at
closed_at
close_reason
socket_error
reconnect_parent_session_id
remote_ping_supported
local_ping_supported
```

Every reconnect creates a new session ID.

Do not reuse one session ID across transport breaks.

---

## 4. Heartbeat sources

Heartbeat evidence may come from:

1. provider-native ping/pong;
2. application-level provider heartbeat;
3. expected market-message cadence;
4. local collector heartbeat.

These are distinct.

A provider pong only proves the socket is alive, not that a particular market feed is updating.

---

## 5. Heartbeat states

```text
HEALTHY
QUIET_BUT_WITHIN_EXPECTATION
STALE_WARNING
STALE_CONFIRMED
TRANSPORT_ALIVE_FEED_STALE
TRANSPORT_DOWN
UNKNOWN
```

Per-feed stale thresholds are configured from expected cadence and capability evidence.

Do not use one universal stale timeout.

---

## 6. Quiet markets and false stale detection

Some event feeds can legitimately produce no messages.

Examples:

```text
liquidation event stream
large-trade event stream
```

For sparse event feeds, health must combine:

- transport heartbeat;
- subscription acknowledgement;
- independent provider health;
- optional periodic REST reconciliation.

Absence of liquidation events cannot by itself mark the feed stale.

---

## 7. REST polling scheduler

Polling schedules must be deterministic and jitter-aware.

Each poll definition includes:

```text
provider
sensor
instrument scope
nominal interval
allowed jitter
request weight
priority
stale deadline
repair window
```

Examples:

```text
OI             every 60s / 5m depending verified endpoint
funding        aligned to provider publication cadence
analytics      provider-specific interval
book snapshot  only where streaming unavailable or for repair
```

No endpoint is hammered merely because the scheduler fell behind.

---

## 8. Poll alignment

For interval-derived provider analytics, prefer alignment to source intervals rather than recorder start time.

Example:

```text
5m analytics
00:00
00:05
00:10
...
```

A small configurable publication delay can be used after interval end.

The delay itself must be observable and versioned.

---

## 9. Poll outcomes

```text
SUCCESS_DATA
SUCCESS_VALID_ZERO
SUCCESS_PROVIDER_EMPTY
NO_CHANGE
RATE_LIMITED
RETRYABLE_ERROR
ACCESS_ERROR
SEMANTIC_ERROR
TIMEOUT
SKIPPED_RESOURCE_PRESSURE
```

`SUCCESS_PROVIDER_EMPTY` is not automatically a zero measurement.

---

## 10. Sequence models

Providers may use:

```text
MONOTONIC_SEQUENCE
UPDATE_ID_RANGE
PREVIOUS_UPDATE_ID_CHAIN
CHECKSUMMED_BOOK
TIMESTAMP_ONLY
NO_SEQUENCE_AVAILABLE
```

The provider adapter must declare which model applies per feed.

---

## 11. Sequence integrity states

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

Sequence failures must create evidence and, when needed, a `LiveGap`.

---

## 12. Order-book snapshot + delta doctrine

For feeds requiring snapshot + deltas:

```text
1 connect
2 buffer deltas
3 fetch authoritative snapshot
4 establish snapshot sequence/update ID
5 discard deltas older than snapshot
6 apply contiguous buffered deltas
7 verify checksum when available
8 begin live application
```

If continuity fails:

```text
STOP CLAIMING VALID BOOK STATE
→ quarantine current reconstruction
→ obtain fresh snapshot
→ restart sequence chain
```

Never bridge a sequence gap by simply applying the next delta.

---

## 13. Trade/event stream ordering

Where exact ordering can be proven with provider IDs, preserve it.

Where only timestamps exist:

- preserve provider timestamp;
- preserve receive order;
- avoid inventing deterministic micro-order within equal timestamps.

`TIMESTAMP_COLLISION_UNORDERED` may be emitted.

---

## 14. Reconnect policy

Reconnect stages:

```text
IMMEDIATE_RETRY
SHORT_BACKOFF
EXPONENTIAL_BACKOFF
COOLDOWN
ACCESS_REVIEW
```

Backoff must respect provider rate limits and Bloc 6 health state.

Example bounded progression:

```text
1s
2s
5s
10s
30s
60s
max configured cap
```

Exact values remain config, not ontology.

---

## 15. Reconnect evidence

Record:

```text
reconnect_attempt
reason
backoff_duration
attempt_started_at
attempt_completed_at
result
new_session_id
```

This makes future outage analysis auditable.

---

## 16. Resubscribe semantics

After reconnect:

1. create new transport session;
2. verify endpoint access class still valid;
3. resubscribe from current PIT universe;
4. wait for provider acknowledgements where available;
5. establish sequence integrity;
6. determine gap interval;
7. trigger bounded repair if allowed;
8. only then return feed to HEALTHY.

---

## 17. Gap determination after reconnect

A reconnect does not automatically mean a data gap.

Gap determination uses:

- last durable source event;
- disconnect time;
- first post-reconnect source event;
- provider sequence IDs;
- periodic REST/bulk endpoints;
- expected feed behavior.

Possible results:

```text
NO_GAP_PROVEN
GAP_PROVEN
GAP_POSSIBLE_UNVERIFIABLE
NO_EVENTS_EXPECTED
```

---

## 18. REST repair after streaming gap

When provider offers a compatible historical/recent REST endpoint:

```text
stream gap
→ bound missing interval
→ query provider-native REST repair
→ commit repair evidence through T0
→ normalize T1
→ mark repaired interval lineage
```

Repair data remains tagged with acquisition mode.

Do not rewrite streaming messages as if they arrived live.

---

## 19. Repair evidence classes

```text
LIVE_NATIVE
LIVE_RECOVERED_SAME_PROVIDER
HISTORICAL_REPAIR_SAME_PROVIDER
ALTERNATE_PROVIDER_COVERAGE
UNREPAIRED
```

Alternate-provider observations improve economic sensor coverage but do not repair the original venue stream.

---

## 20. Duplicate capture after reconnect

Duplicates are expected when a repair query overlaps the last live event.

Policy:

```text
preserve both T0 acquisition paths
→ use hard provider IDs for T1 economic dedupe where available
→ retain lineage to LIVE + REPAIR sources
```

No destructive T0 dedupe beyond byte identity.

---

## 21. Local clock discipline

Recorder host must maintain UTC timing.

Monitor host clock drift where possible.

Quality flags:

```text
HOST_CLOCK_OK
HOST_CLOCK_DRIFT_WARNING
HOST_CLOCK_DRIFT_CRITICAL
HOST_CLOCK_UNVERIFIED
```

A large local clock error can corrupt receive-latency analysis even if provider event timestamps remain usable.

---

## 22. Arrival latency

Derived operational metadata:

```text
arrival_latency_ms = collector_received_at - source_event_at
```

Only calculate when source timestamp semantics make this meaningful.

Do not interpret negative/suspicious latency as market behavior; route it to clock/timestamp QA.

---

## 23. Provider server-time probes

Where public server time exists, periodically store:

```text
provider_server_time
local_send_time
local_receive_time
estimated_offset
round_trip_ms
```

This is operational timing evidence, not a correction silently applied to raw timestamps.

---

## 24. REST idempotency

Every poll request reuses Bloc 3 deterministic request fingerprints.

If a poll is retried:

- repeated identical bytes may dedupe at T0A;
- acquisition history remains separate;
- semantic duplicates may dedupe only in T1 under Bloc 5 rules.

---

## 25. Failure taxonomy additions

Live-specific failures:

```text
SocketConnectFailure
SubscriptionRejected
SubscriptionAckTimeout
UnexpectedDisconnect
HeartbeatTimeout
FeedStale
SequenceGap
ChecksumFailure
SnapshotSyncFailure
ResubscribeFailure
PollingOverrun
LocalClockDrift
LocalShutdownGap
CollectorCrashGap
```

These complement, not replace, Bloc 3 acquisition failures.

---

## 26. Acceptance tests

Future implementation must test:

- socket connect/disconnect/reconnect;
- heartbeat but stale feed;
- sparse event stream with no false stale;
- provider ping timeout;
- sequence duplicate;
- sequence gap;
- checksum failure;
- snapshot+delta bootstrap;
- snapshot+delta gap recovery;
- poll timeout and retry;
- poll schedule drift;
- repair overlap duplicates;
- clock drift warning;
- reconnect session lineage.

All tests use fixtures/fake transports unless explicitly opt-in network smoke tests.

---

## 27. Planning decision

Transport continuity must be proven, not inferred from a green socket icon.
