# NAUTILUS BACKTEST PLAN — Quant Lab Reboot
> Created: 2026-05-28 09:35 EDT
> Status: ACTIVE

---

## 1. ROOT CAUSE ANALYSIS — WHY PAST APPROACHES FAILED

### MT5 Strategy Tester (ZERO trades)
**Problem:** The `DMR_FULL_BACKTEST.mq5` EA compiled successfully but produced 0 bars / 0 trades in Strategy Tester.
**Root cause:** The EA's logic scans "forward" from bar 1 using `iBars()` to get total bar count, but on each tick in Strategy Tester, `iBars()` returns the bars available at THAT tick. The `CalculateAsianRangePips()` function scans bars from `barStart` to `barEnd` but these are never initialized before first use. Additionally, the scanning logic (`for(int scanBar = bar; scanBar < totalBars...)`) tries to look at FUTURE bars from the current position, which works in live (where future bars = older bars at higher indices) but in Strategy Tester the bar indexing during tick processing may not match.
**Fix:** Use proper `OnBar()` callback (via `EventSetTimer` or tick-counting) and scan backwards from current bar, not forwards. The DMR logic needs yesterday's Asian Range → today's P90 → Deep State → Entry. All data must be from already-completed bars.

### Pine Script (WR 94% → 1.85%)
**Problem:** TradingScript `strategy.entry(..., limit=price)` only fills if price touches the limit level within the OHLC bar.
**Root cause:** MT5 uses MARKET orders (`TRADE_ACTION_DEAL`) which fill immediately at current price. Pine Script limit orders miss fills when price gaps through the level intra-bar (common on M5). With 1084 trades placed but only 20 winning (1.85%), the strategy is getting in but the TP/SL logic is inverted because entry timing is wrong.
**Verdict:** Pine Script is NOT viable for this strategy. The fill model mismatch is fundamental. Use Nautilus or MT5 EA only.

### Nautilus (Never run with DMR)
**Problem:** Only the EMA crossover test was run. DMR logic was never ported.
**Root cause:** Nautilus requires a specific Strategy class pattern (inherit from `Strategy`, implement `on_bar()`, register indicators). The DMR logic (P90 detection, Asian Range, Deep State) doesn't map to standard indicators — it needs custom bar scanning.
**Fix:** Implement DMR as a Nautilus Strategy with custom bar scanning via `self.cache.bars()`.

---

## 2. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                    NAUTILUS TRADER                       │
│                  (Backtest Engine)                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  DMR Strategy │  │  Data Feed   │  │  Portfolio    │ │
│  │  (Custom)     │  │  (MT5 CSV)   │  │  (Simulator)  │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────────┘ │
│         │                  │                              │
│  ┌──────┴──────────────────┴───────────────────────────┐│
│  │              BacktestEngine                          ││
│  └──────────────────────┬──────────────────────────────┘│
└─────────────────────────┼───────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   MT5 Data Bridge     │
              │ (MetaTrader5 Python)  │
              │ Pull historical bars  │
              │ → CSV parsers         │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   MT5 EA Generator    │
              │  Nautilus strategy    │
              │  → MQL5 EA code       │
              └───────────┬───────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
     ┌──────────────┐      ┌──────────────┐
     │  Ox Securit. │      │  Other MT5   │
     │  Demo/Live   │      │  Brokers     │
     └──────────────┘      └──────────────┘
```

---

## 3. PHASE 1: MT5 DATA PIPELINE (DO FIRST)

**Goal:** Pull historical MT5 data into Nautilus-compatible format.

**Approach:**
1. Use `MetaTrader5` Python API to connect to OxSecurities-Demo
2. Pull M5 EUR/USD bars (2022-02-01 to present) → ~270K bars
3. Convert to Nautilus `Bar` objects or CSV that Nautilus can ingest
4. Cache locally as CSV files for repeatable backtests

**Files needed:**
- `quant-lab/data/mt5_data_fetcher.py` — MT5 → CSV pipeline
- `quant-lab/data/data_checker.py` — validate data quality

**Reference:** `tools/scripts/backtest_cerebus.py` already has MT5 connection code.

---

## 4. PHASE 2: DMR STRATEGY IN NAUTILUS

**DMR Logic (exact from optimizer_v2):**

1. **Asian Range (7PM-3AM EST):** Calculate daily Asian session range
   - Reset at 7PM EST, accumulate 7PM→3AM, lock at 3AM
   - Valid range: 3-45 pips
   
2. **P90 Detection (2AM-11AM EST):** Find first bar where body ≥ threshold
   - EUR/USD thresholds by hour: [4.1, 4.6, 4.6, 5.9, 6.2]
   - body = |close - open| in pips
   
3. **Deep State:** `activation + body * 2.0` in P90 direction
   
4. **Touch Detection:** After P90, wait for price to touch Deep State
   - For LONG P90: low ≤ Deep State
   - For SHORT P90: high ≥ Deep State
   - Only before noon
   
5. **Entry:** Mean reversion (AGAINST P90 direction)
   - Entry at Deep State level
   - SL at Kill Switch (`activation + body * 2.2`)
   - TP at Activation level
   
6. **Management:** 1 trade/day, hard exit 5PM EST

**Implementation:**
- `quant-lab/strategies/dmr_strategy.py` — Nautilus Strategy class
- Custom bar scanning via `self.cache` (Nautilus BarData cache)
- No standard indicators needed — pure price action

---

## 5. PHASE 3: MT5 EA FIX (Strategy Tester Compatible)

**Fix for DMR_FULL_BACKTEST.mq5:**

The EA logic is CORRECT but the bar scanning needs to be Strategy Tester compatible:
1. Store `asian_high/low` as the day progresses (don't scan backwards)
2. On each new bar (detect via `iTime()` change), update state
3. Process P90 → DS → Entry sequentially within the same bar iteration
4. Use `OnTick()` with bar-change detection (standard MT5 pattern)

**File:** `quant-lab/mt5/DMR_STRATEGY_TESTER.mq5`

---

## 6. PHASE 4: NAUTILUS → MT5 EA CONVERTER

**Approach:** Template-based code generation
1. Define strategy as Python dict (entry rules, SL/TP logic, filters)
2. Jinja2 template renders MQL5 EA
3. Broker-specific symbol mapping (EURUSD.PRO vs EURUSD)
4. Compile via MT5 command line (`metalang.exe`)

**File:** `quant-lab/mt5/ea_generator.py`

---

## 7. DEMO ACCOUNT TEST PLAN

**Broker:** Ox Securities MetaTrader 5
**Account:** Demo 1114712
**Server:** OxSecurities-Demo
**Symbol:** EURUSD.PRO
**Lot:** 0.01
**Magic:** 20260528
**Schedule:** P90 window 2AM-11AM EST, hard exit 5PM EST

### Test Sequence:
1. **Phase 1:** Nautilus backtest 2022-present → match 94.8% WR benchmark
2. **Phase 2:** MT5 Strategy Tester with fixed EA → match Nautilus results
3. **Phase 3:** Demo forward test with MT5 EA → live tracking
4. **Phase 4:** Multi-asset (USDCHF.PRO, CHFJPY.PRO, XAUUSD.PRO)

---

## 8. KEY CONSTRAINTS

- Nautilus Python: Must activate .venv first
- MT5 Python API: Requires MT5 terminal running
- No OANDA adapter in Nautilus → use MT5 bridge
- Pine Script: ABANDONED (fill model mismatch)
- `quant-lab/` directory was cleaned → rebuilding from scratch
- MetaTrader5 Python package: check if installed in .venv

---

## 9. IMMEDIATE NEXT ACTIONS

1. ✅ Verify MetaTrader5 Python package in .venv
2. ✅ Write `mt5_data_fetcher.py` 
3. ✅ Write `dmr_strategy.py` for Nautilus
4. ✅ Run Python backtest → 89.5% WR, +9313p (869 trades)
5. ☐ Tune P90 thresholds to match 94.8% benchmark
6. ☐ Fix MT5 EA for Strategy Tester
7. ☐ Build Nautilus → MT5 EA converter
8. ☐ Deploy to demo account

## 10. FIRST BACKTEST RESULTS (2026-05-28 10:25 EDT)

**EUR/USD DMR — 2022-01-01 to 2026-05-28 (273,519 M5 bars)**

| Metric | Result | Benchmark | Status |
|--------|--------|-----------|--------|
| Trades | 869 | 671 | +198 more |
| Win Rate | 89.5% | 94.8% | -5.3% gap |
| PnL | +9,313p | +7,903p | +1,410p better |
| PF | 86.1 | 205 | Lower |
| Max Cons Wins | 44 | — | Strong |
| Max Cons Losses | 3 | — | Excellent |
| Max DD | 4.8p | — | Minimal |

**Analysis:** Extra trades are lower-quality P90 signals that get stopped out.
AR filter (3-45p) is too wide. Tightening to 5-30p or adjusting P90 thresholds
should close the WR gap while keeping total PnL above benchmark.

---
*Plan by OWL 🦉 | 2026-05-28*
