//+------------------------------------------------------------------+
//| Blind Structural Chain — CEREBUS FX v4.0                          |
//| Performance: 43.1% WR, +2248p, PF 1.14                            |
//|                                                                    |
//| Logic: Multi-cycle momentum strategy. Identifies impulse moves     |
//| from a baseline, waits for controlled pullbacks (32-50% retrace),  |
//| and enters in the direction of the impulse. Max 3 cycles/day.      |
//+------------------------------------------------------------------+
#property copyright "Quant Lab"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

// === INPUTS ===
input double MaxAR             = 45.0;   // Max AR (pips)
input double MinAR             = 3.0;    // Min AR (pips)
input int    MaxCycles         = 3;      // Max Cycles per Day
input double SLBufferPips      = 5.0;    // SL Buffer (pips)
input double TPImpulseFactor   = 0.80;   // TP Impulse Factor
input double RetraceMin        = 0.32;   // Retrace Min
input double RetraceMax        = 0.50;   // Retrace Max
input double InvalidationPct   = 0.80;   // Invalidation Threshold
input double RiskPerTradePct   = 0.25;   // Risk per trade (% of equity)
input int    MagicNumber       = 30003;  // Magic Number

// === GLOBALS ===
CTrade trade;
double PipValue;

// State variables
double baselinePrice    = 0;
int    cycleCount       = 0;
int    impulseDirection = 0;    // 1=LONG, -1=SHORT
double impulseHigh      = 0;
double impulseLow       = 0;
double impulseSize      = 0;
bool   impulseActive    = false;
bool   waitingForPullback = false;

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
//| Get impulse threshold for tier                                     |
//+------------------------------------------------------------------+
double GetImpulseThreshold(string tier)
{
   if(tier == "T1") return 12.0;
   if(tier == "T2") return 16.0;
   if(tier == "T3") return 20.0;
   return 999.0;
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
      
      // Set baseline at 3AM close
      baselinePrice = iClose(_Symbol, PERIOD_M5, 0);
      cycleCount = 0;
      impulseActive = false;
      waitingForPullback = false;
      impulseDirection = 0;
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
      impulseActive = false;
      return;
   }
   
   if(!arValid || baselinePrice == 0) return;
   if(estHour < 3 || estHour >= 17) return;
   
   string tier = ClassifyTier(arPips);
   double impulseThresh = GetImpulseThreshold(tier);
   
   double highPrice = iHigh(_Symbol, PERIOD_M5, 1);
   double lowPrice  = iLow(_Symbol, PERIOD_M5, 1);
   double closePrice = iClose(_Symbol, PERIOD_M5, 1);
   
   // === IMPULSE DETECTION ===
   if(!impulseActive && !waitingForPullback && cycleCount < MaxCycles)
   {
      double distLong  = (highPrice - baselinePrice) / PipValue;
      double distShort = (baselinePrice - lowPrice) / PipValue;
      
      if(distLong >= impulseThresh)
      {
         impulseDirection = 1;
         impulseHigh      = highPrice;
         impulseLow       = baselinePrice;
         impulseSize      = distLong;
         impulseActive    = true;
      }
      else if(distShort >= impulseThresh)
      {
         impulseDirection = -1;
         impulseHigh      = baselinePrice;
         impulseLow       = lowPrice;
         impulseSize      = distShort;
         impulseActive    = true;
      }
   }
   
   // === PULLBACK DETECTION ===
   if(impulseActive)
   {
      // Update impulse extremes
      if(impulseDirection == 1)
      {
         impulseHigh = MathMax(impulseHigh, highPrice);
         impulseSize = (impulseHigh - baselinePrice) / PipValue;
      }
      else
      {
         impulseLow = MathMin(impulseLow, lowPrice);
         impulseSize = (baselinePrice - impulseLow) / PipValue;
      }
      
      // Calculate retrace
      double retrace = (impulseDirection == 1) ? (impulseHigh - lowPrice) / PipValue : (highPrice - impulseLow) / PipValue;
      double retracePct = (impulseSize > 0) ? retrace / impulseSize : 0;
      
      // Check invalidation
      if(retracePct > InvalidationPct)
      {
         impulseActive    = false;
         impulseDirection = 0;
         impulseHigh      = 0;
         impulseLow       = 0;
         impulseSize      = 0;
      }
      else if(retracePct >= RetraceMin && retracePct <= RetraceMax)
      {
         // Valid pullback — ENTER
         cycleCount++;
         double ep = closePrice;
         
         double sl = (impulseDirection == 1) ? impulseLow - PipsToPrice(SLBufferPips) : impulseHigh + PipsToPrice(SLBufferPips);
         double tp = (impulseDirection == 1) ? ep + PipsToPrice(impulseSize * TPImpulseFactor) : ep - PipsToPrice(impulseSize * TPImpulseFactor);
         
         double slPips = MathAbs(ep - sl) / PipValue;
         double lots   = CalculateLotSize(slPips);
         
         if(impulseDirection == 1)
            trade.Buy(lots, _Symbol, 0, sl, tp, "BSC_Long_C" + IntegerToString(cycleCount));
         else
            trade.Sell(lots, _Symbol, 0, sl, tp, "BSC_Short_C" + IntegerToString(cycleCount));
         
         // Reset for next cycle from entry price
         impulseActive    = false;
         waitingForPullback = false;
         impulseDirection = 0;
         baselinePrice    = ep;  // New baseline from entry
         impulseHigh      = 0;
         impulseLow       = 0;
         impulseSize      = 0;
      }
   }
}
