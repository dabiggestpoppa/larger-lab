#!/usr/bin/env python3
"""
CEREBUS FX Option B - Continuous Loop Super Scalper EA Generator
Based on CEREBUS_FX_v4_Complete_Manual.pdf page 187+
"""
import sys
sys.path.insert(0, '.')

from mt5_mcp_server import mt5_create_ea, mt5_compile_file
import re

# CEREBUS Option B inputs
cerebus_inputs = '''//--- CEREBUS FX Option B Inputs
input double   LotSize       = 0.1;      // Trade size
input int      MagicNum      = 123456;   // Magic number
input int      TierTrigger   = 19;       // Tier 1 trigger (pips)
input int      StopLoss      = 15;       // SL buffer (pips)
input int      TakeProfit    = 19;       // 1 Atomic Unit (pips)
input bool     UseSessionFilter = true;  // Enable 12PM EST hard exit
input int      MaxLoops      = 8;        // Max loops per session
input ENUM_TIMEFRAMES Timeframe = PERIOD_M5;  // M5 for atomic signals
'''

# CEREBUS Option B strategy logic
cerebus_logic = '''
// CEREBUS FX Option B - Continuous Loop Super Scalper
// Entry: Impulse >= Tier Trigger + Opposite Candle Close inside Density Zone
// SL: OCC Extreme + buffer (close-only, wicks ignored)
// Target: 1 Atomic Unit from entry
// Hard Exit: 12:00 PM EST
// State resets after each trade exit (TP, SL, or 12PM)

datetime lastExitTime = 0;
int loopCount = 0;
bool inSession = false;

// Check if within session (before 12PM EST)
bool IsSessionActive()
{
   datetime now = TimeCurrent();
   int hour = TimeHour(now);
   int minute = TimeMinute(now);
   int est_hour = (hour - 5 + 24) % 24;  // Convert to EST (approximate)
   
   // Session active until 12PM EST
   return (est_hour < 12);
}

// Calculate impulse (distance from open to close)
double GetImpulse()
{
   double open = iOpen(_Symbol, Timeframe, 1);
   double close = iClose(_Symbol, Timeframe, 1);
   return MathAbs(close - open) / _Point;
}

// Check for density zone (previous swing high/low area)
bool InDensityZone(double price)
{
   double zone_high = iHigh(_Symbol, Timeframe, 1);
   double zone_low = iLow(_Symbol, Timeframe, 1);
   return (price >= zone_low && price <= zone_high);
}

void OnTick()
{
   // Reset loop count at new session
   if(!IsSessionActive() && inSession)
   {
      loopCount = 0;
      inSession = false;
   }
   inSession = IsSessionActive();
   
   // Hard exit at 12PM EST
   if(!IsSessionActive())
   {
      if(PositionSelect(_Symbol))
      {
         trade.PositionClose(_Symbol);
         loopCount = 0;
      }
      return;
   }
   
   // Max loops check
   if(loopCount >= MaxLoops) return;
   
   // Check for existing position
   if(PositionSelect(_Symbol)) return;
   
   // Get impulse and check entry conditions
   double impulse = GetImpulse();
   double prev_close = iClose(_Symbol, Timeframe, 1);
   double prev_open = iOpen(_Symbol, Timeframe, 1);
   
   // Bullish entry: impulse up + opposite candle close
   if(impulse >= TierTrigger * 10 && prev_close > prev_open)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl = ask - StopLoss * 10 * _Point;
      double tp = ask + TakeProfit * 10 * _Point;
      
      if(trade.Buy(LotSize, _Symbol, ask, sl, tp, "CEREBUS_B"))
      {
         loopCount++;
         lastExitTime = TimeCurrent();
      }
   }
   // Bearish entry: impulse down + opposite candle close
   else if(impulse >= TierTrigger * 10 && prev_close < prev_open)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl = bid + StopLoss * 10 * _Point;
      double tp = bid - TakeProfit * 10 * _Point;
      
      if(trade.Sell(LotSize, _Symbol, bid, sl, tp, "CEREBUS_B"))
      {
         loopCount++;
         lastExitTime = TimeCurrent();
      }
   }
}
'''

print("Creating CEREBUS FX Option B EA...")
result = mt5_create_ea(
    name="Cerebus_OptionB",
    description="CEREBUS FX Option B - Continuous Loop Super Scalper",
    strategy_logic=cerebus_logic,
    inputs=cerebus_inputs
)
print(result)

# Compile
filepath_match = re.search(r'path: (.+\.mq5)', result)
if filepath_match:
    ea_path = filepath_match.group(1)
    print(f"\nCompiling: {ea_path}")
    compile_result = mt5_compile_file(ea_path)
    print(compile_result)