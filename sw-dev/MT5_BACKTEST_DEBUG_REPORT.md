# MT5 Native Backtest — Debug Report
> Generated: 2026-05-20 ~09:00 EDT
> Status: BLOCKED — EA loads but OnInit() never executes

## PIPELINE GOAL
```
Idea → Python Backtest (optimizer_v2) → Monte Carlo → NATIVE MT5 BACKTEST → Report
```

## WHAT WORKS
- ✅ `terminal64.exe /config:ini` auto-starts Strategy Tester
- ✅ EA compiles clean (0 errors, 0 warnings)
- ✅ EA file loads in Strategy Tester (log shows "DMR_FULL_BACKTEST.ex5 X64")
- ✅ INI config is read (terminal.ini shows correct values)
- ✅ Python backtest: 91.8% WR, +8746p, PF 112
- ✅ Monte Carlo: 100% prob profit, MaxDD <5.5p

## WHAT DOESN'T WORK
- ❌ EA `OnInit()` never executes (zero Print output in any log)
- ❌ 0 bars processed, 0 trades, test finishes in 0 seconds
- ❌ No HTML report generated (only 32-byte error page)
- ❌ No JSON results file generated

## CURRENT EA CODE
**File:** `quant-lab/mt5/DMR_FULL_BACKTEST.mq5` (v4.00)
**Compiled:** `MQL5/Experts/DMR_FULL_BACKTEST.ex5` (27,542 bytes)

### Key Architecture:
```
OnInit() → Print init info, setup trade object
OnTick() → Process bars sequentially from lastProcessedBar+1
           For each bar: check new day → find P90 → check DS touch → place order
OnDeinit() → Print final results, write JSON
```

### Strategy Logic (matches Python optimizer_v2):
1. Scan for P90 candle (body ≥ threshold for EST hour 2-11)
2. Calculate Deep State = activation + body×2.00 in P90 direction
3. Calculate Kill Switch = activation + body×2.20 in P90 direction
4. Wait for price to touch Deep State
5. Enter mean reversion (AGAINST P90 direction) at Deep State
6. SL at Kill Switch, TP at Activation
7. Hard exit at 17 EST

## INI CONFIG
**File:** `quant-lab/mt5/dmr_tester_config.ini`
```ini
[Common]
Login=1114712
Server=OxSecurities-Demo

[Tester]
Expert=DMR_FULL_BACKTEST.ex5
ExpertParameters=DMR_FULL_BACKTEST.set
Symbol=EURUSD.PRO
Period=M5
Model=2
FromDate=2024.01.01
ToDate=2024.01.31
ShutdownTerminal=1
```

## SUSPECTED ISSUES

### Issue 1: EA OnInit() Crash
**Symptom:** No Print output from OnInit() in any log
**Possible causes:**
- `iBars()` or `iTime()` called before bars are loaded in Strategy Tester
- Array initialization failure
- `#include <Trade\Trade.mqh>` failing

### Issue 2: Period Format in INI
**Symptom:** HTML report shows "Period: M0 (1970.01.01 - 1970.01.01)"
**Current:** `Period=M5`
**Tried:** `Period=5`, `Period=16408`, `Period=M5`
**Note:** The `[Tester]` section might use different format than `[Test]` section

### Issue 3: OnTick() vs OnCalculate()
**Theory:** MT5 Strategy Tester might not call OnTick() for historical bars
**Fix:** Might need to use OnCalculate() or process all bars in OnInit()

### Issue 4: .set File Format
**Current format:** `ParamName=Value||Default||Min||Max||N`
**Risk:** Parameter names might not match EA input names exactly

### Issue 5: Symbol Name
**Current:** `EURUSD.PRO`
**Risk:** MT5 Strategy Tester might need just `EURUSD` without broker suffix

## LOG EVIDENCE

### Tester Log (20260520.log):
```
IO  07:56:13.650  Tester  "DMR_FULL_BACKTEST.ex5" X64
QH  07:56:14.183  Core 1  agent process started on 127.0.0.1:3000
KI  07:56:14.751  Tester  automatical testing finished
```
→ EA loads, agent starts, test finishes in < 1 second

### Expert Log:
→ ZERO entries from DMR_FULL_BACKTEST EA
→ Only entry: "automated trading is disabled because the account has been changed"

### HTML Report:
→ 32 bytes only (error page)
→ Shows: Period M0, History Quality 0%, Bars: 0

## FILES
| File | Path |
|------|------|
| EA Source | `quant-lab/mt5/DMR_FULL_BACKTEST.mq5` |
| EA Compiled | `MQL5/Experts/DMR_FULL_BACKTEST.ex5` |
| INI Config | `quant-lab/mt5/dmr_tester_config.ini` |
| Set File | `MQL5/Profiles/Tester/DMR_FULL_BACKTEST.set` |
| Automation | `quant-lab/mt5/run_native_mt5_backtest.py` |
| Results (empty) | `DMR_FULL_BACKTEST_EURUSD_PRO.htm` |

## RESEARCH NEEDED
1. MT5 Strategy Tester INI format — what Period values work in [Tester] section?
2. Does OnTick() get called for historical bars in Strategy Tester?
3. How to debug EA initialization failures in Strategy Tester?
4. Does the EA need `OnCalculate()` instead of `OnTick()` for backtesting?
5. Is there a way to enable MQL5 expert logging in Strategy Tester?

## EXISTING WORKING EA
There's an existing `DMR_Backtest.mq5` (v2.00) in the Experts folder that was used in yesterday's test. It has the same logic but simpler structure. It was started from GUI, not command line. Worth comparing.
