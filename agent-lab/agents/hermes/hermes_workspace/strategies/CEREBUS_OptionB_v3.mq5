//+------------------------------------------------------------------+
//| CEREBUS_OptionB.mq5 — Continuous Loop Super Scalper              |
//| CEREBUS FX v4 Manual page 187+                                   |
//+------------------------------------------------------------------+
#property copyright "Hermes AI — CEREBUS Manual"
#property version   "3.00"
#property strict

input double   InpLotSize       = 0.1;
input int      InpMagicNum      = 123456;
input int      InpTierTrigger   = 19;
input int      InpStopLoss      = 15;
input int      InpTakeProfit    = 19;
input bool     InpUseSession    = true;
input int      InpMaxLoops      = 8;
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M5;

#include <Trade/Trade.mqh>
CTrade trade;

datetime g_lastExitTime = 0;
int      g_loopCount   = 0;
bool     g_inSession   = false;

int OnInit() {
   trade.SetExpertMagicNumber(InpMagicNum);
   trade.SetDeviationInPoints(10);
   Print("CEREBUS Option B v3 initialized.");
   return(INIT_SUCCEEDED);
}

bool IsSessionActive() {
   datetime now = TimeCurrent();
   int hourEST = (TimeHour(now) - 5 + 24) % 24;
   return (hourEST < 12);
}

double GetImpulsePips() {
   double o = iOpen(_Symbol, InpTimeframe, 1);
   double c = iClose(_Symbol, InpTimeframe, 1);
   return MathAbs(c - o) / _Point;
}

bool InDensityZone(double price) {
   double zh = iHigh(_Symbol, InpTimeframe, 1);
   double zl = iLow(_Symbol, InpTimeframe, 1);
   return (price >= zl && price <= zh);
}

int CountPositions() {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNum)
         count++;
   return count;
}

void OnTick() {
   bool sessionActive = IsSessionActive();
   if(!sessionActive && g_inSession) {
      g_loopCount = 0;
      g_inSession = false;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
         if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNum)
            trade.PositionClose(PositionGetTicket(i));
      return;
   }
   g_inSession = sessionActive;
   if(!sessionActive) return;
   if(g_loopCount >= InpMaxLoops) return;
   if(CountPositions() > 0) return;
   if(Bars(_Symbol, InpTimeframe) < 3) return;

   double impulse = GetImpulsePips();
   double prevClose = iClose(_Symbol, InpTimeframe, 1);
   double prevOpen  = iOpen(_Symbol, InpTimeframe, 1);

   if(impulse >= InpTierTrigger * 10) {
      if(prevClose > prevOpen) {
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         if(InDensityZone(ask)) {
            double sl = ask - InpStopLoss * 10 * _Point;
            double tp = ask + InpTakeProfit * 10 * _Point;
            if(trade.Buy(InpLotSize, _Symbol, ask, sl, tp, "CEREBUS_B")) {
               g_loopCount++;
               Print("BUY loop ", g_loopCount, "/", InpMaxLoops);
            }
         }
      } else if(prevClose < prevOpen) {
         double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         if(InDensityZone(bid)) {
            double sl = bid + InpStopLoss * 10 * _Point;
            double tp = bid - InpTakeProfit * 10 * _Point;
            if(trade.Sell(InpLotSize, _Symbol, bid, sl, tp, "CEREBUS_B")) {
               g_loopCount++;
               Print("SELL loop ", g_loopCount, "/", InpMaxLoops);
            }
         }
      }
   }
}
//+------------------------------------------------------------------+
