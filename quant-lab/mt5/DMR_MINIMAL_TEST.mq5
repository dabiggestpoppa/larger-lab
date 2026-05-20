//+------------------------------------------------------------------+
//|                                    DMR_MINIMAL_TEST.mq5          |
//|                    Minimal EA to diagnose OnInit/OnTick in        |
//|                    MT5 Strategy Tester                             |
//|                                                                    |
//|  PURPOSE: Verify that OnInit, OnTick, OnDeinit are actually       |
//|           called by the Strategy Tester. Use this to diagnose     |
//|           "0 bars processed in 0 seconds" issues.                 |
//|                                                                    |
//|  USAGE:                                                           |
//|    1. Compile in MetaEditor                                       |
//|    2. Open Strategy Tester (Ctrl+R)                               |
//|    3. Select this EA, any symbol, M1 or M5 timeframe              |
//|    4. Set date range (at least 1 day)                             |
//|    5. Run test                                                    |
//|    6. Check Journal tab in Strategy Tester for output             |
//|                                                                    |
//|  EXPECTED OUTPUT (in Strategy Tester Journal tab):                |
//|    OnInit v1.0 called                                             |
//|    Symbol: EURUSD | Period: 5 | Bars: 288                        |
//|    OnTick #1 bar=... price=...                                    |
//|    OnTick #2 bar=... price=...                                    |
//|    ...                                                            |
//|    OnDeinit reason=5                                              |
//|    === SUMMARY: OnInit=YES OnTick=YES ticks=288 ===               |
//+------------------------------------------------------------------+
#property copyright "Quant Lab — Diagnostic"
#property link      ""
#property version   "1.00"
#property strict
#property description "Minimal EA to verify Strategy Tester calls OnInit/OnTick/OnDeinit"

// ─── INPUTS ─────────────────────────────────────────────────────
input bool EnableVerboseLogging = false;  // Log every tick (slow)
input int  LogEveryNTicks      = 100;     // Log every N ticks if verbose off

// ─── GLOBALS ────────────────────────────────────────────────────
int tickCount    = 0;
int initCount    = 0;
int deinitCount  = 0;
bool initCalled  = false;
datetime lastBarTime = 0;
int barCount     = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   initCount++;
   initCalled = true;
   
   Print("============================================================");
   Print("  DMR_MINIMAL_TEST v1.00 — OnInit CALLED");
   Print("  Symbol: ", _Symbol);
   Print("  Period: ", _Period, " (", EnumToString(_Period), ")");
   Print("  Digits: ", _Digits);
   Print("  Point:  ", DoubleToString(_Point, _Digits));
   
   int bars = Bars(_Symbol, _Period);
   Print("  Bars available on init: ", bars);
   
   // Check if we can read bar data in OnInit
   if(bars > 1)
   {
      double close = iClose(_Symbol, _Period, 1);
      datetime time = iTime(_Symbol, _Period, 1);
      Print("  Bar[1] close=", DoubleToString(close, _Digits), 
            " time=", TimeToString(time, TIME_DATE|TIME_MINUTES));
   }
   else
   {
      Print("  WARNING: Not enough bars in OnInit (bars=", bars, ")");
      Print("  This is normal — data may not be ready in OnInit.");
      Print("  Move data access to OnTick for reliability.");
   }
   
   Print("============================================================");
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   deinitCount++;
   
   Print("============================================================");
   Print("  DMR_MINIMAL_TEST — OnDeinit CALLED");
   Print("  Reason code: ", reason, " (", GetDeinitReasonText(reason), ")");
   Print("  OnInit was called: ", initCalled ? "YES" : "NO");
   Print("  Total OnTick calls: ", tickCount);
   Print("  Total new bars seen: ", barCount);
   Print("============================================================");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!initCalled)
   {
      Print("ERROR: OnTick called but OnInit was never called!");
      return;
   }
   
   tickCount++;
   
   // Count new bars
   datetime currentBarTime = iTime(_Symbol, _Period, 0);
   if(currentBarTime != lastBarTime)
   {
      barCount++;
      lastBarTime = currentBarTime;
   }
   
   // Logging
   if(EnableVerboseLogging)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      Print("OnTick #", tickCount, " bar=", barCount, 
            " bid=", DoubleToString(bid, _Digits));
   }
   else if(tickCount == 1 || tickCount % LogEveryNTicks == 0)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      Print("OnTick #", tickCount, " (", barCount, " bars) bid=", 
            DoubleToString(bid, _Digits));
   }
}

//+------------------------------------------------------------------+
//| Convert deinit reason code to text                                |
//+------------------------------------------------------------------+
string GetDeinitReasonText(int reason)
{
   switch(reason)
   {
      case 0:  return "REMOVED";           // EA removed from chart
      case 1:  return "RECOMPILED";        // EA recompiled
      case 2:  return "CHART_CHANGE";      // Symbol/period changed
      case 3:  return "PARAMETERS";        // Input parameters changed
      case 4:  return "ACCOUNT";           // Account changed
      case 5:  return "TEST_END";          // Strategy Tester finished
      case 6:  return "CLOSE";             // Terminal closed
      default: return "UNKNOWN(" + IntegerToString(reason) + ")";
   }
}
//+------------------------------------------------------------------+
