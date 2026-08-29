# BLOC 8 — LIVE HEALTH, GAP REGISTRY & REPAIR HANDOFF

**Planning status:** COMPLETE FOR THIS CHAPTER  
**Implementation status:** NOT STARTED

---

## 1. Objective

Define how live collection surfaces health, records forward-time gaps, distinguishes venue/feed failures from local-machine outages, and hands bounded repair work back to the historical backfill infrastructure without erasing original live provenance.

---

## 2. Health model integration

Bloc 8 does not invent a separate quality model.

It populates the Bloc 6 hierarchy:

```text
ProviderHealth
      ↓
FeedHealth
      ↓
ObservationHealth
      ↓
CanonicalSensorHealth
```

Live acquisition adds high-frequency operational evidence into those objects.

---

## 3. Live provider health inputs

Provider-level health may consider:

```text
transport connect success
public endpoint reachability
server-time response
rate-limit behavior
subscription acceptance
provider-wide error rate
schema/access changes
```

A single stale symbol/feed does not necessarily downgrade the entire provider to failed.

---

## 4. Feed health inputs

Per feed:

```text
last_message_at
expected cadence
heartbeat status
sequence status
checksum status
subscription status
poll success rate
lag distribution
reconnect frequency
```

---

## 5. Observation health inputs

Each T1 live observation may inherit:

- T0 integrity;
- timing confidence;
- identity confidence;
- semantic confidence;
- gap adjacency;
- repair provenance;
- source health at observation time.

---

## 6. Live gap taxonomy

Minimum forward gap reasons:

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

`CONFIG_DISABLED` and `UNIVERSE_NOT_SELECTED` are expected absence, not accidental gap.

---

## 7. Gap scope

A gap is scoped by:

```text
provider
venue
sensor
instrument or instrument_scope
start_at
end_at
transport/session
reason
```

One Binance WebSocket outage should not create a synthetic Gate gap.

---

## 8. Gap confidence

```text
PROVEN
PROBABLE
POSSIBLE
NOT_A_GAP
```

Examples:

- sequence ID jump = PROVEN;
- disconnect in a sparse liquidation event feed with no repair source = POSSIBLE;
- planned disabled feed = NOT_A_GAP.

---

## 9. Gap lifecycle

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

A gap may have both:

```text
original_venue_repair_status
canonical_sensor_coverage_status
```

because alternate venues can restore economic coverage without restoring original venue evidence.

---

## 10. Local machine offline intervals

Recorder supervision must persist:

```text
RecorderOfflineInterval
```

Fields:

```text
host_id
last_clean_heartbeat_at
shutdown_or_loss_detected_at
restart_at
shutdown_type
confidence
```

If the machine was intentionally shut down, preserve that fact.

---

## 11. Restart gap planning

At startup:

```text
last durable checkpoint
→ current wall clock
→ expected feeds
→ provider repair capabilities
→ construct candidate gaps
→ classify expected vs accidental
→ enqueue bounded repairs
```

No unbounded “fill everything since last run” without storage/rate checks.

---

## 12. Repair routing

Repair priority:

```text
same provider + exact same sensor semantics
→ same provider compatible historical endpoint
→ same provider bulk archive
→ alternate provider canonical coverage only
→ unrepaired/data blocked
```

This is the live counterpart of Bloc 7 venue-first gap repair.

---

## 13. Repair window overlap

To avoid edge omissions, repair requests may include a small configurable overlap around the gap boundary.

Example:

```text
gap 12:00–12:05
repair query 11:59:30–12:05:30
```

Overlap duplicates are resolved at T1 using provider IDs/Bloc 5 dedupe rules.

---

## 14. Repair deadline

Some providers expose only limited recent history.

Each gap may have:

```text
repair_deadline_at
```

The repair scheduler prioritizes expiring repair opportunities without violating free-only/rate/storage policy.

---

## 15. Forward repair classes

```text
R0_NOT_NEEDED
R1_SAME_PROVIDER_EXACT
R2_SAME_PROVIDER_NORMALIZABLE
R3_ALTERNATE_PROVIDER_COVERAGE
R4_UNREPAIRABLE
R5_REPAIR_ACCESS_BLOCKED
```

---

## 16. Sensor continuity state

At any time the canonical sensor may be:

```text
LIVE_REDUNDANT
LIVE_SINGLE_SOURCE
LIVE_DEGRADED
LIVE_PARTIAL
LIVE_GAP
HISTORICAL_REPAIR_PENDING
DATA_BLOCKED
```

This is separate from market state.

---

## 17. Independence-aware live redundancy

Bloc 6 dependency groups apply to live data too.

If:

```text
Binance live OI
Bybit live OI
Coinalyze aggregated OI
```

and Coinalyze depends on Binance/Bybit, strict independent source count remains 2.

---

## 18. Live disagreement events

When simultaneously comparable sources diverge materially, create:

```text
LiveDisagreementEvent
```

Fields:

```text
sensor
asset/contract scope
source_set
window
magnitude
comparability_class
suspected_reason
quality_action
```

Disagreement is not automatically an error.

---

## 19. Distinguishing real venue heterogeneity from bad feed

Diagnostic order:

```text
T0 integrity
→ sequence/timestamp health
→ identity
→ units/normalization
→ publication lag
→ provider methodology
→ venue-specific economic divergence
```

Do not quarantine a source merely for disagreeing with the majority.

---

## 20. Health evidence retention

Live health itself is research infrastructure evidence and should be stored as time series/events:

```text
provider_health_history
feed_health_history
sensor_health_history
reconnect_events
gap_events
repair_events
```

This allows later research to exclude poor-quality periods reproducibly.

---

## 21. Quality adjacency to gaps

Observations near a repaired or uncertain gap may carry flags:

```text
PRE_GAP_ADJACENT
POST_GAP_ADJACENT
REPAIRED_INTERVAL
UNKNOWN_CONTINUITY_ADJACENT
```

No blanket deletion is required; research can choose policy later.

---

## 22. Partial repair semantics

A 5-minute gap might be repaired for:

- trades;
- OI;
- funding;

but not full book deltas.

The gap registry must therefore be sensor-specific and allow:

```text
market mechanics repaired
microstructure unrepaired
```

instead of one global repaired boolean.

---

## 23. Book-gap behavior

If full-book deltas gap and no exact replay is available:

- invalidate book reconstruction from gap onward;
- obtain new snapshot;
- mark prior missing delta interval;
- resume a new valid book epoch.

Do not pretend the book can be interpolated through the missing sequence.

---

## 24. Gap impact on derived observables

Bloc 9 later consumes explicit eligibility from Bloc 6.

Example:

```text
flow observable eligible
book-withdrawal observable DATA_BLOCKED
```

for the same event window.

Bloc 8 does not fabricate substitutes.

---

## 25. Operator-facing status packet

The live recorder should expose a concise health snapshot:

```text
recorder status
provider sessions
P0 sensor health
P1 sensor health
P2 sensor health
open gaps
repair queue
storage state
last successful T0 commit
```

This is operational visibility, not a trading dashboard.

---

## 26. Daily integrity summary

At a configurable daily UTC boundary, emit:

```text
messages captured
polls attempted/succeeded
reconnects
gaps opened
gaps repaired
unrepaired minutes/intervals
source revisions
T0 bytes
T1 rows
quality modes by sensor
```

This becomes a long-run evidence trail.

---

## 27. Historical backfill handoff object

Proposed:

```text
GapRepairRequest
```

Fields:

```text
gap_id
provider
venue
sensor
instrument
start_at
end_at
preferred_modes
repair_deadline_at
priority
expected_semantics
```

Bloc 7 infrastructure executes the repair using already verified provider-native methods.

---

## 28. Bounded repair doctrine

The live recorder may request repair only for known forward gaps.

It may not independently launch broad multi-year backfills.

That remains Bloc 7 orchestration.

---

## 29. Access-policy changes during live operation

If a free source becomes paid/restricted:

```text
ACCESS_REVIEW_REQUIRED
```

Open feeds stop cleanly if required.

Gaps begin at the access-loss boundary.

No paid rescue.

---

## 30. Geo restriction changes

A source becoming geo-blocked is distinct from provider outage.

Record:

```text
ACCESS_BLOCKED_GEO
```

Then let Bloc 6 determine whether alternate sources maintain canonical sensor coverage.

---

## 31. Acceptance tests

Must test:

- provider outage but redundant sensor remains available;
- one-feed stale while provider healthy;
- local shutdown gap;
- local crash gap;
- exact same-provider repair;
- alternate-provider coverage without venue repair;
- limited-history repair deadline;
- book sequence gap with new epoch;
- independence-aware source count;
- disagreement without automatic quarantine;
- daily health summary determinism.

---

## 32. Planning decision

A future live gap should be discoverable, bounded, explainable, and repairable where possible—not something the researcher learns about months later from a weird hole in a chart.
