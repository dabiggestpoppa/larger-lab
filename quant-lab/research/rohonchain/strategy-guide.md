# RohOnChain Trading Research — Compiled Summary
> Source: @RohOnChain on X/Twitter + web search synthesis
> Compiled: 2026-05-17 by OWL (OC2) for Algo Agent

## Overview
Roan (@RohOnChain) describes a **systematic, quant-style prediction market desk** focused on:
- Polymarket (on Polygon)
- Cross-venue prediction markets (Betfair, Opinion on BNB, Space on Solana)
- On-chain data, mempool analysis, websocket feeds

Key principle: **Edge = better-calibrated probabilities**, not hot takes.

## The Signal Stack (Multi-Layer)

### Layer 1: Market Microstructure
- Order book depth, bid-ask spreads, trade aggression
- Volume imbalance detection
- Sudden spread widening = informed flow
- Guides execution style (aggressive vs passive)

### Layer 2: On-Chain Data (Polygon/Polymarket)
- Dedicated nodes + RPC (Alchemy, QuickNode)
- Mempool transaction monitoring
- Mint/burn of market shares
- Whale wallet tracking
- **Resolution edge**: 2-4 second window between mempool appearance and market lock

### Layer 3: Cross-Venue Divergence
- Polymarket vs Opinion (BNB) vs Space (Solana) vs Betfair
- Buy underpriced venue, sell overpriced venue
- Profit from spread convergence (market-neutral)
- Manage: execution lag, bridge risk, regulatory risk

### Layer 4: Statistical/Historical Signals
- Calibration drift / longshot bias
- Systematically short markets priced <15% → positive EV
- Reported: 2.8% avg return/trade, 67% WR, Sharpe 2.4 over 12 months

## Alpha Combination Framework
- N signals with M periods of returns each
- Standardize/normalize signals
- Estimate IC (Information Coefficient) per signal
- Estimate covariance matrix between signals
- Penalize noise, shrink covariances
- Solve for optimal weights
- Combined alpha → trade direction + size + risk budget

## Trade Lifecycle (Example: Bitcoin $100K prediction)

1. **Market ID**: Scan all live markets
2. **Fair Value**: Binary option pricing (Black-Scholes adapted)
   - Model says 0.42, market at 0.35 → 7pp edge
3. **Position Sizing**: Kelly criterion
   - f* = (bp - q) / b, empirically adjusted
   - Example: Kelly 0.24 → 35% haircut → 0.156 × $50K = $7,800
4. **Execution**: VWAP-style optimization
   - Split into small slices across levels
   - Target: 80% within 0.5% of initial price over 15 min
5. **Risk Management**:
   - 30-day 95% VaR threshold
   - VPIN (Volume-synchronized Probability of Informed Trading)
   - Auto-halt if drawdown hits VaR
6. **Exit Logic**: Theta-based time decay
   - Exit if edge < 3% or time remaining < 48hrs
   - Example outcome: $1,092 PnL on $7,800 in 8 hours (14% intraday)

## Key Concepts to Adapt for Forex
1. **Alpha combination** — multiple weak signals → one strong composite
2. **Market microstructure** — volume imbalance, spread analysis
3. **Cross-venue arbitrage** — same underlying, different venues
4. **Kelly sizing** — optimal position sizing with fractional Kelly
5. **VWAP execution** — minimize market impact
6. **Risk budgets** — VaR, VPIN, drawdown limits
7. **Longshot bias** — systematic mispricing at extremes

## Relevant ArXiv Papers
- "AI-Powered Energy Algorithmic Trading" (2407.19858): HMM + Neural Networks + Black-Litterman
  - 83% return, Sharpe 0.77 during COVID (2019-2022)
  - Uses log returns for optimal state selection
  - Dual-model alpha system
- "Deep RL for Forex Trading with Multi-Agent Async Distribution" (May 2024)
- "Event-Driven LSTM For Forex Price Prediction" (Feb 2021)
- "GA-MSSR: Genetic Algorithm Maximizing Sharpe and Sterling Ratio" (2024)
- "Applying News Sentiment for Forex Trading Signals" (Mar 2024)

## Strategy Ideas for EUR/USD
1. **HMM Regime-Switching + LSTM Ensemble** (from 2407.19858)
   - Use HMM to detect market regime
   - Different LSTM models per regime
   - Combine with Black-Litterman for position sizing
   - Target: >30% return, <10% DD

2. **Alpha Combination Strategy**
   - Collect 5-7 diverse signals (momentum, mean reversion, sentiment, etc.)
   - Compute IC and covariance
   - Optimal weighting → composite alpha
   - Trade when composite > threshold

3. **Longshot Bias / Calibration Strategy**
   - Identify when EUR/USD moves reach statistical extremes
   - Fade the extreme move with Kelly-sized positions
   - Mean reversion at 1-3 day horizon

4. **Multi-Agent RL Strategy**
   - Multiple RL agents for different time horizons
   - Async distribution for parallel decision-making
   - Risk-adjusted reward function

5. **Cross-Venue FX Arbitrage**
   - Compare EUR/USD pricing across brokers/data feeds
   - Fade prices that diverge from consensus
   - Requires fast execution but scales well
