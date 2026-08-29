# BLOC 5 — TIMESTAMP, REVISION & AVAILABILITY TRUTH

**Planning status:** COMPLETE DRAFT FOR FREEZE  
**Implementation status:** NOT STARTED  
**Purpose:** define point-in-time timing semantics so T1 observations can distinguish event time, economic effective time, publication time, market availability, system ingestion, and later historical revision.

---

## 1. Why timestamp truth matters

A timestamp column is not enough.

Different providers may timestamp:

- trade execution;
- snapshot capture;
- interval start;
- interval end;
- settlement/funding application;
- API publication;
- archive generation;
- download time;
- local ingestion.

If these are collapsed, historical replay can leak information even when every value came from a public source.

Hard rule:

> T1 must preserve the distinction between when something happened, when it became economically effective, when it was publicly available, and when our system acquired it.

---

## 2. Canonical timestamp vocabulary

T1 observations should support the following fields where semantically applicable.

```text
source_event_at
interval_start_at
interval_end_at
effective_at
published_at
market_available_at
observed_at
ingested_at
normalized_at
```

Not every sensor uses every field.

Null means **not applicable or not verified**, never "same as another timestamp" unless a documented rule sets them equal.

---

## 3. Definitions

### `source_event_at`

Timestamp attached to the underlying provider-native market event.

Examples:
- trade execution time;
- liquidation trade time;
- order-book update time.

### `interval_start_at`

Beginning of an aggregation window.

### `interval_end_at`

End of an aggregation window.

### `effective_at`

When the observation becomes economically true for the market object.

Examples:
- funding settlement/application time;
- OI snapshot effective instant;
- interval statistic representing the window just completed.

### `published_at`

When the provider says the observation or file was published, if separately available.

### `market_available_at`

Earliest defensible time that the information could have been observed from a public market-data path by an external participant.

This is the key historical-replay timestamp.

### `observed_at`

When our acquisition process received/observed the source response or stream message.

### `ingested_at`

When the raw evidence was durably committed to T0.

### `normalized_at`

When the T1 record was produced.

---

## 4. Two availability clocks

The system must preserve two different concepts:

```text
MARKET AVAILABILITY
SYSTEM AVAILABILITY
```

`market_available_at` answers:

> When could a market participant using the documented public feed have known this?

`ingested_at` answers:

> When did our system actually store it?

These clocks must not be silently substituted for each other.

Historical research may reconstruct market availability from archived events only when the source semantics prove the event was public contemporaneously.

---

## 5. Availability basis

Every T1 row requiring replay eligibility should carry:

```text
availability_basis
availability_confidence
```

Allowed initial values:

```text
REALTIME_PUBLIC_EVENT
REALTIME_PUBLIC_SNAPSHOT
PUBLIC_INTERVAL_CLOSE
DELAYED_PUBLICATION
HISTORICAL_ARCHIVE_RECONSTRUCTION
PROVIDER_DECLARED_PUBLIC_TIME
SYSTEM_ONLY_OBSERVED
UNKNOWN
```

Interpretation:

- `REALTIME_PUBLIC_EVENT`: event was exposed publicly at/near event time;
- `HISTORICAL_ARCHIVE_RECONSTRUCTION`: row was obtained later, but documentation/evidence says the underlying event was contemporaneously public;
- `SYSTEM_ONLY_OBSERVED`: we only know when our system saw it;
- `UNKNOWN`: cannot safely place in market-time replay.

`UNKNOWN` and unsupported `SYSTEM_ONLY_OBSERVED` rows are blocked from strict historical market replay.

---

## 6. Conservative availability derivation

Planned function:

```python
derive_market_available_at(
    sensor_family,
    provider_semantics,
    event_time,
    interval_start,
    interval_end,
    published_at,
    acquisition_metadata,
) -> AvailabilityResolution
```

Rules should be conservative.

Examples:

### Trade

If provider documentation and live/public interface establish real-time trade publication:

```text
market_available_at ~= source_event_at + documented/minimal feed latency policy
```

v1 may use `source_event_at` as the market-availability anchor only when the source is explicitly classified contemporaneous-public.

### Aggregated interval statistic

If a 5-minute liquidation/OI/taker statistic is only complete after the interval closes:

```text
market_available_at >= interval_end_at
```

Never interval start.

### Funding

If funding is published before settlement, preserve both:

```text
published_at < effective_at
```

The rate may be knowable before it is economically applied.

Research must choose which semantic it needs rather than collapsing them.

### Archive file

Archive download time does not automatically become the market event availability time.

The reconstruction is allowed only when contemporaneous-public semantics are established.

---

## 7. Interval boundary convention

Every interval observation must explicitly declare:

```text
interval_closed
interval_time_convention
```

Initial conventions:

```text
LEFT_CLOSED_RIGHT_OPEN
LEFT_OPEN_RIGHT_CLOSED
PROVIDER_NATIVE_UNKNOWN
POINT_SAMPLE
```

Do not guess whether timestamp `12:00` means:

- window starting at 12:00;
- window ending at 12:00;
- snapshot sampled at 12:00.

Provider mapping config must state it.

---

## 8. Time zone and precision

Canonical timestamps are UTC and timezone-aware.

Preserve source precision metadata:

```text
SECOND
MILLISECOND
MICROSECOND
NANOSECOND
DATE_ONLY
UNKNOWN
```

Do not fabricate microsecond ordering from millisecond input.

If two events share provider timestamp precision and provider sequence IDs exist, retain sequence separately.

---

## 9. Clock skew

Potential provider/system clock discrepancy is flagged rather than silently corrected.

Quality fields:

```text
clock_skew_ms optional
clock_skew_methodology_id optional
```

Correction requires a documented methodology.

Raw source timestamps remain preserved.

---

## 10. Historical revisions

T0 already preserves source mutation/revisions.

Bloc 5 defines how T1 handles them.

Each T1 observation records:

```text
source_revision_id
normalization_generation
supersedes_t1_record_id optional
revision_status
```

Revision statuses:

```text
ORIGINAL
PROVIDER_CORRECTED
SOURCE_MUTATION_REPARSED
NORMALIZATION_REBUILD
IDENTITY_REBUILD
SEMANTIC_REINTERPRETATION
```

No in-place overwrite of prior T1 generation.

---

## 11. Research revision modes

Strict research/replay queries must choose a revision policy.

Initial modes:

```text
AS_KNOWN_THEN
LATEST_VERIFIED
FIRST_SEEN
EXACT_REVISION
ALL_REVISIONS
ERROR_ON_AMBIGUITY
```

### `AS_KNOWN_THEN`

Select only values/revisions that were available by replay cutoff.

### `LATEST_VERIFIED`

Useful for retrospective measurement but **not** automatically PIT-safe.

Every research output must record the revision mode used.

---

## 12. Provider correction leakage

Example:

1. OI for 2022-05-12 was published in 2022.
2. Provider later republishes a corrected historical archive in 2025.
3. Retrospective data file contains corrected value.

A historical replay at 2022-05-12 must not automatically use the 2025 correction under `AS_KNOWN_THEN`.

If original revision is unavailable:

```text
PIT_REVISION_UNCERTAIN
```

The row can remain useful for retrospective science but must not masquerade as exact contemporaneous truth.

---

## 13. Sensor-specific time semantics

### Trades

Primary anchor:

```text
source_event_at
```

Sequence/trade ID retained where available.

### Liquidations

Trade-level liquidation:

```text
source_event_at
```

Interval liquidation statistics:

```text
interval_start_at
interval_end_at
market_available_at >= interval_end_at
```

### Open interest

Must classify each provider observation as:

```text
POINT_SNAPSHOT
WINDOW_STATISTIC
UNKNOWN
```

OI is not automatically flow.

### Funding

Preserve:

```text
published_at
funding_period_start_at optional
funding_period_end_at optional
effective_at
```

### Order book

Preserve snapshot/update timestamp and sequence/version identifiers.

### Positioning/basis

Must document whether the timestamp represents snapshot time or completed interval.

---

## 14. Historical bulk archives

Bulk files need two time layers:

```text
row economic/event timestamps
file acquisition/publication timestamps
```

T0 acquisition metadata proves what file we downloaded.

T1 row semantics prove what each row means economically.

The existence of a 2026 download file containing 2022 rows does not imply those rows first became market information in 2026.

Likewise, archive availability today does not prove the exact archived row existed in that same corrected form in 2022.

Both facts remain represented.

---

## 15. Replay eligibility

A T1 observation is strict-replay eligible only if:

1. identity is PIT-resolved;
2. timestamp semantics are verified;
3. market availability is defensible;
4. revision policy is compatible with replay cutoff;
5. lineage is intact;
6. no blocking quality flag exists.

Planned field:

```text
replay_eligibility =
  ELIGIBLE
  RETROSPECTIVE_ONLY
  BLOCKED_TIMESTAMP
  BLOCKED_REVISION
  BLOCKED_IDENTITY
  BLOCKED_LINEAGE
```

---

## 16. Quality flags

Minimum:

```text
TIME_SEMANTICS_UNVERIFIED
TIME_INTERVAL_BOUNDARY_UNVERIFIED
TIME_MARKET_AVAILABILITY_UNKNOWN
TIME_ARCHIVE_RECONSTRUCTION
TIME_CLOCK_SKEW
TIME_PRECISION_COARSE
TIME_SEQUENCE_MISSING
PIT_REVISION_UNCERTAIN
PIT_LATE_CORRECTION
PIT_PROVIDER_BACKFILL
```

Flags remain attached even if the row is retained for retrospective analysis.

---

## 17. Required modules

```text
normalization/time/
  models.py
  enums.py
  semantics_registry.py
  availability.py
  intervals.py
  revision_policy.py
  replay_gate.py
```

Config:

```text
provider_time_semantics.yaml
revision_policies.yaml
```

---

## 18. Invariants

1. no naive timestamps;
2. no completed interval is available before its end unless provider publishes partial updates and they are modeled separately;
3. `ingested_at` never silently substitutes for `market_available_at`;
4. future corrections do not leak into `AS_KNOWN_THEN` replay;
5. source precision is preserved;
6. archive reconstruction is labeled;
7. unknown provider timestamp semantics fail closed for strict replay;
8. time normalization never mutates T0 evidence.

---

## 19. Handoff

The next document defines the **common semantic/unit normalization contract** used after identity/time resolution.
