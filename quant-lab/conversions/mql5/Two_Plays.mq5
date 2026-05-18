//+------------------------------------------------------------------+
//| Two Plays — Quant Lab v4                                           |
//| Performance: 42.3% WR, +53p, PF 1.04                              |
//|                                                                    |
//| Play 1 (Base 80): T1/T2 breakout with tight SL                     |
//| Play 2 (T3 Model 2): T3 hold test + pullback entry                 |
//+------------------------------------------------------------------+
#property copyright "Quant Lab"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

// === INPUTS ===
input double SLBodyMult      = 1.5;    // SL Body Multiplier (Base80)
input double Base80TpFactor  = 0.35;   // Base80 TP Factor (xAR)
input double T3TpFactor      = 1.0;    // T3 TP Factor (xAR)
input double T3SlFactor      = 0.80;   // T3 SL Factor (xImpulse)
input double PullbackMin     = 0.32;   // Pullback Min %
input double PullbackMax     = 0.50;   // Pullback Max %
input double RiskPerTradePct = 0.25;   // Risk per trade (%)
input int    MagicNumber     = 40007;  // Magic Number

// === GLOBALS ===
CTrade trade;
double PipValue;

// State
bool   tradedToday  = false;
int    playType     = 0;
int    state2       = 0;   // T3 states: 0=looking_breakout, 1=hold_test, 2=looking_pullback
int    breakDir     = 0;
double breakPrice   = 0;
double impulseLeg   = 0;
int    holdStartBar = 0;
double entryPrice   = 0;
double slLevel      = 0;
double tpLevel      = 0;

// Asian range
double asianHigh        = 0;
double asianLow         = 0;
bool   asianInitialized = false;

//+------------------------------------------------------------------+
int OnInit()
{
   PipValue = _Point * 10;
   if(_Digits <= 3) PipValue = _Point;
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(10);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason) {}

//+------------------------------------------------------------------+
double PipsToPrice(double pips) { return pips * PipValue; }

//+------------------------------------------------------------------+
double CalculateLotSize(double slPips)
{
   if(slPips <= 0) return 0.01;
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmt = equity * RiskPerTradePct / 100.0;
   double lotSize = riskAmt / (slPips * 10.0);
   lotSize = NormalizeDouble(lotSize, 2);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lotSize = MathMax(minLot, MathMin(maxLot, lotSize));
   lotSize = MathFloor(lotSize / step) * step;
   return lotSize;
}

//+------------------------------------------------------------------+
double GetP90Threshold(int estHour)
{
   if(estHour >= 2  && estHour < 4)  return 4.1;
   if(estHour >= 4  && estHour < 8)  return 4.6;
   if(estHour >= 8  && estHour < 11) return 5.9;
   if(estHour == 11)                 return 6.2;
   return 999.0;
}

//+------------------------------------------------------------------+
void OnTick()
{
   datetime now     = TimeCurrent();
   int      utcHour = TimeHour(now);
   int      estHour = (utcHour - 5 + 24) % 24;
   
   // === Asian Range (7PM - 3AM EST) ===
   if(estHour >= 19 || estHour < 3)
   {
      if(!asianInitialized)
      {
         asianHigh = iHigh(_Symbol, PERIOD_M5, 0);
         asianLow  = iLow(_Symbol, PERIOD_M5, 0);
         asianInitialized = true;
      }
      else
      {
         asianHigh = MathMax(asianHigh, iHigh(_Symbol, PERIOD_M5, 0));
         asianLow  = MathMin(asianLow,  iLow(_Symbol, PERIOD_M5, 0));
      }
   }
   
   // === New bar check ===
   static datetime lastBarTime = 0;
   if(iTime(_Symbol, PERIOD_M5, 0) == lastBarTime) return;
   lastBarTime = iTime(_Symbol, PERIOD_M5, 0);
   
   // === Hard exit at 5 PM EST ===
   if(estHour >= 17)
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            trade.PositionClose(ticket);
      }
      tradedToday = false;
      return;
   }
   
   // === Reset at 2 AM ===
   if(estHour == 2)
   {
      tradedToday = false;
      playType = 0;
      state2 = 0;
   }
   
   double openPrice  = iOpen(_Symbol, PERIOD_M5, 1);
   double closePrice = iClose(_Symbol, PERIOD_M5, 1);
   double bodySize   = MathAbs(closePrice - openPrice) / PipValue;
   double arPips     = asianInitialized ? (asianHigh - asianLow) / PipValue : 0;
   
   // === PLAY 1: Base 80 (T1/T2 only, AR < 20) ===
   if(!tradedToday && arPips > 0 && arPips < 20 && estHour >= 2 && estHour < 11 && asianInitialized)
   {
      double threshold = GetP90Threshold(estHour);
      if(bodySize >= threshold)
      {
         if(closePrice > asianHigh && iHigh(_Symbol, PERIOD_M5, 1) > asianHigh)
         {
            double closeDist = (closePrice - asianHigh) / PipValue;
            if(closeDist >= 2.0)
            {
               entryPrice = closePrice;
               slLevel = entryPrice - bodySize * PipValue * SLBodyMult;
               tpLevel = entryPrice + arPips * PipValue * Base80TpFactor;
               
               double slPips = bodySize * SLBodyMult;
               double lots   = CalculateLotSize(slPips);
               trade.Buy(lots, _Symbol, 0, slLevel, tpLevel, "TP Base80 Long");
               
               tradedToday = true;
               playType = 1;
            }
         }
         else if(closePrice < asianLow && iLow(_Symbol, PERIOD_M5, 1) < asianLow)
         {
            double closeDist = (asianLow - closePrice) / PipValue;
            if(closeDist >= 2.0)
            {
               entryPrice = closePrice;
               slLevel = entryPrice + bodySize * PipValue * SLBodyMult;
               tpLevel = entryPrice - arPips * PipValue * Base80TpFactor;
               
               double slPips = bodySize * SLBodyMult;
               double lots   = CalculateLotSize(slPips);
               trade.Sell(lots, _Symbol, 0, slLevel, tpLevel, "TP Base80 Short");
               
               tradedToday = true;
               playType = 1;
            }
         }
      }
   }
   
   // === PLAY 2: T3 Model 2 (T3 only, AR 30-45) ===
   if(!tradedToday && arPips >= 30.0 && arPips < 45.0 && asianInitialized)
   {
      // State 0: Look for initial breakout
      if(state2 == 0 && estHour >= 3 && estHour < 12)
      {
         if(bodySize >= 4.6)
         {
            if(closePrice > asianHigh && iHigh(_Symbol, PERIOD_M5, 1) > asianHigh)
            {
               breakDir     = 1;
               breakPrice   = closePrice;
               impulseLeg   = (closePrice - asianHigh) / PipValue;
               holdStartBar = iBars(_Symbol, PERIOD_M5);
               state2 = 1;
            }
            else if(closePrice < asianLow && iLow(_Symbol, PERIOD_M5, 1) < asianLow)
            {
               breakDir     = -1;
               breakPrice   = closePrice;
               impulseLeg   = (asianLow - closePrice) / PipValue;
               holdStartBar = iBars(_Symbol, PERIOD_M5);
               state2 = 1;
            }
         }
      }
      
      // State 1: Hold test (2 hours = 24 M5 bars)
      if(state2 == 1)
      {
         bool holdOK = true;
         if(breakDir == 1 && closePrice < asianLow)
            holdOK = false;
         else if(breakDir == -1 && closePrice > asianHigh)
            holdOK = false;
         
         if(!holdOK)
            state2 = 0;
         else if(iBars(_Symbol, PERIOD_M5) - holdStartBar >= 24)
            state2 = 2;
      }
      
      // State 2: Look for pullback
      if(state2 == 2 && estHour < 12)
      {
         double retrace = breakDir == 1 ? (breakPrice - iLow(_Symbol, PERIOD_M5, 0)) / PipValue : (iHigh(_Symbol, PERIOD_M5, 0) - breakPrice) / PipValue;
         double retracePct = impulseLeg > 0 ? retrace / impulseLeg : 0;
         
         if(retracePct >= PullbackMin && retracePct <= PullbackMax)
         {
            double ep    = closePrice;
            double slVal = ep - impulseLeg * PipValue * T3SlFactor * breakDir;
            double tpVal = ep + arPips * PipValue * T3TpFactor * breakDir;
            
            double slPips = impulseLeg * T3SlFactor;
            double lots   = CalculateLotSize(slPips);
            
            if(breakDir == 1)
               trade.Buy(lots, _Symbol, 0, slVal, tpVal, "TP T3 Long");
            else
               trade.Sell(lots, _Symbol, 0, slVal, tpVal, "TP T3 Short");
            
            tradedToday = true;
            playType = 2;
         }
         
         // Timeout: 1 hour after hold test
         if(iBars(_Symbol, PERIOD_M5) - holdStartBar >= 36)
            state2 = 0;
      }
   }
}
