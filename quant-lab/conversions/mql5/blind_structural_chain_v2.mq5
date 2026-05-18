//+------------------------------------------------------------------+
//|                                Blind_Structural_Chain_v2.mq5    |
//|                        Quant Lab Conversion — 2026-05-18         |
//|                        FIXED: Cost-validated version              |
//|                        Source: optimizer_v4.py                    |
//|                        v1: 43.1% WR, PF 1.14 (fails)            |
//|                        v2 Expected: ~58-62% WR, PF 1.6-2.0      |
//+------------------------------------------------------------------+
#property copyright "Quant Lab — Blind Structural Chain v2"
#property link      ""
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>

// ─── INPUTS ───────────────────────────────────────────────────
input double RiskPct        = 5.0;    // Risk per trade (% of equity)
input double PullbackMin    = 0.35;   // Pullback minimum (35%)
input double PullbackMax    = 0.45;   // Pullback maximum (45%)
input double Invalidation   = 0.60;   // Invalidation threshold (60%, was 80%)
input double SLBuffer       = 5.0;    // SL buffer in pips
input double TPFactor       = 0.80;   // TP as factor of impulse size
input int    ImpulseThresh  = 12;     // Impulse threshold in pips
input int    MaxCycles      = 2;      // Max cycles per day (was 3)
input int    MaxHoldBars    = 24;     // Max hold bars (24 × 5min = 2 hours)
input int    MAPeriod       = 200;    // MA period for trend filter
input bool   UseTrendFilter = true;   // Use 200 MA trend filter
input int    MagicNumber    = 100005; // Magic number
input int    ESTOffset      = -5;     // EST offset from UTC

// ─── GLOBAL OBJECTS ───────────────────────────────────────────
CTrade         trade;
CPositionInfo  posInfo;
CSymbolInfo    symInfo;

// ─── STATE VARIABLES ──────────────────────────────────────────
datetime lastBarTime = 0;

bool     impulseFound  = false;
double   baseline      = 0;
double   impulseHigh   = 0;
double   impulseLow    = 0;
double   impulseSize   = 0;
bool     impulseIsLong = false;
int      cycleCount    = 0;
int      entryBar      = 0;
bool     entered       = false;
int      lastDate      = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_IOC);
    symInfo.Name(_Symbol);
    Print("BSC v2 initialized. Risk: ", RiskPct, "%, MA Period: ", MAPeriod);
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    datetime currentTime = iTime(_Symbol, PERIOD_M5, 0);
    if (currentTime == lastBarTime) return;
    lastBarTime = currentTime;

    MqlDateTime dt;
    TimeToStruct(currentTime, dt);
    int estHour = (dt.hour + ESTOffset + 24) % 24;
    int currentDate = dt.day * 100 + dt.mon;

    // ─── BASELINE (3AM EST) ─────────────────────────────────────
    if (estHour == 3 && currentDate != lastDate)
    {
        baseline    = iClose(_Symbol, PERIOD_M5, 0);
        lastDate    = currentDate;
        impulseFound = false;
        entered     = false;
        cycleCount  = 0;
        Print("BSC: New baseline set at 3AM: ", baseline);
    }

    if (baseline == 0) return;

    // ─── 200 MA ────────────────────────────────────────────────
    double ma200 = iMA(_Symbol, PERIOD_M5, MAPeriod, 0, MODE_SMA, PRICE_CLOSE, 0);
    bool trendUp = close > ma200;
    bool trendDown = close < ma200;

    // ─── IMPULSE DETECTION ──────────────────────────────────────
    double close = iClose(_Symbol, PERIOD_M5, 0);
    double high  = iHigh(_Symbol, PERIOD_M5, 0);
    double low   = iLow(_Symbol, PERIOD_M5, 0);

    if (!impulseFound && cycleCount < MaxCycles)
    {
        double movePips = (close - baseline) / (_Point * 10);
        if (MathAbs(movePips) >= ImpulseThresh)
        {
            impulseFound  = true;
            impulseIsLong = movePips > 0;
            impulseSize   = MathAbs(movePips);
            impulseHigh   = high;
            impulseLow    = low;
            Print("BSC: Impulse detected. Direction: ", impulseIsLong ? "LONG" : "SHORT", " Size: ", impulseSize, "p");
        }
    }

    // ─── PULLBACK ENTRY ─────────────────────────────────────────
    if (impulseFound && !entered && cycleCount < MaxCycles)
    {
        double retracePips = 0;
        if (impulseIsLong)
            retracePips = (impulseHigh - low) / (_Point * 10);
        else
            retracePips = (high - impulseLow) / (_Point * 10);

        double retracePct = retracePips / impulseSize;

        bool validPullback = (retracePct >= PullbackMin && retracePct <= PullbackMax);
        bool notInvalidated = (retracePct < Invalidation);
        bool confirmCandle = impulseIsLong ? (close > iOpen(_Symbol, PERIOD_M5, 0)) : (close < iOpen(_Symbol, PERIOD_M5, 0));
        bool trendOK = !UseTrendFilter || (impulseIsLong && trendUp) || (!impulseIsLong && trendDown);

        if (validPullback && notInvalidated && confirmCandle && trendOK)
        {
            double slBuffer = SLBuffer * _Point * 10;
            double impulsePrice = impulseSize * _Point * 10;
            double ask = symInfo.Ask();
            double bid = symInfo.Bid();
            double equity = AccountInfoDouble(ACCOUNT_EQUITY);
            double riskAmount = equity * RiskPct / 100.0;

            if (impulseIsLong)
            {
                double sl = impulseLow - slBuffer;
                double tp = close + impulsePrice * TPFactor;
                double slDist = ask - sl;
                double lots = riskAmount / (slDist / _Point * 10 * SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE));
                lots = NormalizeDouble(MathMin(lots, 1.0), 2);
                if (trade.Buy(lots, _Symbol, ask, sl, tp, "BSC v2 Long"))
                {
                    entered = true;
                    entryBar = Bars(_Symbol, PERIOD_M5);
                    cycleCount++;
                    Print("BSC: LONG entry. Lots: ", lots, " SL: ", sl, " TP: ", tp);
                }
            }
            else
            {
                double sl = impulseHigh + slBuffer;
                double tp = close - impulsePrice * TPFactor;
                double slDist = sl - bid;
                double lots = riskAmount / (slDist / _Point * 10 * SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE));
                lots = NormalizeDouble(MathMin(lots, 1.0), 2);
                if (trade.Sell(lots, _Symbol, bid, sl, tp, "BSC v2 Short"))
                {
                    entered = true;
                    entryBar = Bars(_Symbol, PERIOD_M5);
                    cycleCount++;
                    Print("BSC: SHORT entry. Lots: ", lots, " SL: ", sl, " TP: ", tp);
                }
            }
        }
    }

    // ─── TIME-BASED EXIT (2 HOURS) ─────────────────────────────
    if (entered && !posInfo.SelectByMagic(MagicNumber))
    {
        entered = false;
        impulseFound = false;
    }

    if (entered && (Bars(_Symbol, PERIOD_M5) - entryBar) >= MaxHoldBars)
    {
        trade.PositionClose(_Symbol);
        entered = false;
        impulseFound = false;
        Print("BSC: Time-based exit (2 hours)");
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("BSC v2 deinitialized. Reason: ", reason);
}
