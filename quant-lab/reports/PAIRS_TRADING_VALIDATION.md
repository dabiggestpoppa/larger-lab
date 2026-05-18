# Pairs Trading EUR/USD-GBP/USD — Validation Report

> **Validation Date:** 2026-05-18 00:17  
> **Validator:** Quant Lab Optimizer  
> **Strategy File:** `projects/trading/nautilus/strategies/pairs_trading_eurusd_gbpusd.py`  
> **Data:** EUR/USD M5 + GBP/USD M5 (2023-01-02 to 2026-05-06)

---

## Executive Summary

**Verdict: BUGS FOUND — NOT production ready.**

The strategy reports +$206K PnL (2,062% return) over ~3.3 years with a 72.6% win rate. This is **not a real edge** — it is an artifact of three compounding issues:

1. **No transaction costs** — Zero commission or spread applied. At ~$24 round-trip per standard lot, 3,931 trades would cost ~$94K+ in fees alone.
2. **Arbitrary P&L scaling** — The $50/z-unit multiplier is not derived from position sizing, pip value, or lot size. It is a magic number that inflates P&L without economic meaning.
3. **Suspiciously high trade count** — 3,931 trades over 3.3 years = ~3.3 trades/day, which is extremely high for a pairs trading strategy that requires |z| > 2.0 entries.

The underlying mean-reversion logic is sound in principle, but the backtest implementation is not trustworthy for production decisions.

---

## Data Quality

| Metric | Value |
|--------|-------|
| EUR/USD bars | 249,484 |
| GBP/USD bars | 249,422 |
| Common bars | 249,410 |
| Date range | 2023-01-02 to 2026-05-06 |
| Duration | 3.3 years (1220 days) |
| EUR/USD duplicates | 0 |
| GBP/USD duplicates | 0 |
| EUR/USD gaps (>30min) | 180 |
| GBP/USD gaps (>30min) | 180 |
| EUR/USD price range | 1.01842 - 1.20561 |
| GBP/USD price range | 1.18118 - 1.38538 |
| Avg 50-bar correlation | 0.7549 |
| Min 50-bar correlation | -0.8246 |
| Correlation < 0.70 | 68,594 bars (27.5%) |
| GBP/USD data source | Real (not synthetic) |

**Data quality is good.** Both files exist, no duplicates, no zero/negative prices, and the correlation between EUR/USD and GBP/USD is consistently high (mean 0.7549), which is expected and validates the pairs trading premise.

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Total trades | 3,929 |
| Win rate | 72.5% |
| Total P&L | $205,974.59 |
| Gross profit | $251,485.69 |
| Gross loss | $45,511.10 |
| Profit factor | 5.53 |
| Max drawdown | $265.00 |
| Max DD % of peak | 0.12% |
| Final equity | $215,974.59 |
| Expectancy/trade | $52.42 |
| Avg win | $88.24 |
| Avg loss | $-42.18 |
| Sharpe (trade-level) | 0.7525 |
| Sharpe (annualized) | 202.7141 |
| Annualized return | 150.9% |

---

## Trade Characteristics

| Metric | Value |
|--------|-------|
| Avg trade duration | 0.8 hours (10 bars) |
| Active trading days | 856 |
| Trades per day | 4.6 |
| Trades per week | 32.1 |

---

## Exit Reasons

| Exit Reason | Count | % |
|-------------|-------|---|
| mean_reversion | 2027 | 51.6% |
| stop_loss | 1348 | 34.3% |
| correlation_breakdown | 512 | 13.0% |
| time_stop | 42 | 1.1% |

---

## Temporal Analysis

### Day of Week

| Day | Trades | P&L | Avg P&L |
|-----|--------|-----|---------|
| Mon | 779 | $43,342.48 | $55.64 |
| Tue | 745 | $39,230.55 | $52.66 |
| Wed | 690 | $34,509.46 | $50.01 |
| Thu | 793 | $40,018.93 | $50.47 |
| Fri | 922 | $48,873.17 | $53.01 |
| Sat | 0 | $0.00 | $0.00 |
| Sun | 0 | $0.00 | $0.00 |

**Best day:** Fri ($48,873.17)  
**Worst day:** Wed ($34,509.46)

### Hour of Day (UTC) — Top 5 by P&L

| Hour | Trades | P&L | Avg P&L |
|------|--------|-----|---------|
| 00:00 | 258 | $23,153.12 | $89.74 |
| 09:00 | 551 | $15,758.43 | $28.60 |
| 10:00 | 385 | $15,160.17 | $39.38 |
| 17:00 | 245 | $13,411.18 | $54.74 |
| 16:00 | 224 | $11,802.07 | $52.69 |

**Best hour:** 00:00 UTC ($23,153.12)  
**Worst hour:** 20:00 UTC ($2,935.67)

### Monthly

| Month | Trades | P&L | Avg P&L |
|-------|--------|-----|---------|
| Jan | 369 | $20,707.90 | $56.12 |
| Feb | 379 | $20,199.09 | $53.30 |
| Mar | 397 | $22,705.24 | $57.19 |
| Apr | 380 | $17,874.24 | $47.04 |
| May | 355 | $17,750.96 | $50.00 |
| Jun | 279 | $14,312.57 | $51.30 |
| Jul | 300 | $15,689.37 | $52.30 |
| Aug | 292 | $14,638.65 | $50.13 |
| Sep | 299 | $17,364.09 | $58.07 |
| Oct | 295 | $17,388.41 | $58.94 |
| Nov | 300 | $16,618.96 | $55.40 |
| Dec | 284 | $10,725.10 | $37.76 |

**Best month:** Mar ($22,705.24)  
**Worst month:** Dec ($10,725.10)

---

## Critical Issues Found

### ❌ Issues (Must Fix)

1. **No commission or spread costs applied in backtest**
2. **P&L uses arbitrary $50/z-unit scaling, not real position sizing or pip-value calculation**

### ⚠️ Warnings (Should Address)

1. Alpha confirmation filter uses same-bar alpha (minor look-ahead risk)
2. Alpha weights and IC values appear hand-tuned/assumed, not empirically measured
3. Annualized return of 151% is unrealistic for pairs trading
4. Win rate of 72.5% is unusually high for pairs trading
5. Profit factor of 5.53 is unusually high
6. High trade frequency: 4.6 trades/day

---

## Detailed Analysis

### 1. Commission & Spread Impact

The backtest applies **zero transaction costs**. For a realistic estimate:

- **Spread cost:** ~0.5 pips per leg (EUR/USD and GBP/USD are tight, but not zero)
- **Commission:** ~0.1 pips per leg (typical ECN)
- **Round-trip cost per trade:** 4 legs x 0.6 pips = 2.4 pips ≈ $24 per standard lot
- **Total cost for 3,929 trades:** ~$94,296

This alone would eat ~47% of the reported P&L. With slippage and wider spreads during off-hours, the real cost could be even higher.

### 2. P&L Calculation

The P&L formula is: `pnl = (|entry_z| - |current_z|) * $50`

This is a **purely arbitrary scaling**. It does not account for:
- Actual position size (lot size)
- Pip value (which depends on the pair and lot size)
- The fact that EUR/USD and GBP/USD have different pip values
- The ratio spread vs. price spread distinction

A proper implementation would:
1. Define position size based on account risk (e.g., 1% per trade)
2. Calculate pip value for each leg
3. Compute actual dollar P&L from price changes

### 3. Look-Ahead Bias Assessment

**No significant look-ahead bias found.** All signals are computed from past data only:
- Rolling z-scores use backward-looking windows
- Entry/exit conditions use current bar values
- The alpha confirmation filter uses the same bar, which is acceptable for a bar-close strategy

### 4. Overfitting Risk

- 9 alpha signals with hand-tuned weights (sum to 1.0)
- IC values appear assumed rather than empirically measured
- Z-score parameters (window=50, entry=2.0, exit=0.5) are common defaults
- No walk-forward analysis or out-of-sample testing performed

### 5. Comparison with Other Strategies

From `unified_results.json`, the pairs trading strategy is the **best-performing** by raw P&L:

| Strategy | Trades | WR% | Total P&L | Max DD |
|----------|--------|-----|-----------|--------|
| Pairs Trading | 3,931 | 72.6% | +$206,245 | -$265 |
| P90 Alpha Combo | 426 | 51.2% | -$300 | -$318 |
| HMM Regime | 367 | 55.9% | -$57 | -$72 |
| Multi-TF CNN | 694 | 55.5% | -$290 | -$351 |
| Sentiment Enhanced | 627 | 48.0% | -$200 | -$258 |

The fact that pairs trading is massively profitable while all other strategies are flat or losing is a **red flag**. It suggests the P&L calculation is not comparable across strategies.

---

## Recommendation

### Status: **NEEDS WORK — Bug Found**

The strategy's mean-reversion logic is conceptually valid for EUR/USD-GBP/USD (highly correlated pairs), but the backtest implementation has critical flaws that make the results unreliable.

### Required Fixes Before Production

1. **Implement proper position sizing** — Risk 1-2% per trade, calculate lot size from stop distance
2. **Add transaction costs** — Include spread (0.5-1.0 pip) and commission per leg
3. **Fix P&L calculation** — Use actual pip values and position sizes, not arbitrary $50/z-unit
4. **Add walk-forward validation** — Test on out-of-sample data
5. **Reduce trade frequency** — 3.3 trades/day is excessive; consider higher z-score entry threshold
6. **Implement proper risk management** — Max daily loss limit, correlation breakdown exit

### Estimated Realistic Performance

After applying transaction costs and proper position sizing, a reasonable estimate:
- **Win rate:** 55-65% (still good for mean-reversion)
- **Profit factor:** 1.2-1.5 (decent but not extraordinary)
- **Annual return:** 15-30% (realistic for pairs trading)
- **Max drawdown:** 8-15% of account

---

*Report generated by Quant Lab Optimizer — 2026-05-18 00:17*
