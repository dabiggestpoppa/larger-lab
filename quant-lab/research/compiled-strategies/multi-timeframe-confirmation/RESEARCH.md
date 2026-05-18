# Strategy: Multi-Timeframe Confirmation

## Sources
- Institutional best practice (widely documented across trading literature)
- arXiv:2412.20138 — TradingAgents framework (multi-analyst approach)
- arXiv:2505.03659 — Meta-learning mixture of strategies (multi-horizon)

## Core Logic
Confirm signals across multiple timeframes before entering a trade. Higher timeframe defines the bias, lower timeframe defines the entry.

### Timeframe Hierarchy
| Role | Timeframe | Purpose |
|------|-----------|---------|
| **Strategic bias** | Daily (D1) | Overall trend direction |
| **Tactical setup** | 4-Hour (H4) | Intermediate structure, S/R levels |
| **Entry trigger** | 1-Hour (H1) or 30-Min (M30) | Precise entry timing |
| **Execution** | 5-Min (M5) | Fine-tuned entry, stop placement |

### Entry Rules
**Long entry requires ALL of:**
1. D1: Price > EMA 50 (strategic bullish bias)
2. D1: EMA 20 > EMA 50 (trend alignment)
3. H4: RSI(14) between 40-60 (not overbought, room to run)
4. H4: Price pulled back to EMA 20 (value entry in trend)
5. H1: RSI(14) crossed above 30 (momentum turning up)
6. H1: MACD histogram turning positive

**Short entry:** Mirror of above (inverted conditions)

### Exit Rules
- **Stop loss:** Below recent H4 swing low (long) or above swing high (short)
- **Take profit:** 2× risk (R:R = 1:2) or next H4 resistance/support
- **Trailing stop:** Move to breakeven after 1× risk profit
- **Time-based:** Close if no follow-through within 5 bars on H1

## Expected Performance
- Higher win rate than single-timeframe (estimated 55-60%)
- Better R:R due to precise lower-TF entries
- Fewer false breakouts (higher TF filter eliminates noise)
- Works best in trending markets; may underperform in choppy/ranging conditions

## Implementation Approach
1. Compute indicators on D1, H4, H1 simultaneously
2. Generate composite score: +1 for each bullish condition met, -1 for each bearish
3. Enter when composite score ≥ +5 (strong long) or ≤ -5 (strong short)
4. Scale position size with score magnitude
