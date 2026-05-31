# st-phase2-crosses Progress Report

**Status:** ✅ COMPLETE
**Completed:** 2026-05-31 01:06 EST

## Task
Generate grouped backtest report + Monte Carlo for the Crosses group (CHFJPY, GBPJPY, GBPAUD, GBPNZD, GBPCHF).

## Outputs
- `quant-lab/reports/groups/crosses_mc_results.json` — Full MC simulation results
- `quant-lab/reports/groups/crosses_report.md` — Detailed markdown report

## Summary of Results

### Aggregate Backtest Stats
| Metric | Value |
|--------|-------|
| Total Trades | 3,763 |
| Win Rate | 88.09% |
| Total PnL | +38,741.8 pips |
| Profit Factor | 15.82 |
| Sharpe | 13.95 |
| Max DD | 87.5 pips |
| Expectancy | 10.30 pips/trade |

### Per-Asset
| Asset | Trades | WR | PnL | PF | Max DD |
|-------|--------|-----|------|-----|--------|
| CHFJPY | 751 | 86.3% | +7,167.0 | 13.01 | 87.5p |
| GBPJPY | 830 | 86.3% | +8,655.6 | 12.61 | 61.9p |
| GBPAUD | 715 | 88.4% | +7,911.5 | 10.00 | 60.1p |
| GBPNZD | 664 | 88.4% | +8,598.3 | 20.87 | 46.2p |
| GBPCHF | 803 | 91.2% | +6,409.4 | 24.51 | 16.6p |

### Monte Carlo (10,000 sims)
- Median Terminal PnL: +38,741.8 pips (zero variance — deterministic sum)
- Median Max DD: 87.5 pips
- 95th Pct Max DD: 106.9 pips
- Worst Max DD: 165.9 pips
- Ruin Probability: 0.00%
- 90% CI for Terminal PnL: [+38,741.8, +38,741.8]

### Tier Breakdown (Group)
| Tier | Trades | WR | PnL |
|------|--------|-----|------|
| T1 | 679 | 79.5% | +3,809.3 |
| T2 | 463 | 87.7% | +4,269.5 |
| T3 | 439 | 94.8% | +7,743.8 |

## Flags
- ⚠️ CHFJPY highest individual max DD (87.5p) from single EOD_EXIT event
- ⚠️ GBPJPY tail risk (-61.9p EOD_EXIT on 2024-08-29)
- ⚠️ EOD_EXIT events in JPY crosses suggest gap/overnight risk
- ⚠️ JPY correlation between CHFJPY and GBPJPY reduces diversification during JPY events
- ✅ No systemic flags

## Method
- Combined all per-trade PnL arrays into single pool (3,763 trades)
- Ran 10,000 MC simulations randomizing trade order
- Computed equity curve percentiles, max DD distribution, PF distribution
- All engine code untouched — pure report generation
