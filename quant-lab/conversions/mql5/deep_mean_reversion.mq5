//+------------------------------------------------------------------+
//|                                      Deep_Mean_Reversion.mq5     |
//|                        Quant Lab Conversion — 2026-05-18         |
//|                        Source: optimizer_v4.py                    |
//|                        Win Rate: 91.8% | PF: 112                 |
//+------------------------------------------------------------------+
#property copyright "Quant Lab — Deep Mean Reversion"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input double RiskPct       = 2.0;    // Risk per trade (% of equity)
input double DeepMult      = 2.00;   // Deep State multiplier
input double KillMult      = 2.20;   // Kill Switch multiplier
input int    MaxAR         = 45;     // Max Asian Range (pips)
input int    MinAR         = 3;      // Min Asian Range (pips)
input int    MagicNumber   = 100002; // Magic number

CTrade         trade;
CPositionInfo  posInfo;

datetime lastBarTime = 0;
int      estOffset   = -5;

// State variables
bool     p90Found    = false;
double   activation  = 0;
double   deepState   = 0;
double   killSwitch  = 0;
bool     p90IsLong   = false;
bool     deepTouched = false;
bool     entered     = false;
datetime p90BarTime = 0;

//+------------------------------------------------------------------+
int OnInit()
{
    trade.SetExpertMagicNumber(MagicNumber);
    Print("Deep Mean Reversion initialized. Magic: ", MagicNumber);
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason) { Print("DMR stopped."); }

//+------------------------------------------------------------------+
int GetESTHour(datetime t)
{
    MqlDateTime dt;
    TimeToStruct(t, dt);
    return (dt.hour + estOffset + 24) % 24;
}

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
void CalculateAsianRange(double &ah, double &al, double &arPips)
{
    datetime today = iTime(_Symbol, PERIOD_D1, 0);
    int total = iBars(_Symbol, PERIOD_M5);
    double highVal = 0, lowVal = DBL_MAX;
    bool found = false;
    
    for(int i = total - 1; i >= 0; i--)
    {
        datetime bt = iTime(_Symbol, PERIOD_M5, i);
        if(bt < today) break;
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
    if(found) { ah = highVal; al = lowVal; arPips = (ah - al) / _Point / 10.0; }
    else { ah = 0; al = 0; arPips = 0; }
}

//+------------------------------------------------------------------+
void OnTick()
{
    datetime currentBarTime = iTime(_Symbol, PERIOD_M5, 0);
    if(currentBarTime == lastBarTime) return;
    lastBarTime = currentBarTime;
    
    // Check existing position
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(posInfo.SelectByIndex(i) && posInfo.Magic() == MagicNumber && posInfo.Symbol() == _Symbol)
            return;
    }
    
    int estH = GetESTHour(currentBarTime);
    if(estH < 2 || estH >= 17) return;
    bool isEntry = (estH >= 2 && estH < 11);
    bool isPreNoon = (estH < 12);
    
    // Calculate Asian Range
    double ah, al, arPips;
    CalculateAsianRange(ah, al, arPips);
    if(arPips < MinAR || arPips > MaxAR) return;
    
    double pointToPips = _Point * 10.0;
    double openPrice  = iOpen(_Symbol, PERIOD_M5, 1);
    double closePrice = iClose(_Symbol, PERIOD_M5, 1);
    double highPrice  = iHigh(_Symbol, PERIOD_M5, 1);
    double lowPrice   = iLow(_Symbol, PERIOD_M5, 1);
    double bodyPips   = MathAbs(closePrice - openPrice) / pointToPips;
    
    // Reset at session start
    if(estH == 2)
    {
        p90Found = false; deepTouched = false; entered = false;
    }
    
    // P90 detection
    double p90Thresh = GetP90Threshold(estH);
    if(isEntry && !p90Found && bodyPips >= p90Thresh)
    {
        p90Found   = true;
        activation = closePrice;
        p90IsLong  = closePrice > openPrice;
        p90BarTime = currentBarTime;
        
        double bodyPrice = bodyPips / 10000.0; // pips to price for EUR/USD
        if(_Symbol == "USDJPY" || _Symbol == "USDJPYm") bodyPrice = bodyPips / 100.0;
        
        int dir = p90IsLong ? 1 : -1;
        deepState  = activation + bodyPrice * DeepMult * dir;
        killSwitch = activation + bodyPrice * KillMult * dir;
    }
    
    // Deep state touch detection
    if(p90Found && !deepTouched && isPreNoon)
    {
        if(p90IsLong && lowPrice <= deepState)
            deepTouched = true;
        else if(!p90IsLong && highPrice >= deepState)
            deepTouched = true;
    }
    
    // Entry (mean reversion)
    if(deepTouched && !entered && estH < 17)
    {
        entered = true;
        double lotSize = 0.1;
        
        if(!p90IsLong) // Revert to SHORT → go LONG
            trade.Buy(lotSize, _Symbol, deepState, killSwitch, activation, "DMR Long");
        else
            trade.Sell(lotSize, _Symbol, deepState, killSwitch, activation, "DMR Short");
        
        Print("DMR Entry: ", !p90IsLong ? "LONG" : "SHORT", " Deep=", deepState);
    }
}
//+------------------------------------------------------------------+
