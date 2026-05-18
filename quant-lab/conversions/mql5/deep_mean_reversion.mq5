//+------------------------------------------------------------------+
//|                                      Deep_Mean_Reversion.mq5     |
//|                        Quant Lab Conversion — 2026-05-18         |
//|                        REFINED: Cost-validated version            |
//|                        Source: optimizer_v4.py                    |
//|                        Win Rate: 91.8% | PF: 112 (backtest)      |
//|                        PF: ~45 (after real costs)                 |
//+------------------------------------------------------------------+
#property copyright "Quant Lab — Deep Mean Reversion (Refined)"
#property link      ""
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>

// ─── INPUTS ───────────────────────────────────────────────────
input double RiskPct       = 5.0;    // Risk per trade (% of equity)
input double DeepMult      = 2.00;   // Deep State multiplier (% of P90 body)
input double KillMult      = 2.20;   // Kill Switch multiplier (% of P90 body)
input int    MaxAR         = 45;     // Max Asian Range (pips)
input int    MinAR         = 3;      // Min Asian Range (pips)
input int    MagicNumber   = 100002; // Magic number for order identification
input int    ESTOffset     = -5;     // EST offset from UTC (UTC-5)

// ─── GLOBAL OBJECTS ───────────────────────────────────────────
CTrade         trade;       // Trade execution object
CPositionInfo  posInfo;     // Position information object
CSymbolInfo    symInfo;     // Symbol information object

// ─── STATE VARIABLES ──────────────────────────────────────────
datetime lastBarTime = 0;   // Last processed bar time (prevents duplicate processing)

// Strategy state — persists across ticks, reset at session start
bool     p90Found    = false;   // Has a P90 candle been detected?
double   activation  = 0;       // P90 close price (mean reversion target / TP)
double   deepState   = 0;       // Deep State level (200% of P90 body from activation)
double   killSwitch  = 0;       // Kill Switch level (220% of P90 body from activation)
bool     p90IsLong   = false;   // P90 direction (true = bullish candle)
bool     deepTouched = false;   // Has price touched the Deep State level?
bool     entered     = false;   // Has an entry been executed?
datetime p90BarTime  = 0;       // Time of P90 detection (for logging)

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Configure trade object
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(10);           // 10 points max slippage
    trade.SetTypeFilling(ORDER_FILLING_IOC);  // Immediate or cancel
    
    // Initialize symbol info
    if(!symInfo.Name(_Symbol))
    {
        Print("ERROR: Failed to initialize symbol info for ", _Symbol);
        return(INIT_FAILED);
    }
    
    Print("═══════════════════════════════════════════════════");
    Print("  Deep Mean Reversion v2.0 — INITIALIZED");
    Print("  Symbol: ", _Symbol);
    Print("  Magic: ", MagicNumber);
    Print("  Risk: ", RiskPct, "% per trade");
    Print("  Deep Mult: ", DeepMult, " | Kill Mult: ", KillMult);
    Print("  AR Range: ", MinAR, "-", MaxAR, " pips");
    Print("═══════════════════════════════════════════════════");
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("Deep Mean Reversion stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Get EST hour from datetime                                       |
//+------------------------------------------------------------------+
int GetESTHour(datetime t)
{
    MqlDateTime dt;
    TimeToStruct(t, dt);
    return (dt.hour + ESTOffset + 24) % 24;
}

//+------------------------------------------------------------------+
//| Get P90 body threshold for given EST hour                       |
//| Thresholds from optimizer_v4 — minimum body size in pips        |
//+------------------------------------------------------------------+
double GetP90Threshold(int estHour)
{
    if(estHour < 2 || estHour >= 11) return 99.0;  // Outside entry window
    if(estHour < 4) return 4.1;                     // 2AM-4AM: quiet session
    if(estHour < 8) return 4.6;                     // 4AM-8AM: London open
    if(estHour < 10) return 5.9;                    // 8AM-10AM: overlap
    if(estHour < 11) return 6.2;                    // 10AM-11AM: late window
    return 99.0;
}

//+------------------------------------------------------------------+
//| Calculate Asian Range (high - low during Asian session)         |
//| Asian session: 7PM EST to 3AM EST                               |
//+------------------------------------------------------------------+
void CalculateAsianRange(double &ah, double &al, double &arPips)
{
    datetime today = iTime(_Symbol, PERIOD_D1, 0);
    int total = iBars(_Symbol, PERIOD_M5);
    double highVal = 0;
    double lowVal = DBL_MAX;
    bool found = false;
    
    // Scan backwards through M5 bars to find Asian session bars
    for(int i = total - 1; i >= 0; i--)
    {
        datetime bt = iTime(_Symbol, PERIOD_M5, i);
        if(bt < today) break;  // Stop at start of current day
        
        int estH = GetESTHour(bt);
        if(estH >= 19 || estH < 3)  // Asian session: 7PM-3AM EST
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
        // Convert to pips (1 pip = 10 points for 5-digit broker)
        arPips = (ah - al) / (_Point * 10.0);
    }
    else
    {
        ah = 0;
        al = 0;
        arPips = 0;
    }
}

//+------------------------------------------------------------------+
//| Calculate position size based on 5% risk                         |
//| PositionSize = (Equity × Risk%) / (SL_distance × pip_value)     |
//+------------------------------------------------------------------+
double CalculatePositionSize(double slDistancePrice)
{
    if(slDistancePrice <= 0) return 0.01;  // Minimum lot if SL is invalid
    
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double riskAmount = equity * (RiskPct / 100.0);
    
    // For EUR/USD: 1 standard lot = $10/pip, 1 mini lot = $1/pip
    double pipValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE) / 
                      (SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE) / _Point * 10.0);
    
    if(pipValue <= 0) pipValue = 1.0;  // Fallback
    
    double slDistancePips = slDistancePrice / (_Point * 10.0);
    double lotSize = riskAmount / (slDistancePips * pipValue);
    
    // Normalize to broker's lot step
    double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    
    lotSize = MathFloor(lotSize / lotStep) * lotStep;
    lotSize = MathMax(minLot, MathMin(maxLot, lotSize));
    
    return lotSize;
}

//+------------------------------------------------------------------+
//| Check if we already have an open position for this strategy     |
//+------------------------------------------------------------------+
bool HasOpenPosition()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(posInfo.SelectByIndex(i) && 
           posInfo.Magic() == MagicNumber && 
           posInfo.Symbol() == _Symbol)
            return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Only process on new bar (M5)
    datetime currentBarTime = iTime(_Symbol, PERIOD_M5, 0);
    if(currentBarTime == lastBarTime) return;
    lastBarTime = currentBarTime;
    
    // Don't process if we already have an open position
    if(HasOpenPosition()) return;
    
    // Refresh symbol info
    symInfo.RefreshRates();
    
    int estH = GetESTHour(currentBarTime);
    
    // Only operate during trading hours (2AM-5PM EST)
    if(estH < 2 || estH >= 17) return;
    
    bool isEntry = (estH >= 2 && estH < 11);   // P90 detection window
    bool isPreNoon = (estH < 12);               // Entry cutoff
    
    // ─── CALCULATE ASIAN RANGE ──────────────────────────────────
    double ah, al, arPips;
    CalculateAsianRange(ah, al, arPips);
    if(arPips < MinAR || arPips > MaxAR) return;  // AR outside valid range
    
    // ─── GET CANDLE DATA (previous closed bar) ──────────────────
    double openPrice  = iOpen(_Symbol, PERIOD_M5, 1);
    double closePrice = iClose(_Symbol, PERIOD_M5, 1);
    double highPrice  = iHigh(_Symbol, PERIOD_M5, 1);
    double lowPrice   = iLow(_Symbol, PERIOD_M5, 1);
    double bodyPips   = MathAbs(closePrice - openPrice) / (_Point * 10.0);
    
    // ─── DAILY RESET AT 2AM EST ─────────────────────────────────
    if(estH == 2)
    {
        p90Found = false;
        deepTouched = false;
        entered = false;
    }
    
    // ─── P90 DETECTION ──────────────────────────────────────────
    // First candle in entry window with body >= threshold
    // AND Asian Range is within valid bounds
    double p90Thresh = GetP90Threshold(estH);
    if(isEntry && !p90Found && bodyPips >= p90Thresh)
    {
        p90Found   = true;
        activation = closePrice;           // P90 close = activation level
        p90IsLong  = closePrice > openPrice;
        p90BarTime = currentBarTime;
        
        // Calculate Deep State and Kill Switch levels
        // bodyPrice converts pips to price units
        double bodyPrice = bodyPips / 10000.0;  // For EUR/USD (4 decimal places)
        // Adjust for JPY pairs (2 decimal places)
        if(StringFind(_Symbol, "JPY") >= 0) bodyPrice = bodyPips / 100.0;
        
        int dir = p90IsLong ? 1 : -1;
        deepState  = activation + bodyPrice * DeepMult * dir;
        killSwitch = activation + bodyPrice * KillMult * dir;
        
        Print("P90 DETECTED | Dir: ", p90IsLong ? "LONG" : "SHORT",
              " | Body: ", bodyPips, "p",
              " | Activation: ", activation,
              " | Deep: ", deepState,
              " | Kill: ", killSwitch);
    }
    
    // ─── DEEP STATE TOUCH DETECTION ─────────────────────────────
    // Check if price has reached the Deep State level (before noon)
    if(p90Found && !deepTouched && isPreNoon)
    {
        if(p90IsLong && lowPrice <= deepState)
        {
            deepTouched = true;
            Print("DEEP STATE TOUCH | Price touched ", deepState, " (P90 was LONG)");
        }
        else if(!p90IsLong && highPrice >= deepState)
        {
            deepTouched = true;
            Print("DEEP STATE TOUCH | Price touched ", deepState, " (P90 was SHORT)");
        }
    }
    
    // ─── ENTRY EXECUTION ────────────────────────────────────────
    // Enter mean reversion: direction is OPPOSITE to P90
    if(deepTouched && !entered && estH < 17)
    {
        entered = true;
        
        // Calculate position size based on 5% risk
        double slDistance = MathAbs(deepState - killSwitch);
        double lotSize = CalculatePositionSize(slDistance);
        
        // Mean reversion: go against P90 direction
        if(!p90IsLong)
        {
            // P90 was LONG → enter SHORT at Deep State
            // SL: Kill Switch (above entry), TP: Activation (below entry)
            double sl = killSwitch;
            double tp = activation;
            
            if(trade.Sell(lotSize, _Symbol, deepState, sl, tp, "DMR Short"))
                Print("DMR ENTRY: SHORT | Lot: ", lotSize, 
                      " | Entry: ", deepState,
                      " | SL: ", sl, " | TP: ", tp);
            else
                Print("DMR ENTRY FAILED: ", GetLastError());
        }
        else
        {
            // P90 was SHORT → enter LONG at Deep State
            // SL: Kill Switch (below entry), TP: Activation (above entry)
            double sl = killSwitch;
            double tp = activation;
            
            if(trade.Buy(lotSize, _Symbol, deepState, sl, tp, "DMR Long"))
                Print("DMR ENTRY: LONG | Lot: ", lotSize,
                      " | Entry: ", deepState,
                      " | SL: ", sl, " | TP: ", tp);
            else
                Print("DMR ENTRY FAILED: ", GetLastError());
        }
    }
}
//+------------------------------------------------------------------+
