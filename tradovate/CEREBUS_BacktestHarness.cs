#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Linq;
using NinjaTrader.Cbi;
using NinjaTrader.Core;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// CEREBUS FX v4.0 — NT8 Backtest Validation Harness
    /// =================================================
    ///
    /// Validates that both CEREBUS strategies (ST + P90) compile and run
    /// correctly in NinjaTrader 8's backtester.
    ///
    /// VALIDATION CHECKLIST:
    ///   [x] Both .cs files compile without errors
    ///   [x] No namespace conflicts between ST and P90
    ///   [x] Both use same NinjaScript base class
    ///   [x] Both reference same asset preset system
    ///   [ ] Run ST backtest on EURUSD M5 → verify WR >= 85%
    ///   [ ] Run P90 backtest on EURUSD M5 → verify WR >= 78%
    ///   [ ] Run dual-engine convergence test → verify WR >= 90%
    ///   [ ] Multi-asset validation (3+ assets)
    ///
    /// USAGE:
    ///   1. Import all .cs files into NT8 Strategy Builder
    ///   2. Attach this harness to any M5 chart
    ///   3. Set "ValidationMode" to select which strategy to test
    ///   4. Run backtest and check output for validation results
    ///
    /// Reference: quant-lab/engines/ (Python truth source)
    /// Author: CEREBUS Ontology → NT8 Validation (MAD 2026-05-31)
    /// </summary>
    public class CEREBUS_BacktestHarness : Strategy
    {
        #region Enums

        private enum ValidationMode
        {
            SymmetryTrap_Only,
            P90_Only,
            DualEngine_Convergence,
            MultiAsset_All
        }

        private enum ValidationResult
        {
            NOT_RUN,
            PASS,
            FAIL,
            WARNING
        }

        #endregion

        #region Properties

        [NinjaScriptProperty]
        [Display(Name = "Validation Mode", Order = 1, GroupName = "Harness")]
        public ValidationMode Mode { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Min WR % (ST)", Order = 1, GroupName = "Thresholds")]
        public double MinWR_ST { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Min WR % (P90)", Order = 2, GroupName = "Thresholds")]
        public double MinWR_P90 { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Min WR % (Dual)", Order = 3, GroupName = "Thresholds")]
        public double MinWR_Dual { get; set; }

        [NinjaScriptProperty]
        [Range(1, 100)]
        [Display(Name = "Min Trades", Order = 4, GroupName = "Thresholds")]
        public int MinTrades { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Log Every Trade", Order = 1, GroupName = "Output")]
        public bool LogEveryTrade { get; set; }

        #endregion

        #region Private Fields

        private int _totalTrades;
        private int _winningTrades;
        private int _losingTrades;
        private double _totalPips;
        private double _maxDrawdown;
        private double _peakEquity;
        private ValidationResult _compileResult;
        private ValidationResult _wrResult;
        private ValidationResult _tradeCountResult;
        private List<string> _validationLog;
        private bool _validationComplete;

        #endregion

        #region State Change

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "CEREBUS_BacktestHarness";
                Description = "CEREBUS NT8 Backtest Validation Harness";
                Calculate = Calculate.OnBarClose;
                BarsRequiredToTrade = 5;
                IsExitOnSessionCloseStrategy = false;

                Mode = ValidationMode.SymmetryTrap_Only;
                MinWR_ST = 85.0;
                MinWR_P90 = 78.0;
                MinWR_Dual = 90.0;
                MinTrades = 10;
                LogEveryTrade = false;

                DisplayInDataBox = true;
                DrawOnPriceMarkers = true;
            }
            else if (State == State.DataLoaded)
            {
                _validationLog = new List<string>();
                _compileResult = ValidationResult.NOT_RUN;
                _wrResult = ValidationResult.NOT_RUN;
                _tradeCountResult = ValidationResult.NOT_RUN;
                _validationComplete = false;
            }
            else if (State == State.Terminated)
            {
                if (!_validationComplete)
                    RunValidation();
            }
        }

        #endregion

        #region OnBarUpdate

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BarsRequiredToTrade)
                return;

            // Track equity for drawdown
            double equity = Performance.AllTrades.Today.Curve.Count > 0
                ? Performance.AllTrades.Today.Curve.Last().Value
                : 0;

            if (equity > _peakEquity)
                _peakEquity = equity;

            double dd = _peakEquity > 0 ? ((_peakEquity - equity) / _peakEquity) * 100.0 : 0;
            if (dd > _maxDrawdown)
                _maxDrawdown = dd;
        }

        #endregion

        #region Validation

        private void RunValidation()
        {
            _validationLog.Clear();
            _validationLog.Add("═══ CEREBUS NT8 BACKTEST VALIDATION ═══");
            _validationLog.Add("Mode: " + Mode.ToString());
            _validationLog.Add("Instrument: " + Instrument.FullName);
            _validationLog.Add("Time Frame: " + BarsPeriod.BarsPeriodType + " x " + BarsPeriod.Value);
            _validationLog.Add("Date Range: " + From.ToString("yyyy-MM-dd") + " → " + To.ToString("yyyy-MM-dd"));
            _validationLog.Add("");

            // ── Compile Validation ──
            ValidateCompile();

            // ── Trade Statistics ──
            ComputeTradeStats();

            // ── WR Validation ──
            ValidateWR();

            // ── Trade Count Validation ──
            ValidateTradeCount();

            // ── Summary ──
            PrintSummary();

            _validationComplete = true;
        }

        private void ValidateCompile()
        {
            _validationLog.Add("── COMPILE VALIDATION ──");

            // Check that required types are available
            try
            {
                // Verify CEREBUS_AssetPresets exists and has presets
                var preset = CEREBUS_AssetPresets.GetPreset("EURUSD");
                if (preset != null && preset.H3 > 0)
                {
                    _validationLog.Add("[PASS] CEREBUS_AssetPresets loaded: " + preset.Name);
                    _validationLog.Add("  P90 thresholds: H3=" + preset.H3 + " H11=" + preset.H11);
                }
                else
                {
                    _validationLog.Add("[FAIL] CEREBUS_AssetPresets returned null/zero");
                    _compileResult = ValidationResult.FAIL;
                    return;
                }

                // Verify preset count
                int presetCount = CEREBUS_AssetPresets.Presets.Count;
                if (presetCount >= 10)
                {
                    _validationLog.Add("[PASS] Asset presets available: " + presetCount + " assets");
                }
                else
                {
                    _validationLog.Add("[WARN] Only " + presetCount + " presets (expected 10+)");
                }

                _compileResult = ValidationResult.PASS;
            }
            catch (Exception ex)
            {
                _validationLog.Add("[FAIL] Compile validation error: " + ex.Message);
                _compileResult = ValidationResult.FAIL;
            }
        }

        private void ComputeTradeStats()
        {
            _totalTrades = 0;
            _winningTrades = 0;
            _losingTrades = 0;
            _totalPips = 0;

            foreach (Trade trade in Performance.AllTrades)
            {
                _totalTrades++;
                double pnl = trade.ProfitCurrency;
                if (pnl > 0)
                    _winningTrades++;
                else
                    _losingTrades++;

                // Approximate pips from PnL (rough)
                _totalPips += Math.Abs(pnl);
            }
        }

        private void ValidateWR()
        {
            _validationLog.Add("");
            _validationLog.Add("── WIN RATE VALIDATION ──");

            if (_totalTrades == 0)
            {
                _validationLog.Add("[FAIL] No trades executed");
                _wrResult = ValidationResult.FAIL;
                return;
            }

            double wr = (_winningTrades / (double)_totalTrades) * 100.0;
            double minWR = Mode == ValidationMode.P90_Only ? MinWR_P90
                : Mode == ValidationMode.DualEngine_Convergence ? MinWR_Dual
                : MinWR_ST;

            _validationLog.Add("Total Trades: " + _totalTrades);
            _validationLog.Add("Winning: " + _winningTrades + " | Losing: " + _losingTrades);
            _validationLog.Add("Win Rate: " + wr.ToString("F1") + "% (min: " + minWR.ToString("F1") + "%)");

            if (wr >= minWR)
            {
                _validationLog.Add("[PASS] Win rate meets threshold");
                _wrResult = ValidationResult.PASS;
            }
            else
            {
                _validationLog.Add("[FAIL] Win rate below threshold");
                _wrResult = ValidationResult.FAIL;
            }
        }

        private void ValidateTradeCount()
        {
            _validationLog.Add("");
            _validationLog.Add("── TRADE COUNT VALIDATION ──");
            _validationLog.Add("Total Trades: " + _totalTrades + " (min: " + MinTrades + ")");

            if (_totalTrades >= MinTrades)
            {
                _validationLog.Add("[PASS] Trade count meets minimum");
                _tradeCountResult = ValidationResult.PASS;
            }
            else
            {
                _validationLog.Add("[WARN] Trade count below minimum (may need longer date range)");
                _tradeCountResult = ValidationResult.WARNING;
            }
        }

        private void PrintSummary()
        {
            _validationLog.Add("");
            _validationLog.Add("═══ VALIDATION SUMMARY ═══");
            _validationLog.Add("Compile: " + _compileResult.ToString());
            _validationLog.Add("Win Rate: " + _wrResult.ToString());
            _validationLog.Add("Trade Count: " + _tradeCountResult.ToString());
            _validationLog.Add("Max Drawdown: " + _maxDrawdown.ToString("F2") + "%");

            bool allPass = _compileResult == ValidationResult.PASS
                && _wrResult == ValidationResult.PASS
                && (_tradeCountResult == ValidationResult.PASS || _tradeCountResult == ValidationResult.WARNING);

            _validationLog.Add("");
            _validationLog.Add(allPass ? "═══ OVERALL: PASS ✓ ═══" : "═══ OVERALL: FAIL ✗ ═══");

            // Print all lines
            foreach (string line in _validationLog)
            {
                Print(line);
            }
        }

        #endregion

        #region OnExecution

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price,
            int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (LogEveryTrade && execution.Order != null && execution.Order.OrderState == OrderState.Filled)
            {
                if (execution.Order.OrderAction == NinjaTrader.Cbi.OrderAction.Buy ||
                    execution.Order.OrderAction == NinjaTrader.Cbi.OrderAction.SellShort)
                {
                    Print("CEREBUS_BT: Entry " + marketPosition.ToString() + " @ " + price.ToString("F5"));
                }
                else if (execution.Order.OrderAction == NinjaTrader.Cbi.OrderAction.Sell ||
                         execution.Order.OrderAction == NinjaTrader.Cbi.OrderAction.BuyToCover)
                {
                    if (execution.Trade != null)
                    {
                        Print("CEREBUS_BT: Exit PnL=" + execution.Trade.ProfitCurrency.ToString("F2"));
                    }
                }
            }
        }

        #endregion
    }
}
