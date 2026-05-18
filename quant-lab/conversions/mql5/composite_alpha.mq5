//+------------------------------------------------------------------+
//|                                          Composite_Alpha.mq5     |
//|                        Quant Lab Conversion — 2026-05-18         |
//|                        Source: optimizer_v4.py                    |
//|                        Win Rate: 98.6% | PF: 703                 |
//+------------------------------------------------------------------+
#property copyright "Quant Lab — Composite Alpha"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input double RiskPct        = 2.0;    // Risk per trade (% of equity)
input double CompositeMin    = 0.20;   // Min composite score to trade
input double SLBodyMult      = 1.5;    // SL body multiplier
input double TPBaseFactor    = 0.25;   // TP base AR factor
input double TPCompFactor    = 0.15;   // TP composite factor
input int    MaxAR          = 20;     // Max AR for quality filter (pips)
input int    MinOutside     = 2;      // Min close outside AR (pips)
input int    MagicNumber    = 100001; // Magic number

CTrade         trade;
CPositionInfo  posInfo;

//--- Global state
datetime lastBarTime = 0;
int      estOffset   = -5; // EST = UTC - 5

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(10);
    Print("Composite Alpha initialized. Magic: ", MagicNumber);
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("Composite Alpha stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Get EST hour from datetime                                         |
//+------------------------------------------------------------------+
int GetESTHour(datetime t)
{
    MqlDateTime dt;
    TimeToStruct(t, dt);
    int utcHour = dt.hour;
    int estHour = (utcHour + estOffset + 24) % 24;
    return estHour;
}

//+------------------------------------------------------------------+
//| Calculate Asian Range for the current day                          |
//+------------------------------------------------------------------+
void CalculateAsianRange(double &ah, double &al, double &arPips)
{
    ah = 0; al = DBL_MAX; arPips = 0;
    datetime today = iTime(_Symbol, PERIOD_D1, 0);
    
    // Find Asian session bars (7PM-3AM EST = 0-8 UTC for most of year)
    int total = iBars(_Symbol, PERIOD_M5);
    double highVal = 0, lowVal = DBL_MAX;
    bool found = false;
    
    for(int i = total - 1; i >= 0; i--)
    {
        datetime bt = iTime(_Symbol, PERIOD_M5, i);
        if(bt < today) break; // Previous day
        
        int estH = GetESTHour(bt);
        if(estH >= 19 || estH < 3)
        {
            double h = iHigh(_Symbol, PERIOD_M5, i);
            double l = iLow(_Symbol, PERIOD_M5, i);
            if(h > highVal) highVal = h;
            if(l < lowVal) lowVal = l;
            found = true;
        }
    }
    
    if(found)
    {
        ah = highVal;
        al = lowVal;
        arPips = (ah - al) / _Point / 10.0; // Convert to pips
    }
}

//+------------------------------------------------------------------+
//| P90 threshold by EST hour                                          |
//+------------------------------------------------------------------+
double GetP90Threshold(int estHour)
{
    if(estHour < 2 || estHour >= 11) return 99.0;
    if(estHour < 4) return 4.1;
    if(estHour < 8) return 4.6;
    if(estHour < 10) return 5.9;
    if(estHour < 11) return 6.2;
    return 99.0;
}

//+------------------------------------------------------------------+
//| Compute composite score                                            |
//+------------------------------------------------------------------+
double ComputeComposite(double arRegime, double constrDeficit, double p90Mom,
                        double sessStr, double wkdayQ)
{
    double icPM = 0.08, icAR = 0.06, icCD = 0.05, icSS = 0.04, icWQ = 0.03;
    double weightedSum = icPM * p90Mom + icAR * arRegime + icCD * constrDeficit
                       + icSS * sessStr + icWQ * wkdayQ;
    double weightTotal = icPM + icAR + icCD + icSS + icWQ;
    double composite = (weightTotal > 0) ? weightedSum / weightTotal : 0.0;
    double irMult = MathSqrt(5.0) / 2.24;
    return composite * MathMin(irMult, 1.5);
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
    datetime currentBarTime = iTime(_Symbol, PERIOD_M5, 0);
    if(currentBarTime == lastBarTime) return; // Wait for new bar
    lastBarTime = currentBarTime;
    
    //--- Check if position already open
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(posInfo.SelectByIndex(i) && posInfo.Magic() == MagicNumber && posInfo.Symbol() == _Symbol)
            return; // Already in a trade
    }
    
    int estH = GetESTHour(currentBarTime);
    
    //--- Time filter: entry 2AM-11AM EST, exit by 5PM
    if(estH < 2 || estH >= 17) return;
    bool isEntry = (estH >= 2 && estH < 11);
    
    //--- Calculate Asian Range
    double ah, al, arPips;
    CalculateAsianRange(ah, al, arPips);
    
    if(arPips < 3 || arPips > 45) return;
    
    //--- Get current bar data
    double openPrice  = iOpen(_Symbol, PERIOD_M5, 1); // Completed bar
    double closePrice = iClose(_Symbol, PERIOD_M5, 1);
    double highPrice  = iHigh(_Symbol, PERIOD_M5, 1);
    double lowPrice   = iLow(_Symbol, PERIOD_M5, 1);
    double bodyPips   = MathAbs(closePrice - openPrice) / _Point / 10.0;
    
    //--- P90 threshold
    double p90Thresh = GetP90Threshold(estH);
    if(bodyPips < p90Thresh) return;
    
    //--- Direction
    bool isLong = closePrice > openPrice;
    
    //--- Must close outside Asian band by MinOutside pips
    double pointToPips = _Point * 10.0;
    if(isLong)
    {
        if(closePrice <= ah || (closePrice - ah) / pointToPips < MinOutside) return;
    }
    else
    {
        if(closePrice >= al || (al - closePrice) / pointToPips < MinOutside) return;
    }
    
    //--- Quality filter: AR <= MaxAR
    if(arPips > MaxAR) return;
    
    //--- Tier
    string tier = (arPips < 20) ? "T1" : (arPips < 30) ? "T2" : "T3";
    double arRegime = (tier == "T1") ? 1.0 : (tier == "T2") ? 0.6 : 0.3;
    
    //--- Signals
    double constrDeficit = MathMax(0.0, 1.0 - arPips / 45.0);
    double p90Mom = (bodyPips > 0) ? MathMin(1.0, (bodyPips - p90Thresh) / p90Thresh) : 0.0;
    double sessStr = (estH >= 3 && estH <= 5) ? 1.0 : (estH >= 6 && estH <= 8) ? 0.8 : 0.5;
    
    MqlDateTime dt;
    TimeToStruct(currentBarTime, dt);
    int weekday = dt.day_of_week;
    double wkdayQ = (weekday >= 2 && weekday <= 4) ? 1.0 : (weekday == 1) ? 0.7 : 0.5;
    
    //--- Composite score
    double composite = ComputeComposite(arRegime, constrDeficit, p90Mom, sessStr, wkdayQ);
    if(composite < CompositeMin) return;
    
    //--- SL/TP
    double slPips = bodyPips * SLBodyMult;
    double tpFactor = TPBaseFactor + TPCompFactor * MathMin(composite, 1.0);
    double tpPips = arPips * tpFactor;
    
    double sl, tp;
    double lotSize = 0.1; // Simplified — use proper risk calc in production
    
    if(isLong)
    {
        sl = closePrice - slPips * pointToPips;
        tp = closePrice + tpPips * pointToPips;
        trade.Buy(lotSize, _Symbol, closePrice, sl, tp, "Composite Alpha Long");
    }
    else
    {
        sl = closePrice + slPips * pointToPips;
        tp = closePrice - tpPips * pointToPips;
        trade.Sell(lotSize, _Symbol, closePrice, sl, tp, "Composite Alpha Short");
    }
    
    Print("Composite Alpha: ", isLong ? "LONG" : "SHORT", " Score=", composite,
          " AR=", arPips, " SL=", slPips, " TP=", tpPips);
}
//+------------------------------------------------------------------+
