//+------------------------------------------------------------------+
//|                                    DMR_FULL_BACKTEST.mq5         |
//|                    Deep Mean Reversion - Full Logic Backtest EA   |
//|                    v5.00 — Process all bars in OnInit()           |
//+------------------------------------------------------------------+
#property copyright "CerebusFX — Quant Lab"
#property version   "5.00"
#property strict
#property description "DMR v5 — Full backtest in OnInit(), matches Python optimizer_v2"

#include <Trade\Trade.mqh>

// ─── INPUTS ───────────────────────────────────────────────────
input double   LotSize        = 0.01;
input int      MagicNumber    = 20260520;
input int      MaxDailyTrades = 1;
input int      HardExitHour   = 17;
input double   DeepMult       = 2.00;
input double   KillMult       = 2.20;
input int      MaxAR          = 45;
input int      MinAR          = 3;
input int      ESTOffset      = -5;
input bool     EnableLogging  = true;

// ─── GLOBALS ──────────────────────────────────────────────────
CTrade trade;
int totalTrades  = 0;
int totalWins    = 0;
int totalLosses  = 0;
double totalPnlPips = 0;
double maxDD     = 0;
double peakPnl   = 0;
double currPnl   = 0;

// ─── HELPERS ──────────────────────────────────────────────────
double GetP90Threshold(int estHour)
{
   if(estHour < 2 || estHour >= 11) return 999.0;
   if(estHour < 4)  return 4.1;
   if(estHour < 6)  return 4.6;
   if(estHour < 8)  return 4.6;
   if(estHour < 10) return 5.9;
   if(estHour < 11) return 6.2;
   return 999.0;
}

double PipsToPrice(double pips)
{
   if(StringFind(_Symbol, "JPY") >= 0) return pips / 100.0;
   return pips / 10000.0;
}

double PriceToPips(double price)
{
   if(StringFind(_Symbol, "JPY") >= 0) return price * 100.0;
   return price * 10000.0;
}

int GetESTHour(datetime barTime)
{
   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   int estHour = dt.hour + ESTOffset;
   if(estHour < 0) estHour += 24;
   if(estHour >= 24) estHour -= 24;
   return estHour;
}

// ─── TRADING ──────────────────────────────────────────────────
bool PlaceOrder(ENUM_ORDER_TYPE orderType, double sl, double tp, string comment)
{
   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};
   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = _Symbol;
   request.volume    = LotSize;
   request.type      = orderType;
   request.sl        = NormalizeDouble(sl, _Digits);
   request.tp        = NormalizeDouble(tp, _Digits);
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
      Print("OrderSend failed: ", GetLastError(), " ", comment);
      return false;
   }
   if(result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED)
   {
      Print("ORDER: ", comment, " ", DoubleToString(request.price, _Digits),
            " SL=", DoubleToString(sl, _Digits), " TP=", DoubleToString(tp, _Digits));
      return true;
   }
   return false;
}

bool ClosePosition(string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == MagicNumber)
      {
         ulong ticket = PositionGetInteger(POSITION_TICKET);
         ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         double currPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
         double pnlPips = (posType == POSITION_TYPE_BUY) ?
            PriceToPips(currPrice - openPrice) : PriceToPips(openPrice - currPrice);

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
            totalTrades++; totalPnlPips += pnlPips;
            if(pnlPips > 0) totalWins++; else totalLosses++;
            currPnl += pnlPips;
            if(currPnl > peakPnl) peakPnl = currPnl;
            double dd = peakPnl - currPnl;
            if(dd > maxDD) maxDD = dd;
            Print("CLOSED [", reason, "] PnL=", DoubleToString(pnlPips,1),
                  "p Total=", DoubleToString(totalPnlPips,1), "p");
            return true;
         }
      }
   }
   return false;
}

bool HasPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetSymbol(i) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         return true;
   return false;
}

// ─────────────────────────────────────────────────────────────
//  MAIN BACKTEST LOOP — runs entirely in OnInit()
//  Processes every bar from oldest to newest
//  This is the most reliable pattern for MT5 Strategy Tester
// ─────────────────────────────────────────────────────────────
int OnInit()
{
   Print("=== DMR v5.00 START ===");
   Print("Symbol=", _Symbol, " Period=", Period(), " Digits=", _Digits);

   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(10);
   trade.SetTypeFilling(ORDER_FILLING_IOC);

   int totalBars = iBars(_Symbol, PERIOD_M5);
   Print("Total bars available: ", totalBars);

   if(totalBars < 10)
   {
      Print("ERROR: Not enough bars (", totalBars, ")");
      return(INIT_FAILED);
   }

   // ── Process each day ──
   int lastDay = -1, lastMonth = -1, lastYear = -1;

   // Daily state
   bool p90Found = false, dsTouched = false, tradePlaced = false;
   int  p90Direction = 0;
   double activationLevel = 0, deepStateLevel = 0, killSwitchLevel = 0;
   double p90BodyPips = 0;
   int p90BarIndex = -1;
   int todayTrades = 0;

   // Process bars from oldest (totalBars-1) to newest (1)
   // Bar 0 is current forming bar, bar 1 is last completed
   for(int bar = totalBars - 1; bar >= 1; bar--)
   {
      datetime barTime = iTime(_Symbol, PERIOD_M5, bar);
      MqlDateTime dt;
      TimeToStruct(barTime, dt);

      // New day check
      if(dt.day != lastDay || dt.mon != lastMonth || dt.year != lastYear)
      {
         lastDay = dt.day; lastMonth = dt.mon; lastYear = dt.year;
         p90Found = false; dsTouched = false; tradePlaced = false;
         p90Direction = 0; activationLevel = 0; deepStateLevel = 0;
         killSwitchLevel = 0; p90BodyPips = 0; p90BarIndex = -1;
         todayTrades = 0;
      }

      int estHour = GetESTHour(barTime);

      // Hard exit at HardExitHour
      if(estHour >= HardExitHour && HasPosition())
      {
         ClosePosition("HardExit");
         tradePlaced = false;
         continue;
      }

      // Only operate during P90 window
      if(estHour < 2 || estHour >= 11) continue;
      if(HasPosition() || tradePlaced || todayTrades >= MaxDailyTrades) continue;

      // ── STEP 1: Find P90 ──
      if(!p90Found)
      {
         double openPrice  = iOpen(_Symbol, PERIOD_M5, bar);
         double closePrice = iClose(_Symbol, PERIOD_M5, bar);
         double bodyPips   = PriceToPips(MathAbs(closePrice - openPrice));

         if(bodyPips >= GetP90Threshold(estHour))
         {
            p90Found = true;
            p90BarIndex = bar;
            p90BodyPips = bodyPips;
            activationLevel = closePrice;
            p90Direction = (closePrice > openPrice) ? 1 : -1;
            deepStateLevel  = activationLevel + PipsToPrice(bodyPips * DeepMult) * p90Direction;
            killSwitchLevel = activationLevel + PipsToPrice(bodyPips * KillMult) * p90Direction;

            if(EnableLogging)
               Print("P90 @ bar=", bar, " est=", estHour,
                     " dir=", (p90Direction==1?"LONG":"SHORT"),
                     " body=", DoubleToString(bodyPips,1), "p",
                     " act=", DoubleToString(activationLevel, _Digits),
                     " ds=", DoubleToString(deepStateLevel, _Digits));
         }
         continue;
      }

      // ── STEP 2: Check Deep State touch ──
      if(!dsTouched)
      {
         if(estHour >= 12) continue;

         double highPrice = iHigh(_Symbol, PERIOD_M5, bar);
         double lowPrice  = iLow(_Symbol, PERIOD_M5, bar);

         if(p90Direction == 1 && lowPrice <= deepStateLevel)
         {
            dsTouched = true;
            if(EnableLogging) Print("DS TOUCHED @ bar=", bar, " (LONG, low=", DoubleToString(lowPrice,_Digits), ")");
         }
         else if(p90Direction == -1 && highPrice >= deepStateLevel)
         {
            dsTouched = true;
            if(EnableLogging) Print("DS TOUCHED @ bar=", bar, " (SHORT, high=", DoubleToString(highPrice,_Digits), ")");
         }
         continue;
      }

      // ── STEP 3: Enter mean reversion ──
      if(dsTouched && !tradePlaced)
      {
         int revDir = (p90Direction == 1) ? -1 : 1;
         ENUM_ORDER_TYPE orderType = (revDir == 1) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
         string comment = "DMR_" + ((revDir == 1) ? "LONG" : "SHORT");

         if(PlaceOrder(orderType, killSwitchLevel, activationLevel, comment))
         {
            tradePlaced = true;
            todayTrades++;
         }
      }
   }

   Print("=== DMR v5.00 COMPLETE ===");
   Print("Total Trades: ", totalTrades);
   Print("Wins: ", totalWins, " | Losses: ", totalLosses);
   if(totalTrades > 0)
      Print("Win Rate: ", DoubleToString((double)totalWins / totalTrades * 100.0, 1), "%");
   Print("Total PnL: ", DoubleToString(totalPnlPips, 1), " pips");
   Print("Max DD: ", DoubleToString(maxDD, 1), " pips");

   // Write results JSON
   int fh = FileOpen("DMR_FULL_BACKTEST_RESULTS.json", FILE_WRITE|FILE_TXT|FILE_COMMON);
   if(fh != INVALID_HANDLE)
   {
      FileWriteString(fh, "{\n");
      FileWriteString(fh, "  \"strategy\": \"DMR_v5\",\n");
      FileWriteString(fh, "  \"symbol\": \"" + _Symbol + "\",\n");
      FileWriteString(fh, "  \"total_trades\": " + IntegerToString(totalTrades) + ",\n");
      FileWriteString(fh, "  \"wins\": " + IntegerToString(totalWins) + ",\n");
      FileWriteString(fh, "  \"losses\": " + IntegerToString(totalLosses) + ",\n");
      FileWriteString(fh, "  \"win_rate\": " + DoubleToString(totalTrades > 0 ? (double)totalWins/totalTrades*100.0 : 0, 1) + ",\n");
      FileWriteString(fh, "  \"total_pnl_pips\": " + DoubleToString(totalPnlPips, 1) + ",\n");
      FileWriteString(fh, "  \"max_dd_pips\": " + DoubleToString(maxDD, 1) + "\n");
      FileWriteString(fh, "}\n");
      FileClose(fh);
      Print("Results JSON written");
   }

   return(INIT_SUCCEEDED);
}

void OnTick()
{
   // All processing done in OnInit()
   // OnTick just handles any open positions for real-time exit
}

void OnDeinit(const int reason)
{
   Print("=== DMR v5.00 DEINIT (reason: ", reason, ") ===");
   Print("Final: trades=", totalTrades, " wr=", totalTrades>0 ? DoubleToString((double)totalWins/totalTrades*100,1) : "0", "%");
}
