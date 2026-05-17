# 🎯 P90 Strategy Implementation Guide

> **Version:** 1.0 | **Date:** 2026-05-17
> **Source:** CEREBUS Manual v4.0 | EUR/USD M5 | 315,000+ Candles
> **Classification:** PROPRIETARY — Educational purposes only
> **MAD Directive (2026-05-17):** This is a MOMENTUM strategy, NOT mean reversion. The -25 and -50 levels are extension targets of the daily distribution (Asian range). Trades start bi-directionally until the bias filter confirms direction, then ride momentum to distribution tails. Bi-directional entry exists to keep logic simple — one measurement, one range — preventing agents from overcomplicating the entry logic.

---

## 1. P90 Candle Detection Algorithm

### Exact Rules
An M5 candle qualifies as P90 when ALL conditions are met:

1. **Time Window:** Candle closes between 2:00 AM – 11:00 AM EST
2. **Body Size:** |Close – Open| >= threshold for its time sub-window
3. **Close Outside Asian Band:** Close > Asian High (bullish) OR Close < Asian Low (bearish)

### Body-Size Thresholds

| EST Window | Threshold | Session Context |
|------------|-----------|-----------------|
| 2:00 – 4:00 AM | >= 4.1 pips | Early London |
| 4:00 – 6:00 AM | >= 4.6 pips | London ramping |
| 6:00 – 8:00 AM | >= 4.6 pips | London-NY overlap |
| 8:00 – 10:00 AM | >= 5.9 pips | NY open |
| 10:00 – 11:00 AM | >= 6.2 pips | Late window |

### Critical Rules
- **CLOSES ONLY** — wicks do not count
- **One per direction per window** — cascades are same-direction P90s
- **Opposite-direction P90s ignored** unless full regime reversal confirmed
- **NOT valid after 11:00 AM EST**

### Pseudocode
```
function is_p90(candle, asian_high, asian_low):
    if candle.close_time not in [2AM-11AM EST]: return False
    body = abs(candle.close - candle.open)
    threshold = get_threshold(candle.close_time)  # per table above
    if body < threshold: return False
    if candle.close > asian_high: return LONG_P90
    if candle.close < asian_low: return SHORT_P90
    return False
```

---

## 2. Cascade Activation Flow Chart

```
[IDLE]
  │
  ▼
[2:00 AM EST] ── Start Scanning
  │
  ▼
[P90 Detected?] ── No ──► Keep Scanning
  │
  Yes (1st P90 = Bias Setter)
  │
  ▼
[INITIAL P90] ── Signal 1: Enter 40% | SL: 80% of P90 body | TP: -25% Asian
  │             ── Signal 2: Enter 40% | SL: 1.5x P90 body | TP: -25% Asian
  │             (Both fire simultaneously at P90 close = 80% initial exposure)
  │             Direction: Set for session
  │
  ├──► [45-Min Timer Start]
  │         │
  │         ▼
  │    [45 min elapsed?] ── No ──► Wait
  │         │
  │         Yes
  │         │
  │         ▼
  │    [Resolution +8p?] ── No ──► Skip
  │         │
  │         Yes
  │         │
  │         ▼
  │    [45-MIN ADD] ── Enter 30% size
  │                      Boundary: Breakeven
  │
  ├──► [Cascade Watch: 30-90 min from Initial]
  │         │
  │         ▼
  │    [New P90 same direction?] ── No ──► Keep Watching
  │         │
  │         Yes
  │         │
  │         ▼
  │    [CASCADE P90 #1] ── Enter 20% size
  │    (Optimal: 45-60 min)   Boundary: 168% of THIS P90 body
  │         │
  │         ▼
  │    [CASCADE P90 #2] ── Enter 10% size
  │                          Boundary: 168% of THIS P90 body
  │
  ▼
[11:00 AM EST] ── No new activations
  │
  ▼
[12:00 PM EST] ── HARD EXIT ── Close ALL positions
```

---

## 3. 45-Minute Add Rules

| Parameter | Value |
|-----------|-------|
| **Trigger** | 45 min after Initial P90 AND resolution output >= +8 pips |
| **Size** | 30% of total risk |
| **Boundary** | Breakeven (Signal 1 entry level) |
| **Target** | -50% Asian Range |
| **Max per session** | 1 |

**Key Insight:** The 45-Min Add and Cascade P90 are **complementary**. When both trigger, combined win rate = **93.4%**.

---

## 4. Tier System Decision Tree

```
[Measure Asian Range: 00:00-08:00 UTC]
  │
  ├──► Range < 20 pips ──► T1 (GOLD)
  │     ├── Size: 100%
  │     ├── Max Cascades: 3
  │     ├── Amplifiers: Up to 2
  │     ├── Overfilled (>40p by 9AM): Anchor only, 50% size
  │     └── Expected Daily Range: ~72 pips
  │
  ├──► Range 20-30 pips ──► T2 (STANDARD)
  │     ├── Size: 75%
  │     ├── Max Cascades: 3
  │     ├── Amplifiers: Max 1
  │     ├── Overfilled (>40p by 9AM): STAND DOWN
  │     └── Expected Daily Range: ~58 pips
  │
  ├──► Range 30-45 pips ──► T3 (CAUTION)
  │     ├── Size: 50%
  │     ├── Max Cascades: 0 (NO cascades)
  │     ├── Amplifiers: NONE
  │     ├── Protocol: Model 2 (2h confirmation after break)
  │     ├── Overfilled (>40p by 9AM): STAND DOWN
  │     └── Expected Daily Range: ~48 pips
  │
  └──► Range > 45 pips ──► NO-GO
        └── SKIP DAY — Do not trade
```

---

## 5. Position Sizing Calculator

### Per-Activation Risk Model
| Parameter | Value |
|-----------|-------|
| Risk per activation | 0.12% of equity |
| Max concurrent risk | 0.36% (3 signals) |
| Daily hard stop | 0.40% of equity |

### Size Allocation Table (from CEREBUS Manual v4.0)

**Two signals fire simultaneously at P90 close:**

| Signal | Timing | Size % | $ Risk (on $10k) | Boundary Method | Target |
|--------|--------|--------|-------------------|-----------------|--------|
| Signal 1 (Initial) | P90 Close | 40% | $4.00 | 80% of P90 body | -25% Asian |
| Signal 2 (Simultaneous) | P90 Close | 40% | $4.00 | 1.5x P90 body | -25% Asian |
| Signal 3 (45-Min Add) | +45 min | 30% | $3.00 | Breakeven (Signal 1) | -50% Asian |
| Cascade 1 (2nd P90) | 30-90 min | 20% | $2.40 | 168% of THIS P90 body | -50% Asian |
| Cascade 2 (3rd P90) | 60-90 min | 10% | $1.20 | 168% of THIS P90 body | -50% Asian |
| **TOTAL** | — | **100%** | **$10.60 (0.106%)** | Mixed | — |

**Note:** Signal 1 + Signal 2 activate together at P90 close (80% total initial exposure). When ONLY 45-Min triggers: split 50/50. When ONLY Cascade triggers: split 50/50. When BOTH trigger: 40/30/20/10 across all 4 activation types (combined WR: 93.4%).

**Max cascades: 3 (4th+ = 76.4% WR → AVOID). Max activations per session: 5.**

### Tier Multiplier
| Tier | Multiplier | Effective Risk ($10k) |
|------|-----------|----------------------|
| T1 | 1.00x | $10.60 |
| T2 | 0.75x | $7.95 |
| T3 | 0.50x | $5.30 |

### Units Calculation
```
Units = $Risk / (Boundary_Distance × Pip_Value)
Example: $4.00 / (3.4 pips × $0.10) = 11,764 units
```

---

## 6. Risk Management Rules

### Kill Switches (Immediate Exit ALL)
| Condition | Action |
|-----------|--------|
| 132% Kill-Switch State | Price violates 132% of Asian Range → Close ALL |
| M5 close back inside Asian band | Exit immediately (81.2% rule) |
| Daily loss hits 0.40% | Close ALL, no more activations |

### Exit Management
| Target | Action |
|--------|--------|
| TP1: -25% Asian Range | Close 50%, move boundary to BE+2p |
| TP2: -50% Asian Range | Close remaining core |
| Hard Exit: 12:00 PM EST | Close ALL — non-negotiable |

### Session Filters
| Filter | Rule |
|--------|------|
| High-impact news (NFP, CPI, FOMC) within 4h | SKIP DAY |
| Monday | Reduce size 25% |
| Friday after 10 AM | Reduce size 50% |
| Overfilled (>40p by 9AM) | T1: Anchor 50% / T2/T3: STAND DOWN |

---

## 7. Common Pitfalls & How to Avoid Them

| Pitfall | Why It Happens | Solution |
|---------|---------------|----------|
| **Counting wicks as P90** | Large wick looks like breakout | Only count CLOSES outside Asian band |
| **Taking 4th+ cascade** | Greed — "one more" | Hard limit: max 3 cascades. Resolution exhausted. |
| **Ignoring tier classification** | Excitement overrode filter | Always measure Asian Range FIRST. >45p = NO-GO. |
| **Holding past 12 PM** | Hoping for more pips | 12:00 PM hard exit. 82% of resolution is done. |
| **Overfilled day trading** | Didn't check 9 AM range | If >40p by 9 AM: T2/T3 = stand down. |
| **Opposite P90 reversal** | Mistaking cascade EWS for reversal | Opposite P90 = trim/exit, NOT reverse (64.8% WR < 85% standard) |
| **Batch config changes** | Trying to optimize multiple params | One change at a time. Test. Then next. |
| **Trading T3 with amplifiers** | Forgetting T3 = pure anchor | T3: NO amplifiers under any circumstances. |

---

## 8. Backtest Validation Checklist

Before deploying any P90 strategy module, verify:

- [ ] **Asian Range Calculation:** 00:00-08:00 UTC window, correct High/Low measurement
- [ ] **P90 Detection:** Body-only measurement, close-outside-band check, time-window thresholds
- [ ] **Tier Classification:** T1/T2/T3/NO-GO correctly assigned per session
- [ ] **Cascade Logic:** Same direction, 30-90 min window, max 3, 168% boundary
- [ ] **45-Min Add:** Time-based trigger + 8-pip extension condition
- [ ] **Position Sizing:** 40/30/20/10 split, tier multiplier applied
- [ ] **Kill Switch:** 132% Asian Range violation detection
- [ ] **Hard Exit:** 12:00 PM EST closes all positions
- [ ] **Overfilled Filter:** 9 AM checkpoint, >40p range check
- [ ] **News Filter:** High-impact event detection within 4-hour window
- [ ] **Day-of-Week Adjustments:** Monday -25%, Friday after 10AM -50%
- [ ] **Minimum Sample:** At least 20 activations before evaluating win rate
- [ ] **Target WR:** Must exceed 80% over 20-activation sample or pause & recalibrate

---

*Generated by Quant Lab Researcher | 2026-05-17 | For educational purposes only. Test all strategies in simulation before live deployment.*
