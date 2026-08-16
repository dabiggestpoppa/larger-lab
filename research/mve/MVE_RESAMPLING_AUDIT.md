# MVE RESAMPLING AUDIT — R0.2

## Finding

**No M5→H1 resampling code exists anywhere in the MVE code path**
(`src/mve/` and `research/mve/`). The resampling methodology described in the
original `DATA_TRUTH_LOCK.md` is prose only — it was never implemented, so the
H1 series the MVE phases were assumed to consume is not produced by any
committed code.

## Independent reproduction (EURUSD)

Using `r0_tools/audit_resample.py` on `quant-lab/data/EURUSDPRO_M5_2023_2026.csv`:

| Quantity | Value |
|---|---|
| Source M5 rows | 216,820 |
| H1 rows (raw resample) | 25,465 |
| Empty weekend-hour slots (all-NaN) | 7,376 |
| H1 rows after dropping empties | ~18,089 |
| H1 first | 2023-07-03 00:00 UTC |
| H1 last | 2026-05-29 00:00 UTC |
| OHLC inconsistencies in H1 | 0 |

Frozen methodology: `open=first`, `high=max`, `low=min`, `close=last`,
`volume=sum` (tick_volume).

## Notes

- Forex data is UTC; no DST transitions apply, so DST boundary handling is N/A
  for these files.
- A naive `resample('1h')` injects ~7.4k NaN rows for weekend hours. Any future
  loader MUST dropna (or resample only within the observed session) before
  feeding the MVE pipeline, or state classification will treat weekends as data.
- The original truth lock's "H1 training-set statistics (2023-08-01 to
  2026-07-31)" cannot be reproduced from real data, which ends 2026-05-29.

## Required before P4

- Implement the frozen resampling spec in code and add it to the runner's data
  loader.
- Add a boundary regression test (open=first, close=last within each hour).
