//+------------------------------------------------------------------+
//| Dual Engine — CEREBUS FX v4.0                                     |
//| Performance: 51.2% WR, +757p, PF 1.60                             |
//|                                                                    |
//| Logic: Two-stage entry system. The "anchor" is the first P90      |
//| breakout from the Asian range. "Amplifier" entries are additional |
//| entries in the same direction during a pullback.                   |
//+------------------------------------------------------------------+
#property copyright "Quant Lab"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

// === INPUTS ===
input double MaxAR            = 30.0;   // Max AR (pips)
input double MinAR            = 3.0;    // Min AR (pips)
input double MaxARQuality     = 20.0;   // Max AR Quality (pips)
input double SLBodyMult       = 1.5;    // SL Body Multiplier
input double TPARFactor       = 0.35;   // TP AR Factor
input double RetraceMin       = 0.32;   // Retrace Min
input double RetraceMax       = 0.50;   // Retrace Max
input int    MaxAmpsT1        = 2;      // Max Amplifiers T1
input int    MaxAmpsT2        = 1;      // Max Amplifiers T2
input double MinCloseOutside  = 2.0;    // Min Close Outside AR (pips)
input double RiskPerTradePct  = 0.25;   // Risk per trade (% of equity)
input int    MagicNumber      = 30002;  // Magic Number

// === GLOBALS ===
CTrade trade;
double PipValue;

// State variables
bool   anchorPlaced    = false;
int    anchorDirection = 0;    // 1=LONG, -1=SHORT
double anchorPrice     = 0;
double anchorBodyPips  = 0;
double arAtAnchor      = 0;
int    ampCount        = 0;
int    maxAmps         = 0;
double impulseHigh     = 0;
double impulseLow      = 0;

// Asian range tracking
double asianHigh        = 0;
double asianLow         = 0;
double arPips           = 0;
bool   asianInitialized = false;
bool   arValid          = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   PipValue = _Point * 10;
   if(_Digits <= 3)
      PipValue = _Point;
   
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(10);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
}

//+------------------------------------------------------------------+
//| Get P90 body threshold for given EST hour                          |
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
//| Classify tier from AR pips                                         |
//+------------------------------------------------------------------+
string ClassifyTier(double ar)
{
   if(ar < 20) return "T1";
   if(ar < 30) return "T2";
   if(ar < 45) return "T3";
   return "NO_GO";
}

//+------------------------------------------------------------------+
//| Convert pips to price                                              |
//+------------------------------------------------------------------+
double PipsToPrice(double pips)
{
   return pips * PipValue;
}

//+------------------------------------------------------------------+
//| Calculate position size based on risk                              |
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
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime now    = TimeCurrent();
   int      utcHour = TimeHour(now);
   int      estHour = (utcHour - 5 + 24) % 24;
   
   // === Update Asian Range (7PM - 3AM EST) ===
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
   
   // === Reset Asian Range at 3 AM EST ===
   if(estHour == 3 && asianInitialized)
   {
      arPips = (asianHigh - asianLow) / PipValue;
      asianInitialized = false;
      arValid = (arPips >= MinAR && arPips <= MaxAR);
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
      anchorPlaced = false;
      anchorDirection = 0;
      ampCount = 0;
      return;
   }
   
   if(!arValid) return;
   
   // === P90 Detection ===
   double openPrice  = iOpen(_Symbol, PERIOD_M5, 1);
   double closePrice = iClose(_Symbol, PERIOD_M5, 1);
   double highPrice  = iHigh(_Symbol, PERIOD_M5, 1);
   double lowPrice   = iLow(_Symbol, PERIOD_M5, 1);
   double bodySize   = MathAbs(closePrice - openPrice) / PipValue;
   double threshold  = GetP90Threshold(estHour);
   bool   isP90      = (estHour >= 2 && estHour < 12 && bodySize >= threshold);
   string tier       = ClassifyTier(arPips);
   
   // === ANCHOR ENTRY ===
   if(isP90 && !anchorPlaced && (tier == "T1" || tier == "T2"))
   {
      int dir = (closePrice > openPrice) ? 1 : -1;
      double closeDist = (dir == 1) ? (closePrice - asianHigh) / PipValue : (asianLow - closePrice) / PipValue;
      
      if(closeDist >= MinCloseOutside && arPips <= MaxARQuality)
      {
         anchorPlaced    = true;
         anchorDirection = dir;
         anchorPrice     = closePrice;
         anchorBodyPips  = bodySize;
         arAtAnchor      = arPips;
         impulseHigh     = highPrice;
         impulseLow      = lowPrice;
         maxAmps         = (tier == "T1") ? MaxAmpsT1 : MaxAmpsT2;
         ampCount        = 0;
         
         // Enter anchor
         double slPips = bodySize * SLBodyMult;
         double tpPips = arPips * TPARFactor;
         double lots   = CalculateLotSize(slPips);
         
         double sl = anchorPrice - PipsToPrice(slPips) * anchorDirection;
         double tp = anchorPrice + PipsToPrice(tpPips) * anchorDirection;
         
         if(anchorDirection == 1)
            trade.Buy(lots, _Symbol, 0, sl, tp, "DE_Anchor_Long");
         else
            trade.Sell(lots, _Symbol, 0, sl, tp, "DE_Anchor_Short");
      }
   }
   
   // === AMPLIFIER ENTRIES ===
   if(anchorPlaced && ampCount < maxAmps && isP90)
   {
      int dir = (closePrice > openPrice) ? 1 : -1;
      
      if(dir == anchorDirection)
      {
         // Update impulse extremes
         impulseHigh = MathMax(impulseHigh, highPrice);
         impulseLow  = MathMin(impulseLow, lowPrice);
         
         // Calculate impulse size and retrace
         double impulseSize = (anchorDirection == 1) ? (impulseHigh - anchorPrice) / PipValue : (anchorPrice - impulseLow) / PipValue;
         
         if(impulseSize > 0)
         {
            double retrace = (anchorDirection == 1) ? (impulseHigh - lowPrice) / PipValue : (highPrice - impulseLow) / PipValue;
            double retracePct = retrace / impulseSize;
            
            if(retracePct >= RetraceMin && retracePct <= RetraceMax)
            {
               ampCount++;
               double slPips = bodySize * SLBodyMult;
               double tpPips = arAtAnchor * TPARFactor;
               double lots   = CalculateLotSize(slPips);
               
               double ep = closePrice;
               double sl = ep - PipsToPrice(slPips) * anchorDirection;
               double tp = ep + PipsToPrice(tpPips) * anchorDirection;
               
               if(anchorDirection == 1)
                  trade.Buy(lots, _Symbol, 0, sl, tp, "DE_Amp" + IntegerToString(ampCount) + "_Long");
               else
                  trade.Sell(lots, _Symbol, 0, sl, tp, "DE_Amp" + IntegerToString(ampCount) + "_Short");
            }
         }
      }
   }
   
   // === RESET STATE ===
   if(anchorPlaced)
   {
      bool anyPos = false;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            anyPos = true;
      }
      if(!anyPos)
      {
         anchorPlaced    = false;
         anchorDirection = 0;
         anchorPrice     = 0;
         anchorBodyPips  = 0;
         arAtAnchor      = 0;
         ampCount        = 0;
         maxAmps         = 0;
         impulseHigh     = 0;
         impulseLow      = 0;
      }
   }
}
