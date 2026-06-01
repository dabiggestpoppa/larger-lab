#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media;
using System.Xml;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Core;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.SuperDom;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// CEREBUS FX v4.0 — P90 Kinetic Engine (NT8 NinjaScript)
    /// =======================================================
    ///
    /// Model A: P90 Kinetic Engine — All Variants (Initial, Cascade, EWS)
    ///
    /// ENTRY (ALL variants): Immediate close of P90 candle
    ///   - NO pullback wait (unlike Symmetry Trap)
    ///   - NO OCC confirmation (unlike Symmetry Trap)
    ///   - P90 = M5 candle body >= 90th percentile threshold
    ///   - Must ALSO breach Asian Range boundary (both conditions)
    ///
    /// VARIANTS:
    ///   INITIAL (Base 80): First P90 of session
    ///     SL = 80% of P90 body from close
    ///     TP1 = +25% AR, TP2 = +50% AR
    ///
    ///   CASCADE: Same-direction P90 within 120 min of last exit
    ///     SL = 168% of NEW P90 body
    ///     TP1 = +25% AR, TP2 = +50% AR
    ///
    ///   EWS (Exit Warning Signal): Opposite P90 at target
    ///     Force-close existing position, NOT reversal entry
    ///
    /// ENGINE ISOLATION:
    ///   P90 entry + SL NEVER crosses with Symmetry Trap mechanics
    ///   SL is ALWAYS 80% or 168% of P90 body — never Zero-Buffer Extreme
    ///   TP is ALWAYS % of AR — never 1 AU
    ///
    /// Reference: quant-lab/engines/p90_engine.py
    /// Author: CEREBUS Ontology → NT8 Translation (MAD 2026-05-31)
    /// </summary>
    public class CEREBUS_P90_NT8 : Strategy
    {
        #region Enums

        private enum P90State
        {
            SEARCH,
            IN_TRADE
        }

        private enum P90Variant
        {
            INITIAL,
            CASCADE,
            EWS
        }

        private enum P90Direction
        {
            FLAT,
            LONG,
            SHORT
        }

        #endregion

        #region Private Fields

        private P90State _state;
        private P90Direction _dir;
        private P90Variant _variant;

        // Session
        private double _asianHigh;
        private double _asianLow;
        private double _asianRange;
        private bool _rangeLocked;
        private string _tierName;

        // P90 tracking
        private double _p90BodySize;       // Current P90 body in price units
        private double _p90BodyPips;
        private int _p90Count;
        private DateTime _lastExitTime;
        private bool _initialP90Fired;

        // Tier config (AU not used by P90 directly, but needed for classification)
        private double _au;
        private double _trigger;

        // Trade levels
        private double _entry;
        private double _sl;
        private double _tp1;               // -25% AR
        private double _tp2;               // -50% AR (not actively used for NT8 single target)
        private string _entryOrderName;

        // Order tracking for scale-in (dual entry)
        private bool _tp1Hit;
        private double _positionSizeAtTp1;

        // Loop
        private int _loopCount;
        private bool _loopExpired;

        // EWS tracking (opposite P90 while in trade)
        private bool _ewsDetected;

        #endregion

        #region Properties

        [NinjaScriptProperty]
        [Range(1, 5)]
        [Display(Name = "Max Loops/Session", Order = 1, GroupName = "Engine")]
        public int MaxLoops { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [Display(Name = "Quantity", Order = 1, GroupName = "Trade")]
        public int TradeQty { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Asian Start (EST)", Order = 1, GroupName = "Session")]
        public int AsianStartEST { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Asian End (EST)", Order = 2, GroupName = "Session")]
        public int AsianEndEST { get; set; }

        [NinjaScriptProperty]
        [Range(4, 12)]
        [Display(Name = "Loop Timeout (hrs after End)", Order = 3, GroupName = "Session")]
        public int LoopTimeoutHrs { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Daily Reset (EST hour)", Order = 4, GroupName = "Session")]
        public int ResetHourEST { get; set; }

        [NinjaScriptProperty]
        [Range(5, 50)] [Display(Name = "T1 Max AR (pips)", Order = 1, GroupName = "Tier Config")]
        public double T1MaxAR { get; set; }

        [NinjaScriptProperty]
        [Range(1, 30)] [Display(Name = "T1 AU (pips)", Order = 2, GroupName = "Tier Config")]
        public double T1AU { get; set; }

        [NinjaScriptProperty]
        [Range(10, 60)] [Display(Name = "T2 Max AR (pips)", Order = 3, GroupName = "Tier Config")]
        public double T2MaxAR { get; set; }

        [NinjaScriptProperty]
        [Range(1, 30)] [Display(Name = "T2 AU (pips)", Order = 4, GroupName = "Tier Config")]
        public double T2AU { get; set; }

        [NinjaScriptProperty]
        [Range(20, 80)] [Display(Name = "T3 Max AR (pips)", Order = 5, GroupName = "Tier Config")]
        public double T3MaxAR { get; set; }

        [NinjaScriptProperty]
        [Range(1, 40)] [Display(Name = "T3 AU (pips)", Order = 6, GroupName = "Tier Config")]
        public double T3AU { get; set; }

        // P90 Threshold Configuration (per hour, in pips)
        // Default values: EUR/USD reference from 3-month lookback
        [NinjaScriptProperty] [Display(Name = "P90 Thresh 3AM (pips)", Order = 1, GroupName = "P90 Thresholds")]
        public double P90Thresh3 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 4AM (pips)", Order = 2, GroupName = "P90 Thresholds")]
        public double P90Thresh4 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 5AM (pips)", Order = 3, GroupName = "P90 Thresholds")]
        public double P90Thresh5 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 6AM (pips)", Order = 4, GroupName = "P90 Thresholds")]
        public double P90Thresh6 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 7AM (pips)", Order = 5, GroupName = "P90 Thresholds")]
        public double P90Thresh7 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 8AM (pips)", Order = 6, GroupName = "P90 Thresholds")]
        public double P90Thresh8 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 9AM (pips)", Order = 7, GroupName = "P90 Thresholds")]
        public double P90Thresh9 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 10AM (pips)", Order = 8, GroupName = "P90 Thresholds")]
        public double P90Thresh10 { get; set; }

        [NinjaScriptProperty] [Display(Name = "P90 Thresh 11AM (pips)", Order = 9, GroupName = "P90 Thresholds")]
        public double P90Thresh11 { get; set; }

        #endregion

        #region State Change

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "CEREBUS_P90_NT8";
                Description = "CEREBUS P90 Kinetic Engine v4.0 — Model A";
                Calculate = Calculate.OnBarClose;
                BarsRequiredToTrade = 5;
                IsExitOnSessionCloseStrategy = false;

                MaxLoops = 1;
                TradeQty = 1;

                AsianStartEST = 19;
                AsianEndEST = 3;
                LoopTimeoutHrs = 9;
                ResetHourEST = 12;

                T1MaxAR = 20.0; T1AU = 10.0;
                T2MaxAR = 30.0; T2AU = 12.0;
                T3MaxAR = 45.0; T3AU = 15.0;

                // EUR/USD reference thresholds (pips) — from CEREBUS_AssetPresets
                // For other assets, use CEREBUS_AssetPresets.GetPreset(symbol)
                // or manually adjust P90Thresh parameters in NT8 Strategy Settings
                P90Thresh3 = 4.6; P90Thresh4 = 4.2; P90Thresh5 = 3.8;
                P90Thresh6 = 3.5; P90Thresh7 = 3.2; P90Thresh8 = 3.0;
                P90Thresh9 = 2.8; P90Thresh10 = 2.6; P90Thresh11 = 2.4;

                DisplayInDataBox = true;
                DrawOnPriceMarkers = true;
                DrawDataGrid = true;
            }
            else if (State == State.DataLoaded)
            {
                _state = P90State.SEARCH;
                _dir = P90Direction.FLAT;
                _variant = P90Variant.INITIAL;
            }
        }

        #endregion

        #region OnBarUpdate

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BarsRequiredToTrade)
                return;

            double estHour = GetESTHour();

            // ── Daily Reset ──
            if ((int)estHour == ResetHourEST)
            {
                DoDailyReset();
                return;
            }

            // ── Asian: accumulate range ──
            if (IsAsianSession(estHour) && !_rangeLocked)
            {
                if (High[0] > _asianHigh) _asianHigh = High[0];
                if (Low[0] < _asianLow || _asianLow == 0) _asianLow = Low[0];
                return;
            }

            // ── Lock range at session end ──
            if (IsAsianEnd(estHour) && !_rangeLocked)
            {
                LockRange();
                return;
            }

            if (!_rangeLocked)
                return;

            // ── Loop timeout ──
            if (IsPastTimeout(estHour) && !_loopExpired)
            {
                _loopExpired = true;
                Print("CEREBUS_P90: Loop expired.");
                ResetToSearch();
                return;
            }

            // ── Main Logic ──
            switch (_state)
            {
                case P90State.SEARCH:
                    DoSearch(estHour);
                    break;
                case P90State.IN_TRADE:
                    DoInTrade();
                    break;
            }
        }

        #endregion

        #region SEARCH

        private void DoSearch(double estHourDouble)
        {
            if (!IsTradingWindow(estHourDouble))
                return;

            int estHour = (int)estHourDouble;
            double close = Close[0];
            double body = Math.Abs(close - Open[0]);
            double threshold = GetP90Threshold(estHour);

            // ── P90 Validation: body >= threshold AND boundary breach ──
            if (body >= threshold)
            {
                // Check boundary breach
                bool breachUp = close > _asianHigh;
                bool breachDown = close < _asianLow;

                if (!breachUp && !breachDown)
                    return; // P90 body but no breach = elastic, ignore

                // ── Determine variant ──
                P90Variant variant = DetectVariant(estHour);

                // ── EWS: opposite P90 at target while flat — just log, no entry ──
                // (EWS only matters when IN_TRADE)

                // ── Direction ──
                P90Direction dir = breachUp ? P90Direction.LONG : P90Direction.SHORT;

                // ── Calculate trade levels ──
                _p90BodySize = body;
                _p90BodyPips = body / TickSize;
                _entry = close;
                _variant = variant;
                _dir = dir;

                double arPips = _asianRange / TickSize;
                double slOffset;
                double arTarget1;
                double arTarget2;

                if (variant == P90Variant.CASCADE)
                {
                    slOffset = body * 1.68;
                    arTarget1 = _asianRange * 0.25;
                    arTarget2 = _asianRange * 0.50;
                }
                else // INITIAL
                {
                    slOffset = body * 0.80;
                    arTarget1 = _asianRange * 0.25;
                    arTarget2 = _asianRange * 0.50;
                }

                if (dir == P90Direction.LONG)
                {
                    _sl = _entry - slOffset;
                    _tp1 = _entry + arTarget1;
                    _tp2 = _entry + arTarget2;
                }
                else
                {
                    _sl = _entry + slOffset;
                    _tp1 = _entry - arTarget1;
                    _tp2 = _entry - arTarget2;
                }

                _state = P90State.IN_TRADE;
                _tp1Hit = false;
                SubmitEntry();

                Draw.HorizontalLine(this, "P90Entry_" + CurrentBar, false, _entry,
                    Brushes.Yellow, DashStyleHelper.Solid, 2);
                Draw.HorizontalLine(this, "P90SL_" + CurrentBar, false, _sl,
                    Brushes.Red, DashStyleHelper.Dash, 1);
                Draw.HorizontalLine(this, "P90TP1_" + CurrentBar, false, _tp1,
                    Brushes.Cyan, DashStyleHelper.Dash, 1);
                Draw.HorizontalLine(this, "P90TP2_" + CurrentBar, false, _tp2,
                    Brushes.Lime, DashStyleHelper.Dash, 1);

                Print("CEREBUS_P90: " + dir.ToString() + " " + variant.ToString() +
                      " | E=" + _entry.ToString("F5") + " SL=" + _sl.ToString("F5") +
                      " TP1=" + _tp1.ToString("F5") + " TP2=" + _tp2.ToString("F5") +
                      " | P90=" + _p90BodyPips.ToString("F1") + "t | AR=" + arPips.ToString("F0") + "t");
            }
        }

        #endregion

        #region IN_TRADE

        private void DoInTrade()
        {
            double close = Close[0];
            double high = High[0];
            double low = Low[0];

            // ── EWS Detection: opposite P90 while in trade ──
            if (DetectOppositeP90())
            {
                Print("CEREBUS_P90: EWS detected | Force close");
                ExitTrade("EWS");
                Draw.Diamond(this, "EWS_" + CurrentBar, false, close, Brushes.Magenta);
                NextLoop();
                return;
            }

            if (_dir == P90Direction.LONG)
            {
                // TP1 hit
                if (high >= _tp1 && !_tp1Hit)
                {
                    _tp1Hit = true;
                    _positionSizeAtTp1 = Position.Quantity;
                    // Move SL to breakeven (entry)
                    if (_entry > _sl)
                    {
                        SetStopLoss("P90_L_L" + _loopCount, CalculationMode.Price, _entry, false);
                    }
                    Print("CEREBUS_P90: LONG TP1 hit | " + _tp1.ToString("F5") + " | SL moved to BE");
                    Draw.Diamond(this, "TP1_" + CurrentBar, false, _tp1, Brushes.Cyan);
                }

                // TP2 hit (full exit)
                if (high >= _tp2)
                {
                    ExitTrade("TP2");
                    Draw.Diamond(this, "TP2_" + CurrentBar, false, _tp2, Brushes.Lime);
                    Print("CEREBUS_P90: LONG TP2 | " + _tp2.ToString("F5"));
                    NextLoop();
                    return;
                }

                // SL hit
                if (low <= _sl)
                {
                    ExitTrade("SL");
                    Draw.Diamond(this, "SL_" + CurrentBar, false, _sl, Brushes.Red);
                    Print("CEREBUS_P90: LONG SL | " + _sl.ToString("F5"));
                    NextLoop();
                    return;
                }
            }
            else if (_dir == P90Direction.SHORT)
            {
                // TP1 hit
                if (low <= _tp1 && !_tp1Hit)
                {
                    _tp1Hit = true;
                    _positionSizeAtTp1 = Position.Quantity;
                    if (_entry < _sl)
                    {
                        SetStopLoss("P90_S_L" + _loopCount, CalculationMode.Price, _entry, false);
                    }
                    Print("CEREBUS_P90: SHORT TP1 hit | " + _tp1.ToString("F5") + " | SL moved to BE");
                    Draw.Diamond(this, "TP1_" + CurrentBar, false, _tp1, Brushes.Cyan);
                }

                // TP2 hit (full exit)
                if (low <= _tp2)
                {
                    ExitTrade("TP2");
                    Draw.Diamond(this, "TP2_" + CurrentBar, false, _tp2, Brushes.Lime);
                    Print("CEREBUS_P90: SHORT TP2 | " + _tp2.ToString("F5"));
                    NextLoop();
                    return;
                }

                // SL hit
                if (high >= _sl)
                {
                    ExitTrade("SL");
                    Draw.Diamond(this, "SL_" + CurrentBar, false, _sl, Brushes.Red);
                    Print("CEREBUS_P90: SHORT SL | " + _sl.ToString("F5"));
                    NextLoop();
                    return;
                }
            }
        }

        #endregion

        #region Variant Detection

        private P90Variant DetectVariant(int estHour)
        {
            // Cascade: same-dir P90 within 120 min of last exit
            if (_lastExitTime != DateTime.MinValue && _initialP90Fired)
            {
                double minSinceExit = (Times[0][0] - _lastExitTime).TotalMinutes;
                if (minSinceExit <= 120.0)
                {
                    Print("CEREBUS_P90: CASCADE detected | " + minSinceExit.ToString("F0") + "min since exit");
                    return P90Variant.CASCADE;
                }
            }

            if (!_initialP90Fired)
                _initialP90Fired = true;

            return P90Variant.INITIAL;
        }

        private bool DetectOppositeP90()
        {
            // EWS: Opposite P90 prints at/beyond TP1
            // Simplified: if current candle body is >= threshold in opposite direction
            // and price is at/beyond TP1 — trigger exit
            if (!_tp1Hit) return false; // Only check after TP1

            double close = Close[0];
            double body = Math.Abs(close - Open[0]);
            int estHour = (int)GetESTHour();
            double threshold = GetP90Threshold(estHour);

            if (body < threshold) return false;

            if (_dir == P90Direction.LONG && close < Open[0])
                return true; // Opposite (bearish) P90 while LONG
            if (_dir == P90Direction.SHORT && close > Open[0])
                return true; // Opposite (bullish) P90 while SHORT

            return false;
        }

        #endregion

        #region Trade Execution

        private void SubmitEntry()
        {
            _entryOrderName = "P90_" + _dir.ToString() + "_" + _variant.ToString() + "_L" + _loopCount + "_" + CurrentBar;

            if (_dir == P90Direction.LONG)
            {
                EnterLong(TradeQty, _entryOrderName);
                SetStopLoss(_entryOrderName, CalculationMode.Price, _sl, false);
                SetProfitTarget(_entryOrderName, CalculationMode.Price, _tp1, false);
            }
            else if (_dir == P90Direction.SHORT)
            {
                EnterShort(TradeQty, _entryOrderName);
                SetStopLoss(_entryOrderName, CalculationMode.Price, _sl, false);
                SetProfitTarget(_entryOrderName, CalculationMode.Price, _tp1, false);
            }
        }

        private void ExitTrade(string reason)
        {
            if (Position.MarketPosition == MarketPosition.Long)
                ExitLong("Close_" + reason + "_" + CurrentBar, _entryOrderName);
            else if (Position.MarketPosition == MarketPosition.Short)
                ExitShort("Close_" + reason + "_" + CurrentBar, _entryOrderName);
        }

        #endregion

        #region Loop Management

        private void NextLoop()
        {
            _lastExitTime = Times[0][0];
            _loopCount++;
            _p90Count++;
            if (_loopCount > MaxLoops)
                Print("CEREBUS_P90: All " + MaxLoops + " loop(s) complete.");
            ResetToSearch();
        }

        private void ResetToSearch()
        {
            _state = P90State.SEARCH;
            _dir = P90Direction.FLAT;
            _variant = P90Variant.INITIAL;
            _sl = 0;
            _tp1 = 0;
            _tp2 = 0;
            _entry = 0;
            _p90BodySize = 0;
            _p90BodyPips = 0;
            _tp1Hit = false;
        }

        private void DoDailyReset()
        {
            ResetToSearch();
            _loopCount = 0;
            _loopExpired = false;
            _rangeLocked = false;
            _asianHigh = 0;
            _asianLow = 0;
            _asianRange = 0;
            _au = 0;
            _trigger = 0;
            _initialP90Fired = false;
            _lastExitTime = DateTime.MinValue;
            _tierName = "";
            _p90Count = 0;
            Print("CEREBUS_P90: ═══ DAILY RESET " + ResetHourEST + ":00 EST ═══");
        }

        #endregion

        #region Session Range

        private void LockRange()
        {
            _asianRange = _asianHigh - _asianLow;
            double rangePips = _asianRange / TickSize;

            if (rangePips <= T1MaxAR)
            {
                _au = T1AU * TickSize;
                _tierName = "T1";
                Print("CEREBUS_P90: T1 | AR=" + rangePips.ToString("F0") + "t | AU=" + T1AU.ToString("F1") + "p");
            }
            else if (rangePips <= T2MaxAR)
            {
                _au = T2AU * TickSize;
                _tierName = "T2";
                Print("CEREBUS_P90: T2 | AR=" + rangePips.ToString("F0") + "t | AU=" + T2AU.ToString("F1") + "p");
            }
            else if (rangePips <= T3MaxAR)
            {
                _au = T3AU * TickSize;
                _tierName = "T3";
                Print("CEREBUS_P90: T3 | AR=" + rangePips.ToString("F0") + "t | AU=" + T3AU.ToString("F1") + "p");
            }
            else
            {
                _au = 0;
                Print("CEREBUS_P90: NO-GO | AR=" + rangePips.ToString("F0") + "t > T3 (" + T3MaxAR.ToString("F0") + "t)");
                return;
            }

            _rangeLocked = true;

            Draw.HorizontalLine(this, "PAH", false, _asianHigh, Brushes.Cyan, DashStyleHelper.Dot, 1);
            Draw.HorizontalLine(this, "PAL", false, _asianLow, Brushes.Cyan, DashStyleHelper.Dot, 1);
        }

        #endregion

        #region P90 Threshold Lookup

        private double GetP90Threshold(int hour)
        {
            // Per-hour P90 thresholds (in price units)
            // NOTE: Default values are EUR/USD calibrated (3-month lookback).
            // For other assets, scale proportionally by k-factor:
            //   GBPUSD: ~1.3x, USDCHF: ~1.1x, indices/crypto: ~1.0-1.1x
            // Adjust P90Thresh parameters in NT8 Strategy Settings per asset.
            switch (hour)
            {
                case 3: return P90Thresh3 * TickSize;
                case 4: return P90Thresh4 * TickSize;
                case 5: return P90Thresh5 * TickSize;
                case 6: return P90Thresh6 * TickSize;
                case 7: return P90Thresh7 * TickSize;
                case 8: return P90Thresh8 * TickSize;
                case 9: return P90Thresh9 * TickSize;
                case 10: return P90Thresh10 * TickSize;
                case 11: return P90Thresh11 * TickSize;
                default: return 999 * TickSize; // Outside window = no entry
            }
        }

        #endregion

        #region Time Helpers

        private double GetESTHour()
        {
            return Time[0].Hour + Time[0].Minute / 60.0;
        }

        private bool IsAsianSession(double estHour)
        {
            if (AsianStartEST > AsianEndEST)
                return estHour >= AsianStartEST || estHour < AsianEndEST;
            return estHour >= AsianStartEST && estHour < AsianEndEST;
        }

        private bool IsAsianEnd(double estHour)
        {
            return (int)estHour == AsianEndEST;
        }

        private bool IsTradingWindow(double estHour)
        {
            if (IsAsianSession(estHour)) return false;
            if (estHour >= ResetHourEST) return false;

            int expiry = (AsianEndEST + LoopTimeoutHrs) % 24;
            if (expiry > AsianEndEST)
                return estHour >= AsianEndEST && estHour < expiry;
            return estHour >= AsianEndEST || estHour < expiry;
        }

        private bool IsPastTimeout(double estHour)
        {
            int expiry = (AsianEndEST + LoopTimeoutHrs) % 24;
            if (expiry > AsianEndEST)
                return estHour >= expiry && estHour < ResetHourEST;
            return estHour >= expiry && estHour < ResetHourEST;
        }

        #endregion

        #region OnExecution / OnPosition

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price,
            int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order != null && execution.Order.OrderState == OrderState.Filled)
            {
                if (execution.Order.Name != null && execution.Order.Name.Contains("Close"))
                    ResetToSearch();
            }
        }

        protected override void OnPositionUpdate(Position position, double averagePrice, int quantity,
            MarketPosition marketPosition)
        {
            if (marketPosition == MarketPosition.Flat && _state == P90State.IN_TRADE)
                ResetToSearch();
        }

        #endregion
    }
}
