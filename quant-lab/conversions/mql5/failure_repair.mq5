//+------------------------------------------------------------------+
//| Failure Repair — CEREBUS FX v4.0                                  |
//| Performance: 50.0% WR, +817p, PF 1.81                             |
//|                                                                    |
//| Logic: When an initial breakout from the Asian range fails         |
//| (price returns to the Asian band), wait for a second breakout      |
//| attempt in the same direction. The "repair" of the failed move     |
//| often produces a strong continuation.                              |
//+------------------------------------------------------------------+
#property copyright "Quant Lab"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

// === INPUTS ===
input double AsianRangeMin    = 3.0;    // Asian Range Min (pips)
input double AsianRangeMax    = 45.0;   // Asian Range Max (pips)
input double SLBodyMult       = 1.0;    // SL Body Multiplier
input double TPARFactor       = 0.50;   // TP AR Factor
input int    FailWindowBars   = 12;     // Failure Window (5min bars)
input int    HoldWindowBars   = 12;     // Hold Window (5min bars)
input double RiskPerTradePct  = 0.25;   // Risk per trade (% of equity)
input int    MagicNumber      = 30001;  // Magic Number

// === GLOBALS ===
CTrade trade;
double PipValue;
int    DigitsAdjust;

// State machine states
// 0=idle, 1=first_signal, 2=failed, 3=second_signal, 4=entered
int    state            = 0;
int    firstDirection   = 0;    // 1=LONG, -1=SHORT
double entryPrice       = 0;
double slLevel          = 0;
double tpLevel          = 0;
double bodyPipsAtEntry  = 0;
int    barsSinceFirst   = 0;
int    barsSinceSecond  = 0;

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
   PipValue     = _Point * 10;
   DigitsAdjust = 1;
   if(_Digits <= 3)
   {
      PipValue = _Point;
      DigitsAdjust = 1;
   }
   
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
   if(estHour >= 0  && estHour < 2)  return 99.0;
   if(estHour >= 2  && estHour < 4)  return 4.1;
   if(estHour >= 4  && estHour < 8)  return 4.6;
   if(estHour >= 8  && estHour < 11) return 5.9;
   if(estHour == 11)                 return 6.2;
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
   // Get current EST hour
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
      arValid = (arPips >= AsianRangeMin && arPips <= AsianRangeMax);
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
      state = 0;
      return;
   }
   
   // === P90 Detection ===
   if(!arValid) return;
   
   double openPrice  = iOpen(_Symbol, PERIOD_M5, 1);
   double closePrice = iClose(_Symbol, PERIOD_M5, 1);
   double highPrice  = iHigh(_Symbol, PERIOD_M5, 1);
   double lowPrice   = iLow(_Symbol, PERIOD_M5, 1);
   double bodySize   = MathAbs(closePrice - openPrice) / PipValue;
   double threshold  = GetP90Threshold(estHour);
   bool   isP90      = (estHour >= 3 && estHour < 12 && bodySize >= threshold);
   
   // === STATE 0: IDLE — Look for first P90 signal ===
   if(state == 0 && isP90)
   {
      int dir = (closePrice > openPrice) ? 1 : -1;
      if((dir == 1 && closePrice > asianHigh) || (dir == -1 && closePrice < asianLow))
      {
         firstDirection = dir;
         state = 1;
         barsSinceFirst = 0;
      }
   }
   
   // === STATE 1: FIRST SIGNAL — Check for failure ===
   if(state == 1)
   {
      barsSinceFirst++;
      double c = iClose(_Symbol, PERIOD_M5, 1);
      
      if(firstDirection == 1 && c < asianHigh)
         state = 2;
      else if(firstDirection == -1 && c > asianLow)
         state = 2;
      
      if(barsSinceFirst > FailWindowBars)
         state = 0;
   }
   
   // === STATE 2: FAILED — Look for second P90 in same direction ===
   if(state == 2 && isP90)
   {
      int dir = (closePrice > openPrice) ? 1 : -1;
      if(dir == firstDirection)
      {
         entryPrice = closePrice;
         bodyPipsAtEntry = bodySize;
         state = 3;
         barsSinceSecond = 0;
      }
   }
   
   // === STATE 3: SECOND SIGNAL — Hold test ===
   if(state == 3)
   {
      barsSinceSecond++;
      double c = iClose(_Symbol, PERIOD_M5, 1);
      bool holdOK = true;
      
      if(firstDirection == 1 && c < asianLow)
         holdOK = false;
      else if(firstDirection == -1 && c > asianHigh)
         holdOK = false;
      
      if(!holdOK)
      {
         state = 0;
      }
      else if(barsSinceSecond >= HoldWindowBars)
      {
         // Hold test passed — ENTER TRADE
         double bodyInPrice = bodyPipsAtEntry * PipValue;
         double sign = firstDirection;
         
         slLevel = entryPrice - bodyInPrice * SLBodyMult * sign;
         tpLevel = entryPrice + PipsToPrice(arPips * TPARFactor) * sign;
         
         double slPips = MathAbs(entryPrice - slLevel) / PipValue;
         double lots   = CalculateLotSize(slPips);
         
         if(firstDirection == 1)
            trade.Buy(lots, _Symbol, 0, slLevel, tpLevel, "FR_Long");
         else
            trade.Sell(lots, _Symbol, 0, slLevel, tpLevel, "FR_Short");
         
         state = 4;
      }
   }
   
   // === STATE 4: IN TRADE — Reset after close ===
   if(state == 4)
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
         state = 0;
         entryPrice = 0;
         slLevel = 0;
         tpLevel = 0;
      }
   }
}
