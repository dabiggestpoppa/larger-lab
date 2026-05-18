# Strategy: Alpha Combination Signal Stacking

## Sources
- RohOnChain X thread: "Math Behind Combining 50 Weak Signals Into One Winning Trade"
- RohOnChain tweet: Step 5 — Kelly position sizing
- PANews article: Summary of RohOnChain's 11-step alpha combination
- arXiv:2409.04471 — Stacking ensemble ML for EUR/USD (58.52% accuracy)

## Core Logic
Combine multiple weak trading signals into one strong "Mega-Alpha" using optimal mathematical weighting, then size positions using Kelly criterion.

### Signal Generation (Weak Alphas)
Each signal produces a score: +1 (bullish), -1 (bearish), 0 (neutral)

**Example signals for EUR/USD:**
1. EMA 20 > EMA 50 → +1, else -1
2. RSI(14) < 30 → +1, > 70 → -1, else 0
3. MACD histogram > 0 → +1, else -1
4. Price > upper Bollinger → -1, < lower → +1, else 0
5. ADX > 25 + DI+ > DI- → +1, ADX > 25 + DI- > DI+ → -1, else 0
6. ATR ratio > 1.5 → reduce exposure (volatility filter)
7. Session filter: London/NY overlap → full weight, Asian → half weight
8. Donchian breakout: price > 20-high → +1, < 20-low → -1
9. Stochastic %K > 80 → -1, < 20 → +1, else 0
10. COT positioning extreme → contrarian signal

### Optimal Weighting
1. Backtest each signal independently → return series
2. Compute μ (mean return) and Σ (covariance matrix)
3. w_raw = Σ⁻¹ μ (Markowitz-style optimal weights)
4. Normalize: w = w_raw / Σ|w_raw|
5. Combined alpha: A(t) = Σ wᵢ × Sᵢ(t)

### Position Sizing (Kelly)
- f* = μ_A / σ_A² (fractional Kelly: 0.3 × f*)
- Position size = f × account / stop_loss_pips
- Scale with |A(t)|: stronger combined signal = larger position

## Expected Performance
- With 10 independent signals (IC ≈ 0.03 each): combined IR ≈ 0.03 × √10 ≈ 0.095
- With 50 independent signals (IC ≈ 0.05 each): combined IR ≈ 0.354
- Kelly sizing maximizes long-term growth rate
- Expected improvement: 20-40% Sharpe ratio vs single-signal strategies

## Implementation Approach
1. Define 8-12 clear signals with backtestable rules
2. Compute historical return matrix
3. Calculate optimal weights (can update weekly)
4. Generate combined alpha for each bar
5. Apply threshold + Kelly sizing
