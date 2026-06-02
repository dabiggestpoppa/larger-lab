# CEREBUS Backtest Report — OILUSD (Regime-Adaptive)

> Generated: 2026-06-01 21:36 | Engine: Symmetry Trap | MC: 10,000 iterations

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Trades | 2651 |
| Win Rate | 75.2% |
| Profit Factor | 6.54 |
| Total PnL | +17667.3 pips |
| Max DD | 89.7 pips (0.1%) |
| Expectancy | 6.66 pips/trade |
| Sharpe | 9.06 |
| Sortino | 15.24 |

## Monte Carlo (10k Simulations)

| Metric | Value |
|--------|-------|
| Equity P5 | +16696.7 pips |
| Equity P25 | +17251.7 pips |
| Equity Median | +17656.1 pips |
| Equity P75 | +18065.0 pips |
| Equity P95 | +18668.2 pips |
| Max DD Median | 72.0 pips |
| Max DD P95 | 99.0 pips |
| Ruin (10%) | 0.0% |
| Ruin (20%) | 0.0% |
| Ruin (30%) | 0.0% |
| Kelly | 0.606 |
| Half-Kelly | 0.303 |

## Regime Breakdown

### PRE_WAR

| Metric | Value |
|--------|-------|
| Trades | 608 |
| Win Rate | 74.5% |
| PnL | +2930.0 pips |
| Profit Factor | 4.36 |
| Tier Dist | {'T2': 385, 'T1': 198, 'T3': 25} |

### WAR_ONSET

| Metric | Value |
|--------|-------|
| Trades | 395 |
| Win Rate | 74.2% |
| PnL | +2171.3 pips |
| Profit Factor | 5.08 |
| Tier Dist | {'T2': 201, 'T1': 132, 'T3': 62} |

### WAR_SPIKE

| Metric | Value |
|--------|-------|
| Trades | 230 |
| Win Rate | 68.3% |
| PnL | +793.9 pips |
| Profit Factor | 4.25 |
| Tier Dist | {'T2': 121, 'T1': 78, 'T3': 31} |

### NORMALIZATION

| Metric | Value |
|--------|-------|
| Trades | 566 |
| Win Rate | 73.3% |
| PnL | +3025.0 pips |
| Profit Factor | 8.08 |
| Tier Dist | {'T2': 295, 'T1': 205, 'T3': 66} |

### CURRENT

| Metric | Value |
|--------|-------|
| Trades | 852 |
| Win Rate | 79.2% |
| PnL | +8747.1 pips |
| Profit Factor | 8.87 |
| Tier Dist | {'T1': 454, 'T2': 280, 'T3': 118} |

## Tier Distribution

- **T1**: 1067 trades | WR=73.3% | PnL=+3795.0 pips
- **T2**: 1282 trades | WR=76.6% | PnL=+10316.4 pips
- **T3**: 302 trades | WR=75.8% | PnL=+3555.9 pips

## Long vs Short

- **LONG**: 1375 trades | WR=75.5% | PnL=+9342.6 pips
- **SHORT**: 1276 trades | WR=74.8% | PnL=+8324.7 pips

## Regime to Tier Mapping (Daily)

- **PRE_WAR**: 198 days | AR mean=29.2p | Tiers: {'T2': 113, 'T1': 55, 'T3': 16, 'NO_GO': 14}
- **WAR_ONSET**: 122 days | AR mean=30.9p | Tiers: {'T2': 61, 'T1': 39, 'T3': 15, 'NO_GO': 7}
- **WAR_SPIKE**: 65 days | AR mean=22.0p | Tiers: {'T2': 38, 'T1': 17, 'T3': 6, 'NO_GO': 4}
- **NORMALIZATION**: 194 days | AR mean=27.0p | Tiers: {'T2': 99, 'T1': 61, 'T3': 20, 'NO_GO': 14}
- **CURRENT**: 300 days | AR mean=64.9p | Tiers: {'T2': 133, 'T1': 117, 'T3': 26, 'NO_GO': 24}
