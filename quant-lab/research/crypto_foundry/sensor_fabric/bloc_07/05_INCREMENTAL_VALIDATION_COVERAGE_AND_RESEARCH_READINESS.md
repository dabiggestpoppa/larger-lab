# BLOC 7 — INCREMENTAL VALIDATION, COVERAGE, AND RESEARCH READINESS

**Purpose:** ensure every historical shard becomes validated evidence before the backfill program declares usable history.

---

## 1. Validation pipeline per shard

Every completed acquisition shard must flow through:

```text
ACQUIRE
  ↓
T0A HASH / MANIFEST VALIDATION
  ↓
T0B LOSSLESS PROJECTION CHECK
  ↓
T1 PIT NORMALIZATION
  ↓
BLOC 6 QUALITY / INDEPENDENCE / COVERAGE
  ↓
BACKFILL COVERAGE UPDATE
  ↓
RESEARCH-READINESS UPDATE
```

A shard is not scientifically ready merely because data exists on disk.

---

## 2. Incremental processing rule

Do not wait for the entire 2020–2026 program before validating.

After each durable shard:
- project to T0B;
- normalize eligible rows to a new/in-progress T1 generation;
- run quality checks;
- update coverage matrix;
- emit any gap/revision tickets;
- record storage/runtime metrics.

This makes errors visible early and prevents six years of bad semantics from accumulating.

---

## 3. Sensor-phase checkpoints

After each major sensor family, issue a checkpoint.

### Checkpoint L — Liquidations

Must report:
- providers actually acquired;
- historical start by provider;
- position-side semantics;
- granularity;
- independent-source redundancy by era;
- trade-level versus interval aggregate distinction;
- terminal gaps.

### Checkpoint O — Open Interest

Must report:
- native OI unit by contract;
- normalized exposure availability;
- cadence;
- symbol launch clipping;
- cross-provider redundancy;
- suspicious level discontinuities.

### Checkpoint F — Funding

Must report:
- realized versus predicted;
- native interval;
- normalized interval methodology;
- publication/availability timing;
- historical redundancy.

### Checkpoint T — Trades / Aggressor Flow Inputs

Must report:
- archive completeness;
- event IDs / sequence continuity;
- aggressor-side semantics;
- duplicates between sources;
- history/venue breadth.

### Checkpoint B — Books / Liquidity

Must report:
- snapshot/delta type;
- reconstruction status;
- sequence integrity;
- retained depth level;
- storage footprint;
- U0/U1 coverage;
- gaps.

---

## 4. Backfill Readiness State

Per canonical sensor and requested research scope:

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

A sensor may be `RESEARCH_MULTI_ERA` for BTC and only `RESEARCH_LOCAL_ONLY` for rank-1000 alts.

Readiness must be scope-aware.

---

## 5. Research scope contract

A readiness query includes:

```text
sensor_family
asset / universe
start_at
end_at
granularity
required_redundancy
required_evidence_class
required_quality_mode
PIT_mode
```

Response includes:

```text
ready: bool
readiness_state
coverage
independent_source_count
providers
venues
known_gaps
quality_flags
allowed_operations
lineage_ref
```

No global `data_ready=true` flag.

---

## 6. Initial research restart requirements

Before MECH-21 / LF14 may consume mechanical history, require at minimum:

### For sign-asymmetry liquidation tests

- at least one strong first-party historical liquidation source for target period;
- preferably R2 independent evidence for materially supported periods;
- clear side semantics;
- PIT-safe timestamps;
- no unclassified source gaps around analyzed events.

### For OI/funding mechanics

- R2 independent providers where available;
- consistent contract identity and normalized units;
- enough history to overlap event sample;
- no future publication leakage.

### For order-flow mechanics

- hard aggressor-side semantics;
- event/archive completeness evidence;
- sequence/duplicate QA.

### For depth/liquidity-withdrawal tests

- valid book reconstruction or verified snapshot semantics;
- no silent sequence gaps;
- known depth/cadence;
- sufficient U0 event overlap.

---

## 7. Event-overlap coverage

A global year-level coverage score is not enough.

For research event sets, compute:

```text
event_id
sensor
provider
window_start
window_end
coverage_state
pre_event_coverage
post_event_coverage
quality_mode
```

LF14 specifically requires mechanical coverage around:

```text
PRE-SHOCK
ABSORPTION
REORGANIZATION
PROPAGATION
CONTAINMENT
```

An event lacking critical mechanical windows must be marked unavailable rather than imputed.

---

## 8. Coverage by static + rolling horizons

To align with research doctrine, historical-readiness reporting should support static windows:

```text
1D / 3D / 7D / 14D / 30D / 60D
```

and rolling windows:

```text
3D / 7D / 14D / 30D
```

This is a coverage/query capability requirement, not yet a feature calculation.

---

## 9. Cross-provider overlap validation

Where two providers observe comparable economics:
- align on PIT time;
- compare expected scale/order;
- detect gross unit errors;
- detect timestamp shifts;
- detect sign reversals;
- preserve true venue heterogeneity.

Cross-provider disagreement is diagnostic, not automatic failure.

---

## 10. Sentinel periods

Every sensor family must include detailed validation across sentinel periods:

```text
2021 high-activity period
2022 stress period
2024 regime sample
2026 recent sample
```

Plus at least one quiet/ordinary period.

Purpose:
- avoid validating only recent schemas;
- expose historical format drift;
- expose scaling/timestamp changes;
- verify 2022 mechanics for current research questions.

---

## 11. Research-coverage evidence package

At each sensor-phase completion create:

```text
coverage_matrix.parquet
redundancy_matrix.parquet
provider_start_end.csv
gap_registry.csv
revision_registry.csv
quality_summary.parquet
event_overlap_report.parquet
sentinel_validation.md
research_readiness.md
```

Git may store compact reports/manifests/checksums, not the underlying large market data.

---

## 12. Promotion rules

A sensor history may be promoted to research use when:
- T0 integrity passes;
- T1 lineage passes;
- PIT rules pass;
- identity/units pass;
- coverage state is explicit;
- unresolved gaps are known;
- evidence independence is known;
- quality mode is compatible with requested analysis;
- research-readiness report is generated.

---

## 13. Demotion rules

A previously ready sensor can be demoted if:
- provider revision changes history materially;
- parser/semantic bug found;
- contract metadata error found;
- source dependency invalidates redundancy claim;
- access terms invalidate reproducibility;
- major gaps discovered.

Demotion must be generation/version specific and leave prior evidence intact.

---

## 14. Planning verdict

`PASS_BLOC_07E_INCREMENTAL_VALIDATION`
