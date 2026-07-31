//+------------------------------------------------------------------+
//| DMR_FULL_BACKTEST.mq5 - Deep Mean Reversion EA                    |
//| Strategy Tester compatible - indexed bar processing              |
//| Ported from Nautilus Trader (strategies/dmr_strategy.py)         |
//| OC2 | 2026-05-28                                                   |
//+------------------------------------------------------------------+
#property copyright "OC2 2026"
#property version   "3.0"
#property strict

input double   LotSize        = 0.01;    // Lot size
input int      MagicNumber    = 20260528;// Magic number
input double   DeepMult       = 2.0;     // Deep State multiplier
input double   KillMult       = 2.2;     // Kill Switch multiplier
input int      MinAR          = 3;       // Min Asian Range (pips)
input int      MaxAR          = 45;      // Max Asian Range (pips)
input int      ESTOffset      = -5;      // EST = UTC + offset (EST = UTC-5)
input int      HardExitHour   = 17;      // Hard exit hour (EST)
input int      MaxDailyTrades = 1;       // Max trades per day
input bool     EnableLogging  = true;    // Enable logging

//--- Global daily state
int      g_LastDay        = -1;
int      g_LastMonth      = -1;
int      g_LastYear       = -1;
bool     g_P90Found       = false;
bool     g_DSTouched      = false;
bool     g_TradePlaced    = false;
int      g_P90Direction   = 0;
double   g_ActivationLevel = 0;
double   g_DeepStateLevel  = 0;
double   g_KillSwitchLevel = 0;
double   g_AsianHigh      = 0;
double   g_AsianLow       = 0;
bool     g_AsianLocked    = false;
int      g_P90BarIndex    = -1;
int      g_TodayTrades    = 0;

//--- Statistics
int      g_TotalTrades    = 0;
int      g_TotalWins      = 0;
int      g_TotalLosses    = 0;
double   g_TotalPnlPips   = 0;

//--- P90 thresholds
double GetP90Threshold(int estHour)
{
   if(estHour == 2 || estHour == 3) return 4.1;
   if(estHour >= 4 && estHour <= 6) return 4.6;
   if(estHour == 7 || estHour == 8) return 5.9;
   if(estHour == 9 || estHour == 10) return 6.2;
   return 999.0;
}

double PipsToPrice(double pips) { return pips / 10000.0; }
double PriceToPips(double price) { return price * 10000.0; }

int GetESTHourFromBar(int barIndex)
{
   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, barIndex);
   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   int estHour = dt.hour + ESTOffset;
   if(estHour < 0) estHour += 24;
   return estHour;
}

bool IsNewDayAtBar(int barIndex)
{
   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, barIndex);
   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   if(dt.day != g_LastDay || dt.mon != g_LastMonth || dt.year != g_LastYear)
   {
      g_LastDay = dt.day; g_LastMonth = dt.mon; g_LastYear = dt.year;
      return true;
   }
   return false;
}

void ResetDailyState()
{
   g_P90Found = false; g_DSTouched = false; g_TradePlaced = false;
   g_P90Direction = 0; g_ActivationLevel = 0; g_DeepStateLevel = 0;
   g_KillSwitchLevel = 0; g_AsianHigh = 0; g_AsianLow = 99999.0;
   g_AsianLocked = false; g_P90BarIndex = -1; g_TodayTrades = 0;
}

bool HasPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         return true;
   }
   return false;
}

double GetPositionPnlPips()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
      {
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double currPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
         ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         if(posType == POSITION_TYPE_BUY) return PriceToPips(currPrice - openPrice);
         else return PriceToPips(openPrice - currPrice);
      }
   }
   return 0;
}

//--- Track and lock Asian Range
void TrackAndLockAsianRange(int currentBar, int estHour)
{
   // Track Asian Range (7PM-3AM EST)
   if(estHour >= 19 || estHour < 3)
   {
      double high = iHigh(_Symbol, PERIOD_CURRENT, currentBar);
      double low  = iLow(_Symbol, PERIOD_CURRENT, currentBar);
      if(high > g_AsianHigh) g_AsianHigh = high;
      if(low < g_AsianLow)  g_AsianLow = low;
   }

   // Lock Asian Range at 3AM
   if(estHour == 3 && !g_AsianLocked)
   {
      g_AsianLocked = true;
      double arPips = PriceToPips(g_AsianHigh - g_AsianLow);
      if(EnableLogging)
         Print("DMR: AR LOCKED | Range=", DoubleToString(arPips,1), "p Bounds=[", MinAR, "-", MaxAR, "]");

      if(arPips < MinAR || arPips > MaxAR)
      {
         g_P90Found = true;
         g_TradePlaced = true;
         if(EnableLogging)
            Print("DMR: SKIP DAY | AR out of bounds");
      }
   }
}

bool PlaceOrder(ENUM_ORDER_TYPE orderType, double sl, double tp, string comment)
{
   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};

   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = _Symbol;
   request.volume    = LotSize;
   request.type      = orderType;
   request.deviation = 10;
   request.magic     = MagicNumber;
   request.comment   = comment;
   request.type_filling = ORDER_FILLING_IOC;

   if(orderType == ORDER_TYPE_BUY)
      request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   else
      request.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   if(!OrderSend(request, result))
   {
      if(EnableLogging) Print("DMR: OrderSend failed: ", GetLastError());
      return false;
   }

   if(result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED)
   {
      if(EnableLogging)
         Print("DMR: ORDER PLACED: ", EnumToString(orderType), " @ ", DoubleToString(request.price, _Digits));
      return true;
   }
   return false;
}

bool CloseAllPositions(string reason)
{
   bool closed = false;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
      {
         ulong ticket = PositionGetInteger(POSITION_TICKET);
         ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         double pnlPips = GetPositionPnlPips();

         MqlTradeRequest request = {};
         MqlTradeResult  result  = {};
         request.action    = TRADE_ACTION_DEAL;
         request.symbol    = _Symbol;
         request.volume    = PositionGetDouble(POSITION_VOLUME);
         request.position  = ticket;
         request.deviation = 10;
         request.magic     = MagicNumber;
         request.comment   = reason;
         request.type_filling = ORDER_FILLING_IOC;

         if(posType == POSITION_TYPE_BUY)
            { request.type = ORDER_TYPE_SELL; request.price = SymbolInfoDouble(_Symbol, SYMBOL_BID); }
         else
            { request.type = ORDER_TYPE_BUY; request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK); }

         if(OrderSend(request, result))
         {
            g_TotalTrades++;
            g_TotalPnlPips += pnlPips;
            if(pnlPips > 0) g_TotalWins++; else if(pnlPips < 0) g_TotalLosses++;
            if(EnableLogging)
               Print("DMR: CLOSED [", reason, "] PnL=", DoubleToString(pnlPips,1), "p");
            closed = true;
         }
      }
   }
   return closed;
}

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   ResetDailyState();
   Print("DMR EA v3.0 - Symbol: ", _Symbol, " | Lot: ", LotSize, " | Magic: ", MagicNumber);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("=== DMR FINAL RESULTS ===");
   Print("Total Trades: ", g_TotalTrades);
   Print("Wins: ", g_TotalWins, " | Losses: ", g_TotalLosses);
   if(g_TotalTrades > 0)
      Print("Win Rate: ", DoubleToString((double)g_TotalWins / g_TotalTrades * 100, 1), "%");
   Print("Total PnL: ", DoubleToString(g_TotalPnlPips, 1), " pips");
   Print("==========================");
}

//+------------------------------------------------------------------+
//| Expert tick function - Strategy Tester compatible                 |
//+------------------------------------------------------------------+
void OnTick()
{
   int bar = 1; // Process the last completed bar

   //--- Check for new day
   if(IsNewDayAtBar(bar))
   {
      ResetDailyState();
      if(EnableLogging) Print("DMR: NEW DAY");
   }

   int estHour = GetESTHourFromBar(bar);

   //--- Track and lock Asian Range
   TrackAndLockAsianRange(bar, estHour);

   //--- Hard exit at 5PM EST
   if(estHour >= HardExitHour && HasPosition())
   {
      CloseAllPositions("HardExit");
      g_TradePlaced = false;
      return;
   }

   //--- Trading window: 2AM-11AM EST only
   if(estHour < 2 || estHour >= 11) return;

   //--- Don't trade if already positioned or traded today
   if(HasPosition() || g_TradePlaced || g_TodayTrades >= MaxDailyTrades) return;

   //--- Step 1: Scan for P90
   if(!g_P90Found)
   {
      int totalBars = iBars(_Symbol, PERIOD_CURRENT);
      for(int scanBar = bar; scanBar < totalBars && scanBar - bar < 500; scanBar++)
      {
         int scanEstH = GetESTHourFromBar(scanBar);
         if(scanEstH < 2 || scanEstH >= 11) continue;

         double open  = iOpen(_Symbol, PERIOD_CURRENT, scanBar);
         double close = iClose(_Symbol, PERIOD_CURRENT, scanBar);
         double bodyPips = PriceToPips(MathAbs(close - open));

         if(bodyPips >= GetP90Threshold(scanEstH))
         {
            g_P90Found = true;
            g_P90BarIndex = scanBar;
            g_ActivationLevel = close;
            g_P90Direction = (close > open) ? 1 : -1;
            g_DeepStateLevel = g_ActivationLevel + PipsToPrice(bodyPips * DeepMult) * g_P90Direction;
            g_KillSwitchLevel = g_ActivationLevel + PipsToPrice(bodyPips * KillMult) * g_P90Direction;

            if(EnableLogging)
               Print("DMR: P90 FOUND | Dir=", (g_P90Direction == 1 ? "BULL" : "BEAR"),
                     " Body=", DoubleToString(bodyPips, 1), "p",
                     " DS=", DoubleToString(g_DeepStateLevel, 5),
                     " KS=", DoubleToString(g_KillSwitchLevel, 5));
            break;
         }
      }
      if(!g_P90Found) return;
   }

   //--- Step 2: Check Deep State touch (before noon)
   if(!g_DSTouched)
   {
      int totalBars = iBars(_Symbol, PERIOD_CURRENT);
      for(int checkBar = g_P90BarIndex + 1; checkBar < totalBars && checkBar <= bar; checkBar++)
      {
         int checkEstH = GetESTHourFromBar(checkBar);
         if(checkEstH >= 12) continue;

         double high = iHigh(_Symbol, PERIOD_CURRENT, checkBar);
         double low  = iLow(_Symbol, PERIOD_CURRENT, checkBar);

         if(g_P90Direction == 1 && low <= g_DeepStateLevel)
         {
            g_DSTouched = true;
            if(EnableLogging) Print("DMR: DS TOUCHED | Low=", DoubleToString(low, 5));
            break;
         }
         if(g_P90Direction == -1 && high >= g_DeepStateLevel)
         {
            g_DSTouched = true;
            if(EnableLogging) Print("DMR: DS TOUCHED | High=", DoubleToString(high, 5));
            break;
         }
      }
      if(!g_DSTouched) return;
   }

   //--- Step 3: Place mean reversion entry
   int revDirection = (g_P90Direction == 1) ? -1 : 1;
   ENUM_ORDER_TYPE orderType = (revDirection == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   string comment = "DMR_" + ((revDirection == 1) ? "LONG" : "SHORT");

   if(PlaceOrder(orderType, g_KillSwitchLevel, g_ActivationLevel, comment))
   {
      g_TradePlaced = true;
      g_TodayTrades++;
      if(EnableLogging)
         Print("DMR: TRADE ", comment, " ", LotSize, " lots",
               " SL=", DoubleToString(g_KillSwitchLevel, 5),
               " TP=", DoubleToString(g_ActivationLevel, 5));
   }
}
//+------------------------------------------------------------------+
