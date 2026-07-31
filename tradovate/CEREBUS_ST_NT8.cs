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
    /// CEREBUS FX v4.0 — Symmetry Trap Engine (NT8 NinjaScript)
    /// ========================================================
    ///
    /// 4-State FSM: SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE → (reset)
    ///
    /// ENTRY: Impulse → Retrace (>= 1 AU) → OCC (close in impulse direction)
    /// SL: Zero-Buffer Impulse Extreme (close-only)
    /// TP: Exactly 1 AU from entry (single target)
    ///
    /// Reference: quant-lab/engines/symmetry_trap.py
    /// Author: CEREBUS Ontology → NT8 Translation (MAD 2026-05-31)
    /// </summary>
    public class CEREBUS_ST_NT8 : Strategy
    {
        #region Enums

        private enum EngineState { SEARCH, WAIT_RETRACE, WAIT_OCC, IN_TRADE }
        private enum EngineDirection { FLAT, LONG, SHORT }

        #endregion

        #region Private Fields

        private EngineState _state;
        private EngineDirection _dir;

        // Session
        private double _asianHigh;
        private double _asianLow;
        private double _asianRange;
        private bool _rangeLocked;
        private DateTime _lastSessionDate;

        // Tier
        private double _au;
        private double _trigger;

        // Impulse
        private double _origin;
        private double _impulseHigh;
        private double _impulseLow;
        private double _impulseExtreme;
        private double _killLevel;
        private bool _impulseDetected;

        // Retrace/OCC
        private double _retraceHigh;
        private double _retraceLow;
        private bool _retraceDone;

        // Trade levels
        private double _entry;
        private double _sl;
        private double _tp;

        // Loop
        private int _loopCount;
        private bool _loopExpired;

        // Order tracking
        private string _entryOrderName;
        private string _lastEntryName;

        #endregion

        #region Properties

        [NinjaScriptProperty]
        [Range(1, 5)]
        [Display(Name = "Max Loops/Session", Order = 1, GroupName = "Engine")]
        public int MaxLoops { get; set; }

        [NinjaScriptProperty]
        [Range(0.1, 1.0)]
        [Display(Name = "Kill Switch %", Order = 1, GroupName = "Risk")]
        public double KillSwitchPct { get; set; }

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
        [Range(1, 25)] [Display(Name = "T1 Trigger (pips)", Order = 3, GroupName = "Tier Config")]
        public double T1Trigger { get; set; }

        [NinjaScriptProperty]
        [Range(10, 60)] [Display(Name = "T2 Max AR (pips)", Order = 4, GroupName = "Tier Config")]
        public double T2MaxAR { get; set; }

        [NinjaScriptProperty]
        [Range(1, 30)] [Display(Name = "T2 AU (pips)", Order = 5, GroupName = "Tier Config")]
        public double T2AU { get; set; }

        [NinjaScriptProperty]
        [Range(1, 40)] [Display(Name = "T2 Trigger (pips)", Order = 6, GroupName = "Tier Config")]
        public double T2Trigger { get; set; }

        [NinjaScriptProperty]
        [Range(20, 80)] [Display(Name = "T3 Max AR (pips)", Order = 7, GroupName = "Tier Config")]
        public double T3MaxAR { get; set; }

        [NinjaScriptProperty]
        [Range(1, 40)] [Display(Name = "T3 AU (pips)", Order = 8, GroupName = "Tier Config")]
        public double T3AU { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50)] [Display(Name = "T3 Trigger (pips)", Order = 9, GroupName = "Tier Config")]
        public double T3Trigger { get; set; }

        #endregion

        #region State Change

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "CEREBUS_ST_NT8";
                Description = "CEREBUS Symmetry Trap v4.0 — Engine B";
                Calculate = Calculate.OnBarClose;
                BarsRequiredToTrade = 5;
                IsExitOnSessionCloseStrategy = false;

                MaxLoops = 1;
                KillSwitchPct = 0.80;
                TradeQty = 1;

                AsianStartEST = 19;
                AsianEndEST = 3;
                LoopTimeoutHrs = 9;
                ResetHourEST = 12;

                T1MaxAR = 20.0; T1AU = 10.0; T1Trigger = 12.0;
                T2MaxAR = 30.0; T2AU = 12.0; T2Trigger = 15.0;
                T3MaxAR = 45.0; T3AU = 15.0; T3Trigger = 19.0;

                DisplayInDataBox = true;
                DrawOnPriceMarkers = true;
                DrawDataGrid = true;
            }
            else if (State == State.DataLoaded)
            {
                _state = EngineState.SEARCH;
                _dir = EngineDirection.FLAT;
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
                Print("CEREBUS_ST: Loop expired. Session over.");
                ResetToSearch();
                return;
            }

            // ── State Machine ──
            switch (_state)
            {
                case EngineState.SEARCH:
                    DoSearch();
                    break;
                case EngineState.WAIT_RETRACE:
                    DoWaitRetrace();
                    break;
                case EngineState.WAIT_OCC:
                    DoWaitOCC();
                    break;
                case EngineState.IN_TRADE:
                    DoInTrade();
                    break;
            }
        }

        #endregion

        #region SEARCH

        private void DoSearch()
        {
            if (!IsTradingWindow(GetESTHour()))
                return;

            // Dynamic trigger based on locked AU
            double thresh = _trigger > 0 ? _trigger : _au * 1.2;
            double close = Close[0];

            // LONG impulse
            if (close > _origin + thresh)
            {
                _impulseDetected = true;
                _dir = EngineDirection.LONG;
                _impulseHigh = High[0];
                _impulseLow = Math.Min(_origin, Low[0]);
                _impulseExtreme = _impulseLow;

                double impulseSize = _impulseHigh - _impulseLow;
                _killLevel = _impulseHigh - impulseSize * KillSwitchPct;

                _state = EngineState.WAIT_RETRACE;
                _retraceDone = false;

                Draw.HorizontalLine(this, "ImpH" + CurrentBar, false, _impulseHigh,
                    Brushes.Lime, DashStyleHelper.Dash, 1);
                Print("CEREBUS_ST: LONG impulse | Close=" + close.ToString("F5") +
                      " | AU=" + _au.ToString("F1") + "p | Ext(SL)=" + _impulseExtreme.ToString("F5"));
            }
            // SHORT impulse
            else if (close < _origin - thresh)
            {
                _impulseDetected = true;
                _dir = EngineDirection.SHORT;
                _impulseHigh = Math.Max(_origin, High[0]);
                _impulseLow = Low[0];
                _impulseExtreme = _impulseHigh;

                double impulseSize = _impulseHigh - _impulseLow;
                _killLevel = _impulseLow + impulseSize * KillSwitchPct;

                _state = EngineState.WAIT_RETRACE;
                _retraceDone = false;

                Draw.HorizontalLine(this, "ImpL" + CurrentBar, false, _impulseLow,
                    Brushes.Red, DashStyleHelper.Dash, 1);
                Print("CEREBUS_ST: SHORT impulse | Close=" + close.ToString("F5") +
                      " | AU=" + _au.ToString("F1") + "p | Ext(SL)=" + _impulseExtreme.ToString("F5"));
            }
        }

        #endregion

        #region WAIT_RETRACE

        private void DoWaitRetrace()
        {
            if (!IsTradingWindow(GetESTHour()))
                return;

            double close = Close[0];
            double high = High[0];
            double low = Low[0];

            // Kill switch (close-only)
            if (_dir == EngineDirection.LONG && close < _killLevel)
            {
                Print("CEREBUS_ST: 80% KILL (L) | Close=" + close.ToString("F5") + " < " + _killLevel.ToString("F5"));
                ResetLoop();
                return;
            }
            if (_dir == EngineDirection.SHORT && close > _killLevel)
            {
                Print("CEREBUS_ST: 80% KILL (S) | Close=" + close.ToString("F5") + " > " + _killLevel.ToString("F5"));
                ResetLoop();
                return;
            }

            // Retrace: pullback >= 1 AU from impulse extreme
            if (!_retraceDone)
            {
                double retrace = 0;
                if (_dir == EngineDirection.LONG)
                    retrace = _impulseHigh - low;
                else
                    retrace = high - _impulseLow;

                if (retrace >= _au)
                {
                    _retraceDone = true;
                    _retraceHigh = high;
                    _retraceLow = low;
                    _state = EngineState.WAIT_OCC;
                    Print("CEREBUS_ST: Retrace OK | " + retrace.ToString("F1") + "p >= AU " + _au.ToString("F1") + "p");
                }
            }
        }

        #endregion

        #region WAIT_OCC

        private void DoWaitOCC()
        {
            if (!IsTradingWindow(GetESTHour()))
                return;

            double close = Close[0];

            // Kill switch still active
            if (_dir == EngineDirection.LONG && close < _killLevel)
            {
                Print("CEREBUS_ST: 80% KILL (L-OCC)");
                ResetLoop();
                return;
            }
            if (_dir == EngineDirection.SHORT && close > _killLevel)
            {
                Print("CEREBUS_ST: 80% KILL (S-OCC)");
                ResetLoop();
                return;
            }

            // OCC: close back in impulse direction beyond retrace zone
            bool occ = false;
            if (_dir == EngineDirection.LONG && close > _retraceHigh)
            {
                occ = true;
                _entry = close;
                _sl = _impulseExtreme;
                _tp = _entry + _au;
            }
            else if (_dir == EngineDirection.SHORT && close < _retraceLow)
            {
                occ = true;
                _entry = close;
                _sl = _impulseExtreme;
                _tp = _entry - _au;
            }

            if (occ)
            {
                _state = EngineState.IN_TRADE;
                SubmitEntry();
            }
        }

        #endregion

        #region IN_TRADE

        private void DoInTrade()
        {
            double close = Close[0];
            double high = High[0];
            double low = Low[0];

            if (_dir == EngineDirection.LONG)
            {
                if (high >= _tp)
                {
                    ExitTrade("TP", _tp);
                    Draw.Diamond(this, "TP" + CurrentBar, false, _tp, Brushes.Lime);
                    Print("CEREBUS_ST: LONG TP | Entry=" + _entry.ToString("F5") + " | TP=" + _tp.ToString("F5"));
                    NextLoop();
                    return;
                }
                if (low <= _sl)
                {
                    ExitTrade("SL", _sl);
                    Draw.Diamond(this, "SL" + CurrentBar, false, _sl, Brushes.Red);
                    Print("CEREBUS_ST: LONG SL | Entry=" + _entry.ToString("F5") + " | SL=" + _sl.ToString("F5"));
                    NextLoop();
                    return;
                }
                if (close < _killLevel)
                {
                    ExitTrade("KILL", close);
                    Print("CEREBUS_ST: LONG KILL IN-TRADE | Close=" + close.ToString("F5"));
                    ResetLoop();
                    return;
                }
            }
            else if (_dir == EngineDirection.SHORT)
            {
                if (low <= _tp)
                {
                    ExitTrade("TP", _tp);
                    Draw.Diamond(this, "TP" + CurrentBar, false, _tp, Brushes.Cyan);
                    Print("CEREBUS_ST: SHORT TP | Entry=" + _entry.ToString("F5") + " | TP=" + _tp.ToString("F5"));
                    NextLoop();
                    return;
                }
                if (high >= _sl)
                {
                    ExitTrade("SL", _sl);
                    Draw.Diamond(this, "SL" + CurrentBar, false, _sl, Brushes.Red);
                    Print("CEREBUS_ST: SHORT SL | Entry=" + _entry.ToString("F5") + " | SL=" + _sl.ToString("F5"));
                    NextLoop();
                    return;
                }
                if (close > _killLevel)
                {
                    ExitTrade("KILL", close);
                    Print("CEREBUS_ST: SHORT KILL IN-TRADE | Close=" + close.ToString("F5"));
                    ResetLoop();
                    return;
                }
            }
        }

        #endregion

        #region Trade Execution

        private void SubmitEntry()
        {
            _entryOrderName = "ST_" + _dir.ToString() + "_L" + _loopCount + "_" + CurrentBar;

            if (_dir == EngineDirection.LONG)
            {
                EnterLong(TradeQty, _entryOrderName);
            }
            else if (_dir == EngineDirection.SHORT)
            {
                EnterShort(TradeQty, _entryOrderName);
            }

            Draw.HorizontalLine(this, "E_" + CurrentBar, false, _entry,
                Brushes.Yellow, DashStyleHelper.Solid, 2);
            Draw.HorizontalLine(this, "SL_" + CurrentBar, false, _sl,
                Brushes.Red, DashStyleHelper.Dash, 1);
            Draw.HorizontalLine(this, "TP_" + CurrentBar, false, _tp,
                Brushes.Lime, DashStyleHelper.Dash, 1);
            Draw.Text(this, "Etxt" + CurrentBar, false,
                "ENTRY " + _dir.ToString() + " AU=" + _au.ToString("F1") + " L=" + _loopCount,
                0, _entry + 3 * TickSize,
                0, Brushes.Yellow, new Gui.Tools.SimpleFont("Arial", 9), TextAlignment.Left,
                Brushes.Transparent, Brushes.Transparent, 0);

            Print("CEREBUS_ST: " + _dir.ToString() + " ENTRY | E=" + _entry.ToString("F5") +
                  " SL=" + _sl.ToString("F5") + " TP=" + _tp.ToString("F5") +
                  " | Risk=" + Math.Abs(_entry - _sl).ToString("F5") +
                  " | Reward=" + Math.Abs(_tp - _entry).ToString("F5"));
        }

        private void ExitTrade(string reason, double price)
        {
            if (Position.MarketPosition == MarketPosition.Long)
                ExitLong("Close_" + reason + "_" + CurrentBar, _entryOrderName);
            else if (Position.MarketPosition == MarketPosition.Short)
                ExitShort("Close_" + reason + "_" + CurrentBar, _entryOrderName);

            _lastEntryName = _entryOrderName;
        }

        #endregion

        #region Loop Management

        private void NextLoop()
        {
            _loopCount++;
            if (_loopCount > MaxLoops)
                Print("CEREBUS_ST: All " + MaxLoops + " loop(s) done for this session.");
            ResetToSearch();
        }

        private void ResetLoop()
        {
            ResetToSearch();
        }

        private void ResetToSearch()
        {
            _state = EngineState.SEARCH;
            _dir = EngineDirection.FLAT;
            _impulseDetected = false;
            _retraceDone = false;
            _impulseHigh = 0;
            _impulseLow = 0;
            _impulseExtreme = 0;
            _killLevel = 0;
            _retraceHigh = 0;
            _retraceLow = 0;
            _entry = 0;
            _sl = 0;
            _tp = 0;
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
            _origin = 0;
            Print("CEREBUS_ST: ═══ DAILY RESET " + ResetHourEST + ":00 EST ═══");
        }

        #endregion

        #region Session Range

        private void LockRange()
        {
            _asianRange = (_asianHigh - _asianLow) / TickSize;

            if (_asianRange <= T1MaxAR)
            {
                _au = T1AU * TickSize;
                _trigger = T1Trigger * TickSize;
                Print("CEREBUS_ST: T1 | AR=" + _asianRange.ToString("F0") + "t | AU=" + T1AU.ToString("F1") + "p");
            }
            else if (_asianRange <= T2MaxAR)
            {
                _au = T2AU * TickSize;
                _trigger = T2Trigger * TickSize;
                Print("CEREBUS_ST: T2 | AR=" + _asianRange.ToString("F0") + "t | AU=" + T2AU.ToString("F1") + "p");
            }
            else if (_asianRange <= T3MaxAR)
            {
                _au = T3AU * TickSize;
                _trigger = T3Trigger * TickSize;
                Print("CEREBUS_ST: T3 | AR=" + _asianRange.ToString("F0") + "t | AU=" + T3AU.ToString("F1") + "p");
            }
            else
            {
                _au = 0;
                _trigger = 0;
                Print("CEREBUS_ST: NO-GO | AR=" + _asianRange.ToString("F0") + "t > T3 (" + T3MaxAR.ToString("F0") + "t)");
                return;
            }

            _rangeLocked = true;
            _origin = Close[0];

            Draw.HorizontalLine(this, "AH", false, _asianHigh, Brushes.Cyan, DashStyleHelper.Dot, 1);
            Draw.HorizontalLine(this, "AL", false, _asianLow, Brushes.Cyan, DashStyleHelper.Dot, 1);
            Draw.Text(this, "RL" + CurrentBar, false,
                "RANGE | AR=" + _asianRange.ToString("F0") + "t | AU=" + (_au / TickSize).ToString("F1") + "t | O=" + _origin.ToString("F5"),
                0, _asianHigh + 5 * TickSize,
                0, Brushes.Cyan, new Gui.Tools.SimpleFont("Arial", 10), TextAlignment.Left,
                Brushes.Transparent, Brushes.Transparent, 0);
        }

        #endregion

        #region Time Helpers

        private double GetESTHour()
        {
            // Use NinjaTrader's built-in EST conversion
            return Time[0].Hour + Time[0].Minute / 60.0;
        }

        private bool IsAsianSession(double estHour)
        {
            // Asian: 19:00 → 03:00 (overnight)
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
            // Between Asian End and the earlier of (loop timeout or daily reset)
            int end = AsianEndEST;
            int expiry = (end + LoopTimeoutHrs) % 24;

            if (end < AsianStartEST)
            {
                // Overnight session: window is end → expiry (may cross midnight)
                if (expiry > end)
                    return estHour >= end && estHour < expiry && estHour < ResetHourEST;
                return (estHour >= end || estHour < expiry) && estHour < ResetHourEST;
            }
            else
            {
                return estHour >= end && estHour < expiry && estHour < ResetHourEST;
            }
        }

        private bool IsPastTimeout(double estHour)
        {
            int expiry = (AsianEndEST + LoopTimeoutHrs) % 24;
            if (expiry > AsianEndEST)
                return estHour >= expiry && estHour < ResetHourEST;
            return estHour >= expiry && estHour < ResetHourEST;
        }

        #endregion
    }
}
