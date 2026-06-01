#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Linq;
using System.Text;
using NinjaTrader.Cbi;
using NinjaTrader.Core;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// CEREBUS FX v4.0 — Trade Copier Signal Bridge
    /// ==============================================
    ///
    /// Reads CEREBUS trade signals from a shared signal file and
    /// outputs standardized JSON commands that MAD's trade copier
    /// can consume for MT5 execution.
    ///
    /// ARCHITECTURE:
    ///   NT8 Strategy (ST or P90) → writes signal to SignalFile
    ///   → TradeCopier reads SignalFile → outputs CopierCommand
    ///   → MAD's Trade Copier reads CopierCommand → executes on MT5
    ///
    /// SIGNAL FILE FORMAT (shared directory):
    ///   Line 1: TIMESTAMP | ACTION | SYMBOL | LOT | SL | TP | MAGIC | COMMENT
    ///
    /// COMMAND OUTPUT:
    ///   Written to OutputDirectory/CEREBUS_copier_cmd.json
    ///   Trade copier polls this file for new commands.
    ///
    /// MAD has the trade copier — this is the NT8-side bridge only.
    ///
    /// Reference: MAD Directive 2026-05-31 (Track A #7)
    /// </summary>
    public class CEREBUS_TradeCopier : Strategy
    {
        #region Properties

        [NinjaScriptProperty]
        [Display(Name = "Signal Directory", Order = 1, GroupName = "Bridge")]
        public string SignalDirectory { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Poll Interval (sec)", Order = 1, GroupName = "Timing")]
        public int PollIntervalSec { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Max Lot Size", Order = 1, GroupName = "Risk")]
        public double MaxLotSize { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Max Spread To Trade (pips)", Order = 2, GroupName = "Risk")]
        public double MaxSpreadPips { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Log Signals", Order = 1, GroupName = "Output")]
        public bool LogSignals { get; set; }

        #endregion

        #region Private Fields

        private string _signalFile;
        private string _commandFile;
        private DateTime _lastPoll;
        private int _lastProcessedLine;
        private Dictionary<string, string> _activePositions;

        #endregion

        #region State Change

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "CEREBUS_TradeCopier";
                Description = "CEREBUS Trade Copier Signal Bridge v4.0";
                Calculate = Calculate.OnEachTick;

                SignalDirectory = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "NinjaTrader 8", "CEREBUS_signals");

                PollIntervalSec = 5;
                MaxLotSize = 1.0;
                MaxSpreadPips = 3.0;
                LogSignals = true;

                DisplayInDataBox = true;
            }
            else if (State == State.DataLoaded)
            {
                _activePositions = new Dictionary<string, string>();
                _lastPoll = DateTime.MinValue;
                _lastProcessedLine = 0;

                // Ensure signal directory exists
                if (!Directory.Exists(SignalDirectory))
                    Directory.CreateDirectory(SignalDirectory);

                _signalFile = Path.Combine(SignalDirectory, "cerebus_signals.txt");
                _commandFile = Path.Combine(SignalDirectory, "cerebus_cmd.json");

                if (LogSignals)
                    Print("CEREBUS_COPIER: Signal directory = " + SignalDirectory);
            }
        }

        #endregion

        #region OnBarUpdate / Signal Polling

        protected override void OnBarUpdate()
        {
            // Poll at interval
            if ((DateTime.Now - _lastPoll).TotalSeconds < PollIntervalSec)
                return;

            _lastPoll = DateTime.Now;

            if (!File.Exists(_signalFile))
                return;

            try
            {
                string[] lines = File.ReadAllLines(_signalFile);
                for (int i = _lastProcessedLine; i < lines.Length; i++)
                {
                    ProcessSignalLine(lines[i]);
                }
                _lastProcessedLine = lines.Length;
            }
            catch (Exception ex)
            {
                if (LogSignals)
                    Print("CEREBUS_COPIER: Read error - " + ex.Message);
            }
        }

        private void ProcessSignalLine(string line)
        {
            if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#"))
                return;

            // Parse: TIMESTAMP | ACTION | SYMBOL | LOT | SL | TP | MAGIC | COMMENT
            string[] parts = line.Split('|');
            if (parts.Length < 8)
                return;

            string timestamp = parts[0].Trim();
            string action = parts[1].Trim().ToUpper();
            string symbol = parts[2].Trim();
            double lot = double.Parse(parts[3].Trim());
            double sl = double.Parse(parts[4].Trim());
            double tp = double.Parse(parts[5].Trim());
            int magic = int.Parse(parts[6].Trim());
            string comment = parts[7].Trim();

            // ── Risk Gate ──
            if (lot > MaxLotSize)
            {
                if (LogSignals)
                    Print("CEREBUS_COPIER: LOT CAP " + lot + " > " + MaxLotSize + " → rejected");
                return;
            }

            // Write command (manual JSON for NT8 sandbox compat)
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("{");
            sb.AppendLine("  ""timestamp"": """ + command.timestamp + """,");
            sb.AppendLine("  ""action"": """ + action + """,");
            sb.AppendLine("  ""symbol"": """ + symbol + """,");
            sb.AppendLine("  ""lot_size"": " + Math.Round(lot, 2).ToString("F2") + ",");
            sb.AppendLine("  ""sl_price"": " + sl.ToString("F5") + ",");
            sb.AppendLine("  ""tp_price"": " + tp.ToString("F5") + ",");
            sb.AppendLine("  ""magic_number"": " + magic + ",");
            sb.AppendLine("  ""comment"": """ + comment + """" );
            sb.AppendLine("}");
            File.WriteAllText(_commandFile, sb.ToString(), Encoding.UTF8);

            // Track
            string posKey = symbol + "_" + magic;
            if (action == "OPEN")
                _activePositions[posKey] = comment;
            else if (action == "CLOSE")
                _activePositions.Remove(posKey);

            if (LogSignals)
            {
                Print("CEREBUS_COPIER: " + action + " " + symbol +
                      " Lot=" + lot.ToString("F2") + " SL=" + sl.ToString("F5") +
                      " TP=" + tp.ToString("F5") + " [" + comment + "]");
            }
        }

        #endregion
    }
}
