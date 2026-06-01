#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.SuperDom;
using NinjaTrader.NinjaScript;
using NinjaTrader.Core.FloatingPoint;

#endregion

// The namespace follows NT8 convention: NinjaTrader.NinjaScript.Strategies
namespace NinjaTrader.NinjaScript.Strategies
{
    /// <summary>
    /// CEREBUS Symmetry Trap Engine B — NinjaTrader 8 Implementation
    /// ==============================================================
    /// Target: ES futures (E-mini S&P 500) on Tradovate/DTN IQFeed
    /// Timeframe: 5-minute bars
    /// Session: 03:00 EST – 12:00 PM EST
    ///
    /// Translated from: quant-lab/engines/symmetry_trap.py (TRUTH SOURCE)
    /// Ontology Reference: cerebus_dual_engine.md, manual_ontology.md, cerebus_qa_recap.md
    ///
    /// STATE MACHINE (4 states):
    ///   Search    → WaitDZ    → WaitOCC   → InTrade   → (reset to Search)
    ///
    /// CORE PIPELINE (all 3 steps mandatory):
    ///   1. Impulse:   M5 close beyond Tier Trigger from swing origin
    ///   2. Retrace:   Pullback >= 1 AU OR 32%-50% Fib retracement (DZ construction)
    ///   3. OCC:       M5 candle closes BACK in impulse direction inside DZ
    ///
    /// TRADE MANAGEMENT:
    ///   Entry:  Close of OCC candle
    ///   SL:     Zero-Buffer Impulse Extreme (CLOSE-ONLY invalidation)
    ///   TP:     Exactly 1 AU from entry (SINGLE TARGET — no ladder)
    ///
    /// INVALIDATION:
    ///   - 80% Kill Switch: M5 close past 80% of impulse leg = pathway VOID
    ///   - 12:00 PM EST hard exit: close ALL positions
    ///
    /// AXIOMS ENFORCED:
    ///   1. Symmetry Trap = Engine B ONLY. Never mix P90/ST SL/TP.
    ///   2. SL = exact impulse extreme (zero buffer), close-only.
    ///   3. TP = 1 AU from entry. Single target. No ladder.
    ///   4. 80% kill switch = close-only, absolute.
    ///   5. 12 PM EST = full state reset, no exceptions.
    /// </summary>
    public class CEREBUS_ST_NT8 : Strategy
    {
        // ═══════════════════════════════════════════════════════════════
        // ENUMS
        // ═══════════════════════════════════════════════════════════════

        /// <summary>
        /// Four states of the Symmetry Trap resolution engine.
        /// These are recursive expressions of one state, NOT independent modes.
        /// </summary>
        public enum CerberusState
        {
            Search,     // Impulse detection (temporal-spatial saturation)
            WaitDZ,     // Density Zone penetration (friction clearing)
            WaitOCC,    // Pathway validation (kinetic reloading)
            InTrade     // Resolution execution (deficit satisfaction)
        }

        /// <summary>
        /// Trade direction enumeration.
        /// </summary>
        public enum TradeDir
        {
            Flat = 0,
            Long = 1,
            Short = -1
        }

        // ═══════════════════════════════════════════════════════════════
        // SERIALIZED PARAMETERS (visible in NT8 UI)
        // ═══════════════════════════════════════════════════════════════

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [GridCategory("Session")]
        public int AsianSessionStartHour { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [GridCategory("Session")]
        public int AsianSessionEndHour { get; set; }

        [NinjaScriptProperty]
        [Range(1, int.MaxValue)]
        [GridCategory("Session")]
        public int ActivationEndHour { get; set; }

        [NinjaScriptProperty]
        [Range(0, 59)]
        [GridCategory("Session")]
        public int AsianSessionStartMinute { get; set; }

        [NinjaScriptProperty]
        [Range(0, 59)]
        [GridCategory("Session")]
        public int AsianSessionEndMinute { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T1")]
        public double T1_AR_Max { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T1")]
        public double T1_AU { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T1")]
        public double T1_Trigger { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T2")]
        public double T2_AR_Max { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T2")]
        public double T2_AU { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T2")]
        public double T2_Trigger { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T3")]
        public double T3_AR_Max { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T3")]
        public double T3_AU { get; set; }

        [NinjaScriptProperty]
        [Range(0, int.MaxValue)]
        [GridCategory("Tier Config — T3")]
        public double T3_Trigger { get; set; }

        [NinjaScriptProperty]
        [Range(1, 10)]
        [GridCategory("Risk")]
        public int MaxLoops { get; set; }

        [NinjaScriptProperty]
        [GridCategory("Risk")]
        public double KillSwitchPct { get; set; }

        // ═══════════════════════════════════════════════════════════════
        // TIER CONFIG (internal, derived from serialized parameters)
        // ═══════════════════════════════════════════════════════════════

        /// <summary>
        /// Holds tier classification parameters.
        /// All values in POINTS (not pips). ES tick = 0.25 pts.
        /// </summary>
        private class TierConfig
        {
            public double AR_Max;
            public double AU;
            public public double Trigger;
        }

        private Dictionary<string, TierConfig> tierConfigs;

        // ═══════════════════════════════════════════════════════════════
        // STATE MACHINE VARIABLES
        // ═══════════════════════════════════════════════════════════════

        private CerberusState state;            // Current engine state
        private TradeDir impulseDirection;      // Direction of detected impulse
        private double swingOrigin;             // Reference price for impulse measurement
        private double impulseExtreme;          // High (LONG) or Low (SHORT) of impulse candle
        private double impulseSize;             // Impulse size in points
        private double killSwitchLevel;         // 80% retracement level — CLOSE ONLY
        private double activeAU;               // AU in points (assigned per tier)

        // ── Trade State ────────────────────────────────────────────────
        private double entryPrice;              // Entry price
        private double slPrice;                 // Stop Loss price (zero-buffer impulse extreme)
        private double tpPrice;                 // Take Profit price (1 AU from entry)
        private bool isActiveTrade;             // True when position is live

        // ── Session State ──────────────────────────────────────────────
        private double asianHigh;              // Asian session high
        private double asianLow;               // Asian session low
        private double asianRange;             // Asian range in points
        private string tierName;               // Current tier: T1, T2, T3, NO-GO
        private bool sessionActive;            // True when session has valid tier

        // ── Loop Tracking (Option B: Continuous Loop) ──────────────────
        private int loopCount;                  // Current loop number (1-based)
        private DateTime loopStartTime;         // When current loop began

        // ── Session Tracking ───────────────────────────────────────────
        private bool sessionInitialized;        // True once Asian Range is set
        private int lastSessionDate;            // DayOfYear of last session init
        private bool sessionBarResetDone;       // Flag to prevent double-reset on 3AM bar
        private double prevDayHigh;             // Previous day's high (used for Asian)
        private double prevDayLow;              // Previous day's low
        private bool asianRangeCaptureActive;   // True during Asian session capture
        private double runningAsianHigh;        // Tentative Asian high during capture
        private double runningAsianLow;         // Tentative Asian low during capture
        private bool asianRangeFinalized;       // True once Asian range is locked

        // ── Gear Shift State ───────────────────────────────────────────
        private double originalAU;              // Original tier AU before gear shift
        private bool gearShiftApplied;          // True if gear shift changed the target

        // ═══════════════════════════════════════════════════════════════
        // INITIALIZE — Called once when strategy is loaded
        // ═══════════════════════════════════════════════════════════════

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"CEREBUS Symmetry Trap Engine B — NT8 Strategy for ES Futures";
                Name = "CEREBUS_ST_NT8";
                Calculate = Calculate.OnBarClose;       // CEREBUS uses close-only invalidation
                BarsRequiredToTrade = 2;
                IsExitOnSessionCloseStrategy = true;     // Force close at session end
                ExitOnSessionCloseMinutes = 0;           // Close exactly at session end
                IsUnfillableProtection = false;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TraceOrders = true;

                // ── Default Session Boundaries (EST) ─────────────────────
                AsianSessionStartHour = 19;
                AsianSessionStartMinute = 0;
                AsianSessionEndHour = 3;
                AsianSessionEndMinute = 0;
                ActivationEndHour = 12;

                // ── ES Futures Tier Config (in POINTS) ───────────────────
                // ES tick size = 0.25 pts, tick value = $12.50
                // T1: AR < 20pts  → AU=10pts,  Trigger=12pts
                // T2: AR 20-30pts → AU=12pts,  Trigger=15pts
                // T3: AR 30-45pts → AU=15pts,  Trigger=19pts
                T1_AR_Max = 20.0;  T1_AU = 10.0;  T1_Trigger = 12.0;
                T2_AR_Max = 30.0;  T2_AU = 12.0;  T2_Trigger = 15.0;
                T3_AR_Max = 45.0;  T3_AU = 15.0;  T3_Trigger = 19.0;

                // ── Risk Parameters ──────────────────────────────────────
                MaxLoops = 5;
                KillSwitchPct = 0.80;

                // ── Display ──────────────────────────────────────────────
                DisplayInDataBox = true;
                DrawOnPricePanel = true;

                // ── Colors for chart markers ────────────────────────────
                AddPlot(new Stroke(Brushes.LimeGreen, 2), PlotStyle.Dot, "StateSignal");
            }
            else if (State == State.Configure)
            {
                // Nothing special needed here
            }
            else if (State == State.DataLoaded)
            {
                // Initialize tier config dictionary
                tierConfigs = new Dictionary<string, TierConfig>
                {
                    {
                        "T1", new TierConfig
                        {
                            AR_Max = T1_AR_Max,
                            AU = T1_AU,
                            Trigger = T1_Trigger
                        }
                    },
                    {
                        "T2", new TierConfig
                        {
                            AR_Max = T2_AR_Max,
                            AU = T2_AU,
                            Trigger = T2_Trigger
                        }
                    },
                    {
                        "T3", new TierConfig
                        {
                            AR_Max = T3_AR_Max,
                            AU = T3_AU,
                            Trigger = T3_Trigger
                        }
                    }
                };
            }
            else if (State == State.Terminated)
            {
                // Cleanup if needed
            }
        }

        // ═══════════════════════════════════════════════════════════════
        // ON BAR UPDATE — Main processing loop (called every bar)
        // ═══════════════════════════════════════════════════════════════

        protected override void OnBarUpdate()
        {
            // ── Guard: Only process primary bars, avoid multi-timeframe conflicts ──
            if (BarsInProgress != 0)
                return;

            // ── Guard: Need at least 2 bars ─────────────────────────────
            if (CurrentBar < 1)
                return;

            // ── Get current bar time in EST ──────────────────────────────
            DateTime barTimeEST = ConvertToEST(Time[0]);
            int barHour = barTimeEST.Hour;
            int barMinute = barTimeEST.Minute;
            int barDayOfYear = barTimeEST.DayOfYear;

            // ═══════════════════════════════════════════════════════════
            // PHASE 1: Capture Asian Range (19:00 EST → 03:00 EST)
            // ═══════════════════════════════════════════════════════════

            // Detect start of Asian session capture window (19:00–23:59 EST)
            bool inAsianPM = (barHour >= AsianSessionStartHour);
            // Detect end of Asian session capture (00:00–02:59 EST)
            bool inAsianAM = (barHour < AsianSessionEndHour);
            // Currently within Asian session?
            bool inAsianSession = inAsianPM || inAsianAM;

            if (inAsianSession && barDayOfYear != lastSessionDate)
            {
                if (!asianRangeCaptureActive)
                {
                    // Start capturing Asian range
                    asianRangeCaptureActive = true;
                    runningAsianHigh = High[0];
                    runningAsianLow = Low[0];
                    asianRangeFinalized = false;
                    PrintOutput(
                        string.Format(
                            "{0} [ASIAN] Capture started — H={1:F2}, L={2:F2}",
                            barTimeEST, runningAsianHigh, runningAsianLow
                        )
                    );
                }
                else
                {
                    // Update running Asian range
                    if (High[0] > runningAsianHigh)
                        runningAsianHigh = High[0];
                    if (Low[0] < runningAsianLow)
                        runningAsianLow = Low[0];
                }
            }

            // ═══════════════════════════════════════════════════════════
            // PHASE 2: Initialize session at 03:00 EST
            // ═══════════════════════════════════════════════════════════

            // Check if we've crossed the 03:00 EST boundary
            bool isActivationBar = (barHour == AsianSessionEndHour && barMinute >= AsianSessionEndMinute)
                                   || (barHour == AsianSessionEndHour + 1 && barMinute == 0 && !sessionInitialized);

            if (isActivationBar && !sessionInitialized && barDayOfYear != lastSessionDate)
            {
                // Finalize Asian range
                if (asianRangeCaptureActive)
                {
                    asianHigh = runningAsianHigh;
                    asianLow = runningAsianLow;
                    asianRangeFinalized = true;
                    asianRangeCaptureActive = false;
                }
                else
                {
                    // Fallback: use current bar's range if capture wasn't active
                    asianHigh = High[0];
                    asianLow = Low[0];
                }

                asianRange = asianHigh - asianLow;

                // Classify tier
                ClassifyTier();

                // Reset state machine
                state = CerberusState.Search;
                impulseDirection = TradeDir.Flat;
                impulseExtreme = 0.0;
                impulseSize = 0.0;
                killSwitchLevel = 0.0;
                entryPrice = 0.0;
                slPrice = 0.0;
                tpPrice = 0.0;
                isActiveTrade = false;
                sessionActive = tierName != "NO-GO";
                sessionInitialized = true;
                lastSessionDate = barDayOfYear;
                sessionBarResetDone = false;

                // Reset loop tracking
                loopCount = 1;
                loopStartTime = barTimeEST;

                // Reset gear shift
                originalAU = activeAU;
                gearShiftApplied = false;

                if (sessionActive)
                {
                    // Set swing origin to the FIRST bar's close at/after 3AM
                    swingOrigin = Close[0];

                    PrintOutput(
                        string.Format(
                            "{0} [SESSION] Init — Tier={1}, AU={2:F1}pts, Trigger={3:F1}pts, AR={4:F1}pts, Origin={5:F2}, Loop=1/{6}",
                            barTimeEST, tierName,
                            GetTierAU(tierName), GetTierTrigger(tierName),
                            asianRange, swingOrigin, MaxLoops
                        )
                    );
                }
                else
                {
                    PrintOutput(
                        string.Format(
                            "{0} [SESSION] NO-GO — AR={1:F1}pts (>{2:F1})",
                            barTimeEST, asianRange, T3_AR_Max
                        )
                    );
                    return;
                }
            }

            // ── Skip processing if session not active ───────────────────
            if (!sessionActive || !sessionInitialized)
                return;

            // ═══════════════════════════════════════════════════════════
            // PHASE 3: Hard Exit at 12:00 PM EST
            // ═══════════════════════════════════════════════════════════

            if (barHour >= ActivationEndHour)
            {
                if (isActiveTrade)
                {
                    PrintOutput(
                        string.Format(
                            "{0} [HARD EXIT] 12PM — Closing position @{1:F2}",
                            barTimeEST, Close[0]
                        )
                    );
                    ExitLong("12PM_HardExit");
                    ExitShort("12PM_HardExit");
                }

                HardExitSession();
                PrintOutput(
                    string.Format(
                        "{0} [SESSION] 12PM hard exit complete. Loop={1}/{2}",
                        barTimeEST, loopCount, MaxLoops
                    )
                );
                return;
            }

            // ═══════════════════════════════════════════════════════════
            // PHASE 4: STATE MACHINE
            // ═══════════════════════════════════════════════════════════

            // Get current bar OHLC (using [0] = current developing bar)
            double barOpen = Open[0];
            double barHigh = High[0];
            double barLow = Low[0];
            double barClose = Close[0];
            bool isBullish = barClose > barOpen;
            bool isBearish = barClose < barOpen;

            // Set swing origin from first bar if not yet set
            if (swingOrigin == 0.0 && state == CerberusState.Search)
                swingOrigin = barClose;

            // Active trigger for current tier
            double activeTrigger = GetTierTrigger(tierName);

            // Impulse measurements from swing origin
            double upMove = barHigh - swingOrigin;
            double dnMove = swingOrigin - barLow;

            // ─────────────────────────────────────────────────────────
            // STATE: SEARCH — Wait for impulse breach >= Tier Trigger
            // Reference: cerebus_qa_recap.md Q4
            // ─────────────────────────────────────────────────────────
            if (state == CerberusState.Search)
            {
                if (upMove >= activeTrigger)
                {
                    // LONG impulse detected
                    impulseDirection = TradeDir.Long;
                    impulseExtreme = barHigh;
                    impulseSize = upMove;

                    // Kill switch = 80% of impulse leg below extreme
                    killSwitchLevel = impulseExtreme - (upMove * KillSwitchPct);

                    // ── Gear Shift Check (from asset_configs.py) ────────
                    ApplyGearShift();

                    state = CerberusState.WaitDZ;

                    PrintOutput(
                        string.Format(
                            "{0} [IMPULSE] LONG — Extreme={1:F2}, Size={2:F1}pts, Kill={3:F2}, AU={4:F1}pts{5}",
                            barTimeEST, impulseExtreme, impulseSize,
                            killSwitchLevel, activeAU,
                            gearShiftApplied ? " [GEAR SHIFT to " + tierName + " AU]" : ""
                        )
                    );
                }
                else if (dnMove >= activeTrigger)
                {
                    // SHORT impulse detected
                    impulseDirection = TradeDir.Short;
                    impulseExtreme = barLow;
                    impulseSize = dnMove;

                    // Kill switch = 80% of impulse leg above extreme
                    killSwitchLevel = impulseExtreme + (dnMove * KillSwitchPct);

                    // ── Gear Shift Check ────────────────────────────────
                    ApplyGearShift();

                    state = CerberusState.WaitDZ;

                    PrintOutput(
                        string.Format(
                            "{0} [IMPULSE] SHORT — Extreme={1:F2}, Size={2:F1}pts, Kill={3:F2}, AU={4:F1}pts{5}",
                            barTimeEST, impulseExtreme, impulseSize,
                            killSwitchLevel, activeAU,
                            gearShiftApplied ? " [GEAR SHIFT to " + tierName + " AU]" : ""
                        )
                    );
                }
            }

            // ─────────────────────────────────────────────────────────
            // STATE: WAIT_DZ — Density Zone construction
            // Wait for pullback >= 1 AU OR 32%-50% Fib retracement
            // Reference: cerebus_qa_recap.md Q5, Q8, Q9
            // ─────────────────────────────────────────────────────────
            else if (state == CerberusState.WaitDZ)
            {
                // ── Kill Switch check (CLOSE-ONLY) ──────────────────────
                if (impulseDirection == TradeDir.Long && barClose < killSwitchLevel)
                {
                    PrintOutput(
                        string.Format(
                            "{0} [KILL SWITCH] Loop {1} — Close {2:F2} < Kill {3:F2}. Pathway VOID.",
                            barTimeEST, loopCount, barClose, killSwitchLevel
                        )
                    );
                    ResetStateAfterExit(barClose);
                    IncrementLoop(barTimeEST);
                    return;
                }
                else if (impulseDirection == TradeDir.Short && barClose > killSwitchLevel)
                {
                    PrintOutput(
                        string.Format(
                            "{0} [KILL SWITCH] Loop {1} — Close {2:F2} > Kill {3:F2}. Pathway VOID.",
                            barTimeEST, loopCount, barClose, killSwitchLevel
                        )
                    );
                    ResetStateAfterExit(barClose);
                    IncrementLoop(barTimeEST);
                    return;
                }

                // ── Dynamic DZ Thresholds (Option B: Continuous Loop) ──
                // Loop 1: strict Goldilocks zone (32%-50%)
                // Loop 2+: relaxed floor (20%-50% for shallow momentum pullbacks)
                double minRetracePct = (loopCount == 1) ? 0.32 : 0.20;
                double maxRetracePct = 0.50;

                // Pullback measurement from impulse extreme
                double pullback;
                if (impulseDirection == TradeDir.Long)
                    pullback = impulseExtreme - barLow;
                else
                    pullback = barHigh - impulseExtreme;

                // Fibonacci retracement ratio
                double retracePct = (impulseSize > 0.0) ? pullback / impulseSize : 0.0;

                // DZ penetration conditions
                bool auPenetrated = pullback >= activeAU;
                bool fibPenetrated = (retracePct >= minRetracePct) && (retracePct <= maxRetracePct);

                if (auPenetrated || fibPenetrated)
                {
                    state = CerberusState.WaitOCC;

                    PrintOutput(
                        string.Format(
                            "{0} [DZ] Penetrated — Pullback={1:F1}pts, Retrace={2:P1}, AU_ok={3}, Fib_ok={4}, Loop={5}",
                            barTimeEST, pullback, retracePct,
                            auPenetrated, fibPenetrated, loopCount
                        )
                    );
                }
            }

            // ─────────────────────────────────────────────────────────
            // STATE: WAIT_OCC — Wait for Opposite Candle Close
            // Candle must close in direction of impulse (confirming)
            // Reference: cerebus_qa_recap.md Q8
            // ─────────────────────────────────────────────────────────
            else if (state == CerberusState.WaitOCC)
            {
                // ── Re-verify Kill Switch ───────────────────────────────
                if (impulseDirection == TradeDir.Long && barClose < killSwitchLevel)
                {
                    PrintOutput(
                        string.Format(
                            "{0} [KILL SWITCH] WAIT_OCC — Close {1:F2} < Kill {2:F2}. Loop {3}.",
                            barTimeEST, barClose, killSwitchLevel, loopCount
                        )
                    );
                    ResetStateAfterExit(barClose);
                    IncrementLoop(barTimeEST);
                    return;
                }
                else if (impulseDirection == TradeDir.Short && barClose > killSwitchLevel)
                {
                    PrintOutput(
                        string.Format(
                            "{0} [KILL SWITCH] WAIT_OCC — Close {1:F2} > Kill {2:F2}. Loop {3}.",
                            barTimeEST, barClose, killSwitchLevel, loopCount
                        )
                    );
                    ResetStateAfterExit(barClose);
                    IncrementLoop(barTimeEST);
                    return;
                }

                // ── OCC Confirmation Check ──────────────────────────────
                bool occConfirmed = false;
                if (impulseDirection == TradeDir.Long && isBullish)
                    occConfirmed = true;
                else if (impulseDirection == TradeDir.Short && isBearish)
                    occConfirmed = true;

                if (occConfirmed)
                {
                    // ── ENTER TRADE ──────────────────────────────────────
                    entryPrice = barClose;
                    slPrice = impulseExtreme;  // ZERO BUFFER — exact extreme

                    // TP = 1 AU from entry in direction of trade
                    if (impulseDirection == TradeDir.Long)
                        tpPrice = entryPrice + activeAU;
                    else
                        tpPrice = entryPrice - activeAU;

                    state = CerberusState.InTrade;
                    isActiveTrade = true;

                    string dirStr = impulseDirection == TradeDir.Long ? "LONG" : "SHORT";
                    PrintOutput(
                        string.Format(
                            "{0} [ENTRY] {1} (Loop {2}/{3}) — Entry={4:F2}, SL={5:F2}, TP={6:F2} (1 AU = {7:F1}pts)",
                            barTimeEST, dirStr, loopCount, MaxLoops,
                            entryPrice, slPrice, tpPrice, activeAU
                        )
                    );

                    // ── Execute Orders ───────────────────────────────────
                    if (impulseDirection == TradeDir.Long)
                    {
                        EnterLong(Long.Limit(
                            entryPrice,
                            "ST_Entry_Loop" + loopCount), "ST_Entry");
                        SetStopLoss("ST_Entry", CalculationMode.Price, slPrice, false);
                        SetProfitTarget("ST_Entry", CalculationMode.Price, tpPrice);
                    }
                    else
                    {
                        EnterShort(Short.Limit(
                            entryPrice,
                            "ST_Entry_Loop" + loopCount), "ST_Entry");
                        SetStopLoss("ST_Entry", CalculationMode.Price, slPrice, false);
                        SetProfitTarget("ST_Entry", CalculationMode.Price, tpPrice);
                    }
                }
            }

            // ─────────────────────────────────────────────────────────
            // STATE: IN_TRADE — Monitor TP and SL
            // TP = wick OR close | SL = CLOSE-ONLY
            // Reference: cerebus_dual_engine.md (Zero-Buffer SL)
            // ─────────────────────────────────────────────────────────
            else if (state == CerberusState.InTrade && isActiveTrade)
            {
                if (impulseDirection == TradeDir.Long)
                {
                    // ── TP check: wick OR close ─────────────────────────
                    if (barHigh >= tpPrice)
                    {
                        PrintOutput(
                            string.Format(
                                "{0} [TP HIT] Loop {1} — High {2:F2} >= TP {3:F2}. Exit @{3:F2}.",
                                barTimeEST, loopCount, barHigh, tpPrice
                            )
                        );
                        ExitLong("ST_TP_Loop" + loopCount, "ST_Entry");
                        ResetStateAfterExit(tpPrice);
                        IncrementLoop(barTimeEST);
                        isActiveTrade = false;
                        return;
                    }

                    // ── SL check: CLOSE-ONLY (wicks don't count) ────────
                    if (barClose <= slPrice)
                    {
                        PrintOutput(
                            string.Format(
                                "{0} [SL HIT] Loop {1} — Close {2:F2} <= SL {3:F2}. Zero-Buffer Exit.",
                                barTimeEST, loopCount, barClose, slPrice
                            )
                        );
                        ExitLong("ST_SL_Loop" + loopCount, "ST_Entry");
                        ResetStateAfterExit(slPrice);
                        IncrementLoop(barTimeEST);
                        isActiveTrade = false;
                        return;
                    }
                }
                else if (impulseDirection == TradeDir.Short)
                {
                    // ── TP check: wick OR close ─────────────────────────
                    if (barLow <= tpPrice)
                    {
                        PrintOutput(
                            string.Format(
                                "{0} [TP HIT] Loop {1} — Low {2:F2} <= TP {3:F2}. Exit @{3:F2}.",
                                barTimeEST, loopCount, barLow, tpPrice
                            )
                        );
                        ExitShort("ST_TP_Loop" + loopCount, "ST_Entry");
                        ResetStateAfterExit(tpPrice);
                        IncrementLoop(barTimeEST);
                        isActiveTrade = false;
                        return;
                    }

                    // ── SL check: CLOSE-ONLY ────────────────────────────
                    if (barClose >= slPrice