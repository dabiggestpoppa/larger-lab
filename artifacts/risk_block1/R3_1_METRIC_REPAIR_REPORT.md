# R3.1 — Time-to-Profit Metric Repair (CR-RISK-R3.1-TIME-TO-PROFIT-METRIC-REPAIR)

> **Base R3:** `ee4516a6` (scientific) · `27164766` (bookkeeping)
> **Scope:** repair `R3_TIME_TO_PROFIT` share denominators + the affected narratives.
> No paths, entries, exits, families, event universe, R definitions, MFE/MAE, final
> returns, alpha logic, or risk rules were altered.

## The defect

`share_of_winners` was computed as

```
N_reached_all / N_winners          # ALL trades reaching the level, divided by
                                   # the number of eventual winners
```

so whenever losers also touched the level (e.g. +0.25R pooled: 643 reached, of which
538 winners but 105 losers), the ratio exceeded 1.0 — an impossible share
(e.g. **1.1544** pooled at +0.25R pre-repair).

## The fix

Population-correct numerators and denominators, computed separately:

| field | definition |
|---|---|
| `N_reached_all` | trades reaching the level (any outcome) |
| `N_winners_reached` / `N_losers_reached` | eventual winners / losers reaching it |
| `share_of_all_trades_reaching` | `N_reached_all / N_trades` |
| `share_of_winners_reaching` | `N_winners_reached / N_winners` |
| `share_of_losers_reaching` | `N_losers_reached / N_losers` |

First-passage **timestamps are untouched** (they depend only on the net-R path);
winner-only / loser-only median times are now also reported.

## Corrected values (pooled A+B)

| level | N_reached_all | N_winners_reached | N_losers_reached | share_all | share_winners | share_losers |
|---|---|---|---|---|---|---|
| +0.10R | 694 | 552 | 142 | 0.780 | 0.991 | 0.426 |
| +0.25R | 643 | 538 | 105 | 0.722 | 0.966 | 0.315 |
| +0.50R | 556 | 502 | 54 | 0.625 | 0.901 | 0.162 |
| +0.75R | 424 | 417 | 7 | 0.476 | 0.749 | 0.021 |
| +1.00R | 306 | 306 | 0 | 0.344 | 0.549 | 0.000 |
| +1.50R | 143 | 143 | 0 | 0.161 | 0.257 | 0.000 |
| +2.00R | 71 | 71 | 0 | 0.080 | 0.127 | 0.000 |

Every share is in [0, 1]; `N_reached_all = N_winners_reached + N_losers_reached`;
pooled = A + B at every level (tested).

## Do the scientific conclusions change?

**No.** The corrected reading strengthens the same story:

- ~97% of winners reach +0.25R, ~90% reach +0.5R, all within median 2h — the edge
  is delivered broadly across winners, not concentrated.
- +1R remains a minority event (55% of winners / 34% of all trades, median 3h), and
  after reaching it **0% finish negative** (n=306).
- Losers touch +0.25R 31.5% of the time and +0.5R 16.2% — the "become profitable
  then fail" population is a minority of losers, consistent with R3's giveback story.

Verdict: **R3_CONCLUSIONS_UNCHANGED** → `r3_repair_pass = true`,
`r4_static_frontier_cleared = true`.

## Affected artifacts (regenerated)

- `R3_TIME_TO_PROFIT.csv` (new columns; timestamps identical)
- `R3_PROFIT_ANATOMY_REPORT.md` (Q2 rewritten)
- `R3_DECISION.json` (`time_to_first_profit` block replaced with corrected fields)
- `R3_INPUT_HASH_MANIFEST.json` (code hashes changed)

All other R3 artifacts verified **byte-identical** to the pre-repair commit
(R3_MFE_DISTRIBUTIONS, R3_TIME_TO_MFE, R3_CAPTURE_RATIO, R3_PROFIT_GIVEBACK,
R3_GIVEBACK_TRANSITIONS, R3_REMAINING_EXPECTANCY_SURFACE, R3_PROFIT_MATURITY,
R3_FAMILY_PROFIT_COMPARISON, R3_CONCURRENCY_PROFIT_EFFECTS,
R3_EPISODE_PROFIT_EFFECTS, R3_WINNER_TAIL_ATTRIBUTION,
R3_TEMPORAL_PROFIT_STABILITY, R3_PROFIT_DELIVERY_CURVE).

## Regression tests (4 added, `tests/test_risk_r3.py`)

1. All shares/probabilities in [0, 1].
2. Numerators match their populations (N_winners_reached <= N_winners, etc.) and
   shares use matching denominators.
3. `N_reached_all == N_winners_reached + N_losers_reached`; pooled = A + B.
4. First-passage median times unchanged vs direct path recomputation.

**Tests:** 23/23 R3 (19 + 4 new) · 267/267 repo-wide (main suite untouched this
repair) · deterministic rerun.
