# BLOC 11 — REPLAY CLOCK, AS-OF, UNIVERSE & GENERATION LOCKS

## 1. Objective

Freeze the temporal semantics that make historical replay scientifically valid.

The replay engine must know not only **what happened at time t**, but also **what data/state definitions were valid and knowable at time t** under the selected revision mode.

---

## 2. Time coordinates

Replay preserves separate fields for:

```text
frame_at
as_of
source_event_at
interval_start_at
interval_end_at
effective_at
published_at
market_available_at
observed_at
ingested_at
normalized_at
replay_computed_at
```

No one field may silently substitute for another.

`frame_at` is the requested reconstruction coordinate.

`as_of` defines the knowledge cutoff for the query.

---

## 3. Replay clock modes

### FIXED_INTERVAL

For evenly spaced reconstruction.

Examples:

```text
5m
15m
1h
4h
1D
```

The step is a query schedule, not a market causality assumption.

### EVENT_DRIVEN

Frames are created at events such as:
- liquidation bursts;
- quality regime changes;
- state transitions;
- research-defined shock timestamps;
- listing/delisting boundaries.

### HYBRID_EVENT_ANCHORED

Creates event-relative windows around an anchor.

Example:

```text
T-30D
T-14D
T-7D
T-3D
T0
T+3D
T+7D
T+14D
T+30D
```

or finer intraday grids around shock events.

### SINGLE_SNAPSHOT

One deterministic `as_of` reconstruction.

---

## 4. Clock boundary rules

All clock boundaries are half-open unless sensor semantics require otherwise:

```text
[start, end)
```

UTC is canonical storage/replay timezone.

User-facing local-time conversion is presentation only.

DST cannot alter historical UTC boundaries.

---

## 5. AS_KNOWN_THEN

This is the default research replay mode.

A record/state is eligible only if its information was publicly/market available by the frame `as_of`, subject to the established Bloc 5 availability semantics.

Disallowed leakage examples:
- later archive corrections inserted into an earlier frame;
- current symbol metadata backfilled into unknown historical periods;
- future stablecoin conversion rates;
- T2 baselines estimated using future observations when the baseline contract is expanding/PIT;
- later provider-quality knowledge used as if known historically when a study explicitly requires contemporaneous operational state.

---

## 6. LATEST_RECONSTRUCTED

Allowed only when explicitly requested.

This mode answers:

> Using our best approved reconstruction today, what do we believe the historical mechanical state was?

It may include later-approved source revisions, but must preserve:
- original revision lineage;
- revision publication/ingestion times;
- reconstruction generation.

Claims from this mode cannot be described as information available contemporaneously.

---

## 7. Generation lock set

Every replay run must pin a `GenerationLockSet`.

Minimum:

```text
t0_manifest_revision
t1_generation
t2_generation
identity_registry_version
normalization_registry_version
quality_policy_version
source_dependency_graph_version
observable_registry_version
baseline_registry_version
market_os_schema_version
code_revision
```

No floating `latest` is allowed inside an in-progress run.

If the run starts with generation G, it finishes with G or aborts.

---

## 8. PIT universe lock

Each frame resolves a `UniverseSnapshot` using:

```text
asset identity
contract identity
listing_at
delisting_at
venue availability
instrument lifecycle
universe tier at t
```

Universe policies supported in v1:

```text
PIT_ALL_ELIGIBLE
PIT_U0
PIT_U1
PIT_U2
EXPLICIT_CONTRACT_SET
RESEARCH_EVENT_SET
```

A replay plan may specify a universe policy, but each frame still records the actual realized membership.

---

## 9. Baseline lock semantics

T2 standardized states depend on baseline registries.

Each derived standardized value must disclose whether its baseline is:

```text
FIXED_TRAINING_WINDOW
EXPANDING_PIT
ROLLING_PIT
STATIC_POST_HOC
```

`STATIC_POST_HOC` baselines are forbidden in `AS_KNOWN_THEN` when they use future data.

Physical amplitude remains available even when standardized amplitude is blocked.

---

## 10. Missing-history policy

Replay may encounter:

```text
NOT_EXPECTED
HISTORY_UNAVAILABLE
KNOWN_GAP
DATA_BLOCKED
QUALITY_BLOCKED
```

Policy options:

```text
FAIL_FRAME
EMIT_PARTIAL_FRAME
SKIP_FRAME_WITH_REASON
```

Default research mode should `EMIT_PARTIAL_FRAME` when scientifically honest, preserving explicit blocked coordinates.

Critical requested sensors may be configured to `FAIL_FRAME`.

---

## 11. Replay checkpointing

Long runs checkpoint only after:
- frame output is durable;
- lineage receipt is durable;
- manifest state is durable.

Checkpoint contains:

```text
last_completed_frame
plan_hash
generation_lock_hash
output_checksum_state
```

Restarting with a different generation lock must fail rather than resume into a mixed run.

---

## 12. Temporal equivalence tests

Required golden tests:

1. same frame under same generation returns same result;
2. `AS_KNOWN_THEN` excludes later revision;
3. `LATEST_RECONSTRUCTED` can include later approved revision with lineage;
4. pre-listing contract is `NOT_EXPECTED`;
5. post-delist data is rejected;
6. rolling/static windows close exactly at declared boundaries;
7. UTC/DST conversion cannot change canonical frame;
8. baseline using future data is rejected in PIT mode;
9. resume cannot cross generation change;
10. physical value remains available when standardized baseline is unavailable.

---

## 13. Blocking conditions

Any of the following block replay promotion:

```text
future leakage
ambiguous as_of semantics
unlocked generation
current-universe backprojection
silent revision substitution
future-informed baseline in PIT mode
mixed-generation resume
```

These are scientific-integrity failures, not warnings.