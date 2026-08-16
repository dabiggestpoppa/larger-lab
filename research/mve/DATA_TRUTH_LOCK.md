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
> `_load_research_data()` to the real loader. Remaining blocker: result
> persistence (print-only) — due for `MVE-R0.5-RUNNER-PERSISTENCE`.

- R0 finding (preserved): the runner crashed on import, two modules did not
  compile, loaded no real data, and wrote no results (see `MVE_RUNNER_AUDIT.md`).

---

**Data truth established (partial):** the real files are measured above.
**Data truth NOT established:** any MVE research result, because the runner
has never executed against real data.
