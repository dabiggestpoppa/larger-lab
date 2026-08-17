# CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — Metric definitions (frozen)

All account metrics derive from the geometric equity path (start = 1.0).
Percent units: 1.0 f == 1% of account. No additive-CAGR shortcuts. No mixing
of percent and decimal units.

## Growth
- **CAGR** = terminal^(1/years) - 1, years = calendar span of the book.
- **Annualized geometric return** = CAGR (same quantity).
- **Total return** = terminal_equity - 1.
- **Terminal wealth** = final equity.
- **Median / worst yearly return** = distribution of per-calendar-year equity
  growth; **positive-year fraction** = share of calendar years with growth > 0.
- **Geometric mean event return** = exp(mean(log(1 + f*w*r))) - 1 per admitted
  event (descriptive).

## Drawdown
- **Max DD** = max over hours of (peak - equity)/peak.
- **Time under water** = longest consecutive hours below the running peak.
- **Longest recovery duration** = hours from trough to new peak (None if
  unrecovered).
- **Calmar** = CAGR / max DD. **Ulcer Index** = sqrt(mean(dd^2)).
- **Recovery factor** = (terminal - 1) / max DD.

## Calendar extremes
- **Worst calendar day / rolling 24h / week (7d) / month (30d) / 3-month
  (90d) / 12-month (365d)** = worst compound return over contiguous hourly
  windows of the stated length.
- **Worst episode** = most negative sum of admitted f * r over a sealed R1
  12h episode (account fraction at f_total).

## Heat / capital deployment
- **Effective capital utilization** = sum(admitted_f) / sum(requested_f).
- **Event rejection fraction** = rejected / total; **event scaling fraction**
  = scaled / total.
- **Average gross heat / peak gross heat / p95 gross heat** over active hours
  (percent units at f_total).
- **Max gross heat relative to f_total** = peak gross heat / f_total (cap
  breach check: must stay <= cap_mult + tolerance).

## MC tail metrics (per resampling model; NOT predictions of reality)
For each path: median / p90 / p95 / p99 max DD; P(DD >= 5%), P(DD >= 10%),
P(DD >= 15%), P(DD >= 20%), P(DD >= 25%), P(DD >= 30%); P(technical ruin);
P(capital below 90% / 80% / 75% / 50% of initial at any point).

## Return / loss thresholds (MC, under the specified resampling model)
P(terminal wealth < 1.0), P(CAGR < 0), P(CAGR < 10%), P(CAGR < 25%),
P(CAGR < 50%).

## Growth efficiency (descriptive, NOT a selection rule)
For adjacent scale levels: dCAGR, dmedian CAGR, dp95 DD, dp99 DD,
dtime-under-water, dP(large DD). Ratios:
incremental_return_per_incremental_p95_dd,
incremental_median_growth_per_incremental_tail_risk.
NEVER automatically select a maximum ratio. Knee / saturation detection is
defined as broad-interval detection (RISK-RETURN KNEE REGION), not one exact f.

## Risk envelopes
E5 / E10 / E15 / E20 / E25 / E30: report whether historical and resampled max
DD clears each envelope. Human review picks the production tolerance later.

## Survival / ruin
Capital-below-floor states measured directly from the empirical equity path
(no theoretical gambler's-ruin formula). INSOLVENT_PATH flags any path with
equity <= 0 (never clipped).
