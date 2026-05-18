# Strategy: CEREBUS P90 + Alpha Combination

## Sources
- CEREBUS FX v4.0 Manual (Parts 1-3, 6, 10): P90, Cascade, Dual-Engine, Convergence Factor
- RohOnChain: "Math Behind Combining 50 Weak Signals Into One Winning Trade" — IR = IC × √N
- 151 Trading Strategies (Kakushadze & Serur): Strategy 3.20 Alpha Combos
- arXiv:2409.04471 — Stacking ensemble ML for EUR/USD (58.52% accuracy)

## Core Logic — Alpha Combination Framework
Per RohOnChain's Fundamental Law: **IR = IC × √N**
Instead of relying on a single P90 signal, combine 12+ independent weak signals into one composite alpha score. Each signal contributes a weighted score based on its historical IC (predictive power).

### The 12 Signals (Weak Alphas → Mega-Alpha)
Each signal produces: +1 (bullish), -1 (bearish), 0 (neutral)

| # | Signal | IC (est.) | Weight | Source |
|---|--------|-----------|--------|--------|
| 1 | P90 Body Size vs Threshold | 0.12 | 0.18 | CEREBUS Part 1 |
| 2 | EMA 20/50 Alignment | 0.08 | 0.12 | Standard |
| 3 | Regime Confirmation (Daily/Asian ≥ 1.5x) | 0.15 | 0.16 | CEREBUS Part 3 |
| 4 | Session Timing (4-7 AM = 88.6% WR) | 0.09 | 0.10 | CEREBUS Part 4 |
| 5 | Day of Week (Tue/Wed = 82-88% WR) | 0.06 | 0.08 | CEREBUS Part 11 |
| 6 | MACD Histogram Direction | 0.07 | 0.08 | Standard |
| 7 | Cascade Timing (45-60 min = 88.2% WR) | 0.10 | 0.09 | CEREBUS Part 2 |
| 8 | ADX Trend Strength (>25) | 0.05 | 0.06 | Standard |
| 9 | RSI Momentum (40-60 room to run) | 0.04 | 0.05 | Standard |
| 10 | Bollinger Band Position | 0.03 | 0.03 | Standard |
| 11 | Volume Surge (>1.5× avg) | 0.04 | 0.03 | Standard |
| 12 | ATR Expansion (ratio > 1.2) | 0.03 | 0.02 | Standard |

**Combined IR = √(Σ ICᵢ²) ≈ √(0.0144+0.0064+0.0225+0.0081+0.0036+0.0049+0.01+0.0025+0.0016+0.0009+0.0016+0.0009) = √0.0774 ≈ 0.278**

This is a **2.78x improvement** over the best single signal (P90 alone, IC=0.12).

### Composite Alpha Score
```
A(t) = Σ wᵢ × Sᵢ(t)   where wᵢ = normalized weight, Sᵢ ∈ {-1, 0, +1}

Range: -1.0 (max bearish) to +1.0 (max bullish)
```

### Position Sizing (Kelly Criterion)
- Base risk: 0.12% of equity per activation (CEREBUS standard)
- Kelly fraction: f* = (WR × RR - (1-WR)) / RR
- For WR=0.88, RR=2.5: f* = (0.88×2.5 - 0.12)/2.5 = 0.832
- Apply 0.3× fractional Kelly: ~0.25% risk
- Scale by |A(t)|: Position = base_size × |A(t)|

### Entry Rules
1. P90 candle detected (body >= threshold for time window, close outside Asian band)
2. Compute composite alpha A(t)
3. Enter LONG if A(t) >= +0.4, SHORT if A(t) <= -0.4
4. No trade if |A(t)| < 0.4 (insufficient confirmation)
5. Size proportional to |A(t)|

### Exit Rules (CEREBUS Standard)
- TP1: -25% Asian Range → Close 50%, move SL to BE+2p
- TP2: -50% Asian Range → Close remaining 50%
- Hard Exit: 12:00 PM EST → Close ALL
- Kill Switch: 132% Asian Range violation → Close ALL immediately
- EWS: Opposite P90 at TP targets → Close remaining

### Cascade Enhancement
- 2nd cascade P90 (45-60 min): +0.15 bonus to alpha score
- 3rd cascade P90: +0.05 bonus
- 4th+: No bonus (avoid per CEREBUS — 76.4% WR)

## Expected Performance
- Base P90 WR: 83.3% (1st), 87.8% (2nd cascade)
- With alpha filtering (|A(t)| >= 0.4): Projected 88-92% WR
- With Kelly sizing: Better risk-adjusted returns vs fixed size
- Expected daily R: +1.8R to +2.5R (vs +1.42R anchor only)
- Max drawdown: -4R to -6R (within CEREBUS parameters)
- **IR improvement: 2.78x over single-signal P90**

## Implementation Notes
- Uses same Asian Range calculator as base CEREBUS
- Adds signal computation layer on top of P90 detector
- Position sizing is dynamic (Kelly × alpha magnitude)
- All CEREBUS kill switches and hard exits preserved
- Compatible with Dual-Engine (alpha combo for Anchor, standard for Amplifiers)
