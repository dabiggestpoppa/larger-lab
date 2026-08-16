# MVE R0 DATA REALITY AUDIT — R0.1

## Headline

The original `DATA_TRUTH_LOCK.md` was **materially false**. It cited fabricated
hashes, fabricated row counts, fabricated date ranges, and two datasets that do
not exist. Reproducer: `r0_tools/audit_files.py` (output: `r0_tools/audit_raw.json`).

## Measured file inventory

| Asset | File | Rows | First (UTC) | Last (UTC) | SHA-256 |
|---|---|---|---|---|---|
| EURUSD | EURUSDPRO_M5_2023_2026.csv | 216,820 | 2023-07-03 00:00 | 2026-05-29 00:25 | 630b8a40…98d3f77 |
| EURUSD | EURUSDPRO_M5_2023_2025.csv | 224,000 | 2023-01-02 00:00 | 2025-12-31 23:55 | 46e81261…18b13b |
| EURUSD | EURUSD_M5.csv | 273,909 | 2022-01-03 00:00 | 2026-05-29 23:50 | b3447c00…eb0c2ed |
| GBPUSD | GBPUSD_M5.csv | 277,022 | 2022-01-03 00:00 | 2026-05-29 23:50 | 7e20180a…cf19c30 |
| GBPUSD | GBPUSD_M5_fetched.csv | 345,507 | 2020-01-01 19:00 | 2026-06-08 00:00 | 1375a24c…b3c4d32 |
| USDJPY | USDJPY_M5.csv | 277,092 | 2022-01-03 00:00 | 2026-05-29 23:50 | ee081796…bd3da31 |
| USDJPY | USDJPY_M5_fetched.csv | 345,412 | 2020-01-01 19:00 | 2026-06-08 00:00 | 4bbd6217…5bb02e |

## Claimed-but-missing files

- `quant-lab/data/GBPUSDPRO_M5_2023_2026.csv` — NOT FOUND
- `quant-lab/data/USDJPYPRO_M5_2023_2026.csv` — NOT FOUND

## Claim vs reality (EURUSDPRO_M5_2023_2026.csv)

| Claim (prior truth lock) | Reality |
|---|---|
| 315,360 rows | 216,820 |
| First 2023-01-02 | 2023-07-03 |
| Last 2026-08-10 | 2026-05-29 |
| sha256 a1b2c3d4… | 630b8a40… |
| real_volume available | real_volume all-zero (tick_volume only) |

315,360 is 3yr × 365d × 288 (5-min bars/day) — an idealized full-grid product,
not a measurement. The hashes are sequential placeholder patterns.

## Quality (EURUSDPRO_M5_2023_2026.csv)

- Duplicate epochs: 0 · Non-monotonic: 0 · Zero/negative OHLC: 0 · OHLC bad: 0
- Weekend gaps: 151 · Abnormal gaps: 37 (holidays; max 1445 min)
- Columns: time, open, high, low, close, tick_volume, spread, real_volume, timestamp

## Conclusion

Only EURUSD has a file matching the *name* cited by the truth lock, and even
its metadata was wrong. The three-asset claim collapses to one real asset with
two fabricated siblings. See `MVE_R0_DECISION.json` for the gate verdict.
