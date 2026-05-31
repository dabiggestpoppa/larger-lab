# CEREBUS Symmetry Trap — Metals & Crypto Group Report

**Generated:** 2026-05-31
**Engine:** Symmetry Trap (Engine B) — 4-state FSM, single AU target
**Risk Model:** 1% risk per trade, $10,000 starting balance
**Monte Carlo:** 10,000 iterations, randomized trade order from pooled universe

---

## ⚠️ CRITICAL FLAG: XAGUSD Insufficient Sample Size

> **XAGUSD has only 2 trades (1W / 1L, 50% WR).** This is statistically meaningless.
> All XAGUSD stats — Win Rate, Profit Factor, Sharpe, Max DD, MC outputs — are **noise**, not signal.
> **Do not make allocation decisions based on XAGUSD data.** The asset needs 50+ trades minimum for
> any statistical validity. It is included here for completeness but should be treated as a
> placeholder until more trade signals materialize on the M5 timeframe.

---

## Group Summary Table

| Asset | Trades | Wins | Losses | Win Rate | Total PnL (pips) | Gross Profit | Gross Loss | Profit Factor | Sharpe | Max DD (pips) | Max DD % | Kelly |
|-------|--------|------|--------|----------|-------------------|--------------|------------|---------------|--------|----------------|----------|-------|
| **XAUUSD** (Gold) | 604 | 510 | 92 | 84.4% | +7,187.7 | 8,307.8 | -1,120.1 | 7.42 | 11.28 | 121.4 | 0.12% | 0.7281 |
| **XAGUSD** (Silver) ⚠️ | 2 | 1 | 1 | 50.0% | +2.5 | 2.6 | -0.1 | 26.00 | 10.39 | 0.1 | 0.00% | 0.4808 |
| **BTCUSD** (Bitcoin) | 801 | 742 | 59 | 92.6% | +152,304.3 | 158,273.4 | -5,969.1 | 26.52 | 13.00 | 785.0 | 0.78% | 0.8914 |
| **ETHUSD** (Ethereum) | 547 | 530 | 17 | 96.9% | +9,562.5 | 9,756.3 | -193.8 | 50.34 | 24.04 | 31.7 | 0.03% | 0.9497 |
| **GROUP AGGREGATE** | **1,954** | **1,783** | **169** | **91.25%** | **+169,057.0** | **+176,340.1** | **-7,283.1** | **24.21** | **7.97** | — | — | — |

*Note: Group aggregate Max DD and Kelly are outputs of the combined MC simulation (see below).*

---

## Per-Asset Breakdown

### XAUUSD (Gold) — 604 Trades

| Metric | Value |
|--------|-------|
| Win Rate | 84.4% (510W / 92L) |
| Expectancy | +11.90 pips/trade |
| Avg Win / Avg Loss | +16.3 / -12.2 pips |
| Best Trade | +94.4 pips |
| Worst Trade | -121.4 pips |
| Max Consec Wins / Losses | 30 / 3 |
| Data Coverage | 306,934 bars / 1,362 days |

**Directional Split:** Long 84.1% WR (+3,727.4p) | Short 84.8% WR (+3,460.3p) — balanced.

**Tier Breakdown:**
| Tier | Trades | AR Range | WR | PnL |
|------|--------|----------|-----|------|
| T1 (AU=16.0p) | 69 | ≤32.0p | 76.8% | +158.4p |
| T2 (AU=29.0p) | 292 | ≤58.0p | 83.9% | +3,366.4p |
| T3 (AU=48.0p) | 243 | ≤95.0p | 87.2% | +3,662.9p |

T2+T3 = 88.4% of trades, 97.7% of PnL. Classic tier scaling — larger AU targets capture more value.

**Best Hours (EST):** 03:00-04:00 (93.0% WR, +630.1p), 09:00-10:00 (89.6% WR)

---

### XAGUSD (Silver) — 2 Trades ⚠️ INSUFFICIENT DATA

| Metric | Value |
|--------|-------|
| Win Rate | 50.0% (1W / 1L) |
| Total PnL | +2.5 pips |
| Avg Win / Avg Loss | +2.6 / -0.1 pips |
| Data Coverage | 304,981 bars / 1,366 days |

> **Only 2 trades in 1,366 days of M5 data.** The engine rarely triggers on Silver at the current
> AU/AR thresholds. This does NOT mean the strategy fails on XAGUSD — it means the symmetry conditions
> are rarely met. Consider: (a) adjusting AU/AR for Silver's volatility regime, (b) using a lower
> timeframe to generate more signals, or (c) accepting that Silver is a low-frequency signal asset.

**Tier Breakdown:** All 2 trades in T3 only (AU=2.6p — note: unusually small XAG target).

---

### BTCUSD (Bitcoin) — 801 Trades

| Metric | Value |
|--------|-------|
| Win Rate | 92.6% (742W / 59L) |
| Expectancy | +190.14 pips/trade |
| Avg Win / Avg Loss | +213.3 / -101.2 pips |
| Best Trade | +2,696.8 pips |
| Worst Trade | -785.0 pips |
| Max Consec Wins / Losses | 66 / 2 |
| Data Coverage | 458,887 bars / 1,611 days |

**Directional Split:** Long 92.8% WR (+75,184.0p) | Short 92.5% WR (+77,120.3p) — perfectly balanced.

**Tier Breakdown:**
| Tier | Trades | AR Range | WR | PnL |
|------|--------|----------|-----|------|
| T1 (AU=205.0p) | 375 | ≤750.0p | 90.9% | +30,246.0p |
| T2 (AU=545.0p) | 297 | ≤1,700.0p | 93.3% | +60,215.7p |
| T3 (AU=1,160.0p) | 129 | ≤3,000.0p | 96.1% | +61,842.6p |

T3 has the highest WR (96.1%) and contributes 40.6% of total PnL despite only 16.1% of trades.
The PnL/Tier distribution is remarkably even — each tier contributes ~30K pips. This indicates
**excellent tier diversification** on BTC.

**Loop Distribution:** Loop 1 dominates (505 trades, 95.2% WR, +111,930.8p). Loop 4 drops to 75.8%
WR — consider reviewing loop 4-5 conditions for potential filtering.

**Best Hours (EST):** 04:00-05:00 (98.5% WR, +14,900.2p), 07:00-08:00 (95.1% WR)

---

### ETHUSD (Ethereum) — 547 Trades

| Metric | Value |
|--------|-------|
| Win Rate | 96.9% (530W / 17L) — **highest in group** |
| Expectancy | +17.48 pips/trade |
| Avg Win / Avg Loss | +18.4 / -11.4 pips |
| Best Trade | +66.6 pips |
| Worst Trade | -31.7 pips |
| Max Consec Wins / Losses | 90 / 2 |
| Data Coverage | 458,015 bars / 1,611 days |

**Directional Split:** Long 97.2% WR (+4,590.6p) | Short 96.6% WR (+4,971.9p) — balanced.

**Tier Breakdown:**
| Tier | Trades | AR Range | WR | PnL |
|------|--------|----------|-----|------|
| T1 (AU=35.0p) | 204 | ≤70.0p | 96.6% | +2,906.9p |
| T2 (AU=42.0p) | 167 | ≤105.0p | 97.0% | +2,745.4p |
| T3 (AU=52.0p) | 176 | ≤160.0p | 97.2% | +3,910.2p |

Extremely consistent WR across tiers (96.6%-97.2%). T3 delivers the best absolute PnL despite
similar win rates — larger targets capture more per win. Tightest Max DD in the group (31.7 pips, 0.03%).

**Loop Distribution:** Loop 1 is dominant (448 trades, 98.2% WR, +8,235.9p). Loop 2 drops to 89.2%
WR. Loops 3-5 barely trigger. **Loop 1 alone is 81.9% of all ETH trades.**

**Best Hours (EST):** 02:00-07:00 block is exceptional (93-100% WR across 5 consecutive hours).
The 06:00-07:00 and 07:00-08:00 windows are 100% WR.

---

## Tier Breakdown — Group Aggregate

| Tier | XAUUSD | XAGUSD | BTCUSD | ETHUSD | Total Trades | Group WR |
|------|--------|--------|--------|--------|--------------|----------|
| T1 | 69 (76.8%) | 0 (--) | 375 (90.9%) | 204 (96.6%) | 648 | ~89% |
| T2 | 292 (83.9%) | 0 (--) | 297 (93.3%) | 167 (97.0%) | 756 | ~91% |
| T3 | 243 (87.2%) | 2 (50.0%) | 129 (96.1%) | 176 (97.2%) | 550 | ~91% |
| **Total** | **604** | **2** | **801** | **547** | **1,954** | **91.25%** |

*Group WR per tier is approximate (weighted by trade count across assets).*

Key observations:
- **T2 is the sweet spot** for the group: 756 trades (~39% of group), ~91% WR
- **T3 has the highest WR** on every asset except XAGUSD (noise), but fewer trades
- **T1 underperforms** on XAUUSD (76.8%) but is strong on ETH (96.6%) — asset-dependent
- **Group is well-distributed** across T1/T2/T3 — no single tier dominates

---

## Monte Carlo Simulation — Combined Pool

**Method:** 10,000 iterations drawing random trade sequences from the pooled 1954-trade universe.
Each simulation randomizes the order of all trades across all 4 assets. Starting balance $10,000,
1% risk per trade.

### Aggregate Performance Distribution

| Metric | Value |
|--------|-------|
| Total Pooled Trades | 1,954 |
| Blended Win Rate | 91.25% (1,783W / 169L) |
| Combined Gross Profit | +176,340.1 pips |
| Combined Gross Loss | -7,283.1 pips |
| Combined Profit Factor | 24.21 |
| Combined Sharpe (annualized) | 7.97 |
| Median Final PnL | +169,057.0 pips |
| Mean Final PnL | +169,057.0 pips |
| Std Dev of Final PnL | ~0.0 pips |
| 90% Confidence Interval | [+169,057.0, +169,057.0] |

*Note: Std Dev and CI collapse to zero because the MC randomizes order, not trade composition.
The total PnL is invariant — all sims use the same trade set. Order variance affects drawdown,
not total PnL. See DD distribution below for the real MC signal.*

### Drawdown Distribution (MC)

| Metric | Value |
|--------|-------|
| Median Max Drawdown | 1.71% |
| 95th Percentile Max DD | 5.43% |
| Worst Max Drawdown (all sims) | 13.56% |
| Ruin Probability (>50% DD) | **0.00%** |

**Interpretation:** Even in the worst-case trade ordering across 10,000 simulations, the maximum
drawdown never exceeded 13.56%. The median worst-case scenario is a mere 1.71% drawdown.
The probability of losing 50% of starting capital is zero — the group has **massive statistical
cushion** against ruin.

### Profit Factor Distribution (MC)

| Metric | Value |
|--------|-------|
| Median Profit Factor | 24.21 |
| 5th Percentile PF | 24.21 |
| 95th Percentile PF | 24.21 |

PF is invariant (same gross profit/loss regardless of order).

### Equity Curve — Median with Confidence Bands

| Trade # | Median PnL (pips) | 5th Percentile | 95th Percentile | Spread |
|---------|-------------------|----------------|-----------------|--------|
| 0 | 0.0 | 0.0 | 0.0 | — |
| 50 | +4,200.9 | +2,533.2 | +6,512.0 | 3,978.8 |
| 100 | +8,543.2 | +6,045.7 | +11,647.8 | 5,602.1 |
| 250 | +21,480.0 | +17,617.6 | +25,905.3 | 8,287.7 |
| 500 | +43,157.4 | +37,859.2 | +48,801.4 | 10,942.2 |
| 750 | +64,818.8 | +58,799.0 | +71,234.2 | 12,435.2 |
| 1,000 | +86,496.7 | +80,213.9 | +92,786.4 | 12,572.5 |
| 1,250 | +108,187.9 | +102,014.8 | +114,110.4 | 12,095.6 |
| 1,500 | +129,799.2 | +124,283.5 | +134,913.2 | 10,629.7 |
| 1,750 | +151,501.2 | +147,412.6 | +155,051.5 | 7,638.9 |
| 1,954 | +169,057.0 | +169,057.0 | +169,057.0 | 0.0 |

**Equity Curve Shape:** Near-monotonic increase. The 5th percentile line stays well above zero
throughout — even in bad orderings, the equity never seriously retraces. Band width peaks around
trade 1000 (widest uncertainty) and narrows as the sample completes.

### Per-Asset PnL Contribution to Group

| Asset | Total PnL (pips) | % of Group PnL | Trade Count | % of Group Trades | PnL/Trade |
|-------|------------------|----------------|-------------|-------------------|-----------|
| BTCUSD | +152,304.3 | **90.1%** | 801 | 41.0% | +190.1 |
| ETHUSD | +9,562.5 | 5.7% | 547 | 28.0% | +17.5 |
| XAUUSD | +7,187.7 | 4.3% | 604 | 30.9% | +11.9 |
| XAGUSD ⚠️ | +2.5 | 0.0% | 2 | 0.1% | +1.3 |

**BTCUSD contributes 90.1% of group PnL** with only 41% of trades. This is driven by BTC's
much larger pip targets (AU=205-1160p vs XAU 16-48p and ETH 35-52p).

---

## Key Observations

### Strengths
1. **Exceptional group win rate: 91.25%** — all 3 meaningful assets exceed 84% WR
2. **BTCUSD dominance** — 92.6% WR, PF=26.52, Sharpe=13.0, and 90% of group PnL. Single strongest performer
3. **ETHUSD: lowest risk** — Max DD 31.7 pips (0.03%), highest Sharpe (24.04), near-perfect 96.9% WR
4. **Ruin probability = 0%** — across 10,000 simulations, no run ever came close to 50% drawdown
5. **Tier scaling works** — higher AU tiers consistently deliver higher WR across all assets
6. **Directional balance** — no asset shows significant long/short bias; symmetry works both ways

### Risks & Concerns
1. **⚠️ XAGUSD: only 2 trades** — cannot be treated as a signal. Needs threshold recalibration or lower timeframe
2. **BTCUSD concentration risk** — 90% of PnL from one asset. If BTC market regime changes, group PnL drops sharply
3. **BTC loop 4-5 decay** — WR drops to 75.8% and 83.8% in loops 4-5. Consider filtering these
4. **ETH narrow signal** — 81.9% of ETH trades fire in Loop 1 only. Loops 2-5 rarely trigger
5. **Correlated drawdowns** — BTC and ETH are crypto-correlated. If crypto dumps, both draw down simultaneously
6. **XAU highest DD relative to PnL** — Gold has 1.7% DD/PnL ratio vs ETH's 0.3%. Least efficient

### Recommendations
1. **Allocate 60-65% to BTCUSD** — it produces 90% of profits with excellent stats
2. **Allocate 20-25% to ETHUSD** — lowest risk, near-perfect WR, good stabilizer for the group
3. **Allocate 10-15% to XAUUSD** — solid but less efficient than_crypto assets
4. **Do NOT allocate to XAGUSD** until it generates 50+ trades under current settings
5. **Consider BTC loop filtering** — adding a Loop ≥4 entry condition may improve BTC efficiency
6. **Cross-asset correlation management** — consider reducing BTC+ETH combined allocation during
   high VIX regimes to manage correlated drawdown risk

---

## Appendix: Data Quality

| Asset | Total Bars | Data Days | Date Range | M5 Coverage |
|-------|------------|-----------|------------|-------------|
| XAUUSD | 306,934 | 1,362 days | ~3.7 years | Full |
| XAGUSD | 304,981 | 1,366 days | ~3.7 years | Full |
| BTCUSD | 458,887 | 1,611 days | ~4.4 years | Full |
| ETHUSD | 458,015 | 1,611 days | ~4.4 years | Full |

All assets have extensive multi-year M5 coverage. Trade counts reflect how often Symmetry Trap
conditions are met — not data availability.

---

*Report generated by CEREBUS Group Aggregation Worker — Symmetry Trap Engine B*
*Monte Carlo: 10,000 simulations | Seed: 42 | Pooling method: full universe shuffle*
*Do not trade based on backtests alone. Past performance does not guarantee future results.*
