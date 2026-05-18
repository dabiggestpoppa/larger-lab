# Strategy: Regime-Switching Adaptive

## Sources
- arXiv:2509.14385 — "Adaptive and Regime-Aware RL for Portfolio Optimization" (Raj, 2025)
- arXiv:2601.19504 — "Hybrid AI-Driven Trading System with Market Regime Adaptation" (2024)
- arXiv:2510.03236 — "Regime-Switching Volatility Forecasting" (2025)
- Reddit: "Building an Adaptive Trading System with Regime Switching, GA's, RL"

## Core Logic
Different market regimes require different strategies. Instead of using one strategy all the time:
1. **Detect current market regime** using volatility, trend strength, and correlation features
2. **Select the optimal strategy** for that regime
3. **Adjust position sizing** based on regime confidence and volatility

### Regime Classification (3-Regime Model)
| Regime | Characteristics | Best Strategy |
|--------|----------------|---------------|
| **Trending** | High ADX (>25), low volatility ratio, directional momentum | Trend-following (EMA cross, breakout) |
| **Mean-Reverting** | Low ADX (<20), high Bollinger Band %B oscillation, range-bound | Mean reversion (RSI extremes, stall zones) |
| **High Volatility** | ATR spike, VIX surge, gap events | Reduce exposure, wider stops, or stay flat |

### Regime Detection Features
- **ADX (Average Directional Index):** Trend strength
- **ATR ratio (current/20-period mean):** Volatility regime
- **Bollinger Band width:** Volatility measure
- **Hurst exponent:** Mean-reversion vs trending (H < 0.5 = mean-reverting, H > 0.5 = trending)
- **Session/time-of-day:** Liquidity regime

## Expected Performance
- Papers report 15-30% improvement in Sharpe ratio vs static strategies
- Better drawdown control (reduce exposure in high-vol regimes)
- Works best when regime detection has >55% accuracy

## Implementation Approach
1. Compute regime features on each bar
2. Classify current regime (simple rule-based or HMM)
3. Activate regime-appropriate strategy
4. Scale position size inversely with regime uncertainty
