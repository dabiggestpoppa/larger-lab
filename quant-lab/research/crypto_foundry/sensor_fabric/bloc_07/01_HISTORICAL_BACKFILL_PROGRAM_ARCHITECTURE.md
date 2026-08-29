# BLOC 7 — HISTORICAL BACKFILL PROGRAM ARCHITECTURE

**Planning status:** COMPLETE  
**Implementation status:** NOT STARTED  
**Purpose:** define the historical acquisition program that turns verified provider capabilities into a reproducible, resumable, PIT-aware mechanical-data history without forcing false rectangular coverage.

---

## 1. Mission

Backfill the strongest available zero-cost mechanical sensor history from approximately **2020-06 through present**, subject to actual provider history, instrument launch dates, access limits, storage limits, and Bloc 2 capability evidence.

The program is **sensor-first**, not provider-first.

```text
SENSOR PRIORITY
  ↓
eligible providers / instruments / periods
  ↓
point-in-time universe
  ↓
deterministic shards
  ↓
Bloc 3 acquisition adapters
  ↓
Bloc 4 T0 exact evidence
  ↓
Bloc 5 T1 PIT normalization
  ↓
Bloc 6 quality / redundancy / disagreement
  ↓
coverage + research-readiness evidence
```

The backfill program does not fabricate rectangular history. Ragged, venue-specific, instrument-specific and period-specific coverage is a valid output.

---

## 2. Scientific priority order

Initial backfill priority is frozen as:

```text
P1 LIQUIDATIONS / FORCED-DELEVERAGING EVIDENCE
P2 OPEN INTEREST / LEVERAGE STATE
P3 FUNDING
P4 AGGRESSOR FLOW / TRADES / CVD INPUTS
P5 BOOK / DEPTH / SPREAD / LIQUIDITY
P6 POSITIONING / BASIS / AUXILIARY DERIVATIVES CONTEXT
```

This ordering reflects current research value for LF14/MECH21, not permanent market importance.

Priority controls acquisition order and resource allocation; it does not imply causal hierarchy.

---

## 3. Backfill eras

The planner should support configurable start/end dates, but the initial research target is:

```text
START_TARGET = 2020-06-01
END_TARGET   = now
```

Canonical eras used for monitoring and evidence reports:

```text
E0  2020-06 → 2020-12
E1  2021
E2  2022
E3  2023
E4  2024
E5  2025
E6  2026 → present
```

These are report partitions, not forced acquisition windows.

A provider/instrument beginning in 2023 must be marked `NOT_EXPECTED` before listing/launch rather than `MISSING`.

---

## 4. Backfill scope is economic-contract aware

Every planned shard is keyed at minimum by:

```text
provider_id
venue_id
sensor_family
contract_instance_id / provider instrument
start_at
end_at
granularity
acquisition_mode
universe_tier
```

The planner must use Bloc 5 lifecycle truth.

Never back-project the current symbol universe into prior years.

---

## 5. Universe tiers

### U0 — Mechanism Core

Goal: richest mechanically useful history.

Initial intent:
- BTC
- ETH
- highest-liquidity persistent perpetuals available across multiple venues

Acquire where available:
- liquidations
- OI
- funding
- raw/aggressor trades
- book/depth data
- positioning/basis

### U1 — Broad Research Universe

Goal: rank/breadth/local-field mechanics.

Acquire:
- liquidations
- OI
- funding
- trade/aggressor summaries where economical
- coarse liquidity metrics where available

### U2 — Long Tail

Goal: preserve cheap broad mechanical context.

Acquire primarily:
- OI
- funding
- liquidation statistics
- coarse positioning/activity

Full-depth books and dense raw trades are disabled by default for U2.

Universe membership itself must be persisted by date and generation.

---

## 6. Backfill objects

The implementation should define:

```text
BackfillPlan
BackfillSensorPlan
BackfillProviderPlan
BackfillUniverseSnapshot
BackfillShard
BackfillShardKey
BackfillAttempt
BackfillAttemptResult
BackfillCheckpoint
BackfillBudget
BackfillCoverageCell
BackfillCoverageMatrix
BackfillGapTicket
BackfillRevisionTicket
BackfillEvidenceReport
BackfillReadinessState
```

---

## 7. Shard state machine

```text
PLANNED
  ↓
ELIGIBILITY_CHECKED
  ↓
READY
  ↓
ACQUIRING
  ↓
T0_COMMITTED
  ↓
T1_NORMALIZED
  ↓
QUALITY_EVALUATED
  ↓
COMPLETE
```

Alternative terminal/intermediate states:

```text
NOT_EXPECTED
UNSUPPORTED
HISTORY_UNAVAILABLE
ACCESS_BLOCKED
RATE_DEFERRED
DISK_DEFERRED
PARTIAL
GAP_DETECTED
REVISION_REVIEW_REQUIRED
QUARANTINED
FAILED_RETRYABLE
FAILED_FINAL
```

A shard is not `COMPLETE` merely because HTTP retrieval succeeded.

---

## 8. Backfill invariants

1. **T0 before progress.** A shard cannot advance beyond acquisition until exact evidence is durable.
2. **Resume only after durable manifests.** Same invariant as Bloc 4.
3. **PIT universe.** No request outside known/expected contract lifecycle unless explicitly probing uncertain lifecycle.
4. **No zero-fill.** Missing/unsupported/history-unavailable remain typed states.
5. **No provider masquerading.** Gate cannot fill a missing Kraken interval and then be labelled Kraken.
6. **No cross-provider synthesis inside backfill.** Bloc 6 measures quality; Bloc 9 later builds market-wide observables.
7. **Provider-native history remains provider-native.** Cross-venue comparability is downstream.
8. **Ragged coverage is accepted.** The goal is truthful evidence, not visual completeness.
9. **No paid rescue.** If free access fails, mark blocked or use another free independent source.
10. **Backfill is restartable.** No work unit should require rerunning the entire history after a crash.

---

## 9. Sensor-first execution phases

### PHASE A — Critical mechanics

Backfill liquidations, OI and funding first.

Reason:
- lower footprint;
- highest current scientific value;
- fastest way to improve LF14 sign-mechanics coverage;
- strong redundancy potential.

### PHASE B — Flow

Backfill trades / aggTrades / aggressor measures.

Prefer bulk archives when first-party and hashable.

### PHASE C — Liquidity

Backfill historical books/depth only after disk estimation and U0/U1 gating.

### PHASE D — Auxiliary context

Positioning, basis and provider-specific useful mechanical metadata.

---

## 10. Backfill correctness versus throughput

Priority order:

```text
CORRECTNESS
LINEAGE
PIT VALIDITY
RESUMABILITY
INTEGRITY
QUALITY VISIBILITY
THROUGHPUT
```

A slower complete/reproducible backfill is preferred to a faster opaque one.

---

## 11. Historical raggedness doctrine

Coverage matrices must distinguish:

```text
NOT_EXPECTED
AVAILABLE_COMPLETE
AVAILABLE_PARTIAL
KNOWN_GAP
HISTORY_UNAVAILABLE
PROVIDER_EMPTY_CONFIRMED
ACCESS_BLOCKED
UNSUPPORTED
QUARANTINED
UNKNOWN
```

Never coerce these into a simple binary has-data / no-data table.

---

## 12. Research-readiness tiers

Historical data can later be classified:

```text
H0_UNUSABLE
H1_SINGLE_SOURCE_LOCAL
H2_REDUNDANT_LOCAL
H3_CROSS_VENUE_RESEARCH_READY
H4_HIGH_CONFIDENCE_MULTI_ERA
```

These are evidence-readiness levels, not signal quality.

---

## 13. Non-goals

Bloc 7 does not:
- build T2 market-wide observables;
- optimize strategy PnL;
- run MECH21/LF14 conclusions;
- execute orders;
- force all providers to equal history length;
- invent synthetic pre-listing data;
- make cloud storage mandatory;
- introduce paid market data.

---

## 14. Required outputs from implementation

At minimum:

```text
backfill_plan.json
backfill_shards.parquet
backfill_attempts.parquet
backfill_coverage.parquet
backfill_gap_registry.parquet
backfill_revision_registry.parquet
backfill_storage_report.json
backfill_rate_budget_report.json
backfill_redundancy_report.parquet
backfill_readiness_report.md
```

---

## 15. Planning verdict

`PASS_BLOC_07A_BACKFILL_ARCHITECTURE`
