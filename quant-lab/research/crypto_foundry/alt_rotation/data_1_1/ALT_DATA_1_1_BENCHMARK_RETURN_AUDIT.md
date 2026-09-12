# ALT-DATA-1.1 Benchmark Return Audit
Generated: 2026-08-25 11:23 UTC

## Root Cause

The V1 benchmark relative-return calculation used row-offset pct_change(w)
instead of calendar-day price lookups. When dates are excluded (79 gaps),
a row-offset of w does not correspond to w calendar days.

## Error Magnitude

| Window | BTC Self-Relative Max Abs | ETH Self-Relative Max Abs |
|--------|--------------------------|--------------------------|
| 1D | 0 | 0 |
| 3D | 0.2388 | 0.214 |
| 7D | 0.2461 | 0.2255 |
| 14D | 0.263 | 0.246 |
| 30D | 0.3515 | 0.31 |
| 60D | 0.6129 | 0.52 |
| 90D | 0.9497 | 0.8134 |

## Post-Repair Identity

BTC self-relative: max_abs = 0.00e+00 for ALL windows [PASS]
ETH self-relative: max_abs = 0.00e+00 for ALL windows [PASS]

## Changed Rows

1,049,060 out of 1,098,000 total rows (95.5%)
