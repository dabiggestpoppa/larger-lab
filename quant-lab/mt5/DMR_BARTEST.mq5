//+------------------------------------------------------------------+
//| DMR_BARTEST.mq5 — Simple bar counter to test Strategy Tester     |
//+------------------------------------------------------------------+
#property copyright "Test"
#property version   "1.00"
#property strict

int tickCount = 0;
int lastBars = 0;

int OnInit()
{
   Print("=== BARTEST INIT ===");
   Print("Symbol: ", _Symbol);
   Print("Period: ", Period());
   Print("Digits: ", _Digits);
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   tickCount++;
   int bars = iBars(_Symbol, PERIOD_M5);
   
   if(bars != lastBars || tickCount <= 5)
   {
      Print("Tick ", tickCount, " | Bars: ", bars, " | Time: ", TimeCurrent());
      lastBars = bars;
   }
}

void OnDeinit(const int reason)
{
   Print("=== BARTEST DEINIT ===");
   Print("Total ticks: ", tickCount);
   Print("Final bars: ", iBars(_Symbol, PERIOD_M5));
}
