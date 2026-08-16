# MVE R0.5.5/6 RESAMPLING VERIFICATION — MVE_R05_RESAMPLING_REPORT.md

## Result: MATCH

The committed `resample_m5_to_h1` was compared bar-by-bar against the R0
independent audit implementation (`r0_tools/audit_resample.py`).

| Metric | Value | Match |
|---|---|---|
| Raw `resample('1h')` bar count | 25465 | MATCH (R0 audited 25,465) |
| Committed H1 bar count (policy-applied) | 18089 | MATCH (25,465 - 7,376 empty weekend hours) |
| Dropped empty weekend hours | 7376 | MATCH (R0 audited 7,376 all-NaN OHLC slots) |
| open equality on shared bars | exact | MATCH |
| high equality on shared bars | exact | MATCH |
| low equality on shared bars | exact | MATCH |
| close equality on shared bars | exact | MATCH |
| volume equality on shared bars | exact | MATCH |

## Frozen conventions

- Source timezone: UTC; target timezone: UTC.
- H1 label convention: `label='left'`, `closed='left'` (bar 00:00 covers [00:00, 01:00)).
- Open=first, High=max, Low=min, Close=last, Volume=sum of selected volume field (tick_volume).
- Incomplete-hour policy: retain an hour if >=1 source M5 bar exists; record
  `source_bar_count`; empty weekend hours are dropped (no forward-fill, no
  synthetic bars, no interpolation).
