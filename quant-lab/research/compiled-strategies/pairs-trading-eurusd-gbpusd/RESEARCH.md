# Strategy: Pairs Trading EUR/USD-GBP/USD with Alpha Combination

## Sources
- Politecnico di Milano thesis: "Statistical Arbitrage in Forex: Pairs Trading and Mean Reversion"
- arXiv:2505.03659 — Meta-learning portfolio selection (allocation framework)
- RohOnChain: IR = IC × √N — spread signals as independent alpha sources
- General stat arb literature (cointegration-based pairs trading)

## Core Logic
Trade the spread between EUR/USD and GBP/USD. Instead of a single z-score threshold, combine multiple spread-related signals into a composite alpha score. The two pairs share USD as the counter currency, creating natural cointegration.

### Spread Definition
- **Ratio spread:** z = EUR/USD ÷ GBP/USD
- **Price spread:** z = EUR/USD - GBP/USD (normalized by ATR)
- **Return spread:** z = returns(EUR/USD, 5-bar) - returns(GBP/USD, 5-bar)

### Alpha Combination Signals (8 signals)
| # | Signal | IC (est.) | Weight | Source |
|---|--------|-----------|--------|--------|
| 1 | Z-score of ratio spread | 0.10 | 0.20 | Stat arb standard |
| 2 | Z-score of price spread | 0.08 | 0.15 | Normalized spread |
| 3 | Rolling correlation breakdown | 0.07 | 0.12 | Correlation regime |
| 4 | Cointegration test (ADF) | 0.09 | 0.15 | Mean-reversion strength |
| 5 | Spread momentum (5-bar) | 0.05 | 0.08 | Short-term divergence |
| 6 | Volatility ratio (EUR/USD vol ÷ GBP/USD vol) | 0.04 | 0.07 | Vol regime |
| 7 | Session timing (London overlap) | 0.06 | 0.10 | Liquidity regime |
| 8 | Day of week (Tue/Wed best) | 0.04 | 0.06 | Calendar effect |
| 9 | Spread Bollinger Band position | 0.05 | 0.07 | Mean-reversion zone |

**Combined IR = √(0.01+0.0064+0.0049+0.0081+0.0025+0.0016+0.0036+0.0016+0.0025) = √0.0412 ≈ 0.203**

### Trading Rules
1. **Entry:** |A(t)| >= 0.5 (strong composite signal)
   - A(t) > 0: Long EUR/USD, Short GBP/USD (spread expected to widen)
   - A(t) < 0: Short EUR/USD, Long GBP/USD (spread expected to narrow)
2. **Position sizing:** Dollar-neutral (equal notional both legs)
   - Kelly-adjusted: base 1% risk × |A(t)| × 0.3 fractional Kelly
3. **Exit:** |z_score| < 0.5 (spread reverted to mean)
4. **Stop loss:** |z_score| > 3.0 (divergence increased — fundamental change)
5. **Time stop:** Close if no mean reversion within 50 bars

### Regime Filter
- Only trade when rolling 50-bar correlation > 0.70
- If correlation drops below 0.60 → close all positions (cointegration breakdown)
- High volatility regime (ATR ratio > 2.0) → reduce size 50%

## Expected Performance
- Market-neutral (profits from relative moves, not direction)
- Sharpe ratio: 1.0-1.8 (with alpha combination vs 0.8-1.5 base)
- Win rate: 60-65% on spread trades
- Max drawdown: 3-5% (diversified across spread mean-reversion)
- **IR improvement: 2.03x over single z-score signal**

## Implementation Approach
1. Load both EUR/USD and GBP/USD M5 data
2. Compute ratio spread and z-score
3. Compute all 9 alpha signals
4. Generate composite alpha A(t)
5. Enter when |A(t)| >= 0.5
6. Monitor correlation regime continuously
7. Exit on mean reversion, stop loss, or time stop
