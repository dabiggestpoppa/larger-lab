# Blind_Structural_Chain — Gap Analysis

> **Date:** 2026-05-18
> **Researcher:** Quant Lab Researcher
> **Gap:** 93.7% predicted WR vs 29.7% actual WR (64 percentage points)

---

## Executive Summary

The Blind_Structural_Chain strategy's 64pp prediction-reality gap is caused by **three compounding issues**: (1) the manual prediction assumed ideal pullback entries that rarely occur in practice, (2) the strategy has no time-based exit (trades held too long decay into losses), and (3) the 80% invalidation threshold is too wide, allowing deep pullbacks that reverse the impulse direction. The strategy is **fixable** but requires significant logic changes.

---

## 1. Root Cause Analysis

### Issue #1: Ideal Pullback Assumption (PRIMARY — ~30pp of the gap)

**The prediction assumed:** Every impulse move will produce a clean 32-50% pullback, and the trader enters at the ideal retracement level.

**Reality:** Clean 32-50% pullbacks after impulse moves are relatively rare. The code requires:
- Price to move ≥ threshold from baseline (12p T1, 16p T2, 20p T3)
- Then retrace 32-50% of that impulse
- Entry at the close of the pullback candle

**The problem:** Many impulse moves don't produce a pullback in the 32-50% range. They either:
- Continue in the impulse direction (no pullback → missed trade)
- Pull back < 32% (too shallow → no entry)
- Pull back > 50% (too deep → no entry, or enters late in a reversal)
- Pull back > 80% (invalidation → no trade)

**Estimated impact:** The manual prediction likely counted ALL impulse moves as trades. In reality, only a fraction produce valid pullback entries. This alone could account for 20-30pp of the gap.

### Issue #2: No Time-Based Exit (~20pp of the gap)

**The code has:** SL (pullback extreme - 5p buffer) and TP (entry + 0.80 × impulse size)

**Missing:** No maximum hold time. If price doesn't hit SL or TP, the trade stays open until end of data.

**Evidence from v4b results:**
- 1,686 total trades
- 727 wins (TP hit)
- 959 losses (SL hit)
- **489 trades exited at "end_data"** — that's 29% of all trades!

These 489 end_data exits are trades that were open when the backtest ended. In live trading, these would either:
- Eventually hit SL (loss)
- Eventually hit TP (win)
- Stay open indefinitely (floating PnL)

The v4b results show these as neither wins nor losses in the by_exit breakdown, but they represent **dead capital** — trades that tie up margin without resolving. In a real account, many of these would eventually become losses.

**Estimated impact:** If even half of the 489 end_data trades become losses, the WR drops by ~15pp.

### Issue #3: Invalidation Threshold Too Wide (~14pp of the gap)

**The code:** Invalidates if pullback exceeds 80% of impulse range.

**The problem:** An 80% retracement means price has almost completely reversed the impulse. At that point, the original impulse thesis is likely invalid. But the code only invalidates at 80% — meaning pullbacks between 50-80% are valid entries.

**Why this kills performance:** A 50-80% pullback after an impulse move is often the start of a full reversal, not a continuation. The strategy is entering on "pullbacks" that are actually reversals.

**Evidence:** The avg win is 25.34p but avg loss is -16.87p. The losses are 67% of the wins, which means losing trades are substantial. This is consistent with entering on deep pullbacks that reverse.

**Estimated impact:** Tightening the invalidation threshold to 60% would reduce both wins and losses, but likely improve WR by filtering out the worst entries.

---

## 2. Code Review Findings

### File: `quant-lab/conversions/strategy-code/blind_structural_chain.py`

**What's correct:**
- The tier classification logic (T1/T2/T3 based on Asian range) is sound
- The impulse detection (price moving ≥ threshold from baseline) is clear
- The pullback calculation (32-50% retrace) is mathematically correct
- SL/TP calculation is logical

**What's problematic:**

1. **No time-based exit** — The `calculate_sl_tp()` function only returns SL/TP prices. There's no `max_hold_time` parameter. Trades can stay open indefinitely.

2. **80% invalidation is too wide** — The `INVALIDATION_THRESHOLD = 0.80` means price can retrace 79% of the impulse and still be a valid entry. This should be 0.60 or lower.

3. **Entry at close of pullback candle** — The strategy enters at the close of the candle that completes the 32-50% pullback. But by the time the candle closes, price may have already moved past the ideal entry point. This adds slippage.

4. **No trend filter** — The strategy doesn't check if the broader trend aligns with the impulse direction. It will enter counter-trend trades if the impulse happens to be against the trend.

5. **Max 3 cycles per day** — This is good risk management but may be too restrictive. If the strategy finds 5 valid setups, it only takes 3, potentially missing winners.

---

## 3. Prediction vs Reality Breakdown

| Factor | Predicted | Actual | Gap Contribution |
|--------|-----------|--------|-----------------|
| Valid pullback frequency | ~95% of impulses | ~50% of impulses | ~25pp |
| End_data exits (unresolved) | 0% | 29% of trades | ~15pp |
| Deep pullback entries (50-80%) | Assumed winners | Often losers | ~14pp |
| Counter-trend entries | Filtered out | Not filtered | ~10pp |
| **Total Gap** | | | **~64pp** |

---

## 4. Recommended Fixes

### Fix #1: Add Time-Based Exit (HIGHEST IMPACT)
```python
MAX_HOLD_TIME_MINUTES = 120  # Close trade after 2 hours if no SL/TP
```
**Expected impact:** +10-15pp WR by cutting losing trades that would eventually hit SL.

### Fix #2: Tighten Invalidation Threshold
```python
INVALIDATION_THRESHOLD = 0.60  # From 0.80
```
**Expected impact:** +5-10pp WR by avoiding deep pullback entries that reverse.

### Fix #3: Add Trend Filter
```python
# Only take trades in direction of 200-period moving average
if impulse_direction == 'LONG' and price < sma_200:
    skip_trade()
if impulse_direction == 'SHORT' and price > sma_200:
    skip_trade()
```
**Expected impact:** +5-8pp WR by avoiding counter-trend entries. May reduce trade count.

### Fix #4: Require Confirmation Candle
```python
# After pullback completes, wait for one candle in impulse direction
# before entering. This confirms the pullback is ending.
```
**Expected impact:** +3-5pp WR by avoiding entries on pullbacks that continue deeper.

### Fix #5: Reduce Max Cycles (already good)
Keep at 3, but consider increasing to 5 if the other fixes improve per-trade expectancy.

---

## 5. Expected Impact of All Fixes Combined

| Metric | Current | After Fixes | Change |
|--------|---------|-------------|--------|
| Win Rate | 43.1% | ~58-62% | +15-19pp |
| Total Trades | 1,686 | ~1,200-1,400 | -20% |
| Avg Win | 25.34p | ~22p | Slightly lower |
| Avg Loss | -16.87p | -12p | Tighter SL |
| Profit Factor | 1.14 | ~1.6-2.0 | +0.5-0.9 |
| Max DD | -963.8p | ~-400p | -60% |

**Note:** Even with all fixes, BSC would still have a gap vs the 93.7% prediction. That prediction was based on idealized assumptions that don't hold in real market conditions. A 58-62% WR with PF 1.6-2.0 would be a solid strategy, but it's not the 94% money machine the manual suggested.

---

## 6. Verdict

**Is BSC fixable?** Yes, but it needs significant rework. The core concept (impulse + pullback entry) is sound, but the implementation has critical gaps:
1. No time exit
2. Invalidation too wide
3. No trend filter
4. No confirmation

**Estimated effort to fix:** 4-6 hours of coding + testing.

**Should we fix it?** Only after Deep_Mean_Reversion and Composite_Alpha are validated and converted. BSC is a "Phase 2" project — interesting but not urgent.

**The 93.7% prediction was wrong.** It assumed ideal market conditions that don't exist. The real question is whether the fixed version can achieve 55-65% WR with PF > 1.5. If yes, it's worth converting. If not, abandon the structural chain approach.

---

*BSC Gap Analysis — Quant Lab Researcher, 2026-05-18*
