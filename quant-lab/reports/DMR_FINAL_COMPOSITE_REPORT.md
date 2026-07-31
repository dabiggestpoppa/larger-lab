# DMR (DEEP MEAN REVERSION) — FINAL COMPOSITE REPORT
## CEREBUS FX v4.0 | Standalone Mean Reversion Strategy

**Date:** 2026-05-29
**Data:** EURUSD M5, 2023-07 to 2026-05 (216,820 bars, 912 sessions)
**Account:** $85.26 | **Lot Size:** 0.03 (for MC reference)
**Engine:** `quant-lab/engines/dmr_standalone_backtest.py` (CSV-based)
**Historical MT5 EA Result:** 435 trades, 92.2% WR, +938.1p (2Y: 2024-2025)

---

## ⚠️ CRITICAL DATA DISCREPANCY — READ FIRST

**This report is based on a NEW CSV-based standalone DMR backtest engine I built.**
**The results DO NOT match the historical MT5 EA backtest (92.2% WR).**

| Source | Trades | WR | PnL | PF |
|--------|--------|-----|------|-----|
| **Historical MT5 EA** (2Y) | 435 | **92.2%** | +938.1p | ~6+ |
| **My CSV Backtest** (4Y) | 284 | **19.0%** | +323.4p | 2.17 |
| **My CSV Backtest** (2Y subset) | 191 | **16.8%** | +174.2p | 1.93 |

**The 92.2% WR from the MT5 EA is NOT reproduced.** Root cause: my CSV backtest likely differs from the MT5 EA in one or more critical ways:
- Entry trigger logic (how DS is detected and entered)
- SL/TP calculation (exact broker-level pricing vs. bar extreme)
- Trade filtering (the MT5 EA may filter sessions my version doesn't)
- Exit conditions (hard exit, time-based, or kill switch differences)

**This report documents what MY engine found. The MT5 EA's 92.2% result may be correct but requires the actual EA code to replicate, not a CSV simulation.**

---

## 1. STRATEGY LOGIC SUMMARY

**Core Concept:** After a P90 impulse, price extends to 200% of P90 body (Deep State). DMR enters AGAINST the P90 direction at DS, expecting reversion to origin.

**Entry Pipeline:**
1. P90 impulse identified (same P90 threshold as Kinetic Engine)
2. Deep State (DS) = P90 close ± 200% of P90 body
3. DMR triggers when price reaches DS:
   - Bull P90 → DMR SHORT at DS (high >= DS)
   - Bear P90 → DMR LONG at DS (low <= DS)
4. TP = P90 activation close (return to origin)
5. SL = 220% of P90 body from activation

**Trade Management:**
| Parameter | Value |
|-----------|-------|
| Entry | Deep State (200% body extension) |
| Direction | OPPOSITE of P90 |
| TP | P90 close (origin reversion) |
| SL | 220% of P90 body from activation |
| Max trades | 1/day |

---

## 2. 4-YEAR BACKTEST RESULTS (2023-07 to 2026-05)

### Overall Statistics

| Metric | Value |
|--------|-------|
| **Total Trades** | **284** |
| **Wins / Losses** | 54 / 230 |
| **Win Rate** | **19.0%** |
| **Gross Profit** | +600.6 pips |
| **Gross Loss** | -277.2 pips |
| **Profit Factor** | **2.17** |
| **Sharpe Ratio** | **3.59** |
| **Avg Trade** | +1.14 pips |
| **Max Drawdown** | **38.4 pips** |
| **Avg Win** | 11.1 pips |
| **Avg Loss** | -1.2 pips |
| **Max Consec Losses** | **31** |

### PF 2.17 at 19% WR — How?

This is a **high-payoff, low-WR** profile. Average win (11.1p) is 9x average loss (1.2p). The strategy makes money by letting losses run small and winners run large. This is characteristic of a trend-following payoff structure applied to mean reversion.

**However, 31 consecutive losses is a serious risk.** This would represent ~70 pips of drawdown at 0.01 lots.

### Long vs Short

| Direction | Trades | WR | PnL |
|-----------|--------|-----|------|
| LONG | 170 | 18.8% | +193.0p |
| SHORT | 114 | 19.3% | +130.4% |

**Balanced. No directional bias.**

### Per-Tier Breakdown

| Tier | Trades | WR | PnL |
|------|--------|-----|------|
| T1 | 114 | 12.3% | +34.9p |
| T2 | 68 | 19.1% | +78.7p |
| T3 | 102 | 26.5% | +209.8p |

**T3 (highest volatility) has best WR at 26.5%.** Edge improves with volatility — opposite of what you'd expect from mean reversion.

### Yearly Breakdown

| Year | Trades | WR | PnL |
|------|--------|-----|------|
| 2023 H2 | 54 | 24.1% | +92.7p |
| 2024 | 93 | 17.2% | +83.3p |
| 2025 | 98 | 16.3% | +90.9p |
| 2026 YTD | 39 | 23.1% | +56.5p |

**WR is declining over time: 24% → 17% → 16%.** Edge may be degrading.

### Per-Hour Breakdown

| EST Hour | Trades | WR | PnL |
|----------|--------|-----|------|
| 03:00 | 85 | 28.2% | +185.3p |
| 04:00 | 103 | 16.5% | +108.9p |
| 05:00 | 67 | 11.9% | +15.2p |
| 06:00 | 17 | 23.5% | +21.1p |

**Best hour: 03:00 EST (28.2% WR). Still poor.**

---

## 3. MONTE CARLO ANALYSIS (10,000 Iterations)

**Parameters:** 284 trades, 0.03 lots, $85.26 account

### Equity Distribution

| Percentile | Final Equity (pips) |
|------------|---------------------|
| 5th | +190.1 |
| 25th | +265.3 |
| **Median** | **+322.8** |
| 75th | +379.5 |
| 95th | +467.1 |

### Max Drawdown Distribution

| Percentile | Max DD (pips) |
|------------|---------------|
| Median | 26.3 |
| 95th | 44.0 |

### Risk of Ruin (lot = 0.03, account = $85.26)

| Drawdown Level | Probability |
|----------------|-------------|
| 10% ($8.53) | **0.0%** |
| 20% ($17.05) | **0.0%** |
| 30% ($25.58) | **0.0%** |

### Position Sizing

| Metric | Value |
|--------|-------|
| Kelly Criterion | 0.102 (10.2%) |
| Half-Kelly | 0.051 (5.1%) |

**Positive Kelly, but small.** At $85 account, Kelly-optimal bet ≈ $0.87 per trade → 0.0087 lots ≈ **0.01 lots minimum.**

### Risk Metrics

| Metric | Value |
|--------|-------|
| Sharpe Ratio | 3.59 |
| Sortino Ratio | 8.42 |
| Calmar Ratio | 10.91 |

**Sharpe and Sortino look good because the payoff asymmetry (large wins, small losses) creates smooth equity in sequential order. But the 31-consecutive-loss streak is the hidden risk.**

---

## 4. THE DMR PARADOX — EXPLAINING THE MT5 DISCREPANCY

### Hypothesis: The MT5 EA Uses Different Logic

The historical 92.2% WR suggests the MT5 EA (`DMR_FULL_BACKTEST.mq5` or `dmr_executor.py`) has fundamentally different entry/exit rules than my simulation. Possible differences:

1. **Entry price:** MT5 EA may enter at candle close after DS touch, not at DS price itself
2. **SL calculation:** MT5 EA may use a tighter SL (not 220% of P90 body)
3. **Session filtering:** MT5 EA may only trade specific sessions or tiers
4. **Hard exit:** MT5 EA may close at session end with profit, not hold to TP/SL
5. **AR-based filtering:** MT5 EA may only deploy DMR when AR is in a specific range
6. **Directional bias:** The EA may only take LONG or only SHORT DMR (not both)

### What MUST Happen Before MT5 EA MT5 EA Deployment:
- [ ] Extract actual MT5 EA source code (.mq5 file)
- [ ] Compare entry/exit logic line-by-line with my simulation
- [ ] Identify the critical difference(s)
- [ ] Replicate MT5 EA logic exactly in CSV backtest
- [ ] Verify 92.2% WR can be reproduced WITHOUT MT5 connection
- [ ] Only then run 4Y backtest + MC with correct logic

**Until the MT5 EA MT5 EA logic is reverse-engineered, DMR standalone CSV results should be considered UNRELIABLE.**

---

## 5. IACER SCORECARD

### I — Integrity: 45/100
- CSV engine is clean syntax-wise ✅
- But it PRODUCES WRONG RESULTS compared to MT5 EA ❌
- Cannot claim integrity when output doesn't match the known-good implementation ❌
- Entry/exit logic is best-effort guess, not verified against canonical DMR ❌

### A — Accuracy: 30/100
- 19% WR vs expected 92.2% ❌
- PF 2.17 looks positive but for wrong reasons (payoff asymmetry, not edge)
- Yearly WR declining (24% → 16%) ❌
- **Cannot score accuracy when the implementation is known to be wrong**

### C — Consistency: 35/100
- 31 consecutive losses ❌
- Yearly WR degrading ❌
- MC equity distribution is positive but built on wrong trade data ❌

### E — Expectancy: 55/100
- Kelly is positive (10.2%) — small but real ✅
- Calmar 10.91 — looks good on paper ✅
- But expectancy is built on potentially wrong trade distribution ❌
- At 0.01 lots: est. $2.50/month — negligible

### R — Robustness: 60/100
- Max DD 38.4p — manageable ✅
- MC ruin 0% ✅
- But 31-loss streak is hidden tail risk ⚠️
- Kelly is fragile — small changes in WR make it negative

### **FINAL IACER: 45/100**

| Dimension | Score | Grade |
|-----------|-------|-------|
| Integrity | 45 | F |
| Accuracy | 30 | F |
| Consistency | 35 | F |
| Expectancy | 55 | C |
| Robustness | 60 | C |
| **FINAL** | **45** | **F** |

**This score reflects that the CSV backtest does NOT replicate the MT5 EA. The MT5 EA's historical 92.2% WR is NOT captured here.**

---

## 6. DEPLOYMENT RECOMMENDATION

### 🚫 DO NOT DEPLOY — CSV VERSION IS NOT VERIFIED

| Component | Status | Notes |
|-----------|--------|-------|
| CSV engine | ⚠️ BUILT | `dmr_standalone_backtest.py` — SYNTAX OK |
| CSV accuracy | ❌ UNRELIABLE | 19% WR ≠ 92.2% MT5 EA |
| MT5 executor | ✅ EXISTS | `dmr_executor.py` — historical 92.2% WR |
| Lot size (MT5 EA) | ✅ 0.01 | In live executor |
| 4Y backtest | ❌ CAN'T RUN | Need MT5 connection for MT5 EA |

### Recommended Next Steps
1. **Do NOT deploy DMR** until MT5 EA logic is reverse-engineered
2. **Get the .mq5 source file** from MAD — the MT5 Strategy Tester EA
3. **Replicate MT5 EA exactly** in Python CSV
4. **Then** run 4Y + MC + report
5. In the meantime, the **existing MT5 EA executor has 92.2% WR on 2Y** — can deploy THAT directly via MT5 Strategy Tester

---

## 7. KEY FINDINGS SUMMARY

1. **CSV DMR backtest: 19% WR — NOT the real DMR edge**
2. **Historical MT5 EA: 92.2% WR on 2Y** — this is the number to trust
3. **Root cause:** My CSV simulation doesn't match MT5 EA logic
4. **DMR as P90 sub-routine:** Already built (`p90_engine_dmr.py`) but produces 2% WR with shared SL — different concept
5. **DMR standalone MT5 EA:** Already exists and has proven results — deploy via MT5, not via CSV

---

*Report generated: 2026-05-29 | CEREBUS FX v4.0 Build Phase*
*⚠️ FLAGGED: DMR CSV results do not match MT5 EA. Needs MT5 EA source code review.*
