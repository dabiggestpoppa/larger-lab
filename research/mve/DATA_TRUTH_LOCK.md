# DATA TRUTH LOCK — CEREBUS MVE PHASE 4-7

> **STATUS: REPAIRED 2026-08-15 (R0).** The previous revision of this file
> contained fabricated hashes, fabricated row counts, fabricated date ranges,
> and referenced two datasets that do not exist. This revision records only
> values measured directly from disk. Anything not verifiable is marked UNSET.

## Verdict

**The MVE research foundation is NOT ready for Phase 4-7 execution.**
See `MVE_R0_DECISION.json`. Two of the three datasets named in the original
truth lock do not exist, and the research runner is non-functional (see
`MVE_RUNNER_AUDIT.md`).

---

## Actual data inventory (measured, M5)

| Asset | File | Rows | First | Last | SHA-256 |
|---|---|---|---|---|---|
| EURUSD (was "primary") | `quant-lab/data/EURUSDPRO_M5_2023_2026.csv` | 216,820 | 2023-07-03 00:00 | 2026-05-29 00:25 | `630b8a40...998d3f77` |
| EURUSD (alt) | `quant-lab/data/EURUSDPRO_M5_2023_2025.csv` | 224,000 | 2023-01-02 00:00 | 2025-12-31 23:55 | `46e81261...18b13b` |
| EURUSD (alt) | `quant-lab/data/EURUSD_M5.csv` | 273,909 | 2022-01-03 00:00 | 2026-05-29 23:50 | `b3447c00...eb0c2ed` |
| GBPUSD | `quant-lab/data/GBPUSD_M5.csv` | 277,022 | 2022-01-03 00:00 | 2026-05-29 23:50 | `7e20180a...cf19c30` |
| GBPUSD | `quant-lab/data/GBPUSD_M5_fetched.csv` | 345,507 | 2020-01-01 19:00 | 2026-06-08 00:00 | `1375a24c...ab3c4d32` |
| USDJPY | `quant-lab/data/USDJPY_M5.csv` | 277,092 | 2022-01-03 00:00 | 2026-05-29 23:50 | `ee081796...1b48e0` |
| USDJPY | `quant-lab/data/USDJPY_M5_fetched.csv` | 345,412 | 2020-01-01 19:00 | 2026-06-08 00:00 | `4bbd6217...f30ec7` |

Full hashes in `MVE_DATA_HASHES.json`.

## Files that DO NOT exist

- `quant-lab/data/GBPUSDPRO_M5_2023_2026.csv` — NOT FOUND
- `quant-lab/data/USDJPYPRO_M5_2023_2026.csv` — NOT FOUND

The original truth lock cited these as secondary/tertiary validation assets with
specific row counts and hashes. Those citations were fabricated.

## Fabrications in the prior revision (corrected)

| Prior claim | Measured reality |
|---|---|
| EURUSD rows = 315,360 | 216,820 (315,360 = 3yr × 365 × 288 is a theoretical full-grid, not a measurement) |
| EURUSD first = 2023-01-02 | 2023-07-03 |
| EURUSD last = 2026-08-10 | 2026-05-29 |
| Hashes a1b2c3d4... / b2c3d4e5... / c3d4e5f6... | Placeholder strings, not SHA-256 digests |
| GBPUSD / USDJPY "PRO_M5_2023_2026" datasets | Files do not exist |
| Holdout = Jan-Aug 2026 | No data after 2026-05-29 (2026-06-08 for *_fetched) |

## Data quality (measured, EURUSDPRO_M5_2023_2026.csv)

- Duplicate timestamps: 0
- Non-monotonic timestamps: 0
- Zero/negative OHLC: 0
- OHLC inconsistencies: 0
- `real_volume` column: all zero (tick_volume present; use tick_volume for volume)
- Weekend gaps: 151
- Abnormal (non-weekend) gaps: 37 (holiday closures; largest 1445 min)

## Resampling (M5 → H1)

> **UPDATED (R0.5 Commit 2):** a committed resampler now exists at
> `src/mve/data_loader.py::resample_m5_to_h1`. It matches the R0 independent
> audit bar-for-bar (raw 25,465 H1 bars; 18,089 after dropping 7,376 empty
> weekend-hour slots per the incomplete-hour policy). See
> `MVE_R05_RESAMPLING_REPORT.md`. The earlier finding (no resampling code) was
> true at R0 time; it is superseded, not erased.

- R0 finding (preserved): no resampling code existed in the MVE path at R0.
- Methodology frozen: open=first, high=max, low=min, close=last, volume=sum of
  the selected volume field (`tick_volume`).

## Holdout status

**FINAL_HOLDOUT_PENDING.** The same CSV is consumed by the quant-lab DMR and
rekey backtest engines, so the 2026 segment cannot be certified untouched.
See `MVE_DATA_ACCESS_LEDGER.csv` and `MVE_DATA_SPLIT_LOCK.json`.

## Runner status

> **UPDATED (R0.5):** Commit 1 fixed import + two broken modules; Commit 2 wired
> `_load_research_data()` to the real loader; Commit 3 added phase-isolated
> orchestration, prerequisite gates, and real result persistence
> (`MVE-R0.5-RUNNER-PERSISTENCE`). Remaining: causality harness (next
> checkpoint) and the scientific phase internals, which remain
> `BLOCKED_SCIENTIFIC_IMPLEMENTATION`.

- R0 finding (preserved): the runner crashed on import, two modules did not
  compile, loaded no real data, and wrote no results (see `MVE_RUNNER_AUDIT.md`).

## Causality status

> **UPDATED (R0.5 Commit 4):** the causality harness is built and the full MVE
> source has been classified (`MVE_CAUSALITY_CONTRACT.md`, `MVE_R05_STATIC_LEAKAGE_AUDIT.md`).
> The research infrastructure (loader, resampler, volatility, coordinates, sigma,
> occupancy/acceptance, runner, persistence) is **future-mutation and truncation
> invariant** on real data. The causality gate formally did NOT pass because 4
> recorded violations live in blocked scientific stubs: RKEY-B repaints (future
> retest scan backdates the anchor; measured diff 1.033) and signal Models A/B/C
> gate the signal at bar i on bar i+1. Per the immutable rule these are recorded
> as blockers, not repaired. See `MVE_R05_CAUSALITY_RESULTS.json`,
> `MVE_R05_FUTURE_PERTURBATION_RESULTS.json`, `MVE_R05_TRUNCATION_INVARIANCE.csv`,
> `MVE_R05_FINAL_DECISION.json`, `MVE_R05_CAUSALITY_REPORT.md`.

- Infrastructure causality: **PASS** (all measured diffs 0.0).
- Scientific stubs: **FAIL** (4 violations + 2 robustness defects: RKEY-C
  `int(NaN)` crash, Model E undefined `n`).
- Delayed confirmation: pivots (event at i, known at i+window) - consumption
  must use `apply_anchor_delay(pivots, window)`.
- Holdout remains `FINAL_HOLDOUT_PENDING`; the causality slice (2023-07-03..
  2024-03-31) is entirely inside the development range.

> **UPDATED (R0.5.1, 2026-08-15):** the four causality violations were repaired
> under human authorization (`MVE-R0.5.1-SCIENTIFIC-STUB-CAUSAL-REPAIR`):
> RKEY-B now activates the anchor at the retest bar (delayed confirmation),
> Models A/C emit at their confirmation bar, Model B is realtime, RKEY-C and
> Model D are NaN-robust. Same-harness re-run: **all repaired components max
> historical mutation diff = 0.0; truncation invariance all_pass**; the only
> remaining perturbation violation is Model E's whole-sample Q component
> (BLOCKED_LOGIC_SPEC, excluded from execution). `r05_1_causal_repair_pass = true`.
> Record corrections: Model E has NO undefined-`n` bug (prior claim was a
> misreading); Model D additionally crashed on warm-up NaN (now guarded).
> See `MVE_R05_1_DECISION.json`, `MVE_R05_1_CAUSAL_REPAIR_REPORT.md`,
> `MVE_R05_1_STUB_CLASSIFICATION.json`, `MVE_R05_1_MODEL_D_AUDIT.md`,
> `MVE_SCIENTIFIC_EVENT_TIME_SCHEMA.json`. P4 remains blocked until the
> independent R0.5.2 regate.

---

**Data truth established (partial):** the real files are measured above.
**Data truth NOT established:** any MVE research result, because the runner
has never executed against real data.
