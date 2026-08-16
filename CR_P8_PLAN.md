# CAPITAL ROUTING — CR-P8-CEREBUS-ROUTING-OVERLAY-DISCOVERY-01

> **Base:** Phase 7.5 sealed baseline — commit `7bc1c024` (ACCEPTED)
> **Repo:** dabiggestpoppa/larger-lab | branch: `capital-routing`
> **Last updated:** 2026-08-15
> **Scope:** Discover whether canonical CEREBUS primitives (daily tier, P90 prints,
> tier impulses, Asian midpoint, 132% rekey) observed inside the post-routing-event
> window improve the sealed EUR→JPY baseline. **OVERLAY DISCOVERY ONLY.**
> STOP after primitive discovery and candidate classification. No parameter
> optimization, no CEREBUS strategy construction, no deploy, no MT5.

---

## 0. Frozen baseline (untouched throughout Phase 8)

| Family | Signal | Trade | Entry | Hold |
|--------|--------|-------|-------|------|
| A | EUR ACCUMULATION | LONG USDJPY | t0 + 2h | 6h |
| B | EUR LIQUIDATION | SHORT USDJPY | t0 + 1h | 6h |
| A+B | — | policy P0 (every qualifying event) | — | — |

Family C (JPY→CHF) is WATCHLIST ONLY and is **excluded** from Phase 8.

Baseline return per event = Phase 7 execution engine `dir_net_bps` for USDJPY at
the frozen (delay, hold) — spread/commission + swap applied (Phase 7 `ONE_WAY_COST_BPS`,
`swap_bps_per_day`). MFE/MAE from the same engine row. No Phase 7.5 numbers are
recomputed differently.

## 1. Canonical CEREBUS primitives (frozen definitions)

All primitives are computed from the **canonical USDJPY M5 parquet**
(`data/USDJPY_M5.parquet`, sha256 `719353ad...` — copied from the canonical
quant-lab CEREBUS data tree; covers 2022-01 → 2026-05, fully covering the
routing-event window 2023-07 → 2026-05).

### Session day / Asian range (canonical `extract_asian_ranges`)
- Session of a bar at EST time t = `t.date()` if `t.hour >= 19` else `t.date() - 1d`.
- Asian window: 19:00 → 03:00 EST (next day). USDJPY pip size = **0.01**.
- Asian range (AR) = max high − min low over the Asian window.
- Asian range completes at 03:00 EST (Pine `asian_range_complete`).

### Daily tier (canonical Pine `get_tier()` / cascade `tier_config`)
- T1: AR < 20 pips · T2: 20–30 · T3: 30–45 · NO-GO: ≥ 45 pips.
- **No new thresholds are invented.** Events before 03:00 EST of their session
  day have no complete AR → tier = NA (canonical: Pine returns "N/A" pre-completion).

### P90 print (canonical Pine P90 signal + cascade config)
- An M5 candle in the 2–11 AM EST entry window whose body (`|close − open|`)
  meets the hour-bucket threshold: (2–4am) 4.1, (4–6am) 4.6, (6–8am) 4.6,
  (8–10am) 5.9, (10–11am) 6.2 pips.
- Direction: close > open → BULL (aligned up), close < open → BEAR (aligned down).
- No Asian-band requirement (Engine A: "the P90 engine only cares about the body
  size of the candle, not the macro band").

### Tier impulse print (canonical dual-engine topology)
- A P90 print that ALSO breaches the Asian band: bull if `high >= asian_high`,
  bear if `low <= asian_low`. ("A Tier Impulse breaches the Asian Band with a
  ≥ P90 body.")

### Asian midpoint (canonical `mlr_test.py`)
- `midpoint = (asian_high + asian_low) / 2`. Event-level primitives: side at t0,
  first touch, first open/close cross, first close-through, aligned/opposed
  reclaim, rejection, cross count, occupancy.

### Rekey (canonical Pine `violation_long/short` + `label_generator_v2`)
- 132% violation: bull rekey when `high >= asian_high + 1.32 × AR`;
  bear rekey when `low <= asian_low − 1.32 × AR`. Each breach bar is a rekey event.

## 2. Observation window (both families)

`t0 → t0 + 120 min`, causal buckets 0–15 / 15–30 / 30–45 / 45–60 / 60–90 / 90–120m,
plus cumulative 15 / 30 / 60 / 90 / 120m. No feature at time t uses future
primitives (bucket streams are built in time order).

## 3. Outcome labels

Every primitive study evaluates: baseline PnL (dir_net_bps), win/loss,
expectancy, MFE, MAE, time-to-MFE, time-to-MAE, failure-before-entry,
failure-after-entry, coverage. Never win-rate alone.

## 4. Statistical discipline

- **Splits (chronological, frozen before discovery):**
  - DISCOVERY: 2023-07-01 → 2024-12-31 (Phase 7 `inner_sel`)
  - CONFIRMATION: 2025-01-01 → 2025-06-30 (Phase 7 `inner_val`)
  - RELATIONSHIP_CONFIRMED_OOS: 2025-07-01 → 2026-05-31 (Phase 6 holdout /
    Phase 7 untouched) — **evaluated ONCE after candidate freeze.**
- Minimum support: N ≥ 30 research-eligible, < 30 exploratory only.
- Bootstrap CIs (fixed seed, event-level resampling) for every reported estimate.
- BH-FDR within logical test families; raw p + adjusted q + effect size.
- Chronological subperiod stability for any A/B candidate.
- A and B analyzed separately; pooled A+B only after separate results.

## 5. Required outputs (artifacts/phase_08/)

P8_EVENT_FINGERPRINT.csv · P8_PRIMITIVE_STREAM_LONG.csv · P8_DAILY_TIER_RESULTS.csv ·
P8_TIER_PRINT_STUDY.csv · P8_P90_PRINT_STUDY.csv · P8_TIER_P90_COMBINATORICS.csv ·
P8_TIER_P90_RATIO_STUDY.csv · P8_SEQUENCE_GRAMMAR.csv · P8_MIDPOINT_STUDY.csv ·
P8_REKEY_STUDY.csv · P8_TIER_CONDITIONED_FINGERPRINTS.csv · P8_TIME_TO_PRIMITIVE.csv ·
P8_MISSING_PRIMITIVE_VETOES.csv · P8_SATURATION_STUDY.csv ·
P8_INCREMENTAL_INFORMATION.csv · P8_EQUAL_WEIGHT_SCORE.csv ·
P8_CANDIDATE_PATTERNS.json · CR_P8_DISCOVERY_REPORT.md · CR_P8_DECISION.json

## 6. Decision rules

- Every candidate pattern tagged: ACTIVATION / VETO / TIMING / EXIT / SIZING / REGIME.
- `phase_9_optimization_cleared = true` ONLY if ≥1 primitive/pattern materially
  improves expectancy or MAE, retains coverage, survives chronological
  confirmation AND OOS confirmation without refitting, and adds incremental
  information beyond the sealed routing signal.

## 7. Stop condition

STOP after primitive discovery + candidate classification. Report commit SHA,
await human review. No threshold optimization, no strategy assembly, no Phase 9.
