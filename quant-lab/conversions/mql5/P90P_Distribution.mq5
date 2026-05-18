//+------------------------------------------------------------------+
//| P90P Distribution Tracker — Quant Lab v4                          |
//| Performance: 20.0% WR, +150p, PF 1.14                             |
//|                                                                    |
//| Logic: P90 breakout with regime-filtered AR-based targets.         |
//+------------------------------------------------------------------+
#property copyright "Quant Lab"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

// === INPUTS ===
input double SLBodyMult      = 0.80;   // SL Body Multiplier
input double RiskPerTradePct = 0.25;   // Risk per trade (%)
input int    MagicNumber     = 40006;  // Magic Number

// === GLOBALS ===
CTrade trade;
double PipValue;

// State
bool   tradedToday  = false;
double entryPrice   = 0;
double slLevel      = 0;
double tpLevel      = 0;
string regime       = "NEUTRAL";

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
      regime = "NEUTRAL";
   }
   
   // === Regime Detection at 9 AM EST ===
   if(estHour == 9 && asianInitialized)
   {
      double arPips = (asianHigh - asianLow) / PipValue;
      if(arPips > 0)
      {
         // Calculate daily range from 3 AM to 9 AM (72 M5 bars)
         double dailyHigh = iHigh(_Symbol, PERIOD_M5, iHighest(_Symbol, PERIOD_M5, MODE_HIGH, 72, 0));
         double dailyLow  = iLow(_Symbol, PERIOD_M5, iLowest(_Symbol, PERIOD_M5, MODE_LOW, 72, 0));
         double dailyRange = (dailyHigh - dailyLow) / PipValue;
         double ratio = dailyRange / arPips;
         
         if(ratio >= 1.50)
            regime = "CONFIRMED";
         else if(ratio < 1.45)
            regime = "FAILED";
         else
            regime = "NEUTRAL";
      }
   }
   
   // === P90 Detection (2-11 AM EST) ===
   if(!tradedToday && estHour >= 2 && estHour < 11 && asianInitialized)
   {
      double openPrice  = iOpen(_Symbol, PERIOD_M5, 1);
      double closePrice = iClose(_Symbol, PERIOD_M5, 1);
      double bodySize   = MathAbs(closePrice - openPrice) / PipValue;
      double threshold  = GetP90Threshold(estHour);
      double arPips     = (asianHigh - asianLow) / PipValue;
      
      if(bodySize >= threshold && arPips >= 3.0 && arPips <= 45.0)
      {
         int dir = closePrice > openPrice ? 1 : -1;
         
         // Must close outside Asian band
         bool validClose = (dir == 1 && closePrice > asianHigh) || (dir == -1 && closePrice < asianLow);
         
         if(validClose && regime != "FAILED")
         {
            // Tier factor
            string tier = arPips < 20 ? "T1" : arPips < 30 ? "T2" : "T3";
            double tierFactor = tier == "T1" ? 1.80 : tier == "T2" ? 1.50 : 1.20;
            double fraction = regime == "CONFIRMED" ? 0.70 : 0.55;
            double targetPips = arPips * tierFactor * fraction;
            
            entryPrice = closePrice;
            double bodyInPrice = bodySize * PipValue;
            slLevel = closePrice - bodyInPrice * SLBodyMult * dir;
            tpLevel = closePrice + targetPips * PipValue * dir;
            
            double slPips = bodySize * SLBodyMult;
            double lots   = CalculateLotSize(slPips);
            
            if(dir == 1)
               trade.Buy(lots, _Symbol, 0, slLevel, tpLevel, "P90P Long");
            else
               trade.Sell(lots, _Symbol, 0, slLevel, tpLevel, "P90P Short");
            
            tradedToday = true;
         }
      }
   }
}
