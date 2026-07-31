# CEREBUS Backtest Report — LCOUSD (Regime-Adaptive)

> Generated: 2026-06-01 21:35 | Engine: Symmetry Trap | MC: 10,000 iterations

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Trades | 240 |
| Win Rate | 76.7% |
| Profit Factor | 7.31 |
| Total PnL | +1937.4 pips |
| Max DD | 29.0 pips (0.0%) |
| Expectancy | 8.07 pips/trade |
| Sharpe | 11.85 |
| Sortino | 16.92 |

## Monte Carlo (10k Simulations)

| Metric | Value |
|--------|-------|
| Equity P5 | +1661.8 pips |
| Equity P25 | +1826.2 pips |
| Equity Median | +1936.8 pips |
| Equity P75 | +2050.0 pips |
| Equity P95 | +2210.2 pips |
| Max DD Median | 31.0 pips |
| Max DD P95 | 50.0 pips |
| Ruin (10%) | 0.0% |
| Ruin (20%) | 0.0% |
| Ruin (30%) | 0.0% |
| Kelly | 0.630 |
| Half-Kelly | 0.315 |

## Regime Breakdown

### PRE_WAR

| Metric | Value |
|--------|-------|
| Trades | 87 |
| Win Rate | 80.5% |
| PnL | +673.4 pips |
| Profit Factor | 7.67 |
| Tier Dist | {'T2': 43, 'T1': 36, 'T3': 8} |

### WAR_ONSET

| Metric | Value |
|--------|-------|
| Trades | 59 |
| Win Rate | 84.7% |
| PnL | +658.2 pips |
| Profit Factor | 13.19 |
| Tier Dist | {'T2': 37, 'T1': 15, 'T3': 7} |

### WAR_SPIKE

| Metric | Value |
|--------|-------|
| Trades | 31 |
| Win Rate | 58.1% |
| PnL | +86.4 pips |
| Profit Factor | 2.11 |
| Tier Dist | {'T3': 12, 'T1': 11, 'T2': 8} |

### NORMALIZATION

| Metric | Value |
|--------|-------|
| Trades | 63 |
| Win Rate | 73.0% |
| PnL | +519.4 pips |
| Profit Factor | 8.02 |
| Tier Dist | {'T2': 35, 'T1': 17, 'T3': 11} |

## Tier Distribution

- **T1**: 79 trades | WR=78.5% | PnL=+486.2 pips
- **T2**: 123 trades | WR=74.8% | PnL=+1130.2 pips
- **T3**: 38 trades | WR=78.9% | PnL=+321.0 pips

## Long vs Short

- **LONG**: 125 trades | WR=74.4% | PnL=+974.9 pips
- **SHORT**: 115 trades | WR=79.1% | PnL=+962.5 pips

## Regime to Tier Mapping (Daily)

- **PRE_WAR**: 39 days | AR mean=47.7p | Tiers: {'T2': 20, 'T1': 12, 'T3': 4, 'NO_GO': 3}
- **WAR_ONSET**: 23 days | AR mean=60.1p | Tiers: {'T2': 11, 'T1': 7, 'T3': 3, 'NO_GO': 2}
- **WAR_SPIKE**: 13 days | AR mean=35.8p | Tiers: {'T1': 6, 'T2': 3, 'T3': 3, 'NO_GO': 1}
- **NORMALIZATION**: 29 days | AR mean=50.3p | Tiers: {'T2': 13, 'T1': 10, 'T3': 5, 'NO_GO': 1}
