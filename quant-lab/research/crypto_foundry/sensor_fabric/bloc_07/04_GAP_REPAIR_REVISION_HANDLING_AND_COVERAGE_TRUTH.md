# BLOC 7 — GAP REPAIR, REVISION HANDLING, AND COVERAGE TRUTH

**Purpose:** define how the historical program detects, classifies, retries and preserves incomplete or revised history without manufacturing continuity.

---

## 1. Historical coverage is multi-state

Canonical backfill coverage state:

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

These states are never collapsed to `0` or `false` in scientific outputs.

---

## 2. Gap categories

### G0 — Request/acquisition gap

Request failed or never completed.

Examples:
- timeout
- 5xx
- archive unavailable temporarily
- retry exhaustion

### G1 — Provider-source temporal gap

Source is accessible but expected interval absent.

### G2 — Raw projection gap

T0A exists but T0B projection failed/incomplete.

### G3 — PIT/normalization gap

Raw provider evidence exists but T1 could not be formed safely.

### G4 — Canonical coverage gap

Requested canonical sensor lacks enough valid evidence for requested scope.

Bloc 7 records G0/G1 directly and imports G2/G3/G4 from downstream validation.

---

## 3. Expected-coverage logic

A gap exists only relative to expectation.

Expectation derives from:

```text
verified provider capability
× instrument active lifecycle
× sensor support
× granularity support
× historical range
× known provider maintenance / archive boundaries
```

Before listing/launch:

```text
NOT_EXPECTED
```

not gap.

After delisting, if source should not exist:

```text
NOT_EXPECTED
```

---

## 4. Provider-empty is not automatically valid zero

Three distinct cases:

```text
VALID_ZERO
  provider explicitly reports zero measurement

PROVIDER_EMPTY_CONFIRMED
  provider confirms no rows/events for a boundary and semantics permit empty

SUSPICIOUS_EMPTY
  endpoint returned no data where data was expected
```

`SUSPICIOUS_EMPTY` enters gap investigation.

---

## 5. Gap repair queue

Create `BackfillGapTicket`:

```text
gap_id
provider
sensor
instrument
start_at
end_at
gap_class
first_detected_at
attempt_count
last_attempt_at
preferred_repair_method
max_attempts
status
evidence_refs
```

Statuses:

```text
OPEN
RETRY_SCHEDULED
ALTERNATE_ENDPOINT_REPAIR
ARCHIVE_REPAIR
SOURCE_CONFIRMED_ABSENT
HISTORY_UNAVAILABLE
RESOLVED
QUARANTINED
MANUAL_REVIEW
```

---

## 6. Repair preference order

For the same provider/venue/sensor:

1. retry original verified source;
2. use same-provider alternate verified acquisition mode;
3. use same-provider archive/API counterpart;
4. confirm provider history unavailable;
5. stop provider-specific repair.

Other providers may improve canonical economic-sensor coverage, but they do **not** resolve the missing provider gap.

---

## 7. Archive/API reconciliation

When both first-party archive and REST history exist for same provider/sensor:

- compare overlapping sample intervals;
- preserve both acquisitions;
- use hard event IDs where possible;
- detect provider revisions;
- do not assume archive is newer/canonical unless provider semantics support it.

Possible verdicts:

```text
MATCH
NORMALIZABLE_MATCH
REVISION_DETECTED
SEMANTIC_DIFFERENCE
SOURCE_CONFLICT
```

---

## 8. Revision handling

Bloc 4 raw rule remains immutable.

When source history changes:

```text
old T0A blob remains
new T0A blob appended
SourceRevision created
T0B/T1 new generation may be produced
```

Never rewrite prior evidence.

`BackfillRevisionTicket` fields:

```text
revision_id
provider
sensor
instrument
source_boundary
old_blob_sha256
new_blob_sha256
first_seen_old
first_seen_new
provider_declared_revision
semantic_diff_status
normalization_impact
research_impact
review_status
```

---

## 9. Source mutation severity

```text
R0_BYTE_CHANGE_NO_SEMANTIC_CHANGE
R1_RECORD_ADDITION_REMOVAL
R2_VALUE_REVISION
R3_TIMESTAMP_OR_IDENTITY_CHANGE
R4_SCHEMA_OR_MEANING_CHANGE
```

R3/R4 require review before replacing a canonical T1 generation for research.

---

## 10. Coverage cell

A coverage matrix cell should include:

```text
provider
venue
sensor
instrument/economic contract
period
requested_granularity
coverage_state
expected_intervals
observed_intervals
valid_intervals
coverage_ratio
first_valid_at
last_valid_at
gap_count
largest_gap
revision_count
quality_mode
independent_source_group
```

Do not hide `expected_intervals` assumptions.

---

## 11. Coverage ratios

Coverage ratio can be computed only where expected cadence is defensible.

For event streams such as trades/liquidations:
- interval occupancy may be misleading;
- distinguish no-event from no-feed;
- use provider sequence continuity, archive completeness, heartbeat/source metadata where available.

For fixed-cadence OI/funding/book analytics:
- interval coverage ratio is more meaningful.

Sensor-specific coverage methodology must be versioned.

---

## 12. Historical redundancy matrix

Per sensor/asset/period report:

```text
raw_sources
independent_sources
venues
first_party_sources
corroboration_sources
quality_mode
coverage_state
```

Example:

```text
BTC OI / 2022
Binance + Bybit + Gate
independent = 3
R3

BTC liquidation / 2022
Gate + Bitfinex community
independent first-party = 1
corroboration = 1
R1 strict
```

Do not inflate quorum from aggregators/community archives.

---

## 13. Coverage heatmaps

Generate machine + human forms for:

```text
sensor × year
sensor × venue × year
asset × sensor × year
rank/universe tier × sensor × year
provider × granularity × year
```

Colors/visuals are convenience only; underlying typed state remains authoritative.

---

## 14. Gap stop rules

Stop repeatedly attacking a gap when:

- provider explicitly confirms history does not exist;
- capability evidence proves endpoint starts later;
- repeated compliant attempts exceed max retry policy;
- source is no longer free-only;
- geo/access block cannot be legally/reproducibly bypassed;
- alternate first-party paths exhausted;
- scientific value is lower than remaining cost/resource budget.

Record:

```text
TERMINAL_GAP_REASON
```

and move on.

---

## 15. No proxy laundering

If 2021 liquidation history does not exist for provider X, do not silently replace it with:
- price drawdown;
- volume spike;
- another venue's liquidation total;
- later aggregate vendor estimate.

Those may be separate observables, not repaired evidence.

---

## 16. Historical truth report

At end of each sensor phase, produce:

```text
what we requested
what existed
what we actually acquired
what normalized safely
where independent redundancy exists
where evidence is single-source
where history is permanently unavailable
where gaps remain repairable
where revisions altered history
```

This report is mandatory before research uses the sensor family.

---

## 17. Planning verdict

`PASS_BLOC_07D_GAP_AND_REVISION_POLICY`
