# RohOnChain — "The Math Behind Combining 50 Weak Signals Into One Winning Trade"
> Source: @RohOnChain (Roan), April 6, 2026
> URL: https://x.com/RohOnChain/status/2041180375838498950
> Views: 2.7M | Likes: 1,529 | Bookmarks: 6,331
> Also: "Inside a Prediction Market Hedge Fund" — https://x.com/RohOnChain/status/2029998336837890193

## Key Quote (From Head of Quantitative Research, 20 years systematic trading)
> "You are trying to find the one signal that is always right. That person does not exist. The desk that wins is the one that correctly combines the signals that are each slightly right."

## The Fundamental Law of Active Management
**IR = IC × √N**

Where:
- **IR** = Information Ratio (risk-adjusted edge of full signal stack)
- **IC** = Information Coefficient (correlation between signal prediction and market outcome)
- **N** = Number of independent signals

### Example from the article:
- 50 signals, each with IC of 0.05 → IR = 0.05 × √50 = **0.354**
- 1 signal with IC of 0.10 → IR = **0.10**
- The 50-signal system is **3.5x more powerful** despite each signal being half as strong

### Key Insight:
- Best institutional signals have IC between 0.05 and 0.15
- Most are wrong the vast majority of the time — this is NORMAL
- Combining independent signals is the entire reason hedge funds employ hundreds of researchers

## The 11-Step Alpha Combination Procedure (Institutional Framework)
1. Construct returns per signal over time
2. Standardize/normalize signals
3. Estimate each signal's IC (predictive power)
4. Estimate covariance matrix between signals (shared variance)
5. Penalize noise / overfit; shrink covariances if needed
6. Solve for optimal weights that reward independent predictive contribution
7. Downweight collinear / redundant signals
8. Convert combined alpha into trade direction
9. Determine position size (risk-budget allocation)
10. Apply execution optimization (VWAP, slicing)
11. Monitor and rebalance weights as market conditions change

## What Qualifies as a Signal
- Any measurable input with positive IC (even 0.01 is valuable)
- Must be genuinely INDEPENDENT from other signals
- Sources: price action, volume, order flow, sentiment, on-chain, cross-venue, macro
- Weak signals are NOT noise — they're the raw material of institutional edge

## Application to CEREBUS Strategies
CEREBUS already has multiple signals that could be combined:
1. P90 candle (momentum signal)
2. Asian Range classification (regime signal)
3. Cascade count (exhaustion signal)
4. Stall Zone touch (mean reversion signal)
5. Failure Repair state (structure signal)
6. Regime Shift confirmation (trend signal)
7. Overfilled filter (risk signal)

**These 7 signals, properly combined via alpha combination, could be significantly more powerful than any single one alone.**

## Related Article: "Inside a Prediction Market Hedge Fund"
Roan works at a liquid hedge fund as a quantitative backend developer. Key insights:
- Institutions run systematic strategies across thousands of markets simultaneously
- Edge comes from structural inefficiencies, not opinions
- Team structure: data ingestion → probability modeling → execution → risk controls
- Prediction market sector: $3B → $10B projected by 2030
- SIG, Jane Street, Jump Trading all building dedicated prediction market desks
- Same framework applies to forex: systematic signal combination > single-signal trading
