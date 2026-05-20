# MT5 Strategy Tester — EA Initialization & Backtesting Research

> **Date:** 2026-05-20
> **Author:** OWL Subagent (Research Task)
> **Problem:** EA loads in Strategy Tester but `OnInit()` never executes — "0 bars processed in 0 seconds"

---

## 1. ROOT CAUSE ANALYSIS

### The Core Problem: "0 bars processed in 0 seconds"

This message in the Strategy Tester means the EA was loaded but **no bars were processed at all**. The test terminated immediately. This is NOT the same as "OnInit was called but OnTick did nothing." This means one of:

1. **The EA failed to load** (compilation error, wrong path, corrupted .ex5)
2. **OnInit returned non-zero** (INIT_FAILED) on the very first call
3. **The test configuration is wrong** (no data for the selected symbol/period/date range)
4. **The EA file being loaded is not the one you think** (wrong path, stale .ex5)

### Critical Diagnostic: Check the Strategy Tester Journal Tab

The **#1 mistake** is looking at the main terminal Journal tab instead of the **Strategy Tester's own Journal tab**. The Tester has a separate log. Open it via:
- View → Strategy Tester → bottom panel → "Journal" tab

If OnInit truly ran, you WILL see the Print() output there. If you see nothing, the EA never loaded.

---

## 2. COMMON CAUSES & FIXES

### Cause A: OnInit Returns Non-Zero or Throws Runtime Error

If `OnInit()` returns anything other than `INIT_SUCCEEDED`, the EA is immediately unloaded.

**Typical failures inside OnInit:**
- **Indicator handle creation fails** (`iCustom` returns `INVALID_HANDLE`)
  - Custom indicator doesn't exist, isn't compiled, or wrong name/path
  - Fix: Check indicator exists in `MQL5/Indicators/`, verify name spelling
- **Array out of range** in OnInit
  - Using `CopyBuffer`, `CopyRates`, etc. when history isn't ready
  - Fix: Don't access bar data in OnInit — move to first OnTick
- **DLL imports not allowed** in tester
  - Fix: Tools → Options → Expert Advisors → "Allow DLL imports"
- **MessageBox or GUI calls** in OnInit
  - These block/break in Strategy Tester
  - Fix: Replace with `Print()`

**Diagnostic approach:**
```mq5
int OnInit()
{
   Print("OnInit ENTERED");  // If you don't see this, EA didn't load at all
   // Comment out ALL other logic
   return(INIT_SUCCEEDED);   // Force success
}
```
If this works, add back logic one piece at a time until it breaks.

### Cause B: Global Scope Code Throws Before OnInit

Any code at global scope (outside functions) that throws a runtime error prevents the EA from loading entirely. Examples:
```mq5
// BAD — at global scope:
double buffer[];
ArrayResize(buffer, 100);  // Can throw if memory issue
CopyRates(_Symbol, PERIOD_M5, 0, 100, rates);  // Can throw if no data
```
**Fix:** Move ALL logic into `OnInit` or `OnTick`. Global scope should only have declarations.

### Cause C: Wrong EA Selected in Tester

- The EA must appear under **Navigator → Expert Advisors** in the Tester
- If multiple EAs have the same name in different folders, the wrong one may be loaded
- **Fix:** Recompile, delete old .ex5 files, re-select in Tester

### Cause D: No Historical Data

If the selected symbol/period has no data in the selected date range, the Tester processes 0 bars.
- **Fix:** Download history via Tools → History Center, or use "Every tick based on real ticks" with downloaded tick data

---

## 3. DMR_BACKTEST.MQ5 vs DMR_FULL_BACKTEST.MQ5 — KEY DIFFERENCES

### DMR_Backtest.mq5 (v2.00) — The "Broken" One

**Architecture:** Processes bars by scanning forward from bar 1 on every tick.

**Critical flaw — the `OnTick()` loop scans from bar 1 every tick:**
```mq5
void OnTick()
{
   int bar = 1;
   // ...
   if(!p90Found)
   {
      int totalBars = iBars(_Symbol, PERIOD_M5);
      for(int scanBar = bar; scanBar < totalBars && scanBar - bar < 500; scanBar++)
      {
         // Scans up to 500 bars from bar 1 on EVERY tick
      }
   }
   // Then scans again for DS touch from p90BarIndex+1 to bar (which is always 1!)
   if(!dsTouched)
   {
      for(int checkBar = p90BarIndex + 1; checkBar < totalBars && checkBar <= bar; checkBar++)
      {
         // bar is always 1, so if p90BarIndex >= 1, this loop NEVER executes
      }
   }
}
```

**Problems identified:**
1. **`bar` is hardcoded to 1** — it never advances. The EA always looks at bar 1.
2. **DS touch check is broken** — `checkBar <= bar` where `bar=1` and `p90BarIndex >= 1` means the loop condition `p90BarIndex+1 <= 1` is false when P90 is found at bar >= 1. DS touch is never detected.
3. **No bar tracking** — no `lastProcessedBar` variable, so the same bars are re-scanned on every tick.
4. **Scans 500 bars per tick** — extremely slow, may cause timeout in Strategy Tester.

### DMR_FULL_BACKTEST.mq5 (v4.00) — The "Fixed" One

**Architecture:** Processes bars sequentially with `lastProcessedBar` tracking.

**Key improvements:**
```mq5
int lastProcessedBar = 0;  // Tracks progress

void OnTick()
{
   int totalBars = iBars(_Symbol, PERIOD_M5);
   if(totalBars < 10) return;
   
   int startBar = lastProcessedBar + 1;  // Resume from where we left off
   if(startBar < 1) startBar = 1;
   
   int endBar = MathMin(startBar + 100, totalBars - 1);  // Process 100 bars per tick
   
   for(int bar = startBar; bar <= endBar; bar++)
   {
      lastProcessedBar = bar;  // Advance the cursor
      // ... process this bar
   }
}
```

**Advantages:**
1. **Sequential processing** — each bar is processed exactly once
2. **No re-scanning** — `lastProcessedBar` prevents duplicate work
3. **Batched processing** — 100 bars per tick avoids timeout
4. **Correct DS detection** — checks bars after P90 in proper sequence
5. **Includes JPY pair handling** — `PipsToPrice` and `PriceToPips` check for "JPY" in symbol
6. **Includes CTrade class** — uses `<Trade\Trade.mqh>` for trade management
7. **Writes results to JSON** — `DMR_FULL_BACKTEST_RESULTS.json` in common files folder

### Summary of Differences

| Aspect | DMR_Backtest v2.00 | DMR_FULL_BACKTEST v4.00 |
|--------|-------------------|------------------------|
| Bar processing | Re-scans from bar 1 every tick | Sequential with cursor |
| DS touch detection | Broken (loop condition wrong) | Correct |
| Performance | O(n²) — scans 500 bars/tick | O(n) — 100 bars/tick |
| JPY handling | No (hardcoded /10000) | Yes (checks symbol string) |
| Trade class | Raw OrderSend | CTrade wrapper |
| Results output | Print only | Print + JSON file |
| OnInit | Basic | Sets CTrade params + verbose logging |
| MaxAR/MinAR filter | Not present | Present (input params) |

---

## 4. MT5 STRATEGY TESTER CONFIGURATION

### INI File Format for [Tester] Section

When running MT5 Strategy Tester via command line (`terminal64.exe /config:...`):

```ini
[Tester]
Expert=DMR_FULL_BACKTEST.ex5
ExpertParameters=DMR_FULL_BACKTEST.set
Symbol=EURUSD
Period=H1
Model=1
FromDate=2022.01.01
ToDate=2022.06.30
Report=reports\EURUSD_H1
ReplaceReport=1
ShutdownTerminal=1
```

**Period format:** Use MT5 timeframe strings, NOT numbers:
- ✅ `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`, `W1`, `MN1`
- ❌ `60` (this is MT4 format, NOT MT5)
- ❌ `PERIOD_H1` (enum name, not the INI value)

**Model values:**
- `0` = Every tick (slowest, most accurate)
- `1` = Open prices only (fastest, only for bar-open strategies)
- `10` = Every tick based on real ticks (requires tick data)

### Tester Mode Selection for DMR Strategy

The DMR strategy:
- Finds P90 on completed bars
- Checks DS touch on subsequent bars
- Places limit orders (not market orders)

**Recommended mode:** `Model=1` (Open prices only) is acceptable IF:
- The strategy only makes decisions on completed bars (bar 1+)
- Entry orders are pending orders (not market orders)
- SL/TP are set at order placement time

**Use `Model=0` (Every tick)** if:
- You need intrabar price movement for DS detection
- You're using market orders for entry
- You want maximum accuracy

---

## 5. OnTick vs OnCalculate in Strategy Tester

### Key Distinction

| | OnTick | OnCalculate |
|---|--------|-------------|
| Used in | Expert Advisors | Custom Indicators |
| Called when | Each simulated tick | Indicator recalculation needed |
| Has rates_total/prev_calculated | No | Yes |
| Bar tracking | Manual (Bars() comparison) | Automatic via prev_calculated |

### For EA Backtesting

**Use OnTick** for EAs. You must track new bars manually:
```mq5
int bars_prev = 0;

void OnTick()
{
   int bars = Bars(_Symbol, _Period);
   if(bars == bars_prev) return;  // No new bar
   
   // New bar appeared — process it
   bars_prev = bars;
   // ... your logic using bar index (bars-1 for newest completed)
}
```

**Do NOT use OnCalculate in an EA** — it's for indicators only.

### Using Indicators Inside an EA

The correct pattern:
```mq5
int handle;

int OnInit()
{
   handle = iCustom(_Symbol, _Period, "MyIndicator", ...);
   if(handle == INVALID_HANDLE)
   {
      Print("Failed to create indicator handle, error=", GetLastError());
      return(INIT_FAILED);
   }
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   double buffer[];
   if(CopyBuffer(handle, 0, 0, 3, buffer) <= 0)
      return;  // Not ready yet
   // Use buffer[0], buffer[1], etc.
}

void OnDeinit(const int reason)
{
   if(handle != INVALID_HANDLE)
      IndicatorRelease(handle);
}
```

---

## 6. DIAGNOSTIC CHECKLIST

If your EA shows "0 bars processed in 0 seconds":

- [ ] **Check Strategy Tester Journal tab** (not main terminal Journal)
- [ ] **Verify EA compiled with no errors** in MetaEditor
- [ ] **Verify EA appears in Navigator → Expert Advisors** in Tester
- [ ] **Simplify OnInit to just Print + return(INIT_SUCCEEDED)**
- [ ] **Check for global scope code** that might throw before OnInit
- [ ] **Verify historical data exists** for symbol/period/date range
- [ ] **Check for duplicate EA files** (wrong .ex5 being loaded)
- [ ] **Try a different symbol/period** to isolate data issues
- [ ] **Enable DLL imports** if EA uses DLLs
- [ ] **Remove any MessageBox/GUI calls** from OnInit and OnTick
- [ ] **Use the DMR_MINIMAL_TEST.mq5** EA to verify basic Tester functionality

---

## 7. RECOMMENDATIONS

### Immediate Fix

1. **Use DMR_FULL_BACKTEST.mq5** (v4.00) — it's the corrected version
2. **Run DMR_MINIMAL_TEST.mq5 first** to verify the Tester environment works
3. **Check the Strategy Tester Journal tab** for OnInit output

### If OnInit Still Not Called

1. Recompile the EA in MetaEditor (ensure 0 errors, 0 warnings)
2. Delete the old .ex5 file and recompile fresh
3. In Tester, re-select the EA from Navigator
4. Try with a simple symbol like EURUSD M5 with a 1-day range
5. Check if the terminal64.exe config INI has the correct Period format (`M5` not `5`)

### Strategy Logic Fix

The DMR_FULL_BACKTEST.mq5 v4.00 is architecturally correct but has one potential issue:
- It places orders at `deepStateLevel` as a **market order** (`TRADE_ACTION_DEAL`), but the intent seems to be a **limit order** at the deep state level. If price never touches the deep state level in the simulation, the order fills immediately at current market price instead of waiting.
- **Fix:** Consider using `TRADE_ACTION_PENDING` with `ORDER_TYPE_BUY_LIMIT` or `ORDER_TYPE_SELL_LIMIT` for the entry.

---

## 8. FILES CREATED

| File | Purpose |
|------|---------|
| `quant-lab/mt5/DMR_MINIMAL_TEST.mq5` | Minimal diagnostic EA — verifies OnInit/OnTick/OnDeinit are called |
| `sw-dev/MT5_BACKTEST_RESEARCH.md` | This document |

---

*Research completed: 2026-05-20*
