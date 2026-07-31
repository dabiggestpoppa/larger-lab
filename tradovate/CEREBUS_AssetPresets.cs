#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.Core;
using NinjaTrader.NinjaScript;

namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// CEREBUS FX v4.0 — Asset Preset Configuration Loader
    /// ====================================================
    ///
    /// Provides per-asset P90 threshold presets for the P90 Kinetic Engine.
    /// Source: quant-lab/configs/asset_configs.py (ASSET_CONFIGS registry)
    ///
    /// P90 threshold formula: AU * k_factor (per asset class)
    ///   Forex Majors: k=0.46
    ///   Forex Crosses: k=0.48
    ///   Indices: k=0.48
    ///   Metals: k=0.50
    ///   Crypto: k=0.52
    ///
    /// Per-hour thresholds are derived from session-calibrated base values.
    /// Hourly distribution: 3AM=highest, 11AM=lowest (intraday volatility curve)
    ///
    /// Reference: cerebus_p90.md Section V (Calibration Protocol)
    /// Author: CEREBUS Ontology → NT8 Config (MAD 2026-05-31)
    /// </summary>
    public class CEREBUS_AssetPresets
    {
        /// <summary>
        /// Complete per-asset P90 configuration.
        /// Key = NT8 instrument suffix (e.g., "EURUSD", "GBPUSD")
        /// Value = P90ThresholdSet with per-hour values in pips
        /// </summary>
        public static readonly Dictionary<string, P90ThresholdSet> Presets = new Dictionary<string, P90ThresholdSet>
        {
            // ── FOREX MAJORS (k=0.46) ──────────────────────────────────
            {
                "EURUSD", new P90ThresholdSet
                {
                    Name = "EUR/USD", KFactor = 0.46, PipValue = 0.0001,
                    H3 = 4.6, H4 = 4.2, H5 = 3.8, H6 = 3.5, H7 = 3.2,
                    H8 = 3.0, H9 = 2.8, H10 = 2.6, H11 = 2.4,
                    T1_AR = 20.0, T1_AU = 10.0, T1_Trigger = 12.0,
                    T2_AR = 30.0, T2_AU = 12.0, T2_Trigger = 15.0,
                    T3_AR = 45.0, T3_AU = 15.0, T3_Trigger = 19.0
                }
            },
            {
                "GBPUSD", new P90ThresholdSet
                {
                    Name = "GBP/USD", KFactor = 0.46, PipValue = 0.0001,
                    H3 = 5.98, H4 = 5.46, H5 = 4.94, H6 = 4.55, H7 = 4.16,
                    H8 = 3.90, H9 = 3.64, H10 = 3.38, H11 = 3.12,
                    T1_AR = 26.0, T1_AU = 13.0, T1_Trigger = 16.0,
                    T2_AR = 39.0, T2_AU = 16.0, T2_Trigger = 19.0,
                    T3_AR = 59.0, T3_AU = 20.0, T3_Trigger = 24.0
                }
            },
            {
                "USDCHF", new P90ThresholdSet
                {
                    Name = "USD/CHF", KFactor = 0.46, PipValue = 0.0001,
                    H3 = 5.06, H4 = 4.62, H5 = 4.18, H6 = 3.85, H7 = 3.52,
                    H8 = 3.29, H9 = 3.07, H10 = 2.84, H11 = 2.62,
                    T1_AR = 19.0, T1_AU = 11.0, T1_Trigger = 11.0,
                    T2_AR = 29.0, T2_AU = 15.0, T2_Trigger = 15.0,
                    T3_AR = 50.0, T3_AU = 20.0, T3_Trigger = 20.0
                }
            },
            {
                "USDJPY", new P90ThresholdSet
                {
                    Name = "USD/JPY", KFactor = 0.46, PipValue = 0.01,
                    H3 = 4.60, H4 = 4.20, H5 = 3.80, H6 = 3.50, H7 = 3.20,
                    H8 = 3.00, H9 = 2.80, H10 = 2.60, H11 = 2.40,
                    T1_AR = 20.0, T1_AU = 10.0, T1_Trigger = 12.0,
                    T2_AR = 30.0, T2_AU = 12.0, T2_Trigger = 15.0,
                    T3_AR = 45.0, T3_AU = 15.0, T3_Trigger = 19.0
                }
            },

            // ── FOREX CROSSES (k=0.48) ─────────────────────────────────
            {
                "EURGBP", new P90ThresholdSet
                {
                    Name = "EUR/GBP", KFactor = 0.48, PipValue = 0.0001,
                    H3 = 3.84, H4 = 3.52, H5 = 3.20, H6 = 2.96, H7 = 2.72,
                    H8 = 2.56, H9 = 2.40, H10 = 2.24, H11 = 2.08,
                    T1_AR = 16.0, T1_AU = 8.0, T1_Trigger = 10.0,
                    T2_AR = 24.0, T2_AU = 10.0, T2_Trigger = 13.0,
                    T3_AR = 36.0, T3_AU = 12.0, T3_Trigger = 17.0
                }
            },
            {
                "EURJPY", new P90ThresholdSet
                {
                    Name = "EUR/JPY", KFactor = 0.48, PipValue = 0.01,
                    H3 = 5.76, H4 = 5.28, H5 = 4.80, H6 = 4.44, H7 = 4.08,
                    H8 = 3.84, H9 = 3.60, H10 = 3.36, H11 = 3.12,
                    T1_AR = 24.0, T1_AU = 12.0, T1_Trigger = 14.0,
                    T2_AR = 36.0, T2_AU = 14.0, T2_Trigger = 17.0,
                    T3_AR = 54.0, T3_AU = 17.0, T3_Trigger = 22.0
                }
            },
            {
                "GBPJPY", new P90ThresholdSet
                {
                    Name = "GBP/JPY", KFactor = 0.48, PipValue = 0.01,
                    H3 = 7.20, H4 = 6.60, H5 = 6.00, H6 = 5.55, H7 = 5.10,
                    H8 = 4.80, H9 = 4.50, H10 = 4.20, H11 = 3.90,
                    T1_AR = 30.0, T1_AU = 15.0, T1_Trigger = 18.0,
                    T2_AR = 45.0, T2_AU = 18.0, T2_Trigger = 22.0,
                    T3_AR = 68.0, T3_AU = 22.0, T3_Trigger = 28.0
                }
            },

            // ── INDICES (k=0.48) ───────────────────────────────────────
            {
                "US500", new P90ThresholdSet
                {
                    Name = "US 500", KFactor = 0.48, PipValue = 1.0,
                    H3 = 23.0, H4 = 21.0, H5 = 19.0, H6 = 17.5, H7 = 16.0,
                    H8 = 15.0, H9 = 14.0, H10 = 13.0, H11 = 12.0,
                    T1_AR = 100.0, T1_AU = 50.0, T1_Trigger = 60.0,
                    T2_AR = 150.0, T2_AU = 60.0, T2_Trigger = 75.0,
                    T3_AR = 200.0, T3_AU = 75.0, T3_Trigger = 100.0
                }
            },
            {
                "NAS100", new P90ThresholdSet
                {
                    Name = "NAS 100", KFactor = 0.48, PipValue = 1.0,
                    H3 = 38.0, H4 = 35.0, H5 = 32.0, H6 = 29.5, H7 = 27.0,
                    H8 = 25.5, H9 = 24.0, H10 = 22.5, H11 = 21.0,
                    T1_AR = 160.0, T1_AU = 80.0, T1_Trigger = 95.0,
                    T2_AR = 240.0, T2_AU = 95.0, T2_Trigger = 120.0,
                    T3_AR = 320.0, T3_AU = 120.0, T3_Trigger = 160.0
                }
            },

            // ── METALS (k=0.50) ────────────────────────────────────────
            {
                "XAUUSD", new P90ThresholdSet
                {
                    Name = "XAU/USD (Gold)", KFactor = 0.50, PipValue = 0.01,
                    H3 = 140.0, H4 = 128.0, H5 = 116.0, H6 = 107.0, H7 = 98.0,
                    H8 = 92.0, H9 = 86.0, H10 = 80.0, H11 = 74.0,
                    T1_AR = 500.0, T1_AU = 250.0, T1_Trigger = 300.0,
                    T2_AR = 750.0, T2_AU = 300.0, T2_Trigger = 375.0,
                    T3_AR = 1000.0, T3_AU = 375.0, T3_Trigger = 500.0
                }
            },

            // ── CRYPTO (k=0.52) ────────────────────────────────────────
            {
                "BTCUSD", new P90ThresholdSet
                {
                    Name = "BTC/USD", KFactor = 0.52, PipValue = 1.0,
                    H3 = 650.0, H4 = 600.0, H5 = 550.0, H6 = 510.0, H7 = 470.0,
                    H8 = 440.0, H9 = 410.0, H10 = 380.0, H11 = 350.0,
                    T1_AR = 2600.0, T1_AU = 1300.0, T1_Trigger = 1560.0,
                    T2_AR = 3900.0, T2_AU = 1560.0, T2_Trigger = 1950.0,
                    T3_AR = 5200.0, T3_AU = 1950.0, T3_Trigger = 2600.0
                }
            },
            {
                "ETHUSD", new P90ThresholdSet
                {
                    Name = "ETH/USD", KFactor = 0.52, PipValue = 0.01,
                    H3 = 26.0, H4 = 24.0, H5 = 22.0, H6 = 20.5, H7 = 19.0,
                    H8 = 18.0, H9 = 17.0, H10 = 16.0, H11 = 15.0,
                    T1_AR = 100.0, T1_AU = 50.0, T1_Trigger = 60.0,
                    T2_AR = 150.0, T2_AU = 60.0, T2_Trigger = 75.0,
                    T3_AR = 200.0, T3_AU = 75.0, T3_Trigger = 100.0
                }
            }
        };

        /// <summary>
        /// Apply preset to a P90 engine strategy instance.
        /// Call from_STRATEGY_NAME_.OnStateChange() after SetDefaults.
        /// </summary>
        public static P90ThresholdSet GetPreset(string symbol)
        {
            string key = symbol.ToUpper().Replace(".", "").Replace("/", "").Replace("-", "");
            if (Presets.ContainsKey(key))
                return Presets[key];
            // Default to EURUSD if unknown
            return Presets["EURUSD"];
        }
    }

    /// <summary>
    /// Per-asset P90 threshold configuration.
    /// All values in pips (native to the asset's display).
    /// </summary>
    public class P90ThresholdSet
    {
        public string Name { get; set; }
        public double KFactor { get; set; }
        public double PipValue { get; set; }

        // Per-hour P90 thresholds (pips)
        public double H3 { get; set; }
        public double H4 { get; set; }
        public double H5 { get; set; }
        public double H6 { get; set; }
        public double H7 { get; set; }
        public double H8 { get; set; }
        public double H9 { get; set; }
        public double H10 { get; set; }
        public double H11 { get; set; }

        // Tier configuration (AR in pips, AU in pips, Trigger in pips)
        public double T1_AR { get; set; }
        public double T1_AU { get; set; }
        public double T1_Trigger { get; set; }
        public double T2_AR { get; set; }
        public double T2_AU { get; set; }
        public double T2_Trigger { get; set; }
        public double T3_AR { get; set; }
        public double T3_AU { get; set; }
        public double T3_Trigger { get; set; }
    }
}
