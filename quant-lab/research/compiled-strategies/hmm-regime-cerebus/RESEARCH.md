# Strategy: HMM Regime-Aware CEREBUS

## Sources
- arXiv:2509.14385 — "Adaptive and Regime-Aware RL for Portfolio Optimization" (Raj, 2025)
- arXiv:2601.19504 — "Hybrid AI-Driven Trading System with Market Regime Adaptation" (2024)
- arXiv:2510.03236 — "Regime-Switching Volatility Forecasting" (2025)
- arXiv:2409.04471 — "Predicting EUR/USD Direction Using ML" (HMM + NN ensemble)
- CEREBUS FX v4.0 Manual: Regime Classification (Part 3), Overfilled Filter (Part 10)
- RohOnChain: IR = IC × √N — regime detection as a signal in the alpha stack

## Core Logic
Use Hidden Markov Model (HMM) for probabilistic regime detection, then adapt CEREBUS strategy parameters per regime. Combines CEREBUS's rule-based regime classification with statistical HMM for more robust regime identification.

### Regime Model (3-State HMM)
| Regime | Characteristics | CEREBUS Adaptation |
|--------|----------------|-------------------|
| **Trending** | High ADX (>25), directional momentum, low vol ratio | Full P90 + Cascade + Dual-Engine. Target -100% AR |
| **Mean-Reverting** | Low ADX (<20), range-bound, high BB %B oscillation | Stall-Harvest + Deep Mean Reversion. Tight targets |
| **High Volatility** | ATR spike (>2× avg), gap events, news | Reduce size 50%, widen stops, or stay flat |

### HMM Observation Features (5 signals for alpha combination)
| # | Feature | IC (est.) | Weight |
|---|---------|-----------|--------|
| 1 | ADX (trend strength) | 0.10 | 0.25 |
| 2 | ATR ratio (vol regime) | 0.08 | 0.20 |
| 3 | Bollinger Band width | 0.06 | 0.15 |
| 4 | Hurst exponent (H) | 0.12 | 0.25 |
| 5 | Session/time-of-day | 0.05 | 0.15 |

**Combined regime IR = √(0.01+0.0064+0.0036+0.0144+0.0025) = √0.0369 ≈ 0.192**

### Regime-Adapted CEREBUS Parameters

| Parameter | Trending | Mean-Reverting | High Vol |
|-----------|----------|----------------|----------|
| P90 Threshold | Standard | Standard | +20% wider |
| Position Size | 100% | 75% | 50% or flat |
| Max Cascades | 3 | 2 | 0 |
| Primary Target | -100% AR | -50% AR | -25% AR |
| Secondary Target | -168% Stall | -25% AR | None |
| Stop Width | 80% P90 | 80% P90 | 120% P90 |
| Sub-strategy | P90 Cascade | Stall-Harvest | Stand down |

### Alpha Combination Integration
The HMM regime probability feeds into the CEREBUS P90 Alpha Combo as signal #13:
- P(Regime=Trending) > 0.7 → +1 for trend-following signals
- P(Regime=MeanReverting) > 0.7 → +1 for mean-reversion signals
- P(Regime=HighVol) > 0.7 → -1 for all directional signals (reduce exposure)

### Entry Rules
1. Compute HMM regime probabilities
2. If P(HighVol) > 0.6 → STAND DOWN (no new trades)
3. If P(Trending) > 0.5 → Use full CEREBUS P90 + Cascade + Dual-Engine
4. If P(MeanReverting) > 0.5 → Use Stall-Harvest + Deep Mean Reversion
5. Apply alpha combination scoring within the active sub-strategy
6. Size = base_size × max_regime_probability (confidence-weighted)

### Exit Rules
- Same as CEREBUS standard (TP1/TP2, 12PM hard exit, 132% kill switch)
- Additional: Regime transition detected → Close 50%, reassess

## Expected Performance
- Regime detection accuracy: 60-70% (HMM) vs 55-60% (rule-based)
- 15-30% improvement in Sharpe ratio vs static CEREBUS (per arXiv papers)
- Better drawdown control (reduce exposure in high-vol regimes)
- **Combined IR (regime + alpha): 0.192 × 0.278 ≈ 0.33 (3.3x over single signal)**

## Implementation Notes
- HMM can be approximated with rule-based regime detection for backtesting
- Full HMM requires hmmlearn library (`pip install hmmlearn`)
- Regime probabilities updated daily at 9 AM EST (CEREBUS checkpoint)
- Compatible with all CEREBUS sub-strategies
